"""Tests for market expansion DTOs — MEU-182.

FIC-182 acceptance criteria:
AC-1: OHLCVBar frozen dataclass with 11 fields
AC-2: FundamentalsSnapshot frozen dataclass with 13 fields
AC-3: EarningsReport frozen dataclass with 10 fields
AC-4: DividendRecord frozen dataclass with 9 fields
AC-5: StockSplit frozen dataclass with 5 fields
AC-6: InsiderTransaction frozen dataclass with 10 fields
AC-7: EconomicCalendarEvent frozen dataclass with 9 fields
AC-8: All 7 DTOs constructed with valid data without error
AC-9: MarketDataPort extended with 8 new async method signatures
AC-10: All new DTOs importable from market_expansion_dtos module
"""

from __future__ import annotations

import dataclasses
from datetime import date, datetime, time, timezone
from decimal import Decimal

import pytest

from zorivest_core.application.market_expansion_dtos import (
    DividendRecord,
    EarningsReport,
    EconomicCalendarEvent,
    FundamentalsSnapshot,
    InsiderTransaction,
    OHLCVBar,
    StockSplit,
)
from zorivest_core.application.ports import MarketDataPort


# ── Fixtures ────────────────────────────────────────────────────────────


@pytest.fixture()
def ohlcv_bar() -> OHLCVBar:
    """Valid OHLCVBar instance."""
    return OHLCVBar(
        ticker="AAPL",
        timestamp=datetime(2024, 3, 8, 16, 0, tzinfo=timezone.utc),
        open=Decimal("170.00"),
        high=Decimal("172.50"),
        low=Decimal("169.00"),
        close=Decimal("171.25"),
        adj_close=Decimal("171.25"),
        volume=50_000_000,
        vwap=Decimal("170.80"),
        trade_count=125_000,
        provider="Alpaca",
    )


@pytest.fixture()
def fundamentals_snapshot() -> FundamentalsSnapshot:
    """Valid FundamentalsSnapshot instance."""
    return FundamentalsSnapshot(
        ticker="AAPL",
        market_cap=Decimal("2800000000000"),
        pe_ratio=Decimal("28.5"),
        pb_ratio=Decimal("45.2"),
        ps_ratio=Decimal("7.8"),
        eps=Decimal("6.42"),
        dividend_yield=Decimal("0.55"),
        beta=Decimal("1.25"),
        sector="Technology",
        industry="Consumer Electronics",
        employees=164000,
        provider="FMP",
        timestamp=datetime(2024, 3, 8, 16, 0, tzinfo=timezone.utc),
    )


@pytest.fixture()
def earnings_report() -> EarningsReport:
    """Valid EarningsReport instance."""
    return EarningsReport(
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


@pytest.fixture()
def dividend_record() -> DividendRecord:
    """Valid DividendRecord instance."""
    return DividendRecord(
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


@pytest.fixture()
def stock_split() -> StockSplit:
    """Valid StockSplit instance."""
    return StockSplit(
        ticker="AAPL",
        execution_date=date(2020, 8, 31),
        ratio_from=1,
        ratio_to=4,
        provider="EODHD",
    )


@pytest.fixture()
def insider_transaction() -> InsiderTransaction:
    """Valid InsiderTransaction instance."""
    return InsiderTransaction(
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


@pytest.fixture()
def economic_calendar_event() -> EconomicCalendarEvent:
    """Valid EconomicCalendarEvent instance."""
    return EconomicCalendarEvent(
        event="Non-Farm Payrolls",
        country="US",
        date=date(2024, 3, 8),
        time=time(8, 30),
        impact="high",
        actual="275K",
        forecast="200K",
        previous="229K",
        provider="Finnhub",
    )


# ── AC-1: OHLCVBar ─────────────────────────────────────────────────────


class TestOHLCVBar:
    """AC-1: OHLCVBar frozen dataclass with 11 fields."""

    def test_construction(self, ohlcv_bar: OHLCVBar) -> None:
        """AC-8: Construction succeeds with valid data."""
        assert ohlcv_bar.ticker == "AAPL"
        assert ohlcv_bar.open == Decimal("170.00")
        assert ohlcv_bar.volume == 50_000_000
        assert ohlcv_bar.provider == "Alpaca"

    def test_field_count(self) -> None:
        """AC-1: Exactly 11 fields."""
        fields = dataclasses.fields(OHLCVBar)
        assert len(fields) == 11

    def test_field_names(self) -> None:
        """AC-1: Field names match spec."""
        field_names = {f.name for f in dataclasses.fields(OHLCVBar)}
        expected = {
            "ticker",
            "timestamp",
            "open",
            "high",
            "low",
            "close",
            "adj_close",
            "volume",
            "vwap",
            "trade_count",
            "provider",
        }
        assert field_names == expected

    def test_frozen(self, ohlcv_bar: OHLCVBar) -> None:
        """AC-1 negative: FrozenInstanceError on attribute assignment."""
        with pytest.raises(dataclasses.FrozenInstanceError):
            ohlcv_bar.ticker = "MSFT"  # type: ignore[misc]

    def test_is_dataclass(self) -> None:
        """AC-1: Must be a dataclass."""
        assert dataclasses.is_dataclass(OHLCVBar)


# ── AC-2: FundamentalsSnapshot ──────────────────────────────────────────


class TestFundamentalsSnapshot:
    """AC-2: FundamentalsSnapshot frozen dataclass with 13 fields."""

    def test_construction(self, fundamentals_snapshot: FundamentalsSnapshot) -> None:
        """AC-8: Construction succeeds with valid data."""
        assert fundamentals_snapshot.ticker == "AAPL"
        assert fundamentals_snapshot.pe_ratio == Decimal("28.5")
        assert fundamentals_snapshot.sector == "Technology"

    def test_field_count(self) -> None:
        """AC-2: Exactly 13 fields."""
        fields = dataclasses.fields(FundamentalsSnapshot)
        assert len(fields) == 13

    def test_field_names(self) -> None:
        """AC-2: Field names match spec."""
        field_names = {f.name for f in dataclasses.fields(FundamentalsSnapshot)}
        expected = {
            "ticker",
            "market_cap",
            "pe_ratio",
            "pb_ratio",
            "ps_ratio",
            "eps",
            "dividend_yield",
            "beta",
            "sector",
            "industry",
            "employees",
            "provider",
            "timestamp",
        }
        assert field_names == expected

    def test_frozen(self, fundamentals_snapshot: FundamentalsSnapshot) -> None:
        """AC-2 negative: FrozenInstanceError on attribute assignment."""
        with pytest.raises(dataclasses.FrozenInstanceError):
            fundamentals_snapshot.ticker = "MSFT"  # type: ignore[misc]

    def test_optional_fields(self) -> None:
        """AC-2: Optional fields accept None."""
        snap = FundamentalsSnapshot(
            ticker="AAPL",
            market_cap=None,
            pe_ratio=None,
            pb_ratio=None,
            ps_ratio=None,
            eps=None,
            dividend_yield=None,
            beta=None,
            sector=None,
            industry=None,
            employees=None,
            provider="FMP",
            timestamp=datetime(2024, 3, 8, tzinfo=timezone.utc),
        )
        assert snap.market_cap is None
        assert snap.employees is None


# ── AC-3: EarningsReport ────────────────────────────────────────────────


class TestEarningsReport:
    """AC-3: EarningsReport frozen dataclass with 10 fields."""

    def test_construction(self, earnings_report: EarningsReport) -> None:
        """AC-8: Construction succeeds with valid data."""
        assert earnings_report.ticker == "AAPL"
        assert earnings_report.fiscal_period == "Q1"
        assert earnings_report.eps_actual == Decimal("2.18")

    def test_field_count(self) -> None:
        """AC-3: Exactly 10 fields."""
        fields = dataclasses.fields(EarningsReport)
        assert len(fields) == 10

    def test_field_names(self) -> None:
        """AC-3: Field names match spec."""
        field_names = {f.name for f in dataclasses.fields(EarningsReport)}
        expected = {
            "ticker",
            "fiscal_period",
            "fiscal_year",
            "report_date",
            "eps_actual",
            "eps_estimate",
            "eps_surprise",
            "revenue_actual",
            "revenue_estimate",
            "provider",
        }
        assert field_names == expected

    def test_frozen(self, earnings_report: EarningsReport) -> None:
        """AC-3 negative: FrozenInstanceError on attribute assignment."""
        with pytest.raises(dataclasses.FrozenInstanceError):
            earnings_report.ticker = "MSFT"  # type: ignore[misc]


# ── AC-4: DividendRecord ───────────────────────────────────────────────


class TestDividendRecord:
    """AC-4: DividendRecord frozen dataclass with 9 fields."""

    def test_construction(self, dividend_record: DividendRecord) -> None:
        """AC-8: Construction succeeds with valid data."""
        assert dividend_record.ticker == "AAPL"
        assert dividend_record.dividend_amount == Decimal("0.24")
        assert dividend_record.frequency == "quarterly"

    def test_field_count(self) -> None:
        """AC-4: Exactly 9 fields."""
        fields = dataclasses.fields(DividendRecord)
        assert len(fields) == 9

    def test_field_names(self) -> None:
        """AC-4: Field names match spec."""
        field_names = {f.name for f in dataclasses.fields(DividendRecord)}
        expected = {
            "ticker",
            "dividend_amount",
            "currency",
            "ex_date",
            "record_date",
            "pay_date",
            "declaration_date",
            "frequency",
            "provider",
        }
        assert field_names == expected

    def test_frozen(self, dividend_record: DividendRecord) -> None:
        """AC-4 negative: FrozenInstanceError on attribute assignment."""
        with pytest.raises(dataclasses.FrozenInstanceError):
            dividend_record.ticker = "MSFT"  # type: ignore[misc]


# ── AC-5: StockSplit ────────────────────────────────────────────────────


class TestStockSplit:
    """AC-5: StockSplit frozen dataclass with 5 fields."""

    def test_construction(self, stock_split: StockSplit) -> None:
        """AC-8: Construction succeeds with valid data."""
        assert stock_split.ticker == "AAPL"
        assert stock_split.ratio_from == 1
        assert stock_split.ratio_to == 4

    def test_field_count(self) -> None:
        """AC-5: Exactly 5 fields."""
        fields = dataclasses.fields(StockSplit)
        assert len(fields) == 5

    def test_field_names(self) -> None:
        """AC-5: Field names match spec."""
        field_names = {f.name for f in dataclasses.fields(StockSplit)}
        expected = {"ticker", "execution_date", "ratio_from", "ratio_to", "provider"}
        assert field_names == expected

    def test_frozen(self, stock_split: StockSplit) -> None:
        """AC-5 negative: FrozenInstanceError on attribute assignment."""
        with pytest.raises(dataclasses.FrozenInstanceError):
            stock_split.ticker = "MSFT"  # type: ignore[misc]


# ── AC-6: InsiderTransaction ───────────────────────────────────────────


class TestInsiderTransaction:
    """AC-6: InsiderTransaction frozen dataclass with 10 fields."""

    def test_construction(self, insider_transaction: InsiderTransaction) -> None:
        """AC-8: Construction succeeds with valid data."""
        assert insider_transaction.ticker == "AAPL"
        assert insider_transaction.name == "Tim Cook"
        assert insider_transaction.shares == 50000

    def test_field_count(self) -> None:
        """AC-6: Exactly 10 fields."""
        fields = dataclasses.fields(InsiderTransaction)
        assert len(fields) == 10

    def test_field_names(self) -> None:
        """AC-6: Field names match spec."""
        field_names = {f.name for f in dataclasses.fields(InsiderTransaction)}
        expected = {
            "ticker",
            "name",
            "title",
            "transaction_date",
            "transaction_code",
            "shares",
            "price",
            "value",
            "shares_owned_after",
            "provider",
        }
        assert field_names == expected

    def test_frozen(self, insider_transaction: InsiderTransaction) -> None:
        """AC-6 negative: FrozenInstanceError on attribute assignment."""
        with pytest.raises(dataclasses.FrozenInstanceError):
            insider_transaction.ticker = "MSFT"  # type: ignore[misc]


# ── AC-7: EconomicCalendarEvent ─────────────────────────────────────────


class TestEconomicCalendarEvent:
    """AC-7: EconomicCalendarEvent frozen dataclass with 9 fields."""

    def test_construction(self, economic_calendar_event: EconomicCalendarEvent) -> None:
        """AC-8: Construction succeeds with valid data."""
        assert economic_calendar_event.event == "Non-Farm Payrolls"
        assert economic_calendar_event.country == "US"
        assert economic_calendar_event.impact == "high"

    def test_field_count(self) -> None:
        """AC-7: Exactly 9 fields."""
        fields = dataclasses.fields(EconomicCalendarEvent)
        assert len(fields) == 9

    def test_field_names(self) -> None:
        """AC-7: Field names match spec."""
        field_names = {f.name for f in dataclasses.fields(EconomicCalendarEvent)}
        expected = {
            "event",
            "country",
            "date",
            "time",
            "impact",
            "actual",
            "forecast",
            "previous",
            "provider",
        }
        assert field_names == expected

    def test_frozen(self, economic_calendar_event: EconomicCalendarEvent) -> None:
        """AC-7 negative: FrozenInstanceError on attribute assignment."""
        with pytest.raises(dataclasses.FrozenInstanceError):
            economic_calendar_event.event = "CPI"  # type: ignore[misc]


# ── AC-8: Missing required fields → TypeError ──────────────────────────


class TestRequiredFieldEnforcement:
    """AC-8 negative: Missing required field → TypeError."""

    def test_ohlcv_bar_missing_ticker(self) -> None:
        with pytest.raises(TypeError):
            OHLCVBar(  # type: ignore[call-arg]
                timestamp=datetime(2024, 3, 8, tzinfo=timezone.utc),
                open=Decimal("170.00"),
                high=Decimal("172.50"),
                low=Decimal("169.00"),
                close=Decimal("171.25"),
                adj_close=None,
                volume=50_000_000,
                vwap=None,
                trade_count=None,
                provider="Alpaca",
            )

    def test_stock_split_missing_provider(self) -> None:
        with pytest.raises(TypeError):
            StockSplit(  # type: ignore[call-arg]
                ticker="AAPL",
                execution_date=date(2020, 8, 31),
                ratio_from=1,
                ratio_to=4,
            )

    def test_earnings_report_missing_fiscal_year(self) -> None:
        with pytest.raises(TypeError):
            EarningsReport(  # type: ignore[call-arg]
                ticker="AAPL",
                fiscal_period="Q1",
                report_date=date(2024, 1, 25),
                eps_actual=None,
                eps_estimate=None,
                eps_surprise=None,
                revenue_actual=None,
                revenue_estimate=None,
                provider="Finnhub",
            )


# ── AC-9: MarketDataPort extended with 8 new methods ───────────────────


class TestMarketDataPortExtension:
    """AC-9: MarketDataPort extended with 8 new async method signatures."""

    def test_port_has_get_ohlcv(self) -> None:
        assert hasattr(MarketDataPort, "get_ohlcv")

    def test_port_has_get_fundamentals(self) -> None:
        assert hasattr(MarketDataPort, "get_fundamentals")

    def test_port_has_get_earnings(self) -> None:
        assert hasattr(MarketDataPort, "get_earnings")

    def test_port_has_get_dividends(self) -> None:
        assert hasattr(MarketDataPort, "get_dividends")

    def test_port_has_get_splits(self) -> None:
        assert hasattr(MarketDataPort, "get_splits")

    def test_port_has_get_insider(self) -> None:
        assert hasattr(MarketDataPort, "get_insider")

    def test_port_has_get_economic_calendar(self) -> None:
        assert hasattr(MarketDataPort, "get_economic_calendar")

    def test_port_has_get_company_profile(self) -> None:
        assert hasattr(MarketDataPort, "get_company_profile")

    def test_existing_methods_preserved(self) -> None:
        """Existing Phase 8 methods must not be removed."""
        assert hasattr(MarketDataPort, "get_quote")
        assert hasattr(MarketDataPort, "get_news")
        assert hasattr(MarketDataPort, "search_ticker")
        assert hasattr(MarketDataPort, "get_sec_filings")


# ── AC-10: All DTOs importable ──────────────────────────────────────────


class TestModuleImportability:
    """AC-10: All new DTOs importable from market_expansion_dtos module."""

    def test_all_dtos_importable(self) -> None:
        """All 7 DTOs are importable."""
        # If imports at module top fail, this file won't even load.
        # This test serves as explicit documentation.
        assert OHLCVBar is not None
        assert FundamentalsSnapshot is not None
        assert EarningsReport is not None
        assert DividendRecord is not None
        assert StockSplit is not None
        assert InsiderTransaction is not None
        assert EconomicCalendarEvent is not None
