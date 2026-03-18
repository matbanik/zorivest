# Handoff 077 — Scheduling API + MCP (MEU-89)

> Date: 2026-03-18
> Phase: 9 (§9.10, §9.11)
> Status: ✅ Complete

## Scope

Full scheduling REST API (16 endpoints), MCP toolset (6 tools + 2 resources), service layer, and delivery wiring.

## Files Created

| File | Purpose |
|------|---------|
| `packages/core/src/zorivest_core/services/scheduler_service.py` | APScheduler wrapper with lazy init, `PipelineRunnerPort` + `PolicyRepositoryPort` protocols |
| `packages/core/src/zorivest_core/services/scheduling_service.py` | Facade: policy CRUD, execution, run history, scheduler status, schedule patching |
| `packages/api/src/zorivest_api/routes/scheduling.py` | 16 REST endpoints (policy CRUD, execution, history, schema, schedule patch) |
| `packages/api/src/zorivest_api/routes/scheduler.py` | 1 power-event endpoint (§9.3f) |
| `mcp-server/src/tools/scheduling-tools.ts` | 6 MCP tools + 2 resources per 05g-mcp-scheduling.md |
| `mcp-server/tests/scheduling-tools.test.ts` | 6 vitest tests for tool registration |
| `tests/unit/test_scheduling_service.py` | 16 unit tests for scheduling service facade |
| `tests/unit/test_api_scheduling.py` | 24 unit tests for scheduling + scheduler API endpoints |

## Files Modified

| File | Change |
|------|--------|
| `packages/api/src/zorivest_api/dependencies.py` | Added `get_scheduling_service` + `get_scheduler_service` |
| `packages/api/src/zorivest_api/main.py` | Registered `scheduling_router` + `scheduler_router`, added OpenAPI tags |
| `packages/core/src/zorivest_core/services/pipeline_runner.py` | Added `delivery_repository` + `smtp_config` optional kwargs, injected into `StepContext.outputs` |
| `mcp-server/src/toolsets/seed.ts` | Updated scheduling toolset from 3-tool stub to 6-tool real registration |
| `tests/unit/test_api_foundation.py` | Updated tag count assertion (8 → 10) |

## Architecture Decisions

- **Protocol-based ports** throughout: `PolicyStore`, `RunStore`, `StepStore`, `AuditLogger` in scheduling service; `PipelineRunnerPort`, `PolicyRepositoryPort` in scheduler service
- **Facade pattern**: `SchedulingService` abstracts all scheduling operations behind a single interface
- **Lazy APScheduler init**: `SchedulerService` only initializes APScheduler when `db_url` is provided
- **Delivery wiring**: `delivery_repository` + `smtp_config` injected as reserved `StepContext.outputs` keys via `PipelineRunner.__init__` keyword args
- **Schedule patching**: `tz_name` param avoids shadowing `datetime.timezone`

## Evidence

```
# Python tests
uv run pytest tests/unit/test_pipeline_guardrails.py tests/unit/test_scheduling_service.py tests/unit/test_api_scheduling.py tests/unit/test_pipeline_runner.py -v
# 79 passed

# Full regression
uv run pytest tests/ -v
# 1514 passed, 1 failed (pre-existing), 16 skipped

# Type check (0 errors)
uv run pyright packages/core/src/zorivest_core/services/scheduling_service.py packages/core/src/zorivest_core/services/scheduler_service.py packages/core/src/zorivest_core/services/pipeline_guardrails.py packages/core/src/zorivest_core/services/pipeline_runner.py packages/api/src/zorivest_api/routes/scheduling.py packages/api/src/zorivest_api/routes/scheduler.py

# TypeScript build
npm run build  # clean

# MCP tests
npx vitest run  # scheduling-tools.test.ts: 6 passed

# MEU gate
uv run python tools/validate_codebase.py --scope meu  # All 8 blocking checks passed
```
