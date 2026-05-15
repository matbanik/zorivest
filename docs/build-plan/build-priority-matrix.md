# Build Priority Matrix

> Part of [Zorivest Build Plan](../BUILD_PLAN.md) — The build order across all priority levels (235 items).

---

## P0 — Build Now (Core Trading + Infrastructure)

| Order | What | Tests First? | Deps on | Key Test Strategy |
|-------|------|-------------|---------|-------------------|
| **1A** | **Logging infrastructure** ([01a-logging.md](01a-logging.md)) — QueueHandler/Listener, JSONL, per-feature routing, redaction | ✅ Yes | Nothing | `pytest` — formatter, filter, routing, thread safety |
| **1** | Position size calculator | ✅ Yes | Nothing | `pytest.approx()` with spec values |
| **2** | Enums (AccountType, TradeAction, etc.) | ✅ Yes | Nothing | Enum membership tests |
| **3** | Domain entities (Trade, Account, Image, BalanceSnapshot) | ✅ Yes | Nothing | Dataclass creation, validation |
| **3a** | Portfolio balance (pure fn: sum all latest balances) | ✅ Yes | Nothing | Sum with negatives, empty accounts |
| **3b** | Display mode service ($ hide, % hide, % mode) | ✅ Yes | Nothing | Formatting logic, mask functions |
| **3c** | Account Review workflow (guided balance update) | ✅ Yes | Account entities | Step-through logic, API vs manual, dedup |
| **4** | Port interfaces (Protocols) | No tests needed | Nothing | Type definitions only |
| **5** | Commands & DTOs | ✅ Yes | Nothing | Dataclass validation (Pydantic deferred to Phase 4) |
| **6** | Service layer (trade, account, image, calculator) | ✅ Yes | Ports only | Mock repositories |
| **7** | SQLAlchemy models (all tables) | ✅ Yes | SQLAlchemy | In-memory SQLite |
| **8** | Repository implementations | ✅ Yes | Models | In-memory SQLite |
| **9** | Unit of Work | ✅ Yes | Repos | Transaction rollback tests |
| **10** | SQLCipher connection | ✅ Yes | sqlcipher3 | Encrypt/decrypt round-trip |
| **10a** | `AppDefaultModel` + seeding migration ([02a](02a-backup-restore.md)) | ✅ Yes | Models | In-memory SQLite, seed + query defaults |
| **10b** | `SettingsRegistry` + `SettingsResolver` ([02a](02a-backup-restore.md)) | ✅ Yes | Nothing | Three-tier resolution, type coercion, unknown key rejection |
| **10c** | `BackupManager` (auto backup + GFS rotation) ([02a](02a-backup-restore.md)) | ✅ Yes | SQLCipher, pyzipper | Snapshot → AES ZIP → rotate → verify |
| **10d** | `BackupRecoveryManager` (restore + repair) ([02a](02a-backup-restore.md)) | ✅ Yes | BackupManager | Restore cycle, hash verify, atomic swap, repair |
| **10e** | `ConfigExportService` (JSON export/import) ([02a](02a-backup-restore.md)) | ✅ Yes | SettingsRegistry | Allowlist enforcement, sensitivity filtering, dry-run |
| **11** | Image processing (validate, WebP standardize, thumbnail) | ✅ Yes | Pillow | WebP conversion + thumbnail generation |
| **12** | FastAPI routes | ✅ Yes | Services | `TestClient` |
| **13** | TypeScript MCP tools (trade, account, calculator, image, discovery) | ✅ Yes | REST API, ToolsetRegistry | `vitest` with mocked `fetch()` |
| **14** | MCP + REST integration test | ✅ Yes | Both live | TS MCP calling live Python API |
| **15** | Electron + React UI shell ([06a](06a-gui-shell.md)) | ✅ Yes | REST API | React Testing Library + Playwright |
| **15a** | Settings REST endpoints (`GET`/`PUT /settings`) | ✅ Yes | Services | `TestClient` round-trip |
| **15b** | Settings MCP tools (`get_settings`, `update_settings`) | ✅ Yes | REST API | `vitest` with mocked `fetch()` |
| **15c** | Command registry (`commandRegistry.ts`) ([06a](06a-gui-shell.md)) | ✅ Yes | Nothing | Vitest: all entries have unique ids, valid actions |
| **15d** | Window state persistence (`electron-store`) ([06a](06a-gui-shell.md)) | Playwright E2E (Wave 0) | Electron | Launch → move → close → relaunch → verify position |
| **15e** | MCP Guard: `McpGuardModel` + REST endpoints + MCP middleware + GUI | ✅ Yes | REST API, MCP tools | Circuit breaker, panic button, per-minute/hour rate limits ([02](02-infrastructure.md), [04](04-rest-api.md), [05](05-mcp-server.md), [06f](06f-gui-settings.md)) |
| **15f** | `zorivest_diagnose` MCP tool ([§5.8](05-mcp-server.md)) | ✅ Yes | REST API, MCP Guard | Vitest: reachable/unreachable backend, never leaks keys |
| **15g** | Per-tool performance metrics middleware ([§5.9](05-mcp-server.md)) | ✅ Yes | Nothing | Vitest: latency recording, percentile accuracy, error rate |
| **15h** | `zorivest_launch_gui` MCP tool ([§5.10](05-mcp-server.md)) | ✅ Yes | Nothing | Vitest: found/not-found paths, platform commands, setup instructions |
| **15i** | MCP Server Status panel ([§6f.9](06f-gui-settings.md)) | Playwright E2E — wave TBD | REST API, MCP tools | E2E: status indicators, IDE config copy |
| **15j** | Discovery meta-tools: `list_available_toolsets`, `describe_toolset`, `enable_toolset`, `get_confirmation_token` ([05j](05j-mcp-discovery.md)) | ✅ Yes | ToolsetRegistry | Vitest: registry enumeration, annotation echo, enable/disable toggle, MCP-local token lifecycle |
| **15k** | `ToolsetRegistry` module + adaptive client detection ([§5.11–§5.14](05-mcp-server.md)) | ✅ Yes | Nothing | Vitest: toolset CRUD, `core` immutability, client capability negotiation |
| **16** | React pages — Trades ([06b](06b-gui-trades.md)), Plans ([06c](06c-gui-planning.md)) | Playwright E2E (Wave 1 + 4) | API hooks | E2E route/nav + happy-path verification |
| **16.1** | Screenshot wiring — ScreenshotPanel → image REST API ([06b §Screenshot](06b-gui-trades.md)) | ✅ Yes | MEU-47 ✅, MEU-22 ✅ | Vitest: upload/delete mutations, query invalidation |
| **16a** | Notification system ([06a](06a-gui-shell.md)) | Playwright E2E — wave TBD | Settings API | E2E toast display + suppression toggle |
| **16b** | Command palette ([06a](06a-gui-shell.md), Ctrl+K) | Playwright E2E — wave TBD | Registry | E2E: open palette, search, navigate |
| **16c** | UI state persistence ([06a](06a-gui-shell.md)) | Playwright E2E (Wave 0) | Settings API | E2E: change → restart → verify restored |

> **Note**: Items 13 and 15 cover **core** MCP tools, discovery meta-tools, and GUI shell only. Market-data MCP tools and the Market Data Settings page depend on Phase 8 (items 21–30 in P1.5) and must not be started until P1.5 is reached.

> **Release gate**: Item 15e (MCP Guard) must pass before any MCP-enabled release. Do not ship MCP tools without abuse controls.

---

## P1 — Build Soon (Trade Reviews + Multi-Account)

| Order | What | Tests First? | Notes |
|-------|------|-------------|-------|
| **17** | TradeReport entity + service | ✅ Yes | Post-trade journaling with ratings, tags, images |
| **18** | TradeReport MCP tools + API routes | ✅ Yes | `create_report`, `get_report_for_trade` |
| **19** | Multi-account UI (account type badges, filtering) | ✅ Yes | Filter trades by account type |
| **20** | Report GUI panel ([06b](06b-gui-trades.md): ratings, tags, lessons) | Playwright E2E — wave TBD | Attached to trade detail view |

---

## P1.5 — Market Data Aggregation (Phase 8)

> **Source**: [`_inspiration/_market_tools_api-architecture.md`](../../_inspiration/_market_tools_api-architecture.md). See [Phase 8](08-market-data.md) for full spec.

| Order | What | Tests First? | Notes |
|-------|------|-------------|-------|
| **21** | `MarketDataProvider` entity + `AuthMethod` enum | ✅ Yes | 11 provider configs, 4 auth methods |
| **22** | Normalized response DTOs (`MarketQuote`, `MarketNewsItem`, etc.) | ✅ Yes | Pydantic models for cross-provider normalization |
| **23** | `MarketProviderSettingModel` + encrypted key storage | ✅ Yes | SQLAlchemy table, Fernet encrypt/decrypt |
| **24** | Provider registry (singleton config map) | ✅ Yes | All 11 providers with auth templates, test endpoints |
| **25** | `ProviderConnectionService` (test, configure, list) | ✅ Yes | Connection testing framework with response validation |
| **26** | `MarketDataService` (quote, news, search, SEC filings) | ✅ Yes | Provider fallback chain, response normalization |
| **27** | Rate limiter (token-bucket per provider) + log redaction | ✅ Yes | Async token-bucket, API key masking |
| **28** | Market data REST API endpoints (8 routes) | ✅ Yes | FastAPI under `/api/v1/market-data/` |
| **29** | Market data MCP tools (6 tools) | ✅ Yes | TypeScript via `registerMarketDataTools` |
| **30** | Market Data Providers GUI settings page ([06f](06f-gui-settings.md)) | Playwright E2E (Wave 6) | Provider list, connection testing, API key management |

---

## P1.5a — Market Data Expansion (Phase 8a)

> **Source**: [08a-market-data-expansion.md](08a-market-data-expansion.md). Extends Phase 8 with full data retrieval across 11 API-key providers.

| Order | What | Tests First? | Notes |
|-------|------|-------------|-------|
| **30.0** | Benzinga code purge: remove provider config, normalizer, validator, service branch, tests (MEU-182a) | N/A | Prerequisite: aligns codebase to 11-provider docs |
| **30.1** | Expansion DTOs: OHLCV, Fundamentals, Earnings, Dividends, Splits, Insider, EconomicCalendar (MEU-182) | ✅ Yes | 7 new frozen dataclasses + `MarketDataPort` extended |
| **30.2** | DB tables: `market_earnings`, `market_dividends`, `market_splits`, `market_insider` (MEU-183) | ✅ Yes | SQLAlchemy models via `create_all()` |
| **30.3** | `ProviderCapabilities` registry (MEU-184) | ✅ Yes | builder_mode, auth_mode, extractor_shape for all 11 providers |
| **30.4** | Simple GET URL builders: Alpaca, FMP, EODHD, API Ninjas, Tradier (MEU-185) | ✅ Yes | `base_url + path + query_params` pattern |
| **30.5** | Special-pattern builders: Alpha Vantage, Nasdaq DL, OpenFIGI, SEC API (MEU-186) | ✅ Yes | function-dispatch, dataset/table, POST-body |
| **30.6** | Standard extractors: Alpaca, FMP, EODHD, API Ninjas, Tradier + ~25 field mappings (MEU-187) | ✅ Yes | JSON envelope unwrap + field mapping tuples |
| **30.7** | Complex extractors: Alpha Vantage, Finnhub, Nasdaq DL, Polygon + ~20 field mappings (MEU-188) | ✅ Yes | Parallel arrays, date-keyed dicts, CSV parsing |
| **30.8** | POST-body extractors: OpenFIGI v3, SEC API + ~10 field mappings (MEU-189) | ✅ Yes | v3 warning key rename, Lucene response |
| **30.9** | Core service methods: `get_ohlcv`, `get_fundamentals`, `get_earnings` + normalizers (MEU-190) | ✅ Yes | Primary/fallback chains, per-provider normalizers |
| **30.10** | Extended service methods: dividends, splits, insider, economic_calendar, company_profile (MEU-191) | ✅ Yes | 5 additional methods + normalizers |
| **30.11** | REST routes + MCP actions: 8 new endpoints + 8 MCP action mappings (MEU-192) | ✅ Yes | `GET /api/v1/market-data/{type}` + `zorivest_market` |
| **30.12** | `MarketDataStoreStep` pipeline step (MEU-193) | ✅ Yes | Route normalized DTOs to DB tables, INSERT/UPSERT |
| **30.13** | Scheduling recipes: 10 pre-built policy templates (MEU-194) | ✅ Yes | Alembic-seeded cron templates |
| **30.14** | Polygon→Massive domain migration (MEU-195) | ✅ Yes | Update `base_url` from `api.polygon.io` to `api.massive.com`, `signup_url`, display name; verify connection test passes; no API schema changes |
| **30.15** | Capability wiring: inject NORMALIZERS + align supported_data_types (MEU-207) | ⬜ Pending | Corrective: inject `normalizers=NORMALIZERS` kwarg in `MarketDataService()`, update `provider_capabilities.py` tuples to match normalizer coverage |

---

## P2 — Build Next (Planning + Watchlists)

| Order | What | Tests First? | Notes |
|-------|------|-------------|-------|
| **31** | TradePlan entity + service | ✅ Yes | Conviction, strategy, entry/exit conditions |
| **32** | TradePlan ↔ Trade linking (plan → execution) | ✅ Yes | `followed_plan` in TradeReport |
| **33** | Watchlist entity + service | ✅ Yes | Named lists of tickers |
| **34** | TradePlan + Watchlist MCP tools | ✅ Yes | AI agent can create/query plans |
| **35** | Planning GUI ([06c](06c-gui-planning.md): plan cards, watchlists) | Playwright E2E ([Wave 4](06-gui.md#wave-activation-schedule)) | List+detail layout, conviction indicators |
| **35a** | Account Management GUI ([06d](06d-gui-accounts.md)) | Playwright E2E ([Wave 2](06-gui.md#wave-activation-schedule)) | Account CRUD, Review wizard, balance history |
| **35b** | Scheduling GUI ([06e](06e-gui-scheduling.md)) | Playwright E2E ([Wave 8](06-gui.md#wave-activation-schedule)) | Policy editor, cron preview, pipeline run history |
| **35b.2** | Email Templates tab ([06k](06k-gui-email-templates.md)) (MEU-72b) | Playwright E2E ([Wave 8](06-gui.md#wave-activation-schedule)) | Template CRUD, preview iframe, default protection. Depends on 35b |
| **35c** | Email Provider Settings GUI ([06f](06f-gui-settings.md)) | Playwright E2E — wave TBD | SMTP config, preset auto-fill, test connection |
| **35d** | Backup & Restore Settings GUI ([06f](06f-gui-settings.md)) | Playwright E2E ([Wave 3](06-gui.md#wave-activation-schedule)) | Manual backup, restore, verify, auto-backup config |
| **35e** | Config Export/Import GUI ([06f](06f-gui-settings.md)) | Playwright E2E — wave TBD | JSON export download, import with preview diff |
| **35f** | Reset to Default on settings pages ([06f](06f-gui-settings.md)) | Playwright E2E — wave TBD | Source indicator, per-setting reset, bulk reset |
| **35g** | `DashboardService` + 6 REST endpoints ([03](03-service-layer.md), [06j](06j-gui-home.md)) | ✅ Yes | Read-only aggregation of accounts, trades, plans, watchlists, jobs |
| **35h** | Home Dashboard GUI ([06j](06j-gui-home.md)) | Playwright E2E (Wave 7) | Default startup route `/`, skeleton loading, settings (toggle/reorder sections), nav rail update |

---

## P2.1 — GUI UX Hardening

> **Source**: [06-gui.md §UX Hardening](06-gui.md#ux-hardening--unsaved-changes-guard). Extracts the unsaved-changes guard from SchedulingLayout into shared infrastructure and rolls it out across all data-entry modules.

| Order | What | Tests First? | Notes |
|-------|------|-------------|-------|
| **35i** | Shared `UnsavedChangesModal` + `useFormGuard` hook + amber-pulse CSS (MEU-196) | ✅ Yes | Extract from SchedulingLayout; refactor Scheduling to consume shared components; Vitest unit tests for hook + component |
| **35j** | Form guard wiring — Market Data Providers (MEU-197) | ✅ Yes | Wire `useFormGuard` to Market Data Providers; add amber-pulse save button; replace "off" → "Disabled" label. Depends on MEU-196 |
| **35k** | Form guard wiring — CRUD pages (MEU-198) | ✅ Yes | Wire `useFormGuard` to Accounts, Trades, Trade Plans, Watchlists; add amber-pulse save button to all. Depends on MEU-196 |

---

## P2.2 — GUI Table & List Enhancements

> **Source**: [06-gui.md §GUI Shipping Gate](06-gui.md#gui-shipping-gate-mandatory-for-all-gui-meus), [approved proposal](../../docs/execution/plans/2026-05-03-gui-table-list-enhancements/gui-table-list-enhancements-proposal.md). Delete confirmation, multi-select + bulk delete, and unified filter/sort across 5 GUI surfaces. Depends on P2.1 (MEU-196/197/198).

| Order | What | Tests First? | Notes |
|-------|------|-------------|-------|
| **35l** | Shared table/list primitives: `ConfirmDeleteModal`, `useConfirmDelete`, `BulkActionBar`, `SortableColumnHeader`, `TableFilterBar`, `SelectionCheckbox`, `useTableSelection`, `table-enhancements.css` (MEU-199) | ✅ Yes | Infrastructure MEU; unblocks 35m–35p. E2E Wave 10. |
| **35m** | Accounts table enhancements (MEU-200) | ✅ Yes | Delete confirm, multi-select, bulk delete, filter/sort on AccountsHome. Depends on 35l |
| **35n** | Trade Plans table enhancements (MEU-201) | ✅ Yes | Delete confirm, multi-select, bulk delete, filter/sort on TradePlanPage. Depends on 35l |
| **35o** | Watchlist tickers table enhancements (MEU-202) | ✅ Yes | Delete confirm, multi-select, bulk remove, filter/sort on WatchlistTable. Depends on 35l |
| **35p** | Scheduling list enhancements — Policies + Email Templates (MEU-203) | ✅ Yes | Delete confirm, multi-select, bulk delete, filter/sort on PolicyList + EmailTemplateList. Sidebar list pattern preserved. Depends on 35l |

---

## P2.5 — Scheduling & Pipeline Engine (Phase 9)

> **Source**: [Scheduling Integration Roadmap](../../_inspiration/scheduling_research/scheduling-integration-roadmap.md). See [Phase 9](09-scheduling.md) for full spec.

| Order | What | Tests First? | Notes |
|-------|------|-------------|-------|
| **36** | Pipeline domain enums (`PipelineStatus`, `StepErrorMode`, `DataType`) | ✅ Yes | 3 enums, Pydantic validation |
| **37** | `PolicyDocument` + `PolicyStep` Pydantic models | ✅ Yes | Schema v1 with trigger, retry, skip_if |
| **38** | `StepBase` Protocol + `RegisteredStep` metaclass + `StepRegistry` | ✅ Yes | Auto-registration, type_name lookup |
| **39** | `PolicyValidator` (schema, refs, cron, blocklist) | ✅ Yes | 8 validation rules, content hashing |
| **40** | SQLAlchemy models (9 tables: policies, runs, steps, state, reports, cache, audit) | ✅ Yes | In-memory SQLite, relationships |
| **41** | Repository implementations + audit triggers | ✅ Yes | CRUD, append-only audit, versioning triggers |
| **42** | `PipelineRunner` (sequential async executor) | ✅ Yes | Retry, skip, dry-run, resume from failure |
| **43** | `RefResolver` + `ConditionEvaluator` | ✅ Yes | Nested ref paths, 10 operators |
| **44** | `FetchStep` + criteria resolver + HTTP cache | ✅ Yes | Rate limiting, ETag revalidation, freshness TTL |
| **45** | `TransformStep` + Pandera validation + write dispositions | ✅ Yes | Field mapping, append/replace/merge, quarantine |
| **46** | `StoreReportStep` + SQL sandbox + `RenderStep` (Jinja2/Plotly/PDF) | ✅ Yes | Default-deny authorizer, snapshot provenance |
| **47** | `SendStep` + async email + delivery tracking | ✅ Yes | aiosmtplib, idempotent dedup, local file |
| **48** | Scheduling REST API (16 endpoints) + MCP tools (6 tools + 2 resources) | ✅ Yes | Policy CRUD, run trigger, scheduler status |
| **49** | Security guardrails (rate limits, approval flow, audit trail) | ✅ Yes | Human-in-the-loop, hash-based re-approval |
| **49.4** | Pipeline runtime wiring (MEU-PW1) | ✅ Yes | Expand `PipelineRunner` constructor (6 new params); create `DbWriteAdapter`; add `get_smtp_runtime_config()` to `EmailProviderService`; wire all services in `main.py`; delete dead stubs. Makes 4/5 step types operational. |
| **49.5** | Fetch step integration (MEU-PW2) | ✅ Yes | Create `MarketDataProviderAdapter` (new service); implement `_check_cache()` with FRESHNESS_TTL; integrate `PipelineRateLimiter`; connect `fetch_with_cache()` HTTP revalidation. Makes 5/5 step types operational. Depends on PW1. |
| **49.6** | Market data schemas (MEU-PW3) | ✅ Yes | 4 SQLAlchemy models (`market_ohlcv/quotes/news/fundamentals`); 3 Pandera schemas; field mappings for non-OHLCV types. Data quality hardening — independent of PW1/PW2. |
| **49.7** | WebSocket infrastructure (MEU-174) | ✅ Yes | FastAPI `ConnectionManager` + `/ws` endpoint; Electron `WebSocketBridge` (main → renderer relay); event routing (`pnl.tick`, `trade.update`, `notification`). Foundation for real-time dashboard updates and tray icon badge count. |

---

## P2.5c — Pipeline Security Hardening

> **Source**: [retail-trader-policy-use-cases.md](../../_inspiration/policy_pipeline_wiring-research/retail-trader-policy-use-cases.md) (validated by 3-model adversarial review — Claude, Gemini, ChatGPT). See [09c](09c-pipeline-security-hardening.md), [09d](09d-pipeline-step-extensions.md), [09e](09e-template-database.md), [09f](09f-policy-emulator.md) for full specs.

| Order | What | Tests First? | Notes |
|-------|------|-------------|-------|
| **49.16** | StepContext `safe_deepcopy` + `Secret` carrier (MEU-PH1) | ✅ Yes | Guarded deep-copy on `get_output()`/`put()`, credential leakage prevention (6 tests). [09c §9C.1](09c-pipeline-security-hardening.md) |
| **49.17** | SQL sandbox: `set_authorizer` + `mode=ro` + AST allowlist (MEU-PH2) | ✅ Yes | 6-layer security stack, sqlglot allowlist, secrets scan, policy content IDs (14 tests). [09c §9C.2](09c-pipeline-security-hardening.md) |
| **49.18** | SendStep confirmation gate + FetchStep MIME/fan-out (MEU-PH3) | ✅ Yes | `requires_confirmation` field, MIME validation, body size cap, fan-out cap (6 tests). [09c §9C.3–9C.4](09c-pipeline-security-hardening.md) |
| **49.19** | QueryStep implementation (MEU-PH4) | ✅ Yes | Read-only SQL via sandbox, parameterized binds, row limit, ref support (8 tests). [09d §9D.1](09d-pipeline-step-extensions.md) |
| **49.20** | ComposeStep implementation (MEU-PH5) | ✅ Yes | Multi-source data merging, `dict_merge`/`array_concat` strategies (5 tests). [09d §9D.2](09d-pipeline-step-extensions.md) |
| **49.21** | EmailTemplateModel + HardenedSandbox + nh3 (MEU-PH6) | ✅ Yes | DB-backed templates, `ImmutableSandboxedEnvironment`, filter allowlist, attribute deny-list, markdown sanitization (17 tests). [09e](09e-template-database.md) |
| **49.22** | PolicyDocument `variables` + assertion gates + step-count cap (MEU-PH7) | ✅ Yes | Variable injection, `kind: assertion` discriminator, 20-step Pydantic cap (8 tests). [09d §9D.3–9D.5](09d-pipeline-step-extensions.md) |
| **49.23** | 4-phase policy emulator + output containment (MEU-PH8) | ✅ Yes | PARSE→VALIDATE→SIMULATE→RENDER, 64 KiB session budget, SHA-256 RENDER, `EmulatorError`/`EmulatorResult` Pydantic models (15 tests). [09f](09f-policy-emulator.md) |
| **49.24** | 11 new MCP tools: emulator, schema discovery, template CRUD (MEU-PH9) | ✅ Yes | TypeScript via `registerPipelineSecurityTools`, Vitest mocks. [05g](05g-mcp-scheduling.md) |
| **49.25** | Default Morning Check-In template (MEU-PH10) | ✅ Yes | Pre-seeded Alembic migration, multi-section template. [09e §9E.6](09e-template-database.md) |

---

## P2.5d — Approval Security & Validation Hardening

> **Source**: [09g-approval-security.md](09g-approval-security.md), [09f-policy-emulator.md](09f-policy-emulator.md) (extension). See also [09h-pipeline-markdown-migration.md](09h-pipeline-markdown-migration.md).

| Order | What | Tests First? | Notes |
|-------|------|-------------|-------|
| **49.26** | CSRF approval token: Electron IPC → API middleware (MEU-PH11) | ✅ Yes | Single-use, 5-min TTL, policy-scoped. Blocks agent self-approval. [09g §1](09g-approval-security.md) |
| **49.27** | MCP scheduling gap fill: `delete_policy`, `update_policy`, `get_email_config` (MEU-PH12) | ✅ Yes | `delete_policy` requires confirmation token. [09g §2](09g-approval-security.md) |
| **49.28** | Emulator VALIDATE phase hardening (MEU-PH13) | ✅ Yes | EXPLAIN SQL errors, SMTP config check, step wiring validation. [09f ext](09f-policy-emulator.md) |
| **49.29** | Pipeline Markdown migration (MEU-PW14) | ✅ Yes | PDF removal, `_render_markdown()`, Playwright dep cleanup. [09h](09h-pipeline-markdown-migration.md) |

---

## P2.5e — MCP Tool Remediation

> **Source**: [MCP Tool Audit Report](../../.agent/context/MCP/mcp-tool-audit-report.md). Resolves [MCP-TOOLAUDIT] findings from comprehensive 74-tool CRUD audit.

| Order | What | Tests First? | Notes |
|-------|------|-------------|-------|
| **5.J** | Fix `delete_trade` 500 error (MEU-TA1) | ✅ Yes | Debug API trade deletion endpoint, fix error handling. [MCP-TOOLAUDIT] High finding. |
| **5.K** | Fix `update_settings` serialization bug (MEU-TA2) | ✅ Yes | TypeScript `[object Object]` → string serialization. [MCP-TOOLAUDIT] Medium. |
| **5.L** | Guard unimplemented MCP tools (MEU-TA3) | ✅ Yes | 6 tools (`list_bank_accounts`, `list_brokers`, `resolve_identifiers`, tax toolset) return 501 instead of 404/500. [MCP-TOOLAUDIT] Medium. |
| **5.M** | Trade plan lifecycle MCP tools (MEU-TA4) | ✅ Yes | Add `list_trade_plans`, `delete_trade_plan`. Fix `create_trade_plan` 409. [MCP-TOOLAUDIT] Medium. |

---

## P2.5f — MCP Tool Consolidation

> **Source**: [mcp-consolidation-proposal-v3.md](../../.agent/context/MCP/mcp-consolidation-proposal-v3.md). Resolves [MCP-TOOLPROLIFERATION] — 85 registerTool() calls → 13 compound tools.

| Order | What | Tests First? | Notes |
|-------|------|-------------|-------|
| **5.N** | Documentation sync: BUILD_PLAN.md, meu-registry.md, known-issues, 05-mcp-server.md §5.11, mcp-tool-index.md, build-priority-matrix.md (MC0) | N/A | Docs-only. Pre-condition for all code MEUs. |
| **5.O** | CompoundToolRouter + `zorivest_system` compound tool, 9 actions (MC1) | ✅ Yes | Router infrastructure + first compound tool. Tools/list: 86→77. |
| **5.P** | `zorivest_trade` (6), `zorivest_report` (2), `zorivest_analytics` (13) compound tools (MC2) | ✅ Yes | Trade vertical. Tools/list: 77→59. |
| **5.Q** | `zorivest_account` (9), `zorivest_market` (7), `zorivest_watchlist` (5), `zorivest_import` (7), `zorivest_tax` (4 stubs) compound tools (MC3) | ✅ Yes | Data vertical. Tools/list: 59→32. |
| **5.R** | `zorivest_plan` (3), `zorivest_policy` (9), `zorivest_template` (6), `zorivest_db` (5) compound tools; seed.ts 10→4 toolsets; CI gate `tool_count ≤ 13` (MC4) | ✅ Yes | Ops vertical + final restructure. Tools/list: 32→13. |
| **5.S** | Baseline snapshot (85→13), server instructions, anti-placeholder scan, MCP audit, archive [MCP-TOOLPROLIFERATION] (MC5) | ✅ Yes | Finalization + evidence. |

---

## P2.5g — MCP Auth Infrastructure

> **Source**: [known-issues.md](../../.agent/context/known-issues.md) [MCP-AUTHRACE]. Resolves authentication race condition in MCP token lifecycle.

| Order | What | Tests First? | Notes |
|-------|------|-------------|-------|
| **5.T** | `TokenRefreshManager` singleton with promise coalescing, 30s proactive expiry, async `getAuthHeaders()` (MEU-PH14) | ✅ Yes | Removes module-level `authState`/`bootstrapAuth()`; all call sites use `await getAuthHeaders()`. 14 FIC tests. [05-mcp-server.md §5.7](05-mcp-server.md) |

---

## P2.6 — Service Daemon (Phase 10)

> See [Phase 10](10-service-daemon.md) for full spec.

| Order | What | Tests First? | Notes |
|-------|------|-------------|-------|
| **49a** | Service config files (WinSW XML, launchd plist, systemd unit) | No tests needed | Template files, platform-native |
| **49b** | `ServiceManager` class + IPC bridge (Electron main process) | ✅ Yes | Vitest: platform-specific start/stop/status commands |
| **49c** | Service REST endpoints (`/service/status`, `/service/graceful-shutdown`) | ✅ Yes | `TestClient`: process metrics, graceful restart |
| **49d** | Service MCP tools (`zorivest_service_status`, `_restart`, `_logs`) | ✅ Yes | Vitest: reachable/unreachable, restart polling, log listing |
| **49e** | Service Manager GUI (Settings panel) + installer hooks (NSIS, first-launch) | Playwright E2E — wave TBD | Status polling, start/stop/restart, auto-start toggle, open log folder |
| **49f** | `TrayIconRenderer` (OffscreenCanvas → NativeImage) | ✅ Yes | 16/24/32px platform-aware base icons; canvas-drawn status dot (green/yellow/red/gray) + notification badge overlay; state machine (NORMAL → WARNING → ERROR → OFFLINE). No file-system icon swapping. |
| **49g** | Tray icon integration + context menu | ✅ Yes | Wire renderer to `ServiceManager` health polling + WebSocket notification events; dynamic context menu (Show/Hide, Quick Actions, status line); OS theme detection (`nativeTheme.on('updated')`); click-to-show behavior. |

---

## P2.75 — Build Plan Expansion (Analytics, Behavioral, Import)

> **Source**: [Build Plan Expansion Ideas](../../_inspiration/import_research/Build%20Plan%20Expansion%20Ideas.md) §1–§26. Features depend on P0–P2 trade/account infrastructure.

### Broker Adapters & Import

| Order | What | Tests First? | Notes |
|-------|------|-------------|-------|
| **50e** | IBKR FlexQuery adapter (§1) | ✅ Yes | XML parsing, trade normalization |
| **51e** | Alpaca REST adapter (§24) | ✅ Yes | `alpaca-py`, position sync |
| **52e** | Tradier REST adapter (§25) | ✅ Yes | REST client, order history |
| **53e** | CSV import service + broker auto-detection (§18) | ✅ Yes | Header pattern matching |
| **54e** | PDF statement parser (§19) | ✅ Yes | `pdfplumber`, tabular extraction |
| **55e** | Deduplication service (§6) | ✅ Yes | Exact + fuzzy matching, merge UI |
| **56e** | Identifier resolver / CUSIP→ticker (§5) | ✅ Yes | OpenFIGI API, cache layer |
| **57e** | Bank statement import (§26) | ✅ Yes | OFX/CSV/QIF parsing, dedup |

### Analytics & Behavioral

| Order | What | Tests First? | Notes |
|-------|------|-------------|-------|
| **58e** | Round-trip service (§3) | ✅ Yes | Entry→exit pairing, aggregate P&L |
| **59e** | MFE/MAE/BSO excursion service (§7) | ✅ Yes | Historical bar data, efficiency % |
| **60e** | Options strategy grouping (§8) | ✅ Yes | Multi-leg detection (condor, straddle) |
| **61e** | Transaction ledger / fee decomposition (§9) | ✅ Yes | Commission + exchange + regulatory |
| **62e** | Execution quality scoring (§10) | ✅ Yes | NBBO comparison, A–F grading |
| **63e** | PFOF analysis (§11) | ✅ Yes | Probabilistic model, labeled ESTIMATE |
| **64e** | AI review multi-persona (§12) | ✅ Yes | Budget cap, opt-in, persona routing |
| **65e** | Expectancy + edge metrics (§13) | ✅ Yes | Win rate, Kelly %, payoff ratio |
| **66e** | Monte Carlo drawdown (§14) | ✅ Yes | `numpy`/`scipy`, seed reproducibility |
| **67e** | Mistake tracking service (§17) | ✅ Yes | Category enum, cost attribution |
| **68e** | Strategy breakdown (§21) | ✅ Yes | P&L per strategy name from tags |
| **68.1e** | SQN service (§15) | ✅ Yes | Van Tharp SQN + grade classification |
| ~~**68.2e**~~ | ~~PDF statement parser (§19)~~ | — | **Duplicate of item 54e** — see Broker Adapters & Import section above |
| **68.3e** | Cost of Free analysis (§22) | ✅ Yes | PFOF + fee hidden cost report |
| **68.4e** | Trade↔journal linking (§16) | ✅ Yes | Bidirectional FK + service |

### Expansion API + MCP + GUI

| Order | What | Tests First? | Notes |
|-------|------|-------------|-------|
| **69e** | REST routes (10 groups: brokers, analytics, banking, import, ...) | ✅ Yes | `TestClient` e2e |
| **70e** | MCP tools (22 expansion tools) | ✅ Yes | `vitest` with mocked `fetch()` |
| **71e** | Trade detail GUI tabs (Excursion, Fees, Mistakes, Expectancy, ...) | Playwright E2E — wave TBD | 10 new React components |
| **72e** | Account GUI enhancements (Bank import, Broker sync, Column mapping) | Playwright E2E — wave TBD | 5 new React components |
| **73e** | Analytics dashboard GUI (planned) | Playwright E2E — wave TBD | SQN, drawdown, strategy, monthly P&L calendar |

---

## P3 — Build Later (Tax Estimation)

> **Research phase complete.** See [Domain Model Reference](domain-model-reference.md) for full feature spec (Modules A–G, 35 features).
> Build in 5 sub-phases so each sub-phase is independently testable.

### Phase 3A — Core Tax Engine (Module A)

| Order | What | Tests First? | Notes |
|-------|------|-------------|-------|
| **50** | `TaxLot` entity + `CostBasisMethod` enum | ✅ Yes | 8 cost basis methods (FIFO → Max ST Loss) |
| **51** | `TaxProfile` entity + `FilingStatus` enum | ✅ Yes | Settings: bracket, state, filing status, section elections |
| **52** | Tax lot tracking: open/close lots, holding period | ✅ Yes | Every buy → TaxLot. Every sell → close lots via selected method |
| **53** | ST vs LT classification + gains calculator | ✅ Yes | < 366 days = ST @ ordinary rate, ≥ 366 = LT @ 0/15/20% |
| **54** | Capital loss carryforward + account exclusion | ✅ Yes | $3K/year cap, IRA/401K skip, prior-year rollover |
| **55** | Options assignment/exercise cost basis pairing | ✅ Yes | Put assignment → reduce basis, call exercise → add proceeds |
| **56** | YTD P&L by symbol | ✅ Yes | Realized gains per ticker, ST vs LT breakdown |

### Phase 3B — Wash Sale Engine (Module B)

| Order | What | Tests First? | Notes |
|-------|------|-------------|-------|
| **57** | `WashSaleChain` entity + basic 30-day detection | ✅ Yes | Loss deferral, basis adjustment on replacement lot |
| **58** | Wash sale chain tracking (deferred loss rolling) | ✅ Yes | Chain events: disallowed → absorbed → released |
| **59** | Cross-account wash sale aggregation | ✅ Yes | Check taxable + IRA + spouse accounts. IRA = permanent loss |
| **60** | Options-to-stock wash sale matching (configurable) | ✅ Yes | Method 1 (Conservative) vs Method 2 (Aggressive) toggle |
| **61** | DRIP wash sale detection | ✅ Yes | Flag when dividend reinvestment conflicts with harvested loss |
| **62** | Auto-rebalance + spousal cross-wash warnings | ✅ Yes | Warn on DCA/rebalance conflicts; optional spouse accounts |
| **63** | Wash sale prevention alerts (proactive) | ✅ Yes | Pre-trade: "Wait N days" or "This will trigger wash sale" |

### Phase 3C — Tax Optimization Tools (Module C)

| Order | What | Tests First? | Notes |
|-------|------|-------------|-------|
| **64** | Pre-trade "what-if" tax simulator | ✅ Yes | MCP: `simulate_tax_impact`. Show tax before executing |
| **65** | Tax-loss harvesting scanner | ✅ Yes | MCP: `harvest_losses`. Rank by amount, filter wash conflicts |
| **66** | Tax-smart replacement suggestions | ✅ Yes | Correlated non-identical securities (VOO→IVV, QQQ→QQQM) |
| **67** | Lot matcher / close specific lots UI | ✅ Yes | MCP: `get_tax_lots`. Show open lots with basis + days to LT |
| **68** | Post-trade lot reassignment window | ✅ Yes | Change method within T+1 settlement. Undo for tax mistakes |
| **69** | ST vs LT tax rate dollar comparison | ✅ Yes | "Wait 12 days → save $1,390." Show dollars at user's bracket |

### Phase 3D — Quarterly Payments & Tax Brackets (Modules D+E)

| Order | What | Tests First? | Notes |
|-------|------|-------------|-------|
| **70** | `QuarterlyEstimate` entity + safe harbor calc | ✅ Yes | 90% current OR 100%/110% prior year. Recommend lower |
| **71** | Annualized income method (Form 2210 Sched AI) | ✅ Yes | Proportional quarterly payments for fluctuating income |
| **72** | Quarterly due date tracker + underpayment penalty | ✅ Yes | MCP: `get_quarterly_estimate`. 4 deadlines + penalty accrual |
| **73** | Marginal tax rate calculator (federal + state) | ✅ Yes | Effective + marginal rate from AGI + filing status |
| **74** | NIIT (3.8% surtax) threshold alert | ✅ Yes | Flag when MAGI approaches $200K/$250K threshold |

### Phase 3E — Reports, Dashboard & MCP/API/GUI (Module F+G)

| Order | What | Tests First? | Notes |
|-------|------|-------------|-------|
| **75** | Tax REST API endpoints (FastAPI) | ✅ Yes | `/tax/estimate`, `/tax/wash-sales`, `/tax/simulate`, `/tax/lots`, `/tax/quarterly`, `/tax/harvest`, `/tax/ytd-summary` |
| **75a** | TaxProfile CRUD API (`GET`/`PUT /api/v1/tax/profile`) | ✅ Yes | Registers 12 TaxProfile keys in SettingsRegistry; returns/accepts TaxProfile as single JSON object; prerequisite for **82** toggle persistence. Depends on: 75 |
| **76** | Tax MCP tool registration (`registerTaxTools`) | ✅ Yes | 8 tools: `estimate_tax`, `find_wash_sales`, `simulate_tax_impact`, `get_tax_lots`, `get_quarterly_estimate`, `record_quarterly_tax_payment`, `harvest_losses`, `get_ytd_tax_summary` |
| **77** | Year-end tax position summary | ✅ Yes | MCP: `get_ytd_tax_summary`. Aggregate dashboard |
| **78** | Deferred loss carryover report | ✅ Yes | Real P&L vs reported P&L, trapped losses in chains |
| **79** | Tax alpha savings summary | ✅ Yes | YTD savings from lot optimization + loss harvesting |
| **80** | Error check / transaction audit | ✅ Yes | Scan for missing basis, dupes, impossible prices |
| **81** | Tax estimator GUI (React) — [06g-gui-tax.md](06g-gui-tax.md) | Playwright E2E — wave TBD (Phase 12+) | Dashboard, lot viewer, wash sales, what-if, harvesting, quarterly tracker |
| **81a** | Position calculator GUI (React) — [06h-gui-calculator.md](06h-gui-calculator.md) | Playwright E2E — wave TBD (expansion; base is [Wave 4](06-gui.md#wave-activation-schedule)) | Calculator expansion: multi-mode, scenario comparison, calculation history |
| **82** | Section 475 / 1256 / Forex toggles (conditional) | ✅ Yes | Mark-to-Market, 60/40 futures, forex worksheet. Depends on: **75a** (TaxProfile CRUD API for persistence) |

---

## P4 — Monetization (Phase 11)

> Source: [Phase 11](11-monetization.md). Subscription infrastructure + OAuth + BYOK.

| Order | What | Tests First? | Notes |
|-------|------|-------------|-------|
| **11.1** | Monetization domain (`License`, `SubscriptionTier`, `UsageMeter`) | ✅ Yes | Ed25519 JWT entities, tier enum, usage tracking |
| **11.2** | Google OAuth PKCE flow | ✅ Yes | BrowserWindow PKCE, encrypted token storage, refresh timer |
| **11.3** | Google Calendar + Tasks integration | ✅ Yes | Plan reminders → Calendar events, Watchlist actions → Tasks |
| **11.4** | License enforcement (`LicenseService`) | ✅ Yes | Ed25519 verify, offline grace (14d soft / 30d hard), device binding |
| **11.5** | BYOK AI provider keys | ✅ Yes | Encrypted key CRUD, periodic validation, usage tracking |
| **11.6** | Usage metering | ✅ Yes | Tier limits, approach-to-limit UX (green → yellow → red) |
| **11.7** | Monetization REST API + GUI | ✅ Yes | 11 endpoints, Subscription Settings page (license/usage/BYOK/Google) |

---

## Research-Enhanced Additions (2026-03-06)

> 10 features from the [MCP ecosystem research synthesis](file:///p:/zorivest/_inspiration/agentic_mcp_research/research-synthesis-correlation.md), placed in build plan execution order by dependency.

### Phase 5: MCP Server — Research Items

| Order | What | Tests First? | Insert After | Notes |
|-------|------|-------------|-------------|-------|
| **5.A** | Multi-dimensional tags (Tier 1) | ✅ Yes | Item 13 | Tag schema before any tool registers. Foundation for pipeline, BM25, metrics. |
| **5.B** | Pipeline stage registry (Tier 1) | ✅ Yes | Item 15e | Named stages need guard/metrics first. Formalizes composition into pluggable registry. |
| **5.C** | Health check route (Tier 1) | ✅ Yes | Item 15f | `/health` on port 8766. Service daemon needs it for liveness probes. |
| **5.D** | Schema drift detection CI (Tier 1) | ✅ Yes | Item 14 | Zod ↔ Pydantic comparison. Phase 5 exit criterion, CI formalized in Phase 7. |
| **5.E** | Structured output schemas (Tier 2) | ✅ Yes | Item 15k | Internal TypeScript interfaces first. Dual-format after SDK #911. |
| **5.F** | BM25 tool search (Tier 1) | ✅ Yes | Item 15k | Indexes tags from 5.A. Powers Anthropic discovery mode. |
| **5.G** | Keyword-triggered loading (Tier 2) | ✅ Yes | After 5.F | "tax" mention → suggest `enable_toolset('tax')`. Requires toolsets + client detection. |
| **5.H1** | Workspace setup tool core (Tier 2) ([05k](05k-mcp-setup-workspace.md)) | ✅ Yes | After 15k, after Phase 9 domain | `zorivest_setup_workspace` MCP tool — path confinement, atomic writes, `.scaffold-meta.json`, idempotency, core toolset registration. |
| **5.H2** | Workspace template content (Tier 2) ([05k](05k-mcp-setup-workspace.md)) | ✅ Yes | After 5.H1 | `AGENTS.md`, IDE shims (GEMINI/CLAUDE/CURSOR/CODEX), `.agent/` directory templates (docs, workflows, roles, rules, skills). |

### Post-Phase 8: Market Data — Research Items

| Order | What | Tests First? | Insert After | Notes |
|-------|------|-------------|-------------|-------|
| **8.A** | Code mode enhancement (Tier 2) | ✅ Yes | Item 29 | Expand PTC beyond Anthropic analytics. Requires stable tools from Phases 5 + 8. |

### Post-Phase 9: Scheduling — Research Items

| Order | What | Tests First? | Insert After | Notes |
|-------|------|-------------|-------------|-------|
| **9.A** | Recursive orchestration (Tier 3) | ✅ Yes | Item 49 | Multi-agent MCP chaining for automated pipelines. Requires scheduling engine maturity. |

### Phase 6: GUI — Research Items

| Order | What | Tests First? | Insert After | Notes |
|-------|------|-------------|-------------|-------|
| **6.A** | Floating P&L widget (BrowserWindow) | ✅ Yes | After 49.7 (WebSocket) | Always-on-top `BrowserWindow`, consumes `pnl.tick` WebSocket events, draggable, transparency/click-through toggle. Requires WebSocket foundation (49.7). |

---

**The first lines of code you write are `test_calculator.py` and `test_logging_config.py`. Phase 1 and Phase 1A start in parallel — both have zero dependencies.**
