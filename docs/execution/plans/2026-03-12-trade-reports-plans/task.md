# Task: Trade Reports & Plans (MEU-53, MEU-66, MEU-67)

## MEU-53 — TradeReport MCP Tools (completion)

- [x] Write RED vitest tests for `create_report` + `get_report_for_trade` MCP tools
- [x] Implement `create_report` tool in `analytics-tools.ts` per 05c spec
- [x] Implement `get_report_for_trade` tool in `analytics-tools.ts` per 05c spec
- [x] Verify: `npx vitest run tests/analytics-tools.test.ts` passes (15/15 ✅)

## MEU-66 — TradePlan Entity + Service + API

- [x] Write RED tests for TradePlan entity (test_entities.py — 10 tests)
- [x] Implement TradePlan dataclass in entities.py (18 fields, computed risk_reward_ratio)
- [x] Add TradePlanRepository Protocol to ports.py + `trade_plans` on UnitOfWork
- [x] Write RED tests for TradePlan repository (test_repositories.py — 5 tests)
- [x] Align existing TradePlanModel — add `risk_reward_ratio` column (models.py)
- [x] Implement SqlAlchemyTradePlanRepository in repositories.py (with mapping helpers)
- [x] Wire trade_plans in unit_of_work.py
- [x] Add `_InMemoryTradePlanRepo` + wire `trade_plans` in StubUnitOfWork (stubs.py)
- [x] Write RED tests for ReportService plan methods (test_report_service.py — 6 tests)
- [x] Implement ReportService plan CRUD (create_plan, get_plan, list_plans, update_plan)
- [x] Write RED tests for TradePlan API routes (test_api_plans.py — 8 tests)
- [x] Implement TradePlan REST endpoints in routes/plans.py (POST, GET, GET/{id}, PUT/{id})
- [x] Register plan_router in main.py
- [x] Add `create_app()` no-override integration test (test_api_plans.py)
- [x] Fix protocol_classes test (14→15 for TradePlanRepository)
- [x] Verify: 961 passed, 1 skipped ✅

## MEU-67 — TradePlan ↔ Trade Linking

> Prerequisite: `create_trade_plan` MCP tool already implemented (MEU-36, handoff 040)

- [x] Write RED tests for link_plan_to_trade service method (test_report_service.py — 3 tests)
- [x] Implement link_plan_to_trade in report_service.py (set linked_trade_id, status→executed)
- [x] Write RED tests for PUT with linked_trade_id (test_api_plans.py — 1 test)
- [x] Verify: link tests pass via existing PUT route from MEU-66 ✅

## Project Closeout

- [x] Full regression: `uv run pytest tests/ -v` — 974 passed, 1 skipped ✅
- [x] BUILD_PLAN.md closeout — updated counts (Total=58), MEU-53/66/67 status rows ✅
- [x] MCP vitest regression: 150 passed ✅
- [x] MEU gate: `uv run python tools/validate_codebase.py --scope meu` ✅
- [x] Create handoff 055 (MEU-53)
- [x] Create handoff 056 (MEU-66)
- [x] Create handoff 057 (MEU-67)
- [x] Update meu-registry.md (MEU-53→✅, MEU-66→✅, MEU-67→✅)
- [x] Reflection file ✅
- [x] Metrics table update ✅
- [x] Pomera session state save (note #480) ✅
- [x] Commit messages prepared ✅
