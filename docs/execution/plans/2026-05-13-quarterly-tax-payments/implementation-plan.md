---
project: "2026-05-13-quarterly-tax-payments"
date: "2026-05-13"
source: "docs/build-plan/build-priority-matrix.md §P3D (Items 70–74), domain-model-reference.md §Module D+E"
meus: ["MEU-143", "MEU-144", "MEU-145", "MEU-146", "MEU-147"]
status: "draft"
template_version: "2.0"
---

# Implementation Plan: Quarterly Tax Payments & Tax Brackets

> **Project**: `2026-05-13-quarterly-tax-payments`
> **Build Plan Section(s)**: build-priority-matrix.md Items 70–74 (Phase 3D — Modules D+E)
> **Status**: `draft`

---

## Goal

Implement the quarterly estimated tax payment engine (Module D) and tax bracket integration (Module E) as pure domain computation with service-layer orchestration. This gives Zorivest the ability to:

1. **Compute required quarterly estimated tax payments** using IRS safe harbor rules (90% current year / 100% or 110% prior year)
2. **Support the annualized income method** (Form 2210 Schedule AI) for users with fluctuating quarterly income
3. **Track quarterly due dates and estimate underpayment penalties** using the IRS-prescribed formula (federal short-term rate + 3%)
4. **Calculate marginal and effective federal tax rates** from bracket lookup tables (2025/2026), plus state tax rate integration
5. **Alert when MAGI approaches NIIT thresholds** ($200K single / $250K MFJ) for the 3.8% surtax

**Disclaimer scope (deferred to presentation layer):** This is an estimator tool, not legal tax advice. The domain/service layer returns computation results as Decimal values and dataclasses — disclaimers are the responsibility of the API response envelope (MEU-148), MCP tool descriptions (MEU-149), and GUI components (MEU-154). No domain-layer code emits disclaimer text.

**Scope boundary:** Domain layer + service layer only. No API routes (Phase 3E / MEU-148), no MCP tools (MEU-149), no GUI (MEU-154). The `QuarterlyEstimate` entity gets a repository port definition but no SQLAlchemy implementation — that is infrastructure work for Phase 3E.

---

## Resolved Design Decisions

> [!NOTE]
> 1. **Bracket table year coverage** — *Research-backed (IRS Rev. Proc. 2024-40, Rev. Proc. 2025-32)*: 2025 and 2026 bracket tables included. 2024 excluded from scope — carryforward scenarios use prior-year tax liability as a scalar input, not full bracket re-computation. If needed later, add as a follow-up.
> 2. **Penalty rate** — *Research-backed (IRS §6654, quarterly rate announcements)*: Hardcoded per year in bracket data tables. This matches IRS quarterly announcement cadence. The rate is not user-configurable — it is an IRS-published constant (federal short-term rate + 3%). 2025 rate: ~8%. Stored as `PENALTY_RATES` dict keyed by tax year in `brackets.py`.
> 3. **QuarterlyEstimate persistence** — *Spec (domain-model-reference.md L403-413) + Local Canon (ports.py pattern)*: Entity and repository port defined in this project. SQLAlchemy model + migration deferred to MEU-148 (Phase 3E). Service methods return computed results without persisting. `record_payment()` is signature-only in this project (see AC-145.7).

---

## Proposed Changes

### MEU-146: Marginal Tax Rate Calculator (federal + state)

> Execution order: **1st** — foundation for all rate-dependent computations.

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| 7-bracket federal tax rate structure | Research-backed | IRS Rev. Proc. 2024-40 (TY2025), Rev. Proc. 2025-32 (TY2026) via NTU Foundation / Tax Foundation |
| Bracket thresholds per filing status | Research-backed | 4 filing statuses × 7 brackets. 2025 thresholds from IRS.gov. 2026 thresholds from IRS inflation adjustments |
| Capital gains tax rates (0%, 15%, 20%) | Spec | domain-model-reference.md §A2: "long-term (0%, 15%, or 20%)" |
| State tax rate integration | Spec | domain-model-reference.md L387: `state_tax_rate: float` on TaxProfile |
| Effective vs marginal rate computation | Spec | domain-model-reference.md §E1: "compute effective + marginal federal rate" |

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-146.1 | `compute_marginal_rate(taxable_income, filing_status, tax_year)` returns correct marginal bracket rate for all 7 brackets | Research-backed (IRS tables) | Income < 0 → raises ValueError |
| AC-146.2 | `compute_effective_rate(taxable_income, filing_status, tax_year)` returns total_tax / taxable_income as effective rate | Spec §E1 | Income = 0 → returns 0.0 (not division error) |
| AC-146.3 | `compute_tax_liability(taxable_income, filing_status, tax_year)` returns total federal income tax in dollars using progressive brackets | Research-backed | Unsupported tax_year → raises ValueError |
| AC-146.4 | `compute_capital_gains_tax(lt_gains, taxable_income, filing_status, tax_year)` returns estimated LT capital gains tax using a simplified single-rate model (selects 0%/15%/20% based on total taxable income, does not stack gains across brackets). Suitable for quarterly estimation; stacked worksheet behavior deferred to a future MEU. | Research-backed (simplified) | Negative gains → returns Decimal("0") |
| AC-146.5 | Bracket data includes 2025 and 2026 tax years, with 4 filing statuses each | Research-backed | Unknown year → raises ValueError |
| AC-146.6 | `compute_combined_rate(federal_effective, state_tax_rate)` returns federal + state combined rate. State tax is a flat passthrough from `TaxProfile.state_tax_rate`. Tests: verify combined rate = federal_effective + state_rate; verify state_rate=0 returns federal-only | Spec (domain-model-reference.md L387, L557) | state_tax_rate < 0 → raises ValueError |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `packages/core/src/zorivest_core/domain/tax/brackets.py` | new | Federal bracket tables (2025/2026), marginal/effective/liability calculators, capital gains rate function |
| `packages/core/src/zorivest_core/domain/tax/__init__.py` | modify | Export new bracket functions |
| `tests/unit/test_tax_brackets.py` | new | ~20 tests covering all brackets, filing statuses, edge cases |

---

### MEU-147: NIIT (3.8% Surtax) Threshold Alert

> Execution order: **2nd** — simple threshold check, depends on bracket context for MAGI understanding.

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| NIIT rate = 3.8% | Research-backed | IRC §1411; rate fixed since 2013, not inflation-adjusted |
| Threshold: $200K single, $250K MFJ, $125K MFS, $200K HoH | Research-backed | IRC §1411(b) — static thresholds, no inflation adjustment |
| Applied to lesser of NII or MAGI excess over threshold | Research-backed | IRS Form 8960 instructions |
| Alert when approaching threshold | Spec | domain-model-reference.md §E2: "Flag when approaching threshold" |

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-147.1 | `compute_niit(magi, net_investment_income, filing_status)` returns NIIT amount when MAGI exceeds threshold | Research-backed (IRC §1411) | MAGI below threshold → returns Decimal("0") |
| AC-147.2 | NIIT = 3.8% × min(NII, MAGI - threshold) | Research-backed (Form 8960) | NII = 0 → returns Decimal("0") regardless of MAGI |
| AC-147.3 | Correct thresholds for all 4 filing statuses: Single=$200K, MFJ=$250K, MFS=$125K, HoH=$200K | Research-backed | N/A (static lookup) |
| AC-147.4 | `check_niit_proximity(magi, filing_status)` returns proximity percentage and alert flag when within 10% of threshold | Spec §E2 | MAGI far below → alert=False |
| AC-147.5 | All monetary computations use Decimal for precision | Local Canon (entities.py pattern) | N/A |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `packages/core/src/zorivest_core/domain/tax/niit.py` | new | NIIT computation + proximity alert function |
| `packages/core/src/zorivest_core/domain/tax/__init__.py` | modify | Export NIIT functions |
| `tests/unit/test_tax_niit.py` | new | ~10 tests: thresholds, partial NII, proximity alerts |

---

### MEU-143: QuarterlyEstimate Entity + Safe Harbor Calculation

> Execution order: **3rd** — entity definition + core safe harbor logic.

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| QuarterlyEstimate entity fields | Spec | domain-model-reference.md L403-413 |
| Safe harbor: 90% of current year tax | Spec | domain-model-reference.md §D1 |
| Safe harbor: 100% of prior year (110% if AGI > $150K) | Spec | domain-model-reference.md §D1 |
| 110% threshold = $150K for all except MFS ($75K) | Research-backed | IRS Pub 505; Form 1040-ES instructions |
| Recommend the lower of two safe harbor amounts | Spec | domain-model-reference.md §D1: "Tool recommends the lower amount" |
| `method` field enum values | Spec | domain-model-reference.md L410-411 |

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-143.1 | `QuarterlyEstimate` dataclass with 9 fields matching domain-model-reference.md L403-413 | Spec | N/A (structural) |
| AC-143.2 | `compute_safe_harbor(current_year_estimate, prior_year_tax, agi, filing_status)` returns the lower of 90%-current vs 100%/110%-prior | Spec §D1 | prior_year_tax = 0 → returns 90%-current only |
| AC-143.3 | 110% threshold applies when AGI > $150K (or > $75K for MFS) | Research-backed (IRS Pub 505) | AGI exactly $150K → uses 100%, not 110% |
| AC-143.4 | Result includes `method` field indicating which safe harbor path was used | Spec | N/A |
| AC-143.5 | Quarterly required payment = annual safe harbor amount / 4 | Spec | N/A |
| AC-143.6 | `QuarterlyEstimateRepository` port defined with get, save, update, list_for_year methods | Local Canon (ports.py pattern) | N/A |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `packages/core/src/zorivest_core/domain/entities.py` | modify | Add `QuarterlyEstimate` dataclass |
| `packages/core/src/zorivest_core/domain/tax/quarterly.py` | new | Safe harbor calculator, due date functions |
| `packages/core/src/zorivest_core/application/ports.py` | modify | Add `QuarterlyEstimateRepository` protocol + wire to UoW |
| `packages/core/src/zorivest_core/domain/tax/__init__.py` | modify | Export quarterly functions |
| `tests/unit/test_tax_quarterly.py` | new | ~15 tests: safe harbor math, threshold logic |

---

### MEU-144: Annualized Income Method (Form 2210 Schedule AI)

> Execution order: **4th** — extends quarterly computation with proportional income logic.

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| Annualization factors: 4, 2.4, 1.5, 1 per IRS period | Research-backed | IRS Form 2210 Schedule AI Line 2 (2025) — factors for individuals |
| Annualization periods: 1/1–3/31, 1/1–5/31, 1/1–8/31, 1/1–12/31 | Research-backed | IRS Form 2210 Schedule AI column headers |
| Required installment = min(annualized installment, regular installment adjusted for prior savings) | Research-backed | IRS Form 2210 Schedule AI Part I instructions |
| Input: quarterly income figures | Spec | domain-model-reference.md §D2 |

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-144.1 | `compute_annualized_installment(quarterly_incomes, filing_status, tax_year)` returns per-quarter required payment using Form 2210 Schedule AI logic | Research-backed | Empty incomes list → raises ValueError |
| AC-144.2 | Annualization factors are [4, 2.4, 1.5, 1] for individuals | Research-backed (Form 2210) | N/A (constant) |
| AC-144.3 | Each quarter's annualized tax = bracket computation on (cumulative_income × factor) | Research-backed | All quarters zero → all payments zero |
| AC-144.4 | Required installment for Q(n) = min(annualized_installment, regular_installment) adjusted for cumulative prior payments. Per IRS Form 2210 Schedule AI: annualized_installment = 25% of annualized tax for that period; regular_installment = 25% of required annual payment (safe harbor amount). The required installment is the *lesser* of these two, minus any cumulative excess from prior quarters, floored to 0 | Research-backed (IRS Form 2210 Schedule AI line 27, Instructions for Form 2210 (2025)) | Q1 income only → Q2-Q4 may have reduced required via prior-quarter savings |
| AC-144.5 | Result includes per-quarter breakdown: annualized_income, annualized_tax, required_installment | Spec §D2 | N/A |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `packages/core/src/zorivest_core/domain/tax/quarterly.py` | modify | Add annualized income installment method |
| `tests/unit/test_tax_quarterly.py` | modify | Add ~12 annualized income tests |

---

### MEU-145: Quarterly Due Date Tracker + Underpayment Penalty

> Execution order: **5th** — capstone, ties together all quarterly logic.

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| 4 due dates: Apr 15, Jun 15, Sep 15, Jan 15 | Spec | domain-model-reference.md §D3 |
| Weekend/holiday adjustment | Research-backed | IRS rule: if due date falls on weekend/holiday, next business day |
| Penalty rate = federal short-term rate + 3% | Spec + Research-backed | domain-model-reference.md §D4 + IRS §6654(a); ~7% for 2025 |
| Penalty accrual per quarter | Spec | domain-model-reference.md §D4: "Show penalty accrual per quarter" |
| Penalty = underpayment × rate × days/365 | Research-backed | IRS Form 2210 Part III penalty worksheet |

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-145.1 | `get_quarterly_due_dates(tax_year)` returns 4 dates: Apr 15, Jun 15, Sep 15, Jan 15(+1) | Spec §D3 | Invalid year → raises ValueError |
| AC-145.2 | Due dates falling on weekends shift to next Monday | Research-backed (IRS) | Saturday Apr 15 → Monday Apr 17 |
| AC-145.3 | `compute_underpayment_penalty(underpayment, due_date, payment_date, penalty_rate)` computes penalty = underpayment × rate × days_late/365 | Research-backed (Form 2210 Part III) | Payment on time → penalty = 0 |
| AC-145.4 | `quarterly_ytd_summary(tax_year, payments, required_amounts)` returns cumulative paid vs required per quarter | Spec §D3 | No payments → all shortfall |
| AC-145.5 | Penalty rate defaults stored in bracket data per tax year (configurable constant, not user input) | Research-backed | N/A |
| AC-145.6 | `TaxService.quarterly_estimate(quarter, tax_year, method)` orchestrates entity creation, safe harbor/annualized computation, and penalty estimation | Spec (04f-api-tax.md L263) | Invalid quarter → raises BusinessRuleError |
| AC-145.7 | `TaxService.record_payment(quarter, tax_year, amount)` — **signature-only contract**. Method defined with parameter validation (quarter 1-4, amount > 0). Body raises `NotImplementedError("MEU-148: requires QuarterlyEstimate SQLAlchemy model")`. Persistence implementation is MEU-148 scope. | Spec (04f-api-tax.md L264) + Local Canon (deferred-stub pattern) | Invalid quarter → raises BusinessRuleError |

#### Boundary Inventory

| Surface | Schema Owner | Field Constraints | Extra-Field Policy |
|---------|-------------|-------------------|-------------------|
| `TaxService.quarterly_estimate()` | Python function signature | quarter: int 1-4, tax_year: int 2024-2099, method: Literal enum | N/A (domain function) |
| `TaxService.record_payment()` | Python function signature | quarter: int 1-4, tax_year: int, amount: Decimal > 0 | N/A (domain function) |

> Note: REST and MCP boundaries are Phase 3E scope (MEU-148/149). Domain functions use Python type annotations + explicit validation raises.

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `packages/core/src/zorivest_core/domain/tax/quarterly.py` | modify | Add due date engine, penalty calculator, YTD summary |
| `packages/core/src/zorivest_core/domain/tax/brackets.py` | modify | Add penalty rate constants per year |
| `packages/core/src/zorivest_core/services/tax_service.py` | modify | Add `quarterly_estimate()`, `record_payment()` methods |
| `tests/unit/test_tax_quarterly.py` | modify | Add ~15 due date + penalty tests |
| `tests/unit/test_tax_service.py` | modify | Add ~5 service-level quarterly tests |

---

## Out of Scope

- **API routes** (`/tax/quarterly`, `/tax/quarterly/payment`, `/tax/estimate`) — Phase 3E / MEU-148
- **MCP tools** (`get_quarterly_estimate`, `record_quarterly_tax_payment`, `estimate_tax`) — Phase 3E / MEU-149
- **GUI** (quarterly tracker panel) — Phase 3E / MEU-154
- **SQLAlchemy model** for `QuarterlyEstimate` — deferred to MEU-148 infrastructure wiring
- **Tax calendar notifications/alerts** — not in Phase 3D spec
- **AMT calculation** — out of scope per domain model
- **2024 or earlier bracket tables** — only 2025 and 2026 included (revisit if carryforward demands it)

---

## BUILD_PLAN.md Status Update

Post-implementation, update `docs/BUILD_PLAN.md` Phase 3D rows (lines ~649-653) to change MEU-143 through MEU-147 status from ⬜ to the appropriate status icon. Also update `build-priority-matrix.md` §Phase 3D (lines ~366-370).

Verification command:

```powershell
rg -n "MEU-14[3-7]" docs/BUILD_PLAN.md *> C:\Temp\zorivest\build-plan-check.txt; Get-Content C:\Temp\zorivest\build-plan-check.txt
```

Expected: 5 rows showing updated status icons for MEU-143 through MEU-147.

---

## Verification Plan

### 1. Unit Tests (primary gate)
```powershell
uv run pytest tests/unit/test_tax_brackets.py tests/unit/test_tax_niit.py tests/unit/test_tax_quarterly.py -v *> C:\Temp\zorivest\pytest-quarterly.txt; Get-Content C:\Temp\zorivest\pytest-quarterly.txt | Select-Object -Last 40
```

### 2. Service-Level Tests
```powershell
uv run pytest tests/unit/test_tax_service.py -v -k "quarterly" *> C:\Temp\zorivest\pytest-tax-svc.txt; Get-Content C:\Temp\zorivest\pytest-tax-svc.txt | Select-Object -Last 30
```

### 3. Full Regression
```powershell
uv run pytest tests/ -x --tb=short -v *> C:\Temp\zorivest\pytest-full.txt; Get-Content C:\Temp\zorivest\pytest-full.txt | Select-Object -Last 40
```

### 4. Type Check
```powershell
uv run pyright packages/core/ *> C:\Temp\zorivest\pyright.txt; Get-Content C:\Temp\zorivest\pyright.txt | Select-Object -Last 30
```

### 5. Lint
```powershell
uv run ruff check packages/core/ *> C:\Temp\zorivest\ruff.txt; Get-Content C:\Temp\zorivest\ruff.txt | Select-Object -Last 20
```

### 6. Anti-Placeholder Scan
```powershell
rg "TODO|FIXME|NotImplementedError" packages/core/src/zorivest_core/domain/tax/brackets.py packages/core/src/zorivest_core/domain/tax/niit.py packages/core/src/zorivest_core/domain/tax/quarterly.py packages/core/src/zorivest_core/services/tax_service.py *> C:\Temp\zorivest\placeholder-scan.txt; Get-Content C:\Temp\zorivest\placeholder-scan.txt
```

> Note: `TaxService.record_payment()` is a signature-only contract in this project. The method validates inputs and raises `NotImplementedError` with an MEU-148 link. Task row status is `[B]` (blocked). Anti-placeholder scan must include `services/tax_service.py` and verify this is the only `NotImplementedError` in the file.

### 7. MEU Gate
```powershell
uv run python tools/validate_codebase.py --scope meu *> C:\Temp\zorivest\validate.txt; Get-Content C:\Temp\zorivest\validate.txt | Select-Object -Last 50
```

---

## Resolved Design Decisions (Additional)

> [!NOTE]
> 1. **Bracket table data source** — *Research-backed*: 2025 brackets from IRS Rev. Proc. 2024-40 (as amended by OBBB Act). 2026 brackets from IRS Rev. Proc. 2025-32. A `BRACKET_DATA_SOURCE` docstring will be added to the bracket data module for audit trail.
> 2. **Capital gains bracket thresholds** — *Research-backed (IRC §1(h), simplified)*: Included in MEU-146. The `compute_capital_gains_tax` function uses 0%/15%/20% LTCG thresholds to select a single applicable rate based on total taxable income. This is a simplified estimator suitable for quarterly tax estimation — it does not implement the IRS Qualified Dividends and Capital Gain Tax Worksheet stacking logic. Stacked LTCG calculation is deferred to a future MEU.

---

## Research References

- [IRS Rev. Proc. 2024-40](https://www.irs.gov/newsroom/irs-provides-tax-inflation-adjustments-for-tax-year-2025) — 2025 bracket thresholds
- [IRS Revenue Procedure 2025-32 (OBBB amendments)](https://www.irs.gov/newsroom/irs-releases-tax-inflation-adjustments-for-tax-year-2026-including-amendments-from-the-one-big-beautiful-bill) — 2026 adjustments
- [NTU Foundation: 2025 & 2026 Tax Rates](https://www.ntu.org/foundation/tax-page/what-are-federal-income-tax-rates-for-2025-and-2026)
- [IRS Form 2210 (2025)](https://www.irs.gov/pub/irs-pdf/f2210.pdf) — Underpayment penalty + Schedule AI
- [IRS Form 2210 Instructions (2025)](https://www.irs.gov/pub/irs-pdf/i2210.pdf) — Annualized income installment method
- [IRS Quarterly Interest Rates](https://www.irs.gov/payments/quarterly-interest-rates) — Federal short-term rate + 3%
- [IRC §1411](https://www.law.cornell.edu/uscode/text/26/1411) — Net Investment Income Tax (3.8%)
- [IRS Pub 505: Tax Withholding and Estimated Tax](https://www.irs.gov/publications/p505) — Safe harbor rules
