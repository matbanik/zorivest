# packages/core/src/zorivest_core/domain/pipeline.py
"""Pipeline domain models for the Scheduling & Pipeline Engine (Phase 9).

This module defines:
- Policy authoring models (Pydantic): RefValue, RetryConfig, SkipCondition,
  PolicyStep, TriggerConfig, PolicyMetadata, PolicyDocument
- Execution runtime types (dataclasses): StepContext, StepResult
- SkipConditionOperator enum

Spec references: 09-scheduling.md §9.1c, §9.1d
"""

from __future__ import annotations

from dataclasses import dataclass, field as dc_field
from datetime import datetime
from enum import StrEnum
from typing import Any

import structlog
from pydantic import BaseModel, Field, field_validator

from zorivest_core.domain.enums import PipelineStatus, StepErrorMode


# ---------------------------------------------------------------------------
# §9.1c: Policy Authoring Models
# ---------------------------------------------------------------------------


class RefValue(BaseModel):
    """A reference to a prior step's output in the pipeline context.

    Usage in policy JSON:
        { "ref": "ctx.fetch_prices.output.quotes" }
    """

    ref: str = Field(..., pattern=r"^ctx\.\w+(\.\w+)*$")


class RetryConfig(BaseModel):
    """Per-step retry configuration."""

    max_attempts: int = Field(default=3, ge=1, le=10)
    backoff_factor: float = Field(default=2.0, ge=1.0, le=10.0)
    jitter: bool = True


class SkipConditionOperator(StrEnum):
    """Operators for runtime skip conditions."""

    EQ = "eq"
    NE = "ne"
    GT = "gt"
    LT = "lt"
    GE = "ge"
    LE = "le"
    IN = "in"
    NOT_IN = "not_in"
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"


class SkipCondition(BaseModel):
    """Condition for skipping a step at runtime.

    Evaluated against the pipeline context before step execution.
    """

    field: str = Field(
        ..., description="Dot-path into ctx, e.g. 'ctx.fetch_data.output.count'"
    )
    operator: SkipConditionOperator
    value: Any = None  # Not required for is_null / is_not_null


class PolicyStep(BaseModel):
    """A single step in a pipeline policy."""

    id: str = Field(
        ..., min_length=1, max_length=64, pattern=r"^[a-z][a-z0-9_]*$"
    )
    type: str = Field(
        ..., description="Registered step type name, e.g. 'fetch', 'transform'"
    )
    params: dict[str, Any] = Field(default_factory=dict)
    timeout: int = Field(
        default=300, ge=10, le=3600, description="Max seconds for this step"
    )
    retry: RetryConfig = Field(default_factory=RetryConfig)
    on_error: StepErrorMode = StepErrorMode.FAIL_PIPELINE
    skip_if: SkipCondition | None = None
    required: bool = Field(
        default=True, description="If false, step failure doesn't block pipeline"
    )

    @field_validator("params", mode="before")
    @classmethod
    def resolve_ref_markers(cls, v: dict) -> dict:
        """Validate that ref values use the correct format.

        Actual resolution happens at runtime via RefResolver.
        """
        return v


class TriggerConfig(BaseModel):
    """Scheduling trigger configuration."""

    cron_expression: str = Field(
        ..., description="5-field cron: minute hour day month weekday"
    )
    timezone: str = Field(default="UTC")
    enabled: bool = True
    misfire_grace_time: int = Field(
        default=3600, ge=60, le=86400, description="Seconds"
    )
    coalesce: bool = True
    max_instances: int = Field(default=1, ge=1, le=3)


class PolicyMetadata(BaseModel):
    """Policy document metadata."""

    author: str = Field(default="", description="Who created/modified this policy")
    created_at: datetime | None = None
    updated_at: datetime | None = None
    description: str = Field(default="", max_length=500)


class PolicyDocument(BaseModel):
    """Root model for a pipeline policy JSON document.

    This is the unit of authoring: AI agents create PolicyDocuments
    via MCP, which are validated, stored, and scheduled for execution.
    """

    schema_version: int = Field(default=1, ge=1, le=99)
    name: str = Field(..., min_length=1, max_length=128)
    metadata: PolicyMetadata = Field(default_factory=PolicyMetadata)
    trigger: TriggerConfig
    steps: list[PolicyStep] = Field(..., min_length=1, max_length=10)

    @field_validator("steps")
    @classmethod
    def unique_step_ids(cls, v: list[PolicyStep]) -> list[PolicyStep]:
        ids = [s.id for s in v]
        if len(ids) != len(set(ids)):
            dupes = [x for x in ids if ids.count(x) > 1]
            raise ValueError(f"Duplicate step IDs: {set(dupes)}")
        return v


# ---------------------------------------------------------------------------
# §9.1d: Execution Runtime Types
# ---------------------------------------------------------------------------


@dataclass
class StepContext:
    """Mutable context passed between pipeline steps.

    Each step reads from `outputs` (prior step results) and writes
    its own output, which is stored under its step_id key.
    """

    run_id: str
    policy_id: str
    outputs: dict[str, Any] = dc_field(default_factory=dict)
    dry_run: bool = False
    logger: structlog.BoundLogger = dc_field(default_factory=structlog.get_logger)

    def get_output(self, step_id: str) -> Any:
        """Get a prior step's output by step_id."""
        if step_id not in self.outputs:
            raise KeyError(f"No output for step '{step_id}' — check step ordering")
        return self.outputs[step_id]


@dataclass
class StepResult:
    """Output of a single step execution."""

    status: PipelineStatus
    output: dict[str, Any] = dc_field(default_factory=dict)
    error: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_ms: int = 0


# ---------------------------------------------------------------------------
# Spec import compatibility: §9.1e defines StepBase in this module's
# conceptual scope. The actual implementation lives in step_registry.py
# to avoid circular imports. Re-export via __getattr__ for lazy loading.
# ---------------------------------------------------------------------------


def __getattr__(name: str) -> Any:
    if name == "StepBase":
        from zorivest_core.domain.step_registry import StepBase

        return StepBase
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

