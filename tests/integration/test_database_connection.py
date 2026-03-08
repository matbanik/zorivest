# tests/integration/test_database_connection.py
"""Integration tests for SQLCipher connection factory (MEU-16)."""

from __future__ import annotations

import sqlite3

import pytest

from zorivest_infra.database.connection import (
    create_encrypted_connection,
    derive_key,
    is_sqlcipher_available,
)


class TestDeriveKey:
    """AC-16.1: Key derivation is deterministic and produces 256-bit keys."""

    def test_deterministic_with_same_salt(self) -> None:
        salt = b"0123456789abcdef"
        key1 = derive_key("password", salt=salt)
        key2 = derive_key("password", salt=salt)
        assert key1 == key2

    def test_32_bytes(self) -> None:
        key = derive_key("password", salt=b"0123456789abcdef")
        assert len(key) == 32

    def test_different_passwords_different_keys(self) -> None:
        salt = b"0123456789abcdef"
        key1 = derive_key("password1", salt=salt)
        key2 = derive_key("password2", salt=salt)
        assert key1 != key2

    def test_different_salts_different_keys(self) -> None:
        key1 = derive_key("password", salt=b"salt_one________")
        key2 = derive_key("password", salt=b"salt_two________")
        assert key1 != key2


class TestCreateEncryptedConnection:
    """AC-16.2: Connection factory creates working database."""

    def test_create_and_use_database(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        db_path = str(tmp_path / "test.db")
        conn = create_encrypted_connection(db_path, passphrase="test123")

        conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)")
        conn.execute("INSERT INTO test (name) VALUES (?)", ("hello",))
        conn.commit()

        cursor = conn.execute("SELECT name FROM test")
        row = cursor.fetchone()
        assert row is not None
        assert row[0] == "hello"
        conn.close()

    def test_wal_mode_enabled(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        """AC-16.3: WAL mode is enabled on the connection."""
        db_path = str(tmp_path / "test_wal.db")
        conn = create_encrypted_connection(db_path, passphrase="test123")

        cursor = conn.execute("PRAGMA journal_mode")
        mode = cursor.fetchone()
        assert mode is not None
        assert mode[0] == "wal"
        conn.close()

    def test_reopen_database(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        """AC-16.4: Database can be reopened with same passphrase."""
        db_path = str(tmp_path / "test_reopen.db")

        # Create and write
        conn1 = create_encrypted_connection(db_path, passphrase="secret")
        conn1.execute("CREATE TABLE data (val TEXT)")
        conn1.execute("INSERT INTO data (val) VALUES (?)", ("persistent",))
        conn1.commit()
        conn1.close()

        # Reopen and read
        conn2 = create_encrypted_connection(db_path, passphrase="secret")
        cursor = conn2.execute("SELECT val FROM data")
        row = cursor.fetchone()
        assert row is not None
        assert row[0] == "persistent"
        conn2.close()


class TestEncryptionContract:
    """AC-16.5: Encryption contract verification."""

    def test_sqlcipher_availability_flag(self) -> None:
        """is_sqlcipher_available() reflects actual import state."""
        result = is_sqlcipher_available()
        assert isinstance(result, bool)

    @pytest.mark.skipif(
        not is_sqlcipher_available(),
        reason="sqlcipher3 not installed — encryption test requires native library",
    )
    def test_encrypted_db_unreadable_by_plain_sqlite(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        """When sqlcipher3 IS available, raw sqlite3 cannot read the DB."""
        db_path = str(tmp_path / "encrypted.db")
        conn = create_encrypted_connection(db_path, passphrase="s3cret!")
        conn.execute("CREATE TABLE secrets (val TEXT)")
        conn.execute("INSERT INTO secrets (val) VALUES (?)", ("hidden",))
        conn.commit()
        conn.close()

        # Plain sqlite3 should fail to read
        raw = sqlite3.connect(db_path)
        with pytest.raises(Exception):  # noqa: B017
            raw.execute("SELECT val FROM secrets")
        raw.close()

    @pytest.mark.skipif(
        is_sqlcipher_available(),
        reason="sqlcipher3 IS installed — fallback test not applicable",
    )
    def test_fallback_produces_plaintext_warning(self, tmp_path, caplog) -> None:  # type: ignore[no-untyped-def]
        """When sqlcipher3 is NOT available, a warning is logged."""
        import logging

        db_path = str(tmp_path / "fallback.db")
        with caplog.at_level(logging.WARNING):
            conn = create_encrypted_connection(db_path, passphrase="test")
            conn.close()
        assert "NOT encrypted" in caplog.text
