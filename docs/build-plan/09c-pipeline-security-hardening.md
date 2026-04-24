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

def safe_deepcopy(obj: object) -> object:
    """Deep-copy with depth and byte guards to prevent DoS."""
    estimated = sys.getsizeof(obj)
    if estimated > MAX_DEEPCOPY_BYTES:
        raise ValueError(f"Object too large for deep-copy: {estimated} bytes > {MAX_DEEPCOPY_BYTES}")
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

### 9C.1d Exit Criteria

- [ ] `safe_copy.py` exists with `Secret` + `safe_deepcopy`
- [ ] `StepContext.get_output()` uses `safe_deepcopy()`
- [ ] `StepContext.put()` (or `PipelineRunner._persist_step()`) uses `safe_deepcopy()`
- [ ] All 6 tests pass
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
| L1 | `sqlite3.Connection.set_authorizer()` | C-level: deny READ on `encrypted_keys`, `auth_users`, `sqlite_master`, `sqlite_schema`; deny ATTACH, PRAGMA write, load_extension |
| L2 | `mode=ro` SQLite URI parameter | C-level: read-only at connection open (immutable) |
| L3 | `PRAGMA query_only = ON` | Defense-in-depth: redundant write block |
| L4 | `PRAGMA trusted_schema = OFF` | Prevent untrusted view/trigger execution |
| L5 | `progress_handler(callback, 50_000)` | 2-second timeout cap on runaway queries |
| L6 | sqlglot AST **allowlist** | Pre-parse: only `{Select, With, Union, Subquery, CTE, Paren}` allowed; reject `exp.Command` and all DML |

```python
class SqlSandbox:
    """Read-only SQL execution sandbox for AI-authored queries."""

    DENY_TABLES = frozenset({
        "encrypted_keys", "auth_users", "sqlite_master",
        "sqlite_schema", "sqlite_temp_master",
    })

    def __init__(self, db_path: str):
        self._conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
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
| `connection.py` (infra) | Add `open_sandbox_connection(db_path) -> SqlSandbox` factory |
| `policy_validator.py` | Replace `SQL_BLOCKLIST` set with `SqlSandbox.validate_sql()` calls |
| `pipeline_runner.py` | Inject `sql_sandbox` into `context.outputs` alongside `db_connection` |
| `main.py` (API) | Wire `SqlSandbox` creation in lifespan |

**New dependency:** `sqlglot` (add to `pyproject.toml`)

### 9C.2c Tests

New file: `tests/unit/test_sql_sandbox.py`

| Test | Assertion |
|------|-----------|
| `test_select_allowed` | Simple SELECT executes successfully |
| `test_insert_blocked` | INSERT raises `SecurityError` |
| `test_update_blocked` | UPDATE raises `SecurityError` |
| `test_delete_blocked` | DELETE raises `SecurityError` |
| `test_drop_blocked` | DROP TABLE raises `SecurityError` |
| `test_attach_blocked` | ATTACH DATABASE raises `SecurityError` |
| `test_pragma_write_blocked` | PRAGMA with arg2 raises `SecurityError` |
| `test_sensitive_table_read_blocked` | SELECT from `encrypted_keys` raises `SecurityError` |
| `test_sqlite_master_blocked` | SELECT from `sqlite_master` raises `SecurityError` |
| `test_cte_allowed` | WITH + SELECT executes successfully |
| `test_nested_dml_in_cte_blocked` | CTE containing INSERT raises `SecurityError` |
| `test_timeout_aborts_long_query` | Recursive CTE aborts after 2 seconds |
| `test_load_extension_blocked` | `load_extension()` call raises `SecurityError` |
| `test_parameterized_binds` | `:param` binds work correctly |

### 9C.2d Exit Criteria

- [ ] `sql_sandbox.py` exists with all 6 security layers
- [ ] `connection.py` has `open_sandbox_connection()` factory
- [ ] `policy_validator.py` uses AST allowlist (not string blocklist)
- [ ] All 14 tests pass
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
