---
project: "2026-05-12-tax-rules-reporting"
date: "2026-05-12"
source: "docs/build-plan/build-priority-matrix.md §P3 Phase 3A, domain-model-reference.md §A4-A7"
meus: ["MEU-127", "MEU-128", "MEU-129"]
status: "draft"
template_version: "2.0"
---

# Implementation Plan: Tax Rules & Reporting

> **Project**: `2026-05-12-tax-rules-reporting`
> **Build Plan Section(s)**: domain-model-reference.md Module A (A4, A5, A6, A7); build-priority-matrix.md §P3 items 54–56
> **Status**: `draft`

---

## Goal

Complete Phase 3A (Core Tax Engine) by implementing the final three MEUs:
1. **MEU-127** — Capital loss carryforward with $3K/$1.5K annual cap and tax-advantaged account exclusion
2. **MEU-128** — Options assignment/exercise cost basis pairing with holder/writer distinction (four IRS paths: long call exercise, long put exercise, short put assignment, short call assignment)
3. **MEU-129** — YTD P&L by symbol with ST vs LT breakdown

These three MEUs close out Module A of the Tax Engine. All are pure domain logic + service-layer orchestration with no API/MCP/GUI surface. The foundation from Phase 3A Sessions 1–2 (MEU-123 through MEU-126) provides entities, repositories, lot selection, and gains calculation.

---

## User Review Required

> [!IMPORTANT]
> 1. **MEU-128 Option Symbol Parsing**: ✅ RESOLVED — The IBKR and TOS infrastructure adapters already normalize raw broker option symbols to a canonical space-separated format (`AAPL 260320 C 200`). The domain parser targets this normalized format, not raw 21-char OCC strings.
> 2. **Carryforward ST/LT Split**: ✅ RESOLVED (Human-approved) — The domain function `apply_capital_loss_rules()` takes separate `st_carryforward` and `lt_carryforward` Decimal inputs, making it IRS-correct. The `TaxProfile` entity keeps its single `capital_loss_carryforward` field for MVP. The service layer allocates carryforward to ST first per IRS Schedule D netting order. Human decision: user approved corrections plan containing ST-first allocation rule (conversation 65dc5cb3, 2026-05-12).

---

## Proposed Changes

### MEU-127: Capital Loss Carryforward + Tax-Advantaged Account Exclusion

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| $3,000 annual deduction cap against ordinary income | Spec | domain-model-reference.md A6 |
| $1,500 cap for MARRIED_SEPARATE filing status | Research-backed | IRS Publication 550; Schedule D instructions; confirmed via irs.gov |
| Carried-forward losses retain ST/LT character | Research-backed | IRS Schedule D Capital Loss Carryover Worksheet |
| Loss netting order: ST losses offset ST gains first, then LT; and vice versa | Research-backed | IRS Schedule D Part III netting logic |
| Domain function takes separate ST/LT carryforward inputs; service allocates entity total to ST first per IRS Schedule D | Human-approved (ST-first MVP, 2026-05-12) | Plan corrections 2026-05-12 |
| IRA/401K accounts excluded from capital gains tax | Spec | domain-model-reference.md A7 |
| IRA purchases still count for wash sale detection | Spec (out-of-scope) | domain-model-reference.md A7 — wash sale is MEU-130+ |
| Account.is_tax_advantaged field exists | Local Canon | entities.py:109 |
| TaxProfile.capital_loss_carryforward field exists (single Decimal) | Local Canon | entities.py:251 |
| Service allocates single carryforward to ST first per IRS Schedule D ordering | Human-approved (ST-first MVP, 2026-05-12) | Plan corrections 2026-05-12 |
| FilingStatus.MARRIED_SEPARATE enum exists | Local Canon | enums.py FilingStatus enum |

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-127.1 | `apply_capital_loss_rules(st_gains, lt_gains, st_carryforward, lt_carryforward, filing_status)` returns `CapitalLossResult` with `deductible_loss`, `remaining_st_carryforward`, `remaining_lt_carryforward`, `net_st`, `net_lt` | Spec + Research-backed (IRS Schedule D) + Human-approved (ST/LT split) | Negative carryforward rejected |
| AC-127.2 | Cap is $3,000 for SINGLE, MARRIED_JOINT, HEAD_OF_HOUSEHOLD; $1,500 for MARRIED_SEPARATE | Research-backed (IRS Pub 550) | Excess loss beyond cap goes to carryforward |
| AC-127.3 | Netting order: ST losses + ST carryforward offset ST gains first, LT losses + LT carryforward offset LT gains first, then cross-net remaining before applying cap | Research-backed (IRS Schedule D Part III) + Human-approved (ST/LT split) | Mixed ST gain + LT loss scenario correctly nets; separate carryforward inputs preserved |
| AC-127.4 | `TaxService.get_taxable_gains(tax_year)` excludes lots from accounts where `is_tax_advantaged=True` | Spec (A7) | Tax-advantaged lot gains not included in totals |
| AC-127.5 | `get_taxable_gains` applies carryforward from `TaxProfile` to net results | Spec (A6) | Missing TaxProfile returns gains without carryforward adjustment |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `packages/core/src/zorivest_core/domain/tax/loss_carryforward.py` | new | Pure domain function: `apply_capital_loss_rules()` + `CapitalLossResult` dataclass |
| `packages/core/src/zorivest_core/domain/tax/__init__.py` | modify | Export new module |
| `packages/core/src/zorivest_core/services/tax_service.py` | modify | Add `get_taxable_gains()` method |
| `tests/unit/test_loss_carryforward.py` | new | 12–18 tests for carryforward rules |
| `tests/unit/test_tax_service.py` | modify | Add tests for `get_taxable_gains()` |

---

### MEU-128: Options Assignment/Exercise Cost Basis Pairing

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| Short put assignment: premium received reduces stock cost basis | Spec + Research-backed | domain-model-reference.md A4; IRS Pub 550 §Puts and Calls |
| Short call assignment: premium received added to amount realized on stock sale | Spec + Research-backed | domain-model-reference.md A4; IRS Pub 550 §Puts and Calls |
| Long call exercise: premium paid added to stock cost basis | Research-backed | IRS Pub 550 §Puts and Calls L6041, L6065 |
| Long put exercise: premium paid reduces amount realized on stock sale | Research-backed | IRS Pub 550 §Puts and Calls L6077-6082 |
| Link option trades to resulting stock positions | Spec | domain-model-reference.md A4 |
| Normalized option symbol format: `"UNDERLYING YYMMDD C/P STRIKE"` (space-separated) | Local Canon | IBKR adapter `_normalize_symbol()` L206-248; TOS adapter `_normalize_tos_option()` L153-169 |
| Infrastructure adapters convert raw broker symbols to normalized format before domain layer | Local Canon | ibkr_flexquery.py:148-149; tos_csv.py:107-108 |
| `TradeAction.BOT/SLD` on option trade indicates holder (long) vs writer (short) side | Local Canon | enums.py L15-17; ibkr_flexquery.py L44-49 |
| Side derived from `option_trade.action` inside domain function; no caller-supplied side param | Local Canon | Prevents caller mismatch; `assignment_type` must be consistent with trade action |
| Trade entity has `instrument: str` but no explicit option fields | Local Canon | entities.py:84 |

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-128.1 | `parse_option_symbol(instrument)` parses normalized format `"UNDERLYING YYMMDD C/P STRIKE"` and returns `OptionDetails` or `None` for non-option/malformed instruments | Local Canon (adapter output format) | Non-option string returns None; malformed date returns None; raw 21-char OCC returns None (handled by infra) |
| AC-128.2 | `adjust_basis_for_assignment(stock_lot, option_trade, assignment_type)` — short put assignment: reduces stock cost basis by premium received. Side derived from `option_trade.action` (must be SLD). | Spec (A4) + Research-backed (IRS Pub 550) | Wrong assignment_type raises BusinessRuleError |
| AC-128.3 | Short call assignment: increases amount realized on stock sale by premium received. Side derived from `option_trade.action` (must be SLD). | Spec (A4) + Research-backed (IRS Pub 550) | Ticker mismatch between option underlying and stock lot raises error |
| AC-128.4 | Long call exercise: adds premium paid to stock cost basis. Side derived from `option_trade.action` (must be BOT). | Research-backed (IRS Pub 550 L6041, L6065) | BOT call with wrong assignment_type raises BusinessRuleError |
| AC-128.5 | Long put exercise: reduces amount realized on stock sale by premium paid. Side derived from `option_trade.action` (must be BOT). | Research-backed (IRS Pub 550 L6077-6082) | BOT put with wrong lot side raises error |
| AC-128.6 | `TaxService.pair_option_assignment(lot_id, option_exec_id, assignment_type)` persists adjusted basis and links trades for all four scenarios. Side derived from loaded option trade's action. | Spec (A4) | Option trade not found raises NotFoundError |
| AC-128.7 | `OptionDetails` is a frozen dataclass with `underlying: str`, `expiry: date`, `put_call: str`, `strike: Decimal` | Local Canon + Research-backed | N/A — structural |
| AC-128.9 | `assignment_type` must be consistent with `option_trade.action`: `LONG_CALL_EXERCISE`/`LONG_PUT_EXERCISE` require BOT; `WRITTEN_PUT_ASSIGNMENT`/`WRITTEN_CALL_ASSIGNMENT` require SLD. Mismatch raises `BusinessRuleError`. | Local Canon (TradeAction enum) | SLD trade + LONG_CALL_EXERCISE → BusinessRuleError |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `packages/core/src/zorivest_core/domain/tax/option_pairing.py` | new | `parse_option_symbol()`, `OptionDetails`, `AssignmentType` enum, `adjust_basis_for_assignment()` |
| `packages/core/src/zorivest_core/domain/tax/__init__.py` | modify | Export new module |
| `packages/core/src/zorivest_core/services/tax_service.py` | modify | Add `pair_option_assignment()` method |
| `tests/unit/test_option_pairing.py` | new | 20–25 tests for symbol parsing + 4 IRS assignment/exercise cases |
| `tests/unit/test_tax_service.py` | modify | Add tests for `pair_option_assignment()` |

---

### MEU-129: YTD P&L by Symbol

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| Year-to-date realized gains/losses per ticker | Spec | domain-model-reference.md A5 |
| Broken down by ST vs LT | Spec | domain-model-reference.md A5 |
| Uses closed lots for the tax year (close_date in year range) | Local Canon | TaxLot entity, close_date field |
| Excludes tax-advantaged accounts | Spec (A7, via MEU-127) | Reuses `get_taxable_gains` filter |
| Depends on gains calculator | Local Canon | MEU-126 gains_calculator.py |

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-129.1 | `compute_ytd_pnl(lots, tax_year)` returns `YtdPnlResult` with per-symbol breakdown and totals | Spec (A5) | Empty lot list returns zero totals |
| AC-129.2 | Each `SymbolPnl` entry has `ticker`, `st_gains`, `lt_gains`, `total_gains`, `lot_count` | Spec (A5) | N/A — structural |
| AC-129.3 | Only lots with `close_date` in the specified `tax_year` are included | Local Canon | Lot closed in different year excluded |
| AC-129.4 | `TaxService.get_ytd_pnl(tax_year)` excludes tax-advantaged accounts and returns structured result | Spec (A5 + A7) | Tax-advantaged lots excluded |
| AC-129.5 | Multiple lots for same ticker are aggregated into single `SymbolPnl` | Spec (A5) | Two AAPL lots produce one AAPL entry |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `packages/core/src/zorivest_core/domain/tax/ytd_pnl.py` | new | `compute_ytd_pnl()` + `SymbolPnl`, `YtdPnlResult` dataclasses |
| `packages/core/src/zorivest_core/domain/tax/__init__.py` | modify | Export new module |
| `packages/core/src/zorivest_core/services/tax_service.py` | modify | Add `get_ytd_pnl()` method |
| `tests/unit/test_ytd_pnl.py` | new | 10–15 tests for aggregation logic |
| `tests/unit/test_tax_service.py` | modify | Add tests for `get_ytd_pnl()` |

---

## Out of Scope

- **Wash Sale Engine** (MEU-130–136) — Phase 3B, separate project
- **Tax API endpoints** (MEU-148) — Phase 3E
- **Tax MCP tools** (MEU-149) — Phase 3E
- **Tax GUI** (MEU-154) — Phase 3E
- **Quarterly estimated payments** (MEU-143–147) — Phase 3D
- **Splitting `capital_loss_carryforward` into ST/LT on `TaxProfile` entity** — deferred to Phase 3D; domain function uses separate params, service allocates from single entity field per IRS Schedule D ordering
- **MEU-128 GUI collision**: `MEU-128` is also assigned to `gui-screenshot` in `06-gui.md:428` and `testing-strategy.md:554`; renumbering deferred to GUI phase — does not block tax domain work
- **Corporate actions** (stock splits, mergers) affecting cost basis — not in Module A spec
- **DRIP wash sale detection** (MEU-134) — Phase 3B

---

## BUILD_PLAN.md Audit

This project updates three MEU status values in `docs/BUILD_PLAN.md` Phase 3A table (lines 618–620). Post-implementation, MEU-127/128/129 move from ⬜ to 🟡. No structural changes to BUILD_PLAN hub references.

```powershell
rg "MEU-127|MEU-128|MEU-129" docs/BUILD_PLAN.md  # Expected: 3 matches in Phase 3A table
```

---

## Verification Plan

### 1. Unit Tests
```powershell
uv run pytest tests/unit/test_loss_carryforward.py tests/unit/test_option_pairing.py tests/unit/test_ytd_pnl.py tests/unit/test_tax_service.py -x --tb=short -v *> C:\Temp\zorivest\pytest-tax-rules.txt; Get-Content C:\Temp\zorivest\pytest-tax-rules.txt | Select-Object -Last 40
```

### 2. Integration Tests
```powershell
uv run pytest tests/integration/test_tax_service_integration.py -x --tb=short -v *> C:\Temp\zorivest\pytest-tax-integ.txt; Get-Content C:\Temp\zorivest\pytest-tax-integ.txt | Select-Object -Last 30
```

### 3. Type Check
```powershell
uv run pyright packages/ *> C:\Temp\zorivest\pyright.txt; Get-Content C:\Temp\zorivest\pyright.txt | Select-Object -Last 30
```

### 4. Lint
```powershell
uv run ruff check packages/ *> C:\Temp\zorivest\ruff.txt; Get-Content C:\Temp\zorivest\ruff.txt | Select-Object -Last 20
```

### 5. MEU Gate
```powershell
uv run python tools/validate_codebase.py --scope meu *> C:\Temp\zorivest\validate.txt; Get-Content C:\Temp\zorivest\validate.txt | Select-Object -Last 50
```

### 6. Full Regression
```powershell
uv run pytest tests/ -x --tb=short -v *> C:\Temp\zorivest\pytest-full.txt; Get-Content C:\Temp\zorivest\pytest-full.txt | Select-Object -Last 40
```

### 7. Anti-Placeholder Scan
```powershell
rg "TODO|FIXME|NotImplementedError" packages/ *> C:\Temp\zorivest\placeholders.txt; Get-Content C:\Temp\zorivest\placeholders.txt
```

---

## Resolved Questions

> [!NOTE]
> All open questions resolved during plan corrections (2026-05-12):
> 1. **IBKR option symbol format**: ✅ Resolved — infrastructure adapters normalize to `"UNDERLYING YYMMDD C/P STRIKE"` before domain layer. Parser targets this format.
> 2. **Carryforward ST/LT split**: ✅ Resolved (Human-approved, Option A) — domain function takes separate ST/LT inputs; service layer allocates total to ST first per IRS Schedule D netting order from the single entity field. Human decision: user approved corrections plan (conversation 65dc5cb3, 2026-05-12).

---

## Research References

- [IRS Publication 550 — Investment Income and Expenses](https://www.irs.gov/publications/p550) — capital loss $3K/$1.5K cap, carryforward rules, options cost basis
- [IRS Schedule D Instructions — Capital Loss Carryover Worksheet](https://www.irs.gov/instructions/i1040sd) — netting order, character retention
- [OCC Options Symbology Initiative (OSI)](https://en.wikipedia.org/wiki/Option_naming_convention) — 21-char symbol format
- [IBKR Tax Optimizer Lot Matching Methods](https://ibkrguides.com/traderworkstation/lot-matching-methods.htm) — cost basis method reference (Phase 3A Sessions 1–2)
