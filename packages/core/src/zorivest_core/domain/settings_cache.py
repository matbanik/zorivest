# packages/core/src/zorivest_core/domain/settings_cache.py
"""Thread-safe in-memory settings cache with TTL expiry.

Source: 02a-backup-restore.md §2A.2c

Eliminates redundant DB reads for frequently-accessed settings.
"""

from __future__ import annotations

import time
from threading import Lock
from typing import Optional

from zorivest_core.domain.settings_resolver import ResolvedSetting


class SettingsCache:
    """Thread-safe in-memory settings cache with TTL expiry.

    Strategy:
    - Populated on startup from get_all_resolved()
    - Invalidated on writes (bulk_upsert, reset_to_default)
    - TTL-based staleness protection (default 60s)
    - Full cache flush on any write (simple strategy; no per-key tracking)
    """

    def __init__(self, ttl_seconds: int = 60) -> None:
        self._cache: dict[str, ResolvedSetting] = {}
        self._loaded_at: float = 0.0
        self._ttl = ttl_seconds
        self._lock = Lock()

    def get(self, key: str) -> Optional[ResolvedSetting]:
        """Read from cache. Returns None on cache miss or stale."""
        with self._lock:
            if self._is_stale():
                return None
            return self._cache.get(key)

    def get_all(self) -> Optional[dict[str, ResolvedSetting]]:
        """Return full cache dict, or None if stale/empty."""
        with self._lock:
            if self._is_stale() or not self._cache:
                return None
            return dict(self._cache)

    def populate(self, resolved: dict[str, ResolvedSetting]) -> None:
        """Bulk load resolved settings into cache."""
        with self._lock:
            self._cache = dict(resolved)
            self._loaded_at = time.monotonic()

    def invalidate(self) -> None:
        """Flush entire cache. Called after any write operation."""
        with self._lock:
            self._cache.clear()
            self._loaded_at = 0.0

    def _is_stale(self) -> bool:
        return (time.monotonic() - self._loaded_at) > self._ttl
