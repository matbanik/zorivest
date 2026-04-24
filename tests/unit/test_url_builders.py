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

    def test_alpha_vantage_returns_generic_builder(self) -> None:
        """Unregistered providers like Alpha Vantage use GenericUrlBuilder."""
        from zorivest_infra.market_data.url_builders import (
            GenericUrlBuilder,
            get_url_builder,
        )

        builder = get_url_builder("Alpha Vantage")
        assert isinstance(builder, GenericUrlBuilder)
