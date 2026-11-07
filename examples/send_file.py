# Built by Esi — https://t.me/Homosapien_001
"""Upload a file with live progress, then send it to a chat.

Shad allows up to 100 MiB per file. For bigger or blocked types use
``send_file_zipped`` / ``send_file_split`` (see README).
"""

from __future__ import annotations

import asyncio
import os
import sys

from shad_api import ShadClient

SESSION_FILE = os.environ.get("SHAD_SESSION", "session.json")
TARGET = os.environ.get("SHAD_TARGET", "me")


def progress(done: int, total: int, label: str = "") -> None:
    percent = int(done / total * 100) if total else 0
    sys.stdout.write(f"\r{percent:3d}% {label[:60]:<60}")
    sys.stdout.flush()
    if done >= total:
        sys.stdout.write("\n")


async def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit("usage: python examples/send_file.py <file> [caption]")
    path = sys.argv[1]
    caption = sys.argv[2] if len(sys.argv) > 2 else ""

    client = ShadClient(SESSION_FILE)
    target = TARGET
    if target == "me":
        target = (await client.get_user_info())["user_guid"]

    result = await client.send_file(target, path, caption, progress=progress)
    print("sent:", result.get("message_update") or result)


if __name__ == "__main__":
    asyncio.run(main())
