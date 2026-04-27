"""Tests for GET /settings/email/status endpoint (AC-20).

Source: 09g §9G.2c L255
MEU: PH12 (mcp-scheduling-gap)

The status endpoint provides a minimal readiness check for MCP tools
without exposing SMTP credentials (username, password, port, security).
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.unit


@pytest.fixture()
def email_svc_configured() -> MagicMock:
    """Mock email service with SMTP configured."""
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
    return svc


@pytest.fixture()
def email_svc_unconfigured() -> MagicMock:
    """Mock email service with no SMTP configured."""
    svc = MagicMock()
    svc.get_config.return_value = {
        "provider_preset": None,
        "smtp_host": None,
        "port": None,
        "security": None,
        "username": None,
        "has_password": False,
        "from_email": None,
    }
    return svc


def _make_client(email_svc: Any) -> TestClient:
    """Build test client with email service override."""
    from zorivest_api.main import create_app
    from zorivest_api.dependencies import (
        get_email_provider_service,
        require_unlocked_db,
    )

    app = create_app()
    app.state.db_unlocked = True
    app.state.start_time = __import__("time").time()

    app.dependency_overrides[require_unlocked_db] = lambda: None
    app.dependency_overrides[get_email_provider_service] = lambda: email_svc

    # PH11: bypass CSRF token validation
    from zorivest_api.middleware.approval_token import validate_approval_token

    app.dependency_overrides[validate_approval_token] = lambda: None

    return TestClient(app)


class TestEmailStatusEndpoint:
    """AC-20: GET /settings/email/status returns readiness without credentials."""

    def test_configured_returns_correct_shape(
        self, email_svc_configured: MagicMock
    ) -> None:
        """AC-20: configured SMTP → {configured: true, provider: "Gmail", host: "smtp.gmail.com"}."""
        client = _make_client(email_svc_configured)
        resp = client.get("/api/v1/settings/email/status")
        assert resp.status_code == 200

        data = resp.json()
        assert data["configured"] is True
        assert data["provider"] == "Gmail"
        assert data["host"] == "smtp.gmail.com"

        # Must NOT contain credentials
        assert "password" not in data
        assert "username" not in data
        assert "port" not in data
        assert "security" not in data

    def test_unconfigured_returns_false(
        self, email_svc_unconfigured: MagicMock
    ) -> None:
        """AC-20: unconfigured SMTP → {configured: false, provider: null, host: null}."""
        client = _make_client(email_svc_unconfigured)
        resp = client.get("/api/v1/settings/email/status")
        assert resp.status_code == 200

        data = resp.json()
        assert data["configured"] is False
        assert data["provider"] is None
        assert data["host"] is None
