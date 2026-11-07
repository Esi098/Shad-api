# Built by Esi — https://t.me/Homosapien_001
"""Shad/IranLMS crypto: tmp-session AES envelope + RSA auth handshake.

Verified against the live API:
  * data_enc = AES-CBC(passphrase(tmp_session|auth), IV=0, PKCS7) of
    JSON {method, input, client}, base64.
  * passphrase: n = s[16:24]+s[0:8]+s[24:32]+s[8:16]; digits +5 mod10,
    letters +9 mod26.
  * public_key sent to the server = obfuscated(base64(PEM)).
  * signIn's auth is RSA-OAEP(SHA1) encrypted with our public key.
  * api_version 6 calls add sign = base64(RSA-SHA256(data_enc)).
"""

from __future__ import annotations

import base64
import json
import secrets
from typing import Any, Dict

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


def obfuscate(text: str) -> str:
    """The bundle's Xg(): reversible Caesar-like transform of base64 text."""
    out = []
    for ch in text:
        if ch.isdigit():
            out.append(chr((13 - (ord(ch) - 48)) % 10 + 48))
        elif "A" <= ch <= "Z":
            out.append(chr((29 - (ord(ch) - 65)) % 26 + 65))
        elif "a" <= ch <= "z":
            out.append(chr((32 - (ord(ch) - 97)) % 26 + 97))
        else:
            out.append(ch)
    return "".join(out)


def passphrase(secret: str) -> str:
    """The bundle's createSecretPassphrase(); needs >= 32 chars."""
    a, b, c, d = secret[0:8], secret[8:16], secret[16:24], secret[24:32]
    n = c + a + d + b
    out = []
    for ch in n:
        if ch.isdigit():
            out.append(str((int(ch) + 5) % 10))
        else:
            out.append(chr((ord(ch) - 97 + 9) % 26 + 97))
    return "".join(out)


def _pkcs7(data: bytes) -> bytes:
    pad = 16 - len(data) % 16
    return data + bytes([pad]) * pad


def encrypt(payload: Dict[str, Any], secret: str) -> str:
    raw = json.dumps(payload, separators=(",", ":")).encode()
    key = passphrase(secret).encode()
    enc = Cipher(algorithms.AES(key), modes.CBC(b"\x00" * 16)).encryptor()
    return base64.b64encode(enc.update(_pkcs7(raw)) + enc.finalize()).decode()


def decrypt(blob: str, secret: str) -> str:
    raw = base64.b64decode(blob)
    key = passphrase(secret).encode()
    dec = Cipher(algorithms.AES(key), modes.CBC(b"\x00" * 16)).decryptor()
    out = dec.update(raw) + dec.finalize()
    return out[:-out[-1]].decode()


def new_tmp_session() -> str:
    return "".join(secrets.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(32))


def generate_keypair() -> Dict[str, str]:
    key = rsa.generate_private_key(public_exponent=65537, key_size=1024)
    priv = key.private_bytes(serialization.Encoding.PEM,
                             serialization.PrivateFormat.TraditionalOpenSSL,
                             serialization.NoEncryption()).decode()
    pub = key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo).decode()
    return {"private_pem": priv, "public_pem": pub,
            "public_key": obfuscate(base64.b64encode(pub.encode()).decode())}


def private_key(pem: str):
    return serialization.load_pem_private_key(pem.encode(), password=None)


def rsa_decrypt_oaep(pem: str, b64: str) -> str:
    key = private_key(pem)
    raw = base64.b64decode(b64)
    for algo, mgf in ((hashes.SHA1(), padding.MGF1(hashes.SHA1())),
                      (hashes.SHA256(), padding.MGF1(hashes.SHA256()))):
        try:
            return key.decrypt(raw, padding.OAEP(mgf=mgf, algorithm=algo,
                                                label=None)).decode()
        except Exception:
            continue
    return key.decrypt(raw, padding.PKCS1v15()).decode()


def sign_data_enc(pem: str, data_enc: str) -> str:
    key = private_key(pem)
    sig = key.sign(data_enc.encode(), padding.PKCS1v15(), hashes.SHA256())
    return base64.b64encode(sig).decode()
