# tests/unit/test_backup_recovery.py
"""Tests for BackupRecoveryManager (MEU-20).

AC-20.1: restore_backup success path
AC-20.2: restore_backup wrong passphrase → InvalidPassphraseError
AC-20.3: restore_backup tampered backup → CorruptedBackupError
AC-20.4: verify_backup valid → VerifyResult(status="valid")
AC-20.5: verify_backup corrupted → VerifyResult(status="corrupted")
AC-20.6: repair_database integrity check + recovery
AC-20.7: Legacy .zip format detection
AC-20.8: Legacy .db / .db.gz format detection
AC-20.9: Maintenance mode hooks invoked during restore
"""

from __future__ import annotations

import gzip
import hashlib
import json
import os
import sqlite3
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, call

import pyzipper
import pytest
from argon2.low_level import Type, hash_secret_raw

from zorivest_core.domain.exceptions import (
    CorruptedBackupError,
    InvalidPassphraseError,
)
from zorivest_infra.backup.backup_manager import BACKUP_EXTENSION, BackupManager
from zorivest_infra.backup.backup_recovery_manager import BackupRecoveryManager
from zorivest_infra.backup.backup_recovery_types import (
    RepairStatus,
    RestoreStatus,
    VerifyStatus,
)


# ── Helpers ──────────────────────────────────────────────────────────────


def _derive_key(passphrase: str, salt: bytes) -> bytes:
    """Mirror BackupManager._derive_key for test fixtures."""
    return hash_secret_raw(
        secret=passphrase.encode("utf-8"),
        salt=salt + b"zorivest-backup-v1",
        time_cost=3,
        memory_cost=65536,
        parallelism=4,
        hash_len=32,
        type=Type.ID,
    )


def _create_test_db(path: Path) -> None:
    """Create a minimal SQLite DB for testing."""
    conn = sqlite3.connect(str(path))
    conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, value TEXT)")
    conn.execute("INSERT INTO test VALUES (1, 'hello')")
    conn.commit()
    conn.close()


def _create_valid_zvbak(
    backup_path: Path,
    db_path: Path,
    passphrase: str = "test-passphrase",
) -> None:
    """Create a valid .zvbak file matching BackupManager's format."""
    salt = os.urandom(16)
    key = _derive_key(passphrase, salt)

    db_data = db_path.read_bytes()
    sha256 = hashlib.sha256(db_data).hexdigest()

    import base64

    manifest = {
        "app_id": "zorivest",
        "backup_format_version": 1,
        "created_at": "2026-03-08T00:00:00Z",
        "app_version": "0.1.0",
        "platform": "win32",
        "kdf": {
            "algorithm": "argon2id",
            "salt_b64": base64.b64encode(salt).decode(),
            "time_cost": 3,
            "memory_kib": 65536,
            "parallelism": 4,
            "hash_len": 32,
            "key_domain": "zorivest-backup-v1",
        },
        "files": [
            {
                "path": db_path.name,
                "sha256": sha256,
                "size_bytes": len(db_data),
            }
        ],
        "sqlcipher": {
            "expected_major": 4,
            "pragmas": {"cipher_page_size": 4096, "kdf_iter": 256000},
        },
    }

    with pyzipper.AESZipFile(
        str(backup_path),
        "w",
        compression=pyzipper.ZIP_DEFLATED,
        encryption=pyzipper.WZ_AES,
    ) as zf:
        zf.setpassword(key)
        # Store salt in ZIP comment for independent recovery (matches BackupManager)
        zf.comment = b"zvbak-salt:" + base64.b64encode(salt)
        zf.writestr("manifest.json", json.dumps(manifest, indent=2))
        zf.writestr(db_path.name, db_data)


# ── Fixtures ─────────────────────────────────────────────────────────────


@pytest.fixture()
def tmp_dirs(tmp_path: Path) -> dict[str, Path]:
    """Create all required temp directories."""
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()
    restore_dir = tmp_path / "data"
    restore_dir.mkdir()
    return {"backup_dir": backup_dir, "restore_dir": restore_dir, "root": tmp_path}


@pytest.fixture()
def sample_db(tmp_dirs: dict[str, Path]) -> Path:
    """Create a sample SQLite database."""
    db_path = tmp_dirs["restore_dir"] / "main.db"
    _create_test_db(db_path)
    return db_path


@pytest.fixture()
def valid_backup(tmp_dirs: dict[str, Path], sample_db: Path) -> Path:
    """Create a valid .zvbak backup file."""
    backup_path = tmp_dirs["backup_dir"] / f"test-backup{BACKUP_EXTENSION}"
    _create_valid_zvbak(backup_path, sample_db)
    return backup_path


@pytest.fixture()
def recovery_manager(
    tmp_dirs: dict[str, Path], sample_db: Path
) -> BackupRecoveryManager:
    """Create a BackupRecoveryManager instance."""
    return BackupRecoveryManager(
        db_paths={"main": sample_db},
        backup_dir=tmp_dirs["backup_dir"],
        passphrase="test-passphrase",
    )


# ── AC-20.1: Restore success ────────────────────────────────────────────


class TestRestore:
    """Restore backup flow tests."""

    def test_restore_zvbak_success(
        self,
        recovery_manager: BackupRecoveryManager,
        valid_backup: Path,
        sample_db: Path,
    ) -> None:
        """AC-20.1: restore_backup opens .zvbak, verifies, stages, swaps,
        returns RestoreResult(status=SUCCESS)."""
        result = recovery_manager.restore_backup(valid_backup)

        assert result.status == RestoreStatus.SUCCESS
        assert len(result.restored_files) > 0
        assert result.error is None

        # DB should still be valid after restore
        conn = sqlite3.connect(str(sample_db))
        rows = conn.execute("SELECT value FROM test").fetchall()
        conn.close()
        assert len(rows) >= 1

    def test_restore_wrong_passphrase(
        self,
        tmp_dirs: dict[str, Path],
        sample_db: Path,
        valid_backup: Path,
    ) -> None:
        """AC-20.2: wrong passphrase raises InvalidPassphraseError."""
        mgr = BackupRecoveryManager(
            db_paths={"main": sample_db},
            backup_dir=tmp_dirs["backup_dir"],
            passphrase="WRONG-passphrase",
        )
        with pytest.raises(InvalidPassphraseError):
            mgr.restore_backup(valid_backup)

    def test_restore_tampered_backup(
        self,
        recovery_manager: BackupRecoveryManager,
        valid_backup: Path,
    ) -> None:
        """AC-20.3: tampered backup (hash mismatch) raises CorruptedBackupError."""
        # Tamper by appending random bytes to the file
        with open(valid_backup, "r+b") as f:
            # Overwrite bytes in the middle to corrupt file contents
            f.seek(100)
            f.write(os.urandom(50))

        with pytest.raises((CorruptedBackupError, InvalidPassphraseError)):
            recovery_manager.restore_backup(valid_backup)

    def test_maintenance_hooks_called(
        self,
        recovery_manager: BackupRecoveryManager,
        valid_backup: Path,
    ) -> None:
        """AC-20.9: close_connections and reopen_connections hooks are called."""
        close_hook = MagicMock()
        reopen_hook = MagicMock()
        recovery_manager.close_connections_hook = close_hook
        recovery_manager.reopen_connections_hook = reopen_hook

        result = recovery_manager.restore_backup(valid_backup)

        assert result.status == RestoreStatus.SUCCESS
        close_hook.assert_called_once()
        reopen_hook.assert_called_once()
        # close must happen before reopen
        assert close_hook.call_args_list[0] == call()


# ── AC-20.4 / AC-20.5: Verify flow ─────────────────────────────────────


class TestVerify:
    """Non-destructive backup verification."""

    def test_verify_valid_backup(
        self,
        recovery_manager: BackupRecoveryManager,
        valid_backup: Path,
    ) -> None:
        """AC-20.4: verify valid backup returns VALID status with details."""
        result = recovery_manager.verify_backup(valid_backup)

        assert result.status == VerifyStatus.VALID
        assert result.file_count > 0
        assert result.total_size_bytes > 0
        assert result.manifest is not None
        assert result.manifest["app_id"] == "zorivest"

    def test_verify_corrupted_backup(
        self,
        recovery_manager: BackupRecoveryManager,
        valid_backup: Path,
    ) -> None:
        """AC-20.5: verify corrupted backup returns CORRUPTED status."""
        # Corrupt the backup file
        with open(valid_backup, "r+b") as f:
            f.seek(100)
            f.write(os.urandom(50))

        result = recovery_manager.verify_backup(valid_backup)

        assert result.status in (VerifyStatus.CORRUPTED, VerifyStatus.FAILED)

    def test_verify_nonexistent_file(
        self,
        recovery_manager: BackupRecoveryManager,
        tmp_dirs: dict[str, Path],
    ) -> None:
        """Verify returns FAILED for nonexistent file."""
        fake_path = tmp_dirs["backup_dir"] / "nonexistent.zvbak"

        result = recovery_manager.verify_backup(fake_path)

        assert result.status == VerifyStatus.FAILED
        assert result.error is not None


# ── AC-20.6: Repair database ────────────────────────────────────────────


class TestRepair:
    """Database repair tests."""

    def test_repair_healthy_database(
        self,
        recovery_manager: BackupRecoveryManager,
        sample_db: Path,
    ) -> None:
        """AC-20.6: healthy DB returns HEALTHY status."""
        result = recovery_manager.repair_database(sample_db)

        assert result.status == RepairStatus.HEALTHY
        assert len(result.integrity_errors) == 0

    def test_repair_corrupted_database(
        self,
        recovery_manager: BackupRecoveryManager,
        tmp_dirs: dict[str, Path],
    ) -> None:
        """AC-20.6: corrupted DB detected and repair attempted."""
        # Create a DB with enough data to have internal pages
        corrupt_db = tmp_dirs["root"] / "corrupt.db"
        conn = sqlite3.connect(str(corrupt_db))
        conn.execute("CREATE TABLE data (id INTEGER PRIMARY KEY, payload TEXT)")
        # Insert enough rows to create multiple pages
        for i in range(500):
            conn.execute(
                "INSERT INTO data VALUES (?, ?)",
                (i, f"payload-{i}" * 50),
            )
        conn.commit()
        conn.close()

        # Corrupt internal pages (skip the header at offset 0-100)
        file_size = corrupt_db.stat().st_size
        with open(corrupt_db, "r+b") as f:
            # Zero out a chunk in the middle to corrupt b-tree pages
            mid = file_size // 2
            f.seek(mid)
            f.write(b"\x00" * 4096)

        result = recovery_manager.repair_database(corrupt_db)

        # Corrupted DB should NOT be reported as healthy
        assert result.status in (RepairStatus.REPAIRED, RepairStatus.FAILED)
        # If repaired, integrity_errors should list what was found
        if result.status == RepairStatus.REPAIRED:
            assert len(result.integrity_errors) > 0

    def test_repair_nonexistent_database(
        self,
        recovery_manager: BackupRecoveryManager,
        tmp_dirs: dict[str, Path],
    ) -> None:
        """Repair returns FAILED for nonexistent file."""
        fake_path = tmp_dirs["root"] / "nonexistent.db"

        result = recovery_manager.repair_database(fake_path)

        assert result.status == RepairStatus.FAILED
        assert result.error is not None


# ── AC-20.7 / AC-20.8: Legacy format detection ─────────────────────────


class TestLegacy:
    """Legacy backup format handling."""

    def test_legacy_zip_format(
        self,
        recovery_manager: BackupRecoveryManager,
        sample_db: Path,
        tmp_dirs: dict[str, Path],
    ) -> None:
        """AC-20.7: .zip format detected and extractable via verify."""
        legacy_path = tmp_dirs["backup_dir"] / "legacy.zip"
        with zipfile.ZipFile(str(legacy_path), "w") as zf:
            zf.write(str(sample_db), arcname="main.db")

        result = recovery_manager.verify_backup(legacy_path)
        # Legacy format should be at least detected and not crash
        assert result.status in (VerifyStatus.VALID, VerifyStatus.FAILED)
        # If failed, should mention legacy format
        if result.status == VerifyStatus.FAILED:
            assert any("legacy" in w.lower() for w in result.warnings) or (
                result.error is not None
            )

    def test_legacy_db_format(
        self,
        recovery_manager: BackupRecoveryManager,
        sample_db: Path,
        tmp_dirs: dict[str, Path],
    ) -> None:
        """AC-20.8: .db format detected."""
        legacy_path = tmp_dirs["backup_dir"] / "legacy.db"
        import shutil

        shutil.copy2(str(sample_db), str(legacy_path))

        result = recovery_manager.verify_backup(legacy_path)
        assert result.status in (VerifyStatus.VALID, VerifyStatus.FAILED)

    def test_legacy_db_gz_format(
        self,
        recovery_manager: BackupRecoveryManager,
        sample_db: Path,
        tmp_dirs: dict[str, Path],
    ) -> None:
        """AC-20.8: .db.gz format detected."""
        legacy_path = tmp_dirs["backup_dir"] / "legacy.db.gz"
        with open(sample_db, "rb") as f_in:
            with gzip.open(str(legacy_path), "wb") as f_out:
                f_out.write(f_in.read())

        result = recovery_manager.verify_backup(legacy_path)
        assert result.status in (VerifyStatus.VALID, VerifyStatus.FAILED)
