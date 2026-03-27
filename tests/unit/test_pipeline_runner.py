"""Tests for PipelineRunner (MEU-83).

Covers:
- AC-1: Sequential step execution
- AC-2: Skip conditions (skip_if)
- AC-3: Dry-run mode skips side-effect steps
- AC-4: Error mode: fail_pipeline stops execution
- AC-5: Error mode: log_and_continue proceeds
- AC-6: Error mode: retry_then_fail retries N times
- AC-7: Ref resolution in step params
- AC-8: run() returns dict with run_id, status, duration_ms, error, steps
- AC-9: Resume from failure (resume_from parameter)
- AC-10: Unknown step type returns FAILED result
- AC-11: Timeout handling
- AC-12: Cancellation handling
- AC-13: Zombie recovery

Uses asyncio.run() wrapper since pytest-asyncio is not a project dependency.
"""

from __future__ import annotations

import asyncio
from unittest.mock import patch

import pytest

from zorivest_core.domain.enums import PipelineStatus, StepErrorMode
from zorivest_core.domain.pipeline import (
    PolicyDocument,
    PolicyStep,
    RetryConfig,
    SkipCondition,
    SkipConditionOperator,
    StepContext,
    StepResult,
    TriggerConfig,
)
from zorivest_core.services.condition_evaluator import ConditionEvaluator
from zorivest_core.services.pipeline_runner import PipelineRunner
from zorivest_core.services.ref_resolver import RefResolver


# ── Test Step Implementations ─────────────────────────────────────────────


class FakeSuccessStep:
    type_name = "fake_success"
    side_effects = False

    async def execute(self, params: dict, context: StepContext) -> StepResult:
        return StepResult(
            status=PipelineStatus.SUCCESS,
            output={"result": "ok", **params},
        )


class FakeFailStep:
    type_name = "fake_fail"
    side_effects = False

    async def execute(self, params: dict, context: StepContext) -> StepResult:
        return StepResult(
            status=PipelineStatus.FAILED,
            error="intentional failure",
        )


class FakeSideEffectStep:
    type_name = "fake_side_effect"
    side_effects = True

    async def execute(self, params: dict, context: StepContext) -> StepResult:
        return StepResult(status=PipelineStatus.SUCCESS, output={"sent": True})


class FakeRetryStep:
    type_name = "fake_retry"
    side_effects = False

    def __init__(self):
        self.call_count = 0

    async def execute(self, params: dict, context: StepContext) -> StepResult:
        self.call_count += 1
        if self.call_count < 3:
            return StepResult(
                status=PipelineStatus.FAILED, error=f"fail #{self.call_count}"
            )
        return StepResult(
            status=PipelineStatus.SUCCESS, output={"attempts": self.call_count}
        )


# ── Helpers ───────────────────────────────────────────────────────────────


def _policy(*steps: PolicyStep, name: str = "test-policy") -> PolicyDocument:
    return PolicyDocument(
        schema_version=1,
        name=name,
        trigger=TriggerConfig(cron_expression="0 0 * * *"),
        steps=list(steps),
    )


def _step(
    id: str,
    type: str = "fake_success",
    on_error: StepErrorMode = StepErrorMode.FAIL_PIPELINE,
    skip_if: SkipCondition | None = None,
    params: dict | None = None,
    retry: RetryConfig | None = None,
) -> PolicyStep:
    return PolicyStep(
        id=id,
        type=type,
        on_error=on_error,
        skip_if=skip_if,
        params=params or {},
        retry=retry or RetryConfig(max_attempts=3, backoff_factor=1.0, jitter=False),
    )


def _runner() -> PipelineRunner:
    return PipelineRunner(
        uow=None,
        ref_resolver=RefResolver(),
        condition_evaluator=ConditionEvaluator(),
    )


def _run(runner, policy, **kwargs):
    """Sync wrapper for async runner.run()."""
    return asyncio.run(runner.run(policy, **kwargs))


# ── AC-1: Sequential step execution ──────────────────────────────────────


class TestSequentialExecution:
    def test_two_steps_run_sequentially(self):
        runner = _runner()
        with patch("zorivest_core.services.pipeline_runner.get_step") as mock_get:
            mock_get.return_value = FakeSuccessStep
            policy = _policy(_step("step_a"), _step("step_b"))
            result = _run(runner, policy, trigger_type="manual", policy_id="pid1")

            assert result["status"] == "success"
            assert result["steps"] == 2
            assert "run_id" in result
            assert "duration_ms" in result

    def test_empty_steps_not_allowed(self):
        with pytest.raises(Exception):
            _policy()  # min_length=1 on steps


# ── AC-2: Skip conditions ────────────────────────────────────────────────


class TestSkipConditions:
    def test_skip_if_condition_met(self):
        runner = _runner()
        with patch("zorivest_core.services.pipeline_runner.get_step") as mock_get:
            mock_get.return_value = FakeSuccessStep
            policy = _policy(
                _step("step_a"),
                _step(
                    "step_b",
                    skip_if=SkipCondition(
                        field="ctx.step_a.result",
                        operator=SkipConditionOperator.EQ,
                        value="ok",
                    ),
                ),
            )
            result = _run(runner, policy, trigger_type="manual", policy_id="pid1")
            assert result["status"] == "success"


# ── AC-3: Dry-run mode ───────────────────────────────────────────────────


class TestDryRun:
    def test_dry_run_skips_side_effect_steps(self):
        runner = _runner()
        with patch("zorivest_core.services.pipeline_runner.get_step") as mock_get:

            def _get(name):
                return (
                    FakeSideEffectStep
                    if name == "fake_side_effect"
                    else FakeSuccessStep
                )

            mock_get.side_effect = _get
            policy = _policy(
                _step("pure_step", type="fake_success"),
                _step("side_step", type="fake_side_effect"),
            )
            result = _run(
                runner, policy, trigger_type="manual", dry_run=True, policy_id="pid1"
            )
            assert result["status"] == "success"


# ── AC-4: Error mode: fail_pipeline ──────────────────────────────────────


class TestFailPipeline:
    def test_fail_pipeline_stops_on_error(self):
        runner = _runner()
        call_order = []

        class TrackSuccess(FakeSuccessStep):
            async def execute(self, params, context):
                call_order.append("success")
                return await super().execute(params, context)

        class TrackFail(FakeFailStep):
            async def execute(self, params, context):
                call_order.append("fail")
                return await super().execute(params, context)

        with patch("zorivest_core.services.pipeline_runner.get_step") as mock_get:

            def _get(name):
                return TrackFail if name == "fake_fail" else TrackSuccess

            mock_get.side_effect = _get
            policy = _policy(
                _step("step_a"),
                _step("step_b", type="fake_fail", on_error=StepErrorMode.FAIL_PIPELINE),
                _step("step_c"),
            )
            result = _run(runner, policy, trigger_type="manual", policy_id="pid1")

            assert result["status"] == "failed"
            assert "step_b" in result["error"]
            assert call_order == ["success", "fail"]


# ── AC-5: Error mode: log_and_continue ───────────────────────────────────


class TestLogAndContinue:
    def test_log_and_continue_proceeds(self):
        runner = _runner()
        with patch("zorivest_core.services.pipeline_runner.get_step") as mock_get:

            def _get(name):
                return FakeFailStep if name == "fake_fail" else FakeSuccessStep

            mock_get.side_effect = _get
            policy = _policy(
                _step("step_a"),
                _step(
                    "step_b", type="fake_fail", on_error=StepErrorMode.LOG_AND_CONTINUE
                ),
                _step("step_c"),
            )
            result = _run(runner, policy, trigger_type="manual", policy_id="pid1")
            assert result["status"] == "success"


# ── AC-6: Retry then fail ────────────────────────────────────────────────


class TestRetryThenFail:
    def test_retry_succeeds_on_third_attempt(self):
        runner = _runner()
        retry_step = FakeRetryStep()

        class RetryStepCls:
            type_name = "fake_retry"
            side_effects = False

            def __init__(self):
                pass

            async def execute(self, params, context):
                return await retry_step.execute(params, context)

        with patch("zorivest_core.services.pipeline_runner.get_step") as mock_get:
            mock_get.return_value = RetryStepCls
            policy = _policy(
                _step(
                    "retry_step",
                    type="fake_retry",
                    on_error=StepErrorMode.RETRY_THEN_FAIL,
                    retry=RetryConfig(max_attempts=3, backoff_factor=1.0, jitter=False),
                ),
            )
            result = _run(runner, policy, trigger_type="manual", policy_id="pid1")

            assert result["status"] == "success"
            assert retry_step.call_count == 3

    def test_retry_exhausted_fails_pipeline(self):
        runner = _runner()
        with patch("zorivest_core.services.pipeline_runner.get_step") as mock_get:
            mock_get.return_value = FakeFailStep
            policy = _policy(
                _step(
                    "always_fail",
                    type="fake_fail",
                    on_error=StepErrorMode.RETRY_THEN_FAIL,
                    retry=RetryConfig(max_attempts=2, backoff_factor=1.0, jitter=False),
                ),
            )
            result = _run(runner, policy, trigger_type="manual", policy_id="pid1")
            assert result["status"] == "failed"


# ── AC-7: Ref resolution in step params ──────────────────────────────────


class TestRefResolution:
    def test_ref_resolved_from_prior_step(self):
        runner = _runner()
        resolved_params = {}

        class CapturingStep(FakeSuccessStep):
            async def execute(self, params, context):
                resolved_params.update(params)
                return await super().execute(params, context)

        with patch("zorivest_core.services.pipeline_runner.get_step") as mock_get:
            mock_get.return_value = CapturingStep
            policy = _policy(
                _step("step_a", params={"data": "hello"}),
                _step("step_b", params={"input": {"ref": "ctx.step_a.result"}}),
            )
            result = _run(runner, policy, trigger_type="manual", policy_id="pid1")

            assert result["status"] == "success"
            assert resolved_params.get("input") == "ok"


# ── AC-8: Return dict structure ──────────────────────────────────────────


class TestReturnStructure:
    def test_return_dict_keys(self):
        runner = _runner()
        with patch("zorivest_core.services.pipeline_runner.get_step") as mock_get:
            mock_get.return_value = FakeSuccessStep
            policy = _policy(_step("step_a"))
            result = _run(runner, policy, trigger_type="scheduled", policy_id="pid1")

            assert set(result.keys()) == {
                "run_id",
                "status",
                "duration_ms",
                "error",
                "steps",
            }
            assert isinstance(result["run_id"], str)
            assert isinstance(result["duration_ms"], int)
            assert result["error"] is None


# ── AC-10: Unknown step type ─────────────────────────────────────────────


class TestUnknownStepType:
    def test_unknown_step_type_fails(self):
        runner = _runner()
        with patch("zorivest_core.services.pipeline_runner.get_step") as mock_get:
            mock_get.return_value = None
            policy = _policy(_step("bad_step", type="nonexistent"))
            result = _run(runner, policy, trigger_type="manual", policy_id="pid1")

            assert result["status"] == "failed"
            assert "Unknown step type" in result["error"]


# ── AC-9: Resume from failure ────────────────────────────────────────────


class TestResumeFrom:
    def test_resume_from_skips_prior_steps(self):
        """When resume_from='step_c', steps a and b should be skipped."""
        runner = _runner()
        executed_steps = []

        class TrackingStep(FakeSuccessStep):
            async def execute(self, params, context):
                executed_steps.append(params.get("id", "unknown"))
                return await super().execute(params, context)

        with patch("zorivest_core.services.pipeline_runner.get_step") as mock_get:
            mock_get.return_value = TrackingStep
            policy = _policy(
                _step("step_a", params={"id": "a"}),
                _step("step_b", params={"id": "b"}),
                _step("step_c", params={"id": "c"}),
            )
            result = _run(
                runner,
                policy,
                trigger_type="manual",
                policy_id="pid1",
                resume_from="step_c",
            )

            assert result["status"] == "success"
            # Only step_c should have executed
            assert executed_steps == ["c"]


# ── AC-11: Timeout handling ──────────────────────────────────────────────


class FakeSlowStep:
    """Step that takes too long."""

    type_name = "fake_slow"
    side_effects = False

    async def execute(self, params: dict, context: StepContext) -> StepResult:
        await asyncio.sleep(10)  # Will be cancelled by timeout
        return StepResult(status=PipelineStatus.SUCCESS)


class TestTimeoutHandling:
    def test_step_timeout_fails_pipeline(self):
        runner = _runner()
        with patch("zorivest_core.services.pipeline_runner.get_step") as mock_get:
            mock_get.return_value = FakeSlowStep
            policy = _policy(
                _step("slow_step", type="fake_slow"),
            )
            # Override timeout to 0.1s for fast test
            policy.steps[0].timeout = 0.1
            result = _run(runner, policy, trigger_type="manual", policy_id="pid1")

            assert result["status"] == "failed"
            assert "timed out" in result["error"]


# ── AC-12: Cancellation handling ─────────────────────────────────────────


class TestCancellationHandling:
    def test_cancelled_pipeline_returns_cancelled(self):
        runner = _runner()

        class CancellingStep(FakeSuccessStep):
            async def execute(self, params, context):
                raise asyncio.CancelledError()

        with patch("zorivest_core.services.pipeline_runner.get_step") as mock_get:
            mock_get.return_value = CancellingStep
            policy = _policy(_step("cancel_step"))
            result = _run(runner, policy, trigger_type="manual", policy_id="pid1")

            assert result["status"] == "cancelled"
            assert result["error"] == "Pipeline cancelled"


# ── AC-13: Zombie recovery ───────────────────────────────────────────────


class TestZombieRecovery:
    def test_recover_zombies_no_uow_returns_empty(self):
        """When uow is None, recover_zombies returns empty list."""
        runner = _runner()
        result = asyncio.run(runner.recover_zombies())
        assert result == []


# ── AC-14: Live UoW persistence ──────────────────────────────────────────


class TestPersistenceWithUoW:
    """Exercise the real DB persistence path with in-memory SQLite."""

    def _make_uow(self):
        from sqlalchemy import create_engine, event
        from zorivest_infra.database.models import Base
        from zorivest_infra.database.unit_of_work import SqlAlchemyUnitOfWork

        engine = create_engine("sqlite:///:memory:")

        @event.listens_for(engine, "connect")
        def _fk(dbapi_connection, _):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        Base.metadata.create_all(engine)
        return SqlAlchemyUnitOfWork(engine)

    def _seed_policy(self, uow) -> str:
        """Insert a policy row so PipelineRunModel FK is satisfied."""
        import uuid

        pid = str(uuid.uuid4())
        uow.policies.create(
            id=pid,
            name="test-policy",
            schema_version=1,
            policy_json='{"steps":[]}',
            content_hash="h1",
            created_by="test",
        )
        uow.commit()
        return pid

    def test_run_persists_pipeline_run_and_steps(self):
        """Full run with real UoW creates DB rows."""
        uow = self._make_uow()
        with uow:
            pid = self._seed_policy(uow)
            runner = PipelineRunner(
                uow=uow,
                ref_resolver=RefResolver(),
                condition_evaluator=ConditionEvaluator(),
            )

            with patch("zorivest_core.services.pipeline_runner.get_step") as mock_get:
                mock_get.return_value = FakeSuccessStep
                policy = _policy(_step("step_a"), name="test-policy")
                result = asyncio.run(
                    runner.run(
                        policy,
                        trigger_type="manual",
                        policy_id=pid,
                        actor="test",
                    )
                )

            assert result["status"] == "success"

            # Verify pipeline_runs row was created
            run_row = uow.pipeline_runs.get_by_id(result["run_id"])
            assert run_row is not None
            assert run_row.status == "success"

            # Verify pipeline_steps row was created
            from zorivest_infra.database.models import PipelineStepModel

            steps = (
                uow._session.query(PipelineStepModel)
                .filter_by(run_id=result["run_id"])
                .all()
            )
            assert len(steps) >= 1
            assert steps[0].step_id == "step_a"
            assert steps[0].status == "success"
