# Phase 3 (Tax Estimation) — Jump-Ahead Feasibility Analysis

> **Verdict: ✅ YES — all 34 MEUs (3A through 3E) can be built before completing P2.6, P2.75, and remaining P2 items.**

---

## Context Clarification

Your foundational layers are **already built**:

| Layer | Status | P3 Needs It? |
|-------|--------|:------------:|
| Phase 1 — Domain (Trade, Account, Execution) | ✅ | Yes → Satisfied |
| Phase 1A — Logging | ✅ | Yes → Satisfied |
| Phase 2 — Infrastructure (SQLAlchemy, Repos, UoW) | ✅ | Yes → Satisfied |
| Phase 2A — Backup/Restore | ✅ | No |
| Phase 3 — Service Layer | ✅ | Yes → Satisfied |
| Phase 4 — REST API (stubs wired) | ✅ | Yes → Satisfied |
| Phase 5 — MCP Server (501 stubs) | ✅ | Yes → Satisfied |
| Phase 6 — GUI Core | ✅ | Yes → Satisfied |

The "underlying systems" you mentioned (logging, application services, etc.) **are already complete**. Your architecture dependency chain (`Domain → Infra → Services → API → MCP → GUI`) is fully satisfied for P3 work.

---

## What's Actually Being Skipped

| Skipped Item | MEU Count | P3 Needs It? | Rationale |
|-------------|:---------:|:------------:|-----------|
| P2 GUI Settings (MEU-74/75/76) | 3 | **No** | Tax GUI (MEU-154) builds its own panels |
| P2 Dashboard (MEU-171/172) | 2 | **No** | Tax widgets can be added later; independent |
| P2.5 WebSocket (MEU-174) | 1 | **No** | Tax is request-driven, not real-time |
| P2.6 Service Daemon (Phase 10) | 7 | **No** | Quarterly reminders work as on-demand checks |
| P2.75 RoundTrip (MEU-104) | 1 | **No** | ⚠️ See critical analysis below |
| P2.75 Analytics (MEU-104–116) | 14 | **No** | Different bounded context |
| P2.75 Import Expansion (MEU-97–103) | 5 | **No** | Tax works with existing imported data |
| MEU-PW8 E2E Test Harness | 1 | **Soft Yes** | Strongly recommended but not blocking |

---

## The Critical Question: RoundTrip vs. TaxLot

This is the only relationship that requires careful analysis.

```
                    ┌─────────────┐
                    │   Trades /  │
                    │ Executions  │  ← Already built (Phase 1 Domain)
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              ▼                         ▼
     ┌────────────────┐       ┌────────────────┐
     │   RoundTrip    │       │    TaxLot      │
     │   (P2.75)      │       │    (P3A)       │
     │                │       │                │
     │ Journal focus  │       │ Tax focus      │
     │ Entry/Exit     │       │ FIFO/LIFO/Spec │
     │ R-multiple     │       │ Wash sale adj  │
     │ Hold time      │       │ ST/LT period   │
     └────────────────┘       └────────────────┘
           │                         │
           ▼                         ▼
    Analytics/Behavior         Tax Engine/Reports
      (P2.75 rest)              (P3B-3E)
```

> [!IMPORTANT]
> **These are parallel abstractions over the same source data** — siblings, not parent-child. RoundTrip pairs trades for journal analytics ("2R winner, 3-day hold"). TaxLot pairs trades for IRS compliance ("FIFO cost basis, wash sale adjustment, 366-day holding period"). Their algorithms are fundamentally different because they serve different purposes.

---

## Sub-Phase Dependency Analysis

### 3A — Core Tax Engine (7 MEUs) → **FULLY INDEPENDENT** ✅

| MEU | Description | Dependencies | Status |
|-----|-------------|-------------|:------:|
| MEU-123 | TaxLot entity + CostBasisMethod enum | Domain layer ✅ | ✅ Go |
| MEU-124 | TaxProfile entity + FilingStatus enum | Domain layer ✅ | ✅ Go |
| MEU-125 | Tax lot tracking: open/close, holding period | MEU-123, Trade data ✅ | ✅ Go |
| MEU-126 | ST vs LT classification + gains calc | MEU-123, MEU-125 | ✅ Go |
| MEU-127 | Capital loss carryforward | MEU-126, MEU-124 | ✅ Go |
| MEU-128 | Options assignment/exercise cost basis | MEU-123, option fields | ⚠️ Verify |
| MEU-129 | YTD P&L by symbol | MEU-126, MEU-127 | ✅ Go |

> [!WARNING]
> **MEU-128 risk:** Options assignment needs option-specific fields on the Trade entity (option_type, strike_price, expiration_date, underlying_symbol, event_type). Verify these exist before starting.

### 3B — Wash Sale Engine (7 MEUs) → **INDEPENDENT** ✅

| MEU | Description | Dependencies | Risk |
|-----|-------------|-------------|:----:|
| MEU-130 | 30-day detection | 3A complete | ✅ |
| MEU-131 | Chain tracking | MEU-130 | ✅ |
| MEU-132 | Cross-account aggregation | MEU-130, Account ✅ | ✅ |
| MEU-133 | Options-to-stock matching | MEU-130, option fields | ⚠️ Same as 128 |
| MEU-134 | DRIP detection | MEU-130, DRIP model | ⚠️ Verify DRIP |
| MEU-135 | Auto-rebalance warnings | MEU-130 | ✅ |
| MEU-136 | Prevention alerts | MEU-130 | ✅ |

### 3C — Tax Optimization Tools (6 MEUs) → **INDEPENDENT** ✅

All items depend on 3A/3B being complete. No external dependencies.

### 3D — Quarterly Payments (5 MEUs) → **FULLY INDEPENDENT** ✅

Zero P2 dependencies. Pure tax computation with calendar logic. Does **not** need Service Daemon — on-demand computation is sufficient.

> [!TIP]
> **3D has no dependency on 3B or 3C.** You could parallelize: `3A → [3B, 3D] → 3C → 3E`

### 3E — Reports, API/MCP/GUI (9 MEUs) → **INDEPENDENT of P2, depends on 3A-3D** ✅

Replaces existing 501 stubs with real implementations. The API framework, MCP server, and GUI core are all built. 3E simply wires tax services into existing presentation layers.

---

## Pre-Flight Audit (Before Starting P3)

> [!CAUTION]
> **Do this before writing any P3 code.** Budget 1-2 days.

### 1. Trade Execution Granularity

Tax lot tracking needs **per-fill granularity**: individual fill price, quantity, commission allocation, and **settlement date** (critical for year-end lot assignment and wash sale 61-day windows).

**Action:** Inspect the `Trade`/`Execution` entity. If only aggregated data exists, add a `Fill` value object to MEU-123 scope.

### 2. Options Domain Completeness

MEU-128 and MEU-133 need option-specific attributes:

```
Required option fields:
├── option_type: Call | Put
├── strike_price: Decimal
├── expiration_date: Date
├── underlying_symbol: str
└── event_type: Exercise | Assignment | Expiration | Close
```

**Action:** Audit the `Trade` entity. Budget domain extension into MEU-123 if fields are missing.

### 3. DRIP Transaction Model

MEU-134 needs to identify dividend reinvestments as share acquisitions.

**Action:** Check if dividend/DRIP transaction types exist. If not, design the `TaxLot.acquisition_source` enum to include `DRIP` from day one, even if the import path comes later.

---

## Risk Assessment

| Scenario | Probability | Impact | Mitigation |
|----------|:----------:|:------:|-----------|
| Trade entity lacks fill-level data | 30% | MEU-123 needs schema extension | Inspect schema now |
| Options fields missing from domain | 40% | MEU-128/133 need domain extension | Inspect schema now |
| DRIP transaction type missing | 50% | MEU-134 needs domain extension | Use manual tagging fallback |
| Tax GUI conflicts with P2 GUI | 15% | Minor shared component rework | Keep tax GUI in isolated panels |
| RoundTrip later duplicates pairing code | 100% | Minimal — intentional separation | Accept as DDD bounded context |

**Overall confidence: 88%** that all 34 MEUs can proceed without rework.

---

## Recommended Execution Order

```
PRE-FLIGHT AUDIT (1-2 days)
  □ Inspect Trade/Execution schema for fill-level data
  □ Inspect Trade entity for option-specific fields
  □ Check if DRIP transaction types exist
  □ Document any domain extensions needed
  □ Add extensions to MEU-123 scope if required

THEN:
┌────────┐   ┌────────┬────────┐   ┌────────┐   ┌────────┐
│  3A    │──▶│  3B    │  3D    │──▶│  3C    │──▶│  3E    │
│ Core   │   │ Wash   │ Qtrly  │   │ Optim  │   │ Reports│
│ Engine │   │ Sales  │ Paymts │   │ Tools  │   │ API/GUI│
│ 7 MEUs │   │ 7 MEUs │ 5 MEUs │   │ 6 MEUs │   │ 9 MEUs │
└────────┘   └────────┴────────┘   └────────┘   └────────┘
                  ↑ parallel ↑
```

> [!TIP]
> **Strong recommendation:** Build MEU-PW8 (E2E test harness) concurrently with early 3A work. The 34 MEUs of P3 involve complex tax logic where edge case bugs are expensive. Having E2E tests by the time you hit 3B (wash sales) significantly de-risks the entire phase.

---

## Full-Stack Integration: Service → API → MCP → GUI

> [!NOTE]
> This section traces how each P3 sub-phase connects through the full stack, and whether service layer wiring is accounted for or missing.

### Architecture of the Integration

The build plan defines a clear **staged wiring** pattern for tax features:

```
                              Already Built                    P3 Builds
                    ┌──────────────────────────────┐  ┌─────────────────────────┐
                    │                              │  │                         │
                    │  ┌──────────────────────┐    │  │  ┌──────────────────┐   │
                    │  │ REST Routes (tax.py) │◄───┼──┼──│ TaxService       │   │
                    │  │ 12 endpoints         │    │  │  │ 8+4 methods      │   │
                    │  │ Wired to StubTax ─ ─ ┼ ─ ┤  │  │ (replaces stub)  │   │
                    │  └─────────┬────────────┘    │  │  └────────┬─────────┘   │
                    │            │                 │  │           │             │
                    │  ┌─────────▼────────────┐    │  │  ┌────────▼─────────┐   │
                    │  │ MCP Compound Tool    │    │  │  │ Domain Logic     │   │
                    │  │ zorivest_tax         │    │  │  │ TaxLot, WashSale │   │
                    │  │ 4 stub actions ────── ┼ ─ ┤  │  │ TaxProfile, etc  │   │
                    │  └─────────┬────────────┘    │  │  └──────────────────┘   │
                    │            │                 │  │                         │
                    │  ┌─────────▼────────────┐    │  │  ┌──────────────────┐   │
                    │  │ GUI (Shell/Nav)      │    │  │  │ Tax GUI Views    │   │
                    │  │ No tax pages yet     │    │  │  │ Dashboard, Lots  │   │
                    │  └──────────────────────┘    │  │  │ WashSale, Sim    │   │
                    │                              │  │  └──────────────────┘   │
                    └──────────────────────────────┘  └─────────────────────────┘
```

### Current Wiring State (What Exists Today)

| Component | File | Status | What It Does |
|-----------|------|:------:|-------------|
| **REST Routes** | `routes/tax.py` | ✅ Built | 12 endpoints registered, all delegate to `service = Depends(get_tax_service)` |
| **Stub Service** | `stubs.py` → `StubTaxService` | ✅ Built | 12 methods returning empty/default dicts. Wired in `main.py` lifespan |
| **DI Wiring** | `dependencies.py` → `get_tax_service` | ✅ Built | Resolves `StubTaxService` from `app.state.tax_service` |
| **MCP Compound Tool** | `compound/tax-tool.ts` | ✅ Built | `zorivest_tax` with 4 action stubs (estimate, wash_sales, manage_lots, harvest) returning 501 |
| **Toolset Seed** | `toolsets/seed.ts` | ✅ Built | `zorivest_tax` registered in toolset manifest |
| **GUI** | — | ⬜ None | No tax pages or components exist |

> [!IMPORTANT]
> **Key finding:** The REST routes and MCP tool are already wired and functional — they just delegate to stubs. The service layer _contract_ is defined (12 methods on `StubTaxService`). What's missing is the _real_ `TaxService` with actual domain logic behind it.

### Per-Sub-Phase Integration Mapping

#### 3A — Core Tax Engine → Service Layer

| Build Plan Item | Domain | Service Method | REST Route | MCP Tool | GUI |
|----------------|--------|---------------|------------|----------|-----|
| Item 50: TaxLot entity | `TaxLot` + `CostBasisMethod` enum | — (entity only) | — | — | — |
| Item 51: TaxProfile entity | `TaxProfile` + `FilingStatus` enum | — (entity only) | — | — | — |
| Item 52: Lot tracking | `TaxLotAssigner` (FIFO/LIFO/SpecID) | `TaxService.get_lots()`, `.close_lot()`, `.reassign_basis()` | `GET /lots`, `POST /lots/{id}/close`, `PUT /lots/{id}/reassign` | `get_tax_lots` (action: `manage_lots`) | Lot Viewer table |
| Item 53: ST/LT + gains calc | Pure domain fn | `TaxService.simulate_impact()` (partial) | `POST /simulate` (partial) | `simulate_tax_impact` | What-If results |
| Item 54: Loss carryforward | Domain rule | `TaxService.ytd_summary()` (partial) | `GET /ytd-summary` (partial) | — | Dashboard card |
| Item 55: Options cost basis | Domain extension | `TaxService.simulate_impact()` (options path) | Same route | Same tool | — |
| Item 56: YTD P&L by symbol | Domain aggregation | `TaxService.ytd_summary()` | `GET /ytd-summary?group_by=symbol` | `get_ytd_tax_summary` | YTD P&L table |

**Service layer accounting:** ✅ **Covered.** The `TaxService` spec in [03-service-layer.md](file:///p:/zorivest/docs/build-plan/03-service-layer.md) explicitly defines all 8 methods. However, 3A only _implements_ the subset needed: `get_lots`, `close_lot`, `reassign_basis`, `simulate_impact` (partial), `ytd_summary` (partial). The REST routes are already wired to the stub — swapping the stub for the real service is defined in 3E's MEU-148.

**Gap identified:** None. The service contract exists, 3A implements the domain logic, and 3E wires it in.

#### 3B — Wash Sale Engine → Service Layer

| Build Plan Item | Domain | Service Method | REST Route | MCP Tool | GUI |
|----------------|--------|---------------|------------|----------|-----|
| Item 57: 30-day detection | `WashSaleChain` entity, detection algorithm | `TaxService.find_wash_sales()` | `POST /wash-sales` | `find_wash_sales` (action: `wash_sales`) | Wash Sale Monitor |
| Item 58: Chain tracking | `WashSaleEntry` sub-entity | `TaxService.scan_wash_sales()` | `POST /wash-sales/scan` | Same tool | Chain Detail view |
| Item 59: Cross-account | Account aggregation logic | Same method, cross-account flag | Same route | Same tool | Cross-account column |
| Item 60: Options-to-stock matching | Matching algorithm | Same method, config toggle | Same route | Same tool | — |
| Item 61: DRIP detection | DRIP identification | Same method, DRIP flag | Same route | Same tool | DRIP alert |
| Item 62: Auto-rebalance warnings | Schedule conflict check | `TaxService.find_wash_sales()` (alert mode) | Same route | Same tool | Alert toast |
| Item 63: Prevention alerts | Pre-trade check | `TaxService.simulate_impact()` (wash_risk field) | `POST /simulate` (wash_sale_risk field) | `simulate_tax_impact` | ⚠️ badge in What-If |

**Service layer accounting:** ✅ **Covered.** Wash sale logic feeds into two existing `TaxService` methods: `find_wash_sales()` and `scan_wash_sales()`. The REST stubs already accept the right request shapes (`WashSaleRequest`). Prevention alerts piggyback on `simulate_impact()`'s `wash_sale_risk` field.

**Gap identified:** None structural. The `zorivest_tax` MCP compound tool currently has `wash_sales` as a single action — the spec in [05h-mcp-tax.md](file:///p:/zorivest/docs/build-plan/05h-mcp-tax.md) expands this to a dedicated `find_wash_sales` tool with full parameters. The compound tool will need refactoring from 4 stub actions to 8 real tools in 3E.

#### 3C — Tax Optimization Tools → Service Layer

| Build Plan Item | Domain | Service Method | REST Route | MCP Tool | GUI |
|----------------|--------|---------------|------------|----------|-----|
| Item 64: What-If simulator | Simulation engine | `TaxService.simulate_impact()` | `POST /simulate` | `simulate_tax_impact` | What-If Simulator page |
| Item 65: Harvesting scanner | Portfolio scan | `TaxService.harvest_scan()` | `GET /harvest` | `harvest_losses` (action: `harvest`) | Loss Harvesting Tool |
| Item 66: Replacement suggestions | Securities correlation | Extension of `harvest_scan()` | Extension of `/harvest` response | Extension of `harvest_losses` | Replacement column |
| Item 67: Lot matcher UI | Lot selection logic | `TaxService.get_lots()` + `close_lot()` | `GET /lots` + `POST /lots/{id}/close` | `get_tax_lots` | Lot Detail panel |
| Item 68: Lot reassignment | T+1 window check | `TaxService.reassign_basis()` | `PUT /lots/{id}/reassign` | Included in `manage_lots` | Reassign dialog |
| Item 69: ST/LT comparison | Dollar computation | Extension of `simulate_impact()` | `hold_savings` field in `/simulate` response | `simulate_tax_impact` | Hold Savings tip |

**Service layer accounting:** ✅ **Covered.** All optimization tools map directly to methods already specified on `TaxService`. No new services needed — the optimization is purely domain-level computation exposed through existing service methods.

**Gap identified:** Minor. Item 66 (replacement suggestions) needs a correlation data source. The build plan references "correlated non-identical securities" but doesn't specify whether this is a static lookup table or uses market data. If it uses `MarketDataService`, that's a _convenience_ dependency (already built in P1.5), not a blocker.

#### 3D — Quarterly Payments & Tax Brackets → Service Layer

| Build Plan Item | Domain | Service Method | REST Route | MCP Tool | GUI |
|----------------|--------|---------------|------------|----------|-----|
| Item 70: QuarterlyEstimate entity | `QuarterlyEstimate` entity | `TaxService.quarterly_estimate()` | `GET /quarterly` | `get_quarterly_estimate` | Quarterly Tracker |
| Item 71: Annualized income | Computation fn | Extension of `quarterly_estimate()` | `estimation_method=annualized` | Same tool | Method comparison |
| Item 72: Due date tracker + penalty | Calendar logic | `TaxService.quarterly_estimate()` (penalty field) | Same route (penalty fields) | Same tool | Penalty preview |
| Item 73: Marginal rate calculator | Pure domain fn | `TaxService.estimate()` | `POST /estimate` | `estimate_tax` | Dashboard card |
| Item 74: NIIT alert | Threshold check | Extension of `estimate()` | `niit_applicable` field | Extension of `estimate_tax` | Alert badge |

**Service layer accounting:** ✅ **Covered.** `TaxService.quarterly_estimate()` and `TaxService.record_payment()` handle all quarterly logic. `TaxService.estimate()` handles bracket/rate computation. The REST routes for both are already wired.

**Gap identified:** None. This is the most self-contained sub-phase — pure computation with calendar logic.

#### 3E — Reports, Dashboard & API/MCP/GUI → Service Layer Wiring

This is where the **actual service layer swap** happens:

| Build Plan Item | What It Does | Wiring Change |
|----------------|-------------|---------------|
| Item 75 (MEU-148): Tax REST API | Activates real routes | Replaces `StubTaxService` with real `TaxService(uow)` in `main.py` lifespan |
| Item 76: Tax MCP tools | Registers 8 real tools | Replaces `zorivest_tax` 4-action stub with 8 individual tool registrations calling real REST endpoints |
| Item 77-80: Reports | Adds `ytd_summary`, `audit`, `deferred_loss`, `tax_alpha` | New service methods on `TaxService` |
| Item 81: Tax GUI | Builds 10+ React components | `TaxDashboard`, `TaxLotViewer`, `WashSaleMonitor`, `WhatIfSimulator`, `LossHarvestingTool`, `QuarterlyPaymentsTracker`, `TransactionAudit` |
| Item 82: Section toggles | Conditional feature flags | Settings toggles in `TaxProfile` |

**Service layer accounting:** ✅ **Covered — and this is the critical MEU.** MEU-148 (Item 75) is explicitly defined in [04f-api-tax.md §Service Wiring](file:///p:/zorivest/docs/build-plan/04f-api-tax.md) with a 5-step checklist:

1. Create `TaxService` in `packages/core/src/zorivest_core/services/tax_service.py`
2. Wire into lifespan (`main.py`) — replace `StubTaxService` with `TaxService(uow)`
3. Remove `StubTaxService` from `stubs.py`
4. Verify `Depends(get_tax_service)` resolves correctly
5. Add integration tests (`test_tax_service.py` + `test_tax_api.py`)

### MCP Tool Transformation (3E Detail)

The current `zorivest_tax` compound tool needs a significant refactoring in 3E:

| Current (Stub) | Target (3E) | Change |
|----------------|-------------|--------|
| 1 compound tool, 4 actions | 8 individual tools | Decompose compound → individual |
| `estimate` action | `estimate_tax` tool | Full params: tax_year, account_id, filing_status, include_unrealized |
| `wash_sales` action | `find_wash_sales` tool | Full params: account_id, ticker, date_range_start, date_range_end |
| `manage_lots` action | `get_tax_lots` tool | Full params: account_id, ticker, status, sort_by |
| `harvest` action | `harvest_losses` tool | Full params: account_id, min_loss_threshold, exclude_wash_risk |
| — (missing) | `simulate_tax_impact` tool | New: ticker, action, quantity, price, account_id, cost_basis_method |
| — (missing) | `get_quarterly_estimate` tool | New: quarter, tax_year, estimation_method |
| — (missing) | `record_quarterly_tax_payment` tool | New: quarter, tax_year, payment_amount, confirm |
| — (missing) | `get_ytd_tax_summary` tool | New: tax_year, account_id |

The [05h-mcp-tax.md](file:///p:/zorivest/docs/build-plan/05h-mcp-tax.md) spec contains **complete TypeScript implementations** for all 8 tools with Zod schemas, annotations (readOnly/destructive hints), and REST endpoint mappings.

### GUI Integration (3E Detail)

The [06g-gui-tax.md](file:///p:/zorivest/docs/build-plan/06g-gui-tax.md) spec defines **10 React components** that consume the Tax REST API:

| Component | REST Endpoints Consumed | Sub-Phase Source |
|-----------|------------------------|-----------------|
| `TaxDashboard` | `GET /ytd-summary`, `GET /harvest` | 3A (data), 3C (harvest) |
| `TaxLotViewer` | `GET /lots`, `POST /lots/{id}/close`, `PUT /lots/{id}/reassign` | 3A |
| `LotDetailPanel` | `GET /lots/{id}` | 3A |
| `WashSaleMonitor` | `GET /wash-sales`, `POST /wash-sales/scan` | 3B |
| `WashSaleChainDetail` | `GET /wash-sales/{chain_id}` | 3B |
| `WhatIfSimulator` | `POST /simulate` | 3A + 3C |
| `ScenarioComparison` | `POST /simulate` (multiple) | 3C |
| `LossHarvestingTool` | `GET /harvest`, `POST /simulate` | 3C |
| `QuarterlyPaymentsTracker` | `GET /quarterly`, `POST /quarterly/payment` | 3D |
| `TransactionAudit` | `POST /audit` | 3E (report) |

### Integration Verdict

```
┌────────────────────────────────────────────────────────────────────┐
│  SERVICE LAYER WIRING STATUS                                       │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ✅ TaxService contract defined       (03-service-layer.md)        │
│  ✅ REST routes pre-wired             (routes/tax.py — 12 routes)  │
│  ✅ DI injection point exists         (dependencies.py)            │
│  ✅ Stub service implements contract  (stubs.py — 12 methods)      │
│  ✅ MCP compound tool registered      (tax-tool.ts — 4 actions)    │
│  ✅ MCP expansion spec complete       (05h-mcp-tax.md — 8 tools)   │
│  ✅ GUI spec complete                 (06g-gui-tax.md — 10 comps)  │
│  ✅ Wiring checklist documented       (04f-api-tax.md §MEU-148)    │
│                                                                    │
│  GAPS:                                                             │
│  ⚠️  MCP compound→individual refactor needed in 3E (4→8 tools)    │
│  ⚠️  GUI has no route stub yet (no /tax page in nav rail)          │
│  ✅  Both are explicitly scoped to 3E items 76 and 81              │
│                                                                    │
│  VERDICT: No missing wiring. Staged approach is by design.         │
│  3A-3D build domain + service internals.                           │
│  3E swaps stubs with real implementations across all surfaces.     │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

> [!TIP]
> **The build plan uses a deliberate "implement internally, then wire externally" pattern.** Sub-phases 3A-3D build the `TaxService` methods incrementally — each method works and is testable via unit/integration tests against the service directly. Sub-phase 3E then "cuts over" by replacing the stub with the real service, expanding MCP tools from 4→8, and building the GUI. This means you get **full test coverage of tax logic before any UI or MCP integration risk is introduced.**

---

## MCP Audit Protocol — Tax Tool Testing ✅ RESOLVED

> [!NOTE]
> The `/mcp-audit` workflow and skill have been **extended** with Phase 2e (Tax Operations CRUD) and Phase 3c (Tax Workflow Coherence). Both phases include skip conditions that gracefully handle the current 501 stub state — they activate automatically when P3 goes live.

### Current Baseline State

From [baseline-snapshot.json](file:///p:/zorivest/.agent/skills/mcp-audit/resources/baseline-snapshot.json):

```json
"zorivest_tax": { "status": "stub", "notes": "4 actions, all return 501 — planned for future phase" }
```

The tool is registered in the `data` toolset with 4 stub actions: `estimate`, `wash_sales`, `manage_lots`, `harvest`.

### What Changes in 3E

| Aspect | Before (Current) | After (3E) |
|--------|-----------------|------------|
| Tool count | 1 compound tool | 1 compound tool with 8 actions (OR 8 individual tools — spec has both options) |
| Actions | 4 stubs (501) | 8 real actions calling live REST endpoints |
| Response shape | `{ success: false, error: "501..." }` | Full tax response envelopes with real data |
| Destructive actions | None | `record_quarterly_tax_payment` (requires confirmation token) |
| Read-only flag | `readOnlyHint: true` | Mixed: `readOnlyHint: true` for queries, `false` for mutations |

### MCP Audit Protocol Updates Required

| When | What to Update | Why |
|------|---------------|-----|
| **After 3A-3D** (domain complete, before 3E wiring) | No audit changes needed | `zorivest_tax` still returns 501 — audit correctly classifies as `stub` |
| **During 3E** (MCP tool rewrite) | Update `baseline-snapshot.json` | Change `status: "stub"` → `status: "pass"`, update action list from 4 → 8, update `total_actions` count |
| **After 3E** (tools live) | Run full `/mcp-audit` | Regression detection confirms all 8 actions return 200 with valid response shapes |

### New CRUD Test Section Needed

The `/mcp-audit` skill (§Phase 2) currently tests Accounts, Trades, Watchlists, and Email Templates. **Tax operations need a new CRUD-like test section:**

```
Phase 2e: Tax Operations (proposed addition to SKILL.md)

1. Create test account (or use existing from §2a)
2. Create test trade for that account → establishes tax lot source data
3. zorivest_tax(action: "estimate", tax_year: current_year) → verify 200 + response shape
4. zorivest_tax(action: "manage_lots", account_id: test_account) → verify lot list
5. zorivest_tax(action: "wash_sales", account_id: test_account) → verify chain list
6. zorivest_tax(action: "harvest", account_id: test_account) → verify opportunities list
7. zorivest_tax(action: "simulate", ticker: "SPY", ...) → verify simulation result
8. zorivest_tax(action: "quarterly", quarter: "Q1", ...) → verify estimate
9. zorivest_tax(action: "ytd_summary", ...) → verify summary
10. zorivest_tax(action: "record_payment", ...) → requires confirmation token → verify recording
11. Cleanup: delete test trade + account
```

### Agentic AI "Real Usage" Testing Gap

> [!WARNING]
> **The `/mcp-audit` tests tool correctness but NOT agentic reasoning quality.** An AI agent using `zorivest_tax` in production will chain multiple tools together (e.g., "What's my tax situation?" → `estimate` → `wash_sales` → `harvest` → `quarterly`). The audit verifies each tool individually but doesn't test multi-tool workflows.

**Recommendation:** After 3E is complete, add a **§Phase 3c: Tax Workflow Validation** to the MCP audit skill:

| Workflow | Tool Chain | What to Verify |
|----------|-----------|---------------|
| "Tax check-in" | `estimate` → `ytd_summary` | Summary totals match estimate inputs |
| "Pre-trade analysis" | `simulate` → `wash_sales` | Wash sale risk in simulation matches wash sale scanner output |
| "Harvesting flow" | `harvest` → `simulate` (for top candidate) | Simulation uses lots identified by scanner |
| "Quarterly planning" | `estimate` → `quarterly` → `record_payment` | Payment amount relates to estimate |

This tests the **coherence between tools** — the kind of thing that breaks when response shapes evolve independently.

### Baseline Update Checklist (3E Exit Gate)

- [ ] Update `baseline-snapshot.json`: `zorivest_tax.status` → `"pass"`
- [ ] Update `baseline-snapshot.json`: `actions_tax` → 8 actions
- [ ] Update `baseline-snapshot.json`: remove `zorivest_tax` from `known_stubs`
- [ ] Update `baseline-snapshot.json`: `total_actions` → +4 (from 74 to 78)
- [ ] Add `Phase 2e: Tax Operations` section to `SKILL.md`
- [ ] Add `Phase 3c: Tax Workflow Validation` section to `SKILL.md`
- [ ] Run `/mcp-audit` → confirm 0 regressions, `zorivest_tax` → `pass`

---

## E2E GUI Testing — Wave 11 Defined ✅ RESOLVED

> [!NOTE]
> **Wave 11 has been defined** in `06-gui.md`, `data-testid` constants added to `test-ids.ts`, `/tax` added to nav rail, and the E2E testing skill updated. The GUI Shipping Gate blocker for Item 81 is **cleared.**

### The Blocking Rule

From `06-gui.md` §GUI Shipping Gate:

> "GUI MEUs that are not yet assigned to a wave (Phase 12+ items in the priority matrix marked `Manual`) are **blocked** from implementation until their E2E wave is defined."

This applies directly to Item 81 (Tax GUI). The tax route `/tax` is already registered in the TanStack Router (`router.tsx` line 189-192), but no E2E test exercises it.

### Current Wave Schedule (Waves 0–10)

| Wave | What | Status |
|:----:|------|:------:|
| 0 | Shell + MCP Status | Active |
| 1 | Trades | Active |
| 2 | Accounts | Active |
| 3 | Backup/Restore | Active |
| 4 | Plans + Calculator | Active |
| 5 | Import | Active |
| 6 | Market Data Settings | Active |
| 7 | Home Dashboard | Active |
| 8 | Scheduling | Active |
| 9 | Screenshots | Active |
| 10 | Table Enhancements (bulk ops) | TBD |
| **11** | **Tax Estimator — NOT YET DEFINED** | ❌ **Blocked** |

### Proposed Wave 11: Tax Estimator

To unblock 3E GUI work, define **Wave 11** before starting Item 81:

| Test File | Tests | What It Verifies |
|-----------|:-----:|-----------------|
| `tax-dashboard.test.ts` | 3 | Nav to `/tax`, dashboard renders, 7 summary cards visible |
| `tax-lots.test.ts` | 2 | Lot viewer renders, sort/filter works |
| `tax-wash-sales.test.ts` | 2 | Wash sale monitor renders, chain detail expandable |
| `tax-what-if.test.ts` | 2 | Simulator form renders, computes result |
| `tax-quarterly.test.ts` | 2 | Quarterly tracker renders, payment entry works |
| **Total** | **11** | Cumulative: 52+ (41 existing + 11 new) |

### `data-testid` Constants Needed

```typescript
// Additions to ui/tests/e2e/test-ids.ts for Wave 11

// Tax Dashboard
export const TAX_PAGE = 'tax-page'
export const TAX_DASHBOARD = 'tax-dashboard'
export const TAX_SUMMARY_CARD = 'tax-summary-card'
export const TAX_YTD_TABLE = 'tax-ytd-table'
export const TAX_DISCLAIMER = 'tax-disclaimer'

// Tax Lot Viewer
export const TAX_LOT_VIEWER = 'tax-lot-viewer'
export const TAX_LOT_ROW = 'tax-lot-row'
export const TAX_LOT_CLOSE_BTN = 'tax-lot-close-btn'
export const TAX_LOT_REASSIGN_BTN = 'tax-lot-reassign-btn'

// Wash Sale Monitor
export const WASH_SALE_MONITOR = 'wash-sale-monitor'
export const WASH_SALE_CHAIN = 'wash-sale-chain'
export const WASH_SALE_CHAIN_DETAIL = 'wash-sale-chain-detail'

// What-If Simulator
export const WHAT_IF_SIMULATOR = 'what-if-simulator'
export const WHAT_IF_TICKER_INPUT = 'what-if-ticker-input'
export const WHAT_IF_RESULT = 'what-if-result'

// Loss Harvesting
export const LOSS_HARVESTING_TOOL = 'loss-harvesting-tool'
export const HARVEST_OPPORTUNITY_ROW = 'harvest-opportunity-row'

// Quarterly Payments
export const QUARTERLY_TRACKER = 'quarterly-tracker'
export const QUARTERLY_PAYMENT_INPUT = 'quarterly-payment-input'
export const QUARTERLY_PAYMENT_SUBMIT = 'quarterly-payment-submit'

// Transaction Audit
export const TX_AUDIT_PANEL = 'tx-audit-panel'
export const TX_AUDIT_FINDING_ROW = 'tx-audit-finding-row'
```

### Nav Rail Addition

The current nav rail in `06-gui.md` has 6 items (Home, Accounts, Trades, Planning, Scheduling, Settings). The tax route (`/tax`) is defined in the router but **not in the nav rail spec**. This needs to be added:

| Position | Icon | Label | Route | Shortcut |
|---|---|---|---|---|
| Top (6th, before Settings) | 💲 | Tax | `/tax` | `Ctrl+6` |

**Settings shortcut shifts:** `Ctrl+,` remains unchanged (pinned to bottom).

### Testing Strategy Summary

| Layer | P3 Sub-Phase | Test Type | Tool |
|-------|-------------|-----------|------|
| Domain | 3A-3D | Unit tests | `pytest` |
| Service | 3A-3D | Integration tests | `pytest` + in-memory SQLite |
| REST API | 3E (Item 75) | API integration tests | `pytest` + `TestClient` |
| MCP Tools | 3E (Item 76) | Unit + functional | `vitest` + `/mcp-audit` live validation |
| GUI | 3E (Item 81) | E2E | Playwright Electron (Wave 11) |
| Cross-tool coherence | Post-3E | Agentic workflow validation | `/mcp-audit` §Phase 3c |

---

## Summary

| Question | Answer |
|----------|--------|
| Can P3 be built before P2.6 Service Daemon? | ✅ Yes — tax is request-driven |
| Can P3 be built before P2.75 RoundTrip? | ✅ Yes — parallel abstractions, different bounded contexts |
| Can P3 be built before P2.75 Analytics? | ✅ Yes — completely independent |
| Can P3 be built before remaining P2 GUI? | ✅ Yes — tax GUI is self-contained |
| Are there hidden circular dependencies? | ❌ No — P3 only reads existing data, nothing reads P3 |
| Is service layer wiring accounted for? | ✅ Yes — staged approach: 3A-3D build internals, 3E wires to API/MCP/GUI |
| Does `/mcp-audit` cover tax tools? | ⚠️ Partially — needs Phase 2e (tax CRUD) + Phase 3c (workflow coherence) added to SKILL.md |
| Does `/mcp-audit` test agentic reasoning chains? | ❌ No — individual tool correctness only. Propose Phase 3c for multi-tool workflow validation |
| Are E2E GUI tests defined for tax pages? | ✅ **Yes — Wave 11 defined** (11 tests across 5 files, 23 data-testid constants) |
| Is `/tax` in the nav rail spec? | ✅ **Yes — added as Top (6th), Ctrl+6** |
| What's the main risk? | Domain completeness (options/DRIP fields) — 1-2 day pre-flight audit resolves this |
