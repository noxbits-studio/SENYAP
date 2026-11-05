"""Utilitas test: respons palsu dan pengganti urlopen.

Tidak ada test yang menyentuh jaringan.
"""

from __future__ import annotations

import email.message
import io
import json
import urllib.error
from typing import Any, Dict, List, Optional


class FakeResponse:
    """Meniru objek respons urlopen secukupnya."""

    def __init__(self, body: Any, status: int = 200, charset: str = "utf-8") -> None:
        if isinstance(body, (dict, list)):
            body = json.dumps(body)
        self._body = body.encode(charset) if isinstance(body, str) else bytes(body)
        self.status = status
        self.headers = email.message.Message()
        self.headers["Content-Type"] = f"application/json; charset={charset}"

    def read(self, amount: Optional[int] = None) -> bytes:
        if amount is None:
            return self._body
        return self._body[:amount]

    def getcode(self) -> int:
        return self.status

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *_exc: Any) -> bool:
        return False


def http_error(url: str, code: int, body: bytes = b"") -> urllib.error.HTTPError:
    """Bangun HTTPError lengkap dengan file-like body."""
    return urllib.error.HTTPError(url, code, f"HTTP {code}", {}, io.BytesIO(body))


class RecordingHttp:
    """Pengganti HttpClient yang merekam panggilan tanpa jaringan."""

    def __init__(self, payload: Any = None, error: Optional[BaseException] = None):
        self.payload = payload
        self.error = error
        self.calls: List[Dict[str, Any]] = []

    def get_json(self, url: str, params: Optional[Dict[str, Any]] = None) -> Any:
        self.calls.append({"url": url, "params": dict(params or {})})
        if self.error is not None:
            raise self.error
        return self.payload