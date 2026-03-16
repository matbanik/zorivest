# packages/core/src/zorivest_core/services/validation_gate.py
"""Pandera validation gate for market data (§9.5c).

Provides OHLCV schema validation and data quality checks.

Spec: 09-scheduling.md §9.5c
MEU: 86
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

# Schema registry by name
_SCHEMAS: dict[str, pa.DataFrameSchema] = {
    "ohlcv": OHLCV_SCHEMA,
}


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
        for _, row in e.failure_cases.iterrows():
            idx = row.get("index")
            if idx is not None:
                failure_indices.add(idx)

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
