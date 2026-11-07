# Built by Esi — https://t.me/Homosapien_001
"""List dialogs with paging (getChats / contacts)."""

from __future__ import annotations

import asyncio
import os

from shad_api import ShadClient

SESSION_FILE = os.environ.get("SHAD_SESSION", "session.json")


async def main() -> None:
    client = ShadClient(SESSION_FILE)
    chats = await client.get_all_chats(limit=200)
    contacts = await client.get_all_contacts(limit=200)

    print(f"Chats: {len(chats)}  |  Contacts: {len(contacts)}\n")
    for chat in chats[:50]:
        obj = chat.get("abs_object") or {}
        print(f"[{obj.get('type', '?'):<7}] {client.chat_title(chat)}")


if __name__ == "__main__":
    asyncio.run(main())
