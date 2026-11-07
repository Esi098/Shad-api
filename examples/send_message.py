# Built by Esi — https://t.me/Homosapien_001
"""Send a text message (defaults to Saved Messages = "me")."""

from __future__ import annotations

import asyncio
import os

from shad_api import ShadClient

SESSION_FILE = os.environ.get("SHAD_SESSION", "session.json")
TARGET = os.environ.get("SHAD_TARGET", "me")  # object_guid, or "me"


async def main() -> None:
    client = ShadClient(SESSION_FILE)
    if not client.session.has_auth:
        raise SystemExit("No session: run examples/login.py first.")

    target = TARGET
    if target == "me":
        # "me" is a CLI convention, not an object_guid; resolve the real one.
        target = (await client.get_user_info())["user_guid"]

    result = await client.send_message(target, "Hello from shad_api 👋")
    print("sent:", result.get("message_update") or result)


if __name__ == "__main__":
    asyncio.run(main())
