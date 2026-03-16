# packages/infrastructure/src/zorivest_infra/repositories/write_dispositions.py
"""Write dispositions for pipeline data persistence (§9.5d).

Security-first write layer: only allow writes to pre-approved tables
with pre-approved columns. Supports append, replace, and merge modes.

Spec: 09-scheduling.md §9.5d
MEU: 86
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session


# Tables approved for pipeline write operations.
# Key: table_name → set of allowed column names.
TABLE_ALLOWLIST: dict[str, set[str]] = {
    "market_ohlcv": {
        "ticker", "open", "high", "low", "close", "volume",
        "vwap", "trade_count", "timestamp", "provider", "data_type",
    },
    "market_quotes": {
        "ticker", "bid", "ask", "last", "volume", "timestamp", "provider",
    },
    "market_news": {
        "ticker", "headline", "summary", "source", "url", "published_at",
        "sentiment", "provider",
    },
    "market_fundamentals": {
        "ticker", "metric", "value", "period", "provider", "fetched_at",
    },
}


def validate_table(table_name: str) -> bool:
    """Check if a table is in the write allowlist."""
    return table_name in TABLE_ALLOWLIST


def validate_columns(table_name: str, columns: list[str]) -> bool:
    """Check if all columns are allowed for the given table."""
    if table_name not in TABLE_ALLOWLIST:
        return False
    allowed = TABLE_ALLOWLIST[table_name]
    return all(col in allowed for col in columns)


def write_append(
    *,
    session: Session,
    table_name: str,
    records: list[dict[str, Any]],
) -> int:
    """Append records to a table.

    Args:
        session: Active SQLAlchemy session.
        table_name: Target table (must be in TABLE_ALLOWLIST).
        records: List of dicts to insert.

    Returns:
        Number of records inserted.
    """
    if not records:
        return 0

    if not validate_table(table_name):
        raise ValueError(f"Table '{table_name}' not in write allowlist")

    columns = list(records[0].keys())
    if not validate_columns(table_name, columns):
        invalid = [c for c in columns if c not in TABLE_ALLOWLIST.get(table_name, set())]
        raise ValueError(f"Columns not allowed for '{table_name}': {invalid}")

    placeholders = ", ".join(f":{col}" for col in columns)
    col_names = ", ".join(columns)
    sql = text(f"INSERT INTO {table_name} ({col_names}) VALUES ({placeholders})")

    for record in records:
        session.execute(sql, record)

    return len(records)


def write_replace(
    *,
    session: Session,
    table_name: str,
    records: list[dict[str, Any]],
) -> int:
    """Replace all rows in a table with new records.

    Args:
        session: Active SQLAlchemy session.
        table_name: Target table.
        records: Replacement records.

    Returns:
        Number of records inserted.
    """
    if not validate_table(table_name):
        raise ValueError(f"Table '{table_name}' not in write allowlist")

    session.execute(text(f"DELETE FROM {table_name}"))
    return write_append(session=session, table_name=table_name, records=records)


def write_merge(
    *,
    session: Session,
    table_name: str,
    records: list[dict[str, Any]],
    key_columns: list[str],
) -> int:
    """Merge (upsert) records into a table based on key columns.

    Uses INSERT OR REPLACE for SQLite.
    """
    if not records:
        return 0

    if not validate_table(table_name):
        raise ValueError(f"Table '{table_name}' not in write allowlist")

    columns = list(records[0].keys())
    placeholders = ", ".join(f":{col}" for col in columns)
    col_names = ", ".join(columns)
    sql = text(
        f"INSERT OR REPLACE INTO {table_name} ({col_names}) VALUES ({placeholders})"
    )

    for record in records:
        session.execute(sql, record)

    return len(records)
