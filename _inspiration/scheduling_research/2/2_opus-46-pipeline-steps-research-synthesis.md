# Pipeline Step Chain Design — Three-Model Research Synthesis

> Cross-referencing ChatGPT, Claude, and Gemini research outputs on the same prompt (Prompt 2).
> Each model produced a document covering pipeline stages: Fetch → Transform → Store Report → Render → Send.
> This synthesis distills where they **agree**, where they **diverge**, and what's **uniquely contributed** by each.

---

## 1. Universal Agreement (All Three Converge)

### 1.1 Fetch Stage

| Decision | Agreement |
|---|---|
| **Provider registry with `typing.Protocol`** | All three use PEP 544 Protocols for structural subtyping over ABCs. Providers satisfy a fetch interface without inheritance coupling. |
| **Criteria-driven dynamic resolution** | Watchlist queries, position filters, and date-relative params are resolved at runtime from DB state, not hardcoded in the policy. |
| **Per-provider rate limiting** | All use `aiolimiter` (or equivalent async token bucket) keyed by provider/domain. Concurrent requests are capped per-provider via `asyncio.Semaphore`. |
| **Incremental loading with high-water marks** | A `pipeline_state` / `fetch_state` table tracks cursor values per (resource, provider) to avoid re-downloading history. All cite `dlt`'s incremental model. |
| **Batch transactions for performance** | Wrapping inserts in `BEGIN…COMMIT` blocks for SQLite performance (individual commits are orders of magnitude slower). |
| **Provider-declared capabilities** | Providers expose metadata: supported datasets, batch size, rate limits, freshness semantics. The engine adapts fetching strategy to provider capabilities. |
| **Retry with exponential backoff + jitter** | All recommend `tenacity` with `wait_random_exponential` for transient errors (429, 5xx, timeouts). Permanent errors (404) are logged and skipped. |

### 1.2 Transform Stage

| Decision | Agreement |
|---|---|
| **Hybrid schema: typed tables + JSON catch-all** | Core entities (OHLCV, positions, transactions) get strict typed columns. Unknown/evolving data goes into a JSON column. All reject pure EAV. |
| **JSON1 extension for flexible queries** | All leverage `json_extract()`, expression indexes, and/or generated columns to query JSON data performantly. |
| **Field mapping: provider → canonical** | A mapping layer translates provider-specific field names to canonical names. All propose declarative mapping configs. |
| **Write dispositions per data type** | OHLCV = append/ignore, positions = replace (atomic snapshot), news = merge/upsert. All align with `dlt`'s three write dispositions. |
| **Deduplication via UNIQUE constraints** | `INSERT OR IGNORE` / `INSERT ON CONFLICT` for idempotent ingestion. |
| **WAL mode for concurrent read/write** | `PRAGMA journal_mode=WAL` is mandatory for allowing UI reads during pipeline writes. |

### 1.3 Store Report Stage

| Decision | Agreement |
|---|---|
| **Reports are versioned domain entities** | Reports have version history, creation metadata, and reproducibility guarantees. |
| **Frozen data snapshots** | Report data is snapshotted at generation time; re-rendering uses the snapshot, not live data. |
| **SHA-256 integrity hashing** | All hash the data snapshot for tamper detection and integrity verification. |
| **Provenance metadata** | Each report records what queries ran, when, with what parameters, for full auditability. |

### 1.4 Render Stage

| Decision | Agreement |
|---|---|
| **Jinja2 for templating** | All use Jinja2 to compose HTML reports from data + template. |
| **Dual output: HTML + PDF** | Interactive HTML for in-app viewing, PDF for email/archival. |
| **Deterministic rendering** | Render is a pure function of (spec, snapshot, template version, settings). Same inputs → same output. |

### 1.5 Send Stage

| Decision | Agreement |
|---|---|
| **Async SMTP via `aiosmtplib`** | Event-loop-native email sending. |
| **Delivery tracking table** | `report_delivery` / `sent_reports` table records every attempt with status, timestamp, and error. |
| **Idempotent sends** | Check if a report+channel+destination has already succeeded before retrying. |

### 1.6 Orchestration

| Decision | Agreement |
|---|---|
| **APScheduler with `AsyncIOScheduler`** | All use APScheduler 3.x (not 4.x) with async integration. |
| **`SQLAlchemyJobStore` for persistence** | Jobs survive restarts via persistent job store. |
| **`coalesce=True`, `max_instances=1`** | Prevent overlapping runs and collapse missed firings. |
| **FastAPI `lifespan` for scheduler init** | Start scheduler in FastAPI's lifespan context manager. |
| **Custom pipeline over Prefect** | All reject Prefect as too heavy (~50+ transitive deps, spawns subprocess). Custom `Pipeline` class preferred. |
| **Sequential stage execution with context passing** | Each stage receives outputs from prior stages via a shared context dict. |

---

## 2. Differing Takes (Same Topic, Different Recommendations)

### 2.1 Provider Registry Implementation

| Topic | ChatGPT | Claude | Gemini |
|---|---|---|---|
| **Registration mechanism** | Protocol + entry points (`importlib.metadata`) for plugin discovery | Protocol + decorator-based self-registration at import time | Protocol + central registry dict with decorator |
| **Plugin philosophy** | Entry points for future 3rd-party extensibility | "Decorator registry is sufficient for ~5–10 built-in providers; pluggy/stevedore/entry_points are overkill" | Generic HTTP Adapter covers novel sources without new code |
| **Auto-discovery** | Not emphasized | `"provider": "auto"` — pick first provider for requested data type | AI generates policy using `generic_http` provider |

> [!IMPORTANT]
> **The Generic HTTP Adapter is Gemini's killer idea.** Instead of writing new provider code for every API, the AI agent authors a policy using a generic HTTP template — URL, method, headers, payload — effectively making the AI the integration layer. Claude's "auto" discovery and ChatGPT's entry points solve different but complementary problems.

### 2.2 Fetch Output Contract

| Topic | ChatGPT | Claude | Gemini |
|---|---|---|---|
| **What gets stored** | Full provenance envelope: raw_payload, content_type, cache_status, observed_schema_version, warnings | Raw JSON blob + SHA-256 content_hash + metadata. UNIQUE on `(ticker, data_type, provider, content_hash)` | Raw data stored, but less emphasis on envelope structure |
| **Normalization timing** | "Raw + normalized" — optionally attach normalized form alongside raw | Raw only at fetch stage; normalization happens entirely in Transform | Mapping schema generated by AI alongside fetch policy |
| **Cache validation** | HTTP ETag / If-None-Match / If-Modified-Since (RFC 9111 compliant) | Custom `FetchCacheManager` with market-aware TTLs (1h during market, refresh after 4PM ET) | Not detailed beyond freshness concept |

> [!TIP]
> **Claude's market-session-aware TTL model is the most pragmatic** — OHLCV gets 1-hour TTL during market hours with mandatory post-close refresh, news gets 15-min TTL, fundamentals daily. ChatGPT's HTTP cache validation is the most standards-compliant. Combine both: use Claude's TTL tiers with ChatGPT's ETag revalidation when available.

### 2.3 Schema Evolution Strategy

| Topic | ChatGPT | Claude | Gemini |
|---|---|---|---|
| **Approach** | JSON document table → add generated columns/expression indexes as fields become important. "Partially materialized schema-on-read." | JSON catch-all with `GENERATED ALWAYS AS … VIRTUAL` columns → index → eventually promote to typed tables. Zero storage overhead. | Proposes `dlt` as a runtime dependency for automatic `ALTER TABLE` on novel fields |
| **Dynamic table creation** | Explicitly warns against it: "fragile, migrations hard to reason about, hard to secure" | Acknowledges `MetaData.create_all()` is viable but warns of table proliferation | Endorses dynamic schema via `dlt` (auto-creates columns, unpacks nested dicts into child tables) |
| **EAV verdict** | Rejected — "trades schema simplicity for query complexity" | Rejected — "3–4× slower, no type safety, superseded by JSON columns" | Rejected — "complex queries, poor analytical performance" |

> [!WARNING]
> **Using `dlt` as a runtime dependency (Gemini's proposal) is the riskiest approach.** Auto-`ALTER TABLE` in a production desktop app introduces migration unpredictability. ChatGPT and Claude's manual promotion pattern (JSON → generated column → typed table) is safer and more controllable.

### 2.4 PDF Generation

| Topic | ChatGPT | Claude | Gemini |
|---|---|---|---|
| **Primary tool** | Electron's `webContents.printToPDF()` — leverages the existing Chromium instance | **WeasyPrint** — pure Python, CSS Paged Media, selectable text, no system binary | Not covered in detail |
| **Chart library** | Not specified | **Plotly** + **Kaleido v1** — native candlestick charts, dual-target (interactive HTML / static PNG) | Not covered |
| **Fallback** | N/A | Playwright for JS-heavy rendering (can potentially reuse Electron's Chromium binary) | N/A |

> [!TIP]
> **Claude provides the most complete render stack.** WeasyPrint for PDF + Plotly/Kaleido for charts + Jinja2 for templating is a concrete, production-ready combination. ChatGPT's `printToPDF()` approach is simpler but ties rendering to Electron's main process.

### 2.5 Report Specification Language

| Topic | ChatGPT | Claude | Gemini |
|---|---|---|---|
| **SQL in reports** | "Treat agent-generated SQL as untrusted. Prefer structured query DSL for common cases. Raw SQL only in advanced/audited mode." | Five section types: `data_table`, `metric_card`, `chart`, `ai_narrative`, `conditional_section`. SQL referenced by named query, not embedded. | Not detailed |
| **Conditional logic** | JsonLogic or JMESPath for section gating (keeps logic in JSON, not SQL) | Condition DSL with field comparisons (`gt`, `lt`, `eq`, `in`) and boolean combinators (`and`, `or`, `not`) | Not covered |
| **AI-generated narrative** | Not discussed | `ai_narrative` section type with Jinja2 prompt template, LLM params, cache key for dedup | Not covered |

### 2.6 Logging

| Topic | ChatGPT | Claude | Gemini |
|---|---|---|---|
| **Library** | Not specified | **structlog** — processor pipeline, `contextvars` for run_id correlation, JSON output | Not specified |
| **Rationale** | — | "Preferred over loguru for FastAPI integration" | — |

### 2.7 HTTP Client Library

| Topic | ChatGPT | Claude | Gemini |
|---|---|---|---|
| **Choice** | Not specified (mentions `httpx` in prior research) | **aiohttp ≥ 3.10** — `TCPConnector(limit=N)` for pooling | Not specified |

### 2.8 APScheduler Job Store Location

| Topic | ChatGPT | Claude | Gemini |
|---|---|---|---|
| **Where** | Inside the main encrypted SQLCipher database | **Separate plain SQLite file** — avoids complicating APScheduler's SQL with encryption | Inside SQLCipher database |

> [!IMPORTANT]
> **Claude's separate-file approach for APScheduler is a pragmatic tradeoff.** APScheduler generates its own SQL internally; mixing it with SQLCipher's `PRAGMA key` sequence adds complexity. But it means job schedule data is unencrypted on disk — evaluate risk.

---

## 3. Unique Contributions (Only One Model Proposes)

### 3.1 Unique to ChatGPT

| Contribution | Details |
|---|---|
| **Fetch envelope with `observed_schema_version`** | Tracks provider API version changes — if a provider publishes versioning, the envelope records it. If not, an inferred schema hash is computed. |
| **HTTP cache revalidation (ETag / If-Modified-Since)** | Full RFC 9111 compliance for sources that support standard HTTP caching headers. Avoids re-downloading unchanged data. |
| **RateLimit/RateLimit-Policy header parsing** | Mentions IETF draft for standardized rate limit headers. Recommends parsing when available but never assuming they exist. |
| **JsonLogic for report conditional sections** | Proposes JSON-native rule language for section gating, keeping logic in JSON rather than SQL. Explicitly cites JsonLogic spec. |
| **JMESPath for data reshaping** | Lightweight JSON query language for derived values and snapshot selection within report specs. |
| **`PRAGMA query_only` + authorizer double-lock** | Explicitly recommends using BOTH `PRAGMA query_only` and `set_authorizer` for report SQL sandboxing. |
| **"Do not enable `load_extension` for untrusted SQL"** | Warns that `load_extension()` turns SQL injection into arbitrary code execution. Unique security callout. |
| **Render caching by content hash** | Cache rendered PDF/HTML keyed by `hash(spec + snapshot + renderer_version)`. If nothing changed, skip re-render. |
| **Criteria as a "compilation problem"** | Frames dynamic criteria resolution as compiling a policy into a concrete run graph before execution, analogous to Airflow's dynamic task mapping. |
| **IBKR pacing rules as design constraints** | Documents specific IBKR rate limits: "identical requests within 15 seconds", "60 requests in 10 minutes", 10 req/sec global for Web API. |
| **Alpha Vantage limit inconsistency** | Notes discrepancy between advertised (25/day premium page) and observed (5/min + 500/day error message) limits. "Implement based on configured tier + observed errors." |

### 3.2 Unique to Claude

| Contribution | Details |
|---|---|
| **Complete library stack table** | 12-library recommendation matrix with specific versions: aiohttp ≥3.10, aiolimiter 1.2.1, tenacity ≥9.0, pandera ≥0.20, WeasyPrint, Plotly + Kaleido v1, structlog, aiosmtplib 5.1, APScheduler 3.x, mcp SDK ≥1.8. |
| **`GENERATED ALWAYS AS … VIRTUAL` columns** | Detailed explanation of virtual generated columns for zero-storage-cost JSON field extraction with indexing. Benchmarks: ~0.15ms queries, identical to native columns. |
| **Pandera for DataFrame validation** | Lightweight (12 deps vs Great Expectations' 107+). Lazy validation mode reports all failures at once. |
| **80% quality threshold as safety net** | If overall batch quality drops below 80%, halt everything — catches upstream provider outages. |
| **Required vs optional stages** | Fetch/Transform/Store = `required=True` (failure halts). Render/Send = `required=False` (failure logs, continues). |
| **Five report section types** | `data_table`, `metric_card`, `chart`, `ai_narrative`, `conditional_section` — a complete DSL for investment reports. |
| **`ai_narrative` section with LLM dedup** | Generates AI-written commentary with prompt templates, model params, and cache key to avoid regenerating identical narratives. |
| **Plotly candlestick with Kaleido export** | Native `go.Candlestick` for OHLCV, interactive HTML via `to_html()`, static PNG via `to_image(format="png", scale=2)`. Base64 data URIs in PDF. |
| **WeasyPrint over wkhtmltopdf** | "Pure Python, produces selectable text (unlike pdfkit which renders pages as images), supports CSS Paged Media." |
| **MCP through 6 core tools** | `create_policy`, `list_policies`, `run_pipeline`, `preview_report`, `update_policy_schedule`, `get_pipeline_history`. MCP resources: `portfolio://holdings`, `schema://policies`. |
| **MCP stdio transport for production** | "Electron spawns Python process, communicates via stdin/stdout with no network exposure." Streamable HTTP only for dev/Inspector. |
| **Azure Data Factory TabularTranslator** | Cites ADF's field mapping pattern as inspiration for provider→canonical mapping config. |
| **Document Versioning Pattern** | `reports` table (current version only) + `report_versions` table (all historical versions as immutable rows). |
| **Decorator-based renderer registry** | `@register_renderer("candlestick_chart")` — mirrors provider registry pattern. Each renderer has `render_html()` and `render_pdf_assets()`. |
| **Gmail app password workflow** | Concrete setup: 2-Step Verification → 16-char app password → store encrypted in SQLCipher. 500 emails/day limit for personal accounts. |
| **Local file delivery with Electron IPC** | `shell.openPath()`, `shell.showItemInFolder()`, `BrowserWindow.loadFile()` — all with path validation. |
| **structlog with `contextvars`** | Bind `run_id` and `stage` at pipeline entry; all downstream logs automatically include correlation fields. |

### 3.3 Unique to Gemini

| Contribution | Details |
|---|---|
| **"Split-Brain" concurrency model** | Names and formalizes the Electron (UI loop) vs Python (asyncio) architecture split. Responsibility partitioning table. |
| **Generic HTTP Adapter for novel sources** | AI reads unknown API docs, constructs policy using `generic_http` provider with raw HTTP params (URL, method, headers, payload). Engine executes without "knowing" what the API is. |
| **"ORIK" mapping protocol** | References tabular mapping research. AI agent generates a Mapping Schema alongside fetch policy using JSONPath source paths + transformation type + target type. |
| **Self-healing loop** | If API structure changes → pipeline fails → error fed to Agent → Agent updates Mapping Schema → pipeline auto-recovers. No software update needed. |
| **Financial data precision: Decimal enforcement** | Explicit callout: parse monetary values as strings → `decimal.Decimal`. Store in SQLite as strings or integer micros/cents. IEEE 754 floats are "unacceptable for financial calculations." |
| **`dlt` as runtime schema evolution engine** | Proposes `dlt` as an actual library dependency for automatic type inference, dynamic `ALTER TABLE`, and nested dict unpacking into child tables with foreign keys. |
| **System-Versioned Tables (Temporal Tables)** | `BEFORE UPDATE` and `BEFORE DELETE` triggers auto-copy old row state to a history table. Enables "time travel queries" — show portfolio as it was known on a specific date. |
| **SQLCipher `cipher_memory_security` tradeoff** | Notes that memory wiping prevents key leakage in RAM but creates massive overhead for high-volume transforms. Suggests disabling for market data tables (not passwords). |
| **SQLCipher `cipher_use_hmac` tuning** | Disabling per-page MAC checks can improve performance but lowers security posture against memory forensics. |
| **Connection pooling for key derivation** | PBKDF2's 64,000+ iterations make opening new connections take 1-2 seconds. Use `QueuePool` so key derivation happens once at startup. |
| **Declarative Policy Pattern framing** | Most strongly articulates the security argument: "AI produces passive JSON configuration; deterministic engine activates pre-defined code paths. System behavior is bounded even if AI reasoning is probabilistic." |
| **Storage strategy comparison table** | Side-by-side assessment of Relational / EAV / JSON Hybrid across 7 dimensions with clear recommendations per entity type. |

---

## 4. Quality Assessment

| Dimension | ChatGPT | Claude | Gemini |
|---|---|---|---|
| **Depth per stage** | ★★★★★ — Deepest on Fetch (rate limits, caching, envelope) | ★★★★★ — Deepest on Render + Send (complete library stack) | ★★★★☆ — Deepest on Transform + Store (schema evolution, temporal tables) |
| **Code examples** | ★★★☆☆ — Pseudocode and concepts | ★★★★★ — Production-ready Python + SQL snippets | ★★★☆☆ — Pseudo-code with some SQL |
| **Library recommendations** | ★★★☆☆ — Mentions libraries but no version pinning | ★★★★★ — 12-library table with specific versions and rationale | ★★☆☆☆ — Mentions `dlt`, `aiolimiter` but fewer specifics |
| **Architecture clarity** | ★★★★☆ — Clear narrative structure | ★★★★★ — Every concept has a code pattern | ★★★★☆ — Academic framing, good tables |
| **Financial domain awareness** | ★★★★★ — IBKR pacing rules, Alpha Vantage inconsistencies, market session caching | ★★★★☆ — Market-hour TTLs, position fail-fast | ★★★★☆ — Decimal precision, temporal tables |
| **Security coverage** | ★★★★★ — `query_only` + authorizer + `load_extension` warning | ★★★☆☆ — Mentions guardrails but less detail | ★★★★☆ — Declarative policy pattern as security stance |
| **Novelty of ideas** | ★★★★☆ — Fetch envelope, render caching, criteria compilation | ★★★★☆ — Virtual generated columns, ai_narrative, required/optional stages | ★★★★★ — Generic HTTP adapter, self-healing loop, temporal tables |
| **Practical readiness** | ★★★★☆ — Strong concepts, needs implementation detail | ★★★★★ — Could almost copy-paste into a codebase | ★★★☆☆ — Some proposals need significant refinement |

---

## 5. Recommended Picks Per Area

| Area | Pick From | Reasoning |
|---|---|---|
| **Provider registry** | **Claude** (decorator) + **Gemini** (Generic HTTP Adapter) | Decorator registry for built-in providers + Generic HTTP for novel sources via AI policy authoring. |
| **Rate limiting** | **All three** (converge) | `aiolimiter` + `asyncio.Semaphore` + `tenacity` stack is unanimous. |
| **Fetch output envelope** | **ChatGPT** | Most complete provenance model: raw_payload, content_type, cache_status, observed_schema_version, warnings. |
| **HTTP cache revalidation** | **ChatGPT** | ETag/If-Modified-Since for sources that support it. Layer on top of Claude's TTLs. |
| **Freshness TTL model** | **Claude** | Market-session-aware TTLs (1h intraday, refresh after close, 15min news, daily fundamentals). |
| **Schema evolution** | **ChatGPT + Claude** | JSON catch-all → virtual generated columns → promote to typed tables. Avoid `dlt` as runtime schema mutator. |
| **Financial precision** | **Gemini** | Explicit `decimal.Decimal` enforcement and integer micros storage. Critical and easy to miss. |
| **Write dispositions** | **Claude** | Clearest mapping: append/replace/merge per data type with `dlt` semantics. |
| **Validation gate** | **Claude** | Hybrid fail-fast + quarantine with 80% quality threshold. Per-criticality halt rules. |
| **Report specification DSL** | **Claude** | Five section types + condition DSL + `ai_narrative` is the most complete design. |
| **Report conditional logic** | **ChatGPT** (JsonLogic) + **Claude** (condition DSL) | Claude's condition DSL for the schema; ChatGPT's JsonLogic as the evaluation engine. |
| **Temporal auditing** | **Gemini** | System-versioned tables via triggers for time-travel queries. Investment-critical for restatements. |
| **PDF rendering** | **Claude** | WeasyPrint + Plotly/Kaleido is the most concrete, production-ready stack. |
| **MCP tool design** | **Claude** | 6 tools + 2 resources is a clean, minimal surface. stdio transport for production. |
| **Structured logging** | **Claude** | `structlog` with `contextvars` for run_id correlation. |
| **Security: SQL sandboxing** | **ChatGPT** | Double-lock: `PRAGMA query_only` + `set_authorizer` + disable `load_extension`. |
| **SQLCipher tuning** | **Gemini** | Connection pooling for key derivation, `cipher_memory_security` tradeoff awareness. |
| **Novel source handling** | **Gemini** | Generic HTTP Adapter + AI-authored mapping schema = zero-code integration for new APIs. |

---

## 6. Open Questions for Build Plan

1. **Generic HTTP Adapter scope**: How much freedom should the AI agent have in constructing raw HTTP requests? Security implications of arbitrary URL/header authoring need guardrails.
2. **`dlt` as dependency vs inspiration**: Use `dlt`'s concepts (incremental loading, write dispositions, schema evolution vocabulary) without the library? Or embed it for the novel-source schema evolution path?
3. **PDF renderer: WeasyPrint vs `printToPDF()`**: WeasyPrint is pure Python and independent of Electron. `printToPDF()` reuses existing Chromium but ties rendering to the Electron process. Which fits the architecture better?
4. **APScheduler job store isolation**: Separate plain SQLite file (Claude) vs inside SQLCipher (ChatGPT/Gemini)? Security vs simplicity tradeoff.
5. **Temporal tables from day one?**: Gemini's system-versioned tables add triggers on every `UPDATE`/`DELETE`. Worth the write overhead from the start, or add later when audit requirements crystallize?
6. **`ai_narrative` section**: Should the report engine call an LLM at generation time? Adds API dependency and latency to scheduled pipelines. Alternative: pre-generate narratives in a separate step.
7. **HTTP client: `aiohttp` vs `httpx`**: Claude recommends `aiohttp ≥ 3.10`. Previous prompt-1 research used `httpx`. Need to pick one and standardize.
