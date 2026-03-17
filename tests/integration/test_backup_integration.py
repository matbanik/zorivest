# tests/integration/test_backup_integration.py
"""Integration test: full backup cycle (AC-19.11).

Creates a real SQLite DB → seeds data → runs BackupManager.create_backup() →
verifies backup file, manifest, encrypted ZIP contents, and GFS rotation.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path

import pyzipper
import pytest

from zorivest_infra.backup.backup_manager import BACKUP_EXTENSION, BackupManager
from zorivest_infra.backup.backup_types import BackupStatus


@pytest.fixture
def real_db(tmp_path: Path) -> Path:
    """Create a realistic SQLite database with multiple tables and data."""
    db_path = tmp_path / "zorivest_settings.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("CREATE TABLE settings (key TEXT PRIMARY KEY, value TEXT, updated_at TEXT)")
    conn.execute("INSERT INTO settings VALUES ('ui.theme', 'dark', '2026-01-01')")
    conn.execute("INSERT INTO settings VALUES ('data.sync_interval_minutes', '15', '2026-01-01')")
    conn.execute("CREATE TABLE app_defaults (key TEXT PRIMARY KEY, value TEXT, category TEXT)")
    conn.execute("INSERT INTO app_defaults VALUES ('ui.theme', 'dark', 'ui')")
    conn.commit()
    conn.close()
    return db_path


@pytest.fixture
def backup_dir(tmp_path: Path) -> Path:
    d = tmp_path / "backups"
    d.mkdir()
    return d


class TestFullBackupCycle:
    """AC-19.11: Full backup cycle: snapshot → package → rotate → verify."""

    def test_full_backup_cycle(self, real_db: Path, backup_dir: Path) -> None:
        """End-to-end: create DB → seed → backup → verify contents match."""
        import base64

        passphrase = "integration-test-passphrase-2026"
        mgr = BackupManager(
            db_paths={"settings": real_db},
            backup_dir=backup_dir,
            passphrase=passphrase,
        )

        # Step 1: Create backup
        result = mgr.create_backup()
        assert result.status == BackupStatus.SUCCESS
        assert result.backup_path is not None
        assert result.backup_path.exists()
        assert result.backup_path.suffix == BACKUP_EXTENSION
        assert result.files_backed_up == 1
        assert result.elapsed_seconds > 0

        # Step 2: Verify manifest structure
        manifest = result.manifest
        assert manifest is not None
        assert manifest.app_id == "zorivest"
        assert manifest.backup_format_version == 1
        assert manifest.kdf.algorithm == "argon2id"
        assert manifest.kdf.key_domain == "zorivest-backup-v1"
        assert len(manifest.files) == 1

        # Step 3: Verify encrypted ZIP can be opened with correct key
        salt = base64.b64decode(manifest.kdf.salt_b64)
        key = mgr._derive_key(salt)

        with pyzipper.AESZipFile(str(result.backup_path), "r") as zf:
            zf.setpassword(key)

            # Manifest is in the ZIP
            assert "manifest.json" in zf.namelist()
            manifest_data = json.loads(zf.read("manifest.json").decode())
            assert manifest_data["app_id"] == "zorivest"

            # Snapshot file is in the ZIP
            for fe in manifest_data["files"]:
                assert fe["path"] in zf.namelist()

                # SHA-256 hash matches
                file_data = zf.read(fe["path"])
                actual_hash = hashlib.sha256(file_data).hexdigest()
                assert actual_hash == fe["sha256"], f"Hash mismatch for {fe['path']}"

                # Snapshot is a valid SQLite DB with original data
                snap_path = backup_dir / "verify_snap.db"
                snap_path.write_bytes(file_data)
                conn = sqlite3.connect(str(snap_path))
                rows = conn.execute("SELECT key, value FROM settings ORDER BY key").fetchall()
                conn.close()
                snap_path.unlink()
                assert ("data.sync_interval_minutes", "15") in rows
                assert ("ui.theme", "dark") in rows

        # Step 4: Verify snapshots were cleaned up
        snapshots = list(backup_dir.glob("*.snapshot.db"))
        assert len(snapshots) == 0

        # Step 5: Verify backup appears in list
        backups = mgr.list_backups()
        assert len(backups) == 1
        assert backups[0] == result.backup_path

    def test_wrong_passphrase_cannot_read(self, real_db: Path, backup_dir: Path) -> None:
        """Backup created with one passphrase cannot be read with another."""
        mgr = BackupManager(
            db_paths={"settings": real_db},
            backup_dir=backup_dir,
            passphrase="correct-passphrase",
        )
        result = mgr.create_backup()
        assert result.status == BackupStatus.SUCCESS

        # Try reading with wrong-passphrase-derived key
        wrong_mgr = BackupManager(
            db_paths={}, backup_dir=backup_dir, passphrase="wrong-passphrase"
        )
        import base64
        salt = base64.b64decode(result.manifest.kdf.salt_b64)
        wrong_key = wrong_mgr._derive_key(salt)

        with pyzipper.AESZipFile(str(result.backup_path), "r") as zf:
            zf.setpassword(wrong_key)
            with pytest.raises(Exception):
                zf.read("manifest.json")
        # Value: verify the derived keys are actually different
        correct_key = mgr._derive_key(salt)
        assert wrong_key != correct_key
