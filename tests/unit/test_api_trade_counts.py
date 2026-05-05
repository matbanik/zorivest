# tests/unit/test_api_trade_counts.py
"""Tests for POST /accounts:trade-counts — batch trade count query endpoint.

Red phase — written FIRST per TDD protocol.
Covers: endpoint input validation, response shape, boundary cases.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client():
    """HTTP test client with mocked account service."""
    account_svc = MagicMock()
    # Default mock: get_latest_balance returns None (enrichment helper)
    account_svc.get_latest_balance.return_value = None
    # Default mock: get_account_metrics returns empty (GET /{id} enrichment)
    account_svc.get_account_metrics.return_value = {
        "trade_count": 0,
        "round_trip_count": 0,
        "win_rate": 0.0,
        "total_realized_pnl": 0.0,
    }

    from zorivest_api.main import create_app
    from zorivest_api.dependencies import require_unlocked_db

    app = create_app()
    app.state.db_unlocked = True
    app.state.start_time = __import__("time").time()
    app.dependency_overrides[require_unlocked_db] = lambda: None

    from zorivest_api import dependencies as deps

    app.dependency_overrides[deps.get_account_service] = lambda: account_svc

    return TestClient(app), account_svc


# ── POST /accounts:trade-counts ─────────────────────────────────────────


class TestTradeCountsEndpoint:
    """POST :trade-counts — batch trade/plan count query."""

    def test_returns_200_with_counts(self, client) -> None:
        """Returns 200 with correct trade/plan counts per account."""
        http, svc = client
        svc.get_trade_counts.return_value = {
            "ACC001": {"trade_count": 5, "plan_count": 2},
            "ACC002": {"trade_count": 0, "plan_count": 0},
        }

        resp = http.post(
            "/api/v1/accounts:trade-counts",
            json={"account_ids": ["ACC001", "ACC002"]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["ACC001"]["trade_count"] == 5
        assert data["ACC001"]["plan_count"] == 2
        assert data["ACC002"]["trade_count"] == 0
        assert data["ACC002"]["plan_count"] == 0
        svc.get_trade_counts.assert_called_once_with(["ACC001", "ACC002"])

    def test_single_account_id(self, client) -> None:
        """Works with a single account ID."""
        http, svc = client
        svc.get_trade_counts.return_value = {
            "ACC001": {"trade_count": 10, "plan_count": 0},
        }

        resp = http.post(
            "/api/v1/accounts:trade-counts",
            json={"account_ids": ["ACC001"]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["ACC001"]["trade_count"] == 10

    def test_empty_account_ids_returns_422(self, client) -> None:
        """Empty account_ids list is rejected by min_length=1 validation."""
        http, svc = client

        resp = http.post(
            "/api/v1/accounts:trade-counts",
            json={"account_ids": []},
        )
        assert resp.status_code == 422

    def test_missing_account_ids_returns_422(self, client) -> None:
        """Missing account_ids field is rejected."""
        http, svc = client

        resp = http.post(
            "/api/v1/accounts:trade-counts",
            json={},
        )
        assert resp.status_code == 422

    def test_extra_fields_rejected(self, client) -> None:
        """Extra fields are rejected by extra='forbid'."""
        http, svc = client

        resp = http.post(
            "/api/v1/accounts:trade-counts",
            json={"account_ids": ["ACC001"], "unexpected": True},
        )
        assert resp.status_code == 422

    def test_passes_through_to_service(self, client) -> None:
        """Verifies service layer is called with the correct arguments."""
        http, svc = client
        svc.get_trade_counts.return_value = {
            "ACC001": {"trade_count": 0, "plan_count": 0},
        }

        http.post(
            "/api/v1/accounts:trade-counts",
            json={"account_ids": ["ACC001"]},
        )

        svc.get_trade_counts.assert_called_once_with(["ACC001"])


class TestTradeCountsBoundaryValidation:
    """Boundary validation for :trade-counts endpoint."""

    def test_max_100_ids_accepted(self, client) -> None:
        """Accepts up to 100 account IDs (max_length=100)."""
        http, svc = client
        ids = [f"ACC{i:03d}" for i in range(100)]
        svc.get_trade_counts.return_value = {
            aid: {"trade_count": 0, "plan_count": 0} for aid in ids
        }

        resp = http.post(
            "/api/v1/accounts:trade-counts",
            json={"account_ids": ids},
        )
        assert resp.status_code == 200

    def test_over_100_ids_rejected(self, client) -> None:
        """Rejects more than 100 account IDs."""
        http, svc = client
        ids = [f"ACC{i:03d}" for i in range(101)]

        resp = http.post(
            "/api/v1/accounts:trade-counts",
            json={"account_ids": ids},
        )
        assert resp.status_code == 422
