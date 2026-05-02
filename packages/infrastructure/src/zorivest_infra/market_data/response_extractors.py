# packages/infrastructure/src/zorivest_infra/market_data/response_extractors.py
"""Per-provider JSON envelope extraction for market data responses (AC-2).

Provider APIs wrap records in different envelope structures:
  - Yahoo: {"quoteResponse": {"result": [...]}}
  - Polygon OHLCV: {"results": [...]}
  - Generic: top-level list or dict

This module provides `extract_records()` which handles these envelopes
and returns a flat list of dicts for field mapping.

Spec: 09-scheduling.md §9.5, deficiency report §3.3
MEU: PW12
"""

from __future__ import annotations

import csv
import io
import json
import re
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Envelope extraction registry
# ---------------------------------------------------------------------------

# Key: (provider, data_type) → callable(parsed_json) → list[dict]
_EXTRACTORS: dict[tuple[str, str], Any] = {}


def _register(provider: str, data_type: str):
    """Decorator to register an envelope extractor."""

    def decorator(fn):
        _EXTRACTORS[(provider, data_type)] = fn
        return fn

    return decorator


# ---------------------------------------------------------------------------
# Yahoo extractors
# ---------------------------------------------------------------------------


@_register("yahoo", "quote")
def _yahoo_quote(data: Any) -> list[dict]:
    """Yahoo Finance quote via v8/chart: {"chart": {"result": [{"meta": {...}}]}}.

    The v6/finance/quote endpoint was deprecated (~2024, returns 404).
    Quote data now comes from v8/finance/chart — the meta block of the
    first result contains all quote fields (regularMarketPrice, symbol, etc.).

    Also supports:
    - Legacy v6 envelope for backward compatibility with cached data.
    - Top-level list of dicts (pre-extracted by multi-ticker fetch loop).
    """
    # Multi-ticker path: adapter already extracted and merged records
    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        # v8/chart envelope: chart.result[0].meta
        chart = data.get("chart", {})
        if isinstance(chart, dict):
            result = chart.get("result", [])
            if isinstance(result, list) and result:
                meta = result[0].get("meta", {})
                if isinstance(meta, dict) and meta:
                    # v8/chart meta lacks regularMarketChange/Percent
                    # — compute from chartPreviousClose + regularMarketPrice
                    price = meta.get("regularMarketPrice")
                    prev = meta.get("chartPreviousClose")
                    if price is not None and prev is not None and prev != 0:
                        change = price - prev
                        change_pct = (change / prev) * 100
                        meta.setdefault("regularMarketChange", round(change, 4))
                        meta.setdefault(
                            "regularMarketChangePercent", round(change_pct, 4)
                        )
                    return [meta]

        # Legacy v6 envelope: quoteResponse.result (cached data compatibility)
        quote_response = data.get("quoteResponse", {})
        if isinstance(quote_response, dict):
            result = quote_response.get("result", [])
            if isinstance(result, list):
                return result
    return []


@_register("yahoo", "news")
def _yahoo_news(data: Any) -> list[dict]:
    """Yahoo Finance news: top-level list or {"news": {"items": [...]}}."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        news = data.get("news", {})
        if isinstance(news, dict):
            return news.get("items", [])
    return []


@_register("yahoo", "ohlcv")
def _yahoo_ohlcv(data: Any) -> list[dict]:
    """Yahoo Finance OHLCV via v8/chart: parallel arrays in indicators.quote.

    Response shape:
        {"chart": {"result": [{
            "timestamp": [epoch1, epoch2, ...],
            "indicators": {"quote": [{
                "open": [v1, v2, ...],
                "high": [...], "low": [...], "close": [...], "volume": [...]
            }]}
        }]}}

    Zips timestamps with OHLCV arrays into flat dicts.
    Yahoo returns None for market-closed bars — preserved as-is.
    """
    # Pre-extracted by multi-ticker adapter
    if isinstance(data, list):
        return data

    if not isinstance(data, dict):
        return []

    chart = data.get("chart", {})
    if not isinstance(chart, dict):
        return []

    result = chart.get("result", [])
    if not isinstance(result, list) or not result:
        return []

    first = result[0]
    timestamps = first.get("timestamp", [])
    if not timestamps:
        return []

    indicators = first.get("indicators", {})
    if not isinstance(indicators, dict):
        return []

    quotes = indicators.get("quote", [])
    if not isinstance(quotes, list) or not quotes:
        return []

    q = quotes[0]
    opens = q.get("open", [])
    highs = q.get("high", [])
    lows = q.get("low", [])
    closes = q.get("close", [])
    volumes = q.get("volume", [])

    records: list[dict] = []
    for i, ts in enumerate(timestamps):
        records.append(
            {
                "timestamp": ts,
                "open": opens[i] if i < len(opens) else None,
                "high": highs[i] if i < len(highs) else None,
                "low": lows[i] if i < len(lows) else None,
                "close": closes[i] if i < len(closes) else None,
                "volume": volumes[i] if i < len(volumes) else None,
            }
        )
    return records


# ---------------------------------------------------------------------------
# Polygon extractors
# ---------------------------------------------------------------------------


@_register("polygon", "ohlcv")
def _polygon_ohlcv(data: Any) -> list[dict]:
    """Polygon OHLCV: {"results": [...]}.

    AC-24: Normalizes millisecond UNIX timestamps (t > 1e12) to seconds.
    """
    if isinstance(data, dict):
        results = data.get("results", [])
        if isinstance(results, list):
            for rec in results:
                t = rec.get("t")
                if isinstance(t, (int, float)) and t > 1e12:
                    rec["t"] = int(t // 1000)
            return results
    return []


@_register("polygon", "quote")
def _polygon_quote(data: Any) -> list[dict]:
    """Polygon quote: {"results": [...]} or {"ticker": {...}} wrapper."""
    if isinstance(data, dict):
        results = data.get("results", [])
        if isinstance(results, list) and results:
            return results
        # Single ticker response: wrap in list
        if "ticker" in data and isinstance(data.get("last"), dict):
            return [data["last"]]
    return []


@_register("polygon", "news")
def _polygon_news(data: Any) -> list[dict]:
    """Polygon news: {"results": [...]}."""
    if isinstance(data, dict):
        results = data.get("results", [])
        if isinstance(results, list):
            return results
    return []


# ---------------------------------------------------------------------------
# Generic / fallback extractor
# ---------------------------------------------------------------------------


def _generic_extract(data: Any) -> list[dict]:
    """Fallback extractor for unknown providers.

    Handles:
    - Top-level list: return as-is
    - Top-level dict with a list-valued key: return first list found
    - Single dict: wrap in list
    """
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        # Look for the first list-valued key
        for value in data.values():
            if isinstance(value, list):
                return value
        # Single record dict
        return [data]
    return []


# ---------------------------------------------------------------------------
# Alpaca extractors (MEU-187)
# ---------------------------------------------------------------------------


@_register("alpaca", "ohlcv")
def _alpaca_ohlcv(data: Any) -> list[dict]:
    """Alpaca bars: {bars: {AAPL: [{...}], MSFT: [{...}]}} or root list."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        bars = data.get("bars", {})
        if isinstance(bars, dict):
            records: list[dict] = []
            for symbol, bar_list in bars.items():
                if isinstance(bar_list, list):
                    for bar in bar_list:
                        bar_copy = dict(bar)
                        bar_copy.setdefault("symbol", symbol)
                        records.append(bar_copy)
            if records:
                return records
    return _generic_extract(data)


@_register("alpaca", "quote")
def _alpaca_quote(data: Any) -> list[dict]:
    """Alpaca snapshot: flatten latestTrade/latestQuote/minuteBar."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        # Multi-snapshot: {snapshots: {AAPL: {...}, ...}}
        snapshots = data.get("snapshots", {})
        if isinstance(snapshots, dict) and snapshots:
            return [dict(v) for v in snapshots.values() if isinstance(v, dict)]
        # Single snapshot — flatten top-level sub-dicts
        flat: dict[str, Any] = {}
        for key, val in data.items():
            if isinstance(val, dict):
                flat.update(val)
            else:
                flat[key] = val
        if flat:
            return [flat]
    return []


@_register("alpaca", "news")
def _alpaca_news(data: Any) -> list[dict]:
    """Alpaca news: {news: [{...}]}."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        news = data.get("news", [])
        if isinstance(news, list):
            return news
    return []


# ---------------------------------------------------------------------------
# FMP extractors (MEU-187)
# ---------------------------------------------------------------------------


@_register("fmp", "quote")
def _fmp_quote(data: Any) -> list[dict]:
    """FMP quote: top-level array."""
    if isinstance(data, list):
        return data
    return _generic_extract(data)


@_register("fmp", "ohlcv")
def _fmp_ohlcv(data: Any) -> list[dict]:
    """FMP OHLCV: {symbol: 'X', historical: [{...}]}."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        historical = data.get("historical", [])
        if isinstance(historical, list):
            return historical
    return _generic_extract(data)


@_register("fmp", "earnings")
def _fmp_earnings(data: Any) -> list[dict]:
    """FMP earnings: top-level array."""
    if isinstance(data, list):
        return data
    return _generic_extract(data)


@_register("fmp", "dividends")
def _fmp_dividends(data: Any) -> list[dict]:
    """FMP dividends: {historical: [{...}]}."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        historical = data.get("historical", [])
        if isinstance(historical, list):
            return historical
    return _generic_extract(data)


@_register("fmp", "news")
def _fmp_news(data: Any) -> list[dict]:
    """FMP news: top-level array."""
    if isinstance(data, list):
        return data
    return _generic_extract(data)


@_register("fmp", "fundamentals")
def _fmp_fundamentals(data: Any) -> list[dict]:
    """FMP fundamentals (income statement): top-level array."""
    if isinstance(data, list):
        return data
    return _generic_extract(data)


@_register("fmp", "splits")
def _fmp_splits(data: Any) -> list[dict]:
    """FMP splits: {historical: [{...}]} wrapper."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        historical = data.get("historical", [])
        if isinstance(historical, list):
            return historical
    return _generic_extract(data)


# ---------------------------------------------------------------------------
# EODHD extractors (MEU-187)
# ---------------------------------------------------------------------------


@_register("eodhd", "ohlcv")
def _eodhd_ohlcv(data: Any) -> list[dict]:
    """EODHD EOD: top-level array."""
    if isinstance(data, list):
        return data
    return _generic_extract(data)


@_register("eodhd", "fundamentals")
def _eodhd_fundamentals(data: Any) -> list[dict]:
    """EODHD fundamentals: {General: {...}, Highlights: {...}, ...}.

    Flatten all sub-sections into a single record.
    """
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        flat: dict[str, Any] = {}
        for section_name, section_data in data.items():
            if isinstance(section_data, dict):
                for k, v in section_data.items():
                    flat[f"{section_name}.{k}"] = v
            else:
                flat[section_name] = section_data
        if flat:
            return [flat]
    return []


@_register("eodhd", "dividends")
def _eodhd_dividends(data: Any) -> list[dict]:
    """EODHD dividends: top-level array."""
    if isinstance(data, list):
        return data
    return _generic_extract(data)


@_register("eodhd", "news")
def _eodhd_news(data: Any) -> list[dict]:
    """EODHD news: top-level array."""
    if isinstance(data, list):
        return data
    return _generic_extract(data)


@_register("eodhd", "splits")
def _eodhd_splits(data: Any) -> list[dict]:
    """EODHD splits: top-level array."""
    if isinstance(data, list):
        return data
    return _generic_extract(data)


# ---------------------------------------------------------------------------
# API Ninjas extractors (MEU-187)
# ---------------------------------------------------------------------------


@_register("api_ninjas", "quote")
def _api_ninjas_quote(data: Any) -> list[dict]:
    """API Ninjas quote: single object → wrap in list."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return [data]
    return []


@_register("api_ninjas", "earnings")
def _api_ninjas_earnings(data: Any) -> list[dict]:
    """API Ninjas earnings: top-level array."""
    if isinstance(data, list):
        return data
    return _generic_extract(data)


# ---------------------------------------------------------------------------
# Tradier extractors (MEU-187)
# ---------------------------------------------------------------------------


@_register("tradier", "quote")
def _tradier_quote(data: Any) -> list[dict]:
    """Tradier quote: {quotes: {quote: {...} or [{...}]}}.

    Single-symbol returns a dict; multi-symbol returns a list.
    """
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        quotes = data.get("quotes", {})
        if isinstance(quotes, dict):
            quote = quotes.get("quote")
            if isinstance(quote, dict):
                return [quote]
            if isinstance(quote, list):
                return quote
    return _generic_extract(data)


@_register("tradier", "ohlcv")
def _tradier_ohlcv(data: Any) -> list[dict]:
    """Tradier OHLCV: {history: {day: [{...}]}}."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        history = data.get("history", {})
        if isinstance(history, dict):
            day = history.get("day", [])
            if isinstance(day, list):
                return day
            if isinstance(day, dict):
                return [day]
    return _generic_extract(data)


# ---------------------------------------------------------------------------
# Alpha Vantage extractors (MEU-188)
# ---------------------------------------------------------------------------


def _av_strip_prefix(data: dict[str, Any]) -> dict[str, Any]:
    """Strip Alpha Vantage numbered prefixes: '1. open' → 'open', '01. symbol' → 'symbol'."""
    return {re.sub(r"^\d+\.\s*", "", k): v for k, v in data.items()}


@_register("alpha_vantage", "ohlcv")
def _alpha_vantage_ohlcv(data: Any) -> list[dict]:
    """Alpha Vantage OHLCV: date-keyed dict + numbered prefix stripping.

    Pattern: {'Time Series (Daily)': {'2024-01-01': {'1. open': '150.00', ...}}}
    Rate-limit: {'Note': '...'} or {'Information': '...'} → empty list.
    """
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        # Rate-limit detection
        if "Note" in data or "Information" in data:
            logger.warning(
                "alpha_vantage_rate_limit",
                note=data.get("Note", data.get("Information")),
            )
            return []
        # Find the Time Series key (varies: 'Time Series (Daily)', 'Time Series (5min)', etc.)
        for key, value in data.items():
            if key.startswith("Time Series") and isinstance(value, dict):
                records: list[dict] = []
                for date_str, fields in value.items():
                    rec = _av_strip_prefix(fields)
                    rec["date"] = date_str
                    records.append(rec)
                return records
    return _generic_extract(data)


@_register("alpha_vantage", "quote")
def _alpha_vantage_quote(data: Any) -> list[dict]:
    """Alpha Vantage GLOBAL_QUOTE: {'Global Quote': {'01. symbol': ...}}."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        if "Note" in data or "Information" in data:
            return []
        gq = data.get("Global Quote", {})
        if isinstance(gq, dict) and gq:
            return [_av_strip_prefix(gq)]
    return _generic_extract(data)


@_register("alpha_vantage", "earnings")
def _alpha_vantage_earnings(data: Any) -> list[dict]:
    """Alpha Vantage earnings: JSON or CSV.

    CSV path is handled in extract_records() before JSON parsing.
    This handles the JSON envelope: {annualEarnings: [...], quarterlyEarnings: [...]}.
    """
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        if "Note" in data or "Information" in data:
            return []
        quarterly = data.get("quarterlyEarnings", [])
        if isinstance(quarterly, list) and quarterly:
            return quarterly
        annual = data.get("annualEarnings", [])
        if isinstance(annual, list) and annual:
            return annual
    return _generic_extract(data)


# ---------------------------------------------------------------------------
# Finnhub candle extractor (MEU-188)
# ---------------------------------------------------------------------------


@_register("finnhub", "ohlcv")
def _finnhub_ohlcv(data: Any) -> list[dict]:
    """Finnhub candle: zip parallel arrays {c:[], h:[], l:[], o:[], t:[], v:[]}.

    AC-22: s='ok' → zip arrays; s='no_data' → empty list.
    """
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        status = data.get("s", "")
        if status == "no_data":
            return []
        # Parallel array fields
        keys = ["c", "h", "l", "o", "t", "v"]
        arrays = [data.get(k, []) for k in keys]
        if all(isinstance(a, list) for a in arrays) and arrays[0]:
            return [dict(zip(keys, values)) for values in zip(*arrays)]
    return _generic_extract(data)


# ---------------------------------------------------------------------------
# Nasdaq Data Link extractor (MEU-188)
# ---------------------------------------------------------------------------


@_register("nasdaq_dl", "fundamentals")
def _nasdaq_dl_fundamentals(data: Any) -> list[dict]:
    """Nasdaq Data Link: {datatable: {data: [[...]], columns: [{name:...}]}}.

    AC-23: Zips column_names with data rows to create record dicts.
    """
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        datatable = data.get("datatable", {})
        if isinstance(datatable, dict):
            columns = datatable.get("columns", [])
            rows = datatable.get("data", [])
            if isinstance(columns, list) and isinstance(rows, list):
                col_names = [
                    c["name"] for c in columns if isinstance(c, dict) and "name" in c
                ]
                return [
                    dict(zip(col_names, row)) for row in rows if isinstance(row, list)
                ]
    return _generic_extract(data)


# ---------------------------------------------------------------------------
# TradingView Scanner extractors (Addendum)
# ---------------------------------------------------------------------------

# Column lists matching TradingViewUrlBuilder._COLUMN_MAP
_TV_QUOTE_COLUMNS = ["close", "volume", "change", "high", "low", "open", "name"]
_TV_FUNDAMENTALS_COLUMNS = [
    "market_cap_basic",
    "earnings_per_share_basic_ttm",
    "price_earnings_ttm",
    "dividend_yield_indication",
    "price_book_ratio",
    "debt_to_equity",
    "name",
]
_TV_COLUMN_MAP: dict[str, list[str]] = {
    "quote": _TV_QUOTE_COLUMNS,
    "fundamentals": _TV_FUNDAMENTALS_COLUMNS,
}


def _tradingview_scanner_extract(data: Any, data_type: str) -> list[dict]:
    """Shared extraction for TradingView scanner {data: [{s, d}]} envelope.

    Zips column names with d-array values for each record.
    """
    if not isinstance(data, dict):
        return _generic_extract(data)

    rows = data.get("data", [])
    if not isinstance(rows, list):
        return _generic_extract(data)

    columns = _TV_COLUMN_MAP.get(data_type, _TV_QUOTE_COLUMNS)
    records: list[dict] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        d_values = row.get("d", [])
        if not isinstance(d_values, list):
            continue
        record = dict(zip(columns, d_values))
        # Include symbol from "s" field if present
        s = row.get("s")
        if s:
            record["symbol"] = s
        records.append(record)
    return records


@_register("tradingview", "quote")
def _tradingview_quote(data: Any) -> list[dict]:
    """TradingView scanner quote: {data: [{s, d}]} → column-zip."""
    return _tradingview_scanner_extract(data, "quote")


@_register("tradingview", "fundamentals")
def _tradingview_fundamentals(data: Any) -> list[dict]:
    """TradingView scanner fundamentals: {data: [{s, d}]} → column-zip."""
    return _tradingview_scanner_extract(data, "fundamentals")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def extract_records(
    raw: bytes,
    provider: str,
    data_type: str,
) -> list[dict]:
    """Extract market data records from raw API response bytes.

    Handles provider-specific JSON envelopes:
      - Yahoo quote: quoteResponse.result
      - Polygon OHLCV: results
      - Generic: top-level list or first list-valued key

    Args:
        raw: Raw response bytes (must be valid JSON).
        provider: Data provider key (e.g., 'yahoo', 'polygon').
        data_type: Data type key (e.g., 'quote', 'ohlcv').

    Returns:
        List of record dicts. Empty list on parse failure or missing data.
    """
    if not raw:
        return []

    # Normalize provider display name to slug for registry lookup
    from zorivest_infra.market_data.field_mappings import _PROVIDER_SLUG_MAP

    slug = _PROVIDER_SLUG_MAP.get(provider, provider)

    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError):
        # AC-25: Alpha Vantage earnings CSV — try CSV parsing before giving up
        if slug in ("alpha_vantage",) and data_type == "earnings":
            try:
                text = raw.decode("utf-8")
                if "," in text and "\n" in text:
                    reader = csv.DictReader(io.StringIO(text))
                    return list(reader)
            except Exception:
                pass
        logger.warning(
            "response_extract_json_error",
            provider=provider,
            data_type=data_type,
            raw_length=len(raw),
        )
        return []

    # Look up provider-specific extractor
    extractor = _EXTRACTORS.get((slug, data_type))
    if extractor is not None:
        # Provider-specific extractor is authoritative: if it returns [],
        # that means the envelope structure was invalid — don't fallback.
        return extractor(data)

    # Fallback: generic extraction (no registered extractor for this combo)
    return _generic_extract(data)
