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

import json
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


# ---------------------------------------------------------------------------
# Polygon extractors
# ---------------------------------------------------------------------------


@_register("polygon", "ohlcv")
def _polygon_ohlcv(data: Any) -> list[dict]:
    """Polygon OHLCV: {"results": [...]}."""
    if isinstance(data, dict):
        results = data.get("results", [])
        if isinstance(results, list):
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

    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError):
        logger.warning(
            "response_extract_json_error",
            provider=provider,
            data_type=data_type,
            raw_length=len(raw),
        )
        return []

    # Normalize provider display name to slug for registry lookup
    from zorivest_infra.market_data.field_mappings import _PROVIDER_SLUG_MAP

    slug = _PROVIDER_SLUG_MAP.get(provider, provider)

    # Look up provider-specific extractor
    extractor = _EXTRACTORS.get((slug, data_type))
    if extractor is not None:
        # Provider-specific extractor is authoritative: if it returns [],
        # that means the envelope structure was invalid — don't fallback.
        return extractor(data)

    # Fallback: generic extraction (no registered extractor for this combo)
    return _generic_extract(data)
