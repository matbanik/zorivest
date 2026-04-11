# tests/unit/test_api_config.py
"""Tests for MEU-75: Config Export/Import API routes.

Red phase — written FIRST per TDD protocol.
FIC Acceptance Criteria: AC-1..AC-6.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from zorivest_api.main import create_app


@pytest.fixture()
def client():
    """HTTP test client with lifespan (services initialized)."""
    app = create_app()
    with TestClient(app, raise_server_exceptions=False) as c:
        app.state.db_unlocked = True
        app.state.start_time = __import__("time").time()
        yield c


# ── AC-1: GET /api/v1/config/export ──────────────────────────────────


class TestConfigExport:
    """MEU-75: Config export returns only portable settings."""

    def test_export_returns_200(self, client: TestClient) -> None:
        """AC-1: GET /config/export returns 200."""
        resp = client.get("/api/v1/config/export")
        assert resp.status_code == 200

    def test_export_has_schema_fields(self, client: TestClient) -> None:
        """AC-1: Export response includes config_version, app_version, created_at, settings."""
        resp = client.get("/api/v1/config/export")
        data = resp.json()
        assert "config_version" in data
        assert "app_version" in data
        assert "created_at" in data
        assert "settings" in data
        assert isinstance(data["settings"], dict)

    def test_export_excludes_sensitive(self, client: TestClient) -> None:
        """AC-1: Export omits sensitive settings (e.g. passphrase-related)."""
        resp = client.get("/api/v1/config/export")
        data = resp.json()
        # No key with 'passphrase' or known-sensitive keys should appear
        for key in data["settings"]:
            assert "passphrase" not in key.lower()


# ── AC-2, AC-3: POST /api/v1/config/import ───────────────────────────


class TestConfigImportDryRun:
    """MEU-75: Config import dry-run validates without persisting."""

    def test_dry_run_returns_200(self, client: TestClient) -> None:
        """AC-2: POST /config/import?dry_run=true returns preview."""
        body = {"config_version": 1, "settings": {"ui.theme": "light"}}
        resp = client.post(
            "/api/v1/config/import", params={"dry_run": "true"}, json=body
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "accepted" in data
        assert "rejected" in data
        assert "unknown" in data
        assert data["applied"] is False

    def test_dry_run_categorizes_keys(self, client: TestClient) -> None:
        """AC-2: Dry run correctly categorizes known-portable vs unknown keys."""
        body = {
            "config_version": 1,
            "settings": {
                "ui.theme": "light",  # should be accepted (portable)
                "totally.fake.key": "whatever",  # should be unknown
            },
        }
        resp = client.post(
            "/api/v1/config/import", params={"dry_run": "true"}, json=body
        )
        data = resp.json()
        assert "ui.theme" in data["accepted"]
        assert "totally.fake.key" in data["unknown"]

    def test_dry_run_does_not_persist(self, client: TestClient) -> None:
        """AC-2: Dry run does not change settings."""
        # Ensure current value
        client.put("/api/v1/settings/ui.theme", json={"value": "dark"})
        # Dry-run import with different value
        body = {"config_version": 1, "settings": {"ui.theme": "light"}}
        client.post("/api/v1/config/import", params={"dry_run": "true"}, json=body)
        # Value should still be original
        get_resp = client.get("/api/v1/settings/ui.theme")
        assert get_resp.json()["value"] == "dark"


class TestConfigImportApply:
    """MEU-75: Config import (no dry_run) applies accepted keys."""

    def test_apply_returns_200(self, client: TestClient) -> None:
        """AC-3: POST /config/import without dry_run applies settings."""
        body = {"config_version": 1, "settings": {"ui.theme": "light"}}
        resp = client.post("/api/v1/config/import", json=body)
        assert resp.status_code == 200
        data = resp.json()
        assert data["applied"] is True

    def test_apply_persists_accepted(self, client: TestClient) -> None:
        """AC-3: After apply, accepted settings are persisted."""
        body = {"config_version": 1, "settings": {"ui.theme": "light"}}
        client.post("/api/v1/config/import", json=body)
        get_resp = client.get("/api/v1/settings/ui.theme")
        assert get_resp.json()["value"] == "light"

    def test_apply_ignores_unknown(self, client: TestClient) -> None:
        """AC-3: Unknown keys in import are ignored (not persisted)."""
        body = {"config_version": 1, "settings": {"fake.key.xyz": "val"}}
        resp = client.post("/api/v1/config/import", json=body)
        data = resp.json()
        assert "fake.key.xyz" in data["unknown"]


# ── AC-6: Boundary validation ────────────────────────────────────────


class TestConfigImportBoundary:
    """MEU-75 BIC: extra='forbid' and request shape enforcement."""

    def test_extra_fields_rejected(self, client: TestClient) -> None:
        """AC-6: Extra top-level fields in import body → 422."""
        body = {
            "config_version": 1,
            "settings": {"ui.theme": "light"},
            "sneaky_field": True,
        }
        resp = client.post("/api/v1/config/import", json=body)
        assert resp.status_code == 422

    def test_missing_settings_key(self, client: TestClient) -> None:
        """AC-6: Missing 'settings' key → 422 (required field)."""
        body = {"config_version": 1}
        resp = client.post("/api/v1/config/import", json=body)
        assert resp.status_code == 422


# ── Mode-gating ──────────────────────────────────────────────────────


class TestConfigModeGating:
    def test_export_403_when_locked(self) -> None:
        """Config export is mode-gated."""
        app = create_app()
        app.state.db_unlocked = False
        app.state.start_time = __import__("time").time()
        locked_client = TestClient(app)
        resp = locked_client.get("/api/v1/config/export")
        assert resp.status_code == 403

    def test_import_403_when_locked(self) -> None:
        """Config import is mode-gated."""
        app = create_app()
        app.state.db_unlocked = False
        app.state.start_time = __import__("time").time()
        locked_client = TestClient(app)
        body = {"config_version": 1, "settings": {}}
        resp = locked_client.post("/api/v1/config/import", json=body)
        assert resp.status_code == 403
