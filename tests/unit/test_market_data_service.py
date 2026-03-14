"""Tests for MarketDataService — MEU-61 RED phase.

Source: docs/build-plan/08-market-data.md §8.3b.
Tests provider fallback, normalizer dispatch, error handling, and rate limiting.

Uses asyncio.run() since pytest-asyncio is not installed.
"""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from zorivest_core.application.market_dtos import (
    MarketNewsItem,
    MarketQuote,
)
from zorivest_core.services.market_data_service import (
    MarketDataError,
    MarketDataService,
)


# ── Helpers ─────────────────────────────────────────────────────────────


class FakeHttpResponse:
    """Minimal HTTP response for testing."""

    def __init__(self, status_code: int = 200, data: Any = None) -> None:
        self.status_code = status_code
        self._data = data or {}

    def json(self) -> Any:
        return self._data


def _make_service(
    *,
    settings: list[Any] | None = None,
    http_responses: list[FakeHttpResponse] | None = None,
    http_side_effect: Exception | None = None,
) -> MarketDataService:
    """Create a MarketDataService with mocked dependencies."""
    # Fake UoW with market_provider_settings
    fake_settings_repo = MagicMock()
    fake_settings_repo.list_all.return_value = settings or []
    fake_settings_repo.get.return_value = None

    fake_uow = MagicMock()
    fake_uow.__enter__ = MagicMock(return_value=fake_uow)
    fake_uow.__exit__ = MagicMock(return_value=False)
    fake_uow.market_provider_settings = fake_settings_repo

    # Encryption (returns plaintext for testing)
    fake_encryption = MagicMock()
    fake_encryption.decrypt.side_effect = lambda x: x.replace("ENC:", "")

    # HTTP client
    fake_http = AsyncMock()
    if http_side_effect:
        fake_http.get.side_effect = http_side_effect
    elif http_responses:
        fake_http.get.side_effect = http_responses
    else:
        fake_http.get.return_value = FakeHttpResponse()

    # Rate limiters (no-op)
    fake_limiter = AsyncMock()
    fake_limiter.wait_if_needed = AsyncMock()

    # Provider registry (just quote-capable providers)
    from zorivest_core.domain.enums import AuthMethod
    from zorivest_core.domain.market_data import ProviderConfig

    registry = {
        "Alpha Vantage": ProviderConfig(
            name="Alpha Vantage",
            base_url="https://www.alphavantage.co/query",
            auth_method=AuthMethod.QUERY_PARAM,
            auth_param_name="apikey",
            headers_template={},
            test_endpoint="?function=GLOBAL_QUOTE&symbol=IBM&apikey={api_key}",
            default_rate_limit=5,
            signup_url="https://www.alphavantage.co",
            response_validator_key="Global Quote",
        ),
        "Finnhub": ProviderConfig(
            name="Finnhub",
            base_url="https://finnhub.io/api/v1",
            auth_method=AuthMethod.CUSTOM_HEADER,
            auth_param_name="X-Finnhub-Token",
            headers_template={"X-Finnhub-Token": "{api_key}"},
            test_endpoint="/quote?symbol=AAPL&token={api_key}",
            default_rate_limit=60,
            signup_url="https://finnhub.io/register",
            response_validator_key="c",
        ),
    }

    # Normalizer registries (simple pass-through for testing)
    quote_normalizers = {
        "Alpha Vantage": lambda data: MarketQuote(
            ticker=data.get("Global Quote", {}).get("01. symbol", ""),
            price=float(data.get("Global Quote", {}).get("05. price", 0)),
            provider="Alpha Vantage",
        ),
        "Finnhub": lambda data, ticker="": MarketQuote(
            ticker=ticker,
            price=float(data.get("c", 0)),
            provider="Finnhub",
        ),
    }

    news_normalizers = {
        "Finnhub": lambda data: [
            MarketNewsItem(
                title=item.get("headline", ""),
                source=item.get("source", ""),
                provider="Finnhub",
            )
            for item in data
        ],
    }

    search_normalizers: dict[str, Any] = {}

    return MarketDataService(
        uow=fake_uow,
        encryption=fake_encryption,
        http_client=fake_http,
        rate_limiters={"Alpha Vantage": fake_limiter, "Finnhub": fake_limiter},
        provider_registry=registry,
        quote_normalizers=quote_normalizers,
        news_normalizers=news_normalizers,
        search_normalizers=search_normalizers,
    )


def _make_setting(
    name: str,
    *,
    enabled: bool = True,
    api_key: str = "ENC:test-key",
) -> MagicMock:
    """Create a fake MarketProviderSettings."""
    setting = MagicMock()
    setting.provider_name = name
    setting.is_enabled = enabled
    setting.encrypted_api_key = api_key
    setting.encrypted_api_secret = None
    setting.rate_limit = 60
    setting.timeout = 30
    return setting


# ── get_quote tests ─────────────────────────────────────────────────────


class TestGetQuote:
    """Tests for MarketDataService.get_quote."""

    def test_returns_quote_from_first_enabled_provider(self) -> None:
        """AC-1: Returns MarketQuote from the first enabled provider with key."""
        settings = [_make_setting("Alpha Vantage")]
        response = FakeHttpResponse(
            200,
            {"Global Quote": {"01. symbol": "AAPL", "05. price": "181.18"}},
        )
        svc = _make_service(settings=settings, http_responses=[response])

        result = asyncio.run(svc.get_quote("AAPL"))

        assert isinstance(result, MarketQuote)
        assert result.ticker == "AAPL"
        assert result.price == pytest.approx(181.18)

    def test_fallback_to_next_provider_on_error(self) -> None:
        """AC-2: Falls through to next provider on HTTP error."""
        settings = [
            _make_setting("Alpha Vantage"),
            _make_setting("Finnhub"),
        ]
        error_response = FakeHttpResponse(500, {})
        success_response = FakeHttpResponse(
            200, {"c": 181.18, "o": 178.55, "h": 182.01, "l": 177.99}
        )
        svc = _make_service(
            settings=settings,
            http_responses=[error_response, success_response],
        )

        result = asyncio.run(svc.get_quote("AAPL"))

        assert isinstance(result, MarketQuote)
        assert result.price == pytest.approx(181.18)
        assert result.provider == "Finnhub"

    def test_raises_market_data_error_when_all_providers_fail(self) -> None:
        """AC-3: Raises MarketDataError when all providers fail."""
        settings = [
            _make_setting("Alpha Vantage"),
            _make_setting("Finnhub"),
        ]
        svc = _make_service(
            settings=settings,
            http_side_effect=ConnectionError("Connection refused"),
        )

        with pytest.raises(MarketDataError, match="All providers failed"):
            asyncio.run(svc.get_quote("AAPL"))

    def test_skips_disabled_providers(self) -> None:
        """Only enabled providers with keys are tried."""
        settings = [
            _make_setting("Alpha Vantage", enabled=False),
            _make_setting("Finnhub"),
        ]
        response = FakeHttpResponse(
            200, {"c": 181.18, "o": 178.55, "h": 182.01, "l": 177.99}
        )
        svc = _make_service(settings=settings, http_responses=[response])

        result = asyncio.run(svc.get_quote("AAPL"))

        assert result.provider == "Finnhub"

    def test_skips_providers_without_api_key(self) -> None:
        """Providers without API keys are skipped."""
        settings = [
            _make_setting("Alpha Vantage", api_key=""),
            _make_setting("Finnhub"),
        ]
        response = FakeHttpResponse(
            200, {"c": 181.18, "o": 178.55, "h": 182.01, "l": 177.99}
        )
        svc = _make_service(settings=settings, http_responses=[response])

        result = asyncio.run(svc.get_quote("AAPL"))

        assert result.provider == "Finnhub"


# ── get_news tests ──────────────────────────────────────────────────────


class TestGetNews:
    """Tests for MarketDataService.get_news."""

    def test_returns_news_from_enabled_provider(self) -> None:
        """AC-4: Returns list[MarketNewsItem] from news-capable provider."""
        settings = [_make_setting("Finnhub")]
        response = FakeHttpResponse(
            200,
            [
                {"headline": "Apple Earns Record", "source": "Reuters"},
                {"headline": "Tech Rallies", "source": "Bloomberg"},
            ],
        )
        svc = _make_service(settings=settings, http_responses=[response])

        results = asyncio.run(svc.get_news(None, 5))

        assert len(results) == 2
        assert all(isinstance(r, MarketNewsItem) for r in results)
        assert results[0].title == "Apple Earns Record"

    def test_raises_when_no_news_providers_available(self) -> None:
        """Raises MarketDataError if no news-capable providers enabled."""
        svc = _make_service(settings=[])

        with pytest.raises(MarketDataError, match="No.*provider"):
            asyncio.run(svc.get_news(None, 5))


# ── get_sec_filings tests ──────────────────────────────────────────────


class TestGetSecFilings:
    """Tests for MarketDataService.get_sec_filings."""

    def test_raises_when_sec_not_configured(self) -> None:
        """Raises MarketDataError when SEC API has no key."""
        svc = _make_service(settings=[])

        with pytest.raises(MarketDataError, match="SEC"):
            asyncio.run(svc.get_sec_filings("AAPL"))


# ── Rate limiter tests ──────────────────────────────────────────────────


class TestRateLimiting:
    """AC-8: Rate limiter integration."""

    def test_rate_limiter_called_before_http_request(self) -> None:
        """Rate limiter wait_if_needed() is called before every HTTP request."""
        settings = [_make_setting("Alpha Vantage")]
        response = FakeHttpResponse(
            200,
            {"Global Quote": {"01. symbol": "AAPL", "05. price": "181.18"}},
        )
        svc = _make_service(settings=settings, http_responses=[response])

        asyncio.run(svc.get_quote("AAPL"))

        # Access the rate limiter through the service's internal state
        for limiter in svc._rate_limiters.values():
            if hasattr(limiter.wait_if_needed, "assert_called"):
                limiter.wait_if_needed.assert_called()
