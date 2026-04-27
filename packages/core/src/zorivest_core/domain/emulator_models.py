# packages/core/src/zorivest_core/domain/emulator_models.py
"""Structured error and result models for the policy emulator (§9F.3).

Models:
    EmulatorError — Structured error from a specific emulation phase.
    EmulatorResult — Complete emulation result with structured errors.

Spec reference: 09f §9F.3a, §9F.3b
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class EmulatorError(BaseModel):
    """Structured error from a specific emulation phase."""

    phase: Literal["PARSE", "VALIDATE", "SIMULATE", "RENDER"]
    step_id: str | None = None
    error_type: str = Field(
        ...,
        description=(
            "Error category: SCHEMA_INVALID, REF_UNRESOLVED, SQL_BLOCKED, "
            "TEMPLATE_MISSING, VARIABLE_UNUSED, SIMULATE_ERROR, RENDER_ERROR, "
            "OUTPUT_TOO_LARGE, SQL_SCHEMA_ERROR, SMTP_NOT_CONFIGURED, STEP_WIRING_ERROR"
        ),
    )
    field: str | None = None
    message: str
    suggestion: str | None = None


class EmulatorResult(BaseModel):
    """Complete emulation result with structured errors."""

    valid: bool = True
    phase: str = ""
    errors: list[EmulatorError] = Field(default_factory=list)
    warnings: list[EmulatorError] = Field(default_factory=list)
    mock_outputs: dict | None = None
    template_preview_hash: str | None = None
    bytes_used: int = 0
