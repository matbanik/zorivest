# tests/integration/test_scheduling_adapters.py
"""Integration tests for scheduling adapters.

Covers AC-3 (scheduling adapters use repos from real UoW),
AC-7 (scheduler db_url), AC-11 (scheduling adapter round-trip).
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

import pytest

from zorivest_infra.database.unit_of_work import SqlAlchemyUnitOfWork


@pytest.fixture()
def uow(engine):
    """Entered UoW for adapter tests — repos are initialized."""
    _uow = SqlAlchemyUnitOfWork(engine)
    with _uow:
        yield _uow


def run_async(coro):
    """Helper to run async coroutines in sync test context."""
    return asyncio.get_event_loop().run_until_complete(coro)


class TestPolicyStoreAdapter:
    """AC-3 + AC-11: PolicyStoreAdapter wraps PolicyRepository."""

    def test_create_and_get(self, uow):
        from zorivest_api.scheduling_adapters import PolicyStoreAdapter

        adapter = PolicyStoreAdapter(uow)
        policy_data = {
            "name": "test-policy",
            "schema_version": 1,
            "policy_json": '{"steps": []}',
            "content_hash": "abc123",
            "enabled": True,
        }

        result = run_async(adapter.create(policy_data))
        assert isinstance(result, dict)
        assert "id" in result
        assert result["name"] == "test-policy"

        fetched = run_async(adapter.get_by_id(result["id"]))
        assert fetched is not None
        assert fetched["name"] == "test-policy"

    def test_list_all(self, uow):
        from zorivest_api.scheduling_adapters import PolicyStoreAdapter

        adapter = PolicyStoreAdapter(uow)
        run_async(
            adapter.create(
                {
                    "name": "list-test",
                    "schema_version": 1,
                    "policy_json": "{}",
                    "content_hash": "def456",
                }
            )
        )

        result = run_async(adapter.list_all())
        assert len(result) >= 1
        names = [p["name"] for p in result]
        assert "list-test" in names

    def test_update(self, uow):
        from zorivest_api.scheduling_adapters import PolicyStoreAdapter

        adapter = PolicyStoreAdapter(uow)
        created = run_async(
            adapter.create(
                {
                    "name": "update-me",
                    "schema_version": 1,
                    "policy_json": "{}",
                    "content_hash": "ghi789",
                }
            )
        )

        updated = run_async(adapter.update(created["id"], {"name": "updated-name"}))
        assert updated is not None
        assert updated["name"] == "updated-name"

    def test_delete(self, uow):
        from zorivest_api.scheduling_adapters import PolicyStoreAdapter

        adapter = PolicyStoreAdapter(uow)
        created = run_async(
            adapter.create(
                {
                    "name": "delete-me",
                    "schema_version": 1,
                    "policy_json": "{}",
                    "content_hash": "jkl012",
                }
            )
        )

        run_async(adapter.delete(created["id"]))
        assert run_async(adapter.get_by_id(created["id"])) is None


class TestRunStoreAdapter:
    """AC-3 + AC-11: RunStoreAdapter wraps PipelineRunRepository."""

    def test_create_and_get(self, uow):
        from zorivest_api.scheduling_adapters import (
            PolicyStoreAdapter,
            RunStoreAdapter,
        )

        # Need a policy first for the foreign key
        policy_adapter = PolicyStoreAdapter(uow)
        policy = run_async(
            policy_adapter.create(
                {
                    "name": "run-test-policy",
                    "schema_version": 1,
                    "policy_json": "{}",
                    "content_hash": "mno345",
                }
            )
        )

        adapter = RunStoreAdapter(uow)
        run_data = {
            "policy_id": policy["id"],
            "status": "pending",
            "trigger_type": "manual",
            "content_hash": "pqr678",
        }
        result = run_async(adapter.create(run_data))
        assert isinstance(result, dict)
        assert result["policy_id"] == policy["id"]

        fetched = run_async(adapter.get_by_id(result["run_id"]))
        assert fetched is not None
        assert fetched["status"] == "pending"

    def test_list_for_policy(self, uow):
        from zorivest_api.scheduling_adapters import (
            PolicyStoreAdapter,
            RunStoreAdapter,
        )

        policy_adapter = PolicyStoreAdapter(uow)
        policy = run_async(
            policy_adapter.create(
                {
                    "name": "list-run-policy",
                    "schema_version": 1,
                    "policy_json": "{}",
                    "content_hash": "stu901",
                }
            )
        )

        adapter = RunStoreAdapter(uow)
        run_async(
            adapter.create(
                {
                    "policy_id": policy["id"],
                    "trigger_type": "cron",
                    "content_hash": "vwx234",
                }
            )
        )

        runs = run_async(adapter.list_for_policy(policy["id"]))
        assert len(runs) >= 1
        assert runs[0]["policy_id"] == policy["id"]

    def test_update_status(self, uow):
        from zorivest_api.scheduling_adapters import (
            PolicyStoreAdapter,
            RunStoreAdapter,
        )

        policy_adapter = PolicyStoreAdapter(uow)
        policy = run_async(
            policy_adapter.create(
                {
                    "name": "update-run-policy",
                    "schema_version": 1,
                    "policy_json": "{}",
                    "content_hash": "yza567",
                }
            )
        )

        adapter = RunStoreAdapter(uow)
        created = run_async(
            adapter.create(
                {
                    "policy_id": policy["id"],
                    "trigger_type": "manual",
                    "content_hash": "bcd890",
                }
            )
        )

        updated = run_async(
            adapter.update(
                created["run_id"], {"status": "completed", "duration_ms": 1500}
            )
        )
        assert updated is not None
        assert updated["status"] == "completed"


class TestStepStoreAdapter:
    """AC-3 + AC-11: StepStoreAdapter wraps PipelineStepModel queries."""

    def test_list_for_run(self, uow):
        from zorivest_api.scheduling_adapters import (
            PolicyStoreAdapter,
            RunStoreAdapter,
            StepStoreAdapter,
        )

        # Create policy → run → steps
        policy_adapter = PolicyStoreAdapter(uow)
        policy = run_async(
            policy_adapter.create(
                {
                    "name": "step-test-policy",
                    "schema_version": 1,
                    "policy_json": "{}",
                    "content_hash": "efg123",
                }
            )
        )

        run_adapter = RunStoreAdapter(uow)
        pipeline_run = run_async(
            run_adapter.create(
                {
                    "policy_id": policy["id"],
                    "trigger_type": "manual",
                    "content_hash": "hij456",
                }
            )
        )

        # Insert step directly via UoW
        from zorivest_infra.database.models import PipelineStepModel

        step = PipelineStepModel(
            run_id=pipeline_run["run_id"],
            step_id="fetch-1",
            step_type="fetch",
            status="completed",
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            duration_ms=150,
        )
        uow._session.add(step)  # noqa: SLF001
        uow.commit()

        adapter = StepStoreAdapter(uow)
        steps = run_async(adapter.list_for_run(pipeline_run["run_id"]))
        assert len(steps) >= 1
        assert steps[0]["step_id"] == "fetch-1"
        assert steps[0]["step_type"] == "fetch"


class TestAuditCounterAdapter:
    """AC-3 + AC-11: AuditCounterAdapter wraps AuditLogRepository."""

    def test_log_and_list(self, uow):
        from zorivest_api.scheduling_adapters import AuditCounterAdapter

        adapter = AuditCounterAdapter(uow)
        run_async(
            adapter.log(
                action="policy.create",
                resource_type="policy",
                resource_id="pol-1",
                details={"name": "test"},
            )
        )

        # Verify via direct query
        entries = uow.audit_log.list_recent(limit=10)
        assert len(entries) >= 1
        # Verify field content, not just count
        found = any(
            getattr(e, "action", None) == "policy.create"
            and getattr(e, "resource_id", None) == "pol-1"
            for e in entries
        )
        assert found, (
            "Audit entry with action='policy.create' and resource_id='pol-1' not found"
        )

    def test_create_preserves_caller_id(self, uow):
        """Caller-supplied ID must survive the adapter's key filter."""
        from zorivest_api.scheduling_adapters import PolicyStoreAdapter

        adapter = PolicyStoreAdapter(uow)
        policy_data = {
            "id": "expected-id-test",
            "name": "id-preservation-test",
            "schema_version": 1,
            "policy_json": "{}",
            "content_hash": "idtest",
        }
        result = run_async(adapter.create(policy_data))
        assert result["id"] == "expected-id-test"

    def test_count_actions_since(self, uow):
        from zorivest_api.scheduling_adapters import AuditCounterAdapter

        adapter = AuditCounterAdapter(uow)
        before = datetime(2020, 1, 1, tzinfo=timezone.utc)

        run_async(
            adapter.log(
                action="test.count",
                resource_type="test",
                resource_id="t-1",
            )
        )
        run_async(
            adapter.log(
                action="test.count",
                resource_type="test",
                resource_id="t-2",
            )
        )

        count = run_async(adapter.count_actions_since("test.count", before))
        assert count >= 2
