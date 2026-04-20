# tests/fixtures/mock_steps.py
"""Mock step implementations for pipeline integration testing.

Auto-registered in the StepRegistry via __init_subclass__.
Must be imported before tests that use them.

Spec: 09b-pipeline-hardening.md §9B.6c
"""

import asyncio

from zorivest_core.domain.enums import PipelineStatus
from zorivest_core.domain.pipeline import StepContext, StepResult
from zorivest_core.domain.step_registry import RegisteredStep


class MockFetchStep(RegisteredStep):
    """Returns canned data from params. No HTTP calls."""

    type_name = "mock_fetch"
    side_effects = False

    async def execute(self, params: dict, context: StepContext) -> StepResult:
        return StepResult(
            status=PipelineStatus.SUCCESS,
            output={
                "data": params.get("data", []),
                "count": len(params.get("data", [])),
            },
        )


class MockTransformStep(RegisteredStep):
    """Passthrough transform — returns source data as result."""

    type_name = "mock_transform"
    side_effects = False

    async def execute(self, params: dict, context: StepContext) -> StepResult:
        return StepResult(
            status=PipelineStatus.SUCCESS,
            output={"result": params.get("source", params)},
        )


class MockStoreStep(RegisteredStep):
    """Mock store — logs data without actual DB write."""

    type_name = "mock_store"
    side_effects = True

    async def execute(self, params: dict, context: StepContext) -> StepResult:
        return StepResult(
            status=PipelineStatus.SUCCESS,
            output={"stored": True, "row_count": len(params.get("data", []))},
        )


class MockFailStep(RegisteredStep):
    """Always fails with configurable error message."""

    type_name = "mock_fail"
    side_effects = False

    async def execute(self, params: dict, context: StepContext) -> StepResult:
        return StepResult(
            status=PipelineStatus.FAILED,
            error=params.get("error_msg", "Mock failure"),
        )


class MockSlowStep(RegisteredStep):
    """Deliberately slow step for cancel testing."""

    type_name = "mock_slow"
    side_effects = False

    async def execute(self, params: dict, context: StepContext) -> StepResult:
        delay = params.get("delay_seconds", 10)
        await asyncio.sleep(delay)
        return StepResult(status=PipelineStatus.SUCCESS, output={"waited": delay})


class MockSideEffectStep(RegisteredStep):
    """Step with side_effects=True for dry-run testing."""

    type_name = "mock_side_effect"
    side_effects = True

    async def execute(self, params: dict, context: StepContext) -> StepResult:
        return StepResult(
            status=PipelineStatus.SUCCESS,
            output={"side_effect": "executed"},
        )
