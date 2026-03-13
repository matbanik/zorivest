# MEU-67: TradePlan ↔ Trade Linking

## Task

- **Date:** 2026-03-12
- **Task slug:** trade-plan-linking
- **Owner role:** coder
- **Scope:** Service method to link TradePlan to executed Trade, status transition logic

## Inputs

- User request: Implement plan-to-trade linking per build plan
- Specs/docs referenced: `docs/build-plan/03-service-layer.md` L387-409, `docs/build-plan/domain-model-reference.md` L78-96
- Constraints: TDD-first, validates both plan and trade exist, sets `linked_trade_id`, transitions status→`executed`

## Coder Output

- Changed files:
  - `packages/core/src/zorivest_core/services/report_service.py` — +`link_plan_to_trade(plan_id, trade_id)` method
  - `tests/unit/test_report_service.py` — +3 tests (happy path, plan not found, trade not found)
  - `tests/unit/test_api_plans.py` — +1 test (PUT with linked_trade_id + status=executed)
- Design notes: `link_plan_to_trade()` validates both plan and trade exist before linking. Uses `dataclasses.replace()` to create updated entity. Status transitions to `"executed"`. Linking works through existing PUT route for API-level access.
- Commands run: `uv run pytest tests/unit/test_report_service.py -k "link" -v`
- Results: 3/3 passed

## Tester Output

- Commands run: `uv run pytest tests/ -v --tb=short -q`
- Pass/fail matrix: 961/961 passed, 1 skipped
- Coverage/test gaps: None — happy path + both error paths (plan missing, trade missing) covered
- Evidence bundle location: This handoff
- FAIL_TO_PASS / PASS_TO_PASS result: RED confirmed (AttributeError: `link_plan_to_trade` before implementation)

## Validation Commands for Codex

```bash
# Linking tests specifically
uv run pytest tests/unit/test_report_service.py -k "link" -v --tb=short

# API linking test
uv run pytest tests/unit/test_api_plans.py -k "link" -v --tb=short

# Full regression
uv run pytest tests/ -v --tb=short -q
```

Expected: 961 passed, 1 skipped

## Final Summary

- Status: GREEN — 961 passed, 1 skipped, 0 failures
- Next steps: Handoff to Codex for validation review
