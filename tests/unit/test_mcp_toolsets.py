# tests/unit/test_mcp_toolsets.py
"""Tests for MEU-46a: MCP REST Proxy endpoints.

Red phase — written FIRST per TDD protocol.
FIC Acceptance Criteria:
  AC-1:  GET /api/v1/mcp/toolsets returns {toolsets: [...], total_tools}
  AC-1b: GET /api/v1/mcp/diagnostics returns {api_uptime_seconds, api_version}
  AC-2:  McpServerStatusPanel shows numeric tool count (GUI — not tested here)
  AC-3:  Toolset count row displays total count (GUI — not tested here)
  AC-4:  OpenAPI spec regen (T4 validation — not tested here)

Source: [PD-46a], 06f §6f.9 L743
"""

from __future__ import annotations

import time
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from zorivest_api.main import create_app


@pytest.fixture()
def client():
    """HTTP test client with lifespan (services initialized)."""
    app = create_app()
    with TestClient(app, raise_server_exceptions=False) as c:
        app.state.db_unlocked = True
        app.state.start_time = time.time()
        yield c


# ── AC-1: GET /api/v1/mcp/toolsets ───────────────────────────────────


class TestMcpToolsets:
    def test_mcp_toolsets_returns_total_tools(self, client: TestClient) -> None:
        """AC-1: /mcp/toolsets returns valid JSON with total_tools field."""
        resp = client.get("/api/v1/mcp/toolsets")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_tools" in data
        assert isinstance(data["total_tools"], int)
        assert data["total_tools"] > 0
        assert "toolsets" in data
        assert isinstance(data["toolsets"], list)
        assert len(data["toolsets"]) > 0
        # Each toolset should have required fields
        ts = data["toolsets"][0]
        assert "name" in ts
        assert "tool_count" in ts
        assert "always_loaded" in ts


# ── AC-1b: GET /api/v1/mcp/diagnostics ──────────────────────────────


class TestMcpDiagnostics:
    def test_mcp_diagnostics_returns_uptime(self, client: TestClient) -> None:
        """AC-1b: /mcp/diagnostics returns api_uptime_seconds as positive number."""
        resp = client.get("/api/v1/mcp/diagnostics")
        assert resp.status_code == 200
        data = resp.json()
        assert "api_uptime_seconds" in data
        assert isinstance(data["api_uptime_seconds"], (int, float))
        assert data["api_uptime_seconds"] >= 0
        assert "api_version" in data
        assert isinstance(data["api_version"], str)


# ── Graceful fallback ────────────────────────────────────────────────


class TestMcpToolsetsGracefulFallback:
    def test_mcp_toolsets_graceful_when_manifest_missing(self) -> None:
        """Toolsets endpoint returns fallback zeros when manifest file is missing.

        Patches _MANIFEST_PATH to a non-existent file and clears the module
        cache so _load_manifest actually hits the FileNotFoundError path.
        """
        import zorivest_api.routes.mcp_toolsets as mod

        fake_path = Path("/nonexistent/zorivest-tools.json")

        app = create_app()
        with TestClient(app, raise_server_exceptions=False) as c:
            app.state.db_unlocked = True
            app.state.start_time = time.time()

            # Patch the path AND clear the module-level cache
            with (
                patch.object(mod, "_MANIFEST_PATH", fake_path),
                patch.object(mod, "_manifest_data", None),
            ):
                resp = c.get("/api/v1/mcp/toolsets")

            assert resp.status_code == 200
            data = resp.json()
            # Fallback returns zero counts
            assert data["total_tools"] == 0
            assert data["toolset_count"] == 0
            assert data["toolsets"] == []
