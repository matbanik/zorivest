# packages/infrastructure/src/zorivest_infra/market_data/field_mappings.py
"""Field mapping registry for market data transformations (§9.5a–b).

Maps provider-specific field names to canonical schema fields.
Unmapped fields are captured in the ``_extra`` key.

Spec: 09-scheduling.md §9.5a–b
MEU: 86
"""

from __future__ import annotations

from typing import Any


# Canonical OHLCV field mappings per provider.
# Key: (provider, data_type) → dict of {source_field: canonical_field}
FIELD_MAPPINGS: dict[tuple[str, str], dict[str, str]] = {
    ("generic", "ohlcv"): {
        "o": "open",
        "h": "high",
        "l": "low",
        "c": "close",
        "v": "volume",
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
    mapping = FIELD_MAPPINGS.get((provider, data_type), {})

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
