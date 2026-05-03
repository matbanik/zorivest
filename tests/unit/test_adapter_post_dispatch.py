# tests/unit/test_adapter_post_dispatch.py
"""TDD Red-phase tests for MarketDataProviderAdapter POST dispatch (MEU-189).

Acceptance criteria AC-6 through AC-8 per implementation-plan.md.

AC-6: Adapter detects build_request() on builder and dispatches POST via _do_fetch
AC-7: GET-only builders (no build_request) continue using build_url → GET path
AC-8: Extra headers from headers_template are forwarded for POST providers
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch as mock_patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_adapter():
    """Build a MarketDataProviderAdapter with mock HTTP client and rate limiter."""
    from zorivest_infra.market_data.market_data_adapter import (
        MarketDataProviderAdapter,
    )

    mock_client = AsyncMock()
    mock_rate_limiter = AsyncMock()

    async def _passthrough(provider, func, *a, **kw):
        return await func(*a, **kw)

    mock_rate_limiter.execute_with_limits = AsyncMock(side_effect=_passthrough)

    adapter = MarketDataProviderAdapter(
        http_client=mock_client,
        rate_limiter=mock_rate_limiter,
    )
    return adapter, mock_client, mock_rate_limiter


# ---------------------------------------------------------------------------
# AC-6: Adapter POST dispatch via build_request()
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_AC6_adapter_dispatches_post_for_openfigi():
    """When builder has build_request(), adapter uses POST path with json_body."""
    adapter, mock_client, _ = _make_adapter()

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b'[{"data":[{"figi":"BBG000BLNNH6"}]}]'
    mock_response.headers = {}
    mock_client.post.return_value = mock_response

    result = await adapter.fetch(
        provider="OpenFIGI",
        data_type="fundamentals",
        criteria={"symbol": "IBM", "id_type": "TICKER"},
    )

    # POST must have been called, not GET
    mock_client.post.assert_called_once()
    mock_client.get.assert_not_called()

    # Verify exact POST URL — catches double-path regression (/v3/v3/mapping)
    call_args = mock_client.post.call_args
    url_called = (
        call_args.args[0] if call_args.args else call_args.kwargs.get("url", "")
    )
    assert url_called == "https://api.openfigi.com/v3/mapping", (
        f"Expected exact OpenFIGI URL, got: {url_called}"
    )

    # Result should be valid FetchAdapterResult
    assert isinstance(result, dict)
    assert result["cache_status"] == "miss"


@pytest.mark.asyncio
async def test_AC6_adapter_dispatches_post_for_sec_api():
    """SEC API builder also has build_request() — adapter uses POST path."""
    adapter, mock_client, _ = _make_adapter()

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b'{"hits":[]}'
    mock_response.headers = {}
    mock_client.post.return_value = mock_response

    result = await adapter.fetch(
        provider="SEC API",
        data_type="fundamentals",
        criteria={"symbol": "AAPL"},
    )

    mock_client.post.assert_called_once()
    mock_client.get.assert_not_called()

    # Verify exact SEC API URL
    call_args = mock_client.post.call_args
    url_called = (
        call_args.args[0] if call_args.args else call_args.kwargs.get("url", "")
    )
    assert url_called == "https://api.sec-api.io/LATEST/search-index", (
        f"Expected exact SEC API URL, got: {url_called}"
    )
    assert result["cache_status"] == "miss"


@pytest.mark.asyncio
async def test_AC6_post_body_matches_builder_output():
    """The json_body passed to fetch_with_cache matches what build_request() produces."""
    adapter, mock_client, _ = _make_adapter()

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b'[{"data":[]}]'
    mock_response.headers = {}
    mock_client.post.return_value = mock_response

    await adapter.fetch(
        provider="OpenFIGI",
        data_type="fundamentals",
        criteria={"symbol": "IBM", "id_type": "TICKER"},
    )

    call_kwargs = mock_client.post.call_args.kwargs
    json_body = call_kwargs.get("json")
    assert json_body is not None, "json_body must be passed to client.post()"
    # OpenFIGI body is a list of dicts: [{"idType": "TICKER", "idValue": "IBM"}]
    assert isinstance(json_body, list)
    assert len(json_body) >= 1
    assert json_body[0]["idType"] == "TICKER"
    assert json_body[0]["idValue"] == "IBM"


# ---------------------------------------------------------------------------
# AC-7: GET-only builders continue working unchanged
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_AC7_get_builder_still_uses_get():
    """Polygon.io builder has no build_request() — adapter uses GET path (unchanged)."""
    adapter, mock_client, _ = _make_adapter()

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b'{"results": []}'
    mock_response.headers = {}
    mock_client.get.return_value = mock_response

    result = await adapter.fetch(
        provider="Polygon.io",
        data_type="ohlcv",
        criteria={"symbol": "AAPL"},
    )

    mock_client.get.assert_called_once()
    mock_client.post.assert_not_called()
    assert result["cache_status"] == "miss"


@pytest.mark.asyncio
async def test_AC7_finnhub_get_unchanged():
    """Finnhub (GET-only) continues using build_url → GET path."""
    adapter, mock_client, _ = _make_adapter()

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b'{"c": 150.0}'
    mock_response.headers = {}
    mock_client.get.return_value = mock_response

    await adapter.fetch(
        provider="Finnhub",
        data_type="quote",
        criteria={"symbol": "AAPL"},
    )

    mock_client.get.assert_called_once()
    mock_client.post.assert_not_called()


# ---------------------------------------------------------------------------
# AC-8: Extra headers forwarded for POST providers
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_AC8_post_forwards_headers_template():
    """OpenFIGI config has headers_template with X-OPENFIGI-APIKEY — forwarded to POST."""
    adapter, mock_client, _ = _make_adapter()

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b"[]"
    mock_response.headers = {}
    mock_client.post.return_value = mock_response

    with mock_patch(
        "zorivest_infra.market_data.market_data_adapter.fetch_with_cache"
    ) as mock_fetch:
        mock_fetch.return_value = {
            "content": b"[]",
            "cache_status": "miss",
            "etag": None,
            "last_modified": None,
        }

        await adapter.fetch(
            provider="OpenFIGI",
            data_type="fundamentals",
            criteria={"symbol": "IBM"},
        )

        mock_fetch.assert_called_once()
        call_kwargs = mock_fetch.call_args[1]
        assert "extra_headers" in call_kwargs
        headers = call_kwargs["extra_headers"]
        assert isinstance(headers, dict)
        # OpenFIGI has X-OPENFIGI-APIKEY in headers_template
        assert "X-OPENFIGI-APIKEY" in headers


# ---------------------------------------------------------------------------
# AC-8 expanded: Multi-ticker POST dispatch
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_AC8_multi_ticker_post_dispatches_post_not_get():
    """Multi-ticker OpenFIGI request must use POST, not fall back to GET."""
    adapter, mock_client, _ = _make_adapter()

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b'[{"data":[{"figi":"BBG1"}]},{"data":[{"figi":"BBG2"}]}]'
    mock_response.headers = {}
    mock_client.post.return_value = mock_response

    result = await adapter.fetch(
        provider="OpenFIGI",
        data_type="fundamentals",
        criteria={"tickers": ["IBM", "AAPL"], "id_type": "TICKER"},
    )

    # POST must have been called (batch), NOT GET
    mock_client.post.assert_called()
    mock_client.get.assert_not_called()

    # Verify exact URL
    call_args = mock_client.post.call_args
    url_called = (
        call_args.args[0] if call_args.args else call_args.kwargs.get("url", "")
    )
    assert url_called == "https://api.openfigi.com/v3/mapping", (
        f"Multi-ticker URL mismatch: {url_called}"
    )

    # Verify batch body contains both tickers
    json_body = call_args.kwargs.get("json")
    assert json_body is not None, "Multi-ticker POST must include json body"
    assert isinstance(json_body, list)
    id_values = [item["idValue"] for item in json_body]
    assert "IBM" in id_values
    assert "AAPL" in id_values

    assert isinstance(result, dict)


@pytest.mark.asyncio
async def test_AC8_multi_ticker_sec_api_dispatches_post():
    """Multi-ticker SEC API also dispatches via POST, not GET."""
    adapter, mock_client, _ = _make_adapter()

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b'{"hits":[]}'
    mock_response.headers = {}
    mock_client.post.return_value = mock_response

    await adapter.fetch(
        provider="SEC API",
        data_type="fundamentals",
        criteria={"tickers": ["AAPL", "MSFT"]},
    )

    # POST must have been called, not GET
    mock_client.post.assert_called()
    mock_client.get.assert_not_called()
