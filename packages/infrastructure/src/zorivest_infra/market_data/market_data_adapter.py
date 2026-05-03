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
from zorivest_infra.market_data.url_builders import (
    RequestSpec,
    get_url_builder,
    resolve_tickers,
)

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

        When multiple tickers are requested and the provider's API only
        supports one ticker per request (e.g. Yahoo v8/chart), this method
        automatically loops over each ticker, fetches individually, and
        merges the results into a combined JSON array.

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

        tickers = resolve_tickers(criteria)

        # When there are multiple tickers and the provider uses per-ticker
        # URLs (e.g. Yahoo v8/chart), iterate and merge results.
        if len(tickers) > 1:
            return await self._fetch_multi_ticker(
                config=config,
                provider=provider,
                data_type=data_type,
                tickers=tickers,
                criteria=criteria,
            )

        # Single ticker (or no tickers) — standard single-request path
        builder = get_url_builder(provider)
        extra_headers = dict(config.headers_template) if config.headers_template else {}

        # POST dispatch: builders with build_request() return a RequestSpec
        method = "GET"
        json_body = None
        if hasattr(builder, "build_request"):
            spec: RequestSpec = builder.build_request(  # type: ignore[union-attr]  # runtime duck-type dispatch
                config.base_url, data_type, tickers, criteria
            )
            url = spec.url
            method = spec.method
            json_body = spec.body
        else:
            url = builder.build_url(config.base_url, data_type, tickers, criteria)

        result: dict[str, Any] = await self._rate_limiter.execute_with_limits(
            provider,
            self._do_fetch,
            url,
            method=method,
            json_body=json_body,
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

    async def _fetch_multi_ticker(
        self,
        *,
        config: Any,
        provider: str,
        data_type: str,
        tickers: list[str],
        criteria: dict[str, Any],
    ) -> FetchAdapterResult:
        """Fetch data for each ticker individually and merge into one response.

        Yahoo v8/chart (and similar APIs) only support one symbol per request.
        This method iterates over all tickers, builds a per-ticker URL, fetches
        via the rate limiter, and merges the parsed JSON records into a single
        JSON array as the combined content.

        The downstream TransformStep → extract_records() will receive a top-level
        JSON list of record dicts, which the generic extractor handles correctly.
        """
        import json as _json

        builder = get_url_builder(provider)
        extra_headers = dict(config.headers_template) if config.headers_template else {}

        # POST-batch dispatch: builders with build_request() support multi-ticker
        # natively (e.g. OpenFIGI sends all tickers in one POST body array).
        if hasattr(builder, "build_request"):
            spec: RequestSpec = builder.build_request(  # type: ignore[union-attr]  # runtime duck-type dispatch
                config.base_url, data_type, tickers, criteria
            )
            logger.info(
                "fetch_multi_ticker_post_batch",
                provider=provider,
                tickers=len(tickers),
                url=spec.url,
            )
            result: dict[str, Any] = await self._rate_limiter.execute_with_limits(
                provider,
                self._do_fetch,
                spec.url,
                method=spec.method,
                json_body=spec.body,
                cached_content=None,
                cached_etag=None,
                cached_last_modified=None,
                extra_headers=extra_headers,
            )
            return FetchAdapterResult(
                content=result["content"],
                cache_status=result["cache_status"],
                etag=result.get("etag"),
                last_modified=result.get("last_modified"),
            )

        # GET per-ticker iteration for providers without build_request()
        all_records: list[dict[str, Any]] = []
        last_etag: str | None = None
        last_modified: str | None = None

        for ticker in tickers:
            # Build per-ticker URL
            url = builder.build_url(config.base_url, data_type, [ticker], criteria)
            logger.info(
                "fetch_multi_ticker",
                provider=provider,
                ticker=ticker,
                url=url,
            )

            try:
                result = await self._rate_limiter.execute_with_limits(
                    provider,
                    self._do_fetch,
                    url,
                    cached_content=None,
                    cached_etag=None,
                    cached_last_modified=None,
                    extra_headers=extra_headers,
                )
            except Exception:
                logger.warning(
                    "fetch_multi_ticker_error",
                    provider=provider,
                    ticker=ticker,
                    exc_info=True,
                )
                continue

            # Parse the individual response and extract records
            content = result["content"]
            try:
                from zorivest_infra.market_data.response_extractors import (
                    extract_records,
                )

                records = extract_records(content, provider, data_type)
                all_records.extend(records)
            except Exception:
                logger.warning(
                    "fetch_multi_ticker_extract_error",
                    provider=provider,
                    ticker=ticker,
                    exc_info=True,
                )
                continue

            # Keep the last response's cache headers
            last_etag = result.get("etag") or last_etag
            last_modified = result.get("last_modified") or last_modified

        logger.info(
            "fetch_multi_ticker_complete",
            provider=provider,
            tickers_requested=len(tickers),
            records_merged=len(all_records),
        )

        # Serialize merged records as a JSON array —
        # TransformStep._extract_records() → generic extractor handles top-level lists
        merged_content = _json.dumps(all_records).encode("utf-8")

        return FetchAdapterResult(
            content=merged_content,
            cache_status="miss",  # Multi-ticker fetches bypass cache
            etag=last_etag,
            last_modified=last_modified,
        )

    async def _do_fetch(
        self,
        url: str,
        *,
        method: str = "GET",
        json_body: Any | None = None,
        cached_content: bytes | None = None,
        cached_etag: str | None = None,
        cached_last_modified: str | None = None,
        extra_headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Execute the HTTP fetch with cache revalidation.

        Supports both GET and POST methods. POST providers (OpenFIGI, SEC API)
        pass method='POST' and json_body from their RequestSpec.
        """
        return await fetch_with_cache(
            client=self._http_client,
            url=url,
            method=method,
            json_body=json_body,
            cached_content=cached_content,
            cached_etag=cached_etag,
            cached_last_modified=cached_last_modified,
            timeout=self._timeout,
            extra_headers=extra_headers,
        )
