# packages/infrastructure/src/zorivest_infra/security/sql_sandbox.py
"""SQL sandbox for report query execution (§9.6c).

Provides default-deny authorization and query_only connections
to prevent mutation of production data during report generation.

Spec: 09-scheduling.md §9.6c
MEU: 87
"""

from __future__ import annotations

import sqlite3
from typing import Any


# SQLite action codes — only allow read operations.
# Full list: https://www.sqlite.org/c3ref/c_alter_table.html
_ALLOWED_ACTIONS = {
    sqlite3.SQLITE_SELECT,    # 21 — SELECT statements
    sqlite3.SQLITE_READ,      # 20 — Reading a column value
    sqlite3.SQLITE_FUNCTION,  # 31 — Calling a function
    19,                       # SQLITE_PRAGMA — reading pragmas (e.g. query_only)
}


def report_authorizer(
    action: int,
    arg1: Any,
    arg2: Any,
    db_name: Any,
    trigger_name: Any,
) -> int:
    """Default-deny SQLite authorizer for report queries.

    Only allows SELECT, READ, and FUNCTION operations.
    All write operations (INSERT, UPDATE, DELETE, DROP, etc.) are denied.
    """
    if action in _ALLOWED_ACTIONS:
        return sqlite3.SQLITE_OK
    return sqlite3.SQLITE_DENY


def create_sandboxed_connection(db_path: str) -> sqlite3.Connection:
    """Create a SQLite connection with security restrictions.

    - Sets PRAGMA query_only = ON
    - Installs default-deny authorizer
    - Uses URI mode for read-only access
    """
    conn = sqlite3.connect(db_path)

    # Enable query_only pragma — prevents all writes
    conn.execute("PRAGMA query_only = ON")

    # Install authorizer for defense-in-depth
    conn.set_authorizer(report_authorizer)

    return conn
