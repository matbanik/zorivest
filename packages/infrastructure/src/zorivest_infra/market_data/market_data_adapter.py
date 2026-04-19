# packages/infrastructure/src/zorivest_infra/market_data/market_data_adapter.py
"""MarketDataProviderAdapter — concrete adapter for pipeline market data fetching (MEU-PW2).

Implements MarketDataAdapterPort from core. Handles:
- URL construction per data_type using provider-specific URL builders (MEU-PW6)
- Rate limiting via PipelineRateLimiter.execute_with_limits()
- HTTP cache revalidation via fetch_with_cache()
- Provider header forwarding from headers_template
- Returns FetchAdapterResult dict

Spec: 09-scheduling.md §9.4, implementation-plan.md Component 2
"""

from __future__ import annotations

from typing import Any

import structlog
import httpx

from zorivest_core.application.ports import FetchAdapterResult
from zorivest_infra.market_data.http_cache import fetch_with_cache
from zorivest_infra.market_data.provider_registry import PROVIDER_REGISTRY
from zorivest_infra.market_data.url_builders import get_url_builder, resolve_tickers

logger = structlog.get_logger()

# Valid data types for dispatch
_VALID_DATA_TYPES = {"ohlcv", "quote", "news", "fundamentals"}


class MarketDataProviderAdapter:
    """Concrete pipeline adapter for market data fetching.

    Routes HTTP calls through PipelineRateLimiter and fetch_with_cache.
    Constructs provider-specific URLs via URL builder registry (MEU-PW6).
    Forwards provider headers_template to the HTTP layer.
    """

    def __init__(
        self,
        *,
        http_client: Any,
        rate_limiter: Any,
        timeout: httpx.Timeout | None = None,
    ) -> None:
        self._http_client = http_client
        self._rate_limiter = rate_limiter
        self._timeout = timeout or httpx.Timeout(
            connect=10.0, read=30.0, write=10.0, pool=10.0
        )

    async def fetch(
        self,
        *,
        provider: str,
        data_type: str,
        criteria: dict[str, Any],
        cached_content: bytes | None = None,
        cached_etag: str | None = None,
        cached_last_modified: str | None = None,
    ) -> FetchAdapterResult:
        """Fetch market data from a provider with rate limiting and cache revalidation.

        Args:
            provider: Provider key (must match PROVIDER_REGISTRY).
            data_type: One of 'ohlcv', 'quote', 'news', 'fundamentals'.
            criteria: Resolved criteria dict with date ranges, symbols, etc.
            cached_content: Previously cached response bytes for conditional request.
            cached_etag: ETag from previous response for If-None-Match.
            cached_last_modified: Last-Modified from previous response.

        Returns:
            FetchAdapterResult with content, cache_status, etag, last_modified.

        Raises:
            ValueError: If data_type is not one of the valid types.
            KeyError: If provider is not in PROVIDER_REGISTRY.
        """
        if data_type not in _VALID_DATA_TYPES:
            raise ValueError(
                f"Invalid data_type '{data_type}'. "
                f"Must be one of: {sorted(_VALID_DATA_TYPES)}"
            )

        config = PROVIDER_REGISTRY.get(provider)
        if config is None:
            available = sorted(PROVIDER_REGISTRY.keys())
            raise KeyError(f"Unknown provider '{provider}'. Available: {available}")

        # MEU-PW6: Use URL builder dispatch instead of legacy _build_url()
        tickers = resolve_tickers(criteria)
        builder = get_url_builder(provider)
        url = builder.build_url(config.base_url, data_type, tickers, criteria)

        # Extract provider headers from config, forwarded to HTTP layer
        extra_headers = dict(config.headers_template) if config.headers_template else {}

        # Route HTTP call through rate limiter
        result: dict[str, Any] = await self._rate_limiter.execute_with_limits(
            provider,
            self._do_fetch,
            url,
            cached_content=cached_content,
            cached_etag=cached_etag,
            cached_last_modified=cached_last_modified,
            extra_headers=extra_headers,
        )

        return FetchAdapterResult(
            content=result["content"],
            cache_status=result["cache_status"],
            etag=result.get("etag"),
            last_modified=result.get("last_modified"),
        )

    async def _do_fetch(
        self,
        url: str,
        *,
        cached_content: bytes | None = None,
        cached_etag: str | None = None,
        cached_last_modified: str | None = None,
        extra_headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Execute the HTTP fetch with cache revalidation."""
        return await fetch_with_cache(
            client=self._http_client,
            url=url,
            cached_content=cached_content,
            cached_etag=cached_etag,
            cached_last_modified=cached_last_modified,
            timeout=self._timeout,
            extra_headers=extra_headers,
        )
