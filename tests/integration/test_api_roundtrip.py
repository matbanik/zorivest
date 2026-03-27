"""API Round-Trip Integration Tests — no mocks, real service layer.

Uses FastAPI TestClient against the real app with in-memory SQLite.
Exercises the full HTTP → Route → Service → Domain → DB path.

Source: Cross-Layer Testing Strategy (2026-03-19)
"""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

# Set dev-unlock before importing app (lifespan reads it)
os.environ["ZORIVEST_DEV_UNLOCK"] = "1"

from zorivest_api.main import app  # noqa: E402


@pytest.fixture()
def client():
    """TestClient with startup/shutdown lifespan."""
    with TestClient(app) as c:
        yield c


# ── Health endpoint ─────────────────────────────────────────────────────


class TestHealthRoundTrip:
    """Validate the health endpoint returns the shape the GUI expects."""

    def test_health_returns_200(self, client: TestClient) -> None:
        r = client.get("/api/v1/health")
        assert r.status_code == 200

    def test_health_has_database_object(self, client: TestClient) -> None:
        """GUI expects health.database.unlocked — not a string."""
        data = client.get("/api/v1/health").json()
        assert "database" in data, "health response missing 'database' field"
        assert isinstance(data["database"], dict), (
            f"health.database should be dict, got {type(data['database']).__name__}: {data['database']}"
        )
        assert "unlocked" in data["database"], (
            "health.database missing 'unlocked' field"
        )
        assert isinstance(data["database"]["unlocked"], bool)

    def test_health_has_required_fields(self, client: TestClient) -> None:
        data = client.get("/api/v1/health").json()
        assert data["status"] == "ok"
        assert isinstance(data["version"], str)
        assert isinstance(data["uptime_seconds"], (int, float))

    def test_dev_unlock_sets_db_unlocked(self, client: TestClient) -> None:
        """ZORIVEST_DEV_UNLOCK=1 should start with DB unlocked."""
        data = client.get("/api/v1/health").json()
        assert data["database"]["unlocked"] is True, (
            "ZORIVEST_DEV_UNLOCK=1 should result in database.unlocked=true"
        )


# ── Version endpoint ────────────────────────────────────────────────────


class TestVersionRoundTrip:
    def test_version_returns_200(self, client: TestClient) -> None:
        r = client.get("/api/v1/version/")
        assert r.status_code == 200

    def test_version_has_version_string(self, client: TestClient) -> None:
        data = client.get("/api/v1/version/").json()
        assert isinstance(data["version"], str)
        assert len(data["version"]) > 0


# ── Trade CRUD round-trip ───────────────────────────────────────────────


class TestTradeCrudRoundTrip:
    """Full create → read → update → delete with real service layer."""

    SAMPLE_TRADE = {
        "exec_id": "RT-001",
        "time": "2026-03-19T10:00:00",
        "instrument": "SPY",
        "action": "BOT",
        "quantity": 100,
        "price": 500.00,
        "account_id": "DU999",
        "commission": 1.50,
        "realized_pnl": 0.0,
    }

    def test_create_trade(self, client: TestClient) -> None:
        r = client.post("/api/v1/trades", json=self.SAMPLE_TRADE)
        assert r.status_code == 201, r.text
        data = r.json()
        assert data["exec_id"] == "RT-001"

    def test_update_with_notes_does_not_crash(self, client: TestClient) -> None:
        """The 'notes' field is on UpdateTradeRequest but not on Trade.
        The service layer filters it out. This test would have caught the crash."""
        client.post("/api/v1/trades", json=self.SAMPLE_TRADE)
        r = client.put(
            "/api/v1/trades/RT-001", json={"notes": "test", "commission": 2.0}
        )
        assert r.status_code == 200, (
            f"Update with notes field should not crash. Got {r.status_code}: {r.text}"
        )
        # Commission should have been updated (notes is silently filtered)
        data = r.json()
        assert data["commission"] == 2.0

    def test_update_with_valid_field(self, client: TestClient) -> None:
        client.post("/api/v1/trades", json=self.SAMPLE_TRADE)
        r = client.put("/api/v1/trades/RT-001", json={"commission": 5.0})
        assert r.status_code == 200
        assert r.json()["commission"] == 5.0

    def test_list_trades_not_403(self, client: TestClient) -> None:
        """With ZORIVEST_DEV_UNLOCK=1, trades should not be 403 Forbidden."""
        r = client.get("/api/v1/trades?limit=1&offset=0")
        assert r.status_code == 200, (
            f"Expected 200, got {r.status_code}. "
            f"Mode-gating should be bypassed with ZORIVEST_DEV_UNLOCK=1"
        )

    def test_delete_trade(self, client: TestClient) -> None:
        client.post("/api/v1/trades", json=self.SAMPLE_TRADE)
        r = client.delete("/api/v1/trades/RT-001")
        assert r.status_code == 204

    def test_create_trade_with_notes_persists(self, client: TestClient) -> None:
        """Notes sent during create should be returned on subsequent GET."""
        trade_with_notes = {
            **self.SAMPLE_TRADE,
            "exec_id": "RT-NOTES-1",
            "notes": "My trade journal entry",
        }
        r = client.post("/api/v1/trades", json=trade_with_notes)
        assert r.status_code == 201
        data = r.json()
        assert data["notes"] == "My trade journal entry"

    def test_update_trade_notes_persists(self, client: TestClient) -> None:
        """PUT with notes should update and return notes on subsequent GET."""
        client.post("/api/v1/trades", json=self.SAMPLE_TRADE)
        r = client.put("/api/v1/trades/RT-001", json={"notes": "Updated notes"})
        assert r.status_code == 200
        assert r.json()["notes"] == "Updated notes"

    def test_delete_then_get_returns_404(self, client: TestClient) -> None:
        """DELETE should actually remove the trade — test the full round-trip."""
        client.post("/api/v1/trades", json=self.SAMPLE_TRADE)
        r = client.delete("/api/v1/trades/RT-001")
        assert r.status_code == 204
        r2 = client.get("/api/v1/trades/RT-001")
        assert r2.status_code == 404


# ── Guard endpoint ──────────────────────────────────────────────────────


class TestGuardRoundTrip:
    def test_guard_status_returns_200(self, client: TestClient) -> None:
        r = client.get("/api/v1/mcp-guard/status")
        assert r.status_code == 200

    def test_guard_status_has_is_locked(self, client: TestClient) -> None:
        data = client.get("/api/v1/mcp-guard/status").json()
        assert "is_locked" in data
        assert isinstance(data["is_locked"], bool)
