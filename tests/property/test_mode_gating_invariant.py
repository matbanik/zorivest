"""Property-based tests for MCP Guard mode-gating invariant.

Invariant: When the MCP Guard is locked, ALL mutation endpoints return
blocked status, regardless of tool name or payload.

Source: 05-mcp-server.md §5.6 (McpGuard)
Phase:  3.1 of Test Rigor Audit
"""

from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from fastapi.testclient import TestClient

from zorivest_api.main import create_app
from zorivest_api.dependencies import require_unlocked_db, get_guard_service


# ── Stub guard service ──────────────────────────────────────────────────


class StubGuardService:
    """In-memory guard service for testing lock/unlock/check cycle."""

    def __init__(self) -> None:
        self._locked = False
        self._reason: str | None = None

    def get_status(self) -> dict:
        return {
            "is_enabled": True,
            "is_locked": self._locked,
            "locked_at": "2025-01-01T00:00:00" if self._locked else None,
            "lock_reason": self._reason,
            "calls_per_minute_limit": 60,
            "calls_per_hour_limit": 3600,
            "recent_calls_1min": 0,
            "recent_calls_1hr": 0,
        }

    def lock(self, reason: str) -> dict:
        self._locked = True
        self._reason = reason
        return self.get_status()

    def unlock(self) -> dict:
        self._locked = False
        self._reason = None
        return self.get_status()

    def check(self) -> dict:
        if self._locked:
            return {"allowed": False, "reason": self._reason or "locked"}
        return {"allowed": True}

    def update_config(self, updates: dict) -> dict:
        return self.get_status()


# ── Fixtures ────────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def guard_service():
    """Shared StubGuardService instance."""
    return StubGuardService()


@pytest.fixture(scope="module")
def client(guard_service):
    """TestClient with dependency overrides for guard testing."""
    app = create_app()
    app.dependency_overrides[require_unlocked_db] = lambda: None
    app.dependency_overrides[get_guard_service] = lambda: guard_service
    return TestClient(app)


# ── Strategies ──────────────────────────────────────────────────────────

# Arbitrary tool names to ensure the guard doesn't whitelist any
tool_name_strat = st.text(
    alphabet=st.sampled_from("abcdefghijklmnopqrstuvwxyz_"),
    min_size=1,
    max_size=50,
)


# ── Invariants ──────────────────────────────────────────────────────────


class TestModeGatingInvariant:
    """Guard MUST block ALL mutations when locked."""

    def _lock_guard(self, client: TestClient) -> None:
        resp = client.post(
            "/api/v1/mcp-guard/lock",
            json={"reason": "property-test"},
        )
        assert resp.status_code == 200

    def _unlock_guard(self, client: TestClient) -> None:
        resp = client.post("/api/v1/mcp-guard/unlock")
        assert resp.status_code == 200

    @given(tool_name=tool_name_strat)
    @settings(max_examples=50)
    def test_locked_guard_blocks_any_tool(self, client, tool_name):
        """POST /mcp-guard/check returns allowed=false for any tool when locked."""
        self._lock_guard(client)
        try:
            resp = client.post("/api/v1/mcp-guard/check")
            assert resp.status_code == 200
            body = resp.json()
            assert body["allowed"] is False
        finally:
            self._unlock_guard(client)

    @given(tool_name=tool_name_strat)
    @settings(max_examples=50)
    def test_unlocked_guard_allows_any_tool(self, client, tool_name):
        """POST /mcp-guard/check returns allowed=true for any tool when unlocked."""
        self._unlock_guard(client)
        resp = client.post("/api/v1/mcp-guard/check")
        assert resp.status_code == 200
        body = resp.json()
        assert body["allowed"] is True

    def test_lock_unlock_toggle(self, client):
        """Lock → check (blocked) → unlock → check (allowed) cycle."""
        self._lock_guard(client)
        check1 = client.post("/api/v1/mcp-guard/check").json()
        assert check1["allowed"] is False

        self._unlock_guard(client)
        check2 = client.post("/api/v1/mcp-guard/check").json()
        assert check2["allowed"] is True
