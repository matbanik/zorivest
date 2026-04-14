# Zorivest — Build Plan & Test-Driven Development Guide

> **Hub file** — This document is the index for the complete build plan. Each phase and reference section lives in its own file under [`build-plan/`](build-plan/).

---

## Architecture Dependency Rule

The build order follows the **dependency rule**: inner layers first, outer layers last. Each layer is fully testable before the next one starts.

```
Domain → Infrastructure → Services → REST API → MCP Server → GUI → Distribution
  (1)        (2)            (3)         (4)         (5)        (6)       (7)
                                                    ↑                    ↑
                                              Market Data(8)    Scheduling(9)
                                                                Service Daemon(10)
```

---

## Build Phases

| Phase | Name | File | Depends On | Key Deliverables |
|-------|------|------|------------|-----------------|
| 0 | [Build Order Overview](build-plan/00-overview.md) | `00-overview.md` | — | Dependency diagram, golden rules |
| 1 | [Domain Layer](build-plan/01-domain-layer.md) | `01-domain-layer.md` | Nothing | Entities, calculator, ports, enums |
| 1A | [Logging](build-plan/01a-logging.md) | `01a-logging.md` | Nothing | QueueHandler/Listener, JSONL, per-feature routing |
| 2 | [Infrastructure](build-plan/02-infrastructure.md) | `02-infrastructure.md` | Phase 1 | SQLCipher DB, SQLAlchemy repos, UoW |
| 2A | [Backup/Restore](build-plan/02a-backup-restore.md) | `02a-backup-restore.md` | Phase 2 | Encrypted backup, settings resolver |
| 3 | [Service Layer](build-plan/03-service-layer.md) | `03-service-layer.md` | Phases 1–2 | Trade/Image/Account services |
| 4 | [REST API](build-plan/04-rest-api.md) | `04-rest-api.md` | Phase 3 | FastAPI routes, TestClient tests |
| 5 | [MCP Server](build-plan/05-mcp-server.md) | `05-mcp-server.md` | Phase 4, 8 | TypeScript MCP tools, Vitest |
| 6 | [GUI](build-plan/06-gui.md) | `06-gui.md` | Phase 4, 8 | Electron + React desktop app |
| 7 | [Distribution](build-plan/07-distribution.md) | `07-distribution.md` | All | Electron Builder, PyPI, npm |
| 8 | [Market Data](build-plan/08-market-data.md) | `08-market-data.md` | Phases 2–4 | 14 market data providers (12 API-key + 2 free via MEU-65), API key encryption, MCP tools |
| 9 | [Scheduling & Pipelines](build-plan/09-scheduling.md) | `09-scheduling.md` | Phases 2–5, 8 | Policy engine, pipeline runner, APScheduler |
| 10 | [Service Daemon](build-plan/10-service-daemon.md) | `10-service-daemon.md` | Phases 4, 7, 9 | Cross-platform OS service, ServiceManager |

---

## Reference Documents

| Document | File | Purpose |
|----------|------|---------|
| [Domain Model Reference](build-plan/domain-model-reference.md) | `domain-model-reference.md` | Complete entity map, relationships, enum definitions |
| [Testing Strategy](build-plan/testing-strategy.md) | `testing-strategy.md` | MCP testing approaches, `conftest.py`, test configuration |
| [Image Architecture](build-plan/image-architecture.md) | `image-architecture.md` | BLOB vs filesystem, processing pipeline, validation |
| [Dependency Manifest](build-plan/dependency-manifest.md) | `dependency-manifest.md` | Install order by phase, version requirements |
| [Build Priority Matrix](build-plan/build-priority-matrix.md) | `build-priority-matrix.md` | P0–P3 tables with P1.5 market data, complete 68-item build order |
| [Market Data API Reference](../_inspiration/_market_tools_api-architecture.md) | `_inspiration/` | Source patterns for 12-provider connectivity |

---

## Phase Status Tracker

| Phase | Status | Last Updated |
|-------|--------|--------------|
| 1 — Domain Layer | ✅ Completed | 2026-03-07 |
| 1A — Logging | ✅ Completed | 2026-03-07 |
| 2 — Infrastructure | ✅ Completed | 2026-03-08 |
| 2A — Backup/Restore | ✅ Completed | 2026-03-08 |
| 3 — Service Layer | ✅ Completed | 2026-03-08 |
| 4 — REST API | ✅ Completed | 2026-03-09 |
| 5 — MCP Server | ✅ Completed | 2026-03-10 |
| 6 — GUI | 🟡 In Progress (P0 complete, P2 items remain) | 2026-03-25 |
| 7 — Distribution | ⚪ Not Started | — |
| 8 — Market Data | ✅ Completed | 2026-03-23 |
| 9 — Scheduling | ✅ Completed (P2.5a integration done) | 2026-03-24 |
| 10 — Service Daemon | ⚪ Not Started | — |

---

## Golden Rules

1. **At every phase**, you should be able to run `pytest` and have all tests pass before moving to the next phase.
2. **Inner layers know nothing about outer layers.** Domain never imports from infrastructure.
3. **Write tests FIRST** — the test file defines the interface before the implementation exists.
4. **Every entity gets a test.** No "it's just a dataclass" exceptions.
5. **Commit after each green test run.** Small, atomic commits.

---

## Complete MEU Registry

> Every build-priority-matrix item mapped to a Manageable Execution Unit.
> Links point to the build-plan spec file that defines each item.
> Status reflects the [execution plans](execution/plans/) and [MEU registry](file:///p:/zorivest/.agent/context/meu-registry.md).

### Status Legend

| Icon | Meaning |
|------|---------|
| ⬜ | pending — not started |
| ⏸ | deferred — dependencies met but intentionally postponed |
| 🔵 | in_progress — Opus implementing |
| 🟡 | ready_for_review — awaiting Codex validation |
| 🔴 | changes_required — Codex found issues |
| ✅ | approved — both agents satisfied |
| 🚫 | closed — won't fix (human decision, ADR documented) |

---

### Phase 1: Domain Layer — P0

> Source: [01-domain-layer.md](build-plan/01-domain-layer.md) | Execution plan: [calculator](execution/plans/2026-03-06-calculator-implementation/), [enums](execution/plans/2026-03-07-enums/), [domain-entities-ports](execution/plans/2026-03-07-domain-entities-ports/), [commands-events-analytics](execution/plans/2026-03-07-commands-events-analytics/), [portfolio-display-review](execution/plans/2026-03-07-portfolio-display-review/)

| MEU | Slug | Matrix Item | Build Plan Ref | Description | Status |
|-----|------|:-----------:|----------------|-------------|:------:|
| MEU-1 | `calculator` | 1 | [01 §1.3](build-plan/01-domain-layer.md) | PositionSizeCalculator + PositionSizeResult | ✅ |
| MEU-2 | `enums` | 2 | [01 §1.2](build-plan/01-domain-layer.md) | All StrEnum definitions (14 enums) | ✅ |
| MEU-3 | `entities` | 3 | [01 §1.4](build-plan/01-domain-layer.md) | Trade, Account, BalanceSnapshot, ImageAttachment | ✅ |
| MEU-4 | `value-objects` | 3 | [01 §1.2](build-plan/01-domain-layer.md) | Money, PositionSize, Ticker, Conviction, ImageData | ✅ |
| MEU-5 | `ports` | 4 | [01 §1.5](build-plan/01-domain-layer.md) | Protocol interfaces (TradeRepo, ImageRepo, UoW, BrokerPort) | ✅ |
| MEU-6 | `commands-dtos` | 5 | [01 §1.1](build-plan/01-domain-layer.md) | Commands (CreateTrade, AttachImage) + Queries + DTOs | ✅ |
| MEU-7 | `events` | 5 | [01 §1.2](build-plan/01-domain-layer.md) | Domain events (TradeCreated, BalanceUpdated, etc.) | ✅ |
| MEU-8 | `analytics` | 5 | [01 §1.2](build-plan/01-domain-layer.md) | Pure analytics functions (expectancy, SQN + result types) | ✅ |
| MEU-9 | `portfolio-balance` | 3a | [matrix 3a](build-plan/build-priority-matrix.md) | Pure fn: sum latest balances per account | ✅ |
| MEU-10 | `display-mode` | 3b | [matrix 3b](build-plan/build-priority-matrix.md) | Display mode service ($, %, mask fns) | ✅ |
| MEU-11 | `account-review` | 3c | [matrix 3c](build-plan/build-priority-matrix.md) | Account Review workflow (guided balance update) | ✅ |

### Phase 1A: Logging Infrastructure — P0 (Parallel)

> Source: [01a-logging.md](build-plan/01a-logging.md)

| MEU | Slug | Matrix Item | Build Plan Ref | Description | Status |
|-----|------|:-----------:|----------------|-------------|:------:|
| MEU-1A | `logging-manager` | 1A | [01a §1–3](build-plan/01a-logging.md) | LoggingManager, QueueHandler/Listener, JSONL format | ✅ |
| MEU-2A | `logging-filters` | 1A | [01a §4](build-plan/01a-logging.md) | FeatureFilter, CatchallFilter + JsonFormatter | ✅ |
| MEU-3A | `logging-redaction` | 1A | [01a §4](build-plan/01a-logging.md) | RedactionFilter (API key masking, PII redaction) | ✅ |

### Phase 2: Infrastructure — P0

> Source: [02-infrastructure.md](build-plan/02-infrastructure.md)

| MEU | Slug | Matrix Item | Build Plan Ref | Description | Status |
|-----|------|:-----------:|----------------|-------------|:------:|
| MEU-12 | `service-layer` | 6 | [03 §3.1](build-plan/03-service-layer.md) | Core services (Trade, Account, Image, System) + domain exceptions + trade fingerprint | ✅ |
| MEU-13 | `sqlalchemy-models` | 7 | [02 §2.1](build-plan/02-infrastructure.md) | All 21 SQLAlchemy ORM models | ✅ |
| MEU-14 | `repositories` | 8 | [02 §2.2](build-plan/02-infrastructure.md) | Repository implementations (SQLAlchemy) | ✅ |
| MEU-15 | `unit-of-work` | 9 | [02 §2.2](build-plan/02-infrastructure.md) | Unit of Work pattern | ✅ |
| MEU-16 | `sqlcipher` | 10 | [02 §2.3](build-plan/02-infrastructure.md) | SQLCipher encrypted connection + Argon2 KDF | ✅ |

### Phase 2A: Backup & Restore — P0

> Source: [02a-backup-restore.md](build-plan/02a-backup-restore.md)

| MEU | Slug | Matrix Item | Build Plan Ref | Description | Status |
|-----|------|:-----------:|----------------|-------------|:------:|
| MEU-17 | `app-defaults` | 10a | [02a §2A.1](build-plan/02a-backup-restore.md) | AppDefaultModel + seeding migration | ✅ |
| MEU-18 | `settings-resolver` | 10b | [02a §2A.2](build-plan/02a-backup-restore.md) | SettingsRegistry, Resolver, Validator, Cache | ✅ |
| MEU-19 | `backup-manager` | 10c | [02a §2A.3](build-plan/02a-backup-restore.md) | BackupManager (auto backup + GFS rotation) | ✅ |
| MEU-20 | `backup-recovery` | 10d | [02a §2A.4](build-plan/02a-backup-restore.md) | BackupRecoveryManager (restore + repair) | ✅ |
| MEU-21 | `config-export` | 10e | [02a §2A.5](build-plan/02a-backup-restore.md) | ConfigExportService (JSON export/import) | ✅ |

### Phase 3: Service Layer — P0

> Source: [03-service-layer.md](build-plan/03-service-layer.md)

| MEU | Slug | Matrix Item | Build Plan Ref | Description | Status |
|-----|------|:-----------:|----------------|-------------|:------:|
| MEU-22 | `image-processing` | 11 | [image-architecture](build-plan/image-architecture.md) | Image validation, WebP conversion, thumbnails | ✅ |

### Phase 4: REST API — P0

> Source: [04-rest-api.md](build-plan/04-rest-api.md)

| MEU | Slug | Matrix Item | Build Plan Ref | Description | Status |
|-----|------|:-----------:|----------------|-------------|:------:|
| MEU-23 | `fastapi-routes` | 12 | [04 §all](build-plan/04-rest-api.md) | FastAPI app factory + core routes (health, trades, accounts, settings, analytics) | ✅ |
| MEU-24 | `api-trades` | 12 | [04a](build-plan/04a-api-trades.md) | Trade CRUD REST endpoints | ✅ |
| MEU-25 | `api-accounts` | 12 | [04b](build-plan/04b-api-accounts.md) | Account REST endpoints | ✅ |
| MEU-26 | `api-auth` | 12 | [04c](build-plan/04c-api-auth.md) | Auth REST endpoints (route surface + error modes; crypto stubs) | ✅ |
| MEU-27 | `api-settings` | 15a | [04d](build-plan/04d-api-settings.md) | Settings GET/PUT REST endpoints | ✅ |
| MEU-28 | `api-analytics` | 12 | [04e](build-plan/04e-api-analytics.md) | Analytics REST endpoints | ✅ |
| MEU-29 | `api-tax` | 12 | [04f](build-plan/04f-api-tax.md) | Tax REST endpoints | ✅ |
| MEU-30 | `api-system` | 12 | [04g](build-plan/04g-api-system.md) | System REST endpoints | ✅ |

### Phase 5: MCP Server — P0

> Source: [05-mcp-server.md](build-plan/05-mcp-server.md)

| MEU | Slug | Matrix Item | Build Plan Ref | Description | Status |
|-----|------|:-----------:|----------------|-------------|:------:|
| MEU-31 | `mcp-core-tools` | 13 | [05 §core](build-plan/05-mcp-server.md) | TypeScript MCP tools (trade, account, calculator, image, discovery) | ✅ |
| MEU-32 | `mcp-integration-test` | 14 | [05](build-plan/05-mcp-server.md) | MCP + REST integration test (TS calling live Python API) | ✅ |
| MEU-33 | `mcp-settings` | 15b | [05a](build-plan/05a-mcp-zorivest-settings.md) | Settings MCP tools (get_settings, update_settings) | ✅ |
| MEU-34 | `mcp-diagnostics` | 15f | [05b](build-plan/05b-mcp-zorivest-diagnostics.md) | zorivest_diagnose MCP tool | ✅ |
| MEU-35 | `mcp-trade-analytics` | 13 | [05c](build-plan/05c-mcp-trade-analytics.md) | Trade analytics MCP tools | ✅ |
| MEU-36 | `mcp-trade-planning` | 13 | [05d](build-plan/05d-mcp-trade-planning.md) | Trade planning MCP tools | ✅ |
| MEU-37 | `mcp-accounts` | 13 | [05f](build-plan/05f-mcp-accounts.md) | Account CRUD MCP tools (8 new: list, get, create, update, delete, archive, reassign_trades, record_balance) + **account-trade integrity**: System Reassignment Account (seeded, undeletable `SYSTEM_DEFAULT`), `is_archived` soft-delete, `is_system` guard, separate action endpoints (`DELETE` block-if-trades, `POST :archive` soft-delete, `POST :reassign-trades` migrate+hard-delete), computed metrics (`trade_count`, `round_trip_count`, `win_rate`, `total_realized_pnl`), `delete_account`/`reassign_trades` registered as destructive (confirmation required) | ✅ |
| MEU-38 | `mcp-guard` | 15e | [05 §guard](build-plan/05-mcp-server.md) | McpGuardModel + REST + middleware + GUI | ✅ |
| MEU-39 | `mcp-perf-metrics` | 15g | [05 §5.9](build-plan/05-mcp-server.md) | Per-tool performance metrics middleware | ✅ |
| MEU-40 | `mcp-launch-gui` | 15h | [05 §5.10](build-plan/05-mcp-server.md) | zorivest_launch_gui MCP tool | ✅ |
| MEU-41 | `mcp-discovery` | 15j | [05j](build-plan/05j-mcp-discovery.md) | Discovery meta-tools (list, describe, enable, confirm) | ✅ |
| MEU-42 | `toolset-registry` | 15k | [05 §5.11–5.14](build-plan/05-mcp-server.md) | ToolsetRegistry + adaptive client detection | ✅ |

### Phase 6: GUI — P0

> Source: [06-gui.md](build-plan/06-gui.md)

| MEU | Slug | Matrix Item | Build Plan Ref | Description | Status |
|-----|------|:-----------:|----------------|-------------|:------:|
| MEU-43 | `gui-shell` | 15 | [06a](build-plan/06a-gui-shell.md) | Electron + React UI shell | ✅ |
| MEU-44 | `gui-command-registry` | 15c | [06a §commands](build-plan/06a-gui-shell.md) | Command registry (commandRegistry.ts) | ✅ |
| MEU-45 | `gui-window-state` | 15d | [06a §window](build-plan/06a-gui-shell.md) | Window state persistence (electron-store) | ✅ |
| MEU-46 | `gui-mcp-status` | 15i | [06f §6f.9](build-plan/06f-gui-settings.md) | MCP Server Status panel · **E2E Wave 0**: sidebar `data-testid` + `launch`/`mcp-tool` tests (5) | ✅ |
| MEU-46a | `mcp-rest-proxy` | 15i.1 | [06f §6f.9 Data Sources](build-plan/06f-gui-settings.md) | REST proxy endpoints for MCP tool data (toolset count, API uptime) → completes MEU-46 panel · **Note:** GUI Settings "Registered tools" field currently shows `—`; this MEU adds `GET /api/v1/mcp/toolsets` + `GET /api/v1/mcp/diagnostics` endpoints so the GUI can display real numbers · `[PD-46a]`: static catalog + API uptime only (runtime loaded state deferred to `[MCP-HTTPBROKEN]`) · Depends on: MEU-46 ✅, Phase 4 ✅, Phase 5 ✅ | ✅ |
| MEU-47 | `gui-trades` | 16 | [06b](build-plan/06b-gui-trades.md) | React pages — Trades · **E2E Wave 1**: `trade-entry`/`mode-gating` tests (+7 = 12) | ✅ |
| MEU-47a | `screenshot-wiring` | 16.1 | [06b §Screenshot](build-plan/06b-gui-trades.md) | Wire ScreenshotPanel to image REST API (useQuery/useMutation); add `DELETE /images/{id}` route + `ImageService.delete_image()`; thumbnail grid, lightbox, upload, delete · Depends on: MEU-47 ✅, MEU-22 ✅ | ✅ |
| MEU-48 | `gui-plans` | 16 | [06c](build-plan/06c-gui-planning.md), [06h](build-plan/06h-gui-calculator.md) | React pages — Plans · **E2E Wave 4**: `position-size` tests (+2 = 18) · **Calculator expansion (deferred per 06h §Exit Criteria):** ① Account balance auto-load from `/api/v1/accounts` ([06h §87-93](build-plan/06h-gui-calculator.md)) — depends on MEU-71 `gui-accounts` · ② Copy-to-clipboard button on share size output · ③ Ticker field to auto-fetch entry price from market data `GET /api/v1/market/quote/{ticker}` — depends on MEU-65 `market-data-gui` for provider setup · ④ Ticker autocomplete dropdown (short + full name) using `GET /api/v1/market/search?q=` (MEU-61 API already built) — reusable for TradePlanPage ticker field too | ✅ |
| MEU-49 | `gui-notifications` | 16a | [06a §notify](build-plan/06a-gui-shell.md) | Notification system (toasts) | ✅ |
| MEU-50 | `gui-command-palette` | 16b | [06a §Ctrl+K](build-plan/06a-gui-shell.md) | Command palette (Ctrl+K) | ✅ |
| MEU-51 | `gui-state-persistence` | 16c | [06a §state](build-plan/06a-gui-shell.md) | UI state persistence | ✅ |

---

### P1 — Trade Reviews & Multi-Account

> Source: [build-priority-matrix.md](build-plan/build-priority-matrix.md) §P1

| MEU | Slug | Matrix Item | Build Plan Ref | Description | Status |
|-----|------|:-----------:|----------------|-------------|:------:|
| MEU-52 | `trade-report-entity` | 17 | [01 §entities](build-plan/01-domain-layer.md) | TradeReport entity + service | ✅ |
| MEU-53 | `trade-report-mcp-api` | 18 | [05c](build-plan/05c-mcp-trade-analytics.md) | TradeReport MCP tools + API routes | ✅ |
| MEU-54 | `multi-account-ui` | 19 | [06b](build-plan/06b-gui-trades.md) | Multi-account UI (badges, filtering) | ✅ |
| MEU-55 | `report-gui` | 20 | [06b](build-plan/06b-gui-trades.md) | Report GUI panel (ratings, tags, lessons) | ✅ |

---

### P1.5 — Market Data Aggregation (Phase 8)

> Source: [08-market-data.md](build-plan/08-market-data.md)

| MEU | Slug | Matrix Item | Build Plan Ref | Description | Status |
|-----|------|:-----------:|----------------|-------------|:------:|
| MEU-56 | `market-provider-entity` | 21 | [08 §entity](build-plan/08-market-data.md) | MarketDataProvider entity + AuthMethod enum | ✅ |
| MEU-57 | `market-response-dtos` | 22 | [08 §dtos](build-plan/08-market-data.md) | Normalized DTOs (MarketQuote, MarketNewsItem, etc.) | ✅ |
| MEU-58 | `market-provider-settings` | 23 | [08 §settings](build-plan/08-market-data.md) | MarketProviderSettingModel + encrypted key storage | ✅ |
| MEU-59 | `market-provider-registry` | 24 | [08 §registry](build-plan/08-market-data.md) | Provider registry (12 API-key + 2 free providers, config map) | ✅ |
| MEU-60 | `market-connection-svc` | 25 | [08 §connection](build-plan/08-market-data.md) | ProviderConnectionService (test, configure, list) | ✅ |
| MEU-61 | `market-data-service` | 26 | [08 §service](build-plan/08-market-data.md) | MarketDataService (quote, news, search, SEC filings) | ✅ |
| MEU-62 | `market-rate-limiter` | 27 | [08 §rate-limit](build-plan/08-market-data.md) | Rate limiter (token-bucket) + log redaction | ✅ |
| MEU-63 | `market-data-api` | 28 | [08 §api](build-plan/08-market-data.md) | Market data REST API (8 routes) | ✅ |
| MEU-64 | `market-data-mcp` | 29 | [05e](build-plan/05e-mcp-market-data.md) | Market data MCP tools (7 tools) | ✅ |
| MEU-65 | `market-data-gui` | 30 | [06f §providers](build-plan/06f-gui-settings.md) | Market Data Providers GUI settings page | ✅ |
| MEU-65a | `market-data-wiring` | 30.1 | [08 §8.9](build-plan/08-market-data.md#step-89-service-wiring) | Wire real `MarketDataService` + `ProviderConnectionService` into FastAPI lifespan (retire stubs); Yahoo Finance zero-config search fallback | ✅ |


---

### P2 — Planning & Watchlists

> Source: [build-priority-matrix.md](build-plan/build-priority-matrix.md) §P2

| MEU | Slug | Matrix Item | Build Plan Ref | Description | Status |
|-----|------|:-----------:|----------------|-------------|:------:|
| MEU-66 | `trade-plan-entity` | 31 | [01 §entities](build-plan/01-domain-layer.md) | TradePlan entity + service + API | ✅ |
| MEU-67 | `trade-plan-linking` | 32 | [03](build-plan/03-service-layer.md) | TradePlan ↔ Trade linking (plan → execution) | ✅ |
| MEU-68 | `watchlist` | 33 | [03](build-plan/03-service-layer.md) | Watchlist entity + service | ✅ |
| MEU-69 | `plan-watchlist-mcp` | 34 | [05d](build-plan/05d-mcp-trade-planning.md) | TradePlan + Watchlist MCP tools | ✅ |
| MEU-70 | `gui-planning` | 35 | [06c](build-plan/06c-gui-planning.md) | Planning GUI (plan cards, watchlists) | ✅ |
| MEU-70a | `watchlist-visual-redesign` | 35.1 | [06i](build-plan/06i-gui-watchlist-visual.md) | Watchlist visual redesign (Level 1: dark palette, price columns, tabular figures, gain/loss arrows) + [PLAN-NOSIZE] full-stack `position_size`/`shares_planned` field · ~~`[BOUNDARY-GAP]` F7 prerequisite~~ satisfied · Depends on: MEU-65 ✅, MEU-70 ✅ | ✅ |
| MEU-70b | `planning-ux-polish` | 35.2 | [06c §ux](build-plan/06c-gui-planning.md) | Trade Planner UX polish: segmented status buttons (no dropdown), conditional Link-to-Trade grayout, picker selection label feedback, editable `shares_planned` field · Frontend-only | ✅ |
| MEU-71 | `account-entity-api` | 35a.0 | [06d](build-plan/06d-gui-accounts.md) | Account entity + service + REST API; FK constraints already exist at infra layer (no Alembic migration needed); balance history + portfolio total endpoints | ✅ |
| MEU-71a | `account-gui` | 35a.1 | [06d](build-plan/06d-gui-accounts.md) | Account Management GUI (list, add, edit, balance display); accounts dropdown in Trade Planner form · Depends on MEU-71 | ✅ |
| MEU-71b | `calculator-account-integration` | 35a.2 | [06h](build-plan/06h-gui-calculator.md) | Position Calculator pulls account balance from selected account for risk % calculation · Depends on MEU-71 ✅ | ✅ |
| MEU-72 | `gui-scheduling` | 35b | [06e](build-plan/06e-gui-scheduling.md) | Scheduling GUI · ✅ ~~`[BOUNDARY-GAP]` F4 prerequisite~~ resolved by MEU-BV6 (2026-04-11) | ⏳ |
| MEU-73 | `gui-email-settings` | 35c | [06f §email](build-plan/06f-gui-settings.md) | Email Provider Settings GUI · ✅ `[BOUNDARY-GAP]` F6 resolved by MEU-BV5 (handoff 102) | ✅ |
| MEU-74 | `gui-backup-restore` | 35d | [06f §backup](build-plan/06f-gui-settings.md) | Backup & Restore Settings GUI · **E2E Wave 3**: `backup-restore` tests (+2 = 16) | ⬜ |
| MEU-75 | `gui-config-export` | 35e | [06f §export](build-plan/06f-gui-settings.md) | Config Export/Import GUI | ⬜ |
| MEU-76 | `gui-reset-defaults` | 35f | [06f §reset](build-plan/06f-gui-settings.md) | Reset to Default on settings pages · ✅ ~~`[BOUNDARY-GAP]` prerequisite~~ resolved by MEU-BV8 (2026-04-11) | ⬜ |

---

### P2.5 — Scheduling & Pipeline Engine (Phase 9)

> Source: [09-scheduling.md](build-plan/09-scheduling.md)

| MEU | Slug | Matrix Item | Build Plan Ref | Description | Status |
|-----|------|:-----------:|----------------|-------------|:------:|
| MEU-77 | `pipeline-enums` | 36 | [09 §enums](build-plan/09-scheduling.md) | PipelineStatus, StepErrorMode, DataType enums | ✅ |
| MEU-78 | `policy-models` | 37 | [09 §policy](build-plan/09-scheduling.md) | PolicyDocument + PolicyStep Pydantic models | ✅ |
| MEU-79 | `step-registry` | 38 | [09 §registry](build-plan/09-scheduling.md) | StepBase Protocol + RegisteredStep + StepRegistry | ✅ |
| MEU-80 | `policy-validator` | 39 | [09 §validator](build-plan/09-scheduling.md) | PolicyValidator (8 validation rules) | ✅ |
| MEU-81 | `scheduling-models` | 40 | [09 §tables](build-plan/09-scheduling.md) | SQLAlchemy models (9 tables) | ✅ |
| MEU-82 | `scheduling-repos` | 41 | [09 §repos](build-plan/09-scheduling.md) | Repository implementations + audit triggers | ✅ |
| MEU-83 | `pipeline-runner` | 42 | [09 §runner](build-plan/09-scheduling.md) | PipelineRunner (sequential async executor) | ✅ |
| MEU-84 | `ref-resolver` | 43 | [09 §resolver](build-plan/09-scheduling.md) | RefResolver + ConditionEvaluator | ✅ |
| MEU-85 | `fetch-step` | 44 | [09 §fetch](build-plan/09-scheduling.md) | FetchStep + HTTP cache | ✅ |
| MEU-86 | `transform-step` | 45 | [09 §transform](build-plan/09-scheduling.md) | TransformStep + Pandera validation | ✅ |
| MEU-87 | `store-render-step` | 46 | [09 §store-render](build-plan/09-scheduling.md) | StoreReportStep + RenderStep (Jinja2/Plotly/PDF) | ✅ |
| MEU-88 | `send-step` | 47 | [09 §send](build-plan/09-scheduling.md) | SendStep + async email delivery | ✅ |
| MEU-89 | `scheduling-api-mcp` | 48 | [05g](build-plan/05g-mcp-scheduling.md) | Scheduling REST API (16 endpoints) + MCP tools (6+2) | ✅ |
| MEU-90 | `scheduling-guardrails` | 49 | [09 §security](build-plan/09-scheduling.md) | Security guardrails (rate limits, approval, audit) | ✅ |

---

### P2.5a — Persistence Integration

> Source: [09a-persistence-integration.md](build-plan/09a-persistence-integration.md)
>
> Prerequisite: Phase 2 (MEU-12–16 ✅), Phase 9 scheduling repos (MEU-82 ✅)
> Unblocks: Phase 10 Service Daemon (MEU-91+), GUI scheduling (MEU-72)

| MEU | Slug | Matrix Item | Build Plan Ref | Description | Status |
|-----|------|:-----------:|----------------|-------------|:------:|
| MEU-90a | `persistence-wiring` | 49.0 | [09a §all](build-plan/09a-persistence-integration.md) | Replace StubUnitOfWork with SqlAlchemyUnitOfWork; wire all 17 real repos; fix guardrails getattr/dict mismatch; Alembic bootstrap | ✅ |
| MEU-90b | `mode-gating-test-isolation` | 49.1 | [testing-strategy](build-plan/testing-strategy.md) | Fix 8 flaky mode-gating tests: per-test `app.state` reset so lock/unlock doesn't leak across modules | ✅ |
| MEU-90c | `sqlcipher-native-deps` | 49.2 | [02 §2.3](build-plan/02-infrastructure.md), [ADR-001](../adrs/ADR-001-optional-sqlcipher-encryption.md) | Resolve sqlcipher3 availability on Windows; clear 15 skipped encryption tests | 🚫 closed — won't fix locally; CI covered via `crypto-tests` job (ADR-001 Option A+B, human decision 2026-03-22) |
| MEU-90d | `rendering-deps` | 49.3 | [09 §9.7d](build-plan/09-scheduling.md) | Install + validate Playwright + kaleido rendering extras; clear 1 skipped RenderStep test | ✅ |

---

### P2.5b — Backend Services Wiring & Quality

> Prerequisite: P2.5a (MEU-90a ✅), Phase 8 (MEU-65a ✅), Phase 9 steps (MEU-85/88 ✅), Email (MEU-73 ✅)
> Unblocks: End-to-end pipeline execution, MEU-72 "Run Now"/"Test Run" functionality
> Resolves: [SCHED-PIPELINE-WIRING], partial [STUB-RETIRE], [MCP-TOOLDISCOVERY]

| MEU | Slug | Matrix Item | Build Plan Ref | Description | Status |
|-----|------|:-----------:|----------------|-------------|:------:|
| MEU-PW1 | `pipeline-runtime-wiring` | 49.4 | [09 §runner](build-plan/09-scheduling.md), [06e](build-plan/06e-gui-scheduling.md) | Expand `PipelineRunner.__init__` with 8 keyword params (7 wired to real services, `provider_adapter` accepted as `None` slot for PW2); create `DbWriteAdapter` bridging `write_dispositions.py`; add `get_smtp_runtime_config()` to `EmailProviderService` (key remapping + password decryption); wire `delivery_repository`, `report_repository`, `pipeline_state_repo`, `db_connection`, `template_engine`, `smtp_config` in `main.py`; delete dead stubs (`StubMarketDataService`, `StubProviderConnectionService`); integration test for dependency wiring verification · Depends on: MEU-90a ✅, MEU-85 ✅, MEU-88 ✅, MEU-65a ✅, MEU-73 ✅ | ✅ |
| MEU-PW2 | `fetch-step-integration` | 49.5 | [09 §9.4](build-plan/09-scheduling.md) | Create `MarketDataProviderAdapter` + `MarketDataAdapterPort`; implement `FetchStep._check_cache` with TTL + market-hours extension; add cache upsert after fetch; wire adapter/rate-limiter/cache-repo in `main.py`; update PW1 contract tests 8→9 kwargs · Depends on: MEU-PW1 ✅ | ✅ |
| MEU-TD1 | `mcp-tool-discovery-audit` | 5.I | [05](build-plan/05-mcp-server.md) | Audit all 9 MCP toolset descriptions; enrich server instructions with workflow summaries; add `policy_json` examples to `create_policy`; reference MCP resources from tool descriptions; add prerequisite state, return shape, and error conditions · Parallel with any MEU | ⬜ |

---

### P2.6 — Service Daemon (Phase 10)


> Source: [10-service-daemon.md](build-plan/10-service-daemon.md)

| MEU | Slug | Matrix Item | Build Plan Ref | Description | Status |
|-----|------|:-----------:|----------------|-------------|:------:|
| MEU-91 | `service-config-files` | 49a | [10 §config](build-plan/10-service-daemon.md) | Service config (WinSW, launchd, systemd) | ⬜ |
| MEU-92 | `service-manager` | 49b | [10 §manager](build-plan/10-service-daemon.md) | ServiceManager class + IPC bridge | ⬜ |
| MEU-93 | `service-api` | 49c | [10 §api](build-plan/10-service-daemon.md) | Service REST endpoints (status, shutdown) | ⬜ |
| MEU-94 | `service-mcp` | 49d | [10 §mcp](build-plan/10-service-daemon.md) | Service MCP tools (status, restart, logs) | ⬜ |
| MEU-95 | `service-gui` | 49e | [10 §gui](build-plan/10-service-daemon.md) | Service Manager GUI + installer hooks | ⬜ |

---

### P2.75 — Build Plan Expansion (Analytics, Behavioral, Import)

> Source: [build-priority-matrix.md](build-plan/build-priority-matrix.md) §P2.75

#### Broker Adapters & Import

| MEU | Slug | Matrix Item | Build Plan Ref | Description | Status |
|-----|------|:-----------:|----------------|-------------|:------:|
| MEU-96 | `ibkr-adapter` | 50e | [matrix §brokers](build-plan/build-priority-matrix.md) | IBKR FlexQuery adapter | ✅ |
| MEU-97 | `alpaca-adapter` | 51e | [matrix §brokers](build-plan/build-priority-matrix.md) | Alpaca REST adapter | ⬜ |
| MEU-98 | `tradier-adapter` | 52e | [matrix §brokers](build-plan/build-priority-matrix.md) | Tradier REST adapter | ⬜ |
| MEU-99 | `csv-import` | 53e | [matrix §brokers](build-plan/build-priority-matrix.md) | CSV import + broker auto-detection | ✅ |
| MEU-100 | `pdf-parser` | 54e | [matrix §brokers](build-plan/build-priority-matrix.md) | PDF statement parser (pdfplumber) | ⬜ |
| MEU-101 | `dedup-service` | 55e | [matrix §brokers](build-plan/build-priority-matrix.md) | Deduplication service (exact + fuzzy) | ⬜ |
| MEU-102 | `identifier-resolver` | 56e | [matrix §brokers](build-plan/build-priority-matrix.md) | CUSIP→ticker resolver (OpenFIGI) | ⬜ |
| MEU-103 | `bank-import` | 57e | [matrix §brokers](build-plan/build-priority-matrix.md) | Bank statement import (OFX/CSV/QIF) | ⬜ |

#### Analytics & Behavioral

| MEU | Slug | Matrix Item | Build Plan Ref | Description | Status |
|-----|------|:-----------:|----------------|-------------|:------:|
| MEU-104 | `round-trip` | 58e | [matrix §analytics](build-plan/build-priority-matrix.md) | Round-trip service (entry→exit P&L) | ⬜ |
| MEU-105 | `mfe-mae-bso` | 59e | [matrix §analytics](build-plan/build-priority-matrix.md) | MFE/MAE/BSO excursion service | ⬜ |
| MEU-106 | `options-grouping` | 60e | [matrix §analytics](build-plan/build-priority-matrix.md) | Options strategy grouping (multi-leg) | ⬜ |
| MEU-107 | `transaction-ledger` | 61e | [matrix §analytics](build-plan/build-priority-matrix.md) | Transaction ledger / fee decomposition | ⬜ |
| MEU-108 | `execution-quality` | 62e | [matrix §analytics](build-plan/build-priority-matrix.md) | Execution quality scoring (NBBO) | ⬜ |
| MEU-109 | `pfof-analysis` | 63e | [matrix §analytics](build-plan/build-priority-matrix.md) | PFOF analysis (probabilistic model) | ⬜ |
| MEU-110 | `ai-review-persona` | 64e | [matrix §analytics](build-plan/build-priority-matrix.md) | AI review multi-persona | ⬜ |
| MEU-111 | `expectancy-edge` | 65e | [matrix §analytics](build-plan/build-priority-matrix.md) | Expectancy + edge metrics | ⬜ |
| MEU-112 | `monte-carlo` | 66e | [matrix §analytics](build-plan/build-priority-matrix.md) | Monte Carlo drawdown simulation | ⬜ |
| MEU-113 | `mistake-tracking` | 67e | [matrix §analytics](build-plan/build-priority-matrix.md) | Mistake tracking service | ⬜ |
| MEU-114 | `strategy-breakdown` | 68e | [matrix §analytics](build-plan/build-priority-matrix.md) | Strategy breakdown (P&L per strategy) | ⬜ |
| MEU-115 | `sqn-service` | 68.1e | [matrix §analytics](build-plan/build-priority-matrix.md) | SQN service (Van Tharp) | ⬜ |
| MEU-116 | `cost-of-free` | 68.3e | [matrix §analytics](build-plan/build-priority-matrix.md) | Cost of Free analysis (PFOF + fees) | ⬜ |
| MEU-117 | `trade-journal-link` | 68.4e | [matrix §analytics](build-plan/build-priority-matrix.md) | Trade↔journal linking (bidirectional FK) | ⬜ |

#### Expansion API + MCP + GUI

| MEU | Slug | Matrix Item | Build Plan Ref | Description | Status |
|-----|------|:-----------:|----------------|-------------|:------:|
| MEU-118 | `expansion-api` | 69e | [matrix §expansion](build-plan/build-priority-matrix.md) | REST routes (10 groups: brokers, analytics, etc.) | ⬜ |
| MEU-119 | `expansion-mcp` | 70e | [matrix §expansion](build-plan/build-priority-matrix.md) | MCP tools (22 expansion tools) | ⬜ |
| MEU-120 | `gui-trade-detail-tabs` | 71e | [matrix §expansion](build-plan/build-priority-matrix.md) | Trade detail GUI tabs (10 components) | ⬜ |
| MEU-121 | `gui-account-enhance` | 72e | [matrix §expansion](build-plan/build-priority-matrix.md) | Account GUI enhancements (5 components) | ⬜ |
| MEU-122 | `gui-analytics-dashboard` | 73e | [matrix §expansion](build-plan/build-priority-matrix.md) | Analytics dashboard GUI | ⬜ |

---

### P3 — Tax Estimation

> Source: [build-priority-matrix.md](build-plan/build-priority-matrix.md) §P3

#### Phase 3A — Core Tax Engine

| MEU | Slug | Matrix Item | Build Plan Ref | Description | Status |
|-----|------|:-----------:|----------------|-------------|:------:|
| MEU-123 | `tax-lot-entity` | 50 | [matrix §3A](build-plan/build-priority-matrix.md) | TaxLot entity + CostBasisMethod enum | ⬜ |
| MEU-124 | `tax-profile` | 51 | [matrix §3A](build-plan/build-priority-matrix.md) | TaxProfile entity + FilingStatus enum | ⬜ |
| MEU-125 | `tax-lot-tracking` | 52 | [matrix §3A](build-plan/build-priority-matrix.md) | Tax lot tracking: open/close, holding period | ⬜ |
| MEU-126 | `tax-gains-calc` | 53 | [matrix §3A](build-plan/build-priority-matrix.md) | ST vs LT classification + gains calculator | ⬜ |
| MEU-127 | `tax-loss-carry` | 54 | [matrix §3A](build-plan/build-priority-matrix.md) | Capital loss carryforward + account exclusion | ⬜ |
| MEU-128 | `options-assignment` | 55 | [matrix §3A](build-plan/build-priority-matrix.md) | Options assignment/exercise cost basis | ⬜ |
| MEU-129 | `ytd-pnl` | 56 | [matrix §3A](build-plan/build-priority-matrix.md) | YTD P&L by symbol (ST vs LT) | ⬜ |

#### Phase 3B — Wash Sale Engine

| MEU | Slug | Matrix Item | Build Plan Ref | Description | Status |
|-----|------|:-----------:|----------------|-------------|:------:|
| MEU-130 | `wash-sale-basic` | 57 | [matrix §3B](build-plan/build-priority-matrix.md) | WashSaleChain + 30-day detection | ⬜ |
| MEU-131 | `wash-sale-chain` | 58 | [matrix §3B](build-plan/build-priority-matrix.md) | Chain tracking (deferred loss rolling) | ⬜ |
| MEU-132 | `wash-sale-cross` | 59 | [matrix §3B](build-plan/build-priority-matrix.md) | Cross-account wash sale aggregation | ⬜ |
| MEU-133 | `wash-sale-options` | 60 | [matrix §3B](build-plan/build-priority-matrix.md) | Options-to-stock wash sale matching | ⬜ |
| MEU-134 | `wash-sale-drip` | 61 | [matrix §3B](build-plan/build-priority-matrix.md) | DRIP wash sale detection | ⬜ |
| MEU-135 | `wash-sale-rebalance` | 62 | [matrix §3B](build-plan/build-priority-matrix.md) | Auto-rebalance + spousal cross-wash warnings | ⬜ |
| MEU-136 | `wash-sale-alerts` | 63 | [matrix §3B](build-plan/build-priority-matrix.md) | Wash sale prevention alerts (proactive) | ⬜ |

#### Phase 3C — Tax Optimization Tools

| MEU | Slug | Matrix Item | Build Plan Ref | Description | Status |
|-----|------|:-----------:|----------------|-------------|:------:|
| MEU-137 | `tax-simulator` | 64 | [matrix §3C](build-plan/build-priority-matrix.md) | Pre-trade what-if tax simulator | ⬜ |
| MEU-138 | `tax-loss-harvest` | 65 | [matrix §3C](build-plan/build-priority-matrix.md) | Tax-loss harvesting scanner | ⬜ |
| MEU-139 | `tax-smart-replace` | 66 | [matrix §3C](build-plan/build-priority-matrix.md) | Tax-smart replacement suggestions | ⬜ |
| MEU-140 | `lot-matcher` | 67 | [matrix §3C](build-plan/build-priority-matrix.md) | Lot matcher / close specific lots UI | ⬜ |
| MEU-141 | `lot-reassignment` | 68 | [matrix §3C](build-plan/build-priority-matrix.md) | Post-trade lot reassignment window | ⬜ |
| MEU-142 | `tax-rate-compare` | 69 | [matrix §3C](build-plan/build-priority-matrix.md) | ST vs LT tax rate dollar comparison | ⬜ |

#### Phase 3D — Quarterly Payments & Tax Brackets

| MEU | Slug | Matrix Item | Build Plan Ref | Description | Status |
|-----|------|:-----------:|----------------|-------------|:------:|
| MEU-143 | `quarterly-estimate` | 70 | [matrix §3D](build-plan/build-priority-matrix.md) | QuarterlyEstimate entity + safe harbor calc | ⬜ |
| MEU-144 | `annualized-income` | 71 | [matrix §3D](build-plan/build-priority-matrix.md) | Annualized income method (Form 2210) | ⬜ |
| MEU-145 | `quarterly-tracker` | 72 | [matrix §3D](build-plan/build-priority-matrix.md) | Due date tracker + underpayment penalty | ⬜ |
| MEU-146 | `marginal-tax-calc` | 73 | [matrix §3D](build-plan/build-priority-matrix.md) | Marginal tax rate calculator (fed + state) | ⬜ |
| MEU-147 | `niit-alert` | 74 | [matrix §3D](build-plan/build-priority-matrix.md) | NIIT (3.8% surtax) threshold alert | ⬜ |

#### Phase 3E — Reports, Dashboard & API/MCP/GUI

| MEU | Slug | Matrix Item | Build Plan Ref | Description | Status |
|-----|------|:-----------:|----------------|-------------|:------:|
| MEU-148 | `tax-api` | 75 | [04f](build-plan/04f-api-tax.md) | Tax REST API endpoints | ⬜ |
| MEU-149 | `tax-mcp` | 76 | [05h](build-plan/05h-mcp-tax.md) | Tax MCP tools (8 tools) | ⬜ |
| MEU-150 | `tax-year-end` | 77 | [matrix §3E](build-plan/build-priority-matrix.md) | Year-end tax position summary | ⬜ |
| MEU-151 | `tax-deferred-loss` | 78 | [matrix §3E](build-plan/build-priority-matrix.md) | Deferred loss carryover report | ⬜ |
| MEU-152 | `tax-alpha` | 79 | [matrix §3E](build-plan/build-priority-matrix.md) | Tax alpha savings summary | ⬜ |
| MEU-153 | `tax-audit` | 80 | [matrix §3E](build-plan/build-priority-matrix.md) | Error check / transaction audit | ⬜ |
| MEU-154 | `gui-tax` | 81 | [06g](build-plan/06g-gui-tax.md) | Tax estimator GUI (React) | ⬜ |
| MEU-155 | `gui-calculator` | 81a | [06h](build-plan/06h-gui-calculator.md) | Position calculator GUI (React) | ⬜ |
| MEU-156 | `tax-section-toggles` | 82 | [matrix §3E](build-plan/build-priority-matrix.md) | Section 475/1256/Forex toggles | ⬜ |

---

### Phase 7: Distribution — P0

> Source: [07-distribution.md](build-plan/07-distribution.md)

| MEU | Slug | Matrix Item | Build Plan Ref | Description | Status |
|-----|------|:-----------:|----------------|-------------|:------:|
| MEU-157 | `distribution` | 7 (phase) | [07](build-plan/07-distribution.md) | Electron Builder, PyPI, npm packaging | ⬜ |

---

### Research-Enhanced Additions

> Source: [build-priority-matrix.md](build-plan/build-priority-matrix.md) §Research-Enhanced

#### Phase 5 Research Items

| MEU | Slug | Matrix Item | Build Plan Ref | Description | Status |
|-----|------|:-----------:|----------------|-------------|:------:|
| MEU-158 | `mcp-tags` | 5.A | [matrix §5.A](build-plan/build-priority-matrix.md) | Multi-dimensional tags (Tier 1) | ⬜ |
| MEU-159 | `mcp-pipeline-stages` | 5.B | [matrix §5.B](build-plan/build-priority-matrix.md) | Pipeline stage registry (Tier 1) | ⬜ |
| MEU-160 | `mcp-health-check` | 5.C | [matrix §5.C](build-plan/build-priority-matrix.md) | Health check route /health (Tier 1) | ⬜ |
| MEU-161 | `schema-drift-ci` | 5.D | [matrix §5.D](build-plan/build-priority-matrix.md) | Schema drift detection CI (Tier 1) | ⬜ |
| MEU-162 | `mcp-structured-output` | 5.E | [matrix §5.E](build-plan/build-priority-matrix.md) | Structured output schemas (Tier 2) | ⬜ |
| MEU-163 | `mcp-bm25-search` | 5.F | [matrix §5.F](build-plan/build-priority-matrix.md) | BM25 tool search (Tier 1) | ⬜ |
| MEU-164 | `mcp-keyword-loading` | 5.G | [matrix §5.G](build-plan/build-priority-matrix.md) | Keyword-triggered loading (Tier 2) | ⬜ |
| MEU-165a | `setup-workspace-core` | 5.H1 | [05k](build-plan/05k-mcp-setup-workspace.md) | Workspace setup tool core (Tier 2) | ⬜ |
| MEU-165b | `setup-workspace-templates` | 5.H2 | [05k](build-plan/05k-mcp-setup-workspace.md) | Workspace template content (Tier 2) | ⬜ |

#### Post-Phase 8 Research Items

| MEU | Slug | Matrix Item | Build Plan Ref | Description | Status |
|-----|------|:-----------:|----------------|-------------|:------:|
| MEU-166 | `code-mode-enhance` | 8.A | [matrix §8.A](build-plan/build-priority-matrix.md) | Code mode enhancement (Tier 2) | ⬜ |

#### Post-Phase 9 Research Items

| MEU | Slug | Matrix Item | Build Plan Ref | Description | Status |
|-----|------|:-----------:|----------------|-------------|:------:|
| MEU-167 | `recursive-orchestration` | 9.A | [matrix §9.A](build-plan/build-priority-matrix.md) | Recursive orchestration (Tier 3) | ⬜ |

#### CI / Quality Gate Research Items

| MEU | Slug | Matrix Item | Build Plan Ref | Description | Status |
|-----|------|:-----------:|----------------|-------------|:------:|
| MEU-168 | `schemathesis-ci` | CI.A | [testing-strategy](build-plan/testing-strategy.md) §Schemathesis | Schemathesis API fuzzing as CI step (start server + fuzz + report) | ⬜ |
| MEU-169 | `guard-auto-trip` | 15e.B | [friction-inventory](build-plan/friction-inventory.md) §FR-2.4, [05](build-plan/05-mcp-server.md) §5.9 | Auto-tripping circuit breaker state machine (CLOSED→OPEN→HALF_OPEN) + tests | ⬜ |
| MEU-170 | `e2e-all-green` | E2E.A | [testing-strategy](build-plan/testing-strategy.md) §E2E, [06-gui](build-plan/06-gui.md) §E2E Waves | All 20 Playwright E2E tests green (final gate after Waves 0–5 complete) | ⬜ |
| MEU-TS1 | `pyright-test-annotations` | TS.A | [testing-strategy](build-plan/testing-strategy.md) | Pyright Tier 1: fix generator fixture typing, Optional narrowing guards, mock protocol compliance, and `__mro__` access across 8 test files (13 errors) — zero production code changes | ✅ |
| MEU-TS2 | `pyright-enum-literals` | TS.B | [testing-strategy](build-plan/testing-strategy.md), [01 §1.2](build-plan/01-domain-layer.md) | Pyright Tier 2: replace ~50 raw string literals (`"BOT"`, `"SLD"`, `"broker"`) with enum values (`TradeAction.BOT`, `AccountType.BROKER`) in test assertions — zero production code changes | ✅ |
| MEU-TS3 | `pyright-entity-factories` | TS.C | [testing-strategy](build-plan/testing-strategy.md), [01 §1.4](build-plan/01-domain-layer.md) | Pyright Tier 3: resolve ~121 entity factory typing errors where `Column[T]` is passed as `T` — options: typed factory fns, `@overload` signatures, or scoped `# type: ignore` suppressions. 2 core service errors (Tier 4: `account_service.py` port ABC, `trade_service.py` type narrowing) included. | ✅ |

---

### MEU Summary

| Priority | MEU Range | Count | Completed |
|----------|-----------|:-----:|:---------:|
| P0 — Phase 1 | MEU-1 → MEU-11 | 11 | 11 |
| P0 — Phase 1A | MEU-1A → MEU-3A | 3 | 3 |
| P0 — Phase 2/2A | MEU-12 → MEU-21 | 10 | 10 |
| P0 — Phase 3/4 | MEU-22 → MEU-30 | 9 | 9 |
| P0 — Phase 5 | MEU-31 → MEU-42 | 12 | 12 |
| P0 — Phase 6 | MEU-43 → MEU-51 | 10 | 10 |
| P1 | MEU-52 → MEU-55 | 4 | 4 |
| P1.5 — Phase 8 | MEU-56 → MEU-65a | 11 | 11 |
| P2 | MEU-66 → MEU-76 | 15 | 7 |
| P2.5 — Phase 9 | MEU-77 → MEU-90 | 14 | 14 |
| P2.5a — Integration | MEU-90a → MEU-90d | 4 | 3 + 1 🚫 |
| P2.5b — Wiring & Quality | MEU-PW1, MEU-PW2, MEU-TD1 | 3 | 0 |
| P2.6 — Phase 10 | MEU-91 → MEU-95 | 5 | 0 |
| P2.75 — Expansion | MEU-96 → MEU-122 | 27 | 2 |
| P3 — Tax | MEU-123 → MEU-156 | 34 | 0 |
| Phase 7 | MEU-157 | 1 | 0 |
| Research | MEU-158 → MEU-170, MEU-TS1 → MEU-TS3 | 16 | 1 |
| **Total** | | **188** | **97 + 1 🚫** |

---

## Quick Start

**The first line of code you write is `test_calculator.py`. The first line of production code is `calculator.py`. Everything flows from there.**

Start here → [Phase 1: Domain Layer](build-plan/01-domain-layer.md)

---

## Validation

Run the build plan validator to check cross-references, numbering, and completeness:

```bash
python tools/validate_build_plan.py
```
