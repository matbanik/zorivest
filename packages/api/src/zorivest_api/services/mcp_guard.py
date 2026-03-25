"""MCP Guard Service — circuit breaker for MCP tool access.

Source: 04g-api-system.md §MCP Guard Routes
MEU: MEU-90a (moved from stubs.py, where it was in-process for MEU-38)
"""

from __future__ import annotations

import time as _time
from datetime import datetime, timezone
from typing import Any


class McpGuardService:
    """In-memory MCP guard — circuit breaker for MCP tool access.

    Source: 04g-api-system.md §MCP Guard Routes
    No __getattr__ — explicit methods only.
    """

    def __init__(self) -> None:
        self._is_enabled: bool = False
        self._is_locked: bool = False
        self._locked_at: str | None = None
        self._lock_reason: str | None = None
        self._calls_per_minute_limit: int = 60
        self._calls_per_hour_limit: int = 1000
        self._recent_calls: list[float] = []

    def _state_dict(self) -> dict[str, Any]:
        """Build state dict for route responses."""
        now = _time.time()
        calls_1min = sum(1 for t in self._recent_calls if now - t < 60)
        calls_1hr = sum(1 for t in self._recent_calls if now - t < 3600)
        return {
            "is_enabled": self._is_enabled,
            "is_locked": self._is_locked,
            "locked_at": self._locked_at,
            "lock_reason": self._lock_reason,
            "calls_per_minute_limit": self._calls_per_minute_limit,
            "calls_per_hour_limit": self._calls_per_hour_limit,
            "recent_calls_1min": calls_1min,
            "recent_calls_1hr": calls_1hr,
        }

    def get_status(self) -> dict[str, Any]:
        return self._state_dict()

    def update_config(self, config: dict[str, Any]) -> dict[str, Any]:
        if "is_enabled" in config:
            self._is_enabled = config["is_enabled"]
        if "calls_per_minute_limit" in config:
            self._calls_per_minute_limit = config["calls_per_minute_limit"]
        if "calls_per_hour_limit" in config:
            self._calls_per_hour_limit = config["calls_per_hour_limit"]
        return self._state_dict()

    def lock(self, reason: str = "manual") -> dict[str, Any]:
        self._is_locked = True
        self._locked_at = datetime.now(timezone.utc).isoformat()
        self._lock_reason = reason
        return self._state_dict()

    def unlock(self) -> dict[str, Any]:
        self._is_locked = False
        self._locked_at = None
        self._lock_reason = None
        return self._state_dict()

    def check(self) -> dict[str, Any]:
        if not self._is_enabled:
            return {"allowed": True, "reason": "guard_disabled"}
        if self._is_locked:
            return {"allowed": False, "reason": self._lock_reason or "locked"}

        now = _time.time()
        self._recent_calls.append(now)
        # Prune old entries
        self._recent_calls = [t for t in self._recent_calls if now - t < 3600]

        calls_1min = sum(1 for t in self._recent_calls if now - t < 60)
        if calls_1min > self._calls_per_minute_limit:
            self.lock("rate_limit_exceeded")
            return {"allowed": False, "reason": "rate_limit_exceeded"}

        return {"allowed": True, "reason": "ok"}
