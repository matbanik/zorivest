"""Market data response normalizers — MEU-61.

Convert provider-specific JSON responses into normalized domain DTOs.
Source: docs/build-plan/08-market-data.md §8.3c.

Each normalizer handles null/missing fields gracefully with safe defaults.
The normalizer_registry dict at the bottom maps provider names to functions
for use by MarketDataService via constructor injection.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from zorivest_core.application.market_dtos import (
    MarketNewsItem,
    MarketQuote,
    SecFiling,
    TickerSearchResult,
)


# ── Quote Normalizers ───────────────────────────────────────────────────


def normalize_alpha_vantage_quote(data: dict[str, Any]) -> MarketQuote:
    """Convert Alpha Vantage 'Global Quote' → MarketQuote."""
    gq = data.get("Global Quote", {})
    return MarketQuote(
        ticker=gq.get("01. symbol", ""),
        price=float(gq.get("05. price", 0)),
        open=float(gq.get("02. open", 0)),
        high=float(gq.get("03. high", 0)),
        low=float(gq.get("04. low", 0)),
        previous_close=float(gq.get("08. previous close", 0)),
        change=float(gq.get("09. change", 0)),
        change_pct=float(str(gq.get("10. change percent", "0")).rstrip("%")),
        volume=int(gq.get("06. volume", 0)),
        provider="Alpha Vantage",
    )


def normalize_polygon_quote(data: dict[str, Any]) -> MarketQuote:
    """Convert Polygon.io v2 snapshot → MarketQuote."""
    results = data.get("results", [])
    if not results:
        return MarketQuote(ticker="", price=0.0, provider="Polygon.io")

    r = results[0]
    ts = r.get("t")
    timestamp = (
        datetime.fromtimestamp(ts / 1000, tz=timezone.utc) if ts is not None else None
    )
    return MarketQuote(
        ticker=r.get("T", ""),
        price=float(r.get("c", 0)),
        open=float(r.get("o", 0)),
        high=float(r.get("h", 0)),
        low=float(r.get("l", 0)),
        volume=int(r.get("v", 0)),
        timestamp=timestamp,
        provider="Polygon.io",
    )


def normalize_finnhub_quote(data: dict[str, Any], *, ticker: str = "") -> MarketQuote:
    """Convert Finnhub /quote response → MarketQuote.

    Finnhub responses don't include the ticker, so it must be passed in.
    """
    ts = data.get("t")
    timestamp = datetime.fromtimestamp(ts, tz=timezone.utc) if ts is not None else None
    return MarketQuote(
        ticker=ticker,
        price=float(data.get("c", 0)),
        open=float(data.get("o", 0)),
        high=float(data.get("h", 0)),
        low=float(data.get("l", 0)),
        previous_close=float(data.get("pc", 0)),
        change=float(data.get("d", 0)),
        change_pct=float(data.get("dp", 0)),
        timestamp=timestamp,
        provider="Finnhub",
    )


def normalize_eodhd_quote(data: dict[str, Any]) -> MarketQuote:
    """Convert EODHD real-time endpoint → MarketQuote."""
    ts = data.get("timestamp")
    timestamp = datetime.fromtimestamp(ts, tz=timezone.utc) if ts is not None else None
    return MarketQuote(
        ticker=data.get("code", ""),
        price=float(data.get("close", 0)),
        open=float(data.get("open", 0)),
        high=float(data.get("high", 0)),
        low=float(data.get("low", 0)),
        previous_close=float(data.get("previousClose", 0)),
        change=float(data.get("change", 0)),
        change_pct=float(data.get("change_p", 0)),
        volume=int(data.get("volume", 0)),
        timestamp=timestamp,
        provider="EODHD",
    )


def normalize_api_ninjas_quote(data: dict[str, Any]) -> MarketQuote:
    """Convert API Ninjas /stockprice → MarketQuote.

    API Ninjas returns minimal data: ticker, price, name, exchange, updated.
    """
    ts = data.get("updated")
    timestamp = datetime.fromtimestamp(ts, tz=timezone.utc) if ts is not None else None
    return MarketQuote(
        ticker=data.get("ticker", ""),
        price=float(data.get("price", 0)),
        timestamp=timestamp,
        provider="API Ninjas",
    )


# ── Search Normalizers ──────────────────────────────────────────────────


def normalize_fmp_search(data: list[dict[str, Any]]) -> list[TickerSearchResult]:
    """Convert FMP /search results → list[TickerSearchResult]."""
    return [
        TickerSearchResult(
            symbol=item.get("symbol", ""),
            name=item.get("name", ""),
            exchange=item.get("exchangeShortName"),
            currency=item.get("currency"),
            provider="Financial Modeling Prep",
        )
        for item in data
    ]


def normalize_alpha_vantage_search(
    data: dict[str, Any],
) -> list[TickerSearchResult]:
    """Convert Alpha Vantage SYMBOL_SEARCH → list[TickerSearchResult].

    Response format: {"bestMatches": [{"1. symbol": ..., "2. name": ...}, ...]}
    """
    matches = data.get("bestMatches", [])
    return [
        TickerSearchResult(
            symbol=item.get("1. symbol", ""),
            name=item.get("2. name", ""),
            exchange=item.get("4. region"),
            currency=item.get("8. currency"),
            provider="Alpha Vantage",
        )
        for item in matches
    ]


# ── Filing Normalizers ──────────────────────────────────────────────────


def normalize_sec_filing(data: list[dict[str, Any]]) -> list[SecFiling]:
    """Convert SEC API /mapping/ticker → list[SecFiling]."""
    results: list[SecFiling] = []
    for item in data:
        filed_at = item.get("filedAt")
        filing_date = None
        if filed_at:
            try:
                filing_date = datetime.fromisoformat(filed_at)
            except (ValueError, TypeError):
                filing_date = None

        results.append(
            SecFiling(
                ticker=item.get("ticker", ""),
                company_name=item.get("companyName", ""),
                cik=item.get("cik", ""),
                filing_type=item.get("formType"),
                filing_date=filing_date,
                provider="SEC API",
            )
        )
    return results


# ── News Normalizers ────────────────────────────────────────────────────


def normalize_finnhub_news(
    data: list[dict[str, Any]],
) -> list[MarketNewsItem]:
    """Convert Finnhub /company-news → list[MarketNewsItem]."""
    results: list[MarketNewsItem] = []
    for item in data:
        ts = item.get("datetime")
        published_at = (
            datetime.fromtimestamp(ts, tz=timezone.utc) if ts is not None else None
        )

        related = item.get("related", "")
        tickers = [t.strip() for t in related.split(",") if t.strip()]

        results.append(
            MarketNewsItem(
                title=item.get("headline", ""),
                source=item.get("source", ""),
                url=item.get("url"),
                published_at=published_at,
                tickers=tickers,
                summary=item.get("summary"),
                provider="Finnhub",
            )
        )
    return results


# ── Normalizer Registry ────────────────────────────────────────────────

# Maps provider name → quote normalizer function.
# Used by MarketDataService via constructor injection.
QUOTE_NORMALIZERS: dict[str, Any] = {
    "Alpha Vantage": normalize_alpha_vantage_quote,
    "Polygon.io": normalize_polygon_quote,
    "Finnhub": normalize_finnhub_quote,
    "EODHD": normalize_eodhd_quote,
    "API Ninjas": normalize_api_ninjas_quote,
}

NEWS_NORMALIZERS: dict[str, Any] = {
    "Finnhub": normalize_finnhub_news,
}

SEARCH_NORMALIZERS: dict[str, Any] = {
    "Financial Modeling Prep": normalize_fmp_search,
    "Alpha Vantage": normalize_alpha_vantage_search,
}
