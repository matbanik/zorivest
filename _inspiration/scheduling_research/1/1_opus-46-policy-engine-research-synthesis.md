# Agentic JSON Policy Engine — Three-Model Research Synthesis

> Cross-referencing ChatGPT, Claude, and Gemini research outputs on the same prompt.
> Each model produced a comprehensive design document. This synthesis distills where they **agree**, where they **diverge**, and what's **uniquely contributed** by each.

---

## 1. Universal Agreement (All Three Converge)

These are architectural decisions where all three models independently reached the same conclusion. **High confidence these are the right calls.**

### 1.1 Policy Schema Fundamentals

| Decision | Agreement |
|---|---|
| **`$schema` / `schema_version`** | All three include a schema version field. ChatGPT uses SemVer string, Claude uses integer, Gemini uses SemVer string with URI reference. |
| **Steps as flat array** | All use an ordered array of steps (not a nested graph). Steps execute sequentially by default. |
| **Stable step `id`** | Every step has a unique string ID used for data referencing, persistence, and UI. |
| **Step `type` discriminator** | Maps to a registry of executors. All namespace it (e.g., `market_data.fetch_quotes`). |
| **Per-step `timeout` and `retry`** | All define timeout and retry at both default and per-step levels with exponential backoff. |
| **`metadata` / `audit` block** | All capture authorship (AI vs human), timestamps, and version history. |
| **`enabled` flag** | Toggle scheduling without deleting the policy. |

### 1.2 Step Type Registry

| Decision | Agreement |
|---|---|
| **Pydantic for parameter schemas** | All three use Pydantic models to define step params and auto-generate JSON Schema for MCP/editor consumption. |
| **Side-effects flag** | Every step declares whether it has side effects (for dry-run and guardrail enforcement). |
| **MCP exposure** | Registry serves as source-of-truth for `tools/list` — AI agent discovers available steps via their JSON Schemas. |
| **Alias map for deprecated types** | Old step type names map to new ones for backward compatibility. |
| **Compensate method** | Optional `compensate()` on step executors for saga-style recovery. |

### 1.3 Execution Engine

| Decision | Agreement |
|---|---|
| **Sequential async execution** | Single `for step in steps` loop with `await`, using `asyncio.timeout()` per step. |
| **Context dict for data flow** | Steps export results to a shared context; subsequent steps reference prior outputs. |
| **Two-table persistence** | `pipeline_runs` + `pipeline_steps` (or equivalent) for run/step-level state tracking. |
| **State machine** | `PENDING → RUNNING → SUCCESS / FAILED / SKIPPED` for each step. |
| **Dry-run mode** | First-class flag; side-effect steps are skipped or stubbed. |
| **Resume from failure** | New run loads prior successful step outputs from DB, re-executes from failed step. |

### 1.4 APScheduler Configuration

| Decision | Agreement |
|---|---|
| **`max_instances=1`** | Prevent overlapping runs of the same policy. |
| **`coalesce=True`** | Collapse multiple missed firings into one execution. |
| **`misfire_grace_time`** | ChatGPT: 6 hours, Claude: 1 hour, Gemini: 1 hour. All agree it should be configurable. |
| **Persistent job store** | Use `SQLAlchemyJobStore` with `replace_existing=True` to survive restarts. |

### 1.5 SQLite/SQLCipher

| Decision | Agreement |
|---|---|
| **WAL mode** | Enable `PRAGMA journal_mode=WAL` for concurrent read/write. |
| **Busy timeout** | Set `PRAGMA busy_timeout` to avoid `SQLITE_BUSY` errors. |
| **Read-only connections** | Separate connection for AI-authored queries with `PRAGMA query_only` or `mode=ro`. |
| **`set_authorizer`** | Use SQLite's authorizer callback to sandbox SQL execution at compile time. |

### 1.6 Security Guardrails

| Decision | Agreement |
|---|---|
| **Step type allowlist** | Only registered types can execute. Unknown types are rejected. |
| **SQL sandboxing** | Authorizer callback + read-only connection, not just keyword filtering. |
| **Email recipient limits** | Enforce max recipients regardless of what the policy says. |
| **Content hash integrity** | Hash policy JSON at creation, verify before execution. |
| **Audit trail** | Append-only log of all actions with actor metadata. |
| **MAPL is overkill locally** | Full cryptographic attestation is unnecessary, but MAPL's boundary model and parameter constraints are directly applicable. |

### 1.7 Saga Pattern

| Decision | Agreement |
|---|---|
| **Full saga is overkill** | For a single-process app, most steps are replayable. Only email/external API steps need compensation. |
| **Orchestration variant** | Single runner decides compensation order (reverse of completed steps). |
| **Email is the "pivot transaction"** | Cannot be undone. Compensation = send correction email. |
| **DB writes use SQLite transactions** | ACID within single DB makes distributed saga unnecessary. |

---

## 2. Differing Takes (Same Topic, Different Recommendations)

### 2.1 Policy Schema Structure

| Topic | ChatGPT | Claude | Gemini |
|---|---|---|---|
| **Schema version format** | SemVer string (`"1.0.0"`) | Integer (`1`) | SemVer string with URI |
| **Step type naming** | Namespaced dotted path (`market_data.fetch_quotes`) | Simple name (`fetch`, `sql_query`, `render`) | `resource` field with dotted path (`market.fetch_prices`) |
| **Data referencing syntax** | `{ "ref": "ctx.quotes" }` — explicit JSON object | `{{steps.fetch_prices.output.quotes}}` — mustache templating | JSONPath (`$.market_data`, `$$.execution.input`) — ASL-style |
| **Error handling per step** | `on_failure` block at pipeline level (`mode: stop`) | `on_error` per step (`fail_pipeline`, `log_and_continue`, `retry_then_fail`) | `retry` array per state with `error_equals` matching |
| **Step versioning** | `type_version` integer on each step | `step_version` on registry class, not on each step in JSON | No per-step version in JSON; handled by registry |

> [!IMPORTANT]
> **Data referencing is the biggest divergence.** ChatGPT's `{ "ref": "ctx.x" }` is most JSON-Schema-friendly and easiest to validate statically. Claude's `{{mustache}}` is most readable but harder to validate. Gemini's JSONPath is most powerful but hardest for an LLM to author correctly.

### 2.2 Registry Implementation Pattern

| Topic | ChatGPT | Claude | Gemini |
|---|---|---|---|
| **Registration mechanism** | `Protocol` class + explicit `registry.register(cls)` call | `__init_subclass__` auto-registration (zero-boilerplate) | `@register` decorator on functions |
| **Step unit** | Class with `run()` method | Class with `execute()` method | Decorated function |
| **Plugin extensibility** | `importlib.metadata` entry points | Import-time scanning (no entry points needed for desktop app) | `plugins/` directory scanning with `importlib` |
| **Schema generation** | `classmethod params_schema() → Json` (manual) | `Params.model_json_schema()` (Pydantic auto) | `_generate_schema(func)` via introspection |

> [!TIP]
> **Claude's `__init_subclass__` approach is the most Pythonic** — zero ceremony, the class just exists and it's registered. ChatGPT's Protocol is more flexible for testing. Gemini's decorator is more familiar to Flask/FastAPI users.

### 2.3 Conditional Execution / Branching

| Topic | ChatGPT | Claude | Gemini |
|---|---|---|---|
| **Approach** | No explicit branching in schema; sequential only with `on_failure` | `conditions.skip_if` field on each step | Full `Choice` state type with comparison operators and `default` path |
| **Complexity** | Simplest — no branching | Middle — skip-if covers 80% of cases | Most powerful — full state machine with DAG transitions |
| **LLM authoring difficulty** | Easiest for LLM | Easy for LLM | Hardest — LLM must reason about state machine graph |

> [!WARNING]
> **This is a critical design decision.** Gemini's ASL-inspired state machine is the most expressive (supports Choice, Map, Pass states) but adds significant complexity. Claude's `skip_if` is the pragmatic middle ground. ChatGPT punts on branching entirely.

### 2.4 Workflow Topology

| Topic | ChatGPT | Claude | Gemini |
|---|---|---|---|
| **Model** | Ordered array (sequential by default), optional DAG via refs | Ordered array (sequential), refs only to prior steps | Named states with `next` transitions — full state machine / DAG |
| **Parallel execution** | Not addressed directly | Not in primary model | `Map` state with `max_concurrency` for item-level parallelism |
| **Iteration** | Not addressed | Not addressed | `Map` state iterates over arrays (like ASL) |

### 2.5 Saga Compensation Detail

| Topic | ChatGPT | Claude | Gemini |
|---|---|---|---|
| **When saga is needed** | Multiple side-effect steps (DB + API + email) | Only when write-steps precede other fallible steps | Always for external API calls (broker trades) |
| **Compensation registration** | Optional `compensation` field in policy step JSON | `compensate()` method on step class (incremental) | Mandatory `compensating_action` on all side-effect steps |
| **Persistence** | Not explicitly detailed | No separate saga log — relies on step status | Dedicated `saga_log` table |

---

## 3. Unique Contributions (Only One Model Proposes)

### 3.1 Unique to ChatGPT

| Contribution | Details |
|---|---|
| **`inputs_schema` on policy** | Policy declares its own input schema (JSON Schema) so external callers know what parameters to provide. Neither Claude nor Gemini include this. |
| **`side_effects: true` on individual step instances** | The flag appears on each step *in the policy JSON*, not just in the registry. This lets the same step type be marked differently in different policies. |
| **`guardrails` block per step** | Step-level guardrail overrides (e.g., `max_recipients: 3`, `require_confirm_if_manual_trigger`). |
| **JMESPath/JSONPath expression language** | Proposes an optional safe expression language for data transformations within the policy. |
| **`concurrency.mode` on policy** | Policy-level setting for handling overlapping runs: `skip`, `queue`, or `reject_manual_when_running`. |
| **Reference to Model Context Shell** | Cites StacklokLabs' MCS for JSON pipeline definitions with tool discovery helpers — unique open-source reference. |
| **CNCF Serverless Workflow DSL** | Deepest analysis of this spec as a schema reference (input/output transformations, export-to-context pattern). |

### 3.2 Unique to Claude

| Contribution | Details |
|---|---|
| **`__init_subclass__` auto-registration** | Zero-boilerplate registry — subclass and it's registered. No decorator, no explicit call. |
| **`on_error` enum per step** | Three clear modes: `fail_pipeline`, `log_and_continue`, `retry_then_fail`. Simpler and more explicit than ChatGPT's block or Gemini's retry arrays. |
| **Rate limiting with specific budgets** | Concrete numbers: 20 policy creations/day, 60 executions/hour, 50 emails/day, 100 SQL queries/hour. Token bucket with SQLite persistence. |
| **SQLCipher PRAGMA ordering** | Explicit note that `PRAGMA key` must come FIRST before WAL/busy_timeout. This is a real gotcha that the others miss. |
| **SQLite authorizer code example** | Most complete authorizer implementation with allowlist approach (default deny, explicit permit for SELECT/READ). |
| **Append-only audit with triggers** | SQL triggers preventing UPDATE/DELETE on audit table. Concrete DDL. |
| **Human-in-the-loop for new policies** | First execution of new/modified policy requires manual GUI approval. Subsequent runs auto-approve if hash unchanged. |
| **"Pivot transaction" framing** | Most clearly articulates email as the point of no return and why compensation is irrelevant for most pipeline shapes. |
| **AgentSpec (ICSE 2026)** | References a second academic paper on runtime enforcement of LLM agent safety — unique citation. |
| **Cordum** | Cites governance-first control plane for AI agents — directly relevant open-source reference unique to Claude. |

### 3.3 Unique to Gemini

| Contribution | Details |
|---|---|
| **ASL (Amazon States Language) foundation** | Models the policy as a full state machine with `start_at`, named `states`, `next` transitions, `end: true`. Most expressive schema. |
| **`Choice` state type** | First-class branching with comparison operators (`numeric_greater_than`, `numeric_less_than`). Investment-specific conditions like "skip rebalance if VIX > 30". |
| **`Map` state type** | Iterate over arrays (e.g., all portfolio positions) with configurable `max_concurrency`. Enables item-level parallelism within a single policy. |
| **`InputPath` / `ResultPath` / `ResultSelector`** | Full ASL-style data filtering: control what goes into a step, what comes out, and where it lands in the context. |
| **`triggers` array (multi-trigger)** | A single policy can have both cron AND event-based triggers. |
| **Startup zombie detection** | On startup, scan for `RUNNING` executions (must be zombies from crash). Auto-resume if last step was read-only; pause if last step had side effects. |
| **System sleep/wake detection** | Electron listens for OS power events (`suspend`/`resume`), notifies Python backend to correct scheduling drift. |
| **`ProcessPoolExecutor` for CPU-bound** | Offload heavy calculations (portfolio optimization) to process pool to avoid blocking the event loop. |
| **Dedicated `saga_log` table** | Persistent log of every side-effect step's action and reversal parameters. Claude and ChatGPT don't have a separate table. |
| **Investment-domain examples** | Only model to provide complete policy JSONs for real use cases: Volatility-Aware Rebalance, Tax-Loss Harvesting Scanner. |
| **Cryptographic policy binding** | Hash the policy JSON, sign/pin it to user's approval. Verify before execution to prevent TOCTOU attacks. |

---

## 4. Quality Assessment

| Dimension | ChatGPT | Claude | Gemini |
|---|---|---|---|
| **Depth** | ★★★★★ — Deepest treatment of each section, most citations | ★★★★☆ — Best practical code examples | ★★★★☆ — Best domain-specific examples |
| **Pragmatism** | ★★★★☆ — Good at "when to use / when not to" | ★★★★★ — Most "ready to implement" | ★★★☆☆ — Most ambitious but potentially over-engineered |
| **Code quality** | ★★★★☆ — Clean Protocol pattern with dataclasses | ★★★★★ — Production-ready snippets with error handling | ★★★☆☆ — More pseudocode, less concrete Python |
| **Schema design** | ★★★★★ — Best JSON example with annotations | ★★★★☆ — Good schema but simpler | ★★★★☆ — Most expressive but harder for LLM |
| **Security** | ★★★★☆ — Good checklist with resource budgets | ★★★★★ — Most complete authorizer + rate limits | ★★★☆☆ — Covers authorizer but less detail |
| **Edge cases** | ★★★★★ — Most comprehensive catalog | ★★★★☆ — Good but shorter | ★★★★☆ — Unique zombie/sleep recovery |
| **Investment context** | ★★☆☆☆ — Generic pipeline examples | ★★★☆☆ — Portfolio report example | ★★★★★ — VIX-based rebalance, tax-loss harvesting |
| **LLM-friendliness** | ★★★★★ — `ref` objects are easiest to validate | ★★★★☆ — Mustache is readable but needs parser | ★★★☆☆ — JSONPath + state machines are hardest |

---

## 5. Recommended Picks Per Area

Based on the synthesis, here are the strongest ideas to carry forward from each model:

| Area | Pick From | Reasoning |
|---|---|---|
| **Policy JSON structure** | **ChatGPT** | Best balance of expressiveness and LLM-authorability. The `{ "ref": "ctx.x" }` pattern is easiest to validate. |
| **Schema versioning** | **ChatGPT** | SemVer + migration module + alias map is the most forward-looking. |
| **Step registry pattern** | **Claude** | `__init_subclass__` is zero-boilerplate and Pythonic. Combined with Pydantic `Params` inner class. |
| **MCP exposure** | **ChatGPT** | Most detailed capability catalog design (`list`, `get`, `validate`). |
| **Error handling** | **Claude** | `on_error` enum is the simplest, clearest model for a sequential pipeline. |
| **Conditional execution** | **Claude**'s `skip_if` | Pragmatic 80% solution. Add Gemini's `Choice` state later if needed. |
| **Security: SQL sandboxing** | **Claude** | Most complete authorizer implementation with default-deny pattern. |
| **Security: rate limiting** | **Claude** | Concrete budgets with SQLite-persisted token bucket. |
| **Security: human-in-the-loop** | **Claude** | First-run approval with hash-based re-approval on modification. |
| **Saga compensation** | **Claude** | "Pivot transaction" framing is the clearest mental model. Keep it simple. |
| **Edge case: zombies** | **Gemini** | Startup scan for orphaned RUNNING states is essential for desktop apps. |
| **Edge case: sleep/wake** | **Gemini** | Electron power event listener is a must-have for desktop. |
| **Investment examples** | **Gemini** | VIX-based rebalance and tax-loss harvesting are the most domain-relevant. |
| **Future expressiveness** | **Gemini** | If you ever need `Choice`/`Map`/state-machine, Gemini's ASL foundation is the upgrade path. |
| **Data filtering** | **Gemini** | `InputPath`/`ResultPath`/`ResultSelector` from ASL is the most granular data flow control. |
| **`inputs_schema` on policy** | **ChatGPT** | Policy self-describes its inputs — essential for external callers and LLM context. |
| **Concurrent execution limits** | **ChatGPT** | `concurrency.mode` at policy level handles overlap beyond just APScheduler's `max_instances`. |

---

## 6. Open Questions for Build Plan

These are areas where the three models don't converge enough to make a definitive call:

1. **Data referencing syntax**: `{ "ref": "ctx.x" }` vs `{{steps.x.output}}` vs JSONPath — needs a decision based on LLM authoring tests.
2. **Branching complexity**: Start with `skip_if` (Claude) or go straight to full state machine (Gemini)?
3. **Step version in policy JSON**: Include `type_version` per step (ChatGPT) or handle it purely in the registry?
4. **Plugin architecture**: Entry points (ChatGPT), import scanning (Claude), or `plugins/` directory (Gemini)?
5. **`saga_log` table**: Separate persistence (Gemini) or rely on step status records (Claude)?
6. **Schema version integer vs SemVer**: Simpler integer (Claude) or richer SemVer (ChatGPT/Gemini)?
