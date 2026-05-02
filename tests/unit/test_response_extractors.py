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

    def test_yahoo_quote_v8_chart_envelope(self) -> None:
        """v8/finance/chart wraps data in chart.result[0].meta."""
        from zorivest_infra.market_data.response_extractors import extract_records

        raw = json.dumps(
            {
                "chart": {
                    "result": [
                        {
                            "meta": {
                                "symbol": "AAPL",
                                "regularMarketPrice": 273.05,
                                "chartPreviousClose": 270.0,
                                "regularMarketVolume": 34667241,
                                "currency": "USD",
                            },
                        }
                    ],
                    "error": None,
                }
            }
        ).encode()

        records = extract_records(raw, provider="yahoo", data_type="quote")

        assert len(records) == 1
        assert records[0]["symbol"] == "AAPL"
        assert records[0]["regularMarketPrice"] == 273.05
        # Computed change fields
        assert "regularMarketChange" in records[0]
        assert abs(records[0]["regularMarketChange"] - 3.05) < 0.01
        assert "regularMarketChangePercent" in records[0]


# ---------------------------------------------------------------------------
# AC-2a-ohlcv: Yahoo OHLCV extraction (v8/chart parallel arrays)
# ---------------------------------------------------------------------------


class TestYahooOHLCVExtraction:
    """Yahoo Finance v8/chart OHLCV: timestamps + indicators.quote parallel arrays."""

    def test_yahoo_ohlcv_parallel_arrays_zipped(self) -> None:
        """chart.result[0].timestamp + indicators.quote[0] → zipped dicts."""
        from zorivest_infra.market_data.response_extractors import extract_records

        raw = json.dumps(
            {
                "chart": {
                    "result": [
                        {
                            "timestamp": [1700000000, 1700086400, 1700172800],
                            "indicators": {
                                "quote": [
                                    {
                                        "open": [100.0, 101.0, 102.0],
                                        "high": [105.0, 106.0, 107.0],
                                        "low": [99.0, 100.0, 101.0],
                                        "close": [103.0, 104.0, 105.0],
                                        "volume": [1000, 2000, 3000],
                                    }
                                ]
                            },
                        }
                    ],
                    "error": None,
                }
            }
        ).encode()

        records = extract_records(raw, provider="yahoo", data_type="ohlcv")

        assert len(records) == 3
        # First bar
        assert records[0]["timestamp"] == 1700000000
        assert records[0]["open"] == 100.0
        assert records[0]["high"] == 105.0
        assert records[0]["low"] == 99.0
        assert records[0]["close"] == 103.0
        assert records[0]["volume"] == 1000
        # Last bar
        assert records[2]["timestamp"] == 1700172800
        assert records[2]["close"] == 105.0
        assert records[2]["volume"] == 3000

    def test_yahoo_ohlcv_single_bar(self) -> None:
        """Single-bar response (range=1d) still produces one record."""
        from zorivest_infra.market_data.response_extractors import extract_records

        raw = json.dumps(
            {
                "chart": {
                    "result": [
                        {
                            "timestamp": [1700000000],
                            "indicators": {
                                "quote": [
                                    {
                                        "open": [150.0],
                                        "high": [155.0],
                                        "low": [149.0],
                                        "close": [153.0],
                                        "volume": [5000000],
                                    }
                                ]
                            },
                        }
                    ],
                    "error": None,
                }
            }
        ).encode()

        records = extract_records(raw, provider="yahoo", data_type="ohlcv")

        assert len(records) == 1
        assert records[0]["timestamp"] == 1700000000
        assert records[0]["open"] == 150.0
        assert records[0]["close"] == 153.0

    def test_yahoo_ohlcv_empty_timestamps(self) -> None:
        """Empty timestamp array → empty list."""
        from zorivest_infra.market_data.response_extractors import extract_records

        raw = json.dumps(
            {
                "chart": {
                    "result": [
                        {
                            "timestamp": [],
                            "indicators": {
                                "quote": [
                                    {
                                        "open": [],
                                        "high": [],
                                        "low": [],
                                        "close": [],
                                        "volume": [],
                                    }
                                ]
                            },
                        }
                    ],
                    "error": None,
                }
            }
        ).encode()

        records = extract_records(raw, provider="yahoo", data_type="ohlcv")

        assert records == []

    def test_yahoo_ohlcv_missing_indicators(self) -> None:
        """Missing indicators block → empty list."""
        from zorivest_infra.market_data.response_extractors import extract_records

        raw = json.dumps(
            {
                "chart": {
                    "result": [{"timestamp": [1700000000]}],
                    "error": None,
                }
            }
        ).encode()

        records = extract_records(raw, provider="yahoo", data_type="ohlcv")

        assert records == []

    def test_yahoo_ohlcv_none_values_preserved(self) -> None:
        """Yahoo returns None for market-closed bars — preserve them."""
        from zorivest_infra.market_data.response_extractors import extract_records

        raw = json.dumps(
            {
                "chart": {
                    "result": [
                        {
                            "timestamp": [1700000000, 1700086400],
                            "indicators": {
                                "quote": [
                                    {
                                        "open": [100.0, None],
                                        "high": [105.0, None],
                                        "low": [99.0, None],
                                        "close": [103.0, None],
                                        "volume": [1000, None],
                                    }
                                ]
                            },
                        }
                    ],
                    "error": None,
                }
            }
        ).encode()

        records = extract_records(raw, provider="yahoo", data_type="ohlcv")

        assert len(records) == 2
        assert records[0]["close"] == 103.0
        assert records[1]["close"] is None

    def test_yahoo_ohlcv_pre_extracted_list(self) -> None:
        """Pre-extracted list (from multi-ticker adapter) → pass-through."""
        from zorivest_infra.market_data.response_extractors import extract_records

        raw = json.dumps(
            [
                {"timestamp": 1700000000, "open": 100.0, "close": 103.0},
                {"timestamp": 1700086400, "open": 101.0, "close": 104.0},
            ]
        ).encode()

        records = extract_records(raw, provider="yahoo", data_type="ohlcv")

        assert len(records) == 2
        assert records[0]["open"] == 100.0


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


# ═══════════════════════════════════════════════════════════════════════════
# MEU-187: Standard Extractors — FIC (Feature Intent Contract)
# ═══════════════════════════════════════════════════════════════════════════
#
# AC-13: Alpaca extractor: symbol_keyed_dict (multi) + flat list (single)
# AC-14: FMP extractor: root_array + {historical: [...]} wrapper
# AC-15: EODHD extractor: root_array for EOD + nested sections for fundamentals
# AC-16: API Ninjas extractor: root_object + root_array
# AC-17: Tradier extractor: dict→list collapse


class TestAlpacaExtractor:
    """AC-13: Alpaca extractor handles multi-symbol dict + single flat list."""

    def test_alpaca_bars_multi_symbol(self) -> None:
        """Alpaca multi-symbol bars: {bars: {AAPL: [{...}]}}."""
        from zorivest_infra.market_data.response_extractors import extract_records

        raw = json.dumps(
            {
                "bars": {
                    "AAPL": [
                        {
                            "o": 150,
                            "h": 155,
                            "l": 149,
                            "c": 153,
                            "v": 1000,
                            "t": "2024-01-01T00:00:00Z",
                        },
                    ],
                    "MSFT": [
                        {
                            "o": 370,
                            "h": 375,
                            "l": 368,
                            "c": 372,
                            "v": 2000,
                            "t": "2024-01-01T00:00:00Z",
                        },
                    ],
                }
            }
        ).encode()
        records = extract_records(raw, provider="alpaca", data_type="ohlcv")
        assert len(records) >= 2

    def test_alpaca_snapshot_single(self) -> None:
        """Alpaca single-symbol snapshot: {latestTrade: {p: 150}, ...}."""
        from zorivest_infra.market_data.response_extractors import extract_records

        raw = json.dumps(
            {
                "latestTrade": {"p": 150.5, "s": 100},
                "latestQuote": {"bp": 150.3, "ap": 150.7},
                "minuteBar": {"o": 150, "h": 151, "l": 149.5, "c": 150.5, "v": 5000},
            }
        ).encode()
        records = extract_records(raw, provider="alpaca", data_type="quote")
        assert len(records) >= 1

    def test_alpaca_news_list(self) -> None:
        """Alpaca news: {news: [{...}, ...]}."""
        from zorivest_infra.market_data.response_extractors import extract_records

        raw = json.dumps(
            {
                "news": [
                    {"headline": "Apple earnings", "source": "Reuters"},
                    {"headline": "Tech rally", "source": "AP"},
                ]
            }
        ).encode()
        records = extract_records(raw, provider="alpaca", data_type="news")
        assert len(records) == 2


class TestFMPExtractor:
    """AC-14: FMP extractor handles root_array and {historical: [...]} wrapper."""

    def test_fmp_quote_root_array(self) -> None:
        """FMP quote: top-level array."""
        from zorivest_infra.market_data.response_extractors import extract_records

        raw = json.dumps(
            [
                {"symbol": "AAPL", "price": 150.0, "volume": 1000000},
            ]
        ).encode()
        records = extract_records(raw, provider="fmp", data_type="quote")
        assert len(records) == 1
        assert records[0]["symbol"] == "AAPL"

    def test_fmp_ohlcv_historical_wrapper(self) -> None:
        """FMP OHLCV: {symbol: 'AAPL', historical: [{...}]}."""
        from zorivest_infra.market_data.response_extractors import extract_records

        raw = json.dumps(
            {
                "symbol": "AAPL",
                "historical": [
                    {
                        "date": "2024-01-01",
                        "open": 150,
                        "high": 155,
                        "low": 149,
                        "close": 153,
                        "volume": 1000,
                    },
                ],
            }
        ).encode()
        records = extract_records(raw, provider="fmp", data_type="ohlcv")
        assert len(records) == 1
        assert records[0]["open"] == 150

    def test_fmp_earnings_root_array(self) -> None:
        """FMP earnings: top-level array."""
        from zorivest_infra.market_data.response_extractors import extract_records

        raw = json.dumps(
            [
                {"symbol": "AAPL", "eps": 1.52, "revenue": 90000000000},
            ]
        ).encode()
        records = extract_records(raw, provider="fmp", data_type="earnings")
        assert len(records) == 1

    def test_fmp_dividends_historical_wrapper(self) -> None:
        """FMP dividends: {historical: [{...}]}."""
        from zorivest_infra.market_data.response_extractors import extract_records

        raw = json.dumps(
            {
                "symbol": "AAPL",
                "historical": [
                    {"date": "2024-01-15", "dividend": 0.24},
                ],
            }
        ).encode()
        records = extract_records(raw, provider="fmp", data_type="dividends")
        assert len(records) == 1

    def test_fmp_news_root_array(self) -> None:
        """FMP news: top-level array."""
        from zorivest_infra.market_data.response_extractors import extract_records

        raw = json.dumps(
            [
                {
                    "symbol": "AAPL",
                    "title": "Apple earnings beat",
                    "publishedDate": "2024-01-15",
                },
            ]
        ).encode()
        records = extract_records(raw, provider="fmp", data_type="news")
        assert len(records) == 1
        assert records[0]["title"] == "Apple earnings beat"

    def test_fmp_fundamentals_root_array(self) -> None:
        """FMP fundamentals (income statement): top-level array."""
        from zorivest_infra.market_data.response_extractors import extract_records

        raw = json.dumps(
            [
                {
                    "symbol": "AAPL",
                    "revenue": 90000000000,
                    "netIncome": 25000000000,
                    "date": "2024-Q1",
                },
            ]
        ).encode()
        records = extract_records(raw, provider="fmp", data_type="fundamentals")
        assert len(records) == 1
        assert records[0]["revenue"] == 90000000000

    def test_fmp_splits_historical_wrapper(self) -> None:
        """FMP splits: {historical: [{...}]}."""
        from zorivest_infra.market_data.response_extractors import extract_records

        raw = json.dumps(
            {
                "symbol": "AAPL",
                "historical": [
                    {"date": "2020-08-31", "numerator": 4, "denominator": 1},
                ],
            }
        ).encode()
        records = extract_records(raw, provider="fmp", data_type="splits")
        assert len(records) == 1
        assert records[0]["numerator"] == 4


class TestEODHDExtractor:
    """AC-15: EODHD extractor handles root_array for EOD + nested sections."""

    def test_eodhd_ohlcv_root_array(self) -> None:
        """EODHD EOD data: top-level array."""
        from zorivest_infra.market_data.response_extractors import extract_records

        raw = json.dumps(
            [
                {
                    "date": "2024-01-01",
                    "open": 150,
                    "high": 155,
                    "low": 149,
                    "close": 153,
                    "volume": 1000,
                },
            ]
        ).encode()
        records = extract_records(raw, provider="eodhd", data_type="ohlcv")
        assert len(records) == 1

    def test_eodhd_fundamentals_nested_sections(self) -> None:
        """EODHD fundamentals: {General: {...}, Highlights: {...}}."""
        from zorivest_infra.market_data.response_extractors import extract_records

        raw = json.dumps(
            {
                "General": {"Code": "AAPL", "Name": "Apple Inc."},
                "Highlights": {"MarketCapitalization": 3000000000000, "PERatio": 28.5},
            }
        ).encode()
        records = extract_records(raw, provider="eodhd", data_type="fundamentals")
        assert len(records) >= 1

    def test_eodhd_dividends_root_array(self) -> None:
        """EODHD dividends: top-level array."""
        from zorivest_infra.market_data.response_extractors import extract_records

        raw = json.dumps(
            [
                {"date": "2024-01-15", "value": "0.24"},
            ]
        ).encode()
        records = extract_records(raw, provider="eodhd", data_type="dividends")
        assert len(records) == 1


class TestAPINinjasExtractor:
    """AC-16: API Ninjas extractor handles root_object + root_array."""

    def test_api_ninjas_quote_root_object(self) -> None:
        """API Ninjas quote: root object (single item, wrap in list)."""
        from zorivest_infra.market_data.response_extractors import extract_records

        raw = json.dumps(
            {"ticker": "AAPL", "price": 150.0, "name": "Apple Inc."}
        ).encode()
        records = extract_records(raw, provider="api_ninjas", data_type="quote")
        assert len(records) == 1
        assert records[0]["ticker"] == "AAPL"

    def test_api_ninjas_earnings_root_array(self) -> None:
        """API Ninjas earnings: top-level array."""
        from zorivest_infra.market_data.response_extractors import extract_records

        raw = json.dumps(
            [
                {"ticker": "AAPL", "actual_eps": 1.52},
                {"ticker": "AAPL", "actual_eps": 1.46},
            ]
        ).encode()
        records = extract_records(raw, provider="api_ninjas", data_type="earnings")
        assert len(records) == 2


class TestTradierExtractor:
    """AC-17: Tradier extractor handles dict→list collapse."""

    def test_tradier_quote_single_dict(self) -> None:
        """Tradier single quote: {quotes: {quote: {...}}}."""
        from zorivest_infra.market_data.response_extractors import extract_records

        raw = json.dumps(
            {
                "quotes": {
                    "quote": {
                        "symbol": "AAPL",
                        "last": 150.0,
                        "volume": 1000000,
                    }
                }
            }
        ).encode()
        records = extract_records(raw, provider="tradier", data_type="quote")
        assert len(records) == 1
        assert records[0]["symbol"] == "AAPL"

    def test_tradier_quote_multi_list(self) -> None:
        """Tradier multi quote: {quotes: {quote: [{...}, {...}]}}."""
        from zorivest_infra.market_data.response_extractors import extract_records

        raw = json.dumps(
            {
                "quotes": {
                    "quote": [
                        {"symbol": "AAPL", "last": 150.0},
                        {"symbol": "MSFT", "last": 370.0},
                    ]
                }
            }
        ).encode()
        records = extract_records(raw, provider="tradier", data_type="quote")
        assert len(records) == 2

    def test_tradier_ohlcv(self) -> None:
        """Tradier OHLCV: {history: {day: [{...}]}}."""
        from zorivest_infra.market_data.response_extractors import extract_records

        raw = json.dumps(
            {
                "history": {
                    "day": [
                        {
                            "date": "2024-01-01",
                            "open": 150,
                            "high": 155,
                            "low": 149,
                            "close": 153,
                            "volume": 1000,
                        },
                    ]
                }
            }
        ).encode()
        records = extract_records(raw, provider="tradier", data_type="ohlcv")
        assert len(records) == 1


# ═══════════════════════════════════════════════════════════════════════════
# MEU-188: Complex Extractors — FIC (Feature Intent Contract)
# ═══════════════════════════════════════════════════════════════════════════
#
# AC-20: Alpha Vantage date-keyed OHLCV extraction + rate-limit detection
# AC-22: Finnhub candle extractor zips parallel arrays
# AC-23: Nasdaq Data Link extractor zips column_names with data rows
# AC-24: Polygon timestamp extractor converts ms UNIX timestamps
# AC-25: Alpha Vantage CSV earnings parsing
# AC-26: Field mappings for complex providers


class TestAlphaVantageExtractor:
    """AC-20/AC-25: Alpha Vantage complex envelope extraction."""

    def test_alpha_vantage_ohlcv_date_keyed(self) -> None:
        """Alpha Vantage OHLCV: {'Time Series (Daily)': {'2024-01-01': {...}}}."""
        from zorivest_infra.market_data.response_extractors import extract_records

        raw = json.dumps(
            {
                "Meta Data": {"1. Information": "Daily Prices", "2. Symbol": "AAPL"},
                "Time Series (Daily)": {
                    "2024-01-02": {
                        "1. open": "150.00",
                        "2. high": "155.00",
                        "3. low": "149.00",
                        "4. close": "153.00",
                        "5. volume": "1000000",
                    },
                    "2024-01-01": {
                        "1. open": "148.00",
                        "2. high": "151.00",
                        "3. low": "147.00",
                        "4. close": "150.00",
                        "5. volume": "900000",
                    },
                },
            }
        ).encode()
        records = extract_records(raw, provider="alpha_vantage", data_type="ohlcv")
        assert len(records) == 2
        # Records should contain date and stripped prefix fields
        assert any("open" in r or "1. open" in r for r in records)

    def test_alpha_vantage_ohlcv_prefix_stripping(self) -> None:
        """Alpha Vantage strips '1. ', '2. ' prefixes from field names."""
        from zorivest_infra.market_data.response_extractors import extract_records

        raw = json.dumps(
            {
                "Time Series (Daily)": {
                    "2024-01-01": {
                        "1. open": "150.00",
                        "2. high": "155.00",
                        "3. low": "149.00",
                        "4. close": "153.00",
                        "5. volume": "1000000",
                    },
                },
            }
        ).encode()
        records = extract_records(raw, provider="alpha_vantage", data_type="ohlcv")
        assert len(records) == 1
        rec = records[0]
        assert "open" in rec
        assert "close" in rec

    def test_alpha_vantage_quote(self) -> None:
        """Alpha Vantage GLOBAL_QUOTE: {'Global Quote': {'01. symbol': ...}}."""
        from zorivest_infra.market_data.response_extractors import extract_records

        raw = json.dumps(
            {
                "Global Quote": {
                    "01. symbol": "AAPL",
                    "02. open": "150.00",
                    "05. price": "153.00",
                    "06. volume": "1000000",
                    "10. change percent": "1.5%",
                }
            }
        ).encode()
        records = extract_records(raw, provider="alpha_vantage", data_type="quote")
        assert len(records) == 1

    def test_alpha_vantage_rate_limit(self) -> None:
        """Alpha Vantage rate-limit: {'Note': 'Thank you for using...'}."""
        from zorivest_infra.market_data.response_extractors import extract_records

        raw = json.dumps(
            {
                "Note": "Thank you for using Alpha Vantage! Our standard API call frequency..."
            }
        ).encode()
        records = extract_records(raw, provider="alpha_vantage", data_type="ohlcv")
        assert records == []

    def test_alpha_vantage_earnings_csv(self) -> None:
        """AC-25: Alpha Vantage CSV earnings parsing."""
        from zorivest_infra.market_data.response_extractors import extract_records

        csv_data = b"symbol,name,reportDate,fiscalDateEnding,estimate,currency\nAAPL,Apple Inc,2024-01-25,2023-12-31,2.10,USD\nAAPL,Apple Inc,2023-10-26,2023-09-30,1.39,USD\n"
        records = extract_records(
            csv_data, provider="alpha_vantage", data_type="earnings"
        )
        assert len(records) == 2
        assert records[0]["symbol"] == "AAPL"


class TestFinnhubCandleExtractor:
    """AC-22: Finnhub candle extractor zips parallel arrays."""

    def test_finnhub_candle_zip(self) -> None:
        """Finnhub candles: {c: [103], h: [105], l: [99], o: [100], s: 'ok', t: [1700000000], v: [1000]}."""
        from zorivest_infra.market_data.response_extractors import extract_records

        raw = json.dumps(
            {
                "c": [103.0, 104.0],
                "h": [105.0, 106.0],
                "l": [99.0, 100.0],
                "o": [100.0, 101.0],
                "t": [1700000000, 1700086400],
                "v": [1000000, 1100000],
                "s": "ok",
            }
        ).encode()
        records = extract_records(raw, provider="finnhub", data_type="ohlcv")
        assert len(records) == 2
        assert records[0]["o"] == 100.0
        assert records[0]["c"] == 103.0
        assert records[0]["v"] == 1000000

    def test_finnhub_candle_no_data(self) -> None:
        """Finnhub candles with s='no_data' → empty list."""
        from zorivest_infra.market_data.response_extractors import extract_records

        raw = json.dumps({"s": "no_data"}).encode()
        records = extract_records(raw, provider="finnhub", data_type="ohlcv")
        assert records == []

    def test_finnhub_candle_single(self) -> None:
        """Finnhub candles with single element."""
        from zorivest_infra.market_data.response_extractors import extract_records

        raw = json.dumps(
            {
                "c": [103.0],
                "h": [105.0],
                "l": [99.0],
                "o": [100.0],
                "t": [1700000000],
                "v": [1000000],
                "s": "ok",
            }
        ).encode()
        records = extract_records(raw, provider="finnhub", data_type="ohlcv")
        assert len(records) == 1


class TestNasdaqDLExtractor:
    """AC-23: Nasdaq Data Link extractor zips column_names with data rows."""

    def test_nasdaq_dl_datatable_zip(self) -> None:
        """Nasdaq DL: {datatable: {data: [[...]], columns: [{name:...}]}}."""
        from zorivest_infra.market_data.response_extractors import extract_records

        raw = json.dumps(
            {
                "datatable": {
                    "data": [
                        ["AAPL", "2024-01-01", 150000000000, 28.5, 1.52],
                        ["AAPL", "2023-10-01", 148000000000, 27.0, 1.46],
                    ],
                    "columns": [
                        {"name": "ticker", "type": "String"},
                        {"name": "calendardate", "type": "Date"},
                        {"name": "revenue", "type": "double"},
                        {"name": "pe", "type": "double"},
                        {"name": "eps", "type": "double"},
                    ],
                }
            }
        ).encode()
        records = extract_records(raw, provider="nasdaq_dl", data_type="fundamentals")
        assert len(records) == 2
        assert records[0]["ticker"] == "AAPL"
        assert records[0]["pe"] == 28.5

    def test_nasdaq_dl_empty_data(self) -> None:
        """Nasdaq DL with empty data → empty list."""
        from zorivest_infra.market_data.response_extractors import extract_records

        raw = json.dumps(
            {
                "datatable": {
                    "data": [],
                    "columns": [{"name": "ticker", "type": "String"}],
                }
            }
        ).encode()
        records = extract_records(raw, provider="nasdaq_dl", data_type="fundamentals")
        assert records == []


class TestPolygonTimestampExtractor:
    """AC-24: Polygon timestamp normalization (ms → seconds)."""

    def test_polygon_ohlcv_timestamp_ms_to_iso(self) -> None:
        """Polygon OHLCV t=1700000000000 (ms) → record has normalized timestamp."""
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
                "status": "OK",
            }
        ).encode()
        records = extract_records(raw, provider="polygon", data_type="ohlcv")
        assert len(records) == 1
        # t should be normalized to seconds (int or ISO string)
        t = records[0]["t"]
        # Either 1700000000 (seconds) or ISO string is acceptable
        if isinstance(t, (int, float)):
            assert t == 1700000000  # Divided by 1000
        else:
            assert "2023-11-14" in str(t)


# ═══════════════════════════════════════════════════════════════════════════
# F3 Corrections: Missing extractor registration tests
# ═══════════════════════════════════════════════════════════════════════════


class TestFMPMissingExtractors:
    """F3: FMP news, fundamentals, splits — all root-array or wrapper patterns."""

    def test_fmp_news_root_array(self) -> None:
        """FMP news returns top-level array."""
        from zorivest_infra.market_data.response_extractors import extract_records

        raw = json.dumps(
            [
                {
                    "title": "AAPL up",
                    "site": "Reuters",
                    "url": "https://ex.com",
                    "publishedDate": "2024-01-15",
                },
                {
                    "title": "MSFT down",
                    "site": "Bloomberg",
                    "url": "https://ex2.com",
                    "publishedDate": "2024-01-16",
                },
            ]
        ).encode()
        records = extract_records(raw, provider="fmp", data_type="news")
        assert len(records) == 2
        assert records[0]["title"] == "AAPL up"

    def test_fmp_fundamentals_root_array(self) -> None:
        """FMP fundamentals returns top-level array."""
        from zorivest_infra.market_data.response_extractors import extract_records

        raw = json.dumps(
            [
                {
                    "date": "2024-01-15",
                    "symbol": "AAPL",
                    "revenue": 100000,
                    "netIncome": 25000,
                },
            ]
        ).encode()
        records = extract_records(raw, provider="fmp", data_type="fundamentals")
        assert len(records) == 1
        assert records[0]["symbol"] == "AAPL"

    def test_fmp_splits_historical_wrapper(self) -> None:
        """FMP splits uses {historical: [{...}]} wrapper."""
        from zorivest_infra.market_data.response_extractors import extract_records

        raw = json.dumps(
            {
                "symbol": "AAPL",
                "historical": [
                    {
                        "date": "2020-08-31",
                        "label": "4:1",
                        "numerator": 4.0,
                        "denominator": 1.0,
                    },
                ],
            }
        ).encode()
        records = extract_records(raw, provider="fmp", data_type="splits")
        assert len(records) == 1
        assert records[0]["label"] == "4:1"
        assert records[0]["numerator"] == 4.0


class TestEODHDMissingExtractors:
    """F3: EODHD news, splits — both root-array patterns."""

    def test_eodhd_news_root_array(self) -> None:
        """EODHD news returns top-level array."""
        from zorivest_infra.market_data.response_extractors import extract_records

        raw = json.dumps(
            [
                {"title": "AAPL up", "link": "https://ex.com", "date": "2024-01-15"},
                {"title": "MSFT down", "link": "https://ex2.com", "date": "2024-01-16"},
            ]
        ).encode()
        records = extract_records(raw, provider="eodhd", data_type="news")
        assert len(records) == 2
        assert records[0]["title"] == "AAPL up"

    def test_eodhd_splits_root_array(self) -> None:
        """EODHD splits returns top-level array."""
        from zorivest_infra.market_data.response_extractors import extract_records

        raw = json.dumps(
            [
                {"date": "2020-08-31", "split": "4:1"},
            ]
        ).encode()
        records = extract_records(raw, provider="eodhd", data_type="splits")
        assert len(records) == 1
        assert records[0]["split"] == "4:1"


# ═══════════════════════════════════════════════════════════════════════════
# TradingView Scanner Addendum — Extractor Tests
# ═══════════════════════════════════════════════════════════════════════════


class TestTradingViewQuoteExtractor:
    """TradingView scanner quote extraction — column-zip pattern."""

    def test_tradingview_quote_scanner_response(self) -> None:
        """Scanner response {data: [{s, d}]} zipped with columns → records."""
        from zorivest_infra.market_data.response_extractors import extract_records

        raw = json.dumps(
            {
                "totalCount": 1,
                "data": [
                    {
                        "s": "NASDAQ:AAPL",
                        "d": [150.0, 1000000, 2.5, 155.0, 149.0, 148.0, "Apple Inc"],
                    },
                ],
            }
        ).encode()
        records = extract_records(raw, provider="tradingview", data_type="quote")
        assert len(records) == 1
        assert records[0]["close"] == 150.0
        assert records[0]["volume"] == 1000000
        assert records[0]["name"] == "Apple Inc"

    def test_tradingview_quote_multi_ticker(self) -> None:
        """Scanner can return multiple tickers in one response."""
        from zorivest_infra.market_data.response_extractors import extract_records

        raw = json.dumps(
            {
                "totalCount": 2,
                "data": [
                    {
                        "s": "NASDAQ:AAPL",
                        "d": [150.0, 1000000, 2.5, 155.0, 149.0, 148.0, "Apple"],
                    },
                    {
                        "s": "NASDAQ:MSFT",
                        "d": [400.0, 500000, 1.0, 405.0, 398.0, 399.0, "Microsoft"],
                    },
                ],
            }
        ).encode()
        records = extract_records(raw, provider="tradingview", data_type="quote")
        assert len(records) == 2
        assert records[1]["close"] == 400.0

    def test_tradingview_quote_empty_data(self) -> None:
        """Scanner with empty data → empty list."""
        from zorivest_infra.market_data.response_extractors import extract_records

        raw = json.dumps({"totalCount": 0, "data": []}).encode()
        records = extract_records(raw, provider="tradingview", data_type="quote")
        assert records == []


class TestTradingViewFundamentalsExtractor:
    """TradingView scanner fundamentals extraction."""

    def test_tradingview_fundamentals_scanner_response(self) -> None:
        """Scanner fundamentals with key metrics."""
        from zorivest_infra.market_data.response_extractors import extract_records

        raw = json.dumps(
            {
                "totalCount": 1,
                "data": [
                    {
                        "s": "NASDAQ:AAPL",
                        "d": [2800000000000, 6.5, 28.5, 0.5, 45.0, 1.2, "Apple Inc"],
                    },
                ],
            }
        ).encode()
        records = extract_records(raw, provider="tradingview", data_type="fundamentals")
        assert len(records) == 1
        assert records[0]["market_cap_basic"] == 2800000000000
        assert records[0]["name"] == "Apple Inc"
