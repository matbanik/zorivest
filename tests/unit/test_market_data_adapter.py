# tests/unit/test_market_data_adapter.py
"""TDD Red-phase tests for MarketDataProviderAdapter (MEU-PW2).

Acceptance criteria AC-1, AC-2, AC-5, AC-6 per implementation-plan.md.

AC-1: MarketDataAdapterPort protocol + FetchAdapterResult TypedDict
AC-2: Adapter dispatches per data_type, returns FetchAdapterResult
AC-5: Every HTTP call goes through PipelineRateLimiter
AC-6: ETag/If-Modified-Since headers sent via fetch_with_cache
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest


# ---------------------------------------------------------------------------
# AC-1: MarketDataAdapterPort protocol + FetchAdapterResult TypedDict
# ---------------------------------------------------------------------------


def test_AC1_port_protocol_exists():
    """MarketDataAdapterPort is importable from ports.py."""
    from zorivest_core.application.ports import MarketDataAdapterPort

    assert hasattr(MarketDataAdapterPort, "fetch")


def test_AC1_fetch_adapter_result_exists():
    """FetchAdapterResult TypedDict is importable from ports.py."""
    from zorivest_core.application.ports import FetchAdapterResult

    # TypedDict should have the expected keys
    assert "content" in FetchAdapterResult.__annotations__
    assert "cache_status" in FetchAdapterResult.__annotations__
    assert "etag" in FetchAdapterResult.__annotations__
    assert "last_modified" in FetchAdapterResult.__annotations__


def test_AC1_port_fetch_signature():
    """MarketDataAdapterPort.fetch() has the correct keyword-only parameters."""
    import inspect

    from zorivest_core.application.ports import MarketDataAdapterPort

    sig = inspect.signature(MarketDataAdapterPort.fetch)
    params = sig.parameters

    # Required keyword args
    assert "provider" in params
    assert "data_type" in params
    assert "criteria" in params

    # Optional keyword args with defaults
    assert "cached_content" in params
    assert params["cached_content"].default is None
    assert "cached_etag" in params
    assert params["cached_etag"].default is None
    assert "cached_last_modified" in params
    assert params["cached_last_modified"].default is None


# ---------------------------------------------------------------------------
# AC-2: Adapter dispatches per data_type, returns FetchAdapterResult
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_AC2_adapter_returns_fetch_adapter_result_ohlcv():
    """MarketDataProviderAdapter.fetch() returns FetchAdapterResult dict
    with content, cache_status, etag, last_modified for ohlcv data type."""
    from zorivest_infra.market_data.market_data_adapter import (
        MarketDataProviderAdapter,
    )

    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b'{"results": [1, 2, 3]}'
    mock_response.headers = {"ETag": "etag-abc", "Last-Modified": "Wed, 01 Jan 2026"}
    mock_client.get.return_value = mock_response

    mock_rate_limiter = AsyncMock()

    async def _passthrough(provider, func, *a, **kw):
        return await func(*a, **kw)

    mock_rate_limiter.execute_with_limits = AsyncMock(side_effect=_passthrough)

    adapter = MarketDataProviderAdapter(
        http_client=mock_client,
        rate_limiter=mock_rate_limiter,
    )

    result = await adapter.fetch(
        provider="Polygon.io",
        data_type="ohlcv",
        criteria={
            "symbol": "AAPL",
            "date_range": {"start_date": "2026-01-01", "end_date": "2026-01-31"},
        },
    )

    assert isinstance(result, dict)
    assert "content" in result
    assert "cache_status" in result
    assert "etag" in result
    assert "last_modified" in result
    assert isinstance(result["content"], bytes)


@pytest.mark.asyncio
async def test_AC2_adapter_dispatches_quote():
    """Adapter handles 'quote' data_type."""
    from zorivest_infra.market_data.market_data_adapter import (
        MarketDataProviderAdapter,
    )

    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b'{"c": 150.0}'
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

    result = await adapter.fetch(
        provider="Finnhub",
        data_type="quote",
        criteria={"symbol": "AAPL"},
    )

    assert isinstance(result, dict)
    assert result["cache_status"] in ("miss", "hit", "revalidated")


@pytest.mark.asyncio
async def test_AC2_adapter_rejects_unknown_data_type():
    """Adapter raises ValueError for unknown data_type."""
    from zorivest_infra.market_data.market_data_adapter import (
        MarketDataProviderAdapter,
    )

    mock_client = AsyncMock()
    mock_rate_limiter = AsyncMock()

    adapter = MarketDataProviderAdapter(
        http_client=mock_client,
        rate_limiter=mock_rate_limiter,
    )

    with pytest.raises(ValueError, match="data_type"):
        await adapter.fetch(
            provider="Polygon.io",
            data_type="invalid_type",
            criteria={"symbol": "AAPL"},
        )


# ---------------------------------------------------------------------------
# AC-5: Every HTTP call goes through PipelineRateLimiter
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_AC5_rate_limiter_invoked_for_every_fetch():
    """Every adapter.fetch() call routes through rate_limiter.execute_with_limits()."""
    from zorivest_infra.market_data.market_data_adapter import (
        MarketDataProviderAdapter,
    )

    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b'{"data": "ohlcv"}'
    mock_response.headers = {}
    mock_client.get.return_value = mock_response

    mock_rate_limiter = AsyncMock()
    # Track that execute_with_limits is called but still execute the function
    call_log: list[str] = []

    async def tracked_execute(provider: str, func, *args, **kwargs):
        call_log.append(provider)
        return await func(*args, **kwargs)

    mock_rate_limiter.execute_with_limits = AsyncMock(side_effect=tracked_execute)

    adapter = MarketDataProviderAdapter(
        http_client=mock_client,
        rate_limiter=mock_rate_limiter,
    )

    await adapter.fetch(
        provider="Polygon.io",
        data_type="ohlcv",
        criteria={"symbol": "AAPL"},
    )

    assert len(call_log) == 1
    assert call_log[0] == "Polygon.io"
    mock_rate_limiter.execute_with_limits.assert_called_once()


# ---------------------------------------------------------------------------
# AC-6: ETag/If-Modified-Since via fetch_with_cache()
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_AC6_etag_headers_passed_to_fetch_with_cache():
    """When cached_etag is provided, adapter passes it to fetch_with_cache
    which sends If-None-Match header."""
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

    cached_data = b'{"old": "data"}'
    result = await adapter.fetch(
        provider="Polygon.io",
        data_type="ohlcv",
        criteria={"symbol": "AAPL"},
        cached_content=cached_data,
        cached_etag="etag-123",
    )

    # On 304, should return the cached content with revalidated status
    assert result["cache_status"] == "revalidated"
    assert result["content"] == cached_data


@pytest.mark.asyncio
async def test_AC6_last_modified_headers_passed():
    """When cached_last_modified is provided, adapter passes it through
    for If-Modified-Since header."""
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

    cached_data = b"old_data"
    result = await adapter.fetch(
        provider="Polygon.io",
        data_type="ohlcv",
        criteria={"symbol": "AAPL"},
        cached_content=cached_data,
        cached_last_modified="Wed, 01 Jan 2026 00:00:00 GMT",
    )

    assert result["cache_status"] == "revalidated"
    assert result["content"] == cached_data
