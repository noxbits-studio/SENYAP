"""Test validasi request."""

from __future__ import annotations

import unittest

from errors import InvalidParameterError, InvalidRequestError, UnknownOperationError
from validator import validate_request


class ValidatorSuccessTests(unittest.TestCase):
    def test_minimal_latest_applies_defaults(self) -> None:
        result = validate_request({"operation": "get_latest"})
        self.assertEqual(result.operation, "get_latest")
        self.assertEqual(result.query, "all")
        self.assertEqual(result.page, 1)
        self.assertEqual(result.per_page, 30)
        self.assertEqual(result.thumbsize, "medium")
        self.assertEqual(result.order, "latest")
        self.assertEqual(result.gay, 0)
        self.assertEqual(result.lq, 1)

    def test_popular_default_order(self) -> None:
        result = validate_request({"operation": "get_popular"})
        self.assertEqual(result.order, "most-popular")

    def test_search_requires_and_keeps_query(self) -> None:
        result = validate_request({"operation": "search_videos", "query": "  anal  "})
        self.assertEqual(result.query, "anal")

    def test_latest_accepts_optional_query(self) -> None:
        result = validate_request({"operation": "get_latest", "query": "milf"})
        self.assertEqual(result.query, "milf")
        self.assertEqual(result.order, "latest")

    def test_numeric_strings_are_coerced(self) -> None:
        result = validate_request(
            {"operation": "get_latest", "page": "3", "per_page": "50"}
        )
        self.assertEqual(result.page, 3)
        self.assertEqual(result.per_page, 50)

    def test_enum_is_case_insensitive(self) -> None:
        result = validate_request({"operation": "get_latest", "thumbsize": "BIG"})
        self.assertEqual(result.thumbsize, "big")

    def test_order_override_accepted(self) -> None:
        result = validate_request({"operation": "get_latest", "order": "top-rated"})
        self.assertEqual(result.order, "top-rated")

    def test_gay_and_lq_bounds_accepted(self) -> None:
        result = validate_request({"operation": "get_latest", "gay": 2, "lq": 0})
        self.assertEqual(result.gay, 2)
        self.assertEqual(result.lq, 0)

    def test_unknown_extra_parameter_ignored(self) -> None:
        result = validate_request({"operation": "get_latest", "whatever": "x"})
        self.assertEqual(result.operation, "get_latest")


class ValidatorFailureTests(unittest.TestCase):
    def test_non_dict_request(self) -> None:
        with self.assertRaises(InvalidRequestError):
            validate_request(["not", "a", "dict"])

    def test_missing_operation(self) -> None:
        with self.assertRaises(InvalidRequestError):
            validate_request({})

    def test_non_string_operation(self) -> None:
        with self.assertRaises(InvalidRequestError):
            validate_request({"operation": 7})

    def test_unknown_operation(self) -> None:
        with self.assertRaises(UnknownOperationError) as ctx:
            validate_request({"operation": "get_stream"})
        self.assertEqual(ctx.exception.code, "unknown_operation")

    def test_search_without_query(self) -> None:
        with self.assertRaises(InvalidParameterError):
            validate_request({"operation": "search_videos"})

    def test_search_with_blank_query(self) -> None:
        with self.assertRaises(InvalidParameterError):
            validate_request({"operation": "search_videos", "query": "   "})

    def test_page_below_minimum(self) -> None:
        with self.assertRaises(InvalidParameterError):
            validate_request({"operation": "get_latest", "page": 0})

    def test_page_above_maximum(self) -> None:
        with self.assertRaises(InvalidParameterError):
            validate_request({"operation": "get_latest", "page": 1_000_001})

    def test_per_page_out_of_range(self) -> None:
        with self.assertRaises(InvalidParameterError):
            validate_request({"operation": "get_latest", "per_page": 0})
        with self.assertRaises(InvalidParameterError):
            validate_request({"operation": "get_latest", "per_page": 1001})

    def test_page_not_integer(self) -> None:
        with self.assertRaises(InvalidParameterError):
            validate_request({"operation": "get_latest", "page": "abc"})

    def test_page_bool_rejected(self) -> None:
        with self.assertRaises(InvalidParameterError):
            validate_request({"operation": "get_latest", "page": True})

    def test_invalid_thumbsize(self) -> None:
        with self.assertRaises(InvalidParameterError):
            validate_request({"operation": "get_latest", "thumbsize": "huge"})

    def test_invalid_order(self) -> None:
        with self.assertRaises(InvalidParameterError):
            validate_request({"operation": "get_latest", "order": "bogus"})

    def test_gay_out_of_range(self) -> None:
        with self.assertRaises(InvalidParameterError):
            validate_request({"operation": "get_latest", "gay": 3})

    def test_query_too_long(self) -> None:
        with self.assertRaises(InvalidParameterError):
            validate_request(
                {"operation": "search_videos", "query": "x" * 201}
            )


if __name__ == "__main__":
    unittest.main()