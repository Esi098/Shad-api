# Built by Esi — https://t.me/Homosapien_001
"""Transport URL handling (no sockets involved)."""

from shad_api.http import ShadTransport


def test_api_url_rotation_wraps():
    transport = ShadTransport(api_urls=["https://a", "https://b"])
    assert transport.api_url == "https://a"
    assert transport.rotate() == "https://b"
    assert transport.rotate() == "https://a"
