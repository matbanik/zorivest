# Wash Sale Engine Corrections Handoff

> **Date**: 2026-05-13
> **Project**: Phase 3B Wash Sale Engine — Execution Corrections
> **Review**: `2026-05-13-wash-sale-engine-implementation-critical-review.md`
> **Status**: Corrections complete, awaiting Codex validation

---

## Corrections Summary

| # | Finding | Fix | Evidence |
|---|---------|-----|----------|
| C3 | `absorb_loss()` no status guard | Added guard: rejects DESTROYED/RELEASED chains with ValueError | 2 new tests pass |
| C4 | `release_chain()` emits `account_id=""` | Added `account_id: str` parameter | 1 new test passes |
| C1 | Basis over-allocation in multi-replacement | Added `amount: Decimal` parameter to `absorb_loss()`, TaxService passes per-match `disallowed_loss` | 3 new tests pass |
| C2 | IRA destruction not wired in TaxService | Validated existing `scan_cross_account_wash_sales()` wiring + added behavior tests | 2 new tests pass |
| C5 | Service/repo tests are method-existence only | Rewrote service tests as behavior tests, created 9 integration CRUD tests | 17 new tests pass |
| Bonus | Repo `update()` identity map collision | Fixed with `expire_all()` + `merge()` instead of `add()` | test_update passes |

## Changed Files

```diff
# packages/core/src/zorivest_core/domain/tax/wash_sale_chain_manager.py
- absorb_loss(chain, replacement_lot) → absorb_loss(chain, replacement_lot, *, amount=None)
+ Status guard: ValueError if chain is DESTROYED or RELEASED
+ Per-match allocation: uses `amount` param instead of chain.disallowed_amount
- release_chain(chain, replacement_lot_id) → release_chain(chain, replacement_lot_id, *, account_id="")
+ account_id parameter flows through to WashSaleEntry

# packages/core/src/zorivest_core/services/tax_service.py
- mgr.absorb_loss(chain, repl_lot)
+ mgr.absorb_loss(chain, repl_lot, amount=match.disallowed_loss)

# packages/infrastructure/src/zorivest_infra/database/wash_sale_repository.py
- session.add(entry_model) in update() → session.merge(entry_model)
+ session.expire_all() between delete and re-add

# tests/ (new/rewritten)
+ tests/unit/domain/tax/test_wash_sale_chain_manager.py — 6 new tests (C1+C4)
+ tests/unit/domain/tax/test_wash_sale_cross_account.py — 2 fixed tests (C3)
+ tests/unit/services/test_tax_service_wash_sale.py — 8 behavior tests (C2+C5)
+ tests/unit/infrastructure/test_wash_sale_repository.py — 6 protocol tests (C5)
+ tests/integration/test_wash_sale_repo_integration.py — 9 CRUD tests (C5)
```

## Quality Gates

| Gate | Result |
|------|--------|
| Wash sale test suite | 68 passed |
| Full regression | 3273 passed, 23 skipped, 0 failed |
| Pyright (touched files) | 0 errors |
| Ruff (touched files) | All checks passed |
