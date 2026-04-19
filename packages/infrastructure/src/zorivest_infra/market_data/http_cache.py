# packages/infrastructure/src/zorivest_infra/market_data/http_cache.py
"""HTTP cache with ETag/If-Modified-Since revalidation (§9.4e).

Provides fetch_with_cache() for conditional HTTP requests that
minimize bandwidth by revalidating cached responses via ETags.

Spec: 09-scheduling.md §9.4e
MEU: 85
"""

from __future__ import annotations

from typing import Any


async def fetch_with_cache(
    *,
    client: Any,
    url: str,
    cached_content: bytes | None = None,
    cached_etag: str | None = None,
    cached_last_modified: str | None = None,
    timeout: int | float | Any = 30,
) -> dict[str, Any]:
    """Fetch URL content with HTTP cache revalidation.

    If cached data is provided with an ETag or Last-Modified header,
    sends conditional request. On 304, returns cached data with
    cache_status='revalidated'.

    Returns:
        Dict with keys: content, cache_status, etag, last_modified
    """
    headers: dict[str, str] = {}
    if cached_etag:
        headers["If-None-Match"] = cached_etag
    if cached_last_modified:
        headers["If-Modified-Since"] = cached_last_modified

    response = await client.get(url, headers=headers, timeout=timeout)

    if response.status_code == 304 and cached_content is not None:
        # Not Modified — cached data is still valid
        return {
            "content": cached_content,
            "cache_status": "revalidated",
            "etag": cached_etag,
            "last_modified": cached_last_modified,
        }

    # New or updated content
    content = response.content if hasattr(response, "content") else response.read()
    return {
        "content": content,
        "cache_status": "miss",
        "etag": response.headers.get("ETag"),
        "last_modified": response.headers.get("Last-Modified"),
    }
