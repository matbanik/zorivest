# packages/core/src/zorivest_core/services/scheduling_service.py
"""SchedulingService facade for the Scheduling & Pipeline Engine (Phase 9, §9.10).

Coordinates policy repos, pipeline execution, scheduling, guardrails,
and auditing behind a single service interface consumed by REST routes.

Spec: 09-scheduling.md §9.10
MEU: MEU-89 (scheduling-api-mcp)
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Protocol

import structlog

from zorivest_core.domain.pipeline import PolicyDocument
from zorivest_core.domain.policy_validator import validate_policy
from zorivest_core.services.pipeline_guardrails import PipelineGuardrails


logger = structlog.get_logger()


# ---------------------------------------------------------------------------
# Protocols for injected dependencies
# ---------------------------------------------------------------------------


class PolicyStore(Protocol):
    """Policy persistence port."""

    async def create(self, data: dict[str, Any]) -> dict[str, Any]: ...
    async def get_by_id(self, policy_id: str) -> dict[str, Any] | None: ...
    async def list_all(self, enabled_only: bool = False) -> list[dict[str, Any]]: ...
    async def update(
        self, policy_id: str, data: dict[str, Any]
    ) -> dict[str, Any] | None: ...
    async def delete(self, policy_id: str) -> None: ...


class RunStore(Protocol):
    """Pipeline run persistence port."""

    async def create(self, data: dict[str, Any]) -> dict[str, Any]: ...
    async def get_by_id(self, run_id: str) -> dict[str, Any] | None: ...
    async def list_for_policy(
        self, policy_id: str, limit: int = 20
    ) -> list[dict[str, Any]]: ...
    async def list_recent(self, limit: int = 20) -> list[dict[str, Any]]: ...
    async def update(
        self, run_id: str, data: dict[str, Any]
    ) -> dict[str, Any] | None: ...


class StepStore(Protocol):
    """Pipeline step persistence port."""

    async def list_for_run(self, run_id: str) -> list[dict[str, Any]]: ...


class AuditLogger(Protocol):
    """Audit log port."""

    async def log(
        self,
        action: str,
        resource_type: str,
        resource_id: str,
        details: dict[str, Any] | None = None,
    ) -> None: ...


# ---------------------------------------------------------------------------
# Result envelope dataclasses
# ---------------------------------------------------------------------------


@dataclass
class PolicyResult:
    """Result of a policy create/update operation."""

    policy: dict[str, Any] | None = None
    errors: list[str] = field(default_factory=list)


@dataclass
class RunResult:
    """Result of a pipeline trigger operation."""

    run: dict[str, Any] | None = None
    error: str | None = None


# ---------------------------------------------------------------------------
# SchedulingService facade
# ---------------------------------------------------------------------------


class SchedulingService:
    """Facade coordinating all scheduling operations.

    Consumed by REST API routes. Delegates to:
    - PolicyStore: CRUD for policy models
    - RunStore: pipeline run records
    - StepStore: step-level run detail
    - PipelineRunner: actual execution
    - SchedulerService: APScheduler management
    - PipelineGuardrails: rate limits + approval checks
    - AuditLogger: append-only audit trail
    """

    def __init__(
        self,
        policy_store: PolicyStore,
        run_store: RunStore,
        step_store: StepStore,
        pipeline_runner: Any,
        scheduler_service: Any,
        guardrails: PipelineGuardrails,
        audit_logger: AuditLogger,
    ) -> None:
        self._policies = policy_store
        self._runs = run_store
        self._steps = step_store
        self._runner = pipeline_runner
        self._scheduler = scheduler_service
        self._guardrails = guardrails
        self._audit = audit_logger

    # ── Policy CRUD ────────────────────────────────────────────────────

    async def create_policy(self, policy_json: dict[str, Any]) -> PolicyResult:
        """Validate, store, and return a new policy."""
        # Validate via domain validator
        try:
            doc = PolicyDocument(**policy_json)
        except Exception as e:
            return PolicyResult(errors=[str(e)])

        errors = validate_policy(doc)
        if errors:
            return PolicyResult(errors=[e.message for e in errors])

        # Check rate limit
        ok, msg = await self._guardrails.check_can_create_policy()
        if not ok:
            return PolicyResult(errors=[msg])

        content_hash = _compute_hash(policy_json)
        policy_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        data = {
            "id": policy_id,
            "name": doc.name,
            "schema_version": doc.schema_version,
            "enabled": doc.trigger.enabled,
            "approved": False,
            "approved_at": None,
            "approved_hash": None,
            "content_hash": content_hash,
            "policy_json": policy_json,
            "created_at": now,
            "updated_at": None,
            "next_run": None,
        }

        result = await self._policies.create(data)
        await self._audit.log("policy.create", "policy", policy_id)
        return PolicyResult(policy=result)

    async def list_policies(self, enabled_only: bool = False) -> list[dict[str, Any]]:
        """List all policies, enriched with live next_run from scheduler."""
        policies = await self._policies.list_all(enabled_only=enabled_only)
        if self._scheduler:
            for p in policies:
                pid = p.get("id", "")
                if pid:
                    next_fire = self._scheduler.get_next_run(pid)
                    p["next_run"] = next_fire.isoformat() if next_fire else None
        return policies

    async def get_policy(self, policy_id: str) -> dict[str, Any] | None:
        """Get a single policy by ID, enriched with live next_run."""
        policy = await self._policies.get_by_id(policy_id)
        if policy and self._scheduler:
            next_fire = self._scheduler.get_next_run(policy_id)
            policy["next_run"] = next_fire.isoformat() if next_fire else None
        return policy

    async def update_policy(
        self, policy_id: str, policy_json: dict[str, Any]
    ) -> PolicyResult:
        """Update a policy, resetting approval if content changed."""
        existing = await self._policies.get_by_id(policy_id)
        if not existing:
            return PolicyResult(errors=["Policy not found"])

        try:
            doc = PolicyDocument(**policy_json)
        except Exception as e:
            return PolicyResult(errors=[str(e)])

        errors = validate_policy(doc)
        if errors:
            return PolicyResult(errors=[e.message for e in errors])

        new_hash = _compute_hash(policy_json)
        old_hash = existing.get("content_hash", "")

        update_data: dict[str, Any] = {
            "name": doc.name,
            "schema_version": doc.schema_version,
            "enabled": doc.trigger.enabled,
            "content_hash": new_hash,
            "policy_json": policy_json,
            "updated_at": datetime.now(timezone.utc),
        }

        # Reset approval if content changed
        if new_hash != old_hash:
            update_data["approved"] = False
            update_data["approved_at"] = None
            update_data["approved_hash"] = None
            self._scheduler.unschedule_policy(policy_id)

        result = await self._policies.update(policy_id, update_data)
        await self._audit.log("policy.update", "policy", policy_id)
        return PolicyResult(policy=result)

    async def delete_policy(self, policy_id: str) -> None:
        """Delete a policy and unschedule its job."""
        self._scheduler.unschedule_policy(policy_id)
        await self._policies.delete(policy_id)
        await self._audit.log("policy.delete", "policy", policy_id)

    async def approve_policy(self, policy_id: str) -> dict[str, Any] | None:
        """Approve a policy for execution.

        Sets approved=True and recomputes the content hash.
        Does NOT auto-schedule — the enabled flag is controlled
        separately via patch_schedule, giving the GUI explicit
        control over Draft → Ready vs Draft → Scheduled transitions.
        """
        policy = await self._policies.get_by_id(policy_id)
        if not policy:
            return None

        # Recompute content_hash through the canonical Pydantic path
        # to ensure approved_hash matches what the runner will compute.
        policy_json = policy.get("policy_json", {})
        canonical_hash = _compute_hash(policy_json)

        now = datetime.now(timezone.utc)
        update_data = {
            "approved": True,
            "approved_at": now,
            "approved_hash": canonical_hash,
            "content_hash": canonical_hash,  # sync stored hash too
        }
        result = await self._policies.update(policy_id, update_data)

        # Schedule only if the policy is already enabled (e.g. re-approval
        # after content edit on a previously-scheduled policy)
        pj = policy.get("policy_json", {})
        trigger = pj.get("trigger", {})
        is_enabled = policy.get("enabled", False) or trigger.get("enabled", False)
        cron = trigger.get("cron_expression", "")
        if is_enabled and cron:
            tz = trigger.get("timezone", "UTC")
            self._scheduler.schedule_policy(
                policy_name=policy.get("name", ""),
                policy_id=policy_id,
                cron_expression=cron,
                timezone=tz,
            )

        await self._audit.log("policy.approve", "policy", policy_id)
        return result

    # ── Pipeline Execution ─────────────────────────────────────────────

    async def trigger_run(
        self,
        policy_id: str,
        dry_run: bool = False,
        trigger_type: str = "manual",
    ) -> RunResult:
        """Trigger a pipeline run with guardrail checks."""
        policy = await self._policies.get_by_id(policy_id)
        if not policy:
            return RunResult(error="Policy not found")

        content_hash = policy.get("content_hash", "")

        # Check approval
        ok, msg = await self._guardrails.check_policy_approved(
            policy_id,
            content_hash,
        )
        if not ok:
            return RunResult(error=msg)

        # Check rate limit
        ok, msg = await self._guardrails.check_can_execute()
        if not ok:
            return RunResult(error=msg)

        run_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        run_data = {
            "run_id": run_id,
            "policy_id": policy_id,
            "status": "pending",
            "trigger_type": trigger_type,
            "content_hash": content_hash,
            "started_at": now,
            "completed_at": None,
            "duration_ms": None,
            "error": None,
            "dry_run": dry_run,
        }

        result = await self._runs.create(run_data)
        await self._audit.log("pipeline.run", "pipeline_run", run_id)

        # Execute pipeline via runner — runner owns status transitions
        # (pending → running → success/failed)
        if self._runner is not None:
            policy_json = policy.get("policy_json", {})
            try:
                doc = PolicyDocument(**policy_json)

                # §9C.3c: Build approval provenance snapshot from persisted state
                from zorivest_core.domain.approval_snapshot import ApprovalSnapshot

                approval_snapshot = ApprovalSnapshot(
                    approved=bool(policy.get("approved", False)),
                    approved_hash=policy.get("approved_hash"),
                    approved_at=policy.get("approved_at"),
                )

                run_result = await self._runner.run(
                    policy=doc,
                    trigger_type=trigger_type,
                    dry_run=dry_run,
                    policy_id=policy_id,
                    run_id=run_id,
                    approval_snapshot=approval_snapshot,
                )
                # Runner finalized the record; reflect status in response
                result.update(
                    {
                        "status": run_result.get("status", "success"),
                        "error": run_result.get("error"),
                    }
                )
            except Exception as exc:
                # Runner crashed before finalizing — service catches as fallback
                final_status = "failed"
                run_error = str(exc)
                logger.error("pipeline_run_failed", run_id=run_id, error=str(exc))
                completed_at = datetime.now(timezone.utc)
                duration_ms = int((completed_at - now).total_seconds() * 1000)
                await self._runs.update(
                    run_id,
                    {
                        "status": final_status,
                        "completed_at": completed_at,
                        "duration_ms": duration_ms,
                        "error": run_error,
                    },
                )
                result.update(
                    {
                        "status": final_status,
                        "completed_at": completed_at,
                        "duration_ms": duration_ms,
                        "error": run_error,
                    }
                )

        return RunResult(run=result)

    async def cancel_run(self, run_id: str) -> RunResult:
        """Cancel a running pipeline run.

        Per spec §9B.5e:
        - Returns RunResult(error="Run not found") if run_id doesn't exist.
        - For terminal states (success/failed/cancelled), returns the run
          idempotently without calling runner.cancel_run().
        - For non-terminal states, delegates to PipelineRunner.cancel_run().
        """
        run = await self._runs.get_by_id(run_id)
        if not run:
            return RunResult(error="Run not found")

        status = run.get("status", "")
        if status in ("success", "failed", "cancelled"):
            # Already terminal — return current state idempotently
            return RunResult(run=run)

        if self._runner is not None:
            await self._runner.cancel_run(run_id)

        await self._audit.log("pipeline.cancel", "pipeline_run", run_id)

        # Re-fetch updated status
        updated_run = await self._runs.get_by_id(run_id)
        return RunResult(run=updated_run)

    # ── Run History ────────────────────────────────────────────────────

    async def get_policy_runs(
        self, policy_id: str, limit: int = 20
    ) -> list[dict[str, Any]]:
        """Get execution history for a specific policy."""
        return await self._runs.list_for_policy(policy_id, limit=limit)

    async def get_run_detail(self, run_id: str) -> dict[str, Any] | None:
        """Get run detail including step-level status."""
        run = await self._runs.get_by_id(run_id)
        if not run:
            return None
        steps = await self._steps.list_for_run(run_id)
        run["steps"] = steps
        return run

    async def get_run_steps(self, run_id: str) -> list[dict[str, Any]]:
        """Get step-level execution detail for a run."""
        return await self._steps.list_for_run(run_id)

    async def list_runs(self, limit: int = 20) -> list[dict[str, Any]]:
        """List recent runs across all policies."""
        return await self._runs.list_recent(limit=limit)

    # ── Scheduler Status ───────────────────────────────────────────────

    def get_scheduler_status(self) -> dict[str, Any]:
        """Get scheduler status (running, job count, next fire times)."""
        return self._scheduler.get_status()

    # ── Schedule Patch ─────────────────────────────────────────────────

    async def patch_schedule(
        self,
        policy_id: str,
        cron_expression: str | None = None,
        enabled: bool | None = None,
        tz_name: str | None = None,
    ) -> dict[str, Any] | None:
        """Patch schedule fields without round-tripping the full policy document."""
        policy = await self._policies.get_by_id(policy_id)
        if not policy:
            return None

        update_data: dict[str, Any] = {"updated_at": datetime.now(tz=timezone.utc)}
        pj = dict(policy.get("policy_json", {}))
        trigger = dict(pj.get("trigger", {}))

        if cron_expression is not None:
            trigger["cron_expression"] = cron_expression
        if enabled is not None:
            update_data["enabled"] = enabled
            trigger["enabled"] = enabled
        if tz_name is not None:
            trigger["timezone"] = tz_name

        pj["trigger"] = trigger
        update_data["policy_json"] = pj

        # compute_content_hash already normalizes trigger.enabled,
        # so we can hash the policy_json directly.
        new_hash = _compute_hash(pj)
        update_data["content_hash"] = new_hash

        # Reset approval only if actual content changed (cron, timezone, etc.)
        # NOT when only enabled changed
        old_hash = policy.get("content_hash", "")
        if new_hash != old_hash:
            update_data["approved"] = False
            update_data["approved_at"] = None
            update_data["approved_hash"] = None

        result = await self._policies.update(policy_id, update_data)

        # Determine effective enabled state
        effective_enabled = (
            enabled if enabled is not None else trigger.get("enabled", True)
        )

        # Schedule or unschedule based on approval + enabled state
        is_approved = policy.get("approved") and new_hash == old_hash
        if is_approved and effective_enabled:
            self._scheduler.schedule_policy(
                policy_name=policy.get("name", ""),
                policy_id=policy_id,
                cron_expression=trigger.get("cron_expression", ""),
                timezone=trigger.get("timezone", "UTC"),
            )
        elif is_approved and not effective_enabled:
            self._scheduler.unschedule_policy(policy_id)
        elif new_hash != old_hash:
            self._scheduler.unschedule_policy(policy_id)

        return result


def _compute_hash(policy_json: dict[str, Any]) -> str:
    """Compute deterministic content hash for a policy JSON.

    Delegates to ``compute_content_hash`` to ensure the same canonical
    representation (Pydantic model_dump) is used everywhere — both at
    policy creation/approval time and at pipeline execution time.
    """
    from zorivest_core.domain.policy_validator import compute_content_hash

    doc = PolicyDocument(**policy_json)
    return compute_content_hash(doc)
