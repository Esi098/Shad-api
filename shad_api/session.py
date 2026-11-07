# Built by Esi — https://t.me/Homosapien_001
"""Per-account Shad session storage (mode 0600, atomic write).

A session file is plain JSON::

    {
      "phone": "+989...", "auth": "<token>", "priv_pem": "...",
      "pub_pem": "...", "public_key": "...", "api_url": "...",
      "device_hash": "...",
      "pending": {"tmp": "...", "priv_pem": "...", "public_key": "...",
                  "phone_code_hash": "...", "api_url": "..."}
    }

Keep it private: it contains the account token and the RSA private key.
"""

from __future__ import annotations

import json
import os
import time


class ShadSession:
    def __init__(self, path: str):
        self.path = path
        self._data = self._load()

    def _load(self) -> dict:
        try:
            with open(self.path, encoding="utf-8") as fh:
                data = json.load(fh)
            return data if isinstance(data, dict) else {}
        except (OSError, ValueError):
            return {}

    def save(self) -> None:
        parent = os.path.dirname(self.path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        self._data["saved_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(self._data, fh, ensure_ascii=False, indent=2)
        os.chmod(tmp, 0o600)
        os.replace(tmp, self.path)

    def __getitem__(self, key, default=None):
        return self._data.get(key, default)

    def __setitem__(self, key, value):
        self._data[key] = value

    def set_many(self, **kwargs) -> None:
        self._data.update(kwargs)

    def pop(self, key, default=None):
        return self._data.pop(key, default)

    @property
    def data(self) -> dict:
        return self._data

    @property
    def auth(self) -> str:
        return str(self._data.get("auth") or "")

    @property
    def phone(self) -> str:
        return str(self._data.get("phone") or "")

    @property
    def has_auth(self) -> bool:
        return bool(self.auth)

    @property
    def masked(self) -> str:
        p = self.phone
        return p[:4] + "***" + p[-2:] if len(p) > 6 else "***"
