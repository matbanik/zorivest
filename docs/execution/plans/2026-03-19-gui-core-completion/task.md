# Task — GUI Core P0 Completion

> **Project**: `2026-03-19-gui-core-completion`
> **MEUs**: MEU-46a, MEU-51 (+ MEU-50 docs correction)

## MEU-46a: MCP REST Proxy

- [x] T1: Create `mcp-server/zorivest-tools.json` manifest + `scripts/generate-tools-manifest.ts`
  - [x] Add `prebuild` script to `mcp-server/package.json`
  - [x] Export `TOOLSET_DEFINITIONS` from `seed.ts`
  - [x] Run `npm run prebuild` to verify manifest generation (51 tools, 9 toolsets)
- [x] T2: Add `GET /api/v1/mcp/toolsets` + `GET /api/v1/mcp/diagnostics` routes
  - [x] Create `routes/mcp_toolsets.py` with both endpoints
  - [x] Register `mcp_toolsets_router` in `main.py`
  - [x] `app.state.start_time` already set in lifespan (L93)
  - [x] Write `test_mcp_toolsets.py` (3 tests: total_tools, uptime, graceful fallback)
  - [x] Run tests green: `uv run pytest tests/unit/test_mcp_toolsets.py -v` — 3/3 ✅
- [x] T3: Wire `McpServerStatusPanel.tsx` to consume both endpoints
  - [x] Add TanStack Query for `/mcp/toolsets` (tool count)
  - [x] Add TanStack Query for `/mcp/diagnostics` (uptime)
  - [x] Replace `—` with live tool count
  - [x] Add `refetchInterval: 30_000` (G5)
  - [x] Write/update vitest for panel
- [x] T4: Regen OpenAPI spec (G8): `uv run python tools/export_openapi.py -o openapi.committed.json` ✅

## MEU-51 Prerequisite: Settings Write Contract Fix

- [x] T2.5: Add `PUT /api/v1/settings/{key}` single-key write route
  - [x] Add route to `routes/settings.py` (delegates to `service.bulk_upsert({key: value})`)
  - [x] Write test: `test_settings_put_single_key` ✅
  - [x] Write test: `test_settings_put_single_key_validates` (422 on invalid) ✅
  - [x] Run tests green: `uv run pytest tests/unit/test_api_settings.py -v -k single_key` — 2/2 ✅

## MEU-51: GUI State Persistence

- [x] T5: Add Zustand `persist` middleware on `useLayoutStore`
  - [x] Storage: localStorage (interim — `electron-store` v9+ is ESM-only `[UI-ESMSTORE]`, pinned to v8 CJS; preload bridge untested)
  - [x] Canon specifies Zustand + electron-store (06a §92) — will migrate when bridge validated
  - [x] Persist: `sidebarWidth`, `isRailCollapsed` (NOT `commandPaletteOpen`)
- [x] T6: Create `useRouteRestoration` hook
  - [x] Read `ui.activePage` on mount → navigate
  - [x] Save current route on route change
  - [x] Write vitest for hook (5 tests in useRouteRestoration.test.tsx)
- [x] T6.5: Wire theme persistence via `usePersistedState`
  - [x] Theme toggle uses `usePersistedState('ui.theme', 'dark')`
  - [x] Write vitest for theme persistence (5 tests in useTheme.test.tsx)
- [x] T7: Wire persistence into `AppShell.tsx`
  - [x] Call `useRouteRestoration()`
  - [x] Wire sidebar collapse persistence

## Documentation

- [x] T8: Mark MEU-50 as ✅ in `BUILD_PLAN.md` (line 210) and `meu-registry.md`
- [x] T9: Update `BUILD_PLAN.md` + `meu-registry.md` for MEU-46a and MEU-51 on completion

## Exit Gate

- [x] T10: Full regression
  - [x] `uv run pytest tests/ --tb=line -q` — 1588 pass, 8 pre-existing fail, 16 skip
  - [x] `cd ui && npx vitest run` — 13 files, 133 tests passed
  - [x] `uv run pyright packages/api/src/zorivest_api/routes/mcp_toolsets.py settings.py` — 0 errors
  - [x] `uv run python tools/export_openapi.py --check openapi.committed.json` — no drift
  - [x] `npx tsc --noEmit` (UI) — 0 errors
  - [x] `uv run ruff check` (API routes) — clean

## Handoff

- [x] T11: Create execution handoff file
  - [x] `.agent/context/handoffs/2026-03-19-gui-core-completion-execution.md`
  - [x] Scope, changes summary, evidence bundle, open items
- [x] T12: Create reflection file
  - [x] `docs/execution/reflections/2026-03-19-gui-core-completion-reflection.md`
- [x] T13: Update metrics row in `docs/execution/metrics.md`
- [x] T14: Update `BUILD_PLAN.md` + `meu-registry.md` (MEU-46a, MEU-50, MEU-51 status)
- [x] T15: Save session state to pomera_notes (ID: 638)
- [x] T16: Prepare commit messages + commit
