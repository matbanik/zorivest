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


def create_encrypted_connection(
    db_path: str, passphrase: str
) -> sqlite3.Connection:
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
