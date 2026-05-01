# MEU Registry — Phase 1 + 1A + 2 + 2A + 3 + 4 + 5 + 6 + 8 + 9

> Source: [BUILD_PLAN.md](../docs/BUILD_PLAN.md) | [build-priority-matrix.md](../docs/build-plan/build-priority-matrix.md)

## Phase 1: Domain Layer (P0)

| MEU | Slug | Matrix | Description | Status |
|-----|------|:------:|-------------|:------:|
| MEU-1 | `calculator` | 1 | Position size calculator (pure math) | ✅ approved |
| MEU-2 | `enums` | 2 | All domain enums (AccountType, TradeAction, etc.) | ✅ approved |
| MEU-3 | `entities` | 3 | Domain entities (Trade, Account, Image, BalanceSnapshot) | ✅ approved |
| MEU-4 | `value-objects` | 4 | Value objects (Money, PositionSize, Ticker, ImageData, Conviction) | ✅ approved |
| MEU-5 | `ports` | 5 | Port interfaces (Protocols) | ✅ approved |
| MEU-6 | `commands-dtos` | 6 | Commands & DTOs | ✅ approved |
| MEU-7 | `events` | 7 | Domain events | ✅ approved |
| MEU-8 | `analytics` | 8 | Pure analytics functions + result types | ✅ approved |
| MEU-9 | `portfolio-balance` | 3a | TotalPortfolioBalance pure fn (sum latest balances) | ✅ approved |
| MEU-10 | `display-mode` | 3b | DisplayMode service ($, %, mask fns) | ✅ approved |
| MEU-11 | `account-review` | 3c | Account Review workflow (guided balance update) | ✅ approved |

## Phase 1A: Logging Infrastructure (P0 — Parallel)

| MEU | Slug | Matrix | Description | Status |
|-----|------|:------:|-------------|:------:|
| MEU-1A | `logging-manager` | 1A | LoggingManager, QueueHandler/Listener, JSONL | ✅ approved |
| MEU-2A | `logging-filters` | 1A | FeatureFilter, CatchallFilter + JsonFormatter | ✅ approved |
| MEU-3A | `logging-redaction` | 1A | RedactionFilter (API key masking, PII redaction) | ✅ approved |

## Phase 2: Infrastructure (P0)

| MEU | Slug | Matrix | Description | Status |
|-----|------|:------:|-------------|:------:|
| MEU-12 | `service-layer` | 6 | Core services (Trade, Account, Image, System) + domain exceptions + trade fingerprint | ✅ approved |
| MEU-13 | `sqlalchemy-models` | 7 | All 21 SQLAlchemy ORM models | ✅ approved |
| MEU-14 | `repositories` | 8 | Repository implementations (Trade, Image, Account, BalanceSnapshot, RoundTrip) | ✅ approved |
| MEU-15 | `unit-of-work` | 9 | SqlAlchemyUnitOfWork (5 repos) + WAL engine factory | ✅ approved |
| MEU-16 | `sqlcipher` | 10 | SQLCipher encrypted connection + Argon2/PBKDF2 KDF | ✅ approved |

## Phase 2A: Backup & Restore (P0)

| MEU | Slug | Matrix | Description | Status |
|-----|------|:------:|-------------|:------:|
| MEU-17 | `app-defaults` | 10a | AppDefaultModel + seed_defaults migration | ✅ approved |
| MEU-18 | `settings-resolver` | 10b | SettingsRegistry, Resolver, Validator, Cache, Service | ✅ approved |
| MEU-19 | `backup-manager` | 10c | BackupManager (Argon2id, GFS rotation, AES-ZIP) | ✅ approved |
| MEU-20 | `backup-recovery` | 10d | BackupRecoveryManager (restore + repair) | ✅ approved |
| MEU-21 | `config-export` | 10e | ConfigExportService (JSON export/import) | ✅ approved |

## Phase 3: Service Layer (P0)

| MEU | Slug | Matrix | Description | Status |
|-----|------|:------:|-------------|:------:|
| MEU-22 | `image-processing` | 11 | Image validation, WebP conversion, thumbnails | ✅ approved |

## Phase 4: REST API (P0)

| MEU | Slug | Matrix | Description | Status |
|-----|------|:------:|-------------|:------:|
| MEU-23 | `fastapi-routes` | 12 | FastAPI app factory + core routes | ✅ approved |
| MEU-24 | `api-trades` | 12 | Trade CRUD REST endpoints | ✅ approved |
| MEU-25 | `api-accounts` | 12 | Account REST endpoints | ✅ approved |
| MEU-26 | `api-auth` | 12 | Auth REST endpoints (unlock/lock/keys) | ✅ approved |
| MEU-27 | `api-settings` | 15a | Settings GET/PUT REST endpoints | ✅ approved |
| MEU-28 | `api-analytics` | 12 | Analytics REST endpoints | ✅ approved |
| MEU-29 | `api-tax` | 12 | Tax REST endpoints | ✅ approved |
| MEU-30 | `api-system` | 12 | System REST endpoints (logs, guard, service) | ✅ approved |

## Phase 5: MCP Server (P0)

| MEU | Slug | Matrix | Description | Status |
|-----|------|:------:|-------------|:------:|
| MEU-31 | `mcp-core-tools` | 13 | MCP server scaffold + trade/calculator tools | ✅ approved |
| MEU-32 | `mcp-integration-test` | 14 | MCP + REST integration test (TS → Python round-trip) | ✅ approved |
| MEU-33 | `mcp-settings` | 15b | Settings MCP tools (get/update) | ✅ approved |
| MEU-34 | `mcp-diagnostics` | 15f | zorivest_diagnose MCP tool | ✅ approved |
| MEU-35 | `mcp-trade-analytics` | 13 | Trade analytics MCP tools | ✅ approved |
| MEU-36 | `mcp-trade-planning` | 13 | Trade planning MCP tools | ✅ approved |
| MEU-37 | `mcp-accounts` | 13 | Account CRUD MCP tools (8 new) + account-trade integrity (system guards, archive, reassign, metrics) | ✅ approved |
| MEU-38 | `mcp-guard` | 15e | McpGuardModel + REST + middleware | ✅ approved |
| MEU-39 | `mcp-perf-metrics` | 15g | Per-tool performance metrics middleware | ✅ approved |
| MEU-40 | `mcp-launch-gui` | 15h | zorivest_launch_gui MCP tool | ✅ approved |
| MEU-41 | `mcp-discovery` | 15j | Discovery meta-tools | ✅ approved |
| MEU-42 | `toolset-registry` | 15k | ToolsetRegistry + adaptive client detection | ✅ approved |

## Phase 8: Market Data (P1)

| MEU | Slug | Matrix | Description | Status |
|-----|------|:------:|-------------|:------:|
| MEU-56 | `market-provider-entity` | 21 | AuthMethod enum + ProviderConfig VO + MarketDataPort Protocol | ✅ approved |
| MEU-57 | `market-response-dtos` | 22 | MarketQuote, MarketNewsItem, TickerSearchResult, SecFiling DTOs | ✅ approved |
| MEU-58 | `market-provider-settings` | 23 | API key encryption + encrypted_api_secret column | ✅ approved |
| MEU-59 | `market-provider-registry` | 24 | Static provider registry (12 providers; 2 free added by MEU-65) | ✅ approved |
| MEU-62 | `market-rate-limiter` | 25 | Token-bucket rate limiter + log redaction | ✅ approved |
| MEU-60 | `market-connection-svc` | 26 | ProviderConnectionService + persistence | ✅ approved |
| MEU-61 | `market-data-service` | 27 | MarketDataService + 10 normalizers | ✅ approved |
| MEU-63 | `market-data-api` | 28 | Market data REST API (8 routes) | ✅ approved |
| MEU-64 | `market-data-mcp` | 29 | Market data MCP tools (7 tools) | ✅ approved |
| MEU-65 | `market-data-gui` | 30 | Market Data Providers GUI settings page (14 providers, real service wiring, free provider badges, IPC external links, Wave 6 E2E) | ✅ approved |

## P1: Trade Reviews & Multi-Account

| MEU | Slug | Matrix | Description | Status |
|-----|------|:------:|-------------|:------:|
| MEU-52 | `trade-report-entity` | 17 | TradeReport entity + enums + service | ✅ approved |
| MEU-53 | `trade-report-mcp-api` | 18 | TradeReport MCP tools + API routes | ✅ approved |

## P2: Planning & Watchlists

| MEU | Slug | Matrix | Description | Status |
|-----|------|:------:|-------------|:------:|
| MEU-66 | `trade-plan-entity` | 31 | TradePlan entity + service + API (full stack) | ✅ approved |
| MEU-67 | `trade-plan-linking` | 32 | TradePlan ↔ Trade linking (link_plan_to_trade) | ✅ approved |
| MEU-68 | `watchlist` | 33 | Watchlist entity + service + API (7 REST endpoints) | ✅ approved |
| MEU-69 | `plan-watchlist-mcp` | 34 | Watchlist MCP tools (5 tools in trade-planning toolset) | ✅ approved |

## Phase 9: Scheduling & Pipeline Engine — Domain Foundation (P2.5)

| MEU | Slug | Matrix | Description | Status |
|-----|------|:------:|-------------|:------:|
| MEU-77 | `pipeline-enums` | 36 | PipelineStatus, StepErrorMode, DataType enums | ✅ approved |
| MEU-78 | `policy-models` | 37 | PolicyDocument + PolicyStep Pydantic models + StepContext/StepResult | ✅ approved |
| MEU-79 | `step-registry` | 38 | StepBase Protocol + RegisteredStep + STEP_REGISTRY + helpers | ✅ approved |
| MEU-80 | `policy-validator` | 39 | PolicyValidator (8 rules) + SHA-256 hash + SQL blocklist | ✅ approved |
| MEU-81 | `scheduling-models` | 40 | SQLAlchemy models (9 scheduling tables) + Alembic DDL trigger | ✅ approved |
| MEU-82 | `scheduling-repos` | 41 | 5 scheduling repositories + UoW extension (10→15 repos) | ✅ approved |
| MEU-83 | `pipeline-runner` | 42 | PipelineRunner (async executor with persistence/resume/zombie) | ✅ approved |
| MEU-84 | `ref-resolver` | 43 | RefResolver + ConditionEvaluator (param resolution + skip logic) | ✅ approved |

## Phase 9: Scheduling & Pipeline Engine — Pipeline Integration (P2.5b)

| MEU | Slug | Matrix | Description | Status |
|-----|------|:------:|-------------|:------:|
| MEU-PW1 | `pipeline-runtime-wiring` | 49.4 | Expand PipelineRunner constructor; DbWriteAdapter; SMTP bridge; wire main.py; delete dead stubs → 4/5 steps operational | ✅ 2026-04-12 |
| MEU-PW2 | `fetch-step-integration` | 49.5 | MarketDataProviderAdapter; cache impl; rate limiter; HTTP cache revalidation → 5/5 steps operational. Depends on PW1. | ✅ 2026-04-13 |
| MEU-PW3 | `market-data-schemas` | 49.6 | 4 SQLAlchemy models + 3 Pandera schemas + field mappings → data quality hardening. Independent. | ✅ complete |
| MEU-PW4 | `pipeline-charmap-fix` | 49.7 | Fix [PIPE-CHARMAP]: structlog UTF-8 config + bytes-safe JSON serialization. No deps. | ✅ 2026-04-19 |
| MEU-PW5 | `pipeline-zombie-fix` | 49.8 | Fix [PIPE-ZOMBIE]: eliminate dual-write, per-phase httpx.Timeout, zombie recovery. Depends PW4. | ✅ 2026-04-19 |
| MEU-PW6 | `provider-url-builders` | 49.9 | Fix [PIPE-URLBUILD]: per-provider URL builder registry + criteria normalization + headers. Depends PW5 (parallel PW7). | ⬜ planned |
| MEU-PW7 | `pipeline-cancellation` | 49.10 | Fix [PIPE-NOCANCEL]: CANCELLING status, task registry, cancel_run() + REST endpoint. Depends PW5 (parallel PW6). | ⬜ planned |
| MEU-PW8 | `pipeline-e2e-test-harness` | 49.11 | E2E test infrastructure: 7 policy fixtures, 6 mock steps, 14+ integration tests validating full service stack. Depends PW4–PW7. | 🟡 in-progress |
| MEU-PW9 | `send-step-template-wiring` | 49.12 | Wire `SendStep._resolve_body()` template rendering: EMAIL_TEMPLATES registry lookup + Jinja2 + html_body priority + raw fallback. Depends MEU-88 ✅. | ✅ 2026-04-20 |
| MEU-PW11 | `pipeline-cursor-tracking` | 49.13 | FetchStep cursor upsert after successful fetch: pipeline_state_repo.upsert() with ISO timestamp + SHA-256 hash. Depends MEU-PW2 ✅. | ✅ 2026-04-20 |
| MEU-72a | `scheduling-gui-tz-polish` | 35f.1 | PolicyList timezone display: replace toLocaleString with formatTimestamp IANA-aware utility. Independent. | ✅ 2026-04-20 |

## Execution Order

Phase 1: MEU-1 → MEU-2 → MEU-3 → MEU-4 → MEU-5 → MEU-6 → MEU-7 → MEU-8 → MEU-9 → MEU-10 → MEU-11
Phase 1A: MEU-2A → MEU-3A → MEU-1A (dependency order, parallel with Phase 1)
Phase 2: MEU-12 → MEU-13 → MEU-14 → MEU-15 → MEU-16
Phase 2A: MEU-17 → MEU-18 → MEU-19 → MEU-20 → MEU-21
Phase 3: MEU-22
Phase 4: MEU-23 → MEU-24 → MEU-25 → MEU-26 → MEU-27 → MEU-28 → MEU-29 → MEU-30
Phase 5: MEU-31 → MEU-32 → MEU-33 → MEU-34 → MEU-35 → MEU-36 → MEU-37 → MEU-38 → MEU-39 → MEU-40 → MEU-41 → MEU-42
Phase 8: MEU-56 → MEU-57 → MEU-58 → MEU-59 → MEU-62 → MEU-60
Phase 9 (domain foundation): MEU-77 → MEU-78 → MEU-79 → MEU-80
Phase 9 (pipeline integration): MEU-PW1 → MEU-PW2 (PW3 independent) → MEU-PW4 → MEU-PW5 → MEU-PW6 ∥ MEU-PW7 → MEU-PW8 → MEU-PW9 ∥ MEU-PW11 (MEU-72a independent)
P2.75 (broker adapters): MEU-96 → MEU-99

## P2.75 — Expansion: Broker Adapters & Import

| MEU | Slug | Matrix | Description | Status |
|-----|------|:------:|-------------|:------:|
| MEU-96 | `ibkr-adapter` | 50e | IBKR FlexQuery XML adapter (defusedxml, OCC symbols, multi-currency) | ✅ approved |
| MEU-99 | `csv-import` | 53e | CSV import framework + broker auto-detection (TOS, NinjaTrader, ImportService) | ✅ approved |

## Phase-Exit Criteria

- Phase 1: All 11 MEUs ✅ + `.\tools\validate.ps1` passes → Phase 2 unblocked
- Phase 1A: All 3 MEUs ✅ → logging available for outer-layer modules
- Phase 2: All 5 MEUs ✅ → Phase 2A unblocked
- Phase 2A: All 5 MEUs ✅ → Phase 3 unblocked
- Phase 3: MEU-22 ✅ → Phase 4 unblocked
- Phase 4: MEU-23..30 ✅ (all routes complete) → Phase 5 unblocked
- Phase 5: MEU-31..42 ✅ (all MCP tools complete) → Phase 6 unblocked
- Phase 8: MEU-56..60,62 ✅ (market data foundation + infrastructure) → Phase 8 adapters unblocked
- Phase 9 (domain): MEU-77..80 ✅ (pipeline enums, models, registry, validator) → Phase 9 infrastructure unblocked

## Phase 6: GUI Shell Foundation (P0)

| MEU | Slug | Matrix | Description | Status |
|-----|------|:------:|-------------|:------:|
| MEU-43 | `gui-shell` | 15 | Electron + React UI shell (AppShell, NavRail, Header, StatusFooter, splash, Python lifecycle) | ✅ approved |
| MEU-44 | `gui-command-registry` | 15c | Command registry + CommandPalette (13 static entries, Fuse.js fuzzy search, keyboard nav) | ✅ approved |
| MEU-45 | `gui-window-state` | 15d | Window state persistence (electron-store, bounds save/restore, first-launch defaults) | ✅ approved |
| MEU-46a | `mcp-rest-proxy` | 15i.1 | REST proxy endpoints (`GET /mcp/toolsets`, `GET /mcp/diagnostics`) + static manifest + McpServerStatusPanel live wiring | ✅ 2026-03-19 |
| MEU-50 | `gui-command-palette` | 16b | Command palette (Ctrl+K) | ✅ 2026-03-19 |
| MEU-51 | `gui-state-persistence` | 16c | UI state persistence: sidebar collapse (Zustand+localStorage `[UI-ESMSTORE]`), route restoration (usePersistedState), theme (usePersistedState) | ✅ 2026-03-19 |

## Phase 6: GUI Feature Wiring

| MEU | Slug | Matrix | Description | Status |
|-----|------|:------:|-------------|:------|
| MEU-47a | `screenshot-wiring` | 16.1 | Wire ScreenshotPanel to image REST API (useQuery/useMutation + DELETE route + ImageService.delete_image) | ✅ 2026-04-07 |
| MEU-70a | `watchlist-redesign-plan-size` | 06i | Watchlist visual redesign (professional data table, dark palette, colorblind toggle) + `position_size` full-stack propagation + calculator write-back (65 tests) | ✅ 2026-04-11 |
| MEU-72 | `gui-scheduling` | 35b | Scheduling & Pipeline GUI: policy list+detail, CodeMirror JSON editor, cron preview, run history, execution controls, default TZ setting, MCP toolset loading | ✅ 2026-04-12 |

## P2: Home Dashboard

| MEU | Slug | Matrix | Description | Status |
|-----|------|:------:|-------------|:------:|
| MEU-171 | `dashboard-service` | 35g | DashboardService (read-only aggregation) + 6 REST endpoints under `/api/v1/dashboard/` | ⬜ planned |
| MEU-172 | `gui-home-dashboard` | 35h | Home Dashboard GUI: startup route (`/`), 6 section cards with skeleton loading, dashboard settings (toggle/reorder), nav rail update (Home → 1st position) | ⬜ planned |

## P2.5: WebSocket Infrastructure

| MEU | Slug | Matrix | Description | Status |
|-----|------|:------:|-------------|:------:|
| MEU-174 | `websocket-infrastructure` | 49.7 | FastAPI `ConnectionManager` + `/ws` endpoint; Electron `WebSocketBridge` (main → renderer relay); event routing (`pnl.tick`, `trade.update`, `notification`). Foundation for real-time dashboard and tray icon badge. | ⬜ planned |

## Phase-Exit Criteria (Updated)

- Phase 6 (foundation): MEU-43..45 ✅ (shell + commands + window state) → Phase 6 features unblocked
- Phase 6 (features): MEU-46a, MEU-50, MEU-51 ✅ (MCP proxy, command palette, state persistence)

## P2.5b: Backend Services Wiring & Quality

| MEU | Slug | Matrix | Description | Status |
|-----|------|:------:|-------------|:------:|
| MEU-PW1 | `pipeline-runtime-wiring` | 49.4 | Expand `PipelineRunner.__init__` (6 new kwargs); create `DbWriteAdapter`; add `get_smtp_runtime_config()` to `EmailProviderService`; wire 7 runtime deps in `main.py` (`provider_adapter=None` until PW2); delete dead stubs (`StubMarketDataService`, `StubProviderConnectionService`); integration test verifying all wired deps | ✅ 2026-04-12 |
| MEU-PW2 | `fetch-step-integration` | 49.5 | Create `MarketDataProviderAdapter` + `MarketDataAdapterPort`; implement `FetchStep._check_cache` with TTL + market-hours extension; add entity_key computation + cache upsert after fetch; add `warnings` field to `FetchResult`; wire adapter/rate-limiter/cache-repo in `main.py` (PipelineRunner 8→9 kwargs); update PW1 contract tests; 5 integration tests | ✅ 2026-04-13 |
| MEU-PW6 | `url-builders` | 9B.4 | Registry-based URL builder dispatch: `YahooUrlBuilder`, `PolygonUrlBuilder`, `FinnhubUrlBuilder`, `GenericUrlBuilder`; `get_url_builder()` factory; `_resolve_tickers()` helper; 22 unit tests | ✅ 2026-04-19 |
| MEU-PW7 | `pipeline-cancellation` | 9B.5 | `PipelineStatus.CANCELLING` enum; `PipelineRunner._active_tasks` + `cancel_run()`; `SchedulingService.cancel_run()` delegation; `POST /runs/{run_id}/cancel` endpoint with UUID regex validation (422/404/200); 15 unit tests; OpenAPI spec updated | ✅ 2026-04-19 |

## P2.6: Service Daemon & Tray Icon (Phase 10)

| MEU | Slug | Matrix | Description | Status |
|-----|------|:------:|-------------|:------:|
| MEU-91 | `service-config-files` | 49a | Service config (WinSW, launchd, systemd) | ⬜ planned |
| MEU-92 | `service-manager` | 49b | ServiceManager class + IPC bridge | ⬜ planned |
| MEU-93 | `service-api` | 49c | Service REST endpoints (status, shutdown) | ⬜ planned |
| MEU-94 | `service-mcp` | 49d | Service MCP tools (status, restart, logs) | ⬜ planned |
| MEU-95 | `service-gui` | 49e | Service Manager GUI + installer hooks | ⬜ planned |
| MEU-95a | `tray-icon-renderer` | 49f | TrayIconRenderer: OffscreenCanvas → NativeImage, status dot (green/yellow/red/gray) + notification badge overlay, platform-aware sizing (16/24/32px), state machine | ⬜ planned |
| MEU-95b | `tray-icon-integration` | 49g | Wire renderer to ServiceManager health + WebSocket notification count; dynamic context menu; OS theme detection; click-to-show behavior | ⬜ planned |

## P4: Monetization (Phase 11)

| MEU | Slug | Matrix | Description | Status |
|-----|------|:------:|-------------|:------:|
| MEU-175 | `monetization-domain` | 11.1 | License entity, SubscriptionTier enum, UsageMeter entity | ⬜ planned |
| MEU-176 | `oauth-google` | 11.2 | Google OAuth PKCE + encrypted token storage, refresh timer | ⬜ planned |
| MEU-177 | `google-calendar-tasks` | 11.3 | Calendar/Tasks API for Plan reminders + Watchlist actions | ⬜ planned |
| MEU-178 | `license-enforcement` | 11.4 | Ed25519 JWT validation, offline grace (14d/30d), device binding | ⬜ planned |
| MEU-179 | `byok-ai-providers` | 11.5 | AI provider key CRUD (encrypted), periodic validation, usage tracking | ⬜ planned |
| MEU-180 | `monetization-api-gui` | 11.7 | Monetization REST routes (11 endpoints) + Subscription Settings GUI | ⬜ planned |
| MEU-181 | `usage-metering` | 11.6 | Usage counters, tier limits, approach-to-limit UX (green → yellow → red) | ⬜ planned |

## Research-Enhanced: Floating P&L Widget (Phase 6)

| MEU | Slug | Matrix | Description | Status |
|-----|------|:------:|-------------|:------:|
| MEU-173 | `floating-pnl-widget` | 6.A | Always-on-top BrowserWindow, consumes `pnl.tick` WebSocket events, draggable, transparency/click-through toggle. Depends on MEU-174 (WebSocket). | ⬜ planned |

## Research-Enhanced: Workspace Setup (Tier 2, after Phase 9 domain)

| MEU | Slug | Matrix | Description | Status |
|-----|------|:------:|-------------|:------:|
| MEU-165a | `setup-workspace-core` | 5.H1 | `zorivest_setup_workspace` tool: path confinement, atomic writes, `.scaffold-meta.json`, idempotency, core toolset registration | 🔲 planned |
| MEU-165b | `setup-workspace-templates` | 5.H2 | AGENTS.md, IDE shims, `.agent/` templates (docs, workflows, roles, rules, skills) | 🔲 planned |

## Phase 9: Scheduling & Pipeline (P0)

| MEU | Slug | Matrix | Description | Status |
|-----|------|:------:|-------------|:------:|
| MEU-77 | `scheduling-domain` | 36 | Scheduling domain models (Policy∕Schedule∕Step∕Condition) | ✅ approved |
| MEU-78 | `calendar-engine` | 37 | CalendarEngine (market-hours-aware scheduling) | ✅ approved |
| MEU-79 | `condition-engine` | 38 | ConditionEngine (market/data/time conditions) | ✅ approved |
| MEU-80 | `policy-validator` | 39 | PolicyValidator (8 validation rules) | ✅ approved |
| MEU-81 | `scheduling-models` | 40 | SQLAlchemy models (9 tables) | ✅ approved |
| MEU-82 | `scheduling-repos` | 41 | Repository implementations + audit triggers | ✅ approved |
| MEU-83 | `pipeline-runner` | 42 | PipelineRunner (sequential async executor) | ✅ approved |
| MEU-84 | `ref-resolver` | 43 | RefResolver + ConditionEvaluator | ✅ approved |
| MEU-85 | `fetch-step` | 44 | FetchStep + CriteriaResolver + HTTP cache + rate limiter | ✅ approved |
| MEU-86 | `transform-step` | 45 | TransformStep + Pandera validation gate + quality enforcement | ✅ approved |
| MEU-87 | `store-render-step` | 46 | StoreReportStep + RenderStep (ReportSpec DSL, SQL sandbox, Jinja2/Plotly/PDF) | ✅ approved |
| MEU-88 | `send-step` | 47 | SendStep + async email delivery (aiosmtplib, SHA-256 dedup, DeliveryRepository) | ✅ approved |
| MEU-89 | `scheduling-api-mcp` | 48 | Scheduling REST API (16 endpoints) + MCP tools (6+2); scheduler lifecycle | ✅ approved |
| MEU-90 | `scheduling-guardrails` | 49 | PipelineGuardrails (4 rate-limit/approval checks) + approval-reset on patch | ✅ approved |
| MEU-90a | `persistence-wiring` | 49.0 | Replace StubUnitOfWork with SqlAlchemyUnitOfWork; wire all 17 real repos into FastAPI lifespan; fix getattr/dict guardrails mismatch; Alembic bootstrap; remove repo-level stubs | ✅ 2026-03-24 |
| MEU-90b | `mode-gating-test-isolation` | 49.1 | Fix 8 flaky mode-gating tests: per-test `app.state` reset so lock/unlock doesn't leak across modules | ✅ 2026-03-24 |
| MEU-90c | `sqlcipher-native-deps` | 49.2 | Resolve sqlcipher3 availability on Windows; clear 15 skipped encryption tests | 🚫 closed — won't fix locally; CI covered by `crypto-tests` job (ADR-001 A+B, human decision) |
| MEU-90d | `rendering-deps` | 49.3 | Install + validate Playwright + kaleido rendering extras; clear 1 skipped RenderStep test | ✅ 2026-03-24 |
| MEU-73 | `gui-email-settings` | 35c | Email Provider Settings GUI — full stack (backend model/repo/service/route, frontend page/route/nav, 16 tests) | ✅ 2026-03-25 |
| MEU-71 | `account-api-completion` | 35a | Account API enrichment: `get_latest`/`list_for_account` on BalanceSnapshotRepo, `AccountService` portfolio total, enriched `AccountResponse` + balance history endpoint, FK enforcement (27 tests) | ✅ 2026-03-26 |
| MEU-71b | `calculator-accounts` | 81a | Calculator Account Integration: `useAccounts` hook, account dropdown with All Accounts default + auto-fill, manual override, zero-total support (12 tests) | ✅ 2026-03-26 |
| MEU-71a | `account-gui` | 35a.1 | Account Management GUI: AccountsHome dashboard (MRU cards, table, split layout), AccountDetailPanel (RHF+Zod CRUD), BalanceHistory (canvas sparkline), AccountReviewWizard (multi-step balance review), AccountContext, G11 event wiring (47 tests) | ✅ 2026-03-27 |
| MEU-BV1 | `boundary-validation-accounts` | 04b | Account schema hardening: `AccountType` enum, `Field(min_length=1)`, `extra="forbid"`, update invariant parity (6 tests) | ✅ 2026-04-05 |
| MEU-BV2 | `boundary-validation-trades` | 04a | Trade schema hardening: `TradeAction` enum, `Field(gt=0)` quantity, `Field(ge=0)` price, `Field(min_length=1)` instrument/exec_id, `extra="forbid"`, update invariant parity (11 tests) | ✅ 2026-04-05 |
| MEU-BV3 | `boundary-validation-plans` | 04a | Plan schema hardening: `TradeAction`/`ConvictionLevel`/`PlanStatus` enums, `Field(min_length=1)` ticker/strategy_name, `extra="forbid"`, update invariant parity, 3 write paths (12 tests) | ✅ 2026-04-05 |
| MEU-BV4 | `boundary-validation-market-data` | 08 §8.4 | Market data provider config hardening: `StrippedStr` on `api_key`/`api_secret`, `Field(ge=1)` on `rate_limit`/`timeout`, `extra="forbid"` (7 tests) | ✅ 2026-04-05 |
| MEU-BV5 | `boundary-validation-email` | 06f | Email settings hardening: `StrippedStr` on string fields (except password), `Literal` on `provider_preset` (6 presets) and `security` (STARTTLS/SSL), `Field(ge=1, le=65535)` on `port`, `extra="forbid"` (11 tests) | ✅ 2026-04-05 |
| MEU-BV6 | `boundary-validation-scheduling` | 09 §9.10 | Scheduling schema hardening: `extra="forbid"` on PolicyCreateRequest/RunTriggerRequest, `Query(min_length=1)` + strip-then-reject on PATCH cron_expression/timezone, `field_validator` non-empty policy_json (6 tests) | ✅ 2026-04-11 |
| MEU-BV7 | `boundary-validation-watchlists` | 04b §1 | Watchlist schema hardening: `StrippedStr` + `Field(min_length=1)` on name/ticker, `extra="forbid"` on 3 request models (7 tests) | ✅ 2026-04-11 |
| MEU-BV8 | `boundary-validation-settings` | 04d §1 | Settings schema hardening: empty-body guard on bulk PUT, `UpdateSettingRequest` with `extra="forbid"` + required value for single-key PUT (3 tests) | ✅ 2026-04-11 |
| MEU-TS1 | `pyright-test-annotations` | TS.A | Pyright Tier 1: fix generator fixture typing, Optional narrowing guards, mock protocol compliance, `__mro__` access across 8 test files (13 errors) — zero production code changes | ✅ 2026-04-06 |
| MEU-TS2 | `pyright-enum-literals` | TS.B | Pyright Tier 2: replace ~50 raw string literals (`"BOT"`, `"SLD"`) with enum values in test assertions — zero production code changes | ✅ 2026-04-11 |
| MEU-TS3 | `pyright-entity-factories` | TS.C | Pyright Tier 3: resolve ~121 entity factory `Column[T]`→`T` typing errors + 2 core service errors | ✅ 2026-04-11 |
| MEU-PW12 | `pipeline-dataflow-fix` | 49.4h | Pipeline data-flow chain fix: response extractor slug normalization, generic identity field mappings, `extra="forbid"` on all step Params, `PipelineStatus.WARNING` enum + output storage, per-step boundary validation in `policy_validator` (142 unit tests) | ✅ 2026-04-21 |
| MEU-PW13 | `pipeline-dataflow-e2e` | 49.5h | Pipeline E2E integration tests: Fetch→Transform→Send chain with Yahoo quote data, envelope extraction, field mapping, cache upserts, zero-record WARNING (7 integration tests) | ✅ 2026-04-21 |

## P2.5c: Pipeline Security Hardening

> Source: [09c](../../docs/build-plan/09c-pipeline-security-hardening.md), [09d](../../docs/build-plan/09d-pipeline-step-extensions.md), [09e](../../docs/build-plan/09e-template-database.md), [09f](../../docs/build-plan/09f-policy-emulator.md)
> Research source: [retail-trader-policy-use-cases.md](../../_inspiration/policy_pipeline_wiring-research/retail-trader-policy-use-cases.md)
> Prerequisite: P2.5b wiring complete (MEU-PW1→PW13 ✅)

| MEU | Slug | Matrix | Description | Status |
|-----|------|:------:|-------------|:------:|
| MEU-PH1 | `stepcontext-safety` | 49.16 | StepContext `safe_deepcopy` + `Secret` carrier class + depth/byte guards | ✅ done |
| MEU-PH2 | `sql-sandbox` | 49.17 | SQL sandbox: `set_authorizer` + `mode=ro` + AST allowlist + `progress_handler` + secrets scan + policy content IDs | ✅ done |
| MEU-PH3 | `send-fetch-guards` | 49.18 | SendStep confirmation gate + FetchStep MIME/fan-out validation | ✅ done |
| MEU-PH4 | `query-step` | 49.19 | QueryStep implementation (read-only SQL via sandbox) | ✅ 2026-04-25 |
| MEU-PH5 | `compose-step` | 49.20 | ComposeStep implementation (multi-source data merging) | ✅ 2026-04-25 |
| MEU-PH6 | `template-database` | 49.21 | EmailTemplateModel + HardenedSandbox + nh3 sanitization + template CRUD | ✅ 2026-04-25 |
| MEU-PH7 | `policy-vars-assertions` | 49.22 | PolicyDocument `variables` + assertion gates + step-count cap + schema v2 | ✅ 2026-04-25 |
| MEU-PH8 | `policy-emulator` | 49.23 | 4-phase emulator + output containment + session budget + error schema | ✅ 2026-04-26 |
| MEU-PH9 | `emulator-mcp-tools` | 49.24 | 11 new MCP tools: emulator, schema discovery, template CRUD, provider discovery | ✅ 2026-04-26 |
| MEU-PH10 | `default-template` | 49.25 | Pre-loaded Morning Check-In template | ✅ 2026-04-26 |

## P2.5d: Approval Security & Validation Hardening

> Source: [09g](../../docs/build-plan/09g-approval-security.md), [09f ext](../../docs/build-plan/09f-policy-emulator.md)
> Prerequisite: P2.5c complete (MEU-PH1→PH10 ✅)
> Resolves: [MCP-APPROVBYPASS], [MCP-POLICYGAP], [EMULATOR-VALIDATE]

| MEU | Slug | Matrix | Description | Status |
|-----|------|:------:|-------------|:------:|
| MEU-PH11 | `approval-csrf-token` | 49.26 | CSRF challenge token: Electron IPC → API middleware on `POST /approve`; single-use, 5-min TTL, policy-scoped | ✅ 2026-04-29 |
| MEU-PH12 | `mcp-scheduling-gap-fill` | 49.27 | 3 MCP tools: `delete_policy` (destructive + confirm), `update_policy`, `get_email_config` | ✅ 2026-04-29 |
| MEU-PH13 | `emulator-validate-hardening` | 49.28 | VALIDATE improvements: EXPLAIN SQL, SMTP check, step output wiring validation | ✅ 2026-04-29 |

## P2.5e: MCP Tool Remediation

> Source: [MCP Tool Audit Report](../../.agent/context/MCP/mcp-tool-audit-report.md)
> Prerequisite: P2.5c complete (MEU-PH1→PH10 ✅); parallel with P2.5d
> Resolves: [MCP-TOOLAUDIT]

| MEU | Slug | Matrix | Description | Status |
|-----|------|:------:|-------------|:------:|
| MEU-TA1 | `mcp-delete-trade-fix` | 5.J | Fix `delete_trade` returning 500 on valid exec_id — debug API trade deletion endpoint, fix error handling, add regression test · [MCP-TOOLAUDIT] High | ✅ done |
| MEU-TA2 | `mcp-settings-serialization-fix` | 5.K | Fix `update_settings` returning 422 with `[object Object]` — TypeScript serialization bug · [MCP-TOOLAUDIT] Medium | ✅ done |
| MEU-TA3 | `mcp-unimplemented-tool-guard` | 5.L | Guard 6 unimplemented MCP tools to return "501 Not Implemented" instead of 404/500 · [MCP-TOOLAUDIT] Medium | ✅ done |
| MEU-TA4 | `mcp-trade-plan-lifecycle` | 5.M | Add `list_trade_plans` + `delete_trade_plan` MCP tools; fix `create_trade_plan` 409 · [MCP-TOOLAUDIT] Medium | ✅ done |

## Other New MEUs (cross-phase)

| MEU | Slug | Matrix | Description | Status |
|-----|------|:------:|-------------|:------:|
| MEU-72b | `gui-email-templates` | 35b.2 | Email Templates tab in SchedulingLayout (CRUD, preview, default protection). Depends on MEU-72. [06k](../../docs/build-plan/06k-gui-email-templates.md) | ✅ done |
| MEU-PW14 | `pipeline-markdown-migration` | 49.29 | PDF removal, Markdown rendering, Playwright dep cleanup. [09h](../../docs/build-plan/09h-pipeline-markdown-migration.md) | ✅ done |

## P2.5f: MCP Tool Consolidation

> Source: [mcp-consolidation-proposal-v3.md](../../.agent/context/MCP/mcp-consolidation-proposal-v3.md)
> Prerequisite: P2.5e complete (MEU-TA1→TA4 ✅)
> Resolves: [MCP-TOOLPROLIFERATION]

| MEU | Slug | Matrix | Description | Status |
|-----|------|:------:|-------------|:------:|
| MC0 | `mcp-consolidation-docs` | 5.N | Documentation sync: BUILD_PLAN.md, meu-registry.md, known-issues.md, 05-mcp-server.md §5.11, mcp-tool-index.md, build-priority-matrix.md | ✅ 2026-04-29 |
| MC1 | `compound-router-system` | 5.O | CompoundToolRouter + `zorivest_system` (9 actions), remove 9 old registrations. Tools/list: 86→77 | ✅ 2026-04-29 |
| MC2 | `compound-trade-analytics` | 5.P | `zorivest_trade` (6), `zorivest_report` (2), `zorivest_analytics` (13 incl. position_size). Tools/list: 77→59 | ✅ 2026-04-29 |
| MC3 | `compound-data-vertical` | 5.Q | `zorivest_account` (9), `zorivest_market` (7), `zorivest_watchlist` (5), `zorivest_import` (7 incl. 3×501), `zorivest_tax` (4 stubs). Tools/list: 59→32 | ✅ 2026-04-29 |
| MC4 | `compound-ops-restructure` | 5.R | `zorivest_plan` (3), `zorivest_policy` (9), `zorivest_template` (6), `zorivest_db` (5); seed.ts 10→4 toolsets; CI gate tool_count ≤ 13. Tools/list: 32→13 | ✅ 2026-04-29 |
| MC5 | `consolidation-finalize` | 5.S | Baseline snapshot (85→13), server instructions, anti-placeholder, MCP audit, archive [MCP-TOOLPROLIFERATION] | ✅ 2026-04-29 |

## P2.5g: MCP Auth Infrastructure

> Source: [known-issues.md](known-issues.md) [MCP-AUTHRACE]
> Prerequisite: P2.5f complete (MC0→MC5 ✅)
> Resolves: [MCP-AUTHRACE]

| MEU | Slug | Matrix | Description | Status |
|-----|------|:------:|-------------|:------:|
| MEU-PH14 | `token-refresh-manager` | 5.T | `TokenRefreshManager` singleton with promise coalescing, 30s proactive expiry, async `getAuthHeaders()`. Removes module-level `authState`/`bootstrapAuth()`. 10 FIC tests. | ✅ 2026-04-30 |

## Technical Debt Remediation

| MEU | Slug | Matrix | Description | Status |
|-----|------|:------:|-------------|:------:|
| MEU-TD1 | `mcp-discoverability-audit` | TD.1 | M7 enforcement: audit all 13 compound tool descriptions for workflow context, prerequisites, return shapes, error conditions. Expand server instructions. Add M7 enforcement gate to emerging-standards. | ✅ 2026-04-30 |
