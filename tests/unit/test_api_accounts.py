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
    # MEU-37 AC-12: GET /{id} calls get_account_metrics — default to empty
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
        assert data["account_id"] == "ACC001"
        assert data["balance"] == 50000.00


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
        svc.get_account_metrics.return_value = {
            "trade_count": 0,
            "round_trip_count": 0,
            "win_rate": 0.0,
            "total_realized_pnl": 0.0,
        }

        resp = http.get("/api/v1/accounts/ACC001")
        assert resp.status_code == 200
        data = resp.json()
        assert data["latest_balance"] is None
        assert data["latest_balance_date"] is None


# ── MEU-37: Account Integrity API Tests ─────────────────────────────────


class TestDeleteAccountBlockOnly:
    """AC-8, AC-9: Block-only DELETE returns 409 or 204."""

    def test_delete_with_trades_returns_409(self, client) -> None:
        """AC-8: DELETE returns 409 when trades exist."""
        from zorivest_core.domain.exceptions import ConflictError

        http, svc = client
        svc.delete_account.side_effect = ConflictError("1 trade(s) exist")
        resp = http.delete("/api/v1/accounts/ACC001")
        assert resp.status_code == 409
        assert "detail" in resp.json()
        assert "trade" in resp.json()["detail"].lower()

    def test_delete_system_returns_403(self, client) -> None:
        """AC-7: DELETE on system account returns 403."""
        from zorivest_core.domain.exceptions import ForbiddenError

        http, svc = client
        svc.delete_account.side_effect = ForbiddenError("Cannot modify system account")
        resp = http.delete("/api/v1/accounts/SYSTEM_DEFAULT")
        assert resp.status_code == 403
        assert "detail" in resp.json()
        assert "system" in resp.json()["detail"].lower()


class TestArchiveEndpoint:
    """AC-10: POST /{id}:archive returns 200 with status."""

    def test_archive_returns_200(self, client) -> None:
        """AC-10: POST :archive returns status=archived."""
        http, svc = client
        resp = http.post("/api/v1/accounts/ACC001:archive")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "archived"
        assert data["account_id"] == "ACC001"
        svc.archive_account.assert_called_once_with("ACC001")

    def test_archive_system_returns_403(self, client) -> None:
        """AC-7: POST :archive on system account returns 403."""
        from zorivest_core.domain.exceptions import ForbiddenError

        http, svc = client
        svc.archive_account.side_effect = ForbiddenError("Cannot modify system account")
        resp = http.post("/api/v1/accounts/SYSTEM_DEFAULT:archive")
        assert resp.status_code == 403
        assert "detail" in resp.json()
        assert "system" in resp.json()["detail"].lower()

    def test_archive_missing_returns_404(self, client) -> None:
        http, svc = client
        svc.archive_account.side_effect = NotFoundError("Account not found: MISSING")
        resp = http.post("/api/v1/accounts/MISSING:archive")
        assert resp.status_code == 404
        assert "detail" in resp.json()


class TestReassignTradesEndpoint:
    """AC-11: POST /{id}:reassign-trades returns 200 with count."""

    def test_reassign_returns_200(self, client) -> None:
        """AC-11: POST :reassign-trades returns trades_reassigned count."""
        http, svc = client
        svc.reassign_trades_and_delete.return_value = 5
        resp = http.post("/api/v1/accounts/ACC001:reassign-trades")
        assert resp.status_code == 200
        data = resp.json()
        assert data["trades_reassigned"] == 5
        assert data["account_id"] == "ACC001"

    def test_reassign_system_returns_403(self, client) -> None:
        """AC-7: POST :reassign-trades on system account returns 403."""
        from zorivest_core.domain.exceptions import ForbiddenError

        http, svc = client
        svc.reassign_trades_and_delete.side_effect = ForbiddenError("Cannot modify")
        resp = http.post("/api/v1/accounts/SYSTEM_DEFAULT:reassign-trades")
        assert resp.status_code == 403
        assert "detail" in resp.json()

    def test_reassign_missing_returns_404(self, client) -> None:
        http, svc = client
        svc.reassign_trades_and_delete.side_effect = NotFoundError("Not found")
        resp = http.post("/api/v1/accounts/MISSING:reassign-trades")
        assert resp.status_code == 404
        assert "detail" in resp.json()


class TestCreateAccountAutoId:
    """AC-13: account_id is optional (auto-assigned)."""

    def test_create_without_account_id(self, client) -> None:
        """AC-13: POST /accounts without account_id generates one."""
        http, svc = client
        svc.create_account.return_value = _sample_account(account_id="auto-123")
        svc.get_latest_balance.return_value = None

        resp = http.post(
            "/api/v1/accounts",
            json={"name": "Auto Account", "account_type": "BROKER"},
        )
        assert resp.status_code == 201
        svc.create_account.assert_called_once()
        cmd = svc.create_account.call_args[0][0]
        assert cmd.account_id  # auto-generated, not empty


class TestUpdateSystemGuard:
    """AC-6: PUT on system account returns 403."""

    def test_update_system_returns_403(self, client) -> None:
        """AC-6: PUT on system account returns 403."""
        from zorivest_core.domain.exceptions import ForbiddenError

        http, svc = client
        svc.update_account.side_effect = ForbiddenError("Cannot modify system account")
        resp = http.put("/api/v1/accounts/SYSTEM_DEFAULT", json={"name": "Hacked"})
        assert resp.status_code == 403
        assert "detail" in resp.json()
        assert "system" in resp.json()["detail"].lower()


class TestListAccountFiltering:
    """AC-4, AC-5: include_archived/include_system query params."""

    def test_list_passes_include_archived(self, client) -> None:
        """AC-4: include_archived=true passes through to service."""
        http, svc = client
        svc.list_accounts.return_value = []
        resp = http.get("/api/v1/accounts?include_archived=true")
        assert resp.status_code == 200
        svc.list_accounts.assert_called_once()
        call_kwargs = svc.list_accounts.call_args[1]
        assert call_kwargs["include_archived"] is True

    def test_list_passes_include_system(self, client) -> None:
        """AC-5: include_system=true passes through to service."""
        http, svc = client
        svc.list_accounts.return_value = []
        resp = http.get("/api/v1/accounts?include_system=true")
        assert resp.status_code == 200
        call_kwargs = svc.list_accounts.call_args[1]
        assert call_kwargs["include_system"] is True

    def test_list_defaults_exclude_both(self, client) -> None:
        """AC-4, AC-5: defaults exclude archived and system."""
        http, svc = client
        svc.list_accounts.return_value = []
        resp = http.get("/api/v1/accounts")
        assert resp.status_code == 200
        call_kwargs = svc.list_accounts.call_args[1]
        assert call_kwargs["include_archived"] is False
        assert call_kwargs["include_system"] is False


class TestAccountResponseMetrics:
    """AC-12: GET /accounts/{id} includes metrics."""

    def test_get_account_includes_metrics(self, client) -> None:
        """AC-12: GET single account response includes computed metrics."""
        http, svc = client
        svc.get_account.return_value = _sample_account()
        svc.get_latest_balance.return_value = None
        svc.get_account_metrics.return_value = {
            "trade_count": 10,
            "round_trip_count": 5,
            "win_rate": 60.0,
            "total_realized_pnl": 1500.50,
        }

        resp = http.get("/api/v1/accounts/ACC001")
        assert resp.status_code == 200
        data = resp.json()
        assert data["trade_count"] == 10
        assert data["round_trip_count"] == 5
        assert data["win_rate"] == 60.0
        assert data["total_realized_pnl"] == 1500.50

    def test_get_account_includes_archived_system_flags(self, client) -> None:
        """AC-1, AC-2: Response includes is_archived, is_system."""
        http, svc = client
        svc.get_account.return_value = _sample_account(
            is_archived=True, is_system=False
        )
        svc.get_latest_balance.return_value = None
        svc.get_account_metrics.return_value = {
            "trade_count": 0,
            "round_trip_count": 0,
            "win_rate": 0.0,
            "total_realized_pnl": 0.0,
        }

        resp = http.get("/api/v1/accounts/ACC001")
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_archived"] is True
        assert data["is_system"] is False


# ── MEU-BV1: Boundary Validation — Account Input Hardening ──────────────


class TestCreateAccountBoundaryValidation:
    """BV1-AC-1,AC-2,AC-3: Schema-level rejection of invalid create input."""

    def test_invalid_account_type_returns_422(self, client) -> None:
        """BV1-AC-1: Invalid account_type enum value is rejected at schema level."""
        http, svc = client
        resp = http.post(
            "/api/v1/accounts",
            json={
                "name": "Test Account",
                "account_type": "INVALID_TYPE",
                "institution": "Test",
            },
        )
        assert resp.status_code == 422

    def test_blank_name_returns_422(self, client) -> None:
        """BV1-AC-2: Empty name string is rejected at schema level."""
        http, svc = client
        resp = http.post(
            "/api/v1/accounts",
            json={
                "name": "",
                "account_type": "broker",
                "institution": "Test",
            },
        )
        assert resp.status_code == 422

    def test_extra_field_on_create_returns_422(self, client) -> None:
        """BV1-AC-3: Unknown extra fields rejected by extra='forbid'."""
        http, svc = client
        resp = http.post(
            "/api/v1/accounts",
            json={
                "name": "Test Account",
                "account_type": "broker",
                "institution": "Test",
                "unexpected_field": "should_reject",
            },
        )
        assert resp.status_code == 422


class TestUpdateAccountBoundaryValidation:
    """BV1-AC-3,AC-4,AC-5: Schema-level rejection of invalid update input."""

    def test_invalid_account_type_on_update_returns_422(self, client) -> None:
        """BV1-AC-4: Invalid account_type enum on update is rejected."""
        http, svc = client
        resp = http.put(
            "/api/v1/accounts/ACC001",
            json={"account_type": "INVALID_TYPE"},
        )
        assert resp.status_code == 422

    def test_blank_name_on_update_returns_422(self, client) -> None:
        """BV1-AC-5: Blank name on update rejected (create/update parity)."""
        http, svc = client
        resp = http.put(
            "/api/v1/accounts/ACC001",
            json={"name": ""},
        )
        assert resp.status_code == 422

    def test_extra_field_on_update_returns_422(self, client) -> None:
        """BV1-AC-3: Unknown extra fields rejected on update."""
        http, svc = client
        resp = http.put(
            "/api/v1/accounts/ACC001",
            json={"unexpected_field": "should_reject"},
        )
        assert resp.status_code == 422


class TestWhitespaceOnlyAccountValidation:
    """F1/F5 fix: Whitespace-only strings must be rejected, not just empty strings."""

    def test_whitespace_name_on_create_returns_422(self, client) -> None:
        """Whitespace-only name is stripped to '' and rejected by min_length=1."""
        http, svc = client
        resp = http.post(
            "/api/v1/accounts",
            json={
                "name": "   ",
                "account_type": "broker",
                "institution": "Test",
            },
        )
        assert resp.status_code == 422

    def test_whitespace_name_on_update_returns_422(self, client) -> None:
        """Whitespace-only name on update is stripped to '' and rejected."""
        http, svc = client
        resp = http.put(
            "/api/v1/accounts/ACC001",
            json={"name": "   "},
        )
        assert resp.status_code == 422
