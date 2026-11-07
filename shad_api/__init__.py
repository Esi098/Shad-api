# Built by Esi — https://t.me/Homosapien_001
"""Shad (web.shad.ir) client — IranLMS API, modular implementation.

A small, dependency-light async client for the Iranian messenger **Shad**
(web.shad.ir). Everything is reverse-engineered from the official Angular web
bundle and verified against the live API.

Quick start::

    import asyncio
    from shad_api import ShadClient

    async def main():
        client = ShadClient("session.json")
        await client.login_send_code("+98912...")
        await client.login_verify(input("code: "))
        await client.send_message("me", "hello from shad_api")

    asyncio.run(main())

Author: Esi — https://t.me/Homosapien_001
License: MIT
"""

from .client import ShadClient
from .config import API_VERSION, APP_VERSION, MAX_FILE_SIZE
from .errors import ShadAuthError, ShadError, ShadResponseError
from .session import ShadSession

__version__ = "1.0.0"
__author__ = "Esi"
__author_telegram__ = "https://t.me/Homosapien_001"
__license__ = "MIT"

__all__ = [
    "ShadClient",
    "ShadSession",
    "ShadError",
    "ShadAuthError",
    "ShadResponseError",
    "API_VERSION",
    "APP_VERSION",
    "MAX_FILE_SIZE",
    "__version__",
    "__author__",
    "__author_telegram__",
]
