"""Test normalisasi respons API ke Data Contract v1."""

from __future__ import annotations

import unittest

import config
from api import EpornerApi
from errors import InvalidResponseError
from tests.helpers import RecordingHttp
from validator import ValidatedRequest


def _request(**overrides) -> ValidatedRequest:
    base = {
        "operation": "get_latest",
        "query": "all",
        "page": 1,
        "per_page": 30,
        "thumbsize": "medium",
        "order": "latest",
        "gay": 0,
        "lq": 1,
    }
    base.update(overrides)
    return ValidatedRequest(**base)


def _payload(videos=None, total_pages=10) -> dict:
    return {
        "count": len(videos or []),
        "start": 0,
        "per_page": 30,
        "page": 1,
        "total_count": 4523524,
        "total_pages": total_pages,
        "videos": videos or [],
    }


def _raw_video(**overrides) -> dict:
    base = {
        "id": "2EggIBhbQWQ",
        "title": "Big Boobs",
        "keywords": "amateur, brunette",
        "views": 107,
        "rate": "5.00",
        "url": "https://www.eporner.com/video-2EggIBhbQWQ/big-boobs/",
        "added": "2026-11-02 16:20:54",
        "length_sec": 1873,
        "length_min": "31:13",
        "embed": "https://www.eporner.com/embed/2EggIBhbQWQ/",
        "default_thumb": {
            "size": "medium",
            "width": 427,
            "height": 240,
            "src": "https://static-ca-cdn.eporner.com/thumbs/x/9_240.jpg",
        },
        "thumbs": [],
    }
    base.update(overrides)
    return base


class MappingTests(unittest.TestCase):
    def test_video_fields_mapped(self) -> None:
        http = RecordingHttp(_payload([_raw_video()]))
        result = EpornerApi(http=http).fetch_catalog(_request())

        self.assertEqual(result["contract_version"], config.CONTRACT_VERSION)
        self.assertEqual(result["type"], "catalog")
        self.assertEqual(result["status"], "success")
        self.assertIsNone(result["error"])

        video = result["data"][0]
        self.assertEqual(video["video_id"], "2EggIBhbQWQ")
        self.assertEqual(video["title"], "Big Boobs")
        self.assertEqual(video["thumbnail_url"], _raw_video()["default_thumb"]["src"])
        self.assertEqual(video["source_url"], _raw_video()["url"])
        self.assertIsNone(video["category"])
        self.assertEqual(video["duration_seconds"], 1873)
        self.assertEqual(video["published_at"], "2026-11-02T16:20:54")
        self.assertEqual(video["source_name"], "eporner")

    def test_keys_are_exactly_contract_fields(self) -> None:
        http = RecordingHttp(_payload([_raw_video()]))
        video = EpornerApi(http=http).fetch_catalog(_request())["data"][0]
        self.assertEqual(
            list(video.keys()),
            [
                "video_id",
                "title",
                "thumbnail_url",
                "source_url",
                "category",
                "duration_seconds",
                "published_at",
                "source_name",
            ],
        )

    def test_published_at_already_iso_kept(self) -> None:
        http = RecordingHttp(_payload([_raw_video(added="2026-11-02T16:20:54")]))
        video = EpornerApi(http=http).fetch_catalog(_request())["data"][0]
        self.assertEqual(video["published_at"], "2026-11-02T16:20:54")

    def test_missing_published_at_becomes_none(self) -> None:
        http = RecordingHttp(_payload([_raw_video(added=None)]))
        video = EpornerApi(http=http).fetch_catalog(_request())["data"][0]
        self.assertIsNone(video["published_at"])

    def test_missing_duration_becomes_none(self) -> None:
        http = RecordingHttp(_payload([_raw_video(length_sec="abc")]))
        video = EpornerApi(http=http).fetch_catalog(_request())["data"][0]
        self.assertIsNone(video["duration_seconds"])

    def test_missing_thumb_becomes_empty_string(self) -> None:
        raw = _raw_video()
        raw.pop("default_thumb")
        http = RecordingHttp(_payload([raw]))
        video = EpornerApi(http=http).fetch_catalog(_request())["data"][0]
        self.assertEqual(video["thumbnail_url"], "")

    def test_entry_without_id_is_skipped(self) -> None:
        http = RecordingHttp(_payload([{"title": "tanpa id"}, _raw_video()]))
        result = EpornerApi(http=http).fetch_catalog(_request())
        self.assertEqual(len(result["data"]), 1)
        self.assertEqual(result["data"][0]["video_id"], "2EggIBhbQWQ")


class PaginationTests(unittest.TestCase):
    def test_has_next_when_page_below_total(self) -> None:
        http = RecordingHttp(_payload([_raw_video()], total_pages=10))
        pagination = EpornerApi(http=http).fetch_catalog(_request(page=1))["pagination"]
        self.assertTrue(pagination["has_next"])
        self.assertEqual(pagination["next_page"], 2)

    def test_last_page_has_no_next(self) -> None:
        http = RecordingHttp(_payload([_raw_video()], total_pages=10))
        pagination = EpornerApi(http=http).fetch_catalog(_request(page=10))["pagination"]
        self.assertFalse(pagination["has_next"])
        self.assertIsNone(pagination["next_page"])

    def test_page_reported_from_request(self) -> None:
        http = RecordingHttp(_payload([_raw_video()], total_pages=10))
        pagination = EpornerApi(http=http).fetch_catalog(
            _request(page=4, per_page=50)
        )["pagination"]
        self.assertEqual(pagination["page"], 4)
        self.assertEqual(pagination["per_page"], 50)

    def test_missing_total_pages_falls_back_to_full_page(self) -> None:
        payload = _payload([_raw_video()])
        payload.pop("total_pages")
        http = RecordingHttp(payload)
        pagination = EpornerApi(http=http).fetch_catalog(
            _request(per_page=1)
        )["pagination"]
        self.assertTrue(pagination["has_next"])

    def test_empty_page_is_success_without_next(self) -> None:
        http = RecordingHttp(_payload([], total_pages=10))
        result = EpornerApi(http=http).fetch_catalog(_request(page=5))
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["data"], [])
        self.assertFalse(result["pagination"]["has_next"])


class RequestBuildingTests(unittest.TestCase):
    def test_params_match_request(self) -> None:
        http = RecordingHttp(_payload([_raw_video()]))
        EpornerApi(http=http).fetch_catalog(
            _request(
                operation="search_videos",
                query="milf",
                page=2,
                per_page=25,
                thumbsize="small",
                order="top-weekly",
                gay=1,
                lq=2,
            )
        )
        params = http.calls[0]["params"]
        self.assertEqual(http.calls[0]["url"], config.API_BASE_URL)
        self.assertEqual(params["query"], "milf")
        self.assertEqual(params["page"], 2)
        self.assertEqual(params["per_page"], 25)
        self.assertEqual(params["thumbsize"], "small")
        self.assertEqual(params["order"], "top-weekly")
        self.assertEqual(params["gay"], 1)
        self.assertEqual(params["lq"], 2)
        self.assertEqual(params["format"], "json")


class InvalidPayloadTests(unittest.TestCase):
    def test_payload_not_dict(self) -> None:
        with self.assertRaises(InvalidResponseError):
            EpornerApi(http=RecordingHttp([])).fetch_catalog(_request())

    def test_videos_missing(self) -> None:
        with self.assertRaises(InvalidResponseError):
            EpornerApi(http=RecordingHttp({"count": 0})).fetch_catalog(_request())

    def test_videos_not_list(self) -> None:
        with self.assertRaises(InvalidResponseError):
            EpornerApi(http=RecordingHttp({"videos": {}})).fetch_catalog(_request())

    def test_all_entries_unmappable(self) -> None:
        with self.assertRaises(InvalidResponseError):
            EpornerApi(http=RecordingHttp(_payload([{"title": "x"}]))).fetch_catalog(
                _request()
            )


if __name__ == "__main__":
    unittest.main()