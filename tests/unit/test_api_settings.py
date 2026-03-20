# tests/unit/test_api_settings.py
"""Tests for MEU-27: Settings API routes.

Red phase — written FIRST per TDD protocol.
FIC Acceptance Criteria: AC-1..AC-10.
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


# ── AC-1: GET /api/v1/settings returns all settings ──────────────────


class TestGetAllSettings:
    def test_get_all_returns_200(self, client: TestClient) -> None:
        """AC-1: GET /api/v1/settings returns 200."""
        resp = client.get("/api/v1/settings")
        assert resp.status_code == 200
        # Value: verify response is a dict
        data = resp.json()
        assert isinstance(data, dict)

    def test_get_all_returns_dict(self, client: TestClient) -> None:
        """AC-1: Response is a key-value dict per 04d spec."""
        resp = client.get("/api/v1/settings")
        data = resp.json()
        assert isinstance(data, dict)
        # Value: verify keys are strings when settings exist
        for key in data:
            assert isinstance(key, str)


# ── AC-2, AC-3: GET /api/v1/settings/{key} ───────────────────────────


class TestGetSettingByKey:
    def test_existing_key_returns_200(self, client: TestClient) -> None:
        """AC-2: GET /{key} returns {key, value, value_type} for existing keys."""
        # First PUT a value so we know a key exists
        client.put("/api/v1/settings", json={"ui.theme": "dark"})
        resp = client.get("/api/v1/settings/ui.theme")
        assert resp.status_code == 200
        data = resp.json()
        assert data["key"] == "ui.theme"
        assert "value" in data
        assert "value_type" in data

    def test_unknown_key_returns_404(self, client: TestClient) -> None:
        """AC-3: GET /{key} returns 404 for unknown keys."""
        resp = client.get("/api/v1/settings/nonexistent.key.xyz")
        assert resp.status_code == 404
        # Value: verify error detail
        data = resp.json()
        assert "detail" in data


# ── AC-4, AC-5, AC-6: PUT /api/v1/settings ───────────────────────────


class TestBulkUpdateSettings:
    def test_valid_update_returns_200(self, client: TestClient) -> None:
        """AC-4: PUT /api/v1/settings with valid data returns {status, count}."""
        resp = client.put("/api/v1/settings", json={"ui.theme": "dark"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "updated"
        assert data["count"] == 1

    def test_invalid_value_returns_422(self, client: TestClient) -> None:
        """AC-5: PUT with invalid values returns 422 with {detail: {errors: dict}}."""
        resp = client.put("/api/v1/settings", json={"logging.rotation_mb": "-5"})
        assert resp.status_code == 422
        data = resp.json()
        assert "detail" in data
        assert "errors" in data["detail"]
        assert "logging.rotation_mb" in data["detail"]["errors"]

    def test_unknown_key_returns_422(self, client: TestClient) -> None:
        """AC-5: PUT with unknown key returns 422."""
        resp = client.put("/api/v1/settings", json={"not.a.real.key": "value"})
        assert resp.status_code == 422
        # Value: verify error shape
        data = resp.json()
        assert "detail" in data

    def test_all_or_nothing(self, client: TestClient) -> None:
        """AC-6: If any key fails validation, no keys are persisted."""
        resp = client.put(
            "/api/v1/settings",
            json={
                "ui.theme": "light",  # valid (different from default 'dark')
                "logging.rotation_mb": "-5",  # invalid (below min)
            },
        )
        assert resp.status_code == 422
        # Valid key should NOT have been persisted — falls back to hardcoded default
        get_resp = client.get("/api/v1/settings/ui.theme")
        assert get_resp.status_code == 200
        assert get_resp.json()["value"] == "dark"  # hardcoded default, not 'light'

    def test_422_per_key_error_shape(self, client: TestClient) -> None:
        """AC-5: 422 errors shape is dict[str, list[str]]."""
        resp = client.put("/api/v1/settings", json={"display.percent_mode": "../hack"})
        assert resp.status_code == 422
        errors = resp.json()["detail"]["errors"]
        assert isinstance(errors, dict)
        for key, msgs in errors.items():
            assert isinstance(key, str)
            assert isinstance(msgs, list)
            assert all(isinstance(m, str) for m in msgs)


# ── AC-7: Settings tag ───────────────────────────────────────────────


class TestSettingsTag:
    def test_settings_tag_on_router(self) -> None:
        """AC-7: Settings router uses tag 'settings'."""
        from zorivest_api.routes.settings import settings_router

        assert any(tag == "settings" for tag in (settings_router.tags or []))


# ── AC-8: Mode-gating ────────────────────────────────────────────────


class TestSettingsModeGating:
    def test_settings_403_when_locked(self) -> None:
        """AC-8: All settings routes gated behind require_unlocked_db."""
        app = create_app()
        app.state.db_unlocked = False
        app.state.start_time = __import__("time").time()
        client = TestClient(app)

        for method, path in [
            ("GET", "/api/v1/settings"),
            ("GET", "/api/v1/settings/ui.theme"),
            ("PUT", "/api/v1/settings"),
        ]:
            resp = client.request(
                method, path, json={"ui.theme": "dark"} if method == "PUT" else None
            )
            assert resp.status_code == 403, (
                f"{method} {path} should be 403 when locked, got {resp.status_code}"
            )
            # Value: verify error detail on locked response
            data = resp.json()
            assert "detail" in data


# ── AC-9: Integration test (Local Canon) ─────────────────────────────


class TestSettingsIntegration:
    def test_no_dependency_overrides(self) -> None:
        """AC-9: Integration test uses create_app() + TestClient with NO dependency overrides."""
        app = create_app()
        with TestClient(app, raise_server_exceptions=False) as client:
            # Unlock first
            key_resp = client.post("/api/v1/auth/keys", json={"name": "test"})
            raw_key = key_resp.json()["raw_key"]
            unlock_resp = client.post("/api/v1/auth/unlock", json={"api_key": raw_key})
            assert unlock_resp.status_code == 200

            # Settings should be accessible after unlock
            resp = client.get("/api/v1/settings")
            assert resp.status_code == 200


# ── AC-10: PUT → GET roundtrip (Local Canon) ─────────────────────────


class TestSettingsRoundtrip:
    def test_put_get_roundtrip(self) -> None:
        """AC-10: PUT → GET roundtrip verified in live app (state persistence)."""
        app = create_app()
        with TestClient(app, raise_server_exceptions=False) as client:
            # Unlock
            key_resp = client.post("/api/v1/auth/keys", json={"name": "test"})
            raw_key = key_resp.json()["raw_key"]
            client.post("/api/v1/auth/unlock", json={"api_key": raw_key})

            # PUT a setting
            put_resp = client.put("/api/v1/settings", json={"ui.theme": "dark"})
            assert put_resp.status_code == 200
            assert put_resp.json()["count"] == 1

            # GET it back by key
            get_resp = client.get("/api/v1/settings/ui.theme")
            assert get_resp.status_code == 200
            assert get_resp.json()["key"] == "ui.theme"

            # GET all should return dict with the key
            all_resp = client.get("/api/v1/settings")
            assert all_resp.status_code == 200
            data = all_resp.json()
            assert isinstance(data, dict)
            assert "ui.theme" in data
            assert data["ui.theme"] == "dark"


# ── T2.5: PUT /api/v1/settings/{key} (single-key write) ─────────────


class TestSettingsPutSingleKey:
    def test_settings_put_single_key(self, client: TestClient) -> None:
        """T2.5: PUT /settings/{key} writes and reads back correctly."""
        resp = client.put(
            "/api/v1/settings/ui.theme",
            json={"value": "light"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "updated"
        assert data["count"] == 1

        # Verify read-back
        get_resp = client.get("/api/v1/settings/ui.theme")
        assert get_resp.status_code == 200
        assert get_resp.json()["value"] == "light"

    def test_settings_put_single_key_validates(self, client: TestClient) -> None:
        """T2.5: PUT /settings/{key} returns 422 on invalid value."""
        resp = client.put(
            "/api/v1/settings/logging.rotation_mb",
            json={"value": "-5"},
        )
        assert resp.status_code == 422
        data = resp.json()
        assert "detail" in data
        assert "errors" in data["detail"]
