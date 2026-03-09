# Task Handoff

## Task

- **Date:** 2026-03-09
- **Task slug:** api-analytics-bp04es4e
- **Owner role:** coder
- **Scope:** MEU-28 Analytics — 10 analytics stubs, mistakes, fees, real calculator

## Inputs

- User request: Implement MEU-28 per `api-settings-analytics-tax-system` plan
- Specs/docs referenced:
  - `04e-api-analytics.md` §Analytics Routes, §Mistakes, §Fees, §Calculator
  - `docs/execution/plans/2026-03-09-api-settings-analytics-tax-system/implementation-plan.md`
- Constraints:
  - Calculator uses real `calculate_position_size()` from domain (MEU-1) — no stub
  - Calculator does NOT require unlock (pure calculation)
  - Analytics/mistakes/fees gated behind `require_unlocked_db`
  - Stub services return properly shaped empty/default responses

## Coder Output

- Changed files:

| File | Change |
|------|--------|
| `packages/api/src/zorivest_api/routes/analytics.py` | [NEW] 10 analytics endpoints |
| `packages/api/src/zorivest_api/routes/mistakes.py` | [NEW] POST / (201), GET /summary |
| `packages/api/src/zorivest_api/routes/fees.py` | [NEW] GET /summary |
| `packages/api/src/zorivest_api/routes/calculator.py` | [NEW] POST /position-size (real domain) |
| `packages/api/src/zorivest_api/stubs.py` | Added `StubAnalyticsService` (11 methods), `StubReviewService` (3 methods) |
| `packages/api/src/zorivest_api/dependencies.py` | Added `get_analytics_service`, `get_review_service` |
| `packages/api/src/zorivest_api/main.py` | Import + lifespan init + include_router (4 routers) |
| `tests/unit/test_api_analytics.py` | [NEW] 24 unit tests |

- Design notes:
  - **Calculator:** Maps `PositionSizeResult.share_size` → response `shares` field, `account_risk_1r` → `risk_amount`
  - **Stubs:** `StubAnalyticsService` has 11 explicit methods (no `__getattr__`), each returns properly shaped dict

- Commands run:
  - `uv run pytest tests/unit/test_api_analytics.py -q` → 24 passed

## Tester Output

- Pass/fail matrix:

| Test | AC | Result |
|------|-----|--------|
| `test_analytics_tag` | AC-1 | ✅ |
| `test_endpoint_returns_200` (10 params) | AC-2 | ✅ |
| `test_track_mistake_201` | AC-3 | ✅ |
| `test_mistake_summary_200` | AC-3 | ✅ |
| `test_fee_summary_200` | AC-4 | ✅ |
| `test_position_size_200` | AC-5 | ✅ |
| `test_calculator_uses_real_domain` | AC-6 | ✅ |
| `test_analytics_locked_403` | AC-7 | ✅ |
| `test_mistakes_locked_403` | AC-7 | ✅ |
| `test_fees_locked_403` | AC-7 | ✅ |
| `test_calculator_no_unlock_needed` | AC-8 | ✅ |
| `test_expectancy_shape` | AC-9 | ✅ |
| `test_sqn_shape` | AC-9 | ✅ |
| `test_no_overrides_non_500` | AC-10 | ✅ |
| `test_calculator_pure_calculation` | AC-10 | ✅ |

- Negative cases: Mode-gated 403 (analytics, mistakes, fees when locked)
- Anti-placeholder: clean

## Reviewer Output

- Findings by severity: None (pending Codex review)
- Verdict: pending

## Final Summary

- Status: MEU-28 implementation complete, 24 tests passing
- Next steps: Codex validation
