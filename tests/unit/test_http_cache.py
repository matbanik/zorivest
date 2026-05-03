# tests/unit/test_http_cache.py
"""TDD Red-phase tests for fetch_with_cache() POST support (MEU-189).

Acceptance criteria AC-1 through AC-5 per implementation-plan.md.

AC-1: fetch_with_cache accepts method="POST" and json_body; dispatches to client.post()
AC-2: fetch_with_cache with method="GET" (default) behaves identically to current
AC-3: POST requests skip ETag/If-Modified-Since conditional headers
AC-4: POST responses still capture ETag/Last-Modified from response headers
AC-5: POST non-2xx responses raise HttpFetchError same as GET
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from zorivest_infra.market_data.http_cache import HttpFetchError, fetch_with_cache


# ---------------------------------------------------------------------------
# AC-1: POST dispatch with json_body
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_AC1_post_dispatches_to_client_post():
    """fetch_with_cache(method="POST", json_body=...) calls client.post() not client.get()."""
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b'[{"figi":"BBG000BLNNH6"}]'
    mock_response.headers = {}
    mock_client.post.return_value = mock_response

    result = await fetch_with_cache(
        client=mock_client,
        url="https://api.openfigi.com/v3/mapping",
        method="POST",
        json_body=[{"idType": "TICKER", "idValue": "IBM"}],
    )

    mock_client.post.assert_called_once()
    mock_client.get.assert_not_called()
    assert result["content"] == b'[{"figi":"BBG000BLNNH6"}]'
    assert result["cache_status"] == "miss"


@pytest.mark.asyncio
async def test_AC1_post_passes_json_body_to_client():
    """The json_body is forwarded to client.post() as the json= parameter."""
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b"[]"
    mock_response.headers = {}
    mock_client.post.return_value = mock_response

    body = [{"idType": "TICKER", "idValue": "AAPL"}]
    await fetch_with_cache(
        client=mock_client,
        url="https://api.openfigi.com/v3/mapping",
        method="POST",
        json_body=body,
    )

    call_kwargs = mock_client.post.call_args
    assert call_kwargs is not None
    # json_body should be passed as json= kwarg
    assert call_kwargs.kwargs.get("json") == body or (
        len(call_kwargs.args) > 0 and call_kwargs.kwargs.get("json") == body
    )


@pytest.mark.asyncio
async def test_AC1_invalid_method_raises_value_error():
    """method="PATCH" raises ValueError — only GET and POST are supported."""
    mock_client = AsyncMock()

    with pytest.raises(ValueError, match="method"):
        await fetch_with_cache(
            client=mock_client,
            url="https://example.com",
            method="PATCH",
        )


# ---------------------------------------------------------------------------
# AC-2: GET default backward compatibility
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_AC2_default_method_is_get():
    """fetch_with_cache() without method= uses GET (backward compatible)."""
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b'{"data": "test"}'
    mock_response.headers = {"ETag": "etag-123"}
    mock_client.get.return_value = mock_response

    result = await fetch_with_cache(
        client=mock_client,
        url="https://api.example.com/data",
    )

    mock_client.get.assert_called_once()
    mock_client.post.assert_not_called()
    assert result["cache_status"] == "miss"
    assert result["etag"] == "etag-123"


@pytest.mark.asyncio
async def test_AC2_explicit_get_same_as_default():
    """method="GET" behaves identically to omitting method=."""
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b'{"c": 150.0}'
    mock_response.headers = {}
    mock_client.get.return_value = mock_response

    result = await fetch_with_cache(
        client=mock_client,
        url="https://api.example.com/quote",
        method="GET",
    )

    mock_client.get.assert_called_once()
    assert result["cache_status"] == "miss"


# ---------------------------------------------------------------------------
# AC-3: POST skips conditional cache headers
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_AC3_post_skips_etag_header():
    """POST requests do NOT send If-None-Match even when cached_etag is provided."""
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b"[]"
    mock_response.headers = {}
    mock_client.post.return_value = mock_response

    await fetch_with_cache(
        client=mock_client,
        url="https://api.openfigi.com/v3/mapping",
        method="POST",
        json_body=[{"idType": "TICKER", "idValue": "IBM"}],
        cached_etag="etag-old",
    )

    # Inspect the headers passed to client.post()
    call_kwargs = mock_client.post.call_args.kwargs
    headers = call_kwargs.get("headers", {})
    assert "If-None-Match" not in headers, (
        f"POST must NOT send If-None-Match. Got headers: {headers}"
    )


@pytest.mark.asyncio
async def test_AC3_post_skips_if_modified_since():
    """POST requests do NOT send If-Modified-Since even when cached_last_modified is provided."""
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b"[]"
    mock_response.headers = {}
    mock_client.post.return_value = mock_response

    await fetch_with_cache(
        client=mock_client,
        url="https://api.openfigi.com/v3/mapping",
        method="POST",
        json_body=[],
        cached_etag="etag-old",
        cached_last_modified="Wed, 01 Jan 2026 00:00:00 GMT",
    )

    call_kwargs = mock_client.post.call_args.kwargs
    headers = call_kwargs.get("headers", {})
    assert "If-Modified-Since" not in headers, (
        f"POST must NOT send If-Modified-Since. Got headers: {headers}"
    )


# ---------------------------------------------------------------------------
# AC-4: POST responses capture ETag/Last-Modified
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_AC4_post_captures_etag_from_response():
    """POST response ETag header is captured in the result dict."""
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b'[{"figi":"BBG000BLNNH6"}]'
    mock_response.headers = {
        "ETag": '"new-etag-abc"',
        "Last-Modified": "Thu, 02 Jan 2026 12:00:00 GMT",
    }
    mock_client.post.return_value = mock_response

    result = await fetch_with_cache(
        client=mock_client,
        url="https://api.openfigi.com/v3/mapping",
        method="POST",
        json_body=[{"idType": "TICKER", "idValue": "IBM"}],
    )

    assert result["etag"] == '"new-etag-abc"'
    assert result["last_modified"] == "Thu, 02 Jan 2026 12:00:00 GMT"


# ---------------------------------------------------------------------------
# AC-5: POST non-2xx raises HttpFetchError
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_AC5_post_400_raises_http_fetch_error():
    """POST returning 400 raises HttpFetchError with status_code and url."""
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.content = b'{"error": "Bad request"}'
    mock_response.headers = {}
    mock_client.post.return_value = mock_response

    with pytest.raises(HttpFetchError) as exc_info:
        await fetch_with_cache(
            client=mock_client,
            url="https://api.openfigi.com/v3/mapping",
            method="POST",
            json_body=[{"idType": "INVALID", "idValue": ""}],
        )

    assert exc_info.value.status_code == 400
    assert "openfigi" in exc_info.value.url


@pytest.mark.asyncio
async def test_AC5_post_500_raises_http_fetch_error():
    """POST returning 500 raises HttpFetchError."""
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.content = b"Internal Server Error"
    mock_response.headers = {}
    mock_client.post.return_value = mock_response

    with pytest.raises(HttpFetchError) as exc_info:
        await fetch_with_cache(
            client=mock_client,
            url="https://api.openfigi.com/v3/mapping",
            method="POST",
            json_body=[],
        )

    assert exc_info.value.status_code == 500


@pytest.mark.asyncio
async def test_AC5_post_with_extra_headers():
    """POST requests forward extra_headers (auth tokens) to the HTTP call."""
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b"[]"
    mock_response.headers = {}
    mock_client.post.return_value = mock_response

    await fetch_with_cache(
        client=mock_client,
        url="https://api.openfigi.com/v3/mapping",
        method="POST",
        json_body=[{"idType": "TICKER", "idValue": "IBM"}],
        extra_headers={"X-OPENFIGI-APIKEY": "test-key-123"},
    )

    call_kwargs = mock_client.post.call_args.kwargs
    headers = call_kwargs.get("headers", {})
    assert headers.get("X-OPENFIGI-APIKEY") == "test-key-123"
