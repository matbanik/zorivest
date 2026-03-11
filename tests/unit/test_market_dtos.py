"""Market data DTO tests — MEU-57 acceptance criteria.

Tests written FIRST (Red phase) before any implementation exists.
All values from docs/build-plan/08-market-data.md §8.1c.
"""

from __future__ import annotations

from datetime import datetime

import pytest

pytestmark = pytest.mark.unit


# ── AC-1: MarketQuote ────────────────────────────────────────────────────


class TestMarketQuote:
    """AC-1 [Spec]: MarketQuote has required ticker, price, provider + 8 optional."""

    def test_market_quote_required_fields(self) -> None:
        from zorivest_core.application.market_dtos import MarketQuote

        quote = MarketQuote(ticker="AAPL", price=185.50, provider="Alpha Vantage")
        assert quote.ticker == "AAPL"
        assert quote.price == 185.50
        assert quote.provider == "Alpha Vantage"

    def test_market_quote_optional_fields_default_none(self) -> None:
        from zorivest_core.application.market_dtos import MarketQuote

        quote = MarketQuote(ticker="AAPL", price=185.50, provider="test")
        assert quote.open is None
        assert quote.high is None
        assert quote.low is None
        assert quote.previous_close is None
        assert quote.change is None
        assert quote.change_pct is None
        assert quote.volume is None
        assert quote.timestamp is None

    def test_market_quote_all_fields(self) -> None:
        from zorivest_core.application.market_dtos import MarketQuote

        now = datetime(2026, 3, 11, 12, 0, 0)
        quote = MarketQuote(
            ticker="AAPL",
            price=185.50,
            open=184.00,
            high=186.00,
            low=183.50,
            previous_close=184.20,
            change=1.30,
            change_pct=0.71,
            volume=45_000_000,
            timestamp=now,
            provider="Finnhub",
        )
        assert quote.open == 184.00
        assert quote.volume == 45_000_000
        assert quote.timestamp == now

    def test_market_quote_json_round_trip(self) -> None:
        """AC-7: All DTOs serialize to/from JSON via Pydantic."""
        from zorivest_core.application.market_dtos import MarketQuote

        quote = MarketQuote(ticker="MSFT", price=420.00, provider="test")
        data = quote.model_dump()
        restored = MarketQuote.model_validate(data)
        assert restored.ticker == "MSFT"
        assert restored.price == 420.00

    def test_market_quote_invalid_type_rejected(self) -> None:
        from pydantic import ValidationError
        from zorivest_core.application.market_dtos import MarketQuote

        with pytest.raises(ValidationError):
            MarketQuote(ticker="AAPL", price="not_a_number", provider="test")  # type: ignore[arg-type]


# ── AC-2: MarketNewsItem ─────────────────────────────────────────────────


class TestMarketNewsItem:
    """AC-2 [Spec]: MarketNewsItem has required title, source, provider + optional."""

    def test_market_news_item_required_fields(self) -> None:
        from zorivest_core.application.market_dtos import MarketNewsItem

        item = MarketNewsItem(title="Test News", source="Reuters", provider="test")
        assert item.title == "Test News"
        assert item.source == "Reuters"

    def test_market_news_item_tickers_default_empty_list(self) -> None:
        """AC-3: tickers defaults to empty list via Field(default_factory=list)."""
        from zorivest_core.application.market_dtos import MarketNewsItem

        item = MarketNewsItem(title="Test", source="AP", provider="test")
        assert item.tickers == []
        assert isinstance(item.tickers, list)

    def test_market_news_item_optional_fields(self) -> None:
        from zorivest_core.application.market_dtos import MarketNewsItem

        item = MarketNewsItem(title="Test", source="AP", provider="test")
        assert item.url is None
        assert item.published_at is None
        assert item.summary is None

    def test_market_news_item_json_round_trip(self) -> None:
        from zorivest_core.application.market_dtos import MarketNewsItem

        item = MarketNewsItem(title="News", source="Reuters", provider="test")
        data = item.model_dump()
        restored = MarketNewsItem.model_validate(data)
        assert restored.title == "News"
        assert restored.source == "Reuters"


# ── AC-4: TickerSearchResult ─────────────────────────────────────────────


class TestTickerSearchResult:
    """AC-4 [Spec]: TickerSearchResult has required symbol, name, provider + optional."""

    def test_ticker_search_result_required_fields(self) -> None:
        from zorivest_core.application.market_dtos import TickerSearchResult

        result = TickerSearchResult(symbol="AAPL", name="Apple Inc.", provider="test")
        assert result.symbol == "AAPL"
        assert result.name == "Apple Inc."

    def test_ticker_search_result_optional_exchange_currency(self) -> None:
        from zorivest_core.application.market_dtos import TickerSearchResult

        result = TickerSearchResult(symbol="TSLA", name="Tesla", provider="test")
        assert result.exchange is None
        assert result.currency is None

    def test_ticker_search_result_json_round_trip(self) -> None:
        from zorivest_core.application.market_dtos import TickerSearchResult

        result = TickerSearchResult(symbol="AAPL", name="Apple Inc.", provider="test")
        data = result.model_dump()
        restored = TickerSearchResult.model_validate(data)
        assert restored.symbol == "AAPL"
        assert restored.name == "Apple Inc."


# ── AC-5: SecFiling ──────────────────────────────────────────────────────


class TestSecFiling:
    """AC-5/6 [Spec]: SecFiling has required ticker, company_name, cik + optional."""

    def test_sec_filing_required_fields(self) -> None:
        from zorivest_core.application.market_dtos import SecFiling

        filing = SecFiling(ticker="AAPL", company_name="Apple Inc.", cik="0000320193")
        assert filing.ticker == "AAPL"
        assert filing.company_name == "Apple Inc."
        assert filing.cik == "0000320193"

    def test_sec_filing_provider_defaults_to_sec_api(self) -> None:
        """AC-6: provider defaults to 'SEC API'."""
        from zorivest_core.application.market_dtos import SecFiling

        filing = SecFiling(ticker="AAPL", company_name="Apple Inc.", cik="0000320193")
        assert filing.provider == "SEC API"

    def test_sec_filing_optional_fields(self) -> None:
        from zorivest_core.application.market_dtos import SecFiling

        filing = SecFiling(ticker="AAPL", company_name="Apple Inc.", cik="0000320193")
        assert filing.filing_type is None
        assert filing.filing_date is None

    def test_sec_filing_json_round_trip(self) -> None:
        from zorivest_core.application.market_dtos import SecFiling

        filing = SecFiling(ticker="AAPL", company_name="Apple Inc.", cik="0000320193")
        data = filing.model_dump()
        restored = SecFiling.model_validate(data)
        assert restored.ticker == "AAPL"
        assert restored.provider == "SEC API"
