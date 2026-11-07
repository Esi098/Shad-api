# Built by Esi — https://t.me/Homosapien_001
# Security policy

## Session files are credentials

A Shad session file (`session.json`) contains:

* the account auth token, and
* the RSA private key used for the IranLMS handshake.

Treat it like a password. Store it with mode `0600`, keep it out of Git
(`.gitignore` covers `session*.json`), and never paste it into issues or chats.
If a session file leaks, terminate that device/session from the official Shad
app (or use `await client.terminate_other_sessions()` after logging in again).

## Reporting a vulnerability

Please do **not** open a public issue for security problems.
Contact the maintainer on Telegram: [@Homosapien_001](https://t.me/Homosapien_001)
with a short description and reproduction steps.

## Scope

This project is an unofficial client. Vulnerabilities in the Shad servers
themselves are out of scope here — report those to Shad/IranLMS.
