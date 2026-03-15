# pyright: reportArgumentType=false, reportReturnType=false, reportAttributeAccessIssue=false
# SQLAlchemy Column/Session types need suppression for Column[T] → T assignments.

"""Scheduling repository implementations (§9.2j).

Source: 09-scheduling.md §9.2j
Provides 5 concrete repositories for scheduling infrastructure.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from zorivest_infra.database.models import (
    AuditLogModel,
    FetchCacheModel,
    PipelineRunModel,
    PolicyModel,
    ReportModel,
    ReportVersionModel,
)


class PolicyRepository:
    """CRUD operations for pipeline policies."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(
        self,
        *,
        id: str | None = None,
        name: str,
        schema_version: int,
        policy_json: str,
        content_hash: str,
        created_by: str = "",
        enabled: bool = True,
    ) -> str:
        pid = id or str(uuid.uuid4())
        model = PolicyModel(
            id=pid,
            name=name,
            schema_version=schema_version,
            policy_json=policy_json,
            content_hash=content_hash,
            enabled=enabled,
            created_at=datetime.now(timezone.utc),
            created_by=created_by,
        )
        self._session.add(model)
        self._session.flush()
        return pid

    def get_by_id(self, policy_id: str) -> PolicyModel | None:
        return self._session.get(PolicyModel, policy_id)

    def get_by_name(self, name: str) -> PolicyModel | None:
        return (
            self._session.query(PolicyModel)
            .filter_by(name=name)
            .first()
        )

    def list_all(
        self, *, enabled_only: bool = False, limit: int = 100
    ) -> list[PolicyModel]:
        q = self._session.query(PolicyModel)
        if enabled_only:
            q = q.filter(PolicyModel.enabled.is_(True))
        return q.order_by(PolicyModel.created_at.desc()).limit(limit).all()

    def update(self, policy_id: str, **fields) -> None:
        model = self.get_by_id(policy_id)
        if model is None:
            raise ValueError(f"Policy not found: {policy_id}")
        for key, val in fields.items():
            setattr(model, key, val)
        model.updated_at = datetime.now(timezone.utc)

    def delete(self, policy_id: str) -> None:
        model = self.get_by_id(policy_id)
        if model is not None:
            self._session.delete(model)


class PipelineRunRepository:
    """CRUD and query operations for pipeline runs."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(
        self,
        *,
        id: str | None = None,
        policy_id: str,
        status: str = "pending",
        trigger_type: str,
        content_hash: str,
        dry_run: bool = False,
        created_by: str = "",
        started_at: datetime | None = None,
    ) -> str:
        rid = id or str(uuid.uuid4())
        model = PipelineRunModel(
            id=rid,
            policy_id=policy_id,
            status=status,
            trigger_type=trigger_type,
            content_hash=content_hash,
            dry_run=dry_run,
            created_by=created_by,
            started_at=started_at or datetime.now(timezone.utc),
        )
        self._session.add(model)
        self._session.flush()
        return rid

    def get_by_id(self, run_id: str) -> PipelineRunModel | None:
        return self._session.get(PipelineRunModel, run_id)

    def list_by_policy(
        self, policy_id: str, *, limit: int = 50
    ) -> list[PipelineRunModel]:
        return (
            self._session.query(PipelineRunModel)
            .filter_by(policy_id=policy_id)
            .order_by(PipelineRunModel.started_at.desc())
            .limit(limit)
            .all()
        )

    def update_status(
        self, run_id: str, *, status: str, error: str | None = None,
        duration_ms: int | None = None,
    ) -> None:
        model = self.get_by_id(run_id)
        if model is None:
            raise ValueError(f"Run not found: {run_id}")
        model.status = status
        if error is not None:
            model.error = error
        if duration_ms is not None:
            model.duration_ms = duration_ms
        model.completed_at = datetime.now(timezone.utc)

    def find_zombies(self) -> list[PipelineRunModel]:
        """Find runs in 'running' status (potential zombies after crash)."""
        return (
            self._session.query(PipelineRunModel)
            .filter(PipelineRunModel.status == "running")
            .all()
        )

    def list_recent(self, *, limit: int = 20) -> list[PipelineRunModel]:
        """Return the most recent pipeline runs across all policies."""
        return (
            self._session.query(PipelineRunModel)
            .order_by(PipelineRunModel.started_at.desc())
            .limit(limit)
            .all()
        )


class ReportRepository:
    """CRUD operations for reports and their versions/deliveries."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(
        self,
        *,
        id: str | None = None,
        name: str,
        version: int = 1,
        spec_json: str,
        format: str = "pdf",
        created_by: str = "",
    ) -> str:
        rid = id or str(uuid.uuid4())
        model = ReportModel(
            id=rid,
            name=name,
            version=version,
            spec_json=spec_json,
            format=format,
            created_at=datetime.now(timezone.utc),
            created_by=created_by,
        )
        self._session.add(model)
        self._session.flush()
        return rid

    def get_by_id(self, report_id: str) -> ReportModel | None:
        return self._session.get(ReportModel, report_id)

    def get_versions(self, report_id: str) -> list[ReportVersionModel]:
        return (
            self._session.query(ReportVersionModel)
            .filter_by(report_id=report_id)
            .order_by(ReportVersionModel.version.desc())
            .all()
        )


class FetchCacheRepository:
    """Cache management for HTTP fetch responses."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_cached(
        self, provider: str, data_type: str, entity_key: str
    ) -> FetchCacheModel | None:
        return (
            self._session.query(FetchCacheModel)
            .filter_by(provider=provider, data_type=data_type, entity_key=entity_key)
            .first()
        )

    def upsert(
        self,
        provider: str,
        data_type: str,
        entity_key: str,
        payload_json: str,
        content_hash: str,
        ttl_seconds: int,
        etag: str | None = None,
        last_modified: str | None = None,
    ) -> None:
        existing = self.get_cached(provider, data_type, entity_key)
        if existing is not None:
            existing.payload_json = payload_json
            existing.content_hash = content_hash
            existing.ttl_seconds = ttl_seconds
            existing.etag = etag
            existing.last_modified = last_modified
            existing.fetched_at = datetime.now(timezone.utc)
        else:
            model = FetchCacheModel(
                id=str(uuid.uuid4()),
                provider=provider,
                data_type=data_type,
                entity_key=entity_key,
                payload_json=payload_json,
                content_hash=content_hash,
                ttl_seconds=ttl_seconds,
                etag=etag,
                last_modified=last_modified,
                fetched_at=datetime.now(timezone.utc),
            )
            self._session.add(model)

    def invalidate(
        self, provider: str, data_type: str | None = None
    ) -> int:
        """Remove cached entries. Returns count deleted."""
        q = self._session.query(FetchCacheModel).filter_by(provider=provider)
        if data_type is not None:
            q = q.filter_by(data_type=data_type)
        count = q.count()
        q.delete(synchronize_session="fetch")
        return count


class AuditLogRepository:
    """Append-only audit log writer."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def append(
        self,
        *,
        actor: str,
        action: str,
        resource_type: str,
        resource_id: str,
        details: dict | None = None,
    ) -> None:
        model = AuditLogModel(
            actor=actor,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details_json=json.dumps(details) if details else None,
            created_at=datetime.now(timezone.utc),
        )
        self._session.add(model)

    def list_recent(self, limit: int = 50) -> list[AuditLogModel]:
        return (
            self._session.query(AuditLogModel)
            .order_by(AuditLogModel.id.desc())
            .limit(limit)
            .all()
        )
