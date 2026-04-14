# packages/core/src/zorivest_core/services/validation_gate.py
"""Pandera validation gate for market data (§9.5c).

Provides OHLCV, Quote, News, and Fundamentals schema validation
and data quality checks.

Spec: 09-scheduling.md §9.5c
MEU: 86, PW3
"""

from __future__ import annotations

from typing import Any, cast

import pandas as pd
import pandera as pa
from pandera.errors import SchemaErrors


# ---------------------------------------------------------------------------
# OHLCV Schema: validates open/high/low/close > 0, volume >= 0
# ---------------------------------------------------------------------------


OHLCV_SCHEMA = pa.DataFrameSchema(
    {
        "open": pa.Column(float, pa.Check.gt(0), nullable=False),
        "high": pa.Column(float, pa.Check.gt(0), nullable=False),
        "low": pa.Column(float, pa.Check.gt(0), nullable=False),
        "close": pa.Column(float, pa.Check.gt(0), nullable=False),
        "volume": pa.Column(int, pa.Check.ge(0), nullable=False, coerce=True),
    },
    strict=False,  # Allow extra columns
)


# ---------------------------------------------------------------------------
# Quote Schema: validates last > 0, bid/ask nullable but > 0 when present
# ---------------------------------------------------------------------------


QUOTE_SCHEMA = pa.DataFrameSchema(
    {
        "ticker": pa.Column(str, nullable=False),
        "last": pa.Column(float, pa.Check.gt(0), nullable=False, coerce=True),
        "timestamp": pa.Column("datetime64[ns]", nullable=False, coerce=True),
        "provider": pa.Column(str, nullable=False),
        "bid": pa.Column(
            float, pa.Check.gt(0), nullable=True, required=False, coerce=True
        ),
        "ask": pa.Column(
            float, pa.Check.gt(0), nullable=True, required=False, coerce=True
        ),
        "volume": pa.Column(
            int, pa.Check.ge(0), nullable=True, required=False, coerce=True
        ),
    },
    strict=False,
)


# ---------------------------------------------------------------------------
# News Schema: validates headline non-empty, url starts with http,
# sentiment in [-1, 1]
# ---------------------------------------------------------------------------


NEWS_SCHEMA = pa.DataFrameSchema(
    {
        "headline": pa.Column(
            str,
            pa.Check(lambda s: s.str.len() > 0, error="headline must not be empty"),
            nullable=False,
        ),
        "source": pa.Column(str, nullable=False),
        "url": pa.Column(
            str,
            pa.Check(
                lambda s: s.str.startswith("http"), error="url must start with http"
            ),
            nullable=False,
        ),
        "published_at": pa.Column("datetime64[ns]", nullable=False, coerce=True),
        "sentiment": pa.Column(
            float,
            [pa.Check.ge(-1.0), pa.Check.le(1.0)],
            nullable=True,
            required=False,
            coerce=True,
        ),
    },
    strict=False,
)


# ---------------------------------------------------------------------------
# Fundamentals Schema: validates period format YYYY-(Q[1-4]|FY|H[12])
# ---------------------------------------------------------------------------


FUNDAMENTALS_SCHEMA = pa.DataFrameSchema(
    {
        "ticker": pa.Column(str, nullable=False),
        "metric": pa.Column(str, nullable=False),
        "value": pa.Column(float, nullable=False, coerce=True),
        "period": pa.Column(
            str,
            pa.Check(
                lambda s: s.str.match(r"^\d{4}-(Q[1-4]|FY|H[12])$"),
                error="period must match YYYY-(Q1-4|FY|H1-2)",
            ),
            nullable=False,
        ),
    },
    strict=False,
)


# ---------------------------------------------------------------------------
# Public schema registry (AC-5)
# ---------------------------------------------------------------------------

SCHEMA_REGISTRY: dict[str, pa.DataFrameSchema] = {
    "ohlcv": OHLCV_SCHEMA,
    "quote": QUOTE_SCHEMA,
    "news": NEWS_SCHEMA,
    "fundamentals": FUNDAMENTALS_SCHEMA,
}

# Internal alias for backward compatibility
_SCHEMAS = SCHEMA_REGISTRY


def validate_dataframe(
    df: pd.DataFrame,
    schema_name: str = "ohlcv",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Validate a DataFrame against a named schema.

    Returns:
        Tuple of (valid_rows, quarantined_rows).
        quarantined_rows contains records that failed validation.
    """
    schema = _SCHEMAS.get(schema_name)
    if schema is None:
        raise ValueError(f"Unknown schema: {schema_name}")

    try:
        valid = schema.validate(df, lazy=True)
        return cast(pd.DataFrame, valid), pd.DataFrame()
    except SchemaErrors as e:
        # Get indices of failed rows
        failure_indices = set()
        has_column_level_error = False
        for _, row in e.failure_cases.iterrows():
            idx = row.get("index")
            if idx is not None and not pd.isna(idx):
                failure_indices.add(idx)
            else:
                # Column-level error (e.g. missing required column)
                # — quarantine all rows
                has_column_level_error = True

        if has_column_level_error:
            return pd.DataFrame(), cast(pd.DataFrame, df.copy())

        valid_mask = ~df.index.isin(failure_indices)
        valid = cast(pd.DataFrame, df[valid_mask].copy())
        quarantined = cast(pd.DataFrame, df[~valid_mask].copy())
        return valid, quarantined


def check_quality(
    valid_count: int,
    total_count: int,
    threshold: float = 0.8,
) -> dict[str, Any]:
    """Check data quality ratio against threshold.

    Args:
        valid_count: Number of valid records.
        total_count: Total number of records.
        threshold: Minimum acceptable ratio (0.0–1.0).

    Returns:
        Dict with 'passed' (bool) and 'ratio' (float).
    """
    if total_count == 0:
        return {"passed": False, "ratio": 0.0}

    ratio = valid_count / total_count
    return {
        "passed": ratio >= threshold,
        "ratio": ratio,
    }
