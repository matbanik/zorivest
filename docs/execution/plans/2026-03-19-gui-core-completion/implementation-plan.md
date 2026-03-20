# GUI Core P0 Completion — Implementation Plan

> **Project**: `2026-03-19-gui-core-completion`
> **Phase**: 6 (GUI) + Phase 4 (API)
> **MEUs**: MEU-46a (`mcp-rest-proxy`), MEU-51 (`gui-state-persistence`)
> **Priority**: P0
> **Date**: 2026-03-19

## Problem

Two remaining P0 Phase 6 GUI items need implementation:

1. **MEU-46a** — The MCP Server Status panel shows `—` for "Registered tools" because there are no REST proxy endpoints for MCP tool metadata. Per 06f canon L743, two endpoints are needed: `GET /api/v1/mcp/toolsets` (tool catalog from manifest) and `GET /api/v1/mcp/diagnostics` (API uptime).

2. **MEU-51** — UI state (sidebar width, theme, active page, panel collapse) doesn't persist across app restarts. The `usePersistedState` hook and Zustand store exist but aren't wired for persistence.

Additionally, **MEU-50** (`gui-command-palette`) was discovered to be **already fully implemented** during the planning investigation and needs documentation cleanup.

## Architecture Decision: MEU-46a Cross-Process Metadata ✅ Confirmed

> [!NOTE]
> **Confirmed: Option A — Build-Time Static Manifest** (approved 2026-03-19).
>
> The MCP server runs as a separate Node.js process (stdio transport). Three approaches were evaluated:
>
> | Option | Approach | Verdict |
> |---|---|---|
> | **A** ⭐ | `prebuild` script reads `seed.ts` → generates `zorivest-tools.json` → Python API reads at startup | **Selected** |
> | B | Hardcode constants (`MCP_TOOL_COUNT = 51`) in Python API config | Rejected — manual sync, no toolset detail |
> | C | Runtime REST-to-MCP proxy (Python calls MCP HTTP endpoint) | Blocked — MCP uses stdio, not HTTP (`[MCP-HTTPBROKEN]`) |
>
> **Evidence**:
> - `_mcp-manager-architecture.md` L104: Pomera loads `ToolRegistry()` directly at init time — no cross-process call
> - `seed.ts`: All 9 toolsets with ~51 tools are statically defined in `TOOLSET_DEFINITIONS` const array
> - Web search: Static manifests recommended for low-volatility tool registries known at build time
> - `prebuild` hook in `package.json` ensures manifest stays in sync automatically

---

## Proposed Changes

### MEU-46a: MCP REST Proxy

#### [NEW] [zorivest-tools.json](file:///p:/zorivest/mcp-server/zorivest-tools.json)
Static JSON manifest of tool/toolset metadata, generated from `ToolsetRegistry`. Contains:
```json
{
  "total_tools": 51,
  "toolset_count": 9,
  "toolsets": [
    { "name": "core", "description": "...", "tool_count": 4, "always_loaded": true },
    ...
  ],
  "generated_at": "2026-03-19T..."
}
```

> [!WARNING]
> **Product Decision [PD-46a]: Canon Narrowing Authorized**
>
> The 06f wireframe (L701-703) specifies `Active toolsets: 8/8` (runtime `loaded` state) and `Uptime: 1h 23m` (from `zorivest_diagnose`). Both require cross-process MCP calls which are blocked by `[MCP-HTTPBROKEN]` (MCP uses stdio, not HTTP).
>
> **Authorized narrowing for MEU-46a**:
> - "Active toolsets" row → shows **total registered count** only (e.g., "9 toolsets"), not active/total ratio
> - "Uptime" row → shows **API process uptime** (`api_uptime_seconds`), not MCP server uptime
> - 06f canon L743 will be updated with a design decision note documenting this narrowing
> - Full runtime state deferred until `[MCP-HTTPBROKEN]` is resolved
>
> The manifest provides the **static catalog** (tool names, counts, descriptions). Runtime `loaded` state can be added later when HTTP transport is available.

#### [NEW] [generate-tools-manifest.ts](file:///p:/zorivest/mcp-server/scripts/generate-tools-manifest.ts)
Script to regenerate `zorivest-tools.json` from the TypeScript toolset registry. Run as part of MCP build.

#### [MODIFY] [package.json](file:///p:/zorivest/mcp-server/package.json)
Add `"prebuild"` script to run `generate-tools-manifest.ts` before `tsc`.

---

#### [NEW] [mcp_toolsets.py](file:///p:/zorivest/packages/api/src/zorivest_api/routes/mcp_toolsets.py)
New route module with **two canon-aligned endpoints** (per 06f L743):
- `GET /api/v1/mcp/toolsets` — Returns `{ toolsets: [{name, description, tool_count, always_loaded}], total_tools }`. Reads `zorivest-tools.json` at startup (cached).
- `GET /api/v1/mcp/diagnostics` — Returns `{ api_uptime_seconds, api_version }`. API uptime from `time.time() - app.state.start_time`. Note: this is API process uptime, not MCP server uptime (see `[PD-46a]`).

#### [MODIFY] [main.py](file:///p:/zorivest/packages/api/src/zorivest_api/main.py)
- Register `mcp_toolsets_router` with the FastAPI app
- Store `app.state.start_time = time.time()` in lifespan

#### [MODIFY] [McpServerStatusPanel.tsx](file:///p:/zorivest/ui/src/renderer/src/features/settings/McpServerStatusPanel.tsx)
- Add TanStack Query for `GET /api/v1/mcp/toolsets` (tool counts)
- Add TanStack Query for `GET /api/v1/mcp/diagnostics` (uptime)
- Replace `health ? '—' : 'N/A'` (line 183) with live tool count
- Show toolset count and uptime from the new endpoints
- Add `refetchInterval: 30_000` (30s polling per **G5**)

---

### MEU-51: GUI State Persistence

#### Prerequisite: Fix Settings Write Contract

#### [MODIFY] [settings.py](file:///p:/zorivest/packages/api/src/zorivest_api/routes/settings.py)
- Add `PUT /api/v1/settings/{key}` single-key write route (delegates to `service.bulk_upsert({key: value})`)
- Required because `usePersistedState` issues `PUT /settings/${key}` but only bulk `PUT /settings` exists today

---

#### [MODIFY] [layout.ts](file:///p:/zorivest/ui/src/renderer/src/stores/layout.ts)
- Add Zustand `persist` middleware wrapping the store
- Persist `sidebarWidth` and `isRailCollapsed`
- **Shipped**: localStorage (Zustand default) — electron-store bridge deferred `[UI-ESMSTORE]` (v9+ ESM-only; v8 pinned but preload bridge integration untested)

> [!NOTE]
> No new IPC bridge creation needed — `window.electronStore` bridge already exists from MEU-45. T5 reuses it.

#### [NEW] [useRouteRestoration.ts](file:///p:/zorivest/ui/src/renderer/src/hooks/useRouteRestoration.ts)
Hook that:
- On mount: reads `ui.activePage` via `usePersistedState` → navigates to last route
- On route change: saves current route via `usePersistedState('ui.activePage', '/')`

#### [MODIFY] [AppShell.tsx](file:///p:/zorivest/ui/src/renderer/src/components/layout/AppShell.tsx)
- Wire `useRouteRestoration()` hook
- Wire theme persistence via `usePersistedState('ui.theme', 'dark')` in theme toggle
- Use `usePersistedState('ui.sidebarCollapsed', false)` for sidebar sections

---

### Documentation Correction: MEU-50

#### [MODIFY] [BUILD_PLAN.md](file:///p:/zorivest/docs/BUILD_PLAN.md)
- Mark MEU-50 (`gui-command-palette`) as ✅ (line 210)
- Mark MEU-46a and MEU-51 when completed

#### [MODIFY] [meu-registry.md](file:///p:/zorivest/.agent/context/meu-registry.md)
- Add MEU-46a, MEU-50, MEU-51 rows with correct statuses

---

## Spec Sufficiency

### MEU-46a

| Behavior | Source Type | Source | Resolved? |
|---|---|---|---|
| `GET /api/v1/mcp/toolsets` endpoint | Spec | [06f §6f.9](file:///p:/zorivest/docs/build-plan/06f-gui-settings.md) L743 | ✅ |
| `GET /api/v1/mcp/diagnostics` endpoint | Spec | [06f §6f.9](file:///p:/zorivest/docs/build-plan/06f-gui-settings.md) L743 | ✅ |
| Response: total_tools, toolset_count, toolsets | Spec | [06f §6f.9 wireframe](file:///p:/zorivest/docs/build-plan/06f-gui-settings.md) L701-703 | ✅ |
| GUI panel consumes live data | Spec | [06f §6f.9](file:///p:/zorivest/docs/build-plan/06f-gui-settings.md) L743 | ✅ |
| Python→MCP metadata access | Local Canon | Static manifest from ToolsetRegistry | ✅ (config file) |
| Runtime `loaded` state omitted | Product Decision | `[PD-46a]` — Active toolset ratio + MCP uptime deferred until `[MCP-HTTPBROKEN]` resolved | ✅ (authorized) |
| 06f canon update | Task | T9 updates 06f L743 with design decision note for `[PD-46a]` | ✅ (in scope) |
| OpenAPI spec regen after route add | Standard | **G8** — `export_openapi.py --check` | ✅ |

### MEU-51

| Behavior | Source Type | Source | Resolved? |
|---|---|---|---|
| Sidebar width persists | Spec | [06a §92](file:///p:/zorivest/docs/build-plan/06a-gui-shell.md) L92 — "Zustand + electron-store" | ✅ |
| Theme persists via REST | Spec | [06a §89](file:///p:/zorivest/docs/build-plan/06a-gui-shell.md) L89 — "SettingModel via REST" | ✅ |
| Active page persists via REST | Spec | [06a §90](file:///p:/zorivest/docs/build-plan/06a-gui-shell.md) L90 | ✅ |
| Panel collapse persists | Spec | [06a §91](file:///p:/zorivest/docs/build-plan/06a-gui-shell.md) L91 | ✅ |
| usePersistedState hook exists | Local Canon | [usePersistedState.ts](file:///p:/zorivest/ui/src/renderer/src/hooks/usePersistedState.ts) | ✅ |
| `PUT /settings/{key}` route needed | Local Canon | settings.py has bulk PUT only — single-key write missing | ✅ (fix in T2.5) |
| electron-store@8 pinned | Local Canon | Known issue `[UI-ESMSTORE]` | ✅ |
| Existing IPC bridge reusable | Local Canon | `window.electronStore` at preload/index.ts:26-33 | ✅ (no new bridge needed) |

---

## Feature Intent Contracts

### MEU-46a FIC

**Intent**: The MCP Server Status panel displays live tool count, toolset count, and API uptime from REST endpoints instead of showing `—`. Per `[PD-46a]`, active/total toolset ratio and MCP uptime are deferred.

| AC | Source | Description |
|---|---|---|
| AC-1 | Spec | `GET /api/v1/mcp/toolsets` returns `{ toolsets: [...], total_tools }` from manifest |
| AC-1b | Spec | `GET /api/v1/mcp/diagnostics` returns `{ api_uptime_seconds, api_version }` |
| AC-2 | Spec | McpServerStatusPanel shows numeric tool count (not `—`) when backend is reachable |
| AC-3 | PD-46a | Toolset count row displays total count (e.g., "9 toolsets") — active/total ratio deferred |
| AC-4 | Standard G8 | OpenAPI spec regenerated and no drift detected |

**Negative cases**:
- Must NOT hardcode tool count in the GUI — must come from API
- Must NOT fail if MCP server config is unreachable — graceful fallback to `—`

### MEU-51 FIC

**Intent**: UI layout state survives app restarts. Sidebar width + rail collapsed state persist locally; theme and active page persist server-side.

| AC | Source | Description |
|---|---|---|
| AC-5 | Spec | Sidebar width restores on app launch (Zustand persist → localStorage; electron-store deferred `[UI-ESMSTORE]`) |
| AC-6 | Spec | Rail collapsed state restores on app launch |
| AC-7 | Spec | Last visited route restores on app launch |
| AC-8 | Spec | Theme preference persists via REST settings API |

**Negative cases**:
- Must NOT block app startup if settings API is unreachable — use defaults
- Must NOT persist `commandPaletteOpen` (transient UI state)

---

## Applicable Emerging Standards

| Standard | Applies To | Enforcement |
|---|---|---|
| **G1** — Buttons must have visible borders | MEU-46a (any new buttons) | Visual check on Refresh button |
| **G5** — Auto-refresh for externally mutated data | MEU-46a (MCP info can change) | `refetchInterval: 30_000` |
| **G6** — Field name contracts | MEU-46a + MEU-51 | API response fields match TS interfaces |
| **G8** — OpenAPI spec regen after route changes | MEU-46a (new route) | `export_openapi.py --check` |

---

## Task Table

| # | Task | Owner | Deliverable | Validation | Status |
|---|---|---|---|---|---|
| T1 | MEU-46a: Create `zorivest-tools.json` manifest + generation script | Opus | `mcp-server/zorivest-tools.json`, `scripts/generate-tools-manifest.ts` | `npm run build` in mcp-server | ⬜ |
| T2 | MEU-46a: Add `GET /api/v1/mcp/toolsets` + `GET /api/v1/mcp/diagnostics` routes | Opus | `routes/mcp_toolsets.py`, `main.py` update | `uv run pytest tests/unit/test_mcp_toolsets.py -v` | ⬜ |
| T2.5 | MEU-51 prereq: Add `PUT /api/v1/settings/{key}` single-key write route | Opus | `routes/settings.py` update | `uv run pytest tests/unit/test_api_settings.py -v` | ⬜ |
| T3 | MEU-46a: Wire McpServerStatusPanel to `/mcp/toolsets` + `/mcp/diagnostics` | Opus | `McpServerStatusPanel.tsx` update | `npx vitest run` | ⬜ |
| T4 | MEU-46a: Regen OpenAPI spec (G8) | Opus | `openapi.committed.json` | `uv run python tools/export_openapi.py --check openapi.committed.json` | ⬜ |
| T5 | MEU-51: Add Zustand persist middleware (reuse existing `window.electronStore`) | Opus | `layout.ts` update only | `npx vitest run` | ⬜ |
| T6 | MEU-51: Create useRouteRestoration hook | Opus | `hooks/useRouteRestoration.ts` | `npx vitest run` | ⬜ |
| T6.5 | MEU-51: Wire theme persistence via `usePersistedState` | Opus | Theme toggle uses `usePersistedState('ui.theme', 'dark')` | `npx vitest run` | ⬜ |
| T7 | MEU-51: Wire persistence into AppShell | Opus | `AppShell.tsx` update | `npx vitest run` | ⬜ |
| T8 | Mark MEU-50 as ✅ in BUILD_PLAN.md + registry | Opus | Documentation update | Visual inspection | ⬜ |
| T9 | Update BUILD_PLAN.md for MEU-46a + MEU-51 | Opus | BUILD_PLAN.md, meu-registry.md | `python tools/validate_build_plan.py` | ⬜ |
| T10 | Full regression + quality gate | Opus | All tests green | `uv run pytest tests/ -v` + `npx vitest run` | ⬜ |

---

## Verification Plan

### Automated Tests

**MEU-46a Python tests** (new):
```bash
uv run pytest tests/unit/test_mcp_toolsets.py -v
```
Tests to write:
- `test_mcp_toolsets_returns_total_tools` — `/mcp/toolsets` returns valid JSON with `total_tools` field
- `test_mcp_diagnostics_returns_uptime` — `/mcp/diagnostics` returns `api_uptime_seconds` as positive number
- `test_mcp_toolsets_graceful_when_manifest_missing` — returns fallback data, not 500

**MEU-51 Settings prereq test** (new):
```bash
uv run pytest tests/unit/test_api_settings.py -v -k single_key
```
Tests to write:
- `test_settings_put_single_key` — `PUT /settings/{key}` writes and reads back correctly
- `test_settings_put_single_key_validates` — returns 422 on invalid value

**MEU-46a UI tests** (existing + new):
```bash
cd ui && npx vitest run --reporter=verbose
```
Additions to existing `McpServerStatusPanel` test or new test file:
- Verify panel renders numeric tool count when API returns data
- Verify panel shows `—` when API is unreachable

**MEU-51 UI tests** (new):
```bash
cd ui && npx vitest run --reporter=verbose
```
New test for `useRouteRestoration`:
- Verify hook reads initial route from `usePersistedState`
- Verify route change triggers save

**Full regression**:
```bash
uv run pytest tests/ --tb=line -q
cd ui && npx vitest run --reporter=verbose
uv run pyright packages/
```

**OpenAPI spec check** (after MEU-46a):
```bash
uv run python tools/export_openapi.py --check openapi.committed.json
```

### Manual Verification

None required — all acceptance criteria are covered by automated tests and visual inspection during development.

---

## Handoff Naming

| MEU | Handoff File |
|---|---|
| MEU-46a | `082-2026-03-19-mcp-rest-proxy-bp06fs6f.9.md` |
| MEU-51 | `083-2026-03-19-gui-state-persistence-bp06as6a.md` |
