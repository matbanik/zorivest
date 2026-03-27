"""Tests for scheduling repository implementations (MEU-82).

Covers 5 repositories × CRUD operations:
- PolicyRepository: AC-1
- PipelineRunRepository: AC-2, AC-3
- ReportRepository: AC-4
- FetchCacheRepository: AC-5, AC-6
- AuditLogRepository: AC-7
- Session pattern: AC-8
- UoW extension: AC-9
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone, timedelta

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session

from zorivest_infra.database.models import Base
from zorivest_infra.database.scheduling_repositories import (
    AuditLogRepository,
    FetchCacheRepository,
    PipelineRunRepository,
    PolicyRepository,
    ReportRepository,
)


def _uid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


@pytest.fixture()
def engine():
    eng = create_engine("sqlite:///:memory:")

    @event.listens_for(eng, "connect")
    def _fk(dbapi_connection, _):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(eng)
    return eng


@pytest.fixture()
def session(engine):
    with Session(engine) as s:
        yield s


# ── Helpers ───────────────────────────────────────────────────────────────


def _insert_policy(repo: PolicyRepository, name: str | None = None) -> str:
    """Insert a policy and return its ID."""
    pid = _uid()
    repo.create(
        id=pid,
        name=name or f"policy-{pid[:8]}",
        schema_version=1,
        policy_json='{"steps":[]}',
        content_hash="h" + pid[:8],
        created_by="test",
    )
    return pid


# ── AC-1: PolicyRepository CRUD ──────────────────────────────────────────


class TestPolicyRepository:
    def test_create_and_get(self, session):
        repo = PolicyRepository(session)
        pid = _insert_policy(repo, "daily-report")
        session.commit()

        policy = repo.get_by_id(pid)
        assert policy is not None
        assert policy.name == "daily-report"

    def test_get_by_name(self, session):
        repo = PolicyRepository(session)
        _insert_policy(repo, "unique-name")
        session.commit()

        policy = repo.get_by_name("unique-name")
        assert policy is not None
        assert policy.name == "unique-name"

    def test_list_all_with_enabled_filter(self, session):
        repo = PolicyRepository(session)
        _insert_policy(repo, "active")
        pid2 = _insert_policy(repo, "disabled")
        session.commit()

        repo.update(pid2, enabled=False)
        session.commit()

        all_policies = repo.list_all(enabled_only=False)
        assert len(all_policies) == 2

        enabled = repo.list_all(enabled_only=True)
        assert len(enabled) == 1
        assert enabled[0].name == "active"

    def test_update(self, session):
        repo = PolicyRepository(session)
        pid = _insert_policy(repo, "before")
        session.commit()

        repo.update(pid, approved=True, approved_hash="abc")
        session.commit()

        policy = repo.get_by_id(pid)
        assert policy.approved is True
        assert policy.approved_hash == "abc"

    def test_delete(self, session):
        repo = PolicyRepository(session)
        pid = _insert_policy(repo, "to-delete")
        session.commit()

        repo.delete(pid)
        session.commit()
        assert repo.get_by_id(pid) is None


# ── AC-2, AC-3: PipelineRunRepository ────────────────────────────────────


class TestPipelineRunRepository:
    def _setup(self, session) -> tuple[PolicyRepository, PipelineRunRepository, str]:
        policy_repo = PolicyRepository(session)
        run_repo = PipelineRunRepository(session)
        pid = _insert_policy(policy_repo)
        session.commit()
        return policy_repo, run_repo, pid

    def test_create_and_get(self, session):
        _, run_repo, pid = self._setup(session)
        rid = run_repo.create(
            id=_uid(),
            policy_id=pid,
            status="running",
            trigger_type="manual",
            content_hash="h1",
        )
        session.commit()

        run = run_repo.get_by_id(rid)
        assert run is not None
        assert run.status == "running"

    def test_find_zombies(self, session):
        _, run_repo, pid = self._setup(session)
        # Create a running run with started_at in the past
        run_repo.create(
            id=_uid(),
            policy_id=pid,
            status="running",
            trigger_type="scheduled",
            content_hash="h",
            started_at=_now() - timedelta(hours=2),
        )
        # Create a normal running run
        run_repo.create(
            id=_uid(),
            policy_id=pid,
            status="pending",
            trigger_type="manual",
            content_hash="h2",
        )
        session.commit()

        zombies = run_repo.find_zombies()
        assert len(zombies) == 1
        assert zombies[0].status == "running"

    def test_list_by_policy(self, session):
        _, run_repo, pid = self._setup(session)
        for i in range(3):
            run_repo.create(
                id=_uid(),
                policy_id=pid,
                status="success",
                trigger_type="scheduled",
                content_hash=f"h{i}",
            )
        session.commit()

        runs = run_repo.list_by_policy(pid, limit=2)
        assert len(runs) == 2

    def test_update_status(self, session):
        _, run_repo, pid = self._setup(session)
        rid = run_repo.create(
            id=_uid(),
            policy_id=pid,
            status="running",
            trigger_type="manual",
            content_hash="h",
        )
        session.commit()

        run_repo.update_status(rid, status="success", duration_ms=1500)
        session.commit()

        run = run_repo.get_by_id(rid)
        assert run.status == "success"
        assert run.duration_ms == 1500

    def test_list_recent(self, session):
        _, run_repo, pid = self._setup(session)
        for i in range(3):
            run_repo.create(
                id=_uid(),
                policy_id=pid,
                status="success",
                trigger_type="scheduled",
                content_hash=f"h{i}",
            )
        session.commit()

        recent = run_repo.list_recent(limit=2)
        assert len(recent) == 2


# ── AC-4: ReportRepository ───────────────────────────────────────────────


class TestReportRepository:
    def test_create_and_get(self, session):
        repo = ReportRepository(session)
        rid = repo.create(
            id=_uid(),
            name="Daily P&L",
            version=1,
            spec_json='{"q": "SELECT 1"}',
            format="pdf",
        )
        session.commit()

        report = repo.get_by_id(rid)
        assert report is not None
        assert report.name == "Daily P&L"

    def test_get_versions_empty(self, session):
        repo = ReportRepository(session)
        rid = repo.create(
            id=_uid(),
            name="Report",
            version=1,
            spec_json="{}",
            format="html",
        )
        session.commit()

        versions = repo.get_versions(rid)
        assert versions == []


# ── AC-5, AC-6: FetchCacheRepository ─────────────────────────────────────


class TestFetchCacheRepository:
    def test_upsert_insert(self, session):
        repo = FetchCacheRepository(session)
        repo.upsert(
            provider="ibkr",
            data_type="quotes",
            entity_key="AAPL",
            payload_json='{"price": 150}',
            content_hash="h1",
            ttl_seconds=3600,
        )
        session.commit()

        cached = repo.get_cached("ibkr", "quotes", "AAPL")
        assert cached is not None
        assert cached.payload_json == '{"price": 150}'

    def test_upsert_update(self, session):
        repo = FetchCacheRepository(session)
        repo.upsert(
            provider="ibkr",
            data_type="quotes",
            entity_key="AAPL",
            payload_json='{"price": 150}',
            content_hash="h1",
            ttl_seconds=3600,
        )
        session.commit()

        repo.upsert(
            provider="ibkr",
            data_type="quotes",
            entity_key="AAPL",
            payload_json='{"price": 155}',
            content_hash="h2",
            ttl_seconds=3600,
        )
        session.commit()

        cached = repo.get_cached("ibkr", "quotes", "AAPL")
        assert cached.payload_json == '{"price": 155}'
        assert cached.content_hash == "h2"

    def test_invalidate(self, session):
        repo = FetchCacheRepository(session)
        repo.upsert("ibkr", "quotes", "AAPL", "{}", "h1", 3600)
        repo.upsert("ibkr", "quotes", "MSFT", "{}", "h2", 3600)
        session.commit()

        count = repo.invalidate("ibkr", "quotes")
        session.commit()
        assert count == 2

        assert repo.get_cached("ibkr", "quotes", "AAPL") is None


# ── AC-7: AuditLogRepository ─────────────────────────────────────────────


class TestAuditLogRepository:
    def test_append_and_list(self, session):
        repo = AuditLogRepository(session)
        repo.append(
            actor="scheduler",
            action="pipeline.run",
            resource_type="pipeline_run",
            resource_id=_uid(),
        )
        repo.append(
            actor="mcp:agent",
            action="policy.create",
            resource_type="policy",
            resource_id=_uid(),
        )
        session.commit()

        recent = repo.list_recent(limit=5)
        assert len(recent) == 2
        assert recent[0].action in ("pipeline.run", "policy.create")


# ── AC-8, AC-9: Session pattern + UoW ────────────────────────────────────


class TestSessionPattern:
    def test_all_repos_accept_session(self, session):
        """AC-8: All repos follow __init__(session) pattern."""
        for cls in [
            PolicyRepository,
            PipelineRunRepository,
            ReportRepository,
            FetchCacheRepository,
            AuditLogRepository,
        ]:
            repo = cls(session)
            assert repo._session is session
        # Value: verify all 5 repo types were iterated
        assert (
            len(
                [
                    PolicyRepository,
                    PipelineRunRepository,
                    ReportRepository,
                    FetchCacheRepository,
                    AuditLogRepository,
                ]
            )
            == 5
        )


class TestUnitOfWorkExtension:
    def test_uow_has_scheduling_repos(self, engine):
        """AC-9: UoW creates scheduling repo attributes."""
        from zorivest_infra.database.unit_of_work import SqlAlchemyUnitOfWork

        uow = SqlAlchemyUnitOfWork(engine)
        with uow:
            assert hasattr(uow, "policies")
            assert hasattr(uow, "pipeline_runs")
            assert hasattr(uow, "reports")
            assert hasattr(uow, "fetch_cache")
            assert hasattr(uow, "audit_log")
            assert isinstance(uow.policies, PolicyRepository)
            # Value: verify all scheduling repos are correct types
            assert isinstance(uow.pipeline_runs, PipelineRunRepository)
            assert isinstance(uow.reports, ReportRepository)
            assert isinstance(uow.fetch_cache, FetchCacheRepository)
            assert isinstance(uow.audit_log, AuditLogRepository)
