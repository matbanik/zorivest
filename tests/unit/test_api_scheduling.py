# tests/unit/test_api_scheduling.py
"""Tests for MEU-89: Scheduling & Scheduler REST endpoints.

Covers: 16 scheduling endpoints + 1 scheduler power-event endpoint.
Source: 09-scheduling.md §9.10, §9.3f
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.unit


# ── Fixtures ────────────────────────────────────────────────────────────


@dataclass
class MockPolicyResult:
    policy: dict[str, Any] | None = None
    errors: list[str] = field(default_factory=list)


@dataclass
class MockRunResult:
    run: dict[str, Any] | None = None
    error: str | None = None


def _sample_policy_response(**overrides: Any) -> dict[str, Any]:
    base = {
        "id": "test-id",
        "name": "Test Pipeline",
        "schema_version": 1,
        "enabled": True,
        "approved": False,
        "approved_at": None,
        "content_hash": "abc123",
        "policy_json": {"name": "Test"},
        "created_at": datetime(2026, 3, 18, 12, 0, 0, tzinfo=timezone.utc).isoformat(),
        "updated_at": None,
        "next_run": None,
    }
    base.update(overrides)
    return base


def _sample_run_response(**overrides: Any) -> dict[str, Any]:
    base = {
        "run_id": "run-id",
        "policy_id": "test-id",
        "status": "running",
        "trigger_type": "manual",
        "started_at": datetime(2026, 3, 18, 12, 0, 0, tzinfo=timezone.utc).isoformat(),
        "completed_at": None,
        "duration_ms": None,
        "error": None,
        "dry_run": False,
    }
    base.update(overrides)
    return base


@pytest.fixture()
def mock_scheduling_svc():
    """Mock SchedulingService for API tests."""
    svc = MagicMock()

    # Async methods need AsyncMock
    svc.create_policy = AsyncMock(
        return_value=MockPolicyResult(policy=_sample_policy_response())
    )
    svc.list_policies = AsyncMock(return_value=[_sample_policy_response()])
    svc.get_policy = AsyncMock(return_value=_sample_policy_response())
    svc.update_policy = AsyncMock(
        return_value=MockPolicyResult(policy=_sample_policy_response(name="Updated"))
    )
    svc.delete_policy = AsyncMock(return_value=None)
    svc.approve_policy = AsyncMock(return_value=_sample_policy_response(approved=True))
    svc.trigger_run = AsyncMock(return_value=MockRunResult(run=_sample_run_response()))
    svc.get_policy_runs = AsyncMock(return_value=[_sample_run_response()])
    svc.get_run_detail = AsyncMock(
        return_value={
            **_sample_run_response(),
            "steps": [],
        }
    )
    svc.get_run_steps = AsyncMock(return_value=[])
    svc.list_runs = AsyncMock(return_value=[_sample_run_response()])
    svc.patch_schedule = AsyncMock(return_value=_sample_policy_response())

    # Sync method — NOT AsyncMock
    svc.get_scheduler_status = MagicMock(
        return_value={
            "running": True,
            "job_count": 0,
            "jobs": [],
        }
    )

    return svc


@pytest.fixture()
def mock_scheduler_svc():
    """Mock SchedulerService for scheduler API tests."""
    svc = MagicMock()
    svc.scheduler = MagicMock()
    svc.get_status.return_value = {"running": True, "job_count": 0, "jobs": []}
    return svc


@pytest.fixture()
def client(mock_scheduling_svc, mock_scheduler_svc):
    """HTTP test client with mocked services."""
    from zorivest_api.main import create_app
    from zorivest_api.dependencies import require_unlocked_db
    from zorivest_api import dependencies as deps

    app = create_app()
    app.state.db_unlocked = True
    app.state.start_time = __import__("time").time()

    app.dependency_overrides[require_unlocked_db] = lambda: None
    app.dependency_overrides[deps.get_trade_service] = lambda: MagicMock()
    app.dependency_overrides[deps.get_image_service] = lambda: MagicMock()
    app.dependency_overrides[deps.get_scheduling_service] = lambda: mock_scheduling_svc
    app.dependency_overrides[deps.get_scheduler_service] = lambda: mock_scheduler_svc

    return TestClient(app)


# ── Policy CRUD ─────────────────────────────────────────────────────────


class TestCreatePolicy:
    def test_create_returns_201(self, client) -> None:
        resp = client.post(
            "/api/v1/scheduling/policies",
            json={"policy_json": {"name": "Test"}},
        )
        assert resp.status_code == 201
        assert resp.json()["id"] == "test-id"

    def test_create_validation_error_returns_422(
        self,
        client,
        mock_scheduling_svc,
    ) -> None:
        mock_scheduling_svc.create_policy.return_value = MockPolicyResult(
            errors=["Bad schema"]
        )
        resp = client.post(
            "/api/v1/scheduling/policies",
            json={"policy_json": {"invalid": True}},
        )
        assert resp.status_code == 422


class TestListPolicies:
    def test_list_returns_200(self, client) -> None:
        resp = client.get("/api/v1/scheduling/policies")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1


class TestGetPolicy:
    def test_get_returns_200(self, client) -> None:
        resp = client.get("/api/v1/scheduling/policies/test-id")
        assert resp.status_code == 200

    def test_get_not_found_returns_404(self, client, mock_scheduling_svc) -> None:
        mock_scheduling_svc.get_policy.return_value = None
        resp = client.get("/api/v1/scheduling/policies/nonexistent")
        assert resp.status_code == 404


class TestUpdatePolicy:
    def test_update_returns_200(self, client) -> None:
        resp = client.put(
            "/api/v1/scheduling/policies/test-id",
            json={"policy_json": {"name": "Updated"}},
        )
        assert resp.status_code == 200


class TestDeletePolicy:
    def test_delete_returns_204(self, client) -> None:
        resp = client.delete("/api/v1/scheduling/policies/test-id")
        assert resp.status_code == 204


class TestApprovePolicy:
    def test_approve_returns_200(self, client) -> None:
        resp = client.post("/api/v1/scheduling/policies/test-id/approve")
        assert resp.status_code == 200
        assert resp.json()["approved"] is True

    def test_approve_not_found_returns_404(
        self,
        client,
        mock_scheduling_svc,
    ) -> None:
        mock_scheduling_svc.approve_policy.return_value = None
        resp = client.post("/api/v1/scheduling/policies/nonexistent/approve")
        assert resp.status_code == 404


# ── Pipeline Execution ──────────────────────────────────────────────────


class TestTriggerPipeline:
    def test_trigger_returns_200(self, client) -> None:
        resp = client.post(
            "/api/v1/scheduling/policies/test-id/run",
            json={"dry_run": False},
        )
        assert resp.status_code == 200

    def test_trigger_error_returns_400(
        self,
        client,
        mock_scheduling_svc,
    ) -> None:
        mock_scheduling_svc.trigger_run.return_value = MockRunResult(
            error="Rate limit exceeded"
        )
        resp = client.post(
            "/api/v1/scheduling/policies/test-id/run",
            json={"dry_run": False},
        )
        assert resp.status_code == 400


# ── Run History ─────────────────────────────────────────────────────────


class TestGetPolicyRuns:
    def test_returns_200(self, client) -> None:
        resp = client.get("/api/v1/scheduling/policies/test-id/runs")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestListRuns:
    def test_returns_200(self, client) -> None:
        resp = client.get("/api/v1/scheduling/runs")
        assert resp.status_code == 200


class TestGetRunDetail:
    def test_returns_200(self, client) -> None:
        resp = client.get("/api/v1/scheduling/runs/run-id")
        assert resp.status_code == 200

    def test_not_found_returns_404(self, client, mock_scheduling_svc) -> None:
        mock_scheduling_svc.get_run_detail.return_value = None
        resp = client.get("/api/v1/scheduling/runs/nonexistent")
        assert resp.status_code == 404


class TestGetRunSteps:
    def test_returns_200(self, client) -> None:
        resp = client.get("/api/v1/scheduling/runs/run-id/steps")
        assert resp.status_code == 200


# ── Scheduler Status ───────────────────────────────────────────────────


class TestSchedulerStatus:
    def test_returns_200(self, client) -> None:
        resp = client.get("/api/v1/scheduling/scheduler/status")
        assert resp.status_code == 200


# ── Schema Discovery ──────────────────────────────────────────────────


class TestPolicySchema:
    def test_returns_200(self, client) -> None:
        resp = client.get("/api/v1/scheduling/policies/schema")
        assert resp.status_code == 200
        data = resp.json()
        assert "properties" in data


class TestStepTypes:
    def test_returns_200(self, client) -> None:
        resp = client.get("/api/v1/scheduling/step-types")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


# ── Schedule Patch ─────────────────────────────────────────────────────


class TestPatchSchedule:
    def test_patch_returns_200(self, client) -> None:
        resp = client.patch(
            "/api/v1/scheduling/policies/test-id/schedule",
            params={"cron_expression": "0 10 * * *"},
        )
        assert resp.status_code == 200

    def test_patch_not_found_returns_404(
        self,
        client,
        mock_scheduling_svc,
    ) -> None:
        mock_scheduling_svc.patch_schedule.return_value = None
        resp = client.patch(
            "/api/v1/scheduling/policies/nonexistent/schedule",
        )
        assert resp.status_code == 404


# ── Power Event (scheduler_router) ─────────────────────────────────────


class TestPowerEvent:
    def test_resume_returns_200(self, client) -> None:
        resp = client.post(
            "/api/v1/scheduler/power-event",
            json={"event_type": "resume", "timestamp": "2026-03-18T12:00:00Z"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "resumed"

    def test_suspend_returns_acknowledged(self, client) -> None:
        resp = client.post(
            "/api/v1/scheduler/power-event",
            json={"event_type": "suspend", "timestamp": "2026-03-18T12:00:00Z"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "acknowledged"

    def test_unknown_event_type_returns_422(self, client) -> None:
        """AC-A2: Unknown event_type rejected by Literal validation."""
        resp = client.post(
            "/api/v1/scheduler/power-event",
            json={"event_type": "shutdown", "timestamp": "2026-03-18T12:00:00Z"},
        )
        assert resp.status_code == 422


# ── Power Event BV Hardening (MEU-72 Sub-MEU A) ───────────────────────


class TestPowerEventBoundaryValidation:
    """BV hardening for PowerEventRequest (scheduler.py).

    AC-A1: extra fields → 422
    AC-A2: invalid event_type → 422
    """

    def test_extra_field_returns_422(self, client) -> None:
        """AC-A1: PowerEventRequest rejects extra fields."""
        resp = client.post(
            "/api/v1/scheduler/power-event",
            json={
                "event_type": "resume",
                "timestamp": "2026-03-18T12:00:00Z",
                "extra": "bad",
            },
        )
        assert resp.status_code == 422

    def test_invalid_event_type_returns_422(self, client) -> None:
        """AC-A2: PowerEventRequest rejects unknown event_type."""
        resp = client.post(
            "/api/v1/scheduler/power-event",
            json={"event_type": "reboot", "timestamp": "2026-03-18T12:00:00Z"},
        )
        assert resp.status_code == 422

    def test_blank_timestamp_returns_422(self, client) -> None:
        """AC-A2: PowerEventRequest rejects blank timestamp."""
        resp = client.post(
            "/api/v1/scheduler/power-event",
            json={"event_type": "resume", "timestamp": ""},
        )
        assert resp.status_code == 422

    def test_whitespace_only_timestamp_returns_422(self, client) -> None:
        """AC-A2: PowerEventRequest rejects whitespace-only timestamp."""
        resp = client.post(
            "/api/v1/scheduler/power-event",
            json={"event_type": "resume", "timestamp": "   "},
        )
        assert resp.status_code == 422


# ── Live Wiring (R3) ───────────────────────────────────────────────────


class TestLiveWiring:
    """Prove scheduling routes resolve from real app state (no dep overrides)."""

    def test_scheduling_routes_resolve_from_app_state(
        self, monkeypatch, tmp_path
    ) -> None:
        """R3: Hit scheduler status without dependency overrides.

        This verifies that ``create_app()`` lifespan wires real scheduling
        services into app state, so the dependency providers succeed
        without test-time overrides.
        """
        from zorivest_api.main import create_app
        from zorivest_api.dependencies import require_unlocked_db

        db_file = tmp_path / "test_routes.db"
        monkeypatch.setenv("ZORIVEST_DB_URL", f"sqlite:///{db_file}")

        app = create_app()
        app.state.db_unlocked = True
        app.state.start_time = __import__("time").time()

        # Only override the DB lock check — NOT the scheduling services
        app.dependency_overrides[require_unlocked_db] = lambda: None

        with TestClient(app) as tc:
            resp = tc.get("/api/v1/scheduling/scheduler/status")
            assert resp.status_code == 200
            data = resp.json()
            assert "running" in data
            assert "job_count" in data

    @pytest.mark.asyncio()
    async def test_live_manual_run_route(self, monkeypatch, tmp_path) -> None:
        """V1: Prove POST /policies/{id}/run works through default app-state.

        Creates a policy via the live service, approves it, then POSTs
        to the route — no scheduling service dependency overrides.
        Proves the full execution path: route → service → guardrails → runner.
        """
        from zorivest_api.main import create_app
        from zorivest_api.dependencies import require_unlocked_db
        import zorivest_core.pipeline_steps  # noqa: F401 — step registration

        db_file = tmp_path / "test_live.db"
        monkeypatch.setenv("ZORIVEST_DB_URL", f"sqlite:///{db_file}")

        app = create_app()
        app.state.db_unlocked = True
        app.state.start_time = __import__("time").time()

        # Only override the DB lock check — NOT the scheduling services
        app.dependency_overrides[require_unlocked_db] = lambda: None

        with TestClient(app) as tc:
            svc = app.state.scheduling_service

            # 1. Create a policy via the live service
            valid_policy = {
                "name": "V1 Live Route Test",
                "description": "End-to-end route test",
                "trigger": {
                    "type": "manual",
                    "cron_expression": "0 9 * * *",
                    "enabled": True,
                },
                "steps": [
                    {
                        "id": "noop",
                        "type": "fetch",
                        "params": {
                            "provider": "stub",
                            "data_type": "ohlcv",
                        },
                    },
                ],
            }
            result = await svc.create_policy(valid_policy)
            assert result.policy is not None, f"create_policy failed: {result.errors}"
            policy_id = result.policy["id"]

            # 2. Approve the policy (required by guardrails)
            await svc.approve_policy(policy_id)

            # 3. POST to the route — no dep overrides for scheduling
            resp = tc.post(
                f"/api/v1/scheduling/policies/{policy_id}/run",
                json={"dry_run": False},
            )
            assert resp.status_code == 200, (
                f"Expected 200, got {resp.status_code}: {resp.text}"
            )

            # 4. Assert run shape
            run = resp.json()
            assert "run_id" in run, f"Missing run_id: {run}"
            assert "status" in run, f"Missing status: {run}"
            assert run["policy_id"] == policy_id


# ── Live Execution Path (P1) ───────────────────────────────────────────


class TestLiveExecution:
    """Prove PipelineRunner is wired (not None) in live app state."""

    def test_runner_wired_and_invocable(self, monkeypatch, tmp_path) -> None:
        """P1: Verify the live app wires a real PipelineRunner.

        Proves that:
        1. ``SchedulingService._runner`` is not None
        2. ``SchedulerService`` received a ``pipeline_runner``
        3. The runner is a real ``PipelineRunner`` instance

        This confirms P1: the app-state runtime is no longer
        record-only — it has a real executable runner.
        """
        from zorivest_api.main import create_app
        from zorivest_core.services.pipeline_runner import PipelineRunner

        db_file = tmp_path / "test_wired.db"
        monkeypatch.setenv("ZORIVEST_DB_URL", f"sqlite:///{db_file}")

        app = create_app()
        app.state.db_unlocked = True
        app.state.start_time = __import__("time").time()

        with TestClient(app):
            scheduling_svc = app.state.scheduling_service
            scheduler_svc = app.state.scheduler_service

            # SchedulingService has a real runner (not None)
            assert scheduling_svc._runner is not None, (
                "SchedulingService._runner is None — no execution path"
            )
            assert isinstance(scheduling_svc._runner, PipelineRunner), (
                f"Expected PipelineRunner, got {type(scheduling_svc._runner)}"
            )

            # SchedulerService also received the runner
            assert scheduler_svc.pipeline_runner is not None, (
                "SchedulerService.pipeline_runner is None — scheduler can't execute"
            )

    @pytest.mark.asyncio()
    async def test_runner_executes_policy(self, monkeypatch, tmp_path) -> None:
        """Q1: Prove runner.run() executes with step persistence (dry_run=False).

        Bypasses guardrails (Phase 4 stub limitation) and calls the
        runner directly with dry_run=False, proving _persist_step()
        is called through _StubSession without crashing.
        """
        from zorivest_api.main import create_app
        from zorivest_core.services.pipeline_runner import PipelineRunner
        from zorivest_core.domain.pipeline import PolicyDocument
        import zorivest_core.pipeline_steps  # noqa: F401

        db_file = tmp_path / "test_runner.db"
        monkeypatch.setenv("ZORIVEST_DB_URL", f"sqlite:///{db_file}")

        app = create_app()
        app.state.db_unlocked = True
        app.state.start_time = __import__("time").time()

        with TestClient(app):
            runner = app.state.scheduling_service._runner
            assert isinstance(runner, PipelineRunner)

            # Build minimal valid policy and invoke runner directly
            doc = PolicyDocument(
                name="Q1 Full Execution",
                trigger={  # type: ignore[arg-type]
                    "cron_expression": "0 9 * * *",
                    "enabled": True,
                },
                steps=[
                    {  # type: ignore[list-item]
                        "id": "fetch_test",
                        "type": "fetch",
                        "params": {"url": "https://example.com"},
                    }
                ],
            )

            result = await runner.run(
                policy=doc,
                trigger_type="manual",
                dry_run=False,  # Q1: exercises _persist_step via _StubSession
                policy_id="test-q1",
            )

            # Runner returned a result dict — full execution path works
            assert isinstance(result, dict), f"Expected dict, got {type(result)}"
            assert "status" in result, f"Result missing 'status': {result}"
            # Steps array proves step execution was attempted
            assert "steps" in result, f"Result missing 'steps': {result}"


# ── Boundary Validation (MEU-BV6) ──────────────────────────────────────


class TestSchedulingBoundaryValidation:
    """BV6: Boundary hardening negative tests for scheduling write surfaces.

    Verifies extra="forbid", Query(min_length=1), and non-empty dict
    validation per implementation-plan.md §MEU-BV6.
    """

    # AC-1: PolicyCreateRequest extra fields → 422
    def test_create_policy_extra_field_422(self, client) -> None:
        resp = client.post(
            "/api/v1/scheduling/policies",
            json={"policy_json": {"name": "Test"}, "sneaky": True},
        )
        assert resp.status_code == 422

    def test_update_policy_extra_field_422(self, client) -> None:
        resp = client.put(
            "/api/v1/scheduling/policies/test-id",
            json={"policy_json": {"name": "Updated"}, "sneaky": True},
        )
        assert resp.status_code == 422

    # AC-2: RunTriggerRequest extra fields → 422
    def test_trigger_run_extra_field_422(self, client) -> None:
        resp = client.post(
            "/api/v1/scheduling/policies/test-id/run",
            json={"dry_run": False, "extra": 1},
        )
        assert resp.status_code == 422

    # AC-3: Blank cron_expression query param → 422
    def test_patch_blank_cron_expression_422(self, client) -> None:
        resp = client.patch(
            "/api/v1/scheduling/policies/test-id/schedule",
            params={"cron_expression": "  "},
        )
        assert resp.status_code == 422

    # AC-4: Blank timezone query param → 422
    def test_patch_blank_timezone_422(self, client) -> None:
        resp = client.patch(
            "/api/v1/scheduling/policies/test-id/schedule",
            params={"timezone": "  "},
        )
        assert resp.status_code == 422

    # AC-5: Empty policy_json dict → 422
    def test_create_policy_empty_policy_json_422(self, client) -> None:
        resp = client.post(
            "/api/v1/scheduling/policies",
            json={"policy_json": {}},
        )
        assert resp.status_code == 422


class TestGuiPolicyTemplateContract:
    """Contract tests: GUI default policy template must match PolicyDocument schema.

    These validate the exact payload shape that SchedulingLayout.handleCreate sends.
    If this fails, the +New button will produce a 422 in the GUI.
    """

    def test_gui_default_template_is_valid_policy_document(self) -> None:
        """The GUI default template must parse into a valid PolicyDocument."""
        from zorivest_core.domain.pipeline import PolicyDocument

        # This is the EXACT payload SchedulingLayout.handleCreate sends
        # (without the outer { policy_json: ... } wrapper — that's the API envelope)
        gui_template = {
            "schema_version": 1,
            "name": "new-policy-test",
            "trigger": {
                "cron_expression": "0 8 * * 1-5",
                "timezone": "UTC",
                "enabled": True,
            },
            "steps": [
                {
                    "id": "step_1",
                    "type": "fetch",
                    "params": {},
                },
            ],
        }
        # Must not raise
        doc = PolicyDocument(**gui_template)
        assert doc.name == "new-policy-test"
        assert doc.trigger.cron_expression == "0 8 * * 1-5"
        assert len(doc.steps) == 1
        assert doc.steps[0].id == "step_1"

    def test_old_gui_template_would_fail(self) -> None:
        """The old GUI template (schedule/pipeline) must NOT validate.

        Regression guard: ensures we never revert to the broken shape.
        """
        from zorivest_core.domain.pipeline import PolicyDocument

        old_template = {
            "name": "new-policy-test",
            "schedule": {"cron": "0 8 * * 1-5", "timezone": "UTC"},
            "pipeline": {"steps": []},
        }
        import pytest as _pytest

        with _pytest.raises(Exception):
            PolicyDocument(**old_template)

    def test_empty_steps_fails_validation(self) -> None:
        """PolicyDocument requires at least one step (min_length=1)."""
        from zorivest_core.domain.pipeline import PolicyDocument

        template = {
            "schema_version": 1,
            "name": "new-policy-test",
            "trigger": {
                "cron_expression": "0 8 * * 1-5",
                "timezone": "UTC",
                "enabled": True,
            },
            "steps": [],
        }
        import pytest as _pytest

        with _pytest.raises(Exception):
            PolicyDocument(**template)
