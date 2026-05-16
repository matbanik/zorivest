# Tax GUI Full-Stack Audit Report

**Date:** 2026-05-16 (Updated)
**Scope:** All 7 Tax GUI tabs — Database → TaxService → API Route → GUI Component
**Purpose:** Trace every calculation, identify every data shape mismatch, document remediation

---

## Executive Summary

> [!IMPORTANT]
> **Remediation Progress:** All 7 tabs have been audited and 6 of 7 remediations are complete. The remaining item (Quarterly payment persistence) is a backend service issue, not a GUI mismatch.

| Tab | Status | Resolution |
|-----|--------|------------|
| **Dashboard** | ✅ Fixed | Removed phantom fields; computes `estimated_tax = federal + state`; defensive normalization |
| **Lots** | ✅ Working | No changes needed |
| **Wash Sales** | ✅ Fixed | Interface mapped to `entries[]` + `disallowed_amount` |
| **Simulator** | ✅ Fixed | Added `action`, `account_id` selector; remapped all fields to actual API response |
| **Harvesting** | ✅ Fixed | Rewrote to match `{ticker, disallowed_amount, status}` shape |
| **Quarterly** | ✅ Fixed | Normalization now handles `required_amount` (success path) + `required` (error fallback) |
| **Audit** | ✅ Fixed | Remapped to `{finding_type, severity, message, lot_id, details}` + `severity_summary` |

---

## 1. Dashboard (`TaxDashboard.tsx`)

### Data Flow

```
DB: tax_lots (closed, year-filtered) + wash_sale_chains (ABSORBED) + tax_profiles + quarterly_estimates
  ↓
TaxService.ytd_summary(tax_year, account_id?)
  ↓
API: GET /api/v1/tax/ytd-summary?tax_year=2026
  ↓
GUI: TaxDashboard.tsx → YtdSummary interface
```

### Pseudocode: `ytd_summary(tax_year)`

```
1. QUERY closed lots WHERE close_date.year == tax_year
2. EXCLUDE lots from tax-advantaged accounts (IRA, 401k, etc.)
3. FOR EACH taxable lot:
     gain = calculate_realized_gain(lot, lot.proceeds)
     IF gain.is_long_term: total_lt += gain
     ELSE: total_st += gain
4. wash_adjustments = SUM(chain.disallowed_amount) WHERE status == ABSORBED
5. IF TaxProfile exists:
     estimated_federal = (total_st + total_lt) * profile.federal_bracket + NIIT
     estimated_state = (total_st + total_lt) * profile.state_tax_rate
6. quarterly_payments = Q1-Q4 records from quarterly_estimates table
7. RETURN YtdTaxSummary {
     realized_st_gain, realized_lt_gain, total_realized,
     wash_sale_adjustments, trades_count,
     estimated_federal_tax, estimated_state_tax,
     quarterly_payments[]
   }
```

### API Response Shape (actual)

```python
# YtdTaxSummary dataclass → _serialize() → JSON
{
  "realized_st_gain": -23075.0,
  "realized_lt_gain": 0.0,
  "total_realized": -23075.0,
  "wash_sale_adjustments": 1000.0,
  "trades_count": 5,
  "estimated_federal_tax": 0.0,
  "estimated_state_tax": 0.0,
  "quarterly_payments": [...]
}
```

### Remediation (COMPLETED ✅)

| # | Issue | Fix Applied |
|---|-------|-------------|
| D1 | `estimated_tax` not in API | GUI now computes: `estimated_tax = estimated_federal_tax + estimated_state_tax` |
| D2-D4 | Phantom fields (`capital_loss_carryforward`, `harvestable_losses`, `tax_alpha`) | Removed — these are not in YtdTaxSummary |
| D5 | `group_by=symbol` not supported | Removed symbol breakdown table; quarterly_payments rendered inline |
| D6 | Button styling inconsistency | "Process Tax Lots" button now uses `bg-accent` pattern matching "Run Audit" |

---

## 2. Lots (`TaxLotExplorer.tsx`)

**Status: ✅ Working** — Lot explorer correctly maps API response. No changes needed.

---

## 3. Wash Sales (`WashSaleMonitor.tsx`) — FIXED

**Status: ✅ Fixed** — Updated GUI interface to match `entries[]` + `disallowed_amount`.

---

## 4. Simulator (`WhatIfSimulator.tsx`)

### Data Flow

```
DB: tax_lots (open, for ticker+account) + tax_profiles
  ↓
TaxService.simulate_impact(account_id, ticker, quantity, sale_price, method)
  ↓
API: POST /api/v1/tax/simulate (SimulateTaxRequest)
  ↓
GUI: WhatIfSimulator.tsx → SimulationResult interface
```

### Pseudocode: `simulate_impact()`

```
1. QUERY open lots WHERE account_id AND ticker
2. SELECT lots using cost_basis_method (FIFO/LIFO/etc.)
3. FOR EACH selected (lot, qty):
     gain = calculate_realized_gain(lot, sale_price)
     proportion = qty / lot.quantity
     scaled_gain = gain.gain_amount * proportion
     IF long_term: total_lt += scaled_gain ELSE: total_st += scaled_gain
4. Get tax rates from TaxProfile (or fallback params)
5. estimated_tax = (total_lt + total_st) * combined_rate
6. Check wash risk: lot.wash_sale_adjustment > 0 OR recent purchases within 30 days
7. RETURN SimulationResult {
     lot_details[], total_lt_gain, total_st_gain,
     estimated_tax, wash_risk, wash_sale_warnings[], wait_days
   }
```

### Remediation (COMPLETED ✅)

| # | Issue | Fix Applied |
|---|-------|-------------|
| S1 | Missing `action` field | Added `action: "sell"` as default in request body |
| S2 | Missing `account_id` | Added account dropdown populated from `/api/v1/accounts` with auto-select |
| S3-S5 | Wrong field names (`realized_pnl`, `short_term_gain`, `long_term_gain`) | Remapped to `total_st_gain`, `total_lt_gain` with `?? 0` fallback |
| S6 | `wash_sale_risk` → `wash_risk` | Fixed |
| S7 | `lot_breakdown` → `lot_details` | Fixed with `?? []` fallback |
| S8 | LotImpact field names | Remapped: `quantity`, `gain_amount`, `is_long_term`, `holding_period_days` |
| S9 | No account selector | Added `<select>` with accounts from API |

---

## 5. Harvesting (`LossHarvestingTool.tsx`)

### Data Flow

```
DB: wash_sale_chains (via get_trapped_losses)
  ↓
TaxService.get_trapped_losses() → list[WashSaleChain]
  ↓
API: GET /api/v1/tax/harvest → { opportunities[], total_harvestable }
  ↓
GUI: LossHarvestingTool.tsx → HarvestOpportunity interface
```

### Remediation (COMPLETED ✅)

| # | Issue | Fix Applied |
|---|-------|-------------|
| H1-H7 | All 7 field mismatches | Rewrote entire component to match `{ticker, disallowed_amount (string→number), status}` |

---

## 6. Quarterly (`QuarterlyTracker.tsx`)

### Data Flow

```
DB: tax_profiles + quarterly_estimates table
  ↓
TaxService.quarterly_estimate(quarter_int, tax_year, method)
  ↓
API: GET /api/v1/tax/quarterly?quarter=Q1&tax_year=2026
  ↓
GUI: QuarterlyTracker.tsx → QuarterData interface (via normalizeQuarterData)
```

### Pseudocode: `quarterly_estimate(quarter, tax_year, method)`

```
1. VALIDATE quarter in 1-4
2. LOAD TaxProfile for tax_year
3. IF no profile: RAISE error → API catches → returns zeroed response
4. IF method == "annualized":
     quarterly_income = profile.agi_estimate / 4
     result = compute_annualized_installment(quarterly_incomes, filing_status, tax_year)
     required_amount = result.installments[quarter - 1]
5. RETURN QuarterlyEstimateResult {
     quarter, tax_year, required_amount, due_date,
     method, paid: 0, due: required_amount, penalty: 0
   }
```

### Remediation (COMPLETED ✅)

| # | Issue | Fix Applied |
|---|-------|-------------|
| Q1-Q2 | `required_amount` vs `required` key inconsistency | Normalization now checks `required_amount ?? required ?? estimated_amount ?? 0` |

### Known Backend Limitation

> [!NOTE]
> **Q3-Q4 (Payment persistence):** The `quarterly_estimate()` service always returns `paid=0` because it recomputes from TaxProfile rather than reading persisted records. The `ytd_summary()` endpoint DOES read from `quarterly_estimates` table. This is a backend service issue, not a GUI mapping issue. Fix requires modifying `TaxService.quarterly_estimate()` to merge persisted payment data.

---

## 7. Audit (`TransactionAudit.tsx`)

### Data Flow

```
DB: tax_lots (all, filtered by account_id/tax_year)
  ↓
TaxService.run_audit(account_id?, tax_year?)
  ↓
API: POST /api/v1/tax/audit → AuditReport serialized
  ↓
GUI: TransactionAudit.tsx → AuditResult interface
```

### Pseudocode: `run_audit()`

```
1. LOAD all tax lots (filtered by account_id, tax_year)
2. CHECK missing_basis: lot.cost_basis == 0 or None → finding(severity="error")
3. CHECK duplicate_lot: same (account, ticker, open_date, qty) → finding(severity="warning")
4. CHECK orphaned_lot: closed but no linked_trade_ids → finding(severity="warning")
5. CHECK invalid_proceeds: closed and proceeds <= 0 → finding(severity="error")
6. Build severity_summary: { error: N, warning: N, info: N }
7. RETURN AuditReport { findings[], severity_summary }
```

### Remediation (COMPLETED ✅)

| # | Issue | Fix Applied |
|---|-------|-------------|
| A1 | No `id` field for React key | Uses `finding.lot_id \|\| idx` as key |
| A2 | Severity mapping (`error`/`warning`/`info` vs `high`/`medium`/`low`) | Changed color map to use API values directly |
| A3 | `category` → `finding_type` | Remapped with friendly `FINDING_LABELS` map |
| A4 | `description` → `message` | Direct field mapping |
| A5 | `affected_trades` removed | Shows lot ID instead |
| A6 | `recommendation` not in API | Generated from `finding_type` via `getRecommendation()` switch |
| A7 | `total_trades_audited` not in API | Shows `severity_summary` breakdown instead |
| A8 | `audit_timestamp` removed | Not needed for display |

---

## Remediation Summary

| Component | Mismatches | Fixed | Remaining |
|-----------|------------|-------|-----------|
| Dashboard | 6 | 6 | 0 |
| Simulator | 10 | 10 | 0 |
| Harvesting | 7 | 7 | 0 |
| Quarterly | 4 | 2 (GUI) | 2 (backend service) |
| Audit | 8 | 8 | 0 |
| Wash Sales | 0 | 0 | 0 |
| Lots | 0 | 0 | 0 |
| **Total** | **35** | **33** | **2** |

---

## MCP Tool Wiring Summary

| MCP Action | API Endpoint | Method | Status |
|------------|-------------|--------|--------|
| `simulate` | POST /tax/simulate | `simulate_impact()` | ✅ Wired + GUI fixed |
| `estimate` | POST /tax/estimate | `get_taxable_gains()` | ✅ Wired |
| `wash_sales` | POST /tax/wash-sales | `get_trapped_losses()` | ✅ Wired + GUI fixed |
| `lots` | GET /tax/lots | `get_lots()` | ✅ Wired |
| `quarterly` | GET /tax/quarterly | `quarterly_estimate()` | ✅ Wired + GUI fixed |
| `record_payment` | POST /tax/quarterly/payment | `record_payment()` | ✅ Wired (backend paid=0 issue remains) |
| `harvest` | GET /tax/harvest | `get_trapped_losses()` | ✅ Wired + GUI fixed |
| `ytd_summary` | GET /tax/ytd-summary | `ytd_summary()` | ✅ Wired + GUI fixed |
| `sync_lots` | POST /tax/sync-lots | `sync_lots()` | ✅ Wired |
| `scan_wash_sales` | POST /tax/wash-sales/scan | `scan_cross_account_wash_sales()` | ✅ Wired |

**Conclusion:** MCP→API→Service wiring is complete. All GUI→API data shape mismatches have been resolved. The only remaining issue is the backend `quarterly_estimate()` method not reading persisted payment data.
