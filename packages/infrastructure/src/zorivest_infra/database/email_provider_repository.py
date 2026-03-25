"""Email provider repository — single-row CRUD with Fernet-encrypted password.

Source: 06f-gui-settings.md §Email Provider (MEU-73)
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from zorivest_infra.database.models import EmailProviderModel


class SqlAlchemyEmailProviderRepository:
    """Single-row repository for email provider configuration.

    The table always holds at most one row (id=1).  ``save`` upserts.
    Password bytes are stored/retrieved as-is; Fernet
    encrypt/decrypt happens in ``EmailProviderService``.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self) -> Optional[EmailProviderModel]:
        """Return the singleton row, or None if not yet configured."""
        return self._session.get(EmailProviderModel, 1)

    def save(self, config: EmailProviderModel) -> None:
        """Upsert the singleton row (always id=1)."""
        config.id = 1  # type: ignore[assignment]
        config.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)  # type: ignore[assignment]
        existing = self._session.get(EmailProviderModel, 1)
        if existing is None:
            self._session.add(config)
        else:
            existing.provider_preset = config.provider_preset  # type: ignore[assignment]
            existing.smtp_host = config.smtp_host  # type: ignore[assignment]
            existing.port = config.port  # type: ignore[assignment]
            existing.security = config.security  # type: ignore[assignment]
            existing.username = config.username  # type: ignore[assignment]
            if config.password_encrypted is not None:
                existing.password_encrypted = config.password_encrypted  # type: ignore[assignment]
            existing.from_email = config.from_email  # type: ignore[assignment]
            existing.updated_at = config.updated_at  # type: ignore[assignment]
        self._session.flush()

    def save_config(self, data: dict, password_encrypted: bytes | None = None) -> None:  # type: ignore[type-arg]
        """Upsert the singleton row from a plain dict.

        Owns EmailProviderModel construction so the service layer (core)
        does not need to import an infra model class.

        Args:
            data: mapping of field names to values.
            password_encrypted: pre-encrypted bytes to store; None preserves existing.
        """
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        existing = self._session.get(EmailProviderModel, 1)
        if existing is None:
            row = EmailProviderModel()
            row.id = 1  # type: ignore[assignment]
            row.provider_preset = data.get("provider_preset")  # type: ignore[assignment]
            row.smtp_host = data.get("smtp_host")  # type: ignore[assignment]
            row.port = data.get("port")  # type: ignore[assignment]
            row.security = data.get("security")  # type: ignore[assignment]
            row.username = data.get("username")  # type: ignore[assignment]
            row.from_email = data.get("from_email")  # type: ignore[assignment]
            row.password_encrypted = password_encrypted  # type: ignore[assignment]
            row.updated_at = now  # type: ignore[assignment]
            self._session.add(row)
        else:
            existing.provider_preset = data.get("provider_preset")  # type: ignore[assignment]
            existing.smtp_host = data.get("smtp_host")  # type: ignore[assignment]
            existing.port = data.get("port")  # type: ignore[assignment]
            existing.security = data.get("security")  # type: ignore[assignment]
            existing.username = data.get("username")  # type: ignore[assignment]
            existing.from_email = data.get("from_email")  # type: ignore[assignment]
            if password_encrypted is not None:
                existing.password_encrypted = password_encrypted  # type: ignore[assignment]
            existing.updated_at = now  # type: ignore[assignment]
        self._session.flush()
