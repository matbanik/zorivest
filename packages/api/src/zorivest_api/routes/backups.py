# packages/api/src/zorivest_api/routes/backups.py
"""Backup & Restore API routes.

Source: 06f-gui-settings.md §6f.5
MEU-74: REST endpoints for manual backup, list, verify, and restore.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from zorivest_api.dependencies import require_unlocked_db

backup_router = APIRouter(prefix="/api/v1/backups", tags=["backups"])


class BackupPathRequest(BaseModel):
    """Request body requiring a filesystem path to a backup file."""

    model_config = {"extra": "forbid"}

    path: str


class BackupEntryResponse(BaseModel):
    """Summary of a single backup file."""

    path: str
    filename: str
    size_bytes: int
    modified_at: str


class BackupResultResponse(BaseModel):
    """Result of a backup create operation."""

    status: str
    backup_path: str | None = None
    files_backed_up: int = 0
    elapsed_seconds: float = 0.0
    error: str | None = None


class VerifyResultResponse(BaseModel):
    """Result of a backup verification."""

    status: str
    error: str | None = None


class RestoreResultResponse(BaseModel):
    """Result of a backup restore operation."""

    status: str
    error: str | None = None


def _get_backup_manager(request: Request) -> Any:
    """Resolve BackupManager from app state."""
    mgr = getattr(request.app.state, "backup_manager", None)
    if mgr is None:
        raise HTTPException(
            503, "Backup manager not available (database may not be unlocked)"
        )
    return mgr


def _get_backup_recovery_manager(request: Request) -> Any:
    """Resolve BackupRecoveryManager from app state."""
    mgr = getattr(request.app.state, "backup_recovery_manager", None)
    if mgr is None:
        raise HTTPException(
            503,
            "Backup recovery manager not available (database may not be unlocked)",
        )
    return mgr


@backup_router.post("", dependencies=[Depends(require_unlocked_db)])
async def create_backup(
    request: Request,
) -> BackupResultResponse:
    """Create a manual backup of all databases.

    Triggers snapshot → encrypt → rotate → verify workflow.

    Source: MEU-74 (06f-gui-settings.md §6f.5)
    """
    mgr = _get_backup_manager(request)
    result = mgr.create_backup()
    return BackupResultResponse(
        status=result.status.value,
        backup_path=str(result.backup_path) if result.backup_path else None,
        files_backed_up=result.files_backed_up,
        elapsed_seconds=result.elapsed_seconds,
        error=result.error,
    )


@backup_router.get("", dependencies=[Depends(require_unlocked_db)])
async def list_backups(
    request: Request,
) -> list[BackupEntryResponse]:
    """List all backup files, newest first.

    Returns file metadata (path, size, modified timestamp).

    Source: MEU-74 (06f-gui-settings.md §6f.5)
    """
    mgr = _get_backup_manager(request)
    paths: list[Path] = mgr.list_backups()
    result: list[BackupEntryResponse] = []
    for p in paths:
        try:
            stat = p.stat()
            result.append(
                BackupEntryResponse(
                    path=str(p),
                    filename=p.name,
                    size_bytes=stat.st_size,
                    modified_at=datetime.fromtimestamp(
                        stat.st_mtime, tz=timezone.utc
                    ).isoformat(),
                )
            )
        except OSError:
            continue  # Skip files that disappear between list and stat
    return result


@backup_router.post("/verify", dependencies=[Depends(require_unlocked_db)])
async def verify_backup(
    body: BackupPathRequest,
    request: Request,
) -> VerifyResultResponse:
    """Non-destructive backup verification.

    Opens the backup, validates manifest, verifies file hashes.

    Source: MEU-74 (06f-gui-settings.md §6f.5)
    """
    mgr = _get_backup_recovery_manager(request)
    result = mgr.verify_backup(Path(body.path))
    return VerifyResultResponse(
        status=result.status.value,
        error=result.error,
    )


@backup_router.post("/restore", dependencies=[Depends(require_unlocked_db)])
async def restore_backup(
    body: BackupPathRequest,
    request: Request,
) -> RestoreResultResponse:
    """Restore from a backup file.

    Detect format → decrypt → verify manifest → stage → swap → migrate.

    Source: MEU-74 (06f-gui-settings.md §6f.5)
    """
    mgr = _get_backup_recovery_manager(request)
    result = mgr.restore_backup(Path(body.path))
    return RestoreResultResponse(
        status=result.status.value,
        error=result.error,
    )
