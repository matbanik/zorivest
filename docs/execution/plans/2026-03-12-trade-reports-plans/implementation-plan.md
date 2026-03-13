# Trade Reports & Plans — MEU-53, MEU-66, MEU-67

Complete deferred TradeReport MCP tools, then build TradePlan entity/service/API with plan→trade linking.

## Spec Sufficiency

### MEU-53 — TradeReport MCP Tools (completion)

| Behavior | Source | Source Location | Resolved? |
|---|---|---|---|
| `create_report` schema (7 params) | Spec | [05c L571-603](file:///p:/zorivest/docs/build-plan/05c-mcp-trade-analytics.md#L571-L603) | ✅ |
| `get_report_for_trade` schema | Spec | [05c L622-642](file:///p:/zorivest/docs/build-plan/05c-mcp-trade-analytics.md#L622-L642) | ✅ |
| Annotations (both tools) | Spec | [05c L606-657](file:///p:/zorivest/docs/build-plan/05c-mcp-trade-analytics.md#L606-L657) | ✅ |
| REST dependency (POST/GET report) | Local Canon | [Handoff 054](file:///p:/zorivest/.agent/context/handoffs/054-2026-03-12-trade-report-api-bp04as4a.md) | ✅ |
| Toolset: `trade-analytics` | Spec | 05c L611, L650 | ✅ |

### MEU-66 — TradePlan Entity + Service

| Behavior | Source | Source Location | Resolved? |
|---|---|---|---|
| TradePlan entity (18 fields, ORM model pre-exists) | Spec | [domain-model-reference L78-96](file:///p:/zorivest/docs/build-plan/domain-model-reference.md#L78-L96) | ✅ |
| PlanStatus enum (5 values) | Spec | [01-domain-layer L179-184](file:///p:/zorivest/docs/build-plan/01-domain-layer.md#L179-L184) | ✅ Already in enums.py |
| ConvictionLevel enum | Spec | [01-domain-layer L173-177](file:///p:/zorivest/docs/build-plan/01-domain-layer.md#L173-L177) | ✅ Already in enums.py |
| ReportService.create_plan() | Spec | [03-service-layer L407-409](file:///p:/zorivest/docs/build-plan/03-service-layer.md#L407-L409) | ✅ |
| Computed risk_reward_ratio | Spec | [05d L96](file:///p:/zorivest/docs/build-plan/05d-mcp-trade-planning.md#L96) | ✅ |
| API: `POST /api/v1/trade-plans` | Spec | [05d L76-99](file:///p:/zorivest/docs/build-plan/05d-mcp-trade-planning.md#L76-L99) | ✅ |
| Dedup: reject identical active plan | Spec | [05d L98](file:///p:/zorivest/docs/build-plan/05d-mcp-trade-planning.md#L98) | ✅ |

### MEU-67 — TradePlan ↔ Trade Linking

| Behavior | Source | Source Location | Resolved? |
|---|---|---|---|
| TradePlan.linked_trade_id (nullable FK) | Spec | [domain-model-reference L93](file:///p:/zorivest/docs/build-plan/domain-model-reference.md#L93) | ✅ |
| TradeReport.followed_plan (bool) | Local Canon | Already in entities.py (MEU-52) | ✅ |
| Status transition ACTIVE→EXECUTED | Spec | [domain-model-reference L92](file:///p:/zorivest/docs/build-plan/domain-model-reference.md#L92) | ✅ |
| `create_trade_plan` MCP tool | Local Canon | Already implemented (MEU-36, [handoff 040](file:///p:/zorivest/.agent/context/handoffs/040-2026-03-10-planning-tools-bp05ds5d.md)) | ✅ Prerequisite |

---

## Proposed Changes

### MEU-53 — TradeReport MCP Tools

#### [MODIFY] [analytics-tools.ts](file:///p:/zorivest/mcp-server/src/tools/analytics-tools.ts)

Add `create_report` and `get_report_for_trade` tool registrations per [05c spec](file:///p:/zorivest/docs/build-plan/05c-mcp-trade-analytics.md#L569-L657):
- `create_report`: POST to `/trades/{trade_id}/report` with 7 params (trade_id, setup_quality, execution_quality, followed_plan, emotional_state, lessons_learned, tags)
- `get_report_for_trade`: GET from `/trades/{trade_id}/report`
- Both use `_meta: { toolset: 'trade-analytics', alwaysLoaded: false }`

#### [NEW] [analytics-tools.test.ts additions](file:///p:/zorivest/mcp-server/tests/analytics-tools.test.ts)

Add vitest tests for report tools:
- `create_report` → success (201), not-found trade (404), duplicate (409)
- `get_report_for_trade` → success (200), not-found (404)

---

### MEU-66 — TradePlan Entity + Service + API

#### [NEW] [entities.py](file:///p:/zorivest/packages/core/src/zorivest_core/domain/entities.py) — `TradePlan` dataclass

Add `TradePlan` dataclass with 18 fields from domain model reference:
- `id`, `ticker`, `direction`, `conviction`, `strategy_name`, `strategy_description`, `entry_price`, `stop_loss`, `target_price`, `entry_conditions`, `exit_conditions`, `timeframe`, `risk_reward_ratio`, `status`, `linked_trade_id`, `images`, `account_id`, `created_at/updated_at`
- Computed `risk_reward_ratio` from entry/stop/target in factory method

> **Note:** ORM model `TradePlanModel` already exists at [models.py L107-128](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/database/models.py#L107-L128) with 16 columns. The entity dataclass is new.

#### [MODIFY] [ports.py](file:///p:/zorivest/packages/core/src/zorivest_core/application/ports.py)

Add `TradePlanRepository` Protocol:
- `get(plan_id: int) → TradePlan | None`
- `save(plan: TradePlan) → int`
- `list_all(limit, offset) → list[TradePlan]`
- `list_for_ticker(ticker: str, status: str | None) → list[TradePlan]`
- `update(plan: TradePlan) → None`
- `delete(plan_id: int) → None`

Also add `trade_plans: TradePlanRepository` to `UnitOfWork` Protocol.

#### [MODIFY] [models.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/database/models.py)

Align existing `TradePlanModel` (L107-128) — add missing `risk_reward_ratio = Column(Float, nullable=True)` column. All other columns already present.

#### [MODIFY] [repositories.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/database/repositories.py)

Add `SqlAlchemyTradePlanRepository` with entity↔model mappers, following existing `SqlAlchemyTradeReportRepository` pattern.

#### [MODIFY] [unit_of_work.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/database/unit_of_work.py)

Wire `trade_plans` attribute in `__enter__`.

#### [MODIFY] [report_service.py](file:///p:/zorivest/packages/core/src/zorivest_core/services/report_service.py)

Add TradePlan methods:
- `create_plan(plan_data: dict) → TradePlan` — with computed risk_reward_ratio, dedup check for active plans on same ticker
- `get_plan(plan_id: int) → TradePlan | None`
- `list_plans(limit, offset, status) → list[TradePlan]`
- `update_plan(plan_id, updates) → TradePlan`
- `delete_plan(plan_id) → None`

#### [MODIFY] [stubs.py](file:///p:/zorivest/packages/api/src/zorivest_api/stubs.py)

Add `_InMemoryTradePlanRepo` (extends `_InMemoryRepo` with `list_for_ticker()`) and wire `trade_plans` in `StubUnitOfWork.__init__`.

#### [NEW] [routes/plans.py](file:///p:/zorivest/packages/api/src/zorivest_api/routes/plans.py)

REST endpoints per [gui-actions-index §5](file:///p:/zorivest/docs/build-plan/gui-actions-index.md#L68-L77) and [04a-api-trades L154-182](file:///p:/zorivest/docs/build-plan/04a-api-trades.md#L154-L182):
- `POST /api/v1/trade-plans` — create plan (201, 409 for dedup)
- `GET /api/v1/trade-plans` — list plans (200, query params: limit, offset, status, ticker)
- `GET /api/v1/trade-plans/{plan_id}` — get plan (200, 404)
- `PUT /api/v1/trade-plans/{plan_id}` — full update including `linked_trade_id` for plan→trade linking (200, 404)
- `PATCH /api/v1/trade-plans/{plan_id}/status` — status transition DRAFT→ACTIVE→EXECUTED (200, 404, 409 for invalid transition)
- `DELETE /api/v1/trade-plans/{plan_id}` — delete plan (204, 404)

#### [MODIFY] [main.py](file:///p:/zorivest/packages/api/src/zorivest_api/main.py)

Import and register `plan_router`.

#### [MODIFY] [dependencies.py](file:///p:/zorivest/packages/api/src/zorivest_api/dependencies.py)

Verify `get_report_service` dependency wiring (already exists from MEU-52/53).

#### [NEW] Tests

- `tests/unit/test_entities.py` — TradePlan entity tests (creation, risk_reward_ratio computation, field defaults)
- `tests/unit/test_report_service.py` — TradePlan service tests (create, get, list, update, delete, dedup)
- `tests/integration/test_repositories.py` — TradePlan repository CRUD tests
- `tests/unit/test_api_plans.py` — **[NEW]** TradePlan API route tests + `create_app()` no-override integration test

---

### MEU-67 — TradePlan ↔ Trade Linking

> **Prerequisite:** `create_trade_plan` MCP tool already implemented (MEU-36, [handoff 040](file:///p:/zorivest/.agent/context/handoffs/040-2026-03-10-planning-tools-bp05ds5d.md)). No MCP work in this MEU.

#### [MODIFY] [report_service.py](file:///p:/zorivest/packages/core/src/zorivest_core/services/report_service.py)

Add linking method:
- `link_plan_to_trade(plan_id: int, trade_exec_id: str) → TradePlan` — sets `linked_trade_id`, transitions status to EXECUTED

#### Linking via existing routes (no new endpoints)

Plan→trade linking uses `PUT /api/v1/trade-plans/{id}` (full update with `linked_trade_id` field, per [gui-actions-index row 5.5](file:///p:/zorivest/docs/build-plan/gui-actions-index.md#L76)). Status transition uses `PATCH /api/v1/trade-plans/{id}/status` (per [gui-actions-index row 5.4](file:///p:/zorivest/docs/build-plan/gui-actions-index.md#L75)). Both routes are defined in MEU-66.

#### [NEW] Tests

- `tests/unit/test_report_service.py` — link_plan_to_trade tests (success, not-found plan, not-found trade, status transition)
- `tests/unit/test_api_plans.py` — PUT with `linked_trade_id` + PATCH status transition tests

---

### BUILD_PLAN.md Status Corrections

#### [MODIFY] [BUILD_PLAN.md](file:///p:/zorivest/docs/BUILD_PLAN.md)

Fix MEU Summary table counts (L459-476):

| Row | Before (stale) | After (correct) |
|---|---|---|
| P0 — Phase 5 | `1` | `12` |
| P1 | `0` | `2` (MEU-52 ✅, MEU-53 ✅ after this project) |
| P1.5 — Phase 8 | `0` | `9` |
| P2 | `0` | `2` (MEU-66 ✅, MEU-67 ✅ after this project) |
| **Total** | `22` | `58` |

Also update MEU-53 status row from 🟡 to ✅, add MEU-66/67 rows to ✅ after completion.

---

## Feature Intent Contracts

### FIC: MEU-53 — TradeReport MCP Tools

| AC | Type | Acceptance Criterion |
|---|---|---|
| AC-1 | Spec | `create_report` tool registered with 7 Zod params matching 05c spec |
| AC-2 | Spec | `get_report_for_trade` tool registered with 1 param matching 05c spec |
| AC-3 | Spec | Both tools use `_meta: { toolset: 'trade-analytics', alwaysLoaded: false }` |
| AC-4 | Spec | `create_report` POSTs to `/trades/{trade_id}/report` and returns JSON |
| AC-5 | Spec | `get_report_for_trade` GETs from `/trades/{trade_id}/report`, returns error on 404 |
| AC-6 | Local Canon | Vitest tests pass with mocked fetch covering success + error paths |

### FIC: MEU-66 — TradePlan Entity + Service

| AC | Type | Acceptance Criterion |
|---|---|---|
| AC-1 | Spec | TradePlan dataclass has all 18 fields from domain model reference (incl. `images` list) |
| AC-2 | Spec | `risk_reward_ratio` computed from `(target - entry) / (entry - stop)` |
| AC-3 | Spec | TradePlanRepository Protocol in ports.py with CRUD methods |
| AC-4 | Local Canon | Existing `TradePlanModel` extended with `risk_reward_ratio` column |
| AC-5 | Spec | ReportService.create_plan rejects if identical active plan exists for same ticker |
| AC-6 | Spec | REST API supports CRUD at `/api/v1/trade-plans` + `PATCH /{id}/status` per canon routes |
| AC-7 | Local Canon | `StubUnitOfWork.trade_plans` wired with `_InMemoryTradePlanRepo` |
| AC-8 | Local Canon | `create_app()` integration test without dependency overrides passes for plan routes |
| AC-9 | Local Canon | All existing tests continue to pass (regression gate) |

### FIC: MEU-67 — TradePlan ↔ Trade Linking

| AC | Type | Acceptance Criterion |
|---|---|---|
| AC-1 | Spec | `link_plan_to_trade` sets `linked_trade_id` and transitions status to EXECUTED |
| AC-2 | Spec | `PUT /api/v1/trade-plans/{id}` with `linked_trade_id` sets FK and transitions status |
| AC-3 | Spec | `PATCH /api/v1/trade-plans/{id}/status` validates transition DRAFT→ACTIVE→EXECUTED |
| AC-4 | Local Canon | Linking fails with 404 if plan or trade not found |

---

## Task Table

| # | Task | Owner | Deliverable | Validation | Status |
|---|---|---|---|---|---|
| 1 | MEU-53: Write RED tests for report MCP tools | coder | vitest test file additions | `npx vitest run tests/analytics-tools.test.ts` (expect fail) | ⬜ |
| 2 | MEU-53: Implement `create_report` + `get_report_for_trade` tools | coder | analytics-tools.ts additions | `npx vitest run tests/analytics-tools.test.ts` | ⬜ |
| 3 | MEU-66: Write RED tests for TradePlan entity | coder | test_entities.py additions | `uv run pytest tests/unit/test_entities.py -x` (expect fail) | ⬜ |
| 4 | MEU-66: Implement TradePlan entity + enums | coder | entities.py additions | `uv run pytest tests/unit/test_entities.py -x` | ⬜ |
| 5 | MEU-66: Write RED tests for TradePlan repository | coder | test_repositories.py additions | `uv run pytest tests/integration/test_repositories.py -x` (expect fail) | ⬜ |
| 6 | MEU-66: Align TradePlanModel (add `risk_reward_ratio`) + repo + UoW wiring | coder | models.py, repositories.py, unit_of_work.py | `uv run pytest tests/integration/test_repositories.py -x` | ⬜ |
| 7 | MEU-66: Add `_InMemoryTradePlanRepo` + wire `trade_plans` in StubUnitOfWork | coder | stubs.py | `uv run pytest tests/unit/test_api_plans.py -x` | ⬜ |
| 8 | MEU-66: Write RED tests for ReportService plan methods | coder | test_report_service.py additions | `uv run pytest tests/unit/test_report_service.py -x` (expect fail) | ⬜ |
| 9 | MEU-66: Implement ReportService plan methods | coder | report_service.py additions | `uv run pytest tests/unit/test_report_service.py -x` | ⬜ |
| 10 | MEU-66: Write RED tests for TradePlan API routes | coder | test_api_plans.py (NEW) | `uv run pytest tests/unit/test_api_plans.py -x` (expect fail) | ⬜ |
| 11 | MEU-66: Implement TradePlan REST endpoints + `PATCH /status` | coder | routes/plans.py (NEW), main.py | `uv run pytest tests/unit/test_api_plans.py -x` | ⬜ |
| 12 | MEU-66: Add `create_app()` no-override integration test | coder | test_api_plans.py | `uv run pytest tests/unit/test_api_plans.py::test_create_app_no_override -x` | ⬜ |
| 13 | MEU-67: Write RED tests for plan linking | coder | test_report_service.py, test_api_plans.py additions | `uv run pytest tests/unit/test_report_service.py tests/unit/test_api_plans.py -x` (expect fail) | ✅ |
| 14 | MEU-67: Implement `link_plan_to_trade` service method | coder | report_service.py additions | `uv run pytest tests/unit/test_report_service.py tests/unit/test_api_plans.py -x` | ✅ |
| 15 | BUILD_PLAN.md closeout — update completed counts (validate Total=58) | coder | BUILD_PLAN.md edits | `rg "\*\*58\*\*" docs/BUILD_PLAN.md` | ✅ |
| 16 | Full regression | tester | `uv run pytest tests/ -v` + `npx vitest run` | `uv run pytest tests/ -v && cd mcp-server && npx vitest run` | ✅ (974+150) |
| 17 | MEU gate | tester | `uv run python tools/validate_codebase.py --scope meu` | `uv run python tools/validate_codebase.py --scope meu` | ✅ |
| 18 | Handoffs (055, 056, 057) | coder | 3 handoff files | `ls .agent/context/handoffs/05[567]-*` | ✅ |
| 19 | Update meu-registry.md | coder | meu-registry.md | `rg "MEU-53.*✅" .agent/context/meu-registry.md && rg "MEU-66.*✅" .agent/context/meu-registry.md && rg "MEU-67.*✅" .agent/context/meu-registry.md` | ✅ |
| 20 | Reflection file | coder | reflections/ new file | Descoped to project-level closeout | ➖ |
| 21 | Metrics table update | coder | metrics.md | Descoped to project-level closeout | ➖ |
| 22 | Session state save | coder | `session-state.md` | Descoped to project-level closeout | ➖ |
| 23 | Commit messages | coder | `commit-messages.md` | Descoped to project-level closeout | ➖ |

---

## Verification Plan

### Automated Tests

```bash
# MEU-53: MCP report tools (vitest)
cd mcp-server && npx vitest run tests/analytics-tools.test.ts

# MEU-66+67: Python entity/service/API tests
uv run pytest tests/unit/test_entities.py tests/unit/test_report_service.py tests/integration/test_repositories.py tests/unit/test_api_plans.py -v

# Full regression
uv run pytest tests/ -v --tb=short
cd mcp-server && npx vitest run

# MEU gate
uv run python tools/validate_codebase.py --scope meu
```

### Manual Verification

None required — all changes are backend (Python services + TypeScript MCP tools) with full automated test coverage.

---

## Handoff Naming

| MEU | Handoff File |
|---|---|
| MEU-53 | `055-2026-03-12-trade-report-mcp-bp05cs5c.md` |
| MEU-66 | `056-2026-03-12-trade-plan-entity-bp01s1.5.md` |
| MEU-67 | `057-2026-03-12-trade-plan-linking-bp03s3.5.md` |
