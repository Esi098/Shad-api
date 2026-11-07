# Built by Esi — https://t.me/Homosapien_001
# Changelog

All notable changes to `shad-api` are documented here.
The format is based on [Keep a Changelog](https://keepachangelog.com/).

## [1.0.0] — 2026-11-08

### Added
- Async `ShadClient` for the IranLMS API: login (SMS + RSA handshake), profile,
  chats/contacts with pagination, messages, chunked file upload/download,
  zip/split helpers, 2FA management, recovery email and device/session
  management.
- Atomic JSON session storage with `0600` permissions.
- Crypto module (AES-CBC envelope, obfuscation, RSA-OAEP/SHA-1) extracted from
  the official web bundle and verified live.
- Typed public API (`py.typed`), examples, reverse-engineering notes and an
  offline test suite (14 tests).
- GitHub Actions CI (Python 3.10–3.13).
