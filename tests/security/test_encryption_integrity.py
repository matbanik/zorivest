# tests/security/test_encryption_integrity.py
"""Encryption verification tests — binary integrity, key management, backup.

Tests SQLCipher encryption at the file level to prove:
1. Encrypted data is not readable as plaintext
2. PRAGMA integrity checks work with correct/wrong keys
3. Key rotation preserves data and invalidates old keys
4. Backup files are also encrypted
5. Envelope encryption (passphrase + API key) both unlock the same data

Uses sqlcipher3-binary (already in zorivest-infra dependencies) and
patterns from poc/poc_envelope_encryption.py.
"""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Generator

import pytest

# Add poc/ for KeyVault import
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "poc"))


# ── Test availability ───────────────────────────────────────────────────

try:
    import sqlcipher3  # type: ignore[import-untyped]

    HAS_SQLCIPHER = True
except ImportError:
    HAS_SQLCIPHER = False

pytestmark = pytest.mark.skipif(
    not HAS_SQLCIPHER,
    reason="sqlcipher3-binary not installed",
)


# ── Constants ───────────────────────────────────────────────────────────

TEST_PASSPHRASE = "TestPa$$w0rd!2026"
WRONG_PASSPHRASE = "WrongPassword123"
TEST_DATA_STRING = "AAPL,BOT,100,189.50,ACC001"
TEST_BLOB = b"\x89PNG\r\n\x1a\n" + os.urandom(1024)


# ── Helpers ─────────────────────────────────────────────────────────────


def _open_encrypted(db_path: str, passphrase: str) -> "sqlcipher3.Connection":
    """Open a SQLCipher DB with the given passphrase."""
    conn = sqlcipher3.connect(db_path)
    conn.execute(f"PRAGMA key = '{passphrase}'")
    return conn


def _create_test_db(db_path: str, passphrase: str) -> None:
    """Create a test DB with sample trades table and data."""
    conn = _open_encrypted(db_path, passphrase)
    conn.execute("""
        CREATE TABLE trades (
            exec_id TEXT PRIMARY KEY,
            instrument TEXT NOT NULL,
            action TEXT NOT NULL,
            quantity REAL NOT NULL,
            price REAL NOT NULL,
            account_id TEXT NOT NULL
        )
    """)
    conn.execute(
        "INSERT INTO trades VALUES (?, ?, ?, ?, ?, ?)",
        ("E001", "AAPL", "BOT", 100, 189.50, "ACC001"),
    )
    conn.execute(
        "INSERT INTO trades VALUES (?, ?, ?, ?, ?, ?)",
        ("E002", "MSFT", "SLD", 50, 415.25, "ACC002"),
    )
    conn.commit()
    conn.close()


# ── Fixtures ────────────────────────────────────────────────────────────


@pytest.fixture()
def tmp_dir() -> Generator[Path, None, None]:
    """Temporary directory for test databases."""
    with tempfile.TemporaryDirectory(prefix="zorivest_sec_") as d:
        yield Path(d)


@pytest.fixture()
def encrypted_db(tmp_dir: Path) -> Path:
    """Pre-created encrypted test database."""
    db_path = tmp_dir / "test.db"
    _create_test_db(str(db_path), TEST_PASSPHRASE)
    return db_path


# ── Test 1: Binary not readable as plaintext ────────────────────────────


class TestBinaryIntegrity:
    """Prove encrypted files don't contain plaintext data."""

    def test_binary_not_readable_as_plaintext(self, encrypted_db: Path) -> None:
        """Known trade data should NOT appear in raw file bytes."""
        raw = encrypted_db.read_bytes()
        # None of these strings should be in the raw encrypted file
        assert b"AAPL" not in raw
        assert b"MSFT" not in raw
        assert b"ACC001" not in raw
        assert b"trades" not in raw  # table name also encrypted

    def test_empty_db_encrypted(self, tmp_dir: Path) -> None:
        """Even an empty encrypted DB is not valid plain sqlite3."""
        db_path = tmp_dir / "empty.db"
        conn = _open_encrypted(str(db_path), TEST_PASSPHRASE)
        conn.execute("CREATE TABLE stub (id INTEGER)")
        conn.commit()
        conn.close()

        # Try opening with plain sqlite3 — should fail
        raw = db_path.read_bytes()
        assert not raw.startswith(b"SQLite format 3")

    def test_large_blob_encrypted(self, tmp_dir: Path) -> None:
        """Binary data (images) survives encrypt→store→retrieve cycle."""
        db_path = tmp_dir / "blob.db"
        conn = _open_encrypted(str(db_path), TEST_PASSPHRASE)
        conn.execute("CREATE TABLE images (id INTEGER PRIMARY KEY, data BLOB)")
        conn.execute("INSERT INTO images VALUES (1, ?)", (TEST_BLOB,))
        conn.commit()
        conn.close()

        # Verify blob not in raw file
        raw = db_path.read_bytes()
        assert TEST_BLOB not in raw

        # Verify round-trip
        conn2 = _open_encrypted(str(db_path), TEST_PASSPHRASE)
        row = conn2.execute("SELECT data FROM images WHERE id = 1").fetchone()
        assert row[0] == TEST_BLOB
        conn2.close()


# ── Test 2: PRAGMA integrity checks ─────────────────────────────────────


class TestPragmaIntegrity:
    """PRAGMA integrity_check with correct and wrong keys."""

    def test_pragma_integrity_check_passes(self, encrypted_db: Path) -> None:
        """Correctly keyed DB passes PRAGMA integrity_check."""
        conn = _open_encrypted(str(encrypted_db), TEST_PASSPHRASE)
        result = conn.execute("PRAGMA integrity_check").fetchone()
        assert result[0] == "ok"
        conn.close()

    def test_pragma_integrity_check_fails_wrong_key(self, encrypted_db: Path) -> None:
        """Wrong key → cannot even read sqlite_master."""
        conn = _open_encrypted(str(encrypted_db), WRONG_PASSPHRASE)
        with pytest.raises(Exception):  # noqa: B017 — DatabaseError varies
            conn.execute("SELECT count(*) FROM sqlite_master")
        conn.close()

    def test_wrong_key_cannot_read(self, encrypted_db: Path) -> None:
        """Wrong passphrase → DatabaseError on SELECT."""
        conn = _open_encrypted(str(encrypted_db), WRONG_PASSPHRASE)
        with pytest.raises(Exception):  # noqa: B017
            conn.execute("SELECT * FROM trades")
        conn.close()


# ── Test 3: Key rotation ────────────────────────────────────────────────


class TestKeyRotation:
    """Rekey changes the passphrase while preserving data."""

    def test_key_rotation_preserves_data(self, encrypted_db: Path) -> None:
        """Rekey to new passphrase → data still accessible with new key."""
        new_passphrase = "NewStr0ng!Key#2026"

        conn = _open_encrypted(str(encrypted_db), TEST_PASSPHRASE)
        conn.execute(f"PRAGMA rekey = '{new_passphrase}'")
        conn.close()

        # Verify data accessible with new key
        conn2 = _open_encrypted(str(encrypted_db), new_passphrase)
        rows = conn2.execute("SELECT * FROM trades ORDER BY exec_id").fetchall()
        assert len(rows) == 2
        assert rows[0][0] == "E001"
        assert rows[1][0] == "E002"
        conn2.close()

    def test_key_rotation_invalidates_old_key(self, encrypted_db: Path) -> None:
        """After rekey → old passphrase should fail."""
        new_passphrase = "NewStr0ng!Key#2026"

        conn = _open_encrypted(str(encrypted_db), TEST_PASSPHRASE)
        conn.execute(f"PRAGMA rekey = '{new_passphrase}'")
        conn.close()

        # Old passphrase should fail
        conn2 = _open_encrypted(str(encrypted_db), TEST_PASSPHRASE)
        with pytest.raises(Exception):  # noqa: B017
            conn2.execute("SELECT * FROM trades")
        conn2.close()


# ── Test 4: WAL mode ────────────────────────────────────────────────────


class TestEncryptedWAL:
    """WAL journal mode works with encryption."""

    def test_wal_mode_enabled(self, encrypted_db: Path) -> None:
        """Encrypted DB can use WAL journal mode."""
        conn = _open_encrypted(str(encrypted_db), TEST_PASSPHRASE)
        conn.execute("PRAGMA journal_mode=wal")
        mode = conn.execute("PRAGMA journal_mode").fetchone()
        assert mode[0] == "wal"
        conn.close()

    def test_concurrent_read_write_encrypted(self, encrypted_db: Path) -> None:
        """WAL allows concurrent readers on encrypted DB."""
        conn1 = _open_encrypted(str(encrypted_db), TEST_PASSPHRASE)
        conn1.execute("PRAGMA journal_mode=wal")

        # Start a read on conn1
        rows1 = conn1.execute("SELECT count(*) FROM trades").fetchone()
        assert rows1[0] == 2

        # Concurrent write on conn2
        conn2 = _open_encrypted(str(encrypted_db), TEST_PASSPHRASE)
        conn2.execute("PRAGMA journal_mode=wal")
        conn2.execute(
            "INSERT INTO trades VALUES (?, ?, ?, ?, ?, ?)",
            ("E003", "GOOG", "BOT", 25, 178.30, "ACC001"),
        )
        conn2.commit()

        # conn1 can still read (and sees updated count after re-query)
        rows2 = conn1.execute("SELECT count(*) FROM trades").fetchone()
        assert rows2[0] == 3

        conn1.close()
        conn2.close()


# ── Test 5: Backup encryption ───────────────────────────────────────────


class TestBackupEncryption:
    """Backup copies of encrypted DBs remain encrypted."""

    def test_backup_file_encrypted(self, encrypted_db: Path, tmp_dir: Path) -> None:
        """File-level copy of encrypted DB is also unreadable as plaintext."""
        backup_path = tmp_dir / "backup.db"
        shutil.copy2(encrypted_db, backup_path)

        raw = backup_path.read_bytes()
        assert b"AAPL" not in raw
        assert b"MSFT" not in raw

    def test_backup_restore_roundtrip(self, encrypted_db: Path, tmp_dir: Path) -> None:
        """Backup → restore with same key → data intact."""
        backup_path = tmp_dir / "backup.db"
        shutil.copy2(encrypted_db, backup_path)

        conn = _open_encrypted(str(backup_path), TEST_PASSPHRASE)
        rows = conn.execute("SELECT * FROM trades ORDER BY exec_id").fetchall()
        assert len(rows) == 2
        assert rows[0][1] == "AAPL"
        assert rows[1][1] == "MSFT"
        conn.close()


# ── Test 6: Envelope encryption (KeyVault) ──────────────────────────────


class TestEnvelopeEncryption:
    """Prove that both passphrase and API key can independently open the DB."""

    def test_envelope_passphrase_unlock(self, tmp_dir: Path) -> None:
        """KeyVault passphrase → DEK → open DB → read data."""
        from key_vault import KeyVault

        bootstrap_path = tmp_dir / "bootstrap.json"
        db_path = str(tmp_dir / "envelope.db")

        vault = KeyVault(bootstrap_path)
        vault.config.db_path = db_path

        passphrase = "EnvelopeTest!2026"
        dek = vault.initialize_with_passphrase(passphrase)

        # Create DB with DEK
        conn = sqlcipher3.connect(db_path)
        conn.execute(f"PRAGMA key=\"x'{dek.hex()}'\"")
        conn.execute("SELECT count(*) FROM sqlite_master")  # verify key works
        conn.execute("CREATE TABLE trades (id TEXT, instrument TEXT)")
        conn.execute("INSERT INTO trades VALUES ('E001', 'AAPL')")
        conn.commit()
        conn.close()

        # Unlock with passphrase via vault
        dek2 = vault.unlock_with_passphrase(passphrase)
        assert dek == dek2

        conn2 = sqlcipher3.connect(db_path)
        conn2.execute(f"PRAGMA key=\"x'{dek2.hex()}'\"")
        row = conn2.execute("SELECT instrument FROM trades WHERE id='E001'").fetchone()
        assert row[0] == "AAPL"
        conn2.close()

    def test_envelope_api_key_unlock(self, tmp_dir: Path) -> None:
        """KeyVault API key → DEK → open DB → read same data."""
        from key_vault import KeyVault

        bootstrap_path = tmp_dir / "bootstrap.json"
        db_path = str(tmp_dir / "envelope_api.db")

        vault = KeyVault(bootstrap_path)
        vault.config.db_path = db_path

        passphrase = "ApiKeyTest!2026"
        dek = vault.initialize_with_passphrase(passphrase)

        # Create DB with DEK
        conn = sqlcipher3.connect(db_path)
        conn.execute(f"PRAGMA key=\"x'{dek.hex()}'\"")
        conn.execute("SELECT count(*) FROM sqlite_master")
        conn.execute("CREATE TABLE trades (id TEXT, instrument TEXT)")
        conn.execute("INSERT INTO trades VALUES ('E001', 'GOOG')")
        conn.commit()
        conn.close()

        # Generate API key
        api_key = vault.generate_api_key(dek, role="read-write")
        assert api_key.startswith("zrv_sk_")

        # Fresh vault — unlock with API key only
        vault2 = KeyVault(bootstrap_path)
        dek_from_api = vault2.unlock_with_api_key(api_key)
        assert dek_from_api == dek

        conn2 = sqlcipher3.connect(db_path)
        conn2.execute(f"PRAGMA key=\"x'{dek_from_api.hex()}'\"")
        row = conn2.execute("SELECT instrument FROM trades WHERE id='E001'").fetchone()
        assert row[0] == "GOOG"
        conn2.close()
