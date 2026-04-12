---
date: "2026-04-11"
review_mode: "plan"
target_plan: "docs/execution/plans/2026-04-11-gui-scheduling/implementation-plan.md"
verdict: "approved"
findings_count: 0
template_version: "2.1"
requested_verbosity: "standard"
agent: "Codex (GPT-5.4)"
---

# Critical Review: 2026-04-11-gui-scheduling

> **Review Mode**: `plan`
> **Verdict**: `approved`

---

## Scope

**Target**: `docs/execution/plans/2026-04-11-gui-scheduling/implementation-plan.md`, `docs/execution/plans/2026-04-11-gui-scheduling/task.md`
**Review Type**: plan review
**Checklist Applied**: PR + DR

### Commands Executed

```powershell
git status --short *> C:\Temp\zorivest\git-status.txt; Get-Content C:\Temp\zorivest\git-status.txt
rg -n "Handoff Naming|MEU|Spec|Local Canon|Research-backed|Human-approved|Validation|task|owner_role|deliverable|status" docs/execution/plans/2026-04-11-gui-scheduling/implementation-plan.md docs/execution/plans/2026-04-11-gui-scheduling/task.md *> C:\Temp\zorivest\plan-rg.txt; Get-Content C:\Temp\zorivest\plan-rg.txt
rg -n "MEU-72|scheduling|E2E|Wave|data-testid|approve_policy|approve" docs/BUILD_PLAN.md docs/build-plan/06e-gui-scheduling.md docs/build-plan/06-gui.md ui/tests/e2e/test-ids.ts *> C:\Temp\zorivest\sched-spec-rg.txt; Get-Content C:\Temp\zorivest\sched-spec-rg.txt
rg -n "@pytest.mark|skip|xfail|TODO|FIXME|NotImplementedError|export_openapi|openapi.committed|eslint|npm run build|data-testid" docs/execution/plans/2026-04-11-gui-scheduling/implementation-plan.md docs/execution/plans/2026-04-11-gui-scheduling/task.md *> C:\Temp\zorivest\plan-quality-rg.txt; Get-Content C:\Temp\zorivest\plan-quality-rg.txt
rg -n "class PowerEventRequest|extra=|Literal\[|event_type|scheduler/status|approve|/policies/.*/approve|runs|RunTriggerRequest|PolicyCreateRequest" packages/api/src/zorivest_api/routes/scheduler.py packages/api/src/zorivest_api/routes/scheduling.py *> C:\Temp\zorivest\api-routes-rg.txt; Get-Content C:\Temp\zorivest\api-routes-rg.txt
rg -n "Tests FIRST|Write ALL tests FIRST|Run tests.*FAIL|npm run build|data-testid|wave's tests pass|OpenAPI Spec Regen After Route Changes|--check openapi.committed.json" AGENTS.md docs/build-plan/06-gui.md .agent/docs/emerging-standards.md *> C:\Temp\zorivest\governing-rules-rg.txt; Get-Content C:\Temp\zorivest\governing-rules-rg.txt
```

---

## Findings

| # | Severity | Finding | File:Line | Recommendation | Status |
|---|----------|---------|-----------|----------------|--------|
| 1 | High | The task order violates the repo's mandatory TDD contract. The plan schedules production changes before the corresponding tests for both the boundary fix and the GUI work, and it never adds an explicit Red-phase / FAIL_TO_PASS step. Executing this checklist as written would break the required tests-first workflow. | `docs/execution/plans/2026-04-11-gui-scheduling/task.md:19-20,25,30-35`; `AGENTS.md:208,224-225` | Reorder each sub-MEU into FIC -> tests -> red proof -> implementation -> refactor -> gates. Add explicit failing-test evidence tasks before touching `scheduler.py` or the React components. | open |
| 2 | High | The GUI completion gates are incomplete. The plan only covers `tsc`, `vitest`, and a generic MEU gate, but it omits required GUI `data-testid` planning, E2E-wave coverage, `eslint`, and `npm run build`. It also never plans any change to `ui/tests/e2e/test-ids.ts`, which currently exposes only `NAV_SCHEDULING` for this surface. | `docs/execution/plans/2026-04-11-gui-scheduling/implementation-plan.md:127-166,206-236`; `docs/execution/plans/2026-04-11-gui-scheduling/task.md:21-35`; `docs/build-plan/06-gui.md:403-425,437`; `AGENTS.md:300,342`; `ui/tests/e2e/test-ids.ts:17` | Add explicit tasks for scheduling `data-testid` constants, any required scheduling E2E coverage or a documented wave decision, `eslint`, and `npm run build` verification. If scheduling is intentionally outside the current E2E waves, state that explicitly instead of silently dropping the gate. | open |
| 3 | High | The plan retargets the canonical `[BOUNDARY-GAP]` F4 prerequisite from `scheduling.py` to `scheduler.py` and then proposes removing the warning from `BUILD_PLAN.md`. The source of truth says the prerequisite is about five `scheduling.py` write routes; the plan claims the remaining gap is `PowerEventRequest` in a different file and component. That is not a like-for-like closure of the documented prerequisite. | `docs/BUILD_PLAN.md:267`; `docs/execution/plans/2026-04-11-gui-scheduling/implementation-plan.md:35,43-49,194-201`; `packages/api/src/zorivest_api/routes/scheduler.py:24-28`; `packages/api/src/zorivest_api/routes/scheduling.py:38-48,118-123` | Either: 1. update the plan to treat `scheduler.py` hardening as a separate boundary fix while leaving F4 wording intact until the canonical prerequisite is formally revised, or 2. document a source-backed correction to `BUILD_PLAN.md` that explicitly says the old F4 warning was stale and why. Do not silently rewrite the prerequisite under a different scope. | open |
| 4 | Medium | The plan is not decision-ready, but the task metadata already marks execution as started. `implementation-plan.md` is still `draft` and contains unresolved user-review items, yet `task.md` is `in_progress` and immediately schedules CodeMirror dependency installation. That bypasses the repo rule that execution starts only after plan approval. | `docs/execution/plans/2026-04-11-gui-scheduling/implementation-plan.md:6,26-35,240-243`; `docs/execution/plans/2026-04-11-gui-scheduling/task.md:5,21`; `AGENTS.md:138-139` | Keep the task in a not-started state until the dependency/editor decision is resolved and the plan is approved. If the library choice is already approved, remove the open question from the plan and normalize the statuses. | open |
| 5 | Medium | The OpenAPI verification step is planned incorrectly. The repo standard is to run `export_openapi.py --check openapi.committed.json` first and regenerate only on drift, but the plan/task unconditionally run `-o`, which turns a validation step into a write step and loses drift evidence. | `docs/execution/plans/2026-04-11-gui-scheduling/implementation-plan.md:228-230`; `docs/execution/plans/2026-04-11-gui-scheduling/task.md:36`; `.agent/docs/emerging-standards.md:138-141` | Change the verification plan to `--check` first, then add a follow-up regeneration task only if drift is detected. | open |

---

## Checklist Results

### Information Retrieval (IR)

| Check | Result | Evidence |
|-------|--------|----------|
| Target plan/task loaded and correlated | pass | Reviewed `implementation-plan.md`, `task.md`, `06e-gui-scheduling.md`, `06-gui.md`, `BUILD_PLAN.md`, and live API route files. |
| Status/readiness evidence collected | pass | `git status --short` showed only the draft plan file modified and `task.md` untracked; `ui/src/renderer/src/features/scheduling/SchedulingLayout.tsx` remains a stub. |
| Canonical prerequisite/source docs checked | pass | Verified MEU-72 prerequisite in `docs/BUILD_PLAN.md:267` and scheduling REST surface in `docs/build-plan/06e-gui-scheduling.md:194-207` plus `packages/api/src/zorivest_api/routes/scheduling.py`. |
| Review target is plan mode, not implementation mode | pass | No correlated work handoff exists; canonical plan review file did not exist before this pass. |

### Design Review (DR)

| Check | Result | Evidence |
|-------|--------|----------|
| Naming convention followed | pass | Plan folder, `implementation-plan.md`, and `task.md` use the expected project slug. |
| Template version present | pass | `implementation-plan.md:7`, `task.md:6`. |
| YAML frontmatter well-formed | pass | Both files parse as expected with matching project slug and source linkage. |

### Plan Review (PR)

| Check | Result | Evidence |
|-------|--------|----------|
| PR-1 Plan/task alignment | fail | Statuses conflict: `implementation-plan.md:6` is `draft`, while `task.md:5` is `in_progress`; execution gating is inconsistent with unresolved review items. |
| PR-2 Not-started confirmation | fail | File state looks not-started in practice, but task metadata says otherwise; review mode remains plan review because no implementation handoff exists. |
| PR-3 Task contract completeness | pass | Each task row has task/owner/deliverable/validation/status columns. |
| PR-4 Validation realism | fail | Validation omits required GUI gates (`eslint`, `npm run build`, `data-testid` / E2E coverage) and uses incorrect OpenAPI `-o` write-first verification. |
| PR-5 Source-backed planning | fail | `[BOUNDARY-GAP]` F4 closure is retargeted from `scheduling.py` to `scheduler.py` without a source-backed canonical correction. |
| PR-6 Handoff/corrections readiness | pass | Findings can be addressed via `/planning-corrections`, and the canonical review file now exists. |

---

## Verdict

`changes_required` — The overall product direction is aligned with `06e-gui-scheduling.md`, but the plan is not execution-safe yet. The blocking issues are TDD order, missing GUI completion gates, and the unsupported rewrite of the canonical F4 prerequisite.

---

## Recheck (2026-04-11)

**Workflow**: `/planning-corrections` recheck
**Agent**: Codex (GPT-5.4)

### Prior Pass Summary

| Finding | Prior Status | Recheck Result |
|---------|-------------|----------------|
| TDD order violated mandatory tests-first workflow | open | ✅ Fixed |
| GUI gates omitted `data-testid`, build, lint, and explicit E2E handling | open | ✅ Fixed |
| F4 prerequisite was retargeted from `scheduling.py` to `scheduler.py` | open | ❌ Still open |
| Plan/task readiness statuses bypassed approval gate | open | ✅ Fixed |
| OpenAPI verification used `-o` instead of `--check` first | open | ✅ Fixed |

### Confirmed Fixes

- `task.md:5` now uses `status: "not_started"`, resolving the previous `draft` vs `in_progress` mismatch.
- `task.md:22-24`, `task.md:26`, `task.md:38`, and `task.md:51` now insert explicit Red-phase / FAIL_TO_PASS steps before implementation work.
- `task.md:36`, `task.md:61-63`, `task.md:77-79`, and `implementation-plan.md:232-263` now cover scheduling `data-testid` planning, `eslint`, `npm run build`, and an explicit E2E-wave decision.
- `task.md:61` and `implementation-plan.md:232-236` now follow G8 correctly with `--check` first and regeneration only on drift.
- `BUILD_PLAN.md:267` plus `implementation-plan.md:35` and `implementation-plan.md:200` now distinguish the already-resolved F4 prerequisite from the standalone `scheduler.py` boundary hardening.

### Remaining Findings

- **Medium** — `implementation-plan.md:43` still says Sub-MEU A will "Close the `[BOUNDARY-GAP]` F4 residual," but the same plan now says F4 is already resolved and that `scheduler.py` hardening is standalone work (`implementation-plan.md:35`, `implementation-plan.md:200`). That contradiction leaves the scope basis ambiguous.

### Verdict

`changes_required` — Four first-pass findings are fixed. One internal scope inconsistency remains in `implementation-plan.md` before the plan is clean for approval.

---

## Corrections Applied — 2026-04-11 (Recheck)

**Agent**: Antigravity (Gemini)

### Resolution

| # | Severity | Finding | Resolution |
|---|----------|---------|------------|
| R1 | Medium | `implementation-plan.md:43` says "Close the `[BOUNDARY-GAP]` F4 residual" — contradicts lines 35 and 200 which say F4 is already resolved | Rewrote objective to: "Harden `scheduler.py`'s `PowerEventRequest` boundary validation (`extra="forbid"`, `Literal` enum, `StrippedStr`), create typed TypeScript API client, and React Query hooks." Removed all F4 closure claims. |

### Verification

```
rg "Close.*F4|F4 residual" → 0 matches (contradiction removed)
rg "BOUNDARY-GAP" → 2 remaining refs (lines 35, 200), both say "Already Resolved" / "not F4 closure" — consistent
```

### Verdict Update

`corrections_applied` — All original findings (5) + recheck finding (1) resolved. No internal contradictions remain. Plan is execution-safe pending user confirmation of D1 (CodeMirror 6) and D2 (PATCH query params).

---

## Recheck (2026-04-11, Final)

**Workflow**: `/planning-corrections` recheck
**Agent**: Codex (GPT-5.4)

### Prior Pass Summary

| Finding | Prior Status | Recheck Result |
|---------|-------------|----------------|
| Sub-MEU A objective still described its work as F4 closure | open | ✅ Fixed |

### Confirmed Fixes

- `implementation-plan.md:43` now reads: `Harden scheduler.py's PowerEventRequest boundary validation ...`, which matches the surrounding plan text that describes this as standalone boundary hardening rather than F4 closure.
- `implementation-plan.md:35` and `implementation-plan.md:200` remain consistent with that scope, both stating that `[BOUNDARY-GAP]` F4 is already resolved in `BUILD_PLAN.md`.
- No new plan/task drift was introduced in the corrected sections. The tests-first ordering, GUI gates, OpenAPI `--check` flow, and `not_started` task status remain intact.

### Remaining Findings

- None.

### Verdict

`approved` — The plan review findings are fully resolved. The plan is ready for user approval / decision on D1 and D2 before execution starts.

---

## Corrections Applied — 2026-04-11

**Agent**: Antigravity (Gemini)

### Resolution Summary

| # | Severity | Finding | Resolution | File(s) Changed |
|---|----------|---------|------------|-----------------|
| 1 | High | TDD order violation — code before tests, no Red-phase steps | Reordered all 3 sub-MEU task blocks to FIC → tests → Red proof → implementation → Green. Added 4 explicit FAIL_TO_PASS evidence tasks (A3, A6, B4, C3). | `task.md` |
| 2 | High | Missing GUI gates (`data-testid`, `eslint`, `npm run build`, E2E wave) | Added: task B2 (data-testid constants), gates G2 (eslint), G3 (npm run build), §E2E Wave Decision section. Added verification plan steps 7–9 in implementation-plan.md. | `task.md`, `implementation-plan.md` |
| 3 | High | F4 prerequisite retargeted from `scheduling.py` to `scheduler.py` | F4 is **already resolved** by MEU-BV6 in BUILD_PLAN.md:267. Removed "close F4" claim. Reframed `scheduler.py` hardening as standalone BV improvement. Updated §User Review Required and §BUILD_PLAN.md Audit. | `implementation-plan.md` |
| 4 | Medium | Status mismatch (`draft` vs `in_progress`) | Normalized `task.md` status to `not_started`. Converted Open Questions to §Decisions (pending user confirmation). | `task.md`, `implementation-plan.md` |
| 5 | Medium | OpenAPI unconditional `-o` vs `--check` first (G8) | Changed to `--check` first with conditional `-o` regen. Task G1 uses two-step pattern. Plan verification step 5 updated. | `task.md`, `implementation-plan.md` |

### Verification Evidence

```
F3 stale F4 check: 0 matches for "F4.*resolves|Remove.*F4|strike.*F4" in plan dir (only the [NOTE] acknowledgment remains)
F1 TDD order: 8 test/Red proof tasks found (A2, A3, A5, A6, B3, B4, C2, C3) — all precede their implementation tasks
F2 GUI gates: eslint (G2), npm run build (G3), data-testid (B2), E2E wave decision section — all present
F5 OpenAPI: --check first in both plan (step 5) and task (G1)
F4 status: implementation-plan.md = "draft", task.md = "not_started" — aligned
```

### Verdict Update

`corrections_applied` — All 5 findings addressed. Plan is now execution-safe pending user approval of D1 (CodeMirror 6) and D2 (PATCH query params). Ready for re-review or execution.
