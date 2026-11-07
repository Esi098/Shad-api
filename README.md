# shad-api

> Async Python client for **Shad** (`web.shad.ir`) — the Iranian messenger built on the **IranLMS** protocol.

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/python-3.10%2B-blue">
  <img alt="License" src="https://img.shields.io/badge/license-MIT-green">
  <img alt="Tests" src="https://img.shields.io/badge/tests-14%20offline-success">
  <a href="https://t.me/Homosapien_001"><img alt="Telegram" src="https://img.shields.io/badge/Telegram-%40Homosapien__001-26A5E4?logo=telegram&logoColor=white"></a>
</p>

`shad-api` is a small, dependency-light, fully async client for Shad. Every endpoint,
crypto step and transport quirk was extracted from the official Angular web bundle
(`app 4.4.26`) and verified against the live API. No browser, no Selenium, no
undocumented npm packages — just `aiohttp` + `cryptography`.

```python
import asyncio
from shad_api import ShadClient

async def main():
    client = ShadClient("session.json")
    await client.login_send_code("+98912...")     # SMS code
    await client.login_verify("12345")
    me = await client.get_user_info()              # "me" is not an object_guid
    await client.send_message(me["user_guid"], "hello from shad_api 👋")

asyncio.run(main())
```

---

## ✨ Features

| Area | What you get |
|---|---|
| **Auth** | SMS `sendCode` → `signIn` → RSA-OAEP key exchange → `registerDevice` |
| **Sessions** | JSON session file (mode `0600`) with token + RSA private key; reuse without SMS |
| **Profile** | `getUserInfo`, full profile fields |
| **Chats** | `getChats` / `getChatsByID` with paging; groups, channels, users, service chats |
| **Contacts** | `getContacts` with paging |
| **Messages** | `sendMessage`, `getMessages`, `deleteMessages` |
| **Files** | chunked upload (up to **100 MiB**), `send_file`, `send_uploaded_file` (upload once, send to many), zip/split helpers, chunked download |
| **2FA** | status, setup, change, disable, recovery email |
| **Devices** | list/terminate sessions, unconfirmed-session actions |
| **Async** | pure `asyncio`, `aiohttp`, no threads |
| **Typing** | complete type hints, ships `py.typed` |
| **Tests** | 14 offline tests (crypto, sessions, static client logic) — no network needed |

## 📦 Install

```bash
git clone <your-fork-url> shad-api
cd shad-api
python -m pip install .
# development: python -m pip install -e ".[dev]"
```

Requires **Python 3.10+**, `aiohttp`, `cryptography`.

## 🚀 Quick start

### 1) Log in once

```bash
python examples/login.py
```

`login.py` asks for the phone number and the SMS code, then saves `session.json`
(contains the auth token and RSA key — **keep it private**).

### 2) Use the session

```python
import asyncio
from shad_api import ShadClient

async def main():
    client = ShadClient("session.json")

    me = await client.get_user_info()
    print(me["first_name"], me.get("username"))

    await client.send_message(me["user_guid"], "Saved Messages test ✅")

asyncio.run(main())
```

### 3) List chats and contacts

```python
chats = await client.get_all_chats()        # follows next_start_id automatically
contacts = await client.get_all_contacts()

for chat in chats[:20]:
    obj = chat.get("abs_object") or {}
    print(obj.get("type"), client.chat_title(chat), chat["object_guid"])
```

### 4) Send a file with progress

```python
def progress(done, total, label=""):
    print(f"\r{done}/{total}  {label}", end="", flush=True)

me = await client.get_user_info()
result = await client.send_file(
    me["user_guid"], "video.mp4", caption="hi", progress=progress,
)
```

### 5) Files that Shad blocks or that are too large

```python
me = await client.get_user_info()
await client.send_file_zipped(me["user_guid"], "app.apk")      # blocked extension
await client.send_file_split(me["user_guid"], "movie.mkv")     # >100 MiB
```

### 6) Download a file descriptor

```python
info = {
    "file_id": "...", "dc_id": "165",
    "access_hash_rec": "...", "size": 12345,
}
await client.download_file(info, "out.bin")
```

### 7) Two-step verification

```python
status = await client.get_two_passcode_status()
await client.setup_two_step("new-password", "my hint")
await client.change_two_step_password("old", "new", "new hint")
await client.turn_off_two_step("current-password")
```

### 8) Sessions on other devices

```python
sessions = await client.get_sessions()
await client.terminate_other_sessions()      # or terminate_session(key)
unconfirmed = await client.get_unconfirmed_sessions()
```

## 🧭 Full API reference

<details>
<summary><b>Click to expand the method table</b></summary>

| Group | Methods |
|---|---|
| Login | `login_send_code(phone)`, `login_verify(code)`, `register_device()` |
| Low-level | `call(method, model=None, api_version="6")` |
| Profile | `get_user_info(user_guid="")` |
| Chats | `get_chats(start_id="")`, `get_chat(guid)`, `get_all_chats(limit=2000)` |
| Contacts | `get_contacts(start_id="")`, `get_all_contacts(limit=2000)` |
| Messages | `get_messages(guid, sort="FromMax", limit=20, max_id="", filter_type="")`, `send_message(guid, text, message_id="")`, `delete_messages(guid, ids, delete_for_all=True)` |
| Files | `request_send_file(name, size, mime)`, `upload_file(path, mime="", chunk_size=131072, progress=None)`, `send_uploaded_file(guid, info, caption="")`, `send_file(guid, path, caption="", mime="", progress=None)`, `send_file_zipped(...)`, `send_file_split(...)`, `download_file(info, out_path, chunk_size=1048576)` |
| 2FA | `get_two_passcode_status()`, `check_passcode(pw)`, `setup_two_step(pw, hint, email="")`, `change_two_step_password(old, new, hint)`, `turn_off_two_step(pw)`, `abort_two_step_setup()` |
| Recovery email | `request_recovery_email(pw, email)`, `verify_recovery_email(code, pw="")`, `resend_recovery_email(pw)`, `abort_recovery_email(pw)` |
| Devices | `get_sessions()`, `terminate_session(key)`, `terminate_other_sessions()`, `get_unconfirmed_sessions()`, `action_on_unconfirmed_session(key, action)` |
| Helpers | `chat_title(chat)`, `chats_overview(data)`, `check_extension(path)`, `guess_mime(path)` |

</details>

## 🔐 How it works (short version)

Shad is **not** REST-per-method. Each operation is a `POST` with an IranLMS
envelope carrying the method name:

```jsonc
{
  "api_version": "6",
  "auth": "<session token>",
  "data_enc": "<AES-encrypted {method, input, client}>",
  "sign": "<RSA-SHA256 signature>"
}
```

* `data_enc` = AES-256-CBC with an IV of zeros; the key is the bundle's
  “secret passphrase” transform of the session token.
* The public key sent during login is the **obfuscated** base64(PEM) transform
  (`Xg()` in the bundle).
* `signIn` returns the auth token RSA-OAEP(SHA-1)-encrypted with your public key.
* API base URLs are discovered with `getDCs` and rotated on failure.
* File bytes are uploaded chunk-by-chunk to the URL returned by
  `requestSendFile`, then sent as a `file_inline` message.

Full reverse-engineering notes: [`docs/API.md`](docs/API.md).

## ⚠️ Limits & caveats

- **Unofficial.** Not affiliated with Shad/ IranLMS. The API can change without notice.
- **100 MiB per file** (`INVALID_INPUT` above that). Blocked extensions:
  `.apk .bin .gz .7z .exe .iso .dmg .msi .jar .sh .bat` — zip them or use
  `send_file_zipped`.
- **2FA sign-in is not implemented** by this client (the CLI could only manage
  2FA, not sign in with it). Accounts with 2FA must disable it temporarily or
  sign in from the official app.
- Session files contain a **token and a private key**. Store them `0600`, never
  commit them (`.gitignore` already excludes them).
- Use responsibly: respect Shad's terms of service and rate limits.

## 🧪 Tests

```bash
python -m pytest          # 14 offline tests, no network
```

The suite covers the crypto round-trip, session persistence/permissions, error
hierarchy, URL rotation, and the static client helpers.

## 🗂 Project layout

```
shad-api/
├── shad_api/
│   ├── __init__.py      # public API, version, author
│   ├── client.py        # ShadClient (all high-level methods)
│   ├── config.py        # endpoints, versions, limits
│   ├── crypto.py        # AES envelope + RSA handshake
│   ├── errors.py        # ShadError / ShadAuthError / ShadResponseError
│   ├── http.py          # transport, discovery, failover
│   └── session.py       # atomic JSON session storage (0600)
├── examples/            # login, list chats, send message, send file
├── docs/API.md          # reverse-engineering notes
├── tests/               # offline pytest suite
├── pyproject.toml
├── LICENSE
└── README.md
```

## 🙌 Credits

**Built by Esi** — [Telegram: @Homosapien_001](https://t.me/Homosapien_001)

If this library saved you some time, a ⭐ on the repo and a message on Telegram
are the best thanks.

## 📄 License

[MIT](LICENSE) © 2026 Esi
