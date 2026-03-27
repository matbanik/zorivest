# tests/unit/test_api_reports.py
"""Tests for MEU-53: Trade Report REST endpoints.

RED phase — written FIRST per TDD protocol.
Source: 04a-api-trades.md L126-151
API contract: letter grades A-F (converted to/from int at boundary).
"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from zorivest_core.domain.entities import TradeReport

pytestmark = pytest.mark.unit


# ── Fixtures ────────────────────────────────────────────────────────────


@pytest.fixture()
def mock_report_svc():
    return MagicMock()


@pytest.fixture()
def client(mock_report_svc):
    """HTTP test client with mocked report service."""
    from zorivest_api.main import create_app
    from zorivest_api.dependencies import require_unlocked_db

    app = create_app()
    app.state.db_unlocked = True
    app.state.start_time = __import__("time").time()

    app.dependency_overrides[require_unlocked_db] = lambda: None

    from zorivest_api import dependencies as deps

    # Also inject mock trade/image services since the app registers those routes
    app.dependency_overrides[deps.get_trade_service] = lambda: MagicMock()
    app.dependency_overrides[deps.get_image_service] = lambda: MagicMock()
    app.dependency_overrides[deps.get_report_service] = lambda: mock_report_svc

    return TestClient(app), mock_report_svc


def _sample_report(**overrides) -> TradeReport:
    defaults = {
        "id": 1,
        "trade_id": "T001",
        "setup_quality": 4,  # int (B grade) — domain stores ints
        "execution_quality": 3,  # int (C grade) — domain stores ints
        "followed_plan": True,
        "emotional_state": "confident",
        "created_at": datetime(2025, 7, 15, 10, 30, 0),
        "lessons_learned": "Good timing",
        "tags": ["spy"],
    }
    defaults.update(overrides)
    return TradeReport(**defaults)


# ── Report CRUD ─────────────────────────────────────────────────────────


class TestCreateReport:
    """AC-7: POST /trades/{id}/report creates report."""

    def test_create_report_201(self, client) -> None:
        http, report_svc = client
        report_svc.create.return_value = _sample_report()

        resp = http.post(
            "/api/v1/trades/T001/report",
            json={
                "setup_quality": "B",  # Letter grade per 04a spec
                "execution_quality": "C",  # Letter grade per 04a spec
                "followed_plan": True,
                "emotional_state": "confident",
                "lessons_learned": "Good timing",
                "tags": ["spy"],
            },
        )

        assert resp.status_code == 201
        data = resp.json()
        assert data["trade_id"] == "T001"
        assert data["setup_quality"] == "B"  # Response returns letter grade
        assert data["execution_quality"] == "C"

    def test_create_report_404_trade_missing(self, client) -> None:
        http, report_svc = client
        report_svc.create.side_effect = ValueError("Trade 'T999' not found")

        resp = http.post(
            "/api/v1/trades/T999/report",
            json={
                "setup_quality": "C",
                "execution_quality": "C",
                "followed_plan": False,
                "emotional_state": "neutral",
            },
        )

        assert resp.status_code == 404
        # Value: verify error detail
        data = resp.json()
        assert "detail" in data

    def test_create_report_409_already_exists(self, client) -> None:
        http, report_svc = client
        report_svc.create.side_effect = ValueError("already exists")

        resp = http.post(
            "/api/v1/trades/T001/report",
            json={
                "setup_quality": "C",
                "execution_quality": "C",
                "followed_plan": False,
                "emotional_state": "neutral",
            },
        )

        assert resp.status_code == 409
        # Value: verify error detail
        data = resp.json()
        assert "detail" in data

    def test_create_report_422_invalid_grade(self, client) -> None:
        """Reject invalid letter grade values."""
        http, report_svc = client

        resp = http.post(
            "/api/v1/trades/T001/report",
            json={
                "setup_quality": "Z",  # Invalid grade
                "execution_quality": "A",
                "followed_plan": True,
            },
        )

        assert resp.status_code == 422  # Pydantic validation
        # Value: verify validation error shape
        data = resp.json()
        assert "detail" in data


class TestGetReport:
    """AC-8: GET /trades/{id}/report returns report."""

    def test_get_report_200(self, client) -> None:
        http, report_svc = client
        report_svc.get_for_trade.return_value = _sample_report()

        resp = http.get("/api/v1/trades/T001/report")
        assert resp.status_code == 200
        data = resp.json()
        assert data["trade_id"] == "T001"
        assert data["setup_quality"] == "B"  # Int 4 → grade B
        assert data["execution_quality"] == "C"  # Int 3 → grade C

    def test_get_report_404(self, client) -> None:
        http, report_svc = client
        report_svc.get_for_trade.return_value = None

        resp = http.get("/api/v1/trades/T001/report")
        assert resp.status_code == 404
        # Value: verify error detail
        data = resp.json()
        assert "detail" in data


class TestUpdateReport:
    """AC-7: PUT /trades/{id}/report updates report."""

    def test_update_report_200(self, client) -> None:
        http, report_svc = client
        report_svc.update.return_value = _sample_report(setup_quality=5)

        resp = http.put(
            "/api/v1/trades/T001/report",
            json={
                "setup_quality": "A",  # Letter grade
            },
        )
        assert resp.status_code == 200
        assert resp.json()["setup_quality"] == "A"  # Int 5 → grade A

    def test_update_report_404(self, client) -> None:
        http, report_svc = client
        report_svc.update.side_effect = ValueError("not found")

        resp = http.put("/api/v1/trades/T001/report", json={"setup_quality": "A"})
        assert resp.status_code == 404
        # Value: verify error detail
        data = resp.json()
        assert "detail" in data


class TestDeleteReport:
    """AC-7: DELETE /trades/{id}/report deletes report."""

    def test_delete_report_204(self, client) -> None:
        http, report_svc = client

        resp = http.delete("/api/v1/trades/T001/report")
        assert resp.status_code == 204
        # Value: verify no body on 204
        assert resp.content == b""
        report_svc.delete.assert_called_once_with("T001")

    def test_delete_report_404(self, client) -> None:
        http, report_svc = client
        report_svc.delete.side_effect = ValueError("not found")

        resp = http.delete("/api/v1/trades/T001/report")
        assert resp.status_code == 404
        # Value: verify error detail
        data = resp.json()
        assert "detail" in data


# ── Route wiring integration (no service override) ─────────────────────


class TestReportRouteWiring:
    """Verify report routes work through real create_app() → StubUoW → ReportService wiring.

    Does NOT override get_report_service — exercises the actual app plumbing.
    """

    @pytest.fixture()
    def wired_client(self):
        """TestClient using real app wiring (only override require_unlocked_db)."""
        from zorivest_api.main import create_app
        from zorivest_api.dependencies import require_unlocked_db

        app = create_app()
        app.dependency_overrides[require_unlocked_db] = lambda: None

        with TestClient(app) as http:
            yield http

    def test_create_and_get_report_real_wiring(self, wired_client) -> None:
        """POST + GET through real StubUoW-backed ReportService returns a valid report with nonzero ID."""
        http = wired_client

        # Step 1: Create a trade so report creation can find it
        trade_resp = http.post(
            "/api/v1/trades",
            json={
                "exec_id": "E_WIRING",
                "time": "2025-07-15T10:30:00",
                "instrument": "AAPL",
                "action": "BOT",
                "quantity": 100,
                "price": 150.0,
                "account_id": "ACC001",
            },
        )
        assert trade_resp.status_code == 201, f"Trade create failed: {trade_resp.text}"

        # Step 2: Create a report for that trade
        report_resp = http.post(
            "/api/v1/trades/E_WIRING/report",
            json={
                "setup_quality": "A",
                "execution_quality": "B",
                "followed_plan": True,
                "emotional_state": "confident",
                "lessons_learned": "Wiring test",
                "tags": ["integration"],
            },
        )
        assert report_resp.status_code == 201, (
            f"Report create failed: {report_resp.text}"
        )
        data = report_resp.json()
        assert data["id"] != 0, f"Expected nonzero ID, got {data['id']}"
        assert data["setup_quality"] == "A"
        assert data["execution_quality"] == "B"

        # Step 3: GET the report back
        get_resp = http.get("/api/v1/trades/E_WIRING/report")
        assert get_resp.status_code == 200
        get_data = get_resp.json()
        assert get_data["id"] == data["id"]
        assert get_data["trade_id"] == "E_WIRING"
        assert get_data["setup_quality"] == "A"
