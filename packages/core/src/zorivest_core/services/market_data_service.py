"""MarketDataService — MEU-61.

Unified market data queries with provider fallback.
Source: docs/build-plan/08-market-data.md §8.3b.

Implements MarketDataPort with protocol-based DI.
Same pattern as ProviderConnectionService (MEU-60).
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Protocol

from zorivest_core.application.market_dtos import (
    MarketNewsItem,
    MarketQuote,
    SecFiling,
    TickerSearchResult,
)
from zorivest_core.domain.market_data import ProviderConfig

logger = logging.getLogger(__name__)


# ── Exceptions ──────────────────────────────────────────────────────────


class MarketDataError(Exception):
    """Raised when a market data request cannot be fulfilled."""


# ── Protocols (same as ProviderConnectionService) ───────────────────────


class HttpClient(Protocol):
    """Async HTTP client protocol."""

    async def get(self, url: str, headers: dict[str, str], timeout: int) -> Any: ...


class EncryptionService(Protocol):
    """API key encryption/decryption protocol."""

    def encrypt(self, plaintext: str) -> str: ...

    def decrypt(self, ciphertext: str) -> str: ...


class RateLimiterProtocol(Protocol):
    """Rate limiter protocol."""

    async def wait_if_needed(self) -> None: ...


# ── Service ─────────────────────────────────────────────────────────────


class MarketDataService:
    """Unified market data queries with provider fallback.

    Args:
        uow: Unit of Work for persistence.
        encryption: Encryption service for API keys.
        http_client: Async HTTP client.
        rate_limiters: Per-provider rate limiters.
        provider_registry: Static provider configuration registry.
        quote_normalizers: Maps provider name → quote normalizer function.
        news_normalizers: Maps provider name → news normalizer function.
        search_normalizers: Maps provider name → search normalizer function.
    """

    def __init__(
        self,
        uow: Any,
        encryption: EncryptionService,
        http_client: HttpClient,
        rate_limiters: dict[str, RateLimiterProtocol],
        provider_registry: dict[str, ProviderConfig],
        quote_normalizers: dict[str, Callable[..., MarketQuote]] | None = None,
        news_normalizers: dict[str, Callable[..., list[MarketNewsItem]]] | None = None,
        search_normalizers: dict[str, Callable[..., list[TickerSearchResult]]] | None = None,
        sec_normalizer: Callable[..., list[SecFiling]] | None = None,
    ) -> None:
        self._uow = uow
        self._encryption = encryption
        self._http = http_client
        self._rate_limiters = rate_limiters
        self._registry = provider_registry
        self._quote_normalizers = quote_normalizers or {}
        self._news_normalizers = news_normalizers or {}
        self._search_normalizers = search_normalizers or {}
        self._sec_normalizer = sec_normalizer

    # ── Core queries ────────────────────────────────────────────────

    async def get_quote(self, ticker: str) -> MarketQuote:
        """Get a stock quote, trying providers in priority order.

        Implements MarketDataPort.get_quote.
        """
        providers = self._get_enabled_providers(self._quote_normalizers)
        if not providers:
            raise MarketDataError(
                "No quote provider available — configure at least one provider with an API key"
            )

        last_error = ""
        for name, setting in providers:
            try:
                data = await self._fetch_quote_data(name, ticker, setting)
                normalizer = self._quote_normalizers[name]

                # Finnhub normalizer needs ticker passed explicitly
                if name == "Finnhub":
                    return normalizer(data, ticker=ticker)
                return normalizer(data)

            except Exception as exc:
                last_error = f"{name}: {exc}"
                logger.warning("Provider %s failed for quote %s: %s", name, ticker, exc)
                continue

        raise MarketDataError(f"All providers failed for quote '{ticker}'. Last error: {last_error}")

    async def get_news(
        self, ticker: str | None = None, count: int = 5
    ) -> list[MarketNewsItem]:
        """Get market news from news-capable providers.

        Implements MarketDataPort.get_news.
        """
        providers = self._get_enabled_providers(self._news_normalizers)
        if not providers:
            raise MarketDataError(
                "No news provider available — configure Finnhub or Benzinga"
            )

        last_error = ""
        for name, setting in providers:
            try:
                data = await self._fetch_news_data(name, ticker, count, setting)
                normalizer = self._news_normalizers[name]
                return normalizer(data)

            except Exception as exc:
                last_error = f"{name}: {exc}"
                logger.warning("Provider %s failed for news: %s", name, exc)
                continue

        raise MarketDataError(f"All providers failed for news. Last error: {last_error}")

    async def search_ticker(self, query: str) -> list[TickerSearchResult]:
        """Search for tickers across providers.

        Implements MarketDataPort.search_ticker.
        """
        providers = self._get_enabled_providers(self._search_normalizers)
        if not providers:
            raise MarketDataError(
                "No search provider available — configure FMP or Alpha Vantage"
            )

        last_error = ""
        for name, setting in providers:
            try:
                data = await self._fetch_search_data(name, query, setting)
                normalizer = self._search_normalizers[name]
                return normalizer(data)

            except Exception as exc:
                last_error = f"{name}: {exc}"
                logger.warning("Provider %s failed for search: %s", name, exc)
                continue

        raise MarketDataError(f"All providers failed for search '{query}'. Last error: {last_error}")

    async def get_sec_filings(self, ticker: str) -> list[SecFiling]:
        """Get SEC filings for a company (SEC API only).

        Implements MarketDataPort.get_sec_filings.
        """
        # SEC API is a single provider — not in the normalizer registries
        settings = self._get_all_settings()
        sec_setting = settings.get("SEC API")

        if not sec_setting or not sec_setting.is_enabled or not sec_setting.encrypted_api_key:
            raise MarketDataError(
                "SEC API not configured — add an API key at https://sec-api.io/"
            )

        api_key = self._encryption.decrypt(sec_setting.encrypted_api_key)
        config = self._registry.get("SEC API")
        if not config:
            raise MarketDataError("SEC API provider not found in registry")

        limiter = self._rate_limiters.get("SEC API")
        if limiter:
            await limiter.wait_if_needed()

        url = f"{config.base_url}/mapping/ticker/{ticker}"
        headers = {
            k: v.format(api_key=api_key)
            for k, v in config.headers_template.items()
        }

        try:
            response = await self._http.get(url, headers, sec_setting.timeout or 30)
        except Exception as exc:
            raise MarketDataError(f"SEC API request failed: {exc}") from exc

        if response.status_code != 200:
            raise MarketDataError(
                f"SEC API returned status {response.status_code}"
            )

        data = response.json()
        if not isinstance(data, list):
            raise MarketDataError("SEC API returned unexpected format")

        if self._sec_normalizer is None:
            raise MarketDataError("SEC filing normalizer not configured")

        return self._sec_normalizer(data)

    # ── Internal helpers ────────────────────────────────────────────

    def _get_all_settings(self) -> dict[str, Any]:
        """Load all provider settings from DB."""
        with self._uow as uow:
            all_settings = uow.market_provider_settings.list_all()
        return {s.provider_name: s for s in all_settings}

    def _get_enabled_providers(
        self, normalizers: dict[str, Any]
    ) -> list[tuple[str, Any]]:
        """Return enabled providers that have both API keys and normalizers.

        Returns providers in alphabetical order (stable priority).
        """
        settings = self._get_all_settings()
        result: list[tuple[str, Any]] = []

        for name in sorted(normalizers):
            setting = settings.get(name)
            if (
                setting
                and setting.is_enabled
                and setting.encrypted_api_key
            ):
                result.append((name, setting))

        return result

    async def _fetch_quote_data(
        self, name: str, ticker: str, setting: Any
    ) -> Any:
        """Fetch quote data from a provider."""
        api_key = self._encryption.decrypt(setting.encrypted_api_key)
        config = self._registry[name]

        limiter = self._rate_limiters.get(name)
        if limiter:
            await limiter.wait_if_needed()

        # Build URL based on provider
        if name == "Alpha Vantage":
            url = f"{config.base_url}?function=GLOBAL_QUOTE&symbol={ticker}&apikey={api_key}"
        elif name == "Finnhub":
            url = f"{config.base_url}/quote?symbol={ticker}&token={api_key}"
        elif name == "Polygon.io":
            url = f"{config.base_url}/aggs/ticker/{ticker}/prev"
        elif name == "EODHD":
            url = f"{config.base_url}/real-time/{ticker}?api_token={api_key}&fmt=json"
        elif name == "API Ninjas":
            url = f"{config.base_url}/stockprice?ticker={ticker}"
        else:
            raise MarketDataError(f"No quote URL template for provider: {name}")

        headers = {
            k: v.format(api_key=api_key)
            for k, v in config.headers_template.items()
        }

        response = await self._http.get(url, headers, setting.timeout or 30)

        if response.status_code != 200:
            raise MarketDataError(
                f"{name} returned status {response.status_code} for {ticker}"
            )

        return response.json()

    async def _fetch_news_data(
        self, name: str, ticker: str | None, count: int, setting: Any
    ) -> Any:
        """Fetch news data from a provider."""
        api_key = self._encryption.decrypt(setting.encrypted_api_key)
        config = self._registry[name]

        limiter = self._rate_limiters.get(name)
        if limiter:
            await limiter.wait_if_needed()

        if name == "Finnhub":
            params = f"?token={api_key}"
            if ticker:
                params += f"&symbol={ticker}"
            url = f"{config.base_url}/company-news{params}"
        elif name == "Benzinga":
            params = f"?token={api_key}&pageSize={count}"
            if ticker:
                params += f"&tickers={ticker}"
            url = f"{config.base_url}/news{params}"
        else:
            raise MarketDataError(f"No news URL template for provider: {name}")

        headers = {
            k: v.format(api_key=api_key)
            for k, v in config.headers_template.items()
        }

        response = await self._http.get(url, headers, setting.timeout or 30)

        if response.status_code != 200:
            raise MarketDataError(
                f"{name} returned status {response.status_code} for news"
            )

        return response.json()

    async def _fetch_search_data(
        self, name: str, query: str, setting: Any
    ) -> Any:
        """Fetch search data from a provider."""
        api_key = self._encryption.decrypt(setting.encrypted_api_key)
        config = self._registry[name]

        limiter = self._rate_limiters.get(name)
        if limiter:
            await limiter.wait_if_needed()

        if name == "Financial Modeling Prep":
            url = f"{config.base_url}/search?query={query}&apikey={api_key}"
        elif name == "Alpha Vantage":
            url = f"{config.base_url}?function=SYMBOL_SEARCH&keywords={query}&apikey={api_key}"
        else:
            raise MarketDataError(f"No search URL template for provider: {name}")

        headers = {
            k: v.format(api_key=api_key)
            for k, v in config.headers_template.items()
        }

        response = await self._http.get(url, headers, setting.timeout or 30)

        if response.status_code != 200:
            raise MarketDataError(
                f"{name} returned status {response.status_code} for search"
            )

        return response.json()
