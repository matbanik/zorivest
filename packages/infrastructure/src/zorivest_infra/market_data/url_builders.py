# packages/infrastructure/src/zorivest_infra/market_data/url_builders.py
"""Provider-specific URL builders — MEU-PW6.

Replaces the monolithic _build_url() dispatch in MarketDataProviderAdapter
with a registry-based builder pattern. Each provider implements the
UrlBuilder protocol with provider-specific endpoint patterns.

Spec: implementation-plan.md §MEU-PW6
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Protocol
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


# ── Alpaca URL Builder (MEU-185) ───────────────────────────────────────


class AlpacaUrlBuilder:
    """Alpaca Market Data API URL construction.

    Data API host: data.alpaca.markets (NOT api.alpaca.markets).

    Patterns:
    - quote: /v2/stocks/{symbol}/snapshot
    - ohlcv: /v2/stocks/{symbol}/bars?timeframe=1Day&start=X&end=Y
    - news: /v1beta1/news?symbols={csv}
    """

    def build_url(
        self,
        base_url: str,
        data_type: str,
        tickers: list[str],
        criteria: dict[str, Any],
    ) -> str:
        symbol = tickers[0] if tickers else ""

        if data_type == "quote":
            return f"{base_url}/v2/stocks/{symbol}/snapshot"

        if data_type == "ohlcv":
            params: dict[str, str] = {"timeframe": "1Day"}
            dr = criteria.get("date_range", {})
            if dr.get("start_date"):
                params["start"] = dr["start_date"]
            if dr.get("end_date"):
                params["end"] = dr["end_date"]
            return f"{base_url}/v2/stocks/{symbol}/bars?{urlencode(params)}"

        if data_type == "news":
            symbols = ",".join(tickers) if tickers else ""
            params_news = {"symbols": symbols}
            return f"{base_url}/v1beta1/news?{urlencode(params_news)}"

        # Fallback
        return f"{base_url}/v2/stocks/{symbol}/{data_type}"


# ── FMP URL Builder (MEU-185) ──────────────────────────────────────────


class FMPUrlBuilder:
    """Financial Modeling Prep URL construction.

    Patterns:
    - quote: /api/v3/quote/{symbol(s)}
    - ohlcv: /api/v3/historical-price-full/{symbol}?from=X&to=Y
    - fundamentals: /api/v3/income-statement/{symbol}
    - earnings: /api/v3/earning_calendar?symbol={symbol}
    - news: /api/v3/stock_news?tickers={symbol}
    - dividends: /api/v3/historical-price-full/stock_dividend/{symbol}
    - splits: /api/v3/historical-price-full/stock_split/{symbol}
    """

    def build_url(
        self,
        base_url: str,
        data_type: str,
        tickers: list[str],
        criteria: dict[str, Any],
    ) -> str:
        symbol = tickers[0] if tickers else ""

        if data_type == "quote":
            # FMP supports comma-separated multi-ticker in path
            symbols = ",".join(tickers) if tickers else ""
            return f"{base_url}/api/v3/quote/{symbols}"

        if data_type == "ohlcv":
            dr = criteria.get("date_range", {})
            params: dict[str, str] = {}
            if dr.get("start_date"):
                params["from"] = dr["start_date"]
            if dr.get("end_date"):
                params["to"] = dr["end_date"]
            qs = f"?{urlencode(params)}" if params else ""
            return f"{base_url}/api/v3/historical-price-full/{symbol}{qs}"

        if data_type == "fundamentals":
            return f"{base_url}/api/v3/income-statement/{symbol}"

        if data_type == "earnings":
            params_earn = {"symbol": symbol}
            return f"{base_url}/api/v3/earning_calendar?{urlencode(params_earn)}"

        if data_type == "news":
            params_news = {"tickers": symbol}
            return f"{base_url}/api/v3/stock_news?{urlencode(params_news)}"

        if data_type == "dividends":
            return f"{base_url}/api/v3/historical-price-full/stock_dividend/{symbol}"

        if data_type == "splits":
            return f"{base_url}/api/v3/historical-price-full/stock_split/{symbol}"

        # Fallback
        return f"{base_url}/api/v3/{data_type}/{symbol}"


# ── EODHD URL Builder (MEU-185) ────────────────────────────────────────


class EODHDUrlBuilder:
    """EODHD API URL construction.

    All endpoints require {symbol}.{exchange} format (default: .US).
    All responses requested in JSON via fmt=json.

    Patterns:
    - ohlcv: /api/eod/{symbol}.US?fmt=json&from=X&to=Y
    - fundamentals: /api/fundamentals/{symbol}.US?fmt=json
    - dividends: /api/div/{symbol}.US?fmt=json
    - splits: /api/splits/{symbol}.US?fmt=json
    - news: /api/news?s={symbol}.US&fmt=json
    """

    def build_url(
        self,
        base_url: str,
        data_type: str,
        tickers: list[str],
        criteria: dict[str, Any],
    ) -> str:
        symbol = tickers[0] if tickers else ""
        exchange = criteria.get("exchange", "US")
        ticker_with_exchange = f"{symbol}.{exchange}"

        if data_type == "ohlcv":
            params: dict[str, str] = {"fmt": "json"}
            dr = criteria.get("date_range", {})
            if dr.get("start_date"):
                params["from"] = dr["start_date"]
            if dr.get("end_date"):
                params["to"] = dr["end_date"]
            return f"{base_url}/api/eod/{ticker_with_exchange}?{urlencode(params)}"

        if data_type == "fundamentals":
            return f"{base_url}/api/fundamentals/{ticker_with_exchange}?fmt=json"

        if data_type == "dividends":
            return f"{base_url}/api/div/{ticker_with_exchange}?fmt=json"

        if data_type == "splits":
            return f"{base_url}/api/splits/{ticker_with_exchange}?fmt=json"

        if data_type == "news":
            params_news = {"s": ticker_with_exchange, "fmt": "json"}
            return f"{base_url}/api/news?{urlencode(params_news)}"

        # Fallback
        return f"{base_url}/api/{data_type}/{ticker_with_exchange}?fmt=json"


# ── API Ninjas URL Builder (MEU-185) ───────────────────────────────────


class APINinjasUrlBuilder:
    """API Ninjas URL construction.

    Patterns:
    - quote: /v1/stockprice?ticker={symbol}
    - earnings: /v1/earningscalendar?ticker={symbol}
    - insider: /v1/insidertrading?ticker={symbol}
    """

    _DATA_TYPE_PATHS: dict[str, str] = {
        "quote": "/v1/stockprice",
        "earnings": "/v1/earningscalendar",
        "insider": "/v1/insidertrading",
    }

    def build_url(
        self,
        base_url: str,
        data_type: str,
        tickers: list[str],
        criteria: dict[str, Any],
    ) -> str:
        symbol = tickers[0] if tickers else ""
        path = self._DATA_TYPE_PATHS.get(data_type, f"/v1/{data_type}")
        params = {"ticker": symbol}
        return f"{base_url}{path}?{urlencode(params)}"


# ── Tradier URL Builder (MEU-185) ──────────────────────────────────────


class TradierUrlBuilder:
    """Tradier API URL construction.

    Patterns:
    - quote: /v1/markets/quotes?symbols={csv}
    - ohlcv: /v1/markets/history?symbol={symbol}&interval=daily&start=X&end=Y
    """

    def build_url(
        self,
        base_url: str,
        data_type: str,
        tickers: list[str],
        criteria: dict[str, Any],
    ) -> str:
        if data_type == "quote":
            symbols = ",".join(tickers) if tickers else ""
            params: dict[str, str] = {"symbols": symbols}
            return f"{base_url}/v1/markets/quotes?{urlencode(params)}"

        if data_type == "ohlcv":
            symbol = tickers[0] if tickers else ""
            params_ohlcv: dict[str, str] = {
                "symbol": symbol,
                "interval": "daily",
            }
            dr = criteria.get("date_range", {})
            if dr.get("start_date"):
                params_ohlcv["start"] = dr["start_date"]
            if dr.get("end_date"):
                params_ohlcv["end"] = dr["end_date"]
            return f"{base_url}/v1/markets/history?{urlencode(params_ohlcv)}"

        # Fallback
        symbol = tickers[0] if tickers else ""
        return f"{base_url}/v1/markets/quotes?symbols={symbol}"


# ── RequestSpec (MEU-186 prerequisite) ─────────────────────────────────


@dataclass(frozen=True)
class RequestSpec:
    """HTTP request specification for providers requiring POST bodies.

    GET providers can ignore this; POST-body providers (OpenFIGI, SEC API)
    return RequestSpec from their build_request() method.
    """

    method: Literal["GET", "POST"] = "GET"
    url: str = ""
    body: dict[str, Any] | list[dict[str, Any]] | None = None


# ── Alpha Vantage URL Builder (MEU-186) ────────────────────────────────


class AlphaVantageUrlBuilder:
    """Alpha Vantage function-dispatch GET URL construction.

    All requests use: /query?function={FUNCTION}&symbol={symbol}

    Patterns:
    - quote: function=GLOBAL_QUOTE
    - ohlcv: function=TIME_SERIES_DAILY
    - fundamentals: function=OVERVIEW
    - earnings: function=EARNINGS
    - insider: function=INSIDER_TRANSACTIONS
    - economic_calendar: function=REAL_GDP (example)
    """

    _FUNCTION_MAP: dict[str, str] = {
        "quote": "GLOBAL_QUOTE",
        "ohlcv": "TIME_SERIES_DAILY",
        "fundamentals": "OVERVIEW",
        "earnings": "EARNINGS",
        "insider": "INSIDER_TRANSACTIONS",
        "economic_calendar": "REAL_GDP",
    }

    def build_url(
        self,
        base_url: str,
        data_type: str,
        tickers: list[str],
        criteria: dict[str, Any],
    ) -> str:
        symbol = tickers[0] if tickers else ""
        function = self._FUNCTION_MAP.get(data_type, data_type.upper())
        params: dict[str, str] = {
            "function": function,
            "symbol": symbol,
        }
        # Support optional outputsize (compact/full) for OHLCV
        if "outputsize" in criteria:
            params["outputsize"] = criteria["outputsize"]
        return f"{base_url}/query?{urlencode(params)}"


# ── Nasdaq Data Link URL Builder (MEU-186) ─────────────────────────────


class NasdaqDataLinkUrlBuilder:
    """Nasdaq Data Link dataset/table GET URL construction.

    Pattern: /datatables/{vendor}/{table}.json?ticker={symbol}
    Default vendor/table: SHARADAR/SF1 (fundamentals).
    """

    _DEFAULT_TABLES: dict[str, tuple[str, str]] = {
        "fundamentals": ("SHARADAR", "SF1"),
    }

    def build_url(
        self,
        base_url: str,
        data_type: str,
        tickers: list[str],
        criteria: dict[str, Any],
    ) -> str:
        symbol = tickers[0] if tickers else ""
        vendor = criteria.get("vendor")
        table = criteria.get("table")

        if vendor is None or table is None:
            default = self._DEFAULT_TABLES.get(data_type, ("SHARADAR", "SF1"))
            vendor = vendor or default[0]
            table = table or default[1]

        params = {"ticker": symbol}
        return f"{base_url}/datatables/{vendor}/{table}.json?{urlencode(params)}"


# ── OpenFIGI URL Builder (MEU-186) ─────────────────────────────────────


class OpenFIGIUrlBuilder:
    """OpenFIGI v3 POST-body URL builder.

    Pattern: POST /v3/mapping with JSON body array.
    Each item: {"idType": "TICKER", "idValue": "AAPL"}

    Note: v2 sunsets July 1, 2026 (410 Gone).
    """

    def build_url(
        self,
        base_url: str,
        data_type: str,
        tickers: list[str],
        criteria: dict[str, Any],
    ) -> str:
        """Return the POST URL (adapter compatibility)."""
        return f"{base_url}/mapping"

    def build_request(
        self,
        base_url: str,
        data_type: str,
        tickers: list[str],
        criteria: dict[str, Any],
    ) -> RequestSpec:
        """Build POST RequestSpec with body array."""
        id_type = criteria.get("id_type", "TICKER")
        body = [{"idType": id_type, "idValue": t} for t in tickers]
        return RequestSpec(
            method="POST",
            url=f"{base_url}/mapping",
            body=body,
        )


# ── SEC API URL Builder (MEU-186) ──────────────────────────────────────


class SECAPIUrlBuilder:
    """SEC EDGAR EFTS POST-body URL builder.

    Pattern: POST /LATEST/search-index?q={ticker}&dateRange=...
    Body is a Lucene query dict.
    """

    _FORM_TYPE_MAP: dict[str, str] = {
        "fundamentals": "10-K,10-Q",
        "insider": "4",
    }

    def build_url(
        self,
        base_url: str,
        data_type: str,
        tickers: list[str],
        criteria: dict[str, Any],
    ) -> str:
        """Return the POST URL (adapter compatibility)."""
        return f"{base_url}/LATEST/search-index"

    def build_request(
        self,
        base_url: str,
        data_type: str,
        tickers: list[str],
        criteria: dict[str, Any],
    ) -> RequestSpec:
        """Build POST RequestSpec with Lucene query body."""
        symbol = tickers[0] if tickers else ""
        form_type = criteria.get("form_type", self._FORM_TYPE_MAP.get(data_type, ""))
        body: dict[str, Any] = {
            "query": symbol,
            "formType": form_type,
        }
        return RequestSpec(
            method="POST",
            url=f"{base_url}/LATEST/search-index",
            body=body,
        )


# ── TradingView Scanner URL Builder (Addendum) ─────────────────────────


class TradingViewUrlBuilder:
    """TradingView scanner POST-body URL builder.

    Pattern: POST /{exchange}/scan with JSON body containing
    columns list and optional ticker filter.
    """

    _QUOTE_COLUMNS: list[str] = [
        "close",
        "volume",
        "change",
        "high",
        "low",
        "open",
        "name",
    ]
    _FUNDAMENTALS_COLUMNS: list[str] = [
        "market_cap_basic",
        "earnings_per_share_basic_ttm",
        "price_earnings_ttm",
        "dividend_yield_indication",
        "price_book_ratio",
        "debt_to_equity",
        "name",
    ]
    _COLUMN_MAP: dict[str, list[str]] = {
        "quote": _QUOTE_COLUMNS,
        "fundamentals": _FUNDAMENTALS_COLUMNS,
    }

    def build_url(
        self,
        base_url: str,
        data_type: str,
        tickers: list[str],
        criteria: dict[str, Any],
    ) -> str:
        """Return the POST URL (adapter compatibility)."""
        exchange = criteria.get("exchange", "america")
        return f"{base_url}/{exchange}/scan"

    def build_request(
        self,
        base_url: str,
        data_type: str,
        tickers: list[str],
        criteria: dict[str, Any],
    ) -> RequestSpec:
        """Build POST RequestSpec with scanner columns and ticker filter."""
        exchange = criteria.get("exchange", "america")
        columns = self._COLUMN_MAP.get(data_type, self._QUOTE_COLUMNS)
        body: dict[str, Any] = {
            "columns": columns,
            "range": [0, 50],
        }
        if tickers:
            body["symbols"] = {
                "tickers": [f"NASDAQ:{t}" if ":" not in t else t for t in tickers],
            }
        return RequestSpec(
            method="POST",
            url=f"{base_url}/{exchange}/scan",
            body=body,
        )


# ── Builder Registry ───────────────────────────────────────────────────

_URL_BUILDER_REGISTRY: dict[str, UrlBuilder] = {
    "Yahoo Finance": YahooUrlBuilder(),
    "Polygon.io": PolygonUrlBuilder(),
    "Finnhub": FinnhubUrlBuilder(),
    "Alpaca": AlpacaUrlBuilder(),
    "Financial Modeling Prep": FMPUrlBuilder(),
    "EODHD": EODHDUrlBuilder(),
    "API Ninjas": APINinjasUrlBuilder(),
    "Tradier": TradierUrlBuilder(),
    "Alpha Vantage": AlphaVantageUrlBuilder(),
    "Nasdaq Data Link": NasdaqDataLinkUrlBuilder(),
    "OpenFIGI": OpenFIGIUrlBuilder(),
    "SEC API": SECAPIUrlBuilder(),
    "TradingView": TradingViewUrlBuilder(),
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
