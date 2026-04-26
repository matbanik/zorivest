# tests/unit/test_assertion_gates.py
"""FIC Red-phase tests for assertion gates (PH7, AC-7.4–AC-7.7).

Spec: 09d-pipeline-step-extensions.md §9D.4c
"""

from __future__ import annotations

import pytest

from zorivest_core.domain.enums import PipelineStatus
from zorivest_core.domain.pipeline import StepContext


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_context(**outputs: object) -> StepContext:
    ctx = StepContext(run_id="r1", policy_id="p1")
    ctx.outputs.update(outputs)
    return ctx


# ---------------------------------------------------------------------------
# AC-7.4: All assertions pass → SUCCESS
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_assertion_passes() -> None:
    """AC-7.4: When all assertions pass, status is SUCCESS."""
    from zorivest_core.pipeline_steps.transform_step import TransformStep

    step = TransformStep()
    ctx = _make_context(
        fetch_data={"output": {"count": 100, "mean_price": 50.0}},
    )
    params = {
        "kind": "assertion",
        "target_table": "_unused",
        "assertions": [
            {
                "field_ref": "ctx.fetch_data.output.count",
                "operator": "ge",
                "expected": 10,
                "severity": "fatal",
            },
        ],
    }
    result = await step.execute(params, ctx)
    assert result.status == PipelineStatus.SUCCESS


# ---------------------------------------------------------------------------
# AC-7.5: Fatal assertion failure → FAILED
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_assertion_fatal_failure() -> None:
    """AC-7.5: Fatal assertion failure → FAILED status."""
    from zorivest_core.pipeline_steps.transform_step import TransformStep

    step = TransformStep()
    ctx = _make_context(
        fetch_data={"output": {"count": 0}},
    )
    params = {
        "kind": "assertion",
        "target_table": "_unused",
        "assertions": [
            {
                "field_ref": "ctx.fetch_data.output.count",
                "operator": "ge",
                "expected": 10,
                "severity": "fatal",
            },
        ],
    }
    result = await step.execute(params, ctx)
    assert result.status == PipelineStatus.FAILED
    assert "assertion_failures" in result.output


# ---------------------------------------------------------------------------
# AC-7.6: Non-fatal assertion failure → SUCCESS with warnings
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_assertion_warning() -> None:
    """AC-7.6: Non-fatal (warning) assertion → SUCCESS with warnings list."""
    from zorivest_core.pipeline_steps.transform_step import TransformStep

    step = TransformStep()
    ctx = _make_context(
        fetch_data={"output": {"count": 5}},
    )
    params = {
        "kind": "assertion",
        "target_table": "_unused",
        "assertions": [
            {
                "field_ref": "ctx.fetch_data.output.count",
                "operator": "ge",
                "expected": 10,
                "severity": "warning",
            },
        ],
    }
    result = await step.execute(params, ctx)
    assert result.status == PipelineStatus.SUCCESS
    # Warnings are captured in assertion_results
    assert "assertion_results" in result.output
    assert len(result.output["assertion_results"]) == 1


# ---------------------------------------------------------------------------
# AC-7.7: ConditionEvaluator supports abs() and arithmetic
# ---------------------------------------------------------------------------


def test_arithmetic_expression() -> None:
    """AC-7.7: ConditionEvaluator.evaluate_assertion supports abs() and arithmetic."""
    from zorivest_core.services.condition_evaluator import ConditionEvaluator

    # abs(-5) should be 5, which is ge 3
    assert ConditionEvaluator.evaluate_assertion(
        actual=-5, operator="ge", expected=3, use_abs=True
    )

    # Without abs: -5 is NOT ge 3
    assert not ConditionEvaluator.evaluate_assertion(
        actual=-5, operator="ge", expected=3, use_abs=False
    )
