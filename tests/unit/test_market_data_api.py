"""Tests for Market Data REST API — MEU-63.

Source: docs/build-plan/08-market-data.md §8.4.
Tests 8 endpoints using TestClient with dependency overrides.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from zorivest_api.dependencies import (
    get_market_data_service,
    get_provider_connection_service,
    require_unlocked_db,
)
from zorivest_api.main import create_app
from zorivest_core.application.market_dtos import (
    MarketNewsItem,
    MarketQuote,
    SecFiling,
    TickerSearchResult,
)
from zorivest_core.services.market_data_service import MarketDataError


# ── Fixtures ────────────────────────────────────────────────────────────


@pytest.fixture()
def mock_market_data_service() -> AsyncMock:
    """Create a mock MarketDataService."""
    svc = AsyncMock()
    svc.get_quote.return_value = MarketQuote(
        ticker="AAPL", price=181.18, provider="Alpha Vantage"
    )
    svc.get_news.return_value = [
        MarketNewsItem(
            title="Test News", source="Reuters", provider="Finnhub"
        )
    ]
    svc.search_ticker.return_value = [
        TickerSearchResult(
            symbol="AAPL",
            name="Apple Inc.",
            provider="Financial Modeling Prep",
        )
    ]
    svc.get_sec_filings.return_value = [
        SecFiling(
            ticker="AAPL",
            company_name="Apple Inc.",
            cik="0000320193",
            provider="SEC API",
        )
    ]
    return svc


@pytest.fixture()
def mock_provider_service() -> AsyncMock:
    """Create a mock ProviderConnectionService."""
    svc = AsyncMock()
    svc.list_providers.return_value = []
    svc.configure_provider.return_value = None
    svc.test_connection.return_value = (True, "Connection successful")
    svc.remove_api_key.return_value = None
    return svc


@pytest.fixture()
def client(
    mock_market_data_service: AsyncMock,
    mock_provider_service: AsyncMock,
) -> TestClient:
    """Create a TestClient with overridden dependencies."""
    app = create_app()
    app.dependency_overrides[require_unlocked_db] = lambda: None
    app.dependency_overrides[get_market_data_service] = lambda: mock_market_data_service
    app.dependency_overrides[get_provider_connection_service] = lambda: mock_provider_service
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


@pytest.fixture()
def locked_client() -> TestClient:
    """Create a TestClient WITHOUT unlocked DB override."""
    app = create_app()
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


# ── Quote endpoint ──────────────────────────────────────────────────────


class TestGetQuote:
    """Tests for GET /api/v1/market-data/quote."""

    def test_returns_200_with_quote(self, client: TestClient) -> None:
        resp = client.get("/api/v1/market-data/quote?ticker=AAPL")
        assert resp.status_code == 200
        data = resp.json()
        assert data["ticker"] == "AAPL"
        assert data["price"] == pytest.approx(181.18)

    def test_missing_ticker_returns_422(self, client: TestClient) -> None:
        resp = client.get("/api/v1/market-data/quote")
        assert resp.status_code == 422

    def test_locked_db_returns_403(self, locked_client: TestClient) -> None:
        resp = locked_client.get("/api/v1/market-data/quote?ticker=AAPL")
        assert resp.status_code == 403

    def test_service_error_returns_503(
        self, client: TestClient, mock_market_data_service: AsyncMock
    ) -> None:
        mock_market_data_service.get_quote.side_effect = MarketDataError("All providers failed")
        resp = client.get("/api/v1/market-data/quote?ticker=AAPL")
        assert resp.status_code == 503


# ── News endpoint ───────────────────────────────────────────────────────


class TestGetNews:
    """Tests for GET /api/v1/market-data/news."""

    def test_returns_200_with_news(self, client: TestClient) -> None:
        resp = client.get("/api/v1/market-data/news")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["title"] == "Test News"

    def test_with_ticker_filter(self, client: TestClient) -> None:
        resp = client.get("/api/v1/market-data/news?ticker=AAPL&count=10")
        assert resp.status_code == 200


# ── Search endpoint ─────────────────────────────────────────────────────


class TestSearchTicker:
    """Tests for GET /api/v1/market-data/search."""

    def test_returns_200_with_results(self, client: TestClient) -> None:
        resp = client.get("/api/v1/market-data/search?query=apple")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["symbol"] == "AAPL"

    def test_missing_query_returns_422(self, client: TestClient) -> None:
        resp = client.get("/api/v1/market-data/search")
        assert resp.status_code == 422


# ── SEC filings endpoint ───────────────────────────────────────────────


class TestGetSecFilings:
    """Tests for GET /api/v1/market-data/sec-filings."""

    def test_returns_200_with_filings(self, client: TestClient) -> None:
        resp = client.get("/api/v1/market-data/sec-filings?ticker=AAPL")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["ticker"] == "AAPL"


# ── Provider management endpoints ──────────────────────────────────────


class TestListProviders:
    """Tests for GET /api/v1/market-data/providers."""

    def test_returns_200(self, client: TestClient) -> None:
        resp = client.get("/api/v1/market-data/providers")
        assert resp.status_code == 200


class TestConfigureProvider:
    """Tests for PUT /api/v1/market-data/providers/{name}."""

    def test_returns_configured(self, client: TestClient) -> None:
        resp = client.put(
            "/api/v1/market-data/providers/Alpha%20Vantage",
            json={"api_key": "test-key", "is_enabled": True},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "configured"
        assert resp.json()["stub"] is True

    def test_unknown_provider_returns_404(
        self, client: TestClient, mock_provider_service: AsyncMock
    ) -> None:
        mock_provider_service.configure_provider.side_effect = KeyError("Unknown")
        resp = client.put(
            "/api/v1/market-data/providers/Unknown",
            json={"api_key": "test"},
        )
        assert resp.status_code == 404


class TestTestProvider:
    """Tests for POST /api/v1/market-data/providers/{name}/test."""

    def test_returns_success(self, client: TestClient) -> None:
        resp = client.post("/api/v1/market-data/providers/Alpha%20Vantage/test")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["message"] == "Connection successful"
        assert data["stub"] is True


class TestRemoveProviderKey:
    """Tests for DELETE /api/v1/market-data/providers/{name}/key."""

    def test_returns_removed(self, client: TestClient) -> None:
        resp = client.delete("/api/v1/market-data/providers/Alpha%20Vantage/key")
        assert resp.status_code == 200
        assert resp.json()["status"] == "removed"
        assert resp.json()["stub"] is True
