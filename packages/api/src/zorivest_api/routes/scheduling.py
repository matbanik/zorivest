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

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from zorivest_api.dependencies import get_scheduling_service


scheduling_router = APIRouter(prefix="/api/v1/scheduling", tags=["scheduling"])


# ── Request/Response Models ─────────────────────────────────────────────


class PolicyCreateRequest(BaseModel):
    """Request body for creating or updating a policy."""

    policy_json: dict[str, Any] = Field(..., description="Full PolicyDocument JSON")


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
    service: Any = Depends(get_scheduling_service),
) -> Any:
    """Manually trigger a pipeline run."""
    result = await service.trigger_run(
        policy_id, dry_run=req.dry_run, trigger_type="manual"
    )
    if result.error:
        raise HTTPException(400, detail=result.error)
    return result.run


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
    cron_expression: str | None = None,
    enabled: bool | None = None,
    timezone: str | None = None,
    service: Any = Depends(get_scheduling_service),
) -> Any:
    """Patch schedule fields without round-tripping the full policy document."""
    result = await service.patch_schedule(policy_id, cron_expression, enabled, timezone)
    if result is None:
        raise HTTPException(404, detail="Policy not found")
    return result
