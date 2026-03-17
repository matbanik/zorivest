# tests/unit/test_api_analytics.py
"""Tests for MEU-28: Analytics, Mistakes, Fees, Calculator API routes.

Red phase — written FIRST per TDD protocol.
FIC Acceptance Criteria: AC-1..AC-10.
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
    """Locked client (no unlock)."""
    app = create_app()
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


# ── AC-1: Analytics router tag ───────────────────────────────────────


class TestAnalyticsRouterTag:
    def test_analytics_tag(self) -> None:
        """AC-1: Analytics router has tag 'analytics'."""
        from zorivest_api.routes.analytics import analytics_router
        assert "analytics" in (analytics_router.tags or [])


# ── AC-2: 10 analytics endpoints exist ───────────────────────────────


class TestAnalyticsEndpoints:
    @pytest.mark.parametrize("path,method", [
        ("/api/v1/analytics/expectancy", "GET"),
        ("/api/v1/analytics/drawdown", "GET"),
        ("/api/v1/analytics/execution-quality", "GET"),
        ("/api/v1/analytics/pfof-report?account_id=DU123", "GET"),
        ("/api/v1/analytics/strategy-breakdown", "GET"),
        ("/api/v1/analytics/sqn", "GET"),
        ("/api/v1/analytics/cost-of-free", "GET"),
        ("/api/v1/analytics/ai-review", "POST"),
        ("/api/v1/analytics/excursion/test123", "POST"),
        ("/api/v1/analytics/options-strategy", "POST"),
    ])
    def test_endpoint_returns_200(self, client: TestClient, path: str, method: str) -> None:
        """AC-2: Each analytics endpoint returns 200 (not 404/405)."""
        if method == "GET":
            resp = client.get(path)
        else:
            resp = client.post(path, json={})
        assert resp.status_code == 200, f"{method} {path} returned {resp.status_code}"
        # Value: verify response is valid JSON
        data = resp.json()
        assert isinstance(data, (dict, list))


# ── AC-3: Mistakes routes ───────────────────────────────────────────


class TestMistakesRoutes:
    def test_track_mistake_201(self, client: TestClient) -> None:
        """AC-3: POST /mistakes/ returns 201."""
        resp = client.post("/api/v1/mistakes", json={"trade_id": "t1", "category": "fomo"})
        assert resp.status_code == 201
        # Value: verify response body is valid JSON
        data = resp.json()
        assert isinstance(data, dict)

    def test_mistake_summary_200(self, client: TestClient) -> None:
        """AC-3: GET /mistakes/summary returns 200."""
        resp = client.get("/api/v1/mistakes/summary")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_cost" in data


# ── AC-4: Fees route ────────────────────────────────────────────────


class TestFeesRoute:
    def test_fee_summary_200(self, client: TestClient) -> None:
        """AC-4: GET /fees/summary returns 200."""
        resp = client.get("/api/v1/fees/summary")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_fees" in data


# ── AC-5: Calculator route ──────────────────────────────────────────


class TestCalculatorRoute:
    def test_position_size_200(self, client: TestClient) -> None:
        """AC-5: POST /calculator/position-size returns 200 with result."""
        resp = client.post("/api/v1/calculator/position-size", json={
            "balance": 100000,
            "risk_pct": 1.0,
            "entry_price": 50.0,
            "stop_loss": 48.0,
            "target_price": 55.0,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["shares"] > 0
        assert data["reward_risk_ratio"] > 0


# ── AC-6: Calculator uses domain PositionSizeCalculator ──────────────


class TestCalculatorDomain:
    def test_calculator_uses_real_domain(self, client: TestClient) -> None:
        """AC-6: Calculator result matches domain calculator output."""
        from zorivest_core.domain.calculator import calculate_position_size
        expected = calculate_position_size(100000, 1.0, 50.0, 48.0, 55.0)
        resp = client.post("/api/v1/calculator/position-size", json={
            "balance": 100000,
            "risk_pct": 1.0,
            "entry_price": 50.0,
            "stop_loss": 48.0,
            "target_price": 55.0,
        })
        data = resp.json()
        assert data["shares"] == expected.share_size
        assert data["reward_risk_ratio"] == expected.reward_risk_ratio


# ── AC-7: Analytics/mistakes/fees require unlocked DB ────────────────


class TestModeGating:
    def test_analytics_locked_403(self, locked_client: TestClient) -> None:
        """AC-7: Analytics routes return 403 when locked."""
        resp = locked_client.get("/api/v1/analytics/expectancy")
        assert resp.status_code == 403
        # Value: verify error detail in response body
        data = resp.json()
        assert "detail" in data

    def test_mistakes_locked_403(self, locked_client: TestClient) -> None:
        """AC-7: Mistakes routes return 403 when locked."""
        resp = locked_client.post("/api/v1/mistakes", json={})
        assert resp.status_code == 403
        data = resp.json()
        assert "detail" in data

    def test_fees_locked_403(self, locked_client: TestClient) -> None:
        """AC-7: Fees routes return 403 when locked."""
        resp = locked_client.get("/api/v1/fees/summary")
        assert resp.status_code == 403
        data = resp.json()
        assert "detail" in data


# ── AC-8: Calculator does NOT require unlock ─────────────────────────


class TestCalculatorNoAuth:
    def test_calculator_no_unlock_needed(self, locked_client: TestClient) -> None:
        """AC-8: Calculator works without unlock (pure calculation)."""
        resp = locked_client.post("/api/v1/calculator/position-size", json={
            "balance": 50000,
            "risk_pct": 2.0,
            "entry_price": 100.0,
            "stop_loss": 95.0,
            "target_price": 110.0,
        })
        assert resp.status_code == 200
        # Value: verify calculator returned computed fields
        data = resp.json()
        assert "shares" in data
        assert data["shares"] > 0


# ── AC-9: Stub services return shaped defaults ──────────────────────


class TestStubShapes:
    def test_expectancy_shape(self, client: TestClient) -> None:
        """AC-9: Expectancy stub returns win_rate, expectancy, kelly_pct."""
        data = client.get("/api/v1/analytics/expectancy").json()
        assert "win_rate" in data
        assert "expectancy" in data
        assert "kelly_pct" in data
        # Value: verify types are numeric
        assert isinstance(data["win_rate"], (int, float))
        assert isinstance(data["expectancy"], (int, float))
        assert isinstance(data["kelly_pct"], (int, float))

    def test_sqn_shape(self, client: TestClient) -> None:
        """AC-9: SQN stub returns sqn, grade, trade_count."""
        data = client.get("/api/v1/analytics/sqn").json()
        assert "sqn" in data
        assert "grade" in data
        # Value: verify types
        assert isinstance(data["sqn"], (int, float))
        assert isinstance(data["grade"], str)


# ── AC-10: Integration test ─────────────────────────────────────────


class TestAnalyticsIntegration:
    def test_no_overrides_non_500(self) -> None:
        """AC-10: create_app() with unlock → analytics returns non-500."""
        app = create_app()
        with TestClient(app, raise_server_exceptions=False) as client:
            app.state.db_unlocked = True
            resp = client.get("/api/v1/analytics/expectancy")
            assert resp.status_code == 200
            # Value: verify valid JSON response
            data = resp.json()
            assert isinstance(data, dict)
            assert "win_rate" in data

    def test_calculator_pure_calculation(self) -> None:
        """AC-10: Calculator works without any state setup."""
        app = create_app()
        with TestClient(app, raise_server_exceptions=False) as client:
            resp = client.post("/api/v1/calculator/position-size", json={
                "balance": 10000,
                "risk_pct": 1.0,
                "entry_price": 10.0,
                "stop_loss": 9.0,
                "target_price": 12.0,
            })
            assert resp.status_code == 200
            # Value: verify calculator fields in response
            data = resp.json()
            assert "shares" in data
            assert isinstance(data["shares"], int)
