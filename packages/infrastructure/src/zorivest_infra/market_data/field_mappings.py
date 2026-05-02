"""Field mapping registry for market data transformations (§9.5a–b).

Maps provider-specific field names to canonical schema fields.
Unmapped fields are captured in the ``_extra`` key.

Spec: 09-scheduling.md §9.5a–b
MEU: 86, PW3
"""

from __future__ import annotations

from typing import Any


# Provider display name → slug normalization map (AC-3).
# Used by apply_field_mapping() to resolve display names to registry slugs.
_PROVIDER_SLUG_MAP: dict[str, str] = {
    "Yahoo Finance": "yahoo",
    "Polygon.io": "polygon",
    "Interactive Brokers": "ibkr",
    "Finnhub": "finnhub",
    # MEU-187: 9 new providers
    "Alpaca": "alpaca",
    "Financial Modeling Prep": "fmp",
    "EODHD": "eodhd",
    "API Ninjas": "api_ninjas",
    "Tradier": "tradier",
    "Alpha Vantage": "alpha_vantage",
    "Nasdaq Data Link": "nasdaq_dl",
    "OpenFIGI": "openfigi",
    "SEC API": "sec_api",
    "TradingView": "tradingview",
}


# Canonical field mappings per provider.
# Key: (provider, data_type) → dict of {source_field: canonical_field}
FIELD_MAPPINGS: dict[tuple[str, str], dict[str, str]] = {
    # ── OHLCV ──────────────────────────────────────────────────────────
    ("generic", "ohlcv"): {
        # Short-form → canonical (Polygon-style)
        "o": "open",
        "h": "high",
        "l": "low",
        "c": "close",
        "v": "volume",
        # Identity mappings — data already in canonical form passes through
        "open": "open",
        "high": "high",
        "low": "low",
        "close": "close",
        "volume": "volume",
    },
    ("ibkr", "ohlcv"): {
        "open": "open",
        "high": "high",
        "low": "low",
        "close": "close",
        "volume": "volume",
        "wap": "vwap",
        "count": "trade_count",
    },
    ("polygon", "ohlcv"): {
        "o": "open",
        "h": "high",
        "l": "low",
        "c": "close",
        "v": "volume",
        "vw": "vwap",
        "n": "trade_count",
        "t": "timestamp",
    },
    # ── Quote ──────────────────────────────────────────────────────────
    ("generic", "quote"): {
        "bid": "bid",
        "ask": "ask",
        "last": "last",
        "volume": "volume",
        "timestamp": "timestamp",
    },
    ("yahoo", "quote"): {
        "regularMarketBid": "bid",
        "regularMarketAsk": "ask",
        "regularMarketPrice": "last",
        "regularMarketVolume": "volume",
        "regularMarketChange": "change",
        "regularMarketChangePercent": "change_pct",
        "symbol": "ticker",
    },
    ("yahoo", "ohlcv"): {
        "timestamp": "timestamp",
        "open": "open",
        "high": "high",
        "low": "low",
        "close": "close",
        "volume": "volume",
    },
    ("polygon", "quote"): {
        "bidPrice": "bid",
        "askPrice": "ask",
        "lastTrade": "last",
        "volume": "volume",
    },
    # ── News ───────────────────────────────────────────────────────────
    ("generic", "news"): {
        "headline": "headline",
        "source": "source",
        "url": "url",
        "published_at": "published_at",
        "sentiment": "sentiment",
    },
    ("yahoo", "news"): {
        "title": "headline",
        "publisher": "source",
        "link": "url",
        "providerPublishTime": "published_at",
    },
    ("polygon", "news"): {
        "title": "headline",
        "publisher": "source",
        "article_url": "url",
        "published_utc": "published_at",
    },
    # ── Fundamentals ───────────────────────────────────────────────────
    ("generic", "fundamentals"): {
        "metric": "metric",
        "value": "value",
        "period": "period",
    },
    ("yahoo", "fundamentals"): {
        "shortName": "metric",
        "raw": "value",
        "fiscalQuarter": "period",
    },
    ("polygon", "fundamentals"): {
        "label": "metric",
        "value": "value",
        "fiscal_period": "period",
    },
    # ── FMP (MEU-187) ─────────────────────────────────────────────────
    ("fmp", "quote"): {
        "symbol": "ticker",
        "price": "last",
        "change": "change",
        "changesPercentage": "change_pct",
        "volume": "volume",
    },
    ("fmp", "ohlcv"): {
        "date": "timestamp",
        "open": "open",
        "high": "high",
        "low": "low",
        "close": "close",
        "volume": "volume",
        "adjClose": "adj_close",
    },
    # ── EODHD (MEU-187) ───────────────────────────────────────────────
    ("eodhd", "ohlcv"): {
        "date": "timestamp",
        "open": "open",
        "high": "high",
        "low": "low",
        "close": "close",
        "volume": "volume",
        "adjusted_close": "adj_close",
    },
    # ── Alpaca (MEU-187) ──────────────────────────────────────────────
    ("alpaca", "quote"): {
        "p": "last",
        "s": "size",
        "bp": "bid",
        "ap": "ask",
        "bs": "bid_size",
        "as": "ask_size",
    },
    ("alpaca", "ohlcv"): {
        "o": "open",
        "h": "high",
        "l": "low",
        "c": "close",
        "v": "volume",
        "t": "timestamp",
        "vw": "vwap",
        "n": "trade_count",
    },
    # ── Tradier (MEU-187) ─────────────────────────────────────────────
    ("tradier", "quote"): {
        "symbol": "ticker",
        "last": "last",
        "bid": "bid",
        "ask": "ask",
        "volume": "volume",
        "change": "change",
        "change_percentage": "change_pct",
    },
    ("tradier", "ohlcv"): {
        "date": "timestamp",
        "open": "open",
        "high": "high",
        "low": "low",
        "close": "close",
        "volume": "volume",
    },
    # ── Alpha Vantage (MEU-188) ──────────────────────────────────────────
    ("alpha_vantage", "ohlcv"): {
        "date": "timestamp",
        "open": "open",
        "high": "high",
        "low": "low",
        "close": "close",
        "volume": "volume",
        "adjusted close": "adj_close",
    },
    ("alpha_vantage", "quote"): {
        "symbol": "ticker",
        "price": "last",
        "open": "open",
        "high": "high",
        "low": "low",
        "volume": "volume",
        "change percent": "change_pct",
        "change": "change",
    },
    # ── Finnhub (MEU-188) ────────────────────────────────────────────────
    ("finnhub", "ohlcv"): {
        "o": "open",
        "h": "high",
        "l": "low",
        "c": "close",
        "v": "volume",
        "t": "timestamp",
    },
    # ── F2/F3 Corrections: missing mapping tuples ────────────────────────
    # Alpaca news (identity — Alpaca uses standard field names)
    ("alpaca", "news"): {
        "headline": "headline",
        "source": "source",
        "url": "url",
        "summary": "summary",
        "created_at": "published_at",
    },
    # FMP earnings
    ("fmp", "earnings"): {
        "date": "date",
        "symbol": "ticker",
        "eps": "eps",
        "epsEstimated": "eps_estimated",
        "revenue": "revenue",
        "revenueEstimated": "revenue_estimated",
    },
    # FMP dividends
    ("fmp", "dividends"): {
        "date": "date",
        "dividend": "dividend",
        "recordDate": "record_date",
        "declarationDate": "declaration_date",
        "paymentDate": "payment_date",
    },
    # FMP news
    ("fmp", "news"): {
        "title": "headline",
        "site": "source",
        "url": "url",
        "publishedDate": "published_at",
        "symbol": "ticker",
    },
    # FMP fundamentals (income statement array items)
    ("fmp", "fundamentals"): {
        "date": "date",
        "symbol": "ticker",
        "revenue": "revenue",
        "netIncome": "net_income",
        "grossProfit": "gross_profit",
        "operatingIncome": "operating_income",
    },
    # FMP splits
    ("fmp", "splits"): {
        "date": "date",
        "label": "label",
        "numerator": "numerator",
        "denominator": "denominator",
    },
    # EODHD fundamentals (section-prefixed keys from flattened extractor)
    ("eodhd", "fundamentals"): {
        "General.Code": "General.Code",
        "General.Name": "General.Name",
        "General.Exchange": "General.Exchange",
        "Highlights.MarketCapitalization": "Highlights.MarketCapitalization",
    },
    # EODHD dividends
    ("eodhd", "dividends"): {
        "date": "date",
        "value": "value",
    },
    # EODHD news
    ("eodhd", "news"): {
        "title": "headline",
        "link": "url",
        "date": "published_at",
    },
    # EODHD splits
    ("eodhd", "splits"): {
        "date": "date",
        "split": "split",
    },
    # API Ninjas quote
    ("api_ninjas", "quote"): {
        "name": "name",
        "price": "last",
        "exchange": "exchange",
        "ticker": "ticker",
        "volume": "volume",
    },
    # API Ninjas earnings
    ("api_ninjas", "earnings"): {
        "date": "date",
        "ticker": "ticker",
        "actual_eps": "actual_eps",
        "estimated_eps": "estimated_eps",
    },
    # Alpha Vantage earnings (CSV columns)
    ("alpha_vantage", "earnings"): {
        "fiscalDateEnding": "date",
        "reportedEPS": "eps",
        "estimatedEPS": "eps_estimated",
        "symbol": "ticker",
        "surprise": "surprise",
        "surprisePercentage": "surprise_pct",
    },
    # Nasdaq Data Link fundamentals (SHARADAR/SF1 columns)
    ("nasdaq_dl", "fundamentals"): {
        "ticker": "ticker",
        "calendardate": "date",
        "pe": "pe",
        "eps": "eps",
        "revenue": "revenue",
        "netinc": "net_income",
        "marketcap": "market_cap",
    },
    # TradingView scanner quote (identity — scanner columns already canonical)
    ("tradingview", "quote"): {
        "close": "close",
        "volume": "volume",
        "change": "change",
        "high": "high",
        "low": "low",
        "open": "open",
        "name": "name",
    },
    # TradingView scanner fundamentals (scanner columns → canonical names)
    ("tradingview", "fundamentals"): {
        "market_cap_basic": "market_cap",
        "earnings_per_share_basic_ttm": "eps",
        "price_earnings_ttm": "pe_ratio",
        "dividend_yield_indication": "dividend_yield",
        "price_book_ratio": "pb_ratio",
        "debt_to_equity": "debt_to_equity",
        "name": "name",
    },
}


def apply_field_mapping(
    *,
    record: dict[str, Any],
    provider: str,
    data_type: str,
) -> dict[str, Any]:
    """Map provider-specific fields to canonical names.

    Unmapped source fields are captured in a ``_extra`` dict.

    Args:
        record: Source data record with provider-specific field names.
        provider: Data provider key (e.g., 'ibkr', 'polygon').
        data_type: Data type key (e.g., 'ohlcv').

    Returns:
        Dict with canonical field names + ``_extra`` for unmapped fields.
    """
    # AC-3: Normalize display names to slugs before lookup.
    slug = _PROVIDER_SLUG_MAP.get(provider, provider)
    mapping = FIELD_MAPPINGS.get((slug, data_type), {})

    # Reverse mapping: source_field → canonical_field
    result: dict[str, Any] = {}
    extras: dict[str, Any] = {}

    for src_field, value in record.items():
        if src_field in mapping:
            result[mapping[src_field]] = value
        else:
            extras[src_field] = value

    result["_extra"] = extras
    return result
