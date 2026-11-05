"""Model data dan pembungkus respons sesuai Data Contract v1.

Kontrak tidak diubah di sini: nama field, urutan, dan tipe mengikuti dokumen
handoff apa adanya.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import config
from errors import ScraperError


@dataclass(frozen=True)
class Video:
    """Objek video sesuai kontrak."""

    video_id: str
    title: str
    thumbnail_url: str
    source_url: str
    category: Optional[str]
    duration_seconds: Optional[int]
    published_at: Optional[str]
    source_name: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "video_id": self.video_id,
            "title": self.title,
            "thumbnail_url": self.thumbnail_url,
            "source_url": self.source_url,
            "category": self.category,
            "duration_seconds": self.duration_seconds,
            "published_at": self.published_at,
            "source_name": self.source_name,
        }


@dataclass(frozen=True)
class Pagination:
    """Objek pagination sesuai kontrak."""

    page: int
    per_page: int
    has_next: bool
    next_page: Optional[int]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "page": self.page,
            "per_page": self.per_page,
            "has_next": self.has_next,
            "next_page": self.next_page,
        }


def envelope(
    response_type: str,
    *,
    status: str = "success",
    data: Optional[Any] = None,
    pagination: Optional[Pagination] = None,
    error: Optional[ScraperError] = None,
) -> Dict[str, Any]:
    """Bangun pembungkus respons v1.

    Selalu mengembalikan keenam kunci kontrak agar bentuknya konsisten.
    """
    return {
        "contract_version": config.CONTRACT_VERSION,
        "type": response_type,
        "status": status,
        "data": [] if data is None else data,
        "pagination": pagination.to_dict() if pagination is not None else None,
        "error": error.to_dict() if error is not None else None,
    }


def error_envelope(error: ScraperError) -> Dict[str, Any]:
    """Pembungkus untuk respons gagal. Tipe respons selalu "error"."""
    return envelope("error", status="error", data=[], error=error)


def catalog_envelope(
    videos: List[Video], pagination: Optional[Pagination]
) -> Dict[str, Any]:
    """Pembungkus respons katalog yang berhasil."""
    return envelope(
        "catalog",
        status="success",
        data=[video.to_dict() for video in videos],
        pagination=pagination,
    )


__all__ = [
    "Video",
    "Pagination",
    "envelope",
    "error_envelope",
    "catalog_envelope",
    "field",
]