"""Unit tests for PipelineRunner constructor expansion (MEU-PW1).

AC-1: PipelineRunner constructor accepts 8 keyword params.
AC-2: All 8 keys present in initial_outputs when run() is called.

Source: docs/execution/plans/2026-04-12-pipeline-runtime-wiring/implementation-plan.md
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from zorivest_core.services.pipeline_runner import PipelineRunner


# ── Helpers ──────────────────────────────────────────────────────────────


def _make_runner(**overrides: Any) -> PipelineRunner:
    """Create a PipelineRunner with minimal required args + optional overrides."""
    defaults: dict[str, Any] = {
        "uow": None,
        "ref_resolver": MagicMock(),
        "condition_evaluator": MagicMock(),
    }
    # Merge overrides as keyword-only args
    return PipelineRunner(**defaults, **overrides)


def _make_policy(steps: list[dict[str, Any]] | None = None) -> MagicMock:
    """Create a minimal PolicyDocument mock."""
    policy = MagicMock()
    policy.name = "test-policy"
    policy.steps = steps or []
    # compute_content_hash calls model_dump(mode="json") for JSON serialization
    policy.model_dump.return_value = {"name": "test-policy", "steps": []}
    return policy


# ── AC-1: Constructor accepts 8 keyword params ──────────────────────────


class TestConstructorSignature:
    """AC-1: PipelineRunner constructor accepts 8 keyword params."""

    def test_accepts_all_8_kwargs(self) -> None:
        """Constructor accepts all 8 keyword-only dependency params."""
        runner = PipelineRunner(
            None,  # uow
            MagicMock(),  # ref_resolver
            MagicMock(),  # condition_evaluator
            delivery_repository=MagicMock(),
            smtp_config={"host": "smtp.test.com"},
            provider_adapter=MagicMock(),
            db_writer=MagicMock(),
            db_connection=MagicMock(),
            report_repository=MagicMock(),
            template_engine=MagicMock(),
            pipeline_state_repo=MagicMock(),
        )
        assert runner is not None

    def test_all_kwargs_default_to_none(self) -> None:
        """All 8 kwargs default to None when not provided."""
        runner = _make_runner()
        assert runner._delivery_repository is None
        assert runner._smtp_config is None
        assert runner._provider_adapter is None
        assert runner._db_writer is None
        assert runner._db_connection is None
        assert runner._report_repository is None
        assert runner._template_engine is None
        assert runner._pipeline_state_repo is None

    def test_unknown_kwarg_raises_type_error(self) -> None:
        """Negative: unknown keyword argument raises TypeError."""
        kwargs = {"unknown_param": 42}
        with pytest.raises(TypeError):
            PipelineRunner(None, MagicMock(), MagicMock(), **kwargs)

    def test_stores_each_kwarg_on_instance(self) -> None:
        """Each kwarg is stored as a private attribute on the instance."""
        delivery_repo = MagicMock()
        smtp = {"host": "h", "port": 587}
        provider = MagicMock()
        db_writer = MagicMock()
        db_conn = MagicMock()
        report_repo = MagicMock()
        tmpl = MagicMock()
        ps_repo = MagicMock()

        runner = _make_runner(
            delivery_repository=delivery_repo,
            smtp_config=smtp,
            provider_adapter=provider,
            db_writer=db_writer,
            db_connection=db_conn,
            report_repository=report_repo,
            template_engine=tmpl,
            pipeline_state_repo=ps_repo,
        )

        assert runner._delivery_repository is delivery_repo
        assert runner._smtp_config is smtp
        assert runner._provider_adapter is provider
        assert runner._db_writer is db_writer
        assert runner._db_connection is db_conn
        assert runner._report_repository is report_repo
        assert runner._template_engine is tmpl
        assert runner._pipeline_state_repo is ps_repo


# ── AC-2: initial_outputs populated when run() is called ────────────────

# Shared helper: build an InspectorStep + step_def for policy injection

_inspector_counter = 0


def _make_inspector_step() -> tuple:
    """Create an InspectorStep class + step_def mock for capturing context.outputs."""
    global _inspector_counter  # noqa: PLW0603
    _inspector_counter += 1
    unique_type = f"inspector_{_inspector_counter}"

    from zorivest_core.domain.enums import PipelineStatus
    from zorivest_core.domain.pipeline import StepContext, StepResult
    from zorivest_core.domain.step_registry import RegisteredStep

    captured_outputs: dict[str, Any] = {}

    class InspectorStep(RegisteredStep):
        type_name = unique_type
        side_effects = False

        async def execute(self, params: dict, context: StepContext) -> StepResult:
            captured_outputs.update(context.outputs)
            return StepResult(status=PipelineStatus.SUCCESS, output={"ok": True})

    step_def = MagicMock()
    step_def.id = "inspect"
    step_def.type = unique_type
    step_def.skip_if = None
    step_def.on_error = MagicMock()
    step_def.on_error.__eq__ = lambda self, other: False
    step_def.timeout = 30
    step_def.params = {}
    step_def.retry = MagicMock()
    step_def.retry.max_attempts = 1

    return InspectorStep, step_def, captured_outputs


class TestInitialOutputsInjection:
    """AC-2: All 8 keys present in initial_outputs when run() is called."""

    @pytest.mark.asyncio()
    async def test_all_non_none_deps_injected_into_context(self) -> None:
        """When all 8 deps are provided, all 8 appear in context.outputs."""
        delivery_repo = MagicMock()
        smtp = {"host": "h"}
        provider = MagicMock()
        db_writer = MagicMock()
        db_conn = MagicMock()
        report_repo = MagicMock()
        tmpl = MagicMock()
        ps_repo = MagicMock()

        runner = _make_runner(
            delivery_repository=delivery_repo,
            smtp_config=smtp,
            provider_adapter=provider,
            db_writer=db_writer,
            db_connection=db_conn,
            report_repository=report_repo,
            template_engine=tmpl,
            pipeline_state_repo=ps_repo,
        )

        _InspectorStep, step_def, captured_outputs = _make_inspector_step()
        policy = _make_policy(steps=[step_def])
        runner.ref_resolver.resolve.return_value = {}

        result = await runner.run(policy, trigger_type="manual")

        assert result["status"] == "success"
        # Assert ALL 8 dependency keys are present in context.outputs
        expected_keys = {
            "delivery_repository",
            "smtp_config",
            "provider_adapter",
            "db_writer",
            "db_connection",
            "report_repository",
            "template_engine",
            "pipeline_state_repo",
        }
        assert set(captured_outputs.keys()) == expected_keys
        # Assert each value is the exact object we injected
        assert captured_outputs["delivery_repository"] is delivery_repo
        assert captured_outputs["smtp_config"] is smtp
        assert captured_outputs["provider_adapter"] is provider
        assert captured_outputs["db_writer"] is db_writer
        assert captured_outputs["db_connection"] is db_conn
        assert captured_outputs["report_repository"] is report_repo
        assert captured_outputs["template_engine"] is tmpl
        assert captured_outputs["pipeline_state_repo"] is ps_repo

    @pytest.mark.asyncio()
    async def test_none_deps_excluded_from_initial_outputs(self) -> None:
        """When all deps are None, context.outputs has no dependency keys."""
        runner = _make_runner()

        _InspectorStep, step_def, captured_outputs = _make_inspector_step()
        policy = _make_policy(steps=[step_def])
        runner.ref_resolver.resolve.return_value = {}

        result = await runner.run(policy, trigger_type="manual")

        assert result["status"] == "success"
        # None deps must NOT appear in context.outputs
        dep_keys = {
            "delivery_repository",
            "smtp_config",
            "provider_adapter",
            "db_writer",
            "db_connection",
            "report_repository",
            "template_engine",
            "pipeline_state_repo",
        }
        assert dep_keys.isdisjoint(captured_outputs.keys())

    @pytest.mark.asyncio()
    async def test_step_can_access_injected_db_writer(self) -> None:
        """A step that reads context.outputs['db_writer'] gets the injected adapter."""
        db_writer = MagicMock()
        runner = _make_runner(db_writer=db_writer)

        _InspectorStep, step_def, captured_outputs = _make_inspector_step()
        policy = _make_policy(steps=[step_def])
        runner.ref_resolver.resolve.return_value = {}

        result = await runner.run(policy, trigger_type="manual")

        assert result["status"] == "success"
        assert captured_outputs.get("db_writer") is db_writer
