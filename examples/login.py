# Built by Esi — https://t.me/Homosapien_001
"""Interactive phone + SMS login.

Run:
    python examples/login.py

The session file (JSON, mode 0600) keeps the account token and the RSA private
key, so the next run needs no SMS.
"""

from __future__ import annotations

import asyncio
import os

from shad_api import ShadClient

SESSION_FILE = os.environ.get("SHAD_SESSION", "session.json")


async def main() -> None:
    phone = input("Phone number (+989...): ").strip()
    client = ShadClient(SESSION_FILE, phone=phone)

    await client.login_send_code(phone)
    print("SMS code requested.")

    code = input("SMS code: ").strip()
    user = await client.login_verify(code)
    print(f"Logged in as: {user.get('user_guid') or user.get('username') or 'you'}")
    print(f"Session saved to {SESSION_FILE}")


if __name__ == "__main__":
    asyncio.run(main())
