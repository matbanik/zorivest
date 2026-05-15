# IRS Constants Externalization Analysis

> **Date:** 2026-05-14  
> **Triggered by:** Phase 3E Tax GUI stabilization — discovered MEU-156 blocked on missing persistence API  
> **Related issues:** [TAX-PROFILE-BLOCKED], [TAX-HARDCODED-IRS]

---

## Problem Statement

All IRS-dependent tax values are hardcoded as Python dict literals and module-level constants across 4 source files. Adding a new tax year (e.g., 2027) requires editing Python source, redeploying, and running tests — rather than updating a data file or settings page. No MEU, build plan section, or spec covers externalization of these constants.

---

## Complete Inventory of Hardcoded IRS Constants

### 1. `brackets.py` — Federal Income Tax Brackets (🔴 Annual IRS updates)

| Constant | Lines | Count | Update Cadence | IRS Source |
|----------|-------|-------|----------------|-----------|
| `_FEDERAL_BRACKETS` | 29–107 | 56 threshold/rate pairs (7 brackets × 4 filing statuses × 2 years) | **Annual** — IRS Rev. Proc. | Rev. Proc. 2024-40 (2025), Rev. Proc. 2025-32 (2026) |
| `_LTCG_BRACKETS` | 113–158 | 24 threshold/rate pairs (3 brackets × 4 filing statuses × 2 years) | **Annual** | Same Rev. Proc. |
| `PENALTY_RATES` | 164–167 | 1 rate per year | **Quarterly** — IRS Rev. Rul. | Fed short-term rate + 3% |
| `SUPPORTED_YEARS` | 171 | Derived from bracket keys | Derived | — |

**Risk**: Every January, IRS publishes new bracket thresholds via Revenue Procedure. Currently requires a code change to `brackets.py` to add a new year's data.

### 2. `niit.py` — Net Investment Income Tax (🟡 Statutory, fixed since 2013)

| Constant | Line | Value | Update Cadence | IRS Source |
|----------|------|-------|----------------|-----------|
| `NIIT_RATE` | 27 | `Decimal("0.038")` (3.8%) | Statutory — IRC §1411 | Fixed since 2013 |
| `NIIT_THRESHOLDS` | 30–35 | $200K single, $250K MFJ, $125K MFS, $200K HoH | Statutory — NOT inflation-adjusted | IRC §1411(b) |
| `_PROXIMITY_ALERT_PCT` | 38 | 10% | Internal design choice | — |

**Risk**: Low — these haven't changed since 2013. However, congressional proposals to index NIIT thresholds periodically resurface. If changed, requires code edit.

### 3. `quarterly.py` — Quarterly Estimated Tax (🟡 Statutory)

| Constant | Line | Value | Update Cadence | IRS Source |
|----------|------|-------|----------------|-----------|
| `ANNUALIZATION_FACTORS` | 29–34 | [4, 2.4, 1.5, 1] | Statutory — Form 2210 Schedule AI | Math-derived |
| `_HIGH_AGI_THRESHOLD` | 37 | $150,000 | Statutory — IRS §6654 | NOT inflation-adjusted |
| `_HIGH_AGI_THRESHOLD_MFS` | 38 | $75,000 | Statutory — IRS §6654 | NOT inflation-adjusted |
| Due dates | 199–204 | Apr 15, Jun 15, Sep 15, Jan 15 | Statutory — IRS §6654(c)(2) | Adjusted for weekends/holidays |

**Risk**: Medium — due dates can shift for federal holidays (e.g., Emancipation Day in DC moves Apr 15 → Apr 17). The current implementation handles weekends but not holiday overrides.

### 4. `loss_carryforward.py` — Capital Loss Deduction Cap (🟢 Statutory since 1978)

| Constant | Line | Value | Update Cadence | IRS Source |
|----------|------|-------|----------------|-----------|
| `_CAP_DEFAULT` | 20 | $3,000 | Statutory — IRS §1211(b) | Unchanged since 1978 |
| `_CAP_MARRIED_SEPARATE` | 21 | $1,500 | Statutory — IRS §1211(b) | Unchanged since 1978 |

**Risk**: Very low — hasn't changed in 48 years. Proposals to increase exist but never pass.

---

## Classification by Update Risk

### Category A: Changes annually by IRS inflation adjustment (MUST externalize)

| Item | Current Location | Values per Year |
|------|-----------------|----------------|
| Federal income tax bracket thresholds | `brackets.py` `_FEDERAL_BRACKETS` | 28 (7 × 4 filing statuses) |
| LTCG rate thresholds | `brackets.py` `_LTCG_BRACKETS` | 12 (3 × 4 filing statuses) |
| Underpayment penalty rate | `brackets.py` `PENALTY_RATES` | 1 (changes quarterly) |

**Total: ~41 values change every year.**

### Category B: Statutory, rarely changes but could (SHOULD externalize)

| Item | Current Location | Risk |
|------|-----------------|------|
| NIIT rate (3.8%) | `niit.py` | Congressional action |
| NIIT thresholds ($200K/$250K/$125K) | `niit.py` | Congressional indexing proposals |
| Safe harbor AGI thresholds ($150K/$75K) | `quarterly.py` | Congressional action |
| Capital loss caps ($3K/$1.5K) | `loss_carryforward.py` | Congressional action |
| LTCG rate percentages (0%, 15%, 20%) | `brackets.py` | Congressional action |

### Category C: Structural/algorithmic (keep in code)

| Item | Reason to Keep |
|------|---------------|
| Annualization factors [4, 2.4, 1.5, 1] | Math-derived from IRS form structure |
| Due dates (Apr 15, Jun 15, Sep 15, Jan 15) | Statutory, only holiday overrides vary |
| 366-day holding period classification | IRC definition, won't change |

---

## What Exists Today

| Concern | Status | MEU | Covers |
|---------|--------|-----|--------|
| User's tax profile (filing status, state, elections) | ✅ Planned | MEU-148a | 12 user-specific settings |
| Tax Profile Settings GUI page | ✅ Placeholder | 06f §P3 | TaxProfile fields only |
| IRS annual bracket tables | ❌ Not planned | — | 80+ threshold/rate pairs |
| IRS scalar constants (NIIT, penalty, caps) | ❌ Not planned | — | ~6 values |
| Tax Schedule admin GUI page | ❌ Not planned | — | No way to view/edit brackets |

**Key distinction**: MEU-148a covers the *user's personal* tax configuration. It does NOT cover the *IRS reference data* that the tax engine computes against. These are two separate concerns:

```
User-specific settings (MEU-148a)     IRS reference data (gap)
├── filing_status                     ├── Federal bracket table (per year)
├── state / state_tax_rate            ├── LTCG bracket table (per year)
├── tax_year                          ├── NIIT rate & thresholds
├── section_475_elected               ├── Penalty rate (per year/quarter)
├── section_1256_eligible             ├── Capital loss deduction caps
├── wash_sale_method                  └── Safe harbor AGI thresholds
├── default_cost_basis
├── prior_year_tax
├── agi_estimate
└── capital_loss_carryforward
```

---

## Design Options Evaluated

### Option A: Database-backed Tax Schedule table
- Store bracket tables, NIIT rates, penalty rates in a `tax_schedules` DB table
- API endpoint to CRUD these values
- Admin GUI page ("Tax Schedule Management")
- **Pro**: No code changes needed for new tax year
- **Con**: Complex migration, risk of user entering wrong values, need seed data

### Option B: JSON/YAML configuration file
- Move constants to `data/irs/federal_brackets_2025.json` etc.
- Load at startup, cache in memory
- **Pro**: Easy to update, versionable, ship with releases
- **Con**: Requires app restart or hot-reload; no GUI editing

### Option C: Settings Registry with `irs.*` namespace
- Register all IRS constants as settings keys (like MEU-148a does for TaxProfile)
- Seed defaults from current hardcoded values
- **Pro**: Consistent with existing architecture, GUI can edit
- **Con**: SettingsRegistry is flat key-value — bracket tables (7 rows × 4 statuses) are complex nested data

### Option D: Hybrid (Recommended) ✅
- **JSON data files** (`data/irs/federal_brackets_{year}.json`) for complex tabular data that changes annually
- **SettingsRegistry** (`irs.*` keys) for simple scalar constants that rarely change but should be overridable
- **REST endpoints** for reading/writing schedule data per year
- **Tax Schedule GUI page** separate from Tax Profile page
- **Pro**: Best of both worlds — complex data in structured files, simple overrides in settings
- **Con**: Two storage patterns (acceptable given different data shapes)

---

## Recommended MEU: 148b `tax-schedule-data`

**Phase**: 3E (Reports, Dashboard & API/MCP/GUI)  
**Matrix item**: 75b (after 75a TaxProfile CRUD, before 76 Tax MCP tools)  
**Dependencies**: MEU-18 ✅ (SettingsRegistry), MEU-124 ✅ (TaxProfile entity), MEU-148 ✅ (Tax API)

### Scope

1. **Extract bracket tables** from `brackets.py` → JSON data files in `data/irs/`
2. **Register scalar constants** (NIIT rate, penalty rate, deduction caps) in SettingsRegistry with `irs.*` namespace
3. **Add REST endpoints**: `GET /api/v1/tax/schedule/{year}`, `PUT /api/v1/tax/schedule/{year}`
4. **Add Tax Schedule settings page** (separate from Tax Profile)
5. **Refactor domain modules** to load from data layer instead of dict literals
6. **Add "Clone to New Year" functionality** for creating next year's schedule from current year

### Settings Page Structure

```
Settings
├── Tax Profile          ← MEU-148a (user's personal config)
│   ├── Filing Status
│   ├── State / Tax Year
│   ├── Section Elections (475, 1256, Forex)
│   └── Cost Basis Default
│
└── Tax Schedule         ← MEU-148b (IRS reference data)
    ├── Active Year: [2026 ▼]
    ├── Federal Brackets (7 rows × rate + threshold)
    ├── LTCG Rate Table (3 rows × rate + threshold)
    ├── NIIT Rate & Thresholds
    ├── Quarterly Penalty Rate
    ├── Capital Loss Deduction Caps
    ├── Safe Harbor AGI Thresholds
    └── [Clone to New Year] [Reset to IRS Defaults]
```

### Files Impacted

| File | Change |
|------|--------|
| `brackets.py` | Load `_FEDERAL_BRACKETS`, `_LTCG_BRACKETS`, `PENALTY_RATES` from data source |
| `niit.py` | Load `NIIT_RATE`, `NIIT_THRESHOLDS` from SettingsRegistry |
| `quarterly.py` | Load `_HIGH_AGI_THRESHOLD`, `_HIGH_AGI_THRESHOLD_MFS` from SettingsRegistry |
| `loss_carryforward.py` | Load `_CAP_DEFAULT`, `_CAP_MARRIED_SEPARATE` from SettingsRegistry |
| `data/irs/*.json` | New — bracket table data files per year |
| `routes/tax.py` | New — `/schedule/{year}` endpoints |
| `06f-gui-settings.md` | New — Tax Schedule page spec |

---

## Current Status

- **[TAX-PROFILE-BLOCKED]**: MEU-148a registered in build plan (75a), spec written in `04f-api-tax.md`
- **[TAX-HARDCODED-IRS]**: Tracked in `known-issues.md`, no MEU registered yet
- **Decision**: Deferred — both issues parked for formal planning when Phase 3E work resumes
