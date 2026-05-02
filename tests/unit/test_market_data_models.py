# tests/unit/test_market_data_models.py
"""TDD Red-phase tests for market data ORM models (MEU-PW3).

AC-1: 4 SQLAlchemy models with proper column types, nullable constraints, indexes.
AC-2: UniqueConstraint prevents duplicate entries per natural key.
AC-3: Base.metadata.create_all() creates all 40 tables (31 + 4 market + 1 email_templates + 4 Phase 8a).
AC-9: TABLE_ALLOWLIST column sets are superset of ORM model columns.
"""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from zorivest_infra.database.models import (
    Base,
    MarketFundamentalsModel,
    MarketNewsModel,
    MarketOHLCVModel,
    MarketQuoteModel,
)
from zorivest_infra.repositories.write_dispositions import TABLE_ALLOWLIST


# ── Helpers ────────────────────────────────────────────────────────────────


def _engine():
    """Create a fresh in-memory SQLite engine with all tables."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


def _session(engine) -> Session:
    return Session(bind=engine)


# ── AC-3: Table count ──────────────────────────────────────────────────────


class TestTableCount:
    """AC-3: 40 tables exist after create_all (36 pre-8a + 4 Phase 8a market)."""

    def test_market_ohlcv_table_exists(self) -> None:
        engine = _engine()
        tables = inspect(engine).get_table_names()
        assert "market_ohlcv" in tables

    def test_market_quotes_table_exists(self) -> None:
        engine = _engine()
        tables = inspect(engine).get_table_names()
        assert "market_quotes" in tables

    def test_market_news_table_exists(self) -> None:
        engine = _engine()
        tables = inspect(engine).get_table_names()
        assert "market_news" in tables

    def test_market_fundamentals_table_exists(self) -> None:
        engine = _engine()
        tables = inspect(engine).get_table_names()
        assert "market_fundamentals" in tables

    def test_total_table_count_is_40(self) -> None:
        engine = _engine()
        tables = inspect(engine).get_table_names()
        assert len(tables) == 40


# ── AC-1: Column types and constraints ─────────────────────────────────────


class TestOHLCVModel:
    """AC-1: MarketOHLCVModel columns, types, indexes."""

    def test_has_required_columns(self) -> None:
        engine = _engine()
        cols = {c["name"] for c in inspect(engine).get_columns("market_ohlcv")}
        expected = {
            "id",
            "ticker",
            "timestamp",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "vwap",
            "trade_count",
            "adjusted_close",
            "provider",
            "data_type",
            "fetched_at",
        }
        assert expected.issubset(cols)

    def test_nullable_constraints(self) -> None:
        """Non-nullable fields must reject NULL."""
        engine = _engine()
        session = _session(engine)
        row = MarketOHLCVModel(
            ticker="AAPL",
            timestamp=None,  # Not-null field
            open=100.0,
            high=105.0,
            low=99.0,
            close=103.0,
            volume=1000,
            provider="test",
        )
        session.add(row)
        with pytest.raises(IntegrityError):
            session.flush()

    def test_insert_valid_row(self) -> None:
        """Valid row inserts without error."""
        from datetime import datetime

        engine = _engine()
        session = _session(engine)
        row = MarketOHLCVModel(
            ticker="AAPL",
            timestamp=datetime(2026, 1, 15),
            open=100.0,
            high=105.0,
            low=99.0,
            close=103.0,
            volume=1000,
            provider="polygon",
        )
        session.add(row)
        session.flush()
        assert row.id is not None

    def test_has_composite_index(self) -> None:
        engine = _engine()
        indexes = inspect(engine).get_indexes("market_ohlcv")
        idx_names = {idx["name"] for idx in indexes}
        assert "ix_ohlcv_ticker_timestamp" in idx_names


class TestQuoteModel:
    """AC-1: MarketQuoteModel columns and indexes."""

    def test_has_required_columns(self) -> None:
        engine = _engine()
        cols = {c["name"] for c in inspect(engine).get_columns("market_quotes")}
        expected = {
            "id",
            "ticker",
            "bid",
            "ask",
            "last",
            "volume",
            "timestamp",
            "provider",
        }
        assert expected.issubset(cols)

    def test_insert_valid_row(self) -> None:
        from datetime import datetime

        engine = _engine()
        session = _session(engine)
        row = MarketQuoteModel(
            ticker="MSFT",
            last=350.0,
            timestamp=datetime(2026, 1, 15, 14, 30),
            provider="yahoo",
        )
        session.add(row)
        session.flush()
        assert row.id is not None

    def test_has_composite_index(self) -> None:
        engine = _engine()
        indexes = inspect(engine).get_indexes("market_quotes")
        idx_names = {idx["name"] for idx in indexes}
        assert "ix_quote_ticker_timestamp" in idx_names

    def test_null_last_raises(self) -> None:
        """F1f: last=None must raise IntegrityError (plan: not-null)."""
        from datetime import datetime

        engine = _engine()
        session = _session(engine)
        row = MarketQuoteModel(
            ticker="AAPL",
            last=None,  # Not-null field
            timestamp=datetime(2026, 1, 15, 14, 30),
            provider="yahoo",
        )
        session.add(row)
        with pytest.raises(IntegrityError):
            session.flush()


class TestNewsModel:
    """AC-1: MarketNewsModel columns and indexes."""

    def test_has_required_columns(self) -> None:
        engine = _engine()
        cols = {c["name"] for c in inspect(engine).get_columns("market_news")}
        expected = {
            "id",
            "ticker",
            "headline",
            "summary",
            "source",
            "url",
            "published_at",
            "sentiment",
            "provider",
        }
        assert expected.issubset(cols)

    def test_insert_valid_row(self) -> None:
        from datetime import datetime

        engine = _engine()
        session = _session(engine)
        row = MarketNewsModel(
            headline="AAPL hits $200",
            source="Reuters",
            url="https://reuters.com/article/1",
            published_at=datetime(2026, 1, 15),
            provider="polygon",
        )
        session.add(row)
        session.flush()
        assert row.id is not None

    def test_has_composite_index(self) -> None:
        engine = _engine()
        indexes = inspect(engine).get_indexes("market_news")
        idx_names = {idx["name"] for idx in indexes}
        assert "ix_news_ticker_published" in idx_names


class TestFundamentalsModel:
    """AC-1: MarketFundamentalsModel columns and indexes."""

    def test_has_required_columns(self) -> None:
        engine = _engine()
        cols = {c["name"] for c in inspect(engine).get_columns("market_fundamentals")}
        expected = {
            "id",
            "ticker",
            "metric",
            "value",
            "period",
            "provider",
            "fetched_at",
        }
        assert expected.issubset(cols)

    def test_insert_valid_row(self) -> None:
        engine = _engine()
        session = _session(engine)
        row = MarketFundamentalsModel(
            ticker="AAPL",
            metric="pe_ratio",
            value=28.5,
            period="2026-Q1",
            provider="yahoo",
        )
        session.add(row)
        session.flush()
        assert row.id is not None

    def test_has_composite_index(self) -> None:
        engine = _engine()
        indexes = inspect(engine).get_indexes("market_fundamentals")
        idx_names = {idx["name"] for idx in indexes}
        assert "ix_fund_ticker_metric" in idx_names

    def test_null_value_raises(self) -> None:
        """F1f: value=None must raise IntegrityError (plan: not-null)."""
        engine = _engine()
        session = _session(engine)
        row = MarketFundamentalsModel(
            ticker="AAPL",
            metric="pe_ratio",
            value=None,  # Not-null field
            period="2026-Q1",
            provider="yahoo",
        )
        session.add(row)
        with pytest.raises(IntegrityError):
            session.flush()


# ── AC-2: UniqueConstraint enforcement ─────────────────────────────────────


class TestUniqueConstraints:
    """AC-2: Duplicate natural keys raise IntegrityError."""

    def test_ohlcv_duplicate_raises(self) -> None:
        from datetime import datetime

        engine = _engine()
        session = _session(engine)
        ts = datetime(2026, 1, 15)
        row1 = MarketOHLCVModel(
            ticker="AAPL",
            timestamp=ts,
            open=100.0,
            high=105.0,
            low=99.0,
            close=103.0,
            volume=1000,
            provider="polygon",
        )
        row2 = MarketOHLCVModel(
            ticker="AAPL",
            timestamp=ts,
            open=101.0,
            high=106.0,
            low=100.0,
            close=104.0,
            volume=2000,
            provider="polygon",
        )
        session.add(row1)
        session.flush()
        session.add(row2)
        with pytest.raises(IntegrityError):
            session.flush()

    def test_quote_duplicate_snapshot_allowed(self) -> None:
        """F2: Quotes are append-only snapshots — duplicates must NOT raise."""
        from datetime import datetime

        engine = _engine()
        session = _session(engine)
        ts = datetime(2026, 1, 15, 14, 30)
        row1 = MarketQuoteModel(
            ticker="AAPL",
            last=150.0,
            timestamp=ts,
            provider="polygon",
        )
        row2 = MarketQuoteModel(
            ticker="AAPL",
            last=151.0,
            timestamp=ts,
            provider="polygon",
        )
        session.add(row1)
        session.flush()
        session.add(row2)
        session.flush()  # No IntegrityError — append-only
        count = session.query(MarketQuoteModel).filter_by(ticker="AAPL").count()
        assert count == 2

    def test_news_duplicate_url_provider_raises(self) -> None:
        from datetime import datetime

        engine = _engine()
        session = _session(engine)
        row1 = MarketNewsModel(
            headline="Title 1",
            source="Reuters",
            url="https://example.com/1",
            published_at=datetime(2026, 1, 15),
            provider="polygon",
        )
        row2 = MarketNewsModel(
            headline="Title 2",
            source="Bloomberg",
            url="https://example.com/1",
            published_at=datetime(2026, 1, 16),
            provider="polygon",
        )
        session.add(row1)
        session.flush()
        session.add(row2)
        with pytest.raises(IntegrityError):
            session.flush()

    def test_fundamentals_duplicate_raises(self) -> None:
        engine = _engine()
        session = _session(engine)
        row1 = MarketFundamentalsModel(
            ticker="AAPL",
            metric="pe_ratio",
            value=28.5,
            period="2026-Q1",
            provider="yahoo",
        )
        row2 = MarketFundamentalsModel(
            ticker="AAPL",
            metric="pe_ratio",
            value=30.0,
            period="2026-Q1",
            provider="yahoo",
        )
        session.add(row1)
        session.flush()
        session.add(row2)
        with pytest.raises(IntegrityError):
            session.flush()


# ── AC-9: TABLE_ALLOWLIST superset check ───────────────────────────────────


class TestAllowlistSync:
    """AC-9: TABLE_ALLOWLIST is superset of ORM model column names."""

    @pytest.mark.parametrize(
        "table_name,model_class",
        [
            ("market_ohlcv", MarketOHLCVModel),
            ("market_quotes", MarketQuoteModel),
            ("market_news", MarketNewsModel),
            ("market_fundamentals", MarketFundamentalsModel),
        ],
    )
    def test_allowlist_is_superset_of_model(self, table_name: str, model_class) -> None:
        """Allowlist columns must include all non-id ORM columns."""
        model_cols = {c.name for c in model_class.__table__.columns if c.name != "id"}
        allowlist_cols = TABLE_ALLOWLIST[table_name]
        missing = model_cols - allowlist_cols
        assert not missing, f"Missing from allowlist: {missing}"
