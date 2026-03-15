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
| MEU-37 | `mcp-accounts` | 13 | Account MCP tools | ✅ approved |
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
| MEU-59 | `market-provider-registry` | 24 | Static provider registry (12 providers) | ✅ approved |
| MEU-62 | `market-rate-limiter` | 25 | Token-bucket rate limiter + log redaction | ✅ approved |
| MEU-60 | `market-connection-svc` | 26 | ProviderConnectionService + persistence | ✅ approved |
| MEU-61 | `market-data-service` | 27 | MarketDataService + 10 normalizers | ✅ approved |
| MEU-63 | `market-data-api` | 28 | Market data REST API (8 routes) | ✅ approved |
| MEU-64 | `market-data-mcp` | 29 | Market data MCP tools (7 tools) | ✅ approved |

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

## Phase-Exit Criteria (Updated)

- Phase 6 (foundation): MEU-43..45 ✅ (shell + commands + window state) → Phase 6 features unblocked


