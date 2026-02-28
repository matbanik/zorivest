# Corrections — Build Plan Foundation Coding Readiness

## Task

- **Date:** 2026-02-28
- **Task slug:** docs-build-plan-foundation-coding-readiness-corrections
- **Owner role:** coder
- **Scope:** Fix 13 findings from the [coding readiness critical review](2026-02-28-docs-build-plan-foundation-coding-readiness-critical-review.md).
- **Workflow:** `/planning-corrections`

## Summary

Applied 13 corrections (1 Critical, 5 High, 5 Medium, 2 Low) across 5 build plan documentation files. All changes are docs-only — no product code was modified.

### Design Decisions Made

1. **Settings key naming** → Standardized on `display.hide_dollars`/`display.hide_percentages` (negative polarity). Phase 2 SettingModel comments updated to match Phase 2A defaults registry.
2. **Image repository API** → Generic port is canonical (`save(owner_type, owner_id, image)`, `get_for_owner(owner_type, owner_id)`). Phase 2 tests fixed to match.
3. **Passphrase strategy** → Session-held for `restore_backup`/`verify_backup`; explicit param only for `repair_database`. Tests updated accordingly.

## Changed Files

| File | Findings Fixed |
|------|---------------|
| `docs/build-plan/02a-backup-restore.md` | F1 (Critical), F4, F5, F11 |
| `docs/build-plan/02-infrastructure.md` | F2, F3, F9, F10 |
| `docs/build-plan/01-domain-layer.md` | F6 |
| `docs/build-plan/01a-logging.md` | F7, F8 |
| `docs/build-plan/dependency-manifest.md` | F6, F12, F13 |

### Per-Finding Summary

| # | Severity | Fix Applied |
|---|----------|-------------|
| F1 | Critical | Moved validation pipeline (stages 1/2/3) from dead code after `_resolve_spec()` `return None` back into `validate()` method body |
| F2 | High | Changed `display.dollar_visible`/`display.percent_visible` → `display.hide_dollars`/`display.hide_percentages` in Phase 2 SettingModel comments |
| F3 | High | Fixed all 5 `img_repo.save()` calls and 1 `get_for_trade()` call to match generic port signature |
| F4 | High | Removed explicit `passphrase` param from `verify_backup` and `restore_backup` test calls; restructured wrong-passphrase test |
| F5 | High | Added `app_version: str = "0.1.0"` param to `ConfigExportService.__init__` with `self._app_version` init |
| F6 | High | Clarified Phase 1 uses dataclasses (not Pydantic); added note in dependency manifest Phase 1 comment |
| F7 | Medium | Fixed routing comment: `app.jsonl` → `misc.jsonl` |
| F8 | Medium | Replaced `os.uname().sysname == "Darwin"` with `sys.platform == "darwin"` |
| F9 | Medium | Added `[!WARNING]` admonition about Float-vs-Numeric for monetary fields with migration decision |
| F10 | Medium | Added `check_same_thread=False` to test fixture + WAL test guidance comment |
| F11 | Medium | Removed "gzip" from compression setting description (backup uses AES-encrypted ZIP) |
| F12 | Low | Added `pyright` to cross-cutting install command |
| F13 | Low | Removed duplicate `pip-audit` from Phase 7; added comment referencing cross-cutting install |

## Verification Results

| Check | Result |
|-------|--------|
| `rg "display.dollar_visible\|display.percent_visible" docs/build-plan/` | ✅ 0 matches |
| `rg "get_for_trade" docs/build-plan/` | ✅ 1 match in `04a` (service method, not image repo — expected) |
| `rg "os.uname()" docs/build-plan/` | ✅ 0 matches |
| `rg "gzip compression" docs/build-plan/02a-backup-restore.md` | ✅ 0 matches |
| `rg -c "Stage 1: Type validation" docs/build-plan/02a-backup-restore.md` | ✅ 1 (in validate(), dead copy removed) |
| `rg "restore_backup(backup_path,\|verify_backup(backup_path," 02a` | ✅ 0 matches |
| `rg ".agent/context/handoffs" docs/build-plan/` | ✅ 1 match in `mcp-planned-readiness.md` (out of scope) |
| `python tools/validate_build_plan.py` | ✅ 17 errors — all pre-existing in non-target files |

## Recheck Pass (4 residual + 2 cascade)

After the initial 13 corrections, a recheck identified 4 residuals:

| File | Fix |
|------|-----|
| `01-domain-layer.md:191` | Renamed `DisplayModeFlag` enum: `DOLLAR_VISIBLE` → `HIDE_DOLLARS`, `PERCENT_VISIBLE` → `HIDE_PERCENTAGES` |
| `01a-logging.md:258` | Added missing `import sys` (regression from `os.uname()` → `sys.platform` fix) |
| `02-infrastructure.md:362` | Upgraded Float advisory to concrete resolution (6 columns → `Numeric`) |
| `02-infrastructure.md:491,501` | Added `test_wal_concurrency.py` to exit criteria and test plan |

**Cascading drift** found in 2 additional files:

| File | Fix |
|------|-----|
| `input-index.md:212-213,220` | Renamed `dollar_visible`/`percent_visible` → `hide_dollars`/`hide_percentages` |
| `domain-model-reference.md:126,131` | Renamed `dollar_visible`/`percent_visible` → `hide_dollars`/`hide_percentages` |

### Final Verification

`rg "dollar_visible|percent_visible|DOLLAR_VISIBLE|PERCENT_VISIBLE" docs/build-plan/` → **0 matches**. Old naming fully eliminated.

## Float → Numeric Model Migration

After recheck, model snippets were updated to use `Numeric(15, 6)` for all monetary/tax-critical columns. 14 columns migrated across 7 models:

| Model | Columns → Numeric |
|-------|-------------------|
| `TradeModel` | `commission`, `realized_pnl` |
| `BalanceSnapshotModel` | `balance` |
| `RoundTripModel` | `realized_pnl`, `total_commission` |
| `ExcursionMetricsModel` | `mfe_dollars`, `mae_dollars` |
| `TransactionLedgerModel` | `amount` |
| `OptionsStrategyModel` | `net_debit_credit`, `max_profit`, `max_loss` |
| `MistakeEntryModel` | `estimated_cost` |
| `BrokerConfigModel` | `pdt_threshold` |
| `BankTransactionModel` | `amount` |

12 display-only columns remain `Float`: `price`, `quantity`, `entry_price`, `stop_loss`, `target_price`, `entry_avg_price`, `exit_avg_price`, `total_quantity`, `mfe_pct`, `mae_pct`, `bso_pct`, `confidence`.

`Numeric` added to SQLAlchemy import (L16).

## Approval Gate

- **Human approval required for merge/release/deploy:** yes
- **Approval status:** pending
