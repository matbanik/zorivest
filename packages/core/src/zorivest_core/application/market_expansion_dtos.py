"""Market expansion DTOs — MEU-182.

7 frozen dataclass DTOs for Phase 8a market data expansion.
These are internal data carriers, not API response models,
so they use frozen dataclasses instead of Pydantic BaseModel.

Source: docs/build-plan/08a-market-data-expansion.md §8a.1
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time
from decimal import Decimal


@dataclass(frozen=True)
class OHLCVBar:
    """OHLCV candlestick bar."""

    ticker: str
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    adj_close: Decimal | None
    volume: int
    vwap: Decimal | None
    trade_count: int | None
    provider: str


@dataclass(frozen=True)
class FundamentalsSnapshot:
    """Company fundamentals at a point in time."""

    ticker: str
    market_cap: Decimal | None
    pe_ratio: Decimal | None
    pb_ratio: Decimal | None
    ps_ratio: Decimal | None
    eps: Decimal | None
    dividend_yield: Decimal | None
    beta: Decimal | None
    sector: str | None
    industry: str | None
    employees: int | None
    provider: str
    timestamp: datetime


@dataclass(frozen=True)
class EarningsReport:
    """Quarterly or annual earnings report."""

    ticker: str
    fiscal_period: str  # Q1, Q2, Q3, Q4, FY
    fiscal_year: int
    report_date: date
    eps_actual: Decimal | None
    eps_estimate: Decimal | None
    eps_surprise: Decimal | None
    revenue_actual: Decimal | None
    revenue_estimate: Decimal | None
    provider: str


@dataclass(frozen=True)
class DividendRecord:
    """Dividend payment record."""

    ticker: str
    dividend_amount: Decimal
    currency: str
    ex_date: date
    record_date: date | None
    pay_date: date | None
    declaration_date: date | None
    frequency: str | None  # quarterly, semi-annual, annual
    provider: str


@dataclass(frozen=True)
class StockSplit:
    """Stock split event."""

    ticker: str
    execution_date: date
    ratio_from: int
    ratio_to: int
    provider: str


@dataclass(frozen=True)
class InsiderTransaction:
    """Insider buy/sell transaction."""

    ticker: str
    name: str
    title: str | None
    transaction_date: date
    transaction_code: str  # P=purchase, S=sale, etc.
    shares: int
    price: Decimal | None
    value: Decimal | None
    shares_owned_after: int | None
    provider: str


@dataclass(frozen=True)
class EconomicCalendarEvent:
    """Scheduled economic indicator release."""

    event: str
    country: str
    date: date
    time: time | None
    impact: str | None  # low, medium, high
    actual: str | None
    forecast: str | None
    previous: str | None
    provider: str
