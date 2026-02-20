# Phase 9: Scheduling & Pipeline Engine — Strategic Integration Roadmap

> Synthesized from 6 AI research documents + 4 composite syntheses.
> This is the high-level picture. Detailed build plan entries will follow in a separate session.

---

## 1. Where This Fits

```
EXISTING BUILD ORDER:
Phase 1 → 1A → 2 → 2A → 3 → 4 → 5 → 6 → 7 → 8 (Market Data)

PROPOSED ADDITION:
                                                            Phase 8
                                                              │
                                                              ▼
                              ┌──────────────────────────────────────────────────────────┐
                              │                    PHASE 9                               │
                              │  ┌──────┐   ┌──────┐   ┌──────┐   ┌──────────────────┐  │
            Phase 2 ─────────▶│  │  9A  │──▶│  9B  │──▶│  9C  │──▶│       9D         │  │
            Phase 3 ─────────▶│  │Found.│   │Engine│   │Stages│   │Security+API+GUI  │  │
            Phase 4 ────────────────────────────────────────────▶──│                  │  │
            Phase 5 ────────────────────────────────────────────▶──│                  │  │
                              │  └──────┘   └──────┘   └──────┘   └──────────────────┘  │
                              └──────────────────────────────────────────────────────────┘
```

**Priority level**: P2 (Build Next) — after Market Data is functional.
**Phase 9A can start in parallel with Phase 8** since it's pure Python with zero external dependencies.

---

## 2. Resolved Decisions

All 13 open questions from the two research syntheses, now answered:

### From Prompt 1 (Policy Engine)

| # | Question | Decision | Rationale |
|---|---|---|---|
| 1 | **Data referencing syntax** | `{ "ref": "ctx.quotes" }` (ChatGPT) | Easiest to validate via JSON Schema. LLMs produce valid JSON objects naturally. Mustache needs a custom parser. JSONPath is overkill. |
| 2 | **Branching complexity** | `skip_if` field (Claude) for v1 | Covers 80% of use cases. Choice/Map states deferred to v2 when real usage patterns emerge. |
| 3 | **Step version in policy JSON?** | No — registry-only (Claude/Gemini) | Simpler policy JSON. Type aliases handle migration transparently. Less for the AI to get wrong. |
| 4 | **Plugin architecture** | `__init_subclass__` auto-registration (Claude) | Zero ceremony. Import the module and it's registered. Entry points are overkill for a ~10-provider desktop app. |
| 5 | **`saga_log` table?** | No separate table | Step status records already capture success/failure. Compensation metadata stored in step output. Full saga infrastructure is overkill for single-process. |
| 6 | **Schema version format** | Integer (1, 2, 3…) | SemVer is overkill for a local app's internal format. Integer is easier to compare and increment. |

### From Prompt 2 (Pipeline Steps)

| # | Question | Decision | Rationale |
|---|---|---|---|
| 7 | **Generic HTTP Adapter** | Defer to v2 | Powerful but widens attack surface significantly. v1 uses only registered providers. Revisit after security guardrails are battle-tested. |
| 8 | **`dlt` as dependency?** | Concepts only — no runtime dependency | Copy dlt's vocabulary (incremental loading, write dispositions, schema evolution) into our own code. Avoids 30+ transitive deps. |
| 9 | **PDF renderer** | WeasyPrint (Claude) | Pure Python, CSS Paged Media, selectable text, no JS dependency. `printToPDF()` remains available as a fallback for UI-capture scenarios. |
| 10 | **APScheduler job store location** | Inside SQLCipher (main DB) | Simpler architecture. APScheduler's internal SQL is simple. Separate file means unencrypted schedule data on disk. |
| 11 | **Temporal tables from day one?** | Yes, for core financial tables only | Positions, balances, tax lots get `BEFORE UPDATE/DELETE` triggers. Market data (OHLCV) doesn't need temporal tracking. |
| 12 | **`ai_narrative` section?** | Defer to v2 | Adds LLM API dependency + latency to scheduled pipelines. Pre-generate narratives separately if needed later. |
| 13 | **HTTP client** | `httpx` | HTTP/2 support, sync+async, `requests`-compatible API, good enough performance for ~50 API calls/run. Web search confirmed aiohttp is ~50% faster for high concurrency, but that's irrelevant at our scale. |

---

## 3. Sub-Phase Breakdown

### Phase 9A — Foundation (Pure Python, 0 external deps)

> **Can start in parallel with Phase 8.** Everything here is pure Pydantic + Python.

| Item | What | Depends On |
|---|---|---|
| Policy JSON Schema | JSON Schema definition (Draft 2020-12) + Pydantic models for policy documents | Nothing |
| Policy validation | Structural validation, referential integrity, cycle detection via topological sort | Policy Schema |
| Step Type Registry | `StepBase` Protocol with `__init_subclass__`, Pydantic `Params` inner class, `side_effects` flag | Nothing |
| Step manifest for MCP | Auto-generated JSON Schema from registry for `tools/list` exposure | Step Registry |
| Error handling model | `on_error` enum per step: `fail_pipeline`, `log_and_continue`, `retry_then_fail` | Policy Schema |
| `skip_if` conditions | Condition evaluator for step-level skip logic | Policy Schema |
| **Test gate** | `pytest` — pure Python unit tests, no DB, no network | |

**Deliverables**: Policy Pydantic models, StepBase class, registry singleton, validation module, condition evaluator.

---

### Phase 9B — Engine Core (depends on 9A + Phase 2)

> **First DB dependency.** Pipeline execution, persistence, and scheduling.

| Item | What | Depends On |
|---|---|---|
| Pipeline Execution Engine | Async runner: `for step in steps: await step.execute(ctx)`, context dict, `asyncio.timeout()` per step | 9A |
| Pipeline persistence | `pipeline_runs` + `pipeline_steps` tables (SQLAlchemy models + repos) | Phase 2 |
| State machine | `PENDING → RUNNING → SUCCESS / FAILED / SKIPPED` per step, FSM transitions | Engine |
| Dry-run mode | Skip/stub side-effect steps based on registry `side_effects` flag | Engine + Registry |
| Resume from failure | Load prior successful step outputs from DB, re-execute from last failed step | Persistence |
| APScheduler integration | `AsyncIOScheduler` + `SQLAlchemyJobStore` (inside SQLCipher) + `CronTrigger` | Phase 2 |
| Misfire handling | `coalesce=True`, `max_instances=1`, configurable `misfire_grace_time` | APScheduler |
| Zombie detection | Startup scan for orphaned `RUNNING` executions; auto-resume if last step was read-only | Persistence |
| Sleep/wake handling | Electron IPC forwards OS power events (`suspend`/`resume`) to Python backend | APScheduler |
| Structured logging | `structlog` with `contextvars` binding `run_id` + `stage` for correlation | Phase 1A |
| **Test gate** | `pytest` — in-memory SQLite integration tests, mock step executors | |

**Deliverables**: `PipelineRunner` class, persistence layer, APScheduler lifecycle, power event handler, structured logging integration.

---

### Phase 9C — Pipeline Stages (depends on 9B + Phase 8)

> **The biggest sub-phase.** Implements the 5 pipeline stages: Fetch → Transform → Store Report → Render → Send.

#### Fetch Stage

| Item | What | Depends On |
|---|---|---|
| Provider registry | Extends Phase 8 `MarketDataProvider` with pipeline-specific capabilities (batch size, freshness, selectors) | Phase 8 |
| Criteria resolver | Dynamic input resolution: `db_query`, `relative` dates, `db_join`, `incremental` high-water marks | Phase 2 |
| Rate limiter | `aiolimiter` (leaky bucket) + `asyncio.Semaphore` per provider | Provider registry |
| Fetch cache | `fetch_cache` table with TTL per dataset, market-session awareness (1h intraday, refresh after close) | Phase 2 |
| HTTP cache revalidation | ETag / If-Modified-Since when providers support it | httpx |
| Fetch envelope | Provenance-first output: raw_payload, content_type, cache_status, content_hash, warnings | — |
| Incremental state | `pipeline_state` table: `(policy_id, provider_id, data_type, entity_key)` → last_cursor, last_hash | Phase 2 |

#### Transform Stage

| Item | What | Depends On |
|---|---|---|
| Field mapping engine | Provider → canonical name mapping config (JSON dict per provider/data_type) | Fetch |
| Hybrid schema storage | Typed tables for core entities + JSON catch-all with virtual generated columns | Phase 2 |
| Validation gate | Pandera for DataFrame validation. Hybrid fail-fast (positions) + quarantine (news). 80% quality threshold. | — |
| Write dispositions | `append` (OHLCV), `replace` (positions), `merge` (news) — matching dlt semantics | Phase 2 |
| Deduplication | UNIQUE constraints + `INSERT OR IGNORE` / `INSERT ON CONFLICT` | Phase 2 |
| Financial precision | Parse monetary values as strings → `decimal.Decimal`. Store as integer micros or text. | — |

#### Store Report Stage

| Item | What | Depends On |
|---|---|---|
| Report entity | `reports` + `report_versions` tables (Document Versioning Pattern) | Phase 2 |
| Report spec DSL | 4 section types: `data_table`, `metric_card`, `chart`, `conditional_section` | — |
| Data snapshot | Frozen query results in columnar JSON, SHA-256 hash for integrity | — |
| Conditional sections | Condition DSL with field comparisons + boolean combinators evaluated against snapshot | — |
| SQL sandboxing | `PRAGMA query_only` + `set_authorizer` for report SQL. Disable `load_extension`. | Phase 2 |

#### Render Stage

| Item | What | Depends On |
|---|---|---|
| Jinja2 templates | HTML report templates with `@page` CSS for print layout | — |
| Plotly charts | Candlestick, line, bar, pie charts via Plotly. Dual output: interactive HTML + static PNG via Kaleido | — |
| WeasyPrint PDF | HTML → PDF via WeasyPrint with CSS Paged Media | Jinja2, Plotly |
| Render caching | Cache keyed by `hash(spec + snapshot + renderer_version)`. Skip if unchanged. | — |
| Renderer registry | `@register_renderer("chart_type")` decorator pattern, mirroring provider registry | — |

#### Send Stage

| Item | What | Depends On |
|---|---|---|
| Async email | `aiosmtplib` + `MIMEMultipart` with HTML body + PDF attachment. Gmail app password support. | Render |
| Delivery tracking | `report_delivery` table: report_id, channel, recipient, status, sent_at, error | Phase 2 |
| Idempotent sends | Check existing success before retrying. SHA-256 dedup key. | Delivery table |
| Local file delivery | Save to structured directory. Electron IPC for `shell.openPath()` / `shell.showItemInFolder()`. | — |

| **Test gate** | Integration tests with real SQLCipher DB, mocked HTTP providers, mocked SMTP | |

**Deliverables**: 5 pipeline stage implementations, all persistence tables, provider integration, render pipeline.

---

### Phase 9D — Security, API, MCP, and GUI (depends on 9C + Phase 4, 5)

> **The integration layer.** Wires everything to REST, MCP, and the GUI.

| Item | What | Depends On |
|---|---|---|
| Security guardrails | SQL authorizer (default-deny), step type allowlist, email recipient limits, hash integrity | 9C |
| Rate limiting | Token bucket: 20 policy creates/day, 60 executions/hour, 50 emails/day, 100 SQL queries/hour | Phase 2 |
| Human-in-the-loop | First execution of new/modified policy requires GUI approval. Hash-based re-approval on change. | GUI |
| Audit trail | Append-only `audit_log` table with SQL triggers preventing UPDATE/DELETE | Phase 2 |
| Pipeline REST API | CRUD for policies, trigger runs, get history, preview reports | Phase 4 |
| Pipeline MCP tools | `create_policy`, `list_policies`, `run_pipeline`, `preview_report`, `update_policy_schedule`, `get_pipeline_history` | Phase 5 |
| MCP resources | `pipeline://policies` (JSON Schema), `pipeline://history` (recent runs) | Phase 5 |
| Scheduling GUI | Wire `06e-gui-scheduling.md` to real API. Policy editor, cron preview, run history, approval flow. | Phase 6 |
| Email settings GUI | Wire `06f` email provider settings to SMTP config. Test connection. | Phase 6 |
| **Test gate** | End-to-end: MCP tool → REST API → Pipeline Engine → mock providers → report → delivery record | |

**Deliverables**: Full REST + MCP surface, security middleware, GUI integration, E2E test suite.

---

## 4. Locked-In Library Stack

| Concern | Library | Version | Rationale |
|---|---|---|---|
| HTTP client | **httpx** | ≥ 0.27 | HTTP/2, sync+async, requests-like API |
| Rate limiting | **aiolimiter** | 1.2.1 | Leaky bucket, pure Python, no Redis |
| Retry | **tenacity** | ≥ 9.0 | Full jitter exponential backoff, async-native |
| DataFrame validation | **pandera** | ≥ 0.20 | Lightweight (12 deps vs Great Expectations' 107) |
| ORM | **SQLAlchemy** | ≥ 2.0 | Already in stack. Async via `aiosqlite`. |
| PDF rendering | **WeasyPrint** | latest | Pure Python, CSS Paged Media, selectable text |
| Charts | **Plotly** + **Kaleido** v1 | latest | Interactive HTML + static PNG dual export |
| Templates | **Jinja2** | latest | Standard, battle-tested |
| Async email | **aiosmtplib** | 5.1 | Native asyncio SMTP |
| Scheduling | **APScheduler** | 3.x | AsyncIOScheduler + SQLAlchemyJobStore. 4.x not production-ready. |
| Structured logging | **structlog** | latest | Processor pipeline, contextvars, JSON output |
| Config validation | **Pydantic** | ≥ 2.0 | Already in FastAPI stack |

---

## 5. Risk Register

| Risk | Impact | Mitigation |
|---|---|---|
| **WeasyPrint Windows installation** | MSYS2 + Pango/GObject dependencies required | Bundle with app installer OR use Electron printToPDF fallback with degraded print CSS |
| **SQLCipher key derivation latency** | 1-2s per new connection (PBKDF2 64K iterations) | Connection pooling via SQLAlchemy `QueuePool`. Key derivation happens once at startup. |
| **APScheduler SQLite concurrency** | Known `database is locked` issues under concurrent access | WAL mode + `busy_timeout` + single-writer pattern. APScheduler job store in same DB simplifies transaction management. |
| **Render stage dependency weight** | WeasyPrint + Plotly + Kaleido add ~200MB to install | Lazy-load render dependencies. Mark render + send as `required=False` stages. |
| **AI-authored SQL in reports** | Even with sandboxing, malformed SQL can cause performance issues | Statement timeout + row limit in authorizer. Read-only connection. No `load_extension`. |

---

## 6. Deferred to v2

| Feature | Why Defer |
|---|---|
| **Choice / Map state types** (Gemini) | Full state machine adds complexity. `skip_if` covers v1 needs. Add when real branching patterns emerge. |
| **Generic HTTP Adapter** (Gemini) | Widens attack surface. v1 uses only registered providers. Revisit after guardrails are proven. |
| **`ai_narrative` report section** (Claude) | Adds LLM API latency to scheduled pipelines. Not worth the complexity for v1. |
| **`dlt` as runtime dependency** (Gemini) | Auto-`ALTER TABLE` is risky in a desktop app. Manual schema promotion (JSON → generated column → typed table) is safer. |
| **Temporal tables for market data** | Write overhead of triggers on high-volume OHLCV tables. Only core financial entities (positions, balances) get temporal tracking in v1. |

---

## 7. Summary: The Path from Research → Build Plan

```
DONE ─────────────────────────────────────────────────────────────
  ✅ 6 research documents (ChatGPT × 2, Claude × 2, Gemini × 2)
  ✅ 4 synthesis documents (2 Opus, 2 Codex)
  ✅ 13 open questions resolved
  ✅ This strategic roadmap

NEXT ─────────────────────────────────────────────────────────────
  ▸ DETAILED BUILD PLAN: Expand each Phase 9 sub-phase into
    numbered items in build-priority-matrix.md (like items 21–30
    for Market Data). Each item gets: order, what, tests-first,
    deps, key test strategy.

  ▸ NEW BUILD PLAN FILES: Create 09-scheduling.md (or split into
    09a/09b/09c/09d) with contracts, Pydantic models, SQL schemas,
    REST endpoints, MCP tool definitions — at the same detail level
    as 08-market-data.md.

  ▸ UPDATE build-priority-matrix.md: Add Phase 9 items at P2 level,
    after items 35a–35f.

  ▸ UPDATE 00-overview.md: Add Phase 9 to the dependency diagram.
```
