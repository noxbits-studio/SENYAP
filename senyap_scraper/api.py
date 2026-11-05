"""Lapisan API: pemanggilan endpoint search dan normalisasi ke Data Contract v1.

Hanya tiga operasi Tahap 1 yang dilayani di sini. Tidak ada parser HTML dan
tidak ada resolver stream.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import config
from client import HttpClient
from errors import InvalidResponseError
from models import Pagination, Video, catalog_envelope
from validator import ValidatedRequest


def _as_int(value: Any) -> Optional[int]:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value.strip(), 10)
        except ValueError:
            return None
    return None


def _as_text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _normalize_published_at(value: Any) -> Optional[str]:
    """Ubah 'YYYY-MM-DD hh:mm:ss' menjadi 'YYYY-MM-DDThh:mm:ss'.

    Nilai yang tidak dikenali diteruskan apa adanya; nilai kosong menjadi None.
    """
    text = _as_text(value)
    if not text:
        return None
    if "T" in text:
        return text
    if len(text) >= 11 and text[10] == " ":
        return f"{text[:10]}T{text[11:]}"
    return text


def _map_video(raw: Any) -> Optional[Video]:
    """Petakan satu entri API ke objek video kontrak.

    Mengembalikan None bila entri tidak punya id yang bisa dipakai.
    """
    if not isinstance(raw, dict):
        return None

    video_id = _as_text(raw.get("id"))
    if not video_id:
        return None

    thumb = raw.get("default_thumb")
    thumbnail_url = ""
    if isinstance(thumb, dict):
        thumbnail_url = _as_text(thumb.get("src"))

    duration = _as_int(raw.get("length_sec"))
    if duration is not None and duration < 0:
        duration = None

    return Video(
        video_id=video_id,
        title=_as_text(raw.get("title")),
        thumbnail_url=thumbnail_url,
        source_url=_as_text(raw.get("url")),
        # API v2 tidak menyediakan kategori; field tetap ada dengan nilai None
        # sampai tahap kategori (HTML) tersedia.
        category=None,
        duration_seconds=duration,
        published_at=_normalize_published_at(raw.get("added")),
        source_name=config.SOURCE_NAME,
    )


class EpornerApi:
    """Klien endpoint search Eporner API v2."""

    def __init__(self, http: Optional[HttpClient] = None) -> None:
        self._http = http if http is not None else HttpClient()

    def fetch_catalog(self, request: ValidatedRequest) -> Dict[str, Any]:
        """Jalankan request dan kembalikan pembungkus respons katalog."""
        payload = self._fetch_payload(request)
        return self._normalize(payload, request)

    # -- internal -------------------------------------------------------------

    def _fetch_payload(self, request: ValidatedRequest) -> Any:
        params: Dict[str, Any] = {
            "query": request.query,
            "per_page": request.per_page,
            "page": request.page,
            "thumbsize": request.thumbsize,
            "order": request.order,
            "gay": request.gay,
            "lq": request.lq,
            "format": "json",
        }
        return self._http.get_json(config.API_BASE_URL, params)

    def _normalize(
        self, payload: Any, request: ValidatedRequest
    ) -> Dict[str, Any]:
        if not isinstance(payload, dict):
            raise InvalidResponseError("Respons API bukan objek JSON.")

        raw_videos = payload.get("videos")
        if not isinstance(raw_videos, list):
            raise InvalidResponseError("Respons API tidak memuat daftar 'videos'.")

        videos: List[Video] = []
        for raw in raw_videos:
            video = _map_video(raw)
            if video is not None:
                videos.append(video)

        if raw_videos and not videos:
            raise InvalidResponseError(
                "Tidak ada satu pun entri video yang bisa dipetakan."
            )

        pagination = self._build_pagination(payload, request, len(videos))
        return catalog_envelope(videos, pagination)

    @staticmethod
    def _build_pagination(
        payload: Dict[str, Any], request: ValidatedRequest, mapped_count: int
    ) -> Pagination:
        total_pages = _as_int(payload.get("total_pages"))
        if total_pages is not None and total_pages >= 0:
            has_next = request.page < total_pages and mapped_count > 0
        else:
            # Fallback bila sumber tidak mengirim total_pages: halaman dianggap
            # masih berlanjut hanya jika terisi penuh.
            has_next = mapped_count > 0 and mapped_count >= request.per_page

        return Pagination(
            page=request.page,
            per_page=request.per_page,
            has_next=has_next,
            next_page=request.page + 1 if has_next else None,
        )
