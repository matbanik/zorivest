# tests/unit/test_scheduling_service.py
"""Tests for MEU-89: SchedulingService facade.

Covers: create/list/get/update/delete policies, approve, trigger_run,
run history, scheduler status, rate-limit/approval guard integration.
Source: 09-scheduling.md §9.10
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from unittest.mock import MagicMock, AsyncMock

import pytest

from zorivest_core.services.pipeline_guardrails import (
    PipelineGuardrails,
    PipelineRateLimits,
)
from zorivest_core.services.scheduling_service import SchedulingService
from zorivest_core.domain.step_registry import STEP_REGISTRY

pytestmark = pytest.mark.unit


@pytest.fixture(autouse=True)
def _register_test_step():
    """Register a dummy 'fetch' step type so validate_policy() passes."""
    class _DummyParams:
        @classmethod
        def model_json_schema(cls):
            return {}

    class _DummyFetchStep:
        type_name = "fetch"
        side_effects = False
        Params = _DummyParams

    STEP_REGISTRY["fetch"] = _DummyFetchStep
    yield
    STEP_REGISTRY.pop("fetch", None)


# ── Test helpers ────────────────────────────────────────────────────────


class FakeAuditCounter:
    def __init__(self, counts: dict[str, int] | None = None) -> None:
        self._counts = counts or {}

    async def count_actions_since(self, action: str, since: datetime) -> int:
        return self._counts.get(action, 0)


class FakePolicyLookup:
    def __init__(self, policies: dict[str, Any] | None = None) -> None:
        self._policies = policies or {}

    async def get_by_id(self, policy_id: str) -> Any:
        return self._policies.get(policy_id)


class FakePolicyStore:
    """In-memory policy store for testing."""

    def __init__(self) -> None:
        self._data: dict[str, dict[str, Any]] = {}

    async def create(self, data: dict[str, Any]) -> dict[str, Any]:
        self._data[data["id"]] = data
        return data

    async def get_by_id(self, policy_id: str) -> dict[str, Any] | None:
        return self._data.get(policy_id)

    async def list_all(self, enabled_only: bool = False) -> list[dict[str, Any]]:
        items = list(self._data.values())
        if enabled_only:
            items = [p for p in items if p.get("enabled")]
        return items

    async def update(self, policy_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
        if policy_id not in self._data:
            return None
        self._data[policy_id].update(data)
        return self._data[policy_id]

    async def delete(self, policy_id: str) -> None:
        self._data.pop(policy_id, None)


class FakeRunStore:
    def __init__(self) -> None:
        self._data: list[dict[str, Any]] = []

    async def create(self, data: dict[str, Any]) -> dict[str, Any]:
        self._data.append(data)
        return data

    async def get_by_id(self, run_id: str) -> dict[str, Any] | None:
        return next((r for r in self._data if r.get("run_id") == run_id), None)

    async def list_for_policy(self, policy_id: str, limit: int = 20) -> list[dict[str, Any]]:
        return [r for r in self._data if r.get("policy_id") == policy_id][:limit]

    async def list_recent(self, limit: int = 20) -> list[dict[str, Any]]:
        return self._data[:limit]

    async def update(self, run_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
        for r in self._data:
            if r.get("run_id") == run_id:
                r.update(data)
                return r
        return None


class FakeStepStore:
    async def list_for_run(self, run_id: str) -> list[dict[str, Any]]:
        return []


class FakeAuditLogger:
    def __init__(self) -> None:
        self.entries: list[dict[str, Any]] = []

    async def log(
        self, action: str, resource_type: str, resource_id: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.entries.append({
            "action": action, "resource_type": resource_type,
            "resource_id": resource_id,
        })


def _sample_policy_json(**overrides: Any) -> dict[str, Any]:
    """Minimal valid PolicyDocument JSON."""
    base = {
        "schema_version": 1,
        "name": "Test Pipeline",
        "metadata": {"author": "test", "description": "Testing"},
        "trigger": {
            "cron_expression": "0 9 * * 1",
            "timezone": "UTC",
            "enabled": True,
            "misfire_grace_time": 3600,
            "coalesce": True,
            "max_instances": 1,
        },
        "steps": [
            {
                "id": "fetch_data",
                "type": "fetch",
                "params": {"tickers": ["AAPL"], "data_type": "quote"},
                "timeout": 300,
            }
        ],
    }
    base.update(overrides)
    return base


def _make_service(
    audit_counts: dict[str, int] | None = None,
    approval_policies: dict[str, Any] | None = None,
) -> tuple[SchedulingService, FakeAuditLogger, FakePolicyStore]:
    audit_counter = FakeAuditCounter(audit_counts)
    policy_lookup = FakePolicyLookup(approval_policies)
    guardrails = PipelineGuardrails(
        audit_counter=audit_counter,
        policy_lookup=policy_lookup,
    )
    policy_store = FakePolicyStore()
    run_store = FakeRunStore()
    step_store = FakeStepStore()
    audit_logger = FakeAuditLogger()
    scheduler_service = MagicMock()
    scheduler_service.get_status.return_value = {
        "running": True, "job_count": 0, "jobs": [],
    }
    pipeline_runner = MagicMock()
    # Make the runner.run() return an awaitable with success result
    pipeline_runner.run = AsyncMock(return_value={"status": "success", "error": None})

    svc = SchedulingService(
        policy_store=policy_store,
        run_store=run_store,
        step_store=step_store,
        pipeline_runner=pipeline_runner,
        scheduler_service=scheduler_service,
        guardrails=guardrails,
        audit_logger=audit_logger,
    )
    return svc, audit_logger, policy_store


# ── Policy CRUD ─────────────────────────────────────────────────────────


class TestCreatePolicy:
    @pytest.mark.asyncio
    async def test_valid_policy_creates(self) -> None:
        svc, audit, _ = _make_service()
        result = await svc.create_policy(_sample_policy_json())
        assert result.policy is not None
        assert result.errors == []
        assert result.policy["name"] == "Test Pipeline"

    @pytest.mark.asyncio
    async def test_invalid_policy_returns_errors(self) -> None:
        svc, _, _ = _make_service()
        result = await svc.create_policy({"invalid": True})
        assert result.errors
        assert result.policy is None

    @pytest.mark.asyncio
    async def test_create_logs_audit(self) -> None:
        svc, audit, _ = _make_service()
        await svc.create_policy(_sample_policy_json())
        assert any(e["action"] == "policy.create" for e in audit.entries)

    @pytest.mark.asyncio
    async def test_rate_limit_blocks_creation(self) -> None:
        svc, _, _ = _make_service(audit_counts={"policy.create": 20})
        result = await svc.create_policy(_sample_policy_json())
        assert result.errors
        assert "limit" in result.errors[0].lower()


class TestListPolicies:
    @pytest.mark.asyncio
    async def test_list_returns_created(self) -> None:
        svc, _, _ = _make_service()
        await svc.create_policy(_sample_policy_json())
        policies = await svc.list_policies()
        assert len(policies) == 1


class TestGetPolicy:
    @pytest.mark.asyncio
    async def test_get_existing(self) -> None:
        svc, _, _ = _make_service()
        result = await svc.create_policy(_sample_policy_json())
        policy = await svc.get_policy(result.policy["id"])
        assert policy is not None

    @pytest.mark.asyncio
    async def test_get_nonexistent_returns_none(self) -> None:
        svc, _, _ = _make_service()
        policy = await svc.get_policy("nonexistent")
        assert policy is None


class TestUpdatePolicy:
    @pytest.mark.asyncio
    async def test_update_resets_approval(self) -> None:
        svc, _, store = _make_service()
        result = await svc.create_policy(_sample_policy_json())
        pid = result.policy["id"]
        # Manually approve
        store._data[pid]["approved"] = True
        store._data[pid]["approved_hash"] = store._data[pid]["content_hash"]
        # Update with different policy
        updated_json = _sample_policy_json(name="Updated Pipeline")
        result2 = await svc.update_policy(pid, updated_json)
        assert result2.policy is not None
        assert result2.policy["approved"] is False

    @pytest.mark.asyncio
    async def test_update_nonexistent_returns_error(self) -> None:
        svc, _, _ = _make_service()
        result = await svc.update_policy("nonexistent", _sample_policy_json())
        assert result.errors


class TestDeletePolicy:
    @pytest.mark.asyncio
    async def test_delete_removes(self) -> None:
        svc, _, _ = _make_service()
        result = await svc.create_policy(_sample_policy_json())
        pid = result.policy["id"]
        await svc.delete_policy(pid)
        assert await svc.get_policy(pid) is None


class TestApprovePolicy:
    @pytest.mark.asyncio
    async def test_approve_sets_flag(self) -> None:
        svc, _, _ = _make_service()
        result = await svc.create_policy(_sample_policy_json())
        pid = result.policy["id"]
        approved = await svc.approve_policy(pid)
        assert approved is not None
        assert approved["approved"] is True

    @pytest.mark.asyncio
    async def test_approve_nonexistent_returns_none(self) -> None:
        svc, _, _ = _make_service()
        result = await svc.approve_policy("nonexistent")
        assert result is None


# ── Pipeline Execution ──────────────────────────────────────────────────


@dataclass
class FakeApprovalPolicy:
    id: str
    approved: bool = True
    approved_hash: str = ""


class TestTriggerRun:
    @pytest.mark.asyncio
    async def test_trigger_approved_policy(self) -> None:
        svc, _, store = _make_service()
        result = await svc.create_policy(_sample_policy_json())
        pid = result.policy["id"]
        # Approve the policy
        await svc.approve_policy(pid)
        # Update the guardrails policy lookup to know about this
        # The PipelineGuardrails._policies needs the approval data
        svc._guardrails._policies = FakePolicyLookup({
            pid: FakeApprovalPolicy(
                id=pid, approved=True,
                approved_hash=store._data[pid]["content_hash"],
            )
        })
        run_result = await svc.trigger_run(pid)
        assert run_result.run is not None
        assert run_result.error is None
        # F5: Assert runner was actually called
        svc._runner.run.assert_called_once()

    @pytest.mark.asyncio
    async def test_trigger_unapproved_blocks(self) -> None:
        svc, _, store = _make_service()
        result = await svc.create_policy(_sample_policy_json())
        pid = result.policy["id"]
        # Policy is not approved — guardrails should block
        svc._guardrails._policies = FakePolicyLookup({
            pid: FakeApprovalPolicy(id=pid, approved=False)
        })
        run_result = await svc.trigger_run(pid)
        assert run_result.error is not None
        assert "approval" in run_result.error.lower()

    @pytest.mark.asyncio
    async def test_trigger_nonexistent_policy(self) -> None:
        svc, _, _ = _make_service()
        run_result = await svc.trigger_run("nonexistent")
        assert run_result.error is not None


# ── Scheduler Status ───────────────────────────────────────────────────


class TestSchedulerStatus:
    def test_returns_status(self) -> None:
        svc, _, _ = _make_service()
        status = svc.get_scheduler_status()
        assert "running" in status
        assert "job_count" in status


# ── Patch Schedule Approval Reset ──────────────────────────────────────


class TestPatchSchedule:
    @pytest.mark.asyncio
    async def test_patch_schedule_resets_approval_on_hash_change(self) -> None:
        """F5: When patch_schedule changes content, approval must be reset."""
        svc, _, store = _make_service()
        # Create and approve a policy
        result = await svc.create_policy(_sample_policy_json())
        pid = result.policy["id"]
        await svc.approve_policy(pid)
        assert store._data[pid]["approved"] is True

        # Patch with a different cron — changes content hash
        patched = await svc.patch_schedule(
            policy_id=pid, cron_expression="30 12 * * *",
        )
        assert patched is not None
        assert patched["approved"] is False
        assert patched.get("approved_hash") is None
