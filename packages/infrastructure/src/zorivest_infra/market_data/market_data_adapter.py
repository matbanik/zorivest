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
from urllib.parse import urlencode, urlparse, parse_qs, urlunparse

import structlog
import httpx

from zorivest_core.application.ports import FetchAdapterResult
from zorivest_core.domain.enums import AuthMethod
from zorivest_infra.market_data.http_cache import fetch_with_cache
from zorivest_infra.market_data.provider_registry import PROVIDER_REGISTRY
from zorivest_infra.market_data.url_builders import (
    RequestSpec,
    get_url_builder,
    resolve_tickers,
)

logger = structlog.get_logger()

# Valid data types for dispatch — must match URL builder + normalizer coverage
_VALID_DATA_TYPES = {
    "ohlcv",
    "quote",
    "news",
    "fundamentals",
    "earnings",
    "dividends",
    "splits",
    "insider",
    "company_profile",
    "economic_calendar",
}


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
        uow: Any | None = None,
        encryption: Any | None = None,
    ) -> None:
        self._http_client = http_client
        self._rate_limiter = rate_limiter
        self._timeout = timeout or httpx.Timeout(
            connect=10.0, read=30.0, write=10.0, pool=10.0
        )
        self._uow = uow
        self._encryption = encryption

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
            data_type: Market data type — one of: ohlcv, quote, news, fundamentals,
                earnings, dividends, splits, insider, company_profile, economic_calendar.
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
        extra_headers = self._resolve_headers(config, provider)

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

        # Append API key as query param for QUERY_PARAM auth providers
        url = self._inject_query_param_key(url, config, provider)

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
        extra_headers = self._resolve_headers(config, provider)

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
            url = self._inject_query_param_key(url, config, provider)
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

    def _get_api_key(self, provider_name: str) -> str | None:
        """Look up and decrypt the API key for a provider.

        Returns None if no key is stored, UoW is not injected,
        or decryption fails.
        """
        if self._uow is None or self._encryption is None:
            return None
        try:
            setting = self._uow.market_provider_settings.get(provider_name)
            if setting and setting.encrypted_api_key:
                return self._encryption.decrypt(setting.encrypted_api_key)
        except Exception:
            logger.warning(
                "api_key_lookup_failed",
                provider=provider_name,
                exc_info=True,
            )
        return None

    def _resolve_headers(
        self, config: Any, provider_key: str | None = None
    ) -> dict[str, str]:
        """Build request headers from headers_template with API key substitution.

        Replaces {api_key} and {api_secret} placeholders in the template
        with the actual decrypted values from market_provider_settings.

        Args:
            config: ProviderConfig from registry.
            provider_key: Registry dict key (e.g. "Polygon.io"). Falls back
                to config.name if not provided (backward compat).
        """
        if not config.headers_template:
            return {}

        headers = dict(config.headers_template)
        # Check if any header value has a placeholder
        needs_key = any(
            "{api_key}" in v or "{api_secret}" in v for v in headers.values()
        )
        if not needs_key:
            return headers

        lookup_name = provider_key or config.name
        api_key = self._get_api_key(lookup_name) or ""
        if not api_key:
            logger.warning(
                "api_key_missing_for_pipeline_fetch",
                provider=lookup_name,
            )
            return headers

        # Resolve placeholders — match MarketDataService pattern
        return {
            k: v.format(api_key=api_key, api_secret=api_key) for k, v in headers.items()
        }

    def _inject_query_param_key(
        self, url: str, config: Any, provider_key: str | None = None
    ) -> str:
        """Append API key as a URL query parameter for QUERY_PARAM auth providers.

        Providers like Alpha Vantage, EODHD, Polygon, Nasdaq Data Link use
        auth_method=QUERY_PARAM with auth_param_name specifying the query key.

        Args:
            url: The request URL to append the key to.
            config: ProviderConfig from registry.
            provider_key: Registry dict key (e.g. "Polygon.io"). Falls back
                to config.name if not provided (backward compat).
        """
        if config.auth_method != AuthMethod.QUERY_PARAM:
            return url
        if not config.auth_param_name:
            return url

        lookup_name = provider_key or config.name
        api_key = self._get_api_key(lookup_name)
        if not api_key:
            logger.warning(
                "api_key_missing_for_query_param",
                provider=lookup_name,
                auth_param=config.auth_param_name,
            )
            return url

        # Parse and append key to existing query string
        parsed = urlparse(url)
        params = parse_qs(parsed.query, keep_blank_values=True)
        params[config.auth_param_name] = [api_key]
        new_query = urlencode(params, doseq=True)
        return urlunparse(parsed._replace(query=new_query))
