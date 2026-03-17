"""Tests for token-bucket rate limiter — MEU-62.

FIC-62 acceptance criteria (rate limiter portion):
AC-1: RateLimiter(max_per_minute=N) enforces N requests per 60s window
AC-2: wait_if_needed() is async and blocks when full
AC-3: Expired timestamps are evicted on each call
AC-4: Burst of N completes without blocking; N+1 blocks
"""

from __future__ import annotations

import asyncio
import time
from unittest.mock import AsyncMock, patch

from zorivest_infra.market_data.rate_limiter import RateLimiter


class TestRateLimiterAC1:
    """AC-1: Enforces N requests per 60-second sliding window."""

    def test_max_per_minute_stored(self) -> None:
        rl = RateLimiter(max_per_minute=10)
        assert rl.max_per_minute == 10

    def test_timestamps_deque_starts_empty(self) -> None:
        rl = RateLimiter(max_per_minute=5)
        assert len(rl.timestamps) == 0


class TestRateLimiterAC2:
    """AC-2: wait_if_needed() is async and blocks when window is full."""

    def test_wait_if_needed_is_coroutine(self) -> None:
        rl = RateLimiter(max_per_minute=5)
        assert asyncio.iscoroutinefunction(rl.wait_if_needed)

    def test_blocks_when_full(self) -> None:
        """After N calls, the N+1 call should trigger asyncio.sleep."""

        async def _run() -> None:
            rl = RateLimiter(max_per_minute=2)
            await rl.wait_if_needed()
            await rl.wait_if_needed()
            # Value: verify 2 timestamps recorded
            assert len(rl.timestamps) == 2

            with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
                await rl.wait_if_needed()
                mock_sleep.assert_called_once()
                # Value: verify sleep time is positive and <= 60
                sleep_time = mock_sleep.call_args[0][0]
                assert 0 < sleep_time <= 60

        asyncio.run(_run())


class TestRateLimiterAC3:
    """AC-3: Expired timestamps (older than 60s) are evicted on each call."""

    def test_expired_timestamps_evicted(self) -> None:
        async def _run() -> None:
            rl = RateLimiter(max_per_minute=2)
            old_time = time.time() - 61
            rl.timestamps.append(old_time)
            assert len(rl.timestamps) == 1

            await rl.wait_if_needed()
            assert len(rl.timestamps) == 1
            assert rl.timestamps[0] > old_time

        asyncio.run(_run())


class TestRateLimiterAC4:
    """AC-4: Burst of N completes without blocking; request N+1 blocks."""

    def test_burst_completes_without_blocking(self) -> None:
        async def _run() -> None:
            rl = RateLimiter(max_per_minute=3)
            with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
                for _ in range(3):
                    await rl.wait_if_needed()
                mock_sleep.assert_not_called()
                # Value: verify all 3 timestamps were recorded
                assert len(rl.timestamps) == 3

        asyncio.run(_run())

    def test_n_plus_1_blocks(self) -> None:
        async def _run() -> None:
            rl = RateLimiter(max_per_minute=3)
            for _ in range(3):
                await rl.wait_if_needed()
            # Value: verify exactly 3 timestamps before blocking
            assert len(rl.timestamps) == 3

            with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
                await rl.wait_if_needed()
                mock_sleep.assert_called_once()
                sleep_time = mock_sleep.call_args[0][0]
                assert 0 < sleep_time <= 60

        asyncio.run(_run())
