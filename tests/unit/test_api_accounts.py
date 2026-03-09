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

        resp = http.post("/api/v1/accounts", json={
            "account_id": "ACC001",
            "name": "Main Brokerage",
            "account_type": "BROKER",
            "institution": "Interactive Brokers",
        })
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


class TestUpdateAccount:
    def test_update_account_200(self, client) -> None:
        """AC-4: PUT /accounts/{id} updates account."""
        http, svc = client
        svc.update_account.return_value = _sample_account(name="Updated")

        resp = http.put("/api/v1/accounts/ACC001", json={"name": "Updated"})
        assert resp.status_code == 200


class TestDeleteAccount:
    def test_delete_account_204(self, client) -> None:
        """AC-5: DELETE /accounts/{id} returns 204."""
        http, svc = client

        resp = http.delete("/api/v1/accounts/ACC001")
        assert resp.status_code == 204
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

        resp = http.post("/api/v1/accounts/ACC001/balances", json={
            "balance": 50000.00,
        })
        assert resp.status_code == 201
