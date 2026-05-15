---
project: "2026-05-14-tax-optimization-tools"
date: "2026-05-14"
source: "docs/build-plan/domain-model-reference.md §Module C (lines 494–525)"
meus: ["MEU-140", "MEU-142", "MEU-137", "MEU-138", "MEU-139", "MEU-141"]
status: "approved"
template_version: "2.0"
---

# Implementation Plan: Tax Optimization Tools (Phase 3C)

> **Project**: `2026-05-14-tax-optimization-tools`
> **Build Plan Section(s)**: domain-model-reference.md §Module C (C1–C6), build-priority-matrix.md §P3 items 64–69
> **Status**: `approved`

---

## Goal

Implement the six Phase 3C Tax Optimization domain-layer functions that compose the already-built tax foundation (Phase 3A: lots, gains, loss carryforward; Phase 3B: wash sale detection; Phase 3D: brackets, NIIT, quarterly estimates) into actionable user-facing optimization tools.

These are **pure domain functions** — no infrastructure, no REST API, no GUI. They consume `TaxLot`, `TaxProfile`, and existing tax functions, and return frozen dataclass results. The API/MCP/GUI wiring is deferred to MEU-148/149/154 (Phase 3E).

**Zorivest does NOT execute trades** — these tools generate information and recommendations only. The API/MCP layer (Phase 3E: MEU-148/149) MUST add the standard tax disclaimer to all user-facing responses. Domain result types are internal computation results and do not carry a disclaimer field.

---

## User Review Required

> [!IMPORTANT]
> **MEU-139 Replacement Table**: The build plan specifies "suggest correlated but NOT substantially identical replacement securities." The implementation uses a **static mapping table** of well-known ETF/stock substitution pairs (VOO↔IVV, VTI↔ITOT, etc.). This is the standard approach in tax-loss harvesting. If you have specific pairs you want included/excluded, note them before execution.
>
> **MEU-141 Settlement Window**: The plan implements T+1 settlement (US equities standard since May 2024). The domain-model-reference mentions `BrokerModel.settlement_days`, but the BrokerModel entity is not yet implemented (MEU-96 area). This plan uses a constant `SETTLEMENT_DAYS = 1` at the domain layer, with a parameter override for future flexibility.

---

## Proposed Changes

### MEU-140: Lot Matcher / Close Specific Lots

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-140.1 | `get_lot_details(lots, current_price) → list[LotDetail]` returns enriched per-lot data: cost_basis, unrealized_gain, unrealized_gain_pct, holding_period_days, days_to_long_term, is_long_term | Spec (domain-model-reference C4) | Empty lots list → empty result |
| AC-140.2 | `LotDetail` frozen dataclass with 9 fields: lot_id, ticker, quantity, cost_basis, unrealized_gain, unrealized_gain_pct, holding_period_days, days_to_long_term, is_long_term | Local Canon (follows RealizedGainResult pattern) | — |
| AC-140.3 | `days_to_long_term = max(0, 366 - holding_period_days)` — returns 0 for already-LT lots | Spec (domain-model-reference A2: 366-day threshold) | LT lot → days_to_long_term == 0 |
| AC-140.4 | `unrealized_gain = (current_price - adjusted_basis) × quantity` where `adjusted_basis = cost_basis + wash_sale_adjustment` | Spec (follows gains_calculator.py formula) | Negative gain = unrealized loss |
| AC-140.5 | `preview_lot_selection(lots, quantity, method, sale_price) → list[LotDetail]` — enriches `select_lots_for_closing` output with per-lot detail | Spec (C4: "pick exactly which lots to close") | quantity > available → ValueError |
| AC-140.6 | Results sorted by the selected CostBasisMethod when using preview_lot_selection | Local Canon (lot_selector already sorts) | — |

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| Per-lot enrichment fields | Spec | domain-model-reference C4: "basis, unrealized gain/loss, holding period, days until LT" |
| unrealized_gain_pct formula | Local Canon | `(current_price - adjusted_basis) / adjusted_basis × 100` |
| Wash sale adjustment in basis | Spec | gains_calculator.py line 56: `adjusted_basis = cost_basis + wash_sale_adjustment` |
| LT threshold = 366 days | Spec | domain-model-reference A2, gains_calculator.py `_LT_THRESHOLD_DAYS` |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `packages/core/src/zorivest_core/domain/tax/lot_matcher.py` | new | `LotDetail` dataclass + `get_lot_details()` + `preview_lot_selection()` |
| `tests/unit/domain/tax/test_lot_matcher.py` | new | 10+ tests covering ACs 140.1–140.6 |

---

### MEU-142: ST vs LT Tax Rate Dollar Comparison

#### Tax Estimation Basis (Simplified Model)

> **Approximation**: Uses `TaxProfile.agi_estimate` as the `taxable_income` input for `compute_marginal_rate` and `compute_capital_gains_tax`. Same simplified model documented in `brackets.py` lines 320–336. See MEU-137 §Tax Estimation Basis for full rationale.

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-142.1 | `compare_st_lt_tax(lot, sale_price, tax_profile) → StLtComparison` returns tax_if_sold_now, tax_if_held_lt, days_remaining, tax_savings | Spec (domain-model-reference C6) | Already LT lot → days_remaining == 0, savings == 0 |
| AC-142.2 | `StLtComparison` frozen dataclass: tax_now, rate_now, tax_lt, rate_lt, days_remaining, tax_savings, holding_classification | Local Canon | — |
| AC-142.3 | `tax_now` uses ST ordinary rate via `compute_marginal_rate(agi_estimate, filing_status, tax_year)` applied to the unrealized gain amount. Uses `agi_estimate` as the taxable income proxy (simplified model). | Local Canon (quarterly.py precedent + brackets.py simplified LTCG model) | — |
| AC-142.4 | `tax_lt` uses LTCG preferential rate via `compute_capital_gains_tax(lt_gains, agi_estimate, filing_status, tax_year)` | Spec (C6: "LT @ 15%") + Local Canon (agi_estimate proxy) | 0% bracket → tax_lt == 0 |
| AC-142.5 | `tax_savings = tax_now - tax_lt` — positive means waiting saves money | Spec (C6: "Waiting saves $1,390") | Already LT → savings == 0 |
| AC-142.6 | Negative gain (unrealized loss) → both taxes are 0, savings is 0 | Local Canon | Loss lot → all zeros |
| AC-142.7 | State tax included via `compute_combined_rate` when `tax_profile.state_tax_rate > 0` | Spec (domain-model-reference E1: "state tax rate") | state_tax_rate=0 → federal-only |

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| Example in spec: "$2,340 tax (ST @ 37%), $950 tax (LT @ 15%), saves $1,390" | Spec | domain-model-reference C6 |
| Tax computation method for ST gains | Local Canon | ST gains taxed at ordinary income rates via `compute_marginal_rate(agi_estimate, ...)` — simplified model using agi_estimate as taxable income proxy |
| Tax computation method for LT gains | Spec + Local Canon | LTCG preferential rates 0/15/20% via `compute_capital_gains_tax(lt_gains, agi_estimate, ...)` |
| State tax treatment | Spec | TaxProfile.state_tax_rate feeds into estimates |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `packages/core/src/zorivest_core/domain/tax/rate_comparison.py` | new | `StLtComparison` dataclass + `compare_st_lt_tax()` |
| `tests/unit/domain/tax/test_rate_comparison.py` | new | 10+ tests covering ACs 142.1–142.7 |

---

### MEU-137: Pre-Trade "What-If" Tax Simulator

#### Tax Estimation Basis (Simplified Model)

> **Approximation**: Tax estimates use `TaxProfile.agi_estimate` as the `taxable_income` input for bracket lookups. ST gains are estimated via `compute_marginal_rate(agi_estimate, ...) * short_term_gain` (marginal delta approach). LT gains use `compute_capital_gains_tax(lt_gains, agi_estimate, ...)`. This follows the same simplified estimation pattern established in `brackets.py` for LTCG (see docstring lines 320–336). The full IRS worksheet stacking logic (ordinary income first, then capital gains layered on top) is deferred to a future MEU.
>
> **Precedent**: `quarterly.py` passes computed income values directly to `compute_tax_liability` for total progressive tax. These optimization tools instead use `compute_marginal_rate` for delta-based ST estimates, since they need the marginal tax impact of additional gains, not total liability.

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-137.1 | `simulate_tax_impact(lots, ticker, quantity, sale_price, tax_profile) → TaxImpactResult` — the main orchestration function | Spec (domain-model-reference C1) | ticker not in lots → ValueError |
| AC-137.2 | `TaxImpactResult` frozen dataclass: lots_selected (list[LotDetail]), realized_st_gain, realized_lt_gain, estimated_st_tax, estimated_lt_tax, estimated_niit, total_estimated_tax, wash_sale_warnings (list[WashSaleMatch]) | Local Canon (composing existing result types) | — |
| AC-137.3 | Lot selection uses `tax_profile.default_cost_basis` method (or explicit override param) | Spec (C1: "using selected lot method") | SPEC_ID without lot_ids → ValueError |
| AC-137.4 | ST/LT classification computed via `calculate_realized_gain` per selected lot | Spec (C1: "shows ST vs LT classification") | — |
| AC-137.5 | `estimated_st_tax = compute_marginal_rate(agi_estimate, filing_status, tax_year) * short_term_gain`. LT tax estimated via `compute_capital_gains_tax(lt_gains, agi_estimate, filing_status, tax_year)`. Uses `TaxProfile.agi_estimate` as the taxable income proxy (simplified model). | Local Canon (quarterly.py precedent + brackets.py simplified LTCG model) | Zero gain → zero tax |
| AC-137.6 | Wash sale risk detected via `detect_wash_sales` against all lots in the same ticker | Spec (C1: "wash sale risk") | No recent purchases → empty warnings |
| AC-137.7 | NIIT computed via `compute_niit(agi_estimate, net_investment_income, filing_status)` | Local Canon (domain-model-reference E2) | AGI below threshold → NIIT == 0 |
| AC-137.8 | `total_estimated_tax = estimated_st_tax + estimated_lt_tax + estimated_niit` | Local Canon | — |
| AC-137.9 | Optional `cost_basis_method` param overrides `tax_profile.default_cost_basis` | Spec (C1: "using selected lot method") | — |
| AC-137.10 | State tax included in estimates when `tax_profile.state_tax_rate > 0` | Spec (E1) | state_tax_rate=0 → federal-only |

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| Orchestration of lot selection + gain calc + wash + brackets + NIIT | Spec | domain-model-reference C1: all components listed |
| Result type composition | Local Canon | Follows RealizedGainResult pattern, composes existing types |
| Tax estimation: ST marginal rate × gain | Local Canon | Follows quarterly.py precedent; `compute_marginal_rate` returns the bracket rate for the last dollar of income, applied to the gain amount for a delta-based estimate |
| NIIT inclusion in what-if | Local Canon | NIIT is part of the broader tax estimate (domain-model-reference E2) |
| State tax inclusion | Spec | TaxProfile.state_tax_rate feeds into estimates |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `packages/core/src/zorivest_core/domain/tax/tax_simulator.py` | new | `TaxImpactResult` + `simulate_tax_impact()` |
| `tests/unit/domain/tax/test_tax_simulator.py` | new | 12+ tests covering ACs 137.1–137.10 |

---

### MEU-138: Tax-Loss Harvesting Scanner

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-138.1 | `scan_harvest_candidates(open_lots, current_prices, tax_profile, all_lots) → HarvestScanResult` | Spec (domain-model-reference C2) | No open lots → empty result |
| AC-138.2 | `HarvestCandidate` frozen dataclass: ticker, lots (list[LotDetail]), total_harvestable_loss, wash_sale_blocked (bool), wash_sale_reason (str), days_to_clear (int) | Local Canon | — |
| AC-138.3 | `HarvestScanResult` frozen dataclass: candidates (list[HarvestCandidate]), total_harvestable (Decimal), total_blocked (Decimal), skipped_tickers (list[str]) | Local Canon | — |
| AC-138.4 | Only lots with unrealized loss are included (current_price < adjusted_basis) | Spec (C2: "open positions with unrealized losses") | All gains → empty candidates |
| AC-138.5 | Positions that would trigger wash sales are flagged `wash_sale_blocked=True` with reason | Spec (C2: "Filter out positions that would trigger wash sales") | Recent repurchase within 30 days → blocked |
| AC-138.6 | Results ranked by `total_harvestable_loss` descending | Spec (C2: "Rank by harvestable loss amount") | — |
| AC-138.7 | `days_to_clear` = days until the 30-day post-sale window expires (0 if no conflict) | Local Canon (wash_sale_warnings.py pattern) | No recent sale → 0 |
| AC-138.8 | Respects `tax_profile.wash_sale_method` (CONSERVATIVE/AGGRESSIVE) for matching | Local Canon (MEU-133 pattern) | — |
| AC-138.9 | `current_prices` is a `dict[str, Decimal]` mapping ticker → current market price. Missing ticker price → exclude that ticker's lots from scan and append ticker to `skipped_tickers` | Local Canon | Missing price for "XYZ" → "XYZ" in skipped_tickers, lots excluded |

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| Scan for unrealized losses | Spec | domain-model-reference C2 |
| Wash sale filtering | Spec | C2: "Filter out positions that would trigger wash sales" |
| Ranking by loss amount | Spec | C2: "Rank by harvestable loss amount" |
| Aggregation by ticker | Local Canon | Group lots by ticker for per-position view |
| Wash sale method config | Local Canon | Follows MEU-133 AC-133.1 pattern |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `packages/core/src/zorivest_core/domain/tax/harvest_scanner.py` | new | `HarvestCandidate` + `HarvestScanResult` + `scan_harvest_candidates()` |
| `tests/unit/domain/tax/test_harvest_scanner.py` | new | 12+ tests covering ACs 138.1–138.9 |

---

### MEU-139: Tax-Smart Replacement Suggestions

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-139.1 | `suggest_replacements(ticker) → list[ReplacementSuggestion]` returns correlated, non-substantially-identical alternatives | Spec (domain-model-reference C3) | Unknown ticker → empty list |
| AC-139.2 | `ReplacementSuggestion` frozen dataclass: ticker, name, category (str), correlation_note (str) | Local Canon | — |
| AC-139.3 | Static `REPLACEMENT_TABLE: dict[str, list[ReplacementSuggestion]]` with ≥15 common ETF pairs | Human-approved (user execution-session invocation, conversation 606fc053) | — |
| AC-139.4 | Bidirectional lookup: VOO → IVV and IVV → VOO | Spec (C3: implies symmetric substitution) | — |
| AC-139.5 | Categories: "US Total Market", "US Large Cap", "International Developed", "Emerging Markets", "US Bonds", "US Small Cap", "US Mid Cap", "S&P 500", "Growth", "Value" | Human-approved (user execution-session invocation, conversation 606fc053) | — |
| AC-139.6 | `suggest_replacements_for_harvest(candidate: HarvestCandidate) → list[ReplacementSuggestion]` — convenience wrapper for scanner output | Local Canon | Blocked candidate → still returns suggestions (user might wait) |
| AC-139.7 | Function is pure — no API calls, no market data lookups. The table is hardcoded. | Spec (pure domain layer) | — |

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| Replacement suggestion concept | Spec | domain-model-reference C3 |
| "Correlated but NOT substantially identical" | Spec | C3: "NOT substantially identical" |
| Example: VOO → IVV | Spec | C3: explicit example |
| Table contents (specific pairs) | Human-approved | User explicitly approved the replacement table pair families and category taxonomy (execution-session invocation, conversation 606fc053). Exact pairs are from major index ETF families (Vanguard ↔ iShares ↔ Schwab ↔ SPDR). |
| Category taxonomy | Human-approved | Categories (US Total Market, S&P 500, etc.) approved as part of the replacement table decision (execution-session invocation, conversation 606fc053). |
| Bidirectional lookup | Local Canon | Logical requirement: if A replaces B, then B replaces A |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `packages/core/src/zorivest_core/domain/tax/replacement_suggestions.py` | new | `ReplacementSuggestion` + `REPLACEMENT_TABLE` + `suggest_replacements()` + `suggest_replacements_for_harvest()` |
| `tests/unit/domain/tax/test_replacement_suggestions.py` | new | 8+ tests covering ACs 139.1–139.7 |

---

### MEU-141: Post-Trade Lot Reassignment Window

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-141.1 | `can_reassign_lots(lot, now) → ReassignmentEligibility` checks if the lot is within the settlement window for reassignment | Spec (domain-model-reference C5) | Lot older than T+1 → eligible=False |
| AC-141.2 | `ReassignmentEligibility` frozen dataclass: eligible (bool), deadline (datetime), hours_remaining (float), reason (str) | Local Canon | — |
| AC-141.3 | Settlement window = `close_date + SETTLEMENT_DAYS` where `SETTLEMENT_DAYS = 1` (T+1 US equities) | Spec (C5: "before settlement (T+1)") | close_date + 2 days → not eligible |
| AC-141.4 | `reassign_lots(lots, closed_lots, quantity, new_method, sale_price) → list[tuple[TaxLot, float]]` re-selects lots using a different CostBasisMethod | Spec (C5: "Allow changing lot-matching method") | quantity > available → ValueError |
| AC-141.5 | `reassign_lots` delegates to `select_lots_for_closing` with the new method | Local Canon (reuses existing lot_selector) | — |
| AC-141.6 | `SETTLEMENT_DAYS` is a module constant with a function parameter override for future broker-specific values | Local Canon (future-proofing for BrokerModel) | Custom settlement_days=2 respected |
| AC-141.7 | Open lots (close_date is None) → always eligible (not yet settled) | Local Canon | Open lot → eligible=True |

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| Post-trade method change | Spec | domain-model-reference C5 |
| Settlement deadline T+1 | Spec | C5: "before settlement (T+1)" |
| Undo capability | Spec | C5: "Undo button for tax mistakes" — domain provides the re-selection; GUI provides the button |
| BrokerModel.settlement_days integration | Local Canon | BrokerModel not yet built (MEU-96 area); use constant with param override |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `packages/core/src/zorivest_core/domain/tax/lot_reassignment.py` | new | `ReassignmentEligibility` + `can_reassign_lots()` + `reassign_lots()` |
| `tests/unit/domain/tax/test_lot_reassignment.py` | new | 8+ tests covering ACs 141.1–141.7 |

---

### Cross-Cutting: Tax Module __init__.py Update

| File | Action | Summary |
|------|--------|---------|
| `packages/core/src/zorivest_core/domain/tax/__init__.py` | modify | Export all new public types and functions from 6 new modules |

---

## Out of Scope

- **MEU-148** (Tax REST API endpoints) — Phase 3E, requires infra wiring
- **MEU-149** (Tax MCP tools) — Phase 3E, requires MCP server
- **MEU-154** (Tax GUI) — Phase 3E, requires React components
- **MEU-133–136** (remaining wash sale features: options matching, DRIP, rebalance, alerts) — Phase 3B completion
- **Market data integration** for current prices — MEU-138's `current_prices` param is manually provided; real-time price feeds are Phase 8 features
- **BrokerModel integration** for settlement_days — MEU-141 uses a constant with parameter override

---

## BUILD_PLAN.md & Registry Audit

Post-execution updates required in two files:

### 1. MEU Registry (`.agent/context/meu-registry.md`)

Update status for MEU-137, MEU-138, MEU-139, MEU-140, MEU-141, MEU-142 from `planned` → `approved`.

```powershell
rg "MEU-13[789]|MEU-14[012]" .agent/context/meu-registry.md *> C:\Temp\zorivest\registry-check.txt; Get-Content C:\Temp\zorivest\registry-check.txt
```

### 2. BUILD_PLAN.md Hub (`docs/BUILD_PLAN.md`)

Update the P3 summary row aggregate count to reflect 6 additional completions. No structural changes — Phase 3C section already exists with correct links.

```powershell
rg "Phase 3C|P3.*summary" docs/BUILD_PLAN.md *> C:\Temp\zorivest\buildplan-check.txt; Get-Content C:\Temp\zorivest\buildplan-check.txt
```

---

## Verification Plan

### 1. Unit Tests (per-MEU RED→GREEN)
```powershell
uv run pytest tests/unit/domain/tax/ -x --tb=short -v *> C:\Temp\zorivest\pytest-tax-opt.txt; Get-Content C:\Temp\zorivest\pytest-tax-opt.txt | Select-Object -Last 40
```

### 2. Full Suite Regression
```powershell
uv run pytest tests/ -x --tb=short -v *> C:\Temp\zorivest\pytest-full.txt; Get-Content C:\Temp\zorivest\pytest-full.txt | Select-Object -Last 40
```

### 3. Type Check
```powershell
uv run pyright packages/ *> C:\Temp\zorivest\pyright.txt; Get-Content C:\Temp\zorivest\pyright.txt | Select-Object -Last 30
```

### 4. Lint
```powershell
uv run ruff check packages/ *> C:\Temp\zorivest\ruff.txt; Get-Content C:\Temp\zorivest\ruff.txt | Select-Object -Last 20
```

### 5. Anti-Placeholder Scan
```powershell
rg "TODO|FIXME|NotImplementedError" packages/core/src/zorivest_core/domain/tax/ *> C:\Temp\zorivest\placeholder.txt; Get-Content C:\Temp\zorivest\placeholder.txt
```

### 6. MEU Gate
```powershell
uv run python tools/validate_codebase.py --scope meu *> C:\Temp\zorivest\validate.txt; Get-Content C:\Temp\zorivest\validate.txt | Select-Object -Last 50
```

---

## Open Questions

> [!WARNING]
> No blocking questions. All behaviors are fully specified between the build plan and existing codebase patterns. The two decisions documented in "User Review Required" (replacement table contents and settlement window constant) are pre-resolved with sensible defaults.

---

## Research References

- [domain-model-reference.md §Module C](file:///p:/zorivest/docs/build-plan/domain-model-reference.md) — Lines 494–525: Tax Optimization Tools spec
- [domain-model-reference.md §Module E](file:///p:/zorivest/docs/build-plan/domain-model-reference.md) — Lines 553–565: Tax Bracket & Rate Integration
- [IRS Publication 550](https://www.irs.gov/publications/p550) — Investment income and expenses (wash sale rule source)
- [IRS Schedule D Instructions](https://www.irs.gov/forms-pubs/about-schedule-d-form-1040) — Capital gains/losses netting
- Tax-loss harvesting ETF pairs: Standard industry knowledge (Vanguard/iShares/Schwab/SPDR index fund families)
- [SEC T+1 Settlement](https://www.sec.gov/rules/2024/03/securities-transaction-settlement-cycle) — US equities T+1 since May 28, 2024
