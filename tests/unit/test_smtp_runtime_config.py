"""Unit tests for EmailProviderService.get_smtp_runtime_config() (MEU-PW1).

AC-3: get_smtp_runtime_config() returns dict with host, port, sender,
      username, password keys — performing internal key remapping from
      the ORM model (smtp_host → host, from_email → sender) and
      Fernet password decryption.

Source: docs/execution/plans/2026-04-12-pipeline-runtime-wiring/implementation-plan.md
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

from zorivest_core.services.email_provider_service import EmailProviderService


def _make_service(
    *,
    row: Any | None = None,
) -> EmailProviderService:
    """Create EmailProviderService with mocked UoW and encryption."""
    uow = MagicMock()
    encryption = MagicMock()

    # Wire repo mock: uow.email_provider.get() returns `row`
    repo_mock = MagicMock()
    repo_mock.get.return_value = row
    uow.email_provider = repo_mock

    # Make UoW context-manageable
    uow.__enter__ = MagicMock(return_value=uow)
    uow.__exit__ = MagicMock(return_value=False)

    svc = EmailProviderService(uow=uow, encryption=encryption)
    return svc


def _make_row(
    *,
    smtp_host: str = "smtp.example.com",
    port: int = 587,
    security: str = "STARTTLS",
    username: str = "user@example.com",
    from_email: str | None = "reports@example.com",
    password_encrypted: bytes | None = b"encrypted-bytes",
) -> MagicMock:
    """Create a mock email provider row."""
    row = MagicMock()
    row.smtp_host = smtp_host
    row.port = port
    row.security = security
    row.username = username
    row.from_email = from_email
    row.password_encrypted = password_encrypted
    return row


class TestGetSmtpRuntimeConfig:
    """AC-3: get_smtp_runtime_config() returns correct dict."""

    def test_returns_all_five_keys(self) -> None:
        """Result dict has exactly: host, port, sender, username, password."""
        row = _make_row()
        svc = _make_service(row=row)
        svc._decrypt_password = MagicMock(return_value="decrypted-pass")

        config = svc.get_smtp_runtime_config()

        assert set(config.keys()) == {
            "host",
            "port",
            "sender",
            "username",
            "password",
            "security",
        }

    def test_key_remapping_smtp_host_to_host(self) -> None:
        """smtp_host is remapped to 'host' key."""
        row = _make_row(smtp_host="mail.zorivest.com")
        svc = _make_service(row=row)
        svc._decrypt_password = MagicMock(return_value="p")

        config = svc.get_smtp_runtime_config()

        assert config["host"] == "mail.zorivest.com"

    def test_key_remapping_from_email_to_sender(self) -> None:
        """from_email is remapped to 'sender' key."""
        row = _make_row(from_email="noreply@zorivest.com")
        svc = _make_service(row=row)
        svc._decrypt_password = MagicMock(return_value="p")

        config = svc.get_smtp_runtime_config()

        assert config["sender"] == "noreply@zorivest.com"

    def test_port_passed_through(self) -> None:
        """Port value is passed through as integer."""
        row = _make_row(port=465)
        svc = _make_service(row=row)
        svc._decrypt_password = MagicMock(return_value="p")

        config = svc.get_smtp_runtime_config()

        assert config["port"] == 465

    def test_username_passed_through(self) -> None:
        """Username is passed through directly."""
        row = _make_row(username="mat@zorivest.com")
        svc = _make_service(row=row)
        svc._decrypt_password = MagicMock(return_value="p")

        config = svc.get_smtp_runtime_config()

        assert config["username"] == "mat@zorivest.com"

    def test_password_decrypted(self) -> None:
        """Encrypted password is decrypted via _decrypt_password."""
        row = _make_row(password_encrypted=b"fernet-encrypted")
        svc = _make_service(row=row)
        svc._decrypt_password = MagicMock(return_value="my-secret-password")

        config = svc.get_smtp_runtime_config()

        assert config["password"] == "my-secret-password"
        svc._decrypt_password.assert_called_once_with(b"fernet-encrypted")


class TestGetSmtpRuntimeConfigDefaults:
    """AC-3 negative: missing config row returns safe defaults."""

    def test_no_config_row_returns_safe_defaults(self) -> None:
        """When no email config row exists, returns dict with all 5 keys and safe defaults."""
        svc = _make_service(row=None)

        config = svc.get_smtp_runtime_config()

        assert set(config.keys()) == {
            "host",
            "port",
            "sender",
            "username",
            "password",
            "security",
        }
        assert config["host"] == "localhost"
        assert config["port"] == 587
        assert config["sender"] == "noreply@zorivest.local"
        assert config["username"] == ""
        assert config["password"] == ""
        assert config["security"] == "STARTTLS"

    def test_no_password_returns_empty_string(self) -> None:
        """When password_encrypted is None, password key is empty string."""
        row = _make_row(password_encrypted=None)
        svc = _make_service(row=row)

        config = svc.get_smtp_runtime_config()

        assert config["password"] == ""

    def test_sender_falls_back_to_username_when_from_email_empty(self) -> None:
        """When from_email is None/empty, sender falls back to username."""
        row = _make_row(from_email=None, username="fallback@test.com")
        svc = _make_service(row=row)
        svc._decrypt_password = MagicMock(return_value="")

        config = svc.get_smtp_runtime_config()

        assert config["sender"] == "fallback@test.com"
