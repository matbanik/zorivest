# packages/infrastructure/src/zorivest_infra/market_data/http_cache.py
"""HTTP cache with ETag/If-Modified-Since revalidation (§9.4e).

Provides fetch_with_cache() for conditional HTTP requests that
minimize bandwidth by revalidating cached responses via ETags.

Spec: 09-scheduling.md §9.4e
MEU: 85
"""

from __future__ import annotations

from typing import Any


class HttpFetchError(Exception):
    """Raised when an HTTP fetch returns a non-2xx status code.

    Prevents error HTML/JSON from being silently cached as valid data.
    """

    def __init__(self, status_code: int, url: str, body_preview: str = "") -> None:
        self.status_code = status_code
        self.url = url
        self.body_preview = body_preview
        super().__init__(
            f"HTTP {status_code} from {url}"
            + (f": {body_preview}" if body_preview else "")
        )


async def fetch_with_cache(
    *,
    client: Any,
    url: str,
    method: str = "GET",
    json_body: Any | None = None,
    cached_content: bytes | None = None,
    cached_etag: str | None = None,
    cached_last_modified: str | None = None,
    timeout: int | float | Any = 30,
    extra_headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Fetch URL content with HTTP cache revalidation.

    Supports both GET and POST methods. GET requests use conditional
    cache headers (ETag/If-Modified-Since) for revalidation. POST
    requests skip conditional headers per RFC 9110 §9.3.3 (POST
    responses are not cacheable by default) but still capture response
    ETag/Last-Modified for downstream use.

    Args:
        method: HTTP method — "GET" (default) or "POST".
        json_body: JSON-serializable body for POST requests. Passed as
            the ``json=`` parameter to the HTTP client. Ignored for GET.
        extra_headers: Provider-specific headers (auth tokens, User-Agent)
            to include in every request. Merged with cache headers.

    Returns:
        Dict with keys: content, cache_status, etag, last_modified

    Raises:
        ValueError: If method is not "GET" or "POST".
        HttpFetchError: If the server returns a non-2xx status code
            (except 304 which is handled as cache revalidation for GET).
    """
    if method not in ("GET", "POST"):
        raise ValueError(
            f"Unsupported HTTP method '{method}'. Only 'GET' and 'POST' are supported."
        )

    headers: dict[str, str] = {}
    # Merge provider-specific headers first (auth tokens, User-Agent, etc.)
    if extra_headers:
        headers.update(extra_headers)

    if method == "POST":
        # POST requests skip conditional cache headers (RFC 9110 §9.3.3)
        response = await client.post(
            url, headers=headers, timeout=timeout, json=json_body
        )
    else:
        # GET: add cache revalidation headers
        if cached_etag:
            headers["If-None-Match"] = cached_etag
        if cached_last_modified:
            headers["If-Modified-Since"] = cached_last_modified
        response = await client.get(url, headers=headers, timeout=timeout)

    if response.status_code == 304 and cached_content is not None:
        # Not Modified — cached data is still valid (GET only)
        return {
            "content": cached_content,
            "cache_status": "revalidated",
            "etag": cached_etag,
            "last_modified": cached_last_modified,
        }

    # Validate HTTP status — reject non-2xx responses before caching
    if response.status_code < 200 or response.status_code >= 300:
        body_bytes = response.content if hasattr(response, "content") else b""
        preview = body_bytes[:200].decode("utf-8", errors="replace")
        raise HttpFetchError(response.status_code, url, preview)

    # New or updated content
    content = response.content if hasattr(response, "content") else response.read()
    return {
        "content": content,
        "cache_status": "miss",
        "etag": response.headers.get("ETag"),
        "last_modified": response.headers.get("Last-Modified"),
    }
