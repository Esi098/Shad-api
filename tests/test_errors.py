# Built by Esi — https://t.me/Homosapien_001
"""Error hierarchy contract."""

from shad_api import ShadAuthError, ShadError, ShadResponseError


def test_error_hierarchy():
    assert issubclass(ShadAuthError, ShadError)
    assert issubclass(ShadResponseError, ShadError)
    err = ShadResponseError("INVALID_INPUT", "bad")
    assert err.status == "INVALID_INPUT"
    assert err.detail == "bad"
