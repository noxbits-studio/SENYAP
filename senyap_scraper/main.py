"""Entry point SENYAP.

handle() menerima request JSON (string atau dict) dan selalu mengembalikan
respons JSON string berbentuk Data Contract v1. Tidak pernah melempar exception
ke pemanggil.
"""

from __future__ import annotations

import json
import sys
from typing import Any, Dict, Union

from api import EpornerApi
from errors import (
    InternalError,
    InvalidJsonError,
    ScraperError,
)
from models import error_envelope
from validator import validate_request

# Client dipakai ulang antar panggilan; HttpClient tidak menyimpan state.
_API = EpornerApi()


def _load_request(request_json: Union[str, bytes, Dict[str, Any]]) -> Any:
    if isinstance(request_json, dict):
        return request_json
    if isinstance(request_json, (bytes, bytearray)):
        request_json = request_json.decode("utf-8", errors="replace")
    if not isinstance(request_json, str):
        raise InvalidJsonError("Request harus berupa JSON string atau objek.")
    text = request_json.strip()
    if not text:
        raise InvalidJsonError("Request JSON kosong.")
    try:
        return json.loads(text)
    except ValueError as error:
        raise InvalidJsonError(
            "Request bukan JSON yang valid.", details={"reason": str(error)}
        ) from None


def _dispatch(request_json: Union[str, bytes, Dict[str, Any]]) -> Dict[str, Any]:
    raw_request = _load_request(request_json)
    request = validate_request(raw_request)
    return _API.fetch_catalog(request)


def _dump(payload: Dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def handle(request_json: Union[str, bytes, Dict[str, Any]]) -> str:
    """Titik masuk utama. Selalu mengembalikan JSON string."""
    try:
        return _dump(_dispatch(request_json))
    except ScraperError as error:
        return _dump(error_envelope(error))
    except Exception as error:  # jaring pengaman terakhir
        internal = InternalError(f"Kesalahan tak terduga: {error}")
        return _dump(error_envelope(internal))


def _main(argv: list) -> int:
    """Smoke test manual: `python main.py '{"operation":"get_latest"}'`."""
    if len(argv) > 1:
        request_json = argv[1]
    else:
        request_json = sys.stdin.read()
    sys.stdout.write(handle(request_json))
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(_main(sys.argv))