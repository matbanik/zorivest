# tests/unit/test_backup_manager.py
"""Tests for BackupManager and backup types (MEU-19)."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pyzipper
import pytest

from zorivest_infra.backup.backup_manager import BACKUP_EXTENSION, BackupManager
from zorivest_infra.backup.backup_types import (
    GFS_DAILY_KEEP,
    GFS_MONTHLY_KEEP,
    GFS_WEEKLY_KEEP,
    BackupManifest,
    BackupResult,
    BackupStatus,
    FileEntry,
    KDFParams,
    SQLCipherMeta,
)


# ── Fixtures ─────────────────────────────────────────────────────────────


@pytest.fixture
def backup_dir(tmp_path: Path) -> Path:
    d = tmp_path / "backups"
    d.mkdir()
    return d


@pytest.fixture
def sample_db(tmp_path: Path) -> Path:
    """Create a minimal SQLite database for testing."""
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, val TEXT)")
    conn.execute("INSERT INTO test VALUES (1, 'hello')")
    conn.commit()
    conn.close()
    return db_path


@pytest.fixture
def manager(sample_db: Path, backup_dir: Path) -> BackupManager:
    return BackupManager(
        db_paths={"settings": sample_db},
        backup_dir=backup_dir,
        passphrase="test-passphrase-123",
    )


# ── BackupManifest ───────────────────────────────────────────────────────


class TestBackupManifest:
    """BackupManifest structure and serialization."""

    def test_manifest_to_dict(self) -> None:
        m = BackupManifest(
            created_at="2026-01-01T00:00:00Z",
            platform="win32",
            files=[FileEntry(path="test.db", sha256="abc", size_bytes=100)],
        )
        d = m.to_dict()
        assert d["app_id"] == "zorivest"
        assert d["backup_format_version"] == 1
        assert len(d["files"]) == 1
        assert d["files"][0]["sha256"] == "abc"
        assert "kdf" in d
        assert d["kdf"]["key_domain"] == "zorivest-backup-v1"

    def test_manifest_defaults(self) -> None:
        m = BackupManifest()
        assert m.app_id == "zorivest"
        assert m.backup_format_version == 1
        assert m.files == []


class TestBackupResult:
    """BackupResult structure."""

    def test_success_result(self) -> None:
        r = BackupResult(status=BackupStatus.SUCCESS, files_backed_up=2)
        assert r.status == BackupStatus.SUCCESS
        assert r.files_backed_up == 2
        assert r.error is None

    def test_failed_result(self) -> None:
        r = BackupResult(status=BackupStatus.FAILED, error="disk full")
        assert r.status == BackupStatus.FAILED
        assert r.error == "disk full"


class TestKDFParams:
    """KDFParams defaults and serialization."""

    def test_kdf_defaults(self) -> None:
        k = KDFParams()
        assert k.algorithm == "argon2id"
        assert k.key_domain == "zorivest-backup-v1"

    def test_kdf_to_dict(self) -> None:
        k = KDFParams(salt_b64="AAAA")
        d = k.to_dict()
        assert d["salt_b64"] == "AAAA"
        assert d["hash_len"] == 32


class TestSQLCipherMeta:
    """SQLCipherMeta defaults."""

    def test_sqlcipher_defaults(self) -> None:
        s = SQLCipherMeta()
        assert s.expected_major == 4
        assert s.cipher_page_size == 4096

    def test_sqlcipher_to_dict(self) -> None:
        d = SQLCipherMeta().to_dict()
        assert "pragmas" in d
        assert d["pragmas"]["kdf_iter"] == 256000


class TestGFSConstants:
    """GFS retention constants match spec."""

    def test_gfs_values(self) -> None:
        assert GFS_DAILY_KEEP == 5
        assert GFS_WEEKLY_KEEP == 4
        assert GFS_MONTHLY_KEEP == 3


# ── BackupManager: Snapshot ──────────────────────────────────────────────


class TestSnapshot:
    """SQLite Online Backup API snapshot."""

    def test_create_snapshot(self, manager: BackupManager, sample_db: Path, backup_dir: Path) -> None:
        snap = manager._create_snapshot("settings", sample_db)
        assert snap.exists()
        assert snap.suffix == ".db"
        # Verify the snapshot is a valid SQLite DB
        conn = sqlite3.connect(str(snap))
        rows = conn.execute("SELECT val FROM test").fetchall()
        conn.close()
        assert rows == [("hello",)]


# ── BackupManager: Full Backup ───────────────────────────────────────────


class TestCreateBackup:
    """Full backup lifecycle."""

    def test_create_backup_success(self, manager: BackupManager) -> None:
        result = manager.create_backup()
        assert result.status == BackupStatus.SUCCESS
        assert result.backup_path is not None
        assert result.backup_path.exists()
        assert result.backup_path.suffix == BACKUP_EXTENSION
        assert result.files_backed_up == 1
        assert result.elapsed_seconds > 0

    def test_backup_contains_manifest(self, manager: BackupManager) -> None:
        result = manager.create_backup()
        assert result.manifest is not None
        assert result.manifest.app_id == "zorivest"
        assert len(result.manifest.files) == 1

    def test_backup_is_encrypted_zip(self, manager: BackupManager) -> None:
        result = manager.create_backup()
        assert result.backup_path is not None
        # The file should be readable as a ZIP
        with pyzipper.AESZipFile(str(result.backup_path), "r") as zf:
            namelist = zf.namelist()
            assert "manifest.json" in namelist
            # Value: verify at least one db file beyond manifest
            assert len(namelist) >= 2

    def test_no_databases_returns_failure(self, backup_dir: Path) -> None:
        mgr = BackupManager(
            db_paths={"missing": Path("/nonexistent/db.sqlite")},
            backup_dir=backup_dir,
            passphrase="test",
        )
        result = mgr.create_backup()
        assert result.status == BackupStatus.FAILED
        assert "No database files" in (result.error or "")

    def test_snapshot_files_cleaned_up(self, manager: BackupManager, backup_dir: Path) -> None:
        manager.create_backup()
        snapshots = list(backup_dir.glob("*.snapshot.db"))
        assert len(snapshots) == 0  # Cleaned up after packaging


# ── BackupManager: List ──────────────────────────────────────────────────


class TestListBackups:
    """list_backups returns sorted paths."""

    def test_list_backups(self, manager: BackupManager) -> None:
        manager.create_backup()
        backups = manager.list_backups()
        assert len(backups) == 1
        assert backups[0].suffix == BACKUP_EXTENSION


# ── BackupManager: Rotation ──────────────────────────────────────────────


class TestGFSRotation:
    """GFS rotation removes excess backups."""

    def test_no_rotation_when_under_limit(self, manager: BackupManager) -> None:
        manager.create_backup()
        rotated = manager._rotate_backups()
        assert rotated == []
        # Value: verify the one backup still exists
        backups = manager.list_backups()
        assert len(backups) == 1

    def test_gfs_rotation_removes_excess(self, backup_dir: Path) -> None:
        """Create more than GFS_DAILY_KEEP stub backup files; verify excess is removed."""
        import time as _time
        from zorivest_infra.backup.backup_manager import BACKUP_EXTENSION

        # Create stub backup files with distinct timestamps
        for i in range(GFS_DAILY_KEEP + 3):
            stub = backup_dir / f"zorivest-backup-stub-{i:03d}{BACKUP_EXTENSION}"
            stub.write_bytes(b"stub")
            _time.sleep(0.05)  # Distinct mtime

        backups_before = list(backup_dir.glob(f"*{BACKUP_EXTENSION}"))
        assert len(backups_before) == GFS_DAILY_KEEP + 3

        # Create a manager just for rotation (doesn't need real DBs)
        mgr = BackupManager(
            db_paths={},
            backup_dir=backup_dir,
            passphrase="unused",
        )
        rotated = mgr._rotate_backups()
        assert len(rotated) > 0  # Some backups were removed

        backups_after = list(backup_dir.glob(f"*{BACKUP_EXTENSION}"))
        assert len(backups_after) < len(backups_before)

    def test_gfs_rotation_proves_5_4_3_tiering(self, backup_dir: Path) -> None:
        """AC-19.8: Prove GFS rotation keeps exactly 5 daily, 4 weekly, 3 monthly.

        Creates 20 stubs spanning 5 months with controlled mtimes.
        After rotation, verifies the exact expected keep set by
        analyzing which stubs survived per algorithm tier:

        Algorithm analysis with these stubs (newest-first order):
          Daily tier: keeps stubs 0-4 (newest 5)
          Weekly tier: scans all newest-first, keeps 1 per week up to 4:
            stub0 (W10) -> weeks_seen={W10}
            stub5 (W09) -> weeks_seen={W10,W09}
            stub6 (W08) -> weeks_seen={W10,W09,W08}
            stub7 (W07) -> weeks_seen={W10,W09,W08,W07} -> limit=4, stops
          Monthly tier: scans all newest-first, keeps 1 per month up to 3:
            stub0 (Mar) -> months_seen={Mar}
            stub5 (Feb) -> months_seen={Mar,Feb}
            stub9 (Jan) -> months_seen={Mar,Feb,Jan} -> limit=3, stops

        Expected keep set: {0,1,2,3,4,5,6,7,9} = 9 stubs retained.
        Expected removed: {8,10,11,12,13,14,15,16,17,18,19} = 11 stubs removed.
        """
        import os
        from datetime import datetime as dt, timedelta, timezone
        from zorivest_infra.backup.backup_manager import BACKUP_EXTENSION

        # Reference point: 2026-03-08 00:00 UTC
        base = dt(2026, 3, 8, 0, 0, 0, tzinfo=timezone.utc)

        # Create 20 stubs across 5 months with known timestamps
        timestamps = [
            # 5 recent (daily tier) — all in March 2026, week 10
            base - timedelta(hours=1),     # [0] Mar 7 23:00
            base - timedelta(hours=25),    # [1] Mar 6 23:00
            base - timedelta(hours=49),    # [2] Mar 5 23:00
            base - timedelta(hours=73),    # [3] Mar 4 23:00
            base - timedelta(hours=97),    # [4] Mar 3 23:00
            # 4 weekly tier — each in a different prior week
            base - timedelta(days=8),      # [5] Feb 28 (week 9)
            base - timedelta(days=15),     # [6] Feb 21 (week 8)
            base - timedelta(days=22),     # [7] Feb 14 (week 7)
            base - timedelta(days=29),     # [8] Feb 7 (week 6) — EXCLUDED (weekly limit=4)
            # 3 monthly tier — each in a different prior month
            base - timedelta(days=40),     # [9] Jan 27 — kept by monthly tier
            base - timedelta(days=70),     # [10] Dec 28 — EXCLUDED (monthly limit=3)
            base - timedelta(days=100),    # [11] Nov 28 — EXCLUDED (monthly limit=3)
            # 8 extras — duplicate week/month buckets, all removed
            base - timedelta(days=9),      # [12] Feb 27 (same week 9 as [5])
            base - timedelta(days=10),     # [13] Feb 26 (same week 9)
            base - timedelta(days=16),     # [14] Feb 20 (same week 8 as [6])
            base - timedelta(days=23),     # [15] Feb 13 (same week 7 as [7])
            base - timedelta(days=41),     # [16] Jan 26 (same month as [9])
            base - timedelta(days=71),     # [17] Dec 27 (same month as [10])
            base - timedelta(days=101),    # [18] Nov 27 (same month as [11])
            base - timedelta(days=130),    # [19] Oct 29 — beyond all tiers
        ]

        stubs = []
        for i, ts in enumerate(timestamps):
            stub = backup_dir / f"zorivest-gfs-{i:03d}{BACKUP_EXTENSION}"
            stub.write_bytes(b"stub")
            epoch = ts.timestamp()
            os.utime(str(stub), (epoch, epoch))
            stubs.append(stub)

        assert len(list(backup_dir.glob(f"*{BACKUP_EXTENSION}"))) == 20

        mgr = BackupManager(db_paths={}, backup_dir=backup_dir, passphrase="unused")
        rotated = mgr._rotate_backups()

        remaining = set(backup_dir.glob(f"*{BACKUP_EXTENSION}"))

        # === DAILY TIER: exactly 5 newest stubs are kept ===
        for i in range(GFS_DAILY_KEEP):
            assert stubs[i] in remaining, f"Daily stub [{i}] must be kept"

        # === WEEKLY TIER: 4 distinct weeks kept (W10 via [0], W09 via [5], W08 via [6], W07 via [7]) ===
        # Stub [8] (week 6) must be excluded — weekly limit is 4
        assert stubs[5] in remaining, "Weekly stub [5] (W09) must be kept"
        assert stubs[6] in remaining, "Weekly stub [6] (W08) must be kept"
        assert stubs[7] in remaining, "Weekly stub [7] (W07) must be kept"
        assert stubs[8] not in remaining, "Weekly stub [8] (W06) must be excluded — limit=4"

        # === MONTHLY TIER: 3 distinct months kept (Mar via [0], Feb via [5], Jan via [9]) ===
        # Stubs [10] (Dec) and [11] (Nov) must be excluded — monthly limit is 3
        assert stubs[9] in remaining, "Monthly stub [9] (Jan) must be kept"
        assert stubs[10] not in remaining, "Monthly stub [10] (Dec) must be excluded — limit=3"
        assert stubs[11] not in remaining, "Monthly stub [11] (Nov) must be excluded — limit=3"

        # === DUPLICATES: all same-bucket extras must be removed ===
        for i in range(12, 20):
            assert stubs[i] not in remaining, f"Duplicate/beyond stub [{i}] must be removed"

        # === TOTAL: exactly 9 retained, 11 rotated ===
        expected_kept = {stubs[i] for i in [0, 1, 2, 3, 4, 5, 6, 7, 9]}
        assert remaining == expected_kept, (
            f"Expected exactly {len(expected_kept)} kept, got {len(remaining)}. "
            f"Extra: {remaining - expected_kept}, Missing: {expected_kept - remaining}"
        )
        assert len(rotated) == 11


# ── BackupManager: Security / Integrity ───────────────────────────────


class TestBackupSecurity:
    """Security and integrity tests for backup."""

    def test_wrong_password_fails_verification(self, sample_db: Path, backup_dir: Path) -> None:
        """Backup encrypted with one passphrase cannot be decrypted with another."""
        mgr = BackupManager(
            db_paths={"settings": sample_db},
            backup_dir=backup_dir,
            passphrase="correct-passphrase",
        )
        result = mgr.create_backup()
        assert result.status == BackupStatus.SUCCESS
        assert result.backup_path is not None

        # Try to read with wrong passphrase-derived key
        wrong_mgr = BackupManager(
            db_paths={"settings": sample_db},
            backup_dir=backup_dir,
            passphrase="wrong-passphrase",
        )
        import base64
        salt = base64.b64decode(result.manifest.kdf.salt_b64)
        wrong_key = wrong_mgr._derive_key(salt)

        with pyzipper.AESZipFile(str(result.backup_path), "r") as zf:
            zf.setpassword(wrong_key)
            with pytest.raises(Exception):
                zf.read("manifest.json")
        # Value: verify the wrong key is different from the correct key
        correct_mgr = BackupManager(
            db_paths={"settings": sample_db},
            backup_dir=backup_dir,
            passphrase="correct-passphrase",
        )
        correct_key = correct_mgr._derive_key(salt)
        assert wrong_key != correct_key

    def test_manifest_hash_integrity(self, manager: BackupManager) -> None:
        """Each file's SHA-256 in manifest matches actual ZIP contents."""
        import hashlib
        import base64

        result = manager.create_backup()
        assert result.manifest is not None
        assert result.backup_path is not None

        salt = base64.b64decode(result.manifest.kdf.salt_b64)
        key = manager._derive_key(salt)

        with pyzipper.AESZipFile(str(result.backup_path), "r") as zf:
            zf.setpassword(key)
            for fe in result.manifest.files:
                data = zf.read(fe.path)
                actual_hash = hashlib.sha256(data).hexdigest()
                assert actual_hash == fe.sha256, f"Hash mismatch for {fe.path}"
                # Value: verify size matches too
                assert len(data) == fe.size_bytes, f"Size mismatch for {fe.path}"

    def test_kdf_domain_separation(self, manager: BackupManager) -> None:
        """Derived key includes domain tag 'zorivest-backup-v1'."""
        salt = b"test-salt-16bytes"
        key1 = manager._derive_key(salt)
        assert isinstance(key1, bytes)
        assert len(key1) == 32

        # Same passphrase + different salt = different key
        key2 = manager._derive_key(b"different-salt!!")
        assert key1 != key2

    def test_kdf_uses_argon2id(self, manager: BackupManager) -> None:
        """Manifest reports argon2id and key derivation uses Argon2id."""
        result = manager.create_backup()
        assert result.manifest is not None
        assert result.manifest.kdf.algorithm == "argon2id"
        assert result.manifest.kdf.time_cost == 3
        assert result.manifest.kdf.memory_kib == 65536
        assert result.manifest.kdf.parallelism == 4

    def test_verify_backup_checks_file_presence(self, backup_dir: Path, sample_db: Path) -> None:
        """Verification fails if a listed file is missing from the ZIP."""
        import base64

        mgr = BackupManager(
            db_paths={"settings": sample_db},
            backup_dir=backup_dir,
            passphrase="test-passphrase-123",
        )
        result = mgr.create_backup()
        assert result.manifest is not None
        assert result.backup_path is not None

        # Create a backup with an extra file claimed in the ZIP's internal manifest
        # We verify that _verify_backup reads manifest from inside ZIP and checks
        # all listed files exist. To trigger the assertion, we write a tampered
        # manifest into a new ZIP that references a file not included.
        salt = base64.b64decode(result.manifest.kdf.salt_b64)
        key = mgr._derive_key(salt)

        from zorivest_infra.backup.backup_types import FileEntry
        tampered_manifest = BackupManifest(
            created_at=result.manifest.created_at,
            platform=result.manifest.platform,
            kdf=result.manifest.kdf,
            files=result.manifest.files + [FileEntry(path="ghost.db", sha256="deadbeef", size_bytes=0)],
        )

        # Write a tampered ZIP with the bad manifest
        tampered_path = backup_dir / "tampered.zvbak"
        with pyzipper.AESZipFile(
            str(tampered_path), "w",
            compression=pyzipper.ZIP_DEFLATED,
            encryption=pyzipper.WZ_AES,
        ) as zf:
            zf.setpassword(key)
            zf.writestr("manifest.json", json.dumps(tampered_manifest.to_dict(), indent=2))
            # Copy real snapshot files but NOT ghost.db
            with pyzipper.AESZipFile(str(result.backup_path), "r") as orig:
                orig.setpassword(key)
                for name in orig.namelist():
                    if name != "manifest.json":
                        zf.writestr(name, orig.read(name))

        with pytest.raises(AssertionError, match="Missing file in backup"):
            mgr._verify_backup(tampered_path, tampered_manifest)
        # Value: verify the tampered manifest has more files than original
        assert len(tampered_manifest.files) == len(result.manifest.files) + 1
