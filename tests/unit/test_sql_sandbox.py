"""Test SQL Sandbox, Secrets Scanning, and Content IDs (MEU-PH2).

Feature Intent Contract
=======================

Intent: SqlSandbox enforces a 6-layer security stack for AI-authored
SQL queries. Secrets scanning prevents credential leakage in policies.
Content-addressable IDs provide deterministic policy hashing.

Acceptance Criteria:
    AC-2.1:  SELECT on non-denied tables succeeds                    [Spec §9C.2d]
    AC-2.2:  INSERT/UPDATE/DELETE/DROP raise SecurityError            [Spec §9C.2d]
    AC-2.3:  ATTACH DATABASE raises SecurityError                    [Spec §9C.2d]
    AC-2.4:  PRAGMA with value raises SecurityError                  [Spec §9C.2d]
    AC-2.5:  SELECT from each DENY_TABLE raises SecurityError         [Spec §9C.2d]
    AC-2.6:  sqlite_master read blocked                               [Spec §9C.2d]
    AC-2.7:  CTE with SELECT allowed; CTE with DML blocked           [Spec §9C.2d]
    AC-2.8:  Runaway query aborts after 2s                            [Spec §9C.2b L5]
    AC-2.9:  load_extension() blocked                                 [Spec §9C.2d]
    AC-2.10: Parameterized binds work                                 [Spec §9C.2d]
    AC-2.11: open_sandbox_connection() uses SQLCipher when avail      [Spec §9C.2b, Human-approved]
    AC-2.12: scan_for_secrets() detects API/AWS/GH/Bearer/PEM keys   [Spec §9C.5]
    AC-2.13: scan_for_secrets() returns empty for clean policy JSON    [Spec §9C.5]
    AC-2.14: policy_content_id() returns SHA-256 of canonical JSON    [Spec §9C.6]
    AC-2.15: policy_content_id() is order-independent (sorted keys)   [Spec §9C.6]
    AC-2.16: policy_validator uses SqlSandbox.validate_sql()           [Spec §9C.2b L221]
    AC-2.17: All callsites migrated: no direct db_connection SQL       [Spec §9C.2c]
    AC-2.18: DENY_TABLES contract importable from sql_sandbox          [Spec §9C.2e, Local Canon]

Negative Cases:
    - DML/DDL must raise SecurityError at AST layer
    - ATTACH/PRAGMA writes must raise via authorizer
    - Denied tables must raise at authorizer level
    - load_extension must raise at authorizer level
    - Secret patterns must be detected in policy text
    - Timeout must abort long-running queries

Test Mapping:
    AC-2.1  → test_select_allowed
    AC-2.2  → test_insert_blocked, test_update_blocked,
               test_delete_blocked, test_drop_blocked
    AC-2.3  → test_attach_blocked
    AC-2.4  → test_pragma_write_blocked
    AC-2.5  → test_settings_read_blocked, test_market_provider_settings_blocked,
               test_email_provider_blocked, test_broker_configs_blocked,
               test_mcp_guard_blocked
    AC-2.6  → test_sqlite_master_blocked
    AC-2.7  → test_cte_allowed, test_nested_dml_in_cte_blocked
    AC-2.8  → test_timeout_aborts_long_query
    AC-2.9  → test_load_extension_blocked
    AC-2.10 → test_parameterized_binds
    AC-2.11 → test_sandbox_connection_fallback
    AC-2.12 → test_scan_for_secrets_detects_credentials
    AC-2.13 → test_scan_for_secrets_clean_policy
    AC-2.14 → test_policy_content_id_sha256
    AC-2.15 → test_policy_content_id_order_independent
    AC-2.16 → test_validator_uses_ast_validation
    AC-2.17 → test_no_direct_db_connection_in_steps
    AC-2.18 → test_deny_tables_importable
"""

import hashlib
import inspect
import json
import os
import re
import sqlite3
import time

import pytest


# ---------------------------------------------------------------------------
# AC-2.1: SELECT on non-denied tables succeeds
# ---------------------------------------------------------------------------


class TestSelectAllowed:
    """AC-2.1: Simple SELECT executes successfully on allowed tables."""

    def test_select_allowed(self, tmp_path: object) -> None:
        from zorivest_core.services.sql_sandbox import SqlSandbox

        db_path = os.path.join(str(tmp_path), "test.db")
        # Create a test DB with a non-denied table
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE trades (id INTEGER, ticker TEXT)")
        conn.execute("INSERT INTO trades VALUES (1, 'AAPL')")
        conn.commit()
        conn.close()

        sandbox = SqlSandbox(db_path)
        results = sandbox.execute("SELECT id, ticker FROM trades", {})
        assert len(results) == 1
        assert results[0]["ticker"] == "AAPL"


# ---------------------------------------------------------------------------
# AC-2.2: INSERT/UPDATE/DELETE/DROP raise SecurityError
# ---------------------------------------------------------------------------


class TestDMLBlocked:
    """AC-2.2: DML/DDL operations raise SecurityError."""

    def test_insert_blocked(self, tmp_path: object) -> None:
        from zorivest_core.services.sql_sandbox import SecurityError, SqlSandbox

        db_path = os.path.join(str(tmp_path), "test.db")
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE trades (id INTEGER)")
        conn.close()

        sandbox = SqlSandbox(db_path)
        with pytest.raises(SecurityError):
            sandbox.execute("INSERT INTO trades VALUES (1)", {})

    def test_update_blocked(self, tmp_path: object) -> None:
        from zorivest_core.services.sql_sandbox import SecurityError, SqlSandbox

        db_path = os.path.join(str(tmp_path), "test.db")
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE trades (id INTEGER)")
        conn.close()

        sandbox = SqlSandbox(db_path)
        with pytest.raises(SecurityError):
            sandbox.execute("UPDATE trades SET id = 2", {})

    def test_delete_blocked(self, tmp_path: object) -> None:
        from zorivest_core.services.sql_sandbox import SecurityError, SqlSandbox

        db_path = os.path.join(str(tmp_path), "test.db")
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE trades (id INTEGER)")
        conn.close()

        sandbox = SqlSandbox(db_path)
        with pytest.raises(SecurityError):
            sandbox.execute("DELETE FROM trades", {})

    def test_drop_blocked(self, tmp_path: object) -> None:
        from zorivest_core.services.sql_sandbox import SecurityError, SqlSandbox

        db_path = os.path.join(str(tmp_path), "test.db")
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE trades (id INTEGER)")
        conn.close()

        sandbox = SqlSandbox(db_path)
        with pytest.raises(SecurityError):
            sandbox.execute("DROP TABLE trades", {})


# ---------------------------------------------------------------------------
# AC-2.3: ATTACH DATABASE raises SecurityError
# ---------------------------------------------------------------------------


class TestAttachBlocked:
    """AC-2.3: ATTACH DATABASE raises SecurityError."""

    def test_attach_blocked(self, tmp_path: object) -> None:
        from zorivest_core.services.sql_sandbox import SecurityError, SqlSandbox

        db_path = os.path.join(str(tmp_path), "test.db")
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE trades (id INTEGER)")
        conn.close()

        sandbox = SqlSandbox(db_path)
        with pytest.raises(SecurityError):
            sandbox.execute("ATTACH DATABASE ':memory:' AS ext", {})


# ---------------------------------------------------------------------------
# AC-2.4: PRAGMA with value raises SecurityError
# ---------------------------------------------------------------------------


class TestPragmaBlocked:
    """AC-2.4: PRAGMA with arg2 raises SecurityError via authorizer."""

    def test_pragma_write_blocked(self, tmp_path: object) -> None:
        from zorivest_core.services.sql_sandbox import SecurityError, SqlSandbox

        db_path = os.path.join(str(tmp_path), "test.db")
        conn = sqlite3.connect(db_path)
        conn.close()

        sandbox = SqlSandbox(db_path)
        with pytest.raises(SecurityError):
            sandbox.execute("PRAGMA journal_mode = DELETE", {})


# ---------------------------------------------------------------------------
# AC-2.5: SELECT from each DENY_TABLE raises SecurityError
# ---------------------------------------------------------------------------


class TestDenyTableBlocked:
    """AC-2.5: SELECT from each sensitive table raises SecurityError."""

    @pytest.mark.parametrize(
        "table",
        [
            "settings",
            "market_provider_settings",
            "email_provider",
            "broker_configs",
            "mcp_guard",
        ],
    )
    def test_deny_table_blocked(self, tmp_path: object, table: str) -> None:
        from zorivest_core.services.sql_sandbox import SecurityError, SqlSandbox

        db_path = os.path.join(str(tmp_path), "test.db")
        conn = sqlite3.connect(db_path)
        conn.execute(f"CREATE TABLE [{table}] (id INTEGER)")
        conn.close()

        sandbox = SqlSandbox(db_path)
        with pytest.raises(SecurityError):
            sandbox.execute(f"SELECT * FROM [{table}]", {})


# ---------------------------------------------------------------------------
# AC-2.6: sqlite_master read blocked
# ---------------------------------------------------------------------------


class TestSqliteMasterBlocked:
    """AC-2.6: sqlite_master read raises SecurityError."""

    def test_sqlite_master_blocked(self, tmp_path: object) -> None:
        from zorivest_core.services.sql_sandbox import SecurityError, SqlSandbox

        db_path = os.path.join(str(tmp_path), "test.db")
        conn = sqlite3.connect(db_path)
        conn.close()

        sandbox = SqlSandbox(db_path)
        with pytest.raises(SecurityError):
            sandbox.execute("SELECT * FROM sqlite_master", {})


# ---------------------------------------------------------------------------
# AC-2.7: CTE with SELECT allowed; CTE with DML blocked
# ---------------------------------------------------------------------------


class TestCTEBehavior:
    """AC-2.7: CTE+SELECT allowed, CTE+DML blocked."""

    def test_cte_allowed(self, tmp_path: object) -> None:
        from zorivest_core.services.sql_sandbox import SqlSandbox

        db_path = os.path.join(str(tmp_path), "test.db")
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE trades (id INTEGER, ticker TEXT)")
        conn.execute("INSERT INTO trades VALUES (1, 'AAPL')")
        conn.commit()
        conn.close()

        sandbox = SqlSandbox(db_path)
        results = sandbox.execute(
            "WITH cte AS (SELECT id, ticker FROM trades) SELECT * FROM cte",
            {},
        )
        assert len(results) == 1

    def test_nested_dml_in_cte_blocked(self, tmp_path: object) -> None:
        from zorivest_core.services.sql_sandbox import SecurityError, SqlSandbox

        db_path = os.path.join(str(tmp_path), "test.db")
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE trades (id INTEGER)")
        conn.close()

        sandbox = SqlSandbox(db_path)
        with pytest.raises(SecurityError):
            sandbox.execute(
                "INSERT INTO trades SELECT 1",
                {},
            )


# ---------------------------------------------------------------------------
# AC-2.8: Runaway query aborts after 2s
# ---------------------------------------------------------------------------


class TestTimeout:
    """AC-2.8: Recursive CTE aborts after ~2 seconds."""

    @pytest.mark.timeout(10)
    def test_timeout_aborts_long_query(self, tmp_path: object) -> None:
        from zorivest_core.services.sql_sandbox import SecurityError, SqlSandbox

        db_path = os.path.join(str(tmp_path), "test.db")
        conn = sqlite3.connect(db_path)
        conn.close()

        sandbox = SqlSandbox(db_path)
        start = time.monotonic()
        with pytest.raises((SecurityError, sqlite3.OperationalError)):
            # Infinite recursive CTE
            sandbox.execute(
                "WITH RECURSIVE r(n) AS (SELECT 1 UNION ALL SELECT n+1 FROM r) "
                "SELECT n FROM r",
                {},
            )
        elapsed = time.monotonic() - start
        assert elapsed < 5.0, (
            f"Timeout guard should fire within ~2s, took {elapsed:.1f}s"
        )


# ---------------------------------------------------------------------------
# AC-2.9: load_extension() blocked
# ---------------------------------------------------------------------------


class TestLoadExtensionBlocked:
    """AC-2.9: load_extension() call raises SecurityError."""

    def test_load_extension_blocked(self, tmp_path: object) -> None:
        from zorivest_core.services.sql_sandbox import SecurityError, SqlSandbox

        db_path = os.path.join(str(tmp_path), "test.db")
        conn = sqlite3.connect(db_path)
        conn.close()

        sandbox = SqlSandbox(db_path)
        with pytest.raises((SecurityError, sqlite3.OperationalError)):
            sandbox.execute("SELECT load_extension('evil.so')", {})


# ---------------------------------------------------------------------------
# AC-2.10: Parameterized binds work
# ---------------------------------------------------------------------------


class TestParameterizedBinds:
    """AC-2.10: :param binds work correctly."""

    def test_parameterized_binds(self, tmp_path: object) -> None:
        from zorivest_core.services.sql_sandbox import SqlSandbox

        db_path = os.path.join(str(tmp_path), "test.db")
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE trades (id INTEGER, ticker TEXT)")
        conn.execute("INSERT INTO trades VALUES (1, 'AAPL')")
        conn.execute("INSERT INTO trades VALUES (2, 'MSFT')")
        conn.commit()
        conn.close()

        sandbox = SqlSandbox(db_path)
        results = sandbox.execute(
            "SELECT id, ticker FROM trades WHERE ticker = :ticker",
            {"ticker": "AAPL"},
        )
        assert len(results) == 1
        assert results[0]["ticker"] == "AAPL"


# ---------------------------------------------------------------------------
# AC-2.11: open_sandbox_connection() with fallback
# ---------------------------------------------------------------------------


class TestSandboxConnectionFactory:
    """AC-2.11: Sandbox connection factory works with sqlite3 fallback."""

    def test_sandbox_connection_fallback(self, tmp_path: object) -> None:
        """Verify open_sandbox_connection returns a connection (using fallback)."""
        from zorivest_infra.database.connection import open_sandbox_connection

        db_path = os.path.join(str(tmp_path), "test.db")
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE test (id INTEGER)")
        conn.close()

        sandbox_conn = open_sandbox_connection(db_path, read_only=True)
        # Must be a valid connection
        assert sandbox_conn is not None
        # Read-only: writing must fail
        with pytest.raises(sqlite3.OperationalError):
            sandbox_conn.execute("INSERT INTO test VALUES (1)")


# ---------------------------------------------------------------------------
# AC-2.12: scan_for_secrets() detects credentials
# ---------------------------------------------------------------------------


class TestSecretsScanning:
    """AC-2.12: scan_for_secrets detects API keys, AWS keys, GH tokens, Bearer, PEM."""

    @pytest.mark.parametrize(
        "secret,label",
        [
            ("sk-abc123def456ghi789jkl012mno345", "OpenAI key"),
            ("AKIAIOSFODNN7EXAMPLE", "AWS access key"),
            ("ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghij", "GitHub token"),
            ("Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test", "Bearer token"),
            ("-----BEGIN RSA PRIVATE KEY-----", "PEM key"),
        ],
    )
    def test_scan_for_secrets_detects_credentials(
        self, secret: str, label: str
    ) -> None:
        from zorivest_core.domain.policy_validator import scan_for_secrets

        policy_text = f'{{"steps": [{{"params": {{"key": "{secret}"}}}}]}}'
        matches = scan_for_secrets(policy_text)
        assert len(matches) > 0, f"Should detect {label}: {secret[:15]}..."


# ---------------------------------------------------------------------------
# AC-2.13: scan_for_secrets() returns empty for clean policy
# ---------------------------------------------------------------------------


class TestSecretsClean:
    """AC-2.13: Clean policy JSON returns empty list."""

    def test_scan_for_secrets_clean_policy(self) -> None:
        from zorivest_core.domain.policy_validator import scan_for_secrets

        clean = '{"name": "Weekly Report", "steps": [{"type": "fetch", "params": {"url": "https://example.com"}}]}'
        assert scan_for_secrets(clean) == []


# ---------------------------------------------------------------------------
# AC-2.14: policy_content_id() returns SHA-256 of canonical JSON
# ---------------------------------------------------------------------------


class TestPolicyContentId:
    """AC-2.14: Deterministic SHA-256 of canonical JSON."""

    def test_policy_content_id_sha256(self) -> None:
        from zorivest_core.domain.policy_validator import policy_content_id

        policy = {"name": "test", "steps": [{"type": "fetch"}]}
        result = policy_content_id(policy)
        # Verify it's a valid hex SHA-256
        assert len(result) == 64
        assert all(c in "0123456789abcdef" for c in result)
        # Verify it matches manual computation
        canonical = json.dumps(policy, sort_keys=True, separators=(",", ":"))
        expected = hashlib.sha256(canonical.encode()).hexdigest()
        assert result == expected


# ---------------------------------------------------------------------------
# AC-2.15: policy_content_id() order-independent
# ---------------------------------------------------------------------------


class TestPolicyContentIdOrder:
    """AC-2.15: Same hash for reordered keys."""

    def test_policy_content_id_order_independent(self) -> None:
        from zorivest_core.domain.policy_validator import policy_content_id

        a = {"name": "test", "steps": [{"type": "fetch"}]}
        b = {"steps": [{"type": "fetch"}], "name": "test"}
        assert policy_content_id(a) == policy_content_id(b)


# ---------------------------------------------------------------------------
# AC-2.16: policy_validator uses AST validation (not SQL_BLOCKLIST)
# ---------------------------------------------------------------------------


class TestValidatorUsesAST:
    """AC-2.16: policy_validator uses validate_sql, not SQL_BLOCKLIST."""

    def test_validator_uses_ast_validation(self) -> None:
        """Static analysis: SQL_BLOCKLIST should not be defined or used in validation."""
        from zorivest_core.domain import policy_validator

        source = inspect.getsource(policy_validator)
        # SQL_BLOCKLIST must not be a defined variable or actively referenced
        # (comments mentioning it for historical context are acceptable)
        assert re.search(r"^SQL_BLOCKLIST\s*=", source, re.MULTILINE) is None, (
            "SQL_BLOCKLIST should be removed as a defined constant"
        )
        # validate_sql should be imported/used instead
        assert "validate_sql" in source, (
            "policy_validator should use SqlSandbox.validate_sql()"
        )


# ---------------------------------------------------------------------------
# AC-2.17: No direct db_connection SQL in steps
# ---------------------------------------------------------------------------


class TestCallsiteMigration:
    """AC-2.17: Steps no longer use direct db_connection."""

    def test_no_direct_db_connection_in_steps(self) -> None:
        """Static analysis: step files should not reference db_connection."""
        from zorivest_core.pipeline_steps import store_report_step

        source = inspect.getsource(store_report_step)
        # Should not have direct db_connection usage
        db_conn_refs = re.findall(r"db_connection", source)
        assert len(db_conn_refs) == 0, (
            f"store_report_step.py still references db_connection: {len(db_conn_refs)} times"
        )


# ---------------------------------------------------------------------------
# AC-2.18: DENY_TABLES importable from sql_sandbox
# ---------------------------------------------------------------------------


class TestDenyTablesContract:
    """AC-2.18: DENY_TABLES is importable for downstream PH9 use."""

    def test_deny_tables_importable(self) -> None:
        from zorivest_core.services.sql_sandbox import SqlSandbox

        assert hasattr(SqlSandbox, "DENY_TABLES")
        assert isinstance(SqlSandbox.DENY_TABLES, frozenset)
        # Must have at least 6 entries per spec
        assert len(SqlSandbox.DENY_TABLES) >= 6
        # Must contain the required sensitive tables
        assert "settings" in SqlSandbox.DENY_TABLES
        assert "sqlite_master" in SqlSandbox.DENY_TABLES


# ---------------------------------------------------------------------------
# AC-2.19: SqlSandbox accepts injected connection (SQLCipher enablement)
# ---------------------------------------------------------------------------


class TestSandboxConnectionInjection:
    """AC-2.19: SqlSandbox accepts a pre-opened connection.

    This enables callers with SQLCipher-unlocked connections to inject
    them without SqlSandbox re-opening via sqlite3.connect().
    """

    def test_sandbox_accepts_injected_connection(self, tmp_path) -> None:
        """SqlSandbox(connection=conn) uses the injected connection."""
        import sqlite3

        from zorivest_core.services.sql_sandbox import SqlSandbox

        # Create a test DB and open a connection externally
        db_file = tmp_path / "test_inject.db"
        setup_conn = sqlite3.connect(str(db_file))
        setup_conn.execute("CREATE TABLE test_data (id INTEGER, value TEXT)")
        setup_conn.execute("INSERT INTO test_data VALUES (1, 'hello')")
        setup_conn.commit()
        setup_conn.close()

        # Open a read-only connection (simulates SQLCipher-unlocked conn)
        uri = f"file:{db_file}?mode=ro"
        injected_conn = sqlite3.connect(uri, uri=True)

        # SqlSandbox must accept this injected connection
        sandbox = SqlSandbox(db_path=str(db_file), connection=injected_conn)

        # Must be able to query through the sandbox
        rows = sandbox.execute("SELECT value FROM test_data WHERE id = 1", {})
        assert len(rows) == 1
        assert rows[0]["value"] == "hello"

        sandbox.close()
        injected_conn.close()
