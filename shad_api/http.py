# Built by Esi — https://t.me/Homosapien_001
"""Shad transport: discovery + IranLMS envelope POST with failover."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import aiohttp

from . import crypto
from .config import (API_URLS, CLIENT, DC_URL, REQUEST_TIMEOUT, SERVICE_BASE,
                     USER_AGENT)
from .errors import ShadError, ShadResponseError


class ShadTransport:
    def __init__(self, api_urls: Optional[List[str]] = None):
        self.api_urls = list(api_urls or API_URLS)
        self._index = 0

    # ------------------------------------------------------------------ #
    @property
    def api_url(self) -> str:
        return self.api_urls[self._index % len(self.api_urls)]

    def rotate(self) -> str:
        self._index += 1
        return self.api_url

    async def _post(self, url: str, payload: Dict[str, Any],
                    content_type: str = "text/plain") -> Dict[str, Any]:
        timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
        headers = {
            "Content-Type": content_type,
            "Origin": "https://web.shad.ir",
            "Referer": "https://web.shad.ir/",
            "User-Agent": USER_AGENT,
        }
        async with aiohttp.ClientSession(timeout=timeout) as http:
            async with http.post(url, data=json.dumps(payload), headers=headers) as resp:
                text = await resp.text()
                if resp.status >= 500:
                    raise ShadResponseError("SERVER_ERROR", f"HTTP {resp.status}")
                try:
                    data = json.loads(text)
                except ValueError as exc:
                    raise ShadError(f"Invalid Shad response: {text[:200]}") from exc
                return data

    # ------------------------------------------------------------------ #
    # plain endpoints (api_version 4/0, no encryption)
    async def get_dcs(self) -> Dict[str, Any]:
        result = await self._post(DC_URL, {
            "api_version": "4", "method": "getDCs", "data": {}, "client": CLIENT,
        }, content_type="application/json")
        data = result.get("data") or result
        if data.get("default_api_urls"):
            self.api_urls = list(data["default_api_urls"])
        return data

    async def get_base_info(self) -> Dict[str, Any]:
        result = await self._post(SERVICE_BASE, {
            "method": "getBaseInfo", "api_version": "0", "data": {},
            "client": CLIENT,
        }, content_type="application/json")
        return result.get("data") or result

    # ------------------------------------------------------------------ #
    # envelope calls
    async def call(self, method: str, model: Optional[Dict[str, Any]],
                   secret: str, *, api_version: str = "6",
                   auth_token: Optional[str] = None, private_pem: Optional[str] = None,
                   not_authorized: bool = False) -> Dict[str, Any]:
        """One API call; `secret` = tmp_session (login) or auth token."""
        payload: Dict[str, Any] = {
            "api_version": api_version,
            "data_enc": crypto.encrypt({"method": method, "input": model or {},
                                        "client": CLIENT}, secret),
        }
        if not_authorized:
            payload["tmp_session"] = secret
        else:
            # api_version 6: obfuscated auth + RSA-SHA256 signature over data_enc
            if auth_token:
                payload["auth"] = crypto.obfuscate(auth_token)
            if private_pem:
                payload["sign"] = crypto.sign_data_enc(private_pem, payload["data_enc"])
        last_error: Optional[Exception] = None
        for _ in range(len(self.api_urls)):
            try:
                result = await self._post(self.api_url, payload)
            except Exception as exc:
                last_error = exc
                self.rotate()
                continue
            if result.get("data_enc"):
                decoded = json.loads(crypto.decrypt(result["data_enc"], secret))
                if decoded.get("status") != "OK":
                    raise ShadResponseError(str(decoded.get("status")),
                                            str(decoded.get("status_det")))
                return decoded.get("data") or {}
            if result.get("status") == "OK":
                return result.get("data") or {}
            raise ShadResponseError(str(result.get("status")),
                                    str(result.get("status_det")))
        raise ShadError(f"All Shad API servers failed: {last_error}")
