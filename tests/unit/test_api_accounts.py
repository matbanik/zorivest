# tests/unit/test_api_accounts.py
"""Tests for MEU-25: Account CRUD REST endpoints.

Red phase — written FIRST per TDD protocol.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from zorivest_core.domain.entities import Account, BalanceSnapshot
from zorivest_core.domain.enums import AccountType
from zorivest_core.domain.exceptions import NotFoundError


@pytest.fixture()
def client():
    """HTTP test client with mocked account service."""
    account_svc = MagicMock()
    # MEU-71: enriched responses call get_latest_balance — default to None
    account_svc.get_latest_balance.return_value = None

    from zorivest_api.main import create_app
    from zorivest_api.dependencies import require_unlocked_db

    app = create_app()
    app.state.db_unlocked = True
    app.state.start_time = __import__("time").time()
    app.dependency_overrides[require_unlocked_db] = lambda: None

    from zorivest_api import dependencies as deps

    app.dependency_overrides[deps.get_account_service] = lambda: account_svc

    return TestClient(app), account_svc


def _sample_account(**overrides) -> Account:
    defaults = {
        "account_id": "ACC001",
        "name": "Main Brokerage",
        "account_type": AccountType.BROKER,
        "institution": "Interactive Brokers",
        "currency": "USD",
        "is_tax_advantaged": False,
        "notes": "",
    }
    defaults.update(overrides)
    return Account(**defaults)


# ── Account CRUD ────────────────────────────────────────────────────────


class TestCreateAccount:
    def test_create_account_201(self, client) -> None:
        """AC-1: POST /accounts creates account and returns 201."""
        http, svc = client
        svc.create_account.return_value = _sample_account()

        resp = http.post(
            "/api/v1/accounts",
            json={
                "account_id": "ACC001",
                "name": "Main Brokerage",
                "account_type": "BROKER",
                "institution": "Interactive Brokers",
            },
        )
        assert resp.status_code == 201
        assert resp.json()["account_id"] == "ACC001"


class TestListAccounts:
    def test_list_accounts_200(self, client) -> None:
        """AC-2: GET /accounts returns account list."""
        http, svc = client
        svc.list_accounts.return_value = [_sample_account()]

        resp = http.get("/api/v1/accounts")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1


class TestGetAccount:
    def test_get_account_200(self, client) -> None:
        """AC-3: GET /accounts/{id} returns account."""
        http, svc = client
        svc.get_account.return_value = _sample_account()

        resp = http.get("/api/v1/accounts/ACC001")
        assert resp.status_code == 200
        assert resp.json()["account_id"] == "ACC001"

    def test_get_account_404(self, client) -> None:
        """AC-3: GET /accounts/{id} returns 404 for missing account."""
        http, svc = client
        svc.get_account.side_effect = NotFoundError("Account not found: MISSING")

        resp = http.get("/api/v1/accounts/MISSING")
        assert resp.status_code == 404
        # Value: verify error detail
        data = resp.json()
        assert "detail" in data


class TestUpdateAccount:
    def test_update_account_200(self, client) -> None:
        """AC-4: PUT /accounts/{id} updates account."""
        http, svc = client
        svc.update_account.return_value = _sample_account(name="Updated")

        resp = http.put("/api/v1/accounts/ACC001", json={"name": "Updated"})
        assert resp.status_code == 200
        # Value: verify updated field in response
        data = resp.json()
        assert data["name"] == "Updated"


class TestDeleteAccount:
    def test_delete_account_204(self, client) -> None:
        """AC-5: DELETE /accounts/{id} returns 204."""
        http, svc = client

        resp = http.delete("/api/v1/accounts/ACC001")
        assert resp.status_code == 204
        # Value: verify no body on 204
        assert resp.content == b""
        svc.delete_account.assert_called_once_with("ACC001")


class TestRecordBalance:
    def test_record_balance_201(self, client) -> None:
        """AC-6: POST /accounts/{id}/balances records balance snapshot."""
        from datetime import datetime
        from decimal import Decimal

        http, svc = client
        svc.add_balance_snapshot.return_value = BalanceSnapshot(
            id=1,
            account_id="ACC001",
            datetime=datetime(2025, 1, 15),
            balance=Decimal("50000.00"),
        )

        resp = http.post(
            "/api/v1/accounts/ACC001/balances",
            json={
                "balance": 50000.00,
            },
        )
        assert resp.status_code == 201
        # Value: verify response body has balance data
        data = resp.json()
        assert isinstance(data, dict)
        assert "account_id" in data or "balance" in data or "id" in data


# ── MEU-71: Account API Completion ──────────────────────────────────────


class TestListBalanceHistory:
    """AC-1, AC-2: GET /accounts/{id}/balances returns balance history."""

    def test_list_balances_200(self, client) -> None:
        """AC-1: GET /{id}/balances returns paginated balance snapshot list."""
        from datetime import datetime
        from decimal import Decimal

        http, svc = client
        svc.list_balance_history.return_value = [
            BalanceSnapshot(
                id=2,
                account_id="ACC001",
                datetime=datetime(2025, 2, 15),
                balance=Decimal("52000.00"),
            ),
            BalanceSnapshot(
                id=1,
                account_id="ACC001",
                datetime=datetime(2025, 1, 15),
                balance=Decimal("50000.00"),
            ),
        ]
        svc.count_balance_history.return_value = 2

        resp = http.get("/api/v1/accounts/ACC001/balances")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert len(data["items"]) == 2
        assert data["items"][0]["balance"] == 52000.00

    def test_list_balances_empty(self, client) -> None:
        """AC-1: returns empty list for account with no snapshots."""
        http, svc = client
        svc.list_balance_history.return_value = []
        svc.count_balance_history.return_value = 0

        resp = http.get("/api/v1/accounts/ACC001/balances")
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []
        assert data["total"] == 0

    def test_list_balances_404_unknown_account(self, client) -> None:
        """AC-2: returns 404 for unknown account."""
        http, svc = client
        svc.list_balance_history.side_effect = NotFoundError(
            "Account not found: MISSING"
        )

        resp = http.get("/api/v1/accounts/MISSING/balances")
        assert resp.status_code == 404


class TestGetAccountEnriched:
    """AC-3: AccountResponse includes latest_balance and latest_balance_date."""

    def test_get_account_includes_latest_balance(self, client) -> None:
        """AC-3: GET /accounts/{id} returns latest balance fields."""
        from datetime import datetime
        from decimal import Decimal

        http, svc = client
        svc.get_account.return_value = _sample_account()
        svc.get_latest_balance.return_value = BalanceSnapshot(
            id=1,
            account_id="ACC001",
            datetime=datetime(2025, 2, 15),
            balance=Decimal("55000.00"),
        )

        resp = http.get("/api/v1/accounts/ACC001")
        assert resp.status_code == 200
        data = resp.json()
        assert data["latest_balance"] == 55000.00
        assert data["latest_balance_date"] is not None

    def test_get_account_null_balance_when_no_snapshots(self, client) -> None:
        """AC-3: latest_balance is null when no snapshots exist."""
        http, svc = client
        svc.get_account.return_value = _sample_account()
        svc.get_latest_balance.return_value = None

        resp = http.get("/api/v1/accounts/ACC001")
        assert resp.status_code == 200
        data = resp.json()
        assert data["latest_balance"] is None
        assert data["latest_balance_date"] is None
