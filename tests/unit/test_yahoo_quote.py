"""Tests for MarketDataService._yahoo_quote — MEU-70a fix.

Source: docs/build-plan/06i-gui-watchlist-visual.md §A L1 (price columns).

Tests that _yahoo_quote extracts change, change_pct, and volume
from the Yahoo Finance /v8/finance/chart API response.

The original implementation (MEU-91) only extracted price and
previousClose. These tests verify the complete field extraction
needed by the watchlist table (CHG $, CHG %, Volume columns).

Uses asyncio.run() since pytest-asyncio is not installed.
"""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from zorivest_core.services.market_data_service import MarketDataService


# ── Helpers ─────────────────────────────────────────────────────────────


class FakeHttpResponse:
    """Minimal HTTP response for testing."""

    def __init__(self, status_code: int = 200, data: Any = None) -> None:
        self.status_code = status_code
        self._data = data or {}

    def json(self) -> Any:
        return self._data


def _make_service_for_yahoo(
    *,
    http_responses: list[FakeHttpResponse] | None = None,
) -> MarketDataService:
    """Create a MarketDataService wired for Yahoo-only testing.

    Does NOT mock _yahoo_quote — tests the real method.
    """
    fake_uow = MagicMock()
    fake_uow.__enter__ = MagicMock(return_value=fake_uow)
    fake_uow.__exit__ = MagicMock(return_value=False)
    fake_settings_repo = MagicMock()
    fake_settings_repo.list_all.return_value = []
    fake_uow.market_provider_settings = fake_settings_repo

    fake_encryption = MagicMock()
    fake_http = AsyncMock()
    if http_responses:
        fake_http.get.side_effect = http_responses
    else:
        fake_http.get.return_value = FakeHttpResponse()

    return MarketDataService(
        uow=fake_uow,
        encryption=fake_encryption,
        http_client=fake_http,
        rate_limiters={},
        provider_registry={},
        quote_normalizers={},
        news_normalizers={},
        search_normalizers={},
    )


def _yahoo_chart_response(
    *,
    price: float = 348.95,
    previous_close: float = 345.50,
    volume: int = 42_500_000,
    include_volume: bool = True,
    include_previous_close: bool = True,
) -> dict[str, Any]:
    """Build a realistic Yahoo Finance /v8/finance/chart response."""
    meta: dict[str, Any] = {"regularMarketPrice": price}
    if include_previous_close:
        meta["chartPreviousClose"] = previous_close
    if include_volume:
        meta["regularMarketVolume"] = volume

    return {
        "chart": {
            "result": [
                {
                    "meta": meta,
                    "timestamp": [1712000000],
                    "indicators": {"quote": [{}]},
                }
            ],
            "error": None,
        }
    }


# ── Tests ───────────────────────────────────────────────────────────────


class TestYahooQuoteFieldExtraction:
    """Verify _yahoo_quote returns complete MarketQuote with change/volume."""

    def test_returns_change_dollar_computed_from_price_minus_previous_close(
        self,
    ) -> None:
        """AC-1: change = regularMarketPrice - chartPreviousClose."""
        data = _yahoo_chart_response(price=348.95, previous_close=345.50)
        response = FakeHttpResponse(200, data)
        svc = _make_service_for_yahoo(http_responses=[response])

        result = asyncio.run(svc.get_quote("TSLA"))

        assert result.change is not None, "change must not be None"
        expected_change = 348.95 - 345.50  # 3.45
        assert result.change == pytest.approx(expected_change, abs=0.01)

    def test_returns_change_pct_computed_from_change_divided_by_previous_close(
        self,
    ) -> None:
        """AC-2: change_pct = (change / chartPreviousClose) * 100."""
        data = _yahoo_chart_response(price=348.95, previous_close=345.50)
        response = FakeHttpResponse(200, data)
        svc = _make_service_for_yahoo(http_responses=[response])

        result = asyncio.run(svc.get_quote("TSLA"))

        assert result.change_pct is not None, "change_pct must not be None"
        expected_change = 348.95 - 345.50
        expected_pct = (expected_change / 345.50) * 100  # ~0.999
        assert result.change_pct == pytest.approx(expected_pct, abs=0.01)

    def test_returns_volume_from_regular_market_volume(self) -> None:
        """AC-3: volume = meta.regularMarketVolume."""
        data = _yahoo_chart_response(volume=42_500_000)
        response = FakeHttpResponse(200, data)
        svc = _make_service_for_yahoo(http_responses=[response])

        result = asyncio.run(svc.get_quote("TSLA"))

        assert result.volume is not None, "volume must not be None"
        assert result.volume == 42_500_000

    def test_returns_negative_change_for_price_drop(self) -> None:
        """AC-4: negative change when price < previousClose."""
        data = _yahoo_chart_response(price=340.00, previous_close=345.50)
        response = FakeHttpResponse(200, data)
        svc = _make_service_for_yahoo(http_responses=[response])

        result = asyncio.run(svc.get_quote("TSLA"))

        assert result.change is not None
        assert result.change < 0
        assert result.change == pytest.approx(-5.50, abs=0.01)
        assert result.change_pct is not None
        assert result.change_pct < 0

    def test_returns_zero_change_when_price_equals_previous_close(self) -> None:
        """AC-5: zero change when price == previousClose."""
        data = _yahoo_chart_response(price=345.50, previous_close=345.50)
        response = FakeHttpResponse(200, data)
        svc = _make_service_for_yahoo(http_responses=[response])

        result = asyncio.run(svc.get_quote("TSLA"))

        assert result.change is not None
        assert result.change == pytest.approx(0.0, abs=0.001)
        assert result.change_pct is not None
        assert result.change_pct == pytest.approx(0.0, abs=0.001)

    def test_change_fields_none_when_no_previous_close(self) -> None:
        """AC-6: graceful degradation — change/change_pct are None
        when chartPreviousClose is missing."""
        data = _yahoo_chart_response(include_previous_close=False)
        response = FakeHttpResponse(200, data)
        svc = _make_service_for_yahoo(http_responses=[response])

        result = asyncio.run(svc.get_quote("TSLA"))

        # Price should still work
        assert result.price == pytest.approx(348.95)
        # Without previous close, can't compute change
        assert result.change is None
        assert result.change_pct is None

    def test_volume_none_when_missing_from_meta(self) -> None:
        """AC-7: graceful degradation — volume is None when not in response."""
        data = _yahoo_chart_response(include_volume=False)
        response = FakeHttpResponse(200, data)
        svc = _make_service_for_yahoo(http_responses=[response])

        result = asyncio.run(svc.get_quote("TSLA"))

        assert result.price == pytest.approx(348.95)
        assert result.volume is None

    def test_provider_is_yahoo_finance(self) -> None:
        """AC-8: provider attribution is 'Yahoo Finance'."""
        data = _yahoo_chart_response()
        response = FakeHttpResponse(200, data)
        svc = _make_service_for_yahoo(http_responses=[response])

        result = asyncio.run(svc.get_quote("TSLA"))

        assert result.provider == "Yahoo Finance"

    def test_ticker_preserved_in_result(self) -> None:
        """AC-9: ticker from input is preserved in the result."""
        data = _yahoo_chart_response()
        response = FakeHttpResponse(200, data)
        svc = _make_service_for_yahoo(http_responses=[response])

        result = asyncio.run(svc.get_quote("MRNA"))

        assert result.ticker == "MRNA"

    def test_returns_none_on_non_200_status(self) -> None:
        """AC-10: returns None (triggering provider fallback) on HTTP error."""
        response = FakeHttpResponse(403, {})
        svc = _make_service_for_yahoo(http_responses=[response])

        # With no providers configured, this should raise MarketDataError
        from zorivest_core.services.market_data_service import MarketDataError

        with pytest.raises(MarketDataError, match="No quote provider"):
            asyncio.run(svc.get_quote("TSLA"))

    def test_returns_none_when_no_results_in_chart(self) -> None:
        """AC-11: returns None when chart.result is empty."""
        data = {"chart": {"result": [], "error": None}}
        response = FakeHttpResponse(200, data)
        svc = _make_service_for_yahoo(http_responses=[response])

        from zorivest_core.services.market_data_service import MarketDataError

        with pytest.raises(MarketDataError, match="No quote provider"):
            asyncio.run(svc.get_quote("FAKE"))

    def test_volume_zero_is_preserved(self) -> None:
        """AC-12: volume of 0 is returned as 0, not None."""
        data = _yahoo_chart_response(volume=0)
        response = FakeHttpResponse(200, data)
        svc = _make_service_for_yahoo(http_responses=[response])

        result = asyncio.run(svc.get_quote("TSLA"))

        assert result.volume == 0
