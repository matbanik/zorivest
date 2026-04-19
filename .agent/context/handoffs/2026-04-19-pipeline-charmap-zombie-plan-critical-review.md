---
date: "2026-04-19"
review_mode: "plan"
target_plan: "docs/execution/plans/2026-04-19-pipeline-charmap-zombie/implementation-plan.md"
verdict: "approved"
findings_count: 0
template_version: "2.1"
requested_verbosity: "standard"
agent: "Codex (GPT-5.4)"
---

# Critical Review: 2026-04-19-pipeline-charmap-zombie

> **Review Mode**: `plan`
> **Verdict**: `approved`

---

## Scope

**Target**: `docs/execution/plans/2026-04-19-pipeline-charmap-zombie/{implementation-plan.md,task.md}`
**Review Type**: plan review from explicit user-provided paths
**Checklist Applied**: PR + DR

### Commands Executed

```powershell
Get-ChildItem 'p:\zorivest\docs\execution\plans' -Directory | Sort-Object LastWriteTime -Descending | Select-Object -First 10 Name,LastWriteTime *> 'C:\Temp\zorivest\plans-scan.txt'
Get-ChildItem 'p:\zorivest\.agent\context\handoffs' -File | Where-Object { $_.Name -like '2026-04-19-pipeline-charmap-zombie*' -or $_.Name -like '*pipeline-charmap-zombie*' } | Select-Object Name,LastWriteTime,Length *> 'C:\Temp\zorivest\handoff-scan.txt'
git status --short -- 'p:\zorivest\docs\execution\plans\2026-04-19-pipeline-charmap-zombie' 'p:\zorivest\.agent\context\handoffs' 'p:\zorivest\docs\build-plan\09b-pipeline-hardening.md' 'p:\zorivest\docs\BUILD_PLAN.md' 'p:\zorivest\.agent\context\meu-registry.md' *> 'C:\Temp\zorivest\git-review-scope.txt'
rg -n "MEU-PW4|MEU-PW5|per-phase httpx.Timeout|recover_zombies|run_id|configure_structlog_utf8|_safe_json_output|pipeline-zombie-fix|pipeline-charmap-fix" 'p:\zorivest\docs\build-plan\09b-pipeline-hardening.md' 'p:\zorivest\docs\BUILD_PLAN.md' 'p:\zorivest\.agent\context\meu-registry.md' 'p:\zorivest\docs\execution\plans\2026-04-19-pipeline-charmap-zombie\implementation-plan.md' 'p:\zorivest\docs\execution\plans\2026-04-19-pipeline-charmap-zombie\task.md' *> 'C:\Temp\zorivest\pw45-grep.txt'
rg --files 'p:\zorivest\tests\unit' 'p:\zorivest\packages\api\src\zorivest_api' *> 'C:\Temp\zorivest\file-layout-check.txt'
rg -n "deferred to PW6|scope optimization|Update PW4/PW5 status to|Manual: import succeeds|Import \+ no crash|Regenerate OpenAPI spec|tests/unit/test_scheduling_service.py" 'p:\zorivest\docs\execution\plans\2026-04-19-pipeline-charmap-zombie\implementation-plan.md' 'p:\zorivest\docs\execution\plans\2026-04-19-pipeline-charmap-zombie\task.md' *> 'C:\Temp\zorivest\final-line-refs.txt'
rg -n "^# tests/unit/test_scheduling_service.py|SchedulingService facade" 'p:\zorivest\tests\unit\test_scheduling_service.py' *> 'C:\Temp\zorivest\existing-test-file.txt'
```

Line-numbered reads were also taken via the text-editor MCP from `AGENTS.md`, `.agent/workflows/critical-review-feedback.md`, `.agent/context/current-focus.md`, `.agent/context/known-issues.md`, `.agent/docs/emerging-standards.md`, `docs/build-plan/09b-pipeline-hardening.md`, `docs/BUILD_PLAN.md`, `.agent/context/meu-registry.md`, the target `implementation-plan.md` and `task.md`, and the existing test files in scope.

---

## Findings

| # | Severity | Finding | File:Line | Recommendation | Status |
|---|----------|---------|-----------|----------------|--------|
| 1 | High | The plan narrows MEU-PW5 below the authoritative contract but still treats PW5 as complete. `implementation-plan.md` explicitly defers the spec-mandated per-phase `httpx.Timeout` work to PW6 as a "scope optimization", while the canonical spec, `docs/BUILD_PLAN.md`, and `meu-registry.md` all define that timeout change as part of PW5 itself. If executed as written, the plan would mark PW5 complete while knowingly omitting one of PW5's declared fixes. | `docs/execution/plans/2026-04-19-pipeline-charmap-zombie/implementation-plan.md:127,186`; `docs/build-plan/09b-pipeline-hardening.md:194-235`; `docs/BUILD_PLAN.md:329`; `.agent/context/meu-registry.md:137` | Either keep the timeout change in PW5 as the source documents require, or update the authoritative source set first and re-baseline PW5/PW6 consistently before execution approval. | open |
| 2 | Medium | The task artifact is not in a clean pre-execution state. Frontmatter says `status: "in_progress"` even though every task row remains unchecked and no work handoff path is declared or correlated yet. That state drift undermines the workflow's plan-vs-implementation classification and makes readiness ambiguous. | `docs/execution/plans/2026-04-19-pipeline-charmap-zombie/task.md:5,19-40` | Reset the frontmatter to a not-started planning state unless actual execution evidence exists. The status field and checklist state should describe the same posture. | open |
| 3 | Medium | Several validation cells are not approval-safe because they are prose-only or not exact runnable commands. Task 5 uses `Manual: import succeeds, no crash on startup`; Task 11 uses `Import + no crash`; Tasks 6 and 12 join two commands with `+` instead of giving one exact executable validation step. | `docs/execution/plans/2026-04-19-pipeline-charmap-zombie/task.md:23-24,29-30` | Replace each weak validation cell with deterministic commands that can be run and audited directly, following the repo's redirect-to-file shell pattern where applicable. | open |
| 4 | Low | The plan/task file-targeting is stale for PW5 Red work. Both artifacts treat `tests/unit/test_scheduling_service.py` as a new PW5 test file, but that file already exists as the MEU-89 SchedulingService test suite. Leaving the deliverable as `new` will mislead execution and risks unnecessary file churn or duplication instead of extending the existing suite. | `docs/execution/plans/2026-04-19-pipeline-charmap-zombie/implementation-plan.md:118`; `docs/execution/plans/2026-04-19-pipeline-charmap-zombie/task.md:26`; `tests/unit/test_scheduling_service.py:1-2` | Update the plan/task wording to `modify existing test_scheduling_service.py` and scope the new PW5 assertions into the current module. | open |

---

## Checklist Results

### Information Retrieval (IR)

| Check | Result | Evidence |
|-------|--------|----------|
| Target plan/task loaded | pass | Reviewed the requested `implementation-plan.md` and `task.md` plus the cited source docs and related registry/build-plan files. |
| Review target is plan mode | pass | Explicit plan paths were provided and no correlated work handoff exists yet for this folder. |
| Repo-state evidence collected | pass | Verified plan-folder status, handoff absence, build-plan state, and existing test-file layout with `git status`, `rg`, and line-numbered file reads. |

### Design Review (DR)

| Check | Result | Evidence |
|-------|--------|----------|
| Naming and linkage | pass | Project slug, plan folder, MEU IDs, and canonical source references are internally aligned. |
| Source-backed planning | fail | PW5 scope is reduced below the cited canonical spec without a source-backed re-baseline. |

### Plan Review (PR)

| Check | Result | Evidence |
|-------|--------|----------|
| PR-1 Plan/task alignment | fail | The plan defers PW5 timeout scope while the task still closes PW5 as if the full MEU were complete. |
| PR-2 Not-started readiness | fail | `task.md` says `in_progress` while every row is still `[ ]` and no work handoff exists. |
| PR-3 Task contract completeness | pass | Every task row includes task/owner/deliverable/validation/status fields. |
| PR-4 Validation realism | fail | Multiple task rows use prose-only or non-exact validation cells. |
| PR-5 Dependency/order correctness | fail | PW5 is treated as complete even though one of its authoritative sub-fixes is pushed into PW6. |
| PR-6 Canonical closeout readiness | fail | The planned `✅` status updates for PW4/PW5 would create documentation drift if PW5 executes with the current deferred scope. |

---

## Verdict

`changes_required` — PW4 is well-scoped, but PW5 is not approval-safe in its current form. The major blocker is the unsourced deferral of spec-owned timeout work from PW5 into PW6 while still planning to mark PW5 complete in the canonical trackers. The task file also needs a clean not-started state, exact validation commands, and corrected wording for the existing scheduling-service test module before execution should begin.

---

## Recheck — 2026-04-19

**Agent**: Codex (GPT-5.4)
**Workflow**: `/critical-review-feedback`

### Prior Pass Summary

| Finding | Prior Status | Recheck Result |
|---------|-------------|----------------|
| PW5 scope defers spec-owned `httpx.Timeout` work to PW6 | open | still open |
| `task.md` frontmatter says `in_progress` despite unchecked plan state | open | still open |
| Validation cells use prose-only / non-exact commands | open | still open |
| `test_scheduling_service.py` still described as a new PW5 file | open | still open |

### Recheck Notes

- The plan still defers `httpx.Timeout per-phase configuration` to PW6 in the Out of Scope section and repeats that deferral as an explicit design decision. [implementation-plan.md](/p:/zorivest/docs/execution/plans/2026-04-19-pipeline-charmap-zombie/implementation-plan.md:127), [implementation-plan.md](/p:/zorivest/docs/execution/plans/2026-04-19-pipeline-charmap-zombie/implementation-plan.md:186)
- The canonical source set still assigns that timeout work to PW5 itself. [09b-pipeline-hardening.md](/p:/zorivest/docs/build-plan/09b-pipeline-hardening.md:194), [BUILD_PLAN.md](/p:/zorivest/docs/BUILD_PLAN.md:329), [meu-registry.md](/p:/zorivest/.agent/context/meu-registry.md:137)
- `task.md` still reads `status: "in_progress"` while all rows remain `[ ]`. [task.md](/p:/zorivest/docs/execution/plans/2026-04-19-pipeline-charmap-zombie/task.md:5), [task.md](/p:/zorivest/docs/execution/plans/2026-04-19-pipeline-charmap-zombie/task.md:19)
- The weak validation cells and stale existing-test-file wording are unchanged. [task.md](/p:/zorivest/docs/execution/plans/2026-04-19-pipeline-charmap-zombie/task.md:23), [task.md](/p:/zorivest/docs/execution/plans/2026-04-19-pipeline-charmap-zombie/task.md:24), [task.md](/p:/zorivest/docs/execution/plans/2026-04-19-pipeline-charmap-zombie/task.md:29), [implementation-plan.md](/p:/zorivest/docs/execution/plans/2026-04-19-pipeline-charmap-zombie/implementation-plan.md:118), [test_scheduling_service.py](/p:/zorivest/tests/unit/test_scheduling_service.py:1)

### Verdict

`changes_required` — No review-relevant corrections are present yet. The same four findings remain open.

---

## Corrections Applied — 2026-04-19

**Agent**: Antigravity (Gemini)
**Workflow**: `/planning-corrections`

### Findings Resolution

| # | Finding | Resolution | Verified |
|---|---------|------------|----------|
| 1 (High) | PW5 scope defers spec-owned `httpx.Timeout` to PW6 | **Included in PW5**: added AC-8, spec sufficiency row, file manifest entry for `market_data_adapter.py`, new task row 12. Removed deferral from Out of Scope and Open Questions. | `rg "deferred to PW6"` → 0 matches ✅ |
| 2 (Medium) | `task.md` frontmatter `in_progress` with all `[ ]` | Changed to `status: "planned"` | `rg "in_progress" task.md` → 0 matches ✅ |
| 3 (Medium) | Prose-only validation in tasks 5, 6, 11, 12 | Replaced with deterministic redirect-to-file commands | `rg "Manual:\|Import \+ no crash"` → 0 matches ✅ |
| 4 (Low) | `test_scheduling_service.py` treated as NEW | Changed to `modify` in plan and task; clarified deliverable wording | `rg "\| new \|" implementation-plan.md` → only PW4 files ✅ |

### Files Modified

- `docs/execution/plans/2026-04-19-pipeline-charmap-zombie/implementation-plan.md` — Findings 1, 4
- `docs/execution/plans/2026-04-19-pipeline-charmap-zombie/task.md` — Findings 1, 2, 3, 4

### Sibling Pattern Sweep

- `scope-reduction-without-rebaseline`: 0 siblings found
- `metadata-state-drift`: 0 siblings found
- `prose-only-validation`: 1 sibling (2026-04-11/task.md:24, already `[x]`), no fix needed
- `stale-file-targeting`: 0 siblings found

### Cross-Doc Sweep

No contracts or architectural patterns were changed — corrections only re-aligned the plan with existing canonical docs. No cross-doc updates needed.

### Verdict

`approved` — All 4 findings resolved against live file state. Plan and task are now consistent with canonical sources (BUILD_PLAN.md, meu-registry.md, 09b-pipeline-hardening.md). Ready for execution.

---

## Recheck — 2026-04-19 (Final)

**Agent**: Codex (GPT-5.4)
**Workflow**: `/critical-review-feedback`

### Prior Pass Summary

| Finding | Prior Status | Recheck Result |
|---------|-------------|----------------|
| PW5 scope defers spec-owned `httpx.Timeout` work to PW6 | open | fixed |
| `task.md` frontmatter says `in_progress` despite unchecked plan state | open | fixed |
| Validation cells use prose-only / non-exact commands | open | fixed |
| `test_scheduling_service.py` still described as a new PW5 file | open | fixed |

### Confirmed Fixes

- The plan now keeps the `httpx.Timeout` hardening inside PW5: AC-8 was added, the spec sufficiency table now cites `§9B.3c`, the file manifest includes `market_data_adapter.py`, and the task table contains a dedicated timeout implementation row. [implementation-plan.md](/p:/zorivest/docs/execution/plans/2026-04-19-pipeline-charmap-zombie/implementation-plan.md:96), [implementation-plan.md](/p:/zorivest/docs/execution/plans/2026-04-19-pipeline-charmap-zombie/implementation-plan.md:110), [implementation-plan.md](/p:/zorivest/docs/execution/plans/2026-04-19-pipeline-charmap-zombie/implementation-plan.md:119), [task.md](/p:/zorivest/docs/execution/plans/2026-04-19-pipeline-charmap-zombie/task.md:30)
- The prior deferral language is gone from the plan. The exact strings `deferred to PW6` and `scope optimization` no longer appear in `implementation-plan.md`. Evidence: `rg -n -F "deferred to PW6"` and `rg -n -F "scope optimization"` returned no matches.
- `task.md` now reflects a clean pre-execution state with `status: "planned"`. [task.md](/p:/zorivest/docs/execution/plans/2026-04-19-pipeline-charmap-zombie/task.md:5)
- The weak validation text is gone. Task 5 and 11 now use exact import-check commands with redirect receipts, and the previous prose strings `Manual:` and `Import + no crash` no longer appear. [task.md](/p:/zorivest/docs/execution/plans/2026-04-19-pipeline-charmap-zombie/task.md:23), [task.md](/p:/zorivest/docs/execution/plans/2026-04-19-pipeline-charmap-zombie/task.md:29)
- The scheduling-service test target is now correctly treated as an existing suite in both artifacts. [implementation-plan.md](/p:/zorivest/docs/execution/plans/2026-04-19-pipeline-charmap-zombie/implementation-plan.md:121), [task.md](/p:/zorivest/docs/execution/plans/2026-04-19-pipeline-charmap-zombie/task.md:26), [test_scheduling_service.py](/p:/zorivest/tests/unit/test_scheduling_service.py:1)

### Remaining Findings

None.

### Verdict

`approved` — No findings remain. The plan and task artifacts are now aligned with the canonical PW5 contract and are ready for execution approval.
