# tests/integration/test_pipeline_fetch_e2e.py
"""TDD Red-phase integration tests for Fetch Step pipeline (MEU-PW2).

AC-7: fetch→transform pipeline completes with mocked HTTP returning OHLCV JSON.

Test Scenarios:
1. Happy path: Mock HTTP returns OHLCV JSON → FetchStep succeeds → data in output
2. Cache hit: Second call returns cache hit without HTTP
3. Rate limiter invoked: Mock rate limiter records call count
4. ETag revalidation: Mock returns 304 → adapter returns cached content
5. Market-closed TTL extension: Extended TTL verified
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.mark.asyncio
async def test_PW2_AC7_fetch_step_happy_path_ohlcv():
    """FetchStep with a real adapter (mocked HTTP) successfully fetches OHLCV data."""
    from zorivest_core.domain.pipeline import StepContext
    from zorivest_core.pipeline_steps.fetch_step import FetchStep
    from zorivest_infra.market_data.market_data_adapter import (
        MarketDataProviderAdapter,
    )

    # Mock HTTP client
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b'{"results": [{"c": 150, "h": 155, "l": 148}]}'
    mock_response.headers = {"ETag": "etag-fresh", "Last-Modified": "Mon, 16 Mar 2026"}
    mock_client.get.return_value = mock_response

    # Mock rate limiter (pass-through)
    mock_rate_limiter = AsyncMock()

    async def _passthrough(provider, func, *a, **kw):
        return await func(*a, **kw)

    mock_rate_limiter.execute_with_limits = AsyncMock(side_effect=_passthrough)

    adapter = MarketDataProviderAdapter(
        http_client=mock_client,
        rate_limiter=mock_rate_limiter,
    )

    step = FetchStep()
    context = StepContext(
        run_id="run-e2e-1",
        policy_id="pol-e2e-1",
        outputs={"provider_adapter": adapter},
    )

    result = await step.execute(
        params={
            "provider": "Polygon.io",
            "data_type": "ohlcv",
            "criteria": {"symbol": "AAPL"},
            "use_cache": False,
        },
        context=context,
    )

    assert result.status.value == "success"
    assert result.output["content"] is not None
    assert result.output["content_len"] > 0
    assert result.output["provider"] == "Polygon.io"
    assert result.output["data_type"] == "ohlcv"


@pytest.mark.asyncio
async def test_PW2_AC7_cache_hit_skips_http():
    """Second fetch with warm cache returns cached data without HTTP call."""
    from zorivest_core.domain.pipeline import StepContext
    from zorivest_core.pipeline_steps.fetch_step import FetchStep

    step = FetchStep()

    # Mock cache repo with fresh entry
    mock_cache_repo = MagicMock()
    mock_entry = MagicMock()
    mock_entry.payload_json = '{"results": [{"c": 150}]}'
    mock_entry.content_hash = "cached-hash"
    mock_entry.etag = "etag-cached"
    mock_entry.last_modified = "Mon, 16 Mar 2026"
    mock_entry.ttl_seconds = 3600
    mock_entry.fetched_at = datetime(2026, 3, 16, 14, 59, tzinfo=timezone.utc)
    mock_cache_repo.get_cached.return_value = mock_entry

    mock_adapter = AsyncMock()
    # Should NOT be called if cache hit

    context = StepContext(
        run_id="run-e2e-2",
        policy_id="pol-e2e-2",
        outputs={
            "provider_adapter": mock_adapter,
            "fetch_cache_repo": mock_cache_repo,
        },
    )

    with patch("zorivest_core.pipeline_steps.fetch_step.datetime") as mock_dt:
        mock_dt.now.return_value = datetime(2026, 3, 16, 15, 0, tzinfo=timezone.utc)
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

        result = await step.execute(
            params={
                "provider": "Polygon.io",
                "data_type": "ohlcv",
                "criteria": {"symbol": "AAPL"},
                "use_cache": True,
            },
            context=context,
        )

    assert result.status.value == "success"
    assert result.output["cache_status"] == "hit"
    # Adapter should NOT have been called
    mock_adapter.fetch.assert_not_called()


@pytest.mark.asyncio
async def test_PW2_AC7_rate_limiter_called_during_fetch():
    """Integration: rate limiter is invoked during adapter fetch."""
    from zorivest_core.domain.pipeline import StepContext
    from zorivest_core.pipeline_steps.fetch_step import FetchStep
    from zorivest_infra.market_data.market_data_adapter import (
        MarketDataProviderAdapter,
    )

    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b'{"data": [1]}'
    mock_response.headers = {}
    mock_client.get.return_value = mock_response

    call_count = 0

    async def counting_execute(provider, func, *args, **kwargs):
        nonlocal call_count
        call_count += 1
        return await func(*args, **kwargs)

    mock_rate_limiter = MagicMock()
    mock_rate_limiter.execute_with_limits = AsyncMock(side_effect=counting_execute)

    adapter = MarketDataProviderAdapter(
        http_client=mock_client,
        rate_limiter=mock_rate_limiter,
    )

    step = FetchStep()
    context = StepContext(
        run_id="run-e2e-3",
        policy_id="pol-e2e-3",
        outputs={"provider_adapter": adapter},
    )

    await step.execute(
        params={
            "provider": "Polygon.io",
            "data_type": "ohlcv",
            "criteria": {"symbol": "AAPL"},
            "use_cache": False,
        },
        context=context,
    )

    assert call_count == 1


@pytest.mark.asyncio
async def test_PW2_AC7_etag_revalidation_304():
    """Integration: stale cache entry triggers 304 revalidation through execute().

    End-to-end path: stale cache → _check_cache returns stale metadata →
    _fetch_from_provider forwards cached_etag to adapter → adapter sends
    If-None-Match → HTTP returns 304 → adapter returns revalidated content.
    """
    from zorivest_core.domain.pipeline import StepContext
    from zorivest_core.pipeline_steps.fetch_step import FetchStep
    from zorivest_infra.market_data.market_data_adapter import (
        MarketDataProviderAdapter,
    )

    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.status_code = 304
    mock_response.headers = {}
    mock_client.get.return_value = mock_response

    mock_rate_limiter = AsyncMock()

    async def _passthrough(provider, func, *a, **kw):
        return await func(*a, **kw)

    mock_rate_limiter.execute_with_limits = AsyncMock(side_effect=_passthrough)

    adapter = MarketDataProviderAdapter(
        http_client=mock_client,
        rate_limiter=mock_rate_limiter,
    )

    # Stale cache entry — TTL expired but entry exists with ETag
    mock_cache_repo = MagicMock()
    mock_entry = MagicMock()
    mock_entry.payload_json = '{"old": "ohlcv"}'
    mock_entry.content_hash = "hash-old"
    mock_entry.etag = "etag-old"
    mock_entry.last_modified = None
    mock_entry.ttl_seconds = 60  # 1-minute TTL
    # fetched_at is 5 minutes ago — stale (5min > 1min TTL)
    from datetime import datetime, timezone

    mock_entry.fetched_at = datetime(2026, 3, 16, 14, 55, tzinfo=timezone.utc)
    mock_cache_repo.get_cached.return_value = mock_entry

    step = FetchStep()
    context = StepContext(
        run_id="run-e2e-4",
        policy_id="pol-e2e-4",
        outputs={
            "provider_adapter": adapter,
            "fetch_cache_repo": mock_cache_repo,
        },
    )

    with patch("zorivest_core.pipeline_steps.fetch_step.datetime") as mock_dt:
        # 15:00 UTC on Monday (during market hours, TTL expired)
        mock_dt.now.return_value = datetime(2026, 3, 16, 15, 0, tzinfo=timezone.utc)
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

        result = await step.execute(
            params={
                "provider": "Polygon.io",
                "data_type": "ohlcv",
                "criteria": {"symbol": "AAPL"},
                "use_cache": True,
            },
            context=context,
        )

    # The step should return revalidated content from the adapter
    assert result.output["cache_status"] == "revalidated"
    assert result.output["content"] == '{"old": "ohlcv"}'


@pytest.mark.asyncio
async def test_PW2_AC7_market_closed_ttl_extension():
    """Integration: market-closed hours extend cache TTL for ohlcv."""
    from zorivest_core.domain.pipeline import StepContext
    from zorivest_core.pipeline_steps.fetch_step import FetchStep

    step = FetchStep()

    mock_cache_repo = MagicMock()
    mock_entry = MagicMock()
    mock_entry.payload_json = '{"data": "weekend_ohlcv"}'
    mock_entry.content_hash = "hash-weekend"
    mock_entry.etag = "etag-wknd"
    mock_entry.last_modified = None
    mock_entry.ttl_seconds = 3600  # 1-hour
    # fetched_at is 3 hours ago — stale w/ base TTL, fresh w/ 4x (4hr)
    mock_entry.fetched_at = datetime(2026, 3, 14, 9, 0, tzinfo=timezone.utc)
    mock_cache_repo.get_cached.return_value = mock_entry

    mock_adapter = AsyncMock()

    context = StepContext(
        run_id="run-e2e-5",
        policy_id="pol-e2e-5",
        outputs={
            "provider_adapter": mock_adapter,
            "fetch_cache_repo": mock_cache_repo,
        },
    )

    # Saturday 12:00 UTC — market closed
    with patch("zorivest_core.pipeline_steps.fetch_step.datetime") as mock_dt:
        mock_dt.now.return_value = datetime(2026, 3, 14, 12, 0, tzinfo=timezone.utc)
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

        result = await step.execute(
            params={
                "provider": "Polygon.io",
                "data_type": "ohlcv",
                "criteria": {"symbol": "AAPL"},
                "use_cache": True,
            },
            context=context,
        )

    assert result.status.value == "success"
    assert result.output["cache_status"] == "hit"
    mock_adapter.fetch.assert_not_called()
