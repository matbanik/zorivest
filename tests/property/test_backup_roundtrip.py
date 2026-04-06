"""Property-based tests for backup/restore round-trip fidelity.

Invariant: backup → restore produces a database with identical content.

Source: 02a-backup-restore.md §2A.3–2A.4
Phase:  3.1 of Test Rigor Audit
"""

from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from zorivest_core.domain.exceptions import InvalidPassphraseError
from zorivest_infra.backup.backup_manager import BackupManager
from zorivest_infra.backup.backup_recovery_manager import BackupRecoveryManager
from zorivest_infra.backup.backup_types import BackupStatus


# ── Helpers ─────────────────────────────────────────────────────────────


def _create_test_db(path: Path, rows: list[tuple[str, str]]) -> None:
    """Create a SQLite DB with a key-value table and insert rows."""
    conn = sqlite3.connect(str(path))
    conn.execute("CREATE TABLE kv (key TEXT PRIMARY KEY, value TEXT)")
    conn.executemany("INSERT INTO kv VALUES (?, ?)", rows)
    conn.commit()
    conn.close()


def _read_all_rows(path: Path) -> list[tuple[str, str]]:
    """Read all rows from the kv table."""
    conn = sqlite3.connect(str(path))
    rows = conn.execute("SELECT key, value FROM kv ORDER BY key").fetchall()
    conn.close()
    return rows


# ── Strategies ──────────────────────────────────────────────────────────

# Key-value pairs for the test database
kv_pairs = st.lists(
    st.tuples(
        st.text(
            alphabet=st.sampled_from("abcdefghijklmnopqrstuvwxyz0123456789"),
            min_size=1,
            max_size=20,
        ),
        st.text(min_size=0, max_size=100),
    ),
    min_size=1,
    max_size=30,
    unique_by=lambda t: t[0],  # Unique keys
)


# ── Invariants ──────────────────────────────────────────────────────────


class TestBackupRestoreRoundtrip:
    """Backup → restore must preserve all database content."""

    @given(rows=kv_pairs)
    @settings(max_examples=20, deadline=15000)
    def test_roundtrip_preserves_data(self, rows: list[tuple[str, str]]) -> None:
        """Data written → backup → restore → identical data read back."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            db_path = tmp / "test.db"
            backup_dir = tmp / "backups"
            backup_dir.mkdir()

            # Write data
            _create_test_db(db_path, rows)
            original_rows = _read_all_rows(db_path)

            # Backup
            db_paths = {"main": db_path}
            mgr = BackupManager(
                db_paths=db_paths,
                backup_dir=backup_dir,
                passphrase="test-passphrase-42",
            )
            result = mgr.create_backup()
            assert result.status == BackupStatus.SUCCESS
            assert result.backup_path is not None
            assert result.backup_path.exists()

            # Delete original to confirm restore works from backup alone
            db_path.unlink()

            # Restore — same db_paths so files swap into place
            recovery = BackupRecoveryManager(
                db_paths=db_paths,
                backup_dir=backup_dir,
                passphrase="test-passphrase-42",
            )
            restore_result = recovery.restore_backup(result.backup_path)
            from zorivest_infra.backup.backup_recovery_types import RestoreStatus

            assert restore_result.status == RestoreStatus.SUCCESS

            # Verify data integrity
            assert db_path.exists()
            restored_rows = _read_all_rows(db_path)
            assert restored_rows == original_rows

    @given(rows=kv_pairs)
    @settings(max_examples=10, deadline=15000)
    def test_wrong_passphrase_fails(self, rows: list[tuple[str, str]]) -> None:
        """Restore with wrong passphrase must raise InvalidPassphraseError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            db_path = tmp / "test.db"
            backup_dir = tmp / "backups"
            backup_dir.mkdir()

            _create_test_db(db_path, rows)

            db_paths = {"main": db_path}
            mgr = BackupManager(
                db_paths=db_paths,
                backup_dir=backup_dir,
                passphrase="correct-passphrase",
            )
            result = mgr.create_backup()
            assert result.status == BackupStatus.SUCCESS
            assert result.backup_path is not None

            recovery = BackupRecoveryManager(
                db_paths=db_paths,
                backup_dir=backup_dir,
                passphrase="wrong-passphrase",
            )
            with pytest.raises(InvalidPassphraseError):
                recovery.restore_backup(result.backup_path)


class TestBackupManifest:
    """Backup manifest must list all expected database files."""

    @given(
        db_count=st.integers(min_value=1, max_value=3),
        rows=kv_pairs,
    )
    @settings(max_examples=10, deadline=15000)
    def test_manifest_lists_all_dbs(
        self, db_count: int, rows: list[tuple[str, str]]
    ) -> None:
        """Manifest file_count equals number of input databases."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            backup_dir = tmp / "backups"
            backup_dir.mkdir()

            db_paths = {}
            for i in range(db_count):
                db_path = tmp / f"db_{i}.db"
                _create_test_db(db_path, [(f"k{i}", f"v{i}")])
                db_paths[f"db_{i}"] = db_path

            mgr = BackupManager(
                db_paths=db_paths,
                backup_dir=backup_dir,
                passphrase="test-pass",
            )
            result = mgr.create_backup()
            assert result.status == BackupStatus.SUCCESS
            assert result.manifest is not None
            assert len(result.manifest.files) == db_count


class TestGFSRotation:
    """GFS rotation must never delete the latest backup."""

    def test_latest_survives_rotation(self) -> None:
        """Create 15 backups (more than GFS limits), verify latest exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            db_path = tmp / "test.db"
            backup_dir = tmp / "backups"
            backup_dir.mkdir()

            _create_test_db(db_path, [("k", "v")])

            mgr = BackupManager(
                db_paths={"main": db_path},
                backup_dir=backup_dir,
                passphrase="test-pass",
            )

            latest_path = None
            for _ in range(15):
                result = mgr.create_backup()
                assert result.status == BackupStatus.SUCCESS
                latest_path = result.backup_path

            # Latest must still exist
            assert latest_path is not None
            assert latest_path.exists()

            # All remaining backups must be present
            backups = mgr.list_backups()
            assert len(backups) > 0
            assert latest_path in backups
