"""Tests for market data response normalizers — MEU-61 RED phase.

Source: docs/build-plan/08-market-data.md §8.3c.
Tests each normalizer function with realistic provider JSON fixtures.
"""

from __future__ import annotations


import pytest

from zorivest_core.application.market_dtos import (
    MarketNewsItem,
    MarketQuote,
    SecFiling,
    TickerSearchResult,
)
from zorivest_infra.market_data.normalizers import (
    normalize_alpha_vantage_quote,
    normalize_alpha_vantage_search,
    normalize_api_ninjas_quote,
    normalize_eodhd_quote,
    normalize_finnhub_news,
    normalize_finnhub_quote,
    normalize_fmp_search,
    normalize_polygon_quote,
    normalize_sec_filing,
)


# ── Fixtures ────────────────────────────────────────────────────────────


@pytest.fixture()
def alpha_vantage_quote_data() -> dict:
    """Alpha Vantage Global Quote response."""
    return {
        "Global Quote": {
            "01. symbol": "AAPL",
            "02. open": "178.5500",
            "03. high": "182.0100",
            "04. low": "177.9900",
            "05. price": "181.1800",
            "06. volume": "52436877",
            "07. latest trading day": "2024-03-08",
            "08. previous close": "178.6500",
            "09. change": "2.5300",
            "10. change percent": "1.4163%",
        }
    }


@pytest.fixture()
def polygon_quote_data() -> dict:
    """Polygon.io v2 snapshot response."""
    return {
        "results": [
            {
                "T": "AAPL",
                "o": 178.55,
                "h": 182.01,
                "l": 177.99,
                "c": 181.18,
                "v": 52436877,
                "vw": 180.25,
                "t": 1709856000000,
            }
        ]
    }


@pytest.fixture()
def finnhub_quote_data() -> dict:
    """Finnhub /quote response."""
    return {
        "c": 181.18,
        "d": 2.53,
        "dp": 1.4163,
        "h": 182.01,
        "l": 177.99,
        "o": 178.55,
        "pc": 178.65,
        "t": 1709856000,
    }


@pytest.fixture()
def eodhd_quote_data() -> dict:
    """EODHD real-time endpoint response."""
    return {
        "code": "AAPL.US",
        "timestamp": 1709856000,
        "gmtoffset": 0,
        "open": 178.55,
        "high": 182.01,
        "low": 177.99,
        "close": 181.18,
        "volume": 52436877,
        "previousClose": 178.65,
        "change": 2.53,
        "change_p": 1.4163,
    }


@pytest.fixture()
def api_ninjas_quote_data() -> dict:
    """API Ninjas /stockprice response."""
    return {
        "ticker": "AAPL",
        "name": "Apple Inc.",
        "price": 181.18,
        "exchange": "NASDAQ",
        "updated": 1709856000,
    }


@pytest.fixture()
def fmp_search_data() -> list:
    """Financial Modeling Prep /search response."""
    return [
        {
            "symbol": "AAPL",
            "name": "Apple Inc.",
            "currency": "USD",
            "stockExchange": "NASDAQ Global Select",
            "exchangeShortName": "NASDAQ",
        },
        {
            "symbol": "APLE",
            "name": "Apple Hospitality REIT Inc.",
            "currency": "USD",
            "stockExchange": "New York Stock Exchange",
            "exchangeShortName": "NYSE",
        },
    ]


@pytest.fixture()
def sec_filing_data() -> list:
    """SEC API /mapping/ticker response."""
    return [
        {
            "ticker": "AAPL",
            "companyName": "Apple Inc.",
            "cik": "0000320193",
            "formType": "10-K",
            "filedAt": "2024-11-01T16:30:24-04:00",
        },
        {
            "ticker": "AAPL",
            "companyName": "Apple Inc.",
            "cik": "0000320193",
            "formType": "10-Q",
            "filedAt": "2024-08-02T16:30:24-04:00",
        },
    ]


@pytest.fixture()
def finnhub_news_data() -> list:
    """Finnhub /company-news response."""
    return [
        {
            "category": "company",
            "datetime": 1709856000,
            "headline": "Apple Unveils New Product Line",
            "id": 67890,
            "image": "https://example.com/image.jpg",
            "related": "AAPL",
            "source": "Reuters",
            "summary": "Apple announced a new product line today...",
            "url": "https://www.reuters.com/article/67890",
        },
        {
            "category": "company",
            "datetime": 1709770000,
            "headline": "Market Update",
            "id": 67891,
            "image": "",
            "related": "AAPL,MSFT",
            "source": "MarketWatch",
            "summary": "Markets ended higher on Friday...",
            "url": "https://www.marketwatch.com/story/67891",
        },
    ]


# ── Alpha Vantage ───────────────────────────────────────────────────────


class TestNormalizeAlphaVantageQuote:
    """Tests for normalize_alpha_vantage_quote."""

    def test_full_response(self, alpha_vantage_quote_data: dict) -> None:
        result = normalize_alpha_vantage_quote(alpha_vantage_quote_data)

        assert isinstance(result, MarketQuote)
        assert result.ticker == "AAPL"
        assert result.price == pytest.approx(181.18)
        assert result.open == pytest.approx(178.55)
        assert result.high == pytest.approx(182.01)
        assert result.low == pytest.approx(177.99)
        assert result.previous_close == pytest.approx(178.65)
        assert result.change == pytest.approx(2.53)
        assert result.change_pct == pytest.approx(1.4163)
        assert result.volume == 52436877
        assert result.provider == "Alpha Vantage"

    def test_empty_global_quote(self) -> None:
        result = normalize_alpha_vantage_quote({})

        assert isinstance(result, MarketQuote)
        assert result.ticker == ""
        assert result.price == 0.0
        assert result.provider == "Alpha Vantage"

    def test_missing_fields_use_defaults(self) -> None:
        data = {"Global Quote": {"01. symbol": "GOOG", "05. price": "150.00"}}
        result = normalize_alpha_vantage_quote(data)

        assert result.ticker == "GOOG"
        assert result.price == pytest.approx(150.0)
        assert result.open == pytest.approx(0.0)


# ── Polygon.io ──────────────────────────────────────────────────────────


class TestNormalizePolygonQuote:
    """Tests for normalize_polygon_quote."""

    def test_full_response(self, polygon_quote_data: dict) -> None:
        result = normalize_polygon_quote(polygon_quote_data)

        assert isinstance(result, MarketQuote)
        assert result.ticker == "AAPL"
        assert result.price == pytest.approx(181.18)
        assert result.open == pytest.approx(178.55)
        assert result.high == pytest.approx(182.01)
        assert result.low == pytest.approx(177.99)
        assert result.volume == 52436877
        assert result.provider == "Polygon.io"

    def test_empty_results(self) -> None:
        result = normalize_polygon_quote({"results": []})

        assert isinstance(result, MarketQuote)
        assert result.ticker == ""
        assert result.price == 0.0

    def test_missing_results_key(self) -> None:
        result = normalize_polygon_quote({})

        assert isinstance(result, MarketQuote)
        assert result.ticker == ""


# ── Finnhub ─────────────────────────────────────────────────────────────


class TestNormalizeFinnhubQuote:
    """Tests for normalize_finnhub_quote."""

    def test_full_response(self, finnhub_quote_data: dict) -> None:
        result = normalize_finnhub_quote(finnhub_quote_data, ticker="AAPL")

        assert isinstance(result, MarketQuote)
        assert result.ticker == "AAPL"
        assert result.price == pytest.approx(181.18)
        assert result.open == pytest.approx(178.55)
        assert result.high == pytest.approx(182.01)
        assert result.low == pytest.approx(177.99)
        assert result.previous_close == pytest.approx(178.65)
        assert result.change == pytest.approx(2.53)
        assert result.change_pct == pytest.approx(1.4163)
        assert result.provider == "Finnhub"

    def test_empty_response(self) -> None:
        result = normalize_finnhub_quote({}, ticker="AAPL")

        assert isinstance(result, MarketQuote)
        assert result.ticker == "AAPL"
        assert result.price == 0.0


# ── EODHD ───────────────────────────────────────────────────────────────


class TestNormalizeEodhdQuote:
    """Tests for normalize_eodhd_quote."""

    def test_full_response(self, eodhd_quote_data: dict) -> None:
        result = normalize_eodhd_quote(eodhd_quote_data)

        assert isinstance(result, MarketQuote)
        assert result.ticker == "AAPL.US"
        assert result.price == pytest.approx(181.18)
        assert result.open == pytest.approx(178.55)
        assert result.high == pytest.approx(182.01)
        assert result.low == pytest.approx(177.99)
        assert result.previous_close == pytest.approx(178.65)
        assert result.change == pytest.approx(2.53)
        assert result.change_pct == pytest.approx(1.4163)
        assert result.volume == 52436877
        assert result.provider == "EODHD"

    def test_empty_response(self) -> None:
        result = normalize_eodhd_quote({})

        assert isinstance(result, MarketQuote)
        assert result.ticker == ""
        assert result.price == 0.0


# ── API Ninjas ──────────────────────────────────────────────────────────


class TestNormalizeApiNinjasQuote:
    """Tests for normalize_api_ninjas_quote."""

    def test_full_response(self, api_ninjas_quote_data: dict) -> None:
        result = normalize_api_ninjas_quote(api_ninjas_quote_data)

        assert isinstance(result, MarketQuote)
        assert result.ticker == "AAPL"
        assert result.price == pytest.approx(181.18)
        assert result.provider == "API Ninjas"

    def test_empty_response(self) -> None:
        result = normalize_api_ninjas_quote({})

        assert isinstance(result, MarketQuote)
        assert result.ticker == ""
        assert result.price == 0.0


# ── FMP Search ──────────────────────────────────────────────────────────


class TestNormalizeFmpSearch:
    """Tests for normalize_fmp_search."""

    def test_multiple_results(self, fmp_search_data: list) -> None:
        results = normalize_fmp_search(fmp_search_data)

        assert len(results) == 2
        assert all(isinstance(r, TickerSearchResult) for r in results)

        assert results[0].symbol == "AAPL"
        assert results[0].name == "Apple Inc."
        assert results[0].exchange == "NASDAQ"
        assert results[0].currency == "USD"
        assert results[0].provider == "Financial Modeling Prep"

        assert results[1].symbol == "APLE"
        assert results[1].exchange == "NYSE"

    def test_empty_list(self) -> None:
        results = normalize_fmp_search([])
        assert results == []

    def test_missing_optional_fields(self) -> None:
        data = [{"symbol": "AAPL", "name": "Apple Inc."}]
        results = normalize_fmp_search(data)

        assert len(results) == 1
        assert results[0].symbol == "AAPL"
        assert results[0].exchange is None
        assert results[0].currency is None


# ── Alpha Vantage Search ────────────────────────────────────────────────


class TestNormalizeAlphaVantageSearch:
    """Tests for normalize_alpha_vantage_search."""

    def test_multiple_results(self) -> None:
        data = {
            "bestMatches": [
                {
                    "1. symbol": "AAPL",
                    "2. name": "Apple Inc.",
                    "3. type": "Equity",
                    "4. region": "United States",
                    "5. marketOpen": "09:30",
                    "6. marketClose": "16:00",
                    "7. timezone": "UTC-04",
                    "8. currency": "USD",
                    "9. matchScore": "1.0000",
                },
                {
                    "1. symbol": "APLE",
                    "2. name": "Apple Hospitality REIT Inc.",
                    "4. region": "United States",
                    "8. currency": "USD",
                },
            ]
        }
        results = normalize_alpha_vantage_search(data)

        assert len(results) == 2
        assert all(isinstance(r, TickerSearchResult) for r in results)
        assert results[0].symbol == "AAPL"
        assert results[0].name == "Apple Inc."
        assert results[0].exchange == "United States"
        assert results[0].currency == "USD"
        assert results[0].provider == "Alpha Vantage"
        assert results[1].symbol == "APLE"

    def test_empty_best_matches(self) -> None:
        results = normalize_alpha_vantage_search({"bestMatches": []})
        assert results == []

    def test_missing_best_matches_key(self) -> None:
        results = normalize_alpha_vantage_search({})
        assert results == []


# ── SEC Filings ─────────────────────────────────────────────────────────


class TestNormalizeSecFiling:
    """Tests for normalize_sec_filing."""

    def test_multiple_filings(self, sec_filing_data: list) -> None:
        results = normalize_sec_filing(sec_filing_data)

        assert len(results) == 2
        assert all(isinstance(r, SecFiling) for r in results)

        assert results[0].ticker == "AAPL"
        assert results[0].company_name == "Apple Inc."
        assert results[0].cik == "0000320193"
        assert results[0].filing_type == "10-K"
        assert results[0].filing_date is not None
        assert results[0].provider == "SEC API"

        assert results[1].filing_type == "10-Q"

    def test_empty_list(self) -> None:
        results = normalize_sec_filing([])
        assert results == []

    def test_missing_optional_fields(self) -> None:
        data = [{"ticker": "GOOG", "companyName": "Alphabet Inc.", "cik": "0001652044"}]
        results = normalize_sec_filing(data)

        assert len(results) == 1
        assert results[0].filing_type is None
        assert results[0].filing_date is None


# ── Finnhub News ────────────────────────────────────────────────────────


class TestNormalizeFinnhubNews:
    """Tests for normalize_finnhub_news."""

    def test_multiple_articles(self, finnhub_news_data: list) -> None:
        results = normalize_finnhub_news(finnhub_news_data)

        assert len(results) == 2
        assert all(isinstance(r, MarketNewsItem) for r in results)

        assert results[0].title == "Apple Unveils New Product Line"
        assert results[0].source == "Reuters"
        assert results[0].url == "https://www.reuters.com/article/67890"
        assert results[0].tickers == ["AAPL"]
        assert results[0].summary == "Apple announced a new product line today..."
        assert results[0].published_at is not None
        assert results[0].provider == "Finnhub"

        assert results[1].source == "MarketWatch"
        assert results[1].tickers == ["AAPL", "MSFT"]

    def test_empty_list(self) -> None:
        results = normalize_finnhub_news([])
        assert results == []

    def test_missing_optional_fields(self) -> None:
        data = [{"headline": "Test", "source": "Unknown", "id": 1}]
        results = normalize_finnhub_news(data)

        assert len(results) == 1
        assert results[0].title == "Test"
        assert results[0].source == "Unknown"
        assert results[0].tickers == []
