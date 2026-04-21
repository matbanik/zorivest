# tests/unit/test_response_extractors.py
"""TDD Red-phase tests for response extractors (MEU-PW12, AC-2).

FIC — Feature Intent Contract:
  extract_records(raw, provider, data_type) unwraps provider-specific
  JSON response envelopes into a flat list[dict] of records.

AC-2: extract_records() unwraps Yahoo quote envelope (`quoteResponse.result`),
      Polygon OHLCV envelope (`results`), and falls back to generic extraction.
      (Research-backed + Local Canon)

Negative tests:
  - Non-JSON bytes → empty list
  - Missing envelope key → empty list
  - Empty bytes → empty list
"""

from __future__ import annotations

import json


# ---------------------------------------------------------------------------
# AC-2a: Yahoo quote envelope extraction
# ---------------------------------------------------------------------------


class TestYahooQuoteExtraction:
    """Yahoo Finance /v6/finance/quote wraps records in quoteResponse.result."""

    def test_yahoo_quote_envelope_unwrapped(self) -> None:
        """extract_records unwraps Yahoo quoteResponse.result envelope."""
        from zorivest_infra.market_data.response_extractors import extract_records

        raw = json.dumps(
            {
                "quoteResponse": {
                    "result": [
                        {
                            "symbol": "AAPL",
                            "regularMarketPrice": 150.0,
                            "regularMarketBid": 149.9,
                            "regularMarketAsk": 150.1,
                            "regularMarketVolume": 1000000,
                            "regularMarketChange": 2.5,
                            "regularMarketChangePercent": 1.7,
                        },
                    ],
                    "error": None,
                }
            }
        ).encode()

        records = extract_records(raw, provider="yahoo", data_type="quote")

        assert len(records) == 1
        assert records[0]["symbol"] == "AAPL"
        assert records[0]["regularMarketPrice"] == 150.0

    def test_yahoo_quote_multiple_symbols(self) -> None:
        """extract_records handles multi-symbol Yahoo response."""
        from zorivest_infra.market_data.response_extractors import extract_records

        raw = json.dumps(
            {
                "quoteResponse": {
                    "result": [
                        {"symbol": "AAPL", "regularMarketPrice": 150.0},
                        {"symbol": "GOOG", "regularMarketPrice": 180.0},
                    ],
                    "error": None,
                }
            }
        ).encode()

        records = extract_records(raw, provider="yahoo", data_type="quote")

        assert len(records) == 2
        assert records[0]["symbol"] == "AAPL"
        assert records[1]["symbol"] == "GOOG"

    def test_yahoo_quote_missing_result_key(self) -> None:
        """Missing quoteResponse.result → empty list."""
        from zorivest_infra.market_data.response_extractors import extract_records

        raw = json.dumps({"quoteResponse": {"error": "Not found"}}).encode()

        records = extract_records(raw, provider="yahoo", data_type="quote")

        assert records == []


# ---------------------------------------------------------------------------
# AC-2b: Polygon OHLCV envelope extraction
# ---------------------------------------------------------------------------


class TestPolygonOHLCVExtraction:
    """Polygon /v2/aggs wraps OHLCV data in results array."""

    def test_polygon_ohlcv_envelope_unwrapped(self) -> None:
        """extract_records unwraps Polygon results envelope."""
        from zorivest_infra.market_data.response_extractors import extract_records

        raw = json.dumps(
            {
                "results": [
                    {
                        "o": 100.0,
                        "h": 105.0,
                        "l": 99.0,
                        "c": 103.0,
                        "v": 1000000,
                        "t": 1700000000000,
                    },
                ],
                "resultsCount": 1,
                "status": "OK",
            }
        ).encode()

        records = extract_records(raw, provider="polygon", data_type="ohlcv")

        assert len(records) == 1
        assert records[0]["o"] == 100.0
        assert records[0]["v"] == 1000000

    def test_polygon_ohlcv_missing_results_key(self) -> None:
        """Missing results key → empty list."""
        from zorivest_infra.market_data.response_extractors import extract_records

        raw = json.dumps({"status": "OK", "resultsCount": 0}).encode()

        records = extract_records(raw, provider="polygon", data_type="ohlcv")

        assert records == []


# ---------------------------------------------------------------------------
# AC-2c: Generic extraction (unknown provider or data_type)
# ---------------------------------------------------------------------------


class TestGenericExtraction:
    """Unknown provider/data_type should try top-level list or wrap in list."""

    def test_generic_top_level_list(self) -> None:
        """Top-level JSON list → returned as-is."""
        from zorivest_infra.market_data.response_extractors import extract_records

        raw = json.dumps([{"foo": 1}, {"foo": 2}]).encode()

        records = extract_records(raw, provider="generic", data_type="ohlcv")

        assert len(records) == 2
        assert records[0]["foo"] == 1

    def test_generic_top_level_dict_returned_as_single(self) -> None:
        """Top-level JSON dict without known envelope → wrapped in list."""
        from zorivest_infra.market_data.response_extractors import extract_records

        raw = json.dumps({"foo": "bar"}).encode()

        records = extract_records(raw, provider="unknown_provider", data_type="ohlcv")

        assert len(records) == 1
        assert records[0]["foo"] == "bar"


# ---------------------------------------------------------------------------
# AC-2d: Error handling
# ---------------------------------------------------------------------------


class TestExtractionErrorHandling:
    """Non-JSON, empty, and malformed inputs."""

    def test_non_json_bytes_returns_empty(self) -> None:
        """Non-JSON bytes → empty list, no crash."""
        from zorivest_infra.market_data.response_extractors import extract_records

        records = extract_records(
            b"not json at all", provider="yahoo", data_type="quote"
        )

        assert records == []

    def test_empty_bytes_returns_empty(self) -> None:
        """Empty bytes → empty list."""
        from zorivest_infra.market_data.response_extractors import extract_records

        records = extract_records(b"", provider="yahoo", data_type="quote")

        assert records == []

    def test_unicode_decode_error_returns_empty(self) -> None:
        """Invalid UTF-8 bytes → empty list, no crash."""
        from zorivest_infra.market_data.response_extractors import extract_records

        records = extract_records(
            b"\xff\xfe\x00\x01", provider="yahoo", data_type="quote"
        )

        assert records == []

    def test_yahoo_display_name_also_works(self) -> None:
        """Provider display name 'Yahoo Finance' should also work
        (matching happens via slug normalization)."""
        from zorivest_infra.market_data.response_extractors import extract_records

        raw = json.dumps(
            {
                "quoteResponse": {
                    "result": [
                        {"symbol": "AAPL", "regularMarketPrice": 150.0},
                    ],
                    "error": None,
                }
            }
        ).encode()

        records = extract_records(raw, provider="Yahoo Finance", data_type="quote")

        assert len(records) == 1
