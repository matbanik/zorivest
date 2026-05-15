---
project: "2026-05-13-wash-sale-engine"
date: "2026-05-13"
source: "docs/build-plan/build-priority-matrix.md §Phase 3B, domain-model-reference.md Module B"
meus: ["MEU-130", "MEU-131", "MEU-132"]
status: "draft"
template_version: "2.0"
---

# Implementation Plan: Phase 3B — Wash Sale Engine

> **Project**: `2026-05-13-wash-sale-engine`
> **Build Plan Section(s)**: build-priority-matrix.md §3B (Items 57–59), domain-model-reference.md Module B (B1–B3)
> **Status**: `draft`

---

## Goal

Implement the core wash sale detection engine for Zorivest's tax module. This project introduces the `WashSaleChain` entity, a 30-day window detection algorithm, chain lifecycle state management (disallowed → absorbed → released), and cross-account wash sale aggregation including IRA permanent loss destruction. This is pure domain + infrastructure work — no API/MCP/GUI changes.

The engine enables Zorivest to:
1. Detect wash sales automatically when lots are closed at a loss
2. Defer disallowed losses by adjusting replacement lot cost basis
3. Track loss chains through multiple wash sale cycles
4. Aggregate wash sales across all accounts (taxable + IRA + spouse)
5. Flag permanently destroyed losses when IRA accounts are involved

---

## User Review Required

> [!IMPORTANT]
> **Q1: 401(k) Treatment** — IRS Publication 550 explicitly discusses IRAs and Roth IRAs for permanent loss destruction. The 401(k) has the same structural issue (no individual lot basis tracking) but is not explicitly named by the IRS. This plan implements IRA-only destruction. K401 treatment is deferred as a blocked task pending human approval.

---

## Proposed Changes

### MEU-130: Wash Sale Detection (Matrix Item 57)

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-130.1 | `WashSaleChain` mutable dataclass with 8 fields: `chain_id`, `ticker`, `loss_lot_id`, `loss_date`, `loss_amount`, `disallowed_amount`, `status`, `entries` | Spec (domain-model-reference.md B1) | Missing required fields raise TypeError |
| AC-130.2 | `WashSaleEntry` frozen dataclass with 7 fields: `entry_id`, `chain_id`, `event_type`, `lot_id`, `amount`, `event_date`, `account_id` | Spec (domain-model-reference.md B1) | — |
| AC-130.3 | `WashSaleStatus` enum: `DISALLOWED`, `ABSORBED`, `RELEASED`, `DESTROYED` | Spec ("disallowed → absorbed → released") + Research-backed (IRA destruction) | Invalid status string raises ValueError |
| AC-130.4 | `WashSaleEventType` enum: `LOSS_DISALLOWED`, `BASIS_ADJUSTED`, `CHAIN_CONTINUED`, `LOSS_RELEASED`, `LOSS_DESTROYED` | Spec (B2 chain events) | — |
| AC-130.5 | `detect_wash_sales()` pure function: given a loss lot + candidate replacement lots, returns `list[WashSaleMatch]` for securities purchased within ±30 calendar days (61-day window) | Research-backed (IRS Pub 550: 30 days before + sale day + 30 days after) | Sale with no repurchase within window → empty list |
| AC-130.6 | Detection matches by ticker (same symbol = substantially identical for this MEU) | Spec (B1: "substantially identical") | Different tickers → no match |
| AC-130.7 | Partial wash sale support: sell 100 shares at loss, buy 50 back → 50 shares' loss disallowed, 50 allowed | Research-backed (IRS Pub 550 proportional rule) | Full quantity → full disallowance |
| AC-130.8 | `WashSaleChainRepository` protocol with `get`, `save`, `update`, `list_for_ticker`, `list_active` | Local Canon (ports.py pattern) | — |
| AC-130.9 | `WashSaleChainModel` + `WashSaleEntryModel` SQLAlchemy models in `database/wash_sale_models.py` | Local Canon (database/ package pattern) | — |
| AC-130.10 | `SqlWashSaleChainRepository` in `database/wash_sale_repository.py` with full CRUD | Local Canon (database/ package pattern) | Non-existent chain_id returns None |
| AC-130.11 | UoW wired: `wash_sale_chains` attribute on `UnitOfWork` | Local Canon (ports.py UoW pattern) | — |

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| 61-day window (30+1+30) | Research-backed | IRS Pub 550: "30 days before or after the date of the sale" = 61-day total window |
| Substantially identical = same ticker | Spec | domain-model-reference.md B1. Options matching deferred to MEU-133 |
| Partial wash sale proportionality | Research-backed | IRS Pub 550: "If the number repurchased differs from sold, adjustment is proportional" |
| WashSaleChain vs flat entries | Spec | B2: "Track full chain until resolved" → parent Chain + child Entries |
| Entity mutability | Local Canon | TaxLot is mutable (open/close lifecycle); WashSaleChain needs `status` mutation → mutable dataclass. WashSaleEntry is an immutable event record → frozen dataclass. |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `packages/core/src/zorivest_core/domain/enums.py` | modify | Add `WashSaleStatus`, `WashSaleEventType` enums |
| `packages/core/src/zorivest_core/domain/tax/wash_sale.py` | new | `WashSaleChain` (mutable), `WashSaleEntry` (frozen) dataclasses |
| `packages/core/src/zorivest_core/domain/tax/wash_sale_detector.py` | new | `detect_wash_sales()` pure function, `WashSaleMatch` result type |
| `packages/core/src/zorivest_core/domain/tax/__init__.py` | modify | Export new entities |
| `packages/core/src/zorivest_core/application/ports.py` | modify | Add `WashSaleChainRepository` protocol, wire into `UnitOfWork` |
| `packages/infrastructure/src/zorivest_infra/database/wash_sale_models.py` | new | `WashSaleChainModel`, `WashSaleEntryModel` |
| `packages/infrastructure/src/zorivest_infra/database/wash_sale_repository.py` | new | `SqlWashSaleChainRepository` |
| `packages/infrastructure/src/zorivest_infra/database/unit_of_work.py` | modify | Add `wash_sale_chains` repo attribute |
| `tests/unit/domain/tax/test_wash_sale.py` | new | Entity tests |
| `tests/unit/domain/tax/test_wash_sale_detector.py` | new | Detection algorithm tests (10+ cases) |
| `tests/unit/infrastructure/test_wash_sale_repository.py` | new | Repository integration tests |

---

### MEU-131: Wash Sale Chain Tracking (Matrix Item 58)

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-131.1 | `WashSaleChainManager` class with `start_chain()`, `absorb_loss()`, `release_chain()`, `continue_chain()` methods | Spec (B2: "disallowed → absorbed → released") | — |
| AC-131.2 | `start_chain()`: creates chain with DISALLOWED status + LOSS_DISALLOWED entry | Spec | — |
| AC-131.3 | `absorb_loss()`: adjusts replacement lot's `wash_sale_adjustment` field, adds BASIS_ADJUSTED entry, sets status to ABSORBED | Research-backed (IRS Pub 550: disallowed loss added to replacement basis) | — |
| AC-131.4 | `absorb_loss()` tacks holding period: sets replacement lot `open_date` to original lot `open_date` | Research-backed (IRS Pub 550: holding period tacking rule) | — |
| AC-131.5 | `release_chain()`: sets status to RELEASED + LOSS_RELEASED entry when replacement lot sold without new wash sale | Spec (B2: "released") | Cannot release a chain that is not ABSORBED |
| AC-131.6 | `continue_chain()`: extends chain when replacement lot sold at loss triggers ANOTHER wash sale, adds CHAIN_CONTINUED entry | Spec (B2: "deferred losses that roll forward through repeated trades") | — |
| AC-131.7 | `get_trapped_losses()`: returns all chains in ABSORBED status (losses that can't be deducted this year) | Spec (B2: "Show trapped losses that can't be deducted this year") | No active chains → empty list |
| AC-131.8 | TaxService integration: `detect_and_apply_wash_sales()` method on TaxService that orchestrates detection + chain creation + basis adjustment via UoW | Local Canon (TaxService orchestration pattern) | — |

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| State machine transitions | Spec | B2: "disallowed → absorbed → released" — 3-state + DESTROYED from B3 |
| Holding period tacking | Research-backed | IRS Pub 550: "holding period of the old stock is added to the new stock" |
| Chain continuation on re-triggered wash sale | Spec | B2: "Deferred losses that roll forward through repeated trades" |
| Trapped losses display | Spec | B2: "Show trapped losses that can't be deducted this year" |
| TaxService method name | Local Canon | Follows `simulate_impact`, `get_taxable_gains` pattern |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `packages/core/src/zorivest_core/domain/tax/wash_sale_chain_manager.py` | new | Chain state machine: start, absorb, release, continue |
| `packages/core/src/zorivest_core/services/tax_service.py` | modify | Add `detect_and_apply_wash_sales()`, `get_trapped_losses()` methods |
| `tests/unit/domain/tax/test_wash_sale_chain_manager.py` | new | State machine tests (8+ cases) |
| `tests/unit/services/test_tax_service_wash_sale.py` | new | TaxService wash sale integration tests |

---

### MEU-132: Cross-Account Wash Sale Aggregation (Matrix Item 59)

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-132.1 | `detect_wash_sales()` extended to accept lots from multiple accounts | Spec (B3: "Check ALL accounts") | — |
| AC-132.2 | Detection scans all accounts in the user's filing scope (taxable, IRA, and spousal accounts when enabled) for replacement purchases | Spec (B3: "taxable + IRA + spouse accounts") | Single-account user → still works (no cross-account match) |
| AC-132.3 | When replacement purchase is in IRA (`AccountType.IRA`), chain status = DESTROYED + LOSS_DESTROYED entry | Research-backed (IRS Pub 550: "loss is permanently disallowed" for IRA wash sales) | Taxable-to-taxable wash sale → DISALLOWED (not DESTROYED) |
| AC-132.4 | `WashSaleChainManager.destroy_chain()` method: sets status DESTROYED, adds LOSS_DESTROYED entry, does NOT adjust replacement lot basis (loss is gone) | Research-backed (IRS Pub 550: "cannot add to cost basis in IRA") | Attempting to absorb after destroy raises BusinessRuleError |
| AC-132.5 | `TaxService.scan_cross_account_wash_sales()` method: given a tax year, scans all accounts for wash sale violations | Spec (B3) | No accounts → empty result |
| AC-132.6 | Cross-account detection identifies the account_id on each WashSaleEntry | Spec (B3: need to know which account triggered the wash sale) | — |
| AC-132.7 | Spousal accounts included when `TaxProfile.include_spousal_accounts = True` | Spec (B7: "spouse's accounts must be checked when filing jointly") | `include_spousal_accounts = False` → spouse accounts excluded |

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| IRA = permanent loss destruction | Research-backed | IRS Pub 550: "If you sell stock at a loss and your IRA buys the same stock, the loss is permanently disallowed" |
| 401(k) treatment | Deferred | IRS Pub 550 does not explicitly name 401(k). Same structural rationale as IRA but requires human approval before implementation. Blocked task added. |
| Spousal account toggle | Spec | domain-model-reference.md B7 + TaxProfile.include_spousal_accounts field already exists |
| Cross-account scan method | Local Canon | TaxService.scan_* pattern for batch operations |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `packages/core/src/zorivest_core/domain/tax/wash_sale_detector.py` | modify | Extend for multi-account lot scanning |
| `packages/core/src/zorivest_core/domain/tax/wash_sale_chain_manager.py` | modify | Add `destroy_chain()` method |
| `packages/core/src/zorivest_core/services/tax_service.py` | modify | Add `scan_cross_account_wash_sales()` method |
| `tests/unit/domain/tax/test_wash_sale_cross_account.py` | new | Cross-account detection tests (8+ cases) |
| `tests/unit/domain/tax/test_wash_sale_detector.py` | modify | Add multi-account scenarios |
| `tests/unit/services/test_tax_service_wash_sale.py` | modify | Add cross-account integration tests |

---

## Out of Scope

- **MEU-133**: Options-to-stock wash sale matching (Conservative/Aggressive toggle) — separate MEU
- **MEU-134**: DRIP wash sale detection — separate MEU
- **MEU-135**: Auto-rebalance + spousal cross-wash warnings — separate MEU
- **MEU-136**: Wash sale prevention alerts (proactive) — separate MEU
- **API/MCP/GUI wiring**: Phase 3E (MEU-148/149/154)
- **Form 8949 reporting**: Phase 3E reports

---

## BUILD_PLAN.md Audit

This project does not introduce new build-plan sections. Phase 3B already exists in BUILD_PLAN.md (L622-632). However, the P3 summary count at L773 shows `34 | 0` but Phase 3A has 7 ✅ MEUs — this stale count needs correction as part of this project.

```powershell
rg "wash-sale-engine" docs/BUILD_PLAN.md *> C:\Temp\zorivest\bp-audit.txt; Get-Content C:\Temp\zorivest\bp-audit.txt
```

Correction task: Update L773 from `34 | 0` to `34 | 7` (Phase 3A completions). After this project, update to `34 | 10` (adding MEU-130/131/132).

---

## Verification Plan

### 1. Unit Tests (per-MEU)
```powershell
uv run pytest tests/unit/domain/tax/ -x --tb=short -v *> C:\Temp\zorivest\pytest-wash-sale.txt; Get-Content C:\Temp\zorivest\pytest-wash-sale.txt | Select-Object -Last 40
```

### 2. Service Integration Tests
```powershell
uv run pytest tests/unit/services/test_tax_service_wash_sale.py -x --tb=short -v *> C:\Temp\zorivest\pytest-tax-svc-ws.txt; Get-Content C:\Temp\zorivest\pytest-tax-svc-ws.txt | Select-Object -Last 40
```

### 3. Repository Integration Tests
```powershell
uv run pytest tests/unit/infrastructure/test_wash_sale_repository.py -x --tb=short -v *> C:\Temp\zorivest\pytest-ws-repo.txt; Get-Content C:\Temp\zorivest\pytest-ws-repo.txt | Select-Object -Last 40
```

### 4. Type Check
```powershell
uv run pyright packages/ *> C:\Temp\zorivest\pyright.txt; Get-Content C:\Temp\zorivest\pyright.txt | Select-Object -Last 30
```

### 5. Lint
```powershell
uv run ruff check packages/ *> C:\Temp\zorivest\ruff.txt; Get-Content C:\Temp\zorivest\ruff.txt | Select-Object -Last 20
```

### 6. Full Regression
```powershell
uv run pytest tests/ -x --tb=short -v *> C:\Temp\zorivest\pytest-full.txt; Get-Content C:\Temp\zorivest\pytest-full.txt | Select-Object -Last 40
```

### 7. MEU Gate
```powershell
uv run python tools/validate_codebase.py --scope meu *> C:\Temp\zorivest\validate.txt; Get-Content C:\Temp\zorivest\validate.txt | Select-Object -Last 50
```

---

## Open Questions

> [!WARNING]
> **Q1: 401(k) permanent loss destruction** — IRS Pub 550 explicitly names IRAs and Roth IRAs. Should 401(k) accounts (`AccountType.K401`) also trigger permanent loss destruction? This plan defers K401 treatment as a blocked task until human approval is recorded.

---

## Research References

- IRS Publication 550 (Investment Income and Expenses): 30-day window, substantially identical securities, partial wash sale proportionality, holding period tacking
- Sources: Schwab, Fidelity, Tradelog, H&R Block, JP Morgan (all confirming Pub 550 interpretation)
- domain-model-reference.md Module B (B1-B3, B7)
- build-priority-matrix.md §Phase 3B (Items 57-59)
