# tests/unit/test_api_email_settings.py
"""Tests for MEU-73: Email Provider Settings API.

Red phase — written FIRST per TDD protocol.
FIC Acceptance Criteria: AC-E1..AC-E5.
Source: 06f-gui-settings.md §Email Provider
"""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from zorivest_api.dependencies import get_email_provider_service
from zorivest_api.main import create_app


@pytest.fixture()
def mock_svc() -> MagicMock:
    """Mock EmailProviderService for unit isolation."""
    svc = MagicMock()
    svc.get_config.return_value = {
        "provider_preset": "Gmail",
        "smtp_host": "smtp.gmail.com",
        "port": 587,
        "security": "STARTTLS",
        "username": "user@gmail.com",
        "has_password": True,
        "from_email": "user@gmail.com",
    }
    svc.save_config.return_value = None
    svc.test_connection.return_value = {
        "success": True,
        "message": "Connection successful.",
    }
    return svc


@pytest.fixture()
def client(mock_svc: MagicMock) -> Generator[TestClient, None, None]:
    """HTTP test client with dependency override for EmailProviderService."""
    app = create_app()
    app.dependency_overrides[get_email_provider_service] = lambda: mock_svc
    with TestClient(app, raise_server_exceptions=False) as c:
        app.state.db_unlocked = True
        yield c


# ── AC-E1: GET returns has_password bool, never raw password ─────────────


class TestGetEmailConfig:
    def test_get_returns_200(self, client: TestClient) -> None:
        """AC-E1: GET /settings/email returns 200."""
        resp = client.get("/api/v1/settings/email")
        assert resp.status_code == 200

    def test_get_returns_has_password_bool(
        self, client: TestClient, mock_svc: MagicMock
    ) -> None:
        """AC-E1: Response has has_password bool, no raw password field."""
        resp = client.get("/api/v1/settings/email")
        data = resp.json()
        assert "has_password" in data
        assert isinstance(data["has_password"], bool)
        assert "password" not in data
        assert "password_encrypted" not in data

    def test_get_returns_all_fields(self, client: TestClient) -> None:
        """AC-E1: Response contains all 7 config fields."""
        resp = client.get("/api/v1/settings/email")
        data = resp.json()
        for field in (
            "provider_preset",
            "smtp_host",
            "port",
            "security",
            "username",
            "from_email",
        ):
            assert field in data, f"Missing field: {field}"


# ── AC-E5: GET on empty config returns safe defaults (no 500) ────────────


class TestGetEmailConfigEmpty:
    def test_get_with_no_config_returns_200(self, mock_svc: MagicMock) -> None:
        """AC-E5: GET when no config stored returns safe defaults, not 500."""
        mock_svc.get_config.return_value = {
            "provider_preset": None,
            "smtp_host": None,
            "port": None,
            "security": None,
            "username": None,
            "has_password": False,
            "from_email": None,
        }
        app = create_app()
        app.dependency_overrides[get_email_provider_service] = lambda: mock_svc
        with TestClient(app, raise_server_exceptions=False) as c:
            app.state.db_unlocked = True
            resp = c.get("/api/v1/settings/email")
        assert resp.status_code == 200
        assert resp.json()["has_password"] is False


# ── AC-E2: PUT saves all 7 fields ────────────────────────────────────────


class TestSaveEmailConfig:
    def test_put_returns_200(self, client: TestClient) -> None:
        """AC-E2: PUT /settings/email returns 200."""
        resp = client.put(
            "/api/v1/settings/email",
            json={
                "provider_preset": "Gmail",
                "smtp_host": "smtp.gmail.com",
                "port": 587,
                "security": "STARTTLS",
                "username": "user@gmail.com",
                "password": "secret123",
                "from_email": "user@gmail.com",
            },
        )
        assert resp.status_code == 200

    def test_put_calls_save_config_with_all_fields(
        self, client: TestClient, mock_svc: MagicMock
    ) -> None:
        """AC-E2: PUT calls save_config with all 7 fields in the payload."""
        payload = {
            "provider_preset": "Brevo",
            "smtp_host": "smtp-relay.brevo.com",
            "port": 587,
            "security": "STARTTLS",
            "username": "api@brevo.com",
            "password": "api_key_here",
            "from_email": "noreply@example.com",
        }
        client.put("/api/v1/settings/email", json=payload)
        mock_svc.save_config.assert_called_once()
        call_data = mock_svc.save_config.call_args[0][0]
        assert call_data["smtp_host"] == "smtp-relay.brevo.com"
        assert call_data["password"] == "api_key_here"


# ── AC-E3: PUT with empty password keeps existing ────────────────────────


class TestSaveEmailConfigKeepPassword:
    def test_put_with_empty_password_passes_empty_to_service(
        self, client: TestClient, mock_svc: MagicMock
    ) -> None:
        """AC-E3: Empty password string passed through — service handles keep-existing logic."""
        payload = {
            "smtp_host": "smtp.gmail.com",
            "port": 587,
            "password": "",  # empty = keep existing
        }
        client.put("/api/v1/settings/email", json=payload)
        call_data = mock_svc.save_config.call_args[0][0]
        assert call_data["password"] == "" or call_data.get("password") is None


# ── AC-E4: POST /test returns success/message ────────────────────────────


class TestTestEmailConnection:
    def test_test_connection_returns_200_on_success(self, client: TestClient) -> None:
        """AC-E4: POST /settings/email/test returns 200 on success."""
        resp = client.post("/api/v1/settings/email/test")
        assert resp.status_code == 200
        data = resp.json()
        assert "success" in data
        assert "message" in data

    def test_test_connection_returns_422_on_failure(self, mock_svc: MagicMock) -> None:
        """AC-E4: POST /settings/email/test returns 422 on connection failure."""
        mock_svc.test_connection.return_value = {
            "success": False,
            "message": "Auth failed",
        }
        app = create_app()
        app.dependency_overrides[get_email_provider_service] = lambda: mock_svc
        with TestClient(app, raise_server_exceptions=False) as c:
            app.state.db_unlocked = True
            resp = c.post("/api/v1/settings/email/test")
        assert resp.status_code == 422


# ── Mode-gating: 403 when locked ─────────────────────────────────────────


class TestEmailSettingsModeGating:
    def test_email_settings_403_when_locked(self, mock_svc: MagicMock) -> None:
        """Email routes require unlocked DB."""
        app = create_app()
        app.dependency_overrides[get_email_provider_service] = lambda: mock_svc
        with TestClient(app, raise_server_exceptions=False) as c:
            app.state.db_unlocked = False
            for method, path in [
                ("GET", "/api/v1/settings/email"),
                ("PUT", "/api/v1/settings/email"),
                ("POST", "/api/v1/settings/email/test"),
            ]:
                resp = c.request(method, path, json={} if method != "GET" else None)
                assert resp.status_code == 403, (
                    f"{method} {path} should be 403 when locked, got {resp.status_code}"
                )


# ── F3: Real service + repository integration (no mocks) ─────────────────────


class TestEmailServiceIntegration:
    """Integration tests using a real SQLite in-memory DB.

    Proves Fernet encryption-at-rest and keep-existing-password without mocks.
    Source: AC-E2, AC-E3; finding F3 from implementation critical review.
    """

    def _make_service(self):
        """Build a real EmailProviderService wired to an in-memory SQLite engine."""
        from unittest.mock import MagicMock

        from cryptography.fernet import Fernet
        from sqlalchemy import create_engine
        from sqlalchemy.orm import Session

        from zorivest_core.services.email_provider_service import EmailProviderService
        from zorivest_infra.database.email_provider_repository import (
            SqlAlchemyEmailProviderRepository,
        )
        from zorivest_infra.database.models import Base

        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        session = Session(engine)

        repo = SqlAlchemyEmailProviderRepository(session)

        uow = MagicMock()
        uow.__enter__ = lambda s: s
        uow.__exit__ = MagicMock(return_value=False)
        uow.email_provider = repo
        uow.commit = session.commit

        key = Fernet.generate_key()
        encryption = MagicMock()
        encryption._fernet = Fernet(key)

        return EmailProviderService(uow=uow, encryption=encryption), session

    def test_fernet_encryption_at_rest(self) -> None:
        """AC-E2: Password stored as Fernet ciphertext — never plaintext.

        Reads the raw bytes from the DB row directly and asserts:
        1. Something is stored (row.password_encrypted is not None/empty)
        2. Stored bytes differ from the UTF-8 plaintext
        3. Stored bytes are a valid Fernet token (starts with b'gAAA')
        """
        from zorivest_infra.database.models import EmailProviderModel

        svc, session = self._make_service()
        svc.save_config(
            {
                "provider_preset": "Gmail",
                "smtp_host": "smtp.gmail.com",
                "port": 587,
                "security": "STARTTLS",
                "username": "user@test.com",
                "password": "plaintext-secret",
                "from_email": "user@test.com",
            }
        )
        # Read the raw row directly from the DB session
        row = session.get(EmailProviderModel, 1)
        assert row is not None, "Row must exist after save_config"
        stored = bytes(row.password_encrypted)  # type: ignore[arg-type]
        assert stored, "password_encrypted must not be empty"
        assert stored != b"plaintext-secret", "Password must not be stored in plaintext"
        assert stored.startswith(b"gAAA"), "Stored value must be a valid Fernet token"
        # Service-level view: has_password=True, raw password never returned
        config = svc.get_config()
        assert config["has_password"] is True
        assert "password" not in config

    def test_empty_password_keeps_existing(self) -> None:
        """AC-E3: Saving with empty password does not clear the stored credential."""
        svc, _session = self._make_service()
        svc.save_config(
            {
                "smtp_host": "smtp.gmail.com",
                "port": 587,
                "security": "STARTTLS",
                "username": "user@test.com",
                "password": "original-secret",
                "from_email": "user@test.com",
            }
        )
        assert svc.get_config()["has_password"] is True

        svc.save_config(
            {
                "smtp_host": "smtp.gmail.com",
                "port": 587,
                "security": "STARTTLS",
                "username": "user@test.com",
                "password": "",
                "from_email": "user@test.com",
            }
        )
        assert svc.get_config()["has_password"] is True


# ── Boundary validation: EmailConfigRequest ─────────────────────────────


class TestEmailConfigBoundaryValidation:
    """Boundary validation tests for PUT /settings/email.

    Addresses finding F6 from handoff 096 — MEU-BV5.
    """

    def test_extra_field_rejected(self, client: TestClient) -> None:
        """AC-EM1: Unknown fields in EmailConfigRequest → 422."""
        resp = client.put(
            "/api/v1/settings/email",
            json={
                "provider_preset": "Gmail",
                "smtp_host": "smtp.gmail.com",
                "port": 587,
                "security": "STARTTLS",
                "username": "user@gmail.com",
                "password": "secret",
                "from_email": "user@gmail.com",
                "unknown_field": "should-reject",
            },
        )
        assert resp.status_code == 422

    def test_whitespace_only_smtp_host_rejected(self, client: TestClient) -> None:
        """AC-EM2: Whitespace-only smtp_host → 422."""
        resp = client.put(
            "/api/v1/settings/email",
            json={"smtp_host": "   "},
        )
        assert resp.status_code == 422

    def test_whitespace_only_username_rejected(self, client: TestClient) -> None:
        """AC-EM3: Whitespace-only username → 422."""
        resp = client.put(
            "/api/v1/settings/email",
            json={"username": "   "},
        )
        assert resp.status_code == 422

    def test_unknown_provider_preset_rejected(self, client: TestClient) -> None:
        """AC-EM4: Unknown provider_preset → 422 (only Gmail/Brevo/SendGrid/Outlook/Yahoo/Custom)."""
        resp = client.put(
            "/api/v1/settings/email",
            json={"provider_preset": "NotARealPreset"},
        )
        assert resp.status_code == 422

    def test_whitespace_only_from_email_rejected(self, client: TestClient) -> None:
        """AC-EM5: Whitespace-only from_email → 422."""
        resp = client.put(
            "/api/v1/settings/email",
            json={"from_email": "   "},
        )
        assert resp.status_code == 422

    def test_zero_port_rejected(self, client: TestClient) -> None:
        """AC-EM6: port=0 → 422 (must be ≥ 1)."""
        resp = client.put(
            "/api/v1/settings/email",
            json={"port": 0},
        )
        assert resp.status_code == 422

    def test_port_above_65535_rejected(self, client: TestClient) -> None:
        """AC-EM7: port=99999 → 422 (must be ≤ 65535)."""
        resp = client.put(
            "/api/v1/settings/email",
            json={"port": 99999},
        )
        assert resp.status_code == 422

    def test_invalid_security_rejected(self, client: TestClient) -> None:
        """AC-EM8: security='INVALID' → 422 (only STARTTLS/SSL accepted)."""
        resp = client.put(
            "/api/v1/settings/email",
            json={"security": "INVALID"},
        )
        assert resp.status_code == 422

    def test_whitespace_password_accepted(self, client: TestClient) -> None:
        """AC-EM9: password=' ' (whitespace-only) is accepted — not stripped."""
        resp = client.put(
            "/api/v1/settings/email",
            json={"password": " "},
        )
        assert resp.status_code == 200

    def test_valid_full_payload_accepted(self, client: TestClient) -> None:
        """AC-EM10: Valid full payload still accepted → 200 (regression guard)."""
        resp = client.put(
            "/api/v1/settings/email",
            json={
                "provider_preset": "Gmail",
                "smtp_host": "smtp.gmail.com",
                "port": 587,
                "security": "STARTTLS",
                "username": "user@gmail.com",
                "password": "secret123",
                "from_email": "user@gmail.com",
            },
        )
        assert resp.status_code == 200

    def test_whitespace_only_provider_preset_rejected(self, client: TestClient) -> None:
        """AC-EM11: Whitespace-only provider_preset → 422 (not a valid preset)."""
        resp = client.put(
            "/api/v1/settings/email",
            json={"provider_preset": "   "},
        )
        assert resp.status_code == 422
