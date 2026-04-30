# packages/api/src/zorivest_api/routes/scheduling.py
"""REST API routes for the Scheduling & Pipeline Engine (Phase 9, §9.10).

16 endpoints under /api/v1/scheduling/ for policy CRUD, pipeline execution,
run history, scheduler status, schema discovery, and schedule patching.

Spec: 09-scheduling.md §9.10
MEU: MEU-89 (scheduling-api-mcp)
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Path, Query

from zorivest_api.middleware.approval_token import validate_approval_token
from pydantic import BaseModel, Field, field_validator
from pydantic.functional_validators import BeforeValidator
from typing import Annotated

from zorivest_api.dependencies import (
    get_policy_emulator,
    get_scheduling_service,
    get_session_budget,
    get_sql_sandbox,
    get_template_repo,
)
from zorivest_api.schemas.template_schemas import (
    EmailTemplateCreateRequest,
    EmailTemplateUpdateRequest,
    EmulateRequest,
    PreviewRequest,
    ValidateSqlRequest,
)


scheduling_router = APIRouter(prefix="/api/v1/scheduling", tags=["scheduling"])


# ── Request/Response Models ─────────────────────────────────────────────


def _strip_whitespace(v: object) -> object:
    """Strip leading/trailing whitespace so min_length=1 rejects blank strings."""
    return v.strip() if isinstance(v, str) else v


StrippedStr = Annotated[str, BeforeValidator(_strip_whitespace)]


class PolicyCreateRequest(BaseModel):
    """Request body for creating or updating a policy."""

    model_config = {"extra": "forbid"}

    policy_json: dict[str, Any] = Field(..., description="Full PolicyDocument JSON")

    @field_validator("policy_json")
    @classmethod
    def policy_json_must_be_non_empty(cls, v: dict[str, Any]) -> dict[str, Any]:
        if not v:
            msg = "policy_json must not be empty"
            raise ValueError(msg)
        return v


class PolicyResponse(BaseModel):
    """Response for a single policy."""

    id: str
    name: str
    schema_version: int
    enabled: bool
    approved: bool
    approved_at: datetime | None = None
    content_hash: str
    policy_json: dict[str, Any]
    created_at: datetime
    updated_at: datetime | None = None
    next_run: datetime | None = None


class PolicyListResponse(BaseModel):
    """Response for listing policies."""

    policies: list[PolicyResponse]
    total: int


class RunResponse(BaseModel):
    """Response for a pipeline run."""

    run_id: str
    policy_id: str
    status: str
    trigger_type: str
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_ms: int | None = None
    error: str | None = None
    dry_run: bool


class StepResponse(BaseModel):
    """Response for a step within a run."""

    step_id: str
    step_type: str
    status: str
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_ms: int | None = None
    error: str | None = None
    attempt: int


class RunDetailResponse(RunResponse):
    """Run detail including step-level status."""

    steps: list[StepResponse] = Field(default_factory=list)


class SchedulerStatusResponse(BaseModel):
    """Scheduler diagnostics response."""

    running: bool
    job_count: int
    jobs: list[dict[str, Any]]


class RunTriggerRequest(BaseModel):
    """Request body for triggering a pipeline run."""

    model_config = {"extra": "forbid"}

    dry_run: bool = False


# ── Policy CRUD ─────────────────────────────────────────────────────────


@scheduling_router.post("/policies", response_model=PolicyResponse, status_code=201)
async def create_policy(
    req: PolicyCreateRequest,
    service: Any = Depends(get_scheduling_service),
) -> Any:
    """Create and validate a new pipeline policy."""
    result = await service.create_policy(req.policy_json)
    if result.errors:
        raise HTTPException(422, detail={"validation_errors": result.errors})
    return result.policy


@scheduling_router.get("/policies", response_model=PolicyListResponse)
async def list_policies(
    enabled_only: bool = Query(False),
    service: Any = Depends(get_scheduling_service),
) -> PolicyListResponse:
    """List all pipeline policies with schedule status."""
    policies = await service.list_policies(enabled_only=enabled_only)
    return PolicyListResponse(policies=policies, total=len(policies))


@scheduling_router.get("/policies/schema")
async def get_policy_schema() -> dict[str, Any]:
    """Return JSON Schema for valid PolicyDocument objects."""
    from zorivest_core.domain.pipeline import PolicyDocument

    return PolicyDocument.model_json_schema()


@scheduling_router.get("/policies/{policy_id}", response_model=PolicyResponse)
async def get_policy(
    policy_id: str,
    service: Any = Depends(get_scheduling_service),
) -> Any:
    """Get a single policy by ID."""
    policy = await service.get_policy(policy_id)
    if not policy:
        raise HTTPException(404, detail="Policy not found")
    return policy


@scheduling_router.put("/policies/{policy_id}", response_model=PolicyResponse)
async def update_policy(
    policy_id: str,
    req: PolicyCreateRequest,
    service: Any = Depends(get_scheduling_service),
) -> Any:
    """Update an existing policy. Resets approval if content changed."""
    result = await service.update_policy(policy_id, req.policy_json)
    if result.errors:
        raise HTTPException(422, detail={"validation_errors": result.errors})
    return result.policy


@scheduling_router.delete("/policies/{policy_id}", status_code=204)
async def delete_policy(
    policy_id: str,
    service: Any = Depends(get_scheduling_service),
) -> None:
    """Delete a policy and unschedule its job."""
    await service.delete_policy(policy_id)


@scheduling_router.post("/policies/{policy_id}/approve", response_model=PolicyResponse)
async def approve_policy(
    policy_id: str,
    _token: None = Depends(validate_approval_token),
    service: Any = Depends(get_scheduling_service),
) -> Any:
    """Approve a policy for execution and schedule it."""
    policy = await service.approve_policy(policy_id)
    if not policy:
        raise HTTPException(404, detail="Policy not found")
    return policy


# ── Pipeline Execution ──────────────────────────────────────────────────


@scheduling_router.post("/policies/{policy_id}/run", response_model=RunResponse)
async def trigger_pipeline(
    policy_id: str,
    req: RunTriggerRequest,
    _token: None = Depends(validate_approval_token),
    service: Any = Depends(get_scheduling_service),
) -> Any:
    """Manually trigger a pipeline run.

    Requires a CSRF approval token from the Electron GUI to prevent
    AI agents from bypassing the MCP confirmation gate via direct API calls.
    """
    result = await service.trigger_run(
        policy_id, dry_run=req.dry_run, trigger_type="manual"
    )
    if result.error:
        raise HTTPException(400, detail=result.error)
    return result.run


@scheduling_router.post("/runs/{run_id}/cancel")
async def cancel_run(
    run_id: str = Path(
        ...,
        pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    ),
    service: Any = Depends(get_scheduling_service),
) -> dict[str, Any]:
    """Cancel a running pipeline.

    Idempotent: calling on already-cancelled/completed run returns 200.
    Returns 404 if run_id not found, 422 if run_id is not a valid UUID.
    """
    result = await service.cancel_run(run_id)
    if result.error and "not found" in result.error.lower():
        raise HTTPException(404, detail=result.error)
    if result.error:
        raise HTTPException(400, detail=result.error)
    return {"run_id": run_id, "status": result.run.get("status", "cancelling")}


# ── Run History ─────────────────────────────────────────────────────────


@scheduling_router.get("/policies/{policy_id}/runs", response_model=list[RunResponse])
async def get_policy_runs(
    policy_id: str,
    limit: int = Query(20, ge=1, le=100),
    service: Any = Depends(get_scheduling_service),
) -> list[Any]:
    """Get execution history for a specific policy."""
    return await service.get_policy_runs(policy_id, limit=limit)


@scheduling_router.get("/runs", response_model=list[RunResponse])
async def list_runs(
    limit: int = Query(default=20, ge=1, le=100),
    service: Any = Depends(get_scheduling_service),
) -> list[Any]:
    """List recent runs across all policies."""
    return await service.list_runs(limit=limit)


@scheduling_router.get("/runs/{run_id}", response_model=RunDetailResponse)
async def get_run_detail(
    run_id: str,
    service: Any = Depends(get_scheduling_service),
) -> Any:
    """Get run detail including step-level status."""
    run = await service.get_run_detail(run_id)
    if not run:
        raise HTTPException(404, detail="Run not found")
    return run


@scheduling_router.get("/runs/{run_id}/steps", response_model=list[StepResponse])
async def get_run_steps(
    run_id: str,
    service: Any = Depends(get_scheduling_service),
) -> list[Any]:
    """Get step-level execution detail for a run."""
    return await service.get_run_steps(run_id)


# ── Scheduler Status ───────────────────────────────────────────────────


@scheduling_router.get("/scheduler/status", response_model=SchedulerStatusResponse)
async def get_scheduler_status(
    service: Any = Depends(get_scheduling_service),
) -> dict[str, Any]:
    """Get scheduler status (running, job count, next fire times)."""
    return service.get_scheduler_status()


# ── Schema / Discovery ─────────────────────────────────────────────────


@scheduling_router.get("/step-types")
async def get_step_types() -> list[dict[str, Any]]:
    """List registered step types with their parameter schemas."""
    from zorivest_core.domain.step_registry import get_all_steps

    results: list[dict[str, Any]] = []
    for s in get_all_steps():
        params_cls = getattr(s, "Params", None)
        results.append(
            {
                "type": s.type_name,
                "params_schema": params_cls.model_json_schema()
                if params_cls is not None
                else {},
            }
        )
    return results


# ── Schedule Patch ──────────────────────────────────────────────────────


@scheduling_router.patch("/policies/{policy_id}/schedule")
async def patch_policy_schedule(
    policy_id: str,
    cron_expression: str | None = Query(default=None, min_length=1),
    enabled: bool | None = None,
    timezone: str | None = Query(default=None, min_length=1),
    service: Any = Depends(get_scheduling_service),
) -> Any:
    """Patch schedule fields without round-tripping the full policy document."""
    # Strip whitespace and reject blank-after-strip strings
    if cron_expression is not None:
        cron_expression = cron_expression.strip()
        if not cron_expression:
            raise HTTPException(422, detail="cron_expression must not be blank")
    if timezone is not None:
        timezone = timezone.strip()
        if not timezone:
            raise HTTPException(422, detail="timezone must not be blank")
    result = await service.patch_schedule(policy_id, cron_expression, enabled, timezone)
    if result is None:
        raise HTTPException(404, detail="Policy not found")
    return result


# ── PH9: Emulator ──────────────────────────────────────────────────────


@scheduling_router.post("/emulator/run")
async def emulator_run(
    req: "EmulateRequest",
    emulator: Any = Depends(get_policy_emulator),
    budget: Any = Depends(get_session_budget),
) -> Any:
    """Run the policy emulator on a JSON policy document.

    Returns a structured EmulatorResult with errors, warnings, and mock outputs.
    Phase subset execution supported via the ``phases`` field.
    Budget enforcement: records response bytes and rate per policy hash.
    MEU-PH9, AC-16, F1 (budget enforcement on runtime path).
    """
    import hashlib
    import json as _json

    from zorivest_core.services.sql_sandbox import SecurityError

    result = await emulator.emulate(req.policy_json, phases=req.phases)
    response_payload = result.model_dump()

    # Compute stable hash for budget tracking
    policy_hash = hashlib.sha256(
        _json.dumps(req.policy_json, sort_keys=True).encode()
    ).hexdigest()
    response_bytes = len(_json.dumps(response_payload).encode())

    try:
        budget.check_budget(policy_hash, response_bytes)
    except SecurityError as exc:
        raise HTTPException(429, detail=str(exc)) from exc

    return response_payload


@scheduling_router.get("/emulator/mock-data")
async def get_emulator_mock_data() -> dict[str, Any]:
    """Return sample mock data sets per step type for emulator SIMULATE phase.

    Used by the ``pipeline://emulator/mock-data`` MCP resource to show AI agents
    what synthetic data the emulator produces for each step type.
    MEU-PH9, AC-27 (R1 correction).
    """
    from zorivest_core.services.policy_emulator import _get_mock_output

    step_types = ("fetch", "query", "transform", "compose", "send")
    return {st: _get_mock_output(st) for st in step_types}


@scheduling_router.post("/validate-sql")
async def validate_sql(
    req: "ValidateSqlRequest",
    sandbox: Any = Depends(get_sql_sandbox),
) -> dict[str, Any]:
    """Validate a SQL query against the sandbox allowlist.

    Returns {valid: bool, errors: list[str]}.
    MEU-PH9, AC-17.
    """
    errors = sandbox.validate_sql(req.sql)
    return {"valid": len(errors) == 0, "errors": errors}


# ── PH9: Schema Discovery ──────────────────────────────────────────────


@scheduling_router.get("/db-schema")
async def get_db_schema(
    sandbox: Any = Depends(get_sql_sandbox),
) -> list[dict[str, Any]]:
    """Return database table/column schemas, DENY_TABLES excluded.

    MEU-PH9, AC-19.
    """
    tables = sandbox.list_tables()

    result: list[dict[str, Any]] = []
    for table_name in tables:
        columns = sandbox.table_info(table_name)
        result.append({"name": table_name, "columns": columns})
    return result


@scheduling_router.get("/db-schema/samples/{table}")
async def get_db_row_samples(
    table: str = Path(...),
    limit: int = Query(default=5, ge=1, le=20),
    sandbox: Any = Depends(get_sql_sandbox),
) -> list[dict[str, Any]]:
    """Return sample rows from a table.

    Security: allowlist-only approach. Only tables present in list_tables()
    (DENY_TABLES excluded) are accepted. Query executes through sandbox.execute().
    MEU-PH9, AC-20, F3 (SQL injection hardening).
    """
    from zorivest_core.services.sql_sandbox import SqlSandbox

    if table in SqlSandbox.DENY_TABLES:
        raise HTTPException(403, detail=f"Access denied: table '{table}' is restricted")

    allowed_tables = sandbox.list_tables()
    if table not in allowed_tables:
        raise HTTPException(404, detail=f"Table '{table}' not found")

    try:
        # Execute through the sandbox's public API
        rows = sandbox.execute(
            f'SELECT * FROM "{table}" LIMIT :limit',  # noqa: S608
            {"limit": limit},
        )
        return rows
    except Exception as exc:
        raise HTTPException(400, detail=str(exc)) from exc


# ── PH9: Template CRUD ─────────────────────────────────────────────────


@scheduling_router.post("/templates", status_code=201)
async def create_email_template(
    req: "EmailTemplateCreateRequest",
    repo: Any = Depends(get_template_repo),
) -> dict[str, Any]:
    """Create a new email template.

    MEU-PH9, AC-21.
    """
    import json
    from datetime import datetime as _dt, timezone as _tz
    from zorivest_infra.database.models import EmailTemplateModel

    # Check for duplicate
    existing = repo.get_by_name(req.name)
    if existing is not None:
        raise HTTPException(409, detail=f"Template '{req.name}' already exists")

    model = EmailTemplateModel(
        name=req.name,
        description=req.description,
        subject_template=req.subject_template,
        body_html=req.body_html,
        body_format=req.body_format,
        required_variables=json.dumps(req.required_variables),
        sample_data_json=req.sample_data_json,
        created_at=_dt.now(_tz.utc),
    )
    repo.create(model)
    return _template_to_response(repo.get_by_name(req.name))


@scheduling_router.get("/templates")
async def list_email_templates(
    repo: Any = Depends(get_template_repo),
) -> list[dict[str, Any]]:
    """List all email templates.

    MEU-PH9, AC-23.
    """
    templates = repo.list_all()
    return [_template_dto_to_response(t) for t in templates]


@scheduling_router.get("/templates/{name}")
async def get_email_template(
    name: str = Path(...),
    repo: Any = Depends(get_template_repo),
) -> dict[str, Any]:
    """Get a single email template by name.

    MEU-PH9, AC-22.
    """
    template = repo.get_by_name(name)
    if template is None:
        raise HTTPException(404, detail=f"Template '{name}' not found")
    return _template_dto_to_response(template)


@scheduling_router.patch("/templates/{name}")
async def update_email_template(
    name: str = Path(...),
    req: "EmailTemplateUpdateRequest" = ...,  # type: ignore[assignment]
    repo: Any = Depends(get_template_repo),
) -> dict[str, Any]:
    """Update an existing email template by name.

    MEU-PH9, AC-24.
    """
    existing = repo.get_by_name(name)
    if existing is None:
        raise HTTPException(404, detail=f"Template '{name}' not found")

    import json

    update_fields: dict[str, Any] = {}
    if req.description is not None:
        update_fields["description"] = req.description
    if req.subject_template is not None:
        update_fields["subject_template"] = req.subject_template
    if req.body_html is not None:
        update_fields["body_html"] = req.body_html
    if req.body_format is not None:
        update_fields["body_format"] = req.body_format
    if req.required_variables is not None:
        update_fields["required_variables"] = json.dumps(req.required_variables)
    if req.sample_data_json is not None:
        update_fields["sample_data_json"] = req.sample_data_json

    if update_fields:
        repo.update(name, **update_fields)

    return _template_to_response(repo.get_by_name(name))


@scheduling_router.delete("/templates/{name}", status_code=204)
async def delete_email_template(
    name: str = Path(...),
    repo: Any = Depends(get_template_repo),
) -> None:
    """Delete an email template by name. Rejects default templates with 403.

    MEU-PH9, AC-30m.
    """
    existing = repo.get_by_name(name)
    if existing is None:
        raise HTTPException(404, detail=f"Template '{name}' not found")

    try:
        repo.delete(name)
    except ValueError as e:
        if "default" in str(e).lower():
            raise HTTPException(
                403, detail=f"Cannot delete default template: {name}"
            ) from e
        raise HTTPException(400, detail=str(e)) from e


@scheduling_router.post("/templates/{name}/preview")
async def preview_email_template(
    name: str = Path(...),
    req: "PreviewRequest" = ...,  # type: ignore[assignment]
    repo: Any = Depends(get_template_repo),
) -> dict[str, Any]:
    """Preview a template rendered with sample or provided data.

    MEU-PH9, AC-25.
    """
    import json

    from zorivest_core.services.secure_jinja import HardenedSandbox

    template = repo.get_by_name(name)
    if template is None:
        raise HTTPException(404, detail=f"Template '{name}' not found")

    # Build context: use provided data or fall back to sample_data_json
    context: dict[str, Any] = {}
    if req.data:
        context = req.data
    elif template.sample_data_json:
        context = json.loads(template.sample_data_json)

    sandbox = HardenedSandbox()
    rendered = sandbox.render_safe(template.body_html, context)
    subject_rendered = None
    if template.subject_template:
        subject_rendered = sandbox.render_safe(template.subject_template, context)

    return {
        "name": name,
        "subject_rendered": subject_rendered,
        "body_rendered": rendered,
    }


# ── PH9 Helpers ─────────────────────────────────────────────────────────


def _template_to_response(template: Any) -> dict[str, Any]:
    """Convert template DTO or dict to response dict."""
    if template is None:
        return {}
    if hasattr(template, "name"):
        return _template_dto_to_response(template)
    return template


def _template_dto_to_response(dto: Any) -> dict[str, Any]:
    """Convert EmailTemplateDTO to response dict."""
    return {
        "name": dto.name,
        "description": dto.description,
        "subject_template": dto.subject_template,
        "body_html": dto.body_html,
        "body_format": dto.body_format,
        "required_variables": dto.required_variables,
        "sample_data_json": dto.sample_data_json,
        "is_default": dto.is_default,
    }
