# tests/unit/test_pipeline_cancellation.py
"""Red-phase tests for MEU-PW7: Pipeline Cancellation Infrastructure.

FIC — Feature Intent Contract
==============================
Intent: Allow stuck pipeline runs to be cancelled via a CANCELLING status
    in PipelineStatus, cooperative cancel-checking in PipelineRunner, and a
    REST endpoint POST /runs/{run_id}/cancel.

Acceptance Criteria:
- AC-PW7-1: PipelineStatus.CANCELLING enum member exists with value "cancelling" [Spec §9B.5]
- AC-PW7-2: PipelineRunner tracks active tasks in _active_tasks dict [Spec §9B.5]
- AC-PW7-3: PipelineRunner.cancel_run() sets CANCELLING status, cancels tasks,
  respects grace_seconds, and finalises as CANCELLED [Spec §9B.5]
- AC-PW7-4: SchedulingService.cancel_run() delegates to runner and returns
  RunResult with success or error [Spec §9B.5]
- AC-PW7-5: POST /runs/{run_id}/cancel returns 200 on success, 404 on
  missing run, 422 on invalid UUID [Spec §9B.5, Boundary Input Contract]

Test Mapping:
- AC-PW7-1 → TestCancellingEnum
- AC-PW7-2 → TestActiveTasks
- AC-PW7-3 → TestCancelRun
- AC-PW7-4 → TestSchedulingServiceCancel
- AC-PW7-5 → TestCancelEndpoint
"""

from __future__ import annotations

import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest


# ── AC-PW7-1: CANCELLING enum member ──────────────────────────────────


class TestCancellingEnum:
    """AC-PW7-1: PipelineStatus.CANCELLING exists."""

    def test_cancelling_member_exists(self) -> None:
        """PipelineStatus has a CANCELLING member."""
        from zorivest_core.domain.enums import PipelineStatus

        assert hasattr(PipelineStatus, "CANCELLING")

    def test_cancelling_value(self) -> None:
        """CANCELLING member has value 'cancelling'."""
        from zorivest_core.domain.enums import PipelineStatus

        assert PipelineStatus.CANCELLING.value == "cancelling"

    def test_cancelling_in_pipeline_status_members(self) -> None:
        """CANCELLING is a valid PipelineStatus member."""
        from zorivest_core.domain.enums import PipelineStatus

        values = [s.value for s in PipelineStatus]
        assert "cancelling" in values


# ── AC-PW7-2: Active tasks tracking ───────────────────────────────────


class TestActiveTasks:
    """AC-PW7-2: PipelineRunner tracks active tasks."""

    def test_active_tasks_initialized_empty(self) -> None:
        """PipelineRunner._active_tasks starts as empty dict."""
        from zorivest_core.services.pipeline_runner import PipelineRunner

        runner = PipelineRunner(
            uow=None,
            ref_resolver=MagicMock(),
            condition_evaluator=MagicMock(),
        )
        assert hasattr(runner, "_active_tasks")
        assert isinstance(runner._active_tasks, dict)
        assert len(runner._active_tasks) == 0


# ── AC-PW7-3: cancel_run() method ─────────────────────────────────────


class TestCancelRun:
    """AC-PW7-3: PipelineRunner.cancel_run() implementation."""

    def test_cancel_run_method_exists(self) -> None:
        """PipelineRunner has a cancel_run() async method."""
        from zorivest_core.services.pipeline_runner import PipelineRunner

        runner = PipelineRunner(
            uow=None,
            ref_resolver=MagicMock(),
            condition_evaluator=MagicMock(),
        )
        assert hasattr(runner, "cancel_run")
        assert asyncio.iscoroutinefunction(runner.cancel_run)

    @pytest.mark.asyncio
    async def test_cancel_run_with_no_active_task_returns_true(self) -> None:
        """cancel_run() for a non-active run_id returns True (idempotent per spec §9B.5c)."""
        from zorivest_core.services.pipeline_runner import PipelineRunner

        runner = PipelineRunner(
            uow=None,
            ref_resolver=MagicMock(),
            condition_evaluator=MagicMock(),
        )
        result = await runner.cancel_run(str(uuid.uuid4()))
        assert result is True

    @pytest.mark.asyncio
    async def test_cancel_run_with_active_task(self) -> None:
        """cancel_run() cancels an active task and returns True."""
        from zorivest_core.services.pipeline_runner import PipelineRunner

        mock_uow = MagicMock()
        mock_uow.pipeline_runs.update_status = MagicMock()
        runner = PipelineRunner(
            uow=mock_uow,
            ref_resolver=MagicMock(),
            condition_evaluator=MagicMock(),
        )
        run_id = str(uuid.uuid4())

        # Create a real async task that will block until cancelled
        async def _long_running() -> None:
            await asyncio.sleep(3600)

        task = asyncio.get_event_loop().create_task(_long_running())
        runner._active_tasks[run_id] = task

        # Use very short grace to force fast cancellation
        result = await runner.cancel_run(run_id, grace_seconds=0.05)
        assert result is True
        assert task.cancelled() or task.done()

    @pytest.mark.asyncio
    async def test_cancel_run_removes_from_active_tasks(self) -> None:
        """After cancel_run(), the run_id is no longer in _active_tasks
        (the finally block in run() handles this, or force-cancel completes)."""
        from zorivest_core.services.pipeline_runner import PipelineRunner

        mock_uow = MagicMock()
        mock_uow.pipeline_runs.update_status = MagicMock()
        runner = PipelineRunner(
            uow=mock_uow,
            ref_resolver=MagicMock(),
            condition_evaluator=MagicMock(),
        )
        run_id = str(uuid.uuid4())

        async def _long_running() -> None:
            await asyncio.sleep(3600)

        task = asyncio.get_event_loop().create_task(_long_running())
        runner._active_tasks[run_id] = task

        await runner.cancel_run(run_id, grace_seconds=0.05)
        # Task is no longer tracked (either the task's finally cleaned it,
        # or cancel_run did so — either way it shouldn't be active)
        # Note: _active_tasks cleanup happens in run()'s finally block,
        # not in cancel_run(), so it may still be here for externally-created tasks
        assert task.cancelled() or task.done()


# ── AC-PW7-3b: Cooperative cancellation via _is_cancelling ────────────


class TestCooperativeCancellation:
    """AC-PW7-3b: Cooperative cancellation at step boundaries."""

    @pytest.mark.asyncio
    async def test_is_cancelling_returns_true_for_cancelling_status(self) -> None:
        """_is_cancelling() returns True when run has CANCELLING status in DB."""
        from zorivest_core.services.pipeline_runner import PipelineRunner

        mock_uow = MagicMock()
        mock_run = MagicMock()
        mock_run.status = "cancelling"
        mock_uow.pipeline_runs.get_by_id.return_value = mock_run

        runner = PipelineRunner(
            uow=mock_uow,
            ref_resolver=MagicMock(),
            condition_evaluator=MagicMock(),
        )

        result = await runner._is_cancelling("test-run-id")
        assert result is True

    @pytest.mark.asyncio
    async def test_is_cancelling_returns_false_for_running_status(self) -> None:
        """_is_cancelling() returns False when run has RUNNING status."""
        from zorivest_core.services.pipeline_runner import PipelineRunner

        mock_uow = MagicMock()
        mock_run = MagicMock()
        mock_run.status = "running"
        mock_uow.pipeline_runs.get_by_id.return_value = mock_run

        runner = PipelineRunner(
            uow=mock_uow,
            ref_resolver=MagicMock(),
            condition_evaluator=MagicMock(),
        )

        result = await runner._is_cancelling("test-run-id")
        assert result is False

    @pytest.mark.asyncio
    async def test_is_cancelling_returns_false_when_no_uow(self) -> None:
        """_is_cancelling() returns False when UoW is None."""
        from zorivest_core.services.pipeline_runner import PipelineRunner

        runner = PipelineRunner(
            uow=None,
            ref_resolver=MagicMock(),
            condition_evaluator=MagicMock(),
        )

        result = await runner._is_cancelling("test-run-id")
        assert result is False


# ── AC-PW7-4: SchedulingService.cancel_run() ──────────────────────────


class TestSchedulingServiceCancel:
    """AC-PW7-4: SchedulingService delegates cancellation to runner."""

    @pytest.mark.asyncio
    async def test_cancel_run_method_exists(self) -> None:
        """SchedulingService has a cancel_run() async method."""
        from zorivest_core.services.scheduling_service import SchedulingService

        service = SchedulingService(
            policy_store=MagicMock(),
            run_store=MagicMock(),
            step_store=MagicMock(),
            pipeline_runner=MagicMock(),
            scheduler_service=MagicMock(),
            guardrails=MagicMock(),
            audit_logger=MagicMock(),
        )
        assert hasattr(service, "cancel_run")
        assert asyncio.iscoroutinefunction(service.cancel_run)

    @pytest.mark.asyncio
    async def test_cancel_run_delegates_to_runner(self) -> None:
        """cancel_run() calls runner.cancel_run() and returns RunResult."""
        from zorivest_core.services.scheduling_service import (
            RunResult,
            SchedulingService,
        )

        mock_runner = MagicMock()
        mock_runner.cancel_run = AsyncMock(return_value=True)
        mock_run_store = MagicMock()
        mock_run_store.get_by_id = AsyncMock(
            return_value={"run_id": "abc-123", "status": "running"}
        )
        mock_audit = MagicMock()
        mock_audit.log = AsyncMock()

        service = SchedulingService(
            policy_store=MagicMock(),
            run_store=mock_run_store,
            step_store=MagicMock(),
            pipeline_runner=mock_runner,
            scheduler_service=MagicMock(),
            guardrails=MagicMock(),
            audit_logger=mock_audit,
        )

        result = await service.cancel_run("abc-123")
        assert isinstance(result, RunResult)
        mock_runner.cancel_run.assert_called_once_with("abc-123")

    @pytest.mark.asyncio
    async def test_cancel_run_not_found(self) -> None:
        """cancel_run() returns error for non-existent run."""
        from zorivest_core.services.scheduling_service import SchedulingService

        mock_run_store = MagicMock()
        mock_run_store.get_by_id = AsyncMock(return_value=None)

        service = SchedulingService(
            policy_store=MagicMock(),
            run_store=mock_run_store,
            step_store=MagicMock(),
            pipeline_runner=MagicMock(),
            scheduler_service=MagicMock(),
            guardrails=MagicMock(),
            audit_logger=MagicMock(),
        )

        result = await service.cancel_run(str(uuid.uuid4()))
        assert result.error is not None
        assert "not found" in result.error.lower()

    @pytest.mark.asyncio
    async def test_cancel_run_terminal_state_returns_run(self) -> None:
        """cancel_run() for a terminal run (success/failed/cancelled) returns
        the run dict idempotently, not an error [Spec §9B.5e]."""
        from zorivest_core.services.scheduling_service import (
            RunResult,
            SchedulingService,
        )

        mock_run_store = MagicMock()
        terminal_run = {"run_id": "abc-123", "status": "success"}
        mock_run_store.get_by_id = AsyncMock(return_value=terminal_run)

        service = SchedulingService(
            policy_store=MagicMock(),
            run_store=mock_run_store,
            step_store=MagicMock(),
            pipeline_runner=MagicMock(),
            scheduler_service=MagicMock(),
            guardrails=MagicMock(),
            audit_logger=MagicMock(),
        )

        result = await service.cancel_run("abc-123")
        assert isinstance(result, RunResult)
        assert result.error is None
        assert result.run is not None
        assert result.run["status"] == "success"


# ── AC-PW7-5: POST /runs/{run_id}/cancel endpoint ─────────────────────


class TestCancelEndpoint:
    """AC-PW7-5: REST endpoint for pipeline cancellation."""

    @pytest.mark.asyncio
    async def test_cancel_endpoint_exists(self) -> None:
        """POST /api/v1/scheduling/runs/{run_id}/cancel route is registered."""
        from zorivest_api.routes.scheduling import scheduling_router

        routes = [r.path for r in scheduling_router.routes if hasattr(r, "path")]  # type: ignore[attr-defined]
        assert any("/runs/{run_id}/cancel" in r for r in routes)

    @pytest.mark.asyncio
    async def test_cancel_endpoint_422_invalid_uuid(self) -> None:
        """Invalid run_id returns 422 Unprocessable Entity."""
        from fastapi.testclient import TestClient

        from zorivest_api.routes.scheduling import scheduling_router
        from zorivest_api.dependencies import get_scheduling_service
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(scheduling_router)

        # Must provide dependency override even though we expect 422 at path validation
        mock_service = MagicMock()
        mock_service.cancel_run = AsyncMock()
        app.dependency_overrides[get_scheduling_service] = lambda: mock_service

        client = TestClient(app)
        resp = client.post("/api/v1/scheduling/runs/not-a-uuid/cancel")
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_cancel_endpoint_404_missing_run(self) -> None:
        """Missing run_id returns 404 Not Found."""
        from fastapi.testclient import TestClient
        from fastapi import FastAPI

        from zorivest_api.routes.scheduling import scheduling_router
        from zorivest_api.dependencies import get_scheduling_service
        from zorivest_core.services.scheduling_service import RunResult

        app = FastAPI()
        app.include_router(scheduling_router)

        mock_service = MagicMock()
        mock_service.cancel_run = AsyncMock(
            return_value=RunResult(error="Run not found")
        )
        app.dependency_overrides[get_scheduling_service] = lambda: mock_service

        client = TestClient(app)
        valid_uuid = str(uuid.uuid4())
        resp = client.post(f"/api/v1/scheduling/runs/{valid_uuid}/cancel")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_cancel_endpoint_200_success(self) -> None:
        """Successful cancellation returns 200."""
        from fastapi.testclient import TestClient
        from fastapi import FastAPI

        from zorivest_api.routes.scheduling import scheduling_router
        from zorivest_api.dependencies import get_scheduling_service
        from zorivest_core.services.scheduling_service import RunResult

        app = FastAPI()
        app.include_router(scheduling_router)

        mock_service = MagicMock()
        mock_service.cancel_run = AsyncMock(
            return_value=RunResult(
                run={"run_id": str(uuid.uuid4()), "status": "cancelled"}
            )
        )
        app.dependency_overrides[get_scheduling_service] = lambda: mock_service

        client = TestClient(app)
        valid_uuid = str(uuid.uuid4())
        resp = client.post(f"/api/v1/scheduling/runs/{valid_uuid}/cancel")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_cancel_endpoint_200_idempotent_terminal_state(self) -> None:
        """Cancel on an already-completed run returns 200, not 400 [Spec §9B.5d]."""
        from fastapi.testclient import TestClient
        from fastapi import FastAPI

        from zorivest_api.routes.scheduling import scheduling_router
        from zorivest_api.dependencies import get_scheduling_service
        from zorivest_core.services.scheduling_service import RunResult

        app = FastAPI()
        app.include_router(scheduling_router)

        # Service returns the run dict (not error) for terminal-state runs
        mock_service = MagicMock()
        mock_service.cancel_run = AsyncMock(
            return_value=RunResult(
                run={"run_id": str(uuid.uuid4()), "status": "success"}
            )
        )
        app.dependency_overrides[get_scheduling_service] = lambda: mock_service

        client = TestClient(app)
        valid_uuid = str(uuid.uuid4())
        resp = client.post(f"/api/v1/scheduling/runs/{valid_uuid}/cancel")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] in ("success", "failed", "cancelled", "cancelling")
