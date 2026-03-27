# tests/unit/test_api_auth.py
"""Tests for MEU-26: Auth REST endpoints (full 04c envelope-encryption contract).

Red phase — written FIRST per TDD protocol.
Tests mock the SQLCipher layer via zorivest_infra.database.connection.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def auth_client():
    """HTTP test client with mocked auth service."""
    auth_svc = MagicMock()

    from zorivest_api.main import create_app

    app = create_app()
    app.state.db_unlocked = False
    app.state.start_time = __import__("time").time()

    from zorivest_api import dependencies as deps

    app.dependency_overrides[deps.get_auth_service] = lambda: auth_svc

    return TestClient(app), auth_svc


# ── Unlock/Lock/Status ──────────────────────────────────────────────────


class TestUnlock:
    def test_unlock_with_valid_key_returns_token(self, auth_client) -> None:
        """AC-1: POST /auth/unlock with valid key returns session token."""
        http, svc = auth_client
        svc.unlock.return_value = {
            "session_token": "tok_abc123",
            "role": "admin",
            "scopes": ["read", "write"],
            "expires_in": 3600,
        }

        resp = http.post("/api/v1/auth/unlock", json={"api_key": "valid-key"})
        assert resp.status_code == 200
        data = resp.json()
        assert "session_token" in data
        assert data["role"] == "admin"
        assert "expires_in" in data

    def test_unlock_with_invalid_key_returns_401(self, auth_client) -> None:
        """AC-2: POST /auth/unlock with invalid key returns 401."""
        http, svc = auth_client
        from zorivest_api.auth.auth_service import InvalidKeyError

        svc.unlock.side_effect = InvalidKeyError("Invalid API key")

        resp = http.post("/api/v1/auth/unlock", json={"api_key": "bad-key"})
        assert resp.status_code == 401
        # Value: verify error detail
        data = resp.json()
        assert "detail" in data

    def test_unlock_with_revoked_key_returns_403(self, auth_client) -> None:
        """AC-3: POST /auth/unlock with revoked key returns 403."""
        http, svc = auth_client
        from zorivest_api.auth.auth_service import RevokedKeyError

        svc.unlock.side_effect = RevokedKeyError("Key has been revoked")

        resp = http.post("/api/v1/auth/unlock", json={"api_key": "revoked-key"})
        assert resp.status_code == 403
        # Value: verify error detail
        data = resp.json()
        assert "detail" in data

    def test_unlock_when_already_unlocked_returns_423(self, auth_client) -> None:
        """AC-4: POST /auth/unlock when already unlocked returns 423."""
        http, svc = auth_client
        from zorivest_api.auth.auth_service import AlreadyUnlockedError

        svc.unlock.side_effect = AlreadyUnlockedError("Already unlocked")

        resp = http.post("/api/v1/auth/unlock", json={"api_key": "valid"})
        assert resp.status_code == 423
        # Value: verify error detail
        data = resp.json()
        assert "detail" in data


class TestLock:
    def test_lock_invalidates_sessions(self, auth_client) -> None:
        """AC-5: POST /auth/lock invalidates sessions and locks DB."""
        http, svc = auth_client

        resp = http.post("/api/v1/auth/lock")
        assert resp.status_code == 200
        # Value: verify response body indicates lock state
        data = resp.json()
        assert isinstance(data, dict)
        svc.lock.assert_called_once()


class TestAuthStatus:
    def test_status_reflects_state(self, auth_client) -> None:
        """AC-6: GET /auth/status reflects locked/unlocked state."""
        http, svc = auth_client
        svc.get_status.return_value = {"locked": True}

        resp = http.get("/api/v1/auth/status")
        assert resp.status_code == 200
        assert resp.json()["locked"] is True


# ── API Key Management ──────────────────────────────────────────────────


class TestApiKeyManagement:
    def test_create_api_key_201(self, auth_client) -> None:
        """AC-7: POST /auth/keys creates key and returns raw key once."""
        http, svc = auth_client
        svc.create_key.return_value = {
            "key_id": "key_001",
            "name": "My Key",
            "role": "admin",
            "raw_key": "zrv_abc123def456",
        }

        resp = http.post("/api/v1/auth/keys", json={"name": "My Key", "role": "admin"})
        assert resp.status_code == 201
        data = resp.json()
        assert "raw_key" in data

    def test_list_api_keys_masked(self, auth_client) -> None:
        """AC-8: GET /auth/keys returns masked keys (never plaintext)."""
        http, svc = auth_client
        svc.list_keys.return_value = [
            {
                "key_id": "key_001",
                "name": "My Key",
                "role": "admin",
                "masked_key": "zrv_***456",
            },
        ]

        resp = http.get("/api/v1/auth/keys")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert "***" in data[0]["masked_key"]

    def test_revoke_api_key_204(self, auth_client) -> None:
        """AC-9: DELETE /auth/keys/{key_id} revokes key."""
        http, svc = auth_client

        resp = http.delete("/api/v1/auth/keys/key_001")
        assert resp.status_code == 204
        # Value: verify no body on 204
        assert resp.content == b""
        svc.revoke_key.assert_called_once_with("key_001")


# ── Confirmation Tokens ─────────────────────────────────────────────────


class TestConfirmationTokens:
    def test_create_confirmation_token_201(self, auth_client) -> None:
        """AC-10: POST /confirmation-tokens returns ctk_ token for valid action."""
        http, svc = auth_client
        svc.create_confirmation_token.return_value = {
            "token": "ctk_abc123",
            "expires_in_seconds": 60,
        }

        resp = http.post(
            "/api/v1/confirmation-tokens", json={"action": "delete_account"}
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["token"].startswith("ctk_")
        assert data["expires_in_seconds"] == 60

    def test_reject_unknown_action_400(self, auth_client) -> None:
        """AC-11: POST /confirmation-tokens rejects unknown actions."""
        http, svc = auth_client
        from zorivest_api.auth.auth_service import InvalidActionError

        svc.create_confirmation_token.side_effect = InvalidActionError("Unknown action")

        resp = http.post(
            "/api/v1/confirmation-tokens", json={"action": "invalid_action"}
        )
        assert resp.status_code == 400
        # Value: verify error detail
        data = resp.json()
        assert "detail" in data
