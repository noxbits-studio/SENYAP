"""HTTP client minimal berbasis stdlib.

Sengaja tanpa dependensi eksternal agar aman di Chaquopy. Seluruh request
memakai timeout, batas ukuran body, dan retry terbatas untuk error sementara.
"""

from __future__ import annotations

import json
import socket
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Callable, Dict, Optional

import config
from errors import (
    BlockedError,
    HttpError,
    InvalidResponseError,
    NetworkError,
    NotFoundError,
    RateLimitedError,
    RequestTimeoutError,
    ServerError,
    ScraperError,
)


def build_url(base_url: str, params: Optional[Dict[str, Any]] = None) -> str:
    """Susun URL lengkap dengan query string yang sudah di-encode."""
    if not params:
        return base_url
    pairs = [(key, str(value)) for key, value in params.items() if value is not None]
    query = urllib.parse.urlencode(pairs, doseq=True)
    separator = "&" if "?" in base_url else "?"
    return f"{base_url}{separator}{query}"


def _map_http_error(error: urllib.error.HTTPError) -> ScraperError:
    """Terjemahkan status HTTP menjadi error domain."""
    status = error.code
    if status in (401, 403):
        return BlockedError(
            f"Akses ditolak oleh sumber (HTTP {status}).",
            details={"status": status},
        )
    if status == 404:
        return NotFoundError("Sumber membalas 404.", details={"status": status})
    if status == 429:
        return RateLimitedError(
            "Terlalu banyak request (HTTP 429).", details={"status": status}
        )
    if 500 <= status <= 599:
        return ServerError(
            f"Sumber mengalami gangguan (HTTP {status}).", details={"status": status}
        )
    return HttpError(
        f"Sumber membalas HTTP {status}.", details={"status": status}
    )


class HttpClient:
    """Client GET JSON dengan timeout, batas ukuran, dan retry terbatas."""

    def __init__(
        self,
        timeout: float = config.DEFAULT_TIMEOUT,
        max_retries: int = config.MAX_RETRIES,
        retry_backoff: float = config.RETRY_BACKOFF,
        user_agent: str = config.USER_AGENT,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff
        self.user_agent = user_agent
        self._sleep = sleep

    # -- publik ---------------------------------------------------------------

    def get_json(
        self, url: str, params: Optional[Dict[str, Any]] = None
    ) -> Any:
        """GET url dan kembalikan body JSON yang sudah di-parse."""
        full_url = build_url(url, params)
        attempt = 0
        while True:
            try:
                return self._fetch_once(full_url)
            except ScraperError as error:
                if not error.retryable or attempt >= self.max_retries:
                    raise
                self._sleep(self.retry_backoff * (2**attempt))
                attempt += 1

    # -- internal -------------------------------------------------------------

    def _fetch_once(self, url: str) -> Any:
        request = urllib.request.Request(
            url,
            method="GET",
            headers={
                "User-Agent": self.user_agent,
                "Accept": "application/json",
                "Referer": config.SITE_URL,
            },
        )

        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                raw = response.read(config.MAX_RESPONSE_BYTES + 1)
                charset = response.headers.get_content_charset() or "utf-8"
        except urllib.error.HTTPError as error:
            raise _map_http_error(error) from None
        except (socket.timeout, TimeoutError):
            raise RequestTimeoutError(
                f"Request melewati batas waktu {self.timeout:g} detik."
            ) from None
        except urllib.error.URLError as error:
            reason = error.reason
            if isinstance(reason, (socket.timeout, TimeoutError)):
                raise RequestTimeoutError(
                    f"Request melewati batas waktu {self.timeout:g} detik."
                ) from None
            raise NetworkError(f"Gagal menghubungi sumber: {reason}") from None
        except OSError as error:
            raise NetworkError(f"Gagal membaca respons: {error}") from None

        if len(raw) > config.MAX_RESPONSE_BYTES:
            raise InvalidResponseError("Respons melebihi batas ukuran yang diizinkan.")

        try:
            text = raw.decode(charset, errors="replace")
        except LookupError:
            text = raw.decode("utf-8", errors="replace")

        return parse_json(text)


def parse_json(text: str) -> Any:
    """Parse teks JSON dan pastikan bentuknya objek atau array."""
    try:
        payload = json.loads(text)
    except ValueError as error:
        raise InvalidResponseError(
            "Respons bukan JSON yang valid.", details={"reason": str(error)}
        ) from None
    if not isinstance(payload, (dict, list)):
        raise InvalidResponseError("JSON respons bukan objek atau array.")
    return payload