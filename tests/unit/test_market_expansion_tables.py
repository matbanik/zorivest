"""Tests for market expansion tables — MEU-183.

FIC-183 acceptance criteria:
AC-1: MarketEarningsModel with (ticker, fiscal_period, fiscal_year) unique constraint
AC-2: MarketDividendsModel with (ticker, ex_date) unique constraint
AC-3: MarketSplitsModel with (ticker, execution_date) unique constraint
AC-4: MarketInsiderModel with (ticker, name, transaction_date, transaction_code) unique constraint
AC-5: All 4 tables created via Base.metadata.create_all()
AC-6: Column types match DTO field types (Decimal→Numeric(18,8), date→Date, etc.)
AC-7: market_ohlcv table NOT duplicated (uses existing MarketOHLCVModel)
AC-8: Economic calendar events NOT persisted (transient — no table)
AC-9: All existing tests pass without modification
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import Date, Integer, Numeric, String, create_engine, inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from zorivest_infra.database.models import (
    Base,
    MarketDividendsModel,
    MarketEarningsModel,
    MarketInsiderModel,
    MarketOHLCVModel,
    MarketSplitsModel,
)


@pytest.fixture()
def engine():
    """In-memory SQLite engine with all tables created."""
    eng = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(eng)
    return eng


@pytest.fixture()
def session(engine):
    """Session bound to in-memory engine."""
    with Session(engine) as sess:
        yield sess


# ── AC-5: All 4 tables created via Base.metadata.create_all() ──────────


class TestTableCreation:
    """AC-5: All 4 new tables exist after create_all()."""

    def test_market_earnings_table_exists(self, engine) -> None:
        inspector = inspect(engine)
        assert "market_earnings" in inspector.get_table_names()

    def test_market_dividends_table_exists(self, engine) -> None:
        inspector = inspect(engine)
        assert "market_dividends" in inspector.get_table_names()

    def test_market_splits_table_exists(self, engine) -> None:
        inspector = inspect(engine)
        assert "market_splits" in inspector.get_table_names()

    def test_market_insider_table_exists(self, engine) -> None:
        inspector = inspect(engine)
        assert "market_insider" in inspector.get_table_names()


# ── AC-7: market_ohlcv NOT duplicated ──────────────────────────────────


class TestExistingTableNotDuplicated:
    """AC-7: market_ohlcv table uses existing MarketOHLCVModel."""

    def test_ohlcv_table_exists(self, engine) -> None:
        inspector = inspect(engine)
        assert "market_ohlcv" in inspector.get_table_names()

    def test_ohlcv_model_is_existing(self) -> None:
        """MarketOHLCVModel is the original — not duplicated."""
        assert MarketOHLCVModel.__tablename__ == "market_ohlcv"


# ── AC-8: No economic calendar table ───────────────────────────────────


class TestEconomicCalendarTransient:
    """AC-8: Economic calendar events are transient — no dedicated table."""

    def test_no_economic_calendar_table(self, engine) -> None:
        inspector = inspect(engine)
        assert "market_economic_calendar" not in inspector.get_table_names()
        assert "economic_calendar" not in inspector.get_table_names()


# ── AC-1: MarketEarningsModel ──────────────────────────────────────────


class TestMarketEarningsModel:
    """AC-1: MarketEarningsModel with unique constraint."""

    def test_insert_valid_row(self, session: Session) -> None:
        row = MarketEarningsModel(
            ticker="AAPL",
            fiscal_period="Q1",
            fiscal_year=2024,
            report_date=date(2024, 1, 25),
            eps_actual=Decimal("2.18"),
            eps_estimate=Decimal("2.10"),
            eps_surprise=Decimal("0.08"),
            revenue_actual=Decimal("119580000000"),
            revenue_estimate=Decimal("117900000000"),
            provider="Finnhub",
        )
        session.add(row)
        session.commit()
        assert row.id is not None

    def test_unique_constraint_violation(self, session: Session) -> None:
        """AC-1 negative: Duplicate (ticker, fiscal_period, fiscal_year) → IntegrityError."""
        row1 = MarketEarningsModel(
            ticker="AAPL",
            fiscal_period="Q1",
            fiscal_year=2024,
            report_date=date(2024, 1, 25),
            provider="Finnhub",
        )
        row2 = MarketEarningsModel(
            ticker="AAPL",
            fiscal_period="Q1",
            fiscal_year=2024,
            report_date=date(2024, 4, 25),
            provider="FMP",
        )
        session.add(row1)
        session.commit()
        session.add(row2)
        with pytest.raises(IntegrityError):
            session.commit()


# ── AC-2: MarketDividendsModel ─────────────────────────────────────────


class TestMarketDividendsModel:
    """AC-2: MarketDividendsModel with unique constraint."""

    def test_insert_valid_row(self, session: Session) -> None:
        row = MarketDividendsModel(
            ticker="AAPL",
            dividend_amount=Decimal("0.24"),
            currency="USD",
            ex_date=date(2024, 2, 9),
            record_date=date(2024, 2, 12),
            pay_date=date(2024, 2, 15),
            declaration_date=date(2024, 2, 1),
            frequency="quarterly",
            provider="Polygon",
        )
        session.add(row)
        session.commit()
        assert row.id is not None

    def test_unique_constraint_violation(self, session: Session) -> None:
        """AC-2 negative: Duplicate (ticker, ex_date) → IntegrityError."""
        row1 = MarketDividendsModel(
            ticker="AAPL",
            dividend_amount=Decimal("0.24"),
            currency="USD",
            ex_date=date(2024, 2, 9),
            provider="Polygon",
        )
        row2 = MarketDividendsModel(
            ticker="AAPL",
            dividend_amount=Decimal("0.25"),
            currency="USD",
            ex_date=date(2024, 2, 9),
            provider="EODHD",
        )
        session.add(row1)
        session.commit()
        session.add(row2)
        with pytest.raises(IntegrityError):
            session.commit()


# ── AC-3: MarketSplitsModel ───────────────────────────────────────────


class TestMarketSplitsModel:
    """AC-3: MarketSplitsModel with unique constraint."""

    def test_insert_valid_row(self, session: Session) -> None:
        row = MarketSplitsModel(
            ticker="AAPL",
            execution_date=date(2020, 8, 31),
            ratio_from=1,
            ratio_to=4,
            provider="EODHD",
        )
        session.add(row)
        session.commit()
        assert row.id is not None

    def test_unique_constraint_violation(self, session: Session) -> None:
        """AC-3 negative: Duplicate (ticker, execution_date) → IntegrityError."""
        row1 = MarketSplitsModel(
            ticker="AAPL",
            execution_date=date(2020, 8, 31),
            ratio_from=1,
            ratio_to=4,
            provider="EODHD",
        )
        row2 = MarketSplitsModel(
            ticker="AAPL",
            execution_date=date(2020, 8, 31),
            ratio_from=4,
            ratio_to=1,
            provider="Polygon",
        )
        session.add(row1)
        session.commit()
        session.add(row2)
        with pytest.raises(IntegrityError):
            session.commit()


# ── AC-4: MarketInsiderModel ──────────────────────────────────────────


class TestMarketInsiderModel:
    """AC-4: MarketInsiderModel with unique constraint."""

    def test_insert_valid_row(self, session: Session) -> None:
        row = MarketInsiderModel(
            ticker="AAPL",
            name="Tim Cook",
            title="CEO",
            transaction_date=date(2024, 3, 1),
            transaction_code="S",
            shares=50000,
            price=Decimal("175.50"),
            value=Decimal("8775000"),
            shares_owned_after=3_000_000,
            provider="Finnhub",
        )
        session.add(row)
        session.commit()
        assert row.id is not None

    def test_unique_constraint_violation(self, session: Session) -> None:
        """AC-4 negative: Duplicate (ticker, name, transaction_date, transaction_code) → IntegrityError."""
        kwargs = dict(
            ticker="AAPL",
            name="Tim Cook",
            transaction_date=date(2024, 3, 1),
            transaction_code="S",
            shares=50000,
            provider="Finnhub",
        )
        session.add(MarketInsiderModel(**kwargs))
        session.commit()
        session.add(MarketInsiderModel(**kwargs, price=Decimal("180")))
        with pytest.raises(IntegrityError):
            session.commit()


# ── AC-6: Column types match DTO field types ───────────────────────────


class TestColumnTypes:
    """AC-6: Column types match DTO field types."""

    def test_earnings_report_date_is_date(self) -> None:
        col = MarketEarningsModel.__table__.c.report_date
        assert isinstance(col.type, Date)

    def test_earnings_eps_actual_is_numeric(self) -> None:
        col = MarketEarningsModel.__table__.c.eps_actual
        assert isinstance(col.type, Numeric)

    def test_dividends_amount_is_numeric(self) -> None:
        col = MarketDividendsModel.__table__.c.dividend_amount
        assert isinstance(col.type, Numeric)

    def test_dividends_ex_date_is_date(self) -> None:
        col = MarketDividendsModel.__table__.c.ex_date
        assert isinstance(col.type, Date)

    def test_splits_ratio_from_is_integer(self) -> None:
        col = MarketSplitsModel.__table__.c.ratio_from
        assert isinstance(col.type, Integer)

    def test_splits_execution_date_is_date(self) -> None:
        col = MarketSplitsModel.__table__.c.execution_date
        assert isinstance(col.type, Date)

    def test_insider_shares_is_integer(self) -> None:
        col = MarketInsiderModel.__table__.c.shares
        assert isinstance(col.type, Integer)

    def test_insider_price_is_numeric(self) -> None:
        col = MarketInsiderModel.__table__.c.price
        assert isinstance(col.type, Numeric)

    def test_earnings_ticker_is_string(self) -> None:
        col = MarketEarningsModel.__table__.c.ticker
        assert isinstance(col.type, String)
