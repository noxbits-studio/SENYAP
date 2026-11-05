"""Validasi dan normalisasi request masuk.

Validator tidak menyentuh jaringan. Semua ketidaksesuaian diubah menjadi
InvalidRequestError / InvalidParameterError agar main.py cukup menangkap satu
jenis exception.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

import config
from errors import InvalidParameterError, InvalidRequestError, UnknownOperationError


@dataclass(frozen=True)
class ValidatedRequest:
    """Request yang sudah divalidasi dan diberi nilai bawaan."""

    operation: str
    query: str
    page: int
    per_page: int
    thumbsize: str
    order: str
    gay: int
    lq: int


def _require_dict(request: Any) -> Dict[str, Any]:
    if not isinstance(request, dict):
        raise InvalidRequestError(
            "Request harus berupa objek JSON.", code="invalid_request"
        )
    return request


def _as_int(raw: Any, name: str) -> int:
    """Konversi ke int tanpa menerima bool dan tanpa menerima string desimal."""
    if isinstance(raw, bool):
        raise InvalidParameterError(f"Parameter '{name}' harus berupa bilangan bulat.")
    if isinstance(raw, int):
        return raw
    if isinstance(raw, str):
        text = raw.strip()
        if not text:
            raise InvalidParameterError(f"Parameter '{name}' tidak boleh kosong.")
        try:
            return int(text, 10)
        except ValueError:
            raise InvalidParameterError(
                f"Parameter '{name}' harus berupa bilangan bulat."
            ) from None
    raise InvalidParameterError(f"Parameter '{name}' harus berupa bilangan bulat.")


def _bounded_int(raw: Any, name: str, minimum: int, maximum: int) -> int:
    value = _as_int(raw, name)
    if value < minimum or value > maximum:
        raise InvalidParameterError(
            f"Parameter '{name}' harus di antara {minimum} dan {maximum}."
        )
    return value


def _enum_str(raw: Any, name: str, allowed: tuple) -> str:
    if not isinstance(raw, str):
        raise InvalidParameterError(f"Parameter '{name}' harus berupa teks.")
    value = raw.strip().lower()
    if value not in allowed:
        raise InvalidParameterError(
            f"Parameter '{name}' tidak dikenal. Nilai yang diterima: "
            + ", ".join(allowed)
            + "."
        )
    return value


def _optional_str(request: Dict[str, Any], name: str) -> Optional[str]:
    raw = request.get(name)
    if raw is None:
        return None
    if not isinstance(raw, str):
        raise InvalidParameterError(f"Parameter '{name}' harus berupa teks.")
    return raw.strip()


def validate_request(request: Any) -> ValidatedRequest:
    """Validasi penuh satu request dan kembalikan bentuk ternormalisasi."""
    payload = _require_dict(request)

    operation = payload.get("operation")
    if operation is None:
        raise InvalidRequestError("Parameter 'operation' wajib diisi.")
    if not isinstance(operation, str):
        raise InvalidRequestError("Parameter 'operation' harus berupa teks.")
    operation = operation.strip().lower()
    if operation not in config.ALLOWED_OPERATIONS:
        raise UnknownOperationError(
            "Operasi tidak dikenal. Operasi yang didukung: "
            + ", ".join(config.ALLOWED_OPERATIONS)
            + "."
        )

    query = _optional_str(payload, "query") or config.QUERY_ALL
    if len(query) > config.MAX_QUERY_LENGTH:
        raise InvalidParameterError(
            f"Parameter 'query' melebihi {config.MAX_QUERY_LENGTH} karakter."
        )
    if operation == config.OPERATION_SEARCH and query == config.QUERY_ALL:
        # search_videos tanpa query berarti seluruh katalog; tetap diizinkan,
        # tetapi hanya jika memang tidak dikirim, bukan dikirim kosong.
        if not (payload.get("query") or "").strip():
            raise InvalidParameterError(
                "Operasi 'search_videos' memerlukan parameter 'query'."
            )

    page_raw = payload.get("page")
    page = (
        config.MIN_PAGE
        if page_raw is None
        else _bounded_int(page_raw, "page", config.MIN_PAGE, config.MAX_PAGE)
    )

    per_page_raw = payload.get("per_page")
    per_page = (
        config.DEFAULT_PER_PAGE
        if per_page_raw is None
        else _bounded_int(
            per_page_raw, "per_page", config.MIN_PER_PAGE, config.MAX_PER_PAGE
        )
    )

    thumbsize_raw = payload.get("thumbsize")
    thumbsize = (
        config.DEFAULT_THUMBSIZE
        if thumbsize_raw is None
        else _enum_str(thumbsize_raw, "thumbsize", config.VALID_THUMBSIZES)
    )

    order_raw = payload.get("order")
    order = (
        config.DEFAULT_ORDER_BY_OPERATION[operation]
        if order_raw is None
        else _enum_str(order_raw, "order", config.VALID_ORDERS)
    )

    gay_raw = payload.get("gay")
    gay = (
        config.DEFAULT_GAY
        if gay_raw is None
        else _bounded_int(gay_raw, "gay", 0, 2)
    )
    if gay not in config.VALID_GAY:
        raise InvalidParameterError("Parameter 'gay' hanya menerima 0, 1, atau 2.")

    lq_raw = payload.get("lq")
    lq = (
        config.DEFAULT_LQ
        if lq_raw is None
        else _bounded_int(lq_raw, "lq", 0, 2)
    )
    if lq not in config.VALID_LQ:
        raise InvalidParameterError("Parameter 'lq' hanya menerima 0, 1, atau 2.")

    return ValidatedRequest(
        operation=operation,
        query=query,
        page=page,
        per_page=per_page,
        thumbsize=thumbsize,
        order=order,
        gay=gay,
        lq=lq,
    )