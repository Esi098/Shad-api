# Built by Esi — https://t.me/Homosapien_001
"""Offline tests for ShadSession persistence and permissions."""

import json
import os

from shad_api import ShadSession


def test_save_load_and_permissions(tmp_path):
    path = tmp_path / "session.json"
    session = ShadSession(str(path))
    session.set_many(auth="token", phone="+989120000000", device_hash="dev")
    session.save()

    assert path.exists()
    if os.name == "posix":
        assert (path.stat().st_mode & 0o777) == 0o600

    again = ShadSession(str(path))
    assert again.auth == "token"
    assert again.phone == "+989120000000"
    assert again.has_auth is True
    assert again.masked.endswith("00")


def test_unknown_keys_and_corrupt_file(tmp_path):
    session = ShadSession(str(tmp_path / "missing.json"))
    assert session.auth == ""
    assert session["does-not-exist"] is None

    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    assert ShadSession(str(bad)).data == {}


def test_pending_login_state_roundtrip(tmp_path):
    path = tmp_path / "session.json"
    session = ShadSession(str(path))
    session.set_many(phone="+98912", pending={"tmp": "t", "phone_code_hash": "h"})
    session.save()
    loaded = ShadSession(str(path))
    assert loaded["pending"]["tmp"] == "t"
    assert json.loads(path.read_text(encoding="utf-8"))["phone"] == "+98912"
