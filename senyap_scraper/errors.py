"""Hirarki error SENYAP.

Setiap error membawa kode stabil, pesan, dan flag retryable sehingga lapisan
atas dapat memutuskan apakah layak mencoba ulang tanpa membaca teks pesan.
"""

from __future__ import annotations

from typing import Any, Dict, Optional


class ScraperError(Exception):
    """Basis semua error scraper."""

    code = "internal_error"
    retryable = False

    def __init__(
        self,
        message: str,
        *,
        code: Optional[str] = None,
        retryable: Optional[bool] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        if code is not None:
            self.code = code
        if retryable is not None:
            self.retryable = retryable
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        """Bentuk error sesuai Data Contract v1."""
        return {
            "code": self.code,
            "message": self.message,
            "retryable": bool(self.retryable),
        }

    def __repr__(self) -> str:  # pragma: no cover - bantuan debug
        return f"{type(self).__name__}(code={self.code!r}, message={self.message!r})"


# --- Error request (tidak perlu jaringan) ------------------------------------


class InvalidRequestError(ScraperError):
    code = "invalid_request"


class InvalidJsonError(InvalidRequestError):
    code = "invalid_json"


class UnknownOperationError(InvalidRequestError):
    code = "unknown_operation"


class InvalidParameterError(InvalidRequestError):
    code = "invalid_parameter"


# --- Error transport ---------------------------------------------------------


class HttpError(ScraperError):
    code = "http_error"


class BlockedError(HttpError):
    code = "blocked"


class NotFoundError(HttpError):
    code = "not_found"


class RateLimitedError(HttpError):
    code = "rate_limited"
    retryable = True


class ServerError(HttpError):
    code = "server_error"
    retryable = True


class RequestTimeoutError(ScraperError):
    code = "timeout"
    retryable = True


class NetworkError(ScraperError):
    code = "network_error"
    retryable = True


# --- Error respons -----------------------------------------------------------


class InvalidResponseError(ScraperError):
    code = "invalid_response"


class InternalError(ScraperError):
    code = "internal_error"