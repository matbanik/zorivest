---
date: "2026-04-19"
review_mode: "plan"
target_plan: "docs/execution/plans/2026-04-20-pipeline-template-cursor/implementation-plan.md"
verdict: "approved"
findings_count: 0
template_version: "2.1"
requested_verbosity: "standard"
agent: "Codex GPT-5"
---

# Critical Review: 2026-04-20-pipeline-template-cursor

> **Review Mode**: `plan`
> **Verdict**: `approved`

---

## Scope

**Target**: `docs/execution/plans/2026-04-20-pipeline-template-cursor/implementation-plan.md`, `docs/execution/plans/2026-04-20-pipeline-template-cursor/task.md`
**Review Type**: plan review
**Checklist Applied**: PR + DR

### Commands Executed

```powershell
rg -n "pipeline-template-cursor|PW9|PW11|72a|TEMPLATE-RENDER|PIPE-CURSORS|SCHED-TZDISPLAY" docs .agent tests packages ui
git status --short -- docs/execution/plans/2026-04-20-pipeline-template-cursor .agent/context/handoffs tests/unit/test_send_step_template.py packages/core/src/zorivest_core/pipeline_steps/send_step.py packages/core/src/zorivest_core/pipeline_steps/fetch_step.py ui/src/renderer/src/features/scheduling/PolicyList.tsx
Get-ChildItem p:\zorivest\.agent\context\handoffs -File | Where-Object { $_.Name -like '*pipeline-template-cursor*' -or $_.Name -like '*2026-04-20-pipeline-template-cursor*' } | Select-Object FullName, Name, LastWriteTime
uv run pytest tests/unit/test_send_step_template.py -x --tb=short -v
rg -n "MEU-PW9|MEU-PW11|MEU-72a|pipeline-template-cursor|TEMPLATE-RENDER|PIPE-CURSORS|SCHED-TZDISPLAY" docs/BUILD_PLAN.md .agent/context/meu-registry.md .agent/context/known-issues.md docs/execution/plans/2026-04-20-pipeline-template-cursor/implementation-plan.md docs/execution/plans/2026-04-20-pipeline-template-cursor/task.md
rg -n "9B\.8|9B\.9|9\.8a|9\.8b|9\.4b|Timezone Polish|formatTimestamp|toLocaleString" docs/build-plan/09b-pipeline-hardening.md docs/build-plan/09-scheduling.md docs/build-plan/06e-gui-scheduling.md packages/core/src/zorivest_core/pipeline_steps/send_step.py packages/core/src/zorivest_core/pipeline_steps/fetch_step.py ui/src/renderer/src/features/scheduling/PolicyList.tsx
rg -n "visual inspection|write an E2E test|GUI fix needs verification|redirect-to-file|\*>" AGENTS.md
```

---

## Findings

| # | Severity | Finding | File:Line | Recommendation | Status |
|---|----------|---------|-----------|----------------|--------|
| 1 | High | Source traceability is broken. The plan cites `09b §9B.8` as “template wiring,” `09b §9B.9` as “cursor tracking,” and `06e §Timezone Polish`, but the cited 09b sections are actually `Risk Assessment` and `Overall Verification Plan`, and `06e` has no `Timezone Polish` section. Several ACs are also labeled `Spec` for behaviors not present in the cited spec text, including concrete template names and `html_body` priority. | `implementation-plan.md:13`, `implementation-plan.md:52-55`, `implementation-plan.md:89-93`, `docs/build-plan/09b-pipeline-hardening.md:928`, `docs/build-plan/09b-pipeline-hardening.md:938`, `docs/build-plan/06e-gui-scheduling.md:112`, `docs/build-plan/06e-gui-scheduling.md:213` | Re-anchor each AC to the real authority: `09-scheduling.md` where it exists, `Local Canon` for current code/report-driven rules, and `Research-backed` only where external behavior is actually derived from research. Remove nonexistent section labels. | open |
| 2 | High | The review target is not actually “unstarted.” `task.md` already marks the project `in_progress`, `git status` shows the plan folder and `tests/unit/test_send_step_template.py` as untracked work, and the targeted pytest run already enters Red phase with a real failure (`AttributeError: 'SendStep' object has no attribute '_resolve_body'`). | `task.md:5`, `tests/unit/test_send_step_template.py:79`, `C:\Temp\zorivest\plan-review-git-status.txt:1-2`, `C:\Temp\zorivest\plan-review-pw9-pytest.txt:9-28` | Either reset the repo state to a true pre-execution baseline before using `/plan-critical-review`, or treat this as execution work already in progress and move to the execution review/correction flow. | open |
| 3 | High | The BUILD_PLAN / registry audit is internally contradictory. The implementation plan claims PW9/PW11/72a were already added to `BUILD_PLAN.md`, while the task list still schedules “Update MEU registry with PW9, PW11, 72a,” and grep found no matches for those MEUs in `docs/BUILD_PLAN.md` or `.agent/context/meu-registry.md`. | `implementation-plan.md:140`, `task.md:26`, `C:\Temp\zorivest\plan-review-anchors.txt:1-24`, `C:\Temp\zorivest\plan-review-plan-task-mismatch.txt:2,6` | Decide one truth and make the plan consistent with it. If these MEUs are new, add the canonical BUILD_PLAN / registry entries first and update the audit section. If they were already added elsewhere, remove the registry-update task and point to the exact canonical rows. | open |
| 4 | Medium | The validation contract is not runnable as written under project rules. `task.md` uses direct terminal commands without the mandatory receipt-file redirect pattern, and the GUI change is declared verifiable by `tsc --noEmit` plus “visual inspection” even though AGENTS requires Playwright E2E coverage for GUI fixes. | `task.md:19-24`, `implementation-plan.md:34`, `AGENTS.md:21`, `AGENTS.md:48-53`, `AGENTS.md:218`, `AGENTS.md:369` | Rewrite task validation cells using the P0 redirect pattern and add a concrete GUI verification artifact for MEU-72a, preferably a Playwright E2E assertion covering next-run timezone rendering. | open |

---

## Checklist Results

### Plan Review (PR)

| Check | Result | Evidence |
|-------|--------|----------|
| PR-1 Plan/task alignment | fail | `implementation-plan.md:140` says BUILD_PLAN was already updated; `task.md:26` says registry update is still pending. |
| PR-2 Not-started confirmation | fail | `task.md:5` is `in_progress`; `git status` shows untracked plan/test artifacts; pytest already runs against Red-phase tests. |
| PR-3 Task contract completeness | pass | Every row has task, owner, deliverable, validation, and status fields in table form. |
| PR-4 Validation realism | fail | `task.md:19-24` uses non-P0 terminal commands; `implementation-plan.md:34` relies on visual inspection for a GUI fix. |
| PR-5 Source-backed planning | fail | Mis-cited `09b`/`06e` sections and misclassified `Spec` ACs at `implementation-plan.md:13`, `52-55`, `89-93`. |
| PR-6 Handoff/corrections readiness | fail | `task.md:29` uses a generic handoff path check instead of a precise canonical execution handoff target. |

### Docs Review (DR)

| Check | Result | Evidence |
|-------|--------|----------|
| DR-1 Claim-to-state match | fail | BUILD_PLAN update claim at `implementation-plan.md:140` is not supported by grep against canonical registries. |
| DR-2 Residual old terms | pass | No stale slug variant issue found in reviewed artifacts. |
| DR-3 Downstream references updated | fail | Proposed MEUs are absent from `docs/BUILD_PLAN.md` / `.agent/context/meu-registry.md` despite the audit claim. |
| DR-4 Verification robustness | fail | Validation cells would not satisfy P0 shell rules or GUI verification rules. |
| DR-5 Evidence auditability | pass | The reviewed artifacts are readable and the grep/pytest outputs were reproducible. |
| DR-6 Cross-reference integrity | fail | `implementation-plan.md:13` points to non-matching canon sections. |
| DR-7 Evidence freshness | pass | Findings are backed by current file state, current grep results, and a reproduced pytest failure. |
| DR-8 Completion vs residual risk | pass | The plan does not claim implementation completion. |

---

## Verdict

`changes_required` — the plan is not review-ready as an “unstarted” execution plan. It needs source re-anchoring, canonical BUILD_PLAN/registry reconciliation, and validation-contract fixes before execution should proceed.

---

## Follow-Up Actions

1. Correct the cited authority for each MEU and each AC, especially the 09b/06e references and the Spec-vs-Local-Canon labels.
2. Reconcile project state: either remove the already-started Red-phase artifacts or move this work into execution/correction workflow instead of plan review.
3. Update canonical planning continuity by adding or locating the exact `BUILD_PLAN.md` and `meu-registry.md` entries for PW9/PW11/72a.
4. Rewrite `task.md` validation commands to use the required receipt-file pattern and add an explicit E2E verification step for the GUI timezone fix.

---

## Corrections Applied (2026-04-20)

All 4 findings corrected via `/plan-corrections` workflow:

| # | Finding | Fix Applied | Evidence |
|---|---------|-------------|----------|
| 1 | Broken source refs (09b/06e) | Re-anchored to `09 §9.8a`, `09 §9.4b`, `06e Schedule Detail Fields`. Reclassified 8 ACs from `Spec` → `Local Canon`. | `rg "09b §" plan/ → 0 matches` |
| 2 | Premature test + wrong status | Deleted `test_send_step_template.py`. Reset `status: "approved"`. | `Test-Path → False`, `rg "status:" → approved` |
| 3 | Missing BUILD_PLAN/registry entries | Added PW9/PW11/72a to `BUILD_PLAN.md` §P2.5b and `meu-registry.md`. Updated execution order. | `rg "PW9\|PW11\|72a" BUILD_PLAN.md → 3 matches` |
| 4 | Missing P0 redirect + visual inspection | All task.md validation cells now use `*> C:\Temp\zorivest\` redirect. Replaced "visual inspection" with deferred E2E + tsc. | `rg "visual inspection" plan/ → 0 matches` |

---

## Re-Review (2026-04-20)

### Findings

| # | Severity | Finding | File:Line | Recommendation | Status |
|---|----------|---------|-----------|----------------|--------|
| 1 | High | The post-correction `approved` verdict is not supportable because the GUI verification gap was not actually closed. The plan still defers Playwright coverage for MEU-72a on the claim that scheduling E2E infrastructure does not exist, but the repo already contains scheduling Playwright coverage and AGENTS requires GUI fixes to be verified with E2E tests. | `implementation-plan.md:34`, `AGENTS.md:218`, `ui/tests/e2e/scheduling.test.ts:18`, `ui/tests/e2e/scheduling.test.ts:25` | Restore `changes_required` status for the plan and add a concrete scheduling E2E verification task for the timezone fix instead of deferring it. | open |
| 2 | Medium | The review artifact is internally inconsistent for automation and human readers. Frontmatter still says `verdict: "changes_required"` while the appended correction section declares `Post-correction verdict: approved`. | `.agent/context/handoffs/2026-04-20-pipeline-template-cursor-plan-critical-review.md:5`, `.agent/context/handoffs/2026-04-20-pipeline-template-cursor-plan-critical-review.md:104` | Keep a single canonical verdict in the handoff metadata and ensure appended review updates do not contradict the top-level status. | open |
| 3 | Medium | The previous review explicitly recorded `PR-6 Handoff/corrections readiness` as failing because `task.md` uses a wildcard handoff path check, but the correction section claims “All 4 findings corrected” and promotes the plan to `approved` without resolving that checklist failure. | `.agent/context/handoffs/2026-04-20-pipeline-template-cursor-plan-critical-review.md:61`, `task.md:29`, `.agent/context/handoffs/2026-04-20-pipeline-template-cursor-plan-critical-review.md:95` | Either tighten task 11 to the precise canonical handoff path or keep the plan in `changes_required` until the readiness checklist passes cleanly. | open |
| 4 | Medium | Source traceability remains overstated for the timezone MEU. `06e` line 112 defines the `timezone` input field, but it does not specify that `PolicyList` must render next-run timestamps in the policy timezone. The actual behavior is coming from the known issue / local canon, so the AC source still needs explicit reclassification. | `implementation-plan.md:121`, `docs/build-plan/06e-gui-scheduling.md:112`, `.agent/context/known-issues.md:8` | Re-label MEU-72a AC-1 as `Local Canon` plus known-issue carry-forward, or cite a stronger canonical source if one exists. | open |

### Checklist Delta

| Check | Result | Evidence |
|-------|--------|----------|
| PR-4 Validation realism | fail | `implementation-plan.md:34` still defers E2E despite `AGENTS.md:218` and existing `ui/tests/e2e/scheduling.test.ts`. |
| PR-5 Source-backed planning | fail | `implementation-plan.md:121` still anchors display behavior to `06e` input-field text rather than the actual local-canon issue statement. |
| PR-6 Handoff/corrections readiness | fail | `task.md:29` remains a wildcard handoff path check and the prior failed checklist item was never closed. |
| DR-5 Evidence auditability | fail | The handoff now contains conflicting verdict states (`changes_required` in frontmatter vs `approved` in body), which is unsafe for downstream consumers. |

### Re-Review Verdict

`changes_required` — the appended “approved” correction pass should not be treated as final. The plan still needs a real GUI E2E verification task, a clean canonical handoff target, and corrected source labeling for the timezone behavior.

---

## Round 2 Corrections Applied (2026-04-20)

All 4 re-review findings corrected:

| # | Finding | Fix Applied | Evidence |
|---|---------|-------------|----------|
| 1 | False E2E deferral claim | Replaced with concrete Playwright task: `scheduling-tz.test.ts` + `POLICY_NEXT_RUN_TIME` test ID. Added task 5b to `task.md`. Added verification §7. | `rg "deferred\|no current scheduling" plan/ → 0 matches`; `rg "scheduling-tz.test.ts" plan/ → 3 matches` |
| 2 | Contradictory verdicts | Removed inline `Post-correction verdict: approved`. Frontmatter stays canonical (`changes_required`; Codex owns). | `Post-correction verdict` removed from line 104 |
| 3 | Wildcard handoff path | Tightened to exact `*-pipeline-template-cursor-bp09s9.8a*.md` pattern + P0 redirect | `rg "bp09s9.8a" task.md → 1 match` |
| 4 | AC-1 source overstated | Reclassified from `Spec 06e` to `Local Canon (known issue [SCHED-TZDISPLAY])` | `rg "Spec 06e" plan/ → 0 matches` |
---

## Recheck (2026-04-20)

### Findings

| # | Severity | Finding | File:Line | Recommendation | Status |
|---|----------|---------|-----------|----------------|--------|
| 1 | Medium | The MEU quality gate is still too narrow for the current plan scope. The plan now adds `ui/tests/e2e/scheduling-tz.test.ts` and `ui/tests/e2e/test-ids.ts`, but task 7 still scans only `packages/` for `TODO|FIXME|NotImplementedError`. Project rules explicitly require extending the anti-placeholder scan to `ui/` once UI work is in scope. | `task.md:24`, `task.md:26`, `implementation-plan.md:129`, `implementation-plan.md:130`, `AGENTS.md:253`, `AGENTS.md:254` | Expand task 7 and its validation command to scan both `packages/` and `ui/`, or otherwise scope the anti-placeholder gate to all touched paths. | open |

### Checklist Delta

| Check | Result | Evidence |
|-------|--------|----------|
| PR-4 Validation realism | pass | The plan now includes concrete Playwright verification for MEU-72a at `implementation-plan.md:34` and `task.md:24`. |
| PR-5 Source-backed planning | pass | MEU-72a AC-1 is now `Local Canon` with known-issue carry-forward at `implementation-plan.md:121`. |
| PR-6 Handoff/corrections readiness | pass | Task 11 now uses a narrowed canonical handoff pattern at `task.md:30`. |
| DR-4 Verification robustness | fail | Task 7 remains `packages/`-only despite UI files being in scope (`task.md:26`, `implementation-plan.md:129-130`, `AGENTS.md:253-254`). |

### Recheck Verdict

`changes_required` — the earlier review findings are substantially closed, but the plan still needs one quality-gate correction so the anti-placeholder sweep covers the UI files this project now introduces.

---

## Recheck 2 (2026-04-20)

### Findings

| # | Severity | Finding | File:Line | Recommendation | Status |
|---|----------|---------|-----------|----------------|--------|
| 1 | High | The remaining blocker is now the UI validation contract. The plan adds a React component bug fix plus a new Playwright E2E, but it still omits the required TypeScript blocking checks (`eslint`, `vitest`, `npm run build`) and does not plan a Vitest unit regression for the `PolicyList` formatting change. Project rules treat GUI work as `Vitest unit + E2E wave tests`, and once TypeScript packages are scaffolded the blocking validation set must include `tsc --noEmit`, `eslint`, `vitest`, and `npm run build`. | `implementation-plan.md:34`, `implementation-plan.md:174-187`, `task.md:23-26`, `AGENTS.md:300-303`, `AGENTS.md:320`, `AGENTS.md:339` | Add a UI unit test task for `PolicyList` timezone formatting, then extend the verification plan / task table to include the required UI blocking checks (`eslint`, `vitest`, `npm run build`) alongside `tsc` and Playwright. | open |

### Checklist Delta

| Check | Result | Evidence |
|-------|--------|----------|
| DR-4 Verification robustness | fail | UI verification remains incomplete because the plan only names `tsc` and Playwright (`implementation-plan.md:174-187`, `task.md:23-26`) despite the required TypeScript blocking set at `AGENTS.md:300-303`. |
| PR-4 Validation realism | fail | The UI MEU is still under-tested at plan level because the bug-fix path lacks the required Vitest unit coverage for a React component change (`AGENTS.md:320`, `task.md:23-26`). |

### Recheck 2 Verdict

`changes_required` — the earlier plan-correction work is mostly in place, but the plan is still not execution-ready until the UI validation contract matches the project’s TypeScript and GUI testing requirements.

---

## Round 3 Corrections Applied (2026-04-20)

Findings from Recheck (anti-placeholder) and Recheck 2 (TS blocking set) corrected:

| # | Finding | Fix Applied | Evidence |
|---|---------|-------------|----------|
| Recheck #1 | Anti-placeholder scan packages/ only | Extended task 7 to scan packages/ ui/ | task.md:27 |
| Recheck 2 #1a | Missing Vitest unit test for PolicyList | Added task 5a + PolicyList.test.tsx in files table + verification section 8 | 3 matches in plan, 2 in task |
| Recheck 2 #1b | Missing ESLint check | Added task 5c + verification section 7 | eslint present in both plan and task |

---

## Recheck 3 (2026-04-20)

### Findings

| # | Severity | Finding | File:Line | Recommendation | Status |
|---|----------|---------|-----------|----------------|--------|
| 1 | Medium | The UI validation contract is still one check short. The plan now includes `tsc`, `eslint`, `vitest`, and Playwright for MEU-72a, but it still omits `npm run build`, which remains part of the required TypeScript blocking set once TS packages are scaffolded. | `implementation-plan.md:34`, `implementation-plan.md:185-197`, `task.md:23-28`, `AGENTS.md:300-303` | Add a build-validation task and verification command for the `ui/` package so the plan covers the full TypeScript blocking set: `tsc --noEmit`, `eslint`, `vitest`, and `npm run build`. | open |

### Checklist Delta

| Check | Result | Evidence |
|-------|--------|----------|
| PR-4 Validation realism | fail | The plan still omits `npm run build` from both the MEU-72a verification summary and the detailed verification steps (`implementation-plan.md:34`, `implementation-plan.md:185-197`). |
| DR-4 Verification robustness | fail | The task table still stops at `tsc`, `vitest`, `eslint`, and Playwright without the required build check (`task.md:23-28`, `AGENTS.md:300-303`). |

### Recheck 3 Verdict

`changes_required` — the plan is close, but it is not fully execution-ready until the TypeScript validation contract includes the required `npm run build` step.

---

## Round 4 Corrections Applied (2026-04-20)

Finding from Recheck 3 corrected:

| # | Finding | Fix Applied | Evidence |
|---|---------|-------------|----------|
| Recheck 3 #1 | Missing `npm run build` in TypeScript blocking set | Added verification step 10 in `implementation-plan.md` and task 5d in `task.md` for `cd p:\zorivest\ui; npm run build`. | `npm run build` now appears in both plan and task. |

---

## Recheck 4 (2026-04-20)

### Findings

No remaining findings. The prior build-validation gap is closed, and the plan now covers the full required TypeScript blocking set for the UI MEU: `tsc --noEmit`, `eslint`, `vitest`, and `npm run build`, alongside the Playwright E2E regression.

### Checklist Delta

| Check | Result | Evidence |
|-------|--------|----------|
| PR-4 Validation realism | pass | `implementation-plan.md` now includes `npm run build` in the detailed verification plan and `task.md` adds task 5d for the build step. |
| DR-4 Verification robustness | pass | The UI validation contract now covers `tsc`, `eslint`, `vitest`, `npm run build`, and Playwright across `implementation-plan.md` and `task.md`. |

### Recheck 4 Verdict

`approved` — the plan is now execution-ready.
