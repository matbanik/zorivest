# Scheduling API + Guardrails — Implementation Plan

> **Project**: `2026-03-18-scheduling-api-guardrails`
> **MEUs**: MEU-90 (`scheduling-guardrails`) → MEU-89 (`scheduling-api-mcp`)
> **Build Plan Refs**: [§9.9](../../build-plan/09-scheduling.md) (guardrails), [§9.10](../../build-plan/09-scheduling.md) (REST API), [05g-mcp-scheduling.md](../../build-plan/05g-mcp-scheduling.md) (MCP tools)
> **Dependencies**: MEU-77–88 ✅ (all Phase 9 domain/infra/steps complete)

---

## Goal

Complete Phase 9 (Scheduling & Pipeline Engine) by building the last two MEUs:
1. **MEU-90**: Security guardrails (rate limits, approval enforcement, audit-based counting)
2. **MEU-89**: REST API (16 endpoints: 16 scheduling + 1 scheduler power-event), SchedulingService facade, SchedulerService (APScheduler wrapper), MCP tools (6 tools + 2 resources), and SendStep wiring

After this project, Phase 9 reaches 14/14 ✅ and is fully complete.

---

## Task Table

| # | Task | owner_role | Deliverable | Validation | Status |
|---|------|------------|-------------|------------|:------:|
| 1 | MEU-90: Write `test_pipeline_guardrails.py` (red phase) | coder | Test file | `uv run pytest tests/unit/test_pipeline_guardrails.py` — all FAIL | `[ ]` |
| 2 | MEU-90: Implement `pipeline_guardrails.py` | coder | Service module | `uv run pytest tests/unit/test_pipeline_guardrails.py -v` — all GREEN | `[ ]` |
| 3 | MEU-90: Create handoff `076-2026-03-18-scheduling-guardrails-bp09s9.9.md` | coder | Handoff file | `powershell -c "Test-Path .agent/context/handoffs/076-2026-03-18-scheduling-guardrails-bp09s9.9.md"` → True; `rg -c "## Evidence" .agent/context/handoffs/076-2026-03-18-scheduling-guardrails-bp09s9.9.md` | `[ ]` |
| 4 | MEU-89: Write `test_scheduling_service.py` (red phase) | coder | Test file | `uv run pytest tests/unit/test_scheduling_service.py` — all FAIL | `[ ]` |
| 5 | MEU-89: Implement `scheduling_service.py` + `scheduler_service.py` | coder | Service modules | `uv run pytest tests/unit/test_scheduling_service.py -v` — all GREEN | `[ ]` |
| 6 | MEU-89: Write `test_api_scheduling.py` (red phase) | coder | Test file | `uv run pytest tests/unit/test_api_scheduling.py` — all FAIL | `[ ]` |
| 7 | MEU-89: Implement `routes/scheduling.py` + `routes/scheduler.py` + wiring | coder | Route modules | `uv run pytest tests/unit/test_api_scheduling.py -v` — all GREEN | `[ ]` |
| 8 | MEU-89: Implement `scheduling-tools.ts` + toolset registration | coder | MCP tools | `cd mcp-server && npm run build` — exit 0 | `[ ]` |
| 9 | MEU-89: Write MCP tool tests (`scheduling-tools.test.ts`) | coder | Test file | `cd mcp-server && npx vitest run src/tools/__tests__/scheduling-tools.test.ts` — all GREEN | `[ ]` |
| 10 | MEU-89: Wire `delivery_repository` + `smtp_config` into StepContext | coder | Wiring in scheduling_service.py | `uv run pytest tests/unit/test_send_step.py -v` — all GREEN | `[ ]` |
| 11 | MEU-89: Create handoff `077-2026-03-18-scheduling-api-mcp-bp09s9.10+9.11.md` | coder | Handoff file | `powershell -c "Test-Path .agent/context/handoffs/077-2026-03-18-scheduling-api-mcp-bp09s9.10+9.11.md"` → True; `rg -c "## Evidence" .agent/context/handoffs/077-2026-03-18-scheduling-api-mcp-bp09s9.10+9.11.md` | `[ ]` |
| 12 | Run full regression | tester | Green suite | `uv run pytest tests/ -v` — 0 failures | `[ ]` |
| 13 | Update `docs/BUILD_PLAN.md` (status + hub drift + description fix) | coder | Hub file | `rg -c "MEU-89.*✅" docs/BUILD_PLAN.md` → 1; `rg -c "MEU-90.*✅" docs/BUILD_PLAN.md` → 1; `powershell -c "if(rg '12 endpoints' docs/BUILD_PLAN.md){exit 1}else{exit 0}"` → exit 0 | `[ ]` |
| 14 | Update `.agent/context/meu-registry.md` | coder | Registry | `rg -c "scheduling-api-mcp" .agent/context/meu-registry.md && rg -c "scheduling-guardrails" .agent/context/meu-registry.md` | `[ ]` |
| 15 | MEU gate validation | tester | Gate pass | `uv run python tools/validate_codebase.py --scope meu` | `[ ]` |
| 16 | Create reflection + metrics + commit messages | coder | Closeout | `powershell -c "Test-Path docs/execution/reflections/2026-03-18-scheduling-api-guardrails-reflection.md"` → True; `rg -c "scheduling-api-guardrails" docs/execution/metrics.md` | `[ ]` |

---

## Spec Sufficiency

### MEU-90: Pipeline Guardrails (§9.9)

| Behavior / Contract | Source Type | Source | Resolved? |
|---|---|---|---|
| `PipelineRateLimits` dataclass (4 configurable limits) | Spec | §9.9b L2321–2329 | ✅ |
| `PipelineGuardrails` class (4 check methods) | Spec | §9.9b L2333–2378 | ✅ |
| Approval check compares `content_hash` vs `approved_hash` | Spec | §9.9c L2381–2388 | ✅ |
| `_count_audit_actions` queries `audit_log` table | Local Canon | AuditLogRepository from MEU-82 | ✅ |
| Audit log actions to track | Spec | §9.9d L2394–2403 | ✅ |

### MEU-89: Scheduling API + MCP (§9.10, §9.11)

| Behavior / Contract | Source Type | Source | Resolved? |
|---|---|---|---|
| 17 REST endpoints (16 scheduling + 1 scheduler power-event) | Spec | §9.10 L2411–2626, §9.3f L1300–1327 | ✅ |
| Request/Response Pydantic models (8 models) | Spec | §9.10 L2421–2473 | ✅ |
| `SchedulingService` facade | Spec (implicit) | §9.10 route signatures | ✅ — defined by route method contracts |
| `SchedulerService` APScheduler wrapper | Spec | §9.3d L1143–1257 | ✅ |
| 6 MCP tools | Spec | 05g-mcp-scheduling.md | ✅ |
| 2 MCP resources | Spec | 05g-mcp-scheduling.md L291–314 | ✅ |
| Toolset registration (`scheduling` toolset) | Local Canon | §5.11–5.14 (ToolsetRegistry) | ✅ |
| `delivery_repository` + `smtp_config` wiring into StepContext | Spec | BUILD_PLAN MEU-89 desc | ✅ |
| Power event endpoint (§9.3f) | Spec | §9.3f L1300–1327 | ✅ — separate `routes/scheduler.py` + `scheduler_router` registration |

---

## Feature Intent Contracts

### FIC: MEU-90

| AC | Source | Description |
|----|--------|-------------|
| AC-1 | `Spec §9.9b` | `check_can_create_policy()` returns `(False, msg)` when daily policy creates ≥ 20 |
| AC-2 | `Spec §9.9b` | `check_can_execute()` returns `(False, msg)` when hourly executions ≥ 60 |
| AC-3 | `Spec §9.9b` | `check_can_send_email()` returns `(False, msg)` when daily emails ≥ 50 |
| AC-4 | `Spec §9.9c` | `check_policy_approved()` returns `(False, msg)` for unapproved policies |
| AC-5 | `Spec §9.9c` | `check_policy_approved()` returns `(False, msg)` when `content_hash ≠ approved_hash` |
| AC-6 | `Spec §9.9c` | `check_policy_approved()` returns `(True, "")` when approved and hash matches |
| AC-7 | `Spec §9.9b` | Custom `PipelineRateLimits` overrides default values |
| AC-8 | `Local Canon` | `_count_audit_actions` correctly time-windows audit_log queries |

### FIC: MEU-89 (REST API)

| AC | Source | Description |
|----|--------|-------------|
| AC-R1 | `Spec §9.10` | `POST /policies` creates policy, returns 201 with `PolicyResponse` |
| AC-R2 | `Spec §9.10` | `POST /policies` returns 422 with validation errors for invalid policy |
| AC-R3 | `Spec §9.10` | `GET /policies` lists all policies (optionally filtered by enabled) |
| AC-R4 | `Spec §9.10` | `GET /policies/{id}` returns 200 or 404 |
| AC-R5 | `Spec §9.10` | `PUT /policies/{id}` updates and resets approval if content changes |
| AC-R6 | `Spec §9.10` | `DELETE /policies/{id}` returns 204, unschedules job |
| AC-R7 | `Spec §9.10` | `POST /policies/{id}/approve` sets `approved=True`, `approved_hash` |
| AC-R8 | `Spec §9.10` | `POST /policies/{id}/run` checks approval + rate limits, returns `RunResponse` |
| AC-R9 | `Spec §9.10` | `GET /policies/{id}/runs` returns run history |
| AC-R10 | `Spec §9.10` | `GET /runs/{id}` returns detail with steps |
| AC-R11 | `Spec §9.10` | `GET /runs/{id}/steps` returns step-level detail |
| AC-R12 | `Spec §9.10` | `GET /scheduler/status` returns scheduler health |
| AC-R13 | `Spec §9.10` | `GET /policies/schema` returns PolicyDocument JSON Schema |
| AC-R14 | `Spec §9.10` | `GET /step-types` returns registered step types with param schemas |
| AC-R15 | `Spec §9.10` | `GET /runs` returns recent runs across all policies |
| AC-R16 | `Spec §9.10` | `PATCH /policies/{id}/schedule` patches cron/enabled/timezone |
| AC-R17 | `Spec §9.3f` | `POST /scheduler/power-event` receives OS suspend/resume events and triggers APScheduler wakeup |

### FIC: MEU-89 (MCP Tools)

| AC | Source | Description |
|----|--------|-------------|
| AC-M1 | `Spec 05g` | `create_policy` proxies to `POST /scheduling/policies` |
| AC-M2 | `Spec 05g` | `list_policies` proxies to `GET /scheduling/policies` |
| AC-M3 | `Spec 05g` | `run_pipeline` proxies to `POST /scheduling/policies/{id}/run` |
| AC-M4 | `Spec 05g` | `preview_report` proxies with `dry_run: true` |
| AC-M5 | `Spec 05g` | `update_policy_schedule` performs read-modify-write via GET+PUT |
| AC-M6 | `Spec 05g` | `get_pipeline_history` proxies to runs endpoints |
| AC-M7 | `Spec 05g` | `pipeline://policies/schema` resource returns JSON Schema |
| AC-M8 | `Spec 05g` | `pipeline://step-types` resource returns step types |

---

## Proposed Changes

### MEU-90: Security Guardrails

#### [NEW] [pipeline_guardrails.py](file:///p:/zorivest/packages/core/src/zorivest_core/services/pipeline_guardrails.py)

- `PipelineRateLimits` dataclass with 4 configurable limits
- `PipelineGuardrails` class with `check_can_create_policy()`, `check_can_execute()`, `check_can_send_email()`, `check_policy_approved()`
- Private `_count_audit_actions()` querying `AuditLogRepository.list_recent()` with time window

#### [NEW] [test_pipeline_guardrails.py](file:///p:/zorivest/tests/unit/test_pipeline_guardrails.py)

- ~12 tests covering: rate limit enforcement (under/at/over each limit), approval checks (approved, unapproved, hash mismatch, policy not found), custom limits

#### [NEW] [076-2026-03-18-scheduling-guardrails-bp09s9.9.md](file:///p:/zorivest/.agent/context/handoffs/076-2026-03-18-scheduling-guardrails-bp09s9.9.md)

---

### MEU-89: Scheduling API + MCP

#### [NEW] [scheduling_service.py](file:///p:/zorivest/packages/core/src/zorivest_core/services/scheduling_service.py)

- `SchedulingService` facade class coordinating: PolicyRepository, PipelineRunner, SchedulerService, PipelineGuardrails, AuditLogRepository
- Methods: `create_policy()`, `list_policies()`, `get_policy()`, `update_policy()`, `delete_policy()`, `approve_policy()`, `trigger_run()`, `get_policy_runs()`, `get_run_detail()`, `get_run_steps()`, `list_runs()`, `get_scheduler_status()`, `patch_schedule()`
- Wire `delivery_repository` and `smtp_config` into `StepContext.outputs` for SendStep

#### [NEW] [scheduler_service.py](file:///p:/zorivest/packages/core/src/zorivest_core/services/scheduler_service.py)

- APScheduler wrapper per §9.3d
- `start()`, `shutdown()`, `schedule_policy()`, `unschedule_policy()`, `get_next_run()`, `pause_policy()`, `resume_policy()`, `get_status()`

#### [NEW] [scheduling.py](file:///p:/zorivest/packages/api/src/zorivest_api/routes/scheduling.py)

- 16 REST endpoints under `/api/v1/scheduling/`
- Request/response Pydantic models
- FastAPI Depends() wiring via `get_scheduling_service`

#### [NEW] [scheduler.py](file:///p:/zorivest/packages/api/src/zorivest_api/routes/scheduler.py)

- 1 REST endpoint: `POST /api/v1/scheduler/power-event` (§9.3f)
- `PowerEventRequest` model, `scheduler_router`
- On resume: calls `SchedulerService.scheduler.wakeup()`

#### [MODIFY] [main.py](file:///p:/zorivest/packages/api/src/zorivest_api/main.py)

- Register `scheduling_router` and `scheduler_router` in `create_app()`

#### [MODIFY] [dependencies.py](file:///p:/zorivest/packages/api/src/zorivest_api/dependencies.py)

- Add `get_scheduling_service` dependency provider

#### [NEW] [scheduling-tools.ts](file:///p:/zorivest/mcp-server/src/tools/scheduling-tools.ts)

- 6 tools: `create_policy`, `list_policies`, `run_pipeline`, `preview_report`, `update_policy_schedule`, `get_pipeline_history`
- 2 resources: `pipeline://policies/schema`, `pipeline://step-types`
- Toolset registration for `scheduling`

#### [MODIFY] [index.ts](file:///p:/zorivest/mcp-server/src/index.ts)

- Register scheduling tools/resources in server initialization

#### [NEW] [test_scheduling_service.py](file:///p:/zorivest/tests/unit/test_scheduling_service.py)

- ~10 tests: CRUD flow, approval flow, trigger with guardrails, history queries

#### [NEW] [test_api_scheduling.py](file:///p:/zorivest/tests/unit/test_api_scheduling.py)

- ~22 tests following `test_api_plans.py` pattern: mocked service, TestClient, status codes + payloads for all 16 scheduling endpoints + 1 scheduler power-event endpoint

#### [NEW] [scheduling-tools.test.ts](file:///p:/zorivest/mcp-server/src/tools/__tests__/scheduling-tools.test.ts)

- ~8 tests: tool registration, parameter validation, REST proxy behavior via mocked fetch

#### [MODIFY] [BUILD_PLAN.md](file:///p:/zorivest/docs/BUILD_PLAN.md)

- MEU-89 ✅, MEU-90 ✅
- Phase 9 status → ✅ Completed (2026-03-18)
- Summary table: P2.5 → 14 completed, total → 79

#### [MODIFY] [meu-registry.md](file:///p:/zorivest/.agent/context/meu-registry.md)

- Add rows for MEU-89 (`scheduling-api-mcp`) and MEU-90 (`scheduling-guardrails`)

#### [NEW] [077-2026-03-18-scheduling-api-mcp-bp09s9.10+9.11.md](file:///p:/zorivest/.agent/context/handoffs/077-2026-03-18-scheduling-api-mcp-bp09s9.10+9.11.md)

---

## `docs/BUILD_PLAN.md` Update Task

Upon project completion, update the hub file with:

1. **Phase Status Tracker**: Phase 9 row → `✅ Completed | 2026-03-18`
2. **MEU status marks**: MEU-89 → `✅`, MEU-90 → `✅`
3. **Summary table**: P2.5 completed → `14`, total → `79`
4. **Execution plan reference** on Phase 9 header: add `[scheduling-api-guardrails](execution/plans/2026-03-18-scheduling-api-guardrails/)`
5. **MEU-89 description**: correct from "12 endpoints" → "16 endpoints (16 scheduling + 1 scheduler power-event)"

**Validation**: `powershell -c "if(rg '12 endpoints' docs/BUILD_PLAN.md){exit 1}else{exit 0}"` must exit 0; `rg -c "16 endpoints" docs/BUILD_PLAN.md` must return 1.

---

## Verification Plan

### Automated Tests

```powershell
# MEU-90: Guardrails tests
uv run pytest tests/unit/test_pipeline_guardrails.py -v

# MEU-89: Service + API tests
uv run pytest tests/unit/test_scheduling_service.py -v
uv run pytest tests/unit/test_api_scheduling.py -v

# MCP tools tests (TypeScript)
cd mcp-server && npx vitest run src/tools/__tests__/scheduling-tools.test.ts

# Type checking
uv run pyright packages/core/src/zorivest_core/services/pipeline_guardrails.py
uv run pyright packages/core/src/zorivest_core/services/scheduling_service.py
uv run pyright packages/api/src/zorivest_api/routes/scheduling.py
uv run pyright packages/api/src/zorivest_api/routes/scheduler.py
cd mcp-server && npx tsc --noEmit

# Full regression
uv run pytest tests/ -v

# MCP server build
cd mcp-server && npm run build

# MEU gate
uv run python tools/validate_codebase.py --scope meu
```

### Manual Verification

None required — all behaviors are testable via automated tests. The REST API tests use FastAPI's TestClient (in-process, no server needed). MCP tool tests use mocked fetch.
