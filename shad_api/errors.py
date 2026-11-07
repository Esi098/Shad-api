# Built by Esi — https://t.me/Homosapien_001
"""Typed errors for the Shad client."""


class ShadError(Exception):
    """Base error."""


class ShadResponseError(ShadError):
    """Server answered ERROR_*; .code carries status_det (e.g. CodeIsInvalid)."""

    def __init__(self, status: str, detail: str = ""):
        super().__init__(f"{status}: {detail}" if detail else status)
        self.status = status
        self.detail = detail
        self.code = detail or status


class ShadAuthError(ShadError):
    """Not logged in / session expired."""
