---
project: "2026-04-11-gui-scheduling"
source: "docs/execution/plans/2026-04-11-gui-scheduling/implementation-plan.md"
meus: ["MEU-72"]
status: "in_progress"
template_version: "2.0"
---

# Task — Scheduling & Pipeline GUI

> **Project:** `2026-04-11-gui-scheduling`
> **Type:** GUI
> **Estimate:** ~15 files changed, ~6 new npm deps

## Task Table

### Sub-MEU A: Foundation (BV Hardening + TypeScript Types + API Hooks)

| # | Task | Owner | Deliverable | Validation | Status |
|---|------|-------|-------------|------------|--------|
| A1 | Write FIC for Sub-MEU A (AC-A1 through AC-A5) | orchestrator | FIC section in handoff | AC list matches implementation-plan.md §Sub-MEU A | `[x]` |
| A2 | Write BV boundary tests for `PowerEventRequest` (extra-field rejection → 422, invalid `event_type` → 422) | coder | 5 new tests in `test_api_scheduling.py` | pytest: 41 passed | `[x]` |
| A3 | **Red proof**: run tests, confirm new BV tests FAIL | tester | FAIL_TO_PASS evidence in handoff | 5 failures confirmed | `[x]` |
| A4 | Harden `PowerEventRequest` in `scheduler.py` (`extra="forbid"`, `Literal["suspend","resume"]`, `StrippedStr`) | coder | Modified `scheduler.py` | pytest: 41 passed (Green) | `[x]` |
| A5 | Write hook unit tests for `useSchedulingPolicies`, `useCreatePolicy`, mutation hooks | coder | `scheduling/__tests__/scheduling.test.tsx` (8 hook tests) | vitest: 8 hook tests pass | `[x]` |
| A6 | **Red proof**: run hook tests, confirm they FAIL | tester | FAIL_TO_PASS evidence in handoff | 8 failures confirmed | `[x]` |
| A7 | Create TypeScript types + API client (`scheduling/api.ts`) | coder | `ui/src/renderer/src/features/scheduling/api.ts` | `tsc --noEmit` clean | `[x]` |
| A8 | Create React Query hooks (`scheduling/hooks.ts`) | coder | `ui/src/renderer/src/features/scheduling/hooks.ts` | Hook tests pass (Green) | `[x]` |
| A9 | Install npm deps: `codemirror`, `@codemirror/*`, `cronstrue` | coder | Updated `ui/package.json` | Dependencies installed | `[x]` |

### Sub-MEU B: Schedule Page UI (List + Detail + CRUD + JSON Editor)

| # | Task | Owner | Deliverable | Validation | Status |
|---|------|-------|-------------|------------|--------|
| B1 | Write FIC for Sub-MEU B (AC-B1 through AC-B10) | orchestrator | FIC section in handoff | AC list matches implementation-plan.md §Sub-MEU B | `[x]` |
| B2 | Add scheduling `data-testid` constants to `ui/tests/e2e/test-ids.ts` | coder | SCHEDULING constants registered | `rg "SCHEDULING" ui/tests/e2e/test-ids.ts` | `[x]` |
| B3 | Write scheduling page component tests (rendering + interaction) | coder | 20 component tests in `scheduling.test.tsx` | vitest: 36 total tests pass | `[x]` |
| B4 | **Red proof**: run scheduling tests, confirm they FAIL | tester | Component tests FAIL before implementation | Red phase confirmed | `[x]` |
| B5 | Build `PolicyList.tsx` | coder | Left-pane policy card list with data-testid | ESLint + tsc clean | `[x]` |
| B6 | Build `CronPreview.tsx` | coder | Cron → human-readable preview component | ESLint + tsc clean | `[x]` |
| B7 | Build `PolicyDetail.tsx` (CodeMirror 6 wrapper) | coder | JSON editor with syntax highlighting | ESLint + tsc clean | `[x]` |
| B8 | Replace `SchedulingLayout.tsx` stub with list+detail split layout | coder | Full scheduling page | vitest: 36 tests pass (Green) | `[x]` |

### Sub-MEU C: Pipeline Execution + Run History

| # | Task | Owner | Deliverable | Validation | Status |
|---|------|-------|-------------|------------|--------|
| C1 | Write FIC for Sub-MEU C (AC-C1 through AC-C6) | orchestrator | FIC section in handoff | AC list matches implementation-plan.md §Sub-MEU C | `[x]` |
| C2 | Write run history component tests | coder | 6 RunHistory tests in `scheduling.test.tsx` | vitest: 36 total tests pass | `[x]` |
| C3 | **Red proof**: run run-history tests, confirm they FAIL | tester | RunHistory tests FAIL before implementation | Red phase confirmed | `[x]` |
| C4 | Build `RunHistory.tsx` | coder | Run history table with status columns + expandable detail | ESLint + tsc clean | `[x]` |
| C5 | Add Run Now / Dry Run buttons to `PolicyDetail.tsx` | coder | Execution action buttons | ESLint + tsc clean | `[x]` |
| C6 | Add run history section to `SchedulingLayout.tsx` | coder | Run history below detail panel | vitest: 36 tests pass (Green) | `[x]` |

### Sub-MEU D: Stabilization & UX Polish (Unplanned Session Work)

| # | Task | Owner | Deliverable | Validation | Status |
|---|------|-------|-------------|------------|--------|
| D1 | Register `scheduling.default_timezone` in `APP_DEFAULTS` + Settings page UI | coder | `settings.py` + `SettingsLayout.tsx` | Setting persists via API | `[x]` |
| D2 | Write TDD tests for timezone setting persistence | coder | Red→Green tests in `test_api_settings.py` | pytest green | `[x]` |
| D3 | Fix keyboard shortcuts Ctrl+1–5 → Ctrl+Shift+{N} + add Settings label | coder | `commandRegistry.ts` | Shortcuts work in Electron | `[x]` |
| D4 | Replace Account Sort dropdown with column header sorting | coder | `AccountsHome.tsx` | Column headers clickable | `[x]` |
| D5 | Fix "Apply to Plan" to copy Account/Price/Stop/Target values | coder | `TradePlanPage.tsx` | Values populated on Apply | `[x]` |
| D6 | Fix scheduling policy deletion (Confirm Delete handler) | coder | `SchedulingLayout.tsx` | Policy deleted on Confirm | `[x]` |
| D7 | Gray out "Apply to Plan" when not in Trade Plan context | coder | Calculator modal context check | Button disabled outside planning | `[x]` |
| D8 | Load default timezone for new scheduling policies from Settings | coder | `SchedulingLayout.tsx` useQuery | New policy uses configured TZ | `[x]` |
| D9 | Configure MCP `--toolsets all` for scheduling tool loading | coder | `mcp_config.json` | All 59 tools registered | `[x]` |
| D10 | Register [SCHED-PIPELINE-WIRING] + [MCP-TOOLDISCOVERY] known issues | orchestrator | `known-issues.md` | Issues documented | `[x]` |
| D11 | Add M7 emerging standard (Tool Description Workflow Context) | orchestrator | `emerging-standards.md` | Standard documented | `[x]` |

### Completion Gates

| # | Task | Owner | Deliverable | Validation | Status |
|---|------|-------|-------------|------------|--------|
| G1 | OpenAPI spec drift check (G8 standard) | tester | Drift detected, spec regenerated | `[x]` |
| G2 | ESLint check (scheduling scope) | tester | 0 warnings | `cd ui; npx eslint src/renderer/src/features/scheduling/ --max-warnings 0` → 0 warnings | `[x]` |
| G3 | Production build | tester | Successful build | `electron-vite build` → success | `[x]` |
| G4 | Anti-placeholder scan | tester | 0 matches | `rg TODO|FIXME` → clean | `[x]` |
| G5 | MEU gate | tester | 8/8 blocking checks pass | `[x]` |
| G6 | Audit `docs/BUILD_PLAN.md` — update MEU-72 status | orchestrator | Status updated | `[x]` |

### Post-MEU Deliverables

| # | Task | Owner | Deliverable | Validation | Status |
|---|------|-------|-------------|------------|--------|
| P1 | Save session state to pomera_notes | orchestrator | `Memory/Session/Zorivest-gui-scheduling-2026-04-12` | `[x]` |
| P2 | Create handoff | reviewer | `.agent/context/handoffs/112-2026-04-12-gui-scheduling-bp06es1.md` | `[x]` |
| P3 | Create reflection | orchestrator | `docs/execution/reflections/2026-04-12-gui-scheduling-reflection.md` | `[x]` |
| P4 | Append metrics row | orchestrator | Row appended to `docs/execution/metrics.md` | `[x]` |

### E2E Wave Decision

> **Scheduling is not part of E2E waves 0–6** (see [06-gui.md §Wave Activation Schedule](file:///p:/zorivest/docs/build-plan/06-gui.md)). E2E test wiring is intentionally deferred to a future wave after the scheduling GUI surface is stable. All new components include `data-testid` attributes (task B2) so E2E tests can be wired later without source changes.

### Status Legend

| Symbol | Meaning |
|--------|---------|
| `[ ]` | Not started |
| `[/]` | In progress |
| `[x]` | Complete |
| `[B]` | Blocked (must link follow-up) |
