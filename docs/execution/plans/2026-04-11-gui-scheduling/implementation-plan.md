# MEU-72: Scheduling & Pipeline GUI

> Build Plan: [06e-gui-scheduling.md](file:///p:/zorivest/docs/build-plan/06e-gui-scheduling.md) | Matrix Item: 35b | Phase: P2

---

## Goal

Replace the `SchedulingLayout.tsx` stub with a full scheduling & pipeline management surface. The system is **MCP-first** — AI agents author JSON policy documents; the GUI provides read/edit inspection, manual overrides, and pipeline monitoring.

---

## User Review Required

> [!IMPORTANT]
> **JSON Editor Library Choice**: The plan proposes **CodeMirror 6** (`@codemirror/lang-json`) for the policy JSON editor. This adds ~6 new npm dependencies. **Alternative**: `react-simple-code-editor` + `prism-react-renderer` (lighter, fewer features). The policy documents are complex nested JSON that benefits from bracket matching and error indicators — CodeMirror 6 is recommended.

> [!IMPORTANT]
> **Cron Preview Library**: The plan proposes **`cronstrue`** (~24KB, 0 deps) for human-readable cron descriptions. This is the standard library for this purpose. No viable alternative exists at comparable quality.

> [!WARNING]
> **`[BOUNDARY-GAP]` F4 Status**: The BUILD_PLAN.md warning says "5 write endpoints lack Pydantic schema enforcement." After investigation, **most hardening is already done** (MEU-89 applied `extra="forbid"` to `PolicyCreateRequest` and `RunTriggerRequest`). The remaining gap is **`scheduler.py`'s `PowerEventRequest`** which lacks `extra="forbid"` and enum constraints on `event_type`. This is resolved as a pre-task in Sub-MEU A.

---

## Proposed Changes

### Sub-MEU A: Foundation (BV Hardening + TypeScript Types + API Hooks)

**Objective**: Close the boundary gap, create typed API client functions, and React Query hooks for the scheduling surface.

---

#### [MODIFY] [scheduler.py](file:///p:/zorivest/packages/api/src/zorivest_api/routes/scheduler.py)
- Add `model_config = {"extra": "forbid"}` to `PowerEventRequest`
- Constrain `event_type` to `Literal["suspend", "resume"]`
- Replace raw `str` timestamp with `StrippedStr` validator
- Add BV tests (extra-field rejection, invalid event_type → 422)

#### [NEW] `ui/src/renderer/src/features/scheduling/api.ts`
TypeScript types + API client functions:
- Types: `Policy`, `PolicyListResponse`, `Run`, `RunDetail`, `Step`, `SchedulerStatus`, `SchedulePatch`
- API functions: `listPolicies`, `getPolicy`, `createPolicy`, `updatePolicy`, `deletePolicy`, `approvePolicy`, `triggerRun`, `getPolicyRuns`, `getRunDetail`, `getSchedulerStatus`, `patchSchedule`

#### [NEW] `ui/src/renderer/src/features/scheduling/hooks.ts`
React Query hooks:
- Queries: `useSchedulingPolicies`, `useSchedulingPolicy`, `usePolicyRuns`, `useRunDetail`, `useSchedulerStatus`
- Mutations: `useCreatePolicy`, `useUpdatePolicy`, `useDeletePolicy`, `useApprovePolicy`, `useTriggerRun`, `usePatchSchedule`
- Polling: 10s for policy list, 30s for scheduler status

**Acceptance Criteria (A):**
- AC-A1: `PowerEventRequest` rejects extra fields with 422 `[Spec: Boundary Input Contract]`
- AC-A2: `PowerEventRequest` rejects unknown `event_type` values `[Spec: Boundary Input Contract]`
- AC-A3: TypeScript types compile without errors `[Local Canon: existing pattern]`
- AC-A4: `useSchedulingPolicies` hook fetches and returns typed policy list `[Local Canon: TradesLayout pattern]`
- AC-A5: Mutation hooks invalidate query cache on success `[Local Canon: TradesLayout pattern]`

---

### Sub-MEU B: Schedule Page UI (List + Detail + CRUD + JSON Editor)

**Objective**: Build the main scheduling page with list+detail split layout, policy CRUD form, cron preview, and JSON policy editor.

---

#### [MODIFY] [SchedulingLayout.tsx](file:///p:/zorivest/ui/src/renderer/src/features/scheduling/SchedulingLayout.tsx)
Replace 10-line stub with full list+detail split layout:
- Left pane (~40%): Schedule list with policy cards
- Right pane (~60%): Schedule detail panel (slides in on selection)
- "+ New Schedule" button in header

#### [NEW] `ui/src/renderer/src/features/scheduling/ScheduleListPanel.tsx`
Left pane component:
- Cards showing: enabled/paused icon, policy name, cron expression (human-readable), next run time
- Selected state highlighting
- Empty state for no policies

#### [NEW] `ui/src/renderer/src/features/scheduling/ScheduleDetailPanel.tsx`
Right pane component with form sections:
- **Schedule Info**: Name (text), Enabled (toggle)
- **Scheduling Trigger**: Cron expression (text + live preview), Timezone (select), Next Run (computed display)
- **Execution Options**: Skip if running (checkbox), Misfire grace (number input)
- **Pipeline Policy**: JSON editor (CodeMirror 6)
- **Actions**: Save, Delete (with confirmation dialog), Approve (GUI-only gate)
- Form validation: cron expression format, required name

#### [NEW] `ui/src/renderer/src/features/scheduling/CronPreview.tsx`
Live cron → human-readable preview using `cronstrue`:
- Displays next scheduled run time
- Error state for invalid cron expressions

#### [NEW] `ui/src/renderer/src/features/scheduling/PolicyEditor.tsx`
JSON editor component wrapping CodeMirror 6:
- Syntax highlighting for JSON
- Error indicators for invalid JSON
- Read-only mode toggle
- Dark theme matching Zorivest palette

**Acceptance Criteria (B):**
- AC-B1: Route `/scheduling` renders SchedulingLayout with policy list `[Spec: 06e §Layout]`
- AC-B2: Clicking a policy card shows detail panel with form fields `[Spec: 06e §Detail Fields]`
- AC-B3: Cron expression field shows live human-readable preview `[Spec: 06e §Cron Preview]`
- AC-B4: JSON editor renders with syntax highlighting `[Spec: 06e §Policy JSON editor]`
- AC-B5: Save persists policy changes via PUT API `[Spec: 06e §Action Buttons]`
- AC-B6: Delete removes policy with confirmation dialog `[Spec: 06e §Action Buttons]`
- AC-B7: "+ New Schedule" creates a new policy via POST API `[Spec: 06e §Layout]`
- AC-B8: Approve button (GUI-only) marks policy for scheduling `[Spec: 06e §MCP-First Design]`
- AC-B9: Timezone dropdown includes common US/EU timezones + UTC `[Spec: 06e §Detail Fields]`
- AC-B10: Empty state shown when no policies exist `[Local Canon: existing pattern]`

---

### Sub-MEU C: Pipeline Execution + Run History

**Objective**: Build execution controls and run history table with expandable error details.

---

#### [MODIFY] `ScheduleDetailPanel.tsx`
Add execution action buttons:
- **Test Run**: Triggers dry-run pipeline (`dry_run=true`), shows status toast
- **Run Now**: Triggers real pipeline execution, shows confirmation first

#### [NEW] `ui/src/renderer/src/features/scheduling/RunHistoryTable.tsx`
Run history table component:
- Columns: Timestamp, Status (✅/❌/⏳), Duration, Details
- Filtered by selected policy ID
- Expandable rows for failed runs → shows step-level error details
- Auto-refresh with 10s polling when a run is in-progress

#### [NEW] `ui/src/renderer/src/features/scheduling/RunDetailExpander.tsx`
Expandable detail for a single run:
- Step-by-step execution status
- Error message and traceback for failed steps
- Duration per step

#### [MODIFY] `SchedulingLayout.tsx`
Add run history section below the list+detail split:
- Visible when a policy is selected
- Shows filtered run history for that policy

**Acceptance Criteria (C):**
- AC-C1: "Test Run" triggers dry-run and shows status feedback `[Spec: 06e §Action Buttons]`
- AC-C2: "Run Now" triggers execution with confirmation prompt `[Spec: 06e §Action Buttons]`
- AC-C3: Run history table displays timestamp, status, duration, and details `[Spec: 06e §Run History Table]`
- AC-C4: Failed runs expand to show step-level error details `[Spec: 06e §Run History]`
- AC-C5: Auto-refresh when a run shows "Running" status `[Local Canon: polling pattern]`
- AC-C6: Run history filters by selected policy `[Spec: 06e §Layout]`

---

## New Dependencies

| Package | Version | Size | Purpose |
|---------|---------|------|---------|
| `@codemirror/state` | ^6 | ~45KB | CodeMirror core state |
| `@codemirror/view` | ^6 | ~90KB | CodeMirror view layer |
| `@codemirror/lang-json` | ^6 | ~15KB | JSON language support |
| `codemirror` | ^6 | meta | CodeMirror convenience package |
| `@codemirror/theme-one-dark` | ^6 | ~5KB | Dark theme matching Zorivest palette |
| `cronstrue` | ^2 | ~24KB | Cron → human-readable text |

Total bundle impact: ~180KB (tree-shakeable).

---

## Open Questions

> [!IMPORTANT]
> **Q1: CodeMirror vs lighter alternative?** CodeMirror 6 adds ~180KB but provides bracket matching, error indicators, and proper JSON editing. `react-simple-code-editor` + PrismJS would be ~30KB but lacks error markers and bracket matching. **Recommendation: CodeMirror 6** for the complexity of policy JSON documents.

> [!IMPORTANT]
> **Q2: PATCH endpoint conversion?** The `PATCH /policies/{id}/schedule` endpoint currently uses query params with manual validation. Should we convert to a body model for BV consistency? **Recommendation: Leave as-is** — query params are valid for this "patch specific fields" pattern and FastAPI handles `Query()` validation natively.

---

## Verification Plan

### Automated Tests

**Python (BV hardening):**
```bash
uv run pytest tests/unit/test_api_scheduling.py -x --tb=short -v *> C:\Temp\zorivest\pytest-sched.txt
```

**TypeScript (GUI):**
```bash
npx vitest run src/renderer/src/features/scheduling/ *> C:\Temp\zorivest\vitest-sched.txt
```

**Type checking:**
```bash
npx tsc --noEmit *> C:\Temp\zorivest\tsc.txt
```

### Test Scope per Sub-MEU

| Sub-MEU | Test File | Test Count (est.) |
|---------|-----------|-------------------|
| A | `test_api_scheduling.py` (extend) | +4 BV tests |
| A | `features/scheduling/__tests__/hooks.test.ts` | ~8 hook tests |
| B | `features/scheduling/__tests__/scheduling.test.tsx` | ~15 component tests |
| C | `features/scheduling/__tests__/run-history.test.tsx` | ~8 run history tests |

### Manual Verification
- Navigate to `/scheduling` and confirm list+detail layout
- Create, edit, and delete a policy
- Verify cron preview updates live
- Trigger test run and verify run history population
