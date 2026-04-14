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
