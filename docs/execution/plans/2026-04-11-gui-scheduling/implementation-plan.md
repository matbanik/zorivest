---
project: "2026-04-11-gui-scheduling"
date: "2026-04-11"
source: "docs/build-plan/06e-gui-scheduling.md"
meus: ["MEU-72"]
status: "draft"
template_version: "2.0"
---

# Implementation Plan: Scheduling & Pipeline GUI

> **Project**: `2026-04-11-gui-scheduling`
> **Build Plan Section(s)**: [06e-gui-scheduling.md](file:///p:/zorivest/docs/build-plan/06e-gui-scheduling.md) (matrix item 35b)
> **Status**: `draft`

---

## Goal

Replace the 10-line `SchedulingLayout.tsx` stub with a full scheduling & pipeline management surface. The system is **MCP-first** — AI agents author JSON policy documents via MCP tools; the GUI provides read/edit inspection, manual approval (human-in-the-loop gate), manual triggering, and pipeline run monitoring.

The backend scheduling API (16 endpoints in `scheduling.py`) and domain layer (MEU-77 through MEU-89) are complete. This MEU builds the React GUI that consumes those endpoints.

---

## User Review Required

> [!IMPORTANT]
> **JSON Editor Library Choice**: The plan proposes **CodeMirror 6** (`@codemirror/lang-json` + `codemirror` + `@codemirror/theme-one-dark`) for the policy JSON editor. This adds ~6 npm packages / ~180KB tree-shakeable. **Alternative**: `react-simple-code-editor` + `prism-react-renderer` (~30KB, fewer features — no bracket matching, no inline error markers). Policy documents are complex nested JSON that benefits from bracket matching and error indicators. **Recommendation: CodeMirror 6.**

> [!IMPORTANT]
> **Cron Preview Library**: The plan proposes **`cronstrue`** (~24KB, 0 deps) for human-readable cron descriptions. No viable alternative at comparable quality.

> [!NOTE]
> **`[BOUNDARY-GAP]` F4 — Already Resolved**: BUILD_PLAN.md:267 shows `✅ ~~[BOUNDARY-GAP] F4~~ resolved by MEU-BV6 (2026-04-11)`. The 5 `scheduling.py` write endpoints (`PolicyCreateRequest`, `RunTriggerRequest`, PATCH query params) were already hardened by MEU-89 and MEU-BV6. The `scheduler.py` `PowerEventRequest` hardening in Sub-MEU A is a **standalone boundary validation improvement** — not F4 closure.

---

## Proposed Changes

### Sub-MEU A: Foundation (BV Hardening + TypeScript Types + API Hooks)

**Objective**: Harden `scheduler.py`'s `PowerEventRequest` boundary validation (`extra="forbid"`, `Literal` enum, `StrippedStr`), create typed TypeScript API client, and React Query hooks.

#### Boundary Inventory

| Surface | Schema Owner | Field Constraints | Extra-Field Policy |
|---------|-------------|-------------------|-------------------|
| `POST /scheduler/power-event` body | `PowerEventRequest` (Pydantic) | `event_type`: `Literal["suspend", "resume"]`; `timestamp`: `StrippedStr`, min_length=1 | `extra="forbid"` |
| `POST /scheduling/policies` body | `PolicyCreateRequest` (Pydantic) | `policy_json`: non-empty dict | `extra="forbid"` ✅ already |
| `PUT /scheduling/policies/{id}` body | `PolicyCreateRequest` (Pydantic) | same as create | `extra="forbid"` ✅ already |
| `POST /scheduling/policies/{id}/run` body | `RunTriggerRequest` (Pydantic) | `dry_run`: bool | `extra="forbid"` ✅ already |
| `PATCH /scheduling/policies/{id}/schedule` query | FastAPI `Query()` params | `cron_expression`: min_length=1 + strip; `timezone`: min_length=1 + strip; `enabled`: bool | N/A (query params) |

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-A1 | `PowerEventRequest` rejects extra fields with 422 | Spec: Boundary Input Contract | `{"event_type":"resume","timestamp":"...","extra":"bad"}` → 422 |
| AC-A2 | `PowerEventRequest` rejects unknown `event_type` with 422 | Spec: Boundary Input Contract | `{"event_type":"shutdown","timestamp":"..."}` → 422 |
| AC-A3 | TypeScript types for Policy, Run, RunDetail, Step, SchedulerStatus compile without errors | Local Canon: TradesLayout pattern | `npx tsc --noEmit` passes |
| AC-A4 | `useSchedulingPolicies` hook fetches and returns typed policy list | Local Canon: TradesLayout pattern | MSW mock returns policy list; hook returns typed array |
| AC-A5 | Mutation hooks (`useCreatePolicy`, etc.) invalidate query cache on success | Local Canon: TradesLayout pattern | After mutation, `queryClient.invalidateQueries` called with `['scheduling-policies']` |

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| PowerEventRequest field constraints | Spec: Boundary Input Contract | `extra="forbid"`, `Literal` enum, `StrippedStr` |
| API response model shapes for TS types | Spec: 06e §REST Endpoints, 09 §9.10 | Map from existing Python response models |
| React Query polling intervals | Local Canon: TradesLayout (5s trades, 5s accounts) | 10s for policy list, 30s for scheduler status |
| Hook naming convention | Local Canon: `useAccounts.ts` pattern | `useSchedulingPolicies`, `useSchedulingPolicy`, etc. |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `packages/api/src/zorivest_api/routes/scheduler.py` | modify | Add `extra="forbid"`, `Literal` enum, `StrippedStr` to `PowerEventRequest` |
| `tests/unit/test_api_scheduling.py` | modify | Add 4 BV boundary tests for `PowerEventRequest` |
| `ui/src/renderer/src/features/scheduling/api.ts` | new | TypeScript types + API client functions |
| `ui/src/renderer/src/features/scheduling/hooks.ts` | new | React Query hooks (queries + mutations) |
| `ui/src/renderer/src/features/scheduling/__tests__/hooks.test.ts` | new | ~8 hook unit tests |

---

### Sub-MEU B: Schedule Page UI (List + Detail + CRUD + JSON Editor)

**Objective**: Build the main scheduling page with list+detail split layout, policy CRUD form, cron expression preview, and JSON policy editor.

#### Boundary Inventory

| Surface | Schema Owner | Field Constraints | Extra-Field Policy |
|---------|-------------|-------------------|-------------------|
| UI form → `POST /scheduling/policies` | `PolicyCreateRequest` (Pydantic, upstream) | `policy_json` required, non-empty | Upstream `extra="forbid"` |
| UI form → `PUT /scheduling/policies/{id}` | `PolicyCreateRequest` (Pydantic, upstream) | same | Upstream `extra="forbid"` |
| UI form → `PATCH /scheduling/policies/{id}/schedule` | FastAPI `Query()` (upstream) | cron, timezone, enabled | N/A (query params) |

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-B1 | Route `/scheduling` renders SchedulingLayout with policy list | Spec: 06e §Layout | Empty-state shown when API returns 0 policies |
| AC-B2 | Clicking a policy card shows detail panel with form fields | Spec: 06e §Detail Fields | — |
| AC-B3 | Cron expression field shows live human-readable preview | Spec: 06e §Cron Preview | Invalid cron shows error message |
| AC-B4 | JSON editor renders with syntax highlighting | Spec: 06e §Policy JSON editor | Invalid JSON shows error indicator |
| AC-B5 | Save persists policy changes via PUT API | Spec: 06e §Action Buttons | — |
| AC-B6 | Delete removes policy with confirmation dialog | Spec: 06e §Action Buttons | Cancel on dialog does NOT delete |
| AC-B7 | "+ New Schedule" creates a new policy via POST API | Spec: 06e §Layout | — |
| AC-B8 | Approve button (GUI-only) marks policy for scheduling | Spec: 06e §MCP-First Design ¶approve_policy is intentionally GUI-only | — |
| AC-B9 | Timezone dropdown includes common US/EU timezones + UTC default | Spec: 06e §Detail Fields | — |
| AC-B10 | Empty state shown when no policies exist | Local Canon: TradesLayout empty state pattern | — |

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| List+detail split layout proportions | Spec: 06e §Layout wireframe | Left ~40%, right ~60% |
| Policy card fields | Spec: 06e §Schedule List Card Fields | enabled icon, name, cron (human-readable), next run time |
| Detail form fields | Spec: 06e §Schedule Detail Fields | 6 fields: name, enabled, cron, timezone, skip_if_running, misfire_grace |
| Action buttons | Spec: 06e §Action Buttons | Save, Test Run, Run Now, Delete |
| Cron preview display | Spec: 06e §Cron Expression Preview | `cronstrue` library for conversion |
| JSON editor component | Spec: 06e §Outputs | CodeMirror 6 with JSON mode |
| Approve is GUI-only | Spec: 06e §MCP-First Design ¶Note | Approve button in detail panel |
| Timezone options | Research-backed | Standard IANA timezones; common US/EU subset |
| Confirmation dialog pattern | Local Canon: TradeDetailPanel delete confirmation | Reuse same dialog pattern |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `ui/src/renderer/src/features/scheduling/SchedulingLayout.tsx` | modify | Replace stub with full list+detail split layout |
| `ui/src/renderer/src/features/scheduling/ScheduleListPanel.tsx` | new | Left pane — policy cards with status icons |
| `ui/src/renderer/src/features/scheduling/ScheduleDetailPanel.tsx` | new | Right pane — form sections + actions |
| `ui/src/renderer/src/features/scheduling/CronPreview.tsx` | new | Live cron → human-readable preview |
| `ui/src/renderer/src/features/scheduling/PolicyEditor.tsx` | new | CodeMirror 6 JSON editor wrapper |
| `ui/src/renderer/src/features/scheduling/__tests__/scheduling.test.tsx` | new | ~15 component rendering + interaction tests |

---

### Sub-MEU C: Pipeline Execution + Run History

**Objective**: Build execution controls (Test Run / Run Now) and run history table with expandable step-level error details.

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-C1 | "Test Run" triggers dry-run (`dry_run=true`) and shows status feedback | Spec: 06e §Action Buttons | — |
| AC-C2 | "Run Now" triggers real execution with confirmation prompt | Spec: 06e §Action Buttons | Cancel on confirmation does NOT trigger |
| AC-C3 | Run history table shows timestamp, status icon, duration, details | Spec: 06e §Run History Table | — |
| AC-C4 | Failed runs expand to show step-level error details | Spec: 06e §Run History ¶"Clicking a failed run expands..." | — |
| AC-C5 | Auto-refresh when a run shows ⏳ Running status | Local Canon: polling pattern (TradesLayout) | — |
| AC-C6 | Run history filters by selected policy | Spec: 06e §Layout | — |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `ui/src/renderer/src/features/scheduling/ScheduleDetailPanel.tsx` | modify | Add Test Run / Run Now action buttons |
| `ui/src/renderer/src/features/scheduling/RunHistoryTable.tsx` | new | Run history table with expandable rows |
| `ui/src/renderer/src/features/scheduling/RunDetailExpander.tsx` | new | Step-level execution detail for a run |
| `ui/src/renderer/src/features/scheduling/SchedulingLayout.tsx` | modify | Add run history section below list+detail |
| `ui/src/renderer/src/features/scheduling/__tests__/run-history.test.tsx` | new | ~8 run history tests |

---

## New Dependencies

| Package | Version | Size (approx.) | Purpose |
|---------|---------|----------------|---------|
| `@codemirror/state` | ^6 | ~45KB | CodeMirror core state management |
| `@codemirror/view` | ^6 | ~90KB | CodeMirror view layer |
| `@codemirror/lang-json` | ^6 | ~15KB | JSON language support |
| `codemirror` | ^6 | meta | CodeMirror convenience meta-package |
| `@codemirror/theme-one-dark` | ^6 | ~5KB | Dark theme matching Zorivest palette |
| `cronstrue` | ^2 | ~24KB | Cron expression → human-readable text |

Total bundle impact: ~180KB (tree-shakeable).

---

## Out of Scope

- MCP tool implementations (already complete in MEU-89)
- Pipeline engine internals (complete in MEU-83–88)
- Step type parameter editing UI (future enhancement)
- Real-time WebSocket updates for run progress (future enhancement; polling is sufficient for MVP)
- Policy template gallery / presets (future enhancement)

---

### Sub-MEU D: Stabilization & UX Polish (Unplanned Session Work)

**Objective**: Address user-reported bugs and UX gaps discovered during live testing of the scheduling GUI and related surfaces.

#### Acceptance Criteria (Post-Hoc)

| AC | Description | Source | Status |
|----|-------------|--------|--------|
| AC-D1 | Default timezone setting (`scheduling.default_timezone`) registered in `APP_DEFAULTS`, persisted via Settings API, and loaded as default for new policies | Human-approved | ✅ |
| AC-D2 | Keyboard shortcuts `Ctrl+1` through `Ctrl+5` work (changed to `Ctrl+Shift+{N}` due to OS conflict) | Human-approved | ✅ |
| AC-D3 | "Settings:" label displayed in front of `Ctrl+K` command palette button | Human-approved | ✅ |
| AC-D4 | Accounts page replaces Sort: dropdown with column header sorting (matching Trades pattern) | Human-approved | ✅ |
| AC-D5 | "Apply to Plan" calculator button copies Account, Price, Stop, Target into Trade Plan form | Human-approved | ✅ |
| AC-D6 | Scheduling policy deletion works (Confirm Delete button functional) | Human-approved | ✅ |
| AC-D7 | "Apply to Plan" button grayed out when Calculator opened from non-Trade Plan context | Human-approved: UX2 pattern | ✅ |
| AC-D8 | New scheduling policies use configured default timezone instead of hardcoded UTC | Human-approved | ✅ |
| AC-D9 | MCP scheduling toolset loads with `--toolsets all` config | Human-approved | ✅ |
| AC-D10 | TDD tests for `scheduling.default_timezone` setting persistence | TDD Protocol (G19) | ✅ |

#### Known Issues Registered

| ID | Issue | Next Steps |
|----|-------|------------|
| `[SCHED-PIPELINE-WIRING]` | Pipeline runtime wiring incomplete for end-to-end fetch step execution | Full discovery MEU |
| `[MCP-TOOLDISCOVERY]` | MCP tool descriptions lack workflow context for AI discoverability | Full audit of all 9 toolsets |

#### Emerging Standard Added

| ID | Title | Severity |
|----|-------|----------|
| M7 | Tool Description Workflow Context | 🟡 Medium |

#### Files Modified (Stabilization)

| File | Action | Summary |
|------|--------|---------|
| `packages/core/src/zorivest_core/domain/settings.py` | modify | Register `scheduling.default_timezone` in `APP_DEFAULTS` |
| `ui/src/renderer/src/registry/commandRegistry.ts` | modify | Fix keyboard shortcuts (Ctrl+Shift+N), add Settings label |
| `ui/src/renderer/src/features/accounts/AccountsHome.tsx` | modify | Replace Sort dropdown with column header sorting |
| `ui/src/renderer/src/features/planning/TradePlanPage.tsx` | modify | Handle Apply to Plan event with Account/Price/Stop/Target |
| `ui/src/renderer/src/features/scheduling/SchedulingLayout.tsx` | modify | Fix policy deletion, load default timezone for new policies |
| `ui/src/renderer/src/features/settings/SettingsLayout.tsx` | modify | Add timezone dropdown in Settings page |
| `c:\Users\Mat\.gemini\antigravity\mcp_config.json` | modify | Add `--toolsets all` to MCP server args |
| `.agent/context/known-issues.md` | modify | Add SCHED-PIPELINE-WIRING, MCP-TOOLDISCOVERY |
| `.agent/docs/emerging-standards.md` | modify | Add M7 standard |
| `tests/unit/test_api_settings.py` | modify | Add TDD tests for timezone setting |

---

## BUILD_PLAN.md Audit

This project modifies the status of MEU-72 from `⬜` to `✅`. Changes needed:

1. Update MEU-72 status column: `⬜` → `✅`
2. Verify no stale references to old scheduling GUI status

> [!NOTE]
> The `[BOUNDARY-GAP]` F4 prerequisite is **already resolved** in BUILD_PLAN.md:267 (`✅ ~~F4~~ resolved by MEU-BV6, 2026-04-11`). The `scheduler.py` `PowerEventRequest` hardening in Sub-MEU A is a standalone boundary validation improvement — it is **not** F4 closure.

```powershell
rg "MEU-72|gui-scheduling" docs/BUILD_PLAN.md *> C:\Temp\zorivest\build-plan-audit.txt; Get-Content C:\Temp\zorivest\build-plan-audit.txt
```

---

## Verification Plan

### 1. Python BV Tests
```powershell
uv run pytest tests/unit/test_api_scheduling.py -x --tb=short -v *> C:\Temp\zorivest\pytest-sched.txt; Get-Content C:\Temp\zorivest\pytest-sched.txt | Select-Object -Last 40
```

### 2. TypeScript Type Check
```powershell
cd p:\zorivest\ui; npx tsc --noEmit *> C:\Temp\zorivest\tsc-sched.txt; Get-Content C:\Temp\zorivest\tsc-sched.txt | Select-Object -Last 30
```

### 3. Vitest GUI Tests
```powershell
cd p:\zorivest\ui; npx vitest run src/renderer/src/features/scheduling/ *> C:\Temp\zorivest\vitest-sched.txt; Get-Content C:\Temp\zorivest\vitest-sched.txt | Select-Object -Last 40
```

### 4. MEU Gate
```powershell
uv run python tools/validate_codebase.py --scope meu *> C:\Temp\zorivest\validate-meu.txt; Get-Content C:\Temp\zorivest\validate-meu.txt | Select-Object -Last 50
```

### 5. OpenAPI Spec Drift Check (G8 standard)
```powershell
uv run python tools/export_openapi.py --check openapi.committed.json *> C:\Temp\zorivest\openapi-check.txt; Get-Content C:\Temp\zorivest\openapi-check.txt
```
> If drift detected, regenerate:
```powershell
uv run python tools/export_openapi.py -o openapi.committed.json *> C:\Temp\zorivest\openapi-regen.txt; Get-Content C:\Temp\zorivest\openapi-regen.txt
```

### 6. Anti-Placeholder Scan
```powershell
rg "TODO|FIXME|NotImplementedError" ui/src/renderer/src/features/scheduling/ *> C:\Temp\zorivest\placeholder-scan.txt; Get-Content C:\Temp\zorivest\placeholder-scan.txt
```

### 7. ESLint Check (Scheduling Scope)

> **Note**: The repo-wide `npx eslint src/ --max-warnings 0` has 22 pre-existing warnings from prior MEUs (accounts, planning, trades, hooks). This project's lint gate is scoped to scheduling files only — 0 warnings in scope.

```powershell
cd p:\zorivest\ui; npx eslint src/renderer/src/features/scheduling/ --max-warnings 0 *> C:\Temp\zorivest\eslint-sched.txt; Get-Content C:\Temp\zorivest\eslint-sched.txt | Select-Object -Last 20
```

### 8. Production Build
```powershell
cd p:\zorivest\ui; npm run build *> C:\Temp\zorivest\build-sched.txt; Get-Content C:\Temp\zorivest\build-sched.txt | Select-Object -Last 20
```

### 9. data-testid Planning
> Scheduling is **not** part of E2E waves 0–6 (see [06-gui.md §Wave Activation Schedule](file:///p:/zorivest/docs/build-plan/06-gui.md)). E2E coverage is intentionally deferred to a future wave after the scheduling GUI surface is stable. However, all new components MUST include `data-testid` attributes using constants from `ui/tests/e2e/test-ids.ts` so that E2E tests can be wired later without source changes.
>
> **Required test-id constants** to add to `test-ids.ts`:
> - `SCHEDULING.POLICY_LIST`, `SCHEDULING.POLICY_CARD`, `SCHEDULING.DETAIL_PANEL`
> - `SCHEDULING.CRON_PREVIEW`, `SCHEDULING.JSON_EDITOR`, `SCHEDULING.RUN_HISTORY`
> - `SCHEDULING.BTN_SAVE`, `SCHEDULING.BTN_TEST_RUN`, `SCHEDULING.BTN_RUN_NOW`, `SCHEDULING.BTN_DELETE`, `SCHEDULING.BTN_APPROVE`

---

## Decisions (Resolved from Open Questions)

> [!NOTE]
> **D1: CodeMirror 6 selected** for policy JSON editor. Provides bracket matching, inline error indicators, and proper JSON editing (~180KB tree-shakeable). Lighter alternative (`react-simple-code-editor` + PrismJS, ~30KB) rejected due to missing bracket matching and error markers — insufficient for complex policy JSON documents. *Pending user confirmation.*

> [!NOTE]
> **D2: PATCH endpoint stays as query params.** The `PATCH /policies/{id}/schedule` endpoint uses FastAPI `Query()` params with manual strip validation. This is consistent with the FastAPI pattern for "patch specific fields" operations and the endpoint already has strip+validation logic. No API contract change needed. *Pending user confirmation.*

---

## Research References

- [06e-gui-scheduling.md](file:///p:/zorivest/docs/build-plan/06e-gui-scheduling.md) — GUI spec
- [09-scheduling.md](file:///p:/zorivest/docs/build-plan/09-scheduling.md) — Backend API spec (§9.10, §9.11)
- [scheduling.py](file:///p:/zorivest/packages/api/src/zorivest_api/routes/scheduling.py) — Existing 16-endpoint API
- [scheduler.py](file:///p:/zorivest/packages/api/src/zorivest_api/routes/scheduler.py) — Power event endpoint (BV gap)
- [TradesLayout.tsx](file:///p:/zorivest/ui/src/renderer/src/features/trades/TradesLayout.tsx) — Reference pattern for list+detail split
- [PlanningLayout.tsx](file:///p:/zorivest/ui/src/renderer/src/features/planning/PlanningLayout.tsx) — Reference pattern for tabbed layout
- Handoff [077](file:///p:/zorivest/.agent/context/handoffs/077-2026-03-18-scheduling-api-mcp-bp09s9.10+9.11.md) — MEU-89 scheduling API+MCP implementation
