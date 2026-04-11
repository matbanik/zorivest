"""MarketDataService — MEU-61.

Unified market data queries with provider fallback.
Source: docs/build-plan/08-market-data.md §8.3b.

Implements MarketDataPort with protocol-based DI.
Same pattern as ProviderConnectionService (MEU-60).
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Mapping, Protocol

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
        rate_limiters: Mapping[str, RateLimiterProtocol],
        provider_registry: dict[str, ProviderConfig],
        quote_normalizers: dict[str, Callable[..., MarketQuote]] | None = None,
        news_normalizers: dict[str, Callable[..., list[MarketNewsItem]]] | None = None,
        search_normalizers: dict[str, Callable[..., list[TickerSearchResult]]]
        | None = None,
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

        MEU-91 complement: Always tries Yahoo Finance first (zero-config, no API key).
        Falls back to configured providers (Finnhub, Alpha Vantage, etc.) if Yahoo fails.
        Implements MarketDataPort.get_quote.
        """
        # Yahoo Finance is always tried first — no API key needed
        try:
            yahoo_quote = await self._yahoo_quote(ticker)
            if yahoo_quote:
                return yahoo_quote
        except Exception as exc:
            logger.debug(
                "Yahoo Finance quote failed, falling back to providers: %s", exc
            )

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

        raise MarketDataError(
            f"All providers failed for quote '{ticker}'. Last error: {last_error}"
        )

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

        raise MarketDataError(
            f"All providers failed for news. Last error: {last_error}"
        )

    async def search_ticker(self, query: str) -> list[TickerSearchResult]:
        """Search for tickers across providers.

        MEU-91: Always tries Yahoo Finance first (zero-config, no API key).
        Falls back to configured providers (FMP, Alpha Vantage) if Yahoo fails.
        Implements MarketDataPort.search_ticker.
        """
        # Yahoo Finance is always tried first — no API key, no provider settings needed
        try:
            yahoo_results = await self._yahoo_search(query)
            if yahoo_results:
                return yahoo_results
        except Exception as exc:
            logger.debug(
                "Yahoo Finance search failed, falling back to providers: %s", exc
            )

        # Fall through to configured API-key providers
        providers = self._get_enabled_providers(self._search_normalizers)
        if not providers:
            return []  # No API-key providers configured and Yahoo returned empty

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

        raise MarketDataError(
            f"All providers failed for search '{query}'. Last error: {last_error}"
        )

    async def _yahoo_search(self, query: str) -> list[TickerSearchResult]:
        """Search Yahoo Finance (no API key required) — MEU-91 zero-config fallback.

        URL: https://query1.finance.yahoo.com/v1/finance/search?q={query}&quotesCount=6&newsCount=0
        Filters out non-equity quote types (FUTURE, CURRENCY, CRYPTOCURRENCY, INDEX).
        """
        _EXCLUDED_TYPES = {
            "FUTURE",
            "CURRENCY",
            "CRYPTOCURRENCY",
            "INDEX",
            "MUTUALFUND",
        }
        url = (
            f"https://query1.finance.yahoo.com/v1/finance/search"
            f"?q={query}&quotesCount=6&newsCount=0"
        )
        response = await self._http.get(
            url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10
        )
        if response.status_code != 200:
            raise MarketDataError(
                f"Yahoo Finance search returned {response.status_code}"
            )
        quotes = response.json().get("quotes", [])
        return [
            TickerSearchResult(
                symbol=q["symbol"],
                name=q.get("shortname") or q.get("longname") or q["symbol"],
                exchange=q.get("exchange"),
                currency=None,
                provider="Yahoo Finance",
            )
            for q in quotes
            if q.get("quoteType") not in _EXCLUDED_TYPES
        ]

    async def _yahoo_quote(self, ticker: str) -> MarketQuote | None:
        """Fetch a quote from Yahoo Finance (no API key required).

        URL: https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?range=1d&interval=1d
        Returns regularMarketPrice, computed change/change_pct, and volume
        from the chart meta object.

        Fields extracted:
        - price: meta.regularMarketPrice
        - previous_close: meta.chartPreviousClose
        - change: price - previous_close (computed, None if no previous_close)
        - change_pct: (change / previous_close) * 100 (computed, None if no previous_close)
        - volume: meta.regularMarketVolume (None if absent)
        """
        url = (
            f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
            f"?range=1d&interval=1d"
        )
        response = await self._http.get(
            url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10
        )
        if response.status_code != 200:
            return None

        data = response.json()
        chart = data.get("chart", {})
        results = chart.get("result")
        if not results:
            return None

        meta = results[0].get("meta", {})
        price = meta.get("regularMarketPrice")
        if price is None:
            return None

        price_f = float(price)
        previous_close = meta.get("chartPreviousClose")

        # Compute change fields from previousClose (graceful None if missing)
        change: float | None = None
        change_pct: float | None = None
        if previous_close is not None:
            prev_f = float(previous_close)
            change = price_f - prev_f
            change_pct = (change / prev_f * 100) if prev_f != 0 else 0.0

        # Extract volume (None if absent, 0 is preserved)
        raw_volume = meta.get("regularMarketVolume")
        volume: int | None = int(raw_volume) if raw_volume is not None else None

        return MarketQuote(
            ticker=ticker,
            price=price_f,
            previous_close=previous_close,
            change=change,
            change_pct=change_pct,
            volume=volume,
            provider="Yahoo Finance",
        )

    async def get_sec_filings(self, ticker: str) -> list[SecFiling]:
        """Get SEC filings for a company (SEC API only).

        Implements MarketDataPort.get_sec_filings.
        """
        # SEC API is a single provider — not in the normalizer registries
        settings = self._get_all_settings()
        sec_setting = settings.get("SEC API")

        if (
            not sec_setting
            or not sec_setting.is_enabled
            or not sec_setting.encrypted_api_key
        ):
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
            k: v.format(api_key=api_key) for k, v in config.headers_template.items()
        }

        try:
            response = await self._http.get(url, headers, sec_setting.timeout or 30)
        except Exception as exc:
            raise MarketDataError(f"SEC API request failed: {exc}") from exc

        if response.status_code != 200:
            raise MarketDataError(f"SEC API returned status {response.status_code}")

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
            if setting and setting.is_enabled and setting.encrypted_api_key:
                result.append((name, setting))

        return result

    async def _fetch_quote_data(self, name: str, ticker: str, setting: Any) -> Any:
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
            k: v.format(api_key=api_key) for k, v in config.headers_template.items()
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
            k: v.format(api_key=api_key) for k, v in config.headers_template.items()
        }

        response = await self._http.get(url, headers, setting.timeout or 30)

        if response.status_code != 200:
            raise MarketDataError(
                f"{name} returned status {response.status_code} for news"
            )

        return response.json()

    async def _fetch_search_data(self, name: str, query: str, setting: Any) -> Any:
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
            k: v.format(api_key=api_key) for k, v in config.headers_template.items()
        }

        response = await self._http.get(url, headers, setting.timeout or 30)

        if response.status_code != 200:
            raise MarketDataError(
                f"{name} returned status {response.status_code} for search"
            )

        return response.json()
