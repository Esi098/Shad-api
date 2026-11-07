# Built by Esi — https://t.me/Homosapien_001
"""Offline tests for the parts of ShadClient that never touch the network."""

import pytest

from shad_api import MAX_FILE_SIZE, ShadClient, ShadError


def test_max_file_size_matches_shad_limit():
    assert MAX_FILE_SIZE == 100 * 1024 * 1024


def test_blocked_extensions_are_rejected():
    for name in ("app.apk", "lib.bin", "bundle.gz", "arch.7z", "x.exe"):
        with pytest.raises(ShadError):
            ShadClient.check_extension(name)
    for name in ("notes.txt", "photo.jpg", "archive.zip"):
        ShadClient.check_extension(name)  # must not raise


def test_guess_mime_defaults_to_octet_stream():
    assert ShadClient.guess_mime("a.pdf") == "application/pdf"
    assert ShadClient.guess_mime("a.unknown") == "application/octet-stream"


def test_chat_helpers():
    chat = {"object_guid": "g1",
            "abs_object": {"type": "Group", "title": "My group"}}
    assert ShadClient.chat_title(chat) == "My group"
    assert ShadClient.chat_title({"object_guid": "g2", "abs_object": {}}) == "g2"

    overview = ShadClient(":memory:").chats_overview({"chats": [chat]})
    assert overview[0]["guid"] == "g1"
    assert overview[0]["type"] == "Group"


def test_client_constructs_without_network(tmp_path):
    client = ShadClient(str(tmp_path / "session.json"), phone="+989120000000")
    assert client.session.phone == "+989120000000"
    assert client.session.has_auth is False
