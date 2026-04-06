# Task — Boundary Validation: Email + Market Data (F5+F6)

## MEU-BV4: Market Data Provider Config Boundary

- [x] Write 7 negative tests (AC-MD1–MD7) in `test_market_data_api.py`
- [x] Verify Red phase: all 7 new tests FAIL (6 failed, 1 passed — AC-MD7 regression guard)
- [x] Harden `ProviderConfigRequest` in `market_data.py` (extra="forbid", StrippedStr, Field constraints)
- [x] Verify Green phase: all tests pass (21 passed)

## MEU-BV5: Email Settings Config Boundary

- [x] Write 11 negative tests (AC-EM1–EM11) in `test_api_email_settings.py`
- [x] Verify Red phase: all 11 new tests FAIL (9 failed, 2 passed — AC-EM9 + AC-EM10 regression guards)
- [x] Harden `EmailConfigRequest` in `email_settings.py` (extra="forbid", StrippedStr, Literal, Field constraints)
- [x] Verify Green phase: all tests pass (23 passed)

## Post-MEU Tasks

- [x] Run full regression: 1718 passed, 15 skipped, 0 failures (excluding pre-existing `[TEST-DRIFT-MDS]` in `test_market_data_service.py`)
- [x] Run MEU gate: pyright fails are pre-existing (`account_service.py`, `trade_service.py`); ruff/pytest PASS
- [x] Update `docs/BUILD_PLAN.md`: removed F5 warning block, updated F6 on MEU-73 to resolved
- [x] Update `known-issues.md`: BOUNDARY-GAP updated to 5/7 resolved (F1-F3+F5+F6 done)
- [x] Regenerate OpenAPI spec: `--check` passes
- [x] Create handoff 101 (BV4): `101-2026-04-05-boundary-market-data-bp08s8.4.md`
- [x] Create handoff 102 (BV5): `102-2026-04-05-boundary-email-bp06fs6f.md`
- [x] Update MEU registry with BV4/BV5 rows
- [x] Create reflection file: `docs/execution/reflections/2026-04-05-boundary-validation-email-market-data.md`
- [x] Save session state to pomera_notes (ID: 745)
- [x] Prepare commit messages

## Correction Passes (Post-Initial Completion)

- [x] Recheck 1: Fix `test_delete_without_trades_succeeds` — stub `trade_plans.count_for_account` (handoff 101/102 corrections)
- [x] Recheck 2: Fix `test_unlock_propagates_db_unlocked` env var leak — identified as separate `[TEST-ISOLATION]` issue
- [x] Recheck 3: Confirmed `test_market_data_service.py` failure is pre-existing `[TEST-DRIFT-MDS]` from MEU-91
- [x] Recheck 4: Resolved `[TEST-ISOLATION]` — added module-scoped env var cleanup fixtures in 3 test files
- [x] Evidence refresh: Updated task/reflection/handoff metrics to match validated state (1718 passed, 0 failures)
