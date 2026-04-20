"""Email provider service — Fernet-encrypted SMTP config with test-send.

Source: 06f-gui-settings.md §Email Provider (MEU-73)
"""

from __future__ import annotations

import smtplib
import ssl
from typing import Any


class EmailProviderService:
    """Manage email SMTP provider configuration with Fernet-encrypted password.

    Wraps the single-row ``EmailProviderRepository``.
    Constructor accepts the UoW (for repository access) and the shared
    Fernet encryption adapter already instantiated in ``main.py`` lifespan.
    """

    def __init__(self, uow: Any, encryption: Any) -> None:
        self._uow = uow
        self._encryption = encryption

    # ── Helpers ──────────────────────────────────────────────────────────

    def _repo(self) -> Any:
        return self._uow.email_provider  # type: ignore[no-any-return]

    def _encrypt_password(self, plaintext: str) -> bytes:
        """Return Fernet-encrypted bytes using the injected Fernet key."""
        return self._encryption._fernet.encrypt(plaintext.encode())

    def _decrypt_password(self, stored: bytes) -> str:
        """Decrypt Fernet bytes back to plaintext string."""
        return self._encryption._fernet.decrypt(stored).decode()

    # ── Public API ────────────────────────────────────────────────────────

    def get_config(self) -> dict:  # type: ignore[type-arg]
        """Return current config dict with ``has_password`` bool (no raw password).

        AC-E1: password field is never returned; has_password reflects presence.
        AC-E5: empty config returns safe defaults (no 500).
        """
        with self._uow:
            row = self._repo().get()
        if row is None:
            return {
                "provider_preset": None,
                "smtp_host": None,
                "port": None,
                "security": None,
                "username": None,
                "has_password": False,
                "from_email": None,
            }
        return {  # type: ignore[return-value]
            "provider_preset": row.provider_preset,
            "smtp_host": row.smtp_host,
            "port": row.port,
            "security": row.security,
            "username": row.username,
            "has_password": bool(row.password_encrypted),  # type: ignore[arg-type]
            "from_email": row.from_email,
        }

    def save_config(self, data: dict) -> None:  # type: ignore[type-arg]
        """Persist email config, Fernet-encrypting the password if provided.

        AC-E2: saves all 7 fields.
        AC-E3: empty/absent password keeps the existing stored password.
        """
        with self._uow:
            existing = self._repo().get()

            password = data.get("password", "")
            if password:
                enc = self._encrypt_password(password)
            elif existing is not None and existing.password_encrypted:
                enc = None  # keep existing — repo.save_config preserves when None
            else:
                enc = None

            self._repo().save_config(data, enc)
            self._uow.commit()

    def test_connection(self) -> dict:  # type: ignore[type-arg]
        """Send a test email using stored SMTP credentials.

        AC-E4: returns ``{"success": bool, "message": str}``.
        """
        with self._uow:
            row = self._repo().get()

        if row is None or not row.smtp_host or not row.username:  # type: ignore[truthy-function]
            return {"success": False, "message": "Email provider not configured."}

        # Explicitly cast ORM column values to plain Python types (pyright)
        host: str = str(row.smtp_host)  # type: ignore[arg-type]
        port: int = int(row.port) if row.port else 587  # type: ignore[arg-type]
        security: str = str(row.security) if row.security else "STARTTLS"  # type: ignore[arg-type]
        username: str = str(row.username)  # type: ignore[arg-type]
        password = ""
        if row.password_encrypted:  # type: ignore[truthy-function]
            enc_bytes: bytes = bytes(row.password_encrypted)  # type: ignore[arg-type]
            password = self._decrypt_password(enc_bytes)

        try:
            from_addr = str(row.from_email) if row.from_email else username  # type: ignore[truthy-function]
            probe_msg = (
                f"From: {from_addr}\r\n"
                f"To: {from_addr}\r\n"
                f"Subject: Zorivest SMTP Connection Test\r\n"
                f"\r\n"
                f"This is an automated connection test sent by Zorivest. "
                f"If you received this email, your SMTP settings are correctly configured."
            )
            if security == "SSL":
                ctx = ssl.create_default_context()
                with smtplib.SMTP_SSL(host, port, context=ctx, timeout=10) as server:
                    server.login(username, password)
                    server.sendmail(from_addr, [from_addr], probe_msg)
            else:
                with smtplib.SMTP(host, port, timeout=10) as server:
                    server.ehlo()
                    server.starttls(context=ssl.create_default_context())
                    server.ehlo()
                    server.login(username, password)
                    server.sendmail(from_addr, [from_addr], probe_msg)

            return {
                "success": True,
                "message": f"Test email sent successfully to {from_addr}.",
            }
        except Exception as exc:  # noqa: BLE001
            return {"success": False, "message": str(exc)}

    def get_smtp_runtime_config(self) -> dict[str, str | int]:
        """Return SMTP config dict for pipeline SendStep injection.

        Performs key remapping from ORM model fields to the contract
        expected by SendStep (send_step.py L108-111):
          smtp_host → host
          from_email → sender

        Password is Fernet-decrypted from stored bytes.
        Missing config returns safe defaults with all 5 keys.
        """
        with self._uow:
            row = self._repo().get()

        if row is None:
            return {
                "host": "localhost",
                "port": 587,
                "sender": "noreply@zorivest.local",
                "username": "",
                "password": "",
                "security": "STARTTLS",
            }

        # Decrypt password if present
        password = ""
        if row.password_encrypted:
            enc_bytes: bytes = bytes(row.password_encrypted)
            try:
                password = self._decrypt_password(enc_bytes)
            except Exception:  # noqa: BLE001
                # Invalid Fernet token (plaintext, wrong key, or corrupt data)
                # — fall back to empty string rather than crashing app startup
                password = ""

        # Sender falls back to username when from_email is absent
        sender = str(row.from_email) if row.from_email else str(row.username)

        return {
            "host": str(row.smtp_host) if row.smtp_host else "localhost",
            "port": int(row.port) if row.port else 587,
            "sender": sender,
            "username": str(row.username) if row.username else "",
            "password": password,
            "security": str(row.security) if row.security else "STARTTLS",
        }
