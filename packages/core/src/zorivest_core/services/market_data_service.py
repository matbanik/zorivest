"""MarketDataService — MEU-61.

Unified market data queries with provider fallback.
Source: docs/build-plan/08-market-data.md §8.3b.

Implements MarketDataPort with protocol-based DI.
Same pattern as ProviderConnectionService (MEU-60).

MEU-190/191: Layer 4 expansion — 8 new service methods
with Yahoo-first fallback + API-key provider chains.
Source: docs/build-plan/08a-market-data-expansion.md §8a.9/§8a.10.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Callable, Mapping, Protocol

from zorivest_core.application.market_dtos import (
    MarketNewsItem,
    MarketQuote,
    SecFiling,
    TickerSearchResult,
)
from zorivest_core.domain.enums import AuthMethod
from zorivest_core.application.market_expansion_dtos import (
    DividendRecord,
    EarningsReport,
    EconomicCalendarEvent,
    FundamentalsSnapshot,
    InsiderTransaction,
    OHLCVBar,
    StockSplit,
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

    async def post(
        self,
        url: str,
        headers: dict[str, str],
        timeout: int,
        json: Any = None,
    ) -> Any: ...


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
        normalizers: Generic normalizer registry for Layer 4+ data types.
            Maps data_type → {provider_name → normalizer_function}.
    """

    # Data types that support Yahoo Finance as first-try source.
    _YAHOO_DATA_TYPES = frozenset({"ohlcv", "fundamentals", "dividends", "splits"})

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
        normalizers: dict[str, dict[str, Callable[..., Any]]] | None = None,
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
        self._normalizers = normalizers or {}

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
            raise MarketDataError("No news provider available — configure Finnhub")

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

    # ── Layer 4: Expansion service methods (MEU-190/191) ────────────

    async def get_ohlcv(
        self, ticker: str, interval: str = "1d", **kwargs: Any
    ) -> list[OHLCVBar]:
        """Get OHLCV bars. Yahoo-first, then Alpaca → EODHD → Polygon.

        Source: §8a.9 — MEU-190.
        """
        result = await self._fetch_data_type(
            "ohlcv", ticker, interval=interval, **kwargs
        )
        if not isinstance(result, list):
            raise MarketDataError(f"Unexpected OHLCV result type for '{ticker}'")
        return result

    async def get_fundamentals(self, ticker: str) -> FundamentalsSnapshot:
        """Get company fundamentals. Yahoo-first, then FMP → EODHD → AV.

        Source: §8a.9 — MEU-190.
        """
        result = await self._fetch_data_type("fundamentals", ticker)
        if not isinstance(result, FundamentalsSnapshot):
            raise MarketDataError(f"Unexpected fundamentals result type for '{ticker}'")
        return result

    async def get_earnings(self, ticker: str) -> list[EarningsReport]:
        """Get earnings reports. Finnhub → FMP → AV (no Yahoo).

        Source: §8a.9 — MEU-190.
        """
        result = await self._fetch_data_type("earnings", ticker)
        if not isinstance(result, list):
            raise MarketDataError(f"Unexpected earnings result type for '{ticker}'")
        return result

    async def get_dividends(self, ticker: str) -> list[DividendRecord]:
        """Get dividend records. Yahoo-first, then Polygon → EODHD → FMP.

        Source: §8a.10 — MEU-191.
        """
        result = await self._fetch_data_type("dividends", ticker)
        if not isinstance(result, list):
            raise MarketDataError(f"Unexpected dividends result type for '{ticker}'")
        return result

    async def get_splits(self, ticker: str) -> list[StockSplit]:
        """Get stock splits. Yahoo-first, then Polygon → EODHD → FMP.

        Source: §8a.10 — MEU-191.
        """
        result = await self._fetch_data_type("splits", ticker)
        if not isinstance(result, list):
            raise MarketDataError(f"Unexpected splits result type for '{ticker}'")
        return result

    async def get_insider(self, ticker: str) -> list[InsiderTransaction]:
        """Get insider transactions. Finnhub → FMP → SEC API (no Yahoo).

        Source: §8a.10 — MEU-191.
        """
        result = await self._fetch_data_type("insider", ticker)
        if not isinstance(result, list):
            raise MarketDataError(f"Unexpected insider result type for '{ticker}'")
        return result

    async def get_economic_calendar(self, **kwargs: Any) -> list[EconomicCalendarEvent]:
        """Get economic calendar events. Finnhub → FMP → AV (no Yahoo).

        Source: §8a.10 — MEU-191.
        """
        result = await self._fetch_data_type("economic_calendar", "", **kwargs)
        if not isinstance(result, list):
            raise MarketDataError("Unexpected economic calendar result type")
        return result

    async def get_company_profile(self, ticker: str) -> FundamentalsSnapshot:
        """Get company profile. FMP → Finnhub → EODHD (no Yahoo).

        Returns FundamentalsSnapshot (same DTO as fundamentals).
        Source: §8a.10 — MEU-191.
        """
        result = await self._fetch_data_type("company_profile", ticker)
        if not isinstance(result, FundamentalsSnapshot):
            raise MarketDataError(
                f"Unexpected company profile result type for '{ticker}'"
            )
        return result

    # ── Generic data-type fetch with fallback ───────────────────────

    async def _fetch_data_type(self, data_type: str, ticker: str, **kwargs: Any) -> Any:
        """Generic fetch with Yahoo-first fallback + API-key provider chain.

        1. If data_type is in _YAHOO_DATA_TYPES, try Yahoo first.
        2. Fall through to API-key providers using normalizers registry.
        3. Raise MarketDataError if all sources fail.
        """
        # Step 1: Try Yahoo first (if applicable)
        if data_type in self._YAHOO_DATA_TYPES:
            yahoo_method = getattr(self, f"_yahoo_{data_type}", None)
            if yahoo_method:
                try:
                    result = await yahoo_method(ticker, **kwargs)
                    if result:
                        return result
                except Exception as exc:
                    logger.debug(
                        "Yahoo Finance %s failed, falling back to providers: %s",
                        data_type,
                        exc,
                    )

        # Step 2: API-key provider chain
        type_normalizers = self._normalizers.get(data_type, {})
        providers = self._get_enabled_providers(type_normalizers)
        if not providers and data_type not in self._YAHOO_DATA_TYPES:
            raise MarketDataError(
                f"No {data_type} provider available — "
                "configure at least one provider with an API key"
            )

        last_error = ""
        for name, setting in providers:
            try:
                data = await self._generic_api_fetch(
                    name,
                    data_type,
                    ticker,
                    setting,
                    criteria=kwargs,
                )
                normalizer = type_normalizers[name]
                return normalizer(data, ticker=ticker)
            except Exception as exc:
                last_error = f"{name}: {exc}"
                logger.warning(
                    "Provider %s failed for %s %s: %s",
                    name,
                    data_type,
                    ticker,
                    exc,
                )
                continue

        raise MarketDataError(
            f"All providers failed for {data_type} '{ticker}'. Last error: {last_error}"
        )

    async def _generic_api_fetch(
        self,
        name: str,
        data_type: str,
        ticker: str,
        setting: Any,
        criteria: dict[str, Any] | None = None,
    ) -> Any:
        """Fetch raw data from an API-key provider.

        Uses provider-specific URL builders from the url_builders registry
        and injects authentication based on the provider's auth_method.
        Supports POST-body providers via builder.build_request() when available.
        """
        from zorivest_infra.market_data.url_builders import get_url_builder

        api_key = self._encryption.decrypt(setting.encrypted_api_key)
        config = self._registry[name]
        resolved_criteria = criteria or {}

        limiter = self._rate_limiters.get(name)
        if limiter:
            await limiter.wait_if_needed()

        # Provider-specific URL construction
        builder = get_url_builder(name)

        # POST dispatch: builders with build_request() return a RequestSpec
        # (mirrors proven pattern from market_data_adapter.py)
        http_method = "GET"
        json_body: Any = None
        build_request_fn = getattr(builder, "build_request", None)
        if build_request_fn is not None:
            spec = build_request_fn(
                config.base_url,
                data_type,
                [ticker],
                resolved_criteria,
            )
            url = spec.url
            http_method = spec.method
            json_body = spec.body
        else:
            url = builder.build_url(
                config.base_url,
                data_type,
                [ticker],
                resolved_criteria,
            )

        # Auth injection based on provider auth method
        if config.auth_method == AuthMethod.QUERY_PARAM:
            separator = "&" if "?" in url else "?"
            url = f"{url}{separator}{config.auth_param_name}={api_key}"
            headers: dict[str, str] = {}
        else:
            headers = {
                k: v.format(api_key=api_key) for k, v in config.headers_template.items()
            }

        timeout = setting.timeout or 30
        if http_method == "POST":
            response = await self._http.post(url, headers, timeout, json=json_body)
        else:
            response = await self._http.get(url, headers, timeout)

        if response.status_code != 200:
            raise MarketDataError(
                f"{name} returned status {response.status_code} for {ticker}"
            )
        return response.json()

    # ── Yahoo Finance private helpers (Layer 4) ─────────────────────

    async def _yahoo_ohlcv(
        self, ticker: str, interval: str = "1d", **kwargs: Any
    ) -> list[OHLCVBar] | None:
        """Fetch OHLCV bars from Yahoo Finance v8/finance/chart."""
        period = kwargs.get("range", "1mo")
        url = (
            f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
            f"?interval={interval}&range={period}"
        )
        response = await self._http.get(
            url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10
        )
        if response.status_code != 200:
            return None

        data = response.json()
        results = data.get("chart", {}).get("result")
        if not results:
            return None

        result = results[0]
        timestamps = result.get("timestamp", [])
        quotes = (result.get("indicators", {}).get("quote") or [{}])[0]

        opens = quotes.get("open", [])
        highs = quotes.get("high", [])
        lows = quotes.get("low", [])
        closes = quotes.get("close", [])
        volumes = quotes.get("volume", [])

        bars: list[OHLCVBar] = []
        for i, ts in enumerate(timestamps):
            if i >= len(closes) or closes[i] is None:
                continue
            bars.append(
                OHLCVBar(
                    ticker=ticker,
                    timestamp=datetime.fromtimestamp(ts, tz=timezone.utc),
                    open=Decimal(str(opens[i]))
                    if i < len(opens) and opens[i] is not None
                    else Decimal("0"),
                    high=Decimal(str(highs[i]))
                    if i < len(highs) and highs[i] is not None
                    else Decimal("0"),
                    low=Decimal(str(lows[i]))
                    if i < len(lows) and lows[i] is not None
                    else Decimal("0"),
                    close=Decimal(str(closes[i])),
                    adj_close=None,
                    volume=int(volumes[i])
                    if i < len(volumes) and volumes[i] is not None
                    else 0,
                    vwap=None,
                    trade_count=None,
                    provider="Yahoo Finance",
                )
            )
        return bars or None

    async def _yahoo_fundamentals(
        self, ticker: str, **kwargs: Any
    ) -> FundamentalsSnapshot | None:
        """Fetch fundamentals from Yahoo Finance v10/quoteSummary."""
        url = (
            f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{ticker}"
            f"?modules=financialData,defaultKeyStatistics,summaryProfile"
        )
        response = await self._http.get(
            url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10
        )
        if response.status_code != 200:
            return None

        data = response.json()
        results = data.get("quoteSummary", {}).get("result")
        if not results:
            return None

        r = results[0]
        stats = r.get("defaultKeyStatistics", {})
        profile = r.get("summaryProfile", {})

        def _raw(d: dict[str, Any], key: str) -> Any:
            v = d.get(key, {})
            return v.get("raw") if isinstance(v, dict) else v

        pe = _raw(stats, "trailingPE")
        pb = _raw(stats, "priceToBook")
        beta = _raw(stats, "beta")
        eps = _raw(stats, "trailingEps")
        mkt_cap = _raw(stats, "marketCap")

        return FundamentalsSnapshot(
            ticker=ticker,
            market_cap=Decimal(str(mkt_cap)) if mkt_cap is not None else None,
            pe_ratio=Decimal(str(pe)) if pe is not None else None,
            pb_ratio=Decimal(str(pb)) if pb is not None else None,
            ps_ratio=None,
            eps=Decimal(str(eps)) if eps is not None else None,
            dividend_yield=None,
            beta=Decimal(str(beta)) if beta is not None else None,
            sector=profile.get("sector"),
            industry=profile.get("industry"),
            employees=profile.get("fullTimeEmployees"),
            provider="Yahoo Finance",
            timestamp=datetime.now(timezone.utc),
        )

    async def _yahoo_dividends(
        self, ticker: str, **kwargs: Any
    ) -> list[DividendRecord] | None:
        """Fetch dividend records from Yahoo Finance v8/chart events."""
        url = (
            f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
            f"?range=10y&interval=1d&events=div"
        )
        response = await self._http.get(
            url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10
        )
        if response.status_code != 200:
            return None

        data = response.json()
        results = data.get("chart", {}).get("result")
        if not results:
            return None

        events = results[0].get("events", {}).get("dividends", {})
        if not events:
            return None

        records: list[DividendRecord] = []
        for _ts, div in events.items():
            amount = div.get("amount", 0)
            div_date = div.get("date", 0)
            records.append(
                DividendRecord(
                    ticker=ticker,
                    dividend_amount=Decimal(str(amount)),
                    currency="USD",
                    ex_date=datetime.fromtimestamp(div_date, tz=timezone.utc).date(),
                    record_date=None,
                    pay_date=None,
                    declaration_date=None,
                    frequency=None,
                    provider="Yahoo Finance",
                )
            )
        return records or None

    async def _yahoo_splits(
        self, ticker: str, **kwargs: Any
    ) -> list[StockSplit] | None:
        """Fetch stock splits from Yahoo Finance v8/chart events."""
        url = (
            f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
            f"?range=10y&interval=1d&events=split"
        )
        response = await self._http.get(
            url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10
        )
        if response.status_code != 200:
            return None

        data = response.json()
        results = data.get("chart", {}).get("result")
        if not results:
            return None

        events = results[0].get("events", {}).get("splits", {})
        if not events:
            return None

        splits: list[StockSplit] = []
        for _ts, sp in events.items():
            splits.append(
                StockSplit(
                    ticker=ticker,
                    execution_date=datetime.fromtimestamp(
                        sp.get("date", 0), tz=timezone.utc
                    ).date(),
                    ratio_from=int(sp.get("denominator", 1)),
                    ratio_to=int(sp.get("numerator", 1)),
                    provider="Yahoo Finance",
                )
            )
        return splits or None

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

        Returns providers in normalizer dict insertion order (spec priority).
        """
        settings = self._get_all_settings()
        result: list[tuple[str, Any]] = []

        for name in normalizers:
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
