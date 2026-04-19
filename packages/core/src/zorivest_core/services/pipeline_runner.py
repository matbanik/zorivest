"""Pipeline execution engine (§9.3a).

Sequential async executor for pipeline policies. Handles:
- Ref resolution (params with { "ref": "ctx.x" })
- Skip conditions (skip_if evaluation)
- Error modes (fail, log+continue, retry)
- Dry-run mode (skip steps with side_effects=True)
- Resume from failure (re-execute from last failed step)
- Persistence hooks for run/step tracking
- Zombie recovery (§9.3e)
"""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from datetime import datetime, timezone
from typing import Any

import structlog

from zorivest_core.domain.enums import PipelineStatus, StepErrorMode
from zorivest_core.domain.pipeline import (
    PolicyDocument,
    PolicyStep,
    StepContext,
    StepResult,
)
from zorivest_core.domain.step_registry import get_step


logger = structlog.get_logger()


def _safe_json_output(output: dict | None) -> str | None:
    """Serialize step output to JSON, handling bytes values.

    Addresses [PIPE-CHARMAP] secondary issue: bytes objects in step
    output from HTTP responses crash json.dumps(). Also handles
    datetime serialization.
    """
    if not output:
        return None

    def _default_serializer(obj: Any) -> Any:
        if isinstance(obj, bytes):
            return obj.decode("utf-8", errors="replace")
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

    return json.dumps(output, default=_default_serializer)


class PipelineRunner:
    """Sequential async executor for pipeline policies.

    Runs steps in order, passing a shared StepContext. Handles:
    - Ref resolution (params with { "ref": "ctx.x" })
    - Skip conditions (skip_if evaluation)
    - Error modes (fail, log+continue, retry)
    - Dry-run mode (skip steps with side_effects=True)
    - Resume from failure (re-execute from last failed step)
    - Persistence hooks for run/step tracking
    - Zombie recovery (§9.3e)
    """

    def __init__(
        self,
        uow: Any,
        ref_resolver: Any,
        condition_evaluator: Any,
        *,
        delivery_repository: Any | None = None,
        smtp_config: Any | None = None,
        provider_adapter: Any | None = None,
        db_writer: Any | None = None,
        db_connection: Any | None = None,
        report_repository: Any | None = None,
        template_engine: Any | None = None,
        pipeline_state_repo: Any | None = None,
        fetch_cache_repo: Any | None = None,
    ) -> None:
        self.uow = uow
        self.ref_resolver = ref_resolver
        self.condition_evaluator = condition_evaluator
        self._delivery_repository = delivery_repository
        self._smtp_config = smtp_config
        self._provider_adapter = provider_adapter
        self._db_writer = db_writer
        self._db_connection = db_connection
        self._report_repository = report_repository
        self._template_engine = template_engine
        self._pipeline_state_repo = pipeline_state_repo
        self._fetch_cache_repo = fetch_cache_repo

    async def run(
        self,
        policy: PolicyDocument,
        trigger_type: str,
        dry_run: bool = False,
        resume_from: str | None = None,
        actor: str = "",
        policy_id: str = "",
        run_id: str = "",
    ) -> dict[str, Any]:
        """Execute a full pipeline.

        Args:
            policy: Validated PolicyDocument to execute.
            trigger_type: "scheduled", "manual", or "mcp".
            dry_run: If True, skip steps with side_effects=True.
            resume_from: Step ID to resume from (skip prior successful steps).
            actor: Who triggered this run.
            policy_id: Stored policy ID (PolicyModel.id) for FK references.
            run_id: Pre-created run record ID from SchedulingService.
                    When non-empty, skips _create_run_record() and updates
                    the existing record to RUNNING status.

        Returns:
            Dict with run_id, status, duration_ms, error, steps.
        """
        from zorivest_core.domain.policy_validator import compute_content_hash

        # Use provided run_id or generate a new one (backward compat)
        externally_created = bool(run_id)
        if not run_id:
            run_id = str(uuid.uuid4())
        content_hash = compute_content_hash(policy)
        run_log = structlog.get_logger().bind(run_id=run_id, policy=policy.name)

        # Build initial outputs with injected service dependencies
        _dep_map: dict[str, Any | None] = {
            "delivery_repository": self._delivery_repository,
            "smtp_config": self._smtp_config,
            "provider_adapter": self._provider_adapter,
            "db_writer": self._db_writer,
            "db_connection": self._db_connection,
            "report_repository": self._report_repository,
            "template_engine": self._template_engine,
            "pipeline_state_repo": self._pipeline_state_repo,
            "fetch_cache_repo": self._fetch_cache_repo,
        }
        initial_outputs: dict[str, Any] = {
            k: v for k, v in _dep_map.items() if v is not None
        }

        context = StepContext(
            run_id=run_id,
            policy_id=policy_id or policy.name,
            outputs=initial_outputs,
            dry_run=dry_run,
            logger=run_log,
        )

        # Persist run record — conditional on whether run_id was pre-created
        if externally_created:
            # Pre-created by SchedulingService: just update to RUNNING
            await self._update_run_status(run_id, PipelineStatus.RUNNING)
        else:
            await self._create_run_record(
                run_id,
                policy_id or policy.name,
                trigger_type,
                dry_run,
                actor,
                content_hash,
            )

        run_start = time.monotonic()
        final_status = PipelineStatus.SUCCESS
        run_error: str | None = None
        skipping = resume_from is not None

        try:
            for step_def in policy.steps:
                # Resume logic: skip until we reach the resume step
                if skipping:
                    if step_def.id == resume_from:
                        skipping = False
                    else:
                        prior_output = await self._load_prior_output(
                            run_id,
                            step_def.id,
                        )
                        if prior_output is not None:
                            context.outputs[step_def.id] = prior_output
                        continue

                step_result = await self._execute_step(step_def, context, run_id)

                if step_result.status == PipelineStatus.FAILED:
                    if step_def.on_error == StepErrorMode.FAIL_PIPELINE:
                        final_status = PipelineStatus.FAILED
                        run_error = f"Step '{step_def.id}' failed: {step_result.error}"
                        run_log.error(
                            "pipeline_failed",
                            step=step_def.id,
                            error=step_result.error,
                        )
                        break
                    elif step_def.on_error == StepErrorMode.LOG_AND_CONTINUE:
                        run_log.warning(
                            "step_failed_continuing",
                            step=step_def.id,
                            error=step_result.error,
                        )
                    elif step_def.on_error == StepErrorMode.RETRY_THEN_FAIL:
                        # Retries were exhausted inside _execute_step
                        final_status = PipelineStatus.FAILED
                        run_error = (
                            f"Step '{step_def.id}' failed after retries: "
                            f"{step_result.error}"
                        )
                        run_log.error(
                            "pipeline_failed_after_retries",
                            step=step_def.id,
                            error=step_result.error,
                        )
                        break

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

        # Finalize run record
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
        if step_def.skip_if and self.condition_evaluator.evaluate(
            step_def.skip_if, context
        ):
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
            log.info(
                "step_dry_run_skipped",
                reason="side_effects=True in dry-run mode",
            )
            result = StepResult(status=PipelineStatus.SKIPPED, output={"dry_run": True})
            await self._persist_step(run_id, step_def, result, attempt=0)
            return result

        # 4. Resolve refs in params
        resolved_params = self.ref_resolver.resolve(step_def.params, context)

        # 5. Execute with retry
        last_result = StepResult(status=PipelineStatus.FAILED, error="No attempts made")
        max_attempts = (
            step_def.retry.max_attempts
            if step_def.on_error == StepErrorMode.RETRY_THEN_FAIL
            else 1
        )

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
                log.info(
                    "step_success",
                    duration_ms=last_result.duration_ms,
                    attempt=attempt,
                )
                break
            elif attempt < max_attempts:
                import random

                wait = step_def.retry.backoff_factor**attempt
                if step_def.retry.jitter:
                    wait *= 0.5 + random.random()  # noqa: S311
                log.warning(
                    "step_retry",
                    attempt=attempt,
                    wait_seconds=round(wait, 1),
                )
                await asyncio.sleep(wait)

        return last_result

    # ── Persistence Hooks ─────────────────────────────────────────────────

    async def _create_run_record(
        self,
        run_id: str,
        policy_id: str,
        trigger_type: str,
        dry_run: bool,
        actor: str,
        content_hash: str,
    ) -> None:
        """Persist the initial pipeline_run row."""
        if self.uow is None:
            return
        self.uow.pipeline_runs.create(
            id=run_id,
            policy_id=policy_id,
            status=PipelineStatus.RUNNING.value,
            trigger_type=trigger_type,
            content_hash=content_hash,
            dry_run=dry_run,
            created_by=actor,
        )
        self.uow.commit()

    async def _update_run_status(
        self,
        run_id: str,
        status: PipelineStatus,
    ) -> None:
        """Update the status of an existing pipeline_run record.

        Used when the run record was pre-created by SchedulingService
        (e.g., transitioning from 'pending' to 'running').
        """
        if self.uow is None:
            return
        self.uow.pipeline_runs.update_status(run_id, status=status.value)
        self.uow.commit()

    async def _persist_step(
        self,
        run_id: str,
        step_def: PolicyStep,
        result: StepResult,
        attempt: int,
    ) -> None:
        """Persist a pipeline_step row."""
        if self.uow is None:
            return
        from zorivest_infra.database.models import PipelineStepModel

        step_row = PipelineStepModel(
            id=str(uuid.uuid4()),
            run_id=run_id,
            step_id=step_def.id,
            step_type=step_def.type,
            status=result.status.value,
            attempt=attempt,
            output_json=_safe_json_output(result.output),
            error=result.error,
            started_at=result.started_at,
            completed_at=result.completed_at,
            duration_ms=result.duration_ms,
        )
        self.uow._session.add(step_row)  # noqa: SLF001
        self.uow._session.flush()  # noqa: SLF001

    async def _finalize_run(
        self,
        run_id: str,
        status: PipelineStatus,
        error: str | None,
        duration_ms: int,
    ) -> None:
        """Update the pipeline_run row with final status."""
        if self.uow is None:
            return
        self.uow.pipeline_runs.update_status(
            run_id,
            status=status.value,
            error=error,
            duration_ms=duration_ms,
        )
        self.uow.commit()

    async def _load_prior_output(self, run_id: str, step_id: str) -> dict | None:
        """Load a prior successful step output for resume."""
        if self.uow is None:
            return None
        from zorivest_infra.database.models import PipelineStepModel

        row = (
            self.uow._session.query(PipelineStepModel)  # noqa: SLF001
            .filter_by(
                run_id=run_id,
                step_id=step_id,
                status=PipelineStatus.SUCCESS.value,
            )
            .order_by(PipelineStepModel.attempt.desc())
            .first()
        )
        if row is not None and row.output_json:
            return json.loads(row.output_json)
        return None

    # ── Zombie Recovery (§9.3e) ───────────────────────────────────────────

    async def recover_zombies(self) -> list[dict]:
        """Scan for orphaned RUNNING pipeline runs at startup.

        Called once during FastAPI lifespan startup. For each zombie:
        - Mark FAILED + log warning/error depending on side_effects

        Returns list of recovered run summaries.
        """
        if self.uow is None:
            return []

        zombies = self.uow.pipeline_runs.find_zombies()
        recovered = []

        for run in zombies:
            # Find the last step executed for this run
            from zorivest_infra.database.models import PipelineStepModel

            last_step = (
                self.uow._session.query(PipelineStepModel)  # noqa: SLF001
                .filter_by(run_id=run.id)
                .order_by(PipelineStepModel.attempt.desc())
                .first()
            )

            step_cls = get_step(last_step.step_type) if last_step else None
            has_side_effects = step_cls.side_effects if step_cls else True

            self.uow.pipeline_runs.update_status(
                run.id,
                status=PipelineStatus.FAILED.value,
                error=(
                    f"Zombie recovery: process terminated during step "
                    f"'{last_step.step_id if last_step else 'unknown'}'"
                ),
            )

            severity = "error" if has_side_effects else "warning"
            logger.log(
                severity,
                "zombie_recovered",
                run_id=run.id,
                last_step=last_step.step_id if last_step else None,
                side_effects=has_side_effects,
            )
            recovered.append({"run_id": run.id, "side_effects": has_side_effects})

        if recovered:
            self.uow.commit()

        return recovered
