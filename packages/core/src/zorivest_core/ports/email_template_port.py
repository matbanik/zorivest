# packages/core/src/zorivest_core/ports/email_template_port.py
"""Core port for email template access — §9E.1e.

Architecture rule: Core MUST NOT import infrastructure.
All template access from core services, pipeline steps, or the policy emulator
goes through this port. Implemented by EmailTemplateRepository in infra layer.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class EmailTemplateDTO:
    """Read-only projection of an email template for core consumers."""

    name: str
    description: str | None
    subject_template: str | None
    body_html: str
    body_format: str
    required_variables: list[str]
    sample_data_json: str | None
    is_default: bool


class EmailTemplatePort(ABC):
    """Core port for email template access.

    Implemented by EmailTemplateRepository in infra layer.
    """

    @abstractmethod
    def get_by_name(self, name: str) -> EmailTemplateDTO | None:
        """Look up a template by its unique name. Returns None if not found."""
        ...

    @abstractmethod
    def list_all(self) -> list[EmailTemplateDTO]:
        """Return all registered templates ordered by name."""
        ...
