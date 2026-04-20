"""Integration test — Pipeline runtime wiring (MEU-PW1).

AC-6: Dependency wiring verification — confirms all injected deps reach step
      context.outputs when runner.run() executes with a real app lifespan.

Source: docs/execution/plans/2026-04-12-pipeline-runtime-wiring/implementation-plan.md
"""

from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from zorivest_api.main import create_app
from zorivest_core.services.pipeline_runner import PipelineRunner


class TestPipelineRuntimeWiring:
    """AC-6: Verify PipelineRunner has all 7 wired deps (+ 1 None)."""

    @pytest.fixture()
    def app_with_runner(self) -> Generator[tuple, None, None]:
        """Create app and extract PipelineRunner for inspection."""
        app = create_app()
        with TestClient(app) as _:
            # Find the pipeline_runner via scheduling_service
            scheduling_svc = app.state.scheduling_service
            runner: PipelineRunner = scheduling_svc._runner
            yield app, runner

    def test_pipeline_runner_has_delivery_repository(
        self, app_with_runner: tuple
    ) -> None:
        """delivery_repository is wired from uow.deliveries."""
        _, runner = app_with_runner
        assert runner._delivery_repository is not None

    def test_pipeline_runner_has_smtp_config(self, app_with_runner: tuple) -> None:
        """smtp_config is wired from EmailProviderService.get_smtp_runtime_config()."""
        _, runner = app_with_runner
        assert runner._smtp_config is not None
        assert isinstance(runner._smtp_config, dict)
        assert set(runner._smtp_config.keys()) == {
            "host",
            "port",
            "sender",
            "username",
            "password",
            "security",
        }

    def test_pipeline_runner_provider_adapter_is_wired(
        self, app_with_runner: tuple
    ) -> None:
        """provider_adapter is wired as MarketDataProviderAdapter (MEU-PW2)."""
        _, runner = app_with_runner
        assert runner._provider_adapter is not None

    def test_pipeline_runner_has_db_writer(self, app_with_runner: tuple) -> None:
        """db_writer is wired as DbWriteAdapter."""
        from zorivest_infra.adapters.db_write_adapter import DbWriteAdapter

        _, runner = app_with_runner
        assert runner._db_writer is not None
        assert isinstance(runner._db_writer, DbWriteAdapter)

    def test_pipeline_runner_has_db_connection(self, app_with_runner: tuple) -> None:
        """db_connection is wired as sandboxed sqlite3.Connection."""
        import sqlite3

        _, runner = app_with_runner
        assert runner._db_connection is not None
        assert isinstance(runner._db_connection, sqlite3.Connection)

    def test_pipeline_runner_has_report_repository(
        self, app_with_runner: tuple
    ) -> None:
        """report_repository is wired from uow.reports."""
        _, runner = app_with_runner
        assert runner._report_repository is not None

    def test_pipeline_runner_has_template_engine(self, app_with_runner: tuple) -> None:
        """template_engine is wired from create_template_engine()."""
        from jinja2 import Environment

        _, runner = app_with_runner
        assert runner._template_engine is not None
        assert isinstance(runner._template_engine, Environment)

    def test_pipeline_runner_has_pipeline_state_repo(
        self, app_with_runner: tuple
    ) -> None:
        """pipeline_state_repo is wired from uow.pipeline_state."""
        _, runner = app_with_runner
        assert runner._pipeline_state_repo is not None


class TestStubDeletion:
    """AC-5: Dead stubs are deleted and no longer importable."""

    def test_stub_market_data_service_not_importable(self) -> None:
        """StubMarketDataService is deleted — no longer exists on the stubs module."""
        import zorivest_api.stubs as stubs_module

        assert not hasattr(stubs_module, "StubMarketDataService")

    def test_stub_provider_connection_service_not_importable(self) -> None:
        """StubProviderConnectionService is deleted — no longer exists on the stubs module."""
        import zorivest_api.stubs as stubs_module

        assert not hasattr(stubs_module, "StubProviderConnectionService")


class TestPipelineRunnerExecution:
    """AC-6 (strengthened): Verify runner.run() populates context.outputs from wired deps.

    Goes beyond attribute inspection — executes the runner with an InspectorStep
    to prove the wired dependencies flow through to step execution context.
    """

    @pytest.fixture()
    def runner_from_app(self) -> Generator[PipelineRunner, None, None]:
        """Create app and extract PipelineRunner for execution."""
        app = create_app()
        with TestClient(app) as _:
            scheduling_svc = app.state.scheduling_service
            runner: PipelineRunner = scheduling_svc._runner
            yield runner

    @pytest.mark.asyncio()
    async def test_run_with_inspector_step_populates_outputs(
        self, runner_from_app: PipelineRunner
    ) -> None:
        """runner.run() with InspectorStep proves wired deps reach step context."""
        from typing import Any
        from unittest.mock import MagicMock

        from zorivest_core.domain.enums import PipelineStatus
        from zorivest_core.domain.pipeline import StepContext, StepResult
        from zorivest_core.domain.step_registry import RegisteredStep

        captured_outputs: dict[str, Any] = {}

        class WiringInspectorStep(RegisteredStep):
            type_name = "wiring_inspector_integ"  # type: ignore[assignment]
            side_effects = False

            async def execute(self, params: dict, context: StepContext) -> StepResult:
                captured_outputs.update(context.outputs)
                return StepResult(status=PipelineStatus.SUCCESS, output={"ok": True})

        # Build a minimal policy with the inspector step
        step_def = MagicMock()
        step_def.id = "inspect"
        step_def.type = "wiring_inspector_integ"
        step_def.skip_if = None
        step_def.on_error = MagicMock()
        step_def.on_error.__eq__ = lambda self, other: False
        step_def.timeout = 30
        step_def.params = {}
        step_def.retry = MagicMock()
        step_def.retry.max_attempts = 1

        policy = MagicMock()
        policy.name = "wiring-integration-test"
        policy.steps = [step_def]
        policy.model_dump.return_value = {
            "name": "wiring-integration-test",
            "steps": [],
        }

        runner = runner_from_app
        runner.ref_resolver.resolve = MagicMock(return_value={})

        result = await runner.run(policy, trigger_type="manual")

        assert result["status"] == "success"

        # Verify ALL 9 non-None wired dependencies reached the step context
        expected_keys = {
            "delivery_repository",
            "smtp_config",
            "provider_adapter",
            "db_writer",
            "db_connection",
            "report_repository",
            "template_engine",
            "pipeline_state_repo",
            "fetch_cache_repo",
        }
        actual_dep_keys = set(captured_outputs.keys()) & expected_keys
        assert actual_dep_keys == expected_keys, (
            f"Missing dependency keys in context.outputs: {expected_keys - actual_dep_keys}"
        )
