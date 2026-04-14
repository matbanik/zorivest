# tests/unit/test_validation_schemas.py
"""TDD Red-phase tests for Pandera validation schemas (MEU-PW3).

AC-4: QUOTE_SCHEMA, NEWS_SCHEMA, FUNDAMENTALS_SCHEMA defined with checks.
AC-5: SCHEMA_REGISTRY resolves all 4 data types.
AC-6: validate_dataframe() applies correct schema per schema_name.
"""

from __future__ import annotations

import pandas as pd
import pytest

from zorivest_core.services.validation_gate import (
    FUNDAMENTALS_SCHEMA,
    NEWS_SCHEMA,
    QUOTE_SCHEMA,
    SCHEMA_REGISTRY,
    validate_dataframe,
)


# ── AC-5: SCHEMA_REGISTRY coverage ────────────────────────────────────────


class TestSchemaRegistry:
    """AC-5: SCHEMA_REGISTRY resolves all 4 data types."""

    @pytest.mark.parametrize("key", ["ohlcv", "quote", "news", "fundamentals"])
    def test_registry_has_key(self, key: str) -> None:
        assert key in SCHEMA_REGISTRY

    def test_unknown_schema_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown schema"):
            validate_dataframe(pd.DataFrame(), schema_name="nonexistent")


# ── AC-4: QUOTE_SCHEMA ────────────────────────────────────────────────────


class TestQuoteSchema:
    """AC-4: QUOTE_SCHEMA validates quote data."""

    def test_valid_quote_passes(self) -> None:
        df = pd.DataFrame(
            [
                {
                    "ticker": "AAPL",
                    "last": 150.0,
                    "bid": 149.9,
                    "ask": 150.1,
                    "volume": 1000,
                    "timestamp": pd.Timestamp("2026-01-15 14:30:00"),
                    "provider": "yahoo",
                }
            ]
        )
        valid, quarantined = validate_dataframe(df, schema_name="quote")
        assert len(valid) == 1
        assert len(quarantined) == 0

    def test_negative_price_quarantined(self) -> None:
        df = pd.DataFrame(
            [
                {
                    "ticker": "AAPL",
                    "last": -5.0,  # Invalid: must be > 0
                    "timestamp": pd.Timestamp("2026-01-15 14:30:00"),
                    "provider": "yahoo",
                }
            ]
        )
        valid, quarantined = validate_dataframe(df, schema_name="quote")
        assert len(quarantined) == 1

    def test_missing_ticker_quarantined(self) -> None:
        df = pd.DataFrame(
            [
                {
                    "last": 150.0,
                    "timestamp": pd.Timestamp("2026-01-15 14:30:00"),
                    "provider": "yahoo",
                }
            ]
        )
        # Missing 'ticker' column — should fail schema validation
        valid, quarantined = validate_dataframe(df, schema_name="quote")
        assert len(quarantined) >= 1 or len(valid) == 0

    def test_extra_columns_pass_through(self) -> None:
        """strict=False allows extra columns."""
        df = pd.DataFrame(
            [
                {
                    "ticker": "AAPL",
                    "last": 150.0,
                    "timestamp": pd.Timestamp("2026-01-15 14:30:00"),
                    "provider": "yahoo",
                    "extra_field": "hello",
                }
            ]
        )
        valid, quarantined = validate_dataframe(df, schema_name="quote")
        assert len(valid) == 1
        assert "extra_field" in valid.columns

    def test_null_last_quarantined(self) -> None:
        """F1: last=None must be rejected (plan: not-null)."""
        df = pd.DataFrame(
            [
                {
                    "ticker": "AAPL",
                    "last": None,
                    "timestamp": pd.Timestamp("2026-01-15 14:30:00"),
                    "provider": "yahoo",
                }
            ]
        )
        valid, quarantined = validate_dataframe(df, schema_name="quote")
        assert len(quarantined) >= 1 or len(valid) == 0

    def test_missing_timestamp_quarantined(self) -> None:
        """F1: missing timestamp column must be rejected."""
        df = pd.DataFrame(
            [
                {
                    "ticker": "AAPL",
                    "last": 150.0,
                    "provider": "yahoo",
                }
            ]
        )
        valid, quarantined = validate_dataframe(df, schema_name="quote")
        assert len(quarantined) >= 1 or len(valid) == 0

    def test_missing_provider_quarantined(self) -> None:
        """F1: missing provider column must be rejected."""
        df = pd.DataFrame(
            [
                {
                    "ticker": "AAPL",
                    "last": 150.0,
                    "timestamp": pd.Timestamp("2026-01-15 14:30:00"),
                }
            ]
        )
        valid, quarantined = validate_dataframe(df, schema_name="quote")
        assert len(quarantined) >= 1 or len(valid) == 0


# ── AC-4: NEWS_SCHEMA ─────────────────────────────────────────────────────


class TestNewsSchema:
    """AC-4: NEWS_SCHEMA validates news articles."""

    def test_valid_news_passes(self) -> None:
        df = pd.DataFrame(
            [
                {
                    "headline": "AAPL hits $200",
                    "source": "Reuters",
                    "url": "https://reuters.com/article/1",
                    "published_at": pd.Timestamp("2026-01-15"),
                    "sentiment": 0.8,
                    "provider": "polygon",
                }
            ]
        )
        valid, quarantined = validate_dataframe(df, schema_name="news")
        assert len(valid) == 1

    def test_empty_headline_quarantined(self) -> None:
        df = pd.DataFrame(
            [
                {
                    "headline": "",  # Invalid: min_length=1
                    "source": "Reuters",
                    "url": "https://reuters.com/article/1",
                    "published_at": pd.Timestamp("2026-01-15"),
                    "provider": "polygon",
                }
            ]
        )
        valid, quarantined = validate_dataframe(df, schema_name="news")
        assert len(quarantined) >= 1

    def test_invalid_sentiment_out_of_range(self) -> None:
        df = pd.DataFrame(
            [
                {
                    "headline": "Breaking news",
                    "source": "Reuters",
                    "url": "https://reuters.com/article/2",
                    "published_at": pd.Timestamp("2026-01-15"),
                    "sentiment": 2.0,  # Invalid: must be in [-1, 1]
                    "provider": "polygon",
                }
            ]
        )
        valid, quarantined = validate_dataframe(df, schema_name="news")
        assert len(quarantined) >= 1

    def test_invalid_url_quarantined(self) -> None:
        df = pd.DataFrame(
            [
                {
                    "headline": "Breaking news",
                    "source": "Reuters",
                    "url": "not-a-url",  # Invalid: must start with http
                    "published_at": pd.Timestamp("2026-01-15"),
                    "provider": "polygon",
                }
            ]
        )
        valid, quarantined = validate_dataframe(df, schema_name="news")
        assert len(quarantined) >= 1

    def test_missing_published_at_quarantined(self) -> None:
        """F1: missing published_at column must be rejected."""
        df = pd.DataFrame(
            [
                {
                    "headline": "Breaking news",
                    "source": "Reuters",
                    "url": "https://reuters.com/article/3",
                    "provider": "polygon",
                }
            ]
        )
        valid, quarantined = validate_dataframe(df, schema_name="news")
        assert len(quarantined) >= 1 or len(valid) == 0


# ── AC-4: FUNDAMENTALS_SCHEMA ─────────────────────────────────────────────


class TestFundamentalsSchema:
    """AC-4: FUNDAMENTALS_SCHEMA validates fundamental metrics."""

    def test_valid_fundamentals_passes(self) -> None:
        df = pd.DataFrame(
            [
                {
                    "ticker": "AAPL",
                    "metric": "pe_ratio",
                    "value": 28.5,
                    "period": "2026-Q1",
                    "provider": "yahoo",
                }
            ]
        )
        valid, quarantined = validate_dataframe(df, schema_name="fundamentals")
        assert len(valid) == 1

    def test_invalid_period_format_quarantined(self) -> None:
        df = pd.DataFrame(
            [
                {
                    "ticker": "AAPL",
                    "metric": "pe_ratio",
                    "value": 28.5,
                    "period": "Q1-2026",  # Invalid: must match ^\d{4}-(Q[1-4]|FY|H[12])$
                    "provider": "yahoo",
                }
            ]
        )
        valid, quarantined = validate_dataframe(df, schema_name="fundamentals")
        assert len(quarantined) >= 1

    def test_fy_period_passes(self) -> None:
        df = pd.DataFrame(
            [
                {
                    "ticker": "MSFT",
                    "metric": "revenue",
                    "value": 1_000_000.0,
                    "period": "2025-FY",
                    "provider": "polygon",
                }
            ]
        )
        valid, quarantined = validate_dataframe(df, schema_name="fundamentals")
        assert len(valid) == 1

    def test_h1_period_passes(self) -> None:
        df = pd.DataFrame(
            [
                {
                    "ticker": "MSFT",
                    "metric": "revenue",
                    "value": 500_000.0,
                    "period": "2025-H1",
                    "provider": "polygon",
                }
            ]
        )
        valid, quarantined = validate_dataframe(df, schema_name="fundamentals")
        assert len(valid) == 1

    def test_null_value_quarantined(self) -> None:
        """F1: value=None must be rejected (plan: not-null)."""
        df = pd.DataFrame(
            [
                {
                    "ticker": "AAPL",
                    "metric": "pe_ratio",
                    "value": None,
                    "period": "2026-Q1",
                    "provider": "yahoo",
                }
            ]
        )
        valid, quarantined = validate_dataframe(df, schema_name="fundamentals")
        assert len(quarantined) >= 1 or len(valid) == 0


# ── AC-6: Cross-schema validation ─────────────────────────────────────────


class TestCrossSchemaValidation:
    """AC-6: validate_dataframe applies correct schema per name."""

    def test_quote_data_through_ohlcv_quarantines(self) -> None:
        """Quote data missing OHLCV required fields gets quarantined."""
        df = pd.DataFrame(
            [
                {
                    "ticker": "AAPL",
                    "last": 150.0,
                    "timestamp": pd.Timestamp("2026-01-15 14:30:00"),
                    "provider": "yahoo",
                }
            ]
        )
        valid, quarantined = validate_dataframe(df, schema_name="ohlcv")
        # Missing open/high/low/close/volume → all quarantined
        assert len(quarantined) >= 1


# ── Smoke test: schema objects are DataFrameSchema ─────────────────────────


class TestSchemaTypes:
    """Verify imported schema objects are Pandera DataFrameSchema instances."""

    def test_quote_schema_is_dataframe_schema(self) -> None:
        import pandera as pa

        assert isinstance(QUOTE_SCHEMA, pa.DataFrameSchema)

    def test_news_schema_is_dataframe_schema(self) -> None:
        import pandera as pa

        assert isinstance(NEWS_SCHEMA, pa.DataFrameSchema)

    def test_fundamentals_schema_is_dataframe_schema(self) -> None:
        import pandera as pa

        assert isinstance(FUNDAMENTALS_SCHEMA, pa.DataFrameSchema)
