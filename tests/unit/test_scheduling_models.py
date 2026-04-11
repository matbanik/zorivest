"""Tests for Phase 9 scheduling SQLAlchemy models (MEU-81).

Covers:
- Table creation for all 9 models (AC-1, AC-2)
- Policy model columns and constraints (AC-3)
- FK relationships and back_populates (AC-4, AC-5, AC-9)
- Unique constraints (AC-6, AC-7, AC-10)
- AuditLog integer PK (AC-8)
- Report versioning trigger (AC-11)
- Audit append-only triggers (AC-12)
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, event, inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from zorivest_infra.database.models import (
    AuditLogModel,
    Base,
    FetchCacheModel,
    PipelineRunModel,
    PipelineStateModel,
    PipelineStepModel,
    PolicyModel,
    ReportDeliveryModel,
    ReportModel,
    ReportVersionModel,
)


@pytest.fixture()
def engine():
    """In-memory SQLite engine with FK enforcement and scheduling triggers."""
    eng = create_engine("sqlite:///:memory:")

    # Enable FK enforcement (SQLite requires this per-connection)
    @event.listens_for(eng, "connect")
    def _set_sqlite_pragma(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(eng)
    return eng


@pytest.fixture()
def session(engine):
    """Scoped session for each test."""
    with Session(engine) as s:
        yield s


def _uid() -> str:
    return str(uuid.uuid4())


# ── AC-1: All 9 model classes exist and inherit Base ──────────────────────


class TestTableCreation:
    """AC-1 + AC-2: 9 new models create valid tables."""

    EXPECTED_TABLES = {
        "policies",
        "pipeline_runs",
        "pipeline_steps",
        "pipeline_state",
        "reports",
        "report_versions",
        "report_delivery",
        "fetch_cache",
        "audit_log",
    }

    def test_all_scheduling_tables_exist(self, engine):
        inspector = inspect(engine)
        tables = set(inspector.get_table_names())
        for expected in self.EXPECTED_TABLES:
            assert expected in tables, f"Missing table: {expected}"

    def test_models_inherit_from_base(self):
        model_classes = [
            PolicyModel,
            PipelineRunModel,
            PipelineStepModel,
            PipelineStateModel,
            ReportModel,
            ReportVersionModel,
            ReportDeliveryModel,
            FetchCacheModel,
            AuditLogModel,
        ]
        for cls in model_classes:
            assert issubclass(cls, Base), f"{cls.__name__} must inherit from Base"
            # Value: verify each model has __tablename__
            assert hasattr(cls, "__tablename__"), (
                f"{cls.__name__} missing __tablename__"
            )
            assert isinstance(cls.__tablename__, str)
        assert len(model_classes) == 9


# ── AC-3: PolicyModel columns ─────────────────────────────────────────────


class TestPolicyModel:
    """AC-3: PolicyModel has required columns."""

    def test_policy_crud(self, session):
        pid = _uid()
        now = datetime.now(timezone.utc)
        policy = PolicyModel(
            id=pid,
            name="test-policy",
            schema_version=1,
            policy_json='{"steps": []}',
            content_hash="abc123",
            enabled=True,
            approved=False,
            created_at=now,
            created_by="test",
        )
        session.add(policy)
        session.commit()

        loaded = session.get(PolicyModel, pid)
        assert loaded is not None
        assert loaded.name == "test-policy"
        assert loaded.policy_json == '{"steps": []}'
        assert loaded.content_hash == "abc123"
        assert loaded.approved is False
        assert loaded.approved_hash is None
        assert loaded.approved_at is None

    def test_policy_name_unique(self, session):
        now = datetime.now(timezone.utc)
        p1 = PolicyModel(
            id=_uid(),
            name="dup-name",
            schema_version=1,
            policy_json="{}",
            content_hash="a",
            created_at=now,
        )
        p2 = PolicyModel(
            id=_uid(),
            name="dup-name",
            schema_version=1,
            policy_json="{}",
            content_hash="b",
            created_at=now,
        )
        session.add(p1)
        session.commit()
        session.add(p2)
        with pytest.raises(IntegrityError):
            session.commit()


# ── AC-4, AC-5: FK relationships ─────────────────────────────────────────


class TestRelationships:
    """AC-4 + AC-5: Bidirectional relationships between run↔policy, step↔run."""

    def _create_policy(self, session) -> PolicyModel:
        pid = _uid()
        policy = PolicyModel(
            id=pid,
            name=f"policy-{pid[:8]}",
            schema_version=1,
            policy_json="{}",
            content_hash="hash",
            created_at=datetime.now(timezone.utc),
        )
        session.add(policy)
        session.flush()
        return policy

    def test_run_policy_relationship(self, session):
        policy = self._create_policy(session)
        run = PipelineRunModel(
            id=_uid(),
            policy_id=policy.id,
            status="pending",
            trigger_type="manual",
            content_hash="h1",
        )
        session.add(run)
        session.commit()

        assert run.policy is policy
        assert run in policy.runs
        # Value: verify FK and status values persisted correctly
        assert run.policy_id == policy.id  # type: ignore[reportGeneralTypeIssues]
        assert run.status == "pending"  # type: ignore[reportGeneralTypeIssues]
        assert run.trigger_type == "manual"  # type: ignore[reportGeneralTypeIssues]

    def test_step_run_relationship(self, session):
        policy = self._create_policy(session)
        run = PipelineRunModel(
            id=_uid(),
            policy_id=policy.id,
            status="running",
            trigger_type="scheduled",
            content_hash="h2",
        )
        session.add(run)
        session.flush()

        step = PipelineStepModel(
            id=_uid(),
            run_id=run.id,
            step_id="fetch_data",
            step_type="fetch",
            status="pending",
        )
        session.add(step)
        session.commit()

        assert step.run is run
        assert step in run.steps
        # Value: verify step fields persisted correctly
        assert step.step_id == "fetch_data"  # type: ignore[reportGeneralTypeIssues]
        assert step.step_type == "fetch"  # type: ignore[reportGeneralTypeIssues]
        assert step.status == "pending"  # type: ignore[reportGeneralTypeIssues]
        assert step.run_id == run.id  # type: ignore[reportGeneralTypeIssues]

    def test_run_fk_constraint(self, session):
        """FK to non-existent policy should fail."""
        run = PipelineRunModel(
            id=_uid(),
            policy_id="nonexistent",
            status="pending",
            trigger_type="manual",
            content_hash="h",
        )
        session.add(run)
        with pytest.raises(IntegrityError):
            session.commit()


# ── AC-6: PipelineStateModel UniqueConstraint ─────────────────────────────


class TestPipelineStateModel:
    """AC-6: 4-column UniqueConstraint on pipeline_state."""

    def _create_policy(self, session) -> str:
        pid = _uid()
        session.add(
            PolicyModel(
                id=pid,
                name=f"pol-{pid[:8]}",
                schema_version=1,
                policy_json="{}",
                content_hash="h",
                created_at=datetime.now(timezone.utc),
            )
        )
        session.flush()
        return pid

    def test_unique_constraint(self, session):
        now = datetime.now(timezone.utc)
        pid = self._create_policy(session)
        common = dict(
            policy_id=pid,
            provider_id="ibkr",
            data_type="quotes",
            entity_key="AAPL",
            updated_at=now,
        )
        s1 = PipelineStateModel(id=_uid(), **common)
        s2 = PipelineStateModel(id=_uid(), **common)
        session.add(s1)
        session.commit()
        session.add(s2)
        with pytest.raises(IntegrityError):
            session.commit()
        # Value: verify the first state was actually saved
        session.rollback()
        saved = session.get(PipelineStateModel, s1.id)
        assert saved is not None
        assert saved.entity_key == "AAPL"

    def test_different_keys_allowed(self, session):
        now = datetime.now(timezone.utc)
        pid = self._create_policy(session)
        s1 = PipelineStateModel(
            id=_uid(),
            policy_id=pid,
            provider_id="ibkr",
            data_type="quotes",
            entity_key="AAPL",
            updated_at=now,
        )
        s2 = PipelineStateModel(
            id=_uid(),
            policy_id=pid,
            provider_id="ibkr",
            data_type="quotes",
            entity_key="MSFT",
            updated_at=now,
        )
        session.add_all([s1, s2])
        session.commit()  # Should not raise
        # Value: verify both states persisted with distinct entity_keys
        assert s1.entity_key == "AAPL"  # type: ignore[reportGeneralTypeIssues]
        assert s2.entity_key == "MSFT"  # type: ignore[reportGeneralTypeIssues]
        assert s1.id != s2.id  # type: ignore[reportGeneralTypeIssues]
        loaded_s1 = session.get(PipelineStateModel, s1.id)
        loaded_s2 = session.get(PipelineStateModel, s2.id)
        assert loaded_s1 is not None
        assert loaded_s2 is not None


# ── AC-7: FetchCacheModel UniqueConstraint ────────────────────────────────


class TestFetchCacheModel:
    """AC-7: 3-column UniqueConstraint on fetch_cache."""

    def test_unique_constraint(self, session):
        now = datetime.now(timezone.utc)
        common = dict(
            provider="ibkr",
            data_type="quotes",
            entity_key="AAPL",
            payload_json="{}",
            content_hash="h",
            fetched_at=now,
            ttl_seconds=3600,
        )
        c1 = FetchCacheModel(id=_uid(), **common)
        c2 = FetchCacheModel(id=_uid(), **common)
        session.add(c1)
        session.commit()
        session.add(c2)
        with pytest.raises(IntegrityError):
            session.commit()


# ── AC-8: AuditLogModel Integer PK ────────────────────────────────────────


class TestAuditLogModel:
    """AC-8: AuditLogModel uses Integer autoincrement PK."""

    def test_autoincrement_pk(self, session):
        now = datetime.now(timezone.utc)
        a1 = AuditLogModel(
            actor="scheduler",
            action="pipeline.run",
            resource_type="pipeline_run",
            resource_id=_uid(),
            created_at=now,
        )
        session.add(a1)
        session.commit()
        assert isinstance(a1.id, int)
        assert a1.id >= 1  # type: ignore[reportGeneralTypeIssues]


# ── AC-9, AC-10: Report cascade + dedup_key ──────────────────────────────


class TestReportModels:
    """AC-9 + AC-10: Report cascade relationships and dedup_key unique."""

    def _create_report(self, session) -> ReportModel:
        report = ReportModel(
            id=_uid(),
            name="Daily P&L",
            version=1,
            spec_json='{"query": "SELECT ..."}',
            format="pdf",
            created_at=datetime.now(timezone.utc),
        )
        session.add(report)
        session.flush()
        return report

    def test_report_version_relationship(self, session):
        report = self._create_report(session)
        version = ReportVersionModel(
            id=_uid(),
            report_id=report.id,
            version=1,
            spec_json='{"old": true}',
            created_at=datetime.now(timezone.utc),
        )
        session.add(version)
        session.commit()
        assert version in report.versions
        # Value: verify version fields
        assert version.report_id == report.id  # type: ignore[reportGeneralTypeIssues]
        assert version.version == 1  # type: ignore[reportGeneralTypeIssues]
        assert version.spec_json == '{"old": true}'  # type: ignore[reportGeneralTypeIssues]

    def test_report_delivery_relationship(self, session):
        report = self._create_report(session)
        delivery = ReportDeliveryModel(
            id=_uid(),
            report_id=report.id,
            channel="email",
            recipient="user@example.com",
            status="pending",
            dedup_key=_uid(),
        )
        session.add(delivery)
        session.commit()
        assert delivery in report.deliveries
        # Value: verify delivery fields
        assert delivery.report_id == report.id  # type: ignore[reportGeneralTypeIssues]
        assert delivery.channel == "email"  # type: ignore[reportGeneralTypeIssues]
        assert delivery.recipient == "user@example.com"  # type: ignore[reportGeneralTypeIssues]
        assert delivery.status == "pending"  # type: ignore[reportGeneralTypeIssues]

    def test_dedup_key_unique(self, session):
        report = self._create_report(session)
        dk = _uid()
        d1 = ReportDeliveryModel(
            id=_uid(),
            report_id=report.id,
            channel="email",
            recipient="a@b.com",
            dedup_key=dk,
        )
        d2 = ReportDeliveryModel(
            id=_uid(),
            report_id=report.id,
            channel="email",
            recipient="c@d.com",
            dedup_key=dk,
        )
        session.add(d1)
        session.commit()
        session.add(d2)
        with pytest.raises(IntegrityError):
            session.commit()
        # Value: verify the first delivery was actually saved
        session.rollback()
        saved = session.get(ReportDeliveryModel, d1.id)
        assert saved is not None
        assert saved.dedup_key == dk

    def test_cascade_delete(self, session):
        report = self._create_report(session)
        version = ReportVersionModel(
            id=_uid(),
            report_id=report.id,
            version=1,
            spec_json="{}",
            created_at=datetime.now(timezone.utc),
        )
        delivery = ReportDeliveryModel(
            id=_uid(),
            report_id=report.id,
            channel="local_file",
            recipient="/tmp/report.pdf",
            dedup_key=_uid(),
        )
        session.add_all([version, delivery])
        session.commit()

        session.delete(report)
        session.commit()

        # Cascade should have removed children
        assert session.get(ReportVersionModel, version.id) is None
        assert session.get(ReportDeliveryModel, delivery.id) is None


# ── AC-11: Report versioning trigger ──────────────────────────────────────


class TestReportVersioningTrigger:
    """AC-11: UPDATE on reports → prior row inserted into report_versions."""

    def test_report_versioning_trigger(self, session):
        report = ReportModel(
            id=_uid(),
            name="Weekly Summary",
            version=1,
            spec_json='{"v1": true}',
            snapshot_json='{"data": 1}',
            snapshot_hash="hash1",
            format="html",
            created_at=datetime.now(timezone.utc),
        )
        session.add(report)
        session.commit()

        # Verify no versions yet
        versions = (
            session.query(ReportVersionModel).filter_by(report_id=report.id).all()
        )
        assert len(versions) == 0

        # Update the report → trigger should fire
        report.version = 2  # type: ignore[reportAttributeAccessIssue]
        report.spec_json = '{"v2": true}'  # type: ignore[reportAttributeAccessIssue]
        report.snapshot_json = '{"data": 2}'  # type: ignore[reportAttributeAccessIssue]
        report.snapshot_hash = "hash2"  # type: ignore[reportAttributeAccessIssue]
        session.commit()

        # Trigger should have inserted old version
        versions = (
            session.query(ReportVersionModel).filter_by(report_id=report.id).all()
        )
        assert len(versions) == 1
        v = versions[0]
        assert v.version == 1
        assert v.spec_json == '{"v1": true}'
        assert v.snapshot_json == '{"data": 1}'
        assert v.snapshot_hash == "hash1"


# ── AC-12: Audit append-only triggers ─────────────────────────────────────


class TestAuditAppendOnlyTriggers:
    """AC-12: UPDATE and DELETE on audit_log raise ABORT errors."""

    def test_audit_no_update_trigger(self, session):
        now = datetime.now(timezone.utc)
        entry = AuditLogModel(
            actor="test",
            action="policy.create",
            resource_type="policy",
            resource_id=_uid(),
            created_at=now,
        )
        session.add(entry)
        session.commit()

        entry.action = "policy.delete"  # type: ignore[reportAttributeAccessIssue]
        with pytest.raises(IntegrityError, match="append-only.*UPDATE"):
            session.commit()

    def test_audit_no_delete_trigger(self, session):
        now = datetime.now(timezone.utc)
        entry = AuditLogModel(
            actor="test",
            action="pipeline.run",
            resource_type="pipeline_run",
            resource_id=_uid(),
            created_at=now,
        )
        session.add(entry)
        session.commit()

        session.delete(entry)
        with pytest.raises(IntegrityError, match="append-only.*DELETE"):
            session.commit()
