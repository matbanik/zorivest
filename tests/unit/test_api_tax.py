# tests/unit/test_api_tax.py
"""Tests for MEU-29: Tax API routes.

Red phase — written FIRST per TDD protocol.
FIC Acceptance Criteria: AC-1..AC-6.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from zorivest_api.main import create_app


# ── Fixtures ─────────────────────────────────────────────────────────


@pytest.fixture()
def client():
    """Unlocked client."""
    app = create_app()
    with TestClient(app, raise_server_exceptions=False) as c:
        app.state.db_unlocked = True
        yield c


@pytest.fixture()
def locked_client():
    """Locked client."""
    app = create_app()
    with TestClient(app, raise_server_exceptions=False) as c:
        # Explicitly lock — lifespan may auto-unlock via ZORIVEST_DEV_UNLOCK env var
        app.state.db_unlocked = False
        yield c


# ── AC-1: Tax router tag ────────────────────────────────────────────


class TestTaxRouterTag:
    def test_tax_tag(self) -> None:
        """AC-1: Tax router has tag 'tax'."""
        from zorivest_api.routes.tax import tax_router

        assert "tax" in (tax_router.tags or [])


# ── AC-2: 12 tax endpoints exist ────────────────────────────────────


class TestTaxEndpoints:
    @pytest.mark.parametrize(
        "path,method,body",
        [
            (
                "/api/v1/tax/simulate",
                "POST",
                {
                    "ticker": "SPY",
                    "action": "sell",
                    "quantity": 100,
                    "price": 500.0,
                    "account_id": "DU123",
                },
            ),
            ("/api/v1/tax/estimate", "POST", {"tax_year": 2026}),
            ("/api/v1/tax/wash-sales", "POST", {"account_id": "DU123"}),
            ("/api/v1/tax/lots?account_id=DU123", "GET", None),
            ("/api/v1/tax/quarterly?quarter=Q1&tax_year=2026", "GET", None),
            (
                "/api/v1/tax/quarterly/payment",
                "POST",
                {
                    "quarter": "Q1",
                    "tax_year": 2026,
                    "payment_amount": 5000,
                    "confirm": True,
                },
            ),
            ("/api/v1/tax/harvest", "GET", None),
            ("/api/v1/tax/ytd-summary?tax_year=2026", "GET", None),
            ("/api/v1/tax/wash-sales/scan", "POST", None),
            ("/api/v1/tax/audit", "POST", None),
        ],
    )
    def test_endpoint_returns_200(
        self, client: TestClient, path: str, method: str, body
    ) -> None:
        """AC-2: Each tax endpoint returns 200 (not 404/405/500)."""
        if method == "GET":
            resp = client.get(path)
        elif method == "PUT":
            resp = client.put(path, json=body or {})
        else:
            resp = client.post(path, json=body or {})
        assert resp.status_code == 200, f"{method} {path} returned {resp.status_code}"
        # Value: verify response is valid JSON
        data = resp.json()
        assert isinstance(data, (dict, list))

    @pytest.mark.parametrize(
        "path,method,body,expected_status",
        [
            # These endpoints correctly return 400/404 for nonexistent lots
            # with real TaxService (was 200 with stubs)
            ("/api/v1/tax/lots/lot1/close", "POST", None, 404),
            ("/api/v1/tax/lots/lot1/reassign", "PUT", {"method": "lifo"}, 404),
        ],
    )
    def test_lot_endpoints_handle_missing(
        self, client: TestClient, path: str, method: str, body, expected_status: int
    ) -> None:
        """AC-2: Lot endpoints return proper error for nonexistent lots (MEU-148)."""
        if method == "PUT":
            resp = client.put(path, json=body or {})
        else:
            resp = client.post(path, json=body or {})
        assert resp.status_code == expected_status, (
            f"{method} {path} returned {resp.status_code}, expected {expected_status}"
        )


# ── AC-3: Quarterly payment requires confirm=true ────────────────────


class TestQuarterlyPayment:
    def test_confirm_false_returns_400(self, client: TestClient) -> None:
        """AC-3: POST /tax/quarterly/payment with confirm=false → 400."""
        resp = client.post(
            "/api/v1/tax/quarterly/payment",
            json={
                "quarter": "Q1",
                "tax_year": 2026,
                "payment_amount": 5000,
                "confirm": False,
            },
        )
        assert resp.status_code == 400
        # Value: verify error detail in response
        data = resp.json()
        assert "detail" in data

    def test_confirm_true_returns_200(self, client: TestClient) -> None:
        """AC-3: POST /tax/quarterly/payment with confirm=true → 200."""
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
        # Value: verify response body has payment data
        data = resp.json()
        assert isinstance(data, dict)


# ── AC-4: All tax routes require unlocked DB ─────────────────────────


class TestTaxModeGating:
    def test_simulate_locked_403(self, locked_client: TestClient) -> None:
        """AC-4: Tax routes return 403 when locked."""
        resp = locked_client.post(
            "/api/v1/tax/simulate",
            json={
                "ticker": "SPY",
                "action": "sell",
                "quantity": 100,
                "price": 500.0,
                "account_id": "DU123",
            },
        )
        assert resp.status_code == 403
        # Value: verify error detail
        data = resp.json()
        assert "detail" in data

    def test_lots_locked_403(self, locked_client: TestClient) -> None:
        """AC-4: Tax GET routes return 403 when locked."""
        resp = locked_client.get("/api/v1/tax/lots?account_id=DU123")
        assert resp.status_code == 403
        data = resp.json()
        assert "detail" in data


# ── AC-5: Real service returns shaped responses (MEU-148) ─────────────


class TestRealServiceShapes:
    def test_simulate_shape(self, client: TestClient) -> None:
        """AC-5: Simulate returns estimated_tax and lot_details."""
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
        data = resp.json()
        assert "estimated_tax" in data
        assert "lot_details" in data
        # Value: verify types
        assert isinstance(data["estimated_tax"], (int, float))
        assert isinstance(data["lot_details"], list)

    def test_quarterly_shape(self, client: TestClient) -> None:
        """AC-5: Quarterly returns required/paid/due."""
        data = client.get("/api/v1/tax/quarterly?quarter=Q1&tax_year=2026").json()
        assert "required" in data
        assert "due" in data
        # Value: verify types
        assert isinstance(data["required"], (int, float))
        assert isinstance(data["due"], (int, float))

    def test_harvest_shape(self, client: TestClient) -> None:
        """AC-5: Harvest returns opportunities (empty on clean DB)."""
        data = client.get("/api/v1/tax/harvest").json()
        assert "opportunities" in data or "candidates" in data
        # Value: verify list type regardless of key name
        harvestable = data.get("opportunities", data.get("candidates", []))
        assert isinstance(harvestable, list)


# ── AC-6: Integration test ───────────────────────────────────────────


class TestTaxIntegration:
    def test_no_overrides_non_500(self) -> None:
        """AC-6: create_app() + unlock → tax routes return non-500."""
        app = create_app()
        with TestClient(app, raise_server_exceptions=False) as client:
            app.state.db_unlocked = True
            resp = client.get("/api/v1/tax/lots?account_id=DU123")
            assert resp.status_code == 200
            # Value: verify valid JSON response
            data = resp.json()
            assert isinstance(data, dict)

    def test_ytd_summary_works(self) -> None:
        """AC-6: YTD summary returns shaped response."""
        app = create_app()
        with TestClient(app, raise_server_exceptions=False) as client:
            app.state.db_unlocked = True
            resp = client.get("/api/v1/tax/ytd-summary?tax_year=2026")
            assert resp.status_code == 200
            data = resp.json()
            # Real service returns estimated_federal_tax or fallback
            assert "estimated_federal_tax" in data or "estimated_tax" in data
