# Build Priority Matrix

> Part of [Zorivest Build Plan](../BUILD_PLAN.md) — The 92-item build order across all priority levels.

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
| **5** | Commands & DTOs | ✅ Yes | Nothing | Pydantic validation |
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
| **11** | Image processing (validate, thumbnail) | ✅ Yes | Pillow | Thumbnail generation |
| **12** | FastAPI routes | ✅ Yes | Services | `TestClient` |
| **13** | TypeScript MCP tools (trade, account, calculator, image) | ✅ Yes | REST API | `vitest` with mocked `fetch()` |
| **14** | MCP + REST integration test | ✅ Yes | Both live | TS MCP calling live Python API |
| **15** | Electron + React UI shell ([06a](06a-gui-shell.md)) | ✅ Yes | REST API | React Testing Library + Playwright |
| **15a** | Settings REST endpoints (`GET`/`PUT /settings`) | ✅ Yes | Services | `TestClient` round-trip |
| **15b** | Settings MCP tools (`get_settings`, `update_settings`) | ✅ Yes | REST API | `vitest` with mocked `fetch()` |
| **15c** | Command registry (`commandRegistry.ts`) ([06a](06a-gui-shell.md)) | ✅ Yes | Nothing | Vitest: all entries have unique ids, valid actions |
| **15d** | Window state persistence (`electron-store`) ([06a](06a-gui-shell.md)) | Manual | Electron | Launch → move → close → relaunch → verify position |
| **15e** | MCP Guard: `McpGuardModel` + REST endpoints + MCP middleware + GUI | ✅ Yes | REST API, MCP tools | Circuit breaker, panic button, per-minute/hour rate limits ([02](02-infrastructure.md), [04](04-rest-api.md), [05](05-mcp-server.md), [06f](06f-gui-settings.md)) |
| **16** | React pages — Trades ([06b](06b-gui-trades.md)), Plans ([06c](06c-gui-planning.md)) | Manual | API hooks | Visual verification |
| **16a** | Notification system ([06a](06a-gui-shell.md)) | Manual | Settings API | Visual: toast categories, suppression toggle |
| **16b** | Command palette ([06a](06a-gui-shell.md), Ctrl+K) | Manual | Registry | Visual: search, navigate, select |
| **16c** | UI state persistence ([06a](06a-gui-shell.md)) | Manual | Settings API | Change → restart → verify restored |

> **Note**: Items 13 and 15 cover **core** MCP tools and GUI shell only. Market-data MCP tools and the Market Data Settings page depend on Phase 8 (items 21–30 in P1.5) and must not be started until P1.5 is reached.

> **Release gate**: Item 15e (MCP Guard) must pass before any MCP-enabled release. Do not ship MCP tools without abuse controls.

---

## P1 — Build Soon (Trade Reviews + Multi-Account)

| Order | What | Tests First? | Notes |
|-------|------|-------------|-------|
| **17** | TradeReport entity + service | ✅ Yes | Post-trade journaling with ratings, tags, images |
| **18** | TradeReport MCP tools + API routes | ✅ Yes | `create_report`, `get_report_for_trade` |
| **19** | Multi-account UI (account type badges, filtering) | ✅ Yes | Filter trades by account type |
| **20** | Report GUI panel ([06b](06b-gui-trades.md): ratings, tags, lessons) | Manual | Attached to trade detail view |

---

## P1.5 — Market Data Aggregation (Phase 8)

> **Source**: [`_inspiration/_market_tools_api-architecture.md`](../../_inspiration/_market_tools_api-architecture.md). See [Phase 8](08-market-data.md) for full spec.

| Order | What | Tests First? | Notes |
|-------|------|-------------|-------|
| **21** | `MarketDataProvider` entity + `AuthMethod` enum | ✅ Yes | 9 provider configs, 4 auth methods |
| **22** | Normalized response DTOs (`MarketQuote`, `MarketNewsItem`, etc.) | ✅ Yes | Pydantic models for cross-provider normalization |
| **23** | `MarketProviderSettingModel` + encrypted key storage | ✅ Yes | SQLAlchemy table, Fernet encrypt/decrypt |
| **24** | Provider registry (singleton config map) | ✅ Yes | All 9 providers with auth templates, test endpoints |
| **25** | `ProviderConnectionService` (test, configure, list) | ✅ Yes | Connection testing framework with response validation |
| **26** | `MarketDataService` (quote, news, search, SEC filings) | ✅ Yes | Provider fallback chain, response normalization |
| **27** | Rate limiter (token-bucket per provider) + log redaction | ✅ Yes | Async token-bucket, API key masking |
| **28** | Market data REST API endpoints (8 routes) | ✅ Yes | FastAPI under `/api/v1/market-data/` |
| **29** | Market data MCP tools (6 tools) | ✅ Yes | TypeScript via `registerMarketDataTools` |
| **30** | Market Data Providers GUI settings page ([06f](06f-gui-settings.md)) | Manual | Provider list, connection testing, API key management |

---

## P2 — Build Next (Planning + Watchlists)

| Order | What | Tests First? | Notes |
|-------|------|-------------|-------|
| **31** | TradePlan entity + service | ✅ Yes | Conviction, strategy, entry/exit conditions |
| **32** | TradePlan ↔ Trade linking (plan → execution) | ✅ Yes | `followed_plan` in TradeReport |
| **33** | Watchlist entity + service | ✅ Yes | Named lists of tickers |
| **34** | TradePlan + Watchlist MCP tools | ✅ Yes | AI agent can create/query plans |
| **35** | Planning GUI ([06c](06c-gui-planning.md): plan cards, watchlists) | Manual | List+detail layout, conviction indicators |
| **35a** | Account Management GUI ([06d](06d-gui-accounts.md)) | Manual | Account CRUD, Review wizard, balance history |
| **35b** | Scheduling GUI ([06e](06e-gui-scheduling.md)) | Manual | Policy editor, cron preview, pipeline run history |
| **35c** | Email Provider Settings GUI ([06f](06f-gui-settings.md)) | Manual | SMTP config, preset auto-fill, test connection |
| **35d** | Backup & Restore Settings GUI ([06f](06f-gui-settings.md)) | Manual | Manual backup, restore, verify, auto-backup config |
| **35e** | Config Export/Import GUI ([06f](06f-gui-settings.md)) | Manual | JSON export download, import with preview diff |
| **35f** | Reset to Default on settings pages ([06f](06f-gui-settings.md)) | Manual | Source indicator, per-setting reset, bulk reset |

---

## P3 — Build Later (Tax Estimation)

> **Research phase complete.** See [Domain Model Reference](domain-model-reference.md) for full feature spec (Modules A–G, 35 features).
> Build in 5 sub-phases so each sub-phase is independently testable.

### Phase 3A — Core Tax Engine (Module A)

| Order | What | Tests First? | Notes |
|-------|------|-------------|-------|
| **36** | `TaxLot` entity + `CostBasisMethod` enum | ✅ Yes | 8 cost basis methods (FIFO → Max ST Loss) |
| **37** | `TaxProfile` entity + `FilingStatus` enum | ✅ Yes | Settings: bracket, state, filing status, section elections |
| **38** | Tax lot tracking: open/close lots, holding period | ✅ Yes | Every buy → TaxLot. Every sell → close lots via selected method |
| **39** | ST vs LT classification + gains calculator | ✅ Yes | < 366 days = ST @ ordinary rate, ≥ 366 = LT @ 0/15/20% |
| **40** | Capital loss carryforward + account exclusion | ✅ Yes | $3K/year cap, IRA/401K skip, prior-year rollover |
| **41** | Options assignment/exercise cost basis pairing | ✅ Yes | Put assignment → reduce basis, call exercise → add proceeds |
| **42** | YTD P&L by symbol | ✅ Yes | Realized gains per ticker, ST vs LT breakdown |

### Phase 3B — Wash Sale Engine (Module B)

| Order | What | Tests First? | Notes |
|-------|------|-------------|-------|
| **43** | `WashSaleChain` entity + basic 30-day detection | ✅ Yes | Loss deferral, basis adjustment on replacement lot |
| **44** | Wash sale chain tracking (deferred loss rolling) | ✅ Yes | Chain events: disallowed → absorbed → released |
| **45** | Cross-account wash sale aggregation | ✅ Yes | Check taxable + IRA + spouse accounts. IRA = permanent loss |
| **46** | Options-to-stock wash sale matching (configurable) | ✅ Yes | Method 1 (Conservative) vs Method 2 (Aggressive) toggle |
| **47** | DRIP wash sale detection | ✅ Yes | Flag when dividend reinvestment conflicts with harvested loss |
| **48** | Auto-rebalance + spousal cross-wash warnings | ✅ Yes | Warn on DCA/rebalance conflicts; optional spouse accounts |
| **49** | Wash sale prevention alerts (proactive) | ✅ Yes | Pre-trade: "Wait N days" or "This will trigger wash sale" |

### Phase 3C — Tax Optimization Tools (Module C)

| Order | What | Tests First? | Notes |
|-------|------|-------------|-------|
| **50** | Pre-trade "what-if" tax simulator | ✅ Yes | MCP: `simulate_tax_impact`. Show tax before executing |
| **51** | Tax-loss harvesting scanner | ✅ Yes | MCP: `harvest_losses`. Rank by amount, filter wash conflicts |
| **52** | Tax-smart replacement suggestions | ✅ Yes | Correlated non-identical securities (VOO→IVV, QQQ→QQQM) |
| **53** | Lot matcher / close specific lots UI | ✅ Yes | MCP: `get_tax_lots`. Show open lots with basis + days to LT |
| **54** | Post-trade lot reassignment window | ✅ Yes | Change method within T+1 settlement. Undo for tax mistakes |
| **55** | ST vs LT tax rate dollar comparison | ✅ Yes | "Wait 12 days → save $1,390." Show dollars at user's bracket |

### Phase 3D — Quarterly Payments & Tax Brackets (Modules D+E)

| Order | What | Tests First? | Notes |
|-------|------|-------------|-------|
| **56** | `QuarterlyEstimate` entity + safe harbor calc | ✅ Yes | 90% current OR 100%/110% prior year. Recommend lower |
| **57** | Annualized income method (Form 2210 Sched AI) | ✅ Yes | Proportional quarterly payments for fluctuating income |
| **58** | Quarterly due date tracker + underpayment penalty | ✅ Yes | MCP: `quarterly_estimate`. 4 deadlines + penalty accrual |
| **59** | Marginal tax rate calculator (federal + state) | ✅ Yes | Effective + marginal rate from AGI + filing status |
| **60** | NIIT (3.8% surtax) threshold alert | ✅ Yes | Flag when MAGI approaches $200K/$250K threshold |

### Phase 3E — Reports, Dashboard & MCP/API/GUI (Module F+G)

| Order | What | Tests First? | Notes |
|-------|------|-------------|-------|
| **61** | Tax REST API endpoints (FastAPI) | ✅ Yes | `/tax/estimate`, `/tax/wash-sales`, `/tax/simulate`, `/tax/lots`, `/tax/quarterly`, `/tax/harvest`, `/tax/ytd-summary` |
| **62** | Tax MCP tool registration (`registerTaxTools`) | ✅ Yes | 7 tools: `estimate_tax`, `find_wash_sales`, `simulate_tax_impact`, `get_tax_lots`, `quarterly_estimate`, `harvest_losses`, `get_ytd_tax_summary` |
| **63** | Year-end tax position summary | ✅ Yes | MCP: `get_ytd_tax_summary`. Aggregate dashboard |
| **64** | Deferred loss carryover report | ✅ Yes | Real P&L vs reported P&L, trapped losses in chains |
| **65** | Tax alpha savings summary | ✅ Yes | YTD savings from lot optimization + loss harvesting |
| **66** | Error check / transaction audit | ✅ Yes | Scan for missing basis, dupes, impossible prices |
| **67** | Tax estimator GUI (React) — [06g-gui-tax.md](06g-gui-tax.md) | Manual | Dashboard, lot viewer, wash sales, what-if, harvesting, quarterly tracker |
| **67a** | Position calculator GUI (React) — [06h-gui-calculator.md](06h-gui-calculator.md) | Manual | Calculator modal, multi-scenario comparison, calculation history |
| **68** | Section 475 / 1256 / Forex toggles (conditional) | ✅ Yes | Mark-to-Market, 60/40 futures, forex worksheet |

---

**The first lines of code you write are `test_calculator.py` and `test_logging_config.py`. Phase 1 and Phase 1A start in parallel — both have zero dependencies.**

