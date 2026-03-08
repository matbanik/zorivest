# packages/infrastructure/src/zorivest_infra/backup/backup_manager.py
"""BackupManager — automatic timed backups with GFS rotation.

Source: 02a-backup-restore.md §2A.3

Responsibilities:
- Create consistent snapshots via SQLite Online Backup API
- Package into AES-encrypted ZIP (pyzipper)
- Build manifest with file hashes and KDF params
- Rotate with GFS retention policy (5 daily, 4 weekly, 3 monthly)
- Post-backup verification (re-open ZIP, verify manifest)
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pyzipper
from argon2.low_level import Type, hash_secret_raw

from zorivest_infra.backup.backup_types import (
    GFS_DAILY_KEEP,
    GFS_MONTHLY_KEEP,
    GFS_WEEKLY_KEEP,
    BackupManifest,
    BackupResult,
    BackupStatus,
    FileEntry,
    KDFParams,
)

# Backup file extension
BACKUP_EXTENSION = ".zvbak"


class BackupManager:
    """Automatic timed backups with GFS rotation.

    Args:
        db_paths: Mapping of logical name → filesystem path for each database.
        backup_dir: Directory where backup files are stored.
        passphrase: User passphrase (injected at app boot, held for session).
    """

    def __init__(
        self,
        db_paths: dict[str, Path],
        backup_dir: Path,
        passphrase: str,
    ) -> None:
        self._db_paths = db_paths
        self._backup_dir = backup_dir
        self._passphrase = passphrase
        self._backup_dir.mkdir(parents=True, exist_ok=True)

    def create_backup(self) -> BackupResult:
        """Create a full backup: snapshot → package → rotate → verify.

        Returns BackupResult with status, path, manifest, and rotation info.
        """
        start = time.monotonic()
        try:
            # Step 1: Create consistent snapshots
            snapshot_paths = []
            for name, db_path in self._db_paths.items():
                if db_path.exists():
                    snap = self._create_snapshot(name, db_path)
                    snapshot_paths.append(snap)

            if not snapshot_paths:
                return BackupResult(
                    status=BackupStatus.FAILED,
                    error="No database files found to back up",
                    elapsed_seconds=time.monotonic() - start,
                )

            # Step 2: Package into AES-encrypted ZIP
            backup_path, manifest = self._package_backup(snapshot_paths)

            # Step 3: Clean up snapshots
            for snap in snapshot_paths:
                snap.unlink(missing_ok=True)

            # Step 4: Rotate old backups (GFS policy)
            rotated = self._rotate_backups()

            # Step 5: Post-backup verification
            self._verify_backup(backup_path, manifest)

            elapsed = time.monotonic() - start
            return BackupResult(
                status=BackupStatus.SUCCESS,
                backup_path=backup_path,
                manifest=manifest,
                files_backed_up=len(snapshot_paths),
                elapsed_seconds=elapsed,
                rotated_files=rotated,
            )
        except Exception as e:
            return BackupResult(
                status=BackupStatus.FAILED,
                error=str(e),
                elapsed_seconds=time.monotonic() - start,
            )

    def _create_snapshot(self, name: str, source_path: Path) -> Path:
        """Use SQLite Online Backup API for a consistent snapshot."""
        snapshot_path = self._backup_dir / f"{name}.snapshot.db"
        source_conn = sqlite3.connect(str(source_path))
        dest_conn = sqlite3.connect(str(snapshot_path))
        try:
            source_conn.backup(dest_conn)
        finally:
            dest_conn.close()
            source_conn.close()
        return snapshot_path

    def _package_backup(
        self, snapshot_paths: list[Path]
    ) -> tuple[Path, BackupManifest]:
        """Create AES-encrypted ZIP with manifest and snapshots."""
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d-%H%M%S")
        backup_filename = f"zorivest-backup-{timestamp}{BACKUP_EXTENSION}"
        backup_path = self._backup_dir / backup_filename

        # Derive backup key
        salt = os.urandom(16)
        key = self._derive_key(salt)

        # Build file entries with SHA-256 hashes
        file_entries: list[FileEntry] = []
        for snap_path in snapshot_paths:
            data = snap_path.read_bytes()
            sha256 = hashlib.sha256(data).hexdigest()
            file_entries.append(
                FileEntry(
                    path=snap_path.name,
                    sha256=sha256,
                    size_bytes=len(data),
                )
            )

        # Build manifest
        manifest = BackupManifest(
            created_at=datetime.now(timezone.utc).isoformat() + "Z",
            platform=sys.platform,
            kdf=KDFParams(salt_b64=base64.b64encode(salt).decode()),
            files=file_entries,
        )

        # Write AES-encrypted ZIP with salt in comment for recovery
        with pyzipper.AESZipFile(
            str(backup_path),
            "w",
            compression=pyzipper.ZIP_DEFLATED,
            encryption=pyzipper.WZ_AES,
        ) as zf:
            zf.setpassword(key)
            # Store salt in ZIP comment for independent recovery
            zf.comment = b"zvbak-salt:" + base64.b64encode(salt)
            # Write manifest
            zf.writestr("manifest.json", json.dumps(manifest.to_dict(), indent=2))
            # Write snapshot files
            for snap_path in snapshot_paths:
                zf.write(str(snap_path), arcname=snap_path.name)

        return backup_path, manifest

    def _derive_key(self, salt: bytes) -> bytes:
        """Derive backup encryption key using Argon2id.

        Uses argon2-cffi low-level API with parameters matching KDFParams defaults:
        - type: Argon2id (hybrid side-channel resistant)
        - time_cost: 3
        - memory_cost: 65536 KiB (64 MB)
        - parallelism: 4
        - hash_len: 32 bytes
        - domain separation via salt + b"zorivest-backup-v1"
        """
        return hash_secret_raw(
            secret=self._passphrase.encode("utf-8"),
            salt=salt + b"zorivest-backup-v1",
            time_cost=3,
            memory_cost=65536,
            parallelism=4,
            hash_len=32,
            type=Type.ID,
        )

    def _rotate_backups(self) -> list[Path]:
        """Apply GFS retention: 5 daily, 4 weekly, 3 monthly. Remove expired."""
        backups = sorted(
            self._backup_dir.glob(f"*{BACKUP_EXTENSION}"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

        if len(backups) <= GFS_DAILY_KEEP:
            return []

        # Simple GFS: keep newest N daily, then weekly, then monthly
        keep: set[Path] = set()

        # Daily: keep newest 5
        for b in backups[:GFS_DAILY_KEEP]:
            keep.add(b)

        # Weekly: keep 1 per week for 4 weeks (oldest of each week bucket)
        weeks_seen: set[str] = set()
        for b in backups:
            week_key = datetime.fromtimestamp(
                b.stat().st_mtime, tz=timezone.utc
            ).strftime("%Y-W%W")
            if week_key not in weeks_seen and len(weeks_seen) < GFS_WEEKLY_KEEP:
                weeks_seen.add(week_key)
                keep.add(b)

        # Monthly: keep 1 per month for 3 months
        months_seen: set[str] = set()
        for b in backups:
            month_key = datetime.fromtimestamp(
                b.stat().st_mtime, tz=timezone.utc
            ).strftime("%Y-%m")
            if month_key not in months_seen and len(months_seen) < GFS_MONTHLY_KEEP:
                months_seen.add(month_key)
                keep.add(b)

        # Remove backups not in keep set
        rotated: list[Path] = []
        for b in backups:
            if b not in keep:
                b.unlink(missing_ok=True)
                rotated.append(b)

        return rotated

    def _verify_backup(self, backup_path: Path, manifest: BackupManifest) -> None:
        """Post-backup verification: re-open ZIP and verify manifest integrity."""
        # Re-derive key from the manifest's salt
        salt = base64.b64decode(manifest.kdf.salt_b64)
        key = self._derive_key(salt)

        with pyzipper.AESZipFile(str(backup_path), "r") as zf:
            zf.setpassword(key)
            manifest_data = json.loads(zf.read("manifest.json").decode())
            assert manifest_data["app_id"] == "zorivest"
            # Verify all listed files exist in the ZIP and hashes match
            zip_names = set(zf.namelist())
            for fe in manifest_data["files"]:
                assert fe["path"] in zip_names, f"Missing file in backup: {fe['path']}"
                # Verify SHA-256 hash integrity
                file_data = zf.read(fe["path"])
                actual_hash = hashlib.sha256(file_data).hexdigest()
                assert actual_hash == fe["sha256"], (
                    f"Hash mismatch for {fe['path']}: "
                    f"expected {fe['sha256']}, got {actual_hash}"
                )

    def list_backups(self) -> list[Path]:
        """List all backup files in the backup directory, newest first."""
        return sorted(
            self._backup_dir.glob(f"*{BACKUP_EXTENSION}"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
