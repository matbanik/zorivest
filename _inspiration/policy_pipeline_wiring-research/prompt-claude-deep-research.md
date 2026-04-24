# Claude Research Prompt — Strategic Architecture Analysis

> **Platform**: Claude.ai → use **Opus 4.7** model (select from model picker)
> **Why Claude**: Leverages Opus 4.7's strength in strategic reasoning, self-verification, precise instruction following, and financial domain analysis. Claude excels at depth over breadth — adversarial analysis, constraint verification, risk matrices, and architectural decision records. Its Adaptive Thinking automatically allocates reasoning depth to match problem complexity.
> **Model**: Claude Opus 4.7 with Adaptive Thinking (set effort to `xhigh` if available)
> **Approach**: Claude doesn't have a branded "Deep Research" tool — instead, use a single detailed prompt in a Project with web search enabled. Claude's strength is in reasoning through the material analytically, not crawling hundreds of sources.

---

## Instructions for Claude

I need a strategic architectural analysis, not a survey. For every recommendation, I need you to:
1. **Verify it against our specific constraints** (single-process, SQLCipher, desktop, financial data)
2. **Stress-test the recommendation** — what could go wrong? What's the failure mode?
3. **Provide an Architectural Decision Record (ADR)** for each major recommendation
4. **Rank by risk-adjusted value** — not just "this is good practice" but "this is worth the complexity for our specific case"

Use web search to verify current best practices, framework capabilities, and library API surfaces. Do not rely on stale training data for framework version details.

---

## The Prompt

You are a principal software architect performing an adversarial review of a pipeline engine's architecture. Your goal is to identify **architectural risks**, **missing failure modes**, and **strategic improvements** — ranked by risk-adjusted value for a single-process desktop application. Be skeptical. Challenge assumptions. Verify constraints.

### Context: Our System (Zorivest)

**Zorivest** is a desktop investment portfolio management platform:
- **Stack**: Python 3.12, FastAPI, SQLAlchemy 2.x (async), SQLCipher (encrypted SQLite), APScheduler 3.x, Pydantic v2
- **Runtime**: Single-process asyncio event loop. Electron + React frontend via localhost HTTP.
- **AI Integration**: MCP server — LLMs author `PolicyDocument` JSON → deterministic engine executes pre-registered step types
- **Purpose**: Fetch market data → transform/validate → generate reports → render PDF/HTML → email delivery. **Does NOT execute trades** — plans and evaluates only.
- **Security model**: Default-deny SQL authorizer, step type allowlist, content hash integrity, append-only audit log, human-in-the-loop approval for new/modified policies

#### Pipeline Architecture

**Execution model**: Sequential `async for step in steps: await step.execute(ctx)` with shared `StepContext` dict for inter-step data flow via `RefResolver` (`{ "ref": "ctx.fetch_prices.output.quotes" }`).

**Step registry**: `__init_subclass__` auto-registration. Each step type declares `type_name`, `side_effects` bool, and a Pydantic `Params` inner class.

**5 Step Types**:

| Step | `side_effects` | Key Behaviors |
|------|:--------------:|---------------|
| **Fetch** | `False` | Per-provider URL builder registry (Yahoo/Polygon/Finnhub + GenericUrlBuilder); `aiolimiter` + `tenacity`; market-session-aware TTL cache; incremental high-water marks via `pipeline_state` table |
| **Transform** | `False` | Pandera DataFrame validation; provider→canonical field mapping; `source_step_id` dynamic predecessor resolution; `min_records` threshold; write dispositions (append/replace/merge) |
| **Store Report** | `True` | Frozen data snapshot; SHA-256 integrity hash; SQL triggers for versioning; `set_authorizer` + `PRAGMA query_only` sandboxing |
| **Render** | `True` | Jinja2 + WeasyPrint PDF + Plotly/Kaleido charts; deterministic rendering by content hash |
| **Send** | `True` | `aiosmtplib` async email; `EMAIL_TEMPLATES` registry; `report_delivery` tracking with SHA-256 dedup key |

**Error handling**: Per-step `on_error` enum — `fail_pipeline` | `log_and_continue` | `retry_then_fail`.

**Cross-cutting infrastructure**:
- `PipelineRunner` — async executor with timeout, retry, dry-run, resume-from-failure
- Cooperative cancellation — `CANCELLING` status + `_active_tasks` task registry + `cancel_run()`
- `ConditionEvaluator` — 10 operators for `skip_if` branching
- `PolicyValidator` — schema version + step type existence + referential integrity + SQL blocklist
- Zombie recovery — startup scan for orphaned `RUNNING` executions
- Sleep/wake — Electron `powerMonitor` → APScheduler `wakeup()`
- structlog with `contextvars` for `run_id` correlation

**DI approach**: `PipelineRunner.__init__` accepts 8+ keyword params (repos, adapters, configs). Steps receive a `StepContext` (runtime) + `params` dict (policy-defined).

---

### Research Topic 1: Architectural Risk Analysis (PRIMARY — use your analytical depth)

Perform an adversarial review of our pipeline architecture. For each risk, provide:
- **Risk description** — what can go wrong
- **Likelihood** (Low/Medium/High) — given our constraints (single-user desktop, ~50 API calls/run)
- **Impact** (Low/Medium/High) — data loss? Silent corruption? User-visible error?
- **Current mitigation** — what we already have
- **Recommended mitigation** — what we should add
- **ADR** — Architectural Decision Record (Status, Context, Decision, Consequences)

Specifically investigate these risk categories:

#### 1a. Data Integrity Risks
- Can `RefResolver` return stale/wrong data if a previous step's output is mutated after being stored in the context dict? (Mutable dict aliasing problem)
- Can `ConditionEvaluator` produce unexpected results with edge cases (null values, missing fields, type coercion)?
- Can the SHA-256 content hash be accidentally bypassed? What happens if the hash check fails mid-run?
- Is our `INSERT OR IGNORE` dedup strategy correct for all data types, or could it silently drop valid records?

#### 1b. Concurrency Risks (Single-Process)
- Can `asyncio.wait_for` timeout leave resources in an inconsistent state?
- Can cooperative cancellation miss a window where a side-effect step has partially committed?
- Can the fetch cache serve stale data if TTL calculation has timezone bugs?
- Can APScheduler fire overlapping runs despite `max_instances=1` if the Python process is suspended/resumed?

#### 1c. Security Risks (AI-Authored Policies)
- Can a malicious policy document bypass the SQL authorizer via clever SQL construction?
- Can `RefResolver` be used to exfiltrate data from one policy's context into another?
- Can the `GenericUrlBuilder` be used to make requests to internal network endpoints (SSRF)?
- Can email templates be used for injection attacks (HTML injection, header injection)?

#### 1d. Operational Risks
- What happens if SQLCipher key derivation (PBKDF2, 64K iterations) blocks the event loop during pipeline execution?
- What happens if WeasyPrint hangs on malformed HTML (it shells out to system libraries)?
- What happens if `aiosmtplib` connection hangs indefinitely?
- What happens if the Electron process kills Python mid-write to SQLCipher?

---

### Research Topic 2: Service Layer Wiring — Tradeoff Analysis (PRIMARY)

Don't just show DI patterns — analyze the **tradeoffs** for our specific constraints.

#### Question 2a: Should we use a DI container library?
Compare: manual injection (current) vs `dependency-injector` vs `dishka` vs `that-depends` vs Dagster-style resources.
- **For each**: What's the learning curve? Does it work with asyncio? Does it add meaningful complexity for a single-process app with ~8 dependencies?
- **Your verdict**: Is a DI library worth it for us, or is manual injection the right call at our scale?

#### Question 2b: Step instantiation — per-run or singleton?
- What are the memory implications of creating fresh `FetchStep`, `TransformStep` instances per run?
- What are the thread-safety implications of reusing step instances across concurrent APScheduler runs (remembering `max_instances=1` should prevent this, but what if it fails)?
- **Your verdict**: Which approach, considering our constraints?

#### Question 2c: The 8-parameter `__init__` problem
- Is our `PipelineRunner.__init__` with 8+ params a code smell that will get worse, or is it appropriate for our scale?
- Compare: parameter object, builder pattern, protocol-based injection
- **Your verdict**: At what dependency count should we refactor, and to what pattern?

#### Question 2d: Saga compensation — is it worth it?
- We have 3 side-effect steps (Store, Render, Send). If Send fails after Store+Render succeeded, should we compensate?
- In our domain (report generation, not financial transactions), what's the actual cost of partial completion?
- **Your verdict**: Implement saga compensation or just log-and-alert?

---

### Research Topic 3: Live Data Testing — Strategic Analysis (PRIMARY)

Analyze testing strategies **ranked by risk-adjusted value** for our specific case.

#### Question 3a: Which testing strategy gives us the most coverage per engineering hour?
Rank these from highest to lowest ROI, with justification:
1. VCR/cassette recording (replay real responses)
2. Contract testing between steps (Pydantic-based)
3. Golden file testing (snapshot comparison)
4. Hypothesis property-based testing (synthetic financial data)
5. Shadow pipeline runs (real data, no side effects)
6. Schema drift monitoring (weekly CI checks against live APIs)

For each:
- **Setup cost** (hours to implement)
- **Maintenance burden** (hours/month)
- **Failure coverage** (what class of bugs does it catch?)
- **False positive rate** (how often will it break for non-bug reasons?)

#### Question 3b: The "provider changed their API" problem
Yahoo Finance, Polygon, and Finnhub can change their response format without notice. What's the most cost-effective way to detect this before our users do? Consider:
- CI schedule (daily? weekly?)
- Alert mechanism (desktop app — no PagerDuty)
- Graceful degradation (what should the pipeline do when it detects drift?)

#### Question 3c: Testing email sending without sending email
Our `SendStep` uses `aiosmtplib`. How do we test:
- Template rendering correctness
- MIME structure validity
- Attachment handling (PDF reports)
- Delivery tracking idempotency
Without actually sending emails or mocking so heavily that tests become meaningless?

---

### Research Topic 4: Observability — Architectural Fit Analysis

#### Question 4a: OpenTelemetry — overkill for single-process?
- We have structlog with `contextvars` for `run_id` correlation. Is OpenTelemetry worth adding?
- What's the operational cost of running OTel with no collector (export to local file)?
- **Your verdict**: OTel traces, or just better structured logging?

#### Question 4b: Circuit breaker — right pattern for us?
- We have `tenacity` retries per step. A circuit breaker tracks provider health across runs.
- With only ~50 API calls/run and 3 providers, is a circuit breaker over-engineering?
- **Your verdict**: Circuit breaker, or just a "provider health log" that humans review?

#### Question 4c: Dead letter queue — in a desktop app?
- Failed records are currently logged. Should they be quarantined in a separate table for manual review?
- In our single-user desktop context, who reviews the DLQ?
- **Your verdict**: DLQ table, or just better error reporting in the GUI?

---

### Research Topic 5: Gap Analysis — Adversarial Review

For each candidate missing step type, perform an **adversarial analysis**:

| Candidate Step | Your Analysis |
|---------------|---------------|
| **Aggregation/Calculation** | Is this a separate step type, or should Transform handle it? What's the domain argument? |
| **Notification** (beyond email) | In a desktop app, is Electron's notification API sufficient, or do we need a pipeline step? |
| **Export** (CSV/Excel) | Is this a Render sub-type, or does it need its own step with different lifecycle? |
| **Archive/Cleanup** | Should this be a pipeline step or a scheduled maintenance job outside the policy engine? |
| **Validation/Assertion** | Beyond Pandera, do we need pipeline-level quality gates? What would trigger them? |
| **Enrichment** | Is multi-source joining a Transform responsibility, or does it need parallel fetch + join semantics? |
| **Branch/Fork** | Does `skip_if` cover our branching needs, or are there real use cases for sub-pipelines? |
| **Wait/Gate** | Should pipelines wait for conditions, or should scheduling handle timing? |

For each: **argue both sides**, then give your verdict with justification.

---

### Output Format

Structure your response as:

1. **Executive Summary** — top 3 risks and top 3 recommendations, one paragraph each
2. **Risk Matrix** — all identified risks in a table (Likelihood × Impact × Current Mitigation × Recommendation)
3. **ADRs** — one per major recommendation (Status, Context, Decision, Consequences format)
4. **Testing Strategy Ranking** — ordered by risk-adjusted ROI with hours estimates
5. **Gap Analysis Verdicts** — for/against arguments with final recommendation
6. **"If we do one thing" list** — single highest-impact action per topic
7. **Anti-patterns for desktop apps** — cloud patterns that would hurt us

### Constraints (verify every recommendation against these)

- **Single process**: No message queues, no distributed workers, no Kubernetes
- **SQLCipher**: All data encrypted at rest in a single DB file. PBKDF2 key derivation is expensive.
- **Desktop app**: Must handle sleep/wake, process crashes, USB-drive portability
- **Financial data**: `Decimal` precision required. Audit trail is mandatory and append-only.
- **AI-authored policies**: Written by LLMs via MCP. Must be sandboxed and validated before execution.
- **~50 API calls/run**: Modest scale. Over-engineering distributed patterns is a real risk.
- **Single user**: No multi-tenancy. The human reviews errors in the GUI, not a NOC.
- **Python 3.12+**: Modern asyncio features available (`TaskGroup`, `ExceptionGroup`)
