# Gemini Deep Research Prompt — Pipeline Architecture Discovery

> **Platform**: Google Gemini → use **Deep Research** tool (Tools menu)
> **Why Gemini**: Leverages multi-round web crawling across hundreds of sources, structured report generation with citations, and visual/interactive output. Gemini excels at breadth — surveying many frameworks, repos, and documentation sites to create comprehensive comparison tables with source verification.
> **Model**: Gemini 3.1 Pro with Deep Research
> **Expected time**: 5–10 minutes per research run

---

## Instructions for Gemini Deep Research

Use the Deep Research tool for this prompt. I need a comprehensive, fully-cited research report that surveys real open-source projects and documentation. Browse GitHub repositories, official framework docs, and recent blog posts/conference talks. Prioritize primary sources (official docs, source code) over secondary sources (blog summaries).

---

## The Prompt

Act as a senior AI systems architect performing a comprehensive technology survey. I need you to research how modern agentic AI frameworks and workflow engines handle **policy execution**, **pipeline orchestration**, and **external data integration testing** — then compare them to our existing architecture.

### Context: What We've Built (Zorivest)

**Zorivest** is a desktop investment portfolio management platform. Key facts:
- **Backend**: Python 3.12, FastAPI, SQLAlchemy, SQLCipher (encrypted SQLite), APScheduler 3.x
- **Frontend**: Electron + React + TypeScript
- **AI Interface**: Model Context Protocol (MCP) server — AI agents author pipeline policies as declarative JSON
- **Architecture**: Single-process async (asyncio). No cloud, no distributed systems, no microservices.
- **Purpose**: Fetches market data, generates investment reports, sends email summaries. Does NOT execute trades.

#### Our Pipeline Engine

A **declarative JSON policy engine** where AI agents author `PolicyDocument` JSON. The engine executes policies sequentially through registered step types:

**Execution model**: Sequential `async for step in steps: await step.execute(ctx)` with shared `StepContext` dict.

**5 Pipeline Step Types**:

| Step | What It Does |
|------|--------------|
| **Fetch** | HTTP fetch from market data providers (Yahoo, Polygon, Finnhub) via provider-specific URL builders; `aiolimiter` rate limiting + `tenacity` retries; fetch cache with market-session-aware TTLs; incremental high-water marks |
| **Transform** | Pandera DataFrame validation; provider→canonical field mapping; `source_step_id` for dynamic predecessor resolution; `min_records` threshold; write dispositions (append/replace/merge) |
| **Store Report** | Generate `ReportModel` with frozen data snapshot; SHA-256 integrity hash; versioned via SQL triggers; SQL-sandboxed queries via `set_authorizer` + `PRAGMA query_only` |
| **Render** | Jinja2 HTML + WeasyPrint PDF + Plotly/Kaleido chart export; deterministic rendering keyed by content hash |
| **Send** | `aiosmtplib` async email; Jinja2 body templates; `report_delivery` tracking with SHA-256 dedup key; idempotent sends |

**Cross-Cutting Infrastructure**: `PipelineRunner` (timeout, retry, dry-run, resume), cooperative cancellation (`CANCELLING` status + task registry), `RefResolver` for `{ "ref": "ctx.x.y.z" }` context references, `ConditionEvaluator` (10 operators for `skip_if`), provider-specific URL builder registry, `PolicyValidator` (schema + referential integrity + SQL blocklist), SHA-256 content hash integrity, append-only audit log, human-in-the-loop approval, zombie detection at startup, sleep/wake handler (Electron `powerMonitor`), structlog with `contextvars` correlation.

**Design decisions**: `__init_subclass__` auto-registration, per-step `on_error` enum (`fail_pipeline`, `log_and_continue`, `retry_then_fail`), step type allowlist, email recipient limits.

---

### Research Topic 1: Framework Comparison Survey (PRIMARY — use your web crawling strength)

**Browse and compare** these 8 frameworks. For each, I need you to visit their GitHub repos, official documentation, and recent release notes:

1. **LangGraph** (LangChain) — `github.com/langchain-ai/langgraph`
2. **Temporal** — `github.com/temporalio/temporal` + `docs.temporal.io`
3. **Prefect** — `github.com/PrefectHQ/prefect` + `docs.prefect.io`
4. **Dagster** — `github.com/dagster-io/dagster` + `docs.dagster.io`
5. **CrewAI** — `github.com/crewAIInc/crewAI`
6. **AutoGen** — `github.com/microsoft/autogen`
7. **Mastra** — `github.com/mastra-ai/mastra`
8. **Rivet** — `github.com/Ironclad/rivet`

For each framework, document in a comparison table:

| Dimension | Details to Capture |
|-----------|-------------------|
| **Policy vs Execution separation** | How is the workflow definition (what to do) separated from the runtime (how to do it)? Is it declarative JSON/YAML, code-first, or visual? |
| **State management** | How is inter-step state passed? Context dict? Event bus? Shared store? Checkpointing? |
| **Error recovery** | Retries, compensation, saga patterns, dead letter handling |
| **Cancellation** | How are running workflows gracefully stopped? |
| **Idempotency** | How are duplicate executions prevented after retry/resume? |
| **Observability** | Built-in tracing, metrics, structured logging, dashboard UIs |
| **Testing story** | How does the framework recommend testing workflows? Mock strategies, replay testing |
| **Desktop viability** | Could this run in a single-process desktop app (no cloud infra)? |

**Specifically identify**:
- Patterns we should adopt for our `PipelineRunner`
- Anti-patterns we might be following unknowingly
- Architectural blind spots in our sequential async model

---

### Research Topic 2: Service Layer Wiring Patterns

Survey how the frameworks above handle dependency injection for pipeline steps. Compare:
- Temporal's activity dependency injection
- Prefect's task parameter passing
- Dagster's `Resources` and `ConfigurableResource`
- LangGraph's state injection

Provide a comparison table showing which pattern best fits a single-process async Python app that needs to inject: DB sessions, HTTP clients, SMTP config, rate limiters, cache repos, template engines, and audit loggers.

---

### Research Topic 3: Live Data Testing Strategies

**Search for real open-source projects** that test data pipelines against live external APIs. Find examples of:

1. **VCR/cassette testing** — projects using `vcrpy`, `respx`, `pytest-recording` for HTTP response recording
2. **Contract testing** — projects using Pact, Schemathesis, or custom contracts between pipeline stages
3. **Golden file testing** — snapshot-based pipeline testing with deterministic outputs
4. **Semi-synthetic financial data** — projects generating realistic OHLCV/quote data for testing
5. **Shadow/canary pipeline runs** — non-destructive validation against real data
6. **Schema drift detection** — monitoring external API response shape changes

For each, cite the specific GitHub repo, the relevant code files, and explain how it works.

---

### Research Topic 4: Pipeline Observability Patterns

Survey observability implementations in data pipeline frameworks. Cover:
1. **OpenTelemetry instrumentation** for async Python pipelines
2. **Circuit breaker patterns** for degraded external providers
3. **Pipeline DAG visualization** tools (Mermaid, Gantt, flame graphs)
4. **Metrics that matter** for data pipelines (step durations, success rates, data volumes, cache hit rates)

---

### Research Topic 5: Missing Operations Gap Analysis (PRIMARY — use your breadth)

Given our 5 step types (Fetch, Transform, Store Report, Render, Send), survey personal finance and investment management platforms to identify if we're missing critical pipeline operations:

1. **Aggregation/Calculation step** — portfolio returns, risk metrics, rebalancing
2. **Notification step** — desktop notifications, webhooks (beyond email)
3. **Export step** — CSV/Excel, API push
4. **Archive/Cleanup step** — data retention, cache garbage collection
5. **Validation/Assertion step** — pipeline output quality gates
6. **Enrichment step** — joining data from multiple sources
7. **Branch/Fork step** — conditional sub-pipelines
8. **Wait/Gate step** — waiting for market open or another pipeline

For each, explain: why needed, how it integrates with our step registry, and whether it's v1-critical.

---

### Output Format

Produce a structured report with:
- **Comparison tables** with framework names in columns and dimensions in rows
- **Source citations** for every claim (link to specific GitHub files, docs pages, or blog posts)
- **"If we adopt one thing" recommendation** per topic — the single highest-impact pattern
- **Anti-patterns section** — specifically things that apply to cloud-native but NOT single-process desktop apps
- **Visual diagrams** where helpful (Mermaid flowcharts for architecture comparisons)

### Constraints

- Single process (no message queues, no K8s, no distributed workers)
- SQLCipher encrypted DB (all data at rest)
- Desktop app (sleep/wake, USB-drive portability, process crashes)
- Financial data (Decimal precision, audit trail mandatory)
- AI-authored policies (sandboxed, validated via MCP)
- ~50 API calls/run (modest rate limits)
- Python 3.12+ (modern asyncio features available)
