# Built by Esi — https://t.me/Homosapien_001
"""High-level async Shad client (IranLMS API).

Features (live-verified):
  * login: sendCode -> signIn -> RSA-OAEP auth decrypt -> registerDevice
  * profile: getUserInfo
  * chats: getChats, getChatsByID, getMessages, sendMessage, deleteMessages
  * contacts: getContacts, getContactsUpdates
  * files: requestSendFile -> chunked POST upload; GetFile.ashx download
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from . import crypto
from .config import API_VERSION, CLIENT_VERSION, MAX_FILE_SIZE
from .errors import ShadAuthError, ShadError, ShadResponseError
from .http import ShadTransport
from .session import ShadSession


class ShadClient:
    def __init__(self, session_file: str, phone: Optional[str] = None):
        self.session = ShadSession(session_file)
        if phone:
            self.session["phone"] = phone
        self.transport = ShadTransport()
        api = self.session["api_url"]
        if api:
            self.transport.api_urls.insert(0, api)

    # ------------------------------------------------------------------ #
    # login
    # ------------------------------------------------------------------ #
    async def login_send_code(self, phone: str) -> Dict[str, Any]:
        phone = "".join(c for c in str(phone) if c.isdigit())
        if phone.startswith("0"):
            phone = "98" + phone[1:]
        if phone.startswith("0098"):
            phone = phone[4:]
        await self.transport.get_dcs()
        keys = crypto.generate_keypair()
        tmp = crypto.new_tmp_session()
        model = {"phone_number": phone, "send_type": "SMS",
                 "public_key": keys["public_key"]}
        result = await self.transport.call("sendCode", model, tmp,
                                           api_version="6", not_authorized=True)
        self.session.set_many(phone=phone, api_url=self.transport.api_url,
                              pending={**keys, "tmp": tmp,
                                       "phone_code_hash": result.get("phone_code_hash")})
        self.session.save()
        return result

    async def login_verify(self, code: str) -> Dict[str, Any]:
        pending = self.session["pending"] or {}
        if not pending.get("tmp"):
            raise ShadAuthError("Call login_send_code() first.")
        model = {"phone_number": self.session["phone"],
                 "phone_code_hash": pending.get("phone_code_hash"),
                 "phone_code": str(code),
                 "public_key": pending["public_key"]}
        data = await self.transport.call("signIn", model, pending["tmp"],
                                          api_version="6", not_authorized=True)
        auth = crypto.rsa_decrypt_oaep(pending["private_pem"], data["auth"])
        self.session.set_many(auth=auth, priv_pem=pending["private_pem"],
                              pub_pem=pending["public_pem"],
                              public_key=pending["public_key"],
                              api_url=self.transport.api_url)
        self.session["device_hash"] = self.session["device_hash"] or ("web-" + os.urandom(8).hex())
        self.session.pop("pending")
        self.session.save()
        await self.register_device()
        return data.get("user") or {}

    # ------------------------------------------------------------------ #
    async def register_device(self) -> Dict[str, Any]:
        model = {"token_type": "Web", "token": "",
                 "app_version": CLIENT_VERSION, "lang_code": "fa",
                 "system_version": "Linux", "device_model": "Chrome",
                 "device_hash": self.session["device_hash"]}
        return await self.call("registerDevice", model)

    async def call(self, method: str, model: Optional[Dict[str, Any]] = None,
                   api_version: str = API_VERSION) -> Dict[str, Any]:
        if not self.session.has_auth:
            raise ShadAuthError("No Shad session: call login_send_code()/login_verify() first.")
        return await self.transport.call(method, model or {}, self.session.auth,
                                         api_version=api_version,
                                         auth_token=self.session.auth,
                                         private_pem=self.session["priv_pem"])

    # ------------------------------------------------------------------ #
    # profile / chats / contacts
    async def get_user_info(self, user_guid: str = "") -> Dict[str, Any]:
        data = await self.call("getUserInfo", {"user_guid": user_guid} if user_guid else {})
        return data.get("user") or data

    async def get_chats(self, start_id: str = "") -> Dict[str, Any]:
        model = {"start_id": start_id} if start_id else {}
        return await self.call("getChats", model)

    async def get_chat(self, object_guid: str) -> Dict[str, Any]:
        data = await self.call("getChatsByID", {"object_guids": [object_guid]})
        chats = data.get("chats") or []
        return chats[0] if chats else {}

    async def get_contacts(self, start_id: str = "") -> Dict[str, Any]:
        return await self.call("getContacts", {"start_id": start_id} if start_id else {})

    # Chat/contact listing is paginated (has_continue/next_start_id); cap the
    # walk so an account with thousands of dialogs still returns promptly.
    MAX_LIST_ITEMS = 2000

    async def get_all_chats(self, limit: int = MAX_LIST_ITEMS) -> List[Dict[str, Any]]:
        """Walk every getChats page and return the raw chat dicts."""
        chats: List[Dict[str, Any]] = []
        start_id = ""
        while len(chats) < limit:
            data = await self.get_chats(start_id)
            chats.extend(data.get("chats") or [])
            next_id = str(data.get("next_start_id") or "")
            # A server that answers has_continue without advancing the cursor
            # would loop forever; stop on it instead.
            if not data.get("has_continue") or not next_id or next_id == start_id:
                break
            start_id = next_id
        return chats[:limit]

    async def get_all_contacts(self, limit: int = MAX_LIST_ITEMS) -> List[Dict[str, Any]]:
        """Walk every getContacts page and return the raw user dicts."""
        users: List[Dict[str, Any]] = []
        start_id = ""
        while len(users) < limit:
            data = await self.get_contacts(start_id)
            users.extend(data.get("users") or [])
            next_id = str(data.get("next_start_id") or "")
            if not data.get("has_continue") or not next_id or next_id == start_id:
                break
            start_id = next_id
        return users[:limit]

    async def get_messages(self, object_guid: str, *, sort: str = "FromMax",
                           limit: int = 20, max_id: str = "",
                           filter_type: str = "") -> Dict[str, Any]:
        model: Dict[str, Any] = {"object_guid": object_guid, "sort": sort,
                                 "limit": limit}
        if max_id:
            model["max_id"] = max_id
        if filter_type:
            model["filter_type"] = filter_type
        return await self.call("getMessages", model)

    @staticmethod
    def chat_title(chat: Dict[str, Any]) -> str:
        obj = chat.get("abs_object") or {}
        if obj.get("title"):
            return str(obj["title"])
        name = " ".join(x for x in (obj.get("first_name"), obj.get("last_name")) if x)
        return name or chat.get("object_guid", "")

    def chats_overview(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        out = []
        for chat in data.get("chats") or []:
            obj = chat.get("abs_object") or {}
            out.append({"guid": chat.get("object_guid"),
                        "title": self.chat_title(chat),
                        "type": obj.get("type"),
                        "unread": chat.get("count_unseen") or 0,
                        "last_message_id": chat.get("last_message_id"),
                        "abs_object": obj})
        return out

    async def send_message(self, object_guid: str, text: str,
                           message_id: str = "") -> Dict[str, Any]:
        model = {"object_guid": object_guid, "rnd": int.from_bytes(os.urandom(4), "big") // 2,
                 "text": text}
        if message_id:
            model["message_id"] = message_id
        return await self.call("sendMessage", model)

    async def delete_messages(self, object_guid: str, message_ids: List[str],
                              delete_for_all: bool = True) -> Dict[str, Any]:
        return await self.call("deleteMessages", {
            "object_guid": object_guid, "message_ids": message_ids,
            "type": "Global" if delete_for_all else "Local"})

    # ------------------------------------------------------------------ #
    # two-step (2FA) & sessions
    async def get_two_passcode_status(self) -> Dict[str, Any]:
        data = await self.call("getTwoPasscodeStatus")
        return data.get("two_step_status") or data

    async def check_passcode(self, password: str) -> Dict[str, Any]:
        return await self.call("checkTwoPasscode", {"password": password})

    async def setup_two_step(self, password: str, hint: str,
                             recovery_email: str = "") -> Dict[str, Any]:
        model: Dict[str, Any] = {"password": password, "hint": hint}
        if recovery_email:
            model["recovery_email"] = recovery_email
        data = await self.call("setupTwoStepVerification", model)
        return data.get("two_step_status") or data

    async def change_two_step_password(self, old_password: str, new_password: str,
                                       new_hint: str) -> Dict[str, Any]:
        data = await self.call("changePassword", {
            "password": old_password, "new_password": new_password,
            "new_hint": new_hint})
        return data.get("two_step_status") or data

    async def turn_off_two_step(self, password: str) -> Dict[str, Any]:
        return await self.call("turnOffTwoStep", {"password": password})

    async def abort_two_step_setup(self) -> Dict[str, Any]:
        return await self.call("abortTwoStepSetup")

    async def request_recovery_email(self, password: str, email: str) -> Dict[str, Any]:
        data = await self.call("requestRecoveryEmail",
                               {"password": password, "recovery_email": email})
        return data.get("two_step_status") or data

    async def verify_recovery_email(self, code: str,
                                    password: str = "") -> Dict[str, Any]:
        model: Dict[str, Any] = {"code": code}
        if password:
            model["password"] = password
        return await self.call("verifyRecoveryEmail", model)

    async def resend_recovery_email(self, password: str) -> Dict[str, Any]:
        return await self.call("resendCodeRecoveryEmail", {"password": password})

    async def abort_recovery_email(self, password: str) -> Dict[str, Any]:
        return await self.call("abortSetRecoveryEmail", {"password": password})

    # sessions
    async def get_sessions(self) -> Dict[str, Any]:
        data = await self.call("getMySessions", {})
        return {"active": data.get("active_session") or {},
                "others": data.get("other_sessions") or [],
                "can_remove_all": bool(data.get("can_remove_all"))}

    async def terminate_session(self, session_key: str) -> Dict[str, Any]:
        return await self.call("terminateSession", {"session_key": session_key})

    async def terminate_other_sessions(self) -> Dict[str, Any]:
        return await self.call("terminateOtherSessions", {})

    async def get_unconfirmed_sessions(self) -> List[Dict[str, Any]]:
        data = await self.call("getUnconfirmedSessions")
        return data.get("unconfirmed_sessions") or []

    async def action_on_unconfirmed_session(self, key: str,
                                            action: str) -> Dict[str, Any]:
        return await self.call("actionOnUnconfirmedSession",
                               {"unconfirmed_session_key": key, "action": action})

    # ------------------------------------------------------------------ #
    # files
    async def request_send_file(self, name: str, size: int, mime: str) -> Dict[str, Any]:
        if size > MAX_FILE_SIZE:
            raise ShadError(
                f"File is {size/1024/1024:.1f}MB, above the Shad limit of "
                f"{MAX_FILE_SIZE/1024/1024:.0f}MB. Compress it or split it into parts.")
        try:
            return await self.call("requestSendFile",
                                   {"file_name": name, "size": size, "mime": mime})
        except ShadResponseError as exc:
            if exc.status == "ERROR_GENERIC" and exc.detail == "INVALID_AUTH":
                raise ShadError(
                    "Shad does not allow this file type (e.g. apk/bin/gz/7z). "
                    "Zip it or send it with send_file_zipped().") from exc
            if exc.detail == "INVALID_INPUT":
                raise ShadError(
                    f"Shad rejected the upload request (INVALID_INPUT): "
                    f"{size/1024/1024:.1f}MB size or invalid MIME.") from exc
            raise

    MIME_TYPES = {
        ".txt": "text/plain", ".pdf": "application/pdf", ".zip": "application/zip",
        ".rar": "application/vnd.rar", ".7z": "application/x-7z-compressed",
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
        ".gif": "image/gif", ".webp": "image/webp", ".mp4": "video/mp4",
        ".mkv": "video/x-matroska", ".mov": "video/quicktime",
        ".mp3": "audio/mpeg", ".ogg": "audio/ogg", ".wav": "audio/wav",
        ".doc": "application/msword",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".xls": "application/vnd.ms-excel",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".ppt": "application/vnd.ms-powerpoint",
        ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    }

    BLOCKED_EXT = {".apk", ".bin", ".gz", ".7z", ".exe", ".iso", ".dmg",
                   ".msi", ".jar", ".sh", ".bat"}

    @classmethod
    def check_extension(cls, path: str) -> None:
        ext = os.path.splitext(path)[1].lower()
        if ext in cls.BLOCKED_EXT:
            raise ShadError(
                f"Shad does not allow the {ext} extension. Zip the file or use send_file_zipped().")

    @classmethod
    def guess_mime(cls, path: str) -> str:
        ext = os.path.splitext(path)[1].lower()
        return cls.MIME_TYPES.get(ext, "application/octet-stream")

    async def upload_file(self, path: str, mime: str = "",
                          chunk_size: int = 131072,
                          progress=None) -> Dict[str, Any]:
        """Upload a local file; returns the file descriptor usable in messages."""
        size = os.path.getsize(path)
        self.check_extension(path)
        mime = mime or self.guess_mime(path)
        info = await self.request_send_file(os.path.basename(path), size, mime)
        upload_url = info.get("upload_url")
        file_id = info.get("id")
        access = info.get("access_hash_send")
        dc_id = str(info.get("dc_id"))
        if not upload_url or not file_id:
            raise ShadError(f"requestSendFile returned an incomplete response: {info}")
        total = max(1, (size + chunk_size - 1) // chunk_size)
        access_hash_rec = None
        import aiohttp
        with open(path, "rb") as fh:
            for part in range(1, total + 1):
                chunk = fh.read(chunk_size)
                headers = {
                    "access-hash-send": access, "auth": self.session.auth,
                    "file-id": str(file_id), "part-number": str(part),
                    "total-part": str(total), "chunk-size": str(len(chunk)),
                    "Content-Type": "application/octet-stream",
                    "User-Agent": "Mozilla/5.0",
                }
                async with aiohttp.ClientSession() as http:
                    async with http.post(upload_url, data=chunk, headers=headers) as resp:
                        body = await resp.json(content_type=None)
                if body.get("status_det") != "OK":
                    raise ShadError(f"Upload of part {part} failed: {body}")
                access_hash_rec = ((body.get("data") or {}).get("access_hash_rec")
                                   or access_hash_rec)
                if progress:
                    try:
                        await progress(part, total, f"uploading part {part}/{total}")
                    except Exception:
                        pass
        return {"file_id": str(file_id), "dc_id": dc_id,
                "access_hash_rec": access_hash_rec, "size": size, "mime": mime,
                "file_name": os.path.basename(path)}

    async def send_file_zipped(self, object_guid: str, path: str, caption: str = "") -> Dict[str, Any]:
        """Zip a file (allowed by Shad) and send the archive."""
        import zipfile
        archive = f"/tmp/{os.path.basename(path)}.zip"
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.write(path, arcname=os.path.basename(path))
        try:
            return await self.send_file(object_guid, archive, caption,
                                        mime="application/zip")
        finally:
            try:
                os.remove(archive)
            except OSError:
                pass

    async def send_file_split(self, object_guid: str, path: str, caption: str = "",
                              part_size: int = MAX_FILE_SIZE - 1) -> List[Dict[str, Any]]:
        """Split a file into <100MiB parts and send each as a separate file message."""
        import math
        size = os.path.getsize(path)
        parts = max(1, math.ceil(size / part_size))
        results: List[Dict[str, Any]] = []
        base = os.path.basename(path)
        with open(path, "rb") as fh:
            for index in range(parts):
                chunk = fh.read(part_size)
                tmp_path = f"/tmp/shad_part_{index+1:02d}_{base}"
                with open(tmp_path, "wb") as out:
                    out.write(chunk)
                cap = f"{caption} ({index+1}/{parts})" if caption else f"{base} {index+1}/{parts}"
                results.append(await self.send_file(object_guid, tmp_path, cap,
                                                  mime=self.guess_mime(path)))
                os.remove(tmp_path)
        return results

    async def send_uploaded_file(self, object_guid: str, info: Dict[str, Any],
                                 caption: str = "") -> Dict[str, Any]:
        """Send a descriptor returned by ``upload_file`` to one chat.

        Bulk sends upload the bytes once and reuse this per target, instead of
        re-uploading the same file for every recipient.
        """
        file_inline = {
            "file_name": info["file_name"], "size": info["size"],
            "type": "File", "mime": info["mime"],
            "file_id": info["file_id"], "dc_id": info["dc_id"],
            "access_hash_rec": info["access_hash_rec"],
        }
        model: Dict[str, Any] = {
            "object_guid": object_guid,
            "rnd": int.from_bytes(os.urandom(4), "big") // 2,
            "file_inline": file_inline,
        }
        if caption:
            model["text"] = caption
        return await self.call("sendMessage", model)

    async def send_file(self, object_guid: str, path: str, caption: str = "",
                        mime: str = "", progress=None) -> Dict[str, Any]:
        """Upload and send a file as an inline file message."""
        info = await self.upload_file(path, mime, progress=progress)
        return await self.send_uploaded_file(object_guid, info, caption)

    async def download_file(self, file: Dict[str, Any], out_path: str,
                            chunk_size: int = 1048576) -> str:
        """Download a file descriptor (dc_id/file_id/access_hash_rec/size)."""
        import aiohttp
        dc_id = str(file.get("dc_id"))
        file_id = str(file.get("file_id"))
        access = file.get("access_hash_rec")
        total = int(file.get("size") or 0)
        dcs = await self.transport.get_dcs()
        url = (dcs.get("storages") or {}).get(dc_id)
        if not url:
            raise ShadError(f"No storage URL for dc_id={dc_id}.")
        with open(out_path, "wb") as fh:
            start = 0
            while True:
                end = start + chunk_size - 1
                if total:
                    end = min(end, total - 1)
                headers = {"access-hash-rec": access, "auth": self.session.auth,
                           "file-id": file_id, "start-index": str(start),
                           "last-index": str(end), "Content-Type": "text/plain"}
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, data=b"", headers=headers) as resp:
                        chunk = await resp.read()
                        fh.write(chunk)
                if total == 0 or start + len(chunk) >= total or not chunk:
                    break
                start += len(chunk)
        return out_path
