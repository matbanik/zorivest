# Task List — Scheduling API + Guardrails

> Project: `2026-03-18-scheduling-api-guardrails`
> MEUs: MEU-90 → MEU-89

## MEU-90: Scheduling Guardrails (§9.9)

- [x] Write `tests/unit/test_pipeline_guardrails.py` (16 tests)
- [x] Implement `packages/core/src/zorivest_core/services/pipeline_guardrails.py`
  - [x] `PipelineRateLimits` dataclass
  - [x] `PipelineGuardrails` class with 4 check methods
  - [x] `_count_audit_actions()` with time-window queries
- [x] All guardrail tests green (16/16)
- [x] Create handoff `076-2026-03-18-scheduling-guardrails-bp09s9.9.md`

## MEU-89: Scheduling API + MCP (§9.10, §9.11)

### Python — Service Layer
- [x] Implement `packages/core/src/zorivest_core/services/scheduler_service.py` (APScheduler wrapper)
- [x] Implement `packages/core/src/zorivest_core/services/scheduling_service.py` (facade)
- [x] Wire `delivery_repository` + `smtp_config` into StepContext.outputs
- [x] Write `tests/unit/test_scheduling_service.py` (16 tests)
- [x] All service tests green (16/16)

### Python — REST API
- [x] Implement `packages/api/src/zorivest_api/routes/scheduling.py` (16 endpoints)
- [x] Implement `packages/api/src/zorivest_api/routes/scheduler.py` (1 power-event endpoint, §9.3f)
- [x] Add `get_scheduling_service` + `get_scheduler_service` to `dependencies.py`
- [x] Register `scheduling_router` + `scheduler_router` in `main.py`
- [x] Write `tests/unit/test_api_scheduling.py` (24 tests incl. power-event)
- [x] All API tests green (24/24)

### TypeScript — MCP Tools
- [x] Implement `mcp-server/src/tools/scheduling-tools.ts` (6 tools + 2 resources)
- [x] Register scheduling toolset in `seed.ts`
- [x] Write `mcp-server/tests/scheduling-tools.test.ts` (6 tests)
- [x] `npm run build` passes (mcp-server)
- [x] MCP tool tests pass (vitest)

### MEU-89 Handoff
- [x] Create handoff `077-2026-03-18-scheduling-api-mcp-bp09s9.10+9.11.md`

## Post-MEU Deliverables

- [x] Full regression green: `uv run pytest tests/ -v` (1514 passed, 1 pre-existing failure)
- [x] Type check: `uv run pyright` on new files (0 errors)
- [x] MEU gate: `uv run python tools/validate_codebase.py --scope meu` (8/8 pass)
- [x] Update `.agent/context/meu-registry.md` — add MEU-89, MEU-90
- [x] Update `docs/BUILD_PLAN.md`:
  - [x] MEU-89 ✅, MEU-90 ✅
  - [x] MEU-89 description: "12 endpoints" → "16 endpoints"
  - [x] Phase 9 status → ✅ Completed (2026-03-18)
  - [x] Summary table P2.5 → 14/14, total → 79
  - [x] Execution plan link on Phase 9 header
- [x] Create reflection at `docs/execution/reflections/2026-03-18-scheduling-api-guardrails-reflection.md`
- [x] Update `docs/execution/metrics.md`
- [x] Save session state to pomera notes
- [x] Prepare commit messages
