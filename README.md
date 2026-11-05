# SENYAP Scraper — Tahap 1

Scraper Python untuk Eporner. Tahap 1 hanya mencakup **Python Core + API Client**
dengan tiga operasi: `get_latest`, `get_popular`, `search_videos`.

Belum termasuk: katalog kategori, detail video, resolver stream. Itu tahap berikutnya.

## Status

Kode ditulis, **belum pernah dieksekusi**. Runtime Python tidak tersedia di sisi
penulis, jadi hasil test di bawah belum dikonfirmasi lulus. Jalankan sendiri:

cd senyap_scraper python -m unittest discover -s tests -t .

Smoke test manual (butuh jaringan):

cd senyap_scraper python main.py '{"operation":"get_latest","per_page":2}'

## Bukti verifikasi endpoint

Semua diverifikasi langsung pada 2026-11-05, bukan dari ingatan:

- Dokumentasi resmi: https://www.eporner.com/api/v2/
- Endpoint: `GET https://www.eporner.com/api/v2/video/search/`
- `query=all` → 200, `total_count` 4523524
- `order=most-popular`, `order=top-weekly` → 200
- `page=2` → 200 dengan `start=2`
- `thumbsize=small`, `thumbsize=medium` → 200
- `order=bogus` → 200, diam-diam jatuh ke `latest` (karena itu order divalidasi lokal)
- Bentuk respons terkonfirmasi: `count`, `start`, `per_page`, `page`, `total_count`,
  `total_pages`, `videos[]` berisi `id`, `title`, `keywords`, `views`, `rate`,
  `url`, `added`, `length_sec`, `length_min`, `embed`, `default_thumb.src`, `thumbs[]`

Tidak ada endpoint terpisah untuk "latest" atau "popular". Keduanya operasi turunan
dari endpoint yang sama dan hanya berbeda pada `order`.

Catatan: `Analisis_2.md` hanya membahas resolver stream, tidak memuat detail API v2.

## Batas parameter (dari dokumentasi)

| Parameter | Nilai | Bawaan |
| --- | --- | --- |
| `query` | teks, `all` untuk semua | `all` |
| `per_page` | 1–1000 | 30 |
| `page` | 1–1.000.000 | 1 |
| `thumbsize` | small, medium, big | medium |
| `order` | latest, longest, shortest, top-rated, most-popular, top-weekly, top-monthly | per operasi |
| `gay` | 0, 1, 2 | 0 |
| `lq` | 0, 1, 2 | 1 |

Order bawaan: `get_latest` → `latest`, `get_popular` → `most-popular`,
`search_videos` → `latest`.

## Struktur

senyap_scraper/ main.py         handle() + CLI smoke test api.py          pemanggilan endpoint dan normalisasi ke kontrak client.py       HTTP client stdlib, timeout, retry, batas ukuran validator.py    validasi request, tanpa jaringan models.py       Video, Pagination, pembungkus respons errors.py       hirarki error berkode config.py       konstanta tests/          test tanpa jaringan samples/          contoh request dan respons

## Pemakaian

```python
from main import handle

respons = handle('{"operation":"get_popular","order":"top-weekly","per_page":20}')

handle() menerima JSON string atau dict dan selalu mengembalikan JSON string. Tidak pernah melempar exception.
Catatan kontrak
Pembungkus selalu memuat keenam kunci: contract_version, type, status, data, pagination, error.
type hanya catalog atau error.
duration_seconds dari length_sec, boleh null.
published_at dinormalisasi dari YYYY-MM-DD hh:mm:ss ke YYYY-MM-DDThh:mm:ss tanpa zona waktu, karena sumber tidak menyediakannya.
category selalu null di tahap ini. API v2 tidak menyediakan kategori.
has_next dihitung dari total_pages, bukan total_count, sebab total_count di-cap di 100.000 oleh sumber.
Respons kosong tetap status: success dengan data: []. Tidak ada penimpaan katalog di lapisan ini.

Yang belum diketahui
Perilaku page di atas total_pages (belum diuji).
Apakah per_page besar (mendekati 1000) memicu pembatasan.
Pembatasan per-IP pada endpoint API.
Isi category yang benar sampai tahap kategori tersedia.

Asumsi yang perlu dikonfirmasi
category dibiarkan null sampai ada sumber kategori, alih-alih diturunkan dari keywords.
get_popular memakai most-popular, dengan top-weekly dan top-monthly tersedia lewat parameter order.
Retry otomatis hanya untuk timeout, jaringan, 429, dan 5xx, maksimal dua kali.
