# ChatGPT Deep Research Prompt — Pipeline Code Patterns & Testing

> **Platform**: ChatGPT → use **Deep Research** mode (select from model picker)
> **Why ChatGPT**: Leverages GPT-5.4's strength in agentic coding — autonomous planning, iterative code generation, production-grade Python patterns, and practical implementation examples. ChatGPT excels at depth on code — generating working, copy-paste-ready implementations rather than theory.
> **Model**: GPT-5.4 Thinking or GPT-5.4 Pro with Deep Research
> **Expected time**: 5–30 minutes

---

## Instructions for ChatGPT Deep Research

I need a code-heavy research report. For every pattern or recommendation, provide **actual Python 3.12+ async code** — not pseudocode, not prose descriptions. Show working implementations that could be adapted into our codebase. Use type hints, `async/await`, Pydantic v2, and modern Python throughout.

---

## The Prompt

You are a senior Python systems engineer specializing in async pipeline architectures and integration testing for financial applications. I need production-ready code patterns for improving our pipeline engine's dependency injection, testing strategy, and observability layer.

### Context: Our Current Architecture (Zorivest)

**Zorivest** is a desktop investment portfolio management platform:
- **Stack**: Python 3.12, FastAPI, SQLAlchemy 2.x (async), SQLCipher, APScheduler 3.x, Pydantic v2
- **Runtime**: Single-process asyncio. Electron + React frontend. No cloud, no distributed systems.
- **AI Integration**: MCP server where AI agents author `PolicyDocument` JSON → engine executes
- **Purpose**: Fetch market data → transform → generate reports → render PDF/HTML → send email. Does NOT execute trades.

#### Pipeline Engine Implementation

```python
# Simplified view of our current architecture

class StepBase:
    """All steps implement this protocol via __init_subclass__ auto-registration."""
    type_name: ClassVar[str]
    side_effects: ClassVar[bool]

    class Params(BaseModel):  # Each step defines its own Pydantic params
        pass

    async def execute(self, ctx: StepContext, params: dict) -> StepResult:
        ...

class PipelineRunner:
    """Sequential async executor — the core orchestration engine."""
    def __init__(
        self,
        session: AsyncSession,
        pipeline_repo: PipelineRepository,
        policy_repo: PolicyRepository,
        market_data_adapter: MarketDataProviderAdapter,
        rate_limiter: PipelineRateLimiter,
        email_config: EmailConfig,
        template_engine: TemplateEngine,
        audit_logger: AuditLogger,
        # ... 8+ injected dependencies
    ):
        self._deps = ...  # stored for step access

    async def execute_run(self, run_id: UUID, policy: PolicyDocument) -> RunResult:
        for step_def in policy.steps:
            step_cls = STEP_REGISTRY[step_def.type]
            ctx = StepContext(run_id=run_id, outputs=self._outputs, ...)

            if self._should_skip(step_def, ctx):
                continue

            result = await asyncio.wait_for(
                step_cls.execute(ctx, step_def.params),
                timeout=step_def.timeout_seconds
            )
            self._outputs[step_def.id] = result
```

**5 Step Types**: Fetch (HTTP + rate limiting + caching), Transform (Pandera validation + field mapping), Store Report (frozen snapshots + SHA-256 + SQL sandboxing), Render (Jinja2 + WeasyPrint + Plotly), Send (aiosmtplib + delivery tracking + idempotent dedup)

**Cross-cutting**: RefResolver for `{ "ref": "ctx.x.y.z" }`, ConditionEvaluator for `skip_if`, PolicyValidator, cooperative cancellation (CANCELLING status + task registry), zombie detection, sleep/wake handling, structlog with contextvars, append-only audit log, human-in-the-loop approval.

**Key libraries**: `aiolimiter`, `tenacity`, `pandera`, `WeasyPrint`, `plotly`+`kaleido`, `aiosmtplib`, `structlog`, `httpx`

---

### Research Topic 1: Service Layer Wiring — Dependency Injection Patterns (PRIMARY)

Our `PipelineRunner.__init__` accepts 8+ keyword params. This works but doesn't scale well.

**Research and provide working Python code for each of these DI patterns**:

#### 1a. Scoped Resource Container
Show a `RunContext` or `ResourceScope` that manages per-run lifecycle of DB sessions, HTTP clients, SMTP connections. Include `async with` context manager pattern for automatic cleanup.

```python
# I want to see something like:
class PipelineResources:
    """Manages lifecycle of all pipeline dependencies for a single run."""
    session: AsyncSession
    http_client: httpx.AsyncClient
    rate_limiter: PipelineRateLimiter
    # ...

    async def __aenter__(self): ...
    async def __aexit__(self, *exc): ...
```

#### 1b. Step Factory Pattern
Show how steps should be instantiated — per-run (fresh instance) vs singleton (reused). Include pros/cons with code for each approach. Show how a factory injects the right dependencies per step type.

#### 1c. Dagster-Style Resources
Adapt Dagster's `ConfigurableResource` pattern for our use case. Show how per-provider config (Yahoo rate limits vs Polygon rate limits) layers with per-run config.

#### 1d. Configuration Scoping
Show a layered config system:
- Global defaults → Provider-specific → Step-specific → Run-specific override
- With Pydantic v2 model inheritance and `model_config` merging

#### 1e. Saga Compensation in Single-Process
Show a practical `compensate()` implementation for our side-effect steps (Store/Render/Send). When is compensation worth the complexity? Show the code and make the case.

---

### Research Topic 2: Live Data Testing — Working Test Examples (PRIMARY)

Provide **complete, runnable pytest fixtures and test functions** for each strategy:

#### 2a. VCR/Cassette Recording with `respx`
```python
# Show a complete test that:
# 1. Records a real Yahoo Finance API response
# 2. Replays it in CI
# 3. Scrubs API keys from headers
# 4. Detects schema drift (response shape changed)
```

#### 2b. Contract Tests Between Pipeline Steps
```python
# Show Pydantic-based contract tests:
# 1. FetchStep output contract → TransformStep input contract
# 2. TransformStep output contract → StoreStep input contract
# 3. Auto-generated from our existing Pydantic models
# 4. Breaking change detection
```

#### 2c. Golden File Testing for Pipeline Stages
```python
# Show:
# 1. How to create golden files from a known pipeline run
# 2. How to handle non-deterministic fields (timestamps, UUIDs)
# 3. How to update golden files when schemas intentionally change
# 4. pytest plugin or fixture for golden file comparison
```

#### 2d. Semi-Synthetic Financial Data with Hypothesis
```python
# Show Hypothesis strategies for:
# 1. Realistic OHLCV data (open <= high, low <= close, volume >= 0)
# 2. Quote data matching Yahoo Finance response shape
# 3. Portfolio position data with valid tickers and quantities
# 4. Edge cases: stock splits, missing data, after-hours
```

#### 2e. Shadow Pipeline Runs
```python
# Show:
# 1. A "shadow mode" decorator/flag that fetches real data but doesn't persist
# 2. Assertion framework for shadow run output quality
# 3. Comparison between shadow and production outputs
```

#### 2f. Provider Schema Drift Detection
```python
# Show:
# 1. Schema fingerprinting (hash response shapes, alert on change)
# 2. Automated CI job that hits real APIs weekly to detect drift
# 3. Graceful degradation when schema changes detected
```

---

### Research Topic 3: Framework Comparison — Code Patterns Only

For these 4 frameworks, show the **actual code pattern** for defining and executing a 5-step pipeline similar to ours:

1. **LangGraph** — State machine with conditional edges
2. **Temporal** — Workflow + Activities
3. **Prefect** — Tasks with retries and caching
4. **Dagster** — Ops with resources and IO managers

For each, show:
- How our Fetch→Transform→Store→Render→Send chain would look
- How dependencies (DB session, HTTP client) are injected
- How errors and retries are configured
- How the pipeline is tested

Then show a **side-by-side comparison** of 20 lines of code from each framework doing the same thing.

---

### Research Topic 4: Observability — Instrumentation Code

#### 4a. OpenTelemetry for Async Pipelines
```python
# Show:
# 1. Tracer setup for a single-process app (no collector needed)
# 2. Span creation for pipeline run → step → HTTP call hierarchy
# 3. Integration with structlog (trace_id in log entries)
# 4. Export to local JSON file for debugging
```

#### 4b. Pipeline Metrics
```python
# Show:
# 1. Step duration histogram (per step type)
# 2. Success/failure counter (per step, per provider)
# 3. Data volume gauge (records fetched/transformed per run)
# 4. Cache hit rate (fetch cache effectiveness)
# Using prometheus_client for local metrics (no server needed)
```

#### 4c. Circuit Breaker for Providers
```python
# Show:
# 1. Circuit breaker that tracks provider health across runs
# 2. States: CLOSED → OPEN → HALF_OPEN
# 3. Integration with our per-step retry logic
# 4. Persistent state (survives app restart) via SQLite
```

---

### Research Topic 5: Gap Analysis — Step Type Proposals

For each candidate missing step type, show a **concrete implementation skeleton** with Pydantic Params, execute method, and integration with our step registry:

1. **Aggregation/Calculation step** — portfolio returns, risk metrics
2. **Notification step** — desktop notifications via Electron IPC
3. **Export step** — CSV/Excel generation
4. **Archive/Cleanup step** — data retention enforcement
5. **Validation/Assertion step** — output quality gates
6. **Enrichment step** — multi-source data joining
7. **Branch/Fork step** — conditional sub-pipelines
8. **Wait/Gate step** — market hours / dependency gating

For each: is it v1-critical or deferrable? Show the step class skeleton.

---

### Output Format

For every recommendation:
1. **Working Python 3.12+ code** with type hints, async/await, Pydantic v2
2. **Before/After comparison** showing our current pattern vs the recommended pattern
3. **Risk/benefit assessment** in a table (complexity cost vs value gained)
4. **"If we adopt one thing" recommendation** per topic
5. **Anti-patterns for desktop apps** — things that apply to cloud but hurt us

### Constraints

- Single process (no message queues, no K8s, no distributed workers)
- SQLCipher encrypted DB (all data at rest)
- Desktop app (sleep/wake, USB-drive portability)
- Financial data (Decimal precision, audit trail mandatory)
- AI-authored policies (sandboxed via MCP)
- ~50 API calls/run (modest rate limits)
- Python 3.12+ (`asyncio.TaskGroup`, `ExceptionGroup`, `type` statement)
