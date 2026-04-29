# Known Issues — Zorivest

> Track bugs, limitations, and workarounds here.
> Resolved issues are archived in [known-issues-archive.md](known-issues-archive.md).

## Active Issues


### [MCP-TOOLAUDIT] — 12 findings from comprehensive MCP tool CRUD audit
- **Severity:** High (1 High, 7 Medium, 4 Low) → **Partially remediated** (TA1–TA4)
- **Component:** mcp-server, api
- **Discovered:** 2026-04-27
- **Status:** Partially resolved — 4 MEUs (TA1–TA4) completed 2026-04-29
- **Remediated (P2.5e):**
  - ✅ **TA1:** `delete_trade` 404 fix — `NotFoundError` propagation (was 500 on not-found).
  - ✅ **TA2:** `update_settings` `[object Object]` serialization fix — `JSON.stringify` for non-string details.
  - ✅ **TA3:** 7 stub handlers → 501 responses: `list_bank_accounts`, `list_brokers`, `resolve_identifiers` (accounts), `estimate_tax`, `find_wash_sales`, `harvest_losses`, `manage_lots` (tax).
  - ✅ **TA4:** `list_trade_plans` + `delete_trade_plan` tools added with M3 confirmation gate.
- **Remaining:**
  - `get_market_news` (503 Finnhub 422) — needs API key configuration
  - `emulate_policy` schema undocumented — TD1 discoverability task
  - No `delete_watchlist` tool — Low priority
  - `list_provider_capabilities` redundant with `list_market_providers` — consolidation candidate
  - `get_sec_filings` 503 (expected — no API key)
- **Consolidation:** See **[MCP-TOOLPROLIFERATION]** below — 76→12 compound-tool architecture proposed but never tracked as actionable work.
- **Audit ref:** [MCP Tool Audit Report](MCP/mcp-tool-audit-report.md)


### [TRADE-CASCADE] — delete_trade 500 on trade with linked report/images
- **Severity:** High
- **Component:** infrastructure (`models.py`), core (`trade_service.py`)
- **Discovered:** 2026-04-29 (live MCP audit)
- **Status:** ✅ Resolved — 2026-04-29
- **Fix:** Added `cascade="all, delete-orphan"` to `TradeModel.report`, `ondelete="CASCADE"` to `TradeReportModel.trade_id` FK, `ImageRepository.delete_for_owner()` port+impl, and explicit image+report cleanup in `TradeService.delete_trade()`.
- **Tests:** 2 integration tests (delete-with-report, delete-with-images) + 2 unit tests (service cleanup behavior). All GREEN (2396 passed).


### [MCP-TOOLPROLIFERATION] — 76+ MCP tools, growing in wrong direction (target: 12)
- **Severity:** High (architectural debt)
- **Component:** mcp-server
- **Discovered:** 2026-04-27 (audit report §Tool Consolidation Reflection)
- **Status:** Open — consolidation never tracked as actionable work; tool count increased from 74→76 during TA remediation
- **Details:** The MCP server registers 76 tools across 10 toolsets. IDE tool listings show ~85 (cross-tagged duplicates inflate the count). Most MCP clients warn or hard-cap at 60–80 tools. Tool definitions consume ~20–30K tokens of context window. The 2026-04-27 audit proposed a **76→12 compound-tool architecture** using discriminated unions (Zod) per resource domain, but this was documented only in [mcp-audit-workflow-proposal.md](MCP/mcp-audit-workflow-proposal.md) §5–6 and [mcp-tool-audit-report.md](MCP/mcp-tool-audit-report.md) §Tool Consolidation Reflection — never added to BUILD_PLAN.md, meu-registry.md, or this file.
- **Growth trajectory:** 68 (initial) → 74 (PH9/PH12 additions) → 76 (TA3/TA4 additions). Each remediation session adds tools instead of consolidating.
- **Proposed architecture:** 12 compound tools (`zorivest_account`, `zorivest_trade`, `zorivest_report`, `zorivest_watchlist`, `zorivest_market`, `zorivest_policy`, `zorivest_template`, `zorivest_analytics`, `zorivest_plan`, `zorivest_import`, `zorivest_db`, `zorivest_system`) — each with an `action` discriminated union parameter routing to isolated handlers. See audit report for full mapping.
- **Phase plan:**
  1. Phase 1: Merge identical tools (−5, zero risk: `list_provider_capabilities` = `list_market_providers`, etc.)
  2. Phase 2: Consolidate CRUD families — accounts, templates, watchlists (−25 tools)
  3. Phase 3: Consolidate analytics + market + scheduling (−20 tools)
  4. Phase 4: Enforce lazy loading for non-core toolsets
- **Consolidation score:** 76/12 = **6.3** (target: <3.0)
- **Anti-pattern note:** Compound tools are NOT "God Tools" — each action gets its own Zod schema and isolated handler. The compound tool is a routing layer. See [mcp-audit-workflow-proposal.md](MCP/mcp-audit-workflow-proposal.md) §Reconciling consolidation with anti-patterns.
- **Needs:** MEU registration in `meu-registry.md` + section in `BUILD_PLAN.md` before work begins.

### [STUB-RETIRE] — stubs.py contains legacy stubs that should be retired progressively
- **Severity:** Low (technical debt)
- **Component:** api (`stubs.py`), tests
- **Discovered:** 2026-03-19
- **Status:** Phase 1+2 cleaned; Phase 3 tracked
- **Phase 2 resolved (MEU-PW1, 2026-04-12):** `StubMarketDataService` and `StubProviderConnectionService` deleted. `MarketQuote` import removed from stubs.py.
- **Phase 3 blocked on:** `StubAnalyticsService` (MEU-104–116), `StubReviewService` (MEU-110), `StubTaxService` (MEU-123–126). Each retires when its real service is implemented.
- **Roadmap:** [09a §Stub Retirement Roadmap](../docs/build-plan/09a-persistence-integration.md)


### [MCP-TOOLDISCOVERY] — MCP tool descriptions lack workflow context and examples for AI discoverability
- **Severity:** Medium
- **Component:** mcp-server
- **Discovered:** 2026-04-12
- **Status:** Open — audit completed 2026-04-27, remediation pending. See [MCP-TOOLAUDIT] and [MCP Tool Audit Report](MCP/mcp-tool-audit-report.md) §Tool Consolidation Reflection.
- **Details:** Server instructions and tool descriptions are too terse for AI agents to discover and correctly use multi-step workflows. Confirmed gaps in scheduling toolset: (1) server instructions say only "Automated task scheduling" — no mention of policy CRUD or pipeline execution, (2) `run_pipeline` description doesn't explain the approval prerequisite or error return shape, (3) `create_policy` has no example of the expected `policy_json` structure, (4) `pipeline://policies/schema` and `pipeline://step-types` MCP resources aren't referenced in any tool description, (5) no workflow guidance for the `create → approve → run` lifecycle. Similar gaps likely exist across `accounts`, `trade-analytics`, `trade-planning`, `market-data`, and other toolsets.
- **Sub-issue — Template registry not exposed to MCP layer (2026-04-20):** *(Partially resolved by MEU-PH9 ✅: template CRUD MCP tools added — `list_email_templates`, `get_email_template`, `create_email_template`, `update_email_template`, `preview_email_template`. `pipeline://templates` resource added. Remaining: broader TD1 audit of all 9 toolset descriptions.)*
  - `create_policy` input is `z.record(z.unknown())` — completely opaque. AI agents cannot discover available template names (`daily_quote_summary`, `generic_report`), their required Jinja2 variables (`quotes`, `records`), variable field shapes (`q.symbol`, `q.price`, etc.), or how steps must be wired for data to flow into the template.
  - ~~No `pipeline://templates` resource exists.~~ → Added by MEU-PH9. `EMAIL_TEMPLATES` dict migrated to DB-backed `EmailTemplateModel`.
  - **Pre-implementation research:** [mcp-template-discoverability-gap.md](scheduling/mcp-template-discoverability-gap.md)
  - **Remaining work:** TD1 audit — enrich `create_policy` description with step-wiring examples and template variable contracts.
- **Next steps:** Full audit of all toolset descriptions against their actual API contracts. Improve server instructions with toolset workflow summaries. Add `policy_json` examples to `create_policy`. Reference MCP resources from tool descriptions. Add `pipeline://templates` resource exposing template registry with variable contracts. Ensure all tool descriptions include prerequisite state, return shape hints, and error conditions.






## Mitigated / Workaround Applied

### [MCP-TOOLCAP] — IDE tool limits render 68-tool flat registration non-viable
- **Severity:** Critical
- **Component:** mcp-server
- **Status:** Mitigated by Design — three-tier strategy (static ≤40 for Cursor, dynamic toolsets for VS Code, full for CLI/API). 2026-04-27 audit proposes 74→12 compound-tool consolidation. See [MCP Tool Audit Report](MCP/mcp-tool-audit-report.md) §Tool Consolidation Reflection.

### [MCP-ZODSTRIP] — `server.tool()` silently strips arguments with z.object()
- **Severity:** Critical
- **Component:** mcp-server
- **Status:** Open — upstream SDK bug (TS-SDK #1291, #1380, PR #1603)
- **Workaround:** Enforce raw shape convention. Startup assertion for non-empty `inputSchema.properties`.

### [MCP-AUTHRACE] — Token refresh race condition under concurrent tool execution
- **Severity:** Critical
- **Component:** mcp-server
- **Status:** Open — needs architectural mitigation
- **Workaround:** In-memory mutex for refresh; proactive JWT expiry check.

### [MCP-WINDETACH] — Node.js `detached: true` broken on Windows since 2016
- **Severity:** Critical
- **Component:** infrastructure
- **Status:** Open — upstream Node.js bug (#5146, #36808)
- **Workaround:** Windows Job Objects for process group management.

### [MCP-HTTPBROKEN] — Streamable HTTP transport has 5 failure modes
- **Severity:** High
- **Component:** mcp-server
- **Status:** Mitigated by Design (stdio primary). Pin SDK version. Never use stateless mode.

### [MCP-DIST-REBUILD] — MCP server runs from compiled `dist/`, not source `src/`
- **Severity:** High
- **Component:** mcp-server
- **Status:** Active — by design
- **Workaround:** After any `mcp-server/src/` change: `cd mcp-server && npm run build` then restart IDE.

### [UI-ESMSTORE] — electron-store v9+ (ESM-only) crashes electron-vite main process
- **Severity:** Medium
- **Component:** ui
- **Status:** Workaround Applied — pinned to `electron-store@8` (last CJS version)

### [E2E-AXEELECTRON] — `@axe-core/playwright` AxeBuilder incompatible with Electron sandbox
- **Severity:** High
- **Component:** ui (E2E tests)
- **Status:** Workaround Applied — load axe-core via `file://` URL + `page.evaluate()`

### [E2E-AXESILENT] — Accessibility scan failures are silent if the scanner itself crashes
- **Severity:** Medium
- **Component:** ui (E2E tests)
- **Status:** Active — process awareness. Wrap scan in try/catch during debugging.

### [E2E-ELECTRONLAUNCH] — Playwright `Process failed to launch!` in headless/sandboxed environments
- **Severity:** High
- **Component:** ui (E2E tests)
- **Status:** Active — environment-specific. E2E verified locally; Codex validates unit/integration only.
- **Resolution path:** `xvfb-run npx playwright test` in CI.

## Archived (see [known-issues-archive.md](known-issues-archive.md))

| ID | Resolved | Summary |
|----|----------|---------|
| PLAN-NOSIZE | 2026-04-11 | position_size full-stack propagation (MEU-70a) |
| BOUNDARY-GAP | 2026-04-11 | 7/7 API validation findings closed |
| PYRIGHT-PREEXIST | 2026-04-11 | TS1+TS2+TS3 all tiers resolved |
| TEST-ISOLATION | 2026-04-06 | Cleanup fixtures added |
| TEST-ISOLATION-2 | 2026-04-11 | Per-module app factory |
| TEST-DRIFT-MDS | 2026-04-12 | All 13 market data service tests pass (silently fixed by MEU-65a) |
| SCHED-PIPELINE-WIRING | 2026-04-12 | Pipeline runtime wiring complete (MEU-PW1) |
| SCHED-WALPICKLE | 2026-03-19 | Module-level callback extraction |
| SCHED-RUNREPO | 2026-03-19 | Key translation in adapter |
| MCP-CONFIRM | 2026-03-19 | Added confirmation_token to schema |
| DOC-STALESLUG | 2026-03-22 | MEU slug reference corrected |
| PIPE-CHARMAP | 2026-04-19 | Pipeline charmap crash fixed — structlog UTF-8 config + bytes-safe JSON (MEU-PW4) |
| PIPE-ZOMBIE | 2026-04-19 | Zombie runs eliminated — dual-write→single-writer, run_id passthrough, recover_zombies (MEU-PW5) |
| PIPE-DEDUP | 2026-04-20 | Dedup blocking fixed — run_id fallback when snapshot_hash absent (TDD-verified) |
| WF-SEGREGATE | 2026-04-19 | Split 2 combined workflows into 4 mode-specific variants with HARD STOP |
| TEMPLATE-RENDER | 2026-04-20 | SendStep template rendering implemented — 4-tier priority chain via Jinja2 (MEU-PW9) |
| PIPE-CURSORS | 2026-04-20 | Pipeline cursor tracking implemented — high-water mark upsert in FetchStep (MEU-PW11) |
| SCHED-TZDISPLAY | 2026-04-20 | Two-part fix: (1) PolicyList migrated to formatTimestamp() with policy timezone (MEU-72a), (2) normalizeUtc() added to formatDate.ts — appends Z to naive ISO strings from SQLAlchemy DateTime columns |
| PIPE-E2E-CHAIN | 2026-04-21 | Integration tests added for Fetch→Transform→Send chain (MEU-PW13) |
| PIPE-CACHEUPSERT | 2026-04-21 | Cache upsert integration test added in test_pipeline_dataflow.py |
| PIPE-STEPKEY | 2026-04-21 | _resolve_source() with 3-tier fallback replaces hardcoded fetch_result key (MEU-PW12) |
| PIPE-TMPLVAR | 2026-04-21 | TransformStep output_key + two-level merge in _resolve_body() feeds template vars (MEU-PW12) |
| PIPE-RAWBLOB | 2026-04-21 | Per-provider response extractors unwrap API envelopes (MEU-PW12) |
| PIPE-PROVNORM | 2026-04-21 | _PROVIDER_SLUG_MAP normalizes display names to registry slugs (MEU-PW12) |
| PIPE-QUOTEFIELD | 2026-04-21 | Presentation mapping (last→price, ticker→symbol) aligns template fields (MEU-PW12) |
| PIPE-SILENTPASS | 2026-04-21 | min_records param + WARNING status on zero records (MEU-PW12) |
| PIPE-URLBUILD | 2026-04-19 | Per-provider URL builder registry + headers_template forwarding (MEU-PW6) |
| PIPE-NOCANCEL | 2026-04-19 | CANCELLING status + cancel endpoint + cooperative step check (MEU-PW7) |
| PIPE-NOLOCALQUERY | 2026-04-25 | QueryStep (MEU-PH4) provides local DB query capability |
| GUI-EMAILTMPL | 2026-04-28 | Email Templates GUI tab in SchedulingLayout (MEU-72b) |
| PIPE-DROPPDF | 2026-04-28 | PDF→Markdown migration, Playwright dep removed (MEU-PW14) |
| MCP-APPROVBYPASS | 2026-04-29 | CSRF approval token: `validate_approval_token` middleware on approve endpoint (MEU-PH11) |
| MCP-POLICYGAP | 2026-04-29 | 3 MCP tools added: `delete_policy`, `update_policy`, `get_email_config` (MEU-PH12) |
| EMULATOR-VALIDATE | 2026-04-29 | VALIDATE phase: EXPLAIN SQL, SMTP check, step wiring validation (MEU-PH13) |
| TRADE-CASCADE | 2026-04-29 | Cascade delete for trade with linked report/images — ORM cascade + service cleanup |

## Template

When adding issues, use this format:

```markdown
### [SHORT-TITLE] — Brief description
- **Severity:** Critical / High / Medium / Low
- **Component:** core / infrastructure / api / ui / mcp-server
- **Discovered:** YYYY-MM-DD
- **Status:** Open / In Progress / Workaround Applied
- **Details:** What happens, how to reproduce
- **Workaround:** (if any)
```
