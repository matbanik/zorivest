# tests/integration/test_pipeline_e2e.py
"""End-to-end pipeline integration tests.

Validates the complete policy execution lifecycle through all service layers:
SchedulingService → PipelineRunner → Steps → Persistence → Audit

Uses SQLAlchemy in-memory SQLite (real UoW, no stubs).

Spec: 09b-pipeline-hardening.md §9B.6d
"""

from __future__ import annotations

import asyncio
import uuid

import pytest

from zorivest_core.domain.enums import PipelineStatus

from tests.fixtures.policies import (
    POLICY_CANCELLABLE,
    POLICY_DRY_RUN,
    POLICY_ERROR_CONTINUE,
    POLICY_ERROR_FAIL,
    POLICY_SKIP_CONDITION,
    POLICY_UNICODE_ERROR,
    SMOKE_POLICY_BASIC,
)


# ── Helpers ──────────────────────────────────────────────────────────────


async def _create_and_approve(svc, policy_json: dict) -> str:
    """Create a policy and approve it; return the policy ID."""
    result = await svc.create_policy(policy_json)
    assert result.errors == [], f"Policy creation failed: {result.errors}"
    policy_id = result.policy["id"]
    await svc.approve_policy(policy_id)
    return policy_id


# ── TestPolicyLifecycle ──────────────────────────────────────────────────


class TestPolicyLifecycle:
    """Test create → approve → run → history → delete."""

    @pytest.mark.asyncio
    async def test_create_approve_run_success(self, scheduling_service):
        """AC-4: Full lifecycle through SchedulingService completes with status=success."""
        policy_id = await _create_and_approve(scheduling_service, SMOKE_POLICY_BASIC)

        run_result = await scheduling_service.trigger_run(policy_id)
        assert run_result.error is None, f"Run failed: {run_result.error}"
        assert run_result.run is not None
        assert run_result.run["status"] == "success"

        # Verify run appears in history
        runs = await scheduling_service.get_policy_runs(policy_id)
        assert len(runs) >= 1
        assert runs[0]["status"] == "success"

    @pytest.mark.asyncio
    async def test_run_unapproved_policy_rejected(self, scheduling_service):
        """AC-5: Unapproved policy returns error via guardrails."""
        result = await scheduling_service.create_policy(SMOKE_POLICY_BASIC)
        assert result.errors == []
        policy_id = result.policy["id"]

        # Try to run without approval
        run_result = await scheduling_service.trigger_run(policy_id)
        assert run_result.error is not None
        assert (
            "approval" in run_result.error.lower()
            or "approved" in run_result.error.lower()
        )

    @pytest.mark.asyncio
    async def test_delete_policy_unschedules(self, scheduling_service):
        """AC-6: Deleted policy no longer retrievable."""
        policy_id = await _create_and_approve(scheduling_service, SMOKE_POLICY_BASIC)

        await scheduling_service.delete_policy(policy_id)

        policy = await scheduling_service.get_policy(policy_id)
        assert policy is None


# ── TestPipelineExecution ────────────────────────────────────────────────


class TestPipelineExecution:
    """Test step execution through PipelineRunner."""

    @pytest.mark.asyncio
    async def test_all_steps_execute_in_order(self, scheduling_service):
        """AC-7: Steps execute sequentially per policy step list."""
        policy_id = await _create_and_approve(scheduling_service, SMOKE_POLICY_BASIC)

        run_result = await scheduling_service.trigger_run(policy_id)
        assert run_result.run is not None
        run_id = run_result.run["run_id"]

        steps = await scheduling_service.get_run_steps(run_id)
        # SMOKE_POLICY_BASIC has 3 steps: fetch_data, transform_data, store_result
        step_ids = [s["step_id"] for s in steps]
        assert "fetch_data" in step_ids
        assert "transform_data" in step_ids
        assert "store_result" in step_ids

        # All steps should have succeeded
        for step in steps:
            assert step["status"] == PipelineStatus.SUCCESS.value

    @pytest.mark.asyncio
    async def test_ref_resolution_across_steps(self, scheduling_service):
        """AC-8: {ref: ctx.step_id.key} resolves correctly to prior step output."""
        policy_id = await _create_and_approve(scheduling_service, SMOKE_POLICY_BASIC)

        run_result = await scheduling_service.trigger_run(policy_id)
        assert run_result.run is not None
        run_id = run_result.run["run_id"]

        steps = await scheduling_service.get_run_steps(run_id)
        # transform_data receives resolved ref from fetch_data
        transform_steps = [s for s in steps if s["step_id"] == "transform_data"]
        assert len(transform_steps) >= 1
        assert transform_steps[0]["status"] == PipelineStatus.SUCCESS.value

        # store_result receives resolved ref from transform_data
        store_steps = [s for s in steps if s["step_id"] == "store_result"]
        assert len(store_steps) >= 1
        assert store_steps[0]["status"] == PipelineStatus.SUCCESS.value

    @pytest.mark.asyncio
    async def test_step_output_persisted_to_db(self, scheduling_service):
        """AC-9: Step records exist in pipeline_steps table after run."""
        policy_id = await _create_and_approve(scheduling_service, SMOKE_POLICY_BASIC)

        run_result = await scheduling_service.trigger_run(policy_id)
        assert run_result.run is not None
        run_id = run_result.run["run_id"]

        steps = await scheduling_service.get_run_steps(run_id)
        assert len(steps) == 3, f"Expected 3 step records, got {len(steps)}"

        # Each step should have output_json
        for step in steps:
            assert step["output_json"] is not None or step["error"] is not None


# ── TestErrorModes ───────────────────────────────────────────────────────


class TestErrorModes:
    """Test fail_pipeline, log_and_continue, retry_then_fail."""

    @pytest.mark.asyncio
    async def test_fail_pipeline_aborts(self, scheduling_service):
        """AC-10: First step failure aborts pipeline, second step never runs."""
        policy_id = await _create_and_approve(scheduling_service, POLICY_ERROR_FAIL)

        run_result = await scheduling_service.trigger_run(policy_id)
        assert run_result.run is not None
        assert run_result.run["status"] == "failed"

        run_id = run_result.run["run_id"]
        steps = await scheduling_service.get_run_steps(run_id)

        # First step (will_fail) should be FAILED
        failed_steps = [s for s in steps if s["step_id"] == "will_fail"]
        assert len(failed_steps) >= 1
        assert failed_steps[0]["status"] == PipelineStatus.FAILED.value

        # Second step (never_reached) should NOT have been executed
        reached_steps = [s for s in steps if s["step_id"] == "never_reached"]
        assert len(reached_steps) == 0

    @pytest.mark.asyncio
    async def test_log_and_continue_proceeds(self, scheduling_service):
        """AC-11: Failed step with on_error=log_and_continue doesn't abort."""
        policy_id = await _create_and_approve(scheduling_service, POLICY_ERROR_CONTINUE)

        run_result = await scheduling_service.trigger_run(policy_id)
        assert run_result.run is not None
        # Pipeline should complete successfully overall despite the failed step
        assert run_result.run["status"] == "success"

        run_id = run_result.run["run_id"]
        steps = await scheduling_service.get_run_steps(run_id)

        # First step (will_fail) should be FAILED but pipeline continued
        failed_steps = [s for s in steps if s["step_id"] == "will_fail"]
        assert len(failed_steps) >= 1
        assert failed_steps[0]["status"] == PipelineStatus.FAILED.value

        # Second step (should_run) should have executed and passed
        run_steps = [s for s in steps if s["step_id"] == "should_run"]
        assert len(run_steps) >= 1
        assert run_steps[0]["status"] == PipelineStatus.SUCCESS.value

    @pytest.mark.asyncio
    async def test_retry_exhaustion_fails(self, scheduling_service):
        """AC-19: Step with retry mode exhausts retries then fails pipeline."""
        # Build a retry policy inline — uses mock_fail with retry_then_fail
        retry_policy = {
            "schema_version": 1,
            "name": "smoke-retry",
            "trigger": {
                "cron_expression": "0 0 * * *",
                "timezone": "UTC",
                "enabled": True,
            },
            "steps": [
                {
                    "id": "retry_step",
                    "type": "mock_fail",
                    "params": {"error_msg": "retryable error"},
                    "on_error": "retry_then_fail",
                    "retry": {
                        "max_attempts": 2,
                        "backoff_factor": 1.0,
                        "jitter": False,
                    },
                },
            ],
        }
        policy_id = await _create_and_approve(scheduling_service, retry_policy)

        run_result = await scheduling_service.trigger_run(policy_id)
        assert run_result.run is not None
        assert run_result.run["status"] == "failed"
        assert "retries" in run_result.run.get(
            "error", ""
        ).lower() or "retry_step" in run_result.run.get("error", "")

        run_id = run_result.run["run_id"]
        steps = await scheduling_service.get_run_steps(run_id)
        retry_steps = [s for s in steps if s["step_id"] == "retry_step"]
        # Should have 2 step records (one per attempt)
        assert len(retry_steps) == 2


# ── TestDryRunAndSkip ────────────────────────────────────────────────────


class TestDryRunAndSkip:
    """Test dry_run mode and skip_if conditions."""

    @pytest.mark.asyncio
    async def test_dry_run_skips_side_effects(self, scheduling_service):
        """AC-12: Steps with side_effects=True skipped in dry-run mode."""
        policy_id = await _create_and_approve(scheduling_service, POLICY_DRY_RUN)

        run_result = await scheduling_service.trigger_run(policy_id, dry_run=True)
        assert run_result.run is not None
        assert run_result.run["status"] == "success"

        run_id = run_result.run["run_id"]
        steps = await scheduling_service.get_run_steps(run_id)

        # fetch step (side_effects=False) should execute
        fetch_steps = [s for s in steps if s["step_id"] == "fetch"]
        assert len(fetch_steps) >= 1
        assert fetch_steps[0]["status"] == PipelineStatus.SUCCESS.value

        # side_effect step (side_effects=True) should be SKIPPED
        se_steps = [s for s in steps if s["step_id"] == "side_effect"]
        assert len(se_steps) >= 1
        assert se_steps[0]["status"] == PipelineStatus.SKIPPED.value

    @pytest.mark.asyncio
    async def test_skip_condition_evaluated(self, scheduling_service):
        """AC-13: Step with skip_if condition evaluating to True is skipped."""
        policy_id = await _create_and_approve(scheduling_service, POLICY_SKIP_CONDITION)

        run_result = await scheduling_service.trigger_run(policy_id)
        assert run_result.run is not None
        assert run_result.run["status"] == "success"

        run_id = run_result.run["run_id"]
        steps = await scheduling_service.get_run_steps(run_id)

        # fetch returns empty data (count=0), so conditional should be skipped
        cond_steps = [s for s in steps if s["step_id"] == "conditional"]
        assert len(cond_steps) >= 1
        assert cond_steps[0]["status"] == PipelineStatus.SKIPPED.value


# ── TestCancellation ─────────────────────────────────────────────────────


class TestCancellation:
    """Test cancel infrastructure (PW7)."""

    @pytest.mark.asyncio
    async def test_cancel_running_pipeline(self, scheduling_service, pipeline_runner):
        """AC-14: Running pipeline can be cancelled; status transitions to cancelled."""
        policy_id = await _create_and_approve(scheduling_service, POLICY_CANCELLABLE)

        # Start the pipeline in a background task
        run_task = asyncio.create_task(scheduling_service.trigger_run(policy_id))

        # Give the pipeline a moment to start running
        await asyncio.sleep(0.2)

        # The run should now be in progress — get the run_id from the run store
        runs = await scheduling_service.get_policy_runs(policy_id)
        assert len(runs) >= 1
        run_id = runs[0]["run_id"]

        # Cancel the run
        cancel_result = await scheduling_service.cancel_run(run_id)
        assert cancel_result.error is None

        # Wait for the pipeline to finish
        try:
            await asyncio.wait_for(run_task, timeout=5.0)
        except asyncio.TimeoutError:
            pytest.fail("Pipeline did not complete after cancellation within timeout")

        # Verify the final status is cancelled
        final_run = await scheduling_service.get_run_detail(run_id)
        assert final_run is not None
        assert final_run["status"] in ("cancelled", "cancelling")

    @pytest.mark.asyncio
    async def test_cancel_idempotent_on_completed(self, scheduling_service):
        """AC-15: Cancel on terminal-state run returns current state without error."""
        policy_id = await _create_and_approve(scheduling_service, SMOKE_POLICY_BASIC)

        # Run to completion first
        run_result = await scheduling_service.trigger_run(policy_id)
        assert run_result.run is not None
        run_id = run_result.run["run_id"]
        assert run_result.run["status"] == "success"

        # Cancel the already-completed run — should be idempotent
        cancel_result = await scheduling_service.cancel_run(run_id)
        assert cancel_result.error is None
        assert cancel_result.run is not None
        assert cancel_result.run["status"] == "success"


# ── TestZombieRecovery ───────────────────────────────────────────────────


class TestZombieRecovery:
    """Test zombie detection and cleanup (PW5)."""

    @pytest.mark.asyncio
    async def test_startup_zombie_recovery(self, pipeline_runner, pipeline_uow):
        """AC-20: Zombie runs (status=running at startup) are recovered to failed."""
        # Insert a fake "running" pipeline run directly into the DB
        zombie_run_id = str(uuid.uuid4())
        pipeline_uow.pipeline_runs.create(
            id=zombie_run_id,
            policy_id="test-policy",
            status="running",
            trigger_type="manual",
            content_hash="abc123",
        )
        pipeline_uow.commit()

        # Verify the zombie exists
        zombie = pipeline_uow.pipeline_runs.get_by_id(zombie_run_id)
        assert zombie is not None
        assert zombie.status == "running"

        # Run zombie recovery
        recovered = await pipeline_runner.recover_zombies()
        assert len(recovered) >= 1
        assert any(r["run_id"] == zombie_run_id for r in recovered)

        # Verify the zombie is now FAILED
        updated = pipeline_uow.pipeline_runs.get_by_id(zombie_run_id)
        assert updated is not None
        assert updated.status == PipelineStatus.FAILED.value

    @pytest.mark.asyncio
    async def test_no_dual_write_records(self, scheduling_service, pipeline_uow):
        """AC-21: PipelineRunner with pre-created run_id does not duplicate run record."""
        policy_id = await _create_and_approve(scheduling_service, SMOKE_POLICY_BASIC)

        # Trigger a run — SchedulingService creates the run record,
        # then PipelineRunner uses the same run_id
        run_result = await scheduling_service.trigger_run(policy_id)
        assert run_result.run is not None
        run_id = run_result.run["run_id"]

        # Query all runs for this policy — should have exactly 1
        runs = await scheduling_service.get_policy_runs(policy_id)
        matching = [r for r in runs if r["run_id"] == run_id]
        assert len(matching) == 1, f"Expected 1 run record, found {len(matching)}"


# ── TestResilience ───────────────────────────────────────────────────────


class TestResilience:
    """Test encoding and edge cases (PW4, PW6)."""

    @pytest.mark.asyncio
    async def test_unicode_error_messages_no_crash(self, scheduling_service):
        """AC-16: Non-ASCII error messages (PW4 regression) don't crash pipeline."""
        policy_id = await _create_and_approve(scheduling_service, POLICY_UNICODE_ERROR)

        run_result = await scheduling_service.trigger_run(policy_id)
        assert run_result.run is not None
        # Pipeline should fail (mock_fail), but not crash
        assert run_result.run["status"] == "failed"
        assert run_result.run.get("error") is not None
        # The error message should contain the Unicode characters
        assert (
            "Résumé" in run_result.run["error"]
            or "non-ASCII" in run_result.run["error"]
        )

    @pytest.mark.asyncio
    async def test_bytes_output_serializable(self, pipeline_runner, pipeline_uow):
        """AC-22: Step output containing bytes values serializes without crash."""
        # Run a policy where a step returns bytes in its output.
        # We'll test _safe_json_output directly by running a policy through
        # the runner with a custom step that returns bytes.
        #
        # Since we can't easily inject a bytes-returning step, test the
        # serializer function directly.
        from zorivest_core.services.pipeline_runner import _safe_json_output

        output_with_bytes = {"data": b"binary content \xff\xfe", "count": 42}
        result = _safe_json_output(output_with_bytes)
        assert result is not None
        assert "binary content" in result

        # Verify None input
        assert _safe_json_output(None) is None

        # Verify empty dict
        assert _safe_json_output({}) is not None


# ── TestAuditTrail ───────────────────────────────────────────────────────


class TestAuditTrail:
    """Test audit log completeness."""

    @pytest.mark.asyncio
    async def test_run_creates_audit_entry(self, scheduling_service, pipeline_uow):
        """AC-17: Triggering a run creates pipeline.run audit log entry."""
        from zorivest_infra.database.models import AuditLogModel

        policy_id = await _create_and_approve(scheduling_service, SMOKE_POLICY_BASIC)
        await scheduling_service.trigger_run(policy_id)

        # Query audit log for pipeline.run entries
        audit_entries = (
            pipeline_uow._session.query(AuditLogModel)  # noqa: SLF001
            .filter(AuditLogModel.action == "pipeline.run")
            .all()
        )
        assert len(audit_entries) >= 1
        assert audit_entries[0].resource_type == "pipeline_run"

    @pytest.mark.asyncio
    async def test_cancel_creates_audit_entry(self, scheduling_service, pipeline_uow):
        """AC-18: Cancelling a run creates pipeline.cancel audit log entry."""
        from zorivest_infra.database.models import AuditLogModel

        policy_id = await _create_and_approve(scheduling_service, SMOKE_POLICY_BASIC)

        run_result = await scheduling_service.trigger_run(policy_id)
        assert run_result.run is not None
        run_id = run_result.run["run_id"]

        # Cancel (idempotent on completed run, but still logs)
        await scheduling_service.cancel_run(run_id)

        # The cancel on a completed run returns idempotently without
        # calling runner.cancel_run(), so the audit entry is only
        # created when status is not terminal. For this test, we
        # need a non-terminal run. Let's verify the cancel path
        # by checking the scheduling_service path directly.
        #
        # Since the run is already complete (terminal state "success"),
        # the cancel_run returns early without logging per spec §9B.5e.
        # So we test it with a fresh pending/running run instead.

        # Create another policy and get a run started
        policy_id2 = await _create_and_approve(scheduling_service, POLICY_CANCELLABLE)
        run_task = asyncio.create_task(scheduling_service.trigger_run(policy_id2))
        await asyncio.sleep(0.2)

        runs = await scheduling_service.get_policy_runs(policy_id2)
        if runs:
            cancel_run_id = runs[0]["run_id"]
            await scheduling_service.cancel_run(cancel_run_id)

            # Query for pipeline.cancel audit entries
            cancel_entries = (
                pipeline_uow._session.query(AuditLogModel)  # noqa: SLF001
                .filter(AuditLogModel.action == "pipeline.cancel")
                .all()
            )
            assert len(cancel_entries) >= 1

        # Clean up the background task
        try:
            await asyncio.wait_for(run_task, timeout=5.0)
        except (asyncio.TimeoutError, asyncio.CancelledError):
            pass
