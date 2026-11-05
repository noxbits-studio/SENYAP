"""Test HTTP client dengan urlopen palsu."""

from __future__ import annotations

import unittest
import urllib.error
from unittest import mock

import client
import config
from errors import (
    BlockedError,
    InvalidResponseError,
    NetworkError,
    NotFoundError,
    RateLimitedError,
    RequestTimeoutError,
    ServerError,
)
from tests.helpers import FakeResponse, http_error


def _client(**kwargs):
    kwargs.setdefault("sleep", lambda _seconds: None)
    return client.HttpClient(**kwargs)


class BuildUrlTests(unittest.TestCase):
    def test_params_are_encoded(self) -> None:
        url = client.build_url("https://x.test/p", {"a": 1, "b": "c d"})
        self.assertEqual(url, "https://x.test/p?a=1&b=c+d")

    def test_none_params_skipped(self) -> None:
        url = client.build_url("https://x.test/p", {"a": None, "b": 2})
        self.assertEqual(url, "https://x.test/p?b=2")

    def test_no_params(self) -> None:
        self.assertEqual(client.build_url("https://x.test/p"), "https://x.test/p")


class GetJsonTests(unittest.TestCase):
    def test_success_parses_json(self) -> None:
        with mock.patch.object(
            client.urllib.request, "urlopen", return_value=FakeResponse({"a": 1})
        ):
            self.assertEqual(_client().get_json("https://x.test"), {"a": 1})

    def test_request_headers_sent(self) -> None:
        captured = {}

        def fake_urlopen(request, timeout=None):
            captured["headers"] = dict(request.headers)
            captured["timeout"] = timeout
            return FakeResponse({"ok": True})

        with mock.patch.object(client.urllib.request, "urlopen", fake_urlopen):
            _client(timeout=3.0).get_json("https://x.test")

        lowered = {key.lower(): value for key, value in captured["headers"].items()}
        self.assertIn("user-agent", lowered)
        self.assertEqual(lowered.get("accept"), "application/json")
        self.assertEqual(lowered.get("referer"), config.SITE_URL)
        self.assertEqual(captured["timeout"], 3.0)

    def test_server_error_is_retried_then_succeeds(self) -> None:
        calls = {"n": 0}

        def fake_urlopen(request, timeout=None):
            calls["n"] += 1
            if calls["n"] == 1:
                raise http_error(request.full_url, 500)
            return FakeResponse({"ok": True})

        with mock.patch.object(client.urllib.request, "urlopen", fake_urlopen):
            self.assertEqual(_client().get_json("https://x.test"), {"ok": True})
        self.assertEqual(calls["n"], 2)

    def test_server_error_exhausts_retries(self) -> None:
        def fake_urlopen(request, timeout=None):
            raise http_error(request.full_url, 503)

        with mock.patch.object(client.urllib.request, "urlopen", fake_urlopen):
            with self.assertRaises(ServerError):
                _client(max_retries=2).get_json("https://x.test")

    def test_not_found_is_not_retried(self) -> None:
        calls = {"n": 0}

        def fake_urlopen(request, timeout=None):
            calls["n"] += 1
            raise http_error(request.full_url, 404)

        with mock.patch.object(client.urllib.request, "urlopen", fake_urlopen):
            with self.assertRaises(NotFoundError):
                _client().get_json("https://x.test")
        self.assertEqual(calls["n"], 1)

    def test_forbidden_maps_to_blocked(self) -> None:
        def fake_urlopen(request, timeout=None):
            raise http_error(request.full_url, 403)

        with mock.patch.object(client.urllib.request, "urlopen", fake_urlopen):
            with self.assertRaises(BlockedError):
                _client().get_json("https://x.test")

    def test_rate_limited_is_retryable(self) -> None:
        def fake_urlopen(request, timeout=None):
            raise http_error(request.full_url, 429)

        with mock.patch.object(client.urllib.request, "urlopen", fake_urlopen):
            with self.assertRaises(RateLimitedError) as ctx:
                _client(max_retries=1).get_json("https://x.test")
        self.assertTrue(ctx.exception.retryable)

    def test_timeout_maps_to_timeout_error(self) -> None:
        def fake_urlopen(request, timeout=None):
            raise TimeoutError("slow")

        with mock.patch.object(client.urllib.request, "urlopen", fake_urlopen):
            with self.assertRaises(RequestTimeoutError):
                _client().get_json("https://x.test")

    def test_urlerror_timeout_reason_maps_to_timeout(self) -> None:
        def fake_urlopen(request, timeout=None):
            raise urllib.error.URLError(TimeoutError("slow"))

        with mock.patch.object(client.urllib.request, "urlopen", fake_urlopen):
            with self.assertRaises(RequestTimeoutError):
                _client().get_json("https://x.test")

    def test_network_error_maps(self) -> None:
        def fake_urlopen(request, timeout=None):
            raise urllib.error.URLError("dns fail")

        with mock.patch.object(client.urllib.request, "urlopen", fake_urlopen):
            with self.assertRaises(NetworkError):
                _client().get_json("https://x.test")

    def test_invalid_json_maps(self) -> None:
        with mock.patch.object(
            client.urllib.request,
            "urlopen",
            return_value=FakeResponse("<html>bukan json</html>"),
        ):
            with self.assertRaises(InvalidResponseError):
                _client().get_json("https://x.test")

    def test_non_object_json_maps(self) -> None:
        with mock.patch.object(
            client.urllib.request, "urlopen", return_value=FakeResponse("42")
        ):
            with self.assertRaises(InvalidResponseError):
                _client().get_json("https://x.test")

    def test_oversized_body_maps(self) -> None:
        with mock.patch.object(client, "MAX_RESPONSE_BYTES", 5):
            with mock.patch.object(
                client.urllib.request,
                "urlopen",
                return_value=FakeResponse('{"a":1}'),
            ):
                with self.assertRaises(InvalidResponseError):
                    _client().get_json("https://x.test")


if __name__ == "__main__":
    unittest.main()