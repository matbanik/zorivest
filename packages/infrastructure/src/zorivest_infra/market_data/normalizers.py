"""Market data response normalizers — MEU-61 + MEU-190/191.

Convert provider-specific JSON responses into normalized domain DTOs.
Source: docs/build-plan/08-market-data.md §8.3c (Layer 1-3).
Layer 4 expansion: docs/build-plan/08a-market-data-expansion.md §8a.9/§8a.10.

Each normalizer handles null/missing fields gracefully with safe defaults.
The normalizer_registry dict at the bottom maps provider names to functions
for use by MarketDataService via constructor injection.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any

from zorivest_core.application.market_dtos import (
    MarketNewsItem,
    MarketQuote,
    SecFiling,
    TickerSearchResult,
)
from zorivest_core.application.market_expansion_dtos import (
    DividendRecord,
    EarningsReport,
    EconomicCalendarEvent,
    FundamentalsSnapshot,
    InsiderTransaction,
    OHLCVBar,
    StockSplit,
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


# ── OHLCV Normalizers (MEU-190) ────────────────────────────────────────


def _safe_decimal(val: Any) -> Decimal:
    if val is None:
        return Decimal("0")
    return Decimal(str(val))


def _safe_ts(val: Any) -> datetime:
    if val is None:
        return datetime.now(timezone.utc)
    if isinstance(val, (int, float)):
        return datetime.fromtimestamp(val, tz=timezone.utc)
    return datetime.fromisoformat(str(val))


def _safe_date(val: Any) -> date:
    if val is None:
        return date.today()
    if isinstance(val, date):
        return val
    return date.fromisoformat(str(val)[:10])


def normalize_alpaca_ohlcv(data: dict[str, Any], *, ticker: str = "") -> list[OHLCVBar]:
    """Alpaca /v2/stocks/{ticker}/bars → list[OHLCVBar]."""
    bars_raw = data.get("bars", [])
    return [
        OHLCVBar(
            ticker=ticker,
            timestamp=_safe_ts(b.get("t")),
            open=_safe_decimal(b.get("o")),
            high=_safe_decimal(b.get("h")),
            low=_safe_decimal(b.get("l")),
            close=_safe_decimal(b.get("c")),
            adj_close=None,
            volume=int(b.get("v", 0)),
            vwap=_safe_decimal(b.get("vw")) if b.get("vw") else None,
            trade_count=b.get("n"),
            provider="Alpaca",
        )
        for b in bars_raw
    ]


def normalize_eodhd_ohlcv(
    data: list[dict[str, Any]] | dict[str, Any], *, ticker: str = ""
) -> list[OHLCVBar]:
    """EODHD /eod/{ticker} → list[OHLCVBar]."""
    rows = data if isinstance(data, list) else []
    return [
        OHLCVBar(
            ticker=ticker,
            timestamp=_safe_ts(r.get("date")),
            open=_safe_decimal(r.get("open")),
            high=_safe_decimal(r.get("high")),
            low=_safe_decimal(r.get("low")),
            close=_safe_decimal(r.get("close")),
            adj_close=_safe_decimal(r.get("adjusted_close"))
            if r.get("adjusted_close") is not None
            else None,
            volume=int(r.get("volume", 0)),
            vwap=None,
            trade_count=None,
            provider="EODHD",
        )
        for r in rows
    ]


def normalize_polygon_ohlcv(
    data: dict[str, Any], *, ticker: str = ""
) -> list[OHLCVBar]:
    """Polygon /v2/aggs/ticker/{ticker}/range → list[OHLCVBar]."""
    results = data.get("results", [])
    return [
        OHLCVBar(
            ticker=ticker or data.get("ticker", ""),
            timestamp=datetime.fromtimestamp(r.get("t", 0) / 1000, tz=timezone.utc),
            open=_safe_decimal(r.get("o")),
            high=_safe_decimal(r.get("h")),
            low=_safe_decimal(r.get("l")),
            close=_safe_decimal(r.get("c")),
            adj_close=None,
            volume=int(r.get("v", 0)),
            vwap=_safe_decimal(r.get("vw")) if r.get("vw") else None,
            trade_count=r.get("n"),
            provider="Polygon.io",
        )
        for r in results
    ]


# ── Fundamentals Normalizers (MEU-190) ─────────────────────────────────


def normalize_fmp_fundamentals(
    data: list[dict[str, Any]] | dict[str, Any], *, ticker: str = ""
) -> FundamentalsSnapshot:
    """FMP /profile/{ticker} → FundamentalsSnapshot."""
    r = (
        data[0]
        if isinstance(data, list) and data
        else (data if isinstance(data, dict) else {})
    )
    return FundamentalsSnapshot(
        ticker=r.get("symbol", ticker),
        market_cap=_safe_decimal(r.get("mktCap")) if r.get("mktCap") else None,
        pe_ratio=_safe_decimal(r.get("pe")) if r.get("pe") else None,
        pb_ratio=None,
        ps_ratio=None,
        eps=_safe_decimal(r.get("eps")) if r.get("eps") else None,
        dividend_yield=_safe_decimal(r.get("lastDiv")) if r.get("lastDiv") else None,
        beta=_safe_decimal(r.get("beta")) if r.get("beta") else None,
        sector=r.get("sector"),
        industry=r.get("industry"),
        employees=r.get("fullTimeEmployees"),
        provider="Financial Modeling Prep",
        timestamp=datetime.now(timezone.utc),
    )


def normalize_eodhd_fundamentals(
    data: dict[str, Any], *, ticker: str = ""
) -> FundamentalsSnapshot:
    """EODHD /fundamentals/{ticker} → FundamentalsSnapshot."""
    gen = data.get("General", {})
    hi = data.get("Highlights", {})
    return FundamentalsSnapshot(
        ticker=gen.get("Code", ticker),
        market_cap=_safe_decimal(hi.get("MarketCapitalization"))
        if hi.get("MarketCapitalization")
        else None,
        pe_ratio=_safe_decimal(hi.get("PERatio")) if hi.get("PERatio") else None,
        pb_ratio=None,
        ps_ratio=None,
        eps=_safe_decimal(hi.get("EarningsShare")) if hi.get("EarningsShare") else None,
        dividend_yield=_safe_decimal(hi.get("DividendYield"))
        if hi.get("DividendYield")
        else None,
        beta=None,
        sector=gen.get("Sector"),
        industry=gen.get("Industry"),
        employees=gen.get("FullTimeEmployees"),
        provider="EODHD",
        timestamp=datetime.now(timezone.utc),
    )


def normalize_av_fundamentals(
    data: dict[str, Any], *, ticker: str = ""
) -> FundamentalsSnapshot:
    """Alpha Vantage OVERVIEW → FundamentalsSnapshot."""
    return FundamentalsSnapshot(
        ticker=data.get("Symbol", ticker),
        market_cap=_safe_decimal(data.get("MarketCapitalization"))
        if data.get("MarketCapitalization")
        else None,
        pe_ratio=_safe_decimal(data.get("PERatio"))
        if data.get("PERatio") not in (None, "None")
        else None,
        pb_ratio=_safe_decimal(data.get("PriceToBookRatio"))
        if data.get("PriceToBookRatio") not in (None, "None")
        else None,
        ps_ratio=_safe_decimal(data.get("PriceToSalesRatioTTM"))
        if data.get("PriceToSalesRatioTTM") not in (None, "None")
        else None,
        eps=_safe_decimal(data.get("EPS"))
        if data.get("EPS") not in (None, "None")
        else None,
        dividend_yield=_safe_decimal(data.get("DividendYield"))
        if data.get("DividendYield") not in (None, "None")
        else None,
        beta=_safe_decimal(data.get("Beta"))
        if data.get("Beta") not in (None, "None")
        else None,
        sector=data.get("Sector"),
        industry=data.get("Industry"),
        employees=int(data["FullTimeEmployees"])
        if data.get("FullTimeEmployees")
        else None,
        provider="Alpha Vantage",
        timestamp=datetime.now(timezone.utc),
    )


# ── Earnings Normalizers (MEU-190) ─────────────────────────────────────


def normalize_finnhub_earnings(
    data: list[dict[str, Any]] | dict[str, Any], *, ticker: str = ""
) -> list[EarningsReport]:
    """Finnhub /stock/earnings → list[EarningsReport]."""
    items = data if isinstance(data, list) else []
    return [
        EarningsReport(
            ticker=e.get("symbol", ticker),
            fiscal_period=f"Q{e.get('quarter', 0)}",
            fiscal_year=int(e.get("year", 0)),
            report_date=_safe_date(e.get("period")),
            eps_actual=_safe_decimal(e.get("actual"))
            if e.get("actual") is not None
            else None,
            eps_estimate=_safe_decimal(e.get("estimate"))
            if e.get("estimate") is not None
            else None,
            eps_surprise=_safe_decimal(e.get("surprise"))
            if e.get("surprise") is not None
            else None,
            revenue_actual=None,
            revenue_estimate=None,
            provider="Finnhub",
        )
        for e in items
    ]


def normalize_fmp_earnings(
    data: list[dict[str, Any]] | dict[str, Any], *, ticker: str = ""
) -> list[EarningsReport]:
    """FMP /earnings-surprises/{ticker} → list[EarningsReport]."""
    items = data if isinstance(data, list) else []
    return [
        EarningsReport(
            ticker=e.get("symbol", ticker),
            fiscal_period=e.get("fiscalPeriod", "Q0")[:2],
            fiscal_year=int(str(e.get("fiscalDateEnding", "0000"))[:4]),
            report_date=_safe_date(e.get("date")),
            eps_actual=_safe_decimal(e.get("actualEarningResult"))
            if e.get("actualEarningResult") is not None
            else None,
            eps_estimate=_safe_decimal(e.get("estimatedEarning"))
            if e.get("estimatedEarning") is not None
            else None,
            eps_surprise=None,
            revenue_actual=_safe_decimal(e.get("actualRevenue"))
            if e.get("actualRevenue") is not None
            else None,
            revenue_estimate=_safe_decimal(e.get("estimatedRevenue"))
            if e.get("estimatedRevenue") is not None
            else None,
            provider="Financial Modeling Prep",
        )
        for e in items
    ]


def normalize_av_earnings(
    data: dict[str, Any], *, ticker: str = ""
) -> list[EarningsReport]:
    """Alpha Vantage EARNINGS → list[EarningsReport]."""
    items = data.get("quarterlyEarnings", [])
    return [
        EarningsReport(
            ticker=ticker,
            fiscal_period=e.get("fiscalDateEnding", "")[-5:].replace("-", "Q")[:2]
            or "Q0",
            fiscal_year=int(str(e.get("fiscalDateEnding", "0000"))[:4]),
            report_date=_safe_date(e.get("reportedDate")),
            eps_actual=_safe_decimal(e.get("reportedEPS"))
            if e.get("reportedEPS") not in (None, "None")
            else None,
            eps_estimate=_safe_decimal(e.get("estimatedEPS"))
            if e.get("estimatedEPS") not in (None, "None")
            else None,
            eps_surprise=_safe_decimal(e.get("surprise"))
            if e.get("surprise") not in (None, "None")
            else None,
            revenue_actual=None,
            revenue_estimate=None,
            provider="Alpha Vantage",
        )
        for e in items
    ]


# ── Dividend Normalizers (MEU-191) ─────────────────────────────────────


def normalize_polygon_dividends(
    data: dict[str, Any], *, ticker: str = ""
) -> list[DividendRecord]:
    """Polygon /v3/reference/dividends → list[DividendRecord]."""
    results = data.get("results", [])
    return [
        DividendRecord(
            ticker=d.get("ticker", ticker),
            dividend_amount=_safe_decimal(d.get("cash_amount")),
            currency=d.get("currency", "USD"),
            ex_date=_safe_date(d.get("ex_dividend_date")),
            record_date=_safe_date(d.get("record_date"))
            if d.get("record_date")
            else None,
            pay_date=_safe_date(d.get("pay_date")) if d.get("pay_date") else None,
            declaration_date=_safe_date(d.get("declaration_date"))
            if d.get("declaration_date")
            else None,
            frequency=d.get("frequency"),
            provider="Polygon.io",
        )
        for d in results
    ]


def normalize_eodhd_dividends(
    data: list[dict[str, Any]] | dict[str, Any], *, ticker: str = ""
) -> list[DividendRecord]:
    """EODHD /div/{ticker} → list[DividendRecord]."""
    items = data if isinstance(data, list) else []
    return [
        DividendRecord(
            ticker=ticker,
            dividend_amount=_safe_decimal(d.get("value")),
            currency=d.get("currency", "USD"),
            ex_date=_safe_date(d.get("date")),
            record_date=_safe_date(d.get("recordDate"))
            if d.get("recordDate")
            else None,
            pay_date=_safe_date(d.get("paymentDate")) if d.get("paymentDate") else None,
            declaration_date=_safe_date(d.get("declarationDate"))
            if d.get("declarationDate")
            else None,
            frequency=None,
            provider="EODHD",
        )
        for d in items
    ]


def normalize_fmp_dividends(
    data: list[dict[str, Any]] | dict[str, Any], *, ticker: str = ""
) -> list[DividendRecord]:
    """FMP /stock_dividend/{ticker} → list[DividendRecord]."""
    items = (
        data.get("historical", [])
        if isinstance(data, dict)
        else (data if isinstance(data, list) else [])
    )
    return [
        DividendRecord(
            ticker=ticker,
            dividend_amount=_safe_decimal(d.get("dividend")),
            currency="USD",
            ex_date=_safe_date(d.get("date")),
            record_date=_safe_date(d.get("recordDate"))
            if d.get("recordDate")
            else None,
            pay_date=_safe_date(d.get("paymentDate")) if d.get("paymentDate") else None,
            declaration_date=_safe_date(d.get("declarationDate"))
            if d.get("declarationDate")
            else None,
            frequency=None,
            provider="Financial Modeling Prep",
        )
        for d in items
    ]


# ── Split Normalizers (MEU-191) ────────────────────────────────────────


def normalize_polygon_splits(
    data: dict[str, Any], *, ticker: str = ""
) -> list[StockSplit]:
    """Polygon /v3/reference/splits → list[StockSplit]."""
    results = data.get("results", [])
    return [
        StockSplit(
            ticker=s.get("ticker", ticker),
            execution_date=_safe_date(s.get("execution_date")),
            ratio_from=int(s.get("split_from", 1)),
            ratio_to=int(s.get("split_to", 1)),
            provider="Polygon.io",
        )
        for s in results
    ]


def normalize_eodhd_splits(
    data: list[dict[str, Any]] | dict[str, Any], *, ticker: str = ""
) -> list[StockSplit]:
    """EODHD /splits/{ticker} → list[StockSplit]."""
    items = data if isinstance(data, list) else []
    splits: list[StockSplit] = []
    for s in items:
        raw = str(s.get("split", "1/1"))
        parts = raw.split("/")
        ratio_to = int(parts[0]) if len(parts) >= 1 else 1
        ratio_from = int(parts[1]) if len(parts) >= 2 else 1
        splits.append(
            StockSplit(
                ticker=ticker,
                execution_date=_safe_date(s.get("date")),
                ratio_from=ratio_from,
                ratio_to=ratio_to,
                provider="EODHD",
            )
        )
    return splits


def normalize_fmp_splits(
    data: list[dict[str, Any]] | dict[str, Any], *, ticker: str = ""
) -> list[StockSplit]:
    """FMP /stock_split/{ticker} → list[StockSplit]."""
    items = (
        data.get("historical", [])
        if isinstance(data, dict)
        else (data if isinstance(data, list) else [])
    )
    return [
        StockSplit(
            ticker=ticker,
            execution_date=_safe_date(s.get("date")),
            ratio_from=int(s.get("denominator", 1)),
            ratio_to=int(s.get("numerator", 1)),
            provider="Financial Modeling Prep",
        )
        for s in items
    ]


# ── Insider Normalizers (MEU-191) ──────────────────────────────────────


def normalize_finnhub_insider(
    data: dict[str, Any], *, ticker: str = ""
) -> list[InsiderTransaction]:
    """Finnhub /stock/insider-transactions → list[InsiderTransaction]."""
    items = data.get("data", [])
    return [
        InsiderTransaction(
            ticker=t.get("symbol", ticker),
            name=t.get("name", ""),
            title=None,
            transaction_date=_safe_date(t.get("transactionDate")),
            transaction_code=t.get("transactionCode", ""),
            shares=int(t.get("share", 0)),
            price=_safe_decimal(t.get("transactionPrice"))
            if t.get("transactionPrice")
            else None,
            value=None,
            shares_owned_after=None,
            provider="Finnhub",
        )
        for t in items
    ]


def normalize_fmp_insider(
    data: list[dict[str, Any]] | dict[str, Any], *, ticker: str = ""
) -> list[InsiderTransaction]:
    """FMP /insider-trading → list[InsiderTransaction]."""
    items = data if isinstance(data, list) else []
    return [
        InsiderTransaction(
            ticker=t.get("symbol", ticker),
            name=t.get("reportingName", ""),
            title=t.get("typeOfOwner"),
            transaction_date=_safe_date(t.get("transactionDate")),
            transaction_code=t.get("transactionType", ""),
            shares=int(t.get("securitiesTransacted", 0)),
            price=_safe_decimal(t.get("price")) if t.get("price") else None,
            value=None,
            shares_owned_after=int(t["securitiesOwned"])
            if t.get("securitiesOwned")
            else None,
            provider="Financial Modeling Prep",
        )
        for t in items
    ]


def normalize_sec_insider(
    data: list[dict[str, Any]] | dict[str, Any], *, ticker: str = ""
) -> list[InsiderTransaction]:
    """SEC EDGAR insider filings → list[InsiderTransaction]."""
    items = data if isinstance(data, list) else []
    return [
        InsiderTransaction(
            ticker=ticker,
            name=t.get("reportingOwner", {}).get("name", "")
            if isinstance(t.get("reportingOwner"), dict)
            else str(t.get("reportingOwner", "")),
            title=None,
            transaction_date=_safe_date(t.get("transactionDate")),
            transaction_code=t.get("transactionCode", ""),
            shares=int(t.get("transactionShares", 0)),
            price=_safe_decimal(t.get("transactionPricePerShare"))
            if t.get("transactionPricePerShare")
            else None,
            value=None,
            shares_owned_after=int(t["sharesOwnedFollowing"])
            if t.get("sharesOwnedFollowing")
            else None,
            provider="SEC API",
        )
        for t in items
    ]


# ── Economic Calendar Normalizers (MEU-191) ────────────────────────────


def normalize_finnhub_calendar(
    data: dict[str, Any], *, ticker: str = ""
) -> list[EconomicCalendarEvent]:
    """Finnhub /calendar/economic → list[EconomicCalendarEvent]."""
    items = data.get("economicCalendar", [])
    return [
        EconomicCalendarEvent(
            event=e.get("event", ""),
            country=e.get("country", ""),
            date=_safe_date(e.get("time", e.get("date"))),
            time=None,
            impact=e.get("impact"),
            actual=str(e["actual"]) if e.get("actual") is not None else None,
            forecast=str(e["estimate"]) if e.get("estimate") is not None else None,
            previous=str(e["prev"]) if e.get("prev") is not None else None,
            provider="Finnhub",
        )
        for e in items
    ]


def normalize_fmp_calendar(
    data: list[dict[str, Any]] | dict[str, Any], *, ticker: str = ""
) -> list[EconomicCalendarEvent]:
    """FMP /economic_calendar → list[EconomicCalendarEvent]."""
    items = data if isinstance(data, list) else []
    return [
        EconomicCalendarEvent(
            event=e.get("event", ""),
            country=e.get("country", ""),
            date=_safe_date(e.get("date")),
            time=None,
            impact=e.get("impact"),
            actual=str(e["actual"]) if e.get("actual") is not None else None,
            forecast=str(e["estimate"]) if e.get("estimate") is not None else None,
            previous=str(e["previous"]) if e.get("previous") is not None else None,
            provider="Financial Modeling Prep",
        )
        for e in items
    ]


def normalize_av_calendar(
    data: dict[str, Any], *, ticker: str = ""
) -> list[EconomicCalendarEvent]:
    """Alpha Vantage economic indicators → list[EconomicCalendarEvent]."""
    items = data.get("data", [])
    return [
        EconomicCalendarEvent(
            event=e.get("name", ""),
            country=e.get("country", "US"),
            date=_safe_date(e.get("date")),
            time=None,
            impact=None,
            actual=str(e["value"]) if e.get("value") is not None else None,
            forecast=None,
            previous=None,
            provider="Alpha Vantage",
        )
        for e in items
    ]


# ── Company Profile Normalizers (MEU-191) ──────────────────────────────


def normalize_fmp_profile(
    data: list[dict[str, Any]] | dict[str, Any], *, ticker: str = ""
) -> FundamentalsSnapshot:
    """FMP /profile/{ticker} → FundamentalsSnapshot (company profile focus)."""
    return normalize_fmp_fundamentals(data, ticker=ticker)


def normalize_finnhub_profile(
    data: dict[str, Any], *, ticker: str = ""
) -> FundamentalsSnapshot:
    """Finnhub /stock/profile2 → FundamentalsSnapshot."""
    return FundamentalsSnapshot(
        ticker=data.get("ticker", ticker),
        market_cap=_safe_decimal(data.get("marketCapitalization"))
        if data.get("marketCapitalization")
        else None,
        pe_ratio=None,
        pb_ratio=None,
        ps_ratio=None,
        eps=None,
        dividend_yield=None,
        beta=None,
        sector=data.get("finnhubIndustry"),
        industry=data.get("finnhubIndustry"),
        employees=None,
        provider="Finnhub",
        timestamp=datetime.now(timezone.utc),
    )


def normalize_eodhd_profile(
    data: dict[str, Any], *, ticker: str = ""
) -> FundamentalsSnapshot:
    """EODHD /fundamentals (profile subset) → FundamentalsSnapshot."""
    return normalize_eodhd_fundamentals(data, ticker=ticker)


# ── Layer 4 Normalizer Registry ────────────────────────────────────────

NORMALIZERS: dict[str, dict[str, Any]] = {
    "ohlcv": {
        "Alpaca": normalize_alpaca_ohlcv,
        "EODHD": normalize_eodhd_ohlcv,
        "Polygon.io": normalize_polygon_ohlcv,
    },
    "fundamentals": {
        "Financial Modeling Prep": normalize_fmp_fundamentals,
        "EODHD": normalize_eodhd_fundamentals,
        "Alpha Vantage": normalize_av_fundamentals,
    },
    "earnings": {
        "Finnhub": normalize_finnhub_earnings,
        "Financial Modeling Prep": normalize_fmp_earnings,
        "Alpha Vantage": normalize_av_earnings,
    },
    "dividends": {
        "Polygon.io": normalize_polygon_dividends,
        "EODHD": normalize_eodhd_dividends,
        "Financial Modeling Prep": normalize_fmp_dividends,
    },
    "splits": {
        "Polygon.io": normalize_polygon_splits,
        "EODHD": normalize_eodhd_splits,
        "Financial Modeling Prep": normalize_fmp_splits,
    },
    "insider": {
        "Finnhub": normalize_finnhub_insider,
        "Financial Modeling Prep": normalize_fmp_insider,
        "SEC API": normalize_sec_insider,
    },
    "economic_calendar": {
        "Finnhub": normalize_finnhub_calendar,
        "Financial Modeling Prep": normalize_fmp_calendar,
        "Alpha Vantage": normalize_av_calendar,
    },
    "company_profile": {
        "Financial Modeling Prep": normalize_fmp_profile,
        "Finnhub": normalize_finnhub_profile,
        "EODHD": normalize_eodhd_profile,
    },
}
