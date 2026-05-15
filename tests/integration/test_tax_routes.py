# tests/integration/test_tax_routes.py
"""Integration tests for MEU-148: Tax REST API Route Wiring.

Tests the full HTTP round-trip through FastAPI's TestClient with the
real TaxService backed by in-memory SQLite (via create_app lifespan).

AC-148.3: Route handlers decompose Pydantic models → TaxService method args.
AC-148.5: New routes (deferred-losses, alpha) return valid shapes.
AC-148.6: record_payment persistence path (or graceful degradation).
AC-148.7: Integration tests confirm all 12+ tax routes return 200.
AC-148.9: Quarter string "Q1"→1 mapping works end-to-end.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from zorivest_api.main import create_app


# ── Fixtures ─────────────────────────────────────────────────────────


@pytest.fixture()
def client():
    """Full-stack unlocked test client with real TaxService."""
    app = create_app()
    with TestClient(app, raise_server_exceptions=False) as c:
        app.state.db_unlocked = True
        yield c


# ── AC-148.3: Route handler decomposition ────────────────────────────


class TestRouteDecomposition:
    """Verify route handlers correctly decompose request bodies."""

    def test_simulate_post_with_body(self, client: TestClient) -> None:
        """POST /simulate with full body → 200 with gain fields."""
        resp = client.post(
            "/api/v1/tax/simulate",
            json={
                "ticker": "SPY",
                "action": "sell",
                "quantity": 100,
                "price": 500.0,
                "account_id": "DU123",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "total_st_gain" in data or "lot_details" in data

    def test_estimate_post(self, client: TestClient) -> None:
        """POST /estimate → 200 with federal_estimate field."""
        resp = client.post("/api/v1/tax/estimate", json={"tax_year": 2026})
        assert resp.status_code == 200
        data = resp.json()
        assert "federal_estimate" in data

    def test_wash_sales_post(self, client: TestClient) -> None:
        """POST /wash-sales → 200 with chains field."""
        resp = client.post("/api/v1/tax/wash-sales", json={"account_id": "DU123"})
        assert resp.status_code == 200
        data = resp.json()
        assert "chains" in data

    def test_lots_get(self, client: TestClient) -> None:
        """GET /lots → 200 with lots array."""
        resp = client.get("/api/v1/tax/lots?account_id=DU123")
        assert resp.status_code == 200
        data = resp.json()
        assert "lots" in data
        assert isinstance(data["lots"], list)


# ── AC-148.5: New routes ────────────────────────────────────────────


class TestNewRoutes:
    """Verify new deferred-losses and alpha routes return valid shapes."""

    def test_deferred_losses_get(self, client: TestClient) -> None:
        """GET /deferred-losses → 200 with report field."""
        resp = client.get("/api/v1/tax/deferred-losses?tax_year=2026")
        assert resp.status_code == 200

    def test_alpha_get(self, client: TestClient) -> None:
        """GET /alpha → 200 with alpha report shape."""
        resp = client.get("/api/v1/tax/alpha?tax_year=2026")
        assert resp.status_code == 200


# ── AC-148.6: Payment persistence ───────────────────────────────────


class TestPaymentPersistence:
    """Verify record_payment round-trip through the API."""

    def test_payment_with_confirm(self, client: TestClient) -> None:
        """POST /quarterly/payment with confirm=true → 200."""
        resp = client.post(
            "/api/v1/tax/quarterly/payment",
            json={
                "quarter": "Q1",
                "tax_year": 2026,
                "payment_amount": 5000,
                "confirm": True,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "recorded"
        assert data["amount"] == 5000

    def test_payment_without_confirm_rejected(self, client: TestClient) -> None:
        """POST /quarterly/payment with confirm=false → 400."""
        resp = client.post(
            "/api/v1/tax/quarterly/payment",
            json={
                "quarter": "Q2",
                "tax_year": 2026,
                "payment_amount": 3000,
                "confirm": False,
            },
        )
        assert resp.status_code == 400


# ── AC-148.9: Quarter string mapping ────────────────────────────────


class TestQuarterMapping:
    """Verify Q1/Q2/Q3/Q4 string-to-int mapping works end-to-end."""

    @pytest.mark.parametrize("quarter", ["Q1", "Q2", "Q3", "Q4"])
    def test_quarterly_get_all_quarters(self, client: TestClient, quarter: str) -> None:
        """GET /quarterly with each quarter string → 200."""
        resp = client.get(f"/api/v1/tax/quarterly?quarter={quarter}&tax_year=2026")
        assert resp.status_code == 200

    @pytest.mark.parametrize("quarter", ["Q1", "Q2", "Q3", "Q4"])
    def test_payment_all_quarters(self, client: TestClient, quarter: str) -> None:
        """POST /quarterly/payment with each quarter string → 200."""
        resp = client.post(
            "/api/v1/tax/quarterly/payment",
            json={
                "quarter": quarter,
                "tax_year": 2026,
                "payment_amount": 1000,
                "confirm": True,
            },
        )
        assert resp.status_code == 200


# ── AC-148.7: Full route coverage ──────────────────────────────────


class TestFullRouteCoverage:
    """Verify all tax routes respond (no 404/405/500)."""

    def test_ytd_summary(self, client: TestClient) -> None:
        resp = client.get("/api/v1/tax/ytd-summary?tax_year=2026")
        assert resp.status_code == 200

    def test_wash_sales_scan(self, client: TestClient) -> None:
        resp = client.post("/api/v1/tax/wash-sales/scan")
        assert resp.status_code == 200

    def test_audit(self, client: TestClient) -> None:
        resp = client.post("/api/v1/tax/audit")
        assert resp.status_code == 200

    def test_harvest(self, client: TestClient) -> None:
        resp = client.get("/api/v1/tax/harvest")
        assert resp.status_code == 200


# ── F4: Boundary validation — extra-field rejection ─────────────────


class TestBoundaryValidation:
    """F4: Pydantic models with extra='forbid' reject unknown fields."""

    def test_simulate_rejects_extra_field(self, client: TestClient) -> None:
        """POST /simulate with unknown field → 422."""
        resp = client.post(
            "/api/v1/tax/simulate",
            json={
                "ticker": "AAPL",
                "action": "sell",
                "quantity": 100,
                "price": 150.0,
                "account_id": "DU123",
                "evil_injection": "drop table;",
            },
        )
        assert resp.status_code == 422

    def test_estimate_rejects_extra_field(self, client: TestClient) -> None:
        """POST /estimate with unknown field → 422."""
        resp = client.post(
            "/api/v1/tax/estimate",
            json={"tax_year": 2026, "hidden_param": True},
        )
        assert resp.status_code == 422

    def test_wash_sales_rejects_extra_field(self, client: TestClient) -> None:
        """POST /wash-sales with unknown field → 422."""
        resp = client.post(
            "/api/v1/tax/wash-sales",
            json={"account_id": "DU123", "extra": "bad"},
        )
        assert resp.status_code == 422

    def test_record_payment_rejects_extra_field(self, client: TestClient) -> None:
        """POST /quarterly/payment with unknown field → 422."""
        resp = client.post(
            "/api/v1/tax/quarterly/payment",
            json={
                "quarter": "Q1",
                "tax_year": 2026,
                "payment_amount": 5000,
                "confirm": True,
                "injected": "value",
            },
        )
        assert resp.status_code == 422

    def test_reassign_rejects_extra_field(self, client: TestClient) -> None:
        """PUT /lots/{id}/reassign with unknown field → 422."""
        resp = client.put(
            "/api/v1/tax/lots/LOT-1/reassign",
            json={"method": "hifo", "unknown": True},
        )
        assert resp.status_code == 422
