# tests/unit/test_api_plans.py
"""Tests for MEU-66/67: TradePlan REST endpoints.

Covers: CRUD, MCP compat, dedup, linking, PATCH/status, DELETE.
Source: domain-model-reference.md L78-96, 04a-api-trades.md, 05d-mcp-trade-planning.md
"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from zorivest_core.domain.entities import TradePlan

pytestmark = pytest.mark.unit


# ── Fixtures ────────────────────────────────────────────────────────────


@pytest.fixture()
def mock_report_svc():
    return MagicMock()


@pytest.fixture()
def client(mock_report_svc):
    """HTTP test client with mocked report service (plan methods live here)."""
    from zorivest_api.main import create_app
    from zorivest_api.dependencies import require_unlocked_db

    app = create_app()
    app.state.db_unlocked = True
    app.state.start_time = __import__("time").time()

    app.dependency_overrides[require_unlocked_db] = lambda: None

    from zorivest_api import dependencies as deps

    app.dependency_overrides[deps.get_trade_service] = lambda: MagicMock()
    app.dependency_overrides[deps.get_image_service] = lambda: MagicMock()
    app.dependency_overrides[deps.get_report_service] = lambda: mock_report_svc

    return TestClient(app), mock_report_svc


def _sample_plan(**overrides) -> TradePlan:
    defaults = {
        "id": 1,
        "ticker": "AAPL",
        "direction": "BOT",
        "conviction": "high",
        "strategy_name": "Gap & Go",
        "strategy_description": "Long after gap up",
        "entry_price": 200.0,
        "stop_loss": 195.0,
        "target_price": 215.0,
        "entry_conditions": "Gap > 2%",
        "exit_conditions": "Target hit or EOD",
        "timeframe": "intraday",
        "risk_reward_ratio": 3.0,
        "status": "draft",
        "created_at": datetime(2026, 3, 12, 9, 0, 0),
        "updated_at": datetime(2026, 3, 12, 9, 0, 0),
    }
    defaults.update(overrides)
    return TradePlan(**defaults)


# ── Plan CRUD ───────────────────────────────────────────────────────────


class TestCreatePlan:
    """AC: POST /api/v1/trade-plans creates plan."""

    def test_create_plan_201(self, client) -> None:
        http, svc = client
        svc.create_plan.return_value = _sample_plan()

        resp = http.post(
            "/api/v1/trade-plans",
            json={
                "ticker": "AAPL",
                "direction": "BOT",
                "conviction": "high",
                "strategy_name": "Gap & Go",
                "strategy_description": "Long after gap up",
                "entry_price": 200.0,
                "stop_loss": 195.0,
                "target_price": 215.0,
                "entry_conditions": "Gap > 2%",
                "exit_conditions": "Target hit or EOD",
                "timeframe": "intraday",
            },
        )

        assert resp.status_code == 201
        data = resp.json()
        assert data["ticker"] == "AAPL"
        assert data["risk_reward_ratio"] == 3.0
        assert data["status"] == "draft"
        svc.create_plan.assert_called_once()

    def test_create_plan_mcp_short_names_201(self, client) -> None:
        """MCP cross-surface: accept {entry, stop, target, conditions}."""
        http, svc = client
        svc.create_plan.return_value = _sample_plan()

        resp = http.post(
            "/api/v1/trade-plans",
            json={
                "ticker": "AAPL",
                "direction": "long",
                "conviction": "high",
                "strategy_name": "breakout",
                "entry": 200.0,
                "stop": 195.0,
                "target": 215.0,
                "conditions": "Gap > 2%",
                "timeframe": "intraday",
            },
        )
        assert resp.status_code == 201
        # Value: verify service-level alias unwrapping
        data = resp.json()
        assert isinstance(data, dict)
        # Verify the alias mapping worked — service received long names
        call_data = svc.create_plan.call_args[0][0]
        assert "entry_price" in call_data
        assert "entry" not in call_data

    def test_create_plan_duplicate_409(self, client) -> None:
        """F3: Duplicate active plan → 409."""
        http, svc = client
        svc.create_plan.side_effect = ValueError("Duplicate active plan for AAPL/BOT")

        resp = http.post(
            "/api/v1/trade-plans",
            json={
                "ticker": "AAPL",
                "direction": "BOT",
                "strategy_name": "Gap & Go",
                "entry_price": 200.0,
                "stop_loss": 195.0,
                "target_price": 215.0,
            },
        )
        assert resp.status_code == 409
        # Value: verify error detail
        data = resp.json()
        assert "detail" in data


class TestGetPlan:
    """AC: GET /api/v1/trade-plans/{id} returns plan."""

    def test_get_plan_200(self, client) -> None:
        http, svc = client
        svc.get_plan.return_value = _sample_plan()

        resp = http.get("/api/v1/trade-plans/1")
        assert resp.status_code == 200
        assert resp.json()["ticker"] == "AAPL"

    def test_get_plan_404(self, client) -> None:
        http, svc = client
        svc.get_plan.return_value = None

        resp = http.get("/api/v1/trade-plans/999")
        assert resp.status_code == 404
        # Value: verify error detail
        data = resp.json()
        assert "detail" in data


class TestListPlans:
    """AC: GET /api/v1/trade-plans returns paginated list."""

    def test_list_plans_200(self, client) -> None:
        http, svc = client
        svc.list_plans.return_value = [_sample_plan()]

        resp = http.get("/api/v1/trade-plans?limit=10&offset=0")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 1
        svc.list_plans.assert_called_once_with(limit=10, offset=0)


class TestUpdatePlan:
    """AC: PUT /api/v1/trade-plans/{id} updates plan."""

    def test_update_plan_200(self, client) -> None:
        http, svc = client
        svc.update_plan.return_value = _sample_plan(status="active")

        resp = http.put("/api/v1/trade-plans/1", json={"status": "active"})
        assert resp.status_code == 200
        assert resp.json()["status"] == "active"

    def test_update_plan_404(self, client) -> None:
        http, svc = client
        svc.update_plan.side_effect = ValueError("Plan 999 not found")

        resp = http.put("/api/v1/trade-plans/999", json={"status": "active"})
        assert resp.status_code == 404
        # Value: verify error detail
        data = resp.json()
        assert "detail" in data


class TestDeletePlan:
    """AC: DELETE /api/v1/trade-plans/{id} deletes plan."""

    def test_delete_plan_204(self, client) -> None:
        http, svc = client
        svc.delete_plan.return_value = None

        resp = http.delete("/api/v1/trade-plans/1")
        assert resp.status_code == 204
        # Value: verify no body on 204
        assert resp.content == b""
        svc.delete_plan.assert_called_once_with(1)

    def test_delete_plan_404(self, client) -> None:
        http, svc = client
        svc.delete_plan.side_effect = ValueError("Plan 999 not found")

        resp = http.delete("/api/v1/trade-plans/999")
        assert resp.status_code == 404
        # Value: verify error detail
        data = resp.json()
        assert "detail" in data


class TestPatchPlanStatus:
    """AC: PATCH /api/v1/trade-plans/{id}/status transitions status."""

    def test_patch_status_to_active(self, client) -> None:
        http, svc = client
        svc.update_plan.return_value = _sample_plan(status="active")

        resp = http.patch("/api/v1/trade-plans/1/status", json={"status": "active"})
        assert resp.status_code == 200
        assert resp.json()["status"] == "active"

    def test_patch_status_executed_with_link(self, client) -> None:
        """PATCH with status=executed + linked_trade_id routes through link_plan_to_trade."""
        http, svc = client
        svc.link_plan_to_trade.return_value = _sample_plan(
            status="executed",
            linked_trade_id="T001",
        )

        resp = http.patch(
            "/api/v1/trade-plans/1/status",
            json={
                "status": "executed",
                "linked_trade_id": "T001",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "executed"
        svc.link_plan_to_trade.assert_called_once_with(1, "T001")

    def test_patch_status_executed_with_link_sets_executed_at(self, client) -> None:
        """F2 regression: PATCH executed+link must set executed_at in the response.

        Previously link_plan_to_trade only returned a plan with executed_at unset,
        and the route tried to patch it in memory (broken). Now link_plan_to_trade
        persists executed_at directly and returns it populated.
        """
        from datetime import datetime, timezone

        ts = datetime.now(timezone.utc)
        http, svc = client
        svc.link_plan_to_trade.return_value = _sample_plan(
            status="executed",
            linked_trade_id="T001",
            executed_at=ts,
        )

        resp = http.patch(
            "/api/v1/trade-plans/1/status",
            json={
                "status": "executed",
                "linked_trade_id": "T001",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "executed"
        # executed_at must be present and non-null in the response
        assert data.get("executed_at") is not None, (
            "executed_at must be persisted and returned when plan is linked+executed"
        )

    def test_patch_status_link_trade_not_found_404(self, client) -> None:
        http, svc = client
        svc.link_plan_to_trade.side_effect = ValueError("Trade 'MISSING' not found")

        resp = http.patch(
            "/api/v1/trade-plans/1/status",
            json={
                "status": "executed",
                "linked_trade_id": "MISSING",
            },
        )
        assert resp.status_code == 404
        # Value: verify error detail
        data = resp.json()
        assert "detail" in data


# ── F2: PUT linking routes through validation ───────────────────────────


class TestPlanLinkingViaPUT:
    """F2: PUT with linked_trade_id + status=executed routes through link_plan_to_trade."""

    def test_put_link_routes_through_validation(self, client) -> None:
        http, svc = client
        svc.link_plan_to_trade.return_value = _sample_plan(
            linked_trade_id="T001",
            status="executed",
        )

        resp = http.put(
            "/api/v1/trade-plans/1",
            json={
                "linked_trade_id": "T001",
                "status": "executed",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["linked_trade_id"] == "T001"
        assert data["status"] == "executed"
        svc.link_plan_to_trade.assert_called_once_with(1, "T001")

    def test_put_link_missing_trade_404(self, client) -> None:
        """PUT with linked_trade_id to nonexistent trade → 404."""
        http, svc = client
        svc.link_plan_to_trade.side_effect = ValueError("Trade 'MISSING' not found")

        resp = http.put(
            "/api/v1/trade-plans/1",
            json={
                "linked_trade_id": "MISSING",
                "status": "executed",
            },
        )
        assert resp.status_code == 404
        # Value: verify error detail
        data = resp.json()
        assert "detail" in data


# ── Wiring integration (no service override) ────────────────────────────


class TestPlanRouteWiring:
    """Verify plan routes work through real create_app() → StubUoW → ReportService wiring."""

    @pytest.fixture()
    def wired_client(self):
        """TestClient using real app wiring (only override require_unlocked_db)."""
        from zorivest_api.main import create_app
        from zorivest_api.dependencies import require_unlocked_db

        app = create_app()
        app.dependency_overrides[require_unlocked_db] = lambda: None

        with TestClient(app) as http:
            yield http

    def test_create_and_get_plan_real_wiring(self, wired_client) -> None:
        """POST + GET through real StubUoW-backed ReportService returns a valid plan."""
        http = wired_client

        plan_resp = http.post(
            "/api/v1/trade-plans",
            json={
                "ticker": "SPY",
                "direction": "SLD",
                "conviction": "medium",
                "strategy_name": "Breakdown",
                "strategy_description": "Short below support",
                "entry_price": 600.0,
                "stop_loss": 605.0,
                "target_price": 585.0,
                "entry_conditions": "Break below VWAP",
                "exit_conditions": "Cover at target",
                "timeframe": "intraday",
            },
        )
        assert plan_resp.status_code == 201, f"Plan create failed: {plan_resp.text}"
        data = plan_resp.json()
        plan_id = data["id"]
        assert plan_id != 0, f"Expected nonzero ID, got {plan_id}"
        assert data["ticker"] == "SPY"
        assert data["risk_reward_ratio"] == pytest.approx(3.0)

        get_resp = http.get(f"/api/v1/trade-plans/{plan_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["id"] == plan_id

    def test_create_duplicate_plan_real_wiring_409(self, wired_client) -> None:
        """Two identical POSTs → first 201, second 409."""
        http = wired_client
        payload = {
            "ticker": "AAPL",
            "direction": "BOT",
            "strategy_name": "Gap & Go",
            "entry_price": 200.0,
            "stop_loss": 195.0,
            "target_price": 215.0,
            "timeframe": "intraday",
        }
        r1 = http.post("/api/v1/trade-plans", json=payload)
        assert r1.status_code == 201

        r2 = http.post("/api/v1/trade-plans", json=payload)
        assert r2.status_code == 409, f"Expected 409, got {r2.status_code}: {r2.text}"

    def test_link_to_missing_trade_real_wiring_404(self, wired_client) -> None:
        """PUT with linked_trade_id to nonexistent trade → 404 (not 200)."""
        http = wired_client

        plan_resp = http.post(
            "/api/v1/trade-plans",
            json={
                "ticker": "TSLA",
                "direction": "BOT",
                "strategy_name": "Momentum",
                "entry_price": 300.0,
                "stop_loss": 290.0,
                "target_price": 330.0,
                "timeframe": "intraday",
            },
        )
        assert plan_resp.status_code == 201
        plan_id = plan_resp.json()["id"]

        link_resp = http.put(
            f"/api/v1/trade-plans/{plan_id}",
            json={
                "linked_trade_id": "MISSING-TRADE",
                "status": "executed",
            },
        )
        assert link_resp.status_code == 404, (
            f"Expected 404, got {link_resp.status_code}: {link_resp.text}"
        )


# ── MEU-BV3: Boundary Validation — Plan Input Hardening ─────────────────


class TestCreatePlanBoundaryValidation:
    """BV3-AC-1 through AC-6: Schema-level rejection of invalid create input."""

    def test_invalid_direction_returns_422(self, client) -> None:
        """BV3-AC-1: Invalid direction enum value rejected at schema level."""
        http, svc = client
        resp = http.post(
            "/api/v1/trade-plans",
            json={
                "ticker": "AAPL",
                "direction": "INVALID",
                "conviction": "high",
                "strategy_name": "Test",
            },
        )
        assert resp.status_code == 422

    def test_invalid_conviction_returns_422(self, client) -> None:
        """BV3-AC-2: Invalid conviction enum value rejected at schema level."""
        http, svc = client
        resp = http.post(
            "/api/v1/trade-plans",
            json={
                "ticker": "AAPL",
                "direction": "BOT",
                "conviction": "INVALID",
                "strategy_name": "Test",
            },
        )
        assert resp.status_code == 422

    def test_blank_ticker_returns_422(self, client) -> None:
        """BV3-AC-3: Blank ticker rejected at schema level."""
        http, svc = client
        resp = http.post(
            "/api/v1/trade-plans",
            json={
                "ticker": "",
                "direction": "BOT",
                "conviction": "high",
                "strategy_name": "Test",
            },
        )
        assert resp.status_code == 422

    def test_blank_strategy_name_returns_422(self, client) -> None:
        """BV3-AC-4: Blank strategy_name rejected at schema level."""
        http, svc = client
        resp = http.post(
            "/api/v1/trade-plans",
            json={
                "ticker": "AAPL",
                "direction": "BOT",
                "conviction": "high",
                "strategy_name": "",
            },
        )
        assert resp.status_code == 422

    def test_extra_field_on_create_returns_422(self, client) -> None:
        """BV3-AC-5: Unknown extra fields rejected by extra='forbid'."""
        http, svc = client
        resp = http.post(
            "/api/v1/trade-plans",
            json={
                "ticker": "AAPL",
                "direction": "BOT",
                "conviction": "high",
                "strategy_name": "Test",
                "unexpected_field": "should_reject",
            },
        )
        assert resp.status_code == 422


class TestUpdatePlanBoundaryValidation:
    """BV3-AC-5,AC-6,AC-7: Schema-level rejection of invalid update input."""

    def test_invalid_direction_on_update_returns_422(self, client) -> None:
        """BV3-AC-6: Invalid direction enum on update rejected."""
        http, svc = client
        resp = http.put(
            "/api/v1/trade-plans/1",
            json={"direction": "INVALID"},
        )
        assert resp.status_code == 422

    def test_invalid_conviction_on_update_returns_422(self, client) -> None:
        """BV3-AC-7: Invalid conviction enum on update rejected."""
        http, svc = client
        resp = http.put(
            "/api/v1/trade-plans/1",
            json={"conviction": "INVALID"},
        )
        assert resp.status_code == 422

    def test_invalid_status_on_update_returns_422(self, client) -> None:
        """BV3-AC-7: Invalid status enum on update rejected."""
        http, svc = client
        resp = http.put(
            "/api/v1/trade-plans/1",
            json={"status": "INVALID"},
        )
        assert resp.status_code == 422

    def test_blank_ticker_on_update_returns_422(self, client) -> None:
        """BV3-AC-8: Blank ticker on update rejected (create/update parity)."""
        http, svc = client
        resp = http.put(
            "/api/v1/trade-plans/1",
            json={"ticker": ""},
        )
        assert resp.status_code == 422

    def test_extra_field_on_update_returns_422(self, client) -> None:
        """BV3-AC-5: Unknown extra fields rejected on update."""
        http, svc = client
        resp = http.put(
            "/api/v1/trade-plans/1",
            json={"unexpected_field": "should_reject"},
        )
        assert resp.status_code == 422


class TestPatchPlanStatusBoundaryValidation:
    """BV3-AC-9: PATCH /trade-plans/{id}/status schema hardening."""

    def test_invalid_status_on_patch_returns_422(self, client) -> None:
        """BV3-AC-9: Invalid status enum on PATCH rejected."""
        http, svc = client
        resp = http.patch(
            "/api/v1/trade-plans/1/status",
            json={"status": "INVALID"},
        )
        assert resp.status_code == 422


class TestWhitespaceOnlyPlanValidation:
    """F3/F5 fix: Whitespace-only strings must be rejected, not just empty strings."""

    def test_whitespace_ticker_on_create_returns_422(self, client) -> None:
        """Whitespace-only ticker is stripped to '' and rejected by min_length=1."""
        http, svc = client
        resp = http.post(
            "/api/v1/trade-plans",
            json={
                "ticker": "   ",
                "direction": "BOT",
                "conviction": "high",
                "strategy_name": "Test",
            },
        )
        assert resp.status_code == 422

    def test_whitespace_strategy_name_on_create_returns_422(self, client) -> None:
        """Whitespace-only strategy_name is stripped to '' and rejected."""
        http, svc = client
        resp = http.post(
            "/api/v1/trade-plans",
            json={
                "ticker": "AAPL",
                "direction": "BOT",
                "conviction": "high",
                "strategy_name": "   ",
            },
        )
        assert resp.status_code == 422

    def test_whitespace_ticker_on_update_returns_422(self, client) -> None:
        """Whitespace-only ticker on update is stripped to '' and rejected."""
        http, svc = client
        resp = http.put(
            "/api/v1/trade-plans/1",
            json={"ticker": "   "},
        )
        assert resp.status_code == 422

    def test_whitespace_strategy_name_on_update_returns_422(self, client) -> None:
        """Whitespace-only strategy_name on update is stripped to '' and rejected."""
        http, svc = client
        resp = http.put(
            "/api/v1/trade-plans/1",
            json={"strategy_name": "   "},
        )
        assert resp.status_code == 422

    def test_blank_strategy_name_on_update_returns_422(self, client) -> None:
        """Empty strategy_name on update rejected (completes missing parity test)."""
        http, svc = client
        resp = http.put(
            "/api/v1/trade-plans/1",
            json={"strategy_name": ""},
        )
        assert resp.status_code == 422


# ── MEU-70a: position_size round-trip ────────────────────────────────────


class TestPositionSizeRoundTrip:
    """AC-4/AC-5/AC-6: position_size accepted on create/update, returned in response."""

    def test_create_plan_with_position_size_returns_value(self, client) -> None:
        """POST with position_size → response includes the value."""
        http, svc = client
        svc.create_plan.return_value = _sample_plan(
            shares_planned=100, position_size=20000.0
        )

        resp = http.post(
            "/api/v1/trade-plans",
            json={
                "ticker": "AAPL",
                "direction": "BOT",
                "strategy_name": "Gap & Go",
                "entry_price": 200.0,
                "stop_loss": 195.0,
                "target_price": 215.0,
                "timeframe": "intraday",
                "shares_planned": 100,
                "position_size": 20000.0,
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["position_size"] == 20000.0
        assert data["shares_planned"] == 100

    def test_create_plan_without_position_size_returns_null(self, client) -> None:
        """POST without position_size → response has null."""
        http, svc = client
        svc.create_plan.return_value = _sample_plan()

        resp = http.post(
            "/api/v1/trade-plans",
            json={
                "ticker": "AAPL",
                "direction": "BOT",
                "strategy_name": "Gap & Go",
                "entry_price": 200.0,
                "stop_loss": 195.0,
                "target_price": 215.0,
                "timeframe": "intraday",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["position_size"] is None

    def test_update_plan_with_position_size(self, client) -> None:
        """PUT with position_size → value persisted in response."""
        http, svc = client
        svc.update_plan.return_value = _sample_plan(position_size=15000.0)

        resp = http.put(
            "/api/v1/trade-plans/1",
            json={"position_size": 15000.0},
        )
        assert resp.status_code == 200
        assert resp.json()["position_size"] == 15000.0

    def test_get_plan_includes_position_size(self, client) -> None:
        """GET includes position_size in response body."""
        http, svc = client
        svc.get_plan.return_value = _sample_plan(position_size=25000.0)

        resp = http.get("/api/v1/trade-plans/1")
        assert resp.status_code == 200
        assert resp.json()["position_size"] == 25000.0


class TestPositionSizeRealWiring:
    """AC-4/AC-5: position_size round-trip through real StubUoW wiring."""

    @pytest.fixture()
    def wired_client(self):
        """TestClient using real app wiring (only override require_unlocked_db)."""
        from zorivest_api.main import create_app
        from zorivest_api.dependencies import require_unlocked_db

        app = create_app()
        app.dependency_overrides[require_unlocked_db] = lambda: None

        with TestClient(app) as http:
            yield http

    def test_create_with_position_size_real_wiring(self, wired_client) -> None:
        """POST→GET round-trip preserves position_size through real wiring."""
        http = wired_client

        resp = http.post(
            "/api/v1/trade-plans",
            json={
                "ticker": "MSFT",
                "direction": "BOT",
                "strategy_name": "Position Size Test",
                "entry_price": 400.0,
                "stop_loss": 390.0,
                "target_price": 420.0,
                "timeframe": "swing",
                "shares_planned": 50,
                "position_size": 20000.0,
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        plan_id = data["id"]
        assert data["position_size"] == 20000.0
        assert data["shares_planned"] == 50

        # GET should return same values
        get_resp = http.get(f"/api/v1/trade-plans/{plan_id}")
        assert get_resp.status_code == 200
        get_data = get_resp.json()
        assert get_data["position_size"] == 20000.0
        assert get_data["shares_planned"] == 50
