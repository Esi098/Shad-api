# Built by Esi — https://t.me/Homosapien_001
"""Shad (web.shad.ir) wire configuration.

Everything here was extracted from the Angular bundle (app 4.4.26) and verified
live. Shad is not REST: every call is a POST to a pool URL with an IranLMS
envelope (see docs/SHAD_API.md).
"""

API_VERSION = "6"
APP_VERSION = "4.4.26"
APK_VERSION = "2.8.2"

DC_URL = "https://shgetdcmess.iranlms.ir"
SERVICE_BASE = "https://shservicesbase.iranlms.ir/"

# Fallbacks from the live getDCs response (2026-11-06); refreshed on every login.
API_URLS = [
    "https://shadmessenger125.iranlms.ir",
    "https://shadmessenger180.iranlms.ir",
    "https://shadmessenger152.iranlms.ir",
]
BOT_URLS = [
    "https://shadmessenger7.iranlms.ir",
    "https://shadmessenger3.iranlms.ir",
    "https://shadmessenger5.iranlms.ir",
]
SOCKET_URLS = [
    "wss://shsocket5.iranlms.ir:80",
    "wss://shsocket1.iranlms.ir:80",
    "wss://shsocket13.iranlms.ir:80",
]
STORAGE_BASE = "https://shstorage501.iranlms.ir/GetFile.ashx"

CLIENT = {
    "app_name": "Main",
    "app_version": APP_VERSION,
    "platform": "Web",
    "package": "web.shad.ir",
    "lang_code": "fa",
}
CLIENT_VERSION = "WB_" + APP_VERSION

USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
REQUEST_TIMEOUT = 25
# requestSendFile rejects anything above 100 MiB with INVALID_INPUT (live tested:
# 104857600 OK, 105000000 INVALID_INPUT).
MAX_FILE_SIZE = 104857600
