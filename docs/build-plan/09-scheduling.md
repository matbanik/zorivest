# Phase 9: Scheduling & Pipeline Engine

> Part of [Zorivest Build Plan](../BUILD_PLAN.md) | Prerequisites: [Phase 2](02-infrastructure.md), [Phase 3](03-service-layer.md), [Phase 4](04-rest-api.md), [Phase 5](05-mcp-server.md), [Phase 8](08-market-data.md) | Consumers: [Phase 6e](06e-gui-scheduling.md)
>
> **Sources**: [`_inspiration/scheduling_research/`](../../_inspiration/scheduling_research/) · [Strategic Roadmap](../../_inspiration/scheduling_research/scheduling-integration-roadmap.md)

---

## Goal

Build a scheduling and pipeline engine that enables AI agents (via MCP) to author declarative JSON policies controlling data fetch, transform, storage, rendering, and email delivery pipelines. Policies are validated, versioned, and require human approval before first execution. Pipelines are scheduled via APScheduler 3.x, persisted in SQLCipher, and expose step-level observability through REST, MCP, and the GUI.

---

## Architecture Overview

```
┌──────────────────┐     ┌───────────────────┐     ┌──────────────────┐
│  MCP Tools       │     │  React GUI        │     │  APScheduler     │
│  (create_policy, │     │  (Policy Editor,  │     │  (CronTrigger,   │
│   run_pipeline)  │     │   Run History)    │     │   misfire grace) │
└────────┬─────────┘     └────────┬──────────┘     └────────┬─────────┘
         │                        │                          │
         └────────────┬───────────┘──────────────────────────┘
                      ▼
         ┌───────────────────────┐
         │  FastAPI REST API     │
         │  /api/v1/scheduling   │
         └───────────┬───────────┘
                     ▼
         ┌───────────────────────┐
         │  PipelineRunner       │──── Policy validation
         │  (async executor)     │──── Ref resolution
         │                       │──── State machine
         └───────────┬───────────┘
                     ▼
    ┌────────────────────────────────────────────────┐
    │              Step Type Registry                │
    │  __init_subclass__ auto-registration           │
    └───┬────────┬────────┬─────────┬────────┬──────┘
        ▼        ▼        ▼         ▼        ▼
    ┌───────┐┌────────┐┌───────┐┌────────┐┌──────┐
    │ Fetch ││Transform││Store  ││ Render ││ Send │
    │       ││        ││Report ││        ││      │
    └───┬───┘└───┬────┘└───┬───┘└───┬────┘└──┬───┘
        │        │         │        │         │
        ▼        ▼         ▼        ▼         ▼
    ┌──────────────────────────────────────────────┐
    │  SQLCipher (WAL mode)                        │
    │  pipeline_runs · pipeline_steps · policies   │
    │  reports · fetch_cache · audit_log           │
    └──────────────────────────────────────────────┘
```

---

## Step 9.1: Domain Layer Additions

### 9.1a: PipelineStatus Enum

```python
# packages/core/src/zorivest_core/domain/enums.py  (append)

class PipelineStatus(str, Enum):
    """Execution status for pipeline runs and individual steps."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"
```

### 9.1b: StepErrorMode Enum

```python
# packages/core/src/zorivest_core/domain/enums.py  (append)

class StepErrorMode(str, Enum):
    """How the pipeline engine handles a step failure."""
    FAIL_PIPELINE = "fail_pipeline"         # Abort entire pipeline (default)
    LOG_AND_CONTINUE = "log_and_continue"   # Log error, mark step FAILED, continue
    RETRY_THEN_FAIL = "retry_then_fail"     # Retry per RetryConfig, then fail_pipeline
```

### 9.1c: Policy Pydantic Models

```python
# packages/core/src/zorivest_core/domain/pipeline.py

from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Any, Literal
from pydantic import BaseModel, Field, field_validator

from zorivest_core.domain.enums import StepErrorMode


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


class SkipConditionOperator(str, Enum):
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
    field: str = Field(..., description="Dot-path into ctx, e.g. 'ctx.fetch_data.output.count'")
    operator: SkipConditionOperator
    value: Any = None  # Not required for is_null / is_not_null


class PolicyStep(BaseModel):
    """A single step in a pipeline policy."""
    id: str = Field(..., min_length=1, max_length=64, pattern=r"^[a-z][a-z0-9_]*$")
    type: str = Field(..., description="Registered step type name, e.g. 'fetch', 'transform'")
    params: dict[str, Any] = Field(default_factory=dict)
    timeout: int = Field(default=300, ge=10, le=3600, description="Max seconds for this step")
    retry: RetryConfig = Field(default_factory=RetryConfig)
    on_error: StepErrorMode = StepErrorMode.FAIL_PIPELINE
    skip_if: SkipCondition | None = None
    required: bool = Field(default=True, description="If false, step failure doesn't block pipeline")

    @field_validator("params", mode="before")
    @classmethod
    def resolve_ref_markers(cls, v: dict) -> dict:
        """Validate that ref values use the correct format (actual resolution at runtime)."""
        return v  # Structural validation only; RefResolver handles runtime resolution


class TriggerConfig(BaseModel):
    """Scheduling trigger configuration."""
    cron_expression: str = Field(..., description="5-field cron: minute hour day month weekday")
    timezone: str = Field(default="UTC")
    enabled: bool = True
    misfire_grace_time: int = Field(default=3600, ge=60, le=86400, description="Seconds")
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
```

### 9.1d: StepContext and StepResult

```python
# packages/core/src/zorivest_core/domain/pipeline.py  (append)

from dataclasses import dataclass, field as dc_field
import structlog


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
```

### 9.1e: StepBase Protocol (Step Type Registry Foundation)

```python
# packages/core/src/zorivest_core/domain/pipeline.py  (append)

from typing import Protocol, ClassVar, runtime_checkable


@runtime_checkable
class StepBase(Protocol):
    """Protocol that all pipeline step types must implement.

    Step types self-register via __init_subclass__. Each step declares:
    - type_name: unique identifier used in policy JSON
    - side_effects: whether the step mutates external state (email, DB write)
    - Params: Pydantic model for parameter validation
    """

    type_name: ClassVar[str]
    side_effects: ClassVar[bool]

    async def execute(self, params: dict, context: StepContext) -> StepResult:
        """Execute the step with resolved parameters and shared context."""
        ...

    @classmethod
    def params_schema(cls) -> dict:
        """Return JSON Schema for this step's parameters (from Pydantic model)."""
        ...

    async def compensate(
        self, params: dict, context: StepContext, prior_result: StepResult
    ) -> None:
        """Optional: undo a step's side effects on pipeline failure."""
        ...
```

### 9.1f: Step Type Registry Singleton

```python
# packages/core/src/zorivest_core/domain/step_registry.py

from __future__ import annotations
from typing import Any

from zorivest_core.domain.pipeline import StepBase, StepResult, StepContext


STEP_REGISTRY: dict[str, type] = {}


class RegisteredStep:
    """Base class for concrete step implementations.

    Subclasses auto-register via __init_subclass__. Usage:

        class FetchStep(RegisteredStep):
            type_name = "fetch"
            side_effects = False
            class Params(BaseModel):
                provider: str
                data_type: str
    """

    type_name: str = ""
    side_effects: bool = False

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if cls.type_name:
            if cls.type_name in STEP_REGISTRY:
                raise ValueError(
                    f"Duplicate step type '{cls.type_name}': "
                    f"{STEP_REGISTRY[cls.type_name].__name__} vs {cls.__name__}"
                )
            STEP_REGISTRY[cls.type_name] = cls

    async def execute(self, params: dict, context: StepContext) -> StepResult:
        raise NotImplementedError

    @classmethod
    def params_schema(cls) -> dict:
        if hasattr(cls, "Params"):
            return cls.Params.model_json_schema()
        return {}

    async def compensate(
        self, params: dict, context: StepContext, prior_result: StepResult
    ) -> None:
        """Default: no compensation. Override for steps with side effects."""
        pass


def get_step(type_name: str) -> type | None:
    """Look up a registered step type by name."""
    return STEP_REGISTRY.get(type_name)


def has_step(type_name: str) -> bool:
    """Check if a step type is registered."""
    return type_name in STEP_REGISTRY


def list_steps() -> list[dict]:
    """List all registered step types with their schemas (for MCP exposure)."""
    return [
        {
            "type_name": cls.type_name,
            "side_effects": cls.side_effects,
            "params_schema": cls.params_schema(),
        }
        for cls in STEP_REGISTRY.values()
    ]
```

### 9.1g: Policy Validation Module

```python
# packages/core/src/zorivest_core/domain/policy_validator.py

from __future__ import annotations
import hashlib
import json
import re
from dataclasses import dataclass

from zorivest_core.domain.pipeline import PolicyDocument, PolicyStep
from zorivest_core.domain.step_registry import has_step


@dataclass
class ValidationError:
    field: str
    message: str
    severity: str = "error"  # "error" | "warning"


# SQL keywords that must never appear in report queries
SQL_BLOCKLIST = {"DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "ATTACH", "PRAGMA", "CREATE"}

# Cron validation — use APScheduler's own parser for correctness
def _validate_cron(expression: str) -> str | None:
    """Validate a cron expression using APScheduler's parser.

    Returns None if valid, or an error message if invalid.
    """
    try:
        from apscheduler.triggers.cron import CronTrigger
        CronTrigger.from_crontab(expression)
        return None
    except (ValueError, KeyError) as exc:
        return str(exc)


def validate_policy(doc: PolicyDocument) -> list[ValidationError]:
    """Full structural and referential validation of a policy document.

    Returns an empty list if the policy is valid.
    """
    errors: list[ValidationError] = []

    # 1. Schema version
    if doc.schema_version != 1:
        errors.append(ValidationError("schema_version", f"Unsupported version: {doc.schema_version}"))

    # 2. Step count
    if len(doc.steps) > 10:
        errors.append(ValidationError("steps", f"Max 10 steps allowed, got {len(doc.steps)}"))

    # 3. Step types exist in registry
    for step in doc.steps:
        if not has_step(step.type):
            errors.append(ValidationError(
                f"steps[{step.id}].type",
                f"Unknown step type: '{step.type}'"
            ))

    # 4. Referential integrity — refs must point to prior steps
    seen_ids: set[str] = set()
    for step in doc.steps:
        _check_refs(step.params, step.id, seen_ids, errors)
        seen_ids.add(step.id)

    cron_error = _validate_cron(doc.trigger.cron_expression)
    if cron_error:
        errors.append(ValidationError(
            "trigger.cron_expression",
            f"Invalid cron expression: {cron_error}"
        ))

    # 6. SQL blocklist check in params
    _check_sql_blocklist(doc, errors)

    return errors


def compute_content_hash(doc: PolicyDocument) -> str:
    """SHA-256 of canonical JSON representation (for change detection)."""
    canonical = json.dumps(doc.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


def _check_refs(params: dict, step_id: str, seen_ids: set[str], errors: list[ValidationError]) -> None:
    """Recursively walk params dict and validate all { "ref": ... } values."""
    for key, value in params.items():
        if isinstance(value, dict):
            if "ref" in value and len(value) == 1:
                ref_path = value["ref"]
                if ref_path.startswith("ctx."):
                    ref_step = ref_path.split(".")[1]
                    if ref_step not in seen_ids:
                        errors.append(ValidationError(
                            f"steps[{step_id}].params.{key}",
                            f"Ref '{ref_path}' points to step '{ref_step}' which "
                            f"hasn't executed yet (or doesn't exist)"
                        ))
            else:
                _check_refs(value, step_id, seen_ids, errors)
        elif isinstance(value, list):
            for i, item in enumerate(value):
                if isinstance(item, dict):
                    _check_refs(item, step_id, seen_ids, errors)


def _check_sql_blocklist(doc: PolicyDocument, errors: list[ValidationError]) -> None:
    """Recursively scan all string values in step params for SQL injection patterns.

    Note: This is defense-in-depth. The primary protection is SQLite's
    set_authorizer + PRAGMA query_only (see Step 9.6c).
    """
    for step in doc.steps:
        _scan_value_for_sql(step.params, f"steps[{step.id}].params", errors)


def _scan_value_for_sql(value: Any, path: str, errors: list[ValidationError]) -> None:
    """Recursively scan a value tree for blocked SQL keywords."""
    if isinstance(value, str):
        tokens = value.upper().split()
        blocked = SQL_BLOCKLIST.intersection(tokens)
        if blocked:
            errors.append(ValidationError(
                path,
                f"Blocked SQL keywords found: {blocked}",
                severity="error",
            ))
    elif isinstance(value, dict):
        for k, v in value.items():
            _scan_value_for_sql(v, f"{path}.{k}", errors)
    elif isinstance(value, list):
        for i, item in enumerate(value):
            _scan_value_for_sql(item, f"{path}[{i}]", errors)
```

---

## Step 9.2: Infrastructure Layer Additions

### 9.2a: PipelineRunModel

```python
# packages/infrastructure/src/zorivest_infra/database/models.py  (append)

import uuid
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship


class PipelineRunModel(Base):
    """A single execution of a pipeline policy."""
    __tablename__ = "pipeline_runs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    policy_id = Column(String(36), ForeignKey("policies.id"), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="pending")  # PipelineStatus
    trigger_type = Column(String(20), nullable=False)  # "scheduled" | "manual" | "mcp"
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    error = Column(Text, nullable=True)
    dry_run = Column(Boolean, default=False)
    created_by = Column(String(128), default="")
    content_hash = Column(String(64), nullable=False)  # Policy hash at execution time

    steps = relationship("PipelineStepModel", back_populates="run", cascade="all, delete-orphan")
    policy = relationship("PolicyModel", back_populates="runs")
```

### 9.2b: PipelineStepModel

```python
# packages/infrastructure/src/zorivest_infra/database/models.py  (append)

class PipelineStepModel(Base):
    """Execution record for a single step within a pipeline run."""
    __tablename__ = "pipeline_steps"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id = Column(String(36), ForeignKey("pipeline_runs.id"), nullable=False, index=True)
    step_id = Column(String(64), nullable=False)     # Matches PolicyStep.id
    step_type = Column(String(64), nullable=False)    # e.g. "fetch", "transform"
    status = Column(String(20), nullable=False, default="pending")
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    output_json = Column(Text, nullable=True)         # JSON-serialized step output
    error = Column(Text, nullable=True)
    attempt = Column(Integer, default=1)

    run = relationship("PipelineRunModel", back_populates="steps")
```

### 9.2c: PolicyModel

```python
# packages/infrastructure/src/zorivest_infra/database/models.py  (append)

class PolicyModel(Base):
    """Persisted pipeline policy document."""
    __tablename__ = "policies"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(128), unique=True, nullable=False)
    schema_version = Column(Integer, nullable=False, default=1)
    policy_json = Column(Text, nullable=False)        # Full PolicyDocument JSON
    content_hash = Column(String(64), nullable=False)
    enabled = Column(Boolean, default=True)
    approved = Column(Boolean, default=False)
    approved_at = Column(DateTime, nullable=True)
    approved_hash = Column(String(64), nullable=True)  # Hash that was approved
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=True)
    created_by = Column(String(128), default="")

    runs = relationship("PipelineRunModel", back_populates="policy")
```

### 9.2d: PipelineStateModel

```python
# packages/infrastructure/src/zorivest_infra/database/models.py  (append)

class PipelineStateModel(Base):
    """Incremental state for fetch steps (high-water marks, cursors)."""
    __tablename__ = "pipeline_state"
    __table_args__ = (
        UniqueConstraint("policy_id", "provider_id", "data_type", "entity_key",
                         name="uq_pipeline_state"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    policy_id = Column(String(36), ForeignKey("policies.id"), nullable=False)
    provider_id = Column(String(64), nullable=False)
    data_type = Column(String(64), nullable=False)
    entity_key = Column(String(128), nullable=False)
    last_cursor = Column(String(256), nullable=True)
    last_hash = Column(String(64), nullable=True)
    updated_at = Column(DateTime, nullable=False)
```

### 9.2e: ReportModel and ReportVersionModel

```python
# packages/infrastructure/src/zorivest_infra/database/models.py  (append)

class ReportModel(Base):
    """Current version of a generated report."""
    __tablename__ = "reports"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(256), nullable=False)
    version = Column(Integer, default=1)
    spec_json = Column(Text, nullable=False)          # ReportSpec JSON
    snapshot_json = Column(Text, nullable=True)        # Frozen query results
    snapshot_hash = Column(String(64), nullable=True)  # SHA-256 of snapshot
    format = Column(String(10), nullable=False, default="pdf")  # "html" | "pdf"
    rendered_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False)
    created_by = Column(String(128), default="")

    versions = relationship("ReportVersionModel", back_populates="report", cascade="all, delete-orphan")
    deliveries = relationship("ReportDeliveryModel", back_populates="report", cascade="all, delete-orphan")


class ReportVersionModel(Base):
    """Historical versions of a report (populated by trigger)."""
    __tablename__ = "report_versions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    report_id = Column(String(36), ForeignKey("reports.id"), nullable=False, index=True)
    version = Column(Integer, nullable=False)
    spec_json = Column(Text, nullable=False)
    snapshot_json = Column(Text, nullable=True)
    snapshot_hash = Column(String(64), nullable=True)
    created_at = Column(DateTime, nullable=False)

    report = relationship("ReportModel", back_populates="versions")
```

### 9.2f: ReportDeliveryModel

```python
# packages/infrastructure/src/zorivest_infra/database/models.py  (append)

class ReportDeliveryModel(Base):
    """Delivery tracking for rendered reports."""
    __tablename__ = "report_delivery"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    report_id = Column(String(36), ForeignKey("reports.id"), nullable=False, index=True)
    channel = Column(String(20), nullable=False)       # "email" | "local_file"
    recipient = Column(String(256), nullable=False)
    status = Column(String(20), nullable=False, default="pending")
    sent_at = Column(DateTime, nullable=True)
    error = Column(Text, nullable=True)
    dedup_key = Column(String(64), unique=True, nullable=False)  # SHA-256 idempotency key

    report = relationship("ReportModel", back_populates="deliveries")
```

### 9.2g: FetchCacheModel

```python
# packages/infrastructure/src/zorivest_infra/database/models.py  (append)

class FetchCacheModel(Base):
    """HTTP response cache for fetch steps."""
    __tablename__ = "fetch_cache"
    __table_args__ = (
        UniqueConstraint("provider", "data_type", "entity_key", name="uq_fetch_cache"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    provider = Column(String(64), nullable=False)
    data_type = Column(String(64), nullable=False)
    entity_key = Column(String(128), nullable=False)
    payload_json = Column(Text, nullable=False)
    content_hash = Column(String(64), nullable=False)
    etag = Column(String(256), nullable=True)
    last_modified = Column(String(128), nullable=True)
    fetched_at = Column(DateTime, nullable=False)
    ttl_seconds = Column(Integer, nullable=False)
```

### 9.2h: System-Versioned Table Triggers

```sql
-- Report versioning triggers (run via Alembic migration)

CREATE TRIGGER IF NOT EXISTS reports_version_on_update
BEFORE UPDATE ON reports
FOR EACH ROW
BEGIN
    INSERT INTO report_versions (
        id, report_id, version, spec_json, snapshot_json, snapshot_hash, created_at
    ) VALUES (
        lower(hex(randomblob(4)) || '-' || hex(randomblob(2)) || '-4' ||
              substr(hex(randomblob(2)),2) || '-' ||
              substr('89ab', abs(random()) % 4 + 1, 1) ||
              substr(hex(randomblob(2)),2) || '-' || hex(randomblob(6))),
        OLD.id, OLD.version, OLD.spec_json, OLD.snapshot_json, OLD.snapshot_hash,
        datetime('now')
    );
END;
```

### 9.2i: AuditLogModel with Append-Only Triggers

```python
# packages/infrastructure/src/zorivest_infra/database/models.py  (append)

class AuditLogModel(Base):
    """Append-only audit trail for pipeline operations."""
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    actor = Column(String(128), nullable=False)        # "scheduler", "mcp:agent_name", "gui:user"
    action = Column(String(64), nullable=False)        # "policy.create", "pipeline.run", "report.send"
    resource_type = Column(String(64), nullable=False)  # "policy", "pipeline_run", "report"
    resource_id = Column(String(36), nullable=False)
    details_json = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False)
```

```sql
-- Append-only enforcement (run via Alembic migration)

CREATE TRIGGER IF NOT EXISTS audit_no_update
BEFORE UPDATE ON audit_log
BEGIN
    SELECT RAISE(ABORT, 'audit_log is append-only: UPDATE not allowed');
END;

CREATE TRIGGER IF NOT EXISTS audit_no_delete
BEFORE DELETE ON audit_log
BEGIN
    SELECT RAISE(ABORT, 'audit_log is append-only: DELETE not allowed');
END;
```

### 9.2j: Repository Implementations

```python
# packages/infrastructure/src/zorivest_infra/repositories/pipeline_repos.py

from zorivest_infra.database.models import (
    PolicyModel, PipelineRunModel, PipelineStepModel,
    ReportModel, FetchCacheModel, AuditLogModel,
)


class PolicyRepository:
    """CRUD for pipeline policies."""

    def __init__(self, session):
        self.session = session

    async def create(self, model: PolicyModel) -> PolicyModel: ...
    async def get_by_id(self, policy_id: str) -> PolicyModel | None: ...
    async def get_by_name(self, name: str) -> PolicyModel | None: ...
    async def list_all(self, enabled_only: bool = False) -> list[PolicyModel]: ...
    async def update(self, model: PolicyModel) -> PolicyModel: ...
    async def delete(self, policy_id: str) -> None: ...


class PipelineRunRepository:
    """CRUD for pipeline execution records."""

    def __init__(self, session):
        self.session = session

    async def create(self, model: PipelineRunModel) -> PipelineRunModel: ...
    async def get_by_id(self, run_id: str) -> PipelineRunModel | None: ...
    async def list_by_policy(self, policy_id: str, limit: int = 20) -> list[PipelineRunModel]: ...
    async def list_recent(self, limit: int = 20) -> list[PipelineRunModel]: ...
    async def update_status(self, run_id: str, status: str, error: str | None = None) -> None: ...
    async def find_zombies(self) -> list[PipelineRunModel]:
        """Find runs with status='running' — candidates for zombie recovery."""
        ...


class ReportRepository:
    """CRUD for generated reports."""

    def __init__(self, session):
        self.session = session

    async def create(self, model: ReportModel) -> ReportModel: ...
    async def get_by_id(self, report_id: str) -> ReportModel | None: ...
    async def get_versions(self, report_id: str) -> list: ...


class FetchCacheRepository:
    """Lookup and invalidation for fetch cache."""

    def __init__(self, session):
        self.session = session

    async def get_cached(self, provider: str, data_type: str, entity_key: str) -> FetchCacheModel | None: ...
    async def upsert(self, model: FetchCacheModel) -> None: ...
    async def invalidate(self, provider: str, data_type: str | None = None) -> int:
        """Remove cached entries. Returns count deleted."""
        ...


class AuditLogRepository:
    """Append-only audit log writer."""

    def __init__(self, session):
        self.session = session

    async def append(self, actor: str, action: str, resource_type: str,
                     resource_id: str, details: dict | None = None) -> None: ...
    async def list_recent(self, limit: int = 50) -> list[AuditLogModel]: ...
```

---

## Step 9.3: Pipeline Execution Engine

### 9.3a: PipelineRunner

```python
# packages/core/src/zorivest_core/services/pipeline_runner.py

from __future__ import annotations
import asyncio
import json
import time
from datetime import datetime, timezone

import structlog

from zorivest_core.domain.enums import PipelineStatus, StepErrorMode
from zorivest_core.domain.pipeline import (
    PolicyDocument, StepContext, StepResult, PolicyStep,
)
from zorivest_core.domain.step_registry import get_step


logger = structlog.get_logger()


class PipelineRunner:
    """Sequential async executor for pipeline policies.

    Runs steps in order, passing a shared StepContext. Handles:
    - Ref resolution (params with { "ref": "ctx.x" })
    - Skip conditions (skip_if evaluation)
    - Error modes (fail, log+continue, retry)
    - Dry-run mode (skip steps with side_effects=True)
    - Resume from failure (re-execute from last failed step)
    """

    def __init__(self, uow, ref_resolver, condition_evaluator):
        self.uow = uow
        self.ref_resolver = ref_resolver
        self.condition_evaluator = condition_evaluator

    async def run(
        self,
        policy: PolicyDocument,
        trigger_type: str,
        dry_run: bool = False,
        resume_from: str | None = None,
        actor: str = "",
    ) -> dict:
        """Execute a full pipeline.

        Args:
            policy: Validated PolicyDocument to execute.
            trigger_type: "scheduled", "manual", or "mcp".
            dry_run: If True, skip steps with side_effects=True.
            resume_from: Step ID to resume from (skip prior successful steps).
            actor: Who triggered this run.

        Returns:
            Dict with run_id, status, step_results, duration_ms.
        """
        from zorivest_core.domain.policy_validator import compute_content_hash

        run_id = str(__import__("uuid").uuid4())
        content_hash = compute_content_hash(policy)
        run_log = structlog.get_logger().bind(run_id=run_id, policy=policy.name)

        context = StepContext(
            run_id=run_id,
            policy_id=policy.id,  # Must use UUID, matches FK policies.id
            dry_run=dry_run,
            logger=run_log,
        )

        # Persist run record
        await self._create_run_record(run_id, policy.name, trigger_type, dry_run, actor, content_hash)

        run_start = time.monotonic()
        final_status = PipelineStatus.SUCCESS
        run_error = None
        skipping = resume_from is not None

        try:
            for step_def in policy.steps:
                # Resume logic: skip until we reach the resume step
                if skipping:
                    if step_def.id == resume_from:
                        skipping = False
                    else:
                        prior_output = await self._load_prior_output(run_id, step_def.id)
                        if prior_output is not None:
                            context.outputs[step_def.id] = prior_output
                        continue

                step_result = await self._execute_step(step_def, context, run_id)

                if step_result.status == PipelineStatus.FAILED:
                    if step_def.on_error == StepErrorMode.FAIL_PIPELINE:
                        final_status = PipelineStatus.FAILED
                        run_error = f"Step '{step_def.id}' failed: {step_result.error}"
                        run_log.error("pipeline_failed", step=step_def.id, error=step_result.error)
                        break
                    elif step_def.on_error == StepErrorMode.LOG_AND_CONTINUE:
                        run_log.warning("step_failed_continuing", step=step_def.id, error=step_result.error)
                    # RETRY_THEN_FAIL is handled inside _execute_step

                if step_result.status == PipelineStatus.SUCCESS:
                    context.outputs[step_def.id] = step_result.output

        except asyncio.CancelledError:
            final_status = PipelineStatus.CANCELLED
            run_error = "Pipeline cancelled"
        except Exception as exc:
            final_status = PipelineStatus.FAILED
            run_error = str(exc)
            run_log.exception("pipeline_unhandled_error")

        duration_ms = int((time.monotonic() - run_start) * 1000)
        await self._finalize_run(run_id, final_status, run_error, duration_ms)

        return {
            "run_id": run_id,
            "status": final_status.value,
            "duration_ms": duration_ms,
            "error": run_error,
            "steps": len(policy.steps),
        }

    async def _execute_step(
        self, step_def: PolicyStep, context: StepContext, run_id: str
    ) -> StepResult:
        """Execute a single step with skip/dry-run/retry handling."""
        log = context.logger.bind(step=step_def.id, step_type=step_def.type)

        # 1. Evaluate skip condition
        if step_def.skip_if and self.condition_evaluator.evaluate(step_def.skip_if, context):
            log.info("step_skipped", reason="skip_if condition met")
            result = StepResult(status=PipelineStatus.SKIPPED)
            await self._persist_step(run_id, step_def, result, attempt=0)
            return result

        # 2. Look up step implementation
        step_cls = get_step(step_def.type)
        if step_cls is None:
            result = StepResult(
                status=PipelineStatus.FAILED,
                error=f"Unknown step type: {step_def.type}",
            )
            await self._persist_step(run_id, step_def, result, attempt=0)
            return result

        step_impl = step_cls()

        # 3. Dry-run: skip side-effect steps
        if context.dry_run and step_cls.side_effects:
            log.info("step_dry_run_skipped", reason="side_effects=True in dry-run mode")
            result = StepResult(status=PipelineStatus.SKIPPED, output={"dry_run": True})
            await self._persist_step(run_id, step_def, result, attempt=0)
            return result

        # 4. Resolve refs in params
        resolved_params = self.ref_resolver.resolve(step_def.params, context)

        # 5. Execute with retry
        last_result = StepResult(status=PipelineStatus.FAILED, error="No attempts made")
        max_attempts = step_def.retry.max_attempts if step_def.on_error == StepErrorMode.RETRY_THEN_FAIL else 1

        for attempt in range(1, max_attempts + 1):
            start = time.monotonic()
            try:
                async with asyncio.timeout(step_def.timeout):
                    last_result = await step_impl.execute(resolved_params, context)
                    last_result.started_at = datetime.now(timezone.utc)
                    last_result.duration_ms = int((time.monotonic() - start) * 1000)
                    last_result.completed_at = datetime.now(timezone.utc)
            except asyncio.TimeoutError:
                last_result = StepResult(
                    status=PipelineStatus.FAILED,
                    error=f"Step timed out after {step_def.timeout}s",
                    duration_ms=int((time.monotonic() - start) * 1000),
                )
            except Exception as exc:
                last_result = StepResult(
                    status=PipelineStatus.FAILED,
                    error=str(exc),
                    duration_ms=int((time.monotonic() - start) * 1000),
                )

            await self._persist_step(run_id, step_def, last_result, attempt)

            if last_result.status == PipelineStatus.SUCCESS:
                log.info("step_success", duration_ms=last_result.duration_ms, attempt=attempt)
                break
            elif attempt < max_attempts:
                wait = step_def.retry.backoff_factor ** attempt
                if step_def.retry.jitter:
                    import random
                    wait *= (0.5 + random.random())
                log.warning("step_retry", attempt=attempt, wait_seconds=round(wait, 1))
                await asyncio.sleep(wait)

        return last_result

    async def _create_run_record(self, run_id, policy_id, trigger_type, dry_run, actor, content_hash):
        """Persist the initial pipeline_run row."""
        ...

    async def _persist_step(self, run_id, step_def, result, attempt):
        """Persist a pipeline_step row."""
        ...

    async def _finalize_run(self, run_id, status, error, duration_ms):
        """Update the pipeline_run row with final status."""
        ...

    async def _load_prior_output(self, run_id, step_id):
        """Load a prior successful step output for resume."""
        ...
```

### 9.3b: RefResolver

```python
# packages/core/src/zorivest_core/services/ref_resolver.py

from __future__ import annotations
from typing import Any

from zorivest_core.domain.pipeline import StepContext


class RefResolver:
    """Resolves { "ref": "ctx.<step_id>.output.<path>" } references in step params.

    Recursively walks the params dict, replacing ref objects with actual values
    from the pipeline context.
    """

    def resolve(self, params: dict, context: StepContext) -> dict:
        """Return a new dict with all refs resolved."""
        return self._walk(params, context)

    def _walk(self, obj: Any, context: StepContext) -> Any:
        if isinstance(obj, dict):
            # Check if this is a ref object
            if "ref" in obj and len(obj) == 1:
                return self._resolve_ref(obj["ref"], context)
            return {k: self._walk(v, context) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._walk(item, context) for item in obj]
        return obj

    def _resolve_ref(self, ref_path: str, context: StepContext) -> Any:
        """Resolve 'ctx.step_id.output.nested.path' to actual value."""
        parts = ref_path.split(".")
        if parts[0] != "ctx" or len(parts) < 2:
            raise ValueError(f"Invalid ref format: {ref_path}")

        step_id = parts[1]
        value = context.get_output(step_id)

        # Navigate nested path: ctx.step_id.output.quotes → outputs["step_id"]["quotes"]
        for part in parts[2:]:
            if isinstance(value, dict):
                if part not in value:
                    raise KeyError(f"Ref path '{ref_path}': key '{part}' not found in {list(value.keys())}")
                value = value[part]
            elif isinstance(value, list):
                try:
                    value = value[int(part)]
                except (ValueError, IndexError):
                    raise KeyError(f"Ref path '{ref_path}': invalid index '{part}'")
            else:
                raise KeyError(f"Ref path '{ref_path}': cannot traverse into {type(value).__name__}")

        return value
```

### 9.3c: ConditionEvaluator

```python
# packages/core/src/zorivest_core/services/condition_evaluator.py

from __future__ import annotations
from typing import Any

from zorivest_core.domain.pipeline import SkipCondition, SkipConditionOperator, StepContext


class ConditionEvaluator:
    """Evaluates SkipCondition against the pipeline context."""

    def evaluate(self, condition: SkipCondition, context: StepContext) -> bool:
        """Returns True if the condition is met (step should be skipped)."""
        value = self._resolve_field(condition.field, context)
        return self._compare(value, condition.operator, condition.value)

    def _resolve_field(self, field_path: str, context: StepContext) -> Any:
        """Resolve a dot-path field reference from context."""
        parts = field_path.split(".")
        if parts[0] != "ctx" or len(parts) < 3:
            raise ValueError(f"Invalid field path: {field_path}")
        step_id = parts[1]
        value = context.get_output(step_id)
        for part in parts[2:]:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return None
        return value

    def _compare(self, value: Any, op: SkipConditionOperator, target: Any) -> bool:
        match op:
            case SkipConditionOperator.EQ:       return value == target
            case SkipConditionOperator.NE:       return value != target
            case SkipConditionOperator.GT:       return value > target
            case SkipConditionOperator.LT:       return value < target
            case SkipConditionOperator.GE:       return value >= target
            case SkipConditionOperator.LE:       return value <= target
            case SkipConditionOperator.IN:       return value in target
            case SkipConditionOperator.NOT_IN:   return value not in target
            case SkipConditionOperator.IS_NULL:  return value is None
            case SkipConditionOperator.IS_NOT_NULL: return value is not None
            case _: raise ValueError(f"Unknown operator: {op}")
```

### 9.3d: APScheduler Integration

```python
# packages/core/src/zorivest_core/services/scheduler_service.py

from __future__ import annotations
from datetime import datetime

import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.triggers.cron import CronTrigger

from zorivest_core.domain.pipeline import PolicyDocument


logger = structlog.get_logger()


class SchedulerService:
    """Manages APScheduler lifecycle and policy scheduling.

    The scheduler uses the same SQLCipher database as the application
    (via SQLAlchemyJobStore) to persist job state across restarts.
    """

    def __init__(self, db_url: str, pipeline_runner):
        self.pipeline_runner = pipeline_runner
        self.scheduler = AsyncIOScheduler(
            jobstores={
                "default": SQLAlchemyJobStore(url=db_url),
            },
            job_defaults={
                "coalesce": True,
                "max_instances": 1,
                "misfire_grace_time": 3600,
            },
        )

    async def start(self) -> None:
        """Start the scheduler (call during FastAPI lifespan startup)."""
        self.scheduler.start()
        logger.info("scheduler_started", job_count=len(self.scheduler.get_jobs()))

    async def shutdown(self) -> None:
        """Graceful shutdown (call during FastAPI lifespan shutdown)."""
        self.scheduler.shutdown(wait=True)
        logger.info("scheduler_shutdown")

    def schedule_policy(self, policy: PolicyDocument, policy_id: str) -> None:
        """Add or update a scheduled job for a policy."""
        trigger = policy.trigger
        cron_parts = trigger.cron_expression.split()

        cron_trigger = CronTrigger(
            minute=cron_parts[0],
            hour=cron_parts[1],
            day=cron_parts[2],
            month=cron_parts[3],
            day_of_week=cron_parts[4],
            timezone=trigger.timezone,
        )

        job_id = f"policy_{policy_id}"
        self.scheduler.add_job(
            func=self._execute_policy,
            trigger=cron_trigger,
            id=job_id,
            name=policy.name,
            args=[policy_id],
            replace_existing=True,
            coalesce=trigger.coalesce,
            max_instances=trigger.max_instances,
            misfire_grace_time=trigger.misfire_grace_time,
        )
        logger.info("policy_scheduled", policy=policy.name, cron=trigger.cron_expression)

    def unschedule_policy(self, policy_id: str) -> None:
        """Remove a policy's scheduled job."""
        job_id = f"policy_{policy_id}"
        try:
            self.scheduler.remove_job(job_id)
        except Exception:
            pass  # Job may not exist

    def get_next_run(self, policy_id: str) -> datetime | None:
        """Get the next fire time for a policy's job."""
        job_id = f"policy_{policy_id}"
        job = self.scheduler.get_job(job_id)
        return job.next_run_time if job else None

    def pause_policy(self, policy_id: str) -> None:
        self.scheduler.pause_job(f"policy_{policy_id}")

    def resume_policy(self, policy_id: str) -> None:
        self.scheduler.resume_job(f"policy_{policy_id}")

    def get_status(self) -> dict:
        """Return scheduler status for diagnostics."""
        jobs = self.scheduler.get_jobs()
        return {
            "running": self.scheduler.running,
            "job_count": len(jobs),
            "jobs": [
                {
                    "id": j.id,
                    "name": j.name,
                    "next_run": j.next_run_time.isoformat() if j.next_run_time else None,
                }
                for j in jobs
            ],
        }

    async def _execute_policy(self, policy_id: str) -> None:
        """Job callback: load policy from DB and execute."""
        # Load policy from repository, deserialize, and run
        ...
```

### 9.3e: Zombie Detection

```python
# packages/core/src/zorivest_core/services/pipeline_runner.py  (append to class)

    async def recover_zombies(self) -> list[dict]:
        """Scan for orphaned RUNNING pipeline runs at startup.

        Called once during FastAPI lifespan startup. For each zombie:
        - If last step had no side_effects → mark FAILED + log warning
        - If last step had side_effects → mark FAILED + log error (manual review needed)

        Returns list of recovered run summaries.
        """
        from zorivest_core.domain.step_registry import get_step

        zombies = await self.uow.pipeline_runs.find_zombies()
        recovered = []

        for run in zombies:
            last_step = max(run.steps, key=lambda s: s.started_at or datetime.min, default=None)
            step_cls = get_step(last_step.step_type) if last_step else None
            has_side_effects = step_cls.side_effects if step_cls else True

            await self.uow.pipeline_runs.update_status(
                run.id, PipelineStatus.FAILED.value,
                error=f"Zombie recovery: process terminated during step '{last_step.step_id if last_step else 'unknown'}'"
            )

            severity = "error" if has_side_effects else "warning"
            logger.log(severity, "zombie_recovered",
                       run_id=run.id, last_step=last_step.step_id if last_step else None,
                       side_effects=has_side_effects)
            recovered.append({"run_id": run.id, "side_effects": has_side_effects})

        return recovered
```

### 9.3f: Sleep/Wake Handler

```python
# packages/api/src/zorivest_api/routes/scheduler.py  (power event endpoint)

from fastapi import APIRouter

scheduler_router = APIRouter(prefix="/api/v1/scheduler", tags=["scheduler"])


@scheduler_router.post("/power-event")
async def receive_power_event(event: PowerEventRequest, scheduler = Depends(get_scheduler)):
    """Receive OS power events from Electron IPC.

    On 'resume': force APScheduler to re-evaluate missed firings.
    On 'suspend': optionally pause in-flight pipelines.
    """
    if event.event_type == "resume":
        # APScheduler will auto-handle misfires on next tick,
        # but we force an immediate wakeup check
        scheduler.scheduler.wakeup()
        return {"status": "resumed", "pending_jobs": len(scheduler.scheduler.get_jobs())}
    elif event.event_type == "suspend":
        return {"status": "acknowledged"}
    return {"status": "unknown_event"}


class PowerEventRequest(BaseModel):
    event_type: str  # "suspend" | "resume"
    timestamp: str   # ISO 8601
```

```typescript
// ui/src/main/power-events.ts  (Electron main process)

import { powerMonitor, BrowserWindow } from 'electron';

const API_BASE = 'http://localhost:8765/api/v1';

export function registerPowerEvents(win: BrowserWindow) {
  powerMonitor.on('suspend', async () => {
    try {
      await fetch(`${API_BASE}/scheduler/power-event`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ event_type: 'suspend', timestamp: new Date().toISOString() }),
      });
    } catch { /* backend may already be sleeping */ }
  });

  powerMonitor.on('resume', async () => {
    try {
      await fetch(`${API_BASE}/scheduler/power-event`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ event_type: 'resume', timestamp: new Date().toISOString() }),
      });
    } catch { /* retry on next tick */ }
  });
}
```

---

## Step 9.4: Fetch Stage

### 9.4a: FetchStep Implementation

```python
# packages/core/src/zorivest_core/pipeline_steps/fetch_step.py

from pydantic import BaseModel, Field
from zorivest_core.domain.step_registry import RegisteredStep
from zorivest_core.domain.pipeline import StepContext, StepResult, PipelineStatus


class FetchStep(RegisteredStep):
    """Fetch data from a market data provider.

    Extends Phase 8's MarketDataService with pipeline-specific capabilities:
    criteria resolution, caching, incremental state, and fetch envelopes.
    """
    type_name = "fetch"
    side_effects = False  # Read-only: no external mutation

    class Params(BaseModel):
        provider: str = Field(..., description="Provider name from Phase 8 registry")
        data_type: str = Field(..., description="quote | ohlcv | news | fundamentals")
        criteria: dict = Field(default_factory=dict, description="Dynamic criteria with resolution rules")
        batch_size: int = Field(default=50, ge=1, le=500)
        use_cache: bool = Field(default=True)

    async def execute(self, params: dict, context: StepContext) -> StepResult:
        """Fetch data from the specified provider.

        1. Resolve criteria (date ranges, incremental cursors)
        2. Check fetch cache (if use_cache=True)
        3. Call market data service with rate limiting
        4. Package result as FetchResult envelope
        5. Update incremental state if applicable
        """
        validated = self.Params(**params)
        log = context.logger.bind(provider=validated.provider, data_type=validated.data_type)

        # Criteria resolution
        resolved_criteria = await self._resolve_criteria(validated.criteria, context)

        # Cache check
        if validated.use_cache:
            cached = await self._check_cache(validated.provider, validated.data_type, resolved_criteria)
            if cached:
                log.info("fetch_cache_hit")
                return StepResult(
                    status=PipelineStatus.SUCCESS,
                    output={"data": cached.payload, "cache_status": "hit"},
                )

        # Fetch from provider
        try:
            result = await self._fetch_from_provider(validated, resolved_criteria)
            log.info("fetch_success", records=len(result.get("data", [])))
            return StepResult(
                status=PipelineStatus.SUCCESS,
                output=result,
            )
        except Exception as exc:
            return StepResult(status=PipelineStatus.FAILED, error=str(exc))

    async def _resolve_criteria(self, criteria: dict, context: StepContext) -> dict:
        """Resolve dynamic criteria at runtime."""
        ...

    async def _check_cache(self, provider: str, data_type: str, criteria: dict):
        """Check fetch_cache table for valid cached data."""
        ...

    async def _fetch_from_provider(self, params, criteria) -> dict:
        """Call MarketDataService with rate limiting."""
        ...
```

### 9.4b: Criteria Resolver

```python
# packages/core/src/zorivest_core/services/criteria_resolver.py

from __future__ import annotations
from datetime import datetime, timedelta, timezone
from typing import Any


class CriteriaResolver:
    """Resolves dynamic criteria in fetch step params.

    Criteria types:
    - db_query: SQL against read-only connection
    - relative: Date math ("today - 30d")
    - incremental: Use high-water mark from pipeline_state
    - static: Pass through unchanged
    """

    def __init__(self, uow):
        self.uow = uow

    async def resolve(self, criteria: dict, policy_id: str = "") -> dict:
        resolved = {}
        for key, value in criteria.items():
            if isinstance(value, dict) and "type" in value:
                resolved[key] = await self._resolve_typed(value, policy_id)
            else:
                resolved[key] = value  # Static passthrough
        return resolved

    async def _resolve_typed(self, spec: dict, policy_id: str) -> Any:
        match spec["type"]:
            case "relative":
                return self._resolve_relative(spec)
            case "incremental":
                return await self._resolve_incremental(spec, policy_id)
            case "db_query":
                return await self._resolve_db_query(spec)
            case _:
                raise ValueError(f"Unknown criteria type: {spec['type']}")

    def _resolve_relative(self, spec: dict) -> str:
        """Resolve 'today - 30d' to an ISO date string."""
        base = datetime.now(timezone.utc)
        offset = spec.get("offset", "0d")
        unit = offset[-1]
        amount = int(offset[:-1])
        delta = {"d": timedelta(days=amount), "h": timedelta(hours=amount)}.get(unit, timedelta())
        result = base - delta
        return result.strftime("%Y-%m-%d")

    async def _resolve_incremental(self, spec: dict, policy_id: str) -> Any:
        """Retrieve high-water mark from pipeline_state table."""
        state = await self.uow.pipeline_state.get(
            policy_id=policy_id,
            provider_id=spec.get("provider", ""),
            data_type=spec.get("data_type", ""),
            entity_key=spec.get("entity_key", ""),
        )
        return state.last_cursor if state else spec.get("default")

    async def _resolve_db_query(self, spec: dict) -> Any:
        """Execute a read-only SQL query and return results.

        Uses PRAGMA query_only connection for safety.
        """
        # SQL sandboxing enforcement via set_authorizer (see Step 9.6d)
        ...
```

### 9.4c: Rate Limiter Integration

```python
# packages/infrastructure/src/zorivest_infra/market_data/pipeline_rate_limiter.py

import asyncio
from aiolimiter import AsyncLimiter
from tenacity import retry, wait_random_exponential, stop_after_attempt, retry_if_exception_type
import httpx


class PipelineRateLimiter:
    """Per-provider rate limiting for pipeline fetch operations.

    Combines:
    - aiolimiter.AsyncLimiter: Leaky bucket per provider
    - asyncio.Semaphore: Global concurrency limit
    - tenacity: Retry with exponential backoff + jitter
    """

    def __init__(self, global_concurrency: int = 5):
        self._limiters: dict[str, AsyncLimiter] = {}
        self._semaphore = asyncio.Semaphore(global_concurrency)

    def get_limiter(self, provider: str, rate_per_minute: int) -> AsyncLimiter:
        if provider not in self._limiters:
            self._limiters[provider] = AsyncLimiter(rate_per_minute, 60)
        return self._limiters[provider]

    async def execute_with_limits(
        self, provider: str, rate_per_minute: int, coro,
        max_attempts: int = 3, backoff_factor: float = 2.0,
    ):
        """Execute a coroutine with rate limiting, concurrency control, and retry."""
        limiter = self.get_limiter(provider, rate_per_minute)

        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_random_exponential(multiplier=backoff_factor, max=60),
            retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.TimeoutException)),
        )
        async def _guarded():
            async with self._semaphore:
                async with limiter:
                    return await coro

        return await _guarded()
```

### 9.4d: Fetch Envelope

```python
# packages/core/src/zorivest_core/domain/pipeline.py  (append)

import hashlib
import json


@dataclass
class FetchResult:
    """Provenance-first output of a fetch operation.

    Every fetch produces a FetchResult that records where the data came from,
    when it was fetched, how it was cached, and a content hash for dedup.
    """
    raw_payload: dict
    content_type: str = "application/json"
    provider: str = ""
    content_hash: str = ""    # SHA-256 of raw_payload
    cache_status: str = "miss"  # "miss" | "hit" | "revalidated"
    warnings: list[str] = dc_field(default_factory=list)
    fetched_at: datetime | None = None

    def __post_init__(self):
        if not self.content_hash:
            payload_str = json.dumps(self.raw_payload, sort_keys=True, separators=(",", ":"))
            self.content_hash = hashlib.sha256(payload_str.encode()).hexdigest()
```

### 9.4e: HTTP Cache Revalidation

```python
# packages/infrastructure/src/zorivest_infra/market_data/http_cache.py

import httpx
from zorivest_infra.database.models import FetchCacheModel


async def fetch_with_cache(
    client: httpx.AsyncClient,
    url: str,
    cached: FetchCacheModel | None,
    headers: dict | None = None,
) -> tuple[dict, str]:
    """Fetch with ETag/If-Modified-Since revalidation.

    Returns (payload, cache_status) where cache_status is:
    - "miss": No cache, fetched fresh
    - "hit": Cache valid (TTL not expired)
    - "revalidated": 304 Not Modified from server
    """
    req_headers = dict(headers or {})

    if cached:
        if cached.etag:
            req_headers["If-None-Match"] = cached.etag
        if cached.last_modified:
            req_headers["If-Modified-Since"] = cached.last_modified

    response = await client.get(url, headers=req_headers)

    if response.status_code == 304 and cached:
        import json
        return json.loads(cached.payload_json), "revalidated"

    response.raise_for_status()
    data = response.json()
    return data, "miss"
```

### 9.4f: Freshness TTL Model

| Data Type | Default TTL | Market-Session Rule |
|-----------|-------------|---|
| `quote` | 3600 (1h) | Refresh after 4:00 PM ET close |
| `ohlcv` | 86400 (daily) | Refresh after market close only |
| `news` | 900 (15min) | Always use TTL |
| `fundamentals` | 86400 (daily) | No market-session dependency |

```python
# packages/core/src/zorivest_core/domain/pipeline.py  (append)

FRESHNESS_TTL: dict[str, int] = {
    "quote": 3600,
    "ohlcv": 86400,
    "news": 900,
    "fundamentals": 86400,
}


def is_market_closed() -> bool:
    """Check if US equity market is closed (after 4 PM ET)."""
    from datetime import datetime
    from zoneinfo import ZoneInfo
    now = datetime.now(ZoneInfo("America/New_York"))
    return now.hour >= 16 or now.weekday() >= 5
```

---

## Step 9.5: Transform Stage

### 9.5a: TransformStep Implementation

```python
# packages/core/src/zorivest_core/pipeline_steps/transform_step.py

from pydantic import BaseModel, Field
from zorivest_core.domain.step_registry import RegisteredStep
from zorivest_core.domain.pipeline import StepContext, StepResult, PipelineStatus


class TransformStep(RegisteredStep):
    """Transform and validate fetched data before storage.

    Applies field mappings, validates with Pandera, enforces write dispositions,
    and quarantines bad records.
    """
    type_name = "transform"
    side_effects = True  # Writes to database

    class Params(BaseModel):
        mapping: dict = Field(default_factory=dict, description="Provider field → canonical field mapping")
        write_disposition: str = Field(default="append", description="append | replace | merge")
        target_table: str = Field(..., description="Target DB table name")
        validation_rules: list[dict] = Field(default_factory=list)
        quality_threshold: float = Field(default=0.8, ge=0.0, le=1.0)

    async def execute(self, params: dict, context: StepContext) -> StepResult:
        validated = self.Params(**params)
        log = context.logger.bind(target=validated.target_table, disposition=validated.write_disposition)

        # 1. Apply field mapping
        mapped_data = self._apply_mapping(context, validated.mapping)

        # 2. Validate with Pandera
        valid_records, quarantined = self._validate(mapped_data, validated)

        # 3. Check quality threshold
        if len(mapped_data) > 0:
            quality = len(valid_records) / len(mapped_data)
            if quality < validated.quality_threshold:
                return StepResult(
                    status=PipelineStatus.FAILED,
                    error=f"Quality {quality:.0%} below threshold {validated.quality_threshold:.0%}",
                    output={"quality": quality, "quarantined": len(quarantined)},
                )

        # 4. Write with disposition
        rows_written = await self._write_data(
            valid_records, validated.target_table, validated.write_disposition
        )

        log.info("transform_complete", rows=rows_written, quarantined=len(quarantined))
        return StepResult(
            status=PipelineStatus.SUCCESS,
            output={"rows_written": rows_written, "quarantined": len(quarantined), "quality": quality if mapped_data else 1.0},
        )

    def _apply_mapping(self, context: StepContext, mapping: dict) -> list[dict]: ...
    def _validate(self, data: list[dict], params) -> tuple[list, list]: ...
    async def _write_data(self, records: list[dict], table: str, disposition: str) -> int: ...
```

### 9.5b: Field Mapping Configuration

```python
# packages/infrastructure/src/zorivest_infra/market_data/field_mappings.py

FIELD_MAPPINGS: dict[tuple[str, str], dict[str, str]] = {
    ("Alpha Vantage", "quote"): {
        "01. symbol": "ticker",
        "05. price": "price",
        "02. open": "open",
        "03. high": "high",
        "04. low": "low",
        "08. previous close": "previous_close",
        "06. volume": "volume",
        "07. latest trading day": "date",
    },
    ("Polygon.io", "ohlcv"): {
        "o": "open", "h": "high", "l": "low", "c": "close",
        "v": "volume", "t": "timestamp",
    },
    # ... additional provider/data_type mappings
}


def apply_field_mapping(record: dict, mapping: dict[str, str]) -> dict:
    """Map provider-specific field names to canonical names."""
    result = {}
    for src_key, dest_key in mapping.items():
        if src_key in record:
            result[dest_key] = record[src_key]
    mapped_keys = set(mapping.keys())
    extra = {k: v for k, v in record.items() if k not in mapped_keys}
    if extra:
        result["_extra"] = extra
    return result
```

### 9.5c: Validation Gate

```python
# packages/core/src/zorivest_core/services/validation_gate.py

import pandera as pa
from pandera import Column, Check, DataFrameSchema

OHLCV_SCHEMA = DataFrameSchema({
    "ticker": Column(str, Check.str_length(min_value=1, max_value=10)),
    "date": Column(str, Check.str_matches(r"^\d{4}-\d{2}-\d{2}$")),
    "open": Column(float, Check.gt(0)),
    "high": Column(float, Check.gt(0)),
    "low": Column(float, Check.gt(0)),
    "close": Column(float, Check.gt(0)),
    "volume": Column(int, Check.ge(0)),
})

VALIDATION_SCHEMAS: dict[str, DataFrameSchema] = {
    "ohlcv": OHLCV_SCHEMA,
}


def validate_dataframe(data: list[dict], schema_name: str, quality_threshold: float = 0.8
) -> tuple[list[dict], list[dict]]:
    """Validate records against a Pandera schema.

    Returns (valid_records, quarantined_records).
    """
    import pandas as pd
    df = pd.DataFrame(data)
    schema = VALIDATION_SCHEMAS.get(schema_name)
    if schema is None:
        return data, []
    try:
        schema.validate(df, lazy=True)
        return data, []
    except pa.errors.SchemaErrors as err:
        failure_indices = set(err.failure_cases["index"].tolist())
        valid = [r for i, r in enumerate(data) if i not in failure_indices]
        quarantined = [r for i, r in enumerate(data) if i in failure_indices]
        return valid, quarantined
```

### 9.5d: Write Dispositions

```python
# packages/infrastructure/src/zorivest_infra/repositories/write_dispositions.py

from sqlalchemy import Table, Column, MetaData, text, insert, delete, select
from sqlalchemy.ext.asyncio import AsyncSession

# Allowlist of tables/columns that policy-authored transforms may target.
# Any table or column NOT in this dict is rejected — no f-string SQL.
TABLE_ALLOWLIST: dict[str, set[str]] = {
    "market_quotes": {"ticker", "date", "open", "high", "low", "close", "volume", "provider"},
    "market_news": {"id", "ticker", "headline", "source", "url", "published_at", "sentiment"},
    "ohlcv": {"ticker", "date", "open", "high", "low", "close", "volume"},
    # Add additional tables as pipeline steps are registered
}


def _resolve_table(table_name: str, metadata: MetaData) -> Table:
    """Resolve a table name against the allowlist and metadata.

    Raises ValueError if the table is not in the allowlist.
    """
    if table_name not in TABLE_ALLOWLIST:
        raise ValueError(f"Table '{table_name}' not in write allowlist: {sorted(TABLE_ALLOWLIST)}")
    table = metadata.tables.get(table_name)
    if table is None:
        raise ValueError(f"Table '{table_name}' not found in SQLAlchemy metadata")
    return table


def _validate_columns(columns: list[str], table_name: str) -> None:
    """Validate that all columns are in the allowlist for this table."""
    allowed = TABLE_ALLOWLIST[table_name]
    disallowed = set(columns) - allowed
    if disallowed:
        raise ValueError(f"Columns {disallowed} not in allowlist for '{table_name}'")


async def write_append(session: AsyncSession, table_name: str, records: list[dict],
                       metadata: MetaData) -> int:
    """INSERT OR IGNORE — used for OHLCV (append-only, skip duplicates)."""
    if not records:
        return 0
    table = _resolve_table(table_name, metadata)
    _validate_columns(list(records[0].keys()), table_name)
    stmt = insert(table).prefix_with("OR IGNORE")
    result = await session.execute(stmt, records)
    return result.rowcount


async def write_replace(session: AsyncSession, table_name: str, records: list[dict],
                        metadata: MetaData, filter_column: str = "") -> int:
    """DELETE + INSERT in transaction — used for positions (full refresh)."""
    table = _resolve_table(table_name, metadata)
    if filter_column:
        _validate_columns([filter_column], table_name)
    if filter_column and records:
        filter_values = list(set(r[filter_column] for r in records))
        col = table.c[filter_column]
        await session.execute(delete(table).where(col.in_(filter_values)))
    else:
        await session.execute(delete(table))
    return await write_append(session, table_name, records, metadata)


async def write_merge(session: AsyncSession, table_name: str, records: list[dict],
                      metadata: MetaData,
                      conflict_columns: list[str], update_columns: list[str]) -> int:
    """INSERT ON CONFLICT DO UPDATE — used for news (upsert).

    Uses SQLAlchemy's insert().on_conflict_do_update() instead of raw SQL.
    """
    if not records:
        return 0
    table = _resolve_table(table_name, metadata)
    _validate_columns(list(records[0].keys()) + conflict_columns + update_columns, table_name)
    stmt = insert(table)
    update_dict = {c: stmt.excluded[c] for c in update_columns}
    stmt = stmt.on_conflict_do_update(index_elements=conflict_columns, set_=update_dict)
    result = await session.execute(stmt, records)
    return result.rowcount
```

### 9.5e: Financial Precision Utilities

```python
# packages/core/src/zorivest_core/domain/precision.py

from decimal import Decimal, ROUND_HALF_UP

MICRO_SCALE = 1_000_000  # 6 decimal places


def to_micros(d: Decimal) -> int:
    """Convert a Decimal to integer micros (× 1,000,000)."""
    return int((d * MICRO_SCALE).to_integral_value(rounding=ROUND_HALF_UP))


def from_micros(i: int) -> Decimal:
    """Convert integer micros back to Decimal."""
    return Decimal(i) / MICRO_SCALE


def parse_monetary(value: str | float | int) -> Decimal:
    """Parse a monetary value to Decimal.

    Always uses string conversion to avoid float precision issues.
    """
    if isinstance(value, float):
        return Decimal(str(round(value, 10)))
    return Decimal(str(value))
```

---

## Step 9.6: Store Report Stage

### 9.6a: StoreReportStep Implementation

```python
# packages/core/src/zorivest_core/pipeline_steps/store_report_step.py

from pydantic import BaseModel, Field
from zorivest_core.domain.step_registry import RegisteredStep
from zorivest_core.domain.pipeline import StepContext, StepResult, PipelineStatus


class StoreReportStep(RegisteredStep):
    """Execute report queries, freeze results as data snapshot, persist report."""
    type_name = "store_report"
    side_effects = True

    class Params(BaseModel):
        report_name: str = Field(..., description="Human-readable report name")
        spec: dict = Field(..., description="Report specification DSL")
        data_queries: list[dict] = Field(default_factory=list, description="Named SQL queries")

    async def execute(self, params: dict, context: StepContext) -> StepResult:
        validated = self.Params(**params)

        # 1. Execute sandboxed SQL queries
        snapshots = {}
        for query_def in validated.data_queries:
            name = query_def["name"]
            sql = query_def["sql"]
            result = await self._execute_sandboxed_sql(sql)
            snapshots[name] = result

        # 2. Compute snapshot hash
        import hashlib, json
        snapshot_json = json.dumps(snapshots, sort_keys=True, separators=(",", ":"), default=str)
        snapshot_hash = hashlib.sha256(snapshot_json.encode()).hexdigest()

        # 3. Persist report
        report_id = await self._persist_report(
            name=validated.report_name,
            spec_json=json.dumps(validated.spec),
            snapshot_json=snapshot_json,
            snapshot_hash=snapshot_hash,
        )

        return StepResult(
            status=PipelineStatus.SUCCESS,
            output={"report_id": report_id, "snapshot_hash": snapshot_hash, "query_count": len(snapshots)},
        )

    async def _execute_sandboxed_sql(self, sql: str) -> list[dict]: ...
    async def _persist_report(self, **kwargs) -> str: ...
```

### 9.6b: Report Specification DSL

```python
# packages/core/src/zorivest_core/domain/report_spec.py

from __future__ import annotations
from typing import Any, Literal
from pydantic import BaseModel, Field


class DataTableSection(BaseModel):
    type: Literal["data_table"] = "data_table"
    title: str = ""
    named_query: str = Field(..., description="Key into data_queries")
    columns: list[str] = Field(default_factory=list)
    sort_by: str = ""
    max_rows: int = Field(default=100, ge=1, le=1000)


class MetricCardSection(BaseModel):
    type: Literal["metric_card"] = "metric_card"
    label: str
    named_query: str = Field(...)
    value_field: str = Field(...)
    format: str = Field(default="number", description="currency | percent | number")
    comparison_field: str = ""


class ChartSection(BaseModel):
    type: Literal["chart"] = "chart"
    title: str = ""
    chart_type: str = Field(..., description="candlestick | line | bar | pie")
    named_query: str
    x_field: str
    y_fields: list[str]
    height: int = Field(default=400, ge=200, le=800)


# Discriminated union of section types
ReportSection = DataTableSection | MetricCardSection | ChartSection


class ReportSpec(BaseModel):
    """Full report specification."""
    title: str
    subtitle: str = ""
    sections: list[ReportSection]
    page_orientation: str = Field(default="portrait")
    include_timestamp: bool = True
    include_page_numbers: bool = True
```

### 9.6c: SQL Sandboxing

```python
# packages/infrastructure/src/zorivest_infra/security/sql_sandbox.py

import sqlite3
from typing import Any

_ALLOWED_ACTIONS = {
    sqlite3.SQLITE_SELECT,
    sqlite3.SQLITE_READ,
    sqlite3.SQLITE_FUNCTION,
}


def report_authorizer(action: int, arg1: Any, arg2: Any, db_name: Any, trigger: Any) -> int:
    """SQLite authorizer callback for report SQL sandboxing.

    Default-deny: only SELECT, READ, and FUNCTION operations are allowed.
    """
    if action in _ALLOWED_ACTIONS:
        return sqlite3.SQLITE_OK
    return sqlite3.SQLITE_DENY


def create_sandboxed_connection(db_path: str, key: str) -> sqlite3.Connection:
    """Create a read-only, sandboxed SQLite connection for report queries."""
    conn = sqlite3.connect(db_path)
    conn.execute(f"PRAGMA key='{key}'")
    conn.execute("PRAGMA query_only = ON")
    conn.set_authorizer(report_authorizer)
    return conn
```

---

## Step 9.7: Render Stage

### 9.7a: RenderStep Implementation

```python
# packages/core/src/zorivest_core/pipeline_steps/render_step.py

from pydantic import BaseModel, Field
from zorivest_core.domain.step_registry import RegisteredStep
from zorivest_core.domain.pipeline import StepContext, StepResult, PipelineStatus


class RenderStep(RegisteredStep):
    """Render a report to HTML and/or PDF."""
    type_name = "render"
    side_effects = True  # Writes files to disk

    class Params(BaseModel):
        template: str = Field(default="base_report", description="Jinja2 template name")
        output_format: str = Field(default="both", description="html | pdf | both")
        chart_settings: dict = Field(default_factory=dict)

    async def execute(self, params: dict, context: StepContext) -> StepResult:
        validated = self.Params(**params)
        log = context.logger.bind(template=validated.template, format=validated.output_format)

        report_data = self._get_report_data(context)

        # Render HTML via Jinja2
        html = await self._render_html(report_data, validated)

        # Render PDF via WeasyPrint (if requested)
        pdf_path = None
        if validated.output_format in ("pdf", "both"):
            pdf_path = await self._render_pdf(html, report_data)

        output = {
            "html": html if validated.output_format in ("html", "both") else None,
            "pdf_path": pdf_path,
        }

        log.info("render_complete", html_len=len(html), pdf=pdf_path is not None)
        return StepResult(status=PipelineStatus.SUCCESS, output=output)

    def _get_report_data(self, context: StepContext) -> dict: ...
    async def _render_html(self, data: dict, params) -> str: ...
    async def _render_pdf(self, html: str, data: dict) -> str: ...
```

### 9.7b: Jinja2 Template System

```python
# packages/infrastructure/src/zorivest_infra/rendering/template_engine.py

from jinja2 import Environment, PackageLoader, select_autoescape
from datetime import datetime, timezone


def create_template_engine() -> Environment:
    """Create a Jinja2 environment for report templates."""
    env = Environment(
        loader=PackageLoader("zorivest_infra", "rendering/templates"),
        autoescape=select_autoescape(["html"]),
    )
    env.globals["now"] = lambda: datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    env.filters["currency"] = lambda v: f"${v:,.2f}" if v else "$0.00"
    env.filters["percent"] = lambda v: f"{v:.2f}%" if v else "0.00%"
    return env
```

### 9.7c: Plotly Chart Rendering

```python
# packages/infrastructure/src/zorivest_infra/rendering/chart_renderer.py

import plotly.graph_objects as go
import base64


def render_candlestick(data: list[dict], x_field: str, title: str = "", height: int = 400) -> dict:
    """Render a candlestick chart with dual output (interactive HTML + static PNG)."""
    fig = go.Figure(data=[go.Candlestick(
        x=[r[x_field] for r in data],
        open=[r["open"] for r in data],
        high=[r["high"] for r in data],
        low=[r["low"] for r in data],
        close=[r["close"] for r in data],
    )])
    fig.update_layout(title=title, height=height, template="plotly_white")

    html = fig.to_html(include_plotlyjs="cdn", full_html=False)
    png_bytes = fig.to_image(format="png", scale=2, engine="kaleido")
    png_b64 = base64.b64encode(png_bytes).decode()

    return {"html": html, "png_data_uri": f"data:image/png;base64,{png_b64}"}


CHART_RENDERERS = {
    "candlestick": render_candlestick,
    # "line", "bar", "pie" follow the same pattern
}
```

### 9.7d: WeasyPrint PDF Generation

```python
# packages/infrastructure/src/zorivest_infra/rendering/pdf_renderer.py

import weasyprint
import os


async def render_pdf(html: str, output_dir: str, report_id: str, version: int) -> str:
    """Convert HTML to PDF via WeasyPrint. Returns the absolute path."""
    os.makedirs(output_dir, exist_ok=True)
    pdf_path = os.path.join(output_dir, f"{report_id}_v{version}.pdf")
    try:
        doc = weasyprint.HTML(string=html)
        doc.write_pdf(pdf_path)
        return pdf_path
    except OSError as exc:
        raise RuntimeError(f"WeasyPrint PDF generation failed: {exc}") from exc
```

---

## Step 9.8: Send Stage

### 9.8a: SendStep Implementation

```python
# packages/core/src/zorivest_core/pipeline_steps/send_step.py

from pydantic import BaseModel, Field
from zorivest_core.domain.step_registry import RegisteredStep
from zorivest_core.domain.pipeline import StepContext, StepResult, PipelineStatus


class SendStep(RegisteredStep):
    """Deliver a rendered report via email or local file."""
    type_name = "send"
    side_effects = True

    class Params(BaseModel):
        channel: str = Field(..., description="email | local_file")
        recipients: list[str] = Field(default_factory=list, max_length=5)
        subject: str = Field(default="", description="Email subject (Jinja2 template)")
        body_template: str = Field(default="", description="Email body template name")

    async def execute(self, params: dict, context: StepContext) -> StepResult:
        validated = self.Params(**params)
        log = context.logger.bind(channel=validated.channel, recipients=len(validated.recipients))

        if validated.channel == "email":
            results = await self._send_emails(validated, context)
        elif validated.channel == "local_file":
            results = await self._save_local(validated, context)
        else:
            return StepResult(status=PipelineStatus.FAILED, error=f"Unknown channel: {validated.channel}")

        sent = sum(1 for r in results if r["status"] == "sent")
        failed = sum(1 for r in results if r["status"] == "failed")
        log.info("send_complete", sent=sent, failed=failed)

        return StepResult(
            status=PipelineStatus.SUCCESS if failed == 0 else PipelineStatus.FAILED,
            output={"deliveries": results, "sent": sent, "failed": failed},
        )

    async def _send_emails(self, params, context) -> list[dict]: ...
    async def _save_local(self, params, context) -> list[dict]: ...
```

### 9.8b: Async Email Delivery

```python
# packages/infrastructure/src/zorivest_infra/email/email_sender.py

import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.utils import formatdate
import structlog

logger = structlog.get_logger()


async def send_report_email(
    smtp_host: str, smtp_port: int, username: str, password: str,
    from_email: str, to_email: str, subject: str, html_body: str,
    pdf_path: str | None = None, use_tls: bool = True,
) -> tuple[bool, str]:
    """Send a report email with optional PDF attachment."""
    msg = MIMEMultipart("mixed")
    msg["From"] = from_email
    msg["To"] = to_email
    msg["Subject"] = subject
    msg["Date"] = formatdate(localtime=True)
    msg.attach(MIMEText(html_body, "html"))

    if pdf_path:
        with open(pdf_path, "rb") as f:
            pdf_part = MIMEApplication(f.read(), _subtype="pdf")
            import os
            pdf_part.add_header("Content-Disposition", "attachment", filename=os.path.basename(pdf_path))
            msg.attach(pdf_part)

    try:
        smtp = aiosmtplib.SMTP(hostname=smtp_host, port=smtp_port, use_tls=not use_tls)
        await smtp.connect()
        if use_tls:
            await smtp.starttls()
        await smtp.login(username, password)
        await smtp.send_message(msg)
        await smtp.quit()
        return True, "Email sent successfully"
    except aiosmtplib.SMTPException as exc:
        logger.error("email_failed", to=to_email, error=str(exc))
        return False, str(exc)
```

### 9.8c: Delivery Tracking

```python
# packages/infrastructure/src/zorivest_infra/email/delivery_tracker.py

import hashlib


def compute_dedup_key(report_id: str, channel: str, recipient: str, snapshot_hash: str) -> str:
    """SHA-256 idempotency key to prevent duplicate sends."""
    raw = f"{report_id}|{channel}|{recipient}|{snapshot_hash}"
    return hashlib.sha256(raw.encode()).hexdigest()
```

---

## Step 9.9: Security Guardrails

### 9.9a: SQL Authorizer (Detail)

Restatement of the authorizer from Step 9.6d with full implementation context. The `report_authorizer` callback is set on every connection used for report SQL queries:

- **Default-deny**: All actions except `SQLITE_SELECT`, `SQLITE_READ`, `SQLITE_FUNCTION` return `SQLITE_DENY`.
- **No `load_extension`**: SQLite's `enable_load_extension` is not called (disabled by default in Python's `sqlite3` module).
- **`PRAGMA query_only`**: Set on the connection as a secondary safety net.

### 9.9b: Pipeline Rate Limits

```python
# packages/core/src/zorivest_core/services/pipeline_guardrails.py

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class PipelineRateLimits:
    """Configurable rate limits for pipeline operations.

    Stored in settings table, checked before execution.
    """
    max_policy_creates_per_day: int = 20
    max_pipeline_executions_per_hour: int = 60
    max_emails_per_day: int = 50
    max_report_queries_per_hour: int = 100


class PipelineGuardrails:
    """Enforce rate limits and security policies."""

    def __init__(self, uow, limits: PipelineRateLimits | None = None):
        self.uow = uow
        self.limits = limits or PipelineRateLimits()

    async def check_can_create_policy(self) -> tuple[bool, str]:
        """Check if a new policy can be created within rate limits."""
        today_count = await self._count_audit_actions("policy.create", hours=24)
        if today_count >= self.limits.max_policy_creates_per_day:
            return False, f"Daily policy creation limit reached ({self.limits.max_policy_creates_per_day})"
        return True, ""

    async def check_can_execute(self) -> tuple[bool, str]:
        """Check if a pipeline can be executed within rate limits."""
        hour_count = await self._count_audit_actions("pipeline.run", hours=1)
        if hour_count >= self.limits.max_pipeline_executions_per_hour:
            return False, f"Hourly execution limit reached ({self.limits.max_pipeline_executions_per_hour})"
        return True, ""

    async def check_can_send_email(self) -> tuple[bool, str]:
        """Check if an email can be sent within rate limits."""
        today_count = await self._count_audit_actions("report.send", hours=24)
        if today_count >= self.limits.max_emails_per_day:
            return False, f"Daily email limit reached ({self.limits.max_emails_per_day})"
        return True, ""

    async def check_policy_approved(self, policy_id: str, content_hash: str) -> tuple[bool, str]:
        """Check if a policy is approved for execution.

        The content_hash at execution time must match the approved_hash.
        If the policy has been modified since approval, block execution.
        """
        policy = await self.uow.policies.get_by_id(policy_id)
        if not policy:
            return False, "Policy not found"
        if not policy.approved:
            return False, "Policy requires approval before execution"
        if policy.approved_hash != content_hash:
            return False, "Policy modified since approval — re-approval required"
        return True, ""

    async def _count_audit_actions(self, action: str, hours: int) -> int:
        """Count audit log entries for an action within a time window."""
        ...
```

### 9.9c: Human-in-the-Loop Approval

First execution of a new or modified policy requires GUI approval:

1. **Policy creation** → `PolicyModel.approved = False`, `approved_hash = None`
2. **Policy modification** → if `content_hash` changes from `approved_hash`, reset `approved = False`
3. **Execution attempt** → `PipelineGuardrails.check_policy_approved()` blocks unapproved policies
4. **GUI approval** → `POST /api/v1/scheduling/policies/{id}/approve` sets `approved = True`, `approved_hash = content_hash`, `approved_at = now()`

### 9.9d: Audit Trail

All policy CRUD, pipeline runs, and delivery events are logged to the append-only `audit_log` table (see 9.2i). Actions logged:

| Action | Resource Type | When |
|--------|---------------|------|
| `policy.create` | `policy` | New policy created |
| `policy.update` | `policy` | Policy modified |
| `policy.delete` | `policy` | Policy deleted |
| `policy.approve` | `policy` | Policy approved for execution |
| `pipeline.run` | `pipeline_run` | Pipeline execution started |
| `pipeline.complete` | `pipeline_run` | Pipeline execution finished |
| `report.render` | `report` | Report rendered |
| `report.send` | `report_delivery` | Report delivered |

---

## Step 9.10: REST API Endpoints

All routes under `/api/v1/scheduling/`:

```python
# packages/api/src/zorivest_api/routes/scheduling.py

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from datetime import datetime

scheduling_router = APIRouter(prefix="/api/v1/scheduling", tags=["scheduling"])


# --- Request/Response Models ---

class PolicyCreateRequest(BaseModel):
    policy_json: dict = Field(..., description="Full PolicyDocument JSON")

class PolicyResponse(BaseModel):
    id: str
    name: str
    schema_version: int
    enabled: bool
    approved: bool
    approved_at: datetime | None
    content_hash: str
    policy_json: dict  # Full PolicyDocument for round-trip editing
    created_at: datetime
    updated_at: datetime | None
    next_run: datetime | None = None

class PolicyListResponse(BaseModel):
    policies: list[PolicyResponse]
    total: int

class RunResponse(BaseModel):
    run_id: str
    policy_id: str
    status: str
    trigger_type: str
    started_at: datetime | None
    completed_at: datetime | None
    duration_ms: int | None
    error: str | None
    dry_run: bool

class StepResponse(BaseModel):
    step_id: str
    step_type: str
    status: str
    started_at: datetime | None
    completed_at: datetime | None
    duration_ms: int | None
    error: str | None
    attempt: int

class RunDetailResponse(RunResponse):
    steps: list[StepResponse]

class SchedulerStatusResponse(BaseModel):
    running: bool
    job_count: int
    jobs: list[dict]

class RunTriggerRequest(BaseModel):
    dry_run: bool = False


# --- Policy CRUD ---

@scheduling_router.post("/policies", response_model=PolicyResponse, status_code=201)
async def create_policy(req: PolicyCreateRequest, service=Depends(get_scheduling_service)):
    """Create and validate a new pipeline policy.

    Validates the policy JSON, computes content hash, stores in DB.
    Does NOT schedule — requires approval first.
    """
    result = await service.create_policy(req.policy_json)
    if result.errors:
        raise HTTPException(422, detail={"validation_errors": result.errors})
    return result.policy


@scheduling_router.get("/policies", response_model=PolicyListResponse)
async def list_policies(
    enabled_only: bool = Query(False),
    service=Depends(get_scheduling_service),
):
    """List all pipeline policies with schedule status."""
    policies = await service.list_policies(enabled_only=enabled_only)
    return PolicyListResponse(policies=policies, total=len(policies))


@scheduling_router.get("/policies/{policy_id}", response_model=PolicyResponse)
async def get_policy(policy_id: str, service=Depends(get_scheduling_service)):
    """Get a single policy by ID."""
    policy = await service.get_policy(policy_id)
    if not policy:
        raise HTTPException(404, detail="Policy not found")
    return policy


@scheduling_router.put("/policies/{policy_id}", response_model=PolicyResponse)
async def update_policy(
    policy_id: str, req: PolicyCreateRequest, service=Depends(get_scheduling_service),
):
    """Update an existing policy. Resets approval if content changed."""
    result = await service.update_policy(policy_id, req.policy_json)
    if result.errors:
        raise HTTPException(422, detail={"validation_errors": result.errors})
    return result.policy


@scheduling_router.delete("/policies/{policy_id}", status_code=204)
async def delete_policy(policy_id: str, service=Depends(get_scheduling_service)):
    """Delete a policy and unschedule its job."""
    await service.delete_policy(policy_id)


@scheduling_router.post("/policies/{policy_id}/approve", response_model=PolicyResponse)
async def approve_policy(policy_id: str, service=Depends(get_scheduling_service)):
    """Approve a policy for execution and schedule it."""
    policy = await service.approve_policy(policy_id)
    if not policy:
        raise HTTPException(404, detail="Policy not found")
    return policy


# --- Pipeline Execution ---

@scheduling_router.post("/policies/{policy_id}/run", response_model=RunResponse)
async def trigger_pipeline(
    policy_id: str, req: RunTriggerRequest, service=Depends(get_scheduling_service),
):
    """Manually trigger a pipeline run.

    Checks approval status and rate limits before execution.
    """
    result = await service.trigger_run(policy_id, dry_run=req.dry_run, trigger_type="manual")
    if result.error:
        raise HTTPException(400, detail=result.error)
    return result.run


# --- Run History ---

@scheduling_router.get("/policies/{policy_id}/runs", response_model=list[RunResponse])
async def get_policy_runs(
    policy_id: str,
    limit: int = Query(20, ge=1, le=100),
    service=Depends(get_scheduling_service),
):
    """Get execution history for a specific policy."""
    return await service.get_policy_runs(policy_id, limit=limit)


@scheduling_router.get("/runs/{run_id}", response_model=RunDetailResponse)
async def get_run_detail(run_id: str, service=Depends(get_scheduling_service)):
    """Get run detail including step-level status."""
    run = await service.get_run_detail(run_id)
    if not run:
        raise HTTPException(404, detail="Run not found")
    return run


@scheduling_router.get("/runs/{run_id}/steps", response_model=list[StepResponse])
async def get_run_steps(run_id: str, service=Depends(get_scheduling_service)):
    """Get step-level execution detail for a run."""
    return await service.get_run_steps(run_id)


# --- Scheduler Status ---

@scheduling_router.get("/scheduler/status", response_model=SchedulerStatusResponse)
async def get_scheduler_status(service=Depends(get_scheduling_service)):
    """Get scheduler status (running, job count, next fire times)."""
    return service.get_scheduler_status()


# --- Schema / Discovery ---

@scheduling_router.get("/policies/schema")
async def get_policy_schema():
    """Return JSON Schema for valid PolicyDocument objects."""
    return PolicyDocument.model_json_schema()


@scheduling_router.get("/step-types")
async def get_step_types():
    """List registered step types with their parameter schemas."""
    from zorivest_core.domain.step_registry import get_all_steps
    return [
        {"type": s.type_name, "params_schema": s.Params.model_json_schema()}
        for s in get_all_steps()
    ]


@scheduling_router.get("/runs", response_model=list[RunResponse])
async def list_runs(
    limit: int = Query(default=20, ge=1, le=100),
    service=Depends(get_scheduling_service),
):
    """List recent runs across all policies."""
    return await service.list_runs(limit=limit)


# --- Schedule Patch ---

@scheduling_router.patch("/policies/{policy_id}/schedule")
async def patch_policy_schedule(
    policy_id: str,
    cron_expression: str | None = None,
    enabled: bool | None = None,
    timezone: str | None = None,
    service=Depends(get_scheduling_service),
):
    """Patch schedule fields without round-tripping the full policy document."""
    return await service.patch_schedule(policy_id, cron_expression, enabled, timezone)
```

### API Endpoint Summary

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/policies` | Create policy (validates, stores, computes hash) |
| `GET` | `/policies` | List all policies |
| `GET` | `/policies/{id}` | Get policy detail |
| `PUT` | `/policies/{id}` | Update policy (resets approval if changed) |
| `DELETE` | `/policies/{id}` | Delete policy + unschedule |
| `POST` | `/policies/{id}/approve` | Approve policy for execution |
| `POST` | `/policies/{id}/run` | Trigger manual pipeline run |
| `GET` | `/policies/{id}/runs` | Get run history for a policy |
| `GET` | `/runs/{id}` | Get run detail with step status |
| `GET` | `/runs/{id}/steps` | Get step-level detail |
| `POST` | `/scheduler/power-event` | Receive OS power events (see 9.3f) |
| `GET` | `/scheduler/status` | Scheduler health + job info |
| `GET` | `/policies/schema` | JSON Schema for PolicyDocument |
| `GET` | `/step-types` | Registered step types with param schemas |
| `GET` | `/runs` | List recent runs across all policies |
| `PATCH` | `/policies/{id}/schedule` | Update schedule fields without full document round-trip |

---

## Step 9.11: MCP Tools (TypeScript)

### 9.11a: Tool Registrations

```typescript
// mcp-server/src/tools/scheduling-tools.ts

import { z } from 'zod';
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';

const API_BASE = process.env.ZORIVEST_API_URL || 'http://localhost:8765/api/v1';

export function registerSchedulingTools(server: McpServer) {

  // --- create_policy ---
  server.tool(
    'create_policy',
    'Create a new pipeline policy from a JSON document. Validates structure, step types, ref integrity, and cron expression.',
    {
      policy_json: z.object({
        name: z.string(),
        schema_version: z.number().default(1),
        trigger: z.object({
          cron_expression: z.string(),
          timezone: z.string().default('UTC'),
          enabled: z.boolean().default(true),
          coalesce: z.boolean().default(true),
          max_instances: z.number().default(1),
          misfire_grace_time: z.number().default(3600),
        }),
        steps: z.array(z.object({
          id: z.string(),
          type: z.string(),
          params: z.record(z.unknown()),
          on_error: z.enum(['fail_pipeline', 'log_and_continue', 'retry_then_fail']).default('fail_pipeline'),
          retry: z.object({
            max_attempts: z.number().default(1),
            backoff_seconds: z.number().default(2),
          }).optional(),
          skip_if: z.object({
            field: z.string(),
            operator: z.string(),
            value: z.unknown(),
          }).optional(),
        })),
      }).describe('Full PolicyDocument JSON object'),
    },
    async ({ policy_json }) => {
      const res = await fetch(`${API_BASE}/scheduling/policies`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ policy_json }),
      });
      const data = await res.json();
      if (!res.ok) {
        return { content: [{ type: 'text' as const, text: `Validation failed:\n${JSON.stringify(data, null, 2)}` }] };
      }
      return { content: [{ type: 'text' as const, text: `Policy created:\n${JSON.stringify(data, null, 2)}` }] };
    }
  );

  // --- list_policies ---
  server.tool(
    'list_policies',
    'List all pipeline policies with their schedule status, approval state, and next run time.',
    {
      enabled_only: z.boolean().default(false).describe('Filter to enabled policies only'),
    },
    async ({ enabled_only }) => {
      const res = await fetch(`${API_BASE}/scheduling/policies?enabled_only=${enabled_only}`);
      const data = await res.json();
      return { content: [{ type: 'text' as const, text: JSON.stringify(data, null, 2) }] };
    }
  );

  // --- run_pipeline ---
  server.tool(
    'run_pipeline',
    'Trigger a manual pipeline run for an approved policy. Returns run_id and initial status.',
    {
      policy_id: z.string().describe('Policy UUID to execute'),
      dry_run: z.boolean().default(false).describe('If true, skip steps with side effects'),
    },
    async ({ policy_id, dry_run }) => {
      const res = await fetch(`${API_BASE}/scheduling/policies/${policy_id}/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ dry_run }),
      });
      const data = await res.json();
      if (!res.ok) {
        return { content: [{ type: 'text' as const, text: `Run failed: ${JSON.stringify(data)}` }] };
      }
      return { content: [{ type: 'text' as const, text: `Pipeline triggered:\n${JSON.stringify(data, null, 2)}` }] };
    }
  );

  // --- preview_report ---
  server.tool(
    'preview_report',
    'Dry-run a pipeline and return the rendered HTML preview without sending emails or saving files.',
    {
      policy_id: z.string().describe('Policy UUID to preview'),
    },
    async ({ policy_id }) => {
      const res = await fetch(`${API_BASE}/scheduling/policies/${policy_id}/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ dry_run: true }),
      });
      const data = await res.json();
      return { content: [{ type: 'text' as const, text: `Preview result:\n${JSON.stringify(data, null, 2)}` }] };
    }
  );

  // --- update_policy_schedule ---
  server.tool(
    'update_policy_schedule',
    'Update a policy\'s schedule (cron expression, enable/disable, timezone).',
    {
      policy_id: z.string().describe('Policy UUID to update'),
      cron_expression: z.string().optional().describe('New 5-field cron expression'),
      enabled: z.boolean().optional().describe('Enable or disable the schedule'),
      timezone: z.string().optional().describe('IANA timezone (e.g. "America/New_York")'),
    },
    async ({ policy_id, cron_expression, enabled, timezone }) => {
      // First, get current policy
      const getRes = await fetch(`${API_BASE}/scheduling/policies/${policy_id}`);
      if (!getRes.ok) {
        return { content: [{ type: 'text' as const, text: 'Policy not found' }] };
      }
      const current = await getRes.json();
      const policy = JSON.parse(current.policy_json || '{}');

      // Apply updates
      if (cron_expression) policy.trigger.cron_expression = cron_expression;
      if (enabled !== undefined) policy.trigger.enabled = enabled;
      if (timezone) policy.trigger.timezone = timezone;

      const res = await fetch(`${API_BASE}/scheduling/policies/${policy_id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ policy_json: policy }),
      });
      const data = await res.json();
      return { content: [{ type: 'text' as const, text: `Updated:\n${JSON.stringify(data, null, 2)}` }] };
    }
  );

  // --- get_pipeline_history ---
  server.tool(
    'get_pipeline_history',
    'Get recent pipeline execution history with step-level detail.',
    {
      policy_id: z.string().optional().describe('Filter to a specific policy (optional)'),
      limit: z.number().default(10).describe('Number of recent runs to return'),
    },
    async ({ policy_id, limit }) => {
      const url = policy_id
        ? `${API_BASE}/scheduling/policies/${policy_id}/runs?limit=${limit}`
        : `${API_BASE}/scheduling/runs?limit=${limit}`;
      const res = await fetch(url);
      const data = await res.json();
      return { content: [{ type: 'text' as const, text: JSON.stringify(data, null, 2) }] };
    }
  );
}
```

### 9.11b: MCP Resources

```typescript
// mcp-server/src/tools/scheduling-tools.ts  (append)

export function registerSchedulingResources(server: McpServer) {
  // Pipeline policy JSON Schema
  server.resource(
    'pipeline://policies/schema',
    'JSON Schema for valid PolicyDocument objects',
    async () => {
      const res = await fetch(`${API_BASE}/scheduling/policies/schema`);
      const schema = await res.json();
      return { contents: [{ uri: 'pipeline://policies/schema', text: JSON.stringify(schema, null, 2), mimeType: 'application/json' }] };
    }
  );

  // Available step types with parameter schemas
  server.resource(
    'pipeline://step-types',
    'List of registered pipeline step types with their parameter schemas',
    async () => {
      const res = await fetch(`${API_BASE}/scheduling/step-types`);
      const types = await res.json();
      return { contents: [{ uri: 'pipeline://step-types', text: JSON.stringify(types, null, 2), mimeType: 'application/json' }] };
    }
  );
}
```

### MCP Tool Summary

| Tool | Description | Key Params |
|------|-------------|------------|
| `create_policy` | Validate + create policy JSON | `policy_json` |
| `list_policies` | List all policies with status | `enabled_only` |
| `run_pipeline` | Trigger manual run | `policy_id`, `dry_run` |
| `preview_report` | Dry-run pipeline, return preview | `policy_id` |
| `update_policy_schedule` | Update cron/enable/disable | `policy_id`, `cron_expression`, `enabled` |
| `get_pipeline_history` | Recent runs with step detail | `policy_id`, `limit` |

| Resource | URI | Description |
|----------|-----|-------------|
| Policy Schema | `pipeline://policies/schema` | JSON Schema for PolicyDocument |
| Step Types | `pipeline://step-types` | Registered step types + params |

---

## Step 9.12: GUI Scheduling Page Updates

Wire the existing [06e-gui-scheduling.md](06e-gui-scheduling.md) wireframes to the real REST API endpoints from Step 9.10. Additional GUI elements:

### 9.12a: Policy Approval Flow

When a policy is first created or modified, the GUI shows an approval banner:

```
┌─────────────────────────────────────────────┐
│ ⚠️ Policy "Daily Performance Report" needs  │
│    approval before it can execute.           │
│                                              │
│    [Review Policy JSON]  [Approve] [Reject]  │
└─────────────────────────────────────────────┘
```

- **Review Policy JSON**: Opens a read-only JSON viewer showing the full policy document.
- **Approve**: Calls `POST /api/v1/scheduling/policies/{id}/approve`, sets `approved = true`.
- **Reject**: No API call; leaves policy in unapproved state.

### 9.12b: Step-Level Run Detail Panel

When viewing a pipeline run, the GUI shows a step progress visualization:

```
┌──────────────────────────────────────────────────────────┐
│  Run #a1b2c3   │  Status: ✅ SUCCESS  │  Duration: 4.2s │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  ✅ fetch_prices     │ 1.2s │ 42 records fetched         │
│  ✅ transform_data   │ 0.8s │ 42 rows written, 0 quarant │
│  ✅ store_report     │ 0.3s │ hash: 9f3a...              │
│  ✅ render_pdf       │ 1.5s │ PDF: 2 pages               │
│  ✅ send_email       │ 0.4s │ 1 sent, 0 failed           │
│                                                          │
│  [View Report]  [Download PDF]  [View Audit Log]         │
└──────────────────────────────────────────────────────────┘
```

Each step row shows status icon, step ID, duration, and output summary. Failed steps show the error message in red.

### 9.12c: Endpoint Wiring

Update existing `06e-gui-scheduling.md` wireframe actions:

| GUI Action | REST Endpoint | MCP Tool |
|------------|---------------|----------|
| Create/Edit schedule form → Save | `POST/PUT /scheduling/policies` | `create_policy` |
| Enable/Disable toggle | `PUT /scheduling/policies/{id}` | `update_policy_schedule` |
| "Run Now" button | `POST /scheduling/policies/{id}/run` | `run_pipeline` |
| Schedule list (with next run time) | `GET /scheduling/policies` | `list_policies` |
| Run history table | `GET /scheduling/policies/{id}/runs` | `get_pipeline_history` |
| Run detail panel (with step progress) | `GET /scheduling/runs/{id}` | — |
| Approve policy | `POST /scheduling/policies/{id}/approve` | — |

---

## Test Plan

> Test strategy details will be incorporated during implementation planning per user request.

| Area | Focus | Type |
|------|-------|------|
| Policy validation | Schema, refs, cron, blocklist | Unit |
| Step registry | Auto-registration, lookup, listing | Unit |
| PipelineRunner | Sequential execution, retry, skip, dry-run, resume | Integration |
| RefResolver | Nested paths, error cases | Unit |
| ConditionEvaluator | All 10 operators | Unit |
| APScheduler | Schedule/unschedule, next fire time, zombie recovery | Integration |
| Fetch stage | Cache hit/miss, rate limiting, HTTP revalidation | Integration (mocked HTTP) |
| Transform stage | Field mapping, validation, write dispositions | Integration |
| Store Report | SQL sandbox, snapshot hash, provenance | Integration |
| Render stage | HTML output, PDF generation, cache key | Integration |
| Send stage | Email delivery, idempotent dedup, local file | Integration |
| Security | Rate limits, approval flow, audit log | Integration |
| REST API | All 12 endpoints | E2E |
| MCP tools | All 6 tools, 2 resources | E2E |

---

## Exit Criteria

- [ ] All domain models (enums, Pydantic, dataclasses) pass `pyright` type checks
- [ ] All 9 SQLAlchemy models create tables successfully in SQLCipher
- [ ] Temporal triggers (report versioning, audit append-only) fire correctly
- [ ] PipelineRunner executes a 5-step policy end-to-end (fetch → transform → store → render → send)
- [ ] APScheduler schedules, fires, and persists jobs across process restart
- [ ] Zombie detection marks orphaned runs as FAILED on startup
- [ ] Sleep/wake IPC handler triggers APScheduler wakeup
- [ ] SQL sandbox denies INSERT/UPDATE/DELETE in report queries
- [ ] Rate limits block excessive policy creation, execution, and email sending
- [ ] Human-in-the-loop blocks unapproved / modified policies from executing
- [ ] All 16 REST endpoints return correct response models
- [ ] All 6 MCP tools and 2 resources respond correctly
- [ ] GUI approval flow, step-level detail panel, and schedule CRUD work end-to-end
- [ ] `ruff check`, `pytest`, `tsc --noEmit`, `vitest`, `npm run build` all pass (no regressions)

---

## Library Stack (Locked)

| Library | Version | Purpose |
|---------|---------|---------|
| `apscheduler` | 3.x | Cron scheduling with SQLAlchemy job store |
| `httpx` | latest | Async HTTP client for fetch stage |
| `aiolimiter` | latest | Leaky bucket rate limiter |
| `tenacity` | latest | Retry with exponential backoff |
| `structlog` | latest | Structured async-safe logging |
| `pandera` | latest | DataFrame validation |
| `weasyprint` | latest | HTML → PDF rendering |
| `plotly` | latest | Chart generation |
| `kaleido` | v1 | Plotly static image export |
| `jinja2` | latest | HTML template engine |
| `aiosmtplib` | latest | Async SMTP email delivery |
| `pydantic` | v2 | Schema validation (already in project) |
