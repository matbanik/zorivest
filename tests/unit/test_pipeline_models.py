# tests/unit/test_pipeline_models.py
"""MEU-78: Policy Pydantic models tests (Red phase)."""

from __future__ import annotations

import pytest
from datetime import datetime, timezone
from typing import Any

from pydantic import ValidationError as PydanticValidationError

from zorivest_core.domain.pipeline import (
    PolicyDocument,
    PolicyStep,
    RefValue,
    RetryConfig,
    SkipConditionOperator,
    StepContext,
    StepResult,
    TriggerConfig,
)
from zorivest_core.domain.enums import PipelineStatus, StepErrorMode


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _minimal_step(**overrides: Any) -> dict:
    defaults = {"id": "fetch_data", "type": "fetch", "params": {}}
    defaults.update(overrides)
    return defaults


def _minimal_trigger(**overrides: Any) -> dict:
    defaults = {"cron_expression": "0 9 * * 1-5"}
    defaults.update(overrides)
    return defaults


def _minimal_policy(**overrides: Any) -> dict:
    defaults = {
        "name": "test-policy",
        "trigger": _minimal_trigger(),
        "steps": [_minimal_step()],
    }
    defaults.update(overrides)
    return defaults


# ---------------------------------------------------------------------------
# AC-1: RefValue.ref validates pattern ^ctx\.\w+(\.\w+)*$
# ---------------------------------------------------------------------------


class TestRefValue:
    def test_valid_ref(self) -> None:
        r = RefValue(ref="ctx.fetch_data.output.quotes")
        assert r.ref == "ctx.fetch_data.output.quotes"

    def test_simple_ref(self) -> None:
        r = RefValue(ref="ctx.step_id")
        assert r.ref == "ctx.step_id"

    def test_invalid_ref_no_ctx(self) -> None:
        with pytest.raises(PydanticValidationError):
            RefValue(ref="output.quotes")

    def test_invalid_ref_empty(self) -> None:
        with pytest.raises(PydanticValidationError):
            RefValue(ref="")

    def test_invalid_ref_spaces(self) -> None:
        with pytest.raises(PydanticValidationError):
            RefValue(ref="ctx.step one")


# ---------------------------------------------------------------------------
# AC-2: RetryConfig.max_attempts constrained ge=1, le=10, default 3
# ---------------------------------------------------------------------------


class TestRetryConfig:
    def test_defaults(self) -> None:
        r = RetryConfig()
        assert r.max_attempts == 3
        assert r.backoff_factor == 2.0
        assert r.jitter is True

    def test_max_attempts_range(self) -> None:
        assert RetryConfig(max_attempts=1).max_attempts == 1
        assert RetryConfig(max_attempts=10).max_attempts == 10

    def test_max_attempts_too_low(self) -> None:
        with pytest.raises(PydanticValidationError):
            RetryConfig(max_attempts=0)

    def test_max_attempts_too_high(self) -> None:
        with pytest.raises(PydanticValidationError):
            RetryConfig(max_attempts=11)

    def test_backoff_range(self) -> None:
        assert RetryConfig(backoff_factor=1.0).backoff_factor == 1.0
        assert RetryConfig(backoff_factor=10.0).backoff_factor == 10.0

    def test_backoff_too_low(self) -> None:
        with pytest.raises(PydanticValidationError):
            RetryConfig(backoff_factor=0.5)


# ---------------------------------------------------------------------------
# AC-3: SkipConditionOperator has 10 members
# ---------------------------------------------------------------------------


class TestSkipConditionOperator:
    def test_member_count(self) -> None:
        assert len(SkipConditionOperator) == 10

    @pytest.mark.parametrize(
        "member, value",
        [
            ("EQ", "eq"),
            ("NE", "ne"),
            ("GT", "gt"),
            ("LT", "lt"),
            ("GE", "ge"),
            ("LE", "le"),
            ("IN", "in"),
            ("NOT_IN", "not_in"),
            ("IS_NULL", "is_null"),
            ("IS_NOT_NULL", "is_not_null"),
        ],
    )
    def test_member_values(self, member: str, value: str) -> None:
        assert SkipConditionOperator[member].value == value


# ---------------------------------------------------------------------------
# AC-4: PolicyStep.id validates pattern, length 1-64
# ---------------------------------------------------------------------------


class TestPolicyStep:
    def test_valid_step(self) -> None:
        s = PolicyStep(**_minimal_step())
        assert s.id == "fetch_data"
        assert s.type == "fetch"

    def test_id_pattern_lowercase(self) -> None:
        s = PolicyStep(**_minimal_step(id="step_1"))
        assert s.id == "step_1"

    def test_id_rejects_uppercase(self) -> None:
        with pytest.raises(PydanticValidationError):
            PolicyStep(**_minimal_step(id="FetchData"))

    def test_id_rejects_leading_number(self) -> None:
        with pytest.raises(PydanticValidationError):
            PolicyStep(**_minimal_step(id="1step"))

    def test_id_rejects_too_long(self) -> None:
        with pytest.raises(PydanticValidationError):
            PolicyStep(**_minimal_step(id="a" * 65))

    def test_id_accepts_max_length(self) -> None:
        s = PolicyStep(**_minimal_step(id="a" * 64))
        assert len(s.id) == 64

    # AC-5: timeout constrained ge=10, le=3600, default 300
    def test_timeout_default(self) -> None:
        s = PolicyStep(**_minimal_step())
        assert s.timeout == 300

    def test_timeout_range(self) -> None:
        assert PolicyStep(**_minimal_step(timeout=10)).timeout == 10
        assert PolicyStep(**_minimal_step(timeout=3600)).timeout == 3600

    def test_timeout_too_low(self) -> None:
        with pytest.raises(PydanticValidationError):
            PolicyStep(**_minimal_step(timeout=9))

    def test_timeout_too_high(self) -> None:
        with pytest.raises(PydanticValidationError):
            PolicyStep(**_minimal_step(timeout=3601))

    def test_on_error_default(self) -> None:
        s = PolicyStep(**_minimal_step())
        assert s.on_error == StepErrorMode.FAIL_PIPELINE

    def test_skip_if_none_default(self) -> None:
        s = PolicyStep(**_minimal_step())
        assert s.skip_if is None

    def test_required_default(self) -> None:
        s = PolicyStep(**_minimal_step())
        assert s.required is True


# ---------------------------------------------------------------------------
# AC-6: TriggerConfig.misfire_grace_time constrained ge=60, le=86400
# ---------------------------------------------------------------------------


class TestTriggerConfig:
    def test_minimal(self) -> None:
        t = TriggerConfig(**_minimal_trigger())
        assert t.cron_expression == "0 9 * * 1-5"
        assert t.timezone == "UTC"
        assert t.enabled is True

    def test_misfire_grace_default(self) -> None:
        t = TriggerConfig(**_minimal_trigger())
        assert t.misfire_grace_time == 3600

    def test_misfire_grace_range(self) -> None:
        assert TriggerConfig(**_minimal_trigger(misfire_grace_time=60)).misfire_grace_time == 60
        assert TriggerConfig(**_minimal_trigger(misfire_grace_time=86400)).misfire_grace_time == 86400

    def test_misfire_grace_too_low(self) -> None:
        with pytest.raises(PydanticValidationError):
            TriggerConfig(**_minimal_trigger(misfire_grace_time=59))

    def test_misfire_grace_too_high(self) -> None:
        with pytest.raises(PydanticValidationError):
            TriggerConfig(**_minimal_trigger(misfire_grace_time=86401))

    def test_coalesce_default(self) -> None:
        t = TriggerConfig(**_minimal_trigger())
        assert t.coalesce is True

    def test_max_instances_default(self) -> None:
        t = TriggerConfig(**_minimal_trigger())
        assert t.max_instances == 1

    def test_max_instances_range(self) -> None:
        assert TriggerConfig(**_minimal_trigger(max_instances=3)).max_instances == 3

    def test_max_instances_too_high(self) -> None:
        with pytest.raises(PydanticValidationError):
            TriggerConfig(**_minimal_trigger(max_instances=4))


# ---------------------------------------------------------------------------
# AC-7: PolicyDocument.steps must have 1-10 items
# ---------------------------------------------------------------------------


class TestPolicyDocument:
    def test_minimal(self) -> None:
        p = PolicyDocument(**_minimal_policy())
        assert p.name == "test-policy"
        assert len(p.steps) == 1

    def test_schema_version_default(self) -> None:
        p = PolicyDocument(**_minimal_policy())
        assert p.schema_version == 1

    def test_steps_min_length(self) -> None:
        with pytest.raises(PydanticValidationError):
            PolicyDocument(**_minimal_policy(steps=[]))

    def test_steps_max_length(self) -> None:
        steps = [_minimal_step(id=f"step_{i}") for i in range(10)]
        p = PolicyDocument(**_minimal_policy(steps=steps))
        assert len(p.steps) == 10

    def test_steps_too_many(self) -> None:
        steps = [_minimal_step(id=f"step_{i}") for i in range(11)]
        with pytest.raises(PydanticValidationError):
            PolicyDocument(**_minimal_policy(steps=steps))

    def test_name_constraints(self) -> None:
        with pytest.raises(PydanticValidationError):
            PolicyDocument(**_minimal_policy(name=""))

        with pytest.raises(PydanticValidationError):
            PolicyDocument(**_minimal_policy(name="x" * 129))

    # AC-8: unique_step_ids validator rejects duplicate IDs
    def test_unique_step_ids_pass(self) -> None:
        steps = [_minimal_step(id="a"), _minimal_step(id="b")]
        p = PolicyDocument(**_minimal_policy(steps=steps))
        assert len(p.steps) == 2

    def test_unique_step_ids_reject_duplicates(self) -> None:
        steps = [_minimal_step(id="a"), _minimal_step(id="a")]
        with pytest.raises(PydanticValidationError, match="Duplicate step IDs"):
            PolicyDocument(**_minimal_policy(steps=steps))

    def test_metadata_defaults(self) -> None:
        p = PolicyDocument(**_minimal_policy())
        assert p.metadata.author == ""
        assert p.metadata.description == ""


# ---------------------------------------------------------------------------
# AC-9: StepContext.get_output() raises KeyError for missing step_id
# ---------------------------------------------------------------------------


class TestStepContext:
    def test_get_output_success(self) -> None:
        ctx = StepContext(run_id="run-1", policy_id="pol-1")
        ctx.outputs["fetch"] = {"data": [1, 2, 3]}
        assert ctx.get_output("fetch") == {"data": [1, 2, 3]}

    def test_get_output_missing(self) -> None:
        ctx = StepContext(run_id="run-1", policy_id="pol-1")
        with pytest.raises(KeyError, match="No output for step"):
            ctx.get_output("nonexistent")

    def test_dry_run_default_false(self) -> None:
        ctx = StepContext(run_id="run-1", policy_id="pol-1")
        assert ctx.dry_run is False

    def test_outputs_default_empty(self) -> None:
        ctx = StepContext(run_id="run-1", policy_id="pol-1")
        assert ctx.outputs == {}

    # AC-11: StepContext.logger uses structlog.BoundLogger
    def test_logger_is_structlog(self) -> None:
        ctx = StepContext(run_id="run-1", policy_id="pol-1")
        # structlog.get_logger() returns a BoundLoggerLazyProxy, which
        # is a proxy to BoundLogger. Verify it's a structlog type.
        assert hasattr(ctx.logger, "bind")
        assert hasattr(ctx.logger, "info")
        assert hasattr(ctx.logger, "error")


# ---------------------------------------------------------------------------
# AC-10: StepResult defaults: empty output dict, None error, 0 duration
# ---------------------------------------------------------------------------


class TestStepResult:
    def test_defaults(self) -> None:
        r = StepResult(status=PipelineStatus.SUCCESS)
        assert r.output == {}
        assert r.error is None
        assert r.duration_ms == 0
        assert r.started_at is None
        assert r.completed_at is None

    def test_with_values(self) -> None:
        now = datetime.now(timezone.utc)
        r = StepResult(
            status=PipelineStatus.FAILED,
            output={"key": "val"},
            error="timeout exceeded",
            started_at=now,
            duration_ms=1500,
        )
        assert r.status == PipelineStatus.FAILED
        assert r.error == "timeout exceeded"
        assert r.duration_ms == 1500
