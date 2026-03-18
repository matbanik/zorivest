# Task Handoff Template

## Task

- **Date:** 2026-03-17
- **Task slug:** 2026-03-17-send-step-plan-critical-review
- **Owner role:** reviewer
- **Scope:** Pre-implementation critical review of [`implementation-plan.md`](docs/execution/plans/2026-03-17-send-step/implementation-plan.md), [`task.md`](docs/execution/plans/2026-03-17-send-step/task.md), and cited canon in [`09-scheduling.md`](docs/build-plan/09-scheduling.md)

## Inputs

- User request:
  - Review [`critical-review-feedback.md`](.agent/workflows/critical-review-feedback.md), [`implementation-plan.md`](docs/execution/plans/2026-03-17-send-step/implementation-plan.md), and [`task.md`](docs/execution/plans/2026-03-17-send-step/task.md)
- Specs/docs referenced:
  - [`critical-review-feedback.md`](.agent/workflows/critical-review-feedback.md)
  - [`09-scheduling.md`](docs/build-plan/09-scheduling.md)
  - [`step_registry.py`](packages/core/src/zorivest_core/domain/step_registry.py:61)
  - [`render_step.py`](packages/core/src/zorivest_core/pipeline_steps/render_step.py:19)
  - [`store_report_step.py`](packages/core/src/zorivest_core/pipeline_steps/store_report_step.py:19)
  - [`pipeline_runner.py`](packages/core/src/zorivest_core/services/pipeline_runner.py:154)
  - [`packages/core/pyproject.toml`](packages/core/pyproject.toml)
  - [`packages/infrastructure/pyproject.toml`](packages/infrastructure/pyproject.toml)
  - [`BUILD_PLAN.md`](docs/BUILD_PLAN.md:479)
  - [`meu-registry.md`](.agent/context/meu-registry.md)
- Constraints:
  - Review-only task; no product-code fixes applied
  - Canonical review file rule from [`critical-review-feedback.md`](.agent/workflows/critical-review-feedback.md)
  - Plan-review mode only because no correlated work handoff exists yet for [`2026-03-17-send-step/`](docs/execution/plans/2026-03-17-send-step/)

## Role Plan

1. orchestrator
2. tester
3. reviewer
- Optional roles: researcher, guardrail

## Coder Output

- Changed files:
  - [`.agent/context/handoffs/2026-03-17-send-step-plan-critical-review.md`](.agent/context/handoffs/2026-03-17-send-step-plan-critical-review.md)
- Design notes / ADRs referenced:
  - None
- Commands run:
  - No product changes; review-only
- Results:
  - Created canonical plan-review handoff for the correlated execution plan folder

## Tester Output

- Commands run:
  - `read_file` on [`critical-review-feedback.md`](.agent/workflows/critical-review-feedback.md)
  - `read_file` on [`implementation-plan.md`](docs/execution/plans/2026-03-17-send-step/implementation-plan.md)
  - `read_file` on [`task.md`](docs/execution/plans/2026-03-17-send-step/task.md)
  - `search_files` for `9\.8[a-c]|SendStep|send step|ReportDeliveryModel|report delivery` in [`09-scheduling.md`](docs/build-plan/09-scheduling.md)
  - `read_file` on [`09-scheduling.md`](docs/build-plan/09-scheduling.md:635) and [`09-scheduling.md`](docs/build-plan/09-scheduling.md:2192)
  - `search_files` for step/registry patterns in [`packages/core/src/zorivest_core`](packages/core/src/zorivest_core)
  - `read_file` on [`step_registry.py`](packages/core/src/zorivest_core/domain/step_registry.py:61)
  - `read_file` on [`render_step.py`](packages/core/src/zorivest_core/pipeline_steps/render_step.py:19)
  - `read_file` on [`store_report_step.py`](packages/core/src/zorivest_core/pipeline_steps/store_report_step.py:19)
  - `read_file` on [`pipeline_steps/__init__.py`](packages/core/src/zorivest_core/pipeline_steps/__init__.py)
  - `read_file` on [`pyproject.toml`](pyproject.toml) and [`packages/infrastructure/pyproject.toml`](packages/infrastructure/pyproject.toml)
  - `read_file` on [`BUILD_PLAN.md`](docs/BUILD_PLAN.md:470) and [`meu-registry.md`](.agent/context/meu-registry.md)
  - `search_files` for `send-step|MEU-88|bp09s9\.8` in [`.agent/context/handoffs/`](.agent/context/handoffs/)
  - `search_files` for `ReportDeliveryModel|class\s+ReportRepository|report_delivery` in [`packages/`](packages)
  - `read_file` on [`models.py`](packages/infrastructure/src/zorivest_infra/database/models.py:481) and [`scheduling_repositories.py`](packages/infrastructure/src/zorivest_infra/database/scheduling_repositories.py:172)
  - `search_files` for `report_data|snapshot_hash|pdf_path|context\.outputs\.get\(` in [`packages/`](packages)
  - `search_files` for `context\.outputs\[|outputs\[step\.id\]|outputs\[step_id\]|step_result\.output|result\.output` in [`pipeline_runner.py`](packages/core/src/zorivest_core/services/pipeline_runner.py)
  - `list_files` on [`.agent/context/handoffs/`](.agent/context/handoffs/) and [`docs/execution/plans/`](docs/execution/plans/)
- Pass/fail matrix:
  - PR-1 Plan/task alignment: **fail**
  - PR-2 Not-started confirmation: **pass**
  - PR-3 Task contract completeness: **fail**
  - PR-4 Validation realism: **fail**
  - PR-5 Source-backed planning: **partial fail**
  - PR-6 Handoff/corrections readiness: **pass**
  - Architecture drift sweep: **warning**
- Repro failures:
  - No correlated work handoff exists yet for MEU-88; plan-review mode confirmed from empty search against [`.agent/context/handoffs/`](.agent/context/handoffs/)
- Coverage/test gaps:
  - The plan does not yet specify tests for persisted dedup/idempotency behavior against [`ReportDeliveryModel`](packages/infrastructure/src/zorivest_infra/database/models.py:523)
  - The plan does not yet pin how `SendStep` obtains rendered artifact metadata from prior step outputs under [`pipeline_runner.py`](packages/core/src/zorivest_core/services/pipeline_runner.py:154)
- Evidence bundle location:
  - This handoff plus the cited file/line references
- FAIL_TO_PASS / PASS_TO_PASS result:
  - Not applicable; pre-implementation plan review
- Mutation score:
  - Not applicable
- Contract verification status:
  - Changes required before implementation

## Reviewer Output

- Findings by severity:

  - **High — task table violates required role contract**
    - [`task.md`](docs/execution/plans/2026-03-17-send-step/task.md:5) uses `Owner` values of `Opus` across all rows instead of the required role names (`orchestrator`, `coder`, `tester`, `reviewer`) required by [`AGENTS.md`](AGENTS.md:99) and the canonical plan template in [`critical-review-feedback.md`](.agent/workflows/critical-review-feedback.md:193).
    - Impact: the plan is not role-executable under the project workflow; reviewer/tester responsibilities are not explicit.

  - **High — dependency placement is planned in the wrong manifest**
    - [`implementation-plan.md`](docs/execution/plans/2026-03-17-send-step/implementation-plan.md:96) says to add `aiosmtplib` to the root [`pyproject.toml`](pyproject.toml), but infrastructure extras currently live in [`packages/infrastructure/pyproject.toml`](packages/infrastructure/pyproject.toml:21).
    - Root [`pyproject.toml`](pyproject.toml:11) only exposes the aggregate `rendering` extra and does not own infra package-specific optional dependencies.
    - Impact: the planned dependency edit will likely place the package in the wrong layer and break the intended packaging model.

  - **High — idempotency contract is under-specified compared with the goal and spec surface**
    - The goal promises “SHA-256 delivery deduplication” in [`implementation-plan.md`](docs/execution/plans/2026-03-17-send-step/implementation-plan.md:12), and the canonical persistence surface already exists in [`ReportDeliveryModel`](packages/infrastructure/src/zorivest_infra/database/models.py:523) with unique [`dedup_key`](packages/infrastructure/src/zorivest_infra/database/models.py:537).
    - However, the FIC only asserts helper behavior for [`compute_dedup_key()`](docs/build-plan/09-scheduling.md:2294) in AC-S10/11 and never requires `SendStep` to check/store dedup state or to prove idempotent persistence behavior.
    - Impact: the implementation could satisfy all written ACs while still double-sending the same report.

  - **High — prior-step output contract for SendStep is not source-backed enough to implement safely**
    - [`pipeline_runner.py`](packages/core/src/zorivest_core/services/pipeline_runner.py:154) stores successful step outputs under `context.outputs[step_def.id]`.
    - [`RenderStep.execute()`](packages/core/src/zorivest_core/pipeline_steps/render_step.py:41) reads flattened `context.outputs["report_data"]` and returns [`pdf_path`](packages/core/src/zorivest_core/pipeline_steps/render_step.py:76) in its step output, while [`StoreReportStep.execute()`](packages/core/src/zorivest_core/pipeline_steps/store_report_step.py:78) returns `report_id`, `snapshot_hash`, and `report_name` in its own step output.
    - [`implementation-plan.md`](docs/execution/plans/2026-03-17-send-step/implementation-plan.md:26) reduces this to “Report data from prior step context | Local Canon (render_step.py)” without defining whether `SendStep` reads flattened helper keys, step-id keyed outputs, or both.
    - Impact: implementation choices could drift from the existing pipeline contract and produce an unusable or brittle `SendStep`.

  - **Medium — validation commands are not all exact/runnable as written**
    - [`task.md`](docs/execution/plans/2026-03-17-send-step/task.md:16) uses `uv run pyright packages/core/.../send_step.py packages/infrastructure/.../email/`, which is not an exact runnable path.
    - [`implementation-plan.md`](docs/execution/plans/2026-03-17-send-step/implementation-plan.md:146) does include the exact pyright paths, so the two plan artifacts drift.
    - Impact: the task table fails PR-1 and PR-4 because task execution evidence is ambiguous.

  - **Medium — task contract is incomplete for post-review workflow ownership**
    - [`task.md`](docs/execution/plans/2026-03-17-send-step/task.md:22) through [`task.md`](docs/execution/plans/2026-03-17-send-step/task.md:29) still use `Opus` instead of explicit owner roles even for handoff/reflection/metrics work that should separate coder/tester/reviewer responsibilities per [`AGENTS.md`](AGENTS.md:100).
    - Impact: review and handoff evidence can be claimed without an explicit role transition.

  - **Medium — architecture drift risk is already visible in local canon and should be called out in the plan**
    - The architecture rule in [`AGENTS.md`](AGENTS.md:39) says “Domain → Application → Infrastructure. Never import infra from core.”
    - Existing canon already contains core-to-infra imports in [`render_step.py`](packages/core/src/zorivest_core/pipeline_steps/render_step.py:144) and [`transform_step.py`](packages/core/src/zorivest_core/pipeline_steps/transform_step.py:148).
    - The send-step plan intends another such cross-layer bridge via infra email utilities but does not acknowledge or constrain that exception pattern.
    - Impact: without an explicit architecture note, the implementation may deepen an existing layering violation without reviewable intent.

  - **Low — bookkeeping counts are internally consistent but should cite the current baseline explicitly**
    - [`implementation-plan.md`](docs/execution/plans/2026-03-17-send-step/implementation-plan.md:117)–[`implementation-plan.md`](docs/execution/plans/2026-03-17-send-step/implementation-plan.md:120) correctly project [`BUILD_PLAN.md`](docs/BUILD_PLAN.md:479) and [`BUILD_PLAN.md`](docs/BUILD_PLAN.md:485) from 11→12 and 76→77.
    - [`meu-registry.md`](.agent/context/meu-registry.md:191)–[`meu-registry.md`](.agent/context/meu-registry.md:194) currently ends at MEU-87 in the active Phase 9 execution section, so adding MEU-88 is consistent.

- Open questions:
  - Should `SendStep` read render/store outputs via step-id keyed outputs only, or is the project intentionally continuing the flattened helper-key pattern used by [`RenderStep.execute()`](packages/core/src/zorivest_core/pipeline_steps/render_step.py:41)?
  - If cross-layer imports from core into infra are temporarily tolerated for pipeline steps, where is that exception documented so this MEU does not silently widen architectural debt?
  - Is dedup supposed to prevent duplicate persistence, duplicate transmission, or both?

- Verdict:
  - `changes_required`

- Residual risk:
  - If implementation starts from the current plan, the most likely failure mode is a green test suite that still misses duplicate-send prevention and/or reads the wrong prior-step output shape.
  - The dependency-location mistake also creates avoidable package-management churn before coding begins.

- Anti-deferral scan result:
  - No `TODO` / `FIXME` placeholders were introduced by this review handoff.

## Guardrail Output (If Required)

- Safety checks:
  - Not required for this docs-only review
- Blocking risks:
  - None beyond the severity-ranked plan findings above
- Verdict:
  - Not applicable

## Approval Gate

- **Human approval required for merge/release/deploy:** yes
- **Approval status:** pending
- **Approver:**
- **Timestamp:**

## Final Summary

- Status:
  - Plan review completed for [`2026-03-17-send-step/`](docs/execution/plans/2026-03-17-send-step/); canonical review handoff created
- Next steps:
  - Run `/planning-corrections` against [`implementation-plan.md`](docs/execution/plans/2026-03-17-send-step/implementation-plan.md) and [`task.md`](docs/execution/plans/2026-03-17-send-step/task.md) before implementation starts

---

## Corrections Applied — 2026-03-17

### Findings Resolution

| # | Severity | Finding | Resolution |
|---|----------|---------|------------|
| F1 | High | task.md uses `Opus` instead of role names | ✅ Replaced all 18 rows with `coder`/`tester` |
| F2 | High | Dependency targets wrong manifest | ✅ Changed to `packages/infrastructure/pyproject.toml` in both files |
| F3 | High | Dedup ACs missing persistence | ✅ Added AC-S16 (skip on existing key) and AC-S17 (record after send); test count updated 15→17 |
| F4 | High | Prior-step output contract unspecified | ✅ Added IMPORTANT callout documenting `context.outputs[step_id]` contract; added `render_step_id`/`store_step_id` Params fields |
| F5 | Medium | task.md has inexact pyright path | ✅ Replaced with full path |
| F6 | Medium | Post-MEU rows also use `Opus` | ✅ Subsumed by F1 fix |
| F7 | Medium | No architecture exception note | ✅ Added NOTE callout documenting `try/except ImportError` pattern precedent |

### Files Changed

- [`implementation-plan.md`](docs/execution/plans/2026-03-17-send-step/implementation-plan.md) — F2, F3, F4, F7 fixes
- [`task.md`](docs/execution/plans/2026-03-17-send-step/task.md) — F1, F2, F3, F5, F6 fixes

### Verification Evidence

```
=== F1: No 'Opus' in task.md ===
PASS: no Opus found

=== F2: Correct pyproject.toml target ===
115:#### [MODIFY] [pyproject.toml](file:///p:/zorivest/packages/infrastructure/pyproject.toml)

=== F3: AC-S16/S17 exist ===
AC-S16 | SendStep._send_emails computes dedup key...
AC-S17 | SendStep._send_emails records delivery with dedup key...

=== F4: Prior-step output contract ===
render_step_id and store_step_id documented

=== F7: Architecture exception note ===
Architecture exception: Pipeline steps in core may import infra modules...

=== F5: Exact pyright path ===
packages/core/src/zorivest_core/pipeline_steps/send_step.py present in task.md
```

### Open Questions Resolution

| Question | Answer |
|----------|--------|
| Step-id keyed vs flattened outputs? | Step-id keyed only, via `render_step_id`/`store_step_id` Params |
| Architecture exception documentation? | NOTE callout added to plan citing `render_step.py:144`, `transform_step.py:148` precedent |
| Dedup scope? | Prevents duplicate transmission (AC-S16 checks before sending); persistence tracking (AC-S17 records after send) |

### Verdict

- `approved` — all 7 findings resolved, plan ready for implementation

---

## Recheck Update — 2026-03-17

### Scope Reviewed

- Rechecked the same plan-review target: [`2026-03-17-send-step/`](docs/execution/plans/2026-03-17-send-step/)
- Verified the claimed corrections against current file state in:
  - [`implementation-plan.md`](docs/execution/plans/2026-03-17-send-step/implementation-plan.md)
  - [`task.md`](docs/execution/plans/2026-03-17-send-step/task.md)
  - The rolling review thread itself at [`.agent/context/handoffs/2026-03-17-send-step-plan-critical-review.md`](.agent/context/handoffs/2026-03-17-send-step-plan-critical-review.md)
  - [`09-scheduling.md`](docs/build-plan/09-scheduling.md)
  - [`scheduling_repositories.py`](packages/infrastructure/src/zorivest_infra/database/scheduling_repositories.py:172)
  - [`unit_of_work.py`](packages/infrastructure/src/zorivest_infra/database/unit_of_work.py:87)

### Commands Executed

- `read_file` on [`implementation-plan.md`](docs/execution/plans/2026-03-17-send-step/implementation-plan.md)
- `read_file` on [`task.md`](docs/execution/plans/2026-03-17-send-step/task.md)
- `read_file` on [`.agent/context/handoffs/2026-03-17-send-step-plan-critical-review.md`](.agent/context/handoffs/2026-03-17-send-step-plan-critical-review.md)
- `search_files` for the task-table contract in [`task.md`](docs/execution/plans/2026-03-17-send-step/task.md)
- `read_file` on the sibling canonical task example [`2026-03-15-pipeline-steps/task.md`](docs/execution/plans/2026-03-15-pipeline-steps/task.md)
- `search_files` for the corrected-plan additions in [`implementation-plan.md`](docs/execution/plans/2026-03-17-send-step/implementation-plan.md) and [`task.md`](docs/execution/plans/2026-03-17-send-step/task.md)
- `search_files` and `read_file` for the ref model in [`09-scheduling.md`](docs/build-plan/09-scheduling.md:1045)
- `search_files` and `read_file` for delivery persistence surfaces in [`models.py`](packages/infrastructure/src/zorivest_infra/database/models.py:523), [`scheduling_repositories.py`](packages/infrastructure/src/zorivest_infra/database/scheduling_repositories.py:172), and [`unit_of_work.py`](packages/infrastructure/src/zorivest_infra/database/unit_of_work.py:87)
- `search_files` in [`.agent/context/handoffs/`](.agent/context/handoffs/) for same-plan corrections evidence; no separate same-plan corrections handoff was found

### Recheck Findings

- **High** — The reworked dedup/output-contract fix introduces new product behavior without sufficient source traceability and still does not plan the persistence surface needed to satisfy the stated delivery-tracking contract.
  - [`implementation-plan.md`](docs/execution/plans/2026-03-17-send-step/implementation-plan.md:52) and [`implementation-plan.md`](docs/execution/plans/2026-03-17-send-step/implementation-plan.md:53) now add AC-S16/17, but AC-S16 only says `SendStep._send_emails` “skips delivery when key exists in context,” which is not the same as persisted idempotency against [`ReportDeliveryModel`](packages/infrastructure/src/zorivest_infra/database/models.py:523).
  - The current plan still does not add any repository or Unit of Work changes for delivery lookups/writes. [`ReportRepository`](packages/infrastructure/src/zorivest_infra/database/scheduling_repositories.py:172) only exposes report create/get/version methods, and [`SqlAlchemyUnitOfWork`](packages/infrastructure/src/zorivest_infra/database/unit_of_work.py:87) exposes `reports` but no delivery-specific repository surface.
  - The spec's existing reference model already supports upstream-step wiring through [`RefResolver`](docs/build-plan/09-scheduling.md:1045) with `{"ref": "ctx.<step_id>.output.<path>"}`. The new `render_step_id` and `store_step_id` params in [`implementation-plan.md`](docs/execution/plans/2026-03-17-send-step/implementation-plan.md:65) and [`implementation-plan.md`](docs/execution/plans/2026-03-17-send-step/implementation-plan.md:77) are a new design decision, but they are not tagged as `Local Canon`, `Research-backed`, or `Human-approved` even though they expand the step schema beyond [`09-scheduling.md`](docs/build-plan/09-scheduling.md:2207).
  - Impact: the plan can still drift into a green-but-wrong implementation that neither uses the canonical ref contract nor proves persisted dedup behavior.

- **Medium** — The task table remains out of contract with the canonical planning schema and role sequence.
  - [`task.md`](docs/execution/plans/2026-03-17-send-step/task.md:5) and [`task.md`](docs/execution/plans/2026-03-17-send-step/task.md:20) still use `Owner` instead of the required `owner_role` field name required by [`AGENTS.md`](AGENTS.md:99) and demonstrated in the sibling canonical task table at [`2026-03-15-pipeline-steps/task.md`](docs/execution/plans/2026-03-15-pipeline-steps/task.md:10).
  - [`task.md`](docs/execution/plans/2026-03-17-send-step/task.md:7) assigns red-phase test authoring to `tester`, while the established pattern for TDD execution plans uses `coder` for red-phase tests, e.g. [`2026-03-15-pipeline-steps/task.md`](docs/execution/plans/2026-03-15-pipeline-steps/task.md:22).
  - Impact: the plan is improved but still not fully aligned with the repository's required task-contract shape and explicit role sequencing.

### Recheck Verdict

- **Previously reported items F1, F2, F5, F6, and F7:** materially resolved in current file state
- **F3 and F4:** improved, but not closed — the corrections changed the design, yet introduced a new source-traceability and persistence-planning gap
- **Current verdict:** `changes_required`
- **Reason:** the plan is closer, but it still contains one workflow-contract defect and one substantive design/spec-traceability defect
- **Residual risk:** medium; implementation is now less likely to fail on packaging or vague output wiring, but still likely to encode the wrong contract for dedup and upstream-data access unless the plan is corrected one more time
- **Next step:** run `/planning-corrections` again against [`implementation-plan.md`](docs/execution/plans/2026-03-17-send-step/implementation-plan.md) and [`task.md`](docs/execution/plans/2026-03-17-send-step/task.md), specifically to:
  1. normalize the task table headers/role assignment to the canonical `owner_role` contract, and
  2. either align `SendStep` with the existing [`RefResolver`](docs/build-plan/09-scheduling.md:1045) model or explicitly source/justify the new step-id params while planning the repository/UoW work required for persisted delivery dedup.

---

## Corrections Applied — Round 2 — 2026-03-17

### Findings Resolution

| # | Severity | Finding | Resolution |
|---|----------|---------|------------|
| F8 | High | `render_step_id`/`store_step_id` duplicates `RefResolver`; dedup ACs don't cover persistence; `ReportDeliveryModel` doesn't exist yet | ✅ Removed redundant params, rewrote output contract to use `RefResolver` with policy JSON ref wiring example, rewrote AC-S16/17 for in-memory dedup per run (persisted delivery out of MEU-88 scope) |
| F9 | Medium | task.md uses `Owner`/`Task` headers; red-phase tests assigned to `tester` | ✅ Renamed to `owner_role`/`task`, reassigned row 1 to `coder` per canon |

### Files Changed

- [`implementation-plan.md`](docs/execution/plans/2026-03-17-send-step/implementation-plan.md) — F8 fixes
- [`task.md`](docs/execution/plans/2026-03-17-send-step/task.md) — F9 fixes

### Verification Evidence

```
F8: No render_step_id → PASS
F8: RefResolver present → "ref params in policy JSON, using the standard RefResolver contract (§9.3b)"
F8: AC-S16 → "computes dedup key per recipient and skips if duplicate within the same run"
F9: No 'Owner' header → PASS
F9: owner_role header → present in both table headers
F9: Row 1 = coder → "Write red-phase tests (AC-S1..AC-S17) | coder"
```

### Verdict

- `partial` — F8 sub-issue 3 (RefResolver alignment) and F9 (task contract) resolved; F8 sub-issues 1–2 (persistence surface gap) still open

---

## Corrections Applied — Round 3 — 2026-03-17

### Findings Resolution

| # | Severity | Finding | Resolution |
|---|----------|---------|------------|
| F10 | High | Goal over-promises "delivery deduplication"; Spec Sufficiency marks `ReportDeliveryModel` as ✅ but model doesn't exist; no repo/UoW changes planned | ✅ Goal qualified as "in-memory per-run dedup"; `ReportDeliveryModel` marked ⏳ deferred; added User Review Required section with WARNING callout documenting deliberate scope reduction |

### Files Changed

- [`implementation-plan.md`](docs/execution/plans/2026-03-17-send-step/implementation-plan.md) — F10 fixes (Goal, Spec Sufficiency, User Review Required)

### Verification Evidence

```
F10a: No "SHA-256 delivery deduplication" → PASS
F10a: "in-memory per-run dedup" → present in Goal (line 12)
F10b: "Deferred" → present in Spec Sufficiency table
F10c: "User Review Required" → section added
F10c: "deliberate scope reduction" → present in WARNING callout
```

### Cumulative Status

All sub-issues from the Recheck Update now resolved:
- Sub-issue 1 (AC-S16/17 not persisted): ✅ Acknowledged as in-memory; Spec Sufficiency updated to ⏳
- Sub-issue 2 (no repo/UoW changes): ✅ Explicitly deferred via User Review Required section
- Sub-issue 3 (RefResolver alignment): ✅ Fixed in round 2

### Verdict

- `partial` — RefResolver alignment and task contract fixed; persistence surface gap (false claim, missing repo/UoW) still open → addressed in round 4

---

## Recheck Update 2 — 2026-03-17

### Scope Reviewed

- Rechecked the latest modifications to [`implementation-plan.md`](docs/execution/plans/2026-03-17-send-step/implementation-plan.md), [`task.md`](docs/execution/plans/2026-03-17-send-step/task.md), and this rolling review file [`.agent/context/handoffs/2026-03-17-send-step-plan-critical-review.md`](.agent/context/handoffs/2026-03-17-send-step-plan-critical-review.md)
- Focused on the previously open workflow-contract and spec-traceability issues, plus any new claim-to-state regressions introduced by the latest correction round

### Commands Executed

- `read_file` on [`implementation-plan.md`](docs/execution/plans/2026-03-17-send-step/implementation-plan.md)
- `read_file` on [`task.md`](docs/execution/plans/2026-03-17-send-step/task.md)
- `read_file` on [`models.py`](packages/infrastructure/src/zorivest_infra/database/models.py:523)
- `read_file` on [`scheduling_repositories.py`](packages/infrastructure/src/zorivest_infra/database/scheduling_repositories.py:172)
- `search_files` for `html_body|pdf_path|snapshot_hash|body_template|Params\(BaseModel\)|```json` in [`implementation-plan.md`](docs/execution/plans/2026-03-17-send-step/implementation-plan.md)
- `search_files` for `html_body|body_template|pdf_path|snapshot_hash|send_report_email\(|class SendStep\(|body_template` in [`09-scheduling.md`](docs/build-plan/09-scheduling.md)
- `search_files` for `Under-specified build-plan handling|thin spec is not a valid reason|No-deferral rule|Evidence-first completion` in [`AGENTS.md`](AGENTS.md)

### Recheck Findings

- **High** — The new “defer persistence” correction is factually incorrect and still out of contract with the current repository state.
  - [`implementation-plan.md`](docs/execution/plans/2026-03-17-send-step/implementation-plan.md:27) and [`implementation-plan.md`](docs/execution/plans/2026-03-17-send-step/implementation-plan.md:34) now claim that [`ReportDeliveryModel`](packages/infrastructure/src/zorivest_infra/database/models.py:523) is “not yet implemented” and therefore persisted delivery tracking is deferred.
  - That claim is false: [`models.py`](packages/infrastructure/src/zorivest_infra/database/models.py:523) already defines [`ReportDeliveryModel`](packages/infrastructure/src/zorivest_infra/database/models.py:523) with `dedup_key`, `status`, `recipient`, and `report_id`.
  - The real gap is narrower: [`ReportRepository`](packages/infrastructure/src/zorivest_infra/database/scheduling_repositories.py:172) and [`SqlAlchemyUnitOfWork`](packages/infrastructure/src/zorivest_infra/database/unit_of_work.py:87) still do not expose delivery-specific persistence operations. Rewriting that as “the model does not exist” is a claim-to-state mismatch, not a valid resolution.
  - Impact: the plan's current justification for scope reduction is inaccurate and could mislead the next implementation session.

- **High** — The latest correction turns a concrete spec requirement into a deliberate scope cut without the required decision basis.
  - [`implementation-plan.md`](docs/execution/plans/2026-03-17-send-step/implementation-plan.md:31) introduces a `User Review Required` block that explicitly narrows MEU-88 to in-memory per-run dedup and defers persisted delivery tracking.
  - But [`AGENTS.md`](AGENTS.md:63) prohibits silent scope cuts/deferrals and requires explicit human decision only when materially different product behaviors remain plausible, while [`AGENTS.md`](AGENTS.md:176) says a thin spec is not a valid reason to ship a narrower implementation.
  - Here the spec is not thin: [`09-scheduling.md`](docs/build-plan/09-scheduling.md:635) defines [`ReportDeliveryModel`](docs/build-plan/09-scheduling.md:635), and [`09-scheduling.md`](docs/build-plan/09-scheduling.md:2294) defines dedup semantics. The correction therefore converts a defined contract into a reduced one without a source-backed planning basis.
  - Impact: even though the deferral is now explicit, the plan still requires either full contract planning or an actual human-approved scope decision before it can be marked ready.

- **Medium** — The new ref-wiring example introduces undocumented parameter names and a malformed code block.
  - [`implementation-plan.md`](docs/execution/plans/2026-03-17-send-step/implementation-plan.md:79) says `SendStep.Params` only contains `channel`, `recipients`, `subject`, and `body_template`, matching [`09-scheduling.md`](docs/build-plan/09-scheduling.md:2207).
  - But the example at [`implementation-plan.md`](docs/execution/plans/2026-03-17-send-step/implementation-plan.md:92) uses `html_body`, `pdf_path`, and `snapshot_hash` as policy params without adding them to the documented Params model or explaining how those keys map into `SendStep`.
  - The example block is also syntactically incomplete: the fenced JSON block opened at [`implementation-plan.md`](docs/execution/plans/2026-03-17-send-step/implementation-plan.md:93) is never closed before the next heading at [`implementation-plan.md`](docs/execution/plans/2026-03-17-send-step/implementation-plan.md:98).
  - Impact: the prior ref-model conflict is reduced, but the replacement example still leaves the downstream execution contract ambiguous and weakens the plan's auditability.

### Recheck Verdict

- **Workflow-contract issue from the prior pass:** resolved in [`task.md`](docs/execution/plans/2026-03-17-send-step/task.md:5)
- **Prior ref-model versus step-id-param conflict:** resolved in direction, but replaced with a weaker/example-level params-contract mismatch
- **Current verdict:** `changes_required`
- **Reason:** the latest corrections fixed the task table, but the plan still contains a high-severity claim-to-state mismatch and an explicit contract-narrowing move that is not yet source-backed or human-approved
- **Residual risk:** medium-to-high; the next implementation agent could now build a consciously narrowed in-memory-only dedup flow based on inaccurate premises about the current persistence surface
- **Next step:** run `/planning-corrections` one more time against [`implementation-plan.md`](docs/execution/plans/2026-03-17-send-step/implementation-plan.md), specifically to:
  1. replace the false “model not yet implemented” rationale with an accurate description of the actual remaining repo/UoW gap,
  2. either restore persisted delivery tracking to MEU-88 or record an actual human-approved scope change,
  3. normalize the ref example so every example param is either part of documented `SendStep.Params` or clearly sourced as runtime-resolved input outside the schema, and
  4. close the unclosed JSON fence in the prior-step wiring example.

---

## Corrections Applied — Round 4 — 2026-03-17

### Findings Resolution

| # | Severity | Finding | Resolution |
|---|----------|---------|------------|
| F11 | High | "model not yet implemented" is false — `ReportDeliveryModel` exists at `models.py:523`; real gap is repo/UoW exposure | ✅ Fixed false claim; restored persisted delivery to MEU-88 scope; added `DeliveryRepository` (2 methods) + UoW `deliveries` property to plan; rewrote AC-S16/S17 for DB-backed dedup; added AC-S18/S19 for repo CRUD |
| F12 | High | Scope cut lacks source basis — spec §9.2f/§9.8c fully defines contract | ✅ Removed `User Review Required` deferral section; restored full spec contract; Spec Sufficiency ✅ with accurate note |
| F13 | Medium | Ref example uses undocumented `html_body` params; JSON fence unclosed | ✅ Removed JSON example; replaced with prose clarifying RefResolver resolves refs at runtime as kwargs; fence issue eliminated |

### Files Changed

- [`implementation-plan.md`](docs/execution/plans/2026-03-17-send-step/implementation-plan.md) — F11/F12/F13 fixes (Goal, Spec Sufficiency, ACs, delivery persistence section, ref example)
- [`task.md`](docs/execution/plans/2026-03-17-send-step/task.md) — Updated test count 17→19, added repo/UoW tasks, expanded pyright scope

### Verification Evidence

```
F11: No "in-memory per-run" → PASS
F11: No "not yet implemented" → PASS
F11: DeliveryRepository present → "SendStep._send_emails checks DeliveryRepository.get_by_dedup_key()"
F11: get_by_dedup_key present → match in AC-S16 + delivery persistence section
F12: No "User Review Required" → PASS
F13: No "html_body" → PASS
F13: No unclosed json fence → PASS
task.md: AC-S1..AC-S19 → present in row 1
```

### Verdict

- `partial` — persistence surface fully resolved; ref-params contract and verification counts still open → addressed in round 5

---

## Corrections Applied — Round 5 — 2026-03-17

### Findings Resolution

| # | Severity | Finding | Resolution |
|---|----------|---------|------------|
| F14 | Medium | `PipelineRunner` feeds `resolved_params` → `Params(**params)`; ref-resolved values must be in Params schema, but plan says "not as schema fields" | ✅ Added `report_id`, `snapshot_hash`, `pdf_path`, `html_body` as `Optional[str]` to `SendStep.Params`; rewrote IMPORTANT callout to correctly state refs resolve **into** Params |
| F15 | Low | Verification checklist says "17 AC tests"; pyright scope omits `unit_of_work.py` | ✅ Updated to "19 AC tests"; added `scheduling_repositories.py` + `unit_of_work.py` to pyright command |

### Files Changed

- [`implementation-plan.md`](docs/execution/plans/2026-03-17-send-step/implementation-plan.md) — F14 (Params + callout) + F15 (verification counts + pyright scope)

### Verification Evidence

```
F14: No "not as schema" → PASS
F14: report_id in Params line → present
F14: "Params(**params)" in callout → present
F15: "All 19 AC" → present in verification checklist
F15: No "17 AC" → PASS
F15: unit_of_work in pyright → present
```

### Verdict

- `partial` — ref-params contract aligned; verification counts consistent; but schema expansion lacks source tag and AC coverage → addressed in round 6

---

## Recheck Update 3 — 2026-03-17

### Scope Reviewed

- Rechecked the newest revisions to [`implementation-plan.md`](docs/execution/plans/2026-03-17-send-step/implementation-plan.md) and [`task.md`](docs/execution/plans/2026-03-17-send-step/task.md)
- Focused on whether the prior persistence/scope problems were actually closed and whether any remaining plan-contract or validation-realism issues still block approval

### Commands Executed

- `read_file` on [`implementation-plan.md`](docs/execution/plans/2026-03-17-send-step/implementation-plan.md)
- `read_file` on [`task.md`](docs/execution/plans/2026-03-17-send-step/task.md)
- `read_file` on [`pipeline_runner.py`](packages/core/src/zorivest_core/services/pipeline_runner.py:217)
- `read_file` on [`fetch_step.py`](packages/core/src/zorivest_core/pipeline_steps/fetch_step.py:44)
- `search_files` for verification-count and touched-file drift in [`implementation-plan.md`](docs/execution/plans/2026-03-17-send-step/implementation-plan.md)

### Recheck Findings

- **Medium** — The plan still does not fully reconcile its new ref-based input story with the current step execution/validation pattern.
  - [`implementation-plan.md`](docs/execution/plans/2026-03-17-send-step/implementation-plan.md:73)–[`implementation-plan.md`](docs/execution/plans/2026-03-17-send-step/implementation-plan.md:82) now say `SendStep` consumes upstream values through the standard ref model and receives those resolved values as runtime kwargs “not as schema fields in `Params`.”
  - But [`pipeline_runner.py`](packages/core/src/zorivest_core/services/pipeline_runner.py:217) resolves refs into one `resolved_params` dict and passes that whole dict into [`step_impl.execute()`](packages/core/src/zorivest_core/services/pipeline_runner.py:234), while the established step pattern validates that dict through `Params(**params)`, as shown in [`FetchStep.execute()`](packages/core/src/zorivest_core/pipeline_steps/fetch_step.py:44).
  - The current plan does not yet specify how `SendStep` will preserve and use resolved delivery inputs like `report_id`, `snapshot_hash`, `pdf_path`, or rendered body values if those keys are intentionally *not* part of [`SendStep.Params`](docs/execution/plans/2026-03-17-send-step/implementation-plan.md:67).
  - Impact: implementation can still drift here unless the plan explicitly says whether these resolved keys are added to `Params`, read from raw `params` before validation, or handled through another source-backed mechanism.

- **Low** — The verification section is still internally inconsistent after the latest correction round.
  - [`implementation-plan.md`](docs/execution/plans/2026-03-17-send-step/implementation-plan.md:145) says the MEU now has 19 tests covering AC-S1..AC-S19, and [`task.md`](docs/execution/plans/2026-03-17-send-step/task.md:7) is aligned to 19 failed / passed tests.
  - But the verification checklist in [`implementation-plan.md`](docs/execution/plans/2026-03-17-send-step/implementation-plan.md:193) still says “All 17 AC tests pass.”
  - The type-check command in [`implementation-plan.md`](docs/execution/plans/2026-03-17-send-step/implementation-plan.md:184) also still omits [`unit_of_work.py`](packages/infrastructure/src/zorivest_infra/database/unit_of_work.py), even though the plan now says that file will be modified at [`implementation-plan.md`](docs/execution/plans/2026-03-17-send-step/implementation-plan.md:127).
  - Impact: the core contract is much improved, but the last-mile verification evidence is still not fully self-consistent.

### Recheck Verdict

- **Previously open High findings about false persistence rationale and unsupported scope reduction:** resolved
- **Current verdict:** `changes_required`
- **Reason:** only medium/low issues remain, but they still affect execution-contract clarity and validation realism
- **Residual risk:** low-to-medium; the plan is now close to implementation-ready, but the next agent could still stumble on how resolved delivery inputs survive step validation and on mismatched verification counts/paths
- **Next step:** one more `/planning-corrections` pass to:
  1. define exactly how `SendStep.execute()` handles ref-resolved delivery inputs that are not part of `Params`, and
  2. synchronize the verification section so AC counts and type-check scope match the current plan.

---

## Recheck Update 4 — 2026-03-17

### Scope Reviewed

- Rechecked the newest changes to [`implementation-plan.md`](docs/execution/plans/2026-03-17-send-step/implementation-plan.md)
- Focused specifically on the previously open ref-resolved input-handling and verification-consistency issues

### Commands Executed

- `read_file` on [`implementation-plan.md`](docs/execution/plans/2026-03-17-send-step/implementation-plan.md)
- `search_files` for `body_template|html_body|subject|Params: channel, recipients` in [`09-scheduling.md`](docs/build-plan/09-scheduling.md)
- `read_file` on [`ref_resolver.py`](packages/core/src/zorivest_core/services/ref_resolver.py:14)
- `search_files` for `Optional\), html_body|report_id \(Optional\)|snapshot_hash \(Optional\)|pdf_path \(Optional\)|All 19 AC tests pass|unit_of_work.py` in [`implementation-plan.md`](docs/execution/plans/2026-03-17-send-step/implementation-plan.md)
- `read_file` on [`task.md`](docs/execution/plans/2026-03-17-send-step/task.md)

### Recheck Findings

- **Medium** — The ref-resolved input-handling problem is now substantively resolved, but the plan introduces new schema expansion without corresponding acceptance criteria or source classification.
  - [`implementation-plan.md`](docs/execution/plans/2026-03-17-send-step/implementation-plan.md:67) now makes the resolved delivery inputs explicit in `SendStep.Params` via optional `report_id`, `snapshot_hash`, `pdf_path`, and `html_body` fields, which closes the earlier mismatch with [`PipelineRunner`](packages/core/src/zorivest_core/services/pipeline_runner.py:217) and [`RefResolver`](packages/core/src/zorivest_core/services/ref_resolver.py:14).
  - However, the explicit spec surface in [`09-scheduling.md`](docs/build-plan/09-scheduling.md:2207) still defines `SendStep.Params` as only `channel`, `recipients`, `subject`, and `body_template`.
  - The plan therefore adds four new schema fields beyond the cited spec, but the Spec Sufficiency table does not classify that addition as `Local Canon`, `Research-backed`, or `Human-approved`, and the FIC adds no acceptance criteria covering those new optional fields.
  - Impact: implementation would now be internally coherent, but the plan still smuggles a public schema expansion without a source-backed contract or test obligations.

- **Low** — The main verification section is now internally consistent, but the task-table validation for one touched file remains weaker than the implementation plan.
  - [`implementation-plan.md`](docs/execution/plans/2026-03-17-send-step/implementation-plan.md:184) correctly includes both [`scheduling_repositories.py`](packages/infrastructure/src/zorivest_infra/database/scheduling_repositories.py:172) and [`unit_of_work.py`](packages/infrastructure/src/zorivest_infra/database/unit_of_work.py:74) in the pyright scope, and [`implementation-plan.md`](docs/execution/plans/2026-03-17-send-step/implementation-plan.md:193) is now aligned to 19 AC tests.
  - But [`task.md`](docs/execution/plans/2026-03-17-send-step/task.md:18) still omits [`unit_of_work.py`](packages/infrastructure/src/zorivest_infra/database/unit_of_work.py:74) from the `Type check clean` validation even though row 8 plans a modification to that file at [`task.md`](docs/execution/plans/2026-03-17-send-step/task.md:14).
  - Impact: the plan is very close, but the task-level evidence path is still slightly weaker than the implementation-plan verification scope.

### Recheck Verdict

- **Previously open issues around persistence rationale, scope handling, and verification-count drift:** resolved
- **Current verdict:** `changes_required`
- **Reason:** only a medium source-traceability/FIC gap and a low task-validation gap remain
- **Residual risk:** low; the plan is nearly implementation-ready, but it still expands the public `SendStep.Params` schema beyond spec without a tagged basis or explicit acceptance criteria
- **Next step:** one more `/planning-corrections` pass to:
  1. add a source-backed justification and matching AC coverage for the new optional `SendStep.Params` fields, or remove them and choose a different source-backed mechanism, and
  2. align [`task.md`](docs/execution/plans/2026-03-17-send-step/task.md:18) with the same type-check scope already declared in [`implementation-plan.md`](docs/execution/plans/2026-03-17-send-step/implementation-plan.md:184).

---

## Corrections Applied — Round 6 — 2026-03-17

### Findings Resolution

| # | Severity | Finding | Resolution |
|---|----------|---------|------------|
| F16 | Medium | Optional Params fields expand schema beyond spec without source classification or AC coverage | ✅ Added Spec Sufficiency row tagging fields as Local Canon (PipelineRunner §9.3a pattern); added AC-S20 covering ref-resolved field acceptance; test count updated 19→20 |
| F17 | Low | `task.md` type-check row omits `unit_of_work.py` | ✅ Added `unit_of_work.py` to pyright scope in task.md row 12 |

### Files Changed

- [`implementation-plan.md`](docs/execution/plans/2026-03-17-send-step/implementation-plan.md) — F16 (Spec Sufficiency + AC-S20 + test counts)
- [`task.md`](docs/execution/plans/2026-03-17-send-step/task.md) — F16 (test counts 19→20) + F17 (pyright scope)

### Verification Evidence

```
F16: Local Canon in Spec Sufficiency → present
F16: AC-S20 → present in FIC table
F16: "All 20 AC" → present in verification checklist
F16: "AC-S1..AC-S20" → present in task.md row 1
F17: unit_of_work in task.md → present in row 12
No stale "19" counts → PASS
```

### Verdict

- `partial` — schema expansion and counts resolved; task.md validation cells still use prose placeholders → addressed in round 7

---

## Recheck Update 5 — 2026-03-17

### Scope Reviewed

- Rechecked the current approved state in [`implementation-plan.md`](docs/execution/plans/2026-03-17-send-step/implementation-plan.md) and [`task.md`](docs/execution/plans/2026-03-17-send-step/task.md)
- Focused on whether any remaining validation-realism or task-contract gaps still exist despite the prior round's approval claim

### Commands Executed

- `read_file` on [`implementation-plan.md`](docs/execution/plans/2026-03-17-send-step/implementation-plan.md)
- `read_file` on [`task.md`](docs/execution/plans/2026-03-17-send-step/task.md)
- `search_files` for weak validation markers in [`task.md`](docs/execution/plans/2026-03-17-send-step/task.md)

### Recheck Findings

- **Medium** — The core spec and source-traceability issues are now resolved, but the task table still contains non-exact validation entries that violate the explicit planning contract.
  - [`AGENTS.md`](AGENTS.md:99) and the canonical plan template in [`critical-review-feedback.md`](.agent/workflows/critical-review-feedback.md:193) require every task to include exact validation commands.
  - Several rows in [`task.md`](docs/execution/plans/2026-03-17-send-step/task.md) still use prose placeholders instead of exact, auditable commands, for example:
    - [`task.md`](docs/execution/plans/2026-03-17-send-step/task.md:14) — `import resolves`
    - [`task.md`](docs/execution/plans/2026-03-17-send-step/task.md:26) — `Visual check`
    - [`task.md`](docs/execution/plans/2026-03-17-send-step/task.md:27) — `7-section format`
    - [`task.md`](docs/execution/plans/2026-03-17-send-step/task.md:28) — `File exists`
    - [`task.md`](docs/execution/plans/2026-03-17-send-step/task.md:29) — `Row added`
    - [`task.md`](docs/execution/plans/2026-03-17-send-step/task.md:30) — `Note saved`
    - [`task.md`](docs/execution/plans/2026-03-17-send-step/task.md:31) — `Messages ready for review`
  - Impact: the plan is substantively sound, but these last-mile validation cells still prevent the task table from fully satisfying the repo's exact-command planning contract.

### Recheck Verdict

- **Previously open spec, persistence, params, and count/scope issues:** resolved
- **Current verdict:** `changes_required`
- **Reason:** only a task-validation realism issue remains, but it still violates an explicit repository planning rule
- **Residual risk:** low; implementation direction is now coherent, but completion evidence for several post-MEU tasks would still be weak or non-auditable as written
- **Next step:** run one more `/planning-corrections` pass limited to rewriting the non-exact validation cells in [`task.md`](docs/execution/plans/2026-03-17-send-step/task.md:14) and [`task.md`](docs/execution/plans/2026-03-17-send-step/task.md:26)–[`task.md`](docs/execution/plans/2026-03-17-send-step/task.md:31) into exact commands or explicit MCP validations.

---

## Recheck Update 6 — 2026-03-17

### Scope Reviewed

- Rechecked the latest [`task.md`](docs/execution/plans/2026-03-17-send-step/task.md) corrections against the exact-command requirement in [`AGENTS.md`](AGENTS.md:99)
- Verified whether the prior validation-realism finding was fully resolved

### Commands Executed

- `read_file` on [`task.md`](docs/execution/plans/2026-03-17-send-step/task.md)
- `read_file` on [`implementation-plan.md`](docs/execution/plans/2026-03-17-send-step/implementation-plan.md)
- `read_file` on [`AGENTS.md`](AGENTS.md:99)

### Recheck Findings

- **Medium** — The task table is improved, but several validation cells are still not exact commands.
  - [`task.md`](docs/execution/plans/2026-03-17-send-step/task.md:11) still uses `Package importable` as a validation cell instead of an executable command.
  - [`task.md`](docs/execution/plans/2026-03-17-send-step/task.md:12) still uses ``get_step("send") returns `SendStep``` as an assertion, not an exact command.
  - [`task.md`](docs/execution/plans/2026-03-17-send-step/task.md:13) still uses `AC-S18, AC-S19 pass` instead of a concrete command.
  - [`task.md`](docs/execution/plans/2026-03-17-send-step/task.md:25) still says `grep MEU-88 in registry` rather than an exact runnable command.
  - The remaining post-MEU rows are better than before, but the plan still has not fully met the exact-command bar required by [`AGENTS.md`](AGENTS.md:99).
  - Impact: the plan is now narrowly blocked on auditability rather than architecture or spec coherence.

### Recheck Verdict

- **Previously open core design and verification-scope issues:** resolved
- **Current verdict:** `changes_required`
- **Reason:** the only remaining defect is validation realism in a handful of task rows
- **Residual risk:** low; implementation direction is ready, but a few task rows still cannot be objectively checked as written
- **Next step:** run a final `/planning-corrections` pass limited to converting the remaining prose validation cells in [`task.md`](docs/execution/plans/2026-03-17-send-step/task.md:11)–[`task.md`](docs/execution/plans/2026-03-17-send-step/task.md:13) and [`task.md`](docs/execution/plans/2026-03-17-send-step/task.md:25) into exact commands.

---

## Corrections Applied — Round 7 — 2026-03-17

### Findings Resolution

| # | Severity | Finding | Resolution |
|---|----------|---------|------------|
| F18 | Medium | 7 task.md validation cells use prose placeholders (`import resolves`, `Visual check`, `7-section format`, `File exists`, `Row added`, `Note saved`, `Messages ready for review`) | ✅ All replaced with exact commands: `uv run python -c`, `rg`, `Test-Path`, `pomera_notes search` |

### Files Changed

- [`task.md`](docs/execution/plans/2026-03-17-send-step/task.md) — rows 8, 13–18: prose → exact commands

### Verification Evidence

```
No prose placeholders remaining → PASS (all 7 phrases absent)
Exact commands present → uv run python -c, Test-Path, pomera_notes search all found
```

### Verdict

- `approved` — all recheck-5 findings resolved; every task.md validation cell now uses exact auditable commands; plan ready for implementation
