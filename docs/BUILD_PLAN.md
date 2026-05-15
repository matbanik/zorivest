# Zorivest — Build Plan & Test-Driven Development Guide

> **Hub file** — This document is the index for the complete build plan. Each phase and reference section lives in its own file under [`build-plan/`](build-plan/).

---

## Architecture Dependency Rule

The build order follows the **dependency rule**: inner layers first, outer layers last. Each layer is fully testable before the next one starts.

```
Domain → Infrastructure → Services → REST API → MCP Server → GUI → Distribution
  (1)        (2)            (3)         (4)         (5)        (6)       (7)
                                         ↑          ↑                    ↑
                                    WebSocket(4.1)  │          Scheduling(9)
                                              Market Data(8)   Service Daemon(10)
                                                                Monetization(11)
```

### Canonical Port

| Component | Port | Source |
|-----------|------|--------|
| **FastAPI backend** | `17787` | [backend-startup SKILL](../.agent/skills/backend-startup/SKILL.md) |
| **WebSocket** | `17787` (sub-path `/api/v1/ws`) | [04-rest-api.md](build-plan/04-rest-api.md#websocket-wiring-contract) |
| **Electron dev** | `5173` (Vite default) | [06-gui.md](build-plan/06-gui.md) |

> [!IMPORTANT]
> All build-plan specs that reference the backend MUST use port `17787`.
> Do NOT hardcode `8000` (FastAPI default) or `3000` — those will fail at runtime.

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
| 7 | [Distribution](build-plan/07-distribution.md) | `07-distribution.md` | Phases 1–6, 8–9 (Phase 10 static artifacts only) | Electron Builder, PyPI, npm |
| 8 | [Market Data](build-plan/08-market-data.md) | `08-market-data.md` | Phases 2–4 | 13 market data providers (11 API-key + 2 free via MEU-65), API key encryption, MCP tools |
| 8a | [Market Data Expansion](build-plan/08a-market-data-expansion.md) | `08a-market-data-expansion.md` | Phase 8 | 8 new data types, URL builders, extractors, service methods, pipeline persistence |
| 9 | [Scheduling & Pipelines](build-plan/09-scheduling.md) | `09-scheduling.md` | Phases 2–5, 8 | Policy engine, pipeline runner, APScheduler |
| 9a | [Persistence Integration](build-plan/09a-persistence-integration.md) | `09a-persistence-integration.md` | Phase 9 | SQLAlchemy wiring, real repos |
| 9b | [Pipeline Runtime Hardening](build-plan/09b-pipeline-hardening.md) | `09b-pipeline-hardening.md` | Phase 9a | Charmap, zombie, URL builder, cancellation fixes |
| 9c | [Pipeline Security Hardening](build-plan/09c-pipeline-security-hardening.md) | `09c-pipeline-security-hardening.md` | Phase 9b | StepContext safety, SQL sandbox, send/fetch guards |
| 9d | [Pipeline Step Extensions](build-plan/09d-pipeline-step-extensions.md) | `09d-pipeline-step-extensions.md` | Phase 9c | QueryStep, ComposeStep, variables, assertions |
| 9e | [Template Database](build-plan/09e-template-database.md) | `09e-template-database.md` | Phase 9 | EmailTemplateModel, HardenedSandbox, nh3 |
| 9f | [Policy Emulator](build-plan/09f-policy-emulator.md) | `09f-policy-emulator.md` | Phases 9c–9e | 4-phase dry-run, output containment |
| 9g | [Approval Security](build-plan/09g-approval-security.md) | `09g-approval-security.md` | Phase 9c | CSRF approval tokens, MCP scheduling gap fill |
| 9h | [Markdown Migration](build-plan/09h-pipeline-markdown-migration.md) | `09h-pipeline-markdown-migration.md` | Phase 9b | PDF removal, Markdown rendering |
| 10 | [Service Daemon](build-plan/10-service-daemon.md) | `10-service-daemon.md` | Phases 4, 9 | Cross-platform OS service, ServiceManager |
| 11 | [Monetization](build-plan/11-monetization.md) | `11-monetization.md` | Phases 2, 4, 8 | Subscription, OAuth, BYOK, usage metering |
| 12 | [Contributor Documentation](build-plan/12-contributor-docs.md) | `12-contributor-docs.md` | Nothing (parallel) | CONTRIBUTING, SECURITY, AGENTS.md, PR templates, governance, AI policy |

---

## Reference Documents

| Document | File | Purpose |
|----------|------|---------|
| [Domain Model Reference](build-plan/domain-model-reference.md) | `domain-model-reference.md` | Complete entity map, relationships, enum definitions |
| [Testing Strategy](build-plan/testing-strategy.md) | `testing-strategy.md` | MCP testing approaches, `conftest.py`, test configuration |
| [Image Architecture](build-plan/image-architecture.md) | `image-architecture.md` | BLOB vs filesystem, processing pipeline, validation |
| [Dependency Manifest](build-plan/dependency-manifest.md) | `dependency-manifest.md` | Install order by phase, version requirements |
| [Build Priority Matrix](build-plan/build-priority-matrix.md) | `build-priority-matrix.md` | P0–P3 tables with P1.5 market data, complete 68-item build order |
| [Market Data API Reference](../_inspiration/_market_tools_api-architecture.md) | `_inspiration/` | Source patterns for 11 API-key provider connectivity |

---

## Phase Status Tracker

| Phase | Status | Last Updated |
|-------|--------|--------------|
| 1 — Domain Layer | ✅ Completed | 2026-03-07 |
| 1A — Logging | ✅ Completed | 2026-03-07 |
| 2 — Infrastructure | ✅ Completed | 2026-03-08 |
| 2A — Backup/Restore | ✅ Completed | 2026-03-08 |
| 3 — Service Layer | ✅ Completed | 2026-03-08 |
| 3A — Tax Foundation | ✅ Completed (MEU-123–129) | 2026-05-12 |
| 3B — Wash Sale Engine | ✅ Completed (MEU-130–136) | 2026-05-13 |
| 3C — Tax Optimization Tools | ✅ Completed (MEU-137–142) | 2026-05-14 |
| 3D — Quarterly Payments | ✅ Completed (MEU-143–147) | 2026-05-13 |
| 3E — Reports & Full-Stack Wiring | ⚪ Not Started | — |
| 4 — REST API | ✅ Completed | 2026-03-09 |
| 5 — MCP Server | ✅ Completed | 2026-03-10 |
| 6 — GUI | 🟡 In Progress (P0 complete, P2.1 ✅, P2.2 ✅, P2.3 ✅, remaining P2 items) | 2026-05-05 |
| 7 — Distribution | ⚪ Not Started | — |
| 8 — Market Data | ✅ Completed | 2026-03-23 |
| 8a — Market Data Expansion | 🟡 In Progress — MEU-182a ✅, MEU-182 ✅, MEU-183 ✅, MEU-184 ✅, MEU-185 ✅, MEU-186 ✅, MEU-187 ✅, MEU-188 ✅, MEU-189 ✅, MEU-195 ✅, MEU-190 ✅, MEU-191 ✅, MEU-192 ✅, MEU-193 ✅, MEU-194 ✅ | 2026-05-05 |
| 9 — Scheduling | ✅ Core complete; P2.5c ✅ (10/10); P2.5b PW14 ✅ + 72b ✅; P2.5d ✅ (3/3); P2.5e ✅ (4/4); P2.5f ✅ (6/6 — 85→13 tools); P2.5g ✅ (1/1 — TokenRefreshManager) | 2026-04-30 |
| 10 — Service Daemon | ⚪ Not Started | — |
| 11 — Monetization | ⚪ Not Started | — |
| 12 — Contributor Documentation | ⚪ Not Started | — |

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
| MEU-48 | `gui-plans` | 16 | [06c](build-plan/06c-gui-planning.md), [06h](build-plan/06h-gui-calculator.md) | React pages — Plans · **E2E [Wave 4](build-plan/06-gui.md#wave-activation-schedule)**: `position-size` tests (+2 = 21) · **Calculator expansion (deferred per 06h §Exit Criteria):** ① Account balance auto-load from `/api/v1/accounts` ([06h §87-93](build-plan/06h-gui-calculator.md)) — depends on MEU-71 `gui-accounts` · ② Copy-to-clipboard button on share size output · ③ Ticker field to auto-fetch entry price from market data `GET /api/v1/market/quote/{ticker}` — depends on MEU-65 `market-data-gui` for provider setup · ④ Ticker autocomplete dropdown (short + full name) using `GET /api/v1/market/search?q=` (MEU-61 API already built) — reusable for TradePlanPage ticker field too | ✅ |
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

### P1.5a — Market Data Expansion (Phase 8a)

> Source: [build-priority-matrix.md](build-plan/build-priority-matrix.md) §P1.5a, [08a-market-data-expansion.md](build-plan/08a-market-data-expansion.md)

| MEU | Slug | Matrix Item | Build Plan Ref | Description | Status |
|-----|------|:-----------:|----------------|-------------|:------:|
| MEU-182a | `benzinga-code-purge` | 30.0 | [08a §8a.0](build-plan/08a-market-data-expansion.md#step-8a0-remove-benzinga-provider-code-meu-182a-benzinga-code-purge) | Remove Benzinga provider config, normalizer, validator, service branch + test cleanup | ✅ |
| MEU-182 | `market-expansion-dtos` | 30.1 | [08a §8a.1](build-plan/08a-market-data-expansion.md#step-8a1-new-dtos-meu-182-market-expansion-dtos) | 7 new DTOs (OHLCV, Fundamentals, Earnings, Dividends, Splits, Insider, EconomicCalendar) + updated `MarketDataPort` | ✅ |
| MEU-183 | `market-expansion-tables` | 30.2 | [08a §8a.2](build-plan/08a-market-data-expansion.md#step-8a2-database-tables-meu-183-market-expansion-tables) | 4 new SQLAlchemy models via `create_all()` | ✅ |
| MEU-184 | `provider-capabilities` | 30.3 | [08a §8a.3](build-plan/08a-market-data-expansion.md#step-8a3-provider-capabilities-registry-meu-184-provider-capabilities) | `ProviderCapabilities` dataclass + 11 registry entries | ✅ |
| MEU-185 | `simple-get-builders` | 30.4 | [08a §8a.4](build-plan/08a-market-data-expansion.md#step-8a4-simple-get-builders-meu-185-simple-get-builders) | 5 Simple GET URL builders: Alpaca, FMP, EODHD, API Ninjas, Tradier | ✅ |
| MEU-186 | `special-pattern-builders` | 30.5 | [08a §8a.5](build-plan/08a-market-data-expansion.md#step-8a5-special-pattern-builders-meu-186-special-pattern-builders) | 4 special-pattern builders: Alpha Vantage, Nasdaq DL, OpenFIGI, SEC API | ✅ |
| MEU-187 | `extractors-standard` | 30.6 | [08a §8a.6](build-plan/08a-market-data-expansion.md#step-8a6-standard-extractors-meu-187-extractors-standard) | Standard JSON extractors for 5 simple-GET providers + ~25 field mappings | ✅ |
| MEU-188 | `extractors-complex` | 30.7 | [08a §8a.7](build-plan/08a-market-data-expansion.md#step-8a7-complex-extractors-meu-188-extractors-complex) | Complex extractors: Alpha Vantage, Finnhub, Nasdaq DL, Polygon + ~20 field mappings | ✅ |
| MEU-189 | `post-body-runtime` | 30.8 | [08a §8a.8](build-plan/08a-market-data-expansion.md#step-8a8-post-body-runtime-wiring-meu-189-post-body-runtime) | POST-body runtime dispatch: `fetch_with_cache` POST support, adapter `_do_fetch` POST routing, OpenFIGI v3 POST connection test | ✅ |
| MEU-195 | `polygon-massive-migration` | 30.14 | [08a](build-plan/08a-market-data-expansion.md) | Polygon.io → Massive.com domain migration: update `base_url`, `signup_url`, display name in provider_registry.py; verify connection test with new domain | ✅ |
| MEU-190 | `service-methods-core` | 30.9 | [08a §8a.9](build-plan/08a-market-data-expansion.md#step-8a9-core-service-methods-meu-190-service-methods-core) | 3 high-value methods: `get_ohlcv`, `get_fundamentals`, `get_earnings` + normalizers | ✅ |
| MEU-191 | `service-methods-extended` | 30.10 | [08a §8a.10](build-plan/08a-market-data-expansion.md#step-8a10-extended-service-methods-meu-191-service-methods-extended) | 5 methods: dividends, splits, insider, economic_calendar, company_profile | ✅ |
| MEU-192 | `market-routes-mcp` | 30.11 | [08a §8a.11](build-plan/08a-market-data-expansion.md#step-8a11-routes--mcp-meu-192-market-routes-mcp) | 8 new REST endpoints + 8 MCP action mappings | ✅ |
| MEU-193 | `market-store-step` | 30.12 | [08a §8a.12](build-plan/08a-market-data-expansion.md#step-8a12-market-data-store-step-meu-193-market-store-step) | `MarketDataStoreStep` pipeline step: route DTOs to DB tables | ✅ |
| MEU-194 | `scheduling-recipes` | 30.13 | [08a §8a.13](build-plan/08a-market-data-expansion.md#step-8a13-scheduling-recipes-meu-194-scheduling-recipes) | 10 pre-built policy templates seeded via migration | ✅ |
| MEU-207 | `capability-wiring` | 30.15 | [08a §corrective](build-plan/08a-market-data-expansion.md) | Inject NORMALIZERS registry into MarketDataService + align provider_capabilities supported_data_types with normalizer coverage | ✅ |


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
| MEU-72 | `gui-scheduling` | 35b | [06e](build-plan/06e-gui-scheduling.md) | Scheduling GUI · **E2E [Wave 8](build-plan/06-gui.md#wave-activation-schedule)**: `scheduling`/`scheduling-tz` tests (+5 = 34) · ✅ ~~`[BOUNDARY-GAP]` F4 prerequisite~~ resolved by MEU-BV6 (2026-04-11) | ✅ |
| MEU-72b | `gui-email-templates` | 35b.2 | [06k](build-plan/06k-gui-email-templates.md) | Email Templates tab in SchedulingLayout (CRUD, preview, default protection) · **E2E [Wave 8](build-plan/06-gui.md#wave-activation-schedule)**: extend scheduling tests (+3) · Depends on MEU-72 ✅ | ✅ |
| MEU-73 | `gui-email-settings` | 35c | [06f §email](build-plan/06f-gui-settings.md) | Email Provider Settings GUI · ✅ `[BOUNDARY-GAP]` F6 resolved by MEU-BV5 (handoff 102) | ✅ |
| MEU-74 | `gui-backup-restore` | 35d | [06f §backup](build-plan/06f-gui-settings.md) | Backup & Restore Settings GUI · **E2E [Wave 3](build-plan/06-gui.md#wave-activation-schedule)**: `backup-restore` tests (+2 = 19) | ⬜ |
| MEU-75 | `gui-config-export` | 35e | [06f §export](build-plan/06f-gui-settings.md) | Config Export/Import GUI · **E2E wave TBD** — define wave before implementation | ⬜ |
| MEU-76 | `gui-reset-defaults` | 35f | [06f §reset](build-plan/06f-gui-settings.md) | Reset to Default on settings pages · ✅ ~~`[BOUNDARY-GAP]` prerequisite~~ resolved by MEU-BV8 (2026-04-11) · **E2E wave TBD** — define wave before implementation | ⬜ |

---

### P2.1 — GUI UX Hardening

> Source: [06-gui.md §UX Hardening](build-plan/06-gui.md#ux-hardening--unsaved-changes-guard)

| MEU | Slug | Matrix Item | Build Plan Ref | Description | Status |
|-----|------|:-----------:|----------------|-------------|:------:|
| MEU-196 | `gui-form-guard-shared` | 35i | [06 §UX](build-plan/06-gui.md) | Shared `UnsavedChangesModal` + `useFormGuard` hook + amber-pulse CSS | ✅ |
| MEU-197 | `gui-form-guard-settings` | 35j | [06 §UX](build-plan/06-gui.md) | Wire form guard to Market Data Providers + Email Provider pages | ✅ |
| MEU-198 | `gui-form-guard-crud` | 35k | [06 §UX](build-plan/06-gui.md) | Wire form guard to Accounts, Trades, Trade Plans, Watchlists | ✅ |

---

### P2.2 — GUI Table & List Enhancements

> Source: [build-priority-matrix.md §P2.2](build-plan/build-priority-matrix.md)

| MEU | Slug | Matrix Item | Build Plan Ref | Description | Status |
|-----|------|:-----------:|----------------|-------------|:------:|
| MEU-199 | `gui-table-primitives` | 35l | [06 §tables](build-plan/06-gui.md) | Shared table/list primitives: ConfirmDeleteModal, BulkActionBar, SortableColumnHeader, TableFilterBar | ✅ |
| MEU-200 | `gui-accounts-table` | 35m | [06d](build-plan/06d-gui-accounts.md) | Accounts table enhancements: delete confirm, multi-select, bulk delete, filter/sort | ✅ |
| MEU-201 | `gui-plans-table` | 35n | [06c](build-plan/06c-gui-planning.md) | Trade Plans table enhancements | ✅ |
| MEU-202 | `gui-watchlist-table` | 35o | [06i](build-plan/06i-gui-watchlist-visual.md) | Watchlist tickers table enhancements | ✅ |
| MEU-203 | `gui-scheduling-list` | 35p | [06e](build-plan/06e-gui-scheduling.md) | Scheduling list enhancements: Policies + Email Templates | ✅ |

---

### P2.3 — Calculator & Validation UX Hardening

> Source: [06-gui.md §UX Hardening](build-plan/06-gui.md), [06c-gui-planning.md](build-plan/06c-gui-planning.md), [06h-gui-calculator.md](build-plan/06h-gui-calculator.md)
> Execution plan: [calculator-validation-ux](execution/plans/2026-05-05-calculator-validation-ux/)

| MEU | Slug | Matrix Item | Build Plan Ref | Description | Status |
|-----|------|:-----------:|----------------|-------------|:------:|
| MEU-204 | `gui-form-validation-hardening` | 35q | [06 §UX](build-plan/06-gui.md) | Inline validation errors (red "X is required"), Save & Continue disable on missing fields across all CRUD forms | ✅ |
| MEU-205 | `gui-calculator-workflow` | 35r | [06h](build-plan/06h-gui-calculator.md) | Calculator plan picker, toggle switches (green/red, 3×2 grid, localStorage), auto-save new plans, Apply closes modal | ✅ |
| MEU-206 | `gui-tradeplan-layout` | 35s | [06c](build-plan/06c-gui-planning.md) | 4-column price grid, auto position_size recalc, centered calculator button | ✅ |

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
> Unblocks: End-to-end pipeline execution, MEU-72 "Run Now"/"Test Run" functionality, GUI scheduling dashboard cancel UX
> Resolves: [SCHED-PIPELINE-WIRING], partial [STUB-RETIRE], [MCP-TOOLDISCOVERY], [PIPE-CHARMAP], [PIPE-ZOMBIE], [PIPE-URLBUILD], [PIPE-NOCANCEL], [PIPE-STEPKEY], [PIPE-TMPLVAR], [PIPE-RAWBLOB], [PIPE-PROVNORM], [PIPE-QUOTEFIELD], [PIPE-SILENTPASS], [PIPE-E2E-CHAIN], [PIPE-CACHEUPSERT]

| MEU | Slug | Matrix Item | Build Plan Ref | Description | Status |
|-----|------|:-----------:|----------------|-------------|:------:|
| MEU-PW1 | `pipeline-runtime-wiring` | 49.4 | [09 §runner](build-plan/09-scheduling.md), [06e](build-plan/06e-gui-scheduling.md) | Expand `PipelineRunner.__init__` with 8 keyword params (7 wired to real services, `provider_adapter` accepted as `None` slot for PW2); create `DbWriteAdapter` bridging `write_dispositions.py`; add `get_smtp_runtime_config()` to `EmailProviderService` (key remapping + password decryption); wire `delivery_repository`, `report_repository`, `pipeline_state_repo`, `db_connection`, `template_engine`, `smtp_config` in `main.py`; delete dead stubs (`StubMarketDataService`, `StubProviderConnectionService`); integration test for dependency wiring verification · Depends on: MEU-90a ✅, MEU-85 ✅, MEU-88 ✅, MEU-65a ✅, MEU-73 ✅ | ✅ |
| MEU-PW2 | `fetch-step-integration` | 49.5 | [09 §9.4](build-plan/09-scheduling.md) | Create `MarketDataProviderAdapter` + `MarketDataAdapterPort`; implement `FetchStep._check_cache` with TTL + market-hours extension; add cache upsert after fetch; wire adapter/rate-limiter/cache-repo in `main.py`; update PW1 contract tests 8→9 kwargs · Depends on: MEU-PW1 ✅ | ✅ |
| MEU-PW3 | `market-data-schemas` | 49.6 | [09 §9.5](build-plan/09-scheduling.md) | 4 SQLAlchemy ORM models (OHLCV, Quote, News, Fundamentals) + 3 Pandera schemas + field mappings → data quality hardening · Independent of PW1/PW2 | ✅ |
| MEU-PW4 | `pipeline-charmap-fix` | 49.7 | [09b §9B.2](build-plan/09b-pipeline-hardening.md) | Fix [PIPE-CHARMAP]: configure structlog UTF-8 output on Windows; bytes-safe JSON serialization in `_persist_step()`; `UnicodeDecoder` processor · Resolves pipeline crash on non-ASCII error messages · No deps | ✅ |
| MEU-PW5 | `pipeline-zombie-fix` | 49.8 | [09b §9B.3](build-plan/09b-pipeline-hardening.md) | Fix [PIPE-ZOMBIE]: eliminate dual-write (SchedulingService sole record creator, PipelineRunner accepts `run_id`); per-phase httpx.Timeout; zombie recovery at startup scan · Depends on: MEU-PW4 | ✅ |
| MEU-PW6 | `provider-url-builders` | 49.9 | [09b §9B.4](build-plan/09b-pipeline-hardening.md) | Fix [PIPE-URLBUILD]: per-provider URL builder registry (Yahoo, Polygon, Finnhub + GenericUrlBuilder fallback); criteria key normalization (`tickers[]` vs `symbol`); forward `headers_template` to HTTP fetch · Depends on: MEU-PW5 (parallel with PW7) | ✅ |
| MEU-PW7 | `pipeline-cancellation` | 49.10 | [09b §9B.5](build-plan/09b-pipeline-hardening.md) | Fix [PIPE-NOCANCEL]: add `CANCELLING` status to PipelineStatus enum; `_active_tasks` task registry; `cancel_run()` (cooperative + forced); `POST /runs/{run_id}/cancel` endpoint; per-step cooperative cancellation check · Depends on: MEU-PW5 (parallel with PW6) | ✅ |
| MEU-PW8 | `pipeline-e2e-test-harness` | 49.11 | [09b §9B.6](build-plan/09b-pipeline-hardening.md) | End-to-end pipeline integration test infrastructure: 7 test policy fixtures (happy path, error modes, dry-run, skip, cancel, unicode); 6 mock step implementations; 14+ integration tests validating full service stack (SchedulingService → PipelineRunner → Steps → Persistence → Audit) · Depends on: MEU-PW4 through MEU-PW7 | 🟡 |
| MEU-PW9 | `send-step-template-wiring` | 49.12 | [09 §9.8a](build-plan/09-scheduling.md) | Wire `SendStep._resolve_body()` template rendering: `EMAIL_TEMPLATES` registry lookup + Jinja2 rendering + `html_body` priority + raw fallback · Depends on: MEU-88 ✅ | ✅ |
| MEU-PW11 | `pipeline-cursor-tracking` | 49.13 | [09 §9.4b](build-plan/09-scheduling.md) | `FetchStep` cursor upsert after successful fetch: `pipeline_state_repo.upsert()` with ISO timestamp + SHA-256 hash · Depends on: MEU-PW2 ✅ | ✅ |
| MEU-PW12 | `pipeline-dataflow-chain-fix` | 49.14 | [09 §9.4–9.8](build-plan/09-scheduling.md), [deficiency report](../.agent/context/scheduling/pipeline-dataflow-deficiency-report.md) | Fix 6 serial data-flow bugs: [PIPE-STEPKEY] add `source_step_id` param to TransformStep for dynamic predecessor output resolution; [PIPE-RAWBLOB] per-provider response envelope extractor (unwrap `quoteResponse.result` etc.); [PIPE-PROVNORM] provider slug normalization at field mapping lookup; [PIPE-QUOTEFIELD] extend Yahoo quote field mappings with `change`, `change_pct`, `symbol` passthrough; [PIPE-TMPLVAR] wire parsed records into `quotes` template variable via TransformStep output key; [PIPE-SILENTPASS] return WARNING/FAILED on 0 records + `min_records` param + `structlog.warning("transform_zero_records")` · Depends on: MEU-PW6 ✅, MEU-PW9 ✅ | ✅ |
| MEU-PW13 | `pipeline-e2e-chain-tests` | 49.15 | [09b §9B.6](build-plan/09b-pipeline-hardening.md), [data flow gap analysis](../.agent/context/scheduling/data_flow_gap_analysis.md) | Integration tests exercising real FetchStep → TransformStep → SendStep data handoff with mocked HTTP (real `MarketDataProviderAdapter`), real field mappings, Pandera validation, in-memory SQLite; includes [PIPE-CACHEUPSERT] write-back assertion; extends MEU-PW8 test harness · Depends on: MEU-PW12 | ✅ |
| MEU-72a | `scheduling-gui-tz-polish` | 35f.1 | [06e](build-plan/06e-gui-scheduling.md) | `PolicyList` timezone display: replace `toLocaleString` with `formatTimestamp` IANA-aware utility · Independent | ✅ |
| MEU-TD1 | `mcp-tool-discovery-audit` | 5.I | [05](build-plan/05-mcp-server.md) | Audit all 13 compound tool descriptions; enrich server instructions with workflow summaries; add `policy_json` examples to `create_policy`; reference MCP resources from tool descriptions; add prerequisite state, return shape, and error conditions · Parallel with any MEU | ✅ |
| MEU-PW14 | `pipeline-markdown-migration` | 49.29 | [09h](build-plan/09h-pipeline-markdown-migration.md) | Remove PDF output pipeline, add Markdown rendering, cleanup Playwright dependency · Resolves [PIPE-DROPPDF] · Depends on MEU-PW9 ✅, MEU-87 ✅ | ✅ |

---

### P2.5c — Pipeline Security Hardening

> Source: [09c-pipeline-security-hardening.md](build-plan/09c-pipeline-security-hardening.md), [09d-pipeline-step-extensions.md](build-plan/09d-pipeline-step-extensions.md), [09e-template-database.md](build-plan/09e-template-database.md), [09f-policy-emulator.md](build-plan/09f-policy-emulator.md)
>
> Prerequisite: P2.5b core wiring complete (MEU-PW1→PW7, PW9, PW11→PW13 ✅); PW8 🟡 and TD1 ⬜ are non-blocking for security hardening
> Unblocks: Full agent-first policy authoring, GUI scheduling templates, Service Daemon scheduling integration
> Resolves: [PIPE-MUTCTX], [PIPE-NOSANDBOX], [PIPE-NOQUERYSTEP], [PIPE-NOCOMPOSE], [PIPE-NOTEMPLATEDB], [PIPE-NOVARS], [PIPE-NOASSERT], [PIPE-NOEMULATOR], [PIPE-NOEMUMCP]
>
> Research source: [retail-trader-policy-use-cases.md](../_inspiration/policy_pipeline_wiring-research/retail-trader-policy-use-cases.md) (validated by 3-model adversarial review)

| MEU | Slug | Matrix Item | Build Plan Ref | Description | Status |
|-----|------|:-----------:|----------------|-------------|:------:|
| MEU-PH1 | `stepcontext-safety` | 49.16 | [09c §9C.1](build-plan/09c-pipeline-security-hardening.md) | StepContext `safe_deepcopy` + `Secret` carrier class + depth/byte guards | ✅ |
| MEU-PH2 | `sql-sandbox` | 49.17 | [09c §9C.2](build-plan/09c-pipeline-security-hardening.md) | SQL sandbox: `set_authorizer` + `mode=ro` + AST allowlist + `progress_handler` + secrets scan + policy content IDs | ✅ |
| MEU-PH3 | `send-fetch-guards` | 49.18 | [09c §9C.3–9C.4](build-plan/09c-pipeline-security-hardening.md) | SendStep confirmation gate + FetchStep MIME/fan-out validation | ✅ |
| MEU-PH4 | `query-step` | 49.19 | [09d §9D.1](build-plan/09d-pipeline-step-extensions.md) | QueryStep implementation (read-only SQL via sandbox) | ✅ |
| MEU-PH5 | `compose-step` | 49.20 | [09d §9D.2](build-plan/09d-pipeline-step-extensions.md) | ComposeStep implementation (multi-source data merging) | ✅ |
| MEU-PH6 | `template-database` | 49.21 | [09e §all](build-plan/09e-template-database.md) | EmailTemplateModel + HardenedSandbox + nh3 sanitization + template CRUD | ✅ |
| MEU-PH7 | `policy-vars-assertions` | 49.22 | [09d §9D.3–9D.5](build-plan/09d-pipeline-step-extensions.md) | PolicyDocument `variables` + assertion gates + step-count cap + schema v2 | ✅ |
| MEU-PH8 | `policy-emulator` | 49.23 | [09f §all](build-plan/09f-policy-emulator.md) | 4-phase emulator + output containment + session budget + error schema | ✅ |
| MEU-PH9 | `emulator-mcp-tools` | 49.24 | [05g §new](build-plan/05g-mcp-scheduling.md) | 11 new MCP tools: emulator, schema discovery, template CRUD, provider discovery | ✅ |
| MEU-PH10 | `default-template` | 49.25 | [09e §9E.6](build-plan/09e-template-database.md) | Pre-loaded Morning Check-In template | ✅ |

---

### P2.5d — Approval Security & Validation Hardening

> Source: [09g-approval-security.md](build-plan/09g-approval-security.md), [09f-policy-emulator.md](build-plan/09f-policy-emulator.md) (extension)
>
> Prerequisite: P2.5c ✅ complete
> Unblocks: Secure agent-first policy lifecycle, MCP-only policy management
> Resolves: [MCP-APPROVBYPASS], [MCP-POLICYGAP], [EMULATOR-VALIDATE]

| MEU | Slug | Matrix Item | Build Plan Ref | Description | Status |
|-----|------|:-----------:|----------------|-------------|:------:|
| MEU-PH11 | `approval-csrf-token` | 49.26 | [09g §1](build-plan/09g-approval-security.md) | CSRF challenge token: Electron IPC generation + API validation middleware on `POST /policies/{id}/approve`; single-use, 5-min TTL, policy-scoped | ✅ |
| MEU-PH12 | `mcp-scheduling-gap-fill` | 49.27 | [09g §2](build-plan/09g-approval-security.md) | Add 3 MCP tools: `delete_policy` (destructive + confirmation), `update_policy` (in-place PATCH), `get_email_config` (SMTP readiness) | ✅ |
| MEU-PH13 | `emulator-validate-hardening` | 49.28 | [09f §ext](build-plan/09f-policy-emulator.md) | VALIDATE phase improvements: EXPLAIN SQL for schema errors, SMTP config check for email channels, step output wiring validation (render→send chain) | ✅ |

---

### P2.5e — MCP Tool Remediation

> Source: [MCP Tool Audit Report](../.agent/context/MCP/mcp-tool-audit-report.md)
>
> Prerequisite: P2.5c ✅ complete; parallel with P2.5d
> Unblocks: Reliable MCP tool surface for AI agents
> Resolves: [MCP-TOOLAUDIT]

| MEU | Slug | Matrix Item | Build Plan Ref | Description | Status |
|-----|------|:-----------:|----------------|-------------|:------:|
| MEU-TA1 | `mcp-delete-trade-fix` | 5.J | [05c](build-plan/05c-mcp-trade-analytics.md) | Fix `delete_trade` returning 500 on valid exec_id — debug API trade deletion, fix error handling, add regression test · [MCP-TOOLAUDIT] High | ✅ |
| MEU-TA2 | `mcp-settings-serialization-fix` | 5.K | [05a](build-plan/05a-mcp-zorivest-settings.md) | Fix `update_settings` returning 422 with `[object Object]` — TypeScript serialization bug, values must be strings at MCP boundary · [MCP-TOOLAUDIT] Medium | ✅ |
| MEU-TA3 | `mcp-unimplemented-tool-guard` | 5.L | [05](build-plan/05-mcp-server.md) | Guard 6 unimplemented MCP tools (`list_bank_accounts`, `list_brokers`, `resolve_identifiers`, tax toolset 4 tools) to return "501 Not Implemented" instead of 404/500 · [MCP-TOOLAUDIT] Medium | ✅ |
| MEU-TA4 | `mcp-trade-plan-lifecycle` | 5.M | [05d](build-plan/05d-mcp-trade-planning.md) | Add `list_trade_plans` and `delete_trade_plan` MCP tools for plan lifecycle management · Fix `create_trade_plan` 409 by enabling stale plan cleanup · [MCP-TOOLAUDIT] Medium | ✅ |

---

### P2.5f — MCP Tool Consolidation

> Source: [mcp-consolidation-proposal-v3.md](../.agent/context/MCP/mcp-consolidation-proposal-v3.md)
>
> Prerequisite: P2.5e complete (MEU-TA1→TA4 ✅)
> Resolves: [MCP-TOOLPROLIFERATION], [MCP-TOOLCAP]

| MEU | Slug | Matrix Item | Build Plan Ref | Description | Status |
|-----|------|:-----------:|----------------|-------------|:------:|
| MC0 | `mcp-consolidation-docs` | 5.N | [05 §5.11](build-plan/05-mcp-server.md) | Documentation sync: BUILD_PLAN.md, meu-registry.md, known-issues.md, 05-mcp-server.md §5.11, mcp-tool-index.md, build-priority-matrix.md | ✅ |
| MC1 | `compound-router-system` | 5.O | [05 §compound](build-plan/05-mcp-server.md) | CompoundToolRouter + `zorivest_system` (9 actions), remove 9 old registrations. Tools/list: 86→77 | ✅ |
| MC2 | `compound-trade-analytics` | 5.P | [05c](build-plan/05c-mcp-trade-analytics.md) | `zorivest_trade` (6), `zorivest_report` (2), `zorivest_analytics` (13 incl. position_size). Tools/list: 77→59 | ✅ |
| MC3 | `compound-data-vertical` | 5.Q | [05f](build-plan/05f-mcp-accounts.md) | `zorivest_account` (9), `zorivest_market` (7), `zorivest_watchlist` (5), `zorivest_import` (7), `zorivest_tax` (4 stubs). Tools/list: 59→32 | ✅ |
| MC4 | `compound-ops-restructure` | 5.R | [05g](build-plan/05g-mcp-scheduling.md) | `zorivest_plan` (3), `zorivest_policy` (9), `zorivest_template` (6), `zorivest_db` (5); seed.ts 10→4 toolsets; CI gate tool_count ≤ 13. Tools/list: 32→13 | ✅ |
| MC5 | `consolidation-finalize` | 5.S | [05](build-plan/05-mcp-server.md) | Baseline snapshot (85→13), server instructions, anti-placeholder, MCP audit, archive [MCP-TOOLPROLIFERATION] | ✅ |

---

### P2.5g — MCP Auth Infrastructure

> Source: [known-issues.md](../.agent/context/known-issues.md) [MCP-AUTHRACE]
>
> Prerequisite: P2.5f complete (MC0→MC5 ✅)
> Resolves: [MCP-AUTHRACE]

| MEU | Slug | Matrix Item | Build Plan Ref | Description | Status |
|-----|------|:-----------:|----------------|-------------|:------:|
| MEU-PH14 | `token-refresh-manager` | 5.T | [05 §5.7](build-plan/05-mcp-server.md) | `TokenRefreshManager` singleton with promise coalescing, 30s proactive expiry, async `getAuthHeaders()`. Removes module-level `authState`/`bootstrapAuth()`. 14 FIC tests. | ✅ |

---

### P2.5 (addition) — WebSocket Infrastructure

> Source: [04-rest-api.md](build-plan/04-rest-api.md) §WebSocket

| MEU | Slug | Matrix Item | Build Plan Ref | Description | Status |
|-----|------|:-----------:|----------------|-------------|:------:|
| MEU-174 | `websocket-infrastructure` | 49.7 | [04 §ws](build-plan/04-rest-api.md) | FastAPI WebSocket endpoint + ConnectionManager + Electron WebSocketBridge relay | ⬜ |

---

### P2 (addition) — Home Dashboard

> Source: [06j-gui-home.md](build-plan/06j-gui-home.md)

| MEU | Slug | Matrix Item | Build Plan Ref | Description | Status |
|-----|------|:-----------:|----------------|-------------|:------:|
| MEU-171 | `dashboard-service` | 35g | [03 §dashboard](build-plan/03-service-layer.md), [06j §6j.2](build-plan/06j-gui-home.md) | DashboardService (read-only aggregation) + 6 REST endpoints | ⬜ |
| MEU-172 | `gui-home-dashboard` | 35h | [06j](build-plan/06j-gui-home.md) | Home Dashboard GUI page (React) — startup route, settings, nav rail update · **E2E [Wave 7](build-plan/06-gui.md#wave-activation-schedule)**: `home-dashboard` tests (+3 = 29) | ⬜ |

---

### P2.6 — Service Daemon (Phase 10)


> Source: [10-service-daemon.md](build-plan/10-service-daemon.md)

| MEU | Slug | Matrix Item | Build Plan Ref | Description | Status |
|-----|------|:-----------:|----------------|-------------|:------:|
| MEU-91 | `service-config-files` | 49a | [10 §config](build-plan/10-service-daemon.md) | Service config (WinSW, launchd, systemd) | ⬜ |
| MEU-92 | `service-manager` | 49b | [10 §manager](build-plan/10-service-daemon.md) | ServiceManager class + IPC bridge | ⬜ |
| MEU-93 | `service-api` | 49c | [10 §api](build-plan/10-service-daemon.md) | Service REST endpoints (status, shutdown) | ⬜ |
| MEU-94 | `service-mcp` | 49d | [10 §mcp](build-plan/10-service-daemon.md) | Service MCP tools (status, restart, logs) | ⬜ |
| MEU-95 | `service-gui` | 49e | [10 §gui](build-plan/10-service-daemon.md) | Service Manager GUI + installer hooks · **E2E wave TBD** — define wave before implementation | ⬜ |
| MEU-95a | `tray-icon-renderer` | 49f | [10 §10.9](build-plan/10-service-daemon.md) | TrayIconRenderer: OffscreenCanvas → NativeImage, state machine, platform-aware sizing | ⬜ |
| MEU-95b | `tray-icon-integration` | 49g | [10 §10.9](build-plan/10-service-daemon.md) | Wire renderer to ServiceManager health, notification count, context menu, theme detection | ⬜ |

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
| MEU-120 | `gui-trade-detail-tabs` | 71e | [matrix §expansion](build-plan/build-priority-matrix.md) | Trade detail GUI tabs (10 components) · **E2E wave TBD** — define wave before implementation | ⬜ |
| MEU-121 | `gui-account-enhance` | 72e | [matrix §expansion](build-plan/build-priority-matrix.md) | Account GUI enhancements (5 components) · **E2E wave TBD** — define wave before implementation | ⬜ |
| MEU-122 | `gui-analytics-dashboard` | 73e | [matrix §expansion](build-plan/build-priority-matrix.md) | Analytics dashboard GUI · **E2E wave TBD** — define wave before implementation | ⬜ |

---

### P3 — Tax Estimation

> Source: [build-priority-matrix.md](build-plan/build-priority-matrix.md) §P3

#### Phase 3A — Core Tax Engine

| MEU | Slug | Matrix Item | Build Plan Ref | Description | Status |
|-----|------|:-----------:|----------------|-------------|:------:|
| MEU-123 | `tax-lot-entity` | 50 | [matrix §3A](build-plan/build-priority-matrix.md) | TaxLot entity + CostBasisMethod enum | ✅ |
| MEU-124 | `tax-profile` | 51 | [matrix §3A](build-plan/build-priority-matrix.md) | TaxProfile entity + FilingStatus enum | ✅ |
| MEU-125 | `tax-lot-tracking` | 52 | [matrix §3A](build-plan/build-priority-matrix.md) | Tax lot tracking: open/close, holding period | ✅ |
| MEU-126 | `tax-gains-calc` | 53 | [matrix §3A](build-plan/build-priority-matrix.md) | ST vs LT classification + gains calculator | ✅ |
| MEU-127 | `tax-loss-carry` | 54 | [matrix §3A](build-plan/build-priority-matrix.md) | Capital loss carryforward + account exclusion | ✅ |
| MEU-128 | `options-assignment` | 55 | [matrix §3A](build-plan/build-priority-matrix.md) | Options assignment/exercise cost basis | ✅ |
| MEU-129 | `ytd-pnl` | 56 | [matrix §3A](build-plan/build-priority-matrix.md) | YTD P&L by symbol (ST vs LT) | ✅ |

#### Phase 3B — Wash Sale Engine

| MEU | Slug | Matrix Item | Build Plan Ref | Description | Status |
|-----|------|:-----------:|----------------|-------------|:------:|
| MEU-130 | `wash-sale-basic` | 57 | [matrix §3B](build-plan/build-priority-matrix.md) | WashSaleChain + 30-day detection | ✅ |
| MEU-131 | `wash-sale-chain` | 58 | [matrix §3B](build-plan/build-priority-matrix.md) | Chain tracking (deferred loss rolling) | ✅ |
| MEU-132 | `wash-sale-cross` | 59 | [matrix §3B](build-plan/build-priority-matrix.md) | Cross-account wash sale aggregation | ✅ |
| MEU-133 | `wash-sale-options` | 60 | [matrix §3B](build-plan/build-priority-matrix.md) | Options-to-stock wash sale matching | ✅ |
| MEU-134 | `wash-sale-drip` | 61 | [matrix §3B](build-plan/build-priority-matrix.md) | DRIP wash sale detection | ✅ |
| MEU-135 | `wash-sale-rebalance` | 62 | [matrix §3B](build-plan/build-priority-matrix.md) | Auto-rebalance + spousal cross-wash warnings | ✅ |
| MEU-136 | `wash-sale-alerts` | 63 | [matrix §3B](build-plan/build-priority-matrix.md) | Wash sale prevention alerts (proactive) | ✅ |

#### Phase 3C — Tax Optimization Tools

| MEU | Slug | Matrix Item | Build Plan Ref | Description | Status |
|-----|------|:-----------:|----------------|-------------|:------:|
| MEU-137 | `tax-simulator` | 64 | [matrix §3C](build-plan/build-priority-matrix.md) | Pre-trade what-if tax simulator | ✅ |
| MEU-138 | `tax-loss-harvest` | 65 | [matrix §3C](build-plan/build-priority-matrix.md) | Tax-loss harvesting scanner | ✅ |
| MEU-139 | `tax-smart-replace` | 66 | [matrix §3C](build-plan/build-priority-matrix.md) | Tax-smart replacement suggestions | ✅ |
| MEU-140 | `lot-matcher` | 67 | [matrix §3C](build-plan/build-priority-matrix.md) | Lot matcher / close specific lots UI | ✅ |
| MEU-141 | `lot-reassignment` | 68 | [matrix §3C](build-plan/build-priority-matrix.md) | Post-trade lot reassignment window | ✅ |
| MEU-142 | `tax-rate-compare` | 69 | [matrix §3C](build-plan/build-priority-matrix.md) | ST vs LT tax rate dollar comparison | ✅ |

#### Phase 3D — Quarterly Payments & Tax Brackets

| MEU | Slug | Matrix Item | Build Plan Ref | Description | Status |
|-----|------|:-----------:|----------------|-------------|:------:|
| MEU-143 | `quarterly-estimate` | 70 | [matrix §3D](build-plan/build-priority-matrix.md) | QuarterlyEstimate entity + safe harbor calc | ✅ |
| MEU-144 | `annualized-income` | 71 | [matrix §3D](build-plan/build-priority-matrix.md) | Annualized income method (Form 2210) | ✅ |
| MEU-145 | `quarterly-tracker` | 72 | [matrix §3D](build-plan/build-priority-matrix.md) | Due date tracker + underpayment penalty | ✅ |
| MEU-146 | `marginal-tax-calc` | 73 | [matrix §3D](build-plan/build-priority-matrix.md) | Marginal tax rate calculator (fed + state) | ✅ |
| MEU-147 | `niit-alert` | 74 | [matrix §3D](build-plan/build-priority-matrix.md) | NIIT (3.8% surtax) threshold alert | ✅ |

#### Phase 3E — Reports, Dashboard & API/MCP/GUI

| MEU | Slug | Matrix Item | Build Plan Ref | Description | Status |
|-----|------|:-----------:|----------------|-------------|:------:|
| MEU-148 | `tax-api` | 75 | [04f](build-plan/04f-api-tax.md) | Tax REST API endpoints | ✅ |
| MEU-148a | `tax-profile-api` | 75a | [04f §profile](build-plan/04f-api-tax.md) | TaxProfile CRUD API: `GET`/`PUT /api/v1/tax/profile` backed by SettingsRegistry; registers 12 TaxProfile keys (filing_status, tax_year, federal_bracket, state_tax_rate, state, prior_year_tax, agi_estimate, capital_loss_carryforward, wash_sale_method, default_cost_basis, section_475_elected, section_1256_eligible) · Depends on: MEU-18 ✅, MEU-124 ✅, MEU-148 ✅ | ⬜ |
| MEU-149 | `tax-mcp` | 76 | [05h](build-plan/05h-mcp-tax.md) | Tax MCP tools (8 tools) | ✅ |
| MEU-150 | `tax-year-end` | 77 | [matrix §3E](build-plan/build-priority-matrix.md) | Year-end tax position summary | ✅ |
| MEU-151 | `tax-deferred-loss` | 78 | [matrix §3E](build-plan/build-priority-matrix.md) | Deferred loss carryover report | ✅ |
| MEU-152 | `tax-alpha` | 79 | [matrix §3E](build-plan/build-priority-matrix.md) | Tax alpha savings summary | ✅ |
| MEU-153 | `tax-audit` | 80 | [matrix §3E](build-plan/build-priority-matrix.md) | Error check / transaction audit | ✅ |
| MEU-154 | `gui-tax` | 81 | [06g](build-plan/06g-gui-tax.md) | Tax estimator GUI (React) · **E2E Wave 11** — 5 test files, 18 E2E tests | ✅ |
| MEU-155 | `gui-calculator` | 81a | [06h](build-plan/06h-gui-calculator.md) | Position calculator GUI (React) — expansion modes (Futures/Options/Forex/Crypto), scenario comparison, calculation history, Copy-to-Plan · **Wave 10** — modal expansion tests | ✅ |
| MEU-156 | `tax-section-toggles` | 82 | [matrix §3E](build-plan/build-priority-matrix.md) | Section 475/1256/Forex toggles · Depends on: MEU-148a | ⬜ |

---

### Phase 12: Contributor Documentation Suite

> Source: [12-contributor-docs.md](build-plan/12-contributor-docs.md) | Research: [COMPOSITE-SYNTHESIS.md](../_inspiration/CONTRIBUTING.md_research/COMPOSITE-SYNTHESIS.md)
>
> Depends on: Nothing — pure documentation; parallel with all code phases
> Blocks: Phase 7 (Distribution) — contributor docs must exist before public release

#### P0 — Foundation (Ship Before First External Contributor)

| MEU | Slug | Matrix Item | Build Plan Ref | Description | Status |
|-----|------|:-----------:|----------------|-------------|:------:|
| MEU-208 | `security-reporting` | 12.1 | [12 §12.1](build-plan/12-contributor-docs.md) | SECURITY.md — vulnerability scope, PVR reporting, response SLAs, no-bounty | ⬜ |
| MEU-209 | `github-templates` | 12.2 | [12 §12.2](build-plan/12-contributor-docs.md) | .github/PULL_REQUEST_TEMPLATE.md + issue templates (bug, feature, config.yml) | ⬜ |
| MEU-210 | `contributor-guide` | 12.3 | [12 §12.3](build-plan/12-contributor-docs.md) | CONTRIBUTING.md (~390 lines) + CODE_OF_CONDUCT.md (Contributor Covenant 2.1) | ⬜ |
| MEU-211 | `dev-setup-docs` | 12.4 | [12 §12.4](build-plan/12-contributor-docs.md) | docs/DEVELOPMENT.md + root AGENTS.md (≤200 lines) + README.md link update | ⬜ |

#### P1 — Governance & AI Policy

| MEU | Slug | Matrix Item | Build Plan Ref | Description | Status |
|-----|------|:-----------:|----------------|-------------|:------:|
| MEU-212 | `governance-ai-policy` | 12.5 | [12 §12.5](build-plan/12-contributor-docs.md) | GOVERNANCE.md + docs/AI_POLICY.md + docs/ARCHITECTURE.md | ⬜ |
| MEU-213 | `ai-tool-shims` | 12.6 | [12 §12.6](build-plan/12-contributor-docs.md) | CLAUDE.md redirect + .windsurfrules + per-package AGENTS.md (×5) + docs_improvement.yml | ⬜ |

#### P2 — Advanced Tooling

| MEU | Slug | Matrix Item | Build Plan Ref | Description | Status |
|-----|------|:-----------:|----------------|-------------|:------:|
| MEU-214 | `native-ai-rules` | 12.7 | [12 §12.7](build-plan/12-contributor-docs.md) | .github/copilot-instructions.md + .cursor/rules/*.mdc + CODEOWNERS | ⬜ |
| MEU-215 | `contributor-ci` | 12.8 | [12 §12.8](build-plan/12-contributor-docs.md) | tools/validate_agent_files.py + agent_issue.yml + CONTRIBUTORS.md | ⬜ |

---

### Phase 7: Distribution — P0

> Source: [07-distribution.md](build-plan/07-distribution.md)

| MEU | Slug | Matrix Item | Build Plan Ref | Description | Status |
|-----|------|:-----------:|----------------|-------------|:------:|
| MEU-157 | `distribution` | 7 (phase) | [07](build-plan/07-distribution.md) | Electron Builder, PyPI, npm packaging | ⬜ |

---

### P4 — Phase 11: Monetization

> Source: [11-monetization.md](build-plan/11-monetization.md)

| MEU | Slug | Matrix Item | Build Plan Ref | Description | Status |
|-----|------|:-----------:|----------------|-------------|:------:|
| MEU-175 | `monetization-domain` | 11.1 | [11 §11.1](build-plan/11-monetization.md) | License entity, SubscriptionTier enum, UsageMeter entity | ⬜ |
| MEU-176 | `oauth-google` | 11.2 | [11 §11.2](build-plan/11-monetization.md) | Google OAuth PKCE + encrypted token storage | ⬜ |
| MEU-177 | `google-calendar-tasks` | 11.3 | [11 §11.3](build-plan/11-monetization.md) | Calendar/Tasks API for Plan reminders | ⬜ |
| MEU-178 | `license-enforcement` | 11.4 | [11 §11.4](build-plan/11-monetization.md) | Ed25519 JWT validation, offline grace, tier gating | ⬜ |
| MEU-179 | `byok-ai-providers` | 11.5 | [11 §11.5](build-plan/11-monetization.md) | AI provider key CRUD (encrypted), extends Phase 8 pattern | ⬜ |
| MEU-180 | `monetization-api-gui` | 11.7 | [11 §11.7–11.8](build-plan/11-monetization.md) | Monetization REST routes (11 endpoints) + Subscription Settings GUI · **E2E wave TBD** — define wave before implementation | ⬜ |
| MEU-181 | `usage-metering` | 11.6 | [11 §11.6](build-plan/11-monetization.md) | Usage counters, tier limits, approach-to-limit UX | ⬜ |

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

#### Phase 6 Research Items

| MEU | Slug | Matrix Item | Build Plan Ref | Description | Status |
|-----|------|:-----------:|----------------|-------------|:------:|
| MEU-173 | `floating-pnl-widget` | 6.A | [matrix §6.A](build-plan/build-priority-matrix.md) | Always-on-top P&L BrowserWindow, consumes `pnl.tick` WebSocket events | ⬜ |

#### CI / Quality Gate Research Items

| MEU | Slug | Matrix Item | Build Plan Ref | Description | Status |
|-----|------|:-----------:|----------------|-------------|:------:|
| MEU-168 | `schemathesis-ci` | CI.A | [testing-strategy](build-plan/testing-strategy.md) §Schemathesis | Schemathesis API fuzzing as CI step (start server + fuzz + report) | ⬜ |
| MEU-169 | `guard-auto-trip` | 15e.B | [friction-inventory](build-plan/friction-inventory.md) §FR-2.4, [05](build-plan/05-mcp-server.md) §5.9 | Auto-tripping circuit breaker state machine (CLOSED→OPEN→HALF_OPEN) + tests | ⬜ |
| MEU-170 | `e2e-all-green` | E2E.A | [testing-strategy](build-plan/testing-strategy.md) §E2E, [06-gui](build-plan/06-gui.md) §E2E Waves | All 37+ Playwright E2E tests green (final gate after Waves 0–9 complete). Wave 10 count TBD. | ⬜ |
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
| P1.5a — Phase 8a | MEU-182a → MEU-195, MEU-207 | 16 | 16 |
| P2 | MEU-66 → MEU-76, MEU-171 → MEU-172, MEU-72b | 18 | 9 |
| P2.1 — GUI UX Hardening | MEU-196 → MEU-198 | 3 | 3 |
| P2.2 — GUI Table Enhancements | MEU-199 → MEU-203 | 5 | 5 |
| P2.3 — Calculator & Validation UX | MEU-204 → MEU-206 | 3 | 3 |
| P2.5 — Phase 9 + WebSocket | MEU-77 → MEU-90, MEU-174 | 15 | 14 |
| P2.5a — Integration | MEU-90a → MEU-90d | 4 | 3 + 1 🚫 |
| P2.5b — Wiring & Quality + Hardening | MEU-PW1 → MEU-PW14, MEU-72a, MEU-TD1 | 15 | 14 + 1 🟡 |
| P2.5c — Security Hardening | MEU-PH1 → MEU-PH10 | 10 | 10 |
| P2.5d — Approval Security | MEU-PH11 → MEU-PH13 | 3 | 3 |
| P2.5e — Tool Remediation | MEU-TA1 → MEU-TA4 | 4 | 4 |
| P2.5f — Tool Consolidation | MC0 → MC5 | 6 | 6 |
| P2.5g — Auth Infrastructure | MEU-PH14 | 1 | 1 |
| P2.6 — Phase 10 | MEU-91 → MEU-95b | 7 | 0 |
| P2.75 — Expansion | MEU-96 → MEU-122 | 27 | 2 |
| P3 — Tax | MEU-123 → MEU-156, MEU-148a | 35 | 33 |
| Phase 7 | MEU-157 | 1 | 0 |
| Phase 12 — Contributor Docs | MEU-208 → MEU-215 | 8 | 0 |
| P4 — Phase 11 | MEU-175 → MEU-181 | 7 | 0 |
| Research | MEU-158 → MEU-170, MEU-173, MEU-TS1 → MEU-TS3 | 17 | 3 |
| **Total** | | **270** | **170 + 1 🟡 + 1 🚫** |

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
