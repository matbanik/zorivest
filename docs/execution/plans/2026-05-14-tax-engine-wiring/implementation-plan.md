---
project: "2026-05-14-tax-engine-wiring"
meus: ["MEU-148", "MEU-149", "MEU-150", "MEU-151", "MEU-152", "MEU-153"]
phase: "3E"
session: "5a — Backend + MCP"
depends_on: ["Phase 3A (MEU-123–129) ✅", "Phase 3B (MEU-130–136) ✅", "Phase 3C (MEU-137–142) ✅", "Phase 3D (MEU-143–147) ✅"]
template_version: "2.0"
---

# Implementation Plan — Phase 3E Tax Engine Wiring (Session 5a)

> **Project:** `2026-05-14-tax-engine-wiring`
> **Scope:** MEU-148 through MEU-153 (6 MEUs)
> **Type:** Service + API + MCP
> **Session:** 5a (Backend + MCP) — Session 5b covers GUI (MEU-154–156)

---

## Spec Sources

| Spec | File | Sections |
|------|------|----------|
| Tax REST API | [04f-api-tax.md](../../../build-plan/04f-api-tax.md) | §Tax Routes, §Service Wiring |
| Tax MCP Tools | [05h-mcp-tax.md](../../../build-plan/05h-mcp-tax.md) | All 8 tool specs |
| Build Matrix | [build-priority-matrix.md](../../../build-plan/build-priority-matrix.md) | §Phase 3E items 75–80 |
| Domain Model | [domain-model-reference.md](../../../build-plan/domain-model-reference.md) | TaxLot, TaxProfile, WashSaleChain |
| Emerging Standards | [emerging-standards.md](../../../../.agent/docs/emerging-standards.md) | M7 (MCP), G20 (Decimal sum) |

---

## Architecture Overview

```
Domain Layer (exists)          Service Layer (exists + new)       API Layer (wiring)        MCP Layer (wiring)
┌─────────────────────┐        ┌──────────────────────────┐      ┌───────────────────┐      ┌──────────────────┐
│ gains_calculator.py │──┐     │ TaxService               │      │ routes/tax.py     │      │ tax-tool.ts      │
│ wash_sale*.py       │──┤     │ ├ get_lots()       ✅    │      │ 12 routes (exist) │      │ 4 stubs → 8 real │
│ lot_selector.py     │──┤     │ ├ simulate_impact() ✅   │      │ StubTaxService →  │      │                  │
│ quarterly.py        │──┤ ──▶ │ ├ quarterly_estimate() ✅│ ◀─── │   real TaxService │ ◀─── │ REST proxy calls │
│ harvest_scanner.py  │──┤     │ ├ ytd_summary()    🆕   │      │                   │      │                  │
│ tax_simulator.py    │──┤     │ ├ deferred_loss()  🆕   │      │ +2 new routes     │      │                  │
│ ytd_pnl.py          │──┤     │ ├ tax_alpha()      🆕   │      │ (deferred, alpha) │      │                  │
│ brackets.py         │──┘     │ ├ run_audit()      🆕   │      └───────────────────┘      └──────────────────┘
│ niit.py             │        │ └ record_payment()  🆕   │
└─────────────────────┘        └──────────────────────────┘
```

---

## Execution Order

| Order | MEU | Slug | Scope | Depends On |
|-------|-----|------|-------|------------|
| 1 | MEU-150 | `tax-year-end` | Service method: `ytd_summary()` | get_ytd_pnl ✅, get_taxable_gains ✅ |
| 2 | MEU-151 | `tax-deferred-loss` | Service method: `deferred_loss_report()` | get_trapped_losses ✅ |
| 3 | MEU-152 | `tax-alpha` | Service method: `tax_alpha_report()` | gains_calculator ✅, lot_selector ✅ |
| 4 | MEU-153 | `tax-audit` | Service method: `run_audit()` | tax_lots repo ✅, trades repo ✅ |
| 5 | MEU-148 | `tax-api-wiring` | Route adapter + stub retirement | MEU-150–153 ✅ |
| 6 | MEU-149 | `tax-mcp-wiring` | 8 real MCP tools | MEU-148 ✅ |

---

## Boundary Input Contract

### REST Write Surfaces (MEU-148)

| Boundary | Pydantic Model | Key Field Constraints | Extra-Field Policy | Error Mapping |
|----------|---------------|----------------------|--------------------|---------------|
| `POST /simulate` body | `SimulateTaxRequest` | `ticker: str` (1–10 chars uppercase), `quantity: float` (>0), `proposed_price: float` (>0), `account_id: str` (optional) | `extra="forbid"` | 422 `RequestValidationError` |
| `POST /estimate` body | `EstimateTaxRequest` | `tax_year: int` (2000–2099), `additional_income: float` (≥0), `additional_deductions: float` (≥0), `account_id: str` (optional) | `extra="forbid"` | 422 `RequestValidationError` |
| `POST /wash-sales` body | `WashSaleRequest` | `ticker: str` (optional, 1–10 chars), `account_id: str` (optional), `include_potential: bool` (default false) | `extra="forbid"` | 422 `RequestValidationError` |
| `POST /quarterly/payment` body | `RecordPaymentRequest` | `quarter: str` (enum: "Q1"–"Q4"), `payment_amount: float` (>0), `tax_year: int` (2000–2099), `confirm: bool` (must be true; 400 when false), `payment_date: str` (ISO date, optional) | `extra="forbid"` | 422 `RequestValidationError` |
| `GET /lots` query | Path/query params | `account_id: str` (optional), `ticker: str` (optional), `is_closed: bool` (optional) | N/A (query params) | 422 on invalid types |
| `GET /deferred-losses` query | Query params | `tax_year: int` (optional, 2000–2099) | N/A | 422 on invalid type |
| `GET /alpha` query | Query params | `tax_year: int` (required, 2000–2099) | N/A | 422 on invalid type |

**Create/Update Parity:** `record_payment` is create-only (no update path). All POST bodies use `extra="forbid"`. `record_payment` requires `confirm=true`; returns 400 when `confirm` is false (per 04f-api-tax.md line 134).

### MCP Input Surfaces (MEU-149)

| Boundary | Zod Schema | Key Constraints | Strict Mode | Error Mapping |
|----------|-----------|-----------------|-------------|---------------|
| `simulate` action | `SimulateInput` | `ticker: z.string().min(1).max(10)`, `quantity: z.number().positive()`, `proposed_price: z.number().positive()` | `.strict()` | Zod parse error → user-facing message |
| `estimate` action | `EstimateInput` | `tax_year: z.number().int().min(2000).max(2099)` | `.strict()` | Zod parse error → user-facing message |
| `wash_sales` action | `WashSalesInput` | `ticker: z.string().optional()`, `include_potential: z.boolean().default(false)` | `.strict()` | Zod parse error → user-facing message |
| `record_payment` action | `RecordPaymentInput` | `quarter: z.enum(["Q1","Q2","Q3","Q4"])`, `payment_amount: z.number().positive()`, `tax_year: z.number().int()`, `confirm: z.literal(true)` | `.strict()` | Zod parse error → user-facing message |
| `lots` action | `LotsInput` | `account_id: z.string().optional()`, `ticker: z.string().optional()` | `.strict()` | Zod parse error → user-facing message |
| `quarterly` action | `QuarterlyInput` | `tax_year: z.number().int()`, `quarter: z.enum(["Q1","Q2","Q3","Q4"])`, `estimation_method: z.string().default("annualized").optional()` | `.strict()` | Zod parse error → user-facing message |
| `harvest` action | `HarvestInput` | `account_id: z.string().optional()` | `.strict()` | Zod parse error → user-facing message |
| `ytd_summary` action | `YtdSummaryInput` | `tax_year: z.number().int()`, `account_id: z.string().optional()` | `.strict()` | Zod parse error → user-facing message |

---

## MEU-150: Year-End Tax Position Summary

> **Matrix Item:** 77 | **Build Plan:** [build-priority-matrix.md §3E](../../../build-plan/build-priority-matrix.md)
> **Spec Source:** 04f-api-tax.md §ytd-summary, 05h-mcp-tax.md §get_ytd_tax_summary

### Acceptance Criteria

| AC | Description | Source |
|----|-------------|--------|
| AC-150.1 | `ytd_summary()` method on TaxService accepts `tax_year: int` and optional `account_id: str \| None` | Spec: 04f-api-tax.md line 156–159 |
| AC-150.2 | Returns `YtdTaxSummary` dataclass with fields: `realized_st_gain`, `realized_lt_gain`, `total_realized`, `wash_sale_adjustments`, `trades_count`, `estimated_federal_tax`, `estimated_state_tax`, `quarterly_payments` | Spec: 05h-mcp-tax.md lines 397–404 |
| AC-150.3 | Composes `get_ytd_pnl()` for per-symbol breakdown, `get_taxable_gains()` for aggregate ST/LT, `get_trapped_losses()` for wash adjustments | Local Canon: existing TaxService methods |
| AC-150.4 | Tax estimates use `compute_tax_liability()` from brackets.py + NIIT threshold check | Local Canon: MEU-146 (marginal_tax_calc), MEU-147 (niit_alert) |
| AC-150.5 | Quarterly payments section shows Q1–Q4 status with required/paid/due per quarter | Spec: 05h-mcp-tax.md line 404 |
| AC-150.6 | Empty portfolio returns zeroed summary (no errors) | Local Canon: established empty-result pattern (see TaxService.get_ytd_pnl empty return) |

### Implementation

- **File:** `packages/core/src/zorivest_core/services/tax_service.py`
- **Test file:** `tests/unit/test_tax_ytd_summary.py`
- **Result type:** `YtdTaxSummary` dataclass (frozen)

---

## MEU-151: Deferred Loss Carryover Report

> **Matrix Item:** 78 | **Build Plan:** [build-priority-matrix.md §3E](../../../build-plan/build-priority-matrix.md)

### Acceptance Criteria

| AC | Description | Source |
|----|-------------|--------|
| AC-151.1 | `deferred_loss_report()` method on TaxService accepts optional `tax_year: int` | Spec: build-priority-matrix.md item 78 |
| AC-151.2 | Returns `DeferredLossReport` dataclass with fields: `trapped_chains[]` (per chain: loss_lot_id, original_loss, deferred_amount, replacement_lot_id, chain_status), `total_deferred`, `total_permanent_loss` (IRA-destroyed chains) | Spec: domain-model-reference.md L353–366 (TaxLot fields), build-priority-matrix item 78 (deferred loss report fields) |
| AC-151.3 | Uses `get_trapped_losses()` to load ABSORBED chains, enriches with lot details | Local Canon: TaxService.get_trapped_losses() |
| AC-151.4 | Computes `real_pnl` vs `reported_pnl` delta: reported = realized gains – deferred losses | Spec: build-priority-matrix.md "Real P&L vs reported P&L" |
| AC-151.5 | Empty result when no trapped chains (no errors) | Local Canon: established empty-result pattern |

### Implementation

- **File:** `packages/core/src/zorivest_core/services/tax_service.py`
- **Test file:** `tests/unit/test_tax_deferred_loss.py`
- **Result type:** `DeferredLossReport` dataclass (frozen)

---

## MEU-152: Tax Alpha Savings Summary

> **Matrix Item:** 79 | **Build Plan:** [build-priority-matrix.md §3E](../../../build-plan/build-priority-matrix.md)

### Acceptance Criteria

| AC | Description | Source |
|----|-------------|--------|
| AC-152.1 | `tax_alpha_report()` method on TaxService accepts `tax_year: int` | Spec: build-priority-matrix.md item 79 |
| AC-152.2 | Returns `TaxAlphaReport` dataclass with fields: `actual_tax_estimate`, `naive_fifo_tax_estimate`, `tax_savings`, `savings_from_lot_optimization`, `savings_from_harvesting`, `trades_optimized_count` | Spec: "YTD savings from lot optimization + loss harvesting" |
| AC-152.3 | Computes counterfactual: re-calculates all closed lots as if FIFO were used, then compares actual realized tax vs FIFO-default tax | Spec: build-priority-matrix item 79 "YTD savings from lot optimization + loss harvesting"; Local Canon: gains_calculator.py FIFO lot selection |
| AC-152.4 | Harvesting savings = sum of losses from harvest_scanner results that were actually executed | Local Canon: harvest_scanner.py results |
| AC-152.5 | When no closed lots exist, returns zeroed report (no errors) | Local Canon: established empty-result pattern |

### Implementation

- **File:** `packages/core/src/zorivest_core/services/tax_service.py`
- **Test file:** `tests/unit/test_tax_alpha.py`
- **Result type:** `TaxAlphaReport` dataclass (frozen)

---

## MEU-153: Error Check / Transaction Audit

> **Matrix Item:** 80 | **Build Plan:** [build-priority-matrix.md §3E](../../../build-plan/build-priority-matrix.md)
> **Spec Source:** 04f-api-tax.md §Transaction audit

### Acceptance Criteria

| AC | Description | Source |
|----|-------------|--------|
| AC-153.1 | `run_audit()` method on TaxService accepts optional `account_id: str \| None` and `tax_year: int \| None` | Spec: 04f-api-tax.md lines 196–206 |
| AC-153.2 | Returns `AuditReport` dataclass with `findings[]` and `severity_summary` (error/warning/info counts) | Spec: StubTaxService.run_audit() return shape |
| AC-153.3 | Checks for missing basis: lots with `cost_basis == 0` or `cost_basis is None` → severity: error | Spec: 04f-api-tax.md §Transaction audit "missing basis" check; Local Canon: TaxLot.cost_basis field (entities.py:210) |
| AC-153.4 | Checks for duplicate lots: same `account_id + ticker + open_date + quantity` → severity: warning | Local Canon: duplicate detection pattern (lot uniqueness: account_id + ticker + open_date + quantity) |
| AC-153.5 | Checks for orphaned lots: closed lots with no `linked_trade_ids` → severity: warning | Local Canon: lot-trade linking pattern |
| AC-153.6 | Checks for negative/zero proceeds on closed lots → severity: error | Local Canon: TaxLot.proceeds field (entities.py:211) — zero/negative proceeds on closed lot is logically invalid |
| AC-153.7 | Each finding includes: `finding_type`, `severity`, `message`, `lot_id`, `details` | Spec: StubTaxService contract shape |

### Implementation

- **File:** `packages/core/src/zorivest_core/services/tax_service.py`
- **Test file:** `tests/unit/test_tax_audit.py`
- **Result types:** `AuditFinding` dataclass, `AuditReport` dataclass (frozen)

---

## MEU-148: Tax REST API Wiring

> **Matrix Item:** 75 | **Build Plan:** [04f-api-tax.md §Service Wiring](../../../build-plan/04f-api-tax.md)

### Acceptance Criteria

| AC | Description | Source |
|----|-------------|--------|
| AC-148.1 | Replace `StubTaxService()` with real `TaxService(uow)` in `main.py` lifespan | Spec: 04f-api-tax.md §Wiring Tasks item 2 |
| AC-148.2 | Remove `StubTaxService` class from `stubs.py` and all imports | Spec: 04f-api-tax.md §Wiring Tasks item 3 |
| AC-148.3 | Route handlers unpack Pydantic request bodies to match TaxService method signatures (e.g., `body.ticker`, `body.quantity` → individual params) | Local Canon: route → service parameter bridging pattern used in other routes |
| AC-148.4 | All 12 existing tax routes return real data instead of stub defaults | Spec: 04f-api-tax.md §Tax Routes |
| AC-148.5 | Add 2 new routes for deferred-loss and tax-alpha reports: `GET /api/v1/tax/deferred-losses`, `GET /api/v1/tax/alpha` | Spec: build-priority-matrix items 78–79 |
| AC-148.6 | `record_payment()` endpoint writes to persistence (remove NotImplementedError from TaxService) | Spec: 04f-api-tax.md line 131–137 |
| AC-148.7 | Route-level integration tests verify real service responses (not stub defaults) | Spec: 04f-api-tax.md §Verification |
| AC-148.8 | `Depends(get_tax_service)` dependency resolves to real TaxService | Spec: 04f-api-tax.md §Wiring Tasks item 4 |
| AC-148.9 | Quarter string conversion: API accepts "Q1"–"Q4" strings, service accepts int 1–4 → route converts | Local Canon: quarterly_estimate() takes int quarter |

### Implementation

- **Files:** `packages/api/src/zorivest_api/main.py`, `routes/tax.py`, `stubs.py`, `dependencies.py`
- **Test file:** `tests/integration/test_tax_routes.py`

### record_payment Persistence

The real `TaxService.record_payment()` currently raises `NotImplementedError`. For MEU-148:

**Design:** Use the existing `QuarterlyEstimate` entity (domain) + `QuarterlyEstimateRepository` protocol (ports), which already have the `actual_payment` field and `save`/`update`/`get_for_quarter` methods. The infrastructure layer needs implementation.

**Implementation steps:**
1. **Infra model:** Add `QuarterlyEstimateModel` to `packages/infrastructure/src/zorivest_infra/database/models.py`
2. **Infra repo:** Add `SqlQuarterlyEstimateRepository` to `packages/infrastructure/src/zorivest_infra/database/` (or extend `tax_repository.py`)
3. **UoW wiring:** Register `quarterly_estimates` on `SqlUnitOfWork` in `unit_of_work.py`
4. **DB init:** Add `QuarterlyEstimateModel` to `Base.metadata.create_all()` path in `database_init.py`
5. **Service logic:** `record_payment()` calls `uow.quarterly_estimates.get_for_quarter(tax_year, quarter)` → if exists, update `actual_payment`; if not, create new `QuarterlyEstimate` with the payment amount and save via `uow.quarterly_estimates.save()`
6. **Integration test:** Verify payment survives a new UoW session

**Files touched (in addition to existing plan):**
- `packages/infrastructure/src/zorivest_infra/database/models.py` (new model)
- `packages/infrastructure/src/zorivest_infra/database/tax_repository.py` (new repo class)
- `packages/infrastructure/src/zorivest_infra/database/unit_of_work.py` (UoW wiring)
- `packages/infrastructure/src/zorivest_infra/database/database_init.py` (table creation)

> Source: `QuarterlyEstimate` entity at `entities.py:270–286`, `QuarterlyEstimateRepository` protocol at `ports.py:446–468`, `UnitOfWork.quarterly_estimates` at `ports.py:334`.

---

## MEU-149: Tax MCP Tool Wiring

> **Matrix Item:** 76 | **Build Plan:** [05h-mcp-tax.md](../../../build-plan/05h-mcp-tax.md)

### Acceptance Criteria

| AC | Description | Source |
|----|-------------|--------|
| AC-149.1 | Replace 4 stub actions with 8 real actions in `zorivest_tax` compound tool | Spec: 05h-mcp-tax.md (all 8 tools) |
| AC-149.2 | Actions: `simulate`, `estimate`, `wash_sales`, `lots`, `quarterly`, `record_payment`, `harvest`, `ytd_summary` | Spec: 05h-mcp-tax.md tool names mapped to compound actions |
| AC-149.3 | Each action proxies to the corresponding REST endpoint with proper method (GET/POST) and parameter marshalling | Spec: 05h-mcp-tax.md §REST Dependency per tool |
| AC-149.4 | Zod schemas match the Pydantic request schemas in tax routes (field names, types, defaults) | Spec: 05h-mcp-tax.md input schemas |
| AC-149.5 | Tool annotations set per spec: readOnlyHint, destructiveHint, idempotentHint | Spec: 05h-mcp-tax.md §Annotations per tool |
| AC-149.6 | `record_payment` action marked destructiveHint=true, requires `confirm: true` | Spec: 05h-mcp-tax.md line 295–303 |
| AC-149.7 | Tax disclaimer from `TaxResponseEnvelope.disclaimer` included in MCP response text | Spec: 05h-mcp-tax.md line 53–54 |
| AC-149.8 | Update `seed.ts` tool description from "4 stub actions" to "8 real actions" | Local Canon: seed.ts line 90 |
| AC-149.9 | Update `client-detection.ts` server instructions to describe real tax tools | Local Canon: client-detection.ts line 146 |
| AC-149.10 | All 8 actions return real data (not 501) when backend is running | Spec: retirement of 501 stubs |

### Implementation

- **Files:** `mcp-server/src/compound/tax-tool.ts`, `mcp-server/src/toolsets/seed.ts`, `mcp-server/src/client-detection.ts`
- **Test file:** `mcp-server/src/__tests__/tax-tool.test.ts` (Vitest)
- **Pattern:** Follow existing compound tools (account-tool.ts, market-tool.ts) for REST proxy pattern

---

## Verification Plan

```bash
# MEU-150–153: Domain method tests
uv run pytest tests/unit/test_tax_ytd_summary.py tests/unit/test_tax_deferred_loss.py tests/unit/test_tax_alpha.py tests/unit/test_tax_audit.py -x --tb=short -v *> C:\Temp\zorivest\pytest-reports.txt; Get-Content C:\Temp\zorivest\pytest-reports.txt | Select-Object -Last 40

# MEU-148: API integration tests
uv run pytest tests/integration/test_tax_routes.py -x --tb=short -v *> C:\Temp\zorivest\pytest-api.txt; Get-Content C:\Temp\zorivest\pytest-api.txt | Select-Object -Last 40

# MEU-149: MCP tool tests
cd mcp-server && npx vitest run src/__tests__/tax-tool.test.ts *> C:\Temp\zorivest\vitest-mcp.txt; Get-Content C:\Temp\zorivest\vitest-mcp.txt | Select-Object -Last 30

# Full regression
uv run pytest tests/ -x --tb=short -v *> C:\Temp\zorivest\pytest-full.txt; Get-Content C:\Temp\zorivest\pytest-full.txt | Select-Object -Last 40

# Type check
uv run pyright packages/ *> C:\Temp\zorivest\pyright.txt; Get-Content C:\Temp\zorivest\pyright.txt | Select-Object -Last 30

# Lint
uv run ruff check packages/ *> C:\Temp\zorivest\ruff.txt; Get-Content C:\Temp\zorivest\ruff.txt | Select-Object -Last 20

# Anti-placeholder scan
rg "TODO|FIXME|NotImplementedError" packages/core/src/zorivest_core/services/tax_service.py packages/api/src/zorivest_api/routes/tax.py mcp-server/src/compound/tax-tool.ts *> C:\Temp\zorivest\placeholder.txt; Get-Content C:\Temp\zorivest\placeholder.txt
```

---

## Risk Register

| Risk | Impact | Mitigation |
|------|--------|------------|
| Route body → service param mismatch | High — runtime errors | Unpack in route handler, test each endpoint |
| record_payment persistence approach | Medium — new infra model required | Use QuarterlyEstimate entity + QuarterlyEstimateRepository (domain layer exists; infra model/repo/UoW wiring planned in task 13b). Risk: table creation must be verified in database_init.py. |
| MCP Zod schema drift from Pydantic | Medium — 422 errors | Cross-reference 05h-mcp-tax.md schemas with routes |
| Existing test regressions from stub retirement | High — cascading failures | Run full pytest suite after each MEU |
| G20 (Decimal sum start) | Low — pyright error | Apply pattern: `sum(decimals, start=Decimal("0"))` |

---

## Ad-Hoc: TAX-DBMIGRATION — Inline Schema Migration for tax_lots

> **Known Issue:** [TAX-DBMIGRATION](../../../../.agent/context/known-issues.md)
> **Discovered:** 2026-05-14 (MCP audit v4)
> **Severity:** High — blocks 4 of 8 tax endpoints at runtime

### Problem

The `TaxLotModel` ORM class (models.py:879–887) defines 3 columns that were added during Phase 3B/3C implementation but **no inline migration was added** to backfill them on existing databases:

| Column | Type | Model Line | Purpose |
|--------|------|-----------|---------|
| `cost_basis_method` | `String(30), nullable=True` | models.py:879 | Per-lot cost basis method override (CostBasisMethod enum) |
| `realized_gain_loss` | `Numeric(15,6), nullable=False, default=0` | models.py:882 | Computed gain/loss on lot close |
| `acquisition_source` | `String(20), nullable=True` | models.py:885 | AcquisitionSource enum (MEU-134) |

**Symptom:** SQLAlchemy queries against `tax_lots` throw `OperationalError: no such column: tax_lots.cost_basis_method`, causing 500 errors on `estimate`, `lots`, `simulate`, and `ytd_summary` endpoints.

**Why it matters:** `Base.metadata.create_all()` correctly creates these columns on **new** databases. But any existing `zorivest.db` (created before Phase 3B) lacks these columns. The project uses **inline ALTER TABLE migrations** (main.py:243–253) — not Alembic — to handle schema evolution.

### Root Cause

The Phase 3B/3C implementation (MEU-130–136) added the columns to the ORM model and repository mapper but did not add corresponding `ALTER TABLE` statements to the `_inline_migrations` list in `main.py`.

### Fix Approach

Add 3 `ALTER TABLE` statements to `_inline_migrations` in `packages/api/src/zorivest_api/main.py` (line ~253), following the existing pattern:

```python
# ── Schema migrations (no Alembic) ────────────────────────────────
_inline_migrations = [
    # ... existing migrations ...
    "ALTER TABLE market_quotes ADD COLUMN change_pct REAL",  # Yahoo v8 quote
    # TAX-DBMIGRATION: 3 columns added to TaxLotModel in Phase 3B/3C
    "ALTER TABLE tax_lots ADD COLUMN cost_basis_method VARCHAR(30)",
    "ALTER TABLE tax_lots ADD COLUMN realized_gain_loss NUMERIC(15,6) DEFAULT 0 NOT NULL",
    "ALTER TABLE tax_lots ADD COLUMN acquisition_source VARCHAR(20)",
]
```

The existing try/except pattern (line 256–261) handles idempotency — if columns already exist (fresh DB), the `ALTER TABLE` silently fails with "duplicate column name" and the rollback is benign.

### Acceptance Criteria

| AC | Description | Source |
|----|-------------|--------|
| AC-MIG.1 | `_inline_migrations` list in `main.py` includes ALTER TABLE for `cost_basis_method`, `realized_gain_loss`, `acquisition_source` | Known Issue: TAX-DBMIGRATION |
| AC-MIG.2 | After backend restart, `zorivest_tax(action: "lots")` returns 200 (not 500) | MCP Audit v4 finding I-1/I-2 |
| AC-MIG.3 | After backend restart, `zorivest_tax(action: "estimate")` returns 200 (not 500) | MCP Audit v4 finding I-1 |
| AC-MIG.4 | After backend restart, `zorivest_tax(action: "simulate", ...)` returns 200 (not 500) | MCP Audit v4 finding I-3 |
| AC-MIG.5 | After backend restart, `zorivest_tax(action: "ytd_summary")` returns 200 (not 500) | MCP Audit v4 finding I-4 |
| AC-MIG.6 | Fresh database (delete zorivest.db, restart) still creates all columns via `create_all` | Regression: existing behavior preserved |
| AC-MIG.7 | Existing database with columns already present does not error on startup (idempotent) | Regression: inline migration try/except pattern |

### Migration Regression Test (Red Phase — FAIL_TO_PASS)

> Source: AGENTS.md §Bug-Fix TDD Protocol — failing test before production code change.

A dedicated integration test at `tests/integration/test_inline_migrations.py` must:

1. **Create an old-shape `tax_lots` table** in a temporary SQLite database with only the 11 original columns (lot_id, account_id, ticker, open_date, close_date, quantity, cost_basis, proceeds, wash_sale_adjustment, is_closed, linked_trade_ids) — deliberately omitting `cost_basis_method`, `realized_gain_loss`, `acquisition_source`.
2. **Extract and run the inline migration logic** from `main.py` (the `_inline_migrations` list + try/except loop) against the old-shape database.
3. **Assert all 3 columns exist** after migration by querying `PRAGMA table_info(tax_lots)` and checking for `cost_basis_method`, `realized_gain_loss`, `acquisition_source`.
4. **Assert idempotency** — run the migration logic a second time against the same database and verify no errors are raised and column count remains stable.
5. **Assert fresh-DB path** — create a fresh database via `Base.metadata.create_all()` and verify all 3 columns exist without needing the ALTER TABLE migration (AC-MIG.6).

**Red phase evidence:** The test must FAIL before the `_inline_migrations` change is applied (the ALTER TABLE statements don't exist yet, so the old-shape DB won't gain the columns). After adding the 3 statements, the test passes (Green phase).

### Implementation

- **Migration file:** `packages/api/src/zorivest_api/main.py` — append 3 ALTER TABLE statements to `_inline_migrations` list (after line 252)
- **Test file:** `tests/integration/test_inline_migrations.py` — Red-phase migration regression test (write FIRST)
- **Regression:** Full pytest suite must remain green (tests use in-memory DBs with `create_all`)

### Verification Plan

```bash
# 1. RED PHASE — write test, confirm failure before code change
uv run pytest tests/integration/test_inline_migrations.py -x --tb=short -v *> C:\Temp\zorivest\pytest-migration-red.txt; Get-Content C:\Temp\zorivest\pytest-migration-red.txt | Select-Object -Last 30

# 2. GREEN PHASE — apply migration to main.py, re-run test
uv run pytest tests/integration/test_inline_migrations.py -x --tb=short -v *> C:\Temp\zorivest\pytest-migration-green.txt; Get-Content C:\Temp\zorivest\pytest-migration-green.txt | Select-Object -Last 30

# 3. Verify previously-failing endpoints via REST (backend must be running)
Invoke-RestMethod -Uri "http://127.0.0.1:17787/api/v1/tax/lots?account_id=99bb9b00-fc7a-44cf-b816-a6bb4dabfaca" -Method GET *> C:\Temp\zorivest\mig-lots.txt; Get-Content C:\Temp\zorivest\mig-lots.txt | Select-Object -Last 20
Invoke-RestMethod -Uri "http://127.0.0.1:17787/api/v1/tax/estimate" -Method POST -ContentType "application/json" -Body '{"tax_year":2026,"account_id":"99bb9b00-fc7a-44cf-b816-a6bb4dabfaca"}' *> C:\Temp\zorivest\mig-estimate.txt; Get-Content C:\Temp\zorivest\mig-estimate.txt | Select-Object -Last 20
Invoke-RestMethod -Uri "http://127.0.0.1:17787/api/v1/tax/simulate" -Method POST -ContentType "application/json" -Body '{"ticker":"MSFT","quantity":50,"proposed_price":420,"account_id":"99bb9b00-fc7a-44cf-b816-a6bb4dabfaca"}' *> C:\Temp\zorivest\mig-simulate.txt; Get-Content C:\Temp\zorivest\mig-simulate.txt | Select-Object -Last 20
Invoke-RestMethod -Uri "http://127.0.0.1:17787/api/v1/tax/ytd-summary?tax_year=2026" -Method GET *> C:\Temp\zorivest\mig-ytd.txt; Get-Content C:\Temp\zorivest\mig-ytd.txt | Select-Object -Last 20

# 4. Full regression
uv run pytest tests/ -x --tb=short -v *> C:\Temp\zorivest\pytest-migration.txt; Get-Content C:\Temp\zorivest\pytest-migration.txt | Select-Object -Last 40
```
