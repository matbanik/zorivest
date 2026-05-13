---
project: "2026-05-12-tax-logic-expansion"
date: "2026-05-12"
source: "docs/build-plan/03-service-layer.md §TaxService, build-priority-matrix.md items 52-53"
meus: ["MEU-125", "MEU-126"]
status: "draft"
template_version: "2.0"
---

# Implementation Plan: Tax Logic Expansion

> **Project**: `2026-05-12-tax-logic-expansion`
> **Build Plan Section(s)**: 03-service-layer.md §TaxService, build-priority-matrix.md items 52 (tax lot tracking) and 53 (gains calculator)
> **Status**: `draft`

---

## Goal

Implement the tax calculation service layer — the computational engine that operates on the TaxLot and TaxProfile entities established in MEU-123/124 (Phase 3A). MEU-125 provides core lot management (open/close, cost basis method selection with IBKR Tax Optimizer 4-tier priority matching). MEU-126 provides ST/LT classification, gains calculation, and TaxService orchestration including pre-trade what-if simulation.

These two MEUs complete the foundational service layer needed before:
- Phase 3B (wash sale engine: MEU-130+)
- Phase 3C (tax optimization tools: harvesting, what-if simulation)
- Phase 3E (tax API routes: MEU-148)

---

## Proposed Changes

### MEU-125: TaxLotTracking (item 52)

#### Boundary Inventory

No external input surfaces. This MEU implements internal service-layer logic only. All external boundaries (REST body, MCP input) are defined in MEU-148 (04f-api-tax.md) and will be validated there.

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-125.1 | `TaxService.__init__(uow)` — constructor takes UnitOfWork | Spec: 03-service-layer.md L348 | N/A (internal) |
| AC-125.2 | `get_lots(account_id, ticker, status, sort_by)` returns filtered, sorted TaxLot list | Spec: 04f-api-tax.md L107-115, 03-service-layer.md L363-365 | Empty result when no lots match |
| AC-125.3 | `close_lot(lot_id, sell_trade_id)` looks up the sell trade via UoW to derive sale_price, close_date, and closed_quantity; sets lot.close_date, lot.proceeds, lot.is_closed=True; computes realized gain/loss | Spec: 04f-api-tax.md L167-173, domain-model-reference.md A3 ("Every sale closes lots"). Data source: sell trade imported via broker adapter (Zorivest imports trades, never executes). | NotFoundError when lot_id invalid; NotFoundError when sell_trade_id invalid; BusinessRuleError when lot already closed; BusinessRuleError when sell trade ticker != lot ticker |
| AC-125.4 | `reassign_basis(lot_id, method)` changes cost basis method within T+1 window | Spec: 04f-api-tax.md L175-180, domain-model-reference.md C5 | BusinessRuleError when outside T+1 window |
| AC-125.5 | `select_lots_for_closing(lots, quantity, method, sale_price)` pure domain function implements all 8 cost basis methods correctly. Requires `sale_price` input for MAX_* methods to compute per-lot gain/loss for priority ranking. | Spec: domain-model-reference.md A1 (8 methods), Research-backed: IBKR lot-matching-methods.htm | ValueError when quantity exceeds total open lot quantity |
| AC-125.6 | FIFO selects oldest lots first; LIFO selects newest first; HIFO selects highest cost basis first | Spec: domain-model-reference.md A1 | Deterministic ordering verified with equal-date lots |
| AC-125.7 | MAX_LT_GAIN (MLG) 4-tier priority: ① Maximize LT gain/share → ② If no LT gain lots: maximize ST gain/share → ③ If no gain lots: minimize ST loss/share → ④ If no ST loss lots: minimize LT loss/share | Research-backed: IBKR lot-matching-methods.htm (ibkrguides.com) | Empty LT lots triggers tier 2; no gain lots triggers tier 3; single lot with loss correctly selected |
| AC-125.8 | MAX_LT_LOSS (MLL) 4-tier priority: ① Maximize LT loss/share → ② If no LT loss lots: maximize ST loss/share → ③ If no loss lots: minimize ST gain/share → ④ If no ST gain lots: minimize LT gain/share | Research-backed: IBKR lot-matching-methods.htm (ibkrguides.com) | Mirror of MLG tier tests |
| AC-125.9 | MAX_ST_GAIN (MSG) 4-tier priority: ① Maximize ST gain/share → ② If no ST gain lots: maximize LT gain/share → ③ If no gain lots: minimize LT loss/share → ④ If no LT loss lots: minimize ST loss/share | Research-backed: IBKR lot-matching-methods.htm (ibkrguides.com) | Mirror of MLG tier tests with ST/LT swapped |
| AC-125.10 | MAX_ST_LOSS (MSL) 4-tier priority: ① Maximize ST loss/share → ② If no ST loss lots: maximize LT loss/share → ③ If no loss lots: minimize LT gain/share → ④ If no LT gain lots: minimize ST gain/share | Research-backed: IBKR lot-matching-methods.htm (ibkrguides.com) | Mirror of MLL tier tests with ST/LT swapped |
| AC-125.11 | SPEC_ID requires explicit lot_ids parameter; raises ValueError if not provided | Spec: domain-model-reference.md C4 | ValueError when lot_ids omitted or empty |

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| 8 cost basis method names | Spec | domain-model-reference.md L395-397 |
| FIFO/LIFO/HIFO sort order | Spec | Standard financial definitions |
| MAX_LT_GAIN 4-tier priority | Research-backed | IBKR lot-matching-methods.htm: Maximize LT gain → Max ST gain → Min ST loss → Min LT loss |
| MAX_LT_LOSS 4-tier priority | Research-backed | IBKR lot-matching-methods.htm: Maximize LT loss → Max ST loss → Min ST gain → Min LT gain |
| MAX_ST_GAIN 4-tier priority | Research-backed | IBKR lot-matching-methods.htm: Maximize ST gain → Max LT gain → Min LT loss → Min ST loss |
| MAX_ST_LOSS 4-tier priority | Research-backed | IBKR lot-matching-methods.htm: Maximize ST loss → Max LT loss → Min LT gain → Min ST gain |
| sale_price required for MAX_* | Research-backed | IBKR methods compute gain/loss per lot to rank candidates; requires knowing sale proceeds |
| ST/LT boundary (366 days) | Spec | domain-model-reference.md A2, L365 |
| T+1 settlement window | Spec | domain-model-reference.md C5 |
| close_lot data source = sell trade | Spec | domain-model-reference.md A3 ("Every sale closes lots"), 04f-api-tax.md L167-173 (lot_id-only API → service derives from linked trade). Zorivest imports trade results (AGENTS.md: "never places, modifies, or cancels orders"). |
| Partial close (quantity < lot.quantity) | Spec | Implied by lot_selector returning partial fills. Creates split lot. |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `packages/core/src/zorivest_core/domain/tax/__init__.py` | new | Package init for tax domain module |
| `packages/core/src/zorivest_core/domain/tax/lot_selector.py` | new | Pure domain function: `select_lots_for_closing()` with 8 cost basis methods (IBKR 4-tier) |
| `packages/core/src/zorivest_core/services/tax_service.py` | new | TaxService class with `get_lots`, `close_lot`, `reassign_basis` |
| `tests/unit/test_lot_selector.py` | new | ~30 tests for 8 cost basis methods + 4-tier priority edge cases |
| `tests/unit/test_tax_service.py` | new | ~10 tests with mocked UoW for lot management methods |

---

### MEU-126: TaxGainsCalc (item 53)

#### Boundary Inventory

No external input surfaces. This MEU implements internal service-layer logic only.

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-126.1 | `calculate_realized_gain(lot, sale_price)` pure domain function returns `RealizedGainResult` with gain/loss amount, ST/LT classification, holding_period_days | Spec: domain-model-reference.md A2, A5 (366-day boundary) | Returns zero gain for cost_basis == sale_price |
| AC-126.2 | `RealizedGainResult` frozen dataclass with: gain_amount (Decimal), is_long_term (bool), holding_period_days (int), tax_type ("short_term" \| "long_term") | Local Canon: follows existing frozen dataclass patterns | N/A (dataclass) |
| AC-126.3 | Gain calculation: `(sale_price - adjusted_cost_basis) × quantity` where `adjusted_cost_basis = cost_basis + wash_sale_adjustment` | Spec: domain-model-reference.md L360-362 (wash_sale_adjustment field) | Verify wash_sale_adjustment correctly increases basis, reducing gain |
| AC-126.4 | `simulate_impact(request)` returns lot-level close preview with ST/LT split, estimated tax, wash risk flag | Spec: 04f-api-tax.md L74-80, domain-model-reference.md C1 | BusinessRuleError when no open lots for ticker |
| AC-126.5 | `simulate_impact` uses `select_lots_for_closing` + `calculate_realized_gain` to produce per-lot breakdown | Local Canon: service orchestrates pure domain functions | Verify correct lot selection order feeds into gain calc |
| AC-126.6 | Integration: TaxService with real SQLite verifies get_lots → close_lot → gain calculation round-trip | Local Canon: follows existing integration test pattern | N/A (integration) |

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| Gain formula (proceeds - basis) × qty | Spec | domain-model-reference.md implied by TaxLot fields (L360-361) |
| Wash sale adjustment in gain calc | Spec | domain-model-reference.md L362: "deferred loss added to basis" |
| ST/LT boundary 366 days | Spec | domain-model-reference.md A2, L365 |
| simulate_impact output shape | Spec | 04f-api-tax.md L77-78 |
| Tax rate application | Spec | TaxProfile.federal_bracket + state_tax_rate (domain-model-reference.md L385-386) |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `packages/core/src/zorivest_core/domain/tax/gains_calculator.py` | new | Pure domain function: `calculate_realized_gain()` + `RealizedGainResult` frozen dataclass |
| `packages/core/src/zorivest_core/services/tax_service.py` | modify | Add `simulate_impact()` method |
| `tests/unit/test_gains_calculator.py` | new | ~10 tests for gain/loss calculation + ST/LT classification |
| `tests/unit/test_tax_service.py` | modify | Add ~5 tests for simulate_impact with mocked UoW |
| `tests/integration/test_tax_service_integration.py` | new | ~8 integration tests with real in-memory SQLite |

---

## Out of Scope

- Item 54: Capital loss carryforward + $3K/year cap + prior-year rollover (MEU-127)
- Item 55: Options assignment/exercise cost basis pairing (MEU-128)
- Item 56: YTD P&L by symbol (MEU-129)
- **Item 57: Basic wash sale detection — WashSaleChain entity, 30-day detection (MEU-130)**
- Items 58–63: Advanced wash sale features (chain tracking, cross-account, options matching, DRIP, rebalance, alerts — MEU-131 through MEU-136)
- Phase 3C: Tax optimization tools (harvesting scanner, tax-smart replacement)
- Phase 3D: Quarterly payment tracking
- Phase 3E: Tax REST API endpoints (MEU-148) and MCP tools
- Phase 6: Tax GUI (06g-gui-tax.md)

---

## BUILD_PLAN.md Audit

This project does not modify BUILD_PLAN.md. MEU-125 (`tax-lot-tracking`, item 52) and MEU-126 (`tax-gains-calc`, item 53) already exist in BUILD_PLAN.md L616-617 with status ⬜.

After implementation: update status to 🟡 in BUILD_PLAN.md and add entries to `meu-registry.md`.

```powershell
rg "tax-logic-expansion" docs/BUILD_PLAN.md  # Expected: 0 matches
```

---

## Verification Plan

### 1. Unit Tests (Pure Domain Functions)
```powershell
uv run pytest tests/unit/test_lot_selector.py tests/unit/test_gains_calculator.py -x --tb=short -v *> C:\Temp\zorivest\pytest-domain.txt; Get-Content C:\Temp\zorivest\pytest-domain.txt | Select-Object -Last 40
```

### 2. Unit Tests (Service Layer)
```powershell
uv run pytest tests/unit/test_tax_service.py -x --tb=short -v *> C:\Temp\zorivest\pytest-service.txt; Get-Content C:\Temp\zorivest\pytest-service.txt | Select-Object -Last 40
```

### 3. Integration Tests
```powershell
uv run pytest tests/integration/test_tax_service_integration.py -x --tb=short -v *> C:\Temp\zorivest\pytest-integ.txt; Get-Content C:\Temp\zorivest\pytest-integ.txt | Select-Object -Last 40
```

### 4. Full Regression
```powershell
uv run pytest tests/ -x --tb=short *> C:\Temp\zorivest\pytest-full.txt; Get-Content C:\Temp\zorivest\pytest-full.txt | Select-Object -Last 40
```

### 5. Type Check
```powershell
uv run pyright packages/ *> C:\Temp\zorivest\pyright.txt; Get-Content C:\Temp\zorivest\pyright.txt | Select-Object -Last 30
```

### 6. Lint
```powershell
uv run ruff check packages/ *> C:\Temp\zorivest\ruff.txt; Get-Content C:\Temp\zorivest\ruff.txt | Select-Object -Last 20
```

### 7. MEU Gate
```powershell
uv run python tools/validate_codebase.py --scope meu *> C:\Temp\zorivest\validate.txt; Get-Content C:\Temp\zorivest\validate.txt | Select-Object -Last 50
```

---

## Open Questions

> None — all behaviors resolved from Spec, Local Canon, or Research-backed sources.
>
> - MAX_* algorithms: resolved via IBKR lot-matching-methods.htm (4-tier priority, verified 2026-05-12)
> - close_lot data source: resolved via domain-model-reference.md A3 + AGENTS.md import model (sell trade provides proceeds)

---

## Research References

- [IBKR Lot Matching Methods](https://www.ibkrguides.com/traderworkstation/lot-matching-methods.htm): Authoritative 4-tier priority rules for MLG, MLL, MSG, MSL methods (verified 2026-05-12)
- [IBKR Tax Optimizer Overview](https://www.interactivebrokers.com/en/trading/tax-optimizer.php): Tax Optimizer product context
- domain-model-reference.md: Module A (Core Tax Engine) — canonical entity/behavior specs
- 03-service-layer.md: TaxService class design — 8-method cohesive service
- 04f-api-tax.md: API route contracts and request/response schemas (consumer reference, not implemented here)
