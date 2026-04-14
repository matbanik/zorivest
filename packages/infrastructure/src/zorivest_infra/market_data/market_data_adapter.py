# packages/infrastructure/src/zorivest_infra/market_data/market_data_adapter.py
"""MarketDataProviderAdapter — concrete adapter for pipeline market data fetching (MEU-PW2).

Implements MarketDataAdapterPort from core. Handles:
- URL construction per data_type using provider registry configs
- Rate limiting via PipelineRateLimiter.execute_with_limits()
- HTTP cache revalidation via fetch_with_cache()
- Returns FetchAdapterResult dict

Spec: 09-scheduling.md §9.4, implementation-plan.md Component 2
"""

from __future__ import annotations

from typing import Any

import structlog

from zorivest_core.application.ports import FetchAdapterResult
from zorivest_infra.market_data.http_cache import fetch_with_cache
from zorivest_infra.market_data.provider_registry import PROVIDER_REGISTRY

logger = structlog.get_logger()

# Valid data types for dispatch
_VALID_DATA_TYPES = {"ohlcv", "quote", "news", "fundamentals"}


class MarketDataProviderAdapter:
    """Concrete pipeline adapter for market data fetching.

    Routes HTTP calls through PipelineRateLimiter and fetch_with_cache.
    Constructs provider-specific URLs per data_type.
    """

    def __init__(
        self,
        *,
        http_client: Any,
        rate_limiter: Any,
        timeout: int = 30,
    ) -> None:
        self._http_client = http_client
        self._rate_limiter = rate_limiter
        self._timeout = timeout

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

        url = self._build_url(config, data_type, criteria)

        # Route HTTP call through rate limiter
        result: dict[str, Any] = await self._rate_limiter.execute_with_limits(
            provider,
            self._do_fetch,
            url,
            cached_content=cached_content,
            cached_etag=cached_etag,
            cached_last_modified=cached_last_modified,
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
    ) -> dict[str, Any]:
        """Execute the HTTP fetch with cache revalidation."""
        return await fetch_with_cache(
            client=self._http_client,
            url=url,
            cached_content=cached_content,
            cached_etag=cached_etag,
            cached_last_modified=cached_last_modified,
            timeout=self._timeout,
        )

    def _build_url(
        self,
        config: Any,
        data_type: str,
        criteria: dict[str, Any],
    ) -> str:
        """Build provider-specific URL for the given data_type and criteria.

        Uses the provider's base_url and constructs appropriate endpoint
        based on data_type. Symbol is extracted from criteria.
        """
        base_url = config.base_url.rstrip("/")
        symbol = criteria.get("symbol", "")

        if data_type == "ohlcv":
            # Date range from criteria
            date_range = criteria.get("date_range", {})
            start = date_range.get("start_date", "")
            end = date_range.get("end_date", "")
            return f"{base_url}/aggs/ticker/{symbol}/range/1/day/{start}/{end}"

        elif data_type == "quote":
            return f"{base_url}/quote?symbol={symbol}"

        elif data_type == "news":
            return f"{base_url}/news?symbol={symbol}"

        elif data_type == "fundamentals":
            return f"{base_url}/fundamentals?symbol={symbol}"

        # Should not reach here due to validation above
        raise ValueError(f"Unhandled data_type: {data_type}")  # pragma: no cover
