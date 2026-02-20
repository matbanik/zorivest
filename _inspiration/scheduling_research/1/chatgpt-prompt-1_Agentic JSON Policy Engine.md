# Local-First Scheduling and Pipeline Policies for an AI-Integrated Investment Desktop App

## Design goals and constraints

Your constraints—single-user, single-process, local desktop app—create a very different design space than distributed workflow platforms. Most of the complexity in systems like distributed workers, message brokers, and “exactly-once” delivery shifts into a smaller set of concerns: deterministic policy interpretation, correctness and observability of runs, safe handling of side effects (especially email), and robust behavior across app restarts and time changes (DST). citeturn16view1turn15view0turn19view0

A helpful mental model is: **you are building a tiny workflow engine + scheduler embedded inside one FastAPI process**, and you want it to be:

- **LLM-authorable**: easy for an agent to generate valid JSON consistently.
- **Human-editable**: readable and reviewable in a React JSON editor with autocompletion and validation.
- **Deterministic and inspectable**: every run produces a durable trail (inputs → step state transitions → outputs → emitted side effects).
- **Policy-governed**: the engine should enforce guardrails regardless of what the agent tries to author. This matches the core thrust in “authenticated workflows” style thinking: treat “agent → tool → data” as boundary crossings and enforce intent at runtime, not just via prompts. citeturn27view0turn28view0turn28view2

The rest of this document is organized to match your requested deliverables: schema, registry, execution architecture, edge cases, security guardrails, minimal saga, and references.

## Policy JSON schema for AI-authored pipelines

### What existing engines teach about step structure and data passing

Even though you are not deploying these systems, their *representation choices* are useful references:

- **entity["company","n8n","workflow automation platform"]** persists workflows as JSON and makes the graph structure explicit: a `nodes` array (each node has `type`, `typeVersion`, `parameters`, etc.) and a `connections` object that routes output of one node into the input of another. n8n’s docs describe connections as the mechanism that passes data between nodes. citeturn21search9turn21search1turn6view0  
  n8n also explicitly supports **node versioning**: workflows saved with version 1 keep using version 1 even if a version 2 exists—an important precedent for backward compatibility. citeturn21search12

- **entity["company","Windmill","open-source workflow platform"]** uses “OpenFlow,” a JSON-serializable workflow format. It models a workflow as a sequence of “modules,” with optional failure handling (`failure_module`) and per-step `retry`. citeturn7view0  
  For data passing, Windmill’s “input transforms” allow any step’s input to reference **any prior step’s result by ID**, making the overall workflow a DAG even if it’s rendered as a step list. citeturn7view1

- **entity["organization","Cloud Native Computing Foundation","cncf foundation"]’s Serverless Workflow DSL/spec** demonstrates a clean separation of concerns that maps well to your use case:
  - tasks can have conditional execution (`if`) and flow control directives,
  - task/workflow `timeout`,
  - reusable `retries` and `timeouts`,
  - explicit input/output schemas and transformations,
  - retry policies with delay/backoff/jitter,
  - and “export” of task output into a workflow context. citeturn10view0turn12view0turn11view0  
  Particularly relevant is the spec’s emphasis that runtimes should validate raw input against schema before transformation and validate output after transformation. citeturn12view0

- **entity["organization","Apache Airflow","workflow scheduler"]** is “workflow-as-code,” but it *does* serialize DAGs into JSON for the webserver. The Airflow code notes that non-serializable fields (functions, custom classes) are cast to strings, and it stores a `__version` for the serializer and refuses to deserialize unknown versions. citeturn13view2  
  This is a strong precedent for (a) avoiding embedding live code in your policy JSON, and (b) strict schema/version separation.

The big structural takeaways for your design:

1. **A stable step ID is central.** Both n8n and Windmill rely on stable node/module identifiers for wiring and data access patterns. citeturn6view0turn7view1  
2. **Schema + examples matter for authoring.** Windmill explicitly uses JSON Schema Draft 2020-12 for describing/validating inputs, and encourages documenting schemas for better tooling. citeturn21search5  
3. **Versioning is operational, not cosmetic.** n8n and Airflow treat versioning as a mechanism for preventing breakage. citeturn21search12turn13view2

### Use JSON Schema + OpenAPI to make policies easy for both LLMs and humans

For your environment, the highest-leverage move is to ship a **machine-checkable JSON Schema** for the policy document, and:
- attach it to the policy file via `$schema` so editors (Monaco/CodeMirror) can autocomplete and validate,
- generate it from your canonical Python models (Pydantic v2) to keep docs, validation, and MCP discovery in sync. citeturn4search4turn4search8turn4search2

This aligns with:
- **JSON Schema** being explicitly intended for validation/documentation of JSON structure. citeturn4search4turn4search8
- **OpenAPI 3.1** aligning with JSON Schema Draft 2020-12, which reduces friction between “policy schema” and “tool schema exposure” (via FastAPI OpenAPI or MCP tool metadata). citeturn4search1turn4search5
- **Pydantic v2** generating JSON Schema compliant with 2020-12 and OpenAPI 3.1, which lets you treat Python as the source-of-truth. citeturn4search2turn25search1
- FastAPI’s ability to add examples / schema extras that can be repurposed to provide GUI affordances (field descriptions, examples, UI hints). citeturn4search11turn4search3

### Recommended policy document format

Below is a **recommended canonical policy document** (the JSON *instance* stored in SQLite) followed by annotations explaining why each piece exists.

#### Recommended policy JSON (example instance)

```json
{
  "$schema": "https://your-app.local/schemas/pipeline-policy/1.0.0.json",
  "kind": "pipeline_policy",
  "schema_version": "1.0.0",

  "policy_id": "pol_weekly_portfolio_digest",
  "title": "Weekly portfolio digest",
  "description": "Fetch latest quotes, compute P&L, render an email, and send to me.",
  "tags": ["portfolio", "email", "weekly"],

  "enabled": true,

  "schedule": {
    "trigger": "cron",
    "cron": "0 8 * * MON",
    "timezone": "America/New_York",
    "misfire_grace_seconds": 21600,
    "coalesce": true,
    "max_instances": 1
  },

  "defaults": {
    "timeout_seconds": 60,
    "retry": {
      "max_attempts": 3,
      "backoff": { "strategy": "exponential", "base_seconds": 1, "max_seconds": 30 },
      "jitter_seconds": 0.5
    }
  },

  "inputs_schema": {
    "type": "object",
    "properties": {
      "as_of": { "type": "string", "format": "date-time" },
      "benchmark_symbol": { "type": "string", "default": "SPY" }
    },
    "required": []
  },

  "steps": [
    {
      "id": "fetch_quotes",
      "type": "market_data.fetch_quotes",
      "type_version": 1,
      "title": "Fetch quotes",

      "timeout_seconds": 30,
      "retry": { "max_attempts": 5, "backoff": { "strategy": "exponential", "base_seconds": 1, "max_seconds": 60 } },

      "inputs": {
        "provider": "alphavantage",
        "symbols": { "ref": "ctx.positions.symbols" }
      },

      "outputs": {
        "export_as": "quotes"
      }
    },

    {
      "id": "load_positions",
      "type": "portfolio.load_positions",
      "type_version": 1,
      "title": "Load positions",
      "inputs": {
        "account_id": "default"
      },
      "outputs": {
        "export_as": "positions"
      }
    },

    {
      "id": "compute_pnl",
      "type": "transform.compute_portfolio_pnl",
      "type_version": 1,
      "title": "Compute P&L",
      "inputs": {
        "positions": { "ref": "ctx.positions" },
        "quotes": { "ref": "ctx.quotes" }
      },
      "outputs": {
        "export_as": "pnl"
      }
    },

    {
      "id": "run_sql",
      "type": "db.run_query",
      "type_version": 1,
      "title": "Query cash balances",
      "inputs": {
        "connection": "app_db_readonly",
        "sql": "SELECT currency, balance FROM cash_balances ORDER BY currency"
      },
      "outputs": { "export_as": "cash" }
    },

    {
      "id": "render_email",
      "type": "template.render",
      "type_version": 1,
      "title": "Render email body",
      "inputs": {
        "template_id": "weekly_digest_v1",
        "context": {
          "as_of": { "ref": "ctx.run.started_at" },
          "positions": { "ref": "ctx.positions" },
          "pnl": { "ref": "ctx.pnl" },
          "cash": { "ref": "ctx.cash" }
        }
      },
      "outputs": { "export_as": "email" }
    },

    {
      "id": "send_email",
      "type": "email.send_smtp",
      "type_version": 1,
      "title": "Send email",
      "side_effects": true,

      "inputs": {
        "smtp_profile_id": "primary_smtp",
        "to": ["me@example.com"],
        "subject": "Weekly portfolio digest",
        "body_text": { "ref": "ctx.email.body_text" },
        "body_html": { "ref": "ctx.email.body_html" }
      },

      "guardrails": {
        "max_recipients": 3,
        "require_confirm_if_manual_trigger": true
      },

      "outputs": { "export_as": "email_send_result" }
    }
  ],

  "on_failure": {
    "mode": "stop",
    "notify": false
  },

  "audit": {
    "authored_by": { "actor_type": "agent", "actor_id": "mcp://ide-agent" },
    "last_edited_by": { "actor_type": "user", "actor_id": "local-user" }
  }
}
```

#### Annotations and best practices (why this shape works)

**A schema envelope that editors and agents can rely on**
- `$schema` enables editor validation/autocomplete and is a common way to tie an instance document to its JSON Schema dialect/URL; JSON Schema formalizes `$schema` as part of dialect identification and related mechanisms. citeturn4search4turn4search17  
- `schema_version` should be treated as “policy document dialect,” similar to how Airflow’s serialized form embeds `__version` and rejects unknown versions. citeturn13view2  
- Use SemVer for `schema_version` so compatibility intent is machine- and human-readable. citeturn30search0

**Human readability**
- `title`, `description`, `tags` match what many workflow systems surface in UI: OpenFlow has `summary`/`description`; n8n stores `name`/`description`. citeturn7view0turn6view0  
- Prefer **arrays of steps** in declared execution order if you intend sequential execution; it’s the simplest mental model and easiest to edit/review.

**Step identity**
- `id` is the stable key for: persistence, data referencing, resumption, and UI diffing. This directly mirrors Windmill’s “refer to results by ID” approach and n8n’s node identity in connections. citeturn7view1turn6view0

**Step typing and backward compatibility**
- `type` is a stable string identifier (namespaced). This resembles n8n’s node `type` string (like `n8n-nodes-base.github`) and OpenFlow’s rich union types across modules. citeturn6view0turn7view0  
- `type_version` is essential if you ever change semantics/params. n8n’s `typeVersion` provides a proven strategy: old workflows keep running against old node behavior. citeturn6view0turn21search12

**Retries, timeouts, and failure handling**
- Centralize defaults (`defaults.timeout_seconds`, `defaults.retry`) and allow per-step override. Serverless Workflow and OpenFlow both encode retry/timeout behavior at the step/task layer, and Serverless Workflow formalizes retry with delay/backoff/jitter. citeturn12view0turn7view0  
- Model explicit per-step `side_effects: true` to support dry-run logic and guardrail policy decisions.

**Step-to-step data passing**
- The `outputs.export_as` plus `inputs.ref` pattern is a **context dictionary** approach: each step can export a value into a global `ctx` namespace. This is conceptually similar to Serverless Workflow’s “export into workflow context” and Windmill’s global access to step results through transforms. citeturn12view0turn7view1  
- For an AI authoring workload, the object form `{ "ref": "ctx.email.body_html" }` is generally more robust than string interpolation alone—because it’s unambiguous and easy to validate statically.

### Schema evolution strategy

Your schema will evolve. Plan for it from day one using *both* policy schema versioning *and* step-type contract versioning:

- **Policy schema version (`schema_version`)**: increment when you change the structure/meaning of the policy document itself. Use SemVer conventions. citeturn30search0turn13view2  
- **Step type version (`type_version`)**: increment when a step type’s contract changes (parameters, semantics, defaults). This follows n8n’s “workflow keeps using the older node version” approach. citeturn21search12turn6view0  
- **Migration strategy**:
  - Maintain a `policy_migrations` module that can transform stored policies forward (e.g., `1.0.0 -> 1.1.0`) deterministically.
  - At load time, either (a) migrate to latest in-memory, or (b) reject + show a “needs migration” UI. Airflow’s “refuse unknown serializer versions” is an explicit precedent for hard-failing incompatible versions. citeturn13view2  
  - Keep `type` rename/removal compatible via an **alias map** inside the step registry (e.g., treat `market.fetch` as alias of `market_data.fetch_quotes`) and emit warnings. This is similar in spirit to how ecosystems keep old identifiers working (n8n node versions; Airflow backward compatibility code paths). citeturn21search12turn13view2  

### Validation at policy creation time vs execution time

A useful division (consistent with Serverless Workflow’s “validate raw input, then validate transformed output” model) is: citeturn12view0turn10view0

**Policy creation-time validation (reject early)**
- JSON Schema structural validation (required fields, types, enums, sizes).
- Step-type existence + `type_version` existence in registry.
- Static reference validation:
  - `ref` values are syntactically valid and point to allowed namespaces.
  - Steps only reference exports that are defined (or are explicitly optional).
- DAG integrity constraints:
  - If you allow referencing arbitrary prior steps (Windmill-like), topologically validate it is acyclic. Windmill explicitly notes that allowing step inputs to reference any previous step result makes flows a DAG. citeturn7view1  
  - If you keep a strict sequence-only model, restrict references to “previous steps only,” which makes cycles impossible by construction.
- Guardrail constraints: max steps, forbidden step types, etc.

**Execution-time validation (validate with real data)**
- Input validation against `inputs_schema` (if provided).
- Step input validation against each step type’s parameter schema (after resolving refs).
- Output validation if you choose to let steps declare output schema (recommended for “db.run_query” and “template.render” to catch shape drift early). Serverless Workflow strongly encourages documenting schemas for input/output and describes runtime validation. citeturn12view0  
- Safety checks tied to real runtime context: “manual trigger requires confirm,” “dry-run forbids side effects,” rate limiting thresholds, etc.

## Step type registry and extensibility model

### Registry design goals

Your registry should answer two questions reliably:

1. **What steps exist and what do they do?** (for humans and for the agent)
2. **How do we validate inputs and execute them deterministically?**

This mirrors the “discover tools + get tool details” pattern used by **entity["organization","StacklokLabs","agent tooling org"]’s Model Context Shell**: it exposes tools for pipeline execution and provides discovery mechanisms so agents can compose workflows from schemas, not guesswork. citeturn20view0

### Recommended “step definition” contract (Python Protocol)

A good local-first pattern is a **registry of step executors** where each step type:

- declares a stable `type_name` and `type_version`,
- publishes a JSON Schema for its parameters,
- declares whether it has side effects,
- supports dry-run behavior,
- defines optional compensation behavior (for saga-like recovery),
- executes as an async function.

Python Protocols give you structural typing (“duck typing for executors”), which is exactly what you want for a plugin-like registry. citeturn25search0turn25search12

#### Python Protocol + registry pattern (example)

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable, Mapping, Optional

Json = dict[str, Any]


@dataclass(frozen=True)
class StepContext:
    run_id: str
    step_id: str
    dry_run: bool
    # Global pipeline context (exports from previous steps + run metadata)
    ctx: Json


@dataclass(frozen=True)
class StepResult:
    ok: bool
    output: Json
    # Optional metadata for observability
    metrics: Json | None = None


@runtime_checkable
class StepExecutor(Protocol):
    # Stable identifiers (for compatibility + migrations)
    type_name: str
    type_version: int

    # Used for policy validation + editor/agent schema hints
    @classmethod
    def params_schema(cls) -> Json: ...

    # For security/dry-run decisions
    @classmethod
    def has_side_effects(cls) -> bool: ...

    async def run(self, *, params: Json, context: StepContext) -> StepResult: ...

    # Optional compensation hook (Saga-style)
    async def compensate(
        self, *, params: Json, context: StepContext, prior_result: StepResult
    ) -> None: ...


class StepRegistry:
    def __init__(self) -> None:
        self._by_type: dict[tuple[str, int], type[StepExecutor]] = {}
        self._aliases: dict[str, str] = {}  # old_type_name -> new_type_name

    def register(self, cls: type[StepExecutor]) -> None:
        key = (cls.type_name, cls.type_version)
        self._by_type[key] = cls

    def add_alias(self, old: str, new: str) -> None:
        self._aliases[old] = new

    def resolve(self, type_name: str, type_version: int) -> type[StepExecutor]:
        type_name = self._aliases.get(type_name, type_name)
        return self._by_type[(type_name, type_version)]
```

### Plugin-like extensibility options in Python

You can support a “core steps” bundle plus optional plugins using **Python packaging entry points**:

- Entry points are a standard way for installed packages to advertise plugins that an application can discover at runtime. citeturn3search22turn3search29  
- The recommended loader is `importlib.metadata` (stdlib). citeturn3search22turn3search29  

This gives you:
- composable internal dev (your own repos can publish steps),
- optional community steps later,
- and a stable discovery mechanism.

### Exposing the registry to the AI agent via MCP

To make an LLM consistently author valid policies, the agent needs a **capability catalog**. A practical MCP-facing design is:

- `pipeline.step_types.list` → returns all step types, with:
  - `type_name`, `type_version`, `title`, `description`
  - parameter JSON schema + examples
  - “side effects” flag
  - resource requirements (network/db/email)
  - constraints (max rows, allowed domains, etc.)
- `pipeline.step_types.get(type_name, type_version)` → one step type, full schema and docs.
- `pipeline.policy.validate(policy_json)` → returns structural + semantic validation results.

This closely resembles the utility tools in Model Context Shell (`list_all_tools`, `get_tool_details`), which exist specifically so agents can build pipelines from schema alone. citeturn20view0

If you already expose a FastAPI OpenAPI schema, you can reuse those generated JSON Schemas and examples to populate the MCP step catalog—OpenAPI 3.1’s alignment with JSON Schema Draft 2020-12 reduces impedance. citeturn4search1turn4search5turn4search2

## Pipeline execution engine and persistence model

### Execution engine architecture diagram (text-based)

```text
+---------------------------- Electron/React ----------------------------+
|  - Policy list / editor (JSON + schema autocomplete)                   |
|  - Manual trigger / dry-run trigger                                    |
+-----------------------------+------------------------------------------+
                              |
                              | REST (localhost) / domain ports
                              v
+----------------------------- FastAPI ----------------------------------+
|  Policy API: CRUD + validate + trigger                                 |
|  Step Registry API: list step types + schemas                           |
|  Run API: status, logs, artifacts                                       |
+-----------------------------+------------------------------------------+
                              |
                              v
+-------------------------- Scheduling Layer ----------------------------+
|  APScheduler AsyncIOScheduler                                          |
|   - job per policy schedule (cron/interval)                             |
|   - max_instances, misfire_grace_time, coalesce                         |
+-----------------------------+------------------------------------------+
                              |
                              v
+------------------------- Pipeline Engine ------------------------------+
|  PipelineRunner (async)                                                |
|   - loads policy JSON (and compiled form)                               |
|   - resolves refs into params                                           |
|   - executes steps sequentially                                         |
|   - persists state transitions to SQLite/SQLCipher                       |
|   - emits artifacts/logs                                                |
|   - supports dry_run + resume                                           |
+-----------------------------+------------------------------------------+
                              |
                              v
+------------------------ Adapters / Steps ------------------------------+
|  market fetch: httpx                                                   |
|  db interactions: SQLAlchemy/SQLite                                     |
|  template: Jinja2                                                     |
|  email: SMTP async client                                               |
+-----------------------------+------------------------------------------+
                              |
                              v
+----------------------- SQLite/SQLCipher -------------------------------+
|  policies, schedules, runs, step_runs, artifacts, audit                 |
+------------------------------------------------------------------------+
```

### Scheduling semantics and overlapping runs

APScheduler has important default behaviors you can lean on:

- **Only one instance of a job runs at a time by default.** If a job is due but its previous run hasn’t finished, the new run is treated as a misfire unless you increase `max_instances`. citeturn16view1  
- **Misfire handling**: if the scheduler was shut down and restarts after a job’s scheduled time, APScheduler checks each missed execution against `misfire_grace_time` and may execute multiple missed runs in succession. `coalesce` can roll multiple missed runs into one. citeturn16view1  

Because you are single-process and single-user, a conservative default is:
- `max_instances = 1` (per policy),
- `coalesce = true` (avoid “burst catch-up” after laptop sleep),
- a `misfire_grace_seconds` that matches user expectations (e.g., 6 hours for “morning digest”—after lunch, skip). citeturn16view1  

### Run and step state persistence

State tracking is simplest if you persist **two levels**:

- `pipeline_run`: one row per triggered execution (scheduled or manual).
- `step_run`: one row per step attempt.

For state names, you can borrow the workflow/task phase vocabulary used in the Serverless Workflow spec (pending/running/faulted/completed, etc.), which is designed for workflow/task execution and observability. citeturn9view0turn10view0

A persistence-friendly state machine:

- `PENDING` → `RUNNING` → (`SUCCESS` | `FAILED` | `SKIPPED` | `CANCELLED`)
- each `step_run` has `attempt`, `started_at`, `finished_at`, `error_type`, `error_detail`, and optionally `output_json`.

Key design choice: **persist step output** (when safe) so resume/dry-run/debug can replay context without re-fetching everything. This mirrors how many workflow systems emphasize tracked state and recorded transitions. citeturn30search3turn30search35

### Async step timeouts and cancellation

For local, asyncio-based execution, enforce timeouts at the step boundary:

- Python’s `asyncio.wait_for()` is the standard pattern for enforcing timeouts on awaitables. citeturn3search23  
- In Python 3.11+ (and therefore 3.12), `asyncio.timeout()` is also available as a structured timeout context manager; the canonical details are in the Python asyncio docs and examples. citeturn3search23  

Operationally:
- Prefer a per-step timeout (because external APIs and SMTP are the common hang points).
- Persist “timed out” as a distinct failure reason so users can distinguish a timeout from logical failure.

### Step-to-step data flow: context dict vs explicit output mapping

You can support both, but keep the default simple:

- **Context dict**: `ctx` holds run metadata + exports (`ctx.positions`, `ctx.quotes`, etc.). This resembles Windmill’s “results.{id}” access pattern and Serverless Workflow’s “export to context.” citeturn7view1turn12view0  
- **Explicit output mapping**: optionally allow `outputs.select` (JMESPath/JSONPath) so a step can publish only a subset (reduces stored artifact size and stabilizes downstream contract). This is aligned with Serverless Workflow’s input/output transformations (`input.from`, `output.as`, `export.as`). citeturn12view0  

A pragmatic compromise:
- Implement `ref` for deterministic structural referencing.
- Add an *optional* safe expression language for transformations (e.g., JMESPath-style queries), taking inspiration from n8n’s emphasis on expressions and Windmill’s transforms—while keeping the evaluation environment constrained. citeturn21search0turn7view1

### Dry-run mode

Dry-run should be a first-class, explicit runtime mode:

- At execution start, set `dry_run = true` in run context.
- Each step executor declares `has_side_effects()`; the engine enforces a policy:
  - If side effects and dry-run: either skip or replace with a stub executor.
- Persist a run-level flag (`pipeline_run.dry_run`) and step-level `SKIPPED_DRY_RUN` status.

This is analogous to “preview stages” in Model Context Shell, where the system provides a mechanism for agents to “inspect shape” without committing to full execution. citeturn20view0

### Resume after failure

Resume is much easier in a single-process app if you persist step outputs:

Recommended approach:
- A resume request creates a **new pipeline_run** with `resumed_from_run_id`.
- The engine loads prior successful steps’ `output_json` into the initial `ctx` (marked as “cached”).
- It re-executes from the last failed step (or a user-selected step), skipping steps that are marked successful in the prior run.

This is conceptually related to “idempotency” and “result reuse/caching” ideas in workflow tooling (e.g., Prefect emphasizes caching and state tracking). citeturn30search3turn30search35

If you adopt idempotency keys (recommended), you can treat retries/resume as “safe replays” rather than ad hoc reruns. Trigger.dev’s documentation explains idempotency keys as a mechanism to ensure a task is executed only once even if triggered multiple times. citeturn30search12turn30search1  

## Edge cases and failure modes with mitigations

### Overlapping runs

**Failure mode**: schedule fires while a previous run is still executing; the user manually triggers at the same time.

**Mitigations**
- At scheduler layer: keep `max_instances=1` unless you explicitly want overlap. APScheduler defaults to one concurrent instance and treats overlap as misfire. citeturn16view1  
- At engine layer: implement a per-policy async lock (`asyncio.Lock`) keyed by `policy_id`. This prevents overlap even if invoked outside APScheduler (manual trigger).  
- Define policy-level concurrency handling (`concurrency.mode`): `skip`, `queue`, or `reject_manual_when_running`. If you later add multi-policy concurrency, you can also cap “total active runs.”

### Misfire behavior across app restarts / laptop sleep

**Failure mode**: the app was closed or suspended when a cron should have fired; on restart, the scheduler may execute missed runs.

**Mitigations**
- Use APScheduler’s `misfire_grace_time` to decide whether a missed run is still valid, and `coalesce` to collapse multiple missed triggers into one execution. APScheduler documents these behaviors explicitly. citeturn16view1  
- Persist schedules (or store policy schedules in your own DB and re-register them deterministically on startup) so restart doesn’t create duplicates; APScheduler warns that persistent job stores require stable job IDs and `replace_existing=True` to avoid duplication. citeturn14view1  
- Expose the “last intended fire time” and “actual start time” in the run record so the user can reason about “did it run late?” (critical around market hours).

### Step idempotency and retries

**Failure mode**: a retry re-fetches data or re-sends email, causing duplicates or inconsistent outputs.

**Mitigations**
- Treat idempotency as a property at the step boundary:
  - Each step can declare `idempotency.key_template` derived from run_id + step_id + (meaningful input hash).  
  - On execution, compute key → check a local `idempotency_cache` table → reuse output if present.  
- The practical value of idempotency keys is documented in workflow tooling: Trigger.dev describes idempotency keys as preventing duplicate executions when triggers fire multiple times and calls out “attempt-scoped” idempotency control. citeturn30search12turn30search1  
- For fetch steps, idempotency can mean “cache response by (provider, symbols, date)” with TTL.
- For email steps, idempotency can mean “store message fingerprint + recipients + subject + body hash” and refuse duplicates unless user overrides.

### Compensation and rollback when side effects have occurred

**Failure mode**: email was sent successfully but upstream data was incorrect; or a DB write occurred and later steps fail.

**Mitigations**
- Recognize that some actions cannot be “undone.” The Saga literature explicitly models compensating transactions but also acknowledges the real-world difficulty of fully reversing certain actions. citeturn26search0turn26search1  
- For your pipeline types, a pragmatic recovery path is:
  - For DB writes: wrap in SQLite transactions where possible; rollback is straightforward within a single database boundary.
  - For emails: implement “compensation by correction”:
    - a “send_correction_email” step template,
    - an “email recall” is generally not reliable; instead, produce a follow-up with corrected facts and clear labeling.
- Persist a strong audit trail so the user can identify exactly what was sent and why.

### API rate limits and transient network failures

**Failure mode**: market data APIs throttle; retries amplify the problem; the whole single-process app becomes slow or unresponsive.

**Mitigations**
- Use bounded concurrency + connection pooling:
  - HTTPX supports explicit timeout configuration and connection pool limits. This matters in a single-process app to prevent exhausting sockets and memory. citeturn25search3turn25search35  
- Implement retry policy with exponential backoff + jitter:
  - Serverless Workflow’s retry policy structure includes delay, backoff strategies, and jitter, which maps cleanly into your local retry config. citeturn12view0  
  - If you prefer a library, Tenacity is a general-purpose retrying library intended to simplify retry behavior. citeturn25search2turn25search14  
- Add a local “circuit breaker” per provider: after N failures, short-circuit for a cooldown period and mark step as failed fast.

### Schema evolution and missing step types

**Failure mode**: a stored policy references a step type that was renamed/removed.

**Mitigations**
- Adopt a compatibility contract similar to n8n node versioning:
  - Keep old `type_name` aliases for at least one deprecation cycle.
  - Keep executor implementations for older `type_version` as long as you can. citeturn21search12turn6view0  
- If a step is truly removed:
  - Fail policy validation at load time (policy creation-time check).
  - Provide a “migration assistant” in the GUI that can rewrite known old types → new types.

### Circular dependencies and DAG validity

**Failure mode**: steps reference each other’s outputs, creating a cycle; or a step references a future step output.

**Mitigations**
- Easiest for your sequential engine: forbid references to future steps (only allow refs to `ctx` exports from prior steps). This is “acyclic by construction.”
- If you intentionally allow “reference any step” (Windmill-style), then you must treat the policy as a DAG:
  - Build a dependency graph from `ref` edges.
  - Topologically sort; reject cycles.  
Windmill explicitly frames flows as DAGs because any step input can reference any step result via transforms. citeturn7view1

### Resource exhaustion in a single-process app

**Failure mode**: long-running pipelines consume memory, keep DB transactions open, or leak connections; UI becomes sluggish.

**Mitigations**
- Strict timeouts per step and overall run timeout.
- Enforce bounded output size:
  - store large artifacts to disk (encrypted if needed), persist only metadata + pointer in SQLite.
- Ensure DB operations are short-lived; avoid holding write transactions across long network operations.
- Use HTTPX connection limits and timeouts to avoid runaway outbound I/O. citeturn25search35turn25search3  

### Timezone and DST edge cases

**Failure mode**: cron schedules behave unexpectedly during DST spring-forward/fall-back; jobs run twice or not at all.

**Mitigations**
- APScheduler’s CronTrigger explicitly warns that cron triggers use “wall clock time,” and DST transitions can cause scheduled times to not exist or to repeat; it recommends using a non-DST timezone like UTC if you need to avoid this. citeturn15view0  
- Offer a user-visible “next 10 fire times” preview in the GUI so scheduling surprises are caught early.
- Store timestamps in RFC 3339 format (ISO 8601 profile) in logs/audit to reduce ambiguity in run records. citeturn26search8

### SQLite/SQLCipher locking and concurrent access

**Failure mode**: pipeline execution is writing while the GUI reads; SQLite throws `SQLITE_BUSY` / “database is locked”; or long reads block writes.

**Mitigations**
- Configure SQLite busy timeout so transient locks wait rather than failing immediately. SQLite documents `PRAGMA busy_timeout` as the way to set the busy handler timeout. citeturn19view0turn17search9  
- Use WAL mode if appropriate for your workload: WAL improves concurrency as readers do not block writers and writers do not block readers (with caveats). citeturn3search35  
- Split read and write sessions:
  - keep write transactions short,
  - avoid “read then upgrade to write” patterns when possible (a known source of contention).
- For “run_query” steps, consider a *separate read-only connection*:
  - SQLite URI filenames support `mode=ro` (read-only). citeturn18search1turn18search17  
  - `PRAGMA query_only` prevents data changes (CREATE/INSERT/UPDATE/DELETE/etc.) by returning `SQLITE_READONLY` on attempted write statements. citeturn19view0  

## Security guardrails for AI-authored policies

### Threat model: assume the agent can be wrong or adversarial

Even for a single-user desktop app, the risk surface is real: an IDE agent can author policies that exfiltrate data (email), trigger expensive or endless work, or run dangerous SQL.

The OWASP Top 10 for LLM Applications highlights risks like prompt injection, insecure output handling, and denial-of-service patterns that map directly to an “agent authors a pipeline that runs tools” architecture. citeturn17search4turn17search0

Additionally, MCP’s own security guidance enumerates protocol-related risks (confused deputy, token passthrough, SSRF, session hijacking, local server compromise) and emphasizes strong authorization design. citeturn29view0turn29view1

### Guardrail checklist (enforced by the backend, not by prompts)

This checklist is written as **backend-enforced rules** (policy creation-time + runtime enforcement).

**Policy creation constraints**
- Enforce a strict allowlist of step types; reject unknown `type`/`type_version`.
- Bound structural complexity:
  - max steps per policy,
  - max refs per step,
  - max policy JSON size.
- Require explicit acknowledgment fields on dangerous steps (`side_effects: true` steps must include guardrails).
- Validate schedule parameters and show DST warnings for cron schedules. citeturn15view0turn16view1  

**Runtime constraints**
- Per-policy concurrency controls (`max_instances=1` by default). citeturn16view1  
- Per-step and per-run timeouts. citeturn3search23turn30search10  
- Resource budgets:
  - HTTP request count cap per run,
  - max bytes downloaded per run,
  - max DB rows returned per query step,
  - max rendered email size.

**Email safety**
- Recipient allowlist (or “only self” by default).
- Max recipients per run (enforced even if policy says otherwise).
- Optional “manual-trigger confirmation” gate for side-effect steps.
- Persist a copy of sent content (or a hash + storage pointer) for audit and correction workflows.

**SQL sandboxing for `run_query`**
- Prefer *connection-level controls* over string filtering:
  - Open DB in read-only mode (`mode=ro`) where possible. citeturn18search1turn18search17  
  - Enable `PRAGMA query_only` for the query connection to prevent writes even if a write statement slips through. citeturn19view0  
- Treat PRAGMAs as sensitive:
  - SQLite notes PRAGMA statements can modify SQLite operation and may change across versions; unknown pragmas are ignored, which is hostile to “string allowlisting” approaches. citeturn18search0turn19view0  
- If you allow user-authored SQL, consider parsing SQL into an AST and permitting only `SELECT` statements; do not rely solely on keyword blacklists.

**MCP-facing authorization and tool exposure**
- Don’t accept “token passthrough” patterns; MCP security guidance explicitly calls token passthrough an anti-pattern and forbids accepting tokens not issued for the MCP server. citeturn29view1  
- Treat the step registry as **capabilities** with explicit scopes:
  - “market data fetch” (network to approved domains),
  - “db query read-only,”
  - “email send to allowlisted recipients.”
- Log every MCP-triggered policy creation/edit with actor metadata.

### MAPL / Authenticated Workflows applicability to a local desktop app

The “Authenticated Workflows” paper introduces MAPL as a policy language with:
- allow/deny resource patterns,
- parameter constraints,
- and “attestations” (cryptographically verified claims) to express workflow dependencies (“only export after anonymization completed”). citeturn28view0turn27view0  

For your local app, the *full* cryptographic trust layer (multi-surface PEPs, cross-framework enforcement) may be overkill. But **MAPL’s shape is directly applicable** in a simplified, local form:

- Your “resources” are step types (`email.send_smtp`, `db.run_query`, etc.).
- “Denied resources” are disallowed step types or adapters.
- “Parameter constraints” map cleanly to guardrails (max recipients, allowed domains, max rows).
- “Attestations” can be implemented as **runtime-proven step completion predicates** (not necessarily cryptographic): e.g., require `anonymize` step success before `email.send`. The MAPL grammar explicitly includes attestations as required constraints. citeturn28view0  

If you want stronger tamper-evidence even locally, the paper’s emphasis on hash chains and audit integrity can inspire how you store run logs (append-only, hash-chained audit records). citeturn27view0turn28view2  

## Minimal saga design for single-process pipelines

### How sagas simplify in a single-process + single SQLite DB context

The original Saga concept models a long-lived transaction as a sequence of transactions `T1..Tn` with compensations `C1..Cn`; the system guarantees either the forward path completes or it executes compensations in reverse for a partial execution. citeturn26search0turn26search17  

In distributed microservices, sagas are often about consistency across independent databases and message passing (a “sequence of local transactions” with compensations). citeturn26search1  

In your local app:
- **DB writes** can often be handled with normal SQLite transactions (ACID) in a single datastore, so many “distributed transaction” drivers disappear.
- **External side effects** (email, outbound HTTP to third parties) still require compensation thinking because you can’t roll them back like a DB transaction.

So the “minimal saga” you need is really:
1. persist step state and outputs durably,
2. define compensations only for steps with durable side effects,
3. provide a recovery workflow for “irreversible” actions (usually: send a correction email).

### Minimal saga implementation for fetch → transform → render → send

A minimal, sufficient approach for your 4-step pipeline:

- `fetch` and `transform` are typically *replayable* and don’t need compensation.
- `render` is deterministic given inputs; no compensation.
- `send` produces an irreversible effect; compensation is **corrective send** (or mark-and-alert).

#### Suggested runtime contract additions

In your policy step schema, add:
- `side_effects: boolean`
- `compensation` (optional):
  - `type`: compensation step type name
  - `params`: how to generate compensation params from context
  - or `mode: "manual_only"` meaning “surface a UI button for correction.”

#### Orchestrated saga pseudocode

```python
async def run_pipeline(policy, ctx):
    completed = []
    try:
        for step in policy.steps:
            result = await run_step(step, ctx)
            completed.append((step, result))
            if result.ok and step.outputs.export_as:
                ctx[step.outputs.export_as] = result.output
            if not result.ok:
                raise StepFailed(step.id)
        return "SUCCESS"
    except Exception:
        # Compensate in reverse order for steps that define it
        for step, result in reversed(completed):
            if step.compensation and step.side_effects:
                await run_compensation(step, ctx, result)
        return "FAILED"
```

This is “orchestrated saga”: a single runner decides when to compensate, which matches classic saga descriptions (sequence of local transactions + compensations) but is much simpler in a single process. citeturn26search1turn26search0  

### When saga is overkill

A full saga framework tends to be overkill when:
- only the last step has side effects and it’s easily auditable,
- you can correct errors by rerunning and sending a corrected message,
- the pipeline is short and deterministic.

In those cases, **try/except + durable status tracking + a “correction run” button** is often enough, especially in a single-user environment.

Sagas become worth it when:
- you have multiple side-effect steps (e.g., DB write + brokerage API call + email),
- compensations matter (e.g., “reverse a pending export,” “delete a created draft,” “revoke a token”),
- you need explicit, automated unwind behavior for user trust and compliance.

## Open-source references and further reading

The following are directly relevant to your requested comparison points and implementation inspiration:

- **Workflow JSON structures**
  - entity["company","n8n","workflow automation platform"] workflow JSON export/import and the structural requirement for workflows (`name`, `nodes`, `connections`, `settings`). citeturn21search9turn21search14  
  - Example of real n8n workflow JSON with `nodes` + `connections` and node `typeVersion`. citeturn6view0  
  - n8n node versioning behavior (existing workflows keep their node version). citeturn21search12  

- **Declarative workflow formats**
  - entity["company","Windmill","open-source workflow platform"] OpenFlow spec (modules, retry, failure module, stop-after-if, etc.) and architecture/data exchange notes about referencing step results by ID. citeturn7view0turn7view1  
  - CNCF Serverless Workflow DSL/reference for retries, timeouts, input/output schema validation, export-to-context, and scheduling semantics. citeturn10view0turn12view0turn9view0  

- **Workflow-as-code serialization**
  - entity["organization","Apache Airflow","workflow scheduler"] serialized DAG design: serializer versioning, schema validation, and notes about non-serializable elements being cast to strings. citeturn13view2turn13view1  

- **Local pipeline orchestration patterns**
  - entity["organization","StacklokLabs","agent tooling org"] Model Context Shell: JSON pipeline definitions, allowlisted transformations, tool discovery helpers, and server-side coordination of multi-step tool pipelines. citeturn20view0  

- **Scheduling and DST reality checks**
  - APScheduler on misfires, `misfire_grace_time`, `coalesce`, and `max_instances`. citeturn16view1turn14view1  
  - APScheduler cron trigger DST behavior and its “wall clock time” warning. citeturn15view0  

- **Security references**
  - OWASP Top 10 for LLM Applications (2025) overview and PDF. citeturn17search4turn17search0  
  - MCP Security Best Practices (confused deputy, token passthrough, SSRF, session hijacking). citeturn29view0turn29view1  
  - Authenticated Workflows / MAPL policy language and attestations concept. citeturn27view0turn28view0turn28view2  

- **Saga and compensations**
  - Original “Sagas” paper (Garcia-Molina / Salem) describing compensating transactions and guarantees. citeturn26search0turn26search17  
  - Microservices.io saga pattern summary (sequence of local transactions + compensations). citeturn26search1  

- **SQLite enforcement primitives useful for guardrails**
  - SQLite URI filename `mode=ro` and immutability flags. citeturn18search1turn18search17  
  - `PRAGMA query_only` behavior (write attempts return `SQLITE_READONLY`). citeturn19view0  
  - SQLite busy timeout and concurrency notes in PRAGMA docs. citeturn19view0turn17search9