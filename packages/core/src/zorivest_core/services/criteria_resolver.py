# packages/core/src/zorivest_core/services/criteria_resolver.py
"""CriteriaResolver — resolves fetch criteria to concrete values (§9.4b).

Supports per-field resolution with static passthrough:
- relative: date math (e.g., "-30d", "-7d")
- incremental: high-water mark from pipeline_state table
- db_query: read-only SQL query
- static: plain value passthrough (no "type" key)

Spec: 09-scheduling.md §9.4b (lines 1461-1468)
MEU: 85
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any


class CriteriaResolver:
    """Resolves per-field fetch criteria definitions.

    Each field in the criteria dict is resolved independently:
    - If value is a dict with a "type" key → resolve via typed resolver
    - Otherwise → pass through unchanged (static value)
    """

    def __init__(
        self,
        pipeline_state_repo: Any = None,
        db_connection: Any = None,
    ) -> None:
        self._state_repo = pipeline_state_repo
        self._db_connection = db_connection

    def resolve(self, criteria: dict[str, Any]) -> dict[str, Any]:
        """Resolve criteria per-field with static passthrough.

        Args:
            criteria: Dict where each value is either:
                - A dict with 'type' key → resolved via _resolve_typed()
                - Any other value → passed through unchanged

        Returns:
            Dict with resolved values for typed fields and
            original values for static fields.
        """
        resolved: dict[str, Any] = {}
        for key, value in criteria.items():
            if isinstance(value, dict) and "type" in value:
                resolved[key] = self._resolve_typed(value)
            else:
                resolved[key] = value  # Static passthrough
        return resolved

    def _resolve_typed(self, spec: dict[str, Any]) -> Any:
        """Dispatch a single typed field to its resolver."""
        ctype = spec["type"]

        if ctype == "relative":
            return self._resolve_relative(spec)
        elif ctype == "incremental":
            return self._resolve_incremental(spec)
        elif ctype == "db_query":
            return self._resolve_db_query(spec)
        else:
            raise ValueError(f"Unknown criteria type: {ctype}")

    def _resolve_relative(self, spec: dict[str, Any]) -> dict[str, Any]:
        """Resolve relative date expressions like '-30d'."""
        expr = spec.get("expr", "-1d")
        now = datetime.now(timezone.utc)

        # Parse expression: -Nd where N is number of days
        if expr.startswith("-") and expr.endswith("d"):
            days = int(expr[1:-1])
            start = now - timedelta(days=days)
        else:
            raise ValueError(f"Invalid relative expression: {expr}")

        return {
            "start_date": start,
            "end_date": now,
        }

    def _resolve_incremental(self, spec: dict[str, Any]) -> dict[str, Any]:
        """Resolve incremental criteria using pipeline state high-water mark."""
        if self._state_repo is None:
            raise ValueError("pipeline_state_repo required for incremental criteria")

        state = self._state_repo.get(
            policy_id=spec["policy_id"],
            provider_id=spec["provider_id"],
            data_type=spec["data_type"],
            entity_key=spec.get("entity_key", ""),
        )

        now = datetime.now(timezone.utc)

        if state is not None:
            # Start from the last known value
            start = datetime.fromisoformat(state.last_cursor)
        else:
            # No prior state — fetch last 30 days as default
            start = now - timedelta(days=30)

        return {
            "start_date": start,
            "end_date": now,
        }

    def _resolve_db_query(self, spec: dict[str, Any]) -> dict[str, Any]:
        """Resolve criteria via read-only SQL query.

        Executes a sandboxed SQL query that returns start_date, end_date
        as the first two columns of the first row.
        """
        if self._db_connection is None:
            raise ValueError(
                "db_connection required for db_query criteria resolution"
            )

        sql = spec.get("sql", "")
        if not sql:
            raise ValueError("db_query criteria requires 'sql' field")

        cursor = self._db_connection.execute(sql)
        row = cursor.fetchone()

        now = datetime.now(timezone.utc)

        if row is None or len(row) < 2:
            return {
                "start_date": now - timedelta(days=30),
                "end_date": now,
            }

        start_raw, end_raw = row[0], row[1]
        if isinstance(start_raw, str):
            start_raw = datetime.fromisoformat(start_raw)
        if isinstance(end_raw, str):
            end_raw = datetime.fromisoformat(end_raw)

        return {
            "start_date": start_raw,
            "end_date": end_raw,
        }
