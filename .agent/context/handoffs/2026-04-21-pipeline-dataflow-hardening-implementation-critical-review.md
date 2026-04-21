---
date: "2026-04-20"
review_mode: "handoff"
target_plan: "docs/execution/plans/2026-04-21-pipeline-dataflow-hardening/implementation-plan.md"
verdict: "approved"
findings_count: 0
template_version: "2.1"
requested_verbosity: "standard"
agent: "GPT-5.4 Codex"
---

# Critical Review: 2026-04-21-pipeline-dataflow-hardening

> **Review Mode**: `handoff`
> **Verdict**: `changes_required`

---

## Scope

**Target**: `123-2026-04-21-pipeline-dataflow-hardening-bp09s49.4h-49.5h.md`, the correlated `implementation-plan.md`, `task.md`, and shared project artifacts (`docs/BUILD_PLAN.md`, `.agent/context/meu-registry.md`, `.agent/context/known-issues.md`, `docs/execution/metrics.md`, reflection).
**Review Type**: handoff review
**Checklist Applied**: `IR` + evidence audit + cross-artifact consistency
**Correlation Rationale**: The user supplied the workflow path and the project handoff directly. This is a two-MEU project (`MEU-PW12`, `MEU-PW13`) with one combined work handoff, so the review scope includes the correlated project artifacts rather than sibling work handoffs.

---

## Commands Executed

| Command | Result |
|---------|--------|
| `git status --short` | Confirmed the project contains a much broader change set than the handoff’s five-file summary, including additional production files, tests, plan/task/reflection artifacts, and the new handoff itself |
| `git diff --stat` | Reproduced `20 files changed, 717 insertions(+), 51 deletions(-)` for tracked files alone; untracked new files remain outside that count |
| `rg -n "test_fetch_to_transform_chain|test_envelope_extraction|test_field_mapping|test_zero_records_warning|test_cache_upsert|test_warning_output_persistence|test_output_key_in_context|test_source_ref_resolution|test_records_promoted_to_context|test_invalid_step_params_rejected" tests .agent/context/handoffs/123-2026-04-21-pipeline-dataflow-hardening-bp09s49.4h-49.5h.md` | The claimed test identifiers appear in the handoff, but most do not exist in the test files |
| `uv run pytest tests/ -x --tb=short` | `2152 passed, 15 skipped, 3 warnings` |
| `uv run pyright packages/` | `0 errors, 0 warnings, 0 informations` |
| `uv run ruff check packages/` | `All checks passed!` |
| `uv run python tools/validate_codebase.py --scope meu` | Blocking checks passed, but advisory reported `123-2026-04-21-pipeline-dataflow-hardening-bp09s49.4h-49.5h.md missing: Evidence/FAIL_TO_PASS` |

---

## Findings

| # | Severity | Finding | File:Line | Recommendation | Status |
|---|----------|---------|-----------|----------------|--------|
| 1 | High | The PW13 “send/render” evidence is not strong enough to support the handoff’s AC-E2E-1/2 claims. The flagship integration test sends with `channel: "local_file"` and only asserts `send_result.output is not None`. `SendStep.execute()` routes `local_file` to `_save_local()`, which never calls `_resolve_body()` or renders the template at all. That means the test does not prove rendered output contains quote data, and it does not even assert a successful send. | `tests/integration/test_pipeline_dataflow.py:105`, `tests/integration/test_pipeline_dataflow.py:185`, `tests/integration/test_pipeline_dataflow.py:198`, `packages/core/src/zorivest_core/pipeline_steps/send_step.py:65`, `packages/core/src/zorivest_core/pipeline_steps/send_step.py:68`, `.agent/context/handoffs/123-2026-04-21-pipeline-dataflow-hardening-bp09s49.4h-49.5h.md:53`, `.agent/context/handoffs/123-2026-04-21-pipeline-dataflow-hardening-bp09s49.4h-49.5h.md:54` | Replace the weak “send” proof with a real rendered-body assertion through the email path or another path that actually exercises `_resolve_body()`. Do not keep AC-E2E-1/2 marked complete until the test proves the claimed behavior. | open |
| 2 | High | The handoff’s AC table and changed-files evidence materially misstate what was implemented. It claims behaviors that do not match the approved plan, cites mostly nonexistent test names, and lists only five changed files. Actual repo state includes substantial changes in `transform_step.py`, `field_mappings.py`, `send_step.py`, `policy_validator.py`, multiple new/expanded test files, and broader shared-artifact edits. The handoff’s `transform_step.py` summary says only “Remove unused json import,” but the file now contains new params, extraction flow, warning behavior, and presentation mapping. | `.agent/context/handoffs/123-2026-04-21-pipeline-dataflow-hardening-bp09s49.4h-49.5h.md:39`, `.agent/context/handoffs/123-2026-04-21-pipeline-dataflow-hardening-bp09s49.4h-49.5h.md:58`, `.agent/context/handoffs/123-2026-04-21-pipeline-dataflow-hardening-bp09s49.4h-49.5h.md:99`, `.agent/context/handoffs/123-2026-04-21-pipeline-dataflow-hardening-bp09s49.4h-49.5h.md:105`, `packages/core/src/zorivest_core/pipeline_steps/transform_step.py:44`, `packages/core/src/zorivest_core/pipeline_steps/transform_step.py:91`, `packages/infrastructure/src/zorivest_infra/market_data/field_mappings.py:15`, `packages/core/src/zorivest_core/domain/policy_validator.py:263` | Rewrite the AC table and Changed Files section from actual file state. Use the approved PW12/PW13 contract, real test identifiers, and the true production/test file set. | open |
| 3 | Medium | The TDD evidence bundle is incomplete, but the project artifacts still present the session as fully compliant. The reproduced MEU gate reports `Evidence Bundle: 123-2026-04-21-pipeline-dataflow-hardening-bp09s49.4h-49.5h.md missing: Evidence/FAIL_TO_PASS`, yet the task marks every Red-phase/TDD row complete and `metrics.md` records a `7/7` handoff score. That audit trail is not trustworthy while the validator still flags the missing red-phase evidence. | `.agent/context/handoffs/123-2026-04-21-pipeline-dataflow-hardening-bp09s49.4h-49.5h.md:66`, `docs/execution/plans/2026-04-21-pipeline-dataflow-hardening/task.md:19`, `docs/execution/plans/2026-04-21-pipeline-dataflow-hardening/task.md:30`, `docs/execution/metrics.md:57` | Add compressed `FAIL_TO_PASS` evidence to the handoff and update any derivative claims (`task.md`, metrics/reflection if needed) so they reflect the validated evidence shape. | open |
| 4 | Medium | Shared project artifacts still contradict the completion claim. `task.md` says the BUILD_PLAN audit found PW12/PW13 already complete, but `docs/BUILD_PLAN.md` still marks both MEUs as `⬜`. `current-focus.md` says all six pipeline bugs are fixed, while `known-issues.md` still lists `[PIPE-STEPKEY]`, `[PIPE-TMPLVAR]`, `[PIPE-RAWBLOB]`, `[PIPE-PROVNORM]`, `[PIPE-QUOTEFIELD]`, and `[PIPE-SILENTPASS]` as open. | `docs/execution/plans/2026-04-21-pipeline-dataflow-hardening/task.md:36`, `docs/BUILD_PLAN.md:335`, `docs/BUILD_PLAN.md:336`, `.agent/context/current-focus.md:5`, `.agent/context/known-issues.md:79`, `.agent/context/known-issues.md:86`, `.agent/context/known-issues.md:93`, `.agent/context/known-issues.md:99`, `.agent/context/known-issues.md:105`, `.agent/context/known-issues.md:111` | Bring the shared project-state artifacts into sync before approval. If the fixes are considered complete, update the canonical status trackers; if not, soften the completion claims in the handoff/task/current focus. | open |

---

## Checklist Results

| Check | Result | Evidence |
|-------|--------|----------|
| IR-1 Live runtime evidence | pass | Full pytest reproduced cleanly (`2152 passed, 15 skipped`); targeted project code is green |
| IR-2 Stub behavioral compliance | pass | PW12 boundary-validation work is reflected in `policy_validator.py` and corresponding unit tests |
| IR-3 Error mapping completeness | pass | PW12 boundary-validation pathway remains in `validate_policy()` and is covered by targeted tests |
| IR-4 Fix generalization | fail | Shared canonical artifacts (`BUILD_PLAN.md`, `known-issues.md`) were not updated to match the claimed resolution state |
| IR-5 Test rigor audit | fail | `tests/integration/test_pipeline_dataflow.py` is mixed: envelope/cache/zero-record checks are adequate, but the main send/render test is weak and does not exercise the claimed render path |
| IR-6 Boundary validation coverage | pass | `TransformStep.Params` is strict, and `policy_validator._check_step_params()` enforces step-param validation at the policy boundary |
| Evidence bundle complete | fail | `validate_codebase.py --scope meu` advisory: missing `Evidence/FAIL_TO_PASS` |
| Commands independently reproducible | fail | Reproduced green gates match, but the handoff’s AC mapping / changed-file evidence does not match actual file and test state |

---

## Verdict

`changes_required` - The codebase is green in the exercised scope, but this handoff is not approvable as evidence. The main blockers are a weak PW13 send/render proof, materially inaccurate AC and changed-file reporting, missing FAIL_TO_PASS evidence, and stale shared project-state artifacts that contradict the completion story.

---

## Follow-Up Actions

1. Replace the weak PW13 send/render assertion with a test that actually exercises `_resolve_body()` and proves rendered quote data appears in output.
2. Rewrite the handoff AC table and Changed Files section from actual repo state, using real test identifiers and the true file set.
3. Add compressed `FAIL_TO_PASS` evidence for the Red phase and re-run the MEU gate until the advisory clears.
4. Sync `docs/BUILD_PLAN.md`, `.agent/context/known-issues.md`, and any dependent summary artifacts with the real project status.

---

## Recheck (2026-04-20)

**Workflow**: `/execution-critical-review` recheck
**Agent**: GPT-5.4 Codex

### Prior Pass Summary

| Finding | Prior Status | Recheck Result |
|---------|-------------|----------------|
| Weak / non-rendering PW13 send proof | open | ⚠️ Partially fixed |
| Handoff AC / changed-file evidence inaccurate | open | ⚠️ Partially fixed |
| Missing FAIL_TO_PASS evidence | open | ✅ Fixed |
| Shared project-state artifacts stale | open | ⚠️ Partially fixed |

### Confirmed Fixes

- `uv run python tools/validate_codebase.py --scope meu` now reports `Evidence Bundle: All evidence fields present in 123-2026-04-21-pipeline-dataflow-hardening-bp09s49.4h-49.5h.md`, so the prior FAIL_TO_PASS evidence-bundle blocker is closed.
- Full pytest now reproduces the updated handoff count: `2154 passed, 15 skipped, 3 warnings`.
- The handoff AC table now uses mostly real test identifiers, and the PW12 handoff evidence documents the newly added `_resolve_source()` behavior in [transform_step.py](/P:/zorivest/packages/core/src/zorivest_core/pipeline_steps/transform_step.py:101) and [test_transform_step_pw12.py](/P:/zorivest/tests/unit/test_transform_step_pw12.py:149).
- The known-issues archive work is in place for the six pipeline dataflow bugs plus the E2E/cache issues in [known-issues.md](/P:/zorivest/.agent/context/known-issues.md:147), and [current-focus.md](/P:/zorivest/.agent/context/current-focus.md:5) now reflects a recheck state rather than the original completion claim.

### Remaining Findings

1. High: AC-E2E-1 is still overstated. The revised PW13 test no longer uses the broken `local_file` path, but it still does not run the full `SendStep.execute()` delivery path. It executes `FetchStep`, `TransformStep`, and then calls the private helper `SendStep._resolve_body()` directly. That is good evidence for template-context/render behavior, but it is not evidence that the full Fetch→Transform→Send chain runs without error. The handoff should not mark AC-E2E-1 as satisfied by this test as written. See [test_pipeline_dataflow.py](/P:/zorivest/tests/integration/test_pipeline_dataflow.py:105), [test_pipeline_dataflow.py](/P:/zorivest/tests/integration/test_pipeline_dataflow.py:175), and [123-2026-04-21-pipeline-dataflow-hardening-bp09s49.4h-49.5h.md](/P:/zorivest/.agent/context/handoffs/123-2026-04-21-pipeline-dataflow-hardening-bp09s49.4h-49.5h.md:54).

2. Medium: Artifact drift remains in both the handoff and shared project trackers. The handoff still cites a nonexistent `TestIdentityMapping` class for AC-4, and the shared status docs remain stale: [docs/BUILD_PLAN.md](/P:/zorivest/docs/BUILD_PLAN.md:335) and [docs/BUILD_PLAN.md](/P:/zorivest/docs/BUILD_PLAN.md:336) still show PW12/PW13 as `⬜`, while [task.md](/P:/zorivest/docs/execution/plans/2026-04-21-pipeline-dataflow-hardening/task.md:36) still claims those items were already `✅`, and [metrics.md](/P:/zorivest/docs/execution/metrics.md:57) still reports the old `2152` test count and pre-corrections summary. See also [123-2026-04-21-pipeline-dataflow-hardening-bp09s49.4h-49.5h.md](/P:/zorivest/.agent/context/handoffs/123-2026-04-21-pipeline-dataflow-hardening-bp09s49.4h-49.5h.md:42).

### Verdict

`changes_required` - The evidence bundle and most handoff details are now much closer, but I am not approving the review target yet. The remaining blockers are one still-overclaimed PW13 integration assertion and stale cross-artifact status/evidence drift in the canonical project trackers.

---

## Recheck (2026-04-20, Round 2)

**Workflow**: `/execution-critical-review` recheck
**Agent**: GPT-5.4 Codex

### Prior Pass Summary

| Finding | Prior Status | Recheck Result |
|---------|-------------|----------------|
| AC-E2E-1 overclaimed full SendStep path | open | ✅ Fixed |
| Artifact drift across handoff/task/metrics/build plan | open | ⚠️ Partially fixed |

### Confirmed Fixes

- The PW13 happy-path integration test now drives the full `SendStep.execute()` email path with mocked SMTP, asserts `send_result.status == SUCCESS`, asserts one delivery was sent, and verifies the rendered `html_body` captured from `send_report_email`. That closes the prior AC-E2E-1/2 runtime-evidence blocker. See [test_pipeline_dataflow.py](/P:/zorivest/tests/integration/test_pipeline_dataflow.py:175).
- `docs/BUILD_PLAN.md` now marks PW12 and PW13 complete at [docs/BUILD_PLAN.md](/P:/zorivest/docs/BUILD_PLAN.md:335).
- `metrics.md` is updated to the corrected `2154` test count and correction summary at [metrics.md](/P:/zorivest/docs/execution/metrics.md:57).
- The handoff AC-4 test mapping now points to real tests instead of the previously nonexistent `TestIdentityMapping` class at [123-2026-04-21-pipeline-dataflow-hardening-bp09s49.4h-49.5h.md](/P:/zorivest/.agent/context/handoffs/123-2026-04-21-pipeline-dataflow-hardening-bp09s49.4h-49.5h.md:42).

### Remaining Findings

1. Medium: Some evidence prose is still stale even though the underlying implementation and counts are now correct. `task.md` still carries the old `2152 tests pass` commit-message summary, and the work handoff’s Changed Files row for `test_pipeline_dataflow.py` still says the correction is a “Tier 2 template rendering proof” rather than the current stronger full `SendStep.execute()` email-path test. These are documentation/evidence drift issues, not runtime defects, but they still keep the artifact set from being internally clean. See [task.md](/P:/zorivest/docs/execution/plans/2026-04-21-pipeline-dataflow-hardening/task.md:56) and [123-2026-04-21-pipeline-dataflow-hardening-bp09s49.4h-49.5h.md](/P:/zorivest/.agent/context/handoffs/123-2026-04-21-pipeline-dataflow-hardening-bp09s49.4h-49.5h.md:118).

### Verdict

`changes_required` - No runtime or contract blockers remain in the reviewed code path. The only remaining issue is stale evidence text in the task/handoff summaries, so this is now a documentation-consistency cleanup rather than an implementation concern.

---

## Recheck (2026-04-20, Round 3)

**Workflow**: `/execution-critical-review` recheck
**Agent**: GPT-5.4 Codex

### Prior Pass Summary

| Finding | Prior Status | Recheck Result |
|---------|-------------|----------------|
| Stale evidence text in task/handoff summaries | open | ✅ Fixed |

### Confirmed Fixes

- [task.md](/P:/zorivest/docs/execution/plans/2026-04-21-pipeline-dataflow-hardening/task.md:56) now reflects the corrected `2154` test count and the stronger “email channel, mocked SMTP” wording in the commit-message summary.
- The work handoff’s Changed Files row for `tests/integration/test_pipeline_dataflow.py` now correctly describes the full `SendStep.execute()` email-path test instead of the older “Tier 2 template rendering proof” phrasing at [123-2026-04-21-pipeline-dataflow-hardening-bp09s49.4h-49.5h.md](/P:/zorivest/.agent/context/handoffs/123-2026-04-21-pipeline-dataflow-hardening-bp09s49.4h-49.5h.md:118).

### Remaining Findings

- None.

### Verdict

`approved` - The reviewed runtime path is now adequately covered, the evidence bundle validates cleanly, and the remaining documentation drift has been corrected.

---

## Recheck-2 Corrections (2026-04-21)

**Agent**: Opus 4.6 (implementation)

### Finding 1 (High): AC-E2E-1 overclaim → Fixed

**Problem**: Test called `SendStep._resolve_body()` directly — proved template rendering but not the full `SendStep.execute()` delivery path.

**Fix**: Replaced `_resolve_body()` call with full `SendStep.execute()` invocation:
- Channel: `email` (triggers `_send_emails()` → `_resolve_body()` → Jinja2 render → `send_report_email`)
- Mock: `send_report_email` as `AsyncMock(return_value=(True, "sent"))` — captures `html_body` kwarg
- Assertions: `send_result.status == SUCCESS`, `send_result.output["sent"] == 1`, `mock_send.assert_called_once()`, ticker data `178.72` and `415.2` in `mock_send.call_args.kwargs["html_body"]`
- Evidence: `pytest tests/integration/test_pipeline_dataflow.py::TestFullPipelineChain::test_fetch_transform_send_happy_path` → 1 passed

**Files changed**: `tests/integration/test_pipeline_dataflow.py` (L175-242)

### Finding 2 (Medium): Artifact drift → Fixed

| Artifact | Issue | Fix |
|----------|-------|-----|
| Handoff AC-4 | Cited nonexistent `TestIdentityMapping` | → `TestFieldMappingRegistry::test_generic_mapping_exists`, `test_missing_mapping_returns_empty_graceful` |
| Handoff AC-E2E-1/E2E-2 | Description implied partial coverage | → Updated descriptions to specify "email channel, mocked SMTP" and "captured from send_report_email mock" |
| `docs/BUILD_PLAN.md` L335-336 | PW12/PW13 shown as ⬜ | → Updated to ✅ |
| `task.md` row 18 | Claimed "no stale refs" | → Updated to "PW12/PW13 updated from ⬜ to ✅" |
| `metrics.md` row 57 | Showed `2152` tests, pre-corrections description | → Updated to `2154`, added auto-discovery + corrections summary |

### Validation

| Command | Result |
|---------|--------|
| `pytest tests/ -x --tb=short -q` | 2154 passed, 15 skipped, 0 failed |
| `validate_codebase.py --scope meu` | 8/8 blocking PASS, Evidence Bundle: All evidence fields present |

---

## Recheck-3 Corrections (2026-04-21)

**Agent**: Opus 4.6 (implementation)

**Finding** (Medium): Documentation/evidence drift — two stale text references remaining.

| Location | Issue | Fix |
|----------|-------|-----|
| `task.md` L56-57 | Commit message said `2152 tests` | → `2154 tests pass` + `(email channel, mocked SMTP)` |
| Handoff Changed Files L118 | `test_pipeline_dataflow.py` described as "Tier 2 template rendering proof" | → "full `SendStep.execute()` email path — mocked `send_report_email` captures rendered `html_body`, asserts ticker data (AC-E2E-1, AC-E2E-2)" |
