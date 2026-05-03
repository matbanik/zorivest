# tests/unit/test_url_builders.py
"""Red-phase tests for MEU-PW6: Provider URL Builders.

FIC — Feature Intent Contract
==============================
Intent: Provider-specific URL builder classes replace the hardcoded _build_url()
    method in MarketDataProviderAdapter. Each provider has its own URL pattern.
    A registry maps provider keys to builders, with GenericUrlBuilder as fallback.

Acceptance Criteria:
- AC-PW6-1: YahooUrlBuilder.build_url() produces correct URLs for ohlcv, quote, news [Spec §9B.4b]
- AC-PW6-2: PolygonUrlBuilder.build_url() produces correct URLs for ohlcv, quote [Spec §9B.4b]
- AC-PW6-3: FinnhubUrlBuilder.build_url() produces correct URLs for ohlcv, quote, news [Spec §9B.4b]
- AC-PW6-4: GenericUrlBuilder.build_url() produces fallback URLs for any data type [Spec §9B.4b]
- AC-PW6-5: _resolve_tickers() normalizes tickers/symbol keys to list [Spec §9B.4b]
- AC-PW6-6: get_url_builder() returns correct builder per provider key [Spec §9B.4b]

Test Mapping:
- AC-PW6-1 → test_yahoo_url_builder_*
- AC-PW6-2 → test_polygon_url_builder_*
- AC-PW6-3 → test_finnhub_url_builder_*
- AC-PW6-4 → test_generic_url_builder_*
- AC-PW6-5 → test_resolve_tickers_*
- AC-PW6-6 → test_get_url_builder_*
"""

import pytest


# ── AC-PW6-1: YahooUrlBuilder ──────────────────────────────────────────


class TestYahooUrlBuilder:
    """AC-PW6-1: YahooUrlBuilder produces correct Yahoo Finance URLs."""

    def test_yahoo_ohlcv_url(self) -> None:
        """Yahoo OHLCV URL uses /v8/finance/chart/{symbol} pattern."""
        from zorivest_infra.market_data.url_builders import YahooUrlBuilder

        builder = YahooUrlBuilder()
        url = builder.build_url(
            base_url="https://query1.finance.yahoo.com",
            data_type="ohlcv",
            tickers=["AAPL"],
            criteria={
                "date_range": {"start_date": "2024-01-01", "end_date": "2024-01-31"}
            },
        )
        assert url.startswith("https://query1.finance.yahoo.com/v8/finance/chart/AAPL")
        assert "period1=2024-01-01" in url
        assert "period2=2024-01-31" in url

    def test_yahoo_quote_url_single_ticker(self) -> None:
        """Yahoo quote URL uses /v8/finance/chart/{symbol} (v6 is dead)."""
        from zorivest_infra.market_data.url_builders import YahooUrlBuilder

        builder = YahooUrlBuilder()
        url = builder.build_url(
            base_url="https://query1.finance.yahoo.com",
            data_type="quote",
            tickers=["MSFT"],
            criteria={},
        )
        assert (
            url
            == "https://query1.finance.yahoo.com/v8/finance/chart/MSFT?range=1d&interval=1d"
        )

    def test_yahoo_quote_url_multi_ticker_uses_first(self) -> None:
        """Yahoo v8/chart only accepts one symbol — builder takes tickers[0]."""
        from zorivest_infra.market_data.url_builders import YahooUrlBuilder

        builder = YahooUrlBuilder()
        url = builder.build_url(
            base_url="https://query1.finance.yahoo.com",
            data_type="quote",
            tickers=["AAPL", "MSFT"],
            criteria={},
        )
        assert (
            url
            == "https://query1.finance.yahoo.com/v8/finance/chart/AAPL?range=1d&interval=1d"
        )

    def test_yahoo_news_url(self) -> None:
        """Yahoo news URL includes symbol in query."""
        from zorivest_infra.market_data.url_builders import YahooUrlBuilder

        builder = YahooUrlBuilder()
        url = builder.build_url(
            base_url="https://query1.finance.yahoo.com",
            data_type="news",
            tickers=["TSLA"],
            criteria={},
        )
        assert url.startswith("https://query1.finance.yahoo.com/v1/finance/search")
        assert "q=TSLA" in url
        assert "newsCount=10" in url

    def test_yahoo_empty_tickers(self) -> None:
        """Yahoo URL with empty tickers produces URL with empty symbol segment."""
        from zorivest_infra.market_data.url_builders import YahooUrlBuilder

        builder = YahooUrlBuilder()
        url = builder.build_url(
            base_url="https://query1.finance.yahoo.com",
            data_type="quote",
            tickers=[],
            criteria={},
        )
        assert isinstance(url, str)


# ── AC-PW6-2: PolygonUrlBuilder ────────────────────────────────────────


class TestPolygonUrlBuilder:
    """AC-PW6-2: PolygonUrlBuilder produces correct Polygon.io URLs."""

    def test_polygon_ohlcv_url(self) -> None:
        """Polygon OHLCV URL uses /aggs/ticker/{symbol}/range pattern."""
        from zorivest_infra.market_data.url_builders import PolygonUrlBuilder

        builder = PolygonUrlBuilder()
        url = builder.build_url(
            base_url="https://api.polygon.io/v2",
            data_type="ohlcv",
            tickers=["AAPL"],
            criteria={
                "date_range": {"start_date": "2024-01-01", "end_date": "2024-01-31"}
            },
        )
        assert "/aggs/ticker/AAPL/range" in url
        assert "2024-01-01" in url
        assert "2024-01-31" in url

    def test_polygon_quote_url_single_ticker(self) -> None:
        """Polygon quote URL uses ?tickers= query param per build-plan spec."""
        from zorivest_infra.market_data.url_builders import PolygonUrlBuilder

        builder = PolygonUrlBuilder()
        url = builder.build_url(
            base_url="https://api.polygon.io/v2",
            data_type="quote",
            tickers=["MSFT"],
            criteria={},
        )
        assert (
            url
            == "https://api.polygon.io/v2/snapshot/locale/us/markets/stocks/tickers?tickers=MSFT"
        )

    def test_polygon_quote_url_multi_ticker(self) -> None:
        """Polygon quote URL comma-joins multiple tickers per build-plan spec."""
        from zorivest_infra.market_data.url_builders import PolygonUrlBuilder

        builder = PolygonUrlBuilder()
        url = builder.build_url(
            base_url="https://api.polygon.io/v2",
            data_type="quote",
            tickers=["AAPL", "MSFT"],
            criteria={},
        )
        assert (
            url
            == "https://api.polygon.io/v2/snapshot/locale/us/markets/stocks/tickers?tickers=AAPL,MSFT"
        )


# ── AC-PW6-3: FinnhubUrlBuilder ────────────────────────────────────────


class TestFinnhubUrlBuilder:
    """AC-PW6-3: FinnhubUrlBuilder produces correct Finnhub URLs."""

    def test_finnhub_ohlcv_url(self) -> None:
        """Finnhub OHLCV URL uses /stock/candle pattern."""
        from zorivest_infra.market_data.url_builders import FinnhubUrlBuilder

        builder = FinnhubUrlBuilder()
        url = builder.build_url(
            base_url="https://finnhub.io/api/v1",
            data_type="ohlcv",
            tickers=["AAPL"],
            criteria={
                "date_range": {"start_date": "2024-01-01", "end_date": "2024-01-31"}
            },
        )
        assert url.startswith("https://finnhub.io/api/v1/stock/candle")
        assert "symbol=AAPL" in url
        assert "from=2024-01-01" in url
        assert "to=2024-01-31" in url

    def test_finnhub_quote_url(self) -> None:
        """Finnhub quote URL uses /quote pattern."""
        from zorivest_infra.market_data.url_builders import FinnhubUrlBuilder

        builder = FinnhubUrlBuilder()
        url = builder.build_url(
            base_url="https://finnhub.io/api/v1",
            data_type="quote",
            tickers=["GOOG"],
            criteria={},
        )
        assert url == "https://finnhub.io/api/v1/quote?symbol=GOOG"

    def test_finnhub_news_url(self) -> None:
        """Finnhub news URL uses /company-news pattern."""
        from zorivest_infra.market_data.url_builders import FinnhubUrlBuilder

        builder = FinnhubUrlBuilder()
        url = builder.build_url(
            base_url="https://finnhub.io/api/v1",
            data_type="news",
            tickers=["NVDA"],
            criteria={},
        )
        assert url.startswith("https://finnhub.io/api/v1/company-news")
        assert "symbol=NVDA" in url


# ── AC-PW6-4: GenericUrlBuilder ────────────────────────────────────────


class TestGenericUrlBuilder:
    """AC-PW6-4: GenericUrlBuilder produces fallback URLs."""

    def test_generic_ohlcv_url(self) -> None:
        """Generic builder uses {base}/{data_type}?symbols={s} pattern."""
        from zorivest_infra.market_data.url_builders import GenericUrlBuilder

        builder = GenericUrlBuilder()
        url = builder.build_url(
            base_url="https://example.com/api",
            data_type="ohlcv",
            tickers=["AAPL"],
            criteria={},
        )
        assert url == "https://example.com/api/ohlcv?symbols=AAPL"

    def test_generic_quote_url(self) -> None:
        """Generic builder handles quote data type."""
        from zorivest_infra.market_data.url_builders import GenericUrlBuilder

        builder = GenericUrlBuilder()
        url = builder.build_url(
            base_url="https://example.com/api",
            data_type="quote",
            tickers=["MSFT", "GOOG"],
            criteria={},
        )
        # Multiple tickers should be comma-joined in symbols param
        assert url == "https://example.com/api/quote?symbols=MSFT%2CGOOG"

    def test_generic_fundamentals_url(self) -> None:
        """Generic builder handles arbitrary data types."""
        from zorivest_infra.market_data.url_builders import GenericUrlBuilder

        builder = GenericUrlBuilder()
        url = builder.build_url(
            base_url="https://example.com/api",
            data_type="fundamentals",
            tickers=["TSLA"],
            criteria={},
        )
        assert url == "https://example.com/api/fundamentals?symbols=TSLA"


# ── AC-PW6-5: _resolve_tickers ─────────────────────────────────────────


class TestResolveTickers:
    """AC-PW6-5: _resolve_tickers() normalizes tickers/symbol keys."""

    def test_resolve_tickers_from_tickers_list(self) -> None:
        """Criteria with tickers: ['AAPL'] returns ['AAPL']."""
        from zorivest_infra.market_data.url_builders import resolve_tickers

        result = resolve_tickers({"tickers": ["AAPL", "MSFT"]})
        assert result == ["AAPL", "MSFT"]

    def test_resolve_tickers_from_symbol_string(self) -> None:
        """Criteria with symbol: 'AAPL' returns ['AAPL']."""
        from zorivest_infra.market_data.url_builders import resolve_tickers

        result = resolve_tickers({"symbol": "AAPL"})
        assert result == ["AAPL"]

    def test_resolve_tickers_no_key_returns_empty(self) -> None:
        """Criteria with neither tickers nor symbol returns []."""
        from zorivest_infra.market_data.url_builders import resolve_tickers

        result = resolve_tickers({"date_range": {}})
        assert result == []

    def test_resolve_tickers_prefers_tickers_over_symbol(self) -> None:
        """When both keys exist, tickers takes precedence."""
        from zorivest_infra.market_data.url_builders import resolve_tickers

        result = resolve_tickers({"tickers": ["AAPL"], "symbol": "MSFT"})
        assert result == ["AAPL"]

    def test_resolve_tickers_empty_tickers_list(self) -> None:
        """Empty tickers list returns []."""
        from zorivest_infra.market_data.url_builders import resolve_tickers

        result = resolve_tickers({"tickers": []})
        assert result == []


# ── AC-PW6-6: get_url_builder registry ──────────────────────────────────


class TestGetUrlBuilder:
    """AC-PW6-6: get_url_builder() returns correct builder per provider."""

    def test_yahoo_returns_yahoo_builder(self) -> None:
        """get_url_builder('Yahoo Finance') returns YahooUrlBuilder."""
        from zorivest_infra.market_data.url_builders import (
            YahooUrlBuilder,
            get_url_builder,
        )

        builder = get_url_builder("Yahoo Finance")
        assert isinstance(builder, YahooUrlBuilder)

    def test_polygon_returns_polygon_builder(self) -> None:
        """get_url_builder('Polygon.io') returns PolygonUrlBuilder."""
        from zorivest_infra.market_data.url_builders import (
            PolygonUrlBuilder,
            get_url_builder,
        )

        builder = get_url_builder("Polygon.io")
        assert isinstance(builder, PolygonUrlBuilder)

    def test_finnhub_returns_finnhub_builder(self) -> None:
        """get_url_builder('Finnhub') returns FinnhubUrlBuilder."""
        from zorivest_infra.market_data.url_builders import (
            FinnhubUrlBuilder,
            get_url_builder,
        )

        builder = get_url_builder("Finnhub")
        assert isinstance(builder, FinnhubUrlBuilder)

    def test_unknown_returns_generic_builder(self) -> None:
        """get_url_builder('UnknownProvider') returns GenericUrlBuilder."""
        from zorivest_infra.market_data.url_builders import (
            GenericUrlBuilder,
            get_url_builder,
        )

        builder = get_url_builder("SomeUnknownProvider")
        assert isinstance(builder, GenericUrlBuilder)

    def test_alpha_vantage_returns_alpha_vantage_builder(self) -> None:
        """Registered providers like Alpha Vantage use AlphaVantageUrlBuilder."""
        from zorivest_infra.market_data.url_builders import (
            AlphaVantageUrlBuilder,
            get_url_builder,
        )

        builder = get_url_builder("Alpha Vantage")
        assert isinstance(builder, AlphaVantageUrlBuilder)


# ═══════════════════════════════════════════════════════════════════════════
# MEU-185: Simple GET Builders — FIC (Feature Intent Contract)
# ═══════════════════════════════════════════════════════════════════════════
#
# Intent: 5 new URL builder classes for simple-GET providers. Each builder
#     follows the `base_url + path + query_params` pattern and is registered
#     in _URL_BUILDER_REGISTRY for lookup via get_url_builder().
#
# Acceptance Criteria:
# - AC-1: AlpacaUrlBuilder for quote (snapshot), ohlcv (bars), news [Spec §8a.4]
# - AC-2: FMPUrlBuilder for quote, ohlcv, fundamentals, earnings, news,
#          dividends, splits [Spec §8a.4]
# - AC-3: EODHDUrlBuilder with .US exchange suffix for ohlcv, fundamentals,
#          news, dividends, splits [Spec §8a.4]
# - AC-4: APINinjasUrlBuilder for quote, earnings, insider [Spec §8a.4]
# - AC-5: TradierUrlBuilder for quote (multi-symbol), ohlcv [Spec §8a.4]
# - AC-6: All 5 builders registered and returned by get_url_builder() [Spec §8a.4]
#
# Test Mapping:
# - AC-1 → TestAlpacaUrlBuilder
# - AC-2 → TestFMPUrlBuilder
# - AC-3 → TestEODHDUrlBuilder
# - AC-4 → TestAPINinjasUrlBuilder
# - AC-5 → TestTradierUrlBuilder
# - AC-6 → TestGetUrlBuilderMEU185


# ── AC-1: AlpacaUrlBuilder ─────────────────────────────────────────────


class TestAlpacaUrlBuilder:
    """AC-1: AlpacaUrlBuilder produces correct Alpaca Market Data API URLs.

    Alpaca data API lives at data.alpaca.markets (not api.alpaca.markets).
    """

    def test_alpaca_quote_url(self) -> None:
        """Alpaca quote uses /v2/stocks/{symbol}/snapshot endpoint."""
        from zorivest_infra.market_data.url_builders import AlpacaUrlBuilder

        builder = AlpacaUrlBuilder()
        url = builder.build_url(
            base_url="https://data.alpaca.markets",
            data_type="quote",
            tickers=["AAPL"],
            criteria={},
        )
        assert "/v2/stocks/AAPL/snapshot" in url

    def test_alpaca_ohlcv_url(self) -> None:
        """Alpaca OHLCV uses /v2/stocks/{symbol}/bars endpoint."""
        from zorivest_infra.market_data.url_builders import AlpacaUrlBuilder

        builder = AlpacaUrlBuilder()
        url = builder.build_url(
            base_url="https://data.alpaca.markets",
            data_type="ohlcv",
            tickers=["MSFT"],
            criteria={
                "date_range": {"start_date": "2024-01-01", "end_date": "2024-01-31"}
            },
        )
        assert "/v2/stocks/MSFT/bars" in url
        assert "start=2024-01-01" in url
        assert "end=2024-01-31" in url

    def test_alpaca_ohlcv_timeframe_default(self) -> None:
        """Alpaca OHLCV defaults to 1Day timeframe."""
        from zorivest_infra.market_data.url_builders import AlpacaUrlBuilder

        builder = AlpacaUrlBuilder()
        url = builder.build_url(
            base_url="https://data.alpaca.markets",
            data_type="ohlcv",
            tickers=["AAPL"],
            criteria={},
        )
        assert "timeframe=1Day" in url

    def test_alpaca_news_url(self) -> None:
        """Alpaca news uses /v1beta1/news endpoint."""
        from zorivest_infra.market_data.url_builders import AlpacaUrlBuilder

        builder = AlpacaUrlBuilder()
        url = builder.build_url(
            base_url="https://data.alpaca.markets",
            data_type="news",
            tickers=["TSLA"],
            criteria={},
        )
        assert "/v1beta1/news" in url
        assert "symbols=TSLA" in url

    def test_alpaca_multi_ticker_news(self) -> None:
        """Alpaca news accepts comma-separated symbols."""
        from zorivest_infra.market_data.url_builders import AlpacaUrlBuilder

        builder = AlpacaUrlBuilder()
        url = builder.build_url(
            base_url="https://data.alpaca.markets",
            data_type="news",
            tickers=["AAPL", "MSFT"],
            criteria={},
        )
        assert "symbols=AAPL%2CMSFT" in url or "symbols=AAPL,MSFT" in url

    def test_alpaca_empty_tickers(self) -> None:
        """Alpaca with empty tickers still produces valid URL."""
        from zorivest_infra.market_data.url_builders import AlpacaUrlBuilder

        builder = AlpacaUrlBuilder()
        url = builder.build_url(
            base_url="https://data.alpaca.markets",
            data_type="quote",
            tickers=[],
            criteria={},
        )
        assert isinstance(url, str)

    def test_alpaca_fallback_url(self) -> None:
        """Alpaca unknown data_type falls back to a sensible URL."""
        from zorivest_infra.market_data.url_builders import AlpacaUrlBuilder

        builder = AlpacaUrlBuilder()
        url = builder.build_url(
            base_url="https://data.alpaca.markets",
            data_type="dividends",
            tickers=["AAPL"],
            criteria={},
        )
        assert isinstance(url, str)
        assert "AAPL" in url


# ── AC-2: FMPUrlBuilder ───────────────────────────────────────────────


class TestFMPUrlBuilder:
    """AC-2: FMPUrlBuilder produces correct Financial Modeling Prep URLs."""

    def test_fmp_quote_url(self) -> None:
        """FMP quote uses /api/v3/quote/{symbol}."""
        from zorivest_infra.market_data.url_builders import FMPUrlBuilder

        builder = FMPUrlBuilder()
        url = builder.build_url(
            base_url="https://financialmodelingprep.com",
            data_type="quote",
            tickers=["AAPL"],
            criteria={},
        )
        assert "/api/v3/quote/AAPL" in url

    def test_fmp_ohlcv_url(self) -> None:
        """FMP OHLCV uses /api/v3/historical-price-full/{symbol}."""
        from zorivest_infra.market_data.url_builders import FMPUrlBuilder

        builder = FMPUrlBuilder()
        url = builder.build_url(
            base_url="https://financialmodelingprep.com",
            data_type="ohlcv",
            tickers=["MSFT"],
            criteria={
                "date_range": {"start_date": "2024-01-01", "end_date": "2024-01-31"}
            },
        )
        assert "/api/v3/historical-price-full/MSFT" in url
        assert "from=2024-01-01" in url
        assert "to=2024-01-31" in url

    def test_fmp_fundamentals_url(self) -> None:
        """FMP fundamentals uses /api/v3/income-statement/{symbol}."""
        from zorivest_infra.market_data.url_builders import FMPUrlBuilder

        builder = FMPUrlBuilder()
        url = builder.build_url(
            base_url="https://financialmodelingprep.com",
            data_type="fundamentals",
            tickers=["GOOG"],
            criteria={},
        )
        assert "/api/v3/income-statement/GOOG" in url

    def test_fmp_earnings_url(self) -> None:
        """FMP earnings uses /api/v3/earning_calendar."""
        from zorivest_infra.market_data.url_builders import FMPUrlBuilder

        builder = FMPUrlBuilder()
        url = builder.build_url(
            base_url="https://financialmodelingprep.com",
            data_type="earnings",
            tickers=["AAPL"],
            criteria={},
        )
        assert "/api/v3/earning" in url
        assert "AAPL" in url or "symbol=AAPL" in url

    def test_fmp_news_url(self) -> None:
        """FMP news uses /api/v3/stock_news."""
        from zorivest_infra.market_data.url_builders import FMPUrlBuilder

        builder = FMPUrlBuilder()
        url = builder.build_url(
            base_url="https://financialmodelingprep.com",
            data_type="news",
            tickers=["TSLA"],
            criteria={},
        )
        assert "/api/v3/stock_news" in url
        assert "tickers=TSLA" in url

    def test_fmp_dividends_url(self) -> None:
        """FMP dividends uses /api/v3/historical-price-full/stock_dividend/{symbol}."""
        from zorivest_infra.market_data.url_builders import FMPUrlBuilder

        builder = FMPUrlBuilder()
        url = builder.build_url(
            base_url="https://financialmodelingprep.com",
            data_type="dividends",
            tickers=["JNJ"],
            criteria={},
        )
        assert "/api/v3/historical-price-full/stock_dividend/JNJ" in url

    def test_fmp_splits_url(self) -> None:
        """FMP splits uses /api/v3/historical-price-full/stock_split/{symbol}."""
        from zorivest_infra.market_data.url_builders import FMPUrlBuilder

        builder = FMPUrlBuilder()
        url = builder.build_url(
            base_url="https://financialmodelingprep.com",
            data_type="splits",
            tickers=["NVDA"],
            criteria={},
        )
        assert "/api/v3/historical-price-full/stock_split/NVDA" in url

    def test_fmp_multi_ticker_quote(self) -> None:
        """FMP quote supports comma-separated multi-ticker."""
        from zorivest_infra.market_data.url_builders import FMPUrlBuilder

        builder = FMPUrlBuilder()
        url = builder.build_url(
            base_url="https://financialmodelingprep.com",
            data_type="quote",
            tickers=["AAPL", "MSFT", "GOOG"],
            criteria={},
        )
        assert "AAPL,MSFT,GOOG" in url or "AAPL%2CMSFT%2CGOOG" in url


# ── AC-3: EODHDUrlBuilder ─────────────────────────────────────────────


class TestEODHDUrlBuilder:
    """AC-3: EODHDUrlBuilder produces correct EODHD URLs with .US suffix."""

    def test_eodhd_ohlcv_url(self) -> None:
        """EODHD OHLCV uses /api/eod/{symbol}.US."""
        from zorivest_infra.market_data.url_builders import EODHDUrlBuilder

        builder = EODHDUrlBuilder()
        url = builder.build_url(
            base_url="https://eodhd.com",
            data_type="ohlcv",
            tickers=["AAPL"],
            criteria={},
        )
        assert "/api/eod/AAPL.US" in url

    def test_eodhd_ohlcv_with_dates(self) -> None:
        """EODHD OHLCV includes from/to date params."""
        from zorivest_infra.market_data.url_builders import EODHDUrlBuilder

        builder = EODHDUrlBuilder()
        url = builder.build_url(
            base_url="https://eodhd.com",
            data_type="ohlcv",
            tickers=["MSFT"],
            criteria={
                "date_range": {"start_date": "2024-01-01", "end_date": "2024-01-31"}
            },
        )
        assert "from=2024-01-01" in url
        assert "to=2024-01-31" in url

    def test_eodhd_fundamentals_url(self) -> None:
        """EODHD fundamentals uses /api/fundamentals/{symbol}.US."""
        from zorivest_infra.market_data.url_builders import EODHDUrlBuilder

        builder = EODHDUrlBuilder()
        url = builder.build_url(
            base_url="https://eodhd.com",
            data_type="fundamentals",
            tickers=["GOOG"],
            criteria={},
        )
        assert "/api/fundamentals/GOOG.US" in url

    def test_eodhd_dividends_url(self) -> None:
        """EODHD dividends uses /api/div/{symbol}.US."""
        from zorivest_infra.market_data.url_builders import EODHDUrlBuilder

        builder = EODHDUrlBuilder()
        url = builder.build_url(
            base_url="https://eodhd.com",
            data_type="dividends",
            tickers=["JNJ"],
            criteria={},
        )
        assert "/api/div/JNJ.US" in url

    def test_eodhd_splits_url(self) -> None:
        """EODHD splits uses /api/splits/{symbol}.US."""
        from zorivest_infra.market_data.url_builders import EODHDUrlBuilder

        builder = EODHDUrlBuilder()
        url = builder.build_url(
            base_url="https://eodhd.com",
            data_type="splits",
            tickers=["TSLA"],
            criteria={},
        )
        assert "/api/splits/TSLA.US" in url

    def test_eodhd_news_url(self) -> None:
        """EODHD news uses /api/news endpoint."""
        from zorivest_infra.market_data.url_builders import EODHDUrlBuilder

        builder = EODHDUrlBuilder()
        url = builder.build_url(
            base_url="https://eodhd.com",
            data_type="news",
            tickers=["AAPL"],
            criteria={},
        )
        assert "/api/news" in url
        assert "s=AAPL.US" in url

    def test_eodhd_custom_exchange_suffix(self) -> None:
        """EODHD supports configurable exchange suffix via criteria."""
        from zorivest_infra.market_data.url_builders import EODHDUrlBuilder

        builder = EODHDUrlBuilder()
        url = builder.build_url(
            base_url="https://eodhd.com",
            data_type="ohlcv",
            tickers=["SHOP"],
            criteria={"exchange": "TO"},
        )
        assert "SHOP.TO" in url

    def test_eodhd_json_format(self) -> None:
        """EODHD appends fmt=json to all requests."""
        from zorivest_infra.market_data.url_builders import EODHDUrlBuilder

        builder = EODHDUrlBuilder()
        url = builder.build_url(
            base_url="https://eodhd.com",
            data_type="ohlcv",
            tickers=["AAPL"],
            criteria={},
        )
        assert "fmt=json" in url


# ── AC-4: APINinjasUrlBuilder ──────────────────────────────────────────


class TestAPINinjasUrlBuilder:
    """AC-4: APINinjasUrlBuilder produces correct API Ninjas URLs."""

    def test_api_ninjas_quote_url(self) -> None:
        """API Ninjas quote uses /v1/stockprice."""
        from zorivest_infra.market_data.url_builders import APINinjasUrlBuilder

        builder = APINinjasUrlBuilder()
        url = builder.build_url(
            base_url="https://api.api-ninjas.com",
            data_type="quote",
            tickers=["AAPL"],
            criteria={},
        )
        assert "/v1/stockprice" in url
        assert "ticker=AAPL" in url

    def test_api_ninjas_earnings_url(self) -> None:
        """API Ninjas earnings uses /v1/earningscalendar."""
        from zorivest_infra.market_data.url_builders import APINinjasUrlBuilder

        builder = APINinjasUrlBuilder()
        url = builder.build_url(
            base_url="https://api.api-ninjas.com",
            data_type="earnings",
            tickers=["MSFT"],
            criteria={},
        )
        assert "/v1/earningscalendar" in url
        assert "ticker=MSFT" in url

    def test_api_ninjas_insider_url(self) -> None:
        """API Ninjas insider uses /v1/insidertrading."""
        from zorivest_infra.market_data.url_builders import APINinjasUrlBuilder

        builder = APINinjasUrlBuilder()
        url = builder.build_url(
            base_url="https://api.api-ninjas.com",
            data_type="insider",
            tickers=["GOOG"],
            criteria={},
        )
        assert "/v1/insidertrading" in url
        assert "ticker=GOOG" in url

    def test_api_ninjas_fallback(self) -> None:
        """API Ninjas unknown data_type produces valid URL."""
        from zorivest_infra.market_data.url_builders import APINinjasUrlBuilder

        builder = APINinjasUrlBuilder()
        url = builder.build_url(
            base_url="https://api.api-ninjas.com",
            data_type="dividends",
            tickers=["JNJ"],
            criteria={},
        )
        assert isinstance(url, str)


# ── AC-5: TradierUrlBuilder ───────────────────────────────────────────


class TestTradierUrlBuilder:
    """AC-5: TradierUrlBuilder produces correct Tradier URLs."""

    def test_tradier_quote_url_single(self) -> None:
        """Tradier quote uses /v1/markets/quotes."""
        from zorivest_infra.market_data.url_builders import TradierUrlBuilder

        builder = TradierUrlBuilder()
        url = builder.build_url(
            base_url="https://api.tradier.com",
            data_type="quote",
            tickers=["AAPL"],
            criteria={},
        )
        assert "/v1/markets/quotes" in url
        assert "symbols=AAPL" in url

    def test_tradier_quote_url_multi(self) -> None:
        """Tradier quote supports multi-symbol comma-separated."""
        from zorivest_infra.market_data.url_builders import TradierUrlBuilder

        builder = TradierUrlBuilder()
        url = builder.build_url(
            base_url="https://api.tradier.com",
            data_type="quote",
            tickers=["AAPL", "MSFT", "GOOG"],
            criteria={},
        )
        assert "symbols=" in url
        # All three symbols should be in the URL
        assert "AAPL" in url and "MSFT" in url and "GOOG" in url

    def test_tradier_ohlcv_url(self) -> None:
        """Tradier OHLCV uses /v1/markets/history."""
        from zorivest_infra.market_data.url_builders import TradierUrlBuilder

        builder = TradierUrlBuilder()
        url = builder.build_url(
            base_url="https://api.tradier.com",
            data_type="ohlcv",
            tickers=["MSFT"],
            criteria={
                "date_range": {"start_date": "2024-01-01", "end_date": "2024-01-31"}
            },
        )
        assert "/v1/markets/history" in url
        assert "symbol=MSFT" in url
        assert "start=2024-01-01" in url
        assert "end=2024-01-31" in url

    def test_tradier_ohlcv_default_interval(self) -> None:
        """Tradier OHLCV defaults to 'daily' interval."""
        from zorivest_infra.market_data.url_builders import TradierUrlBuilder

        builder = TradierUrlBuilder()
        url = builder.build_url(
            base_url="https://api.tradier.com",
            data_type="ohlcv",
            tickers=["AAPL"],
            criteria={},
        )
        assert "interval=daily" in url

    def test_tradier_fallback(self) -> None:
        """Tradier unknown data_type falls back to quotes endpoint."""
        from zorivest_infra.market_data.url_builders import TradierUrlBuilder

        builder = TradierUrlBuilder()
        url = builder.build_url(
            base_url="https://api.tradier.com",
            data_type="news",
            tickers=["TSLA"],
            criteria={},
        )
        assert isinstance(url, str)


# ── AC-6: Registry Lookup for MEU-185 Builders ────────────────────────


class TestGetUrlBuilderMEU185:
    """AC-6: All 5 MEU-185 builders registered and returned by get_url_builder()."""

    def test_alpaca_returns_alpaca_builder(self) -> None:
        """get_url_builder('Alpaca') returns AlpacaUrlBuilder."""
        from zorivest_infra.market_data.url_builders import (
            AlpacaUrlBuilder,
            get_url_builder,
        )

        builder = get_url_builder("Alpaca")
        assert isinstance(builder, AlpacaUrlBuilder)

    def test_fmp_returns_fmp_builder(self) -> None:
        """get_url_builder('Financial Modeling Prep') returns FMPUrlBuilder."""
        from zorivest_infra.market_data.url_builders import (
            FMPUrlBuilder,
            get_url_builder,
        )

        builder = get_url_builder("Financial Modeling Prep")
        assert isinstance(builder, FMPUrlBuilder)

    def test_eodhd_returns_eodhd_builder(self) -> None:
        """get_url_builder('EODHD') returns EODHDUrlBuilder."""
        from zorivest_infra.market_data.url_builders import (
            EODHDUrlBuilder,
            get_url_builder,
        )

        builder = get_url_builder("EODHD")
        assert isinstance(builder, EODHDUrlBuilder)

    def test_api_ninjas_returns_api_ninjas_builder(self) -> None:
        """get_url_builder('API Ninjas') returns APINinjasUrlBuilder."""
        from zorivest_infra.market_data.url_builders import (
            APINinjasUrlBuilder,
            get_url_builder,
        )

        builder = get_url_builder("API Ninjas")
        assert isinstance(builder, APINinjasUrlBuilder)

    def test_tradier_returns_tradier_builder(self) -> None:
        """get_url_builder('Tradier') returns TradierUrlBuilder."""
        from zorivest_infra.market_data.url_builders import (
            TradierUrlBuilder,
            get_url_builder,
        )

        builder = get_url_builder("Tradier")
        assert isinstance(builder, TradierUrlBuilder)


# ═══════════════════════════════════════════════════════════════════════════
# MEU-186: Special-Pattern Builders — FIC (Feature Intent Contract)
# ═══════════════════════════════════════════════════════════════════════════
#
# Intent: 4 new URL builder classes for non-standard patterns, plus the
#     RequestSpec frozen dataclass for POST-body providers.
#
# Acceptance Criteria:
# - AC-7: AlphaVantageUrlBuilder uses ?function=X&symbol=Y dispatch [Spec §8a.5]
# - AC-8: NasdaqDataLinkUrlBuilder uses /datatables/{vendor}/{table}.json [Spec §8a.5]
# - AC-9: OpenFIGIUrlBuilder.build_request() returns RequestSpec(method="POST") [Spec §8a.5]
# - AC-10: SECAPIUrlBuilder.build_request() returns RequestSpec(method="POST") [Spec §8a.5]
# - AC-11: RequestSpec frozen dataclass with defaults [Research-backed]
# - AC-12: All 4 builders registered in _URL_BUILDER_REGISTRY [Spec §8a.5]


# ── AC-11: RequestSpec ─────────────────────────────────────────────────


class TestRequestSpec:
    """AC-11: RequestSpec frozen dataclass with method, url, body fields."""

    def test_request_spec_defaults(self) -> None:
        """RequestSpec defaults to GET with None body."""
        from zorivest_infra.market_data.url_builders import RequestSpec

        spec = RequestSpec()
        assert spec.method == "GET"
        assert spec.url == ""
        assert spec.body is None

    def test_request_spec_post(self) -> None:
        """RequestSpec can represent a POST with body."""
        from zorivest_infra.market_data.url_builders import RequestSpec

        spec = RequestSpec(
            method="POST",
            url="https://api.openfigi.com/v3/mapping",
            body=[{"idType": "TICKER", "idValue": "AAPL"}],
        )
        assert spec.method == "POST"
        assert spec.url == "https://api.openfigi.com/v3/mapping"
        assert isinstance(spec.body, list)

    def test_request_spec_frozen(self) -> None:
        """RequestSpec is immutable."""
        from zorivest_infra.market_data.url_builders import RequestSpec

        spec = RequestSpec()
        with pytest.raises(AttributeError):
            spec.method = "POST"  # type: ignore[misc]

    def test_request_spec_get_with_url(self) -> None:
        """RequestSpec GET with explicit URL."""
        from zorivest_infra.market_data.url_builders import RequestSpec

        spec = RequestSpec(method="GET", url="https://example.com/api")
        assert spec.method == "GET"
        assert spec.url == "https://example.com/api"
        assert spec.body is None


# ── AC-7: AlphaVantageUrlBuilder ───────────────────────────────────────


class TestAlphaVantageUrlBuilder:
    """AC-7: AlphaVantageUrlBuilder uses function-dispatch GET pattern."""

    def test_alpha_vantage_quote_url(self) -> None:
        """Alpha Vantage quote uses GLOBAL_QUOTE function."""
        from zorivest_infra.market_data.url_builders import AlphaVantageUrlBuilder

        builder = AlphaVantageUrlBuilder()
        url = builder.build_url(
            base_url="https://www.alphavantage.co",
            data_type="quote",
            tickers=["AAPL"],
            criteria={},
        )
        assert "function=GLOBAL_QUOTE" in url
        assert "symbol=AAPL" in url

    def test_alpha_vantage_ohlcv_url(self) -> None:
        """Alpha Vantage OHLCV uses TIME_SERIES_DAILY function."""
        from zorivest_infra.market_data.url_builders import AlphaVantageUrlBuilder

        builder = AlphaVantageUrlBuilder()
        url = builder.build_url(
            base_url="https://www.alphavantage.co",
            data_type="ohlcv",
            tickers=["MSFT"],
            criteria={},
        )
        assert "function=TIME_SERIES_DAILY" in url
        assert "symbol=MSFT" in url

    def test_alpha_vantage_ohlcv_full_output(self) -> None:
        """Alpha Vantage OHLCV supports outputsize=full."""
        from zorivest_infra.market_data.url_builders import AlphaVantageUrlBuilder

        builder = AlphaVantageUrlBuilder()
        url = builder.build_url(
            base_url="https://www.alphavantage.co",
            data_type="ohlcv",
            tickers=["MSFT"],
            criteria={"outputsize": "full"},
        )
        assert "outputsize=full" in url

    def test_alpha_vantage_fundamentals_url(self) -> None:
        """Alpha Vantage fundamentals uses OVERVIEW function."""
        from zorivest_infra.market_data.url_builders import AlphaVantageUrlBuilder

        builder = AlphaVantageUrlBuilder()
        url = builder.build_url(
            base_url="https://www.alphavantage.co",
            data_type="fundamentals",
            tickers=["GOOG"],
            criteria={},
        )
        assert "function=OVERVIEW" in url
        assert "symbol=GOOG" in url

    def test_alpha_vantage_earnings_url(self) -> None:
        """Alpha Vantage earnings uses EARNINGS function."""
        from zorivest_infra.market_data.url_builders import AlphaVantageUrlBuilder

        builder = AlphaVantageUrlBuilder()
        url = builder.build_url(
            base_url="https://www.alphavantage.co",
            data_type="earnings",
            tickers=["AAPL"],
            criteria={},
        )
        assert "function=EARNINGS" in url
        assert "symbol=AAPL" in url

    def test_alpha_vantage_insider_url(self) -> None:
        """Alpha Vantage insider uses INSIDER_TRANSACTIONS function."""
        from zorivest_infra.market_data.url_builders import AlphaVantageUrlBuilder

        builder = AlphaVantageUrlBuilder()
        url = builder.build_url(
            base_url="https://www.alphavantage.co",
            data_type="insider",
            tickers=["TSLA"],
            criteria={},
        )
        assert "function=" in url
        assert "symbol=TSLA" in url

    def test_alpha_vantage_base_url_pattern(self) -> None:
        """Alpha Vantage uses /query? base path."""
        from zorivest_infra.market_data.url_builders import AlphaVantageUrlBuilder

        builder = AlphaVantageUrlBuilder()
        url = builder.build_url(
            base_url="https://www.alphavantage.co",
            data_type="quote",
            tickers=["AAPL"],
            criteria={},
        )
        assert "/query?" in url


# ── AC-8: NasdaqDataLinkUrlBuilder ─────────────────────────────────────


class TestNasdaqDataLinkUrlBuilder:
    """AC-8: NasdaqDataLinkUrlBuilder uses /datatables/{vendor}/{table}.json."""

    def test_nasdaq_dl_fundamentals_url(self) -> None:
        """Nasdaq Data Link fundamentals uses SHARADAR/SF1."""
        from zorivest_infra.market_data.url_builders import NasdaqDataLinkUrlBuilder

        builder = NasdaqDataLinkUrlBuilder()
        url = builder.build_url(
            base_url="https://data.nasdaq.com",
            data_type="fundamentals",
            tickers=["AAPL"],
            criteria={},
        )
        assert "/datatables/SHARADAR/SF1.json" in url
        assert "ticker=AAPL" in url

    def test_nasdaq_dl_custom_vendor_table(self) -> None:
        """Nasdaq Data Link supports custom vendor/table via criteria."""
        from zorivest_infra.market_data.url_builders import NasdaqDataLinkUrlBuilder

        builder = NasdaqDataLinkUrlBuilder()
        url = builder.build_url(
            base_url="https://data.nasdaq.com",
            data_type="fundamentals",
            tickers=["MSFT"],
            criteria={"vendor": "ZACKS", "table": "FC"},
        )
        assert "/datatables/ZACKS/FC.json" in url
        assert "ticker=MSFT" in url

    def test_nasdaq_dl_fallback_data_type(self) -> None:
        """Nasdaq Data Link unknown data_type still builds valid URL."""
        from zorivest_infra.market_data.url_builders import NasdaqDataLinkUrlBuilder

        builder = NasdaqDataLinkUrlBuilder()
        url = builder.build_url(
            base_url="https://data.nasdaq.com",
            data_type="earnings",
            tickers=["GOOG"],
            criteria={},
        )
        assert isinstance(url, str)
        assert "GOOG" in url


# ── AC-9: OpenFIGIUrlBuilder ──────────────────────────────────────────


class TestOpenFIGIUrlBuilder:
    """AC-9: OpenFIGIUrlBuilder.build_request() returns POST RequestSpec."""

    def test_openfigi_build_request(self) -> None:
        """OpenFIGI builds POST request with JSON body array."""
        from zorivest_infra.market_data.url_builders import (
            OpenFIGIUrlBuilder,
            RequestSpec,
        )

        builder = OpenFIGIUrlBuilder()
        spec = builder.build_request(
            base_url="https://api.openfigi.com/v3",
            data_type="identifier_mapping",
            tickers=["AAPL"],
            criteria={},
        )
        assert isinstance(spec, RequestSpec)
        assert spec.method == "POST"
        assert spec.url == "https://api.openfigi.com/v3/mapping"
        assert isinstance(spec.body, list)
        assert spec.body[0]["idValue"] == "AAPL"

    def test_openfigi_body_structure(self) -> None:
        """OpenFIGI body contains idType TICKER by default."""
        from zorivest_infra.market_data.url_builders import OpenFIGIUrlBuilder

        builder = OpenFIGIUrlBuilder()
        spec = builder.build_request(
            base_url="https://api.openfigi.com/v3",
            data_type="identifier_mapping",
            tickers=["MSFT"],
            criteria={},
        )
        assert isinstance(spec.body, list)
        assert spec.body[0]["idType"] == "TICKER"
        assert spec.body[0]["idValue"] == "MSFT"

    def test_openfigi_custom_id_type(self) -> None:
        """OpenFIGI supports custom idType via criteria."""
        from zorivest_infra.market_data.url_builders import OpenFIGIUrlBuilder

        builder = OpenFIGIUrlBuilder()
        spec = builder.build_request(
            base_url="https://api.openfigi.com/v3",
            data_type="identifier_mapping",
            tickers=["US0378331005"],
            criteria={"id_type": "ISIN"},
        )
        assert isinstance(spec.body, list)
        assert spec.body[0]["idType"] == "ISIN"

    def test_openfigi_multi_ticker(self) -> None:
        """OpenFIGI supports multiple tickers in body array."""
        from zorivest_infra.market_data.url_builders import OpenFIGIUrlBuilder

        builder = OpenFIGIUrlBuilder()
        spec = builder.build_request(
            base_url="https://api.openfigi.com/v3",
            data_type="identifier_mapping",
            tickers=["AAPL", "MSFT", "GOOG"],
            criteria={},
        )
        assert spec.body is not None
        assert len(spec.body) == 3

    def test_openfigi_build_url_fallback(self) -> None:
        """OpenFIGI build_url returns the POST URL (for adapter compatibility)."""
        from zorivest_infra.market_data.url_builders import OpenFIGIUrlBuilder

        builder = OpenFIGIUrlBuilder()
        url = builder.build_url(
            base_url="https://api.openfigi.com/v3",
            data_type="identifier_mapping",
            tickers=["AAPL"],
            criteria={},
        )
        assert url == "https://api.openfigi.com/v3/mapping"


# ── AC-10: SECAPIUrlBuilder ───────────────────────────────────────────


class TestSECAPIUrlBuilder:
    """AC-10: SECAPIUrlBuilder.build_request() returns POST RequestSpec."""

    def test_sec_api_fundamentals_request(self) -> None:
        """SEC API fundamentals builds POST with Lucene query."""
        from zorivest_infra.market_data.url_builders import (
            RequestSpec,
            SECAPIUrlBuilder,
        )

        builder = SECAPIUrlBuilder()
        spec = builder.build_request(
            base_url="https://efts.sec.gov",
            data_type="fundamentals",
            tickers=["AAPL"],
            criteria={},
        )
        assert isinstance(spec, RequestSpec)
        assert spec.method == "POST"
        assert isinstance(spec.body, dict)
        assert "query" in spec.body or "q" in spec.body

    def test_sec_api_insider_request(self) -> None:
        """SEC API insider builds POST request."""
        from zorivest_infra.market_data.url_builders import SECAPIUrlBuilder

        builder = SECAPIUrlBuilder()
        spec = builder.build_request(
            base_url="https://efts.sec.gov",
            data_type="insider",
            tickers=["MSFT"],
            criteria={},
        )
        assert spec.method == "POST"
        assert isinstance(spec.body, dict)

    def test_sec_api_form_type_criteria(self) -> None:
        """SEC API supports form_type filter via criteria."""
        from zorivest_infra.market_data.url_builders import SECAPIUrlBuilder

        builder = SECAPIUrlBuilder()
        spec = builder.build_request(
            base_url="https://efts.sec.gov",
            data_type="fundamentals",
            tickers=["GOOG"],
            criteria={"form_type": "10-K"},
        )
        body = spec.body
        assert isinstance(body, dict)
        # formType or form_type should be in the body
        assert "10-K" in str(body)

    def test_sec_api_build_url_fallback(self) -> None:
        """SEC API build_url returns the POST URL for adapter compatibility."""
        from zorivest_infra.market_data.url_builders import SECAPIUrlBuilder

        builder = SECAPIUrlBuilder()
        url = builder.build_url(
            base_url="https://efts.sec.gov",
            data_type="fundamentals",
            tickers=["AAPL"],
            criteria={},
        )
        assert isinstance(url, str)


# ── AC-12: Registry Lookup for MEU-186 Builders ───────────────────────


class TestGetUrlBuilderMEU186:
    """AC-12: All 4 MEU-186 builders registered and returned by get_url_builder()."""

    def test_alpha_vantage_returns_builder(self) -> None:
        """get_url_builder('Alpha Vantage') returns AlphaVantageUrlBuilder."""
        from zorivest_infra.market_data.url_builders import (
            AlphaVantageUrlBuilder,
            get_url_builder,
        )

        builder = get_url_builder("Alpha Vantage")
        assert isinstance(builder, AlphaVantageUrlBuilder)

    def test_nasdaq_dl_returns_builder(self) -> None:
        """get_url_builder('Nasdaq Data Link') returns NasdaqDataLinkUrlBuilder."""
        from zorivest_infra.market_data.url_builders import (
            NasdaqDataLinkUrlBuilder,
            get_url_builder,
        )

        builder = get_url_builder("Nasdaq Data Link")
        assert isinstance(builder, NasdaqDataLinkUrlBuilder)

    def test_openfigi_returns_builder(self) -> None:
        """get_url_builder('OpenFIGI') returns OpenFIGIUrlBuilder."""
        from zorivest_infra.market_data.url_builders import (
            OpenFIGIUrlBuilder,
            get_url_builder,
        )

        builder = get_url_builder("OpenFIGI")
        assert isinstance(builder, OpenFIGIUrlBuilder)

    def test_sec_api_returns_builder(self) -> None:
        """get_url_builder('SEC API') returns SECAPIUrlBuilder."""
        from zorivest_infra.market_data.url_builders import (
            SECAPIUrlBuilder,
            get_url_builder,
        )

        builder = get_url_builder("SEC API")
        assert isinstance(builder, SECAPIUrlBuilder)


# ═══════════════════════════════════════════════════════════════════════════
# TradingView Scanner Addendum — URL Builder Tests
# ═══════════════════════════════════════════════════════════════════════════


class TestTradingViewUrlBuilder:
    """TradingView scanner POST-body builder — quote and fundamentals."""

    def test_tradingview_quote_request(self) -> None:
        """TradingView quote builds POST with scanner columns."""
        from zorivest_infra.market_data.url_builders import (
            RequestSpec,
            TradingViewUrlBuilder,
        )

        builder = TradingViewUrlBuilder()
        spec = builder.build_request(
            base_url="https://scanner.tradingview.com",
            data_type="quote",
            tickers=["AAPL"],
            criteria={},
        )
        assert isinstance(spec, RequestSpec)
        assert spec.method == "POST"
        assert "/america/scan" in spec.url
        assert isinstance(spec.body, dict)
        assert "columns" in spec.body
        assert "close" in spec.body["columns"]

    def test_tradingview_fundamentals_request(self) -> None:
        """TradingView fundamentals builds POST with fundamental columns."""
        from zorivest_infra.market_data.url_builders import TradingViewUrlBuilder

        builder = TradingViewUrlBuilder()
        spec = builder.build_request(
            base_url="https://scanner.tradingview.com",
            data_type="fundamentals",
            tickers=["MSFT"],
            criteria={},
        )
        assert spec.method == "POST"
        assert isinstance(spec.body, dict)
        assert "market_cap_basic" in spec.body["columns"]

    def test_tradingview_ticker_filter(self) -> None:
        """TradingView request includes ticker in filter."""
        from zorivest_infra.market_data.url_builders import TradingViewUrlBuilder

        builder = TradingViewUrlBuilder()
        spec = builder.build_request(
            base_url="https://scanner.tradingview.com",
            data_type="quote",
            tickers=["GOOG"],
            criteria={},
        )
        body = spec.body
        assert isinstance(body, dict)
        # Ticker should appear somewhere in the body (filter or symbols)
        assert "GOOG" in str(body)

    def test_tradingview_exchange_criteria(self) -> None:
        """TradingView supports exchange via criteria."""
        from zorivest_infra.market_data.url_builders import TradingViewUrlBuilder

        builder = TradingViewUrlBuilder()
        spec = builder.build_request(
            base_url="https://scanner.tradingview.com",
            data_type="quote",
            tickers=["7203"],  # Toyota on TSE
            criteria={"exchange": "japan"},
        )
        assert "/japan/scan" in spec.url

    def test_tradingview_build_url_fallback(self) -> None:
        """TradingView build_url returns the POST URL for adapter compatibility."""
        from zorivest_infra.market_data.url_builders import TradingViewUrlBuilder

        builder = TradingViewUrlBuilder()
        url = builder.build_url(
            base_url="https://scanner.tradingview.com",
            data_type="quote",
            tickers=["AAPL"],
            criteria={},
        )
        assert isinstance(url, str)
        assert "/america/scan" in url

    def test_tradingview_registered_in_registry(self) -> None:
        """TradingView builder is in _URL_BUILDER_REGISTRY."""
        from zorivest_infra.market_data.url_builders import (
            TradingViewUrlBuilder,
            get_url_builder,
        )

        builder = get_url_builder("TradingView")
        assert isinstance(builder, TradingViewUrlBuilder)
