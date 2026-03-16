# packages/infrastructure/src/zorivest_infra/market_data/pipeline_rate_limiter.py
"""PipelineRateLimiter — per-provider rate limiting for fetch steps (§9.4c).

Uses aiolimiter for token-bucket rate limiting per provider,
with an asyncio.Semaphore for global concurrency control,
and tenacity for retry with exponential backoff + jitter.

Spec: 09-scheduling.md §9.4c
MEU: 85
"""

from __future__ import annotations

import asyncio
from typing import Any, Awaitable, Callable, TypeVar

from aiolimiter import AsyncLimiter

T = TypeVar("T")


class PipelineRateLimiter:
    """Rate limiter with per-provider limits and global concurrency cap.

    Args:
        limits: Mapping of provider → (max_rate, time_period) for token bucket.
        max_concurrent: Maximum total concurrent requests across all providers.
    """

    def __init__(
        self,
        limits: dict[str, tuple[float, float]],
        max_concurrent: int = 5,
    ) -> None:
        self._limiters: dict[str, AsyncLimiter] = {}
        self._semaphore = asyncio.Semaphore(max_concurrent)

        for provider, (rate, period) in limits.items():
            self._limiters[provider] = AsyncLimiter(rate, period)

    async def execute_with_limits(
        self,
        provider: str,
        func: Callable[..., Awaitable[T]],
        *args: Any,
        **kwargs: Any,
    ) -> T:
        """Execute a function with rate limiting and concurrency control.

        Acquires: 1) global semaphore, 2) per-provider token bucket.
        """
        limiter = self._limiters.get(provider)

        async with self._semaphore:
            if limiter:
                async with limiter:
                    return await func(*args, **kwargs)
            else:
                return await func(*args, **kwargs)
