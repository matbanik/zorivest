"""Account API Round-Trip Integration Tests — no mocks, real service layer.

Uses FastAPI TestClient against the real app with in-memory SQLite.
Exercises the full HTTP → Route → AccountService → Domain → DB path
for account lifecycle operations: CRUD, archive, and reassign.

Source: Codex Review Finding 2 — MEU-37 corrections (2026-04-06)
"""

from __future__ import annotations

import os

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from zorivest_api.main import create_app


@pytest.fixture(scope="module")
def app():
    """Create a fresh app with ZORIVEST_DEV_UNLOCK for this module only.

    Each module gets its own ``create_app()`` instance so that lifespan
    reads the env var at fixture setup — not at import time.  This prevents
    cross-module env var leakage (TEST-ISOLATION-2).
    """
    os.environ["ZORIVEST_DEV_UNLOCK"] = "1"
    _app = create_app()
    yield _app
    os.environ.pop("ZORIVEST_DEV_UNLOCK", None)


@pytest.fixture()
def client(app: FastAPI):
    """TestClient with startup/shutdown lifespan from module's app."""
    with TestClient(app) as c:
        yield c


SAMPLE_ACCOUNT = {
    "name": "Integration Test Account",
    "account_type": "broker",
    "institution": "Test Broker Inc.",
    "currency": "USD",
}


# ── Account CRUD round-trip ────────────────────────────────────────────


class TestAccountCrudRoundTrip:
    """Full create → read → update → list → delete with real service layer."""

    def test_create_account(self, client: TestClient) -> None:
        """POST /accounts creates an account and returns 201."""
        r = client.post("/api/v1/accounts", json=SAMPLE_ACCOUNT)
        assert r.status_code == 201, r.text
        data = r.json()
        assert data["name"] == "Integration Test Account"
        assert data["account_type"] == "broker"
        assert data["institution"] == "Test Broker Inc."
        assert data["is_archived"] is False
        assert data["is_system"] is False

    def test_get_account(self, client: TestClient) -> None:
        """GET /accounts/{id} returns the created account with metrics."""
        r = client.post(
            "/api/v1/accounts", json={**SAMPLE_ACCOUNT, "account_id": "INT-GET-001"}
        )
        assert r.status_code == 201
        account_id = r.json()["account_id"]

        r2 = client.get(f"/api/v1/accounts/{account_id}")
        assert r2.status_code == 200
        data = r2.json()
        assert data["account_id"] == account_id
        assert data["name"] == "Integration Test Account"
        # Metrics should be present (may be zero for new account)
        assert "trade_count" in data

    def test_update_account(self, client: TestClient) -> None:
        """PUT /accounts/{id} updates account fields."""
        r = client.post(
            "/api/v1/accounts", json={**SAMPLE_ACCOUNT, "account_id": "INT-UPD-001"}
        )
        assert r.status_code == 201

        r2 = client.put("/api/v1/accounts/INT-UPD-001", json={"name": "Updated Name"})
        assert r2.status_code == 200
        assert r2.json()["name"] == "Updated Name"

    def test_list_accounts(self, client: TestClient) -> None:
        """GET /accounts returns a list containing seeded system + created accounts."""
        client.post(
            "/api/v1/accounts", json={**SAMPLE_ACCOUNT, "account_id": "INT-LIST-001"}
        )
        r = client.get("/api/v1/accounts")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        # Should have at least the one we just created
        ids = [a["account_id"] for a in data]
        assert "INT-LIST-001" in ids

    def test_delete_empty_account(self, client: TestClient) -> None:
        """DELETE /accounts/{id} succeeds for account with no trades."""
        r = client.post(
            "/api/v1/accounts", json={**SAMPLE_ACCOUNT, "account_id": "INT-DEL-001"}
        )
        assert r.status_code == 201

        r2 = client.delete("/api/v1/accounts/INT-DEL-001")
        assert r2.status_code == 204

        # Verify it's gone
        r3 = client.get("/api/v1/accounts/INT-DEL-001")
        assert r3.status_code == 404

    def test_get_missing_account_returns_404(self, client: TestClient) -> None:
        """GET /accounts/{id} returns 404 for non-existent account."""
        r = client.get("/api/v1/accounts/DOES-NOT-EXIST")
        assert r.status_code == 404
        assert "detail" in r.json()


# ── System account guards ──────────────────────────────────────────────


class TestSystemAccountGuards:
    """Verify system account protection through real service layer."""

    def test_system_account_exists_after_startup(self, client: TestClient) -> None:
        """SYSTEM_DEFAULT should be seeded by lifespan."""
        r = client.get("/api/v1/accounts?include_system=true")
        assert r.status_code == 200
        ids = [a["account_id"] for a in r.json()]
        assert "SYSTEM_DEFAULT" in ids

    def test_system_account_excluded_by_default(self, client: TestClient) -> None:
        """Default listing excludes system accounts."""
        r = client.get("/api/v1/accounts")
        assert r.status_code == 200
        ids = [a["account_id"] for a in r.json()]
        assert "SYSTEM_DEFAULT" not in ids

    def test_update_system_account_returns_403(self, client: TestClient) -> None:
        """PUT on SYSTEM_DEFAULT returns 403 Forbidden."""
        r = client.put("/api/v1/accounts/SYSTEM_DEFAULT", json={"name": "Hacked"})
        assert r.status_code == 403
        assert "detail" in r.json()

    def test_delete_system_account_returns_403(self, client: TestClient) -> None:
        """DELETE on SYSTEM_DEFAULT returns 403 Forbidden."""
        r = client.delete("/api/v1/accounts/SYSTEM_DEFAULT")
        assert r.status_code == 403
        assert "detail" in r.json()


# ── Archive lifecycle ──────────────────────────────────────────────────


class TestArchiveLifecycle:
    """POST :archive soft-deletes, then excluded from default list."""

    def test_archive_account(self, client: TestClient) -> None:
        """Archive → verify excluded from default list → visible with include_archived."""
        r = client.post(
            "/api/v1/accounts", json={**SAMPLE_ACCOUNT, "account_id": "INT-ARC-001"}
        )
        assert r.status_code == 201

        # Archive it
        r2 = client.post("/api/v1/accounts/INT-ARC-001:archive")
        assert r2.status_code == 200
        assert r2.json()["status"] == "archived"

        # Should be excluded from default list
        r3 = client.get("/api/v1/accounts")
        ids = [a["account_id"] for a in r3.json()]
        assert "INT-ARC-001" not in ids

        # Should be visible with include_archived
        r4 = client.get("/api/v1/accounts?include_archived=true")
        ids = [a["account_id"] for a in r4.json()]
        assert "INT-ARC-001" in ids


# ── Reassign trades lifecycle ──────────────────────────────────────────


class TestReassignTradesLifecycle:
    """POST :reassign-trades moves trades to SYSTEM_DEFAULT and deletes account."""

    def test_reassign_empty_account(self, client: TestClient) -> None:
        """Reassign on account with no trades still succeeds (0 trades moved)."""
        r = client.post(
            "/api/v1/accounts", json={**SAMPLE_ACCOUNT, "account_id": "INT-RSN-001"}
        )
        assert r.status_code == 201

        r2 = client.post("/api/v1/accounts/INT-RSN-001:reassign-trades")
        assert r2.status_code == 200
        data = r2.json()
        assert data["trades_reassigned"] == 0
        assert data["account_id"] == "INT-RSN-001"

        # Account should be deleted after reassign
        r3 = client.get("/api/v1/accounts/INT-RSN-001")
        assert r3.status_code == 404


# ── Balance snapshot round-trip ────────────────────────────────────────


class TestBalanceSnapshotRoundTrip:
    """POST /accounts/{id}/balances records and returns balance data."""

    def test_record_balance(self, client: TestClient) -> None:
        """Record a balance snapshot and verify response."""
        r = client.post(
            "/api/v1/accounts", json={**SAMPLE_ACCOUNT, "account_id": "INT-BAL-001"}
        )
        assert r.status_code == 201

        r2 = client.post(
            "/api/v1/accounts/INT-BAL-001/balances",
            json={"balance": 50000.00},
        )
        assert r2.status_code == 201
        data = r2.json()
        assert data["account_id"] == "INT-BAL-001"
        assert data["balance"] == 50000.00

    def test_record_balance_missing_account_returns_404(
        self, client: TestClient
    ) -> None:
        """POST balance for non-existent account returns 404."""
        r = client.post(
            "/api/v1/accounts/MISSING-BAL/balances",
            json={"balance": 1000.00},
        )
        assert r.status_code == 404
        assert "detail" in r.json()
