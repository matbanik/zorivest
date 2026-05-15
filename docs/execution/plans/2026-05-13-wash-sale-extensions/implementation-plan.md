---
project: "2026-05-13-wash-sale-extensions"
date: "2026-05-13"
source: "docs/build-plan/build-priority-matrix.md Items 60–63"
meus: ["MEU-133", "MEU-134", "MEU-135", "MEU-136"]
status: "draft"
template_version: "2.0"
---

# Implementation Plan: Wash Sale Extensions

> **Project**: `2026-05-13-wash-sale-extensions`
> **Build Plan Section(s)**: Phase 3B Items 60–63
> **Status**: `draft`
> **Session**: Phase 3B Session 2 (of proposed 4 sessions)

---

## Goal

Harden the wash sale engine with four specialized extensions that close coverage gaps identified after the core engine (Session 1 / MEUs 130–132) shipped:

1. **Options-to-stock matching** — IRS Pub 550 treats equity options as "substantially identical" to the underlying stock. The current `detect_wash_sales` only matches by ticker. Under CONSERVATIVE mode, a sale of AAPL stock followed by buying an AAPL call option must trigger a wash sale.
2. **DRIP detection** — Automatic dividend reinvestment creates purchases within the 61-day window that brokers don't flag cross-account. We need an `AcquisitionSource` enum on `TaxLot` and logic to warn when a DRIP lot conflicts with a harvested loss.
3. **Rebalance & spousal warnings** — Surface alerts when a pending DCA/rebalance or spousal-account purchase would create a wash sale conflict.
4. **Proactive pre-trade alerts** — Enrich `simulate_impact()` to return "Wait N days" or "This ticker has wash sale risk" before the user commits to a trade.

All four MEUs consume the existing `detect_wash_sales()`, `WashSaleChainManager`, and `scan_cross_account_wash_sales()` from Session 1.

---

## Design Decisions (Resolved)

The following decisions were resolved during planning. Source: `Human-approved` — user reviewed and approved the plan on 2026-05-13.

1. **Options matching scope**: CONSERVATIVE treats equity call/put options on the same underlying as substantially identical per IRS Pub 550 p.58. AGGRESSIVE uses strict CUSIP comparison. Both toggles implemented via `TaxProfile.wash_sale_method`.
2. **DRIP detection default**: `TaxProfile.include_drip_wash_detection` defaults to `True` (already on entity). DRIP lots included in wash sale scans by default.
3. **Spousal accounts**: Existing `include_spousal` parameter on `scan_cross_account_wash_sales()` wired to `TaxProfile.include_spousal_accounts`. No new entity fields needed.
4. **AcquisitionSource enum**: 7 values: `PURCHASE`, `DRIP`, `TRANSFER`, `GIFT`, `INHERITANCE`, `EXERCISE`, `ASSIGNMENT`. Nullable field on `TaxLot` — existing lots have `None` (treated as `PURCHASE` for backward compat).

---

## Proposed Changes

### MEU-133: Options-to-Stock Wash Sale Matching

#### Boundary Inventory

| Surface | Schema Owner | Field Constraints | Extra-Field Policy |
|---------|-------------|-------------------|-------------------|
| Domain function input | `detect_wash_sales()` signature | `wash_sale_method: WashSaleMatchingMethod` (CONSERVATIVE\|AGGRESSIVE) | N/A — pure function |

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-133.1 | `detect_wash_sales()` accepts optional `wash_sale_method` param (default CONSERVATIVE) | Spec: build-priority-matrix.md Item 60 | Invalid enum value raises TypeError |
| AC-133.2 | CONSERVATIVE mode: option on same underlying within 61-day window → wash sale match | Research-backed: IRS Pub 550 p.58 "acquire a contract or option to buy substantially identical stock" | Stock purchase of different underlying → no match |
| AC-133.3 | AGGRESSIVE mode: only exact ticker match triggers wash sale (options ignored unless same CUSIP) | Spec: domain-model-reference.md L391-394 | CONSERVATIVE mode option → match; AGGRESSIVE mode same option → no match |
| AC-133.4 | `parse_option_symbol()` extracts underlying for cross-check against loss lot ticker | Local Canon: option_pairing.py AC-128.1 | Malformed option string → None → skip (no crash) |
| AC-133.5 | `TaxService.detect_and_apply_wash_sales()` passes `TaxProfile.wash_sale_method` to detector | Spec: entity `TaxProfile` field `wash_sale_method` | No TaxProfile → defaults to CONSERVATIVE |
| AC-133.6 | `scan_cross_account_wash_sales()` passes `wash_sale_method` to detector | Spec: build-priority-matrix.md Item 60 | N/A |

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| Options = substantially identical to stock | Research-backed | IRS Pub 550 p.58: "Acquire a contract or option to buy substantially identical stock or securities" |
| CONSERVATIVE vs AGGRESSIVE toggle | Spec | domain-model-reference.md L391-394, `WashSaleMatchingMethod` enum |
| Non-equity options (futures, indices) exempt | Research-backed | IRS Pub 550: Section 1256 contracts exempt from wash sale rule |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `packages/core/src/zorivest_core/domain/tax/wash_sale_detector.py` | modify | Add `wash_sale_method` param, implement option-to-stock matching for CONSERVATIVE mode |
| `packages/core/src/zorivest_core/services/tax_service.py` | modify | Pass `wash_sale_method` from TaxProfile to `detect_wash_sales()` and `scan_cross_account_wash_sales()` |
| `tests/unit/domain/tax/test_wash_sale_detector.py` | modify | Add tests for CONSERVATIVE option matching, AGGRESSIVE skip, malformed options |

---

### MEU-134: DRIP Wash Sale Detection

#### Boundary Inventory

| Surface | Schema Owner | Field Constraints | Extra-Field Policy |
|---------|-------------|-------------------|-------------------|
| Domain enum | `AcquisitionSource(StrEnum)` | 7 values: PURCHASE, DRIP, TRANSFER, GIFT, INHERITANCE, EXERCISE, ASSIGNMENT | N/A |
| Entity field | `TaxLot.acquisition_source` | Optional[AcquisitionSource], default None | N/A |
| Domain function | `detect_wash_sales()` | `include_drip: bool` param | N/A |

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-134.1 | `AcquisitionSource` enum with 7 members defined in `enums.py` | Local Canon: phase3b-meu-grouping-proposal.md "design AcquisitionSource enum defensively with DRIP variant" | Import with invalid value → ValueError |
| AC-134.2 | `TaxLot.acquisition_source: AcquisitionSource | None = None` field added | Spec: build-priority-matrix.md Item 61 | Existing lot creation without field → None (backward compat) |
| AC-134.3 | `detect_wash_sales()` accepts `include_drip: bool = True`; when True, DRIP lots are valid replacement candidates | Research-backed: IRS Pub 550, Fidelity, Schwab — "reinvested dividends count as acquiring substantially identical securities" | `include_drip=False` → DRIP lots excluded from matching |
| AC-134.4 | When a DRIP lot matches as replacement within the 61-day window, the `WashSaleMatch.is_drip_triggered` flag is set | Local Canon: phase3b-meu-grouping-proposal.md "Flag when dividend reinvestment conflicts with harvested loss" | Non-DRIP purchase match → `is_drip_triggered=False` |
| AC-134.5 | `TaxService` passes `TaxProfile.include_drip_wash_detection` to detector | Spec: entity TaxProfile field `include_drip_wash_detection` (default True) | Profile with `include_drip_wash_detection=False` → DRIP lots skipped |

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| DRIP purchases trigger wash sales | Research-backed | IRS Pub 550 p.58; Fidelity "Wash-Sale Rules" — "reinvested dividends via DRIPs count" |
| AcquisitionSource enum values | Local Canon | Defensive enum covering known acquisition types from broker import patterns |
| `TaxLot` field nullable for backward compat | Local Canon | Existing lots → None → treated as PURCHASE in detection logic |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `packages/core/src/zorivest_core/domain/enums.py` | modify | Add `AcquisitionSource` enum |
| `packages/core/src/zorivest_core/domain/entities.py` | modify | Add `acquisition_source` field to `TaxLot` |
| `packages/core/src/zorivest_core/domain/tax/wash_sale_detector.py` | modify | Add `include_drip` param, `is_drip_triggered` on WashSaleMatch |
| `packages/core/src/zorivest_core/services/tax_service.py` | modify | Pass `include_drip_wash_detection` from TaxProfile |
| `packages/infrastructure/src/zorivest_infra/database/models.py` | modify | Add `acquisition_source` column to `TaxLotModel` (line ~878) |
| `packages/infrastructure/src/zorivest_infra/database/tax_repository.py` | modify | Add `acquisition_source` to mapper functions `_lot_model_to_entity` and `_lot_entity_to_model`, and `update()` method |
| `tests/unit/domain/tax/test_wash_sale_detector.py` | modify | DRIP detection tests |
| `tests/unit/infrastructure/test_tax_lot_repository.py` | modify | Round-trip persistence test for `acquisition_source` field |

---

### MEU-135: Auto-Rebalance + Spousal Cross-Wash Warnings

#### Boundary Inventory

| Surface | Schema Owner | Field Constraints | Extra-Field Policy |
|---------|-------------|-------------------|-------------------|
| Domain result type | `WashSaleWarning(frozen dataclass)` | Fields: `warning_type`, `ticker`, `message`, `conflicting_lot_id`, `days_remaining` | N/A |
| Service method | `TaxService.check_wash_sale_conflicts()` | `account_id: str, ticker: str` | N/A |

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-135.1 | `WashSaleWarning` frozen dataclass with 5 fields: `warning_type`, `ticker`, `message`, `conflicting_lot_id`, `days_remaining` | Spec: build-priority-matrix.md Item 62 | N/A |
| AC-135.2 | `WarningType` enum: `REBALANCE_CONFLICT`, `SPOUSAL_CONFLICT`, `DRIP_CONFLICT` | Local Canon: phase3b-meu-grouping-proposal.md "Auto-rebalance conflict detection" | N/A |
| AC-135.3 | `check_wash_sale_conflicts()` returns warnings when recent loss exists and a rebalance/DCA purchase would occur within the 30-day post-sale window | Spec: Item 62 "Warn on DCA/rebalance conflicts" | No recent loss in ticker → empty list |
| AC-135.4 | When `TaxProfile.include_spousal_accounts=True`, spousal account lots included in conflict check | Spec: entity TaxProfile `include_spousal_accounts`, IRS spousal rule | `include_spousal_accounts=False` → spousal lots excluded |
| AC-135.5 | `days_remaining` computed as days until the 30-day post-sale window expires | Research-backed: IRS 30-day window | Loss older than 30 days → 0 days remaining, no warning |

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| Spousal purchases trigger wash sales | Research-backed | IRS Pub 550: "If you sell stock and your spouse... buys substantially identical stock, you also have a wash sale" |
| DCA/rebalance = regular purchase for wash sale purposes | Research-backed | No IRS exemption for automated/scheduled purchases |
| Warning vs enforcement | Spec | Build plan says "warnings" — advisory only, does not block |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `packages/core/src/zorivest_core/domain/tax/wash_sale_warnings.py` | new | `WashSaleWarning`, `WarningType` enum, `check_conflicts()` pure function |
| `packages/core/src/zorivest_core/services/tax_service.py` | modify | Add `check_wash_sale_conflicts()` service method |
| `tests/unit/domain/tax/test_wash_sale_warnings.py` | new | Warning generation tests |
| `tests/unit/services/test_tax_service_wash_sale.py` | modify | Service integration tests for conflict checker |

---

### MEU-136: Wash Sale Prevention Alerts (Proactive Pre-Trade)

#### Boundary Inventory

| Surface | Schema Owner | Field Constraints | Extra-Field Policy |
|---------|-------------|-------------------|-------------------|
| Service method return | `SimulationResult` | New fields: `wash_sale_warnings: list[WashSaleWarning]`, `wait_days: int` | N/A |

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-136.1 | `SimulationResult` gains `wash_sale_warnings: list[WashSaleWarning]` field (default empty) | Spec: build-priority-matrix.md Item 63 | Simulation with no wash conflicts → empty list |
| AC-136.2 | `SimulationResult` gains `wait_days: int = 0` field — days to wait to avoid triggering a wash sale | Spec: Item 63 "Wait N days" | No conflict → `wait_days=0` |
| AC-136.3 | `simulate_impact()` checks if the proposed sale would create a loss on a ticker with a recent purchase in the 61-day window, and populates `wash_sale_warnings` | Spec: Item 63 "This will trigger wash sale" | Proposed sale at gain → no wash risk → no warnings |
| AC-136.4 | `simulate_impact()` calculates `wait_days` as days until the 30-day pre-sale window expires relative to the most recent conflicting purchase | Research-backed: IRS 30-day pre-sale window | Purchase older than 30 days → `wait_days=0` |
| AC-136.5 | Existing `wash_risk: bool` field on `SimulationResult` computed from `len(wash_sale_warnings) > 0` for backward compat | Local Canon: existing field in `SimulationResult` | N/A |

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| Pre-trade wash sale alert | Spec | Build plan: "Pre-trade: 'Wait N days' or 'This will trigger wash sale'" |
| "Wait N days" calculation | Research-backed | 30 days from most recent substantially identical purchase |
| Alert is advisory, does not block execution | Spec | Zorivest imports trade results — never executes trades |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `packages/core/src/zorivest_core/services/tax_service.py` | modify | Enrich `simulate_impact()` with wash sale warnings and wait_days |
| `tests/unit/services/test_tax_service.py` | modify | Tests for pre-trade wash sale alerting |

---

## Out of Scope

- **Inline migration for `acquisition_source` on existing databases** — This domain-only session adds the column to `TaxLotModel` (which `create_all()` picks up for new databases) and updates the mapper/round-trip test. For existing databases, an `ALTER TABLE tax_lots ADD COLUMN acquisition_source TEXT` entry must be added to the `_inline_migrations` list in `packages/api/src/zorivest_api/main.py:243-253`. That file belongs to the API layer (Phase 3E, Items 75–76) and is out of scope for this domain session. The inline migration will be added when the API tax routes wire `acquisition_source` end-to-end.
- **MCP/API exposure of warnings** — Phase 3E (Items 75–76) will wire these to REST + MCP endpoints.
- **GUI rendering of warnings** — Phase 12+ (Item 81) per build plan.
- **Section 1256 contracts** — Futures/broad-based indices exempt from wash sales; out of scope for this session.
- **Cross-broker CUSIP comparison** — Requires identifier resolution (Phase 5 / `IdentifierType`); deferred.

---

## BUILD_PLAN.md Audit

This project does not modify build-plan sections. Items 60–63 are in `build-priority-matrix.md` and will be marked complete in the registry upon validation. No stale refs expected:

```powershell
rg "wash-sale-extensions" docs/BUILD_PLAN.md  # Expected: 0 matches
```

---

## Verification Plan

### 1. Unit Tests (Domain + Service)
```powershell
uv run pytest tests/unit/domain/tax/ tests/unit/services/test_tax_service_wash_sale.py tests/unit/services/test_tax_service.py -x --tb=short -v *> C:\Temp\zorivest\pytest-wash-ext.txt; Get-Content C:\Temp\zorivest\pytest-wash-ext.txt | Select-Object -Last 40
```

### 2. Type Checking
```powershell
uv run pyright packages/core/ *> C:\Temp\zorivest\pyright-wash-ext.txt; Get-Content C:\Temp\zorivest\pyright-wash-ext.txt | Select-Object -Last 30
```

### 3. Lint
```powershell
uv run ruff check packages/core/ *> C:\Temp\zorivest\ruff-wash-ext.txt; Get-Content C:\Temp\zorivest\ruff-wash-ext.txt | Select-Object -Last 20
```

### 4. Anti-Placeholder Scan
```powershell
rg "TODO|FIXME|NotImplementedError" packages/core/src/zorivest_core/domain/tax/ packages/core/src/zorivest_core/services/tax_service.py *> C:\Temp\zorivest\placeholder-wash-ext.txt; Get-Content C:\Temp\zorivest\placeholder-wash-ext.txt
```

### 5. MEU Gate
```powershell
uv run python tools/validate_codebase.py --scope meu *> C:\Temp\zorivest\validate-wash-ext.txt; Get-Content C:\Temp\zorivest\validate-wash-ext.txt | Select-Object -Last 50
```

---

## Open Questions

> [!NOTE]
> All design decisions resolved. See §Design Decisions (Resolved) above for human-approved choices. Spec gaps resolved via IRS Pub 550 research and documented in Spec Sufficiency Tables.

---

## Research References

- [IRS Publication 550 (2025) — Investment Income and Expenses](https://www.irs.gov/publications/p550)
- [Fidelity — Wash-Sale Rules](https://www.fidelity.com/learning-center/personal-finance/wash-sales-rules-tax)
- [Schwab — Primer on Wash Sales](https://www.schwab.com/learn/story/primer-on-wash-sales)
- [TurboTax — Wash Sale Rule](https://turbotax.intuit.com/tax-tips/investments-and-taxes/wash-sale-rule-what-is-it-how-does-it-work-and-more/c5ANd7xnJ)
- [KPMG — Related-Party Wash Sale Transactions (PDF)](https://kpmg.com/kpmg-us/content/dam/kpmg/pdf/2022/wash-sale-transactions-current-law-and-proposals-jotfp-aug-2022.pdf)
- [Tax Portal FAQ — Wash Sale](https://www.taxportalfaq.com/wash-sale)
