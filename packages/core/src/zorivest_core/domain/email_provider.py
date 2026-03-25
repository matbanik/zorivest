"""Email provider configuration domain dataclass.

Source: 06f-gui-settings.md §Email Provider (MEU-73)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class EmailProviderConfig:
    """Email SMTP provider configuration.

    ``password_encrypted`` is stored as Fernet-encrypted bytes and is
    never exposed in HTTP responses. HTTP responses use ``has_password``
    (a derived boolean).
    """

    id: int = 1
    provider_preset: Optional[str] = None
    smtp_host: Optional[str] = None
    port: Optional[int] = None
    security: Optional[str] = None  # "STARTTLS" | "SSL"
    username: Optional[str] = None
    password_encrypted: Optional[bytes] = field(default=None, repr=False)
    from_email: Optional[str] = None

    @property
    def has_password(self) -> bool:
        """True when a Fernet-encrypted password is stored."""
        return bool(self.password_encrypted)

    def to_response_dict(self) -> dict:  # type: ignore[type-arg]
        """Return HTTP-safe dict — never exposes raw encrypted bytes."""
        return {
            "provider_preset": self.provider_preset,
            "smtp_host": self.smtp_host,
            "port": self.port,
            "security": self.security,
            "username": self.username,
            "has_password": self.has_password,
            "from_email": self.from_email,
        }
