# MEU-66: TradePlan Entity + Service + API

## Task

- **Date:** 2026-03-12
- **Task slug:** trade-plan-entity-service-api
- **Owner role:** coder
- **Scope:** TradePlan dataclass, repository port, SqlAlchemy repo, in-memory repo, service methods, REST API routes, app wiring

## Inputs

- User request: Implement TradePlan entity through full stack per build plan
- Specs/docs referenced: `docs/build-plan/domain-model-reference.md` L78-96, `docs/build-plan/01-domain-layer.md`, `docs/build-plan/03-service-layer.md` L387-409
- Constraints: TDD-first, 18 fields per domain-model-reference, computed `risk_reward_ratio`, reuse `ReportService` for plan methods

## Coder Output

- Changed files:
  - `packages/core/src/zorivest_core/domain/entities.py` — +`TradePlan` dataclass (18 fields, `compute_risk_reward()` static method)
  - `packages/core/src/zorivest_core/application/ports.py` — +`TradePlanRepository` Protocol (get/save/list_all/update/delete), +`UoW.trade_plans`
  - `packages/core/src/zorivest_core/services/report_service.py` — +`create_plan()`, `get_plan()`, `list_plans()`, `update_plan()` methods
  - `packages/infrastructure/src/zorivest_infra/database/models.py` — +`risk_reward_ratio` column on `TradePlanModel`
  - `packages/infrastructure/src/zorivest_infra/database/repositories.py` — +`TradePlanModel` import, +`_plan_to_model()`/`_model_to_plan()` mappers, +`SqlAlchemyTradePlanRepository`
  - `packages/infrastructure/src/zorivest_infra/database/unit_of_work.py` — +`SqlAlchemyTradePlanRepository` import and `trade_plans` wiring in `__enter__`
  - `packages/api/src/zorivest_api/routes/plans.py` — **[NEW]** POST/GET/GET/{id}/PUT/{id} endpoints with Pydantic schemas
  - `packages/api/src/zorivest_api/main.py` — +`plan_router` import/registration
  - `packages/api/src/zorivest_api/stubs.py` — +`_InMemoryTradePlanRepo` class, +`trade_plans` on `StubUnitOfWork`
  - `tests/unit/test_entities.py` — +10 tests (construction, defaults, images, R:R bullish/bearish/zero-risk, ConvictionLevel, PlanStatus)
  - `tests/unit/test_report_service.py` — +6 tests (create_plan, get_plan, get_plan None, list_plans, update_plan, update_plan not found)
  - `tests/unit/test_api_plans.py` — **[NEW]** 8 tests (create 201, get 200/404, list 200, update 200/404, wiring integration, linking via PUT)
  - `tests/integration/test_repositories.py` — +5 tests (save+get, get None, list_all, update, delete)
  - `tests/unit/test_ports.py` — Module integrity: 14 → 15 protocols (+TradePlanRepository)
- Design notes: Plan methods live on `ReportService` per 03-service-layer.md L387-409 (single service absorbs reports + plans). `compute_risk_reward()` is a static method on the entity. API routes use `/api/v1/plans` prefix (not nested under trades).
- Commands run: `uv run pytest tests/ -v --tb=short -q`
- Results: 961 passed, 1 skipped

## Tester Output

- Commands run: `uv run pytest tests/ -v --tb=short -q`
- Pass/fail matrix: 961/961 passed, 1 skipped
- Coverage/test gaps: None identified — all CRUD verbs tested at entity, service, repo (in-memory + SqlAlchemy), and API layers
- Evidence bundle location: This handoff
- FAIL_TO_PASS / PASS_TO_PASS result: RED confirmed (AttributeError: `create_plan` before implementation)

## Validation Commands for Codex

```bash
# Unit tests — entity + service + API
uv run pytest tests/unit/test_entities.py tests/unit/test_report_service.py tests/unit/test_api_plans.py tests/unit/test_ports.py -v --tb=short -q

# Integration tests — SqlAlchemy repository
uv run pytest tests/integration/test_repositories.py -v --tb=short -q -k "TradePlan"

# Full regression
uv run pytest tests/ -v --tb=short -q
```

Expected: 961 passed, 1 skipped

## Final Summary

- Status: GREEN — 961 passed, 1 skipped, 0 failures
- Next steps: Handoff to Codex for validation review
