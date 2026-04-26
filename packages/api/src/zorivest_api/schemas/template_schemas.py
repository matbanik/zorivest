# packages/api/src/zorivest_api/schemas/template_schemas.py
"""Pydantic request/response schemas for emulator + template CRUD endpoints.

MEU: MEU-PH9 (emulator-mcp-tools)
Spec: 09f §9F.1 (emulator), 09e §9E.2 (template CRUD)
"""

from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, Field, field_validator


# ── Template Schemas ──────────────────────────────────────────────────────


_TEMPLATE_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")


class EmailTemplateCreateRequest(BaseModel):
    """Request body for creating a new email template.

    Field constraints per §9E.0:
    - name: 1–128 chars, lowercase alphanumeric + hyphens + underscores
    - body_html: 1–65536 chars
    - body_format: html or markdown
    """

    model_config = {"extra": "forbid"}

    name: str = Field(..., min_length=1, max_length=128)
    description: str | None = Field(default=None, max_length=500)
    subject_template: str | None = Field(default=None, max_length=500)
    body_html: str = Field(..., min_length=1, max_length=65536)
    body_format: str = Field(default="html")
    required_variables: list[str] = Field(default_factory=list)
    sample_data_json: str | None = Field(default=None, max_length=65536)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not _TEMPLATE_NAME_RE.match(v):
            msg = (
                "Template name must start with lowercase letter/digit "
                "and contain only lowercase letters, digits, hyphens, underscores"
            )
            raise ValueError(msg)
        return v

    @field_validator("body_format")
    @classmethod
    def validate_body_format(cls, v: str) -> str:
        if v not in ("html", "markdown"):
            msg = "body_format must be 'html' or 'markdown'"
            raise ValueError(msg)
        return v


class EmailTemplateUpdateRequest(BaseModel):
    """Request body for updating an existing email template.

    Same field constraints as create. All fields optional except name (path key).
    """

    model_config = {"extra": "forbid"}

    description: str | None = Field(default=None, max_length=500)
    subject_template: str | None = Field(default=None, max_length=500)
    body_html: str | None = Field(default=None, min_length=1, max_length=65536)
    body_format: str | None = Field(default=None)
    required_variables: list[str] | None = None
    sample_data_json: str | None = Field(default=None, max_length=65536)

    @field_validator("body_format")
    @classmethod
    def validate_body_format(cls, v: str | None) -> str | None:
        if v is not None and v not in ("html", "markdown"):
            msg = "body_format must be 'html' or 'markdown'"
            raise ValueError(msg)
        return v


class EmailTemplateResponse(BaseModel):
    """Response model for a single email template."""

    name: str
    description: str | None = None
    subject_template: str | None = None
    body_html: str
    body_format: str
    required_variables: list[str] = Field(default_factory=list)
    sample_data_json: str | None = None
    is_default: bool = False


class PreviewRequest(BaseModel):
    """Request body for template preview endpoint.

    Optional data dict overrides sample_data_json from the template.
    """

    model_config = {"extra": "forbid"}

    data: dict[str, Any] | None = None


# ── Emulator Schemas ──────────────────────────────────────────────────────


class EmulateRequest(BaseModel):
    """Request body for POST /scheduling/emulator/run.

    Accepts full policy JSON and optional phase subset.
    """

    model_config = {"extra": "forbid"}

    policy_json: dict[str, Any] = Field(..., description="Full PolicyDocument JSON")
    phases: list[str] | None = Field(
        default=None,
        description="Optional phase subset: PARSE, VALIDATE, SIMULATE, RENDER",
    )

    @field_validator("policy_json")
    @classmethod
    def policy_json_must_be_non_empty(cls, v: dict[str, Any]) -> dict[str, Any]:
        if not v:
            msg = "policy_json must not be empty"
            raise ValueError(msg)
        return v

    @field_validator("phases")
    @classmethod
    def validate_phases(cls, v: list[str] | None) -> list[str] | None:
        if v is not None:
            valid = {"PARSE", "VALIDATE", "SIMULATE", "RENDER"}
            for phase in v:
                if phase not in valid:
                    msg = f"Invalid phase '{phase}'. Must be one of: {sorted(valid)}"
                    raise ValueError(msg)
        return v


class ValidateSqlRequest(BaseModel):
    """Request body for POST /scheduling/validate-sql."""

    model_config = {"extra": "forbid"}

    sql: str = Field(..., min_length=1, max_length=10000)
