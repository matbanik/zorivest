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
from datetime import datetime, timedelta, timezone
from enum import StrEnum
from typing import Any

import hashlib

import structlog
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

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

    id: str = Field(..., min_length=1, max_length=64, pattern=r"^[a-z][a-z0-9_]*$")
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

    Schema v2 adds: variables, query/compose step types, assertion kind.
    """

    model_config = ConfigDict(extra="forbid")

    schema_version: int = Field(default=1, ge=1, le=2)
    name: str = Field(..., min_length=1, max_length=128)
    metadata: PolicyMetadata = Field(default_factory=PolicyMetadata)
    trigger: TriggerConfig
    steps: list[PolicyStep] = Field(..., min_length=1, max_length=20)
    variables: dict[str, Any] = Field(default_factory=dict)

    @field_validator("steps")
    @classmethod
    def unique_step_ids(cls, v: list[PolicyStep]) -> list[PolicyStep]:
        ids = [s.id for s in v]
        if len(ids) != len(set(ids)):
            dupes = [x for x in ids if ids.count(x) > 1]
            raise ValueError(f"Duplicate step IDs: {set(dupes)}")
        return v

    @model_validator(mode="after")
    def enforce_version_features(self) -> "PolicyDocument":
        """Reject v2 features used with schema_version=1 (§9D.6b)."""
        v2_step_types = {"query", "compose"}
        has_assertion_steps = any(
            s.params.get("kind") == "assertion" for s in self.steps
        )

        has_v2_features = (
            bool(self.variables)
            or any(s.type in v2_step_types for s in self.steps)
            or has_assertion_steps
        )

        if has_v2_features and self.schema_version < 2:
            raise ValueError(
                "Features used require schema_version >= 2: "
                "variables, query/compose step types, or assertion kind. "
                "Set schema_version: 2 in your policy JSON."
            )
        return self


# ---------------------------------------------------------------------------
# §9.1d: Execution Runtime Types
# ---------------------------------------------------------------------------


@dataclass
class StepContext:
    """Mutable context passed between pipeline steps.

    Each step reads from `outputs` (prior step results) and writes
    its own output, which is stored under its step_id key.

    Per §9C.1b: get_output() returns deep copies and put_output()
    stores deep copies to prevent cross-step mutation contamination.
    """

    run_id: str
    policy_id: str
    outputs: dict[str, Any] = dc_field(default_factory=dict)
    dry_run: bool = False
    logger: structlog.BoundLogger = dc_field(default_factory=structlog.get_logger)
    # §9C.3b: UI confirmation flag for SendStep gate
    has_user_confirmation: bool = False
    # §9C.3c: Approval provenance snapshot from PolicyModel
    approval_snapshot: Any = None  # ApprovalSnapshot | None
    # §9C.3c: Current policy content hash for drift detection
    policy_hash: str = ""
    # §9C.4d: Cumulative URL fetch counter (policy-level cap = 10)
    fetch_url_count: int = 0
    # §9D.3c: Policy-level variables for ref resolution
    variables: dict[str, Any] = dc_field(default_factory=dict)

    def get_output(self, step_id: str) -> Any:
        """Get a prior step's output by step_id (returns isolated deep copy)."""
        if step_id not in self.outputs:
            raise KeyError(f"No output for step '{step_id}' — check step ordering")
        from zorivest_core.services.safe_copy import safe_deepcopy

        return safe_deepcopy(self.outputs[step_id])

    def put_output(self, step_id: str, value: Any) -> None:
        """Store a step's output (stores isolated deep copy)."""
        from zorivest_core.services.safe_copy import safe_deepcopy

        self.outputs[step_id] = safe_deepcopy(value)


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
# §9.4d: FetchResult Provenance Envelope (MEU-85)
# ---------------------------------------------------------------------------


@dataclass
class FetchResult:
    """Output envelope for FetchStep with provenance tracking.

    Computes SHA-256 content hash on init for data integrity verification.
    """

    provider: str
    data_type: str
    content: bytes
    content_hash: str = dc_field(init=False)
    cache_status: str = "miss"  # miss | hit | revalidated
    fetched_at: datetime = dc_field(default_factory=lambda: datetime.now(timezone.utc))
    warnings: list[str] = dc_field(default_factory=list)

    def __post_init__(self) -> None:
        self.content_hash = hashlib.sha256(self.content).hexdigest()


# ---------------------------------------------------------------------------
# §9.4f: Freshness TTL + Market Hours (MEU-85)
# ---------------------------------------------------------------------------


# TTL in seconds per data type — how long fetched data stays fresh.
FRESHNESS_TTL: dict[str, int] = {
    "quote": 60,  # 1 minute — real-time quotes
    "ohlcv": 3600,  # 1 hour — daily bars
    "news": 1800,  # 30 minutes — news feed
    "fundamentals": 86400,  # 24 hours — changes infrequently
}


# US market hours: NYSE/NASDAQ open 9:30 AM–4:00 PM Eastern (UTC-5 / UTC-4 DST).
_ET_OFFSET_STANDARD = timedelta(hours=-5)
_ET_OFFSET_DST = timedelta(hours=-4)
_MARKET_OPEN_HOUR, _MARKET_OPEN_MINUTE = 9, 30
_MARKET_CLOSE_HOUR, _MARKET_CLOSE_MINUTE = 16, 0


def _is_dst(dt: datetime) -> bool:
    """Check if a UTC datetime falls in US Eastern DST (March–November)."""
    year = dt.year
    # Second Sunday in March
    march_second_sunday = 14 - datetime(year, 3, 1).weekday()
    if march_second_sunday > 14:
        march_second_sunday -= 7
    dst_start = datetime(year, 3, march_second_sunday, 7, tzinfo=timezone.utc)
    # First Sunday in November
    november_first_sunday = 7 - datetime(year, 11, 1).weekday()
    if november_first_sunday > 7:
        november_first_sunday -= 7
    dst_end = datetime(year, 11, november_first_sunday, 6, tzinfo=timezone.utc)
    return dst_start <= dt < dst_end


def is_market_closed(dt: datetime | None = None) -> bool:
    """Check if US equity markets are closed at the given UTC datetime.

    Returns True on weekends and outside 9:30 AM – 4:00 PM ET on weekdays.
    Does not account for holidays.
    """
    if dt is None:
        dt = datetime.now(timezone.utc)

    # Convert UTC to Eastern
    offset = _ET_OFFSET_DST if _is_dst(dt) else _ET_OFFSET_STANDARD
    et_time = dt + offset

    # Weekend check (Saturday=5, Sunday=6)
    if et_time.weekday() >= 5:
        return True

    # Outside trading hours
    market_open = et_time.replace(
        hour=_MARKET_OPEN_HOUR, minute=_MARKET_OPEN_MINUTE, second=0, microsecond=0
    )
    market_close = et_time.replace(
        hour=_MARKET_CLOSE_HOUR, minute=_MARKET_CLOSE_MINUTE, second=0, microsecond=0
    )
    return not (market_open <= et_time < market_close)


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
