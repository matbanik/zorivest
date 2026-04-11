---
date: "2026-04-11"
review_mode: "implementation"
target_plan: "docs/execution/plans/2026-04-11-pyright-test-cleanup/implementation-plan.md"
verdict: "changes_required"
findings_count: 3
template_version: "2.1"
requested_verbosity: "standard"
agent: "GPT-5.4 Codex"
---

# Critical Review: 2026-04-11-pyright-test-cleanup

> **Review Mode**: `implementation`
> **Verdict**: `changes_required`

---

## Scope

**Target**: `docs/execution/plans/2026-04-11-pyright-test-cleanup/implementation-plan.md`, `task.md`, sibling handoffs [108-2026-04-11-pyright-enum-literals-bpTSsB.md](/p:/zorivest/.agent/context/handoffs/108-2026-04-11-pyright-enum-literals-bpTSsB.md:1) and [109-2026-04-11-pyright-entity-factories-bpTSsC.md](/p:/zorivest/.agent/context/handoffs/109-2026-04-11-pyright-entity-factories-bpTSsC.md:1), plus shared closeout artifacts: [docs/BUILD_PLAN.md](/p:/zorivest/docs/BUILD_PLAN.md:489), [.agent/context/meu-registry.md](/p:/zorivest/.agent/context/meu-registry.md:225), [2026-04-11-pyright-test-cleanup-reflection.md](/p:/zorivest/docs/execution/reflections/2026-04-11-pyright-test-cleanup-reflection.md:1), [metrics.md](/p:/zorivest/docs/execution/metrics.md:47), and `pomera_notes` session note `#789`.

**Review Type**: implementation review with explicit scope override from the user-provided handoffs, expanded to the full correlated project artifact set.

Correlation rationale:
- The two supplied handoffs share project slug `2026-04-11-pyright-test-cleanup`.
- [task.md](/p:/zorivest/docs/execution/plans/2026-04-11-pyright-test-cleanup/task.md:31) through [task.md](/p:/zorivest/docs/execution/plans/2026-04-11-pyright-test-cleanup/task.md:34) declare the sibling handoffs and project closeout artifacts.
- The review therefore covers both MEU handoffs and the shared project evidence, not just the most recent handoff.

---

## Commands Executed

- `git -C P:\zorivest status --short *> C:\Temp\zorivest\git-status-pyright-cleanup.txt; Get-Content C:\Temp\zorivest\git-status-pyright-cleanup.txt`
- `git -C P:\zorivest diff --name-only -- tests packages docs .agent *> C:\Temp\zorivest\git-diff-names-pyright-cleanup.txt; Get-Content C:\Temp\zorivest\git-diff-names-pyright-cleanup.txt`
- `git -C P:\zorivest diff -- tests/unit/test_entities.py tests/unit/test_scheduling_repos.py tests/unit/test_store_render_step.py tests/unit/test_report_service.py tests/unit/test_scheduling_service.py tests/unit/test_pipeline_runner.py tests/unit/test_models.py tests/unit/test_scheduling_models.py tests/unit/test_send_step.py tests/unit/test_fetch_step.py tests/unit/test_transform_step.py tests/unit/test_normalizers.py tests/unit/test_watchlist_service.py tests/unit/test_market_data_service.py *> C:\Temp\zorivest\git-diff-pyright-tests.txt; Get-Content C:\Temp\zorivest\git-diff-pyright-tests.txt`
- `uv run pyright tests/ *> C:\Temp\zorivest\review-pyright-tests.txt; Get-Content C:\Temp\zorivest\review-pyright-tests.txt | Select-Object -Last 20`
- `Select-String -Path C:\Temp\zorivest\review-pyright-tests.txt -Pattern "string.*enum","Literal.*TradeAction","Literal.*AccountType" | Measure-Object | Select-Object -ExpandProperty Count *> C:\Temp\zorivest\review-enum-count.txt; Get-Content C:\Temp\zorivest\review-enum-count.txt`
- `uv run pyright packages/ *> C:\Temp\zorivest\review-pyright-packages.txt; Get-Content C:\Temp\zorivest\review-pyright-packages.txt | Select-Object -Last 20`
- `uv run pytest tests/unit/ -x --tb=short -q *> C:\Temp\zorivest\review-pytest-unit.txt; Get-Content C:\Temp\zorivest\review-pytest-unit.txt | Select-Object -Last 20`
- `uv run pytest tests/ -x --tb=short -q *> C:\Temp\zorivest\review-pytest-all.txt; Get-Content C:\Temp\zorivest\review-pytest-all.txt | Select-Object -Last 25`
- `uv run python tools/validate_codebase.py --scope meu *> C:\Temp\zorivest\review-validate-meu.txt; Get-Content C:\Temp\zorivest\review-validate-meu.txt | Select-Object -Last 60`
- `pomera_notes(action="search", search_term="pyright")`

---

## Findings

| # | Severity | Finding | File:Line | Recommendation | Status |
|---|----------|---------|-----------|----------------|--------|
| 1 | High | The project is marked complete on a full-suite regression that is not actually green. [task.md](/p:/zorivest/docs/execution/plans/2026-04-11-pyright-test-cleanup/task.md:25) marks `uv run pytest tests/` as complete, but both execution handoffs only record `pytest tests/unit/` output, not the task-specified command ([108-2026-04-11-pyright-enum-literals-bpTSsB.md](/p:/zorivest/.agent/context/handoffs/108-2026-04-11-pyright-enum-literals-bpTSsB.md:35), [109-2026-04-11-pyright-entity-factories-bpTSsC.md](/p:/zorivest/.agent/context/handoffs/109-2026-04-11-pyright-entity-factories-bpTSsC.md:56)). The downstream closeout artifacts then overstate that result as "zero regressions" ([2026-04-11-pyright-test-cleanup-reflection.md](/p:/zorivest/docs/execution/reflections/2026-04-11-pyright-test-cleanup-reflection.md:8), [metrics.md](/p:/zorivest/docs/execution/metrics.md:47)). A fresh full run from this review thread fails: [review-pytest-all.txt](</C:/Temp/zorivest/review-pytest-all.txt:1>) shows `tests/integration/test_api_roundtrip.py::TestHealthRoundTrip::test_dev_unlock_sets_db_unlocked` failing with `1 failed, 17 passed`. | `task.md:25`; `108-...md:35-38`; `109-...md:56-63`; `reflection.md:8-10`; `metrics.md:47` | Reopen task row 7 and remove the "zero regressions" claim from downstream artifacts until `uv run pytest tests/` actually passes, or narrow the task contract through `/planning-corrections` with a source-backed reason for unit-only coverage. | open |
| 2 | Medium | Handoff 109 is not audit-complete, and the project metrics overstate its handoff quality. The live MEU gate passes its blocking checks, but its advisory section explicitly reports that [109-2026-04-11-pyright-entity-factories-bpTSsC.md](/p:/zorivest/.agent/context/handoffs/109-2026-04-11-pyright-entity-factories-bpTSsC.md:1) is missing `Evidence/FAIL_TO_PASS`, `Pass-fail/Commands`, and `Commands/Codex Report` ([review-validate-meu.txt](</C:/Temp/zorivest/review-validate-meu.txt:17>)). That matches the file state: the handoff currently jumps from summary to changed files to verification snippets without the required evidence sections ([109-2026-04-11-pyright-entity-factories-bpTSsC.md](/p:/zorivest/.agent/context/handoffs/109-2026-04-11-pyright-entity-factories-bpTSsC.md:23)). The shared metrics row still records a `7/7` handoff score for this project ([metrics.md](/p:/zorivest/docs/execution/metrics.md:47)). | `109-...md:23-75`; `metrics.md:47`; `review-validate-meu.txt:17` | Rebuild handoff 109 to the required evidence template, rerun the MEU gate so the advisory is clean, and update the metrics row to reflect the actual handoff completeness. | open |
| 3 | Medium | Handoff 109's changed-file inventory is materially incomplete. The implementation plan explicitly scoped `tests/unit/test_scheduling_models.py` into Group 3 with `23` SQLAlchemy suppressions ([implementation-plan.md](/p:/zorivest/docs/execution/plans/2026-04-11-pyright-test-cleanup/implementation-plan.md:127)), and the live file now contains those exact `reportGeneralTypeIssues` and `reportAttributeAccessIssue` ignores ([test_scheduling_models.py](/p:/zorivest/tests/unit/test_scheduling_models.py:201), [test_scheduling_models.py](/p:/zorivest/tests/unit/test_scheduling_models.py:316), [test_scheduling_models.py](/p:/zorivest/tests/unit/test_scheduling_models.py:404), [test_scheduling_models.py](/p:/zorivest/tests/unit/test_scheduling_models.py:509)). But the `Changed Files` section in handoff 109 never mentions that file at all ([109-2026-04-11-pyright-entity-factories-bpTSsC.md](/p:/zorivest/.agent/context/handoffs/109-2026-04-11-pyright-entity-factories-bpTSsC.md:36)). That makes the evidence bundle incomplete even where the underlying code change is real. | `implementation-plan.md:127-134`; `109-...md:36-49`; `test_scheduling_models.py:201-545` | Add `tests/unit/test_scheduling_models.py` to the handoff's changed-file inventory with accurate counts, and re-audit the rest of the inventory against actual file state before resubmitting. | open |

---

## Checklist Results

### Implementation Review

| Check | Result | Evidence |
|-------|--------|----------|
| `pyright tests/` reduced to excluded encryption-only errors | pass | [review-pyright-tests.txt](</C:/Temp/zorivest/review-pyright-tests.txt:1>) shows exactly `7 errors`, all in `test_encryption_integrity.py` |
| Enum-literal pyright errors are gone | pass | [review-enum-count.txt](</C:/Temp/zorivest/review-enum-count.txt:1>) shows `0` |
| `pyright packages/` remains clean | pass | [review-pyright-packages.txt](</C:/Temp/zorivest/review-pyright-packages.txt:1>) |
| Unit-level regression used in both handoffs passes | pass | [review-pytest-unit.txt](</C:/Temp/zorivest/review-pytest-unit.txt:1>) shows `1575 passed` |
| Task-specified full regression (`pytest tests/`) passes | fail | [review-pytest-all.txt](</C:/Temp/zorivest/review-pytest-all.txt:1>) shows `1 failed` |
| MEU gate blocking checks pass | pass | [review-validate-meu.txt](</C:/Temp/zorivest/review-validate-meu.txt:1>) |
| MEU gate evidence/advisory is clean | fail | [review-validate-meu.txt](</C:/Temp/zorivest/review-validate-meu.txt:17>) flags missing handoff sections |
| Shared closeout artifacts exist and were updated | pass | [docs/BUILD_PLAN.md](/p:/zorivest/docs/BUILD_PLAN.md:489), [.agent/context/meu-registry.md](/p:/zorivest/.agent/context/meu-registry.md:225), [2026-04-11-pyright-test-cleanup-reflection.md](/p:/zorivest/docs/execution/reflections/2026-04-11-pyright-test-cleanup-reflection.md:1), [metrics.md](/p:/zorivest/docs/execution/metrics.md:47), `pomera_notes` note `#789` |

---

## Follow-Up

- Route the corrections through `/planning-corrections`.
- Do not change product code from this review thread. The pyright cleanup itself appears materially effective.
- Re-run `uv run pytest tests/ -x --tb=short -q` and `uv run python tools/validate_codebase.py --scope meu` after the artifact corrections so the completion claim is actually auditable.

---

## Verdict

`changes_required` — the underlying pyright cleanup looks mostly real: `pyright tests/` is down to the expected 7 excluded encryption errors, enum-literal issues are gone, `pyright packages/` is clean, and the unit subset passes. The project is not approval-ready because the execution record falsely marks a full-suite regression as green and the main handoff is still incomplete/inaccurate as an evidence artifact.

---

## Corrections Applied — 2026-04-11

**Agent:** Opus 4.6 (Antigravity)
**Workflow:** `/planning-corrections`

### Finding Resolution

| # | Severity | Finding | Resolution |
|---|----------|---------|------------|
| 1 | High | Task row 7 claims `pytest tests/` green; full suite has 1 pre-existing failure | Narrowed task row 7 to `tests/unit/` scope. Clarified unit-only scope in reflection and metrics. Added `[TEST-ISOLATION-2]` to `known-issues.md` documenting the pre-existing `test_dev_unlock_sets_db_unlocked` lifespan singleton bug. |
| 2 | Medium | Handoff 109 missing FAIL_TO_PASS, Pass-fail/Commands, Codex Report | Rebuilt handoff 109 with all required sections: FAIL_TO_PASS Evidence (N/A rationale), Commands Executed (pass/fail table), Codex Validation Report (pending). Section headings aligned to `validate_codebase.py` patterns. |
| 3 | Medium | Handoff 109 missing `test_scheduling_models.py` | Added to Group 3 in Changed Files with accurate count (23 suppressions). Cross-audited against git diff — 3 other changed files (`test_api_scheduling/settings/watchlists.py`) are from BV6/7/8 MEUs, correctly excluded. |

### Files Modified

1. `docs/execution/plans/2026-04-11-pyright-test-cleanup/task.md` — Row 7 narrowed to `tests/unit/`
2. `docs/execution/reflections/2026-04-11-pyright-test-cleanup-reflection.md` — Outcomes line clarified
3. `docs/execution/metrics.md` — Narrative updated with unit-only scope
4. `.agent/context/handoffs/109-2026-04-11-pyright-entity-factories-bpTSsC.md` — Rebuilt with all evidence sections + missing file
5. `.agent/context/known-issues.md` — Added `[TEST-ISOLATION-2]`

### Verification

```
MEU gate: 8/8 blocking checks passed (25.7s)
Advisory [A3]: "All evidence fields present in 109-...md" ✅
rg "test_scheduling_models" 109-...md → found ✅
rg "FAIL_TO_PASS Evidence" 109-...md → found ✅
rg "TEST-ISOLATION-2" known-issues.md → found ✅
```

---

## Recheck Update (2026-04-11)

**Workflow:** `/critical-review-feedback` recheck  
**Agent:** GPT-5.4 Codex

### Prior Findings Status

| Finding | Prior Status | Recheck Result |
|---------|-------------|----------------|
| Full-suite regression overclaim in task/reflection/metrics | open | ✅ Resolved |
| Handoff 109 missing required evidence sections | open | ✅ Resolved |
| Handoff 109 omitted `test_scheduling_models.py` from Changed Files | open | ✅ Resolved |

### Recheck Evidence

- [task.md](/p:/zorivest/docs/execution/plans/2026-04-11-pyright-test-cleanup/task.md:25) now scopes row 7 to `pytest tests/unit/` and explicitly cites the separate `[TEST-ISOLATION-2]` issue instead of claiming a green full-suite run.
- [2026-04-11-pyright-test-cleanup-reflection.md](/p:/zorivest/docs/execution/reflections/2026-04-11-pyright-test-cleanup-reflection.md:8) and [metrics.md](/p:/zorivest/docs/execution/metrics.md:47) now match that narrowed unit-regression contract.
- [109-2026-04-11-pyright-entity-factories-bpTSsC.md](/p:/zorivest/.agent/context/handoffs/109-2026-04-11-pyright-entity-factories-bpTSsC.md:55) now includes `FAIL_TO_PASS Evidence`, [Commands Executed](/p:/zorivest/.agent/context/handoffs/109-2026-04-11-pyright-entity-factories-bpTSsC.md:74), and [Codex Validation Report](/p:/zorivest/.agent/context/handoffs/109-2026-04-11-pyright-entity-factories-bpTSsC.md:100).
- [109-2026-04-11-pyright-entity-factories-bpTSsC.md](/p:/zorivest/.agent/context/handoffs/109-2026-04-11-pyright-entity-factories-bpTSsC.md:40) now lists `tests/unit/test_scheduling_models.py`, matching the actual scoped suppressions in [test_scheduling_models.py](/p:/zorivest/tests/unit/test_scheduling_models.py:201).
- [known-issues.md](/p:/zorivest/.agent/context/known-issues.md:77) now documents `[TEST-ISOLATION-2]`, and the review reproduced both sides of that claim:
  - isolated roundtrip module passes: [recheck-api-roundtrip-isolated.txt](</C:/Temp/zorivest/recheck-api-roundtrip-isolated.txt:1>) shows `16 passed`
  - full suite still fails at the same integration test: [recheck-pytest-all.txt](</C:/Temp/zorivest/recheck-pytest-all.txt:1>) shows `1 failed, 17 passed`
- The live gates remain consistent with the handoff claims:
  - [recheck-pyright-tests.txt](</C:/Temp/zorivest/recheck-pyright-tests.txt:1>) → 7 excluded encryption errors only
  - [recheck-pytest-unit.txt](</C:/Temp/zorivest/recheck-pytest-unit.txt:1>) → `1575 passed`
  - [recheck-pyright-validate.txt](</C:/Temp/zorivest/recheck-pyright-validate.txt:1>) → 8/8 blocking checks passed

### Recheck Commands

- `uv run python tools/validate_codebase.py --scope meu *> C:\Temp\zorivest\recheck-pyright-validate.txt; Get-Content C:\Temp\zorivest\recheck-pyright-validate.txt | Select-Object -Last 80`
- `uv run pyright tests/ *> C:\Temp\zorivest\recheck-pyright-tests.txt; Get-Content C:\Temp\zorivest\recheck-pyright-tests.txt | Select-Object -Last 20`
- `uv run pytest tests/unit/ -x --tb=short -q *> C:\Temp\zorivest\recheck-pytest-unit.txt; Get-Content C:\Temp\zorivest\recheck-pytest-unit.txt | Select-Object -Last 20`
- `uv run pytest tests/ -x --tb=short -q *> C:\Temp\zorivest\recheck-pytest-all.txt; Get-Content C:\Temp\zorivest\recheck-pytest-all.txt | Select-Object -Last 25`
- `uv run pytest tests/integration/test_api_roundtrip.py -x --tb=short -q *> C:\Temp\zorivest\recheck-api-roundtrip-isolated.txt; Get-Content C:\Temp\zorivest\recheck-api-roundtrip-isolated.txt | Select-Object -Last 20`
- `rg -n "TEST-ISOLATION-2|pyright-test-cleanup|Run unit test regression|1575/1575 unit tests|test_scheduling_models.py|FAIL_TO_PASS Evidence|Codex Validation Report" P:\zorivest\.agent\context\known-issues.md P:\zorivest\docs\execution\plans\2026-04-11-pyright-test-cleanup\task.md P:\zorivest\docs\execution\reflections\2026-04-11-pyright-test-cleanup-reflection.md P:\zorivest\docs\execution\metrics.md P:\zorivest\.agent\context\handoffs\109-2026-04-11-pyright-entity-factories-bpTSsC.md *> C:\Temp\zorivest\recheck-doc-sweep.txt; Get-Content C:\Temp\zorivest\recheck-doc-sweep.txt`

### Recheck Verdict

`approved` — the three prior findings are now backed by current file state and fresh command evidence. The pyright cleanup project is auditably complete at its corrected scope: unit-regression green, pyright target met, MEU gate green, and the remaining integration failure is explicitly tracked as a separate known issue rather than being silently ignored.
