# API Settings, Analytics, Tax & System — Implementation Plan

> Project: `api-settings-analytics-tax-system` | Date: 2026-03-09
> MEUs: 27, 28, 29, 30 | Build-plan: [04d](../../build-plan/04d-api-settings.md), [04e](../../build-plan/04e-api-analytics.md), [04f](../../build-plan/04f-api-tax.md), [04g](../../build-plan/04g-api-system.md)

---

## Lessons Applied from REST API Foundation (11-pass reflection)

> [!IMPORTANT]
> The previous project (MEU-23..26) required 11 review passes with ~25 findings. The root causes were: (1) mocked tests masking broken runtime, (2) stubs that compiled but violated service contracts, (3) missing exception mapping, (4) split-brain state propagation. **This plan explicitly addresses every lesson.**

| # | Lesson | How Applied in This Plan |
|---|--------|--------------------------|
| 1 | Green tests ≠ working app | Every MEU includes ≥1 `create_app()` + `TestClient(raise_server_exceptions=False)` integration test — no dependency overrides |
| 2 | Stubs must honor behavioral contracts | New stub services (analytics, tax, guard) return properly shaped empty/default responses, not `None` or `__getattr__` catch-alls |
| 3 | Every route must map every domain exception | FIC acceptance criteria require explicit `NotFoundError→404`, `ValidationError→422`, `BusinessRuleError→409` exception mapping in every write route |
| 4 | Live probes are the only reliable verification | Each MEU has an explicit live-probe protocol run after tests pass |
| 5 | State propagation must be tested E2E | Settings PUT→GET roundtrip, MCP guard lock/unlock cycle tested via live app |
| 6 | `__getattr__` catch-alls mask violations | New stub services use explicit methods only — no catch-alls |
| 7 | Response shape matters | Tests assert response keys/structure, not just status codes |
| 8 | Domain-aware repo methods | Settings stub repo implements `get`, `set`, `list_all` with real dict-backed persistence |
| 9 | Understand reviewer protocol early | Plan pre-structures handoff evidence to match Codex's file-state > claims methodology |
| 10 | No premature "approved" claims | Handoff claims scoped exactly to what is implemented and verified |
| 11 | Canon docs define behavior | All routes match the spec exactly — method, path, response shape, exception mapping |

---

## Task Table

| # | Task | Owner Role | Deliverable | Validation | Status |
|---|------|-----------|-------------|------------|--------|
| 1 | MEU-27: Settings routes (04d) | coder | `routes/settings.py`, `test_api_settings.py` | `uv run pytest tests/unit/test_api_settings.py -v` | ⬜ |
| 2 | MEU-30: System routes (04g) | coder | `routes/logs.py`, `routes/mcp_guard.py`, `routes/service.py`, `test_api_system.py` | `uv run pytest tests/unit/test_api_system.py -v` | ⬜ |
| 3 | MEU-28: Analytics routes (04e) | coder | `routes/analytics.py`, `routes/mistakes.py`, `routes/fees.py`, `routes/calculator.py`, `test_api_analytics.py` | `uv run pytest tests/unit/test_api_analytics.py -v` | ⬜ |
| 4 | MEU-29: Tax routes (04f) | coder | `routes/tax.py`, `test_api_tax.py` | `uv run pytest tests/unit/test_api_tax.py -v` | ⬜ |
| 5 | Router registration in main.py | coder | Updated `main.py` imports + `include_router` calls | `uv run pytest tests/unit/test_api_foundation.py::TestAppStateWiring -v` | ⬜ |
| 6 | DI providers in dependencies.py | coder | New `get_settings_service`, `get_guard_service`, `get_analytics_service`, `get_tax_service`, `get_review_service`, `require_authenticated`, `require_admin` providers | `uv run pyright packages/api/src/zorivest_api/dependencies.py` | ⬜ |
| 7 | StubUnitOfWork extensions | coder | Additional repos if needed in `stubs.py` | `uv run pytest tests/unit/ -q` | ⬜ |
| 8 | Integration tests (all MEUs) | coder | `test_api_foundation.py` additions | `uv run pytest tests/unit/test_api_foundation.py -v` | ⬜ |
| 9 | MEU gate | tester | `uv run python tools/validate_codebase.py --scope meu` | `uv run python tools/validate_codebase.py --scope meu` | ⬜ |
| 10 | BUILD_PLAN.md update | coder | Phase 4 status + MEU-27..30 → ✅ | `rg "MEU-27\|MEU-28\|MEU-29\|MEU-30" docs/BUILD_PLAN.md` | ⬜ |
| 11 | MEU registry update | coder | MEU-27..30 rows → ✅ approved | `rg "MEU-27\|MEU-28\|MEU-29\|MEU-30" .agent/context/meu-registry.md` | ⬜ |
| 12 | Dependency manifest update | coder | Any new deps (psutil) | `rg "psutil" docs/build-plan/dependency-manifest.md` | ⬜ |
| 13 | Reflection + metrics | coder | `docs/execution/reflections/2026-03-09-*.md`, metrics row | `Test-Path docs/execution/reflections/2026-03-09-*.md` | ⬜ |
| 14 | Handoffs (028–031) | coder | 4 sequenced handoffs | `Get-ChildItem .agent/context/handoffs/02[89]-*.md,.agent/context/handoffs/03[01]-*.md` | ⬜ |
| 15 | Session state + commit msgs | coder | pomera note ID in handoff + commit messages section in handoff | `rg -q "pomera.*note" .agent/context/handoffs/031-*.md && rg -q "Commit Messages" .agent/context/handoffs/031-*.md` | ⬜ |

---

## Spec Sufficiency

### MEU-27: Settings Routes

| Behavior | Source Type | Source | Resolved? |
|----------|-----------|--------|-----------|
| GET /settings returns all settings as dict | Spec | [04d §routes](../../build-plan/04d-api-settings.md#L39) | ✅ |
| GET /settings/{key} returns single setting or 404 | Spec | [04d §routes](../../build-plan/04d-api-settings.md#L45) | ✅ |
| PUT /settings bulk upsert with validation | Spec | [04d §routes](../../build-plan/04d-api-settings.md#L54) | ✅ |
| SettingsValidationError → 422 with per-key errors | Spec | [04d §routes](../../build-plan/04d-api-settings.md#L66) | ✅ |
| All-or-nothing: no writes if any key fails | Spec | [04d §routes](../../build-plan/04d-api-settings.md#L61) | ✅ |
| SettingsService dependency from Phase 2A | Local Canon | [02a §2A.2](../../build-plan/02a-backup-restore.md) | ✅ (MEU-18 approved) |
| Settings tag on router | Spec | [04-rest-api.md](../../build-plan/04-rest-api.md#L24) | ✅ |
| Phase 2A delegated routes (resolved, reset, etc.) | Spec | [04d §Phase 2A](../../build-plan/04d-api-settings.md#L154) | ⚠️ Out-of-scope for MEU-27 — matrix item 15a is "GET/PUT /settings" only |

### MEU-28: Analytics Routes

| Behavior | Source Type | Source | Resolved? |
|----------|-----------|--------|-----------|
| 10 analytics endpoints (expect, drawdown, etc.) | Spec | [04e §routes](../../build-plan/04e-api-analytics.md#L9) | ✅ |
| Mistakes routes (POST, GET summary) | Spec | [04e §mistakes](../../build-plan/04e-api-analytics.md#L87) | ✅ |
| Fees summary route | Spec | [04e §fees](../../build-plan/04e-api-analytics.md#L107) | ✅ |
| Calculator position-size route | Spec | [04e §calculator](../../build-plan/04e-api-analytics.md#L122) | ✅ |
| Analytics tag on main router | Spec | [04-rest-api.md](../../build-plan/04-rest-api.md#L25) | ✅ |
| Services: AnalyticsService, ReviewService | Spec | [04e §routes](../../build-plan/04e-api-analytics.md#L9) — services not yet built (P2.75) | ⚠️ Route stubs with default responses |

### MEU-29: Tax Routes

| Behavior | Source Type | Source | Resolved? |
|----------|-----------|--------|-----------|
| 12 tax endpoints (simulate, estimate, etc.) | Spec | [04f §routes](../../build-plan/04f-api-tax.md#L9) | ✅ |
| Pydantic schemas (SimulateTaxRequest, etc.) | Spec | [04f §schemas](../../build-plan/04f-api-tax.md#L23) | ✅ |
| Tax tag on router | Spec | [04-rest-api.md](../../build-plan/04-rest-api.md#L26) | ✅ |
| Services: TaxService | Spec | [04f §routes](../../build-plan/04f-api-tax.md#L9) — services not yet built (P3) | ⚠️ Route stubs with default responses |

### MEU-30: System Routes

| Behavior | Source Type | Source | Resolved? |
|----------|-----------|--------|-----------|
| POST /logs (204 no-content) | Spec | [04g §logging](../../build-plan/04g-api-system.md#L9) | ✅ |
| LogEntry Pydantic schema | Spec | [04g §logging](../../build-plan/04g-api-system.md#L35) | ✅ |
| MCP guard routes (status, config, lock, unlock, check) | Spec | [04g §guard](../../build-plan/04g-api-system.md#L50) | ✅ |
| Guard status available pre-unlock | Spec | [04g §guard](../../build-plan/04g-api-system.md#L81) | ✅ |
| Rate-limit threshold auto-lock | Spec | [04g §guard](../../build-plan/04g-api-system.md#L111) | ✅ |
| Health endpoint (no auth, pre-unlock) | Spec | [04g §health](../../build-plan/04g-api-system.md#L189) | ✅ (already exists from MEU-23) |
| Version endpoint (no auth) | Spec | [04g §version](../../build-plan/04g-api-system.md#L281) | ✅ (already exists from MEU-23) |
| Service status (PID, uptime, memory, CPU) | Spec | [04g §service](../../build-plan/04g-api-system.md#L219) | ✅ |
| Graceful shutdown via BackgroundTasks | Spec | [04g §service](../../build-plan/04g-api-system.md#L245) | ✅ |
| Service routes require authenticated user + admin role | Spec | [04g §service](../../build-plan/04g-api-system.md#L239-L247) — `Depends(get_current_user)` | ✅ — implemented as `require_authenticated` + `require_admin` DI deps |
| System tag on router | Spec | [04-rest-api.md](../../build-plan/04-rest-api.md#L27) | ✅ |
| MCP guard in-memory state management | Local Canon | [04g §guard schemas](../../build-plan/04g-api-system.md#L57) | ✅ — implemented as in-memory McpGuardService |

---

## Feature Intent Contracts (FIC)

### MEU-27: api-settings

**Acceptance Criteria:**

- **AC-1** (`Spec`): `GET /api/v1/settings` returns all settings as `dict[str, Any]` — 200 response
- **AC-2** (`Spec`): `GET /api/v1/settings/{key}` returns `{key, value, value_type}` for existing keys — 200
- **AC-3** (`Spec`): `GET /api/v1/settings/{key}` returns 404 for unknown keys
- **AC-4** (`Spec`): `PUT /api/v1/settings` bulk upserts with `{status, count}` response — 200
- **AC-5** (`Spec`): `PUT /api/v1/settings` with invalid values returns 422 with `{detail: {errors: dict}}`
- **AC-6** (`Spec`): All-or-nothing: if any key fails validation, no keys are persisted
- **AC-7** (`Spec`): Settings router uses tag `settings`
- **AC-8** (`Spec`): All settings routes gated behind `require_unlocked_db`
- **AC-9** (`Local Canon` — [reflection](../../reflections/2026-03-08-rest-api-foundation.md)): Integration test uses `create_app()` + `TestClient(raise_server_exceptions=False)` with NO dependency overrides
- **AC-10** (`Local Canon` — [reflection](../../reflections/2026-03-08-rest-api-foundation.md)): PUT→GET roundtrip verified in live app (state persistence)

### MEU-30: api-system

**Acceptance Criteria:**

- **AC-1** (`Spec`): `POST /api/v1/logs` accepts LogEntry and returns 204 — no body
- **AC-2** (`Spec`): LogEntry schema: `{level, component, message, data}`
- **AC-3** (`Spec`): `GET /api/v1/mcp-guard/status` returns guard state, available pre-unlock
- **AC-4** (`Spec`): `PUT /api/v1/mcp-guard/config` updates thresholds, returns updated state
- **AC-5** (`Spec`): `POST /api/v1/mcp-guard/lock` sets locked=True with reason
- **AC-6** (`Spec`): `POST /api/v1/mcp-guard/unlock` sets locked=False
- **AC-7** (`Spec`): `POST /api/v1/mcp-guard/check` increments counter, auto-locks on threshold
- **AC-8** (`Spec`): Guard mutation routes (config/lock/unlock) require unlocked DB — 403 otherwise
- **AC-9** (`Spec`): `GET /api/v1/service/status` returns `{pid, uptime_seconds, memory_mb, cpu_percent, python_version}` — requires authenticated user via `Depends(require_authenticated)`
- **AC-10** (`Spec`): `POST /api/v1/service/graceful-shutdown` returns 202 — requires admin role via `Depends(require_admin)`
- **AC-11** (`Spec`): Health and version routes already exist (MEU-23) — no changes
- **AC-12** (`Spec`): System-related routers use tags: `logs` → system tag via sub-router, `mcp-guard`, `service`, `health` (existing), `version` (existing)
- **AC-13** (`Local Canon` — [reflection](../../reflections/2026-03-08-rest-api-foundation.md)): Integration test uses `create_app()` with no overrides — verifies guard status available pre-unlock and log ingest works
- **AC-14** (`Local Canon` — [auth_service.py](file:///p:/zorivest/packages/api/src/zorivest_api/auth/auth_service.py#L57-L97)): `require_authenticated` and `require_admin` DI providers resolve session token from `AuthService._sessions` — returns 403 if missing/invalid/non-admin

### MEU-28: api-analytics

**Acceptance Criteria:**

- **AC-1** (`Spec`): Analytics router registered with tag `analytics` at prefix `/api/v1/analytics`
- **AC-2** (`Spec`): 10 analytics endpoints exist with correct HTTP methods and paths
- **AC-3** (`Spec`): Mistakes router at `/api/v1/mistakes` with POST / and GET /summary
- **AC-4** (`Spec`): Fees router at `/api/v1/fees` with GET /summary
- **AC-5** (`Spec`): Calculator router at `/api/v1/calculator` with POST /position-size
- **AC-6** (`Spec`): Calculator uses existing `PositionSizeCalculator` from domain layer (MEU-1 ✅)
- **AC-7** (`Spec`): All analytics/mistakes/fees routes gated behind `require_unlocked_db`
- **AC-8** (`Spec`): Calculator route does NOT require unlock (pure calculation)
- **AC-9** (`Local Canon` — [reflection](../../reflections/2026-03-08-rest-api-foundation.md)): Stub analytics/review services return properly shaped empty/default responses
- **AC-10** (`Local Canon` — [reflection](../../reflections/2026-03-08-rest-api-foundation.md)): Integration test with `create_app()` verifies routes return non-500 after unlock

### MEU-29: api-tax

**Acceptance Criteria:**

- **AC-1** (`Spec`): Tax router at `/api/v1/tax` with tag `tax`
- **AC-2** (`Spec`): 12 tax endpoints exist with correct HTTP methods, paths, and Pydantic schemas
- **AC-3** (`Spec`): `POST /tax/quarterly/payment` validates `confirm=True` — returns 400 if false
- **AC-4** (`Spec`): All tax routes gated behind `require_unlocked_db`
- **AC-5** (`Local Canon` — [reflection](../../reflections/2026-03-08-rest-api-foundation.md)): Stub tax service returns properly shaped default responses
- **AC-6** (`Local Canon` — [reflection](../../reflections/2026-03-08-rest-api-foundation.md)): Integration test with `create_app()` verifies routes return non-500 after unlock

---

## Proposed Changes

### Route Files

---

#### [NEW] [settings.py](file:///p:/zorivest/packages/api/src/zorivest_api/routes/settings.py)

Settings CRUD routes (GET all, GET by key, PUT bulk). Wires to real `SettingsService` from Phase 2A. Maps `SettingsValidationError` → 422 with per-key errors.

#### [NEW] [logs.py](file:///p:/zorivest/packages/api/src/zorivest_api/routes/logs.py)

Log ingestion route (POST /logs → 204). Pydantic `LogEntry` schema. Routes to Python `logging` module under `zorivest.frontend` logger.

#### [NEW] [mcp_guard.py](file:///p:/zorivest/packages/api/src/zorivest_api/routes/mcp_guard.py)

MCP guard routes (status/config/lock/unlock/check). In-memory `McpGuardService` initialized in lifespan. Status route available pre-unlock; mutation routes require unlock.

#### [NEW] [service.py](file:///p:/zorivest/packages/api/src/zorivest_api/routes/service.py)

Service lifecycle routes (GET /service/status, POST /service/graceful-shutdown). Uses `psutil` for process metrics.

#### [NEW] [analytics.py](file:///p:/zorivest/packages/api/src/zorivest_api/routes/analytics.py)

Analytics stub routes (10 endpoints). All return properly shaped empty/default responses until P2.75 services are built.

#### [NEW] [mistakes.py](file:///p:/zorivest/packages/api/src/zorivest_api/routes/mistakes.py)

Mistakes stub routes (POST /, GET /summary). Stub service returns empty results.

#### [NEW] [fees.py](file:///p:/zorivest/packages/api/src/zorivest_api/routes/fees.py)

Fee summary stub route (GET /summary). Stub service returns empty results.

#### [NEW] [calculator.py](file:///p:/zorivest/packages/api/src/zorivest_api/routes/calculator.py)

Position size calculator route. Wires to existing `PositionSizeCalculator` from domain layer — NO stub needed.

#### [NEW] [tax.py](file:///p:/zorivest/packages/api/src/zorivest_api/routes/tax.py)

Tax stub routes (12 endpoints with Pydantic request schemas). All return properly shaped default responses until P3 tax engine is built.

---

### Infrastructure Changes

---

#### [MODIFY] [main.py](file:///p:/zorivest/packages/api/src/zorivest_api/main.py)

Add imports and `include_router` calls for all new routers. Add `McpGuardService` and `SettingsService` initialization in lifespan.

#### [MODIFY] [dependencies.py](file:///p:/zorivest/packages/api/src/zorivest_api/dependencies.py)

Add DI providers: `get_settings_service`, `get_guard_service`, `get_analytics_service`, `get_tax_service`, `get_review_service`, `require_authenticated`, `require_admin`.

#### [MODIFY] [stubs.py](file:///p:/zorivest/packages/api/src/zorivest_api/stubs.py)

Add stub service classes: `StubAnalyticsService`, `StubTaxService`, `StubReviewService`. Each returns properly shaped defaults — no `__getattr__` catch-alls.

---

### Test Files

---

#### [NEW] [test_api_settings.py](file:///p:/zorivest/tests/unit/test_api_settings.py)

Unit tests for settings routes + integration test with `create_app()`.

#### [NEW] [test_api_system.py](file:///p:/zorivest/tests/unit/test_api_system.py)

Unit tests for log ingest, MCP guard, service status + integration tests with `create_app()`.

#### [NEW] [test_api_analytics.py](file:///p:/zorivest/tests/unit/test_api_analytics.py)

Unit tests for analytics/mistakes/fees/calculator stubs + integration test.

#### [NEW] [test_api_tax.py](file:///p:/zorivest/tests/unit/test_api_tax.py)

Unit tests for tax stubs + integration test.

#### [MODIFY] [test_api_foundation.py](file:///p:/zorivest/tests/unit/test_api_foundation.py)

Add integration tests verifying all new routers are registered and respond after unlock.

---

### Shared Artifacts

---

#### [MODIFY] [BUILD_PLAN.md](file:///p:/zorivest/docs/BUILD_PLAN.md)

Phase 4 status → ✅ Completed. MEU-27..30 → ✅. MEU summary counts updated.

#### [MODIFY] [meu-registry.md](file:///p:/zorivest/.agent/context/meu-registry.md)

MEU-27..30 rows → ✅ approved. Phase 4 exit criteria updated.

#### [MODIFY] [dependency-manifest.md](file:///p:/zorivest/docs/build-plan/dependency-manifest.md)

Add `psutil` if not already listed for Phase 4.

---

### Handoff Files

---

#### [NEW] 028-2026-03-09-api-settings-bp04ds4d.md
#### [NEW] 029-2026-03-09-api-system-bp04gs4g.md
#### [NEW] 030-2026-03-09-api-analytics-bp04es4e.md
#### [NEW] 031-2026-03-09-api-tax-bp04fs4f.md

---

## In-scope / Out-of-scope

**In-scope:**
- Core settings routes (GET all, GET by key, PUT bulk) — MEU-27
- Log ingestion, MCP guard, service lifecycle — MEU-30
- Analytics/mistakes/fees/calculator route stubs — MEU-28
- Tax route stubs with Pydantic schemas — MEU-29
- Integration tests per MEU with live app probes
- Position-size calculator wired to real domain service

**Out-of-scope:**
- Phase 2A delegated routes (resolved, reset, delete, config export/import, backups) — different matrix items
- Real analytics/tax service implementations (P2.75, P3)
- Real MCP guard DB persistence (Phase 5)
- Broker, banking, import, identifier routes (separate MEUs in P2.75)
- Trade plan and report routes (P1)

---

## Stop Conditions

Halt execution and escalate to human decision gate if any of the following occur:

1. **Spec ambiguity**: A route's response shape, status code, or gating behavior cannot be fully determined from the build-plan spec (04d/04e/04f/04g) and existing local canon. Do not invent behavior.
2. **Service contract mismatch**: A stub service's method signature conflicts with the service port interface defined in Phase 3. Do not silently adapt.
3. **Auth mechanism drift**: The `require_authenticated`/`require_admin` implementation requires capabilities not present in `AuthService` (e.g., token expiry, refresh). Do not extend `AuthService` beyond its current contract.
4. **Test infrastructure failure**: `create_app()` or `TestClient` fails due to missing lifespan initialization — indicates a wiring gap that must be resolved before continuing.
5. **Dependency conflict**: Adding `psutil` or any new dependency causes version conflicts with existing packages.
6. **Phase-exit gate**: Do not mark Phase 4 as ✅ Complete until all 8 MEUs (23–30) pass their individual MEU gates.

---

## Verification Plan

### Automated Tests

```bash
# Run all new tests
uv run pytest tests/unit/test_api_settings.py tests/unit/test_api_system.py tests/unit/test_api_analytics.py tests/unit/test_api_tax.py -v

# Run foundation integration tests (verifies router registration)
uv run pytest tests/unit/test_api_foundation.py -v

# Full regression
uv run pytest tests/unit/ -q

# Type checking
uv run pyright packages/api packages/core/src/zorivest_core/version.py

# Lint
uv run ruff check packages/api packages/core packages/infrastructure

# MEU gate
uv run python tools/validate_codebase.py --scope meu

# Anti-placeholder scan
rg "TODO|FIXME|NotImplementedError" packages/api/src/zorivest_api/routes/
```

### Live Probe Protocol (per MEU)

Each MEU includes a live-app probe using `create_app()` + `TestClient(raise_server_exceptions=False)` with NO dependency overrides. The probes verify:

**MEU-27 (settings):**
1. Unlock via keys + unlock
2. PUT /settings → 200
3. GET /settings/{key} → 200 (value matches what was PUT)
4. GET /settings → 200 (contains the key)
5. PUT /settings with invalid value → 422

**MEU-30 (system):**
1. GET /mcp-guard/status → 200 (available pre-unlock)
2. POST /logs → 204 (available pre-unlock)
3. POST /mcp-guard/lock → 403 (pre-unlock)
4. Unlock → POST /mcp-guard/lock → 200 → GET status → locked=true
5. GET /service/status → 200 (pid > 0)

**MEU-28 (analytics):**
1. Unlock → GET /analytics/expectancy → 200
2. POST /calculator/position-size → 200 (no unlock needed, pure calc)
3. GET /fees/summary → 200
4. GET /mistakes/summary → 200

**MEU-29 (tax):**
1. Unlock → POST /tax/simulate → 200
2. GET /tax/lots?account_id=X → 200
3. POST /tax/quarterly/payment with confirm=false → 400
