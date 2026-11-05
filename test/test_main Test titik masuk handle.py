"""Test titik masuk handle()."""

from __future__ import annotations

import json
import unittest

import main
from errors import ServerError
from tests.helpers import RecordingHttp
from tests.test_api import _payload, _raw_video


class HandleSuccessTests(unittest.TestCase):
    def setUp(self) -> None:
        self._original_api = main._API
        main._API = main.EpornerApi(http=RecordingHttp(_payload([_raw_video()])))

    def tearDown(self) -> None:
        main._API = self._original_api

    def test_success_string_roundtrip(self) -> None:
        result = json.loads(main.handle(json.dumps({"operation": "get_latest"})))
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["type"], "catalog")
        self.assertEqual(len(result["data"]), 1)

    def test_dict_input_accepted(self) -> None:
        result = json.loads(main.handle({"operation": "get_popular"}))
        self.assertEqual(result["status"], "success")

    def test_unicode_title_not_escaped(self) -> None:
        main._API = main.EpornerApi(
            http=RecordingHttp(_payload([_raw_video(title="日本語")]))
        )
        self.assertIn("日本語", main.handle({"operation": "get_latest"}))

    def test_error_field_none_on_success(self) -> None:
        result = json.loads(main.handle({"operation": "get_latest"}))
        self.assertIsNone(result["error"])


class HandleFailureTests(unittest.TestCase):
    def setUp(self) -> None:
        self._original_api = main._API

    def tearDown(self) -> None:
        main._API = self._original_api

    def _error(self, request) -> dict:
        result = json.loads(main.handle(request))
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["type"], "error")
        self.assertEqual(result["data"], [])
        self.assertIsNone(result["pagination"])
        return result["error"]

    def test_invalid_json(self) -> None:
        error = self._error("{bukan json")
        self.assertEqual(error["code"], "invalid_json")
        self.assertFalse(error["retryable"])

    def test_empty_request(self) -> None:
        self.assertEqual(self._error("")["code"], "invalid_json")

    def test_missing_operation(self) -> None:
        self.assertEqual(self._error(json.dumps({}))["code"], "invalid_request")

    def test_unknown_operation(self) -> None:
        error = self._error(json.dumps({"operation": "get_stream"}))
        self.assertEqual(error["code"], "unknown_operation")

    def test_invalid_parameter(self) -> None:
        error = self._error(json.dumps({"operation": "get_latest", "page": 0}))
        self.assertEqual(error["code"], "invalid_parameter")

    def test_transport_error_is_propagated(self) -> None:
        main._API = main.EpornerApi(
            http=RecordingHttp(error=ServerError("rusak"))
        )
        error = self._error(json.dumps({"operation": "get_latest"}))
        self.assertEqual(error["code"], "server_error")
        self.assertTrue(error["retryable"])

    def test_unexpected_exception_becomes_internal_error(self) -> None:
        class Boom:
            def get_json(self, *_args, **_kwargs):
                raise RuntimeError("boom")

        main._API = main.EpornerApi(http=Boom())
        self.assertEqual(
            self._error(json.dumps({"operation": "get_latest"}))["code"],
            "internal_error",
        )

    def test_envelope_always_has_all_keys(self) -> None:
        result = json.loads(main.handle("{bukan json"))
        self.assertEqual(
            sorted(result.keys()),
            [
                "contract_version",
                "data",
                "error",
                "pagination",
                "status",
                "type",
            ],
        )


if __name__ == "__main__":
    unittest.main()