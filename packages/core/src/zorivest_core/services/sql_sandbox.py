"""Read-only SQL execution sandbox for AI-authored queries (§9C.2b).

Provides a 6-layer security stack:
    L1: sqlite3.Connection.set_authorizer() — C-level deny on tables/ATTACH/PRAGMA/extensions
    L2: mode=ro SQLite URI — read-only at connection open (immutable)
    L3: PRAGMA query_only = ON — defense-in-depth write block
    L4: PRAGMA trusted_schema = OFF — prevent untrusted view/trigger execution
    L5: progress_handler(callback, 50_000) — 2-second timeout cap
    L6: sqlglot AST allowlist — pre-parse: reject DML/DDL/Command nodes

Also provides:
    SecurityError — raised when SQL is blocked by any layer
"""

from __future__ import annotations

import sqlite3
import time
from typing import Any

import sqlglot
from sqlglot import exp
from sqlglot.errors import SqlglotError


class SecurityError(Exception):
    """Raised when SQL sandbox blocks an operation."""


class SqlSandbox:
    """Read-only SQL execution sandbox for AI-authored queries.

    Per §9C.2b: connection uses read-only mode + authorizer + AST validation.
    The DENY_TABLES frozenset is the shared contract consumed by PH9 for
    schema-discovery filtering.
    """

    # Actual table names from zorivest_infra.database.models
    DENY_TABLES: frozenset[str] = frozenset(
        {
            # Credential / auth tables
            "settings",  # Contains encrypted API keys, OAuth tokens
            "market_provider_settings",  # API keys, auth tokens for market data
            "email_provider",  # SMTP credentials
            "broker_configs",  # Broker API credentials
            "mcp_guard",  # MCP confirmation tokens
            # SQLite internals
            "sqlite_master",
            "sqlite_schema",
            "sqlite_temp_master",
        }
    )

    def __init__(
        self,
        db_path: str,
        connection: sqlite3.Connection | None = None,
    ) -> None:
        """Open a sandboxed read-only connection.

        Args:
            db_path: Path to the SQLite database file.
            connection: Optional pre-opened connection (e.g. SQLCipher-unlocked).
                        When provided, the sandbox uses this connection instead
                        of opening one via sqlite3.connect().
        """
        if connection is not None:
            self._conn = connection
        else:
            # L2: Read-only URI mode
            uri = f"file:{db_path}?mode=ro"
            self._conn = sqlite3.connect(uri, uri=True)

        # L3-L4: Set PRAGMAs BEFORE authorizer (authorizer blocks PRAGMA writes)
        self._conn.execute("PRAGMA query_only = ON")
        self._conn.execute("PRAGMA trusted_schema = OFF")

        # L1: Authorizer callback (installed after PRAGMAs to allow setup)
        self._conn.set_authorizer(self._authorizer_callback)

        # L5: Progress handler for timeout (2 seconds)
        self._start_time = 0.0
        self._conn.set_progress_handler(self._check_timeout, 50_000)

    def _authorizer_callback(
        self,
        action: int,
        arg1: str | None,
        arg2: str | None,
        db_name: str | None,
        trigger: str | None,
    ) -> int:
        """L1: C-level authorizer — blocks dangerous operations."""
        # Block ATTACH DATABASE
        if action == sqlite3.SQLITE_ATTACH:
            return sqlite3.SQLITE_DENY

        # Block PRAGMA writes (arg2 is the value being set)
        if action == sqlite3.SQLITE_PRAGMA and arg2 is not None:
            return sqlite3.SQLITE_DENY

        # Block reads on denied tables
        if action == sqlite3.SQLITE_READ and arg1 in self.DENY_TABLES:
            return sqlite3.SQLITE_DENY

        # Block load_extension
        if action == sqlite3.SQLITE_FUNCTION and arg1 == "load_extension":
            return sqlite3.SQLITE_DENY

        return sqlite3.SQLITE_OK

    def validate_sql(self, sql: str) -> list[str]:
        """L6: AST-level validation via sqlglot.

        Only SELECT/WITH/UNION/Subquery/CTE/Paren are allowed.
        All DML, DDL, and Command nodes are rejected.

        Returns:
            List of error messages. Empty list means SQL is valid.
        """
        try:
            parsed = sqlglot.parse(sql, dialect="sqlite")
        except SqlglotError as e:
            return [f"SQL parse error: {e}"]

        errors: list[str] = []
        for stmt in parsed:
            if stmt is None:
                continue
            for node in stmt.walk():
                if isinstance(node, exp.Command):
                    errors.append(f"Command statement blocked: {node.key}")
                if isinstance(
                    node,
                    (
                        exp.Insert,
                        exp.Update,
                        exp.Delete,
                        exp.Drop,
                        exp.Create,
                        exp.Alter,
                    ),
                ):
                    errors.append(f"DML/DDL blocked: {type(node).__name__}")
        return errors

    def execute(self, sql: str, binds: dict[str, Any]) -> list[dict[str, Any]]:
        """Execute SQL in the sandbox with all security layers.

        Args:
            sql: The SQL query to execute.
            binds: Named parameter bindings (e.g., {":param": value}).

        Returns:
            List of dicts, one per row, with column-name keys.

        Raises:
            SecurityError: If any security layer blocks the query.
        """
        # L6: AST validation first
        errors = self.validate_sql(sql)
        if errors:
            raise SecurityError(f"SQL blocked: {errors}")

        # L5: Reset timeout start
        self._start_time = time.monotonic()

        try:
            cursor = self._conn.execute(sql, binds)
        except (sqlite3.OperationalError, sqlite3.DatabaseError) as e:
            error_msg = str(e)
            if "not authorized" in error_msg or "query_only" in error_msg:
                raise SecurityError(f"SQL blocked by authorizer: {error_msg}") from e
            raise SecurityError(f"SQL execution error: {error_msg}") from e

        if cursor.description is None:
            return []

        columns = [d[0] for d in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def _check_timeout(self) -> int:
        """L5: Progress handler — abort after 2 seconds."""
        if time.monotonic() - self._start_time > 2.0:
            return 1  # non-zero aborts the operation
        return 0

    def close(self) -> None:
        """Close the sandbox connection."""
        self._conn.close()
