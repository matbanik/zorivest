# tests/unit/test_field_mappings.py
"""TDD Red-phase tests for field mappings (MEU-PW3).

AC-7: FIELD_MAPPINGS has entries for all 4 data types with generic mapping each.
AC-8: apply_field_mapping() translates provider-specific fields correctly.
"""

from __future__ import annotations

import pytest

from zorivest_infra.market_data.field_mappings import (
    FIELD_MAPPINGS,
    apply_field_mapping,
)


# ── AC-7: FIELD_MAPPINGS coverage ──────────────────────────────────────────


class TestFieldMappingRegistry:
    """AC-7: All 4 data types have generic mappings."""

    @pytest.mark.parametrize("data_type", ["ohlcv", "quote", "news", "fundamentals"])
    def test_generic_mapping_exists(self, data_type: str) -> None:
        assert ("generic", data_type) in FIELD_MAPPINGS

    @pytest.mark.parametrize(
        "provider,data_type",
        [
            ("yahoo", "quote"),
            ("polygon", "quote"),
            ("yahoo", "news"),
            ("polygon", "news"),
            ("yahoo", "fundamentals"),
            ("polygon", "fundamentals"),
            ("yahoo", "ohlcv"),
            # F2 corrections: 9 extractor-present pairs missing mappings
            ("alpaca", "news"),
            ("fmp", "earnings"),
            ("fmp", "dividends"),
            ("eodhd", "fundamentals"),
            ("eodhd", "dividends"),
            ("api_ninjas", "quote"),
            ("api_ninjas", "earnings"),
            ("alpha_vantage", "earnings"),
            ("nasdaq_dl", "fundamentals"),
            # F3 corrections: 5 new extractor pairs also need mappings
            ("fmp", "news"),
            ("fmp", "fundamentals"),
            ("fmp", "splits"),
            ("eodhd", "news"),
            ("eodhd", "splits"),
            # TradingView addendum: scanner quote + fundamentals
            ("tradingview", "quote"),
            ("tradingview", "fundamentals"),
        ],
    )
    def test_provider_mapping_exists(self, provider: str, data_type: str) -> None:
        assert (provider, data_type) in FIELD_MAPPINGS

    def test_missing_mapping_returns_empty_graceful(self) -> None:
        """Unknown provider/data_type returns input as _extra."""
        result = apply_field_mapping(
            record={"foo": "bar"},
            provider="nonexistent",
            data_type="nonexistent",
        )
        assert result["_extra"] == {"foo": "bar"}


# ── AC-8: Quote field mappings ─────────────────────────────────────────────


class TestOhlcvMappings:
    """Yahoo OHLCV field mapping: v8/chart parallel arrays → canonical OHLCV."""

    def test_yahoo_ohlcv_mapping(self) -> None:
        """Yahoo v8/chart indicators → canonical open/high/low/close/volume."""
        record = {
            "timestamp": 1700000000,
            "open": 100.0,
            "high": 105.0,
            "low": 99.0,
            "close": 103.0,
            "volume": 1000000,
        }
        result = apply_field_mapping(record=record, provider="yahoo", data_type="ohlcv")
        assert result["timestamp"] == 1700000000
        assert result["open"] == 100.0
        assert result["high"] == 105.0
        assert result["low"] == 99.0
        assert result["close"] == 103.0
        assert result["volume"] == 1000000


# ── AC-8: Quote field mappings ─────────────────────────────────────────────


class TestQuoteMappings:
    """AC-8: Quote field translation for each provider."""

    def test_generic_quote_identity(self) -> None:
        record = {
            "bid": 149.9,
            "ask": 150.1,
            "last": 150.0,
            "volume": 1000,
            "timestamp": "2026-01-15",
        }
        result = apply_field_mapping(
            record=record, provider="generic", data_type="quote"
        )
        assert result["bid"] == 149.9
        assert result["last"] == 150.0

    def test_yahoo_quote_mapping(self) -> None:
        record = {
            "regularMarketBid": 149.9,
            "regularMarketAsk": 150.1,
            "regularMarketPrice": 150.0,
            "regularMarketVolume": 1000,
        }
        result = apply_field_mapping(record=record, provider="yahoo", data_type="quote")
        assert result["bid"] == 149.9
        assert result["ask"] == 150.1
        assert result["last"] == 150.0
        assert result["volume"] == 1000

    def test_polygon_quote_mapping(self) -> None:
        record = {
            "bidPrice": 149.9,
            "askPrice": 150.1,
            "lastTrade": 150.0,
            "volume": 1000,
        }
        result = apply_field_mapping(
            record=record, provider="polygon", data_type="quote"
        )
        assert result["bid"] == 149.9
        assert result["ask"] == 150.1
        assert result["last"] == 150.0
        assert result["volume"] == 1000


# ── AC-8: News field mappings ──────────────────────────────────────────────


class TestNewsMappings:
    """AC-8: News field translation for each provider."""

    def test_generic_news_identity(self) -> None:
        record = {
            "headline": "Breaking news",
            "source": "Reuters",
            "url": "https://example.com",
            "published_at": "2026-01-15",
            "sentiment": 0.5,
        }
        result = apply_field_mapping(
            record=record, provider="generic", data_type="news"
        )
        assert result["headline"] == "Breaking news"
        assert result["source"] == "Reuters"

    def test_yahoo_news_mapping(self) -> None:
        record = {
            "title": "Breaking news",
            "publisher": "Reuters",
            "link": "https://example.com",
            "providerPublishTime": "2026-01-15",
        }
        result = apply_field_mapping(record=record, provider="yahoo", data_type="news")
        assert result["headline"] == "Breaking news"
        assert result["source"] == "Reuters"
        assert result["url"] == "https://example.com"
        assert result["published_at"] == "2026-01-15"

    def test_polygon_news_mapping(self) -> None:
        record = {
            "title": "Breaking news",
            "publisher": "Reuters",
            "article_url": "https://example.com",
            "published_utc": "2026-01-15T00:00:00Z",
        }
        result = apply_field_mapping(
            record=record, provider="polygon", data_type="news"
        )
        assert result["headline"] == "Breaking news"
        assert result["source"] == "Reuters"
        assert result["url"] == "https://example.com"
        assert result["published_at"] == "2026-01-15T00:00:00Z"


# ── AC-8: Fundamentals field mappings ──────────────────────────────────────


class TestFundamentalsMappings:
    """AC-8: Fundamentals field translation for each provider."""

    def test_generic_fundamentals_identity(self) -> None:
        record = {"metric": "pe_ratio", "value": 28.5, "period": "2026-Q1"}
        result = apply_field_mapping(
            record=record, provider="generic", data_type="fundamentals"
        )
        assert result["metric"] == "pe_ratio"
        assert result["value"] == 28.5

    def test_yahoo_fundamentals_mapping(self) -> None:
        record = {"shortName": "PE Ratio", "raw": 28.5, "fiscalQuarter": "2026-Q1"}
        result = apply_field_mapping(
            record=record, provider="yahoo", data_type="fundamentals"
        )
        assert result["metric"] == "PE Ratio"
        assert result["value"] == 28.5
        assert result["period"] == "2026-Q1"

    def test_polygon_fundamentals_mapping(self) -> None:
        record = {"label": "PE Ratio", "value": 28.5, "fiscal_period": "2026-Q1"}
        result = apply_field_mapping(
            record=record, provider="polygon", data_type="fundamentals"
        )
        assert result["metric"] == "PE Ratio"
        assert result["value"] == 28.5
        assert result["period"] == "2026-Q1"


# ── AC-8: Unmapped fields go to _extra ─────────────────────────────────────


class TestExtraFields:
    """AC-8: Fields not in mapping go to _extra dict."""

    def test_unmapped_fields_captured(self) -> None:
        record = {
            "regularMarketBid": 149.9,
            "regularMarketPrice": 150.0,
            "unknownField": "surprise",
        }
        result = apply_field_mapping(record=record, provider="yahoo", data_type="quote")
        assert "unknownField" in result["_extra"]
        assert result["_extra"]["unknownField"] == "surprise"


# ── AC-3: Provider slug normalization (MEU-PW12) ──────────────────────────


class TestProviderSlugNormalization:
    """AC-3: apply_field_mapping() normalizes provider display names to slugs
    via _PROVIDER_SLUG_MAP before FIELD_MAPPINGS lookup."""

    def test_yahoo_finance_display_name_normalized(self) -> None:
        """'Yahoo Finance' (display name) should map to 'yahoo' (slug)."""
        record = {
            "regularMarketBid": 149.9,
            "regularMarketPrice": 150.0,
        }
        result = apply_field_mapping(
            record=record, provider="Yahoo Finance", data_type="quote"
        )
        assert result["bid"] == 149.9
        assert result["last"] == 150.0

    def test_polygon_io_display_name_normalized(self) -> None:
        """'Polygon.io' (display name) should map to 'polygon' (slug)."""
        record = {
            "bidPrice": 149.9,
            "lastTrade": 150.0,
        }
        result = apply_field_mapping(
            record=record, provider="Polygon.io", data_type="quote"
        )
        assert result["bid"] == 149.9
        assert result["last"] == 150.0

    def test_existing_slug_still_works(self) -> None:
        """Existing slug-based calls must not regress."""
        record = {"regularMarketBid": 149.9}
        result = apply_field_mapping(record=record, provider="yahoo", data_type="quote")
        assert result["bid"] == 149.9

    def test_unknown_display_name_passthrough(self) -> None:
        """Unknown display name passes through unchanged (no mapping found)."""
        record = {"foo": "bar"}
        result = apply_field_mapping(
            record=record, provider="Unknown Provider", data_type="ohlcv"
        )
        assert result["_extra"] == {"foo": "bar"}

    def test_ibkr_display_name_normalized(self) -> None:
        """'Interactive Brokers' should map to 'ibkr'."""
        record = {
            "open": 100.0,
            "high": 110.0,
            "low": 95.0,
            "close": 105.0,
            "volume": 1000,
            "wap": 102.5,
        }
        result = apply_field_mapping(
            record=record, provider="Interactive Brokers", data_type="ohlcv"
        )
        assert result["open"] == 100.0
        assert result["vwap"] == 102.5


# ── AC-4: Extended Yahoo quote field mappings (MEU-PW12) ───────────────────


class TestExtendedYahooQuoteMappings:
    """AC-4: Yahoo quote mapping extended with change, change_pct, symbol→ticker."""

    def test_yahoo_change_field_mapped(self) -> None:
        """regularMarketChange → change."""
        record = {
            "regularMarketChange": 2.5,
            "regularMarketBid": 149.9,
        }
        result = apply_field_mapping(record=record, provider="yahoo", data_type="quote")
        assert result["change"] == 2.5

    def test_yahoo_change_pct_field_mapped(self) -> None:
        """regularMarketChangePercent → change_pct."""
        record = {
            "regularMarketChangePercent": 1.7,
            "regularMarketBid": 149.9,
        }
        result = apply_field_mapping(record=record, provider="yahoo", data_type="quote")
        assert result["change_pct"] == 1.7

    def test_yahoo_symbol_field_mapped_to_ticker(self) -> None:
        """symbol → ticker."""
        record = {
            "symbol": "AAPL",
            "regularMarketBid": 149.9,
        }
        result = apply_field_mapping(record=record, provider="yahoo", data_type="quote")
        assert result["ticker"] == "AAPL"

    def test_missing_extended_fields_still_maps_existing(self) -> None:
        """Records missing new fields still map remaining fields correctly."""
        record = {
            "regularMarketBid": 149.9,
            "regularMarketPrice": 150.0,
        }
        result = apply_field_mapping(record=record, provider="yahoo", data_type="quote")
        assert result["bid"] == 149.9
        assert result["last"] == 150.0
        # Extended fields simply not present — no crash
        assert "change" not in result


# ═══════════════════════════════════════════════════════════════════════════
# MEU-187: Standard Extractors — Slug Map + Field Mappings FIC
# ═══════════════════════════════════════════════════════════════════════════
#
# AC-18: FIELD_MAPPINGS extended with entries for 5 new providers
# AC-19: _PROVIDER_SLUG_MAP extended with 9 new provider display names


class TestProviderSlugMapMEU187:
    """AC-19: 9 new slug map entries for MEU-185/186/187 providers."""

    @pytest.mark.parametrize(
        "display_name,expected_slug",
        [
            ("Alpaca", "alpaca"),
            ("Financial Modeling Prep", "fmp"),
            ("EODHD", "eodhd"),
            ("API Ninjas", "api_ninjas"),
            ("Tradier", "tradier"),
            ("Alpha Vantage", "alpha_vantage"),
            ("Nasdaq Data Link", "nasdaq_dl"),
            ("OpenFIGI", "openfigi"),
            ("SEC API", "sec_api"),
        ],
    )
    def test_display_name_normalized(
        self, display_name: str, expected_slug: str
    ) -> None:
        """Display name resolves to correct slug via _PROVIDER_SLUG_MAP."""
        from zorivest_infra.market_data.field_mappings import _PROVIDER_SLUG_MAP

        assert _PROVIDER_SLUG_MAP.get(display_name) == expected_slug

    def test_existing_slug_map_not_broken(self) -> None:
        """Pre-existing slug map entries still work."""
        from zorivest_infra.market_data.field_mappings import _PROVIDER_SLUG_MAP

        assert _PROVIDER_SLUG_MAP["Yahoo Finance"] == "yahoo"
        assert _PROVIDER_SLUG_MAP["Polygon.io"] == "polygon"
        assert _PROVIDER_SLUG_MAP["Interactive Brokers"] == "ibkr"


class TestFieldMappingsMEU187:
    """AC-18: FIELD_MAPPINGS has entries for new providers."""

    @pytest.mark.parametrize(
        "provider,data_type",
        [
            # FMP mappings
            ("fmp", "quote"),
            ("fmp", "ohlcv"),
            # EODHD mappings
            ("eodhd", "ohlcv"),
            # Alpaca mappings
            ("alpaca", "quote"),
            ("alpaca", "ohlcv"),
            # Tradier mappings
            ("tradier", "quote"),
            ("tradier", "ohlcv"),
        ],
    )
    def test_provider_mapping_exists(self, provider: str, data_type: str) -> None:
        """FIELD_MAPPINGS has an entry for (provider, data_type)."""
        assert (provider, data_type) in FIELD_MAPPINGS

    def test_fmp_quote_mapping(self) -> None:
        """FMP quote maps price→last, changesPercentage→change_pct."""
        result = apply_field_mapping(
            record={
                "symbol": "AAPL",
                "price": 150.0,
                "changesPercentage": 1.5,
                "volume": 1000000,
            },
            provider="fmp",
            data_type="quote",
        )
        assert result["last"] == 150.0
        assert result["change_pct"] == 1.5
        assert result["ticker"] == "AAPL"

    def test_fmp_ohlcv_mapping(self) -> None:
        """FMP OHLCV maps date→timestamp."""
        result = apply_field_mapping(
            record={
                "date": "2024-01-01",
                "open": 150,
                "high": 155,
                "low": 149,
                "close": 153,
                "volume": 1000,
            },
            provider="fmp",
            data_type="ohlcv",
        )
        assert result["timestamp"] == "2024-01-01"
        assert result["open"] == 150

    def test_eodhd_ohlcv_mapping(self) -> None:
        """EODHD OHLCV maps date→timestamp, adjusted_close→adj_close."""
        result = apply_field_mapping(
            record={
                "date": "2024-01-01",
                "open": 150,
                "close": 153,
                "adjusted_close": 152.5,
                "volume": 1000,
            },
            provider="eodhd",
            data_type="ohlcv",
        )
        assert result["timestamp"] == "2024-01-01"
        assert result["adj_close"] == 152.5

    def test_alpaca_quote_mapping(self) -> None:
        """Alpaca snapshot maps p→last (from latestTrade)."""
        result = apply_field_mapping(
            record={"p": 150.5, "s": 100, "bp": 150.3, "ap": 150.7},
            provider="alpaca",
            data_type="quote",
        )
        assert result["last"] == 150.5

    def test_alpaca_ohlcv_mapping(self) -> None:
        """Alpaca bars maps o→open, h→high, l→low, c→close, v→volume, t→timestamp."""
        result = apply_field_mapping(
            record={
                "o": 150,
                "h": 155,
                "l": 149,
                "c": 153,
                "v": 1000,
                "t": "2024-01-01T00:00:00Z",
            },
            provider="alpaca",
            data_type="ohlcv",
        )
        assert result["open"] == 150
        assert result["high"] == 155
        assert result["close"] == 153
        assert result["volume"] == 1000
        assert result["timestamp"] == "2024-01-01T00:00:00Z"

    def test_tradier_quote_mapping(self) -> None:
        """Tradier quote maps last→last, bid→bid, ask→ask."""
        result = apply_field_mapping(
            record={
                "symbol": "AAPL",
                "last": 150.0,
                "bid": 149.9,
                "ask": 150.1,
                "volume": 1000000,
            },
            provider="tradier",
            data_type="quote",
        )
        assert result["last"] == 150.0
        assert result["ticker"] == "AAPL"

    def test_tradier_ohlcv_mapping(self) -> None:
        """Tradier OHLCV maps date→timestamp."""
        result = apply_field_mapping(
            record={
                "date": "2024-01-01",
                "open": 150,
                "high": 155,
                "low": 149,
                "close": 153,
                "volume": 1000,
            },
            provider="tradier",
            data_type="ohlcv",
        )
        assert result["timestamp"] == "2024-01-01"

    def test_slug_map_works_with_apply(self) -> None:
        """Display name 'Financial Modeling Prep' normalizes to 'fmp' in apply_field_mapping."""
        result = apply_field_mapping(
            record={"symbol": "AAPL", "price": 150.0, "volume": 1000000},
            provider="Financial Modeling Prep",
            data_type="quote",
        )
        assert result["last"] == 150.0
        assert result["ticker"] == "AAPL"


# ═══════════════════════════════════════════════════════════════════════════
# MEU-188: Complex Field Mappings — FIC (Feature Intent Contract)
# ═══════════════════════════════════════════════════════════════════════════
#
# AC-26: ~20 field mapping tuples for complex providers


class TestFieldMappingsMEU188:
    """AC-26: FIELD_MAPPINGS entries for complex providers."""

    @pytest.mark.parametrize(
        "provider,data_type",
        [
            ("alpha_vantage", "quote"),
            ("alpha_vantage", "ohlcv"),
            ("alpha_vantage", "earnings"),
            ("finnhub", "ohlcv"),
            ("nasdaq_dl", "fundamentals"),
        ],
    )
    def test_complex_provider_mapping_exists(
        self, provider: str, data_type: str
    ) -> None:
        """FIELD_MAPPINGS has an entry for complex (provider, data_type) pair."""
        assert (provider, data_type) in FIELD_MAPPINGS

    def test_alpha_vantage_ohlcv_mapping(self) -> None:
        """Alpha Vantage OHLCV maps stripped prefix fields."""
        result = apply_field_mapping(
            record={
                "date": "2024-01-01",
                "open": "150.00",
                "high": "155.00",
                "low": "149.00",
                "close": "153.00",
                "volume": "1000000",
            },
            provider="alpha_vantage",
            data_type="ohlcv",
        )
        assert result["timestamp"] == "2024-01-01"
        assert result["open"] == "150.00"

    def test_alpha_vantage_quote_mapping(self) -> None:
        """Alpha Vantage Global Quote maps stripped prefix fields."""
        result = apply_field_mapping(
            record={
                "symbol": "AAPL",
                "price": "153.00",
                "volume": "1000000",
                "change_percent": "1.5%",
            },
            provider="alpha_vantage",
            data_type="quote",
        )
        assert result["ticker"] == "AAPL"
        assert result["last"] == "153.00"

    def test_finnhub_ohlcv_mapping(self) -> None:
        """Finnhub candle OHLCV maps o→open, h→high, l→low, c→close, v→volume, t→timestamp."""
        result = apply_field_mapping(
            record={
                "o": 100.0,
                "h": 105.0,
                "l": 99.0,
                "c": 103.0,
                "v": 1000000,
                "t": 1700000000,
            },
            provider="finnhub",
            data_type="ohlcv",
        )
        assert result["open"] == 100.0
        assert result["high"] == 105.0
        assert result["close"] == 103.0
        assert result["volume"] == 1000000
        assert result["timestamp"] == 1700000000


# ═══════════════════════════════════════════════════════════════════════════
# F2/F3 Corrections: Missing field mapping functional tests
# ═══════════════════════════════════════════════════════════════════════════


class TestCorrectionsMappings:
    """F2/F3: Functional mapping tests for previously missing (provider, data_type) pairs."""

    def test_alpaca_news_mapping(self) -> None:
        record = {
            "headline": "Big news",
            "source": "Reuters",
            "url": "https://ex.com",
            "created_at": "2024-01-01",
        }
        result = apply_field_mapping(record=record, provider="alpaca", data_type="news")
        assert result["headline"] == "Big news"
        assert result["source"] == "Reuters"
        assert result["url"] == "https://ex.com"
        assert result["published_at"] == "2024-01-01"

    def test_fmp_earnings_mapping(self) -> None:
        record = {
            "date": "2024-01-15",
            "symbol": "AAPL",
            "eps": 2.1,
            "epsEstimated": 2.0,
            "revenue": 100000,
        }
        result = apply_field_mapping(
            record=record, provider="fmp", data_type="earnings"
        )
        assert result["date"] == "2024-01-15"
        assert result["ticker"] == "AAPL"
        assert result["eps"] == 2.1

    def test_fmp_dividends_mapping(self) -> None:
        record = {
            "date": "2024-01-15",
            "dividend": 0.24,
            "recordDate": "2024-01-10",
            "declarationDate": "2024-01-01",
        }
        result = apply_field_mapping(
            record=record, provider="fmp", data_type="dividends"
        )
        assert result["date"] == "2024-01-15"
        assert result["dividend"] == 0.24

    def test_fmp_news_mapping(self) -> None:
        record = {
            "title": "AAPL up",
            "site": "Reuters",
            "url": "https://ex.com",
            "publishedDate": "2024-01-15",
        }
        result = apply_field_mapping(record=record, provider="fmp", data_type="news")
        assert result["headline"] == "AAPL up"
        assert result["source"] == "Reuters"
        assert result["url"] == "https://ex.com"
        assert result["published_at"] == "2024-01-15"

    def test_fmp_fundamentals_mapping(self) -> None:
        record = {
            "date": "2024-01-15",
            "symbol": "AAPL",
            "revenue": 100000,
            "netIncome": 25000,
        }
        result = apply_field_mapping(
            record=record, provider="fmp", data_type="fundamentals"
        )
        assert result["date"] == "2024-01-15"
        assert result["ticker"] == "AAPL"
        assert result["revenue"] == 100000

    def test_fmp_splits_mapping(self) -> None:
        record = {
            "date": "2024-01-15",
            "label": "4:1",
            "numerator": 4,
            "denominator": 1,
        }
        result = apply_field_mapping(record=record, provider="fmp", data_type="splits")
        assert result["date"] == "2024-01-15"
        assert result["numerator"] == 4

    def test_eodhd_fundamentals_mapping(self) -> None:
        record = {
            "General.Code": "AAPL",
            "General.Name": "Apple",
            "Highlights.MarketCapitalization": 2800000,
        }
        result = apply_field_mapping(
            record=record, provider="eodhd", data_type="fundamentals"
        )
        assert result["General.Code"] == "AAPL"

    def test_eodhd_dividends_mapping(self) -> None:
        record = {"date": "2024-01-15", "value": 0.24}
        result = apply_field_mapping(
            record=record, provider="eodhd", data_type="dividends"
        )
        assert result["date"] == "2024-01-15"
        assert result["value"] == 0.24

    def test_eodhd_news_mapping(self) -> None:
        record = {"title": "AAPL up", "link": "https://ex.com", "date": "2024-01-15"}
        result = apply_field_mapping(record=record, provider="eodhd", data_type="news")
        assert result["headline"] == "AAPL up"
        assert result["url"] == "https://ex.com"
        assert result["published_at"] == "2024-01-15"

    def test_eodhd_splits_mapping(self) -> None:
        record = {"date": "2024-01-15", "split": "4:1"}
        result = apply_field_mapping(
            record=record, provider="eodhd", data_type="splits"
        )
        assert result["date"] == "2024-01-15"
        assert result["split"] == "4:1"

    def test_api_ninjas_quote_mapping(self) -> None:
        record = {
            "name": "Apple Inc",
            "price": 150.0,
            "exchange": "NASDAQ",
            "ticker": "AAPL",
        }
        result = apply_field_mapping(
            record=record, provider="api_ninjas", data_type="quote"
        )
        assert result["name"] == "Apple Inc"
        assert result["last"] == 150.0
        assert result["exchange"] == "NASDAQ"

    def test_api_ninjas_earnings_mapping(self) -> None:
        record = {
            "date": "2024-01-15",
            "ticker": "AAPL",
            "actual_eps": 2.1,
            "estimated_eps": 2.0,
        }
        result = apply_field_mapping(
            record=record, provider="api_ninjas", data_type="earnings"
        )
        assert result["date"] == "2024-01-15"
        assert result["actual_eps"] == 2.1

    def test_alpha_vantage_earnings_mapping(self) -> None:
        record = {
            "fiscalDateEnding": "2024-01-15",
            "reportedEPS": "2.10",
            "symbol": "AAPL",
        }
        result = apply_field_mapping(
            record=record, provider="alpha_vantage", data_type="earnings"
        )
        assert result["date"] == "2024-01-15"
        assert result["eps"] == "2.10"
        assert result["ticker"] == "AAPL"

    def test_nasdaq_dl_fundamentals_mapping(self) -> None:
        record = {
            "ticker": "AAPL",
            "pe": 28.5,
            "eps": 6.5,
            "calendardate": "2024-01-15",
        }
        result = apply_field_mapping(
            record=record, provider="nasdaq_dl", data_type="fundamentals"
        )
        assert result["ticker"] == "AAPL"
        assert result["pe"] == 28.5
        assert result["date"] == "2024-01-15"


# ═══════════════════════════════════════════════════════════════════════════
# TradingView Scanner Addendum — Field Mapping Tests
# ═══════════════════════════════════════════════════════════════════════════


class TestTradingViewMappings:
    """TradingView scanner field mappings — identity for canonical columns."""

    def test_tradingview_quote_mapping(self) -> None:
        record = {
            "close": 150.0,
            "volume": 1000000,
            "change": 2.5,
            "high": 155.0,
            "low": 149.0,
            "open": 148.0,
            "name": "Apple Inc",
        }
        result = apply_field_mapping(
            record=record, provider="tradingview", data_type="quote"
        )
        assert result["close"] == 150.0
        assert result["volume"] == 1000000
        assert result["name"] == "Apple Inc"

    def test_tradingview_fundamentals_mapping(self) -> None:
        record = {
            "market_cap_basic": 2800000000000,
            "earnings_per_share_basic_ttm": 6.5,
            "price_earnings_ttm": 28.5,
            "dividend_yield_indication": 0.5,
            "name": "Apple Inc",
        }
        result = apply_field_mapping(
            record=record, provider="tradingview", data_type="fundamentals"
        )
        assert result["market_cap"] == 2800000000000
        assert result["eps"] == 6.5
        assert result["pe_ratio"] == 28.5
        assert result["dividend_yield"] == 0.5
        assert result["name"] == "Apple Inc"
