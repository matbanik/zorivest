# Designing a local-first investment pipeline with AI-driven policy orchestration

**A single-process Electron + Python/FastAPI + SQLCipher desktop application can orchestrate a full Fetch → Transform → Store Report → Render → Send pipeline using APScheduler, with an AI agent authoring policies through MCP tool calls.** The architecture avoids distributed systems entirely, relying on asyncio concurrency within one Python process, a decorator-based provider registry, and a custom async pipeline engine that outperforms heavier orchestrators like Prefect for this use case. This report covers concrete patterns, code architecture, and library choices for each stage, optimized for SQLite/SQLCipher constraints and the Python async ecosystem.

---

## Stage 1: Criteria-driven multi-source data fetching

The Fetch stage resolves *what* to fetch at runtime from a declarative policy JSON, then fans out requests across providers with per-provider rate limiting.

### Policy JSON and dynamic criteria resolution

A fetch policy should be a declarative JSON document that the engine resolves against database state at runtime. Four criteria types cover all investment use cases:

- **DB entity reference** (`"type": "db_query"`): resolves `"SELECT ticker FROM watchlist WHERE active = 1"` against SQLCipher at execution time
- **Date-relative parameters** (`"type": "relative"`): `"-30d"` resolved via `datetime.now() + timedelta(days=-30)`
- **DB join criteria** (`"type": "db_join"`): `"SELECT DISTINCT ticker FROM positions WHERE quantity > 0"` dynamically determines which tickers need data
- **Incremental/delta** (`"type": "incremental"`): stores a high-water mark cursor (like dlt's `dlt.sources.incremental`) in a `fetch_state` table — `(resource_id, cursor_field, last_value, last_run_at)` — fetching only records newer than the cursor

A lightweight `CriteriaResolver` class uses Python's `match/case` to dispatch on criteria type, executing queries against SQLCipher and resolving date arithmetic. This is far simpler than importing Dagster or Prefect's parameter systems, which are designed for distributed environments.

```python
FETCH_POLICY = {
    "fetch_jobs": [{
        "id": "watchlist_ohlcv",
        "provider": "yahoo_finance",
        "data_type": "ohlcv",
        "criteria": {"type": "db_query", "query": "SELECT ticker FROM watchlist WHERE active = 1"},
        "params": {"period": {"type": "relative", "value": "-30d"}, "interval": "1d"},
        "freshness": {"max_age_seconds": 14400}
    }]
}
```

### Provider abstraction with Protocol + decorator registry

The provider interface uses **`typing.Protocol` (PEP 544)** for structural subtyping, enabling duck-typed providers without inheritance coupling. A **decorator-based registry** is the cleanest pattern for a single-process app — providers self-register at import time, requiring zero configuration:

```python
@runtime_checkable
class FetchProvider(Protocol):
    @property
    def name(self) -> str: ...
    @property
    def supported_data_types(self) -> frozenset[DataType]: ...
    @property
    def rate_limit(self) -> tuple[int, float]: ...  # (max_requests, per_seconds)
    async def fetch(self, request: FetchRequest) -> FetchResult: ...
```

The `ProviderRegistry` maintains two indexes: by name and by data type. This enables both explicit provider selection (`"provider": "alpha_vantage"`) and automatic discovery (`"provider": "auto"` — pick the first available provider for the requested data type). Provider configuration (API keys, rate limits, base URLs) lives in a `provider_config` table in SQLCipher. Since the database is already encrypted at rest, API keys are protected without additional encryption.

Alternative plugin systems — **pluggy** (used by pytest), **stevedore** (OpenStack), and `importlib.metadata.entry_points` — are all overkill for ~5–10 built-in providers. The decorator registry has zero dependencies and works perfectly for single-process apps.

### Rate limiting and parallel fetch execution

Financial APIs impose strict rate limits: **Alpha Vantage allows 5 requests/minute** on free tier, Yahoo Finance approximately 2,000/hour, and Polygon.io 5/minute free. The architecture needs *both* a rate limiter and a concurrency limiter per provider, because a rate limiter alone permits burst concurrent requests that exceed connection limits, while a semaphore alone doesn't enforce time-based quotas.

The recommended stack: **`aiolimiter` (v1.2.1)** for leaky-bucket rate limiting, **`asyncio.Semaphore`** for concurrency caps, and **`tenacity` (v9.x)** for retry with `wait_random_exponential` (full jitter per AWS best practice). Fetch execution groups jobs by provider, then runs all provider groups in parallel via `asyncio.gather`, while each provider's requests are individually gated through its limiter/semaphore pair. Transient errors (429, 5xx, timeouts) trigger retries; permanent errors (404, invalid ticker) are logged and skipped.

```python
@retry(
    stop=stop_after_attempt(5),
    wait=wait_random_exponential(multiplier=1, max=60),
    retry=retry_if_exception_type((RateLimitError, aiohttp.ClientError)),
)
async def fetch_with_retry(session, url, limiter):
    async with limiter.concurrency_sem:
        async with limiter.rate_limiter:
            async with session.get(url) as resp:
                if resp.status == 429:
                    raise RateLimitError()
                return await resp.json()
```

### Freshness policies and fetch output contract

Data freshness follows natural market boundaries: OHLCV data gets a **1-hour TTL during market hours** with a mandatory re-fetch after market close (4:00 PM ET) for final adjusted prices, news uses a **15-minute TTL**, fundamentals are refreshed **daily**, and dividends **weekly**. A `FetchCacheManager` checks `fetched_at` in the cache table against these policies before deciding whether to re-fetch.

The fetch stage outputs **raw JSON blobs plus metadata** — normalization happens in the Transform stage. This preserves raw responses for auditability and replayability. Each `FetchOutput` includes `raw_json`, `content_hash` (SHA-256 for deduplication), `provider_name`, and `fetched_at`. Raw data lands in a `raw_fetch_data` table with a UNIQUE constraint on `(ticker, data_type, provider, content_hash)`.

---

## Stage 2: Hybrid schema transform with validation gates

The Transform stage normalizes raw provider data into canonical schemas, validates quality, and routes records to either typed tables or a flexible JSON catch-all.

### The hybrid schema architecture

**Strongly typed tables for known data** (OHLCV, positions, dividends) deliver maximum query performance with native B-tree indexes and CHECK constraints. **A JSON catch-all with virtual generated columns** handles unknown or evolving data — this is the critical architectural insight for SQLite.

SQLite's `GENERATED ALWAYS AS ... VIRTUAL` columns compute values from `json_extract()` on the fly with zero storage cost, and *can be indexed*. Benchmarks show indexed generated columns achieve **~0.15ms query times**, identical to native columns. The workflow is: store everything as JSON initially → add generated columns + indexes as query patterns emerge → promote to typed tables when schemas stabilize. No data migration is needed at any step.

```sql
CREATE TABLE raw_data_store (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider TEXT NOT NULL,
    data_type TEXT NOT NULL,
    ticker TEXT,
    payload TEXT NOT NULL CHECK (json_valid(payload)),
    -- Virtual generated columns for fast queries:
    symbol TEXT GENERATED ALWAYS AS (json_extract(payload, '$.symbol')) VIRTUAL,
    revenue REAL GENERATED ALWAYS AS (json_extract(payload, '$.revenue')) VIRTUAL
);
CREATE INDEX idx_raw_symbol ON raw_data_store(symbol);
```

**EAV (Entity-Attribute-Value) is explicitly not recommended** — it requires multiple self-joins to reconstruct entities (3–4× slower minimum), offers no type safety, and has been superseded by JSON columns in every modern database. Dynamic table creation at runtime via SQLAlchemy's `MetaData.create_all()` is viable when schemas are known but not pre-coded, but creates table proliferation for truly unknown data.

### Field mapping and deduplication

A JSON-based field mapping configuration (inspired by Azure Data Factory's TabularTranslator pattern) maps provider-specific names to canonical names without code changes. Each provider/data_type combination has a mapping dictionary:

```python
FIELD_MAPS = {
    "yahoo_finance": {"ohlcv": {"Adj Close": "adj_close", "Volume": "volume", ...}},
    "alpha_vantage": {"ohlcv": {"5. adjusted close": "adj_close", "6. volume": "volume", ...}},
    "polygon": {"ohlcv": {"c": "close", "v": "volume", "t": "timestamp_ms", ...}}
}
```

When the same ticker is fetched from multiple providers, a **priority-based conflict resolution** strategy selects the most trusted source (Polygon > Yahoo > Alpha Vantage for exchange-level data) while recording alternative source count for transparency.

### Write dispositions per data type

Each data type follows a different loading strategy, matching dlt's three write dispositions:

- **OHLCV**: `append` via `INSERT OR IGNORE` with a UNIQUE constraint on `(ticker, date)` — the most efficient SQLite deduplication pattern
- **Current positions**: `replace` via `DELETE` + `INSERT` in a single transaction for atomic snapshot replacement
- **News articles**: `merge` via `INSERT OR REPLACE` keyed on `article_id` — append with deduplication
- **Dividends/fundamentals**: `merge` via upsert on `(ticker, ex_date)` or `(ticker, fiscal_period)`

All batch inserts are wrapped in single transactions (100× faster than individual commits on SQLite), and WAL mode (`PRAGMA journal_mode=WAL`) enables concurrent reads during writes.

### Validation gate with quarantine

The validation strategy uses a **hybrid fail-fast + quarantine** approach. **Pandera** validates DataFrames against schemas (lightweight at ~12 pip packages, far lighter than Great Expectations' 107+), catching schema drift with lazy validation mode that reports all failures at once. A `quarantine` table stores failed records with full JSON originals and failure reasons, while a `data_quality_log` tracks per-run quality scores.

The halt-vs-continue decision depends on data criticality: **positions and trades fail-fast** (incorrect position data risks bad investment decisions), **OHLCV continues with quality flags** (missing days shouldn't block the app), and **news/sentiment always continues**. A safety net halts everything if overall batch quality drops below **80%**, catching upstream provider outages.

---

## Stage 3: Reports as versioned, snapshot-frozen domain entities

### The Report data model

Reports are first-class domain entities stored in two tables following the **Document Versioning Pattern**: a `reports` table holding only the current version (fast queries, small table) and a `report_versions` table storing all historical versions as immutable rows. This is critical for an investment app where regulatory/audit requirements demand reproducibility.

Key fields on the Report entity: `id` (UUID), `report_type` (portfolio_summary, performance_review, risk_analysis, custom), `title`, `created_by` ("user" or "ai_agent"), `specification` (JSON — the report blueprint), `data_snapshot` (JSON — frozen data at generation time), `rendered_outputs` (JSON — paths to PDF/HTML files), `status` (draft → generating → completed → failed → archived), `version` (incrementing integer), and `data_snapshot_hash` (SHA-256 for tamper detection).

JSON columns use SQLAlchemy's `TypeDecorator` wrapping TEXT with `json.dumps`/`json.loads`, since SQLCipher may lack native JSON type support depending on build configuration.

### Report specification DSL

The specification JSON is a typed, discriminated-union schema that an AI agent generates to describe report structure. **Five core section types** cover investment reporting needs:

- **`data_table`**: configures columns, sort order, grouping, totals, and a named query reference
- **`metric_card`**: displays KPIs (total value, period return, Sharpe ratio) with optional comparison values and color thresholds
- **`chart`**: specifies chart type (line, bar, pie, candlestick), axes, series, and dimensions
- **`ai_narrative`**: contains a Jinja2-style prompt template, data query references for context injection, LLM parameters (temperature, max_tokens, tone), and a cache key for deduplication
- **`conditional_section`**: wraps any sections in an `if/then/else` evaluated against a condition expression tree

The condition DSL supports field comparisons (`gt`, `lt`, `eq`, `in`) and boolean combinators (`and`, `or`, `not`) with dot-path field references into the data context. This enables investment-specific logic like "include tax-loss harvesting section only if there are positions with unrealized losses AND it's before December."

### Always freeze data snapshots

**Reports must store a frozen data snapshot** — not re-query live data. Market data changes, prices get restated, and holdings evolve. The snapshot captures all query results in a columnar JSON format (columns array + rows array — compact and parseable), all AI-generated narrative responses (with exact prompts, model parameters, and token counts for auditability), and source metadata (price source, as-of dates). The snapshot gets a SHA-256 hash stored in `data_snapshot_hash` for integrity verification. For snapshots exceeding ~1MB, store as a separate file on disk with a path reference to avoid bloating SQLCipher.

---

## Stage 4: Dual-target rendering with Plotly and WeasyPrint

### WeasyPrint for PDF, Plotly for charts

**WeasyPrint** is the best PDF renderer for this architecture: pure Python (no system binary like wkhtmltopdf), produces selectable text (unlike pdfkit which renders pages as images), supports CSS Paged Media for headers/footers/page numbers, and requires no JavaScript — charts are pre-rendered as static images. Playwright is the fallback for JS-heavy content, and since Electron already bundles Chromium, its binary could potentially be reused.

**Plotly** strongly outperforms Matplotlib for investment reports. It provides native `go.Candlestick` with volume subplots, polished pie charts for allocation views, and a modern look suitable for financial applications. The dual-target strategy: for **HTML reports viewed in Electron**, embed interactive Plotly divs (`fig.to_html(full_html=False, include_plotlyjs='cdn')`); for **PDF reports**, export static PNG via **Kaleido v1** (`fig.to_image(format="png", scale=2)`), then embed as base64 data URIs in the Jinja2 template.

### Registry-based renderer plugin architecture

A decorator-based renderer registry maps section types to renderer classes, mirroring the provider registry pattern:

```python
@register_renderer("candlestick_chart")
class CandlestickRenderer:
    def render_html(self, data, ctx) -> str:
        fig = create_candlestick(data['df'], data['symbol'])
        return fig.to_html(full_html=False)  # Interactive for Electron

    def render_pdf_assets(self, data, ctx) -> dict:
        chart_bytes = fig.to_image(format="png", scale=2)  # Static for WeasyPrint
        return {"type": "candlestick_chart", "chart_bytes": chart_bytes}
```

The report builder iterates over specification sections, dispatches each to its registered renderer, collects the outputs, then feeds them into a Jinja2 template. HTML reports get interactive Plotly charts; PDF reports get static images embedded via base64 `<img>` tags. The Jinja2 template uses `@page` CSS rules for page breaks, margins, and page counters.

---

## Stage 5: Async email delivery with tracking

### Email via aiosmtplib with Gmail app passwords

**aiosmtplib (v5.1)** provides async SMTP for FastAPI's event loop. Gmail requires 2-Step Verification plus a 16-character app password (generated at myaccount.google.com/apppasswords), stored encrypted in SQLCipher. The send flow: connect plaintext → STARTTLS upgrade → login → send `MIMEMultipart` with HTML body + PDF attachment → quit. Gmail's daily limit is ~500 emails for personal accounts.

For local delivery, reports save to a structured `~/.investapp/reports/` directory with timestamp-prefixed filenames. Electron's main process exposes IPC handlers (`shell.openPath()` for default PDF viewer, `shell.showItemInFolder()` for file manager, `BrowserWindow.loadFile()` for HTML reports in-app) — all with path validation to prevent directory traversal.

A `sent_reports` table tracks every delivery: `report_id`, `channel` (email/local/webhook), `recipient`, `status` (pending → sent → failed → opened), `sent_at`, `error_message`, `smtp_response`, and `file_path`. The `DeliveryTracker` service provides `log_send()`, `mark_sent()`, `mark_failed()`, and `mark_opened()` lifecycle methods.

---

## APScheduler and the custom pipeline engine

### APScheduler 3.x with AsyncIOScheduler

**APScheduler 3.x** (not 4.x, which has breaking API changes and SQLite caveats) integrates with FastAPI via `AsyncIOScheduler`, sharing the event loop. The job store uses `SQLAlchemyJobStore` pointed at a **separate plain SQLite file** — not the encrypted SQLCipher app database — to avoid complicating APScheduler's internal SQL with encryption. Key configuration: `coalesce=True` (merge missed runs), `max_instances=1` (prevent overlapping runs), `misfire_grace_time=300` (5-minute grace period). Jobs use `replace_existing=True` with explicit string IDs to prevent duplicates on restart.

Start the scheduler in FastAPI's `lifespan` context manager and register event listeners for `EVENT_JOB_EXECUTED` and `EVENT_JOB_ERROR` to feed the pipeline run history table.

### Custom pipeline over Prefect

A custom `Pipeline` class is strongly preferred over Prefect for this single-process desktop app. **Prefect adds ~50 transitive dependencies** and auto-spawns a local API subprocess even in "local mode." The custom pipeline provides:

- **Sequential stage execution** with output passing: each stage receives a `context` dict containing all previous stages' outputs (`ctx["fetch"]`, `ctx["transform"]`, etc.)
- **Required vs optional stages**: Fetch, Transform, and Store are `required=True` (failure halts the pipeline); Render and Send are `required=False` (failure logs and continues)
- **Structured run tracking**: a `PipelineRun` dataclass records `run_id`, `policy_id`, per-stage status/timing/errors, and serializes to a `pipeline_run_history` table

```python
class Pipeline:
    async def run(self, context: dict = None) -> PipelineRun:
        for stage_name, fn, required in self._stages:
            try:
                result = await fn(ctx)
                ctx[stage_name] = result
            except Exception as e:
                if required:
                    run.status = StageStatus.FAILED
                    return run
                # Non-required: log, skip, continue
```

### Structured logging with structlog

**structlog** is preferred over loguru for FastAPI integration. It provides a processor pipeline, native `contextvars` support (critical for correlating logs across pipeline stages with `run_id`), and stdlib-compatible formatting. Configure JSON output for production, `ConsoleRenderer` with colors for development. Bind `run_id` and `stage` to the logger context at pipeline entry, and all downstream log calls automatically include these fields.

---

## The AI agent's MCP tool interface

### MCP server mounted on FastAPI

The **MCP Python SDK (v1.8+)** provides `FastMCP`, which auto-generates tool schemas from Python type hints and docstrings. For the desktop app, **stdio transport** is the production choice: Electron spawns the Python process and communicates via stdin/stdout with no network exposure. Streamable HTTP (`app.mount("/mcp", mcp.streamable_http_app())`) serves development and MCP Inspector testing.

Six core tools expose the pipeline to the AI agent:

- **`create_policy`**: accepts name, pipeline_type, schedule_cron, data_sources, filters, output config, delivery config — all validated by Pydantic models with field constraints
- **`list_policies`**: returns all configured policies with schedules and last-run timestamps
- **`run_pipeline`**: manually triggers a pipeline run with optional `dry_run=True` for simulation
- **`preview_report`**: generates a report preview without persisting or sending
- **`update_policy_schedule`**: modifies cron schedule for an existing policy
- **`get_pipeline_history`**: returns recent run history with per-stage status

MCP **resources** (read-only context) expose `portfolio://holdings` (current portfolio for agent context) and `schema://policies` (the Pydantic-generated JSON Schema, so the agent understands valid inputs).

### Policy validation and guardrails

The `PolicyCreate` Pydantic model enforces structural validity: cron expressions must have exactly 5 fields, tickers are validated against known symbols, `min_volume` must be ≥ 0, and `date_range` must match a pattern (`last_30d` or `YYYY-MM-DD:YYYY-MM-DD`). The model's `json_schema_extra` provides concrete examples that help the AI agent construct valid policies. Resource limits (maximum tickers per policy, minimum schedule interval, allowed providers) prevent the agent from creating runaway configurations.

The agent workflow follows a natural conversational pattern: query current state via `list_policies` → read schema via resources → create or modify a policy → dry-run to preview → confirm and enable. This pattern requires no human-in-the-loop for routine operations while preserving full auditability through the pipeline run history table.

---

## Recommended library stack at a glance

| Concern | Library | Key rationale |
|---|---|---|
| Async HTTP | **aiohttp** ≥ 3.10 | Best async HTTP client; `TCPConnector(limit=N)` for pooling |
| Rate limiting | **aiolimiter** 1.2.1 | Leaky bucket, pure Python, no Redis needed |
| Retry | **tenacity** ≥ 9.0 | Full jitter exponential backoff, async-native |
| DataFrame validation | **pandera** ≥ 0.20 | Lightweight (12 deps vs Great Expectations' 107) |
| ORM | **SQLAlchemy** ≥ 2.0 | Async via `aiosqlite`, generated column support |
| PDF rendering | **WeasyPrint** | Pure Python, CSS Paged Media, selectable text |
| Charts | **Plotly** + **Kaleido** v1 | Interactive HTML + static PNG export |
| Templates | **Jinja2** | Standard, battle-tested, custom filters |
| Async email | **aiosmtplib** 5.1 | Native asyncio SMTP, MIT license |
| Scheduling | **APScheduler** 3.x | AsyncIOScheduler + SQLAlchemyJobStore |
| MCP server | **mcp** SDK ≥ 1.8 | FastMCP auto-generates schemas from type hints |
| Logging | **structlog** | Processor pipeline, contextvars, JSON output |
| Config validation | **Pydantic** ≥ 2.0 | Already in FastAPI stack, JSON Schema generation |

## Conclusion

The architecture's central insight is that **a single-process async Python app can handle every concern** — rate-limited parallel fetching, schema-flexible storage, AI-generated reports, dual-target rendering, and scheduled delivery — without any distributed infrastructure. Three patterns recur across every stage and deserve emphasis: the **decorator-based registry** (used for providers, renderers, and normalizers) eliminates plugin framework dependencies; the **JSON catch-all with virtual generated columns** gives SQLite the schema flexibility of a document store with the query performance of typed tables; and the **custom Pipeline class with required/optional stages** provides exactly the error semantics investment data needs (fail-fast for positions, continue-with-flags for news) without Prefect's dependency weight. The MCP tool interface closes the loop by letting an AI agent author, modify, and monitor pipeline policies through the same validated Pydantic models that the pipeline engine consumes — no translation layer needed.