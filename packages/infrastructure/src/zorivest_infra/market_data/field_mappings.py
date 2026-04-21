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
