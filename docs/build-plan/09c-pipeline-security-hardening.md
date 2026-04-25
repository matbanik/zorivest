# 09c — Pipeline Security Hardening

> Phase: P2.5c · MEU-PH1, MEU-PH2, MEU-PH3
> Prerequisites: P2.5b wiring complete (MEU-PW1→PW13 ✅)
> Unblocks: QueryStep (09d), Template DB (09e), Policy Emulator (09f)
> Resolves: [PIPE-MUTCTX], [PIPE-NOSANDBOX]
> Source: [retail-trader-policy-use-cases.md](../../_inspiration/policy_pipeline_wiring-research/retail-trader-policy-use-cases.md) Gaps A, B, B+
> Status: ⬜ planned

---

## 9C.1 StepContext Deep-Copy Boundary (MEU-PH1)

### 9C.1a Problem

[`pipeline.py:159–177`](file:///p:/zorivest/packages/core/src/zorivest_core/domain/pipeline.py#L159-L177) — `StepContext.outputs` is a mutable `dict[str, Any]`. `get_output()` returns direct references. Steps can mutate upstream outputs without detection.

**Why dangerous:** A `transform` step that modifies a list in-place silently corrupts what a downstream `compose` or `render` step sees. In financial reporting, this means wrong P&L numbers in emailed reports.

### 9C.1b Fix — `safe_copy.py`

New module: `packages/core/src/zorivest_core/services/safe_copy.py`

**`Secret` carrier class** — credentials must never traverse `StepContext`. Injected via closure at FetchStep call time only.

```python
import copy
import sys

class Secret:
    """Opaque credential wrapper — prevents leakage into StepContext or logs."""
    __slots__ = ("_value",)

    def __init__(self, value: str):
        object.__setattr__(self, "_value", value)

    def reveal(self) -> str:
        return self._value

    def __str__(self) -> str:
        raise RuntimeError("Secret must not be stringified — use .reveal() explicitly")

    def __repr__(self) -> str:
        return "Secret(***)"

    def __format__(self, format_spec: str) -> str:
        return "<REDACTED>"

    def __deepcopy__(self, memo: dict) -> "Secret":
        raise RuntimeError("Secret must not be deep-copied into StepContext")


MAX_DEEPCOPY_DEPTH = 64
MAX_DEEPCOPY_BYTES = 10 * 1024 * 1024  # 10 MB

def _estimate_size_recursive(obj: object, depth: int = 0, seen: set | None = None) -> int:
    """Walk object graph to estimate total size with cycle and depth protection."""
    if depth > MAX_DEEPCOPY_DEPTH:
        raise ValueError(f"Object nesting depth exceeds {MAX_DEEPCOPY_DEPTH}")
    if seen is None:
        seen = set()
    obj_id = id(obj)
    if obj_id in seen:
        return 0  # cycle — already counted
    seen.add(obj_id)
    total = sys.getsizeof(obj)
    if isinstance(obj, dict):
        for k, v in obj.items():
            total += _estimate_size_recursive(k, depth + 1, seen)
            total += _estimate_size_recursive(v, depth + 1, seen)
    elif isinstance(obj, (list, tuple, set, frozenset)):
        for item in obj:
            total += _estimate_size_recursive(item, depth + 1, seen)
    elif hasattr(obj, '__dict__'):
        total += _estimate_size_recursive(vars(obj), depth + 1, seen)
    return total

def safe_deepcopy(obj: object) -> object:
    """Deep-copy with recursive depth, aggregate byte, and Secret guards."""
    total_bytes = _estimate_size_recursive(obj)
    if total_bytes > MAX_DEEPCOPY_BYTES:
        raise ValueError(f"Object too large for deep-copy: {total_bytes} bytes > {MAX_DEEPCOPY_BYTES}")
    return copy.deepcopy(obj)
```

**Changes to existing files:**

| File | Change |
|------|--------|
| `pipeline.py` (L173) | `get_output()` returns `safe_deepcopy(self.outputs[step_id])` |
| `pipeline_runner.py` (L240) | `put()` stores `safe_deepcopy(value)` |

### 9C.1c Tests

New file: `tests/unit/test_stepcontext_isolation.py`

| Test | Assertion |
|------|-----------|
| `test_get_output_returns_isolated_copy` | Mutating returned value does NOT change stored value |
| `test_put_stores_isolated_copy` | Mutating original after `put()` does NOT change stored value |
| `test_secret_blocks_stringify` | `str(Secret("x"))` raises `RuntimeError` |
| `test_secret_blocks_deepcopy` | `copy.deepcopy(Secret("x"))` raises `RuntimeError` |
| `test_secret_reveal` | `Secret("x").reveal() == "x"` |
| `test_safe_deepcopy_rejects_oversized` | Objects > 10 MB raise `ValueError` |
| `test_safe_deepcopy_rejects_deep_nesting` | 65-deep nested dict raises `ValueError` |
| `test_safe_deepcopy_handles_cycles` | Cyclic reference does not infinite-loop |
| `test_safe_deepcopy_secret_in_nested_obj` | Dict containing `Secret` raises on deepcopy |

### 9C.1d Exit Criteria

- [ ] `safe_copy.py` exists with `Secret` + `safe_deepcopy` + `_estimate_size_recursive`
- [ ] `StepContext.get_output()` uses `safe_deepcopy()`
- [ ] `StepContext.put()` (or `PipelineRunner._persist_step()`) uses `safe_deepcopy()`
- [ ] All 9 tests pass
- [ ] No existing tests break

---

## 9C.2 SQL Sandbox (MEU-PH2)

### 9C.2a Problem

[`pipeline_runner.py:80`](file:///p:/zorivest/packages/core/src/zorivest_core/services/pipeline_runner.py#L80) — single `db_connection` kwarg injected into `context.outputs`. [`store_report_step.py:58`](file:///p:/zorivest/packages/core/src/zorivest_core/pipeline_steps/store_report_step.py#L58) calls `_execute_sandboxed_sql()` on the same trusted connection used for writes. [`policy_validator.py:34–43`](file:///p:/zorivest/packages/core/src/zorivest_core/domain/policy_validator.py#L34-L43) — SQL blocklist is string-match only.

**Why dangerous:** AI-authored SQL in a `query` step runs on the trusted app connection. A missed keyword bypasses the string blocklist. `ATTACH DATABASE` can mount external files. Recursive CTEs and nested DML bypass any blocklist approach.

### 9C.2b Fix — `sql_sandbox.py`

New module: `packages/core/src/zorivest_core/services/sql_sandbox.py`

> [!CAUTION]
> **`set_authorizer` is the PRIMARY control** (validated by Claude, Gemini, ChatGPT independently). It operates at the SQLite C-level, sees inside CTEs, subqueries, views, and triggers at prepare-time.

**Security Control Stack (layered, all mandatory):**

| Layer | Control | Purpose |
|:-----:|---------|---------|
| L1 | `sqlite3.Connection.set_authorizer()` | C-level: deny READ on all tables in `SqlSandbox.DENY_TABLES` plus `sqlite_master`, `sqlite_schema`; deny ATTACH, PRAGMA write, load_extension |
| L2 | `mode=ro` SQLite URI parameter | C-level: read-only at connection open (immutable) |
| L3 | `PRAGMA query_only = ON` | Defense-in-depth: redundant write block |
| L4 | `PRAGMA trusted_schema = OFF` | Prevent untrusted view/trigger execution |
| L5 | `progress_handler(callback, 50_000)` | 2-second timeout cap on runaway queries |
| L6 | sqlglot AST **allowlist** | Pre-parse: only `{Select, With, Union, Subquery, CTE, Paren}` allowed; reject `exp.Command` and all DML |

```python
class SqlSandbox:
    """Read-only SQL execution sandbox for AI-authored queries.

    Connection uses SQLCipher via open_sandbox_connection() factory,
    which derives the read-only key from the existing DEK. See
    packages/infrastructure/src/zorivest_infra/database/connection.py.
    """

    # Actual table names from zorivest_infra.database.models
    DENY_TABLES = frozenset({
        # Credential / auth tables
        "settings",                 # Contains encrypted API keys, OAuth tokens
        "market_provider_settings", # API keys, auth tokens for market data
        "email_provider",           # SMTP credentials
        "broker_configs",           # Broker API credentials
        "mcp_guard",                # MCP confirmation tokens
        # SQLite internals
        "sqlite_master", "sqlite_schema", "sqlite_temp_master",
    })

    def __init__(self, db_path: str, key: bytes):
        # SQLCipher-aware read-only connection
        self._conn = open_sandbox_connection(db_path, key, read_only=True)
        self._conn.set_authorizer(self._authorizer_callback)
        self._conn.execute("PRAGMA query_only = ON")
        self._conn.execute("PRAGMA trusted_schema = OFF")
        self._start_time = 0.0
        self._conn.set_progress_handler(self._check_timeout, 50_000)

    def _authorizer_callback(self, action, arg1, arg2, db_name, trigger):
        import sqlite3
        if action == sqlite3.SQLITE_ATTACH:
            return sqlite3.SQLITE_DENY
        if action == sqlite3.SQLITE_PRAGMA and arg2 is not None:
            return sqlite3.SQLITE_DENY
        if action == sqlite3.SQLITE_READ and arg1 in self.DENY_TABLES:
            return sqlite3.SQLITE_DENY
        if action == sqlite3.SQLITE_FUNCTION and arg1 == "load_extension":
            return sqlite3.SQLITE_DENY
        return sqlite3.SQLITE_OK

    def validate_sql(self, sql: str) -> list[str]:
        import sqlglot
        from sqlglot import exp
        parsed = sqlglot.parse(sql, dialect="sqlite")
        errors = []
        for stmt in parsed:
            for node in stmt.walk():
                if isinstance(node, exp.Command):
                    errors.append(f"Command statement blocked: {node.key}")
                if isinstance(node, (exp.Insert, exp.Update, exp.Delete,
                                     exp.Drop, exp.Create, exp.Alter)):
                    errors.append(f"DML/DDL blocked: {node.key}")
        return errors

    def execute(self, sql: str, binds: dict) -> list[dict]:
        errors = self.validate_sql(sql)
        if errors:
            raise SecurityError(f"SQL blocked: {errors}")
        self._start_time = time.monotonic()
        cursor = self._conn.execute(sql, binds)
        columns = [d[0] for d in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def _check_timeout(self) -> int:
        if time.monotonic() - self._start_time > 2.0:
            return 1
        return 0
```

**Changes to existing files:**

| File | Change |
|------|--------|
| `connection.py` (infra) | Add `open_sandbox_connection(db_path, key, read_only=True) -> SqlSandbox` factory |
| `policy_validator.py` | Replace `SQL_BLOCKLIST` set with `SqlSandbox.validate_sql()` calls |
| `pipeline_runner.py` | Replace `db_connection` with `sql_sandbox` in `context.outputs` (steps no longer access raw connection) |
| `main.py` (API) | Wire `SqlSandbox` creation in lifespan |

**New dependency:** `sqlglot` (add to `pyproject.toml`)

### 9C.2c Callsite Migration (Mandatory)

> [!CAUTION]
> The sandbox is incomplete unless ALL policy-authored SQL is routed through it.

| Callsite | Current Path | Required Change |
|----------|-------------|------------------|
| `StoreReportStep._execute_sandboxed_sql()` | Uses trusted `db_connection` from context | Replace with `sql_sandbox.execute()`. Remove `_execute_sandboxed_sql` method entirely. |
| `CriteriaResolver._resolve_db_query()` | Builds SQL from policy criteria, executes on trusted connection | Replace with `sql_sandbox.execute()`. CriteriaResolver receives `sql_sandbox` from context, not `db_connection`. |
| `pipeline_runner.py` context injection | Exposes raw `db_connection` to steps via `context.outputs` | Replace `db_connection` with `sql_sandbox` in step-accessible context. Only `sql_sandbox` is available to steps. The runner's own persistence uses `db_connection` internally (not exposed to steps). |

### 9C.2d Tests

New file: `tests/unit/test_sql_sandbox.py`

> [!NOTE]
> Deny table expansion is merged into the canonical `DENY_TABLES` above.
> There is no separate addendum — the snippet is the single source of truth.

| Test | Assertion |
|------|-----------|
| `test_select_allowed` | Simple SELECT executes successfully |
| `test_insert_blocked` | INSERT raises `SecurityError` |
| `test_update_blocked` | UPDATE raises `SecurityError` |
| `test_delete_blocked` | DELETE raises `SecurityError` |
| `test_drop_blocked` | DROP TABLE raises `SecurityError` |
| `test_attach_blocked` | ATTACH DATABASE raises `SecurityError` |
| `test_pragma_write_blocked` | PRAGMA with arg2 raises `SecurityError` |
| `test_settings_read_blocked` | SELECT from `settings` raises `SecurityError` |
| `test_sqlite_master_blocked` | SELECT from `sqlite_master` raises `SecurityError` |
| `test_cte_allowed` | WITH + SELECT executes successfully |
| `test_nested_dml_in_cte_blocked` | CTE containing INSERT raises `SecurityError` |
| `test_timeout_aborts_long_query` | Recursive CTE aborts after 2 seconds |
| `test_load_extension_blocked` | `load_extension()` call raises `SecurityError` |
| `test_parameterized_binds` | `:param` binds work correctly |
| `test_market_provider_settings_blocked` | SELECT from `market_provider_settings` raises `SecurityError` |
| `test_email_provider_blocked` | SELECT from `email_provider` raises `SecurityError` |
| `test_broker_configs_blocked` | SELECT from `broker_configs` raises `SecurityError` |
| `test_mcp_guard_blocked` | SELECT from `mcp_guard` raises `SecurityError` |

#### Schema-Discovery Security Tests

These tests validate that `DENY_TABLES` filtering is enforced at the backend
schema-discovery layer, not just at SQL execution time. Owner: MEU-PH9.

| Test | Assertion |
|------|-----------|
| `test_db_schema_endpoint_excludes_denied_tables` | `GET /scheduling/db-schema` response contains zero entries for any table in `SqlSandbox.DENY_TABLES` |
| `test_list_db_tables_excludes_denied_tables` | MCP `list_db_tables` output contains zero entries for any table in `SqlSandbox.DENY_TABLES` |
| `test_get_db_row_samples_rejects_denied_table` | MCP `get_db_row_samples(table_name="settings")` returns error, not rows |
| `test_db_schema_resource_excludes_denied_tables` | MCP `pipeline://db-schema` resource output contains zero entries for any table in `SqlSandbox.DENY_TABLES` |

### 9C.2e Backend Schema-Discovery Route

The MCP `pipeline://db-schema` resource and `list_db_tables` tool both fetch
`GET /scheduling/db-schema`. This route is owned by the scheduling API router
(MEU-PH9) and **must** filter `SqlSandbox.DENY_TABLES` server-side.

```python
# packages/api/src/zorivest_api/routes/scheduling.py (MEU-PH9)
# Externally reachable as: GET /api/v1/scheduling/db-schema
# (scheduling_router prefix = "/api/v1/scheduling")

from zorivest_infra.database.sql_sandbox import SqlSandbox

@scheduling_router.get("/db-schema")
async def get_db_schema(db: Session = Depends(get_db)):
    """Return table/column metadata for query-step SQL authoring.

    Filters SqlSandbox.DENY_TABLES to prevent schema discovery of
    sensitive tables (credentials, guard tokens, etc.).
    """
    all_tables = inspect(db.bind).get_table_names()
    safe_tables = [t for t in all_tables if t not in SqlSandbox.DENY_TABLES]
    schema = []
    for table_name in safe_tables:
        columns = inspect(db.bind).get_columns(table_name)
        schema.append({
            "name": table_name,
            "columns": [{"name": c["name"], "type": str(c["type"]), "nullable": c["nullable"]} for c in columns]
        })
    return schema
```

> [!IMPORTANT]
> The backend route is the security boundary — MCP resources/tools are thin
> fetch wrappers. If the backend leaks denied tables, MCP-side filtering alone
> cannot compensate because the fetch response is already tainted.

### 9C.2f Exit Criteria

- [ ] `sql_sandbox.py` exists with all 6 security layers
- [ ] `connection.py` has `open_sandbox_connection()` factory
- [ ] `policy_validator.py` uses AST allowlist (not string blocklist)
- [ ] All callsites migrated — no direct `db_connection` SQL in steps
- [ ] `DENY_TABLES` covers all sensitive tables (6+ entries)
- [ ] All 20 tests pass (16 sandbox + 4 schema-discovery security)
- [ ] `GET /scheduling/db-schema` filters `SqlSandbox.DENY_TABLES` server-side
- [ ] `sqlglot` added to dependencies

---

## 9C.3 SendStep Confirmation Gate (MEU-PH3)

### 9C.3a Problem

SendStep can execute email delivery without any user approval. In an agent-first workflow, a hijacked prompt could compose a policy that exfiltrates data via email.

### 9C.3b Fix

Add `requires_confirmation: bool = True` to `SendStep.Params`. If `True` and no interactive UI confirmation is available, raise `PolicyExecutionError`.

```python
class SendStep(RegisteredStep):
    class Params(BaseModel):
        requires_confirmation: bool = True  # default safe

    async def execute(self, params, context):
        p = self.Params(**params)
        if p.requires_confirmation and not context.has_user_confirmation:
            raise PolicyExecutionError(
                "SendStep requires user confirmation. "
                "Set requires_confirmation=False only for pre-approved templates."
            )
```

**File changes:** `send_step.py` (add param + gate check), `pipeline.py` (add `has_user_confirmation: bool = False` to `StepContext`)

### 9C.3c Approval Provenance Contract

> [!IMPORTANT]
> `requires_confirmation=False` is only honored when the policy has a stored approval record.
> Without this, a malicious policy can set the opt-out flag and bypass confirmation.

```python
if not p.requires_confirmation:
    if not context.policy_approval:
        raise PolicyExecutionError(
            "requires_confirmation=False requires a stored policy approval record. "
            "Use POST /api/v1/scheduling/policies/{id}/approve first."
        )
    if context.policy_approval.content_hash != context.policy_hash:
        raise PolicyExecutionError(
            "Policy content has changed since approval. Re-approve before executing."
        )
```

The `PolicyApproval` record stores:
- `policy_id`, `content_hash` (SHA-256 of policy JSON), `approved_at`, `approved_by` (user or "system")
- Approval is invalidated when the policy is updated (content_hash changes)

---

## 9C.4 FetchStep Content-Type Validation (MEU-PH3)

### 9C.4a Problem

FetchStep accepts any response content regardless of MIME type. A malicious provider could return HTML/JS instead of JSON, potentially enabling downstream template injection.

### 9C.4b Fix

Add MIME validation and body size cap to `FetchStep.execute()`:

```python
EXPECTED_MIME = {"quote": "application/json", "ohlcv": "application/json",
                 "news": "application/json", "fundamentals": "application/json"}
MAX_FETCH_BODY_BYTES = 5 * 1024 * 1024  # 5 MB

# After response received:
content_type = response.headers.get("content-type", "").split(";")[0].strip()
expected = EXPECTED_MIME.get(data_type, "application/json")
if content_type != expected:
    raise SecurityError(f"MIME mismatch: expected {expected}, got {content_type}")
if len(response.content) > MAX_FETCH_BODY_BYTES:
    raise SecurityError(f"Response body exceeds {MAX_FETCH_BODY_BYTES} bytes")
```

Add fan-out cap: max 5 URLs per step, max 10 per policy execution.

**File changes:** `fetch_step.py` (add MIME check + fan-out cap)

### 9C.4c Tests (MEU-PH3)

| Test | Assertion |
|------|-----------|
| `test_send_requires_confirmation` | SendStep raises if `requires_confirmation=True` and no UI |
| `test_send_allows_when_confirmed` | SendStep proceeds if `has_user_confirmation=True` |
| `test_send_allows_when_opt_out` | SendStep proceeds if `requires_confirmation=False` |
| `test_fetch_rejects_mime_mismatch` | Non-JSON response raises `SecurityError` |
| `test_fetch_rejects_oversized_body` | >5 MB response raises `SecurityError` |
| `test_fetch_fan_out_cap` | >5 URLs in single step raises validation error |

### 9C.4d Exit Criteria

- [ ] SendStep has `requires_confirmation` field with gate logic
- [ ] StepContext has `has_user_confirmation: bool` field
- [ ] FetchStep validates MIME type and body size
- [ ] FetchStep enforces fan-out cap (5 URLs/step, 10/policy)
- [ ] All 6 tests pass

---

## 9C.5 Secrets Scanning

Co-delivered with MEU-PH2. Regex guard on policy text before save or emulation.

```python
import re

_SECRETS_PATTERN = re.compile(
    r"(sk-[a-zA-Z0-9]{20,}"
    r"|AKIA[0-9A-Z]{16}"
    r"|ghp_[a-zA-Z0-9]{36}"
    r"|Bearer\s+[a-zA-Z0-9\-._~+/]+=*"
    r"|-----BEGIN.*PRIVATE KEY-----"
    r")"
)

def scan_for_secrets(policy_json: str) -> list[str]:
    matches = _SECRETS_PATTERN.findall(policy_json)
    if matches:
        return [f"Possible credential detected: {m[:10]}..." for m in matches]
    return []
```

**File changes:** Add to `policy_validator.py` validation chain.

---

## 9C.6 Content-Addressable Policy IDs

Co-delivered with MEU-PH2. SHA-256 of canonical JSON for audit trail and TOCTOU prevention.

```python
import hashlib, json

def policy_content_id(policy: dict) -> str:
    canonical = json.dumps(policy, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()
```

**File changes:** Add to `pipeline_runner.py` — compute and log at run start.
