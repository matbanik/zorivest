# tests/unit/test_api_system.py
"""Tests for MEU-30: System & Infrastructure API routes.

Red phase — written FIRST per TDD protocol.
FIC Acceptance Criteria: AC-1..AC-14.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from zorivest_api.main import create_app


# ── Helper: unlocked client with auth ────────────────────────────────


def _make_authed_client():
    """Create app, unlock DB, get session token, return (client, token)."""
    app = create_app()
    with TestClient(app, raise_server_exceptions=False) as client:
        # Create key + unlock
        key_resp = client.post("/api/v1/auth/keys", json={"name": "test"})
        raw_key = key_resp.json()["raw_key"]
        unlock_resp = client.post("/api/v1/auth/unlock", json={"api_key": raw_key})
        token = unlock_resp.json()["session_token"]
        yield client, token


# ── Fixtures ─────────────────────────────────────────────────────────


@pytest.fixture()
def client():
    """Unlocked client (no auth headers)."""
    app = create_app()
    with TestClient(app, raise_server_exceptions=False) as c:
        app.state.db_unlocked = True
        app.state.start_time = __import__("time").time()
        yield c


@pytest.fixture()
def authed_client():
    """Unlocked client WITH auth session token."""
    yield from _make_authed_client()


@pytest.fixture()
def locked_client():
    """Locked client (no unlock)."""
    app = create_app()
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


# ── AC-1, AC-2: POST /api/v1/logs ───────────────────────────────────


class TestLogIngestion:
    def test_log_ingest_returns_204(self, client: TestClient) -> None:
        """AC-1: POST /api/v1/logs returns 204."""
        resp = client.post("/api/v1/logs", json={
            "level": "info",
            "component": "startup",
            "message": "App started",
        })
        assert resp.status_code == 204

    def test_log_entry_schema(self, client: TestClient) -> None:
        """AC-2: LogEntry accepts {level, component, message, data}."""
        resp = client.post("/api/v1/logs", json={
            "level": "error",
            "component": "renderer",
            "message": "Failed to render",
            "data": {"error_code": 42},
        })
        assert resp.status_code == 204

    def test_log_default_level(self, client: TestClient) -> None:
        """AC-2: LogEntry defaults to level='info' and component='unknown'."""
        resp = client.post("/api/v1/logs", json={"message": "test"})
        assert resp.status_code == 204

    def test_log_no_auth_required(self, locked_client: TestClient) -> None:
        """Logs available pre-unlock (no auth required)."""
        resp = locked_client.post("/api/v1/logs", json={"message": "test"})
        assert resp.status_code == 204


# ── AC-3: GET /api/v1/mcp-guard/status ───────────────────────────────


class TestMcpGuardStatus:
    def test_guard_status_returns_defaults(self, client: TestClient) -> None:
        """AC-3: GET /mcp-guard/status returns is_enabled=False, is_locked=False."""
        resp = client.get("/api/v1/mcp-guard/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_enabled"] is False
        assert data["is_locked"] is False

    def test_guard_status_pre_unlock(self, locked_client: TestClient) -> None:
        """AC-3: Guard status available pre-unlock."""
        resp = locked_client.get("/api/v1/mcp-guard/status")
        assert resp.status_code == 200


# ── AC-4: PUT /api/v1/mcp-guard/config ───────────────────────────────


class TestMcpGuardConfig:
    def test_config_update(self, client: TestClient) -> None:
        """AC-4: PUT config updates thresholds."""
        resp = client.put("/api/v1/mcp-guard/config", json={"calls_per_minute_limit": 30})
        assert resp.status_code == 200
        data = resp.json()
        assert data["calls_per_minute_limit"] == 30


# ── AC-5, AC-6: POST lock/unlock ────────────────────────────────────


class TestMcpGuardLockUnlock:
    def test_lock_sets_locked(self, client: TestClient) -> None:
        """AC-5: POST /lock sets locked=True with reason."""
        resp = client.post("/api/v1/mcp-guard/lock", json={"reason": "test"})
        assert resp.status_code == 200
        assert resp.json()["is_locked"] is True
        assert resp.json()["lock_reason"] == "test"

    def test_unlock_clears_locked(self, client: TestClient) -> None:
        """AC-6: POST /unlock sets locked=False."""
        client.post("/api/v1/mcp-guard/lock", json={"reason": "test"})
        resp = client.post("/api/v1/mcp-guard/unlock")
        assert resp.status_code == 200
        assert resp.json()["is_locked"] is False


# ── AC-7: POST /api/v1/mcp-guard/check ──────────────────────────────


class TestMcpGuardCheck:
    def test_check_allowed_when_disabled(self, client: TestClient) -> None:
        """AC-7: Guard disabled → check returns allowed=true."""
        resp = client.post("/api/v1/mcp-guard/check")
        assert resp.status_code == 200
        assert resp.json()["allowed"] is True

    def test_check_auto_locks_on_threshold(self, client: TestClient) -> None:
        """AC-7: Enable guard with limit=2, third call auto-locks."""
        client.put("/api/v1/mcp-guard/config", json={
            "is_enabled": True,
            "calls_per_minute_limit": 2,
        })
        assert client.post("/api/v1/mcp-guard/check").json()["allowed"] is True
        assert client.post("/api/v1/mcp-guard/check").json()["allowed"] is True
        result = client.post("/api/v1/mcp-guard/check").json()
        assert result["allowed"] is False
        assert result["reason"] == "rate_limit_exceeded"
        # Verify status reflects the lock
        status = client.get("/api/v1/mcp-guard/status").json()
        assert status["is_locked"] is True
        assert status["lock_reason"] == "rate_limit_exceeded"


# ── AC-8: Guard mutation routes require unlocked DB ──────────────────


class TestMcpGuardAuth:
    def test_mutation_routes_require_unlock(self, locked_client: TestClient) -> None:
        """AC-8: Config/lock/unlock/check require unlocked DB → 403."""
        assert locked_client.put("/api/v1/mcp-guard/config", json={}).status_code == 403
        assert locked_client.post("/api/v1/mcp-guard/lock", json={}).status_code == 403
        assert locked_client.post("/api/v1/mcp-guard/unlock").status_code == 403
        assert locked_client.post("/api/v1/mcp-guard/check").status_code == 403


# ── AC-9: GET /api/v1/service/status ─────────────────────────────────


class TestServiceStatus:
    def test_service_status_returns_pid(self, authed_client) -> None:
        """AC-9: GET /service/status returns PID, uptime, etc. Requires auth."""
        client, token = authed_client
        resp = client.get(
            "/api/v1/service/status",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["pid"] > 0
        assert "uptime_seconds" in data
        assert "python_version" in data

    def test_service_status_requires_auth(self, client: TestClient) -> None:
        """AC-9: GET /service/status returns 403 without auth."""
        resp = client.get("/api/v1/service/status")
        assert resp.status_code == 403


# ── AC-10: POST /api/v1/service/graceful-shutdown ────────────────────


class TestGracefulShutdown:
    def test_graceful_shutdown_returns_202(self, authed_client) -> None:
        """AC-10: POST /service/graceful-shutdown returns 202 with admin.
        Mock _shutdown_process to prevent real SIGINT from killing pytest."""
        from unittest.mock import patch
        client, token = authed_client
        with patch("zorivest_api.routes.service._shutdown_process"):
            resp = client.post(
                "/api/v1/service/graceful-shutdown",
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == 202
        assert resp.json()["status"] == "shutdown_initiated"

    def test_graceful_shutdown_requires_admin(self, client: TestClient) -> None:
        """AC-10: POST /service/graceful-shutdown returns 403 without admin."""
        resp = client.post("/api/v1/service/graceful-shutdown")
        assert resp.status_code == 403


# ── AC-12: Router tags ──────────────────────────────────────────────


class TestSystemTags:
    def test_log_router_tag(self) -> None:
        """AC-12: Log router uses tag 'system'."""
        from zorivest_api.routes.logs import log_router
        assert "system" in (log_router.tags or [])

    def test_guard_router_tag(self) -> None:
        """AC-12: Guard router uses tag 'mcp-guard'."""
        from zorivest_api.routes.mcp_guard import guard_router
        assert "mcp-guard" in (guard_router.tags or [])

    def test_service_router_tag(self) -> None:
        """AC-12: Service router uses tag 'service'."""
        from zorivest_api.routes.service import service_router
        assert "service" in (service_router.tags or [])


# ── AC-13: Integration test (no overrides) ───────────────────────────


class TestSystemIntegration:
    def test_guard_and_logs_pre_unlock(self) -> None:
        """AC-13: Guard status and log ingest work pre-unlock."""
        app = create_app()
        with TestClient(app, raise_server_exceptions=False) as client:
            # Guard status available pre-unlock
            guard_resp = client.get("/api/v1/mcp-guard/status")
            assert guard_resp.status_code == 200

            # Log ingest works pre-unlock
            log_resp = client.post("/api/v1/logs", json={"message": "test"})
            assert log_resp.status_code == 204
