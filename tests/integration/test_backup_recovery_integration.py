# tests/integration/test_backup_recovery_integration.py
"""Integration tests for BackupManager + BackupRecoveryManager full cycle.

Tests the end-to-end flow: BackupManager creates a backup,
BackupRecoveryManager restores/verifies it.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from zorivest_core.domain.exceptions import InvalidPassphraseError
from zorivest_infra.backup.backup_manager import BackupManager
from zorivest_infra.backup.backup_recovery_manager import BackupRecoveryManager
from zorivest_infra.backup.backup_recovery_types import (
    RestoreStatus,
    VerifyStatus,
)
from zorivest_infra.backup.backup_types import BackupStatus


PASSPHRASE = "integration-test-passphrase-2026"


@pytest.fixture()
def db_dir(tmp_path: Path) -> Path:
    """Create a directory with a sample SQLite database."""
    db_path = tmp_path / "data" / "main.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))
    conn.execute("CREATE TABLE accounts (id TEXT PRIMARY KEY, name TEXT, balance REAL)")
    conn.execute(
        "INSERT INTO accounts VALUES ('acc-1', 'Savings', 12345.67)"
    )
    conn.execute(
        "INSERT INTO accounts VALUES ('acc-2', 'Checking', 9876.54)"
    )
    conn.commit()
    conn.close()

    return tmp_path


@pytest.fixture()
def db_paths(db_dir: Path) -> dict[str, Path]:
    """Return the db_paths dict for managers."""
    return {"main": db_dir / "data" / "main.db"}


@pytest.fixture()
def backup_dir(db_dir: Path) -> Path:
    """Return the backup directory."""
    bdir = db_dir / "backups"
    bdir.mkdir(parents=True, exist_ok=True)
    return bdir


@pytest.fixture()
def backup_manager(
    db_paths: dict[str, Path], backup_dir: Path
) -> BackupManager:
    """Create a BackupManager."""
    return BackupManager(
        db_paths=db_paths,
        backup_dir=backup_dir,
        passphrase=PASSPHRASE,
    )


@pytest.fixture()
def recovery_manager(
    db_paths: dict[str, Path], backup_dir: Path
) -> BackupRecoveryManager:
    """Create a BackupRecoveryManager with the same passphrase."""
    return BackupRecoveryManager(
        db_paths=db_paths,
        backup_dir=backup_dir,
        passphrase=PASSPHRASE,
    )


@pytest.fixture()
def created_backup(
    backup_manager: BackupManager,
) -> Path:
    """Create a backup and return its path."""
    result = backup_manager.create_backup()
    assert result.status == BackupStatus.SUCCESS
    assert result.backup_path is not None
    return result.backup_path


class TestFullCycle:
    """End-to-end backup → verify → restore cycle."""

    def test_create_and_verify(
        self,
        recovery_manager: BackupRecoveryManager,
        created_backup: Path,
    ) -> None:
        """BackupManager creates backup, RecoveryManager verifies it."""
        result = recovery_manager.verify_backup(created_backup)

        assert result.status == VerifyStatus.VALID
        assert result.file_count is not None
        assert result.file_count >= 1
        assert result.total_size_bytes is not None
        assert result.total_size_bytes > 0
        assert result.manifest is not None

    def test_create_and_restore(
        self,
        recovery_manager: BackupRecoveryManager,
        created_backup: Path,
        db_paths: dict[str, Path],
    ) -> None:
        """BackupManager creates backup, RecoveryManager restores it.

        Verifies data integrity by reading the DB after restore.
        """
        # Modify the DB before restore to prove restore reverts changes
        conn = sqlite3.connect(str(db_paths["main"]))
        conn.execute("DELETE FROM accounts")
        conn.execute("INSERT INTO accounts VALUES ('new', 'Modified', 0.0)")
        conn.commit()
        conn.close()

        # Verify the DB was modified
        conn = sqlite3.connect(str(db_paths["main"]))
        count = conn.execute("SELECT COUNT(*) FROM accounts").fetchone()[0]
        conn.close()
        assert count == 1  # Only the new row

        # Restore from backup
        result = recovery_manager.restore_backup(created_backup)
        assert result.status == RestoreStatus.SUCCESS
        assert len(result.restored_files) >= 1
        assert result.error is None

        # Verify original data was restored
        conn = sqlite3.connect(str(db_paths["main"]))
        rows = conn.execute(
            "SELECT id, name, balance FROM accounts ORDER BY id"
        ).fetchall()
        conn.close()

        assert len(rows) == 2
        assert rows[0] == ("acc-1", "Savings", 12345.67)
        assert rows[1] == ("acc-2", "Checking", 9876.54)

    def test_wrong_passphrase_fails(
        self,
        db_paths: dict[str, Path],
        backup_dir: Path,
        created_backup: Path,
    ) -> None:
        """Restore with wrong passphrase raises InvalidPassphraseError."""
        wrong_mgr = BackupRecoveryManager(
            db_paths=db_paths,
            backup_dir=backup_dir,
            passphrase="WRONG-passphrase-completely",
        )
        with pytest.raises(InvalidPassphraseError):
            wrong_mgr.restore_backup(created_backup)

    def test_maintenance_hooks_called(
        self,
        db_paths: dict[str, Path],
        backup_dir: Path,
        created_backup: Path,
    ) -> None:
        """Maintenance mode hooks (close/reopen) are called during restore."""
        call_log: list[str] = []

        mgr = BackupRecoveryManager(
            db_paths=db_paths,
            backup_dir=backup_dir,
            passphrase=PASSPHRASE,
        )
        mgr.close_connections_hook = lambda: call_log.append("close")
        mgr.reopen_connections_hook = lambda: call_log.append("reopen")

        result = mgr.restore_backup(created_backup)
        assert result.status == RestoreStatus.SUCCESS
        assert "close" in call_log
        assert "reopen" in call_log
        # reopen must come after close
        assert call_log.index("close") < call_log.index("reopen")

    def test_verify_then_restore_roundtrip(
        self,
        recovery_manager: BackupRecoveryManager,
        created_backup: Path,
        db_paths: dict[str, Path],
    ) -> None:
        """Full roundtrip: verify (non-destructive) → restore → verify DB."""
        # Step 1: Verify — should not change anything
        verify_result = recovery_manager.verify_backup(created_backup)
        assert verify_result.status == VerifyStatus.VALID

        # Step 2: Corrupt the DB
        conn = sqlite3.connect(str(db_paths["main"]))
        conn.execute("DROP TABLE accounts")
        conn.commit()
        conn.close()

        # Step 3: Restore
        restore_result = recovery_manager.restore_backup(created_backup)
        assert restore_result.status == RestoreStatus.SUCCESS

        # Step 4: Verify DB is intact
        conn = sqlite3.connect(str(db_paths["main"]))
        rows = conn.execute("SELECT COUNT(*) FROM accounts").fetchone()
        conn.close()
        assert rows[0] == 2
