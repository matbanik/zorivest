# packages/infrastructure/src/zorivest_infra/market_data/url_builders.py
"""Provider-specific URL builders — MEU-PW6.

Replaces the monolithic _build_url() dispatch in MarketDataProviderAdapter
with a registry-based builder pattern. Each provider implements the
UrlBuilder protocol with provider-specific endpoint patterns.

Spec: implementation-plan.md §MEU-PW6
"""

from __future__ import annotations

from typing import Any, Protocol
from urllib.parse import urlencode


class UrlBuilder(Protocol):
    """Protocol for provider-specific URL construction."""

    def build_url(
        self,
        base_url: str,
        data_type: str,
        tickers: list[str],
        criteria: dict[str, Any],
    ) -> str: ...


def resolve_tickers(criteria: dict[str, Any]) -> list[str]:
    """Normalize tickers/symbol keys to a list of ticker strings.

    Handles two input patterns from pipeline policy params:
    - ``{"tickers": ["AAPL", "MSFT"]}`` → list as-is
    - ``{"symbol": "AAPL"}`` → wraps in list
    - neither key → empty list

    When both keys exist, ``tickers`` takes precedence.
    """
    if "tickers" in criteria:
        return list(criteria["tickers"])
    if "symbol" in criteria:
        return [criteria["symbol"]]
    return []


# ── Yahoo Finance URL Builder ──────────────────────────────────────────


class YahooUrlBuilder:
    """Yahoo Finance URL construction.

    Patterns:
    - ohlcv: /v8/finance/chart/{symbol}
    - quote: /v8/finance/chart/{symbol} (v6/quote is dead — 404 since ~2024)
    - news: /v1/finance/search?q={symbol}&newsCount=10

    Quote data uses the same v8/chart endpoint as OHLCV but with 1d range.
    The response envelope is ``chart.result[0].meta`` which contains:
    regularMarketPrice, currency, symbol, etc.
    """

    def build_url(
        self,
        base_url: str,
        data_type: str,
        tickers: list[str],
        criteria: dict[str, Any],
    ) -> str:
        symbol = tickers[0] if tickers else ""

        if data_type == "ohlcv":
            params: dict[str, str] = {"interval": "1d"}
            dr = criteria.get("date_range", {})
            if dr.get("start_date"):
                # Yahoo uses epoch timestamps but accept ISO for builder
                params["period1"] = dr["start_date"]
            if dr.get("end_date"):
                params["period2"] = dr["end_date"]
            return f"{base_url}/v8/finance/chart/{symbol}?{urlencode(params)}"

        if data_type == "quote":
            # v6/finance/quote was deprecated (~2024, returns 404).
            # Use v8/finance/chart with 1d range — meta block has all quote fields.
            return f"{base_url}/v8/finance/chart/{symbol}?range=1d&interval=1d"

        if data_type == "news":
            params_news = {"q": symbol, "newsCount": "10", "quotesCount": "0"}
            return f"{base_url}/v1/finance/search?{urlencode(params_news)}"

        # Fallback for unknown data types
        return f"{base_url}/v1/finance/search?q={symbol}"


# ── Polygon.io URL Builder ─────────────────────────────────────────────


class PolygonUrlBuilder:
    """Polygon.io URL construction.

    Patterns:
    - ohlcv: /aggs/ticker/{symbol}/range/1/day/{from}/{to}
    - quote: /snapshot/locale/us/markets/stocks/tickers?tickers={symbols}
    """

    def build_url(
        self,
        base_url: str,
        data_type: str,
        tickers: list[str],
        criteria: dict[str, Any],
    ) -> str:
        symbol = tickers[0] if tickers else ""

        if data_type == "ohlcv":
            dr = criteria.get("date_range", {})
            start = dr.get("start_date", "")
            end = dr.get("end_date", "")
            return f"{base_url}/aggs/ticker/{symbol}/range/1/day/{start}/{end}"

        if data_type == "quote":
            symbols = ",".join(tickers)
            return f"{base_url}/snapshot/locale/us/markets/stocks/tickers?tickers={symbols}"

        # Fallback
        return f"{base_url}/ticker/{symbol}"


# ── Finnhub URL Builder ────────────────────────────────────────────────


class FinnhubUrlBuilder:
    """Finnhub URL construction.

    Patterns:
    - ohlcv: /stock/candle?symbol={symbol}&resolution=D&from={ts}&to={ts}
    - quote: /quote?symbol={symbol}
    - news: /company-news?symbol={symbol}&from={date}&to={date}
    """

    def build_url(
        self,
        base_url: str,
        data_type: str,
        tickers: list[str],
        criteria: dict[str, Any],
    ) -> str:
        symbol = tickers[0] if tickers else ""

        if data_type == "ohlcv":
            dr = criteria.get("date_range", {})
            params = {
                "symbol": symbol,
                "resolution": "D",
                "from": dr.get("start_date", ""),
                "to": dr.get("end_date", ""),
            }
            return f"{base_url}/stock/candle?{urlencode(params)}"

        if data_type == "quote":
            return f"{base_url}/quote?symbol={symbol}"

        if data_type == "news":
            dr = criteria.get("date_range", {})
            params_news = {
                "symbol": symbol,
                "from": dr.get("start_date", ""),
                "to": dr.get("end_date", ""),
            }
            return f"{base_url}/company-news?{urlencode(params_news)}"

        # Fallback
        return f"{base_url}/quote?symbol={symbol}"


# ── Generic URL Builder (fallback) ─────────────────────────────────────


class GenericUrlBuilder:
    """Fallback URL builder for providers without specific patterns.

    Produces: {base_url}/{data_type}?symbols={comma-joined-tickers}
    """

    def build_url(
        self,
        base_url: str,
        data_type: str,
        tickers: list[str],
        criteria: dict[str, Any],
    ) -> str:
        symbols = ",".join(tickers) if tickers else ""
        params = {"symbols": symbols} if symbols else {}
        qs = f"?{urlencode(params)}" if params else ""
        return f"{base_url}/{data_type}{qs}"


# ── Builder Registry ───────────────────────────────────────────────────

_URL_BUILDER_REGISTRY: dict[str, UrlBuilder] = {
    "Yahoo Finance": YahooUrlBuilder(),
    "Polygon.io": PolygonUrlBuilder(),
    "Finnhub": FinnhubUrlBuilder(),
}

_GENERIC_BUILDER = GenericUrlBuilder()


def get_url_builder(provider_name: str) -> UrlBuilder:
    """Look up a URL builder by provider name.

    Returns the provider-specific builder if registered,
    otherwise returns GenericUrlBuilder as fallback.

    Args:
        provider_name: Provider name matching the provider registry key.

    Returns:
        A UrlBuilder instance for the given provider.
    """
    return _URL_BUILDER_REGISTRY.get(provider_name, _GENERIC_BUILDER)
