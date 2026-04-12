---
seq: "112"
date: "2026-04-12"
project: "gui-scheduling"
meu: "MEU-72"
status: "draft"
action_required: "VALIDATE_AND_APPROVE"
template_version: "2.1"
verbosity: "standard"
plan_source: "docs/execution/plans/2026-04-11-gui-scheduling/implementation-plan.md"
build_plan_section: "bp06es1"
agent: "Antigravity (Gemini)"
reviewer: "Codex (GPT-5.4)"
predecessor: "111-2026-04-11-watchlist-redesign-bp06is1+PLAN-NOSIZE.md"
---

# Handoff: 112-2026-04-12-gui-scheduling-bp06es1

> **Status**: `draft`
> **Action Required**: `VALIDATE_AND_APPROVE`

---

## Scope

**MEU**: MEU-72 — Scheduling & Pipeline GUI + Stabilization
**Build Plan Section**: [06e-gui-scheduling.md](file:///p:/zorivest/docs/build-plan/06e-gui-scheduling.md) (matrix item 35b)
**Predecessor**: [111-2026-04-11](file:///p:/zorivest/.agent/context/handoffs/111-2026-04-11-watchlist-redesign-bp06is1+PLAN-NOSIZE.md)

Four sub-MEUs:
- **Sub-MEU A**: BV hardening (PowerEventRequest) + TypeScript types + React Query hooks
- **Sub-MEU B**: Scheduling page UI (list + detail + CRUD + CodeMirror JSON editor)
- **Sub-MEU C**: Pipeline execution controls + run history table
- **Sub-MEU D**: Stabilization & UX polish (unplanned — timezone settings, keyboard shortcuts, account sorting, calculator apply-to-plan, policy deletion fix, MCP toolset loading)

---

## Acceptance Criteria

### Sub-MEU A: Foundation

| AC | Description | Source | Test(s) | Status |
|----|-------------|--------|---------|--------|
| AC-A1 | `PowerEventRequest` rejects extra fields with 422 | Spec: Boundary Input Contract | `test_api_scheduling.py::test_power_event_extra_field_rejected` | ✅ |
| AC-A2 | `PowerEventRequest` rejects unknown `event_type` with 422 | Spec: Boundary Input Contract | `test_api_scheduling.py::test_power_event_invalid_type` | ✅ |
| AC-A3 | TypeScript types compile without errors | Local Canon: TradesLayout pattern | `tsc --noEmit` | ✅ |
| AC-A4 | `useSchedulingPolicies` hook fetches typed policy list | Local Canon: TradesLayout pattern | `scheduling.test.tsx` hook tests | ✅ |
| AC-A5 | Mutation hooks invalidate query cache on success | Local Canon: TradesLayout pattern | `scheduling.test.tsx` mutation tests | ✅ |

### Sub-MEU B: Schedule Page UI

| AC | Description | Source | Test(s) | Status |
|----|-------------|--------|---------|--------|
| AC-B1 | Route `/scheduling` renders SchedulingLayout with policy list | Spec: 06e §Layout | `scheduling.test.tsx` | ✅ |
| AC-B2 | Clicking a policy card shows detail panel | Spec: 06e §Detail Fields | `scheduling.test.tsx` | ✅ |
| AC-B3 | Cron expression shows human-readable preview | Spec: 06e §Cron Preview | `scheduling.test.tsx` | ✅ |
| AC-B4 | JSON editor renders with syntax highlighting | Spec: 06e §Policy JSON editor | `scheduling.test.tsx` | ✅ |
| AC-B5 | Save persists via PUT API | Spec: 06e §Action Buttons | `scheduling.test.tsx` | ✅ |
| AC-B6 | Delete with confirmation | Spec: 06e §Action Buttons | `scheduling.test.tsx` | ✅ |
| AC-B7 | "+ New Schedule" creates policy | Spec: 06e §Layout | `scheduling.test.tsx` | ✅ |
| AC-B8 | Approve button marks policy | Spec: 06e §MCP-First Design | `scheduling.test.tsx` | ✅ |
| AC-B9 | Timezone dropdown with common zones | Spec: 06e §Detail Fields | `scheduling.test.tsx` | ✅ |
| AC-B10 | Empty state when no policies | Local Canon: TradesLayout | `scheduling.test.tsx` | ✅ |

### Sub-MEU C: Pipeline Execution + Run History

| AC | Description | Source | Test(s) | Status |
|----|-------------|--------|---------|--------|
| AC-C1 | "Test Run" triggers dry-run | Spec: 06e §Action Buttons | `scheduling.test.tsx` | ✅ |
| AC-C2 | "Run Now" with confirmation | Spec: 06e §Action Buttons | `scheduling.test.tsx` | ✅ |
| AC-C3 | Run history table | Spec: 06e §Run History Table | `scheduling.test.tsx` | ✅ |
| AC-C4 | Failed runs show step errors | Spec: 06e §Run History | `scheduling.test.tsx` | ✅ |
| AC-C5 | Auto-refresh on Running status | Local Canon: polling pattern | `scheduling.test.tsx` | ✅ |
| AC-C6 | History filters by policy | Spec: 06e §Layout | `scheduling.test.tsx` | ✅ |

### Sub-MEU D: Stabilization (Post-Hoc)

| AC | Description | Source | Status |
|----|-------------|--------|--------|
| AC-D1 | Default timezone setting registered + persisted | Human-approved | ✅ |
| AC-D2 | TDD tests for timezone persistence | TDD Protocol (G19) | ✅ |
| AC-D3 | Keyboard shortcuts Ctrl+Shift+{N} | Human-approved | ✅ |
| AC-D4 | Account column header sorting | Human-approved | ✅ |
| AC-D5 | Calculator Apply to Plan copies values | Human-approved | ✅ |
| AC-D6 | Policy deletion works | Human-approved | ✅ |
| AC-D7 | Apply to Plan disabled outside planning | Human-approved: UX2 | ✅ |
| AC-D8 | New policies use configured TZ | Human-approved | ✅ |
| AC-D9 | MCP `--toolsets all` config | Human-approved | ✅ |
| AC-D10 | TDD timezone tests (Red→Green) | TDD Protocol | ✅ |

<!-- CACHE BOUNDARY -->
<!-- Content above this line is stable across revision passes (KV cache prefix). -->
<!-- Content below this line changes between passes (evidence, results, corrections). -->

---

## Evidence

### FAIL_TO_PASS

| Test | Red Output | Green Output | File:Line |
|------|-----------|--------------|----------|
| Sub-MEU A BV tests (5) | 5 FAILED (422 not raised, extra fields accepted) | 41 passed (final) | `tests/unit/test_api_scheduling.py` |
| Sub-MEU A hook tests (8) | 8 FAILED (modules not found) | 8 passed | `scheduling/__tests__/scheduling.test.tsx` |
| Sub-MEU B component tests (20) | 20 FAILED (components not implemented) | 36 passed (final) | `scheduling/__tests__/scheduling.test.tsx` |
| Sub-MEU C run history tests (6) | 6 FAILED (RunHistory not implemented) | 36 passed (final) | `scheduling/__tests__/scheduling.test.tsx` |
| Sub-MEU D timezone tests | FAILED (setting not registered) | passed | `tests/unit/test_api_settings.py` |

### Commands Executed

| Command | Exit Code | Key Output |
|---------|-----------|------------|
| `uv run pytest tests/unit/test_api_scheduling.py -x --tb=short -v` | 0 | 41 passed |
| `cd ui; npx tsc --noEmit` | 0 | Clean |
| `cd ui; npx vitest run src/renderer/src/features/scheduling/` | 0 | 36 tests passed |
| `cd ui; npx eslint src/renderer/src/features/scheduling/ --max-warnings 0` | 0 | 0 warnings |
| `electron-vite build` | 0 | Build success |
| `rg "TODO\|FIXME\|NotImplementedError" ui/src/renderer/src/features/scheduling/` | 0 | 0 matches |
| `uv run python tools/validate_codebase.py --scope meu` | 0 | 8/8 blocking checks pass |
| `uv run python tools/export_openapi.py --check openapi.committed.json` | 1 | Drift detected, regenerated |

### Quality Gate Results

```
pyright: 0 errors
ruff: 0 violations
pytest: 41 passed (scheduling)
vitest: 36 passed (scheduling) — 29 original + 7 new PolicyDetail action tests
eslint (scheduling scope): 0 warnings (CronPicker + PolicyDetail ESLint fixed)
anti-placeholder: 0 matches
```

---

## Changed Files

| File | Action | Summary |
|------|--------|---------|
| `packages/api/src/zorivest_api/routes/scheduler.py` | modified | `PowerEventRequest` BV hardening (`extra="forbid"`, `Literal`, `StrippedStr`) |
| `tests/unit/test_api_scheduling.py` | modified | 5 BV boundary tests added |
| `ui/src/renderer/src/features/scheduling/api.ts` | new | TypeScript types + API client |
| `ui/src/renderer/src/features/scheduling/hooks.ts` | new | React Query hooks (queries + mutations) |
| `ui/src/renderer/src/features/scheduling/SchedulingLayout.tsx` | modified | Full list+detail split layout, policy CRUD, deletion fix, TZ default |
| `ui/src/renderer/src/features/scheduling/PolicyList.tsx` | new | Left-pane policy card list |
| `ui/src/renderer/src/features/scheduling/PolicyDetail.tsx` | new | Right-pane form + CodeMirror JSON editor |
| `ui/src/renderer/src/features/scheduling/CronPreview.tsx` | new | Cron → human-readable preview |
| `ui/src/renderer/src/features/scheduling/RunHistory.tsx` | new | Run history table with expandable errors |
| `ui/src/renderer/src/features/scheduling/__tests__/scheduling.test.tsx` | modified | 36 component + hook + action tests (originally 29, +7 PolicyDetail action tests in corrections pass) |
| `ui/tests/e2e/test-ids.ts` | modified | SCHEDULING test-id constants |
| `packages/core/src/zorivest_core/domain/settings.py` | modified | `scheduling.default_timezone` in APP_DEFAULTS |
| `ui/src/renderer/src/registry/commandRegistry.ts` | modified | Ctrl+Shift+{N} shortcuts, Settings label |
| `ui/src/renderer/src/features/accounts/AccountsHome.tsx` | modified | Column header sorting (replaces Sort dropdown) |
| `ui/src/renderer/src/features/planning/TradePlanPage.tsx` | modified | Apply to Plan value propagation |
| `ui/src/renderer/src/features/settings/SettingsLayout.tsx` | modified | Timezone dropdown |
| `c:\Users\Mat\.gemini\antigravity\mcp_config.json` | modified | `--toolsets all` for MCP scheduling |
| `.agent/context/known-issues.md` | modified | Added SCHED-PIPELINE-WIRING, MCP-TOOLDISCOVERY |
| `.agent/docs/emerging-standards.md` | modified | Added M7 standard |
| `.agent/context/meu-registry.md` | modified | Added MEU-72 entry |

---

## Known Issues Registered

| ID | Severity | Summary |
|----|----------|---------|
| `[SCHED-PIPELINE-WIRING]` | High | Pipeline runtime wiring incomplete — FetchStep needs PipelineProviderAdapter |
| `[MCP-TOOLDISCOVERY]` | Medium | MCP tool descriptions lack workflow context for AI discoverability — full audit of all 9 toolsets needed |

## Emerging Standards Added

| ID | Title | Severity |
|----|-------|----------|
| M7 | Tool Description Workflow Context | 🟡 Medium |

---

## Codex Validation Report

_Left blank for reviewer agent._

### Recheck Protocol

1. Read Scope + AC table
2. Verify each AC against Evidence section (file:line, not memory)
3. Run all Commands Executed and compare output
4. Run Quality Gate commands independently
5. Record findings below

### Findings

| # | Severity | Finding | File:Line | Recommendation | Status |
|---|----------|---------|-----------|----------------|--------|

### Verdict

`pending` — awaiting Codex review

---

## Deferred Items

| Item | Reason | Follow-up |
|------|--------|-----------|
| End-to-end pipeline execution | Blocked on FetchStep provider adapter wiring | `[SCHED-PIPELINE-WIRING]` known issue — future MEU |
| MCP tool description audit | Out-of-scope for GUI MEU | `[MCP-TOOLDISCOVERY]` known issue — future MEU |
| Cron expression picker UI | Future enhancement | Not in current build plan scope |
| Policy name editing in UI | Future enhancement | UX refinement backlog |

---

## History

| Event | Date | Agent | Detail |
|-------|------|-------|--------|
| Created | 2026-04-12 | Antigravity (Gemini) | Initial handoff — 4 sub-MEUs (A+B+C planned, D stabilization) |
| Submitted for review | 2026-04-12 | Antigravity (Gemini) | Sent to Codex (GPT-5.4) |
| Corrections pass | 2026-04-12 | Antigravity (Gemini) | F1: Separate Test Run/Run Now + window.confirm delete + 7 tests. F2: BUILD_PLAN ⬜→⏳. F3: ESLint 0 warnings + evidence refresh. F4: AccountsLayout→AccountsHome filename. |
