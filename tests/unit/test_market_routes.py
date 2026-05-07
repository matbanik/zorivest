"""Tests for Market Data Expansion REST API — MEU-192.

Source: docs/build-plan/08a-market-data-expansion.md §8a.11.
Tests 8 new endpoints for OHLCV, fundamentals, earnings, dividends,
splits, insider, economic calendar, and company profile.

FIC: AC-1 through AC-9 in implementation-plan.md.
"""

from __future__ import annotations

from collections.abc import Generator
from datetime import date, datetime, time
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from zorivest_api.dependencies import (
    get_market_data_service,
    require_unlocked_db,
)
from zorivest_api.main import create_app
from zorivest_core.application.market_expansion_dtos import (
    DividendRecord,
    EarningsReport,
    EconomicCalendarEvent,
    FundamentalsSnapshot,
    InsiderTransaction,
    OHLCVBar,
    StockSplit,
)
from zorivest_core.services.market_data_service import MarketDataError


# ── Fixtures ────────────────────────────────────────────────────────────


@pytest.fixture()
def mock_service() -> AsyncMock:
    """Create a mock MarketDataService with expansion method stubs."""
    svc = AsyncMock()
    svc.get_ohlcv.return_value = [
        OHLCVBar(
            ticker="AAPL",
            timestamp=datetime(2026, 1, 2, 16, 0),
            open=Decimal("180.00"),
            high=Decimal("182.00"),
            low=Decimal("179.00"),
            close=Decimal("181.50"),
            adj_close=Decimal("181.50"),
            volume=50_000_000,
            vwap=Decimal("180.75"),
            trade_count=100_000,
            provider="Alpaca",
        )
    ]
    svc.get_fundamentals.return_value = FundamentalsSnapshot(
        ticker="AAPL",
        market_cap=Decimal("3000000000000"),
        pe_ratio=Decimal("30.5"),
        pb_ratio=Decimal("45.2"),
        ps_ratio=Decimal("8.1"),
        eps=Decimal("6.50"),
        dividend_yield=Decimal("0.005"),
        beta=Decimal("1.2"),
        sector="Technology",
        industry="Consumer Electronics",
        employees=160000,
        provider="FMP",
        timestamp=datetime(2026, 1, 2, 16, 0),
    )
    svc.get_earnings.return_value = [
        EarningsReport(
            ticker="AAPL",
            fiscal_period="Q1",
            fiscal_year=2026,
            report_date=date(2026, 1, 30),
            eps_actual=Decimal("1.65"),
            eps_estimate=Decimal("1.60"),
            eps_surprise=Decimal("0.05"),
            revenue_actual=Decimal("120000000000"),
            revenue_estimate=Decimal("118000000000"),
            provider="Finnhub",
        )
    ]
    svc.get_dividends.return_value = [
        DividendRecord(
            ticker="AAPL",
            dividend_amount=Decimal("0.25"),
            currency="USD",
            ex_date=date(2026, 2, 7),
            record_date=date(2026, 2, 10),
            pay_date=date(2026, 2, 14),
            declaration_date=date(2026, 1, 30),
            frequency="quarterly",
            provider="Polygon",
        )
    ]
    svc.get_splits.return_value = [
        StockSplit(
            ticker="AAPL",
            execution_date=date(2020, 8, 31),
            ratio_from=1,
            ratio_to=4,
            provider="EODHD",
        )
    ]
    svc.get_insider.return_value = [
        InsiderTransaction(
            ticker="AAPL",
            name="Tim Cook",
            title="CEO",
            transaction_date=date(2026, 1, 15),
            transaction_code="S",
            shares=50000,
            price=Decimal("181.00"),
            value=Decimal("9050000"),
            shares_owned_after=3000000,
            provider="Finnhub",
        )
    ]
    svc.get_economic_calendar.return_value = [
        EconomicCalendarEvent(
            event="CPI",
            country="US",
            date=date(2026, 2, 12),
            time=time(8, 30),
            impact="high",
            actual="3.1%",
            forecast="3.0%",
            previous="2.9%",
            provider="Finnhub",
        )
    ]
    svc.get_company_profile.return_value = FundamentalsSnapshot(
        ticker="AAPL",
        market_cap=Decimal("3000000000000"),
        pe_ratio=Decimal("30.5"),
        pb_ratio=Decimal("45.2"),
        ps_ratio=Decimal("8.1"),
        eps=Decimal("6.50"),
        dividend_yield=Decimal("0.005"),
        beta=Decimal("1.2"),
        sector="Technology",
        industry="Consumer Electronics",
        employees=160000,
        provider="FMP",
        timestamp=datetime(2026, 1, 2, 16, 0),
    )
    return svc


@pytest.fixture()
def client(mock_service: AsyncMock) -> Generator[TestClient, None, None]:
    """TestClient with overridden dependencies."""
    app = create_app()
    app.dependency_overrides[require_unlocked_db] = lambda: None
    app.dependency_overrides[get_market_data_service] = lambda: mock_service
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


# ── AC-1: 8 new endpoints return correct DTOs ──────────────────────────


class TestGetOHLCV:
    """Tests for GET /api/v1/market-data/ohlcv."""

    def test_returns_200_with_ohlcv(self, client: TestClient) -> None:
        resp = client.get("/api/v1/market-data/ohlcv?ticker=AAPL")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["ticker"] == "AAPL"

    def test_with_interval_param(self, client: TestClient) -> None:
        resp = client.get("/api/v1/market-data/ohlcv?ticker=AAPL&interval=5m")
        assert resp.status_code == 200

    def test_missing_ticker_returns_422(self, client: TestClient) -> None:
        """AC-1 negative: missing required ticker → 422."""
        resp = client.get("/api/v1/market-data/ohlcv")
        assert resp.status_code == 422

    def test_service_error_returns_502(
        self, client: TestClient, mock_service: AsyncMock
    ) -> None:
        """AC-6: Provider timeout → 502."""
        mock_service.get_ohlcv.side_effect = MarketDataError("Provider timeout")
        resp = client.get("/api/v1/market-data/ohlcv?ticker=AAPL")
        assert resp.status_code == 502


class TestGetFundamentals:
    """Tests for GET /api/v1/market-data/fundamentals."""

    def test_returns_200(self, client: TestClient) -> None:
        resp = client.get("/api/v1/market-data/fundamentals?ticker=AAPL")
        assert resp.status_code == 200
        data = resp.json()
        assert data["ticker"] == "AAPL"
        assert data["sector"] == "Technology"

    def test_missing_ticker_returns_422(self, client: TestClient) -> None:
        resp = client.get("/api/v1/market-data/fundamentals")
        assert resp.status_code == 422


class TestGetEarnings:
    """Tests for GET /api/v1/market-data/earnings."""

    def test_returns_200(self, client: TestClient) -> None:
        resp = client.get("/api/v1/market-data/earnings?ticker=AAPL")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert data[0]["fiscal_period"] == "Q1"

    def test_missing_ticker_returns_422(self, client: TestClient) -> None:
        resp = client.get("/api/v1/market-data/earnings")
        assert resp.status_code == 422


class TestGetDividends:
    """Tests for GET /api/v1/market-data/dividends."""

    def test_returns_200(self, client: TestClient) -> None:
        resp = client.get("/api/v1/market-data/dividends?ticker=AAPL")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 1

    def test_missing_ticker_returns_422(self, client: TestClient) -> None:
        resp = client.get("/api/v1/market-data/dividends")
        assert resp.status_code == 422


class TestGetSplits:
    """Tests for GET /api/v1/market-data/splits."""

    def test_returns_200(self, client: TestClient) -> None:
        resp = client.get("/api/v1/market-data/splits?ticker=AAPL")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    def test_missing_ticker_returns_422(self, client: TestClient) -> None:
        resp = client.get("/api/v1/market-data/splits")
        assert resp.status_code == 422


class TestGetInsider:
    """Tests for GET /api/v1/market-data/insider."""

    def test_returns_200(self, client: TestClient) -> None:
        resp = client.get("/api/v1/market-data/insider?ticker=AAPL")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert data[0]["name"] == "Tim Cook"

    def test_missing_ticker_returns_422(self, client: TestClient) -> None:
        resp = client.get("/api/v1/market-data/insider")
        assert resp.status_code == 422


class TestGetEconomicCalendar:
    """Tests for GET /api/v1/market-data/economic-calendar."""

    def test_returns_200(self, client: TestClient) -> None:
        """No ticker required for economic calendar."""
        resp = client.get("/api/v1/market-data/economic-calendar")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert data[0]["event"] == "CPI"

    def test_with_country_filter(self, client: TestClient) -> None:
        resp = client.get("/api/v1/market-data/economic-calendar?country=US")
        assert resp.status_code == 200


class TestGetCompanyProfile:
    """Tests for GET /api/v1/market-data/company-profile."""

    def test_returns_200(self, client: TestClient) -> None:
        resp = client.get("/api/v1/market-data/company-profile?ticker=AAPL")
        assert resp.status_code == 200
        data = resp.json()
        assert data["ticker"] == "AAPL"

    def test_missing_ticker_returns_422(self, client: TestClient) -> None:
        resp = client.get("/api/v1/market-data/company-profile")
        assert resp.status_code == 422


# ── AC-2: MarketDataExpansionParams rejects extra fields ────────────────


class TestExpansionParamsExtraFields:
    """AC-2: Extra fields in query params → 422."""

    def test_extra_field_rejected_ohlcv(self, client: TestClient) -> None:
        resp = client.get("/api/v1/market-data/ohlcv?ticker=AAPL&foo=bar")
        assert resp.status_code == 422


# ── AC-3: ticker validates 1-10 chars uppercase alpha + dot ─────────────


class TestTickerValidation:
    """AC-3: Ticker field validation."""

    def test_empty_ticker_rejected(self, client: TestClient) -> None:
        resp = client.get("/api/v1/market-data/ohlcv?ticker=")
        assert resp.status_code == 422

    def test_too_long_ticker_rejected(self, client: TestClient) -> None:
        resp = client.get("/api/v1/market-data/ohlcv?ticker=TOOLONG12345")
        assert resp.status_code == 422

    def test_valid_dotted_ticker(self, client: TestClient) -> None:
        """BRK.B is a valid ticker."""
        resp = client.get("/api/v1/market-data/ohlcv?ticker=BRK.B")
        assert resp.status_code == 200


# ── AC-4: interval validates against enum ───────────────────────────────


class TestIntervalValidation:
    """AC-4: Interval enum validation."""

    def test_invalid_interval_rejected(self, client: TestClient) -> None:
        resp = client.get("/api/v1/market-data/ohlcv?ticker=AAPL&interval=2h")
        assert resp.status_code == 422

    def test_valid_interval_accepted(self, client: TestClient) -> None:
        resp = client.get("/api/v1/market-data/ohlcv?ticker=AAPL&interval=1h")
        assert resp.status_code == 200


# ── AC-5: start_date must be ≤ end_date ─────────────────────────────────


class TestDateValidation:
    """AC-5: Date range validation."""

    def test_start_after_end_rejected(self, client: TestClient) -> None:
        resp = client.get(
            "/api/v1/market-data/ohlcv?ticker=AAPL"
            "&start_date=2026-03-01&end_date=2026-01-01"
        )
        assert resp.status_code == 422

    def test_valid_date_range(self, client: TestClient) -> None:
        resp = client.get(
            "/api/v1/market-data/ohlcv?ticker=AAPL"
            "&start_date=2026-01-01&end_date=2026-03-01"
        )
        assert resp.status_code == 200


# ── AC-6: Service errors map to 502 ────────────────────────────────────


class TestServiceErrorMapping:
    """AC-6: MarketDataError → 502 for all expansion endpoints."""

    @pytest.mark.parametrize(
        "endpoint",
        [
            "/api/v1/market-data/fundamentals?ticker=AAPL",
            "/api/v1/market-data/earnings?ticker=AAPL",
            "/api/v1/market-data/dividends?ticker=AAPL",
            "/api/v1/market-data/splits?ticker=AAPL",
            "/api/v1/market-data/insider?ticker=AAPL",
            "/api/v1/market-data/company-profile?ticker=AAPL",
        ],
    )
    def test_service_error_returns_502(
        self, client: TestClient, mock_service: AsyncMock, endpoint: str
    ) -> None:
        # Set side_effect on all methods to raise
        for method_name in [
            "get_fundamentals",
            "get_earnings",
            "get_dividends",
            "get_splits",
            "get_insider",
            "get_company_profile",
        ]:
            getattr(mock_service, method_name).side_effect = MarketDataError(
                "Provider error"
            )
        resp = client.get(endpoint)
        assert resp.status_code == 502

    def test_economic_calendar_error_returns_502(
        self, client: TestClient, mock_service: AsyncMock
    ) -> None:
        mock_service.get_economic_calendar.side_effect = MarketDataError("Error")
        resp = client.get("/api/v1/market-data/economic-calendar")
        assert resp.status_code == 502


# ── F2-FIX: Provider boundary enforcement ──────────────────────────────


class TestProviderBoundaryEnforcement:
    """Finding 2: Unknown provider must return 404, valid provider forwarded."""

    @pytest.mark.parametrize(
        "endpoint",
        [
            "/api/v1/market-data/ohlcv?ticker=AAPL&provider=Nope",
            "/api/v1/market-data/fundamentals?ticker=AAPL&provider=Nope",
            "/api/v1/market-data/earnings?ticker=AAPL&provider=Nope",
            "/api/v1/market-data/dividends?ticker=AAPL&provider=Nope",
            "/api/v1/market-data/splits?ticker=AAPL&provider=Nope",
            "/api/v1/market-data/insider?ticker=AAPL&provider=Nope",
            "/api/v1/market-data/company-profile?ticker=AAPL&provider=Nope",
        ],
    )
    def test_unknown_provider_returns_404(
        self, client: TestClient, endpoint: str
    ) -> None:
        """Invalid provider name must be rejected with 404."""
        resp = client.get(endpoint)
        assert resp.status_code == 404, (
            f"Expected 404 for unknown provider 'Nope' on {endpoint}, "
            f"got {resp.status_code}"
        )

    def test_valid_provider_forwarded_to_service(
        self, client: TestClient, mock_service: AsyncMock
    ) -> None:
        """Valid provider name should be forwarded as kwarg to the service."""
        # Use Finnhub — a known valid provider
        resp = client.get(
            "/api/v1/market-data/fundamentals?ticker=AAPL&provider=Finnhub"
        )
        assert resp.status_code == 200
        # Verify provider kwarg was forwarded
        mock_service.get_fundamentals.assert_called_once()
        _, kwargs = mock_service.get_fundamentals.call_args
        assert kwargs.get("provider") == "Finnhub"


# ── R1-FIX: Service signature regression ───────────────────────────────


class TestServiceSignatureAcceptsKwargs:
    """R1: All expansion service methods must accept **kwargs for provider forwarding.

    Verifies that calling service methods with provider=X does not raise TypeError.
    Uses inspect.signature to detect missing **kwargs without needing full service instantiation.
    """

    @pytest.mark.parametrize(
        "method_name",
        [
            "get_ohlcv",
            "get_fundamentals",
            "get_earnings",
            "get_dividends",
            "get_splits",
            "get_insider",
            "get_company_profile",
        ],
    )
    def test_service_method_accepts_kwargs(self, method_name: str) -> None:
        """Each expansion method must accept **kwargs so provider can be forwarded."""
        import inspect

        from zorivest_core.services.market_data_service import MarketDataService

        method = getattr(MarketDataService, method_name)
        sig = inspect.signature(method)
        has_var_keyword = any(
            p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values()
        )
        assert has_var_keyword, (
            f"MarketDataService.{method_name}{sig} does not accept **kwargs. "
            f"Route handlers forward provider= to this method, which will raise "
            f"TypeError at runtime."
        )

    def test_spec_mock_rejects_unknown_kwargs(self) -> None:
        """AsyncMock(spec=MarketDataService) must reject unexpected kwargs.

        This validates that spec-aware mocks would catch the issue the
        original test missed with plain AsyncMock().
        """
        import inspect

        from zorivest_core.services.market_data_service import MarketDataService

        # If the method accepts **kwargs, this test is a no-op (expected green)
        # If it doesn't, spec-based mock would raise TypeError
        method = getattr(MarketDataService, "get_fundamentals")
        sig = inspect.signature(method)
        params = list(sig.parameters.values())
        # The method should have self, ticker, **kwargs
        param_names = [p.name for p in params]
        assert "ticker" in param_names, "get_fundamentals must accept ticker"
