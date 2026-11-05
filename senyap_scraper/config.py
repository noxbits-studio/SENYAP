"""Konstanta konfigurasi SENYAP scraper.

Seluruh nilai yang boleh berubah tanpa menyentuh logika kode ditempatkan di sini.
Tidak ada dependensi eksternal.
"""

from __future__ import annotations

# --- Identitas kontrak -------------------------------------------------------

# Versi Data Contract v1. Jangan diubah tanpa persetujuan.
CONTRACT_VERSION = 1

# Nama sumber yang ditulis ke setiap objek video.
SOURCE_NAME = "eporner"

# --- Endpoint ----------------------------------------------------------------

# Satu-satunya endpoint yang dipakai pada Tahap 1.
# Terverifikasi dari dokumentasi resmi /api/v2/ dan dari respons live 2026-11-05.
API_BASE_URL = "https://www.eporner.com/api/v2/video/search/"

# Halaman situs, dipakai sebagai Referer. Analisis mencatat Referer wajib untuk
# host CDN; untuk API v2 nilainya tidak berbahaya.
SITE_URL = "https://www.eporner.com/"

# User-Agent browser. Analisis mencatat UA bawaan ExoPlayer sering ditolak CDN.
USER_AGENT = (
    "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36 SENYAP/0.1"
)

# --- Jaringan ----------------------------------------------------------------

# Timeout per request (detik). Semua request wajib punya timeout.
DEFAULT_TIMEOUT = 15.0

# Jumlah percobaan ulang untuk error yang ditandai retryable.
MAX_RETRIES = 2

# Jeda dasar backoff (detik), dikalikan 2^attempt.
RETRY_BACKOFF = 0.5

# Batas ukuran body respons (byte) agar tidak menghabiskan memori di perangkat.
MAX_RESPONSE_BYTES = 8 * 1024 * 1024

# --- Batas parameter (mengikuti dokumentasi API) -----------------------------

DEFAULT_PER_PAGE = 30
MIN_PER_PAGE = 1
MAX_PER_PAGE = 1000

MIN_PAGE = 1
MAX_PAGE = 1_000_000

DEFAULT_THUMBSIZE = "medium"
VALID_THUMBSIZES = ("small", "medium", "big")

VALID_ORDERS = (
    "latest",
    "longest",
    "shortest",
    "top-rated",
    "most-popular",
    "top-weekly",
    "top-monthly",
)

# Order bawaan per operasi. get_latest dan get_popular adalah operasi turunan
# dari endpoint search yang sama, hanya berbeda pada order.
DEFAULT_ORDER_BY_OPERATION = {
    "get_latest": "latest",
    "get_popular": "most-popular",
    "search_videos": "latest",
}

VALID_GAY = (0, 1, 2)
VALID_LQ = (0, 1, 2)
DEFAULT_GAY = 0
DEFAULT_LQ = 1

# Nilai khusus dokumentasi API untuk "semua video".
QUERY_ALL = "all"
MAX_QUERY_LENGTH = 200

# --- Operasi -----------------------------------------------------------------

OPERATION_GET_LATEST = "get_latest"
OPERATION_GET_POPULAR = "get_popular"
OPERATION_SEARCH = "search_videos"

ALLOWED_OPERATIONS = (
    OPERATION_GET_LATEST,
    OPERATION_GET_POPULAR,
    OPERATION_SEARCH,
)