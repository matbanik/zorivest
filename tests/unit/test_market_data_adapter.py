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


# ---------------------------------------------------------------------------
# AC-PW6-7: Adapter uses URL builder dispatch (Finding 1 correction)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_AC7_adapter_dispatches_through_url_builder():
    """Adapter.fetch() uses get_url_builder() to construct URLs — not legacy _build_url().

    Proves the builder registry is wired into the live fetch path.
    """
    from unittest.mock import patch as mock_patch

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

    with mock_patch(
        "zorivest_infra.market_data.market_data_adapter.get_url_builder"
    ) as mock_get_builder:
        mock_builder = MagicMock(spec=["build_url"])
        mock_builder.build_url.return_value = (
            "https://finnhub.io/api/v1/quote?symbol=AAPL"
        )
        mock_get_builder.return_value = mock_builder

        await adapter.fetch(
            provider="Finnhub",
            data_type="quote",
            criteria={"symbol": "AAPL"},
        )

        mock_get_builder.assert_called_once_with("Finnhub")
        mock_builder.build_url.assert_called_once()


@pytest.mark.asyncio
async def test_AC7_adapter_resolves_tickers_from_criteria():
    """Adapter resolves 'tickers' key from criteria into URL — not legacy 'symbol' key.

    When criteria has {"tickers": ["AAPL", "MSFT"]}, the final URL must contain
    the tickers (not be empty like the legacy _build_url produced).
    """
    from zorivest_infra.market_data.market_data_adapter import (
        MarketDataProviderAdapter,
    )

    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b'{"results": []}'
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

    await adapter.fetch(
        provider="Yahoo Finance",
        data_type="quote",
        criteria={"tickers": ["AAPL", "MSFT"]},
    )

    # Verify the URL uses v8/finance/chart (v6/finance/quote is dead — 404)
    # v8/chart accepts one symbol at a time; multi-ticker path calls per ticker
    # base_url from registry: https://query1.finance.yahoo.com
    assert mock_client.get.call_count == 2, (
        f"Expected 2 calls (multi-ticker), got {mock_client.get.call_count}"
    )
    urls_called = [call[0][0] for call in mock_client.get.call_args_list]
    assert (
        "https://query1.finance.yahoo.com/v8/finance/chart/AAPL?range=1d&interval=1d"
        in urls_called
    ), f"AAPL URL not found in: {urls_called}"
    assert (
        "https://query1.finance.yahoo.com/v8/finance/chart/MSFT?range=1d&interval=1d"
        in urls_called
    ), f"MSFT URL not found in: {urls_called}"


# ---------------------------------------------------------------------------
# AC-PW6-8: Adapter forwards headers_template from provider config
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_AC8_adapter_forwards_provider_headers():
    """Adapter passes headers_template from provider config to fetch_with_cache().

    The Finnhub config has headers_template={"X-Finnhub-Token": "{api_key}"},
    which must be forwarded as extra_headers to the HTTP layer.
    """
    from unittest.mock import patch as mock_patch

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

    with mock_patch(
        "zorivest_infra.market_data.market_data_adapter.fetch_with_cache"
    ) as mock_fetch:
        mock_fetch.return_value = {
            "content": b'{"c": 150.0}',
            "cache_status": "miss",
            "etag": None,
            "last_modified": None,
        }

        await adapter.fetch(
            provider="Finnhub",
            data_type="quote",
            criteria={"symbol": "AAPL"},
        )

        # fetch_with_cache should have been called with extra_headers
        mock_fetch.assert_called_once()
        call_kwargs = mock_fetch.call_args[1]
        assert "extra_headers" in call_kwargs, (
            f"fetch_with_cache must receive extra_headers kwarg. Got: {list(call_kwargs.keys())}"
        )
        headers = call_kwargs["extra_headers"]
        assert isinstance(headers, dict)
        assert "X-Finnhub-Token" in headers


# ---------------------------------------------------------------------------
# Multi-ticker fetch — offline regression tests
# ---------------------------------------------------------------------------


def _make_adapter_with_mock_client(
    responses: list[MagicMock],
) -> tuple:
    """Helper: build an adapter with a mock httpx client that returns canned responses.

    Returns (adapter, mock_client, mock_rate_limiter).
    """
    from zorivest_infra.market_data.market_data_adapter import (
        MarketDataProviderAdapter,
    )

    mock_client = AsyncMock()
    # Queue responses for successive .get() calls
    mock_client.get = AsyncMock(side_effect=responses)

    mock_rate_limiter = AsyncMock()

    async def _passthrough(provider, func, *a, **kw):
        return await func(*a, **kw)

    mock_rate_limiter.execute_with_limits = AsyncMock(side_effect=_passthrough)

    adapter = MarketDataProviderAdapter(
        http_client=mock_client,
        rate_limiter=mock_rate_limiter,
    )
    return adapter, mock_client, mock_rate_limiter


def _make_yahoo_quote_response(ticker: str, price: float) -> MagicMock:
    """Build a mock httpx.Response for a single Yahoo v8/chart quote."""
    import json

    payload = {
        "chart": {
            "result": [
                {
                    "meta": {
                        "symbol": ticker,
                        "regularMarketPrice": price,
                        "regularMarketVolume": 10_000_000,
                        "regularMarketChange": 1.5,
                        "regularMarketChangePercent": 0.55,
                    }
                }
            ]
        }
    }
    resp = MagicMock()
    resp.status_code = 200
    resp.content = json.dumps(payload).encode("utf-8")
    resp.headers = {}
    return resp


@pytest.mark.asyncio
async def test_multi_ticker_merges_all_results():
    """Multi-ticker fetch iterates N tickers and merges N result sets into one JSON array.

    This is the offline regression test for the contract previously only verified
    against the live Yahoo API.
    """
    import json

    responses = [
        _make_yahoo_quote_response("AAPL", 198.50),
        _make_yahoo_quote_response("MSFT", 420.00),
        _make_yahoo_quote_response("GOOGL", 175.25),
    ]
    adapter, mock_client, _ = _make_adapter_with_mock_client(responses)

    result = await adapter.fetch(
        provider="Yahoo Finance",
        data_type="quote",
        criteria={"tickers": ["AAPL", "MSFT", "GOOGL"]},
    )

    # Must return a valid FetchAdapterResult
    assert isinstance(result, dict)
    assert "content" in result
    assert result["cache_status"] == "miss"  # Multi-ticker bypasses cache

    # Content must be a JSON array of 3 merged records
    records = json.loads(result["content"])
    assert isinstance(records, list)
    assert len(records) == 3

    # Verify all tickers are present in the merged output
    symbols = {r.get("symbol") or r.get("ticker") for r in records}
    assert "AAPL" in symbols
    assert "MSFT" in symbols
    assert "GOOGL" in symbols

    # Verify the HTTP client was called 3 times (one per ticker)
    assert mock_client.get.call_count == 3


@pytest.mark.asyncio
async def test_multi_ticker_handles_per_ticker_error():
    """When one ticker fails, the other tickers still produce results.

    The failing ticker is silently skipped via the per-ticker error handler
    in _fetch_multi_ticker.
    """
    import json

    good_response = _make_yahoo_quote_response("AAPL", 198.50)
    bad_response = MagicMock()
    bad_response.status_code = 500
    bad_response.content = b"Internal Server Error"
    bad_response.headers = {}
    # Simulate a server error that causes fetch_with_cache to raise
    bad_response.raise_for_status = MagicMock(side_effect=Exception("500 Server Error"))

    # The passthrough will call _do_fetch which calls fetch_with_cache
    # For the bad response, we need the mock client to raise on .get()
    good_response_2 = _make_yahoo_quote_response("GOOGL", 175.25)

    from zorivest_infra.market_data.market_data_adapter import (
        MarketDataProviderAdapter,
    )

    mock_client = AsyncMock()
    call_count = 0

    async def _sequential_get(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 2:
            raise Exception("500 Server Error for MSFT")
        if call_count == 1:
            return good_response
        return good_response_2

    mock_client.get = AsyncMock(side_effect=_sequential_get)

    mock_rate_limiter = AsyncMock()

    async def _passthrough(provider, func, *a, **kw):
        return await func(*a, **kw)

    mock_rate_limiter.execute_with_limits = AsyncMock(side_effect=_passthrough)

    adapter = MarketDataProviderAdapter(
        http_client=mock_client,
        rate_limiter=mock_rate_limiter,
    )

    result = await adapter.fetch(
        provider="Yahoo Finance",
        data_type="quote",
        criteria={"tickers": ["AAPL", "MSFT", "GOOGL"]},
    )

    # Should still return a result even though MSFT failed
    records = json.loads(result["content"])
    assert isinstance(records, list)
    # MSFT failed → only AAPL and GOOGL should be in the merged result
    assert len(records) == 2
    symbols = {r.get("symbol") or r.get("ticker") for r in records}
    assert "AAPL" in symbols
    assert "GOOGL" in symbols
    assert "MSFT" not in symbols


@pytest.mark.asyncio
async def test_single_ticker_does_not_use_multi_ticker_path():
    """Single-ticker requests use the standard single-request path, not _fetch_multi_ticker.

    Regression: verify we didn't break the single-ticker path when adding multi-ticker.
    """
    response = _make_yahoo_quote_response("AAPL", 198.50)
    adapter, mock_client, _ = _make_adapter_with_mock_client([response])

    result = await adapter.fetch(
        provider="Yahoo Finance",
        data_type="quote",
        criteria={"tickers": ["AAPL"]},
    )

    # Single ticker returns raw content (not re-serialized JSON array)
    assert isinstance(result, dict)
    assert isinstance(result["content"], bytes)
    # Only one HTTP call for single ticker
    assert mock_client.get.call_count == 1


@pytest.mark.asyncio
async def test_multi_ticker_empty_list_falls_through():
    """Empty tickers list uses the standard path (len(tickers) is not > 1)."""
    from zorivest_infra.market_data.market_data_adapter import (
        MarketDataProviderAdapter,
    )

    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b'{"chart": {"result": [{"meta": {}}]}}'
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
        provider="Yahoo Finance",
        data_type="quote",
        criteria={"tickers": []},
    )

    # Should work via standard path (empty tickers → len 0, not > 1)
    assert isinstance(result, dict)
    assert mock_client.get.call_count == 1
