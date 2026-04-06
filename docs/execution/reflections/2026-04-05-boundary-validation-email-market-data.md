# Reflection — Boundary Validation: Email + Market Data (BV4+BV5)

> **Date**: 2026-04-05
> **Project**: `2026-04-05-boundary-validation-email-market-data`
> **MEUs**: MEU-BV4, MEU-BV5

## What Went Well

1. **Plan review caught two real spec-drift issues** — Codex correctly identified that the plan's `security` Literal included an unsupported `NONE` value and that `provider_preset` should be a closed set, not free-form string. Both were genuine improvements.
2. **TDD discipline continued strong** — Red→Green cycle was clean: 6/7 fail for BV4, 9/11 fail for BV5 (expected regression guards passed).
3. **Pattern reuse** — The `_strip_whitespace` + `StrippedStr` + `ConfigDict(extra="forbid")` pattern from BV1–BV3 required zero invention for BV4. BV5 extended it with `Literal` constraints.
4. **Combined project efficiency** — Scoping BV4+BV5 together saved context-establishment overhead.

## What Could Improve

1. **Known issues tracking gap** — The pre-existing `test_delete_without_trades_succeeds` failure in `test_account_service.py` wasn't in `known-issues.md`. Should have been caught earlier. *(Resolved: stub fix applied in Recheck 1.)*
2. **Pyright pre-existing errors not tracked with specific test names** — The known-issues entry documents file:line but not test names for quick exclusion.
3. **Env var hygiene in test modules** — Module-level `os.environ` assignments in `test_api_roundtrip.py` and `test_gui_api_seams.py` caused `[TEST-ISOLATION]` flakiness across 3 rechecks before root-causing. *(Resolved: fixture-based cleanup in Recheck 4.)*
4. **Evidence metrics not refreshed after corrections** — Initial "211 passed" count persisted in task/reflection after the underlying failures were fixed, triggering reviewer `changes_required` on evidence integrity. *(Resolved: metrics refreshed across all artifacts.)*

## Metrics

| Metric | BV4 | BV5 | Total |
|--------|-----|-----|-------|
| Tests added | 7 | 11 | 18 |
| Files modified | 2 | 2 | 4 |
| Red phase failures | 6 | 9 | 15 |
| Green phase passes | 21 | 23 | 44 |
| Full regression | — | — | 1718 passed, 0 failures (excl. [TEST-DRIFT-MDS]) |

## Boundary Validation Progress

| Finding | Status | MEU | Handoff |
|---------|--------|-----|---------|
| F1 Accounts | ✅ | BV1 | 098 |
| F2 Trades | ✅ | BV2 | 099 |
| F3 Plans | ✅ | BV3 | 100 |
| F4 Scheduling | ⬜ | — | — |
| F5 Market Data | ✅ | BV4 | 101 |
| F6 Email Settings | ✅ | BV5 | 102 |
| F7 Watchlists | ⬜ | — | — |
| Settings | ⬜ | — | — |

## Post-Completion Correction Passes

> Four Codex review rechecks were required to achieve a fully green repo gate.

| Recheck | Date | Finding | Resolution |
|---------|------|---------|------------|
| 1 | 2026-04-05 | `test_delete_without_trades_succeeds` — unstubbed `trade_plans.count_for_account` on MagicMock | Added `count_for_account.return_value = 0` stubs to 3 test methods across 2 files |
| 2 | 2026-04-05 | `test_unlock_propagates_db_unlocked` — 403→200 after env var leak | Identified as `[TEST-ISOLATION]` — `ZORIVEST_DEV_UNLOCK` set at module import, never cleaned |
| 3 | 2026-04-05 | `test_market_data_service.py` — 5 tests fail on wiring mismatch | Classified as pre-existing `[TEST-DRIFT-MDS]` from MEU-91, not introduced by BV4/BV5 |
| 4 | 2026-04-06 | `[TEST-ISOLATION]` root cause fix | Added module-scoped autouse cleanup fixtures in `test_api_roundtrip.py`, `test_gui_api_seams.py`, and defensive clear in `test_api_foundation.py` |

### Lessons from Correction Passes

1. **Module-level `os.environ` is toxic in pytest** — env vars set at import time leak across test modules. Always use fixtures with cleanup.
2. **Pre-existing failures must be enumerated exhaustively before declaring gate green** — the initial "211 passed, 1 fail" claim hid the fact that `-x` stopped before reaching 5 additional failures in `test_market_data_service.py`.
3. **Evidence metrics must be refreshed after every correction** — stale counts erode reviewer trust and trigger unnecessary recheck cycles.
