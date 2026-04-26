# pyright: reportArgumentType=false, reportReturnType=false, reportGeneralTypeIssues=false, reportAttributeAccessIssue=false
# packages/infrastructure/src/zorivest_infra/database/email_template_repository.py
"""EmailTemplateRepository — CRUD for EmailTemplateModel (§9E.2a).

Implements EmailTemplatePort from core for dependency-inverted access.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from zorivest_core.ports.email_template_port import EmailTemplateDTO, EmailTemplatePort
from zorivest_infra.database.models import EmailTemplateModel

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


class EmailTemplateRepository(EmailTemplatePort):
    """CRUD repository for email templates.

    Backed by SQLAlchemy session. Implements EmailTemplatePort from core
    so pipeline steps can access templates without importing infra.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, template: EmailTemplateModel) -> EmailTemplateModel:
        """Insert a new email template."""
        self._session.add(template)
        self._session.flush()
        return template

    def get_by_name(self, name: str) -> EmailTemplateDTO | None:
        """Look up a template by unique name. Returns DTO (port contract)."""
        model = (
            self._session.query(EmailTemplateModel)
            .filter(EmailTemplateModel.name == name)
            .first()
        )
        if model is None:
            return None
        return self._to_dto(model)

    def get_model_by_name(self, name: str) -> EmailTemplateModel | None:
        """Return raw SQLAlchemy model (infra-only use)."""
        return (
            self._session.query(EmailTemplateModel)
            .filter(EmailTemplateModel.name == name)
            .first()
        )

    def list_all(self) -> list[EmailTemplateDTO]:
        """Return all templates ordered by name. Returns DTOs (port contract)."""
        models = (
            self._session.query(EmailTemplateModel)
            .order_by(EmailTemplateModel.name)
            .all()
        )
        return [self._to_dto(m) for m in models]

    def update(self, name: str, **kwargs: object) -> EmailTemplateModel:
        """Update fields on a template by name. Sets updated_at automatically."""
        model = self.get_model_by_name(name)
        if model is None:
            raise ValueError(f"Template not found: {name}")
        for key, value in kwargs.items():
            setattr(model, key, value)
        model.updated_at = datetime.now(timezone.utc)
        self._session.flush()
        return model

    def delete(self, name: str) -> None:
        """Delete a template by name. Raises ValueError for default templates."""
        model = self.get_model_by_name(name)
        if model is None:
            raise ValueError(f"Template not found: {name}")
        if model.is_default:
            raise ValueError(f"Cannot delete default template: {name}")
        self._session.delete(model)
        self._session.flush()

    @staticmethod
    def _to_dto(model: EmailTemplateModel) -> EmailTemplateDTO:
        """Convert ORM model to frozen DTO."""
        import json

        required_vars: list[str] = []
        if model.required_variables:
            required_vars = json.loads(model.required_variables)

        return EmailTemplateDTO(
            name=model.name,
            description=model.description,
            subject_template=model.subject_template,
            body_html=model.body_html,
            body_format=model.body_format,
            required_variables=required_vars,
            sample_data_json=model.sample_data_json,
            is_default=bool(model.is_default),
        )
