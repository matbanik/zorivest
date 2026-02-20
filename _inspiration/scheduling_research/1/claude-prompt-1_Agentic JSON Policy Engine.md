# Scheduling & pipeline system for a local-first desktop app

**A single-process Electron + Python/FastAPI application needs a pipeline engine where AI agents author JSON "policy documents" that define multi-step data workflows.** The optimal design combines Windmill-style explicit input transforms with Pydantic discriminated unions for schema validation, an `__init_subclass__` step registry exposed via MCP-compatible manifests, and a lightweight sequential async executor with SQLite-persisted state. This architecture avoids distributed-systems complexity while giving AI agents a discoverable, strongly-typed interface for composing pipelines. The sections below present a complete design: schema, registry, executor, edge cases, security, and saga adaptation — all scoped to a single-process, single-user, SQLite-backed desktop app.

---

## 1. JSON policy schema that machines write and humans read

The schema draws from **Windmill's OpenFlow** (explicit `input_transforms` per step referencing prior outputs) and **n8n's flat node array** (scannable, each step a self-contained object). It avoids Airflow's XCom indirection and Temporal's code-only approach, since the goal is a declarative JSON document an LLM generates and a human edits in Monaco/CodeMirror.

### Annotated example policy

```json
{
  "$schema": "https://myapp.local/schemas/pipeline/v1.json",
  "schema_version": 1,
  "metadata": {
    "id": "pol_7f3a9c2e",
    "name": "Daily Portfolio Report",
    "description": "Fetches positions, aggregates by sector, renders HTML report, emails to user",
    "author": { "type": "ai_agent", "model": "claude-sonnet-4-20250514", "session": "sess_abc123" },
    "created_at": "2026-02-19T08:30:00Z",
    "version": 3,
    "tags": ["daily", "portfolio", "email"]
  },
  "schedule": {
    "cron": "0 7 * * 1-5",
    "timezone": "America/New_York",
    "misfire_grace_seconds": 3600,
    "coalesce": true,
    "enabled": true
  },
  "defaults": {
    "timeout_seconds": 60,
    "retry": { "max_attempts": 2, "backoff_seconds": 5, "backoff_multiplier": 2.0 }
  },
  "steps": [
    {
      "id": "fetch_prices",
      "type": "fetch",
      "description": "Get latest equity prices from market data API",
      "params": {
        "url": "https://api.marketdata.example/v1/quotes",
        "method": "GET",
        "headers": { "Authorization": "Bearer {{secrets.market_data_key}}" },
        "query_params": { "symbols": "{{inputs.watchlist}}" }
      },
      "timeout_seconds": 30,
      "retry": { "max_attempts": 3, "backoff_seconds": 2, "backoff_multiplier": 2.0 },
      "on_error": "fail_pipeline"
    },
    {
      "id": "aggregate_positions",
      "type": "sql_query",
      "description": "Aggregate portfolio positions by sector with latest prices",
      "params": {
        "query": "SELECT sector, SUM(quantity * :price_factor) AS exposure FROM positions GROUP BY sector",
        "bind_params": { "price_factor": "{{steps.fetch_prices.output.adjustment_factor}}" },
        "max_rows": 500
      },
      "input_refs": { "price_data": "{{steps.fetch_prices.output}}" },
      "on_error": "fail_pipeline"
    },
    {
      "id": "render_report",
      "type": "render",
      "description": "Generate HTML email body from Jinja2 template",
      "params": {
        "template_name": "portfolio_daily.html.j2",
        "context_vars": {
          "positions": "{{steps.aggregate_positions.output.rows}}",
          "prices": "{{steps.fetch_prices.output.quotes}}",
          "report_date": "{{runtime.date_iso}}"
        },
        "output_format": "html"
      },
      "on_error": "fail_pipeline"
    },
    {
      "id": "send_report",
      "type": "send_email",
      "description": "Email the rendered report",
      "params": {
        "to": ["user@example.com"],
        "subject": "Portfolio Report — {{runtime.date_iso}}",
        "body_html": "{{steps.render_report.output.rendered}}"
      },
      "on_error": "log_and_continue",
      "conditions": { "skip_if": "{{steps.aggregate_positions.output.row_count == 0}}" }
    }
  ],
  "inputs": {
    "watchlist": { "type": "string", "default": "AAPL,MSFT,GOOG", "description": "Comma-separated ticker symbols" }
  }
}
```

### Design decisions behind each field

**Document-level fields.** `schema_version` is an integer that increments on breaking changes — the executor checks it and rejects unknown versions. `metadata.author` captures whether a human or AI created the policy and which model, forming the first link in the audit chain. `metadata.version` is a per-document revision counter, incremented on every edit.

**Schedule block.** Maps directly to APScheduler's `CronTrigger` with `misfire_grace_time` and `coalesce` exposed as policy-level settings rather than hidden in code. The `timezone` field accepts IANA zone names. The `enabled` flag lets the GUI toggle scheduling without deleting the cron expression.

**Step structure.** Each step is a flat object with `id` (machine-stable), `type` (discriminator for the step registry), `description` (human context), `params` (type-specific), `timeout_seconds`, `retry`, `on_error`, and optional `conditions`. This mirrors **n8n's node structure** — flat, scannable, self-contained — while adding Windmill's explicit `input_refs` for cross-step data references.

**Data passing: the `{{steps.<id>.output}}` expression pattern.** Inspired by Windmill's `input_transforms` with `results.<step_id>`, every parameter value can contain mustache-style expressions that reference prior step outputs, pipeline inputs, runtime variables, or secrets. At execution time, the engine resolves these from the accumulated context dict. This is more explicit than Airflow's XCom (where you pull by task_id in code) and more readable than n8n's `$node["Name"].json.field` syntax. The expression syntax doubles as documentation — a reader sees exactly where data flows.

**Error handling per step.** `on_error` accepts `fail_pipeline` (halt and mark run as failed), `log_and_continue` (record error, proceed to next step), or `retry_then_fail` (exhaust retries, then fail). This is simpler than Airflow's `trigger_rule` system but covers the practical cases for a 4-step pipeline.

**Conditional execution.** The `conditions.skip_if` field accepts a boolean expression evaluated against the context. This handles the common case of "don't send an empty report" without requiring a full branching DAG.

### Schema versioning strategy

Follow the **additive-only** pattern used by Airflow's serialization schema and n8n's `typeVersion`:

- **Non-breaking changes** (new optional fields with defaults): increment `metadata.version`, keep `schema_version` unchanged. The executor ignores unknown fields.
- **Breaking changes** (removed fields, changed semantics): increment `schema_version`. The executor maintains handlers for each schema version. Old policies are migrated forward on load via a `migrate(policy, from_version, to_version)` function chain.
- **Per-step type versioning**: Each step type in the registry carries a version. If a step type's parameter schema changes incompatibly, bump the step type version. Policies that reference the old version are flagged for migration.

### Validation split: creation-time vs execution-time

**Creation-time** (when the AI agent submits or human saves): full Pydantic schema validation, step type existence check, expression syntax parsing (not evaluation), policy allowlist enforcement (max steps, allowed types, recipient limits), DAG integrity check (no circular `input_refs`), SQL safety analysis via keyword blocklist.

**Execution-time** (when the scheduler fires): re-validate schema hash integrity (detect tampering), resolve secret references (verify they exist), evaluate `conditions.skip_if` expressions, check rate limits, verify step types still exist in registry (handles schema evolution where a step was removed after policy creation).

---

## 2. Step type registry with auto-discovery and AI exposure

The registry combines Python's `__init_subclass__` for zero-boilerplate auto-registration with Pydantic models for parameter schemas, exposed to AI agents as MCP-compatible tool definitions.

### Core registry pattern

```python
from __future__ import annotations
from abc import abstractmethod
from typing import Any, ClassVar
from pydantic import BaseModel
import json

class StepBase:
    """Base class for pipeline steps. Subclasses auto-register."""

    _registry: ClassVar[dict[str, type[StepBase]]] = {}

    # Subclasses must define these class variables:
    step_name: ClassVar[str]
    step_version: ClassVar[int]
    Params: ClassVar[type[BaseModel]]

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if hasattr(cls, "step_name") and hasattr(cls, "Params"):
            StepBase._registry[cls.step_name] = cls

    @abstractmethod
    async def execute(
        self, params: BaseModel, context: dict[str, Any], dry_run: bool = False
    ) -> Any:
        """Execute step. Return value stored as step output in context."""
        ...

    async def compensate(self, context: dict[str, Any]) -> None:
        """Optional: undo side effects on pipeline failure."""
        pass

    # --- Registry API ---

    @classmethod
    def get(cls, name: str) -> type[StepBase]:
        if name not in cls._registry:
            raise StepTypeNotFound(f"Unknown step type: {name}")
        return cls._registry[name]

    @classmethod
    def manifest(cls) -> list[dict]:
        """Generate MCP-compatible capability manifest for AI agents."""
        return [
            {
                "name": step_cls.step_name,
                "version": step_cls.step_version,
                "description": (step_cls.Params.__doc__ or step_cls.__doc__ or ""),
                "inputSchema": step_cls.Params.model_json_schema(),
            }
            for step_cls in cls._registry.values()
        ]
```

### Concrete step type example

```python
from pydantic import BaseModel, Field
from typing import Literal

class FetchParams(BaseModel):
    """Fetch JSON data from an HTTP API endpoint."""
    url: str = Field(description="Full URL to fetch")
    method: Literal["GET", "POST"] = Field(default="GET")
    headers: dict[str, str] = Field(default_factory=dict)
    query_params: dict[str, str] = Field(default_factory=dict)

class FetchStep(StepBase):
    step_name = "fetch"
    step_version = 1
    Params = FetchParams

    async def execute(self, params: FetchParams, context, dry_run=False):
        if dry_run:
            return {"mock": True, "url": params.url, "status": 200}
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.request(
                params.method, params.url,
                headers=params.headers, params=params.query_params,
            )
            resp.raise_for_status()
            return resp.json()
```

### Exposing the registry to AI agents via MCP

The TypeScript MCP server (thin REST proxy) calls a FastAPI endpoint that returns the manifest:

```python
# FastAPI route
@router.get("/api/pipeline/step-types")
async def list_step_types():
    return {"tools": StepBase.manifest()}
```

The MCP server translates this into the MCP `tools/list` response. Each step's `inputSchema` is a JSON Schema object generated by Pydantic's `model_json_schema()`, which maps directly to MCP's tool `inputSchema` field. When an AI agent in an IDE calls `tools/list`, it receives something like:

```json
{
  "tools": [
    {
      "name": "fetch",
      "version": 1,
      "description": "Fetch JSON data from an HTTP API endpoint.",
      "inputSchema": {
        "type": "object",
        "properties": {
          "url": {"type": "string", "description": "Full URL to fetch"},
          "method": {"enum": ["GET", "POST"], "default": "GET", "type": "string"},
          "headers": {"type": "object", "additionalProperties": {"type": "string"}}
        },
        "required": ["url"]
      }
    }
  ]
}
```

The agent sees all available step types, their descriptions, and the exact parameter shapes it must produce. This is the same pattern Windmill uses — derive JSON Schema from typed function signatures — but using Pydantic instead of Windmill's runtime introspection.

**Extensibility model.** Adding a new step type requires one file: define a `Params` model and a `StepBase` subclass. Import the file (or place it in a `steps/` directory scanned at startup), and `__init_subclass__` auto-registers it. No configuration files, no manual registry calls. For the desktop app context, entry points and dynamic plugin discovery are unnecessary complexity — a simple import-time registry suffices.

---

## 3. Pipeline execution engine architecture

### Text-based architecture diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│  APScheduler (AsyncIOScheduler)                                      │
│  ┌─────────────────────┐                                             │
│  │ SQLAlchemyJobStore   │  Persists jobs to SQLCipher                │
│  │ (SQLCipher DB)       │  coalesce=True, max_instances=1            │
│  └────────┬────────────┘                                             │
│           │ fires cron trigger                                       │
│           ▼                                                          │
│  ┌────────────────────┐     ┌──────────────────────┐                │
│  │ PipelineDispatcher  │────▶│ PolicyLoader          │                │
│  │ (async entrypoint)  │     │ - Load JSON from DB   │                │
│  └────────┬────────────┘     │ - Validate schema hash│                │
│           │                  │ - Check rate limits    │                │
│           │ validated        │ - Resolve secrets      │                │
│           │ policy           └──────────────────────┘                │
│           ▼                                                          │
│  ┌────────────────────────────────────────────────┐                  │
│  │ PipelineExecutor                                │                  │
│  │                                                 │                  │
│  │  context = {inputs: {...}, runtime: {...}}       │                  │
│  │                                                 │                  │
│  │  for step in policy.steps:                      │                  │
│  │    ┌───────────────────────────────────┐        │                  │
│  │    │ 1. Persist status → RUNNING       │        │                  │
│  │    │ 2. Resolve {{expressions}}        │        │                  │
│  │    │ 3. Validate params (Pydantic)     │        │                  │
│  │    │ 4. Execute with asyncio.timeout() │        │                  │
│  │    │ 5. Store output in context        │        │                  │
│  │    │ 6. Persist status → SUCCESS       │        │                  │
│  │    │ 7. Persist context snapshot        │        │                  │
│  │    └───────────────────────────────────┘        │                  │
│  │                                                 │                  │
│  │  on error: run compensations in reverse         │                  │
│  └─────────────────────┬──────────────────────────┘                  │
│                        │                                              │
│           ┌────────────┴────────────┐                                │
│           ▼                         ▼                                │
│  ┌─────────────┐          ┌──────────────┐                          │
│  │ StepRegistry │          │ State Store   │                          │
│  │ (in-memory)  │          │ (SQLCipher)   │                          │
│  │              │          │               │                          │
│  │ fetch ──────▶│ FetchStep│ pipeline_runs │                          │
│  │ sql_query ──▶│ SQLStep  │ pipeline_steps│                          │
│  │ render ─────▶│ RenderSt.│ audit_log     │                          │
│  │ send_email ─▶│ SendStep │               │                          │
│  └─────────────┘          └──────────────┘                          │
└──────────────────────────────────────────────────────────────────────┘

          │ Events (SSE or WebSocket)           ▲ REST API
          ▼                                     │
┌──────────────────────────────────────────────────────────────────────┐
│  Electron Frontend (React + TanStack Query)                          │
│  - Pipeline list, status, logs                                       │
│  - Monaco editor for policy JSON                                     │
│  - Run history with step-level status                                │
└──────────────────────────────────────────────────────────────────────┘
```

### Execution engine core implementation

```python
class PipelineExecutor:
    def __init__(self, db: AsyncSession, run_id: str, dry_run: bool = False):
        self.db = db
        self.run_id = run_id
        self.dry_run = dry_run
        self.completed_steps: list[StepBase] = []

    async def execute(self, policy: dict, resume_from: str | None = None):
        context = {
            "inputs": policy.get("inputs", {}),
            "runtime": {"date_iso": date.today().isoformat(), "run_id": self.run_id},
            "steps": {},
        }

        started = resume_from is None
        for step_def in policy["steps"]:
            if not started:
                if step_def["id"] == resume_from:
                    started = True
                    context = await self._load_persisted_context()
                else:
                    continue

            # Evaluate skip conditions
            if self._should_skip(step_def, context):
                await self._persist_status(step_def["id"], "SKIPPED")
                continue

            await self._persist_status(step_def["id"], "RUNNING")

            try:
                step_cls = StepBase.get(step_def["type"])
                resolved_params = self._resolve_expressions(step_def["params"], context)
                validated_params = step_cls.Params(**resolved_params)
                timeout = step_def.get("timeout_seconds", 60)

                async with asyncio.timeout(timeout):
                    output = await step_cls().execute(
                        validated_params, context, dry_run=self.dry_run
                    )

                context["steps"][step_def["id"]] = {"output": output}
                self.completed_steps.append(step_cls())
                await self._persist_status(step_def["id"], "SUCCESS")
                await self._persist_context(context)

            except Exception as e:
                await self._persist_status(step_def["id"], "FAILED", str(e))
                if step_def.get("on_error") == "log_and_continue":
                    continue
                await self._run_compensations(context)
                raise PipelineFailedError(step_def["id"], e)
```

**The context dict pattern** wins over explicit output mapping for this use case. Each step's output is stored at `context["steps"][step_id]["output"]`, and `{{steps.fetch_prices.output.quotes}}` expressions resolve against this dict. This is simpler than Windmill's JavaScript transform layer (overkill for a local app) and more explicit than Airflow's global XCom store.

**Resume from failure** loads the persisted context snapshot (saved after each successful step) and skips steps that already completed. The `pipeline_steps` table tracks which steps are `SUCCESS`, `FAILED`, or `PENDING`. On resume, the executor queries for the first non-`SUCCESS` step and replays from there with the accumulated context.

---

## 4. Comprehensive edge case catalog with mitigations

### Overlapping runs

**Problem:** Cron fires at 7:00 AM while yesterday's 7:00 AM run is still executing (e.g., slow API).
**Mitigation:** APScheduler's **`max_instances=1`** (the default) rejects the new execution as a misfire. Combined with `coalesce=True`, if multiple firings pile up, only one runs. Configuration:

```python
scheduler.add_job(run_pipeline, "cron", hour=7, max_instances=1, coalesce=True)
```

### Misfire on app restart

**Problem:** User closes the app at 6:50 AM, scheduled job was set for 7:00 AM, app reopens at 9:00 AM.
**Mitigation:** Use `SQLAlchemyJobStore` (persists jobs to SQLCipher) with **`misfire_grace_time=3600`** (1 hour). On restart, APScheduler checks `current_time - scheduled_time`: if within grace period, the job runs immediately; if past, it's skipped and logged. With `coalesce=True`, even if the app was off for multiple scheduled firings, only one execution occurs.

### Step idempotency

**Problem:** The `fetch` step runs twice (after a retry) — does it produce different results or duplicate records?
**Mitigation:** Fetch and SQL query steps are naturally **read-only and idempotent** — re-running them produces the same (or fresher) data. For the `send_email` step, which is **not** idempotent, guard with a **deduplication key**: store `SHA256(run_id + step_id + recipient + subject)` in a `sent_emails` table before sending, and check for existence before re-sending. This prevents duplicate emails on retry.

### Compensation and the email pivot transaction

**Problem:** Email was sent, but the underlying data was wrong (e.g., stale prices).
**Mitigation:** Email send is the **pivot transaction** — the point of no return. You cannot un-send an email. Design the pipeline so the send step is last. If data correctness is critical, add a **validation step** between render and send that checks data freshness (e.g., "prices are less than 15 minutes old"). For post-send discovery of bad data, the compensation path is a **follow-up correction email**, triggered manually or by a separate pipeline.

### API rate limits during fetch steps

**Problem:** Market data API returns 429 Too Many Requests.
**Mitigation:** Use **tenacity** with exponential backoff and jitter on the fetch step. Respect `Retry-After` headers. For a desktop app, a full circuit breaker is usually unnecessary — the fetch step runs once per scheduled execution, not continuously. Configuration:

```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential_jitter(initial=2, max=30, jitter=2),
    retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.ConnectTimeout)),
)
async def fetch_with_retry(url, headers): ...
```

### Schema evolution: removed or renamed step type

**Problem:** A policy references `step_type: "fetch_v1"` but the step was renamed to `"http_fetch"`.
**Mitigation:** Maintain an **alias map** in the registry: `{"fetch_v1": "http_fetch"}`. When loading a policy, resolve aliases before execution. Log a deprecation warning. For removed step types with no replacement, fail at **execution-time validation** (not silently) and surface the error to the user with a suggested fix. The `step_version` field on registry entries enables the executor to detect version mismatches.

### Circular dependencies in step references

**Problem:** Step A references `{{steps.B.output}}` and step B references `{{steps.A.output}}`.
**Mitigation:** At **creation-time validation**, parse all `{{steps.<id>.output}}` expressions, build a dependency graph, and run a **topological sort** (or simple cycle detection via DFS). Reject policies with cycles. Since the policy defines a linear step order (array), a simpler check suffices: verify that every `{{steps.X.output}}` reference in step N refers to a step that appears **before** N in the array.

### Resource exhaustion in long-running pipelines

**Problem:** A pipeline fetches 100MB of data, holds it in the context dict, and the single-process app's memory grows.
**Mitigation:** Set a **max context size** (e.g., 50MB). After each step, check `sys.getsizeof()` on the context. For large data, store intermediate results in **SQLite temp tables** rather than in-memory dicts, and pass table references through the context. The `sql_query` step should enforce `max_rows` (default 1000) to prevent unbounded result sets. For HTTP connections, use `httpx.AsyncClient` as a context manager so connections are released after each step.

### Timezone and DST transitions

**Problem:** A cron job scheduled for 2:30 AM local time during spring-forward — that time doesn't exist. During fall-back, 1:30 AM happens twice.
**Mitigation:** **Store and schedule in UTC internally.** Display local times in the GUI by converting from UTC using the user's timezone. If the user insists on local-time scheduling (e.g., "7 AM my time"), use APScheduler's timezone-aware `CronTrigger` but **avoid scheduling between 1:00–3:00 AM**. Set `misfire_grace_time=7200` (2 hours) so DST-shifted jobs still fire. `coalesce=True` prevents duplicate runs during fall-back.

### SQLite/SQLCipher locking during concurrent access

**Problem:** Pipeline writes step status to SQLite while the Electron GUI reads pipeline history.
**Mitigation:** Enable **WAL (Write-Ahead Logging) mode**, which allows concurrent readers and a single writer without blocking. WAL mode dramatically improves throughput — benchmarks show **462K select QPS** vs 30 QPS in default journal mode during concurrent read+write. Configuration order for SQLCipher matters:

```python
conn.execute("PRAGMA key='...'")          # Must be first for SQLCipher
conn.execute("PRAGMA journal_mode=WAL")    # After key
conn.execute("PRAGMA busy_timeout=5000")   # Wait up to 5s for locks
conn.execute("PRAGMA synchronous=NORMAL")  # Good safety/perf tradeoff
```

Use a **dedicated writer connection** for the pipeline executor and **separate read-only connections** for the GUI (`PRAGMA query_only=ON`).

---

## 5. Security guardrail checklist for AI-authored policies

The defense model borrows from the **MAPL paper's four-boundary framework** (prompts, tools, data, context) adapted for a local-first app where the threat model is primarily an LLM producing unintended or excessive operations, not adversarial multi-tenant attacks.

### Layer 1 — Schema validation (creation-time)

- **Pydantic discriminated union** validates every step against its type-specific schema with field constraints (`max_length`, `le`/`ge`, allowed `Literal` values)
- **Step type allowlist**: reject any `type` not in `StepBase._registry`
- **Pipeline-level limits**: max **10 steps** per pipeline, max **5 recipients** per email step, max **2 email steps** per pipeline, max **2000 characters** per SQL query
- **SQL keyword blocklist**: reject queries containing `DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, `ATTACH`, `PRAGMA`, `CREATE` at the Pydantic validator level (field-level `@field_validator`)
- **Expression syntax check**: parse all `{{...}}` expressions and verify they only reference known namespaces (`steps`, `inputs`, `runtime`, `secrets`)
- **Content hash**: compute `SHA-256` of the canonical JSON at creation time, store alongside the policy, verify at execution time

### Layer 2 — SQL sandboxing (execution-time)

The **SQLite authorizer callback** is the single highest-impact security control. It intercepts operations at compile time (during `sqlite3_prepare()`), making SQL injection bypass impossible:

```python
def read_only_authorizer(action, arg1, arg2, db_name, trigger_name):
    if action in (sqlite3.SQLITE_SELECT, sqlite3.SQLITE_READ):
        if ALLOWED_TABLES and arg1 not in ALLOWED_TABLES:
            return sqlite3.SQLITE_DENY
        return sqlite3.SQLITE_OK
    if action == sqlite3.SQLITE_FUNCTION:
        if arg2 in {"load_extension", "writefile"}:
            return sqlite3.SQLITE_DENY
        return sqlite3.SQLITE_OK
    return sqlite3.SQLITE_DENY  # Deny everything else (fail-closed)
```

This is an **allowlist** approach — default deny, explicitly permit only `SELECT`, `READ`, and safe functions. Open the database in read-only mode (`file:db.sqlite?mode=ro`) as additional defense-in-depth. Use a **separate connection** for AI-authored queries, never the application's writer connection.

### Layer 3 — Rate limiting (runtime)

Use an **in-memory token bucket** (or `pyrate-limiter` with SQLite persistence for survival across restarts):

- **Pipeline creation**: 20/day, burst of 5
- **Pipeline execution**: 60/hour, burst of 10
- **Email sends**: 50/day, burst of 5
- **SQL queries**: 100/hour, burst of 20

### Layer 4 — Audit trail (append-only)

Every action writes to an `audit_log` table with SQLite triggers preventing `UPDATE` and `DELETE`:

```sql
CREATE TABLE audit_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp       TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%f','now')),
    event_source    TEXT NOT NULL,  -- 'ai_agent' | 'user' | 'scheduler'
    action          TEXT NOT NULL,  -- 'pipeline.create' | 'step.execute' | 'policy.violation'
    pipeline_id     TEXT,
    execution_id    TEXT,
    step_id         TEXT,
    outcome         TEXT NOT NULL,  -- 'success' | 'denied' | 'error'
    input_hash      TEXT,           -- SHA-256 of step input
    duration_ms     INTEGER,
    metadata_json   TEXT
);

CREATE TRIGGER prevent_audit_update BEFORE UPDATE ON audit_log
BEGIN SELECT RAISE(ABORT, 'Audit records are immutable'); END;

CREATE TRIGGER prevent_audit_delete BEFORE DELETE ON audit_log
BEGIN SELECT RAISE(ABORT, 'Audit records are immutable'); END;
```

### Layer 5 — Human-in-the-loop for sensitive operations

Flag `send_email` and any new step types for **manual approval** on first execution of a new or modified policy. The GUI shows a confirmation dialog with the rendered email preview and recipient list. After the user approves, subsequent scheduled runs of the same (unmodified) policy execute without prompting. If the policy's content hash changes, re-approval is required.

### Applicability of MAPL to this context

The MAPL paper's full cryptographic attestation model (signed claims between distributed agents) is **overkill for a single-process local app** — there's no multi-tenant identity to verify and no network boundary between agents. However, three MAPL concepts translate directly. First, the **four-boundary model** (prompts, tools, data, context) provides a clean mental framework for where to place guardrails. Second, **hierarchical policy composition** — system defaults that can be narrowed (never widened) by user preferences — maps to a simple policy overlay: the system policy sets `max_recipients: 10`, the user can set `max_recipients: 5` but not `max_recipients: 20`. Third, **attestation as a precondition** simplifies to "each step must persist a SUCCESS record before the next step's `input_refs` can resolve."

---

## 6. Minimal saga implementation for single-process apps

### Why the full saga pattern is unnecessary here

The saga pattern solves a **distributed coordination problem**: maintaining consistency across multiple services with separate databases when ACID transactions can't span them. In a single-process app with one SQLite database, every condition that motivates sagas evaporates. There are no network partitions. There are no separate transaction coordinators. ACID transactions are available for all database operations. All steps run in the same event loop.

What **is** useful from the saga concept is the idea of **compensating actions** — but the implementation reduces to a simple try/except with a cleanup list.

### Minimal implementation

```python
@dataclass
class CompensatingStep:
    step_id: str
    execute: Callable[[dict, bool], Awaitable[Any]]
    compensate: Callable[[dict], Awaitable[None]] | None = None

async def execute_with_compensation(steps: list[CompensatingStep], context: dict):
    executed: list[CompensatingStep] = []
    try:
        for step in steps:
            result = await step.execute(context, dry_run=False)
            context["steps"][step.step_id] = {"output": result}
            executed.append(step)
        return context
    except Exception as e:
        # Compensate in reverse order (skip steps with no compensator)
        for step in reversed(executed):
            if step.compensate:
                try:
                    await step.compensate(context)
                except Exception as comp_err:
                    logger.error(f"Compensation failed for {step.step_id}: {comp_err}")
        raise
```

### Where each step falls in the compensation model

For the `fetch → transform → render → send` pipeline:

- **Fetch** (read-only HTTP GET): No compensation needed. Idempotent. Safe to re-run.
- **Transform** (SQL SELECT, in-memory aggregation): No compensation needed. Pure computation, no side effects.
- **Render** (Jinja2 template → HTML string): No compensation needed. If temp files are produced, compensation deletes them.
- **Send** (SMTP email): **Pivot transaction.** Cannot be compensated — you cannot un-send an email. This is the point of no return.

**The practical implication**: for this specific pipeline, compensation is irrelevant because the only irreversible step is the last one. If any earlier step fails, no side effects have occurred. If the send step fails, no email was sent — just retry or alert the user. The only scenario requiring compensation is if a future pipeline adds a step that writes to the database *before* the send step — in that case, compensation would wrap the write in a SQLite transaction and roll it back on failure.

**When saga becomes worthwhile**: If the pipeline grows to include steps that write to external systems (POST to an API, write to a file, update a third-party CRM), and those steps precede other fallible steps. Until then, **status tracking with try/except is sufficient**. Add compensating functions incrementally as write-steps are introduced, rather than building a saga coordinator upfront.

---

## 7. Open-source references and relevant implementations

### Workflow engine internals worth studying

**n8n** (github.com/n8n-io/n8n) provides the best reference for graph-based JSON workflow definitions with a visual editor. Its `INodeType` interface — a TypeScript class with a `description` object containing `properties`, `credentials`, `inputs`, and `outputs` — is directly analogous to the `StepBase` registry pattern. The `typeVersion` field per node is the most battle-tested approach to per-step schema versioning.

**Windmill** (github.com/windmill-labs/windmill) provides the best reference for schema-driven workflow definitions. Its OpenFlow specification uses JSON Schema (Draft 2020-12) derived from function signatures, `input_transforms` with static and JavaScript transforms for data passing, per-step retry with constant and exponential backoff, and a global `failure_module` as a try-catch handler. The three-file pattern (`*.script.yaml` + `*.py` + `*.script.lock`) is a clean separation of schema, logic, and dependencies.

**Trigger.dev** (github.com/triggerdotdev/trigger.dev) demonstrates a code-first approach with `task()` definitions that include retry config, queue concurrency limits, machine presets, and `maxDuration`. Its `triggerAndWait()` pattern for task composition is elegant but code-only — not directly applicable to JSON-defined pipelines.

### AI-agent workflow authoring

**Cordum** (github.com/cordum-io/cordum) is the most directly relevant open-source project — a governance-first control plane for AI agents with policy-before-dispatch, approval gates, audit trails, and DAG workflows. Its architecture of "define rules for what agents can do, enforce before execution" maps closely to this design.

**AgentSpec** (from the ICSE 2026 paper, arxiv.org/abs/2503.18666) provides a lightweight DSL for runtime enforcement of LLM agent safety using `rule → trigger → predicate → enforcement` structures. Its approach of checking each action against declarative rules before execution is directly applicable to pipeline step validation.

### Libraries and tools used in this design

- **APScheduler 3.10+** (github.com/agronholm/apscheduler): `AsyncIOScheduler` with `SQLAlchemyJobStore`, `CronTrigger`, misfire/coalesce configuration
- **Pydantic v2** (docs.pydantic.dev): `model_json_schema()` for step parameter schemas, discriminated unions for step types, `@field_validator` for SQL safety
- **tenacity** (github.com/jd/tenacity): Async-native retry with exponential backoff and jitter for fetch steps
- **aiobreaker** (github.com/arlyon/aiobreaker): Asyncio circuit breaker (optional, for high-frequency API polling)
- **pyrate-limiter** (github.com/vutran1710/PyrateLimiter): Token bucket with SQLite persistence for rate limiting across app restarts

### Papers

The **MAPL paper** ("Authenticated Workflows: A Systems Approach to Protecting Agentic AI," arxiv.org/abs/2602.10465) provides the four-boundary model and hierarchical policy composition concepts adapted in the security section above. While its cryptographic attestation model targets distributed multi-agent systems, the boundary enforcement framework and intent-specification approach apply at any scale.

## Conclusion

The design converges on a few non-obvious insights that emerged from cross-referencing the workflow engine landscape. **Windmill's `input_transforms` pattern — not Airflow's XCom — is the right model** for JSON-defined pipelines where an LLM must explicitly declare data flow between steps; `{{steps.<id>.output}}` expressions make data provenance visible in the policy document itself. **The `__init_subclass__` + Pydantic combination eliminates the registration ceremony** that plagues Airflow's operator system while auto-generating the JSON Schema that MCP tool definitions require — one class definition serves triple duty as executor, validator, and AI-agent capability advertisement. **SQLite's authorizer callback is an underused security primitive** that provides compile-time SQL sandboxing with zero runtime overhead, far stronger than regex-based keyword filtering. And the most important architectural choice may be the simplest: **the full saga pattern, circuit breakers, and distributed scheduling coordination are all unnecessary** for a single-process desktop app — status tracking with try/except, tenacity retries, and APScheduler's `coalesce=True` cover every practical failure mode at a fraction of the complexity.