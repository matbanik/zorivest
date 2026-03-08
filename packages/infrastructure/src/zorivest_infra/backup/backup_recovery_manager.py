# packages/infrastructure/src/zorivest_infra/backup/backup_recovery_manager.py
"""BackupRecoveryManager — manual backup operations: restore, verify, repair.

Source: 02a-backup-restore.md §2A.4

Responsibilities:
- Restore from .zvbak backup (decrypt → verify → stage → swap)
- Non-destructive backup verification
- Database integrity check and repair
- Legacy format detection (.zip, .db, .db.gz)
- Maintenance mode hooks for connection lifecycle
"""

from __future__ import annotations

import base64
import gzip
import hashlib
import json
import logging
import os
import shutil
import sqlite3
import zipfile
from pathlib import Path
from typing import Callable

import pyzipper
from argon2.low_level import Type, hash_secret_raw

from zorivest_core.domain.exceptions import (
    CorruptedBackupError,
    InvalidPassphraseError,
)
from zorivest_infra.backup.backup_manager import BACKUP_EXTENSION
from zorivest_infra.backup.backup_recovery_types import (
    RepairResult,
    RepairStatus,
    RestoreResult,
    RestoreStatus,
    VerifyResult,
    VerifyStatus,
)

logger = logging.getLogger(__name__)


class BackupRecoveryManager:
    """Manual backup operations: restore, verify, repair.

    Args:
        db_paths: Mapping of logical name → filesystem path for each database.
        backup_dir: Directory where backup files are stored.
        passphrase: User passphrase for backup decryption.
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
        # Maintenance mode hooks: called during restore to manage connections
        self.close_connections_hook: Callable[[], None] | None = None
        self.reopen_connections_hook: Callable[[], None] | None = None

    # ── Public API ───────────────────────────────────────────────────────

    def restore_backup(self, backup_path: Path) -> RestoreResult:
        """Restore from a backup file.

        Flow: detect format → decrypt → verify manifest → stage → swap → migrate.

        Args:
            backup_path: Path to the backup file (.zvbak, .zip, .db, .db.gz).

        Returns:
            RestoreResult with status and details.

        Raises:
            InvalidPassphraseError: If the passphrase is wrong.
            CorruptedBackupError: If the backup is corrupted (hash mismatch).
        """
        if not backup_path.exists():
            return RestoreResult(
                status=RestoreStatus.FAILED,
                error=f"Backup file not found: {backup_path}",
            )

        fmt = self._detect_format(backup_path)

        if fmt == "zvbak":
            return self._restore_zvbak(backup_path)
        elif fmt == "zip":
            return self._restore_legacy_zip(backup_path)
        elif fmt == "db":
            return self._restore_legacy_db(backup_path)
        elif fmt == "db.gz":
            return self._restore_legacy_db_gz(backup_path)
        else:
            return RestoreResult(
                status=RestoreStatus.FAILED,
                error=f"Unsupported backup format: {backup_path.suffix}",
            )

    def verify_backup(self, backup_path: Path) -> VerifyResult:
        """Non-destructive backup verification.

        Opens the backup, validates manifest, verifies file hashes.
        Does NOT modify any files.

        Returns:
            VerifyResult with status and file details.
        """
        if not backup_path.exists():
            return VerifyResult(
                status=VerifyStatus.FAILED,
                error=f"Backup file not found: {backup_path}",
            )

        fmt = self._detect_format(backup_path)

        if fmt == "zvbak":
            return self._verify_zvbak(backup_path)
        elif fmt == "zip":
            return self._verify_legacy_zip(backup_path)
        elif fmt in ("db", "db.gz"):
            return self._verify_legacy_db(backup_path, fmt)
        else:
            return VerifyResult(
                status=VerifyStatus.FAILED,
                error=f"Unsupported backup format: {backup_path.suffix}",
            )

    def repair_database(self, db_path: Path) -> RepairResult:
        """Run integrity checks and attempt repair on a database.

        Steps:
        1. PRAGMA integrity_check
        2. If errors found, attempt recovery (export → reimport)
        3. Log results

        Returns:
            RepairResult with status and integrity details.
        """
        if not db_path.exists():
            return RepairResult(
                status=RepairStatus.FAILED,
                error=f"Database file not found: {db_path}",
            )

        try:
            conn = sqlite3.connect(str(db_path))
            try:
                rows = conn.execute("PRAGMA integrity_check").fetchall()
                errors = [
                    row[0] for row in rows if row[0] != "ok"
                ]

                if not errors:
                    logger.info("Database integrity check passed: %s", db_path)
                    return RepairResult(status=RepairStatus.HEALTHY)

                # Integrity errors found — attempt repair via export/reimport
                logger.warning(
                    "Integrity errors in %s: %s", db_path, errors
                )
                self._attempt_repair(conn, db_path)

                return RepairResult(
                    status=RepairStatus.REPAIRED,
                    integrity_errors=errors,
                    warnings=["Database was repaired via export/reimport"],
                )
            finally:
                conn.close()

        except Exception as e:
            logger.error("Database repair failed for %s: %s", db_path, e)
            return RepairResult(
                status=RepairStatus.FAILED,
                error=str(e),
            )

    # ── Format Detection ─────────────────────────────────────────────────

    @staticmethod
    def _detect_format(backup_path: Path) -> str:
        """Detect backup format from file extension and magic bytes.

        Returns: 'zvbak', 'zip', 'db', 'db.gz', or 'unknown'.
        """
        name = backup_path.name.lower()

        if name.endswith(BACKUP_EXTENSION):
            return "zvbak"
        elif name.endswith(".db.gz"):
            return "db.gz"
        elif name.endswith(".zip"):
            return "zip"
        elif name.endswith(".db"):
            return "db"
        else:
            # Try magic bytes
            try:
                with open(backup_path, "rb") as f:
                    magic = f.read(4)
                if magic[:2] == b"PK":
                    return "zvbak"  # ZIP-based
                elif magic[:4] == b"SQLi":
                    return "db"
                elif magic[:2] == b"\x1f\x8b":
                    return "db.gz"
            except OSError:
                pass
            return "unknown"

    # ── zvbak Restore ────────────────────────────────────────────────────

    def _restore_zvbak(self, backup_path: Path) -> RestoreResult:
        """Restore from a .zvbak (AES-encrypted ZIP) backup.

        Steps:
        1. Open encrypted ZIP
        2. Read and parse manifest
        3. Verify file hashes
        4. Stage files to temp directory
        5. Close connections (maintenance mode)
        6. Atomic swap via os.replace
        7. Reopen connections
        """
        # Step 1-2: Open and read manifest
        try:
            manifest_data, zf = self._open_zvbak(backup_path)
        except InvalidPassphraseError:
            raise
        except Exception as e:
            raise CorruptedBackupError(f"Failed to open backup: {e}") from e

        try:
            # Step 3: Verify file hashes
            restored_files: list[str] = []
            file_data_map: dict[str, bytes] = {}
            for fe in manifest_data["files"]:
                try:
                    data = zf.read(fe["path"])
                except KeyError as e:
                    raise CorruptedBackupError(
                        f"Missing file in backup: {fe['path']}"
                    ) from e

                actual_hash = hashlib.sha256(data).hexdigest()
                if actual_hash != fe["sha256"]:
                    raise CorruptedBackupError(
                        f"Hash mismatch for {fe['path']}: "
                        f"expected {fe['sha256']}, got {actual_hash}"
                    )
                file_data_map[fe["path"]] = data
                restored_files.append(fe["path"])

            # Step 4: Stage files to temp directory
            stage_dir = self._backup_dir / ".restore_staging"
            stage_dir.mkdir(exist_ok=True)
            for filename, data in file_data_map.items():
                staged_path = stage_dir / filename
                staged_path.write_bytes(data)

            # Step 5: Close connections (maintenance mode)
            if self.close_connections_hook:
                self.close_connections_hook()

            try:
                # Step 6: Atomic swap
                for filename in restored_files:
                    staged = stage_dir / filename
                    # Find the target DB path — match by snapshot name pattern
                    target = self._find_target_for_file(filename)
                    if target:
                        os.replace(str(staged), str(target))
                    else:
                        # Fallback: place in first db_path's parent
                        first_db = next(iter(self._db_paths.values()))
                        os.replace(
                            str(staged), str(first_db.parent / filename)
                        )
            finally:
                # Step 7: Reopen connections (always, even on error)
                if self.reopen_connections_hook:
                    self.reopen_connections_hook()

            # Cleanup staging
            shutil.rmtree(str(stage_dir), ignore_errors=True)

            logger.info(
                "Restore completed: %d files from %s",
                len(restored_files),
                backup_path,
            )
            return RestoreResult(
                status=RestoreStatus.SUCCESS,
                restored_files=restored_files,
            )

        finally:
            zf.close()

    def _open_zvbak(
        self, backup_path: Path
    ) -> tuple[dict, pyzipper.AESZipFile]:
        """Open an encrypted .zvbak file and return (manifest_dict, zip_handle).

        Strategy:
        1. Try extracting salt from ZIP comment (zvbak-salt:...) — new format
        2. If comment present: derive key → set password → read manifest
        3. If no comment: try reading manifest without password (legacy unencrypted manifest)
        4. If manifest has KDF salt: derive key → set password → verify access

        Raises:
            InvalidPassphraseError: If the passphrase is wrong.
        """
        try:
            zf = pyzipper.AESZipFile(str(backup_path), "r")
        except Exception as e:
            raise CorruptedBackupError(
                f"Cannot open backup file: {e}"
            ) from e

        try:
            # Strategy 1: Extract salt from ZIP comment (new format)
            comment = zf.comment or b""
            if comment.startswith(b"zvbak-salt:"):
                salt_b64 = comment[len(b"zvbak-salt:"):]
                salt = base64.b64decode(salt_b64)
                key = self._derive_key(salt)
                zf.setpassword(key)

                try:
                    raw_manifest = zf.read("manifest.json")
                except RuntimeError as e:
                    zf.close()
                    raise InvalidPassphraseError(
                        "Wrong passphrase for backup"
                    ) from e

                manifest_data = json.loads(raw_manifest.decode("utf-8"))

                # Verify we can access at least one data file
                for fe in manifest_data.get("files", []):
                    try:
                        zf.read(fe["path"])
                    except RuntimeError as e:
                        if "password" in str(e).lower() or "bad" in str(e).lower():
                            zf.close()
                            raise InvalidPassphraseError(
                                "Wrong passphrase for backup"
                            ) from e
                        raise
                    break  # Only need to test one file

                return manifest_data, zf

            # Strategy 2: Legacy format — try reading manifest without password
            try:
                raw_manifest = zf.read("manifest.json")
            except RuntimeError:
                zf.close()
                raise InvalidPassphraseError(
                    "Cannot read manifest — wrong passphrase or corrupted file"
                )

            manifest_data = json.loads(raw_manifest.decode("utf-8"))
            salt_b64 = manifest_data.get("kdf", {}).get("salt_b64", "")

            if salt_b64:
                salt = base64.b64decode(salt_b64)
                key = self._derive_key(salt)
                zf.setpassword(key)

            # Verify we can access files
            for fe in manifest_data.get("files", []):
                try:
                    zf.read(fe["path"])
                except RuntimeError as e:
                    if "password" in str(e).lower() or "bad" in str(e).lower():
                        zf.close()
                        raise InvalidPassphraseError(
                            "Wrong passphrase for backup"
                        ) from e
                    raise
                break  # Only need to test one file

            return manifest_data, zf

        except (InvalidPassphraseError, CorruptedBackupError):
            zf.close()
            raise
        except Exception as e:
            zf.close()
            raise CorruptedBackupError(
                f"Failed to read backup manifest: {e}"
            ) from e

    def _find_target_for_file(self, filename: str) -> Path | None:
        """Find the target database path for a restored file.

        Matches snapshot filenames like 'main.snapshot.db' to db_paths keys.
        """
        # Strip .snapshot.db suffix if present
        base = filename.replace(".snapshot.db", "").replace(".db", "")
        if base in self._db_paths:
            return self._db_paths[base]

        # Try matching just the filename
        for _name, path in self._db_paths.items():
            if path.name == filename:
                return path

        return None

    # ── Legacy Format Restores ───────────────────────────────────────────

    def _restore_legacy_zip(self, backup_path: Path) -> RestoreResult:
        """Restore from a plain (unencrypted) ZIP backup."""
        try:
            with zipfile.ZipFile(str(backup_path), "r") as zf:
                stage_dir = self._backup_dir / ".restore_staging"
                stage_dir.mkdir(exist_ok=True)
                zf.extractall(str(stage_dir))

                restored_files: list[str] = []
                if self.close_connections_hook:
                    self.close_connections_hook()

                try:
                    for name in zf.namelist():
                        staged = stage_dir / name
                        if staged.is_file():
                            target = self._find_target_for_file(name)
                            if target:
                                os.replace(str(staged), str(target))
                            restored_files.append(name)
                finally:
                    if self.reopen_connections_hook:
                        self.reopen_connections_hook()

                shutil.rmtree(str(stage_dir), ignore_errors=True)

            return RestoreResult(
                status=RestoreStatus.SUCCESS,
                restored_files=restored_files,
                warnings=["Restored from legacy ZIP format (unencrypted)"],
            )
        except Exception as e:
            return RestoreResult(
                status=RestoreStatus.FAILED,
                error=f"Legacy ZIP restore failed: {e}",
            )

    def _restore_legacy_db(self, backup_path: Path) -> RestoreResult:
        """Restore from a plain .db file."""
        try:
            if self.close_connections_hook:
                self.close_connections_hook()
            try:
                target = next(iter(self._db_paths.values()))
                shutil.copy2(str(backup_path), str(target))
            finally:
                if self.reopen_connections_hook:
                    self.reopen_connections_hook()

            return RestoreResult(
                status=RestoreStatus.SUCCESS,
                restored_files=[backup_path.name],
                warnings=["Restored from legacy .db format"],
            )
        except Exception as e:
            return RestoreResult(
                status=RestoreStatus.FAILED,
                error=f"Legacy .db restore failed: {e}",
            )

    def _restore_legacy_db_gz(self, backup_path: Path) -> RestoreResult:
        """Restore from a gzipped .db.gz file."""
        try:
            if self.close_connections_hook:
                self.close_connections_hook()
            try:
                target = next(iter(self._db_paths.values()))
                with gzip.open(str(backup_path), "rb") as f_in:
                    target.write_bytes(f_in.read())
            finally:
                if self.reopen_connections_hook:
                    self.reopen_connections_hook()

            return RestoreResult(
                status=RestoreStatus.SUCCESS,
                restored_files=[backup_path.name],
                warnings=["Restored from legacy .db.gz format"],
            )
        except Exception as e:
            return RestoreResult(
                status=RestoreStatus.FAILED,
                error=f"Legacy .db.gz restore failed: {e}",
            )

    # ── Verify Operations ────────────────────────────────────────────────

    def _verify_zvbak(self, backup_path: Path) -> VerifyResult:
        """Verify a .zvbak backup without modifying anything."""
        try:
            manifest_data, zf = self._open_zvbak(backup_path)
        except InvalidPassphraseError:
            return VerifyResult(
                status=VerifyStatus.FAILED,
                error="Wrong passphrase",
            )
        except CorruptedBackupError as e:
            return VerifyResult(
                status=VerifyStatus.CORRUPTED,
                error=str(e),
            )
        except Exception as e:
            return VerifyResult(
                status=VerifyStatus.FAILED,
                error=str(e),
            )

        try:
            total_size = 0
            warnings: list[str] = []

            for fe in manifest_data.get("files", []):
                try:
                    data = zf.read(fe["path"])
                except KeyError:
                    return VerifyResult(
                        status=VerifyStatus.CORRUPTED,
                        manifest=manifest_data,
                        error=f"Missing file: {fe['path']}",
                    )
                except RuntimeError:
                    return VerifyResult(
                        status=VerifyStatus.CORRUPTED,
                        error="Cannot decrypt backup contents",
                    )

                actual_hash = hashlib.sha256(data).hexdigest()
                if actual_hash != fe["sha256"]:
                    return VerifyResult(
                        status=VerifyStatus.CORRUPTED,
                        manifest=manifest_data,
                        error=(
                            f"Hash mismatch for {fe['path']}: "
                            f"expected {fe['sha256']}, got {actual_hash}"
                        ),
                    )
                total_size += len(data)

            return VerifyResult(
                status=VerifyStatus.VALID,
                file_count=len(manifest_data.get("files", [])),
                total_size_bytes=total_size,
                manifest=manifest_data,
                warnings=warnings,
            )
        finally:
            zf.close()

    def _verify_legacy_zip(self, backup_path: Path) -> VerifyResult:
        """Verify a legacy ZIP backup."""
        try:
            with zipfile.ZipFile(str(backup_path), "r") as zf:
                bad = zf.testzip()
                if bad is not None:
                    return VerifyResult(
                        status=VerifyStatus.CORRUPTED,
                        error=f"Corrupted file in ZIP: {bad}",
                        warnings=["Legacy ZIP format (unencrypted)"],
                    )

                total_size = sum(info.file_size for info in zf.infolist())
                return VerifyResult(
                    status=VerifyStatus.VALID,
                    file_count=len(zf.namelist()),
                    total_size_bytes=total_size,
                    warnings=["Legacy ZIP format (unencrypted)"],
                )
        except zipfile.BadZipFile:
            return VerifyResult(
                status=VerifyStatus.CORRUPTED,
                error="Invalid ZIP file",
            )
        except Exception as e:
            return VerifyResult(
                status=VerifyStatus.FAILED,
                error=str(e),
            )

    def _verify_legacy_db(
        self, backup_path: Path, fmt: str
    ) -> VerifyResult:
        """Verify a legacy .db or .db.gz file."""
        warnings = [f"Legacy {fmt} format"]
        try:
            if fmt == "db.gz":
                with gzip.open(str(backup_path), "rb") as f:
                    data = f.read()
            else:
                data = backup_path.read_bytes()

            # Check SQLite magic bytes
            if data[:16] != b"SQLite format 3\x00":
                return VerifyResult(
                    status=VerifyStatus.CORRUPTED,
                    error="Not a valid SQLite database",
                    warnings=warnings,
                )

            return VerifyResult(
                status=VerifyStatus.VALID,
                file_count=1,
                total_size_bytes=len(data),
                warnings=warnings,
            )
        except Exception as e:
            return VerifyResult(
                status=VerifyStatus.FAILED,
                error=str(e),
                warnings=warnings,
            )

    # ── Repair Operations ────────────────────────────────────────────────

    def _attempt_repair(self, conn: sqlite3.Connection, db_path: Path) -> None:
        """Attempt database repair via export/reimport.

        Steps:
        1. Dump all data from corrupted DB
        2. Create new DB
        3. Import dumped data
        4. Replace original with repaired version
        """
        repair_path = db_path.with_suffix(".repair.db")
        try:
            # Export via iterdump()
            dump_lines = list(conn.iterdump())

            # Create new database and reimport
            repair_conn = sqlite3.connect(str(repair_path))
            try:
                for line in dump_lines:
                    repair_conn.execute(line)
                repair_conn.commit()
            finally:
                repair_conn.close()

            # Close original connection before swap
            conn.close()

            # Atomic swap
            os.replace(str(repair_path), str(db_path))
            logger.info("Database repaired via export/reimport: %s", db_path)

        except Exception:
            # Clean up repair file on failure
            if repair_path.exists():
                repair_path.unlink(missing_ok=True)
            raise

    # ── KDF (shared with BackupManager) ──────────────────────────────────

    def _derive_key(self, salt: bytes) -> bytes:
        """Derive backup encryption key using Argon2id.

        Uses identical parameters to BackupManager._derive_key for compatibility.
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
