"""Async token-bucket rate limiter — MEU-62.

Per-provider rate limiter using a sliding-window deque.
Source: docs/build-plan/08-market-data.md §8.2e.
"""

from __future__ import annotations

import asyncio
import time
from collections import deque


class RateLimiter:
    """Token-bucket rate limiter per provider.

    Uses a sliding 60-second window to enforce a maximum number
    of requests per minute.
    """

    def __init__(self, max_per_minute: int) -> None:
        self.max_per_minute = max_per_minute
        self.timestamps: deque[float] = deque()

    async def wait_if_needed(self) -> None:
        """Block until a request slot is available.

        Evicts expired timestamps (older than 60s), then sleeps
        if the window is full.
        """
        now = time.time()
        # Evict expired timestamps
        while self.timestamps and self.timestamps[0] < now - 60:
            self.timestamps.popleft()

        # Block if window is full
        if len(self.timestamps) >= self.max_per_minute:
            sleep_time = 60 - (now - self.timestamps[0])
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)

        self.timestamps.append(time.time())
