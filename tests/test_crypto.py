# Built by Esi — https://t.me/Homosapien_001
"""Offline tests for the IranLMS crypto helpers."""

import json

from shad_api import crypto


def test_obfuscate_is_involutive():
    samples = ["abcXYZ019+/=", "SGVsbG8gV29ybGQ=", "a1B2c3", ""]
    for sample in samples:
        assert crypto.obfuscate(crypto.obfuscate(sample)) == sample


def test_encrypt_decrypt_roundtrip():
    payload = {"method": "getChats", "input": {"start_id": ""},
               "client": {"app_name": "Main"}}
    # passphrase() needs at least 32 characters to produce an AES-256 key
    for secret in ("a" * 32, "0123456789abcdef0123456789abcdef"):
        blob = crypto.encrypt(payload, secret)
        assert isinstance(blob, str) and blob
        assert json.loads(crypto.decrypt(blob, secret)) == payload


def test_passphrase_maps_digits_and_letters():
    phrase = crypto.passphrase("aaaa1111" * 4)
    assert len(phrase) == len("aaaa1111" * 4)
    assert all(ch.isalnum() for ch in phrase)


def test_keypair_and_session_helpers():
    keys = crypto.generate_keypair()
    assert "BEGIN PUBLIC KEY" in keys["public_pem"]
    assert "PRIVATE KEY" in keys["private_pem"]
    # public_key is the obfuscated base64(PEM) sent to the server
    assert keys["public_key"] and "BEGIN" not in keys["public_key"]
    assert len(crypto.new_tmp_session()) == 32
