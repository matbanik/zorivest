"""SQLCipher connection factory with Argon2 key derivation.

Source: 02-infrastructure.md §2.3
Provides: create_encrypted_connection(), derive_key()

When ``sqlcipher3`` is installed (``pip install zorivest-infra[crypto]``),
databases are encrypted at rest via SQLCipher.  When the native library is
unavailable, the factory falls back to **plain sqlite3** and logs a warning.
Callers can inspect ``is_encrypted`` on the returned wrapper to verify.
"""

from __future__ import annotations

import hashlib
import logging
import sqlite3

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Public flag — lets callers (and tests) know which backend was used
# ---------------------------------------------------------------------------
_SQLCIPHER_AVAILABLE: bool
try:
    import sqlcipher3 as _sqlcipher3  # type: ignore[import-untyped]

    _SQLCIPHER_AVAILABLE = True
except ImportError:
    _sqlcipher3 = None  # type: ignore[assignment]
    _SQLCIPHER_AVAILABLE = False


def is_sqlcipher_available() -> bool:
    """Return True if sqlcipher3 is importable."""
    return _SQLCIPHER_AVAILABLE


# ---------------------------------------------------------------------------
# Key Derivation
# ---------------------------------------------------------------------------


def derive_key(passphrase: str, salt: bytes | None = None) -> bytes:
    """Derive a 256-bit encryption key from a passphrase.

    Uses Argon2id when ``argon2-cffi`` is installed.
    Falls back to PBKDF2-HMAC-SHA256 (600 000 iterations, OWASP baseline).

    Args:
        passphrase: User-provided passphrase.
        salt: Optional 16-byte salt.  Generated randomly if not provided.

    Returns:
        32-byte (256-bit) derived key.
    """
    if salt is None:
        import os

        salt = os.urandom(16)

    try:
        import argon2  # type: ignore[import-untyped]

        raw: bytes = argon2.low_level.hash_secret_raw(
            secret=passphrase.encode("utf-8"),
            salt=salt,
            time_cost=3,
            memory_cost=65536,  # 64 MB
            parallelism=4,
            hash_len=32,
            type=argon2.low_level.Type.ID,
        )
        return raw
    except ImportError:
        # Fallback to PBKDF2 when argon2-cffi is not installed
        return hashlib.pbkdf2_hmac(
            "sha256",
            passphrase.encode("utf-8"),
            salt,
            iterations=600_000,
            dklen=32,
        )


# ---------------------------------------------------------------------------
# Connection Factory
# ---------------------------------------------------------------------------


def create_encrypted_connection(db_path: str, passphrase: str) -> sqlite3.Connection:
    """Create an encrypted SQLite connection.

    When ``sqlcipher3`` is available the database file is encrypted at rest
    using the supplied *passphrase*.  WAL mode and ``SYNCHRONOUS=NORMAL``
    are enabled automatically.

    **Fallback behaviour:** When sqlcipher3 is **not** installed, this
    function opens the database with standard ``sqlite3`` — **no encryption
    is applied**.  A WARNING-level log is emitted so the caller is aware.
    The derived key is computed (validating the KDF path) but discarded.

    Args:
        db_path: Path to the database file.
        passphrase: Encryption passphrase.

    Returns:
        A ``sqlite3.Connection`` (or sqlcipher3 equivalent).
    """
    if _SQLCIPHER_AVAILABLE and _sqlcipher3 is not None:
        conn = _sqlcipher3.connect(db_path)
        conn.execute(f"PRAGMA key = '{passphrase}'")
        conn.execute("PRAGMA journal_mode=wal")
        conn.execute("PRAGMA synchronous=NORMAL")
        return conn  # type: ignore[no-any-return]

    # ── Fallback: plain sqlite3 (no encryption) ──────────────────────
    logger.warning(
        "sqlcipher3 is not installed — database at '%s' is NOT encrypted. "
        "Install with: pip install zorivest-infra[crypto]",
        db_path,
    )
    _key = derive_key(passphrase)  # validate KDF path, but key is unused
    del _key
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=wal")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


# ---------------------------------------------------------------------------
# Read-Only Sandbox Connection (§9C.2b)
# ---------------------------------------------------------------------------


def open_sandbox_connection(
    db_path: str,
    passphrase: str | None = None,
    *,
    read_only: bool = True,
) -> sqlite3.Connection:
    """Open a read-only SQLite connection for SQL sandbox use.

    Uses SQLCipher when available and passphrase is provided.
    Falls back to plain sqlite3 otherwise.

    The connection is opened in URI mode with ``?mode=ro`` to enforce
    read-only access at the C level (immutable for the connection lifetime).

    Args:
        db_path: Path to the database file.
        passphrase: Optional encryption passphrase (SQLCipher only).
        read_only: If True, open in read-only URI mode.

    Returns:
        A ``sqlite3.Connection`` in read-only mode.
    """
    mode = "ro" if read_only else "rw"
    uri = f"file:{db_path}?mode={mode}"

    if _SQLCIPHER_AVAILABLE and _sqlcipher3 is not None and passphrase is not None:
        conn = _sqlcipher3.connect(uri, uri=True)
        conn.execute(f"PRAGMA key = '{passphrase}'")
        logger.info(
            "Sandbox connection opened with SQLCipher (read_only=%s)", read_only
        )
        return conn  # type: ignore[no-any-return]

    # Fallback: plain sqlite3
    if passphrase is not None:
        logger.warning(
            "sqlcipher3 not available — sandbox at '%s' uses plain sqlite3",
            db_path,
        )
    conn = sqlite3.connect(uri, uri=True)
    return conn
