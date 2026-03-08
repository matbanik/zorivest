# packages/infrastructure/src/zorivest_infra/backup/backup_types.py
"""Backup data types: BackupManifest, BackupResult, GFS policy constants.

Source: 02a-backup-restore.md §2A.3
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class BackupStatus(Enum):
    """Status of a backup operation."""

    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"


@dataclass
class FileEntry:
    """A single file in the backup manifest."""

    path: str
    sha256: str
    size_bytes: int


@dataclass
class KDFParams:
    """Key derivation parameters for backup container encryption."""

    algorithm: str = "argon2id"
    salt_b64: str = ""
    time_cost: int = 3
    memory_kib: int = 65536
    parallelism: int = 4
    hash_len: int = 32
    key_domain: str = "zorivest-backup-v1"

    def to_dict(self) -> dict[str, Any]:
        return {
            "algorithm": self.algorithm,
            "salt_b64": self.salt_b64,
            "time_cost": self.time_cost,
            "memory_kib": self.memory_kib,
            "parallelism": self.parallelism,
            "hash_len": self.hash_len,
            "key_domain": self.key_domain,
        }


@dataclass
class SQLCipherMeta:
    """SQLCipher compatibility metadata for the manifest."""

    expected_major: int = 4
    cipher_page_size: int = 4096
    kdf_iter: int = 256000

    def to_dict(self) -> dict[str, Any]:
        return {
            "expected_major": self.expected_major,
            "pragmas": {
                "cipher_page_size": self.cipher_page_size,
                "kdf_iter": self.kdf_iter,
            },
        }


@dataclass
class BackupManifest:
    """Manifest stored inside the encrypted backup ZIP.

    Source: 02a-backup-restore.md §2A.3 L504-539
    """

    app_id: str = "zorivest"
    backup_format_version: int = 1
    created_at: str = ""
    app_version: str = "0.1.0"
    platform: str = ""
    kdf: KDFParams = field(default_factory=KDFParams)
    files: list[FileEntry] = field(default_factory=list)
    sqlcipher: SQLCipherMeta = field(default_factory=SQLCipherMeta)

    def to_dict(self) -> dict[str, Any]:
        return {
            "app_id": self.app_id,
            "backup_format_version": self.backup_format_version,
            "created_at": self.created_at,
            "app_version": self.app_version,
            "platform": self.platform,
            "kdf": self.kdf.to_dict(),
            "files": [
                {"path": f.path, "sha256": f.sha256, "size_bytes": f.size_bytes}
                for f in self.files
            ],
            "sqlcipher": self.sqlcipher.to_dict(),
        }


@dataclass
class BackupResult:
    """Result of a backup operation."""

    status: BackupStatus
    backup_path: Path | None = None
    manifest: BackupManifest | None = None
    error: str | None = None
    files_backed_up: int = 0
    elapsed_seconds: float = 0.0
    rotated_files: list[Path] = field(default_factory=list)


# ── GFS Rotation Policy Constants ────────────────────────────────────────

GFS_DAILY_KEEP = 5
GFS_WEEKLY_KEEP = 4
GFS_MONTHLY_KEEP = 3
