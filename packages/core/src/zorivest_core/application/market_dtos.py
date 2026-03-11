"""Market data response DTOs — MEU-57.

Pydantic BaseModel DTOs for normalized market data responses.
Source: docs/build-plan/08-market-data.md §8.1c.

Placed in a separate file from dtos.py to avoid mixing
frozen dataclass DTOs (Phase 1) with Pydantic models (Phase 8).
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class MarketQuote(BaseModel):
    """Normalized stock quote across all providers."""

    ticker: str
    price: float
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    previous_close: Optional[float] = None
    change: Optional[float] = None
    change_pct: Optional[float] = None
    volume: Optional[int] = None
    timestamp: Optional[datetime] = None
    provider: str


class MarketNewsItem(BaseModel):
    """Normalized news article."""

    title: str
    source: str
    url: Optional[str] = None
    published_at: Optional[datetime] = None
    tickers: list[str] = Field(default_factory=list)
    summary: Optional[str] = None
    provider: str


class TickerSearchResult(BaseModel):
    """Normalized ticker search result."""

    symbol: str
    name: str
    exchange: Optional[str] = None
    currency: Optional[str] = None
    provider: str


class SecFiling(BaseModel):
    """SEC filing reference."""

    ticker: str
    company_name: str
    cik: str
    filing_type: Optional[str] = None
    filing_date: Optional[datetime] = None
    provider: str = "SEC API"
