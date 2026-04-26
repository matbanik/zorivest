# tests/unit/test_email_template_repository.py
"""FIC: EmailTemplateRepository + EmailTemplateModel (MEU-PH6) — Spec §9E.1c–2a.

Acceptance Criteria:
  AC-6.1:  EmailTemplateModel has 12 columns per §9E.1c           [Spec §9E.1c]
  AC-6.2:  Repository CRUD: create, get_by_name, list_all, update, delete  [Spec §9E.2a]
  AC-6.3:  delete() rejects default templates (is_default=True)   [Spec §9E.2a]
  AC-6.4:  EmailTemplatePort ABC with get_by_name and list_all    [Spec §9E.1e]
  AC-6.5:  EmailTemplateDTO frozen dataclass matches port contract [Spec §9E.1e]
  AC-6.6:  SqlAlchemyUnitOfWork has email_templates property       [Spec §9E.2b]
  AC-6.21: Model has 12 columns per schema                        [Spec §9E.1c]
  AC-6.22: Default template seeding from EMAIL_TEMPLATES dict      [Spec §9E.1d]
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def db_session():
    """Create an in-memory SQLite session with email_templates table."""
    from zorivest_infra.database.models import Base, EmailTemplateModel  # noqa: F401

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(engine)
    yield session
    session.close()


# ---------------------------------------------------------------------------
# AC-6.1 / AC-6.21: EmailTemplateModel has 12 columns
# ---------------------------------------------------------------------------


def test_model_has_12_columns(db_session: Session) -> None:
    """AC-6.1/AC-6.21: EmailTemplateModel has exactly 12 columns per §9E.1c."""
    from zorivest_infra.database.models import EmailTemplateModel

    mapper = inspect(EmailTemplateModel)
    column_names = {c.key for c in mapper.columns}
    expected = {
        "id",
        "name",
        "description",
        "subject_template",
        "body_html",
        "body_format",
        "required_variables",
        "sample_data_json",
        "is_default",
        "created_at",
        "updated_at",
        "created_by",
    }
    assert column_names == expected, (
        f"Missing: {expected - column_names}, Extra: {column_names - expected}"
    )


# ---------------------------------------------------------------------------
# AC-6.21: Model table name is "email_templates"
# ---------------------------------------------------------------------------


def test_model_tablename() -> None:
    """AC-6.21: EmailTemplateModel __tablename__ is 'email_templates'."""
    from zorivest_infra.database.models import EmailTemplateModel

    assert EmailTemplateModel.__tablename__ == "email_templates"


# ---------------------------------------------------------------------------
# AC-6.2: Repository CRUD
# ---------------------------------------------------------------------------


def test_crud_operations(db_session: Session) -> None:
    """AC-6.2: create, get_by_name, list_all, update, delete all work."""
    from zorivest_infra.database.email_template_repository import (
        EmailTemplateRepository,
    )
    from zorivest_infra.database.models import EmailTemplateModel

    repo = EmailTemplateRepository(db_session)

    # Create
    tmpl = EmailTemplateModel(
        name="test-template",
        body_html="<p>{{ greeting }}</p>",
        body_format="html",
        created_at=datetime.now(timezone.utc),
        created_by="test",
    )
    created = repo.create(tmpl)
    assert created.name == "test-template"  # type: ignore[reportGeneralTypeIssues]

    # get_by_name
    found = repo.get_by_name("test-template")
    assert found is not None
    assert found.body_html == "<p>{{ greeting }}</p>"

    # list_all
    all_templates = repo.list_all()
    assert len(all_templates) == 1

    # update
    updated = repo.update("test-template", body_html="<p>Updated</p>")
    assert updated.body_html == "<p>Updated</p>"  # type: ignore[reportGeneralTypeIssues]
    assert updated.updated_at is not None

    # delete
    repo.delete("test-template")
    db_session.flush()
    assert repo.get_by_name("test-template") is None


# ---------------------------------------------------------------------------
# AC-6.3: delete() rejects default templates
# ---------------------------------------------------------------------------


def test_delete_default_rejected(db_session: Session) -> None:
    """AC-6.3: delete() raises ValueError for is_default=True templates."""
    from zorivest_infra.database.email_template_repository import (
        EmailTemplateRepository,
    )
    from zorivest_infra.database.models import EmailTemplateModel

    repo = EmailTemplateRepository(db_session)
    tmpl = EmailTemplateModel(
        name="default-template",
        body_html="<p>Default</p>",
        body_format="html",
        is_default=True,
        created_at=datetime.now(timezone.utc),
    )
    repo.create(tmpl)

    with pytest.raises(ValueError, match="Cannot delete default"):
        repo.delete("default-template")


# ---------------------------------------------------------------------------
# AC-6.4: EmailTemplatePort ABC
# ---------------------------------------------------------------------------


def test_port_abc_exists() -> None:
    """AC-6.4: EmailTemplatePort ABC defines get_by_name and list_all."""
    from zorivest_core.ports.email_template_port import EmailTemplatePort
    import inspect as py_inspect

    assert py_inspect.isabstract(EmailTemplatePort)
    # Verify abstract methods exist
    abstract_methods = EmailTemplatePort.__abstractmethods__
    assert "get_by_name" in abstract_methods
    assert "list_all" in abstract_methods


# ---------------------------------------------------------------------------
# AC-6.5: EmailTemplateDTO frozen dataclass
# ---------------------------------------------------------------------------


def test_dto_frozen() -> None:
    """AC-6.5: EmailTemplateDTO is a frozen dataclass with expected fields."""
    from zorivest_core.ports.email_template_port import EmailTemplateDTO
    import dataclasses

    assert dataclasses.is_dataclass(EmailTemplateDTO)
    # Frozen check
    dto = EmailTemplateDTO(
        name="test",
        description=None,
        subject_template=None,
        body_html="<p>hi</p>",
        body_format="html",
        required_variables=[],
        sample_data_json=None,
        is_default=False,
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        dto.name = "modified"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# AC-6.6: UoW has email_templates property
# ---------------------------------------------------------------------------


def test_uow_has_email_templates_property() -> None:
    """AC-6.6: SqlAlchemyUnitOfWork has email_templates annotation."""
    from zorivest_infra.database.unit_of_work import SqlAlchemyUnitOfWork

    assert "email_templates" in SqlAlchemyUnitOfWork.__annotations__


# ---------------------------------------------------------------------------
# AC-6.22: Default template seeding
# ---------------------------------------------------------------------------


def test_default_template_seeding(db_session: Session) -> None:
    """AC-6.22: Default templates can be seeded from EMAIL_TEMPLATES dict."""
    from zorivest_infra.database.email_template_repository import (
        EmailTemplateRepository,
    )
    from zorivest_infra.database.models import EmailTemplateModel
    from zorivest_infra.rendering.email_templates import EMAIL_TEMPLATES

    repo = EmailTemplateRepository(db_session)

    # Seed all hardcoded templates
    for name, body in EMAIL_TEMPLATES.items():
        tmpl = EmailTemplateModel(
            name=name,
            body_html=body,
            body_format="html",
            is_default=True,
            created_at=datetime.now(timezone.utc),
            created_by="system",
        )
        repo.create(tmpl)

    db_session.flush()

    # Verify all were created
    all_templates = repo.list_all()
    assert len(all_templates) == len(EMAIL_TEMPLATES)
    for tmpl in all_templates:
        assert tmpl.is_default is True
