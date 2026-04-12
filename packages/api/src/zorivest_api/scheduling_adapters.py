# packages/api/src/zorivest_api/scheduling_adapters.py
"""Scheduling adapters — bridge SchedulingService's async dict protocols
to synchronous ORM repositories via SqlAlchemyUnitOfWork.

MEU-90a: These adapters translate between the async dict-based APIs
expected by SchedulingService and the sync ORM repository methods
provided by SqlAlchemyUnitOfWork.  The UoW is pre-entered in the
lifespan with reentrant depth tracking, so adapters access repos
directly via the shared session.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from zorivest_infra.database.models import AuditLogModel, PipelineStepModel
from zorivest_infra.database.unit_of_work import SqlAlchemyUnitOfWork


def _model_to_dict(model: Any) -> dict[str, Any]:
    """Generic ORM model → dict serializer."""
    return {c.name: getattr(model, c.name) for c in model.__table__.columns}


def _policy_model_to_dict(model: Any) -> dict[str, Any]:
    """Policy model → dict with policy_json deserialized.

    SchedulingService expects policy_json as a Python dict,
    but the DB stores it as a JSON string.
    """
    d = _model_to_dict(model)
    if "policy_json" in d and isinstance(d["policy_json"], str):
        try:
            d["policy_json"] = json.loads(d["policy_json"])
        except (json.JSONDecodeError, TypeError):
            pass
    return d


# ── PolicyStoreAdapter ───────────────────────────────────────────────────


class PolicyStoreAdapter:
    """Wraps PolicyRepository → PolicyStore protocol (async, dict-based).

    Data-shape translations handled here:
    - ``create()``/``update()`` filter dict keys to match repo signatures
    - ``policy_json``: dict → JSON string on write, JSON string → dict on read
    """

    _CREATE_KEYS = frozenset(
        {
            "id",
            "name",
            "schema_version",
            "policy_json",
            "content_hash",
            "created_by",
            "enabled",
        }
    )
    _UPDATE_KEYS = frozenset(
        {
            "name",
            "schema_version",
            "policy_json",
            "content_hash",
            "enabled",
            "approved",
            "approved_hash",
            "approved_at",
        }
    )

    def __init__(self, uow: SqlAlchemyUnitOfWork) -> None:
        self._uow = uow

    async def create(self, data: dict[str, Any]) -> dict[str, Any]:
        filtered = {k: v for k, v in data.items() if k in self._CREATE_KEYS}
        # SchedulingService passes policy_json as a dict; repo expects JSON string
        if "policy_json" in filtered and isinstance(filtered["policy_json"], dict):
            filtered["policy_json"] = json.dumps(filtered["policy_json"])
        policy_id = self._uow.policies.create(**filtered)
        self._uow.commit()
        model = self._uow.policies.get_by_id(policy_id)
        return _policy_model_to_dict(model) if model else {"id": policy_id}

    async def get_by_id(self, policy_id: str) -> dict[str, Any] | None:
        model = self._uow.policies.get_by_id(policy_id)
        return _policy_model_to_dict(model) if model else None

    async def list_all(self, enabled_only: bool = False) -> list[dict[str, Any]]:
        models = self._uow.policies.list_all(enabled_only=enabled_only)
        return [_policy_model_to_dict(m) for m in models]

    async def update(
        self, policy_id: str, data: dict[str, Any]
    ) -> dict[str, Any] | None:
        filtered = {k: v for k, v in data.items() if k in self._UPDATE_KEYS}
        # SchedulingService passes policy_json as a dict; repo expects JSON string
        if "policy_json" in filtered and isinstance(filtered["policy_json"], dict):
            filtered["policy_json"] = json.dumps(filtered["policy_json"])
        self._uow.policies.update(policy_id, **filtered)
        self._uow.commit()
        model = self._uow.policies.get_by_id(policy_id)
        return _policy_model_to_dict(model) if model else None

    async def delete(self, policy_id: str) -> None:
        self._uow.policies.delete(policy_id)
        self._uow.commit()


# ── RunStoreAdapter ──────────────────────────────────────────────────────


def _run_model_to_dict(model: Any) -> dict[str, Any]:
    """PipelineRun ORM → dict with id remapped to run_id.

    The ORM column is 'id' but the service/route layer uses 'run_id'.
    """
    d = _model_to_dict(model)
    if "id" in d:
        d["run_id"] = d.pop("id")
    return d


class RunStoreAdapter:
    """Wraps PipelineRunRepository → RunStore protocol (async, dict-based).

    Method translations:
    - list_for_policy() → list_by_policy() (renamed)
    - update(run_id, data) → update_status(run_id, *, status, error, duration_ms) (shape split)
    - id → run_id (key remapped in all outputs)
    """

    _CREATE_KEYS = frozenset(
        {
            "id",
            "policy_id",
            "status",
            "trigger_type",
            "content_hash",
            "dry_run",
            "created_by",
            "started_at",
        }
    )

    def __init__(self, uow: SqlAlchemyUnitOfWork) -> None:
        self._uow = uow

    async def create(self, data: dict[str, Any]) -> dict[str, Any]:
        # Translate service-layer keys → repo-layer keys
        mapped = dict(data)
        if "run_id" in mapped:
            mapped["id"] = mapped.pop("run_id")
        filtered = {k: v for k, v in mapped.items() if k in self._CREATE_KEYS}
        run_id = self._uow.pipeline_runs.create(**filtered)
        self._uow.commit()
        model = self._uow.pipeline_runs.get_by_id(run_id)
        return _run_model_to_dict(model) if model else {"run_id": run_id}

    async def get_by_id(self, run_id: str) -> dict[str, Any] | None:
        model = self._uow.pipeline_runs.get_by_id(run_id)
        return _run_model_to_dict(model) if model else None

    async def list_for_policy(
        self, policy_id: str, limit: int = 20
    ) -> list[dict[str, Any]]:
        # Method renamed: list_for_policy → list_by_policy
        models = self._uow.pipeline_runs.list_by_policy(policy_id, limit=limit)
        return [_run_model_to_dict(m) for m in models]

    async def list_recent(self, limit: int = 20) -> list[dict[str, Any]]:
        models = self._uow.pipeline_runs.list_recent(limit=limit)
        return [_run_model_to_dict(m) for m in models]

    async def update(self, run_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
        # Shape split: extract status/error/duration_ms from dict
        self._uow.pipeline_runs.update_status(
            run_id,
            status=data.get("status", "completed"),
            error=data.get("error"),
            duration_ms=data.get("duration_ms"),
        )
        self._uow.commit()
        model = self._uow.pipeline_runs.get_by_id(run_id)
        return _run_model_to_dict(model) if model else None


# ── AuditCounterAdapter ─────────────────────────────────────────────────


class AuditCounterAdapter:
    """Wraps AuditLogRepository → AuditLogger + AuditCounter dual protocol.

    Method translations:
    - log() → append() (renamed, adds actor="system")
    - count_actions_since() → new query (no direct repo method)
    """

    def __init__(self, uow: SqlAlchemyUnitOfWork) -> None:
        self._uow = uow

    async def log(
        self,
        action: str,
        resource_type: str,
        resource_id: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        self._uow.audit_log.append(
            actor="system",
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
        )
        self._uow.commit()

    async def count_actions_since(self, action: str, since: datetime) -> int:
        return (
            self._uow._session.query(AuditLogModel)  # noqa: SLF001  # pyright: ignore[reportOptionalMemberAccess]
            .filter(
                AuditLogModel.action == action,
                AuditLogModel.created_at >= since,
            )
            .count()
        )


# ── StepStoreAdapter ────────────────────────────────────────────────────


class StepStoreAdapter:
    """Wraps PipelineStepModel queries → StepStore protocol."""

    def __init__(self, uow: SqlAlchemyUnitOfWork) -> None:
        self._uow = uow

    async def list_for_run(self, run_id: str) -> list[dict[str, Any]]:
        models = (
            self._uow._session.query(PipelineStepModel)  # noqa: SLF001  # pyright: ignore[reportOptionalMemberAccess]
            .filter_by(run_id=run_id)
            .all()
        )
        return [_model_to_dict(m) for m in models]
