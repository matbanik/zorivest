# packages/infrastructure/src/zorivest_infra/backup/backup_recovery_types.py
"""Result types for BackupRecoveryManager operations.

Source: 02a-backup-restore.md §2A.4
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class RestoreStatus(Enum):
    """Status of a restore operation."""

    SUCCESS = "success"
    FAILED = "failed"


class VerifyStatus(Enum):
    """Status of a backup verification."""

    VALID = "valid"
    CORRUPTED = "corrupted"
    FAILED = "failed"


class RepairStatus(Enum):
    """Status of a database repair operation."""

    HEALTHY = "healthy"
    REPAIRED = "repaired"
    FAILED = "failed"


@dataclass(frozen=True)
class RestoreResult:
    """Result of a restore_backup() operation."""

    status: RestoreStatus
    restored_files: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    error: str | None = None


@dataclass(frozen=True)
class VerifyResult:
    """Result of a verify_backup() operation."""

    status: VerifyStatus
    file_count: int = 0
    total_size_bytes: int = 0
    manifest: dict[str, Any] | None = None
    warnings: list[str] = field(default_factory=list)
    error: str | None = None


@dataclass(frozen=True)
class RepairResult:
    """Result of a repair_database() operation."""

    status: RepairStatus
    integrity_errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    error: str | None = None
