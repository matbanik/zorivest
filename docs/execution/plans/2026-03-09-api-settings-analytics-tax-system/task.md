# API Settings, Analytics, Tax & System — Task Tracker

## Project Setup
- [x] Read create-plan workflow
- [x] Read SOUL.md, current-focus.md, known-issues.md
- [x] Read REST API foundation reflection (11 lessons)
- [x] Read full critical review handoff (983 lines)
- [x] Read MEU registry + BUILD_PLAN.md
- [x] Read build-plan specs (04d, 04e, 04f, 04g, 04-rest-api)
- [x] Analyze existing source (main.py, dependencies.py, stubs.py, routes/)
- [x] Check existing tests and handoff sequence (latest=027)
- [x] Scope project via sequential thinking
- [x] Generate implementation plan
- [x] Generate task.md (this file)
- [x] Present plan for approval
- [x] Critical review completed — corrections applied

## MEU-27: Settings Routes (04d)
- [x] Create `routes/settings.py` with GET all, GET by key, PUT bulk
- [x] Wire to real SettingsService from Phase 2A
- [x] Map SettingsValidationError → 422 with per-key errors
- [x] Add `get_settings_service` to dependencies.py
- [x] Create `test_api_settings.py` (unit + integration)
- [x] Run live probe: PUT → GET roundtrip

## MEU-30: System Routes (04g)
- [x] Create `routes/logs.py` with POST /logs → 204
- [x] Create `routes/mcp_guard.py` with 5 guard routes
- [x] Create `routes/service.py` with status + shutdown (auth-gated)
- [x] Implement in-memory McpGuardService (no __getattr__)
- [x] Add `get_guard_service` to dependencies.py
- [x] Add `require_authenticated` + `require_admin` DI deps to dependencies.py
- [x] Wire service routes to use `require_authenticated` + `require_admin`
- [x] Initialize McpGuardService + settings in lifespan
- [x] Create `test_api_system.py` (unit + integration)
- [x] Run live probe: guard lock/unlock cycle, log ingest, service auth

## MEU-28: Analytics Routes (04e)
- [x] Create `routes/analytics.py` with 10 analytics stubs
- [x] Create `routes/mistakes.py` with POST + GET summary
- [x] Create `routes/fees.py` with GET summary
- [x] Create `routes/calculator.py` with POST position-size
- [x] Create StubAnalyticsService + StubReviewService in stubs.py
- [x] Add `get_review_service` DI provider to dependencies.py
- [x] Wire calculator to real PositionSizeCalculator
- [x] Create `test_api_analytics.py` (unit + integration)
- [x] Run live probe: analytics endpoints return non-500

## MEU-29: Tax Routes (04f)
- [x] Create `routes/tax.py` with 12 endpoints + Pydantic schemas
- [x] Create StubTaxService in stubs.py
- [x] Add `get_tax_service` to dependencies.py
- [x] Create `test_api_tax.py` (unit + integration)
- [x] Run live probe: confirm=false → 400, simulate → 200

## Router Registration & Wiring
- [x] Import all new routers in main.py
- [x] Add include_router calls for all new routers
- [x] Add new services to lifespan initialization
- [x] Verify `/docs` shows all new routes

## Integration & Foundation Tests
- [x] Add new router registration tests to test_api_foundation.py
- [x] Verify all routes respond correctly after unlock
- [x] Verify pre-unlock routes (health, version, guard status, logs)
- [x] Verify gated routes return 403 before unlock

## Quality Gates
- [x] pytest — all tests pass (610/610)
- [x] pyright — 0 errors
- [x] ruff — 0 errors
- [x] Anti-placeholder scan — no TODO/FIXME/NotImplementedError in routes/
- [x] MEU gate: validate_codebase.py --scope meu

## Project Closeout
- [x] Update BUILD_PLAN.md (Phase 4 → ✅, MEU-27..30 → ✅)
- [x] Update meu-registry.md (MEU-27..30 → ✅ approved)
- [x] Update dependency-manifest.md (psutil added via `uv add psutil`)
- [ ] Write reflection doc *(deferred to project-level closeout)*
- [ ] Update metrics *(deferred to project-level closeout)*
- [x] Create 4 handoffs (028–031)
- [ ] Save session state to pomera *(deferred to project-level closeout)*
- [ ] Prepare commit messages *(deferred to project-level closeout)*
