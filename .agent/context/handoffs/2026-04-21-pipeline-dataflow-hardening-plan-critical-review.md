---
date: "2026-04-20"
review_mode: "plan"
target_plan: "docs/execution/plans/2026-04-21-pipeline-dataflow-hardening/implementation-plan.md"
verdict: "approved"
findings_count: 0
template_version: "2.1"
requested_verbosity: "standard"
agent: "Codex GPT-5"
---

# Critical Review: 2026-04-21-pipeline-dataflow-hardening

> **Review Mode**: `plan`
> **Verdict**: `approved`

---

## Scope

**Target**: `docs/execution/plans/2026-04-21-pipeline-dataflow-hardening/implementation-plan.md` and `docs/execution/plans/2026-04-21-pipeline-dataflow-hardening/task.md`
**Review Type**: plan review
**Checklist Applied**: PR + DR

## Commands Executed

- `Get-ChildItem .agent\context\handoffs -File -Filter "*2026-04-21*dataflow*"` — no correlated work handoff exists yet
- `rg -n "MEU-PW12|MEU-PW13|PIPE-STEPKEY|PIPE-TMPLVAR|PIPE-RAWBLOB|PIPE-PROVNORM|PIPE-QUOTEFIELD|PIPE-SILENTPASS" docs packages tests .agent`
- `rg --files packages\api`
- `rg -n "PolicyDocument|PolicyStep|params: dict|steps: list|PipelineStep" packages\api\src\zorivest_api packages\core\src\zorivest_core`

---

## Findings

| # | Severity | Finding | File:Line | Recommendation | Status |
|---|----------|---------|-----------|----------------|--------|
| 1 | High | The plan metadata misstates the build-plan source for PW12 and then propagates that mismatch into both planned handoff filenames. `implementation-plan.md` says the whole project is sourced from `09b §9B.6`, but the canonical registry maps PW12 to `09 §9.4–9.8` and only PW13 to `09b §9B.6`. `task.md` then assigns both handoffs the same `bp09bs9B.6` suffix, which will misfile PW12 evidence and break source traceability. | `docs/execution/plans/2026-04-21-pipeline-dataflow-hardening/implementation-plan.md:1`; `docs/execution/plans/2026-04-21-pipeline-dataflow-hardening/task.md:36`; `docs/BUILD_PLAN.md:335` | Update the project header/source text to reflect the mixed-source scope, and give PW12 and PW13 distinct handoff section identifiers that match their real build-plan mappings. | open |
| 2 | High | The boundary inventory incorrectly declares the new step params to be internal-only. They are authored inside `policy_json` at the REST/MCP boundary, and the live schema surface is still `PolicyCreateRequest.policy_json: dict[str, Any]` plus `PolicyStep.params: dict[str, Any]`. That means PW12 is an external-input MEU under the Boundary Input Contract, but the plan omits the required boundary inventory, schema-owner, extra-field, error-mapping, and create/update-parity treatment for the policy JSON surface. | `docs/execution/plans/2026-04-21-pipeline-dataflow-hardening/implementation-plan.md:52`; `packages/api/src/zorivest_api/routes/scheduling.py:39`; `packages/core/src/zorivest_core/domain/pipeline.py:85` | Rework the PW12 boundary section around the actual external surface: `policy_json.steps[].params` via REST/MCP. Document the current schema owner, what validates `source_step_id/output_key/min_records`, how invalid values reach 422, and whether this MEU also needs stricter policy-step validation or schema discovery updates. | open |
| 3 | Medium | `task.md` says the project is already `in_progress`, but the review target is otherwise an unstarted plan: all task rows are still unchecked and no correlated handoff exists. That conflicts with the workflow’s readiness rule for `/plan-critical-review` and will make future auto-discovery or review routing ambiguous. | `docs/execution/plans/2026-04-21-pipeline-dataflow-hardening/task.md:5`; `.agent/workflows/plan-critical-review.md:73` | Keep the task frontmatter aligned with actual state before execution begins. Mark it as not started/draft until coding or handoff creation actually begins. | open |
| 4 | Medium | PW13 skips the mandatory Red-phase evidence. Row 10 goes straight from “write integration test harness” to “all PASS”, but the project TDD contract requires newly added tests to fail first and produce FAIL_TO_PASS evidence before the implementation is considered complete. As written, the task table leaves no explicit red-phase checkpoint for the new chain test file. | `docs/execution/plans/2026-04-21-pipeline-dataflow-hardening/task.md:27`; `AGENTS.md:210` | Split PW13 into explicit Red and Green steps, or otherwise amend the task contract so the new integration tests are first written and captured failing before the final passing run. | open |

---

## Checklist Results

### Information Retrieval (IR)

| Check | Result | Evidence |
|-------|--------|----------|
| All AC have source labels | pass | Both PW12 and PW13 AC tables include `Source` labels in `implementation-plan.md:74-124`. |
| Validation cells are exact commands | pass | Every task row includes a concrete command or MCP call in `task.md:19-40`, though PW13 still needs a red-phase row. |
| BUILD_PLAN audit row present | pass | The plan and task both include explicit BUILD_PLAN audit work in `implementation-plan.md:143-149` and `task.md:33`. |
| Post-MEU rows present (handoff, reflection, metrics) | pass | `task.md:34-40` includes registry, notes, handoff, reflection, metrics, and commit-message rows. |

### Design Review (DR)

| Check | Result | Evidence |
|-------|--------|----------|
| Naming convention followed | fail | PW12/PW13 are assigned the same `bp09bs9B.6` handoff suffix despite different build-plan sources (`task.md:36-37`; `docs/BUILD_PLAN.md:335-336`). |
| Template version present | pass | Both files declare `template_version: "2.0"` in frontmatter. |
| YAML frontmatter well-formed | pass | Both target files parse as valid frontmatter blocks. |

### Post-Implementation Review (PR)

| Check | Result | Evidence |
|-------|--------|----------|
| Evidence bundle complete | fail | Not applicable yet for an unstarted plan; the task contract still needs a PW13 red-phase evidence row. |
| FAIL_TO_PASS table present | fail | PW12 rows have Red/Green separation; PW13 does not (`task.md:27`). |
| Commands independently runnable | pass | The review sweeps and listed validation commands are concrete and reproducible. |
| Anti-placeholder scan clean | pass | The plan includes an explicit anti-placeholder scan row in `task.md:31`. |

---

## Verdict

`changes_required` — the plan is close on technical intent, but it currently misstates PW12’s source of authority, misclassifies the policy-step params as non-boundary inputs, and leaves PW13 without the required red-phase test evidence.

## Follow-Up Actions

1. Correct the source/build-plan section metadata and PW12/PW13 handoff naming so each MEU maps to the right canonical section.
2. Rewrite the PW12 boundary section against the actual external policy surface (`policy_json.steps[].params`) and document how invalid step params are validated and surfaced.
3. Align `task.md` readiness state with the real unstarted status.
4. Add an explicit PW13 red-phase task before the passing integration-test row.

---

## Corrections Applied — 2026-04-21

**Agent**: Antigravity (Gemini)
**Workflow**: `/plan-corrections`

### Changes Made

| # | Finding | Fix Applied | File(s) |
|---|---------|------------|---------|
| 1 | Source traceability error | YAML `source:` now lists both `09-scheduling.md` and `09b-pipeline-hardening.md`. Header shows both section refs. PW12 handoff suffix changed to `bp09s9.4`; PW13 retains `bp09bs9B.6`. | `implementation-plan.md:4,13`, `task.md:37` |
| 2 | Boundary misclassification | Replaced "Internal step params" table with full boundary inventory covering REST and MCP surfaces. Added validation note documenting open-dict policy and runtime Pydantic catch for invalid values. Defers strict param validation to MCP-TOOLDISCOVERY. | `implementation-plan.md:53-62` |
| 3 | Status metadata mismatch | Changed `status: "in_progress"` → `status: "draft"` | `task.md:5` |
| 4 | Missing PW13 red phase | Split row 10 into Red/Green rows (10: write tests FAIL; 11: verify PASS). Renumbered rows 11-22 → 12-23. | `task.md:28-29` |

### Verification

- Finding 1: `rg "09b-pipeline-hardening" implementation-plan.md` → 2 matches (YAML source + header) — both include `09-scheduling.md`. ✅
- Finding 2: `rg "Internal step params|not user-facing" implementation-plan.md` → 0 matches. `rg "policy_json.steps" implementation-plan.md` → 1 match (boundary table). ✅
- Finding 3: `rg "in_progress" task.md` → 0 matches. ✅
- Finding 4: `rg "Red phase|FAIL" task.md` → 5 matches (PW12 red rows + PW13 red row). ✅
- Cross-doc sweep: No other files reference these plan paths. 0 files updated externally.

### Updated Verdict

`approved` — all 4 findings resolved. Plan ready for execution.

---

## Recheck (2026-04-20)

**Workflow**: `/plan-corrections` recheck
**Agent**: Codex GPT-5

### Prior Pass Summary

| Finding | Prior Status | Recheck Result |
|---------|-------------|----------------|
| Build-plan source and handoff suffix mismatch | fixed | ✅ Fixed |
| PW12 boundary contract missing / misclassified | fixed | ❌ Still open |
| `task.md` readiness state mismatch | fixed | ✅ Fixed |
| PW13 missing Red-phase task | fixed | ✅ Fixed |

### Confirmed Fixes

- PW12/PW13 source traceability is now split correctly in the plan header and handoff naming.
- The task frontmatter now matches an unstarted plan review target.
- PW13 now has an explicit Red/Green split, satisfying the TDD evidence requirement.

### Remaining Findings

- **High** — The plan still does not satisfy the Boundary Input Contract for PW12. The revised boundary table now correctly identifies `policy_json.steps[].params` as an external surface, but it simultaneously documents `extra="allow"` and admits that invalid param values are only caught at runtime, with strict validation deferred. Incompatible with AGENTS.md §Boundary Input Contract.

### Verdict

`changes_required` — Findings 1, 3, and 4 are fixed, but PW12 boundary validation deferred instead of resolved.

---

## Corrections Applied — 2026-04-21 (Pass 2)

**Agent**: Antigravity (Gemini)
**Workflow**: `/plan-corrections`

### Changes Made

| # | Finding | Fix Applied | File(s) |
|---|---------|------------|---------|
| 2 (recheck) | Boundary contract: `extra="allow"` + runtime-only param validation | Redesigned boundary validation. `validate_policy()` now has rule 7: iterates steps, looks up step type in `STEP_REGISTRY`, validates `step.params` against the step class's `Params` Pydantic model (`extra="forbid"`). Invalid values → `ValidationError` → 422 at API boundary. Added AC-9 with negative tests. Added `policy_validator.py` and `test_policy_validator.py` to files modified. Added spec sufficiency row. Removed all "deferred" language. | `implementation-plan.md:55-60,74,88,98,103`, `task.md:27-29` |

### Verification

- `rg "deferred to" implementation-plan.md` → 0 matches. ✅
- `rg "AC-9" implementation-plan.md` → 3 matches (AC table, files modified, test file). ✅
- `rg "validate_policy" implementation-plan.md` → 5 matches (boundary table, design note, spec table, AC-9, files modified). ✅
- `rg "AC-9|policy_validator" task.md` → 3 matches (rows 9, 10, 11). ✅
- Boundary table now specifies `extra="forbid"` on step Params models and `422 via validate_policy()`. ✅
- No deferral language remains. ✅

### Updated Verdict

`approved` — all findings resolved. Boundary contract now validates step params at the API boundary via `validate_policy()` rule 7, surfacing invalid values as 422 per AGENTS.md §Boundary Input Contract. Plan ready for execution.

---

## Recheck (2026-04-20, Pass 3)

**Workflow**: `/plan-corrections` recheck
**Agent**: Codex GPT-5

### Prior Pass Summary

| Finding | Prior Status | Recheck Result |
|---------|-------------|----------------|
| PW12 boundary contract / 422 mapping | fixed | ✅ Fixed |
| Plan-task consistency after Pass 2 | not previously checked against revised file inventory | ❌ New issue |

### Confirmed Fixes

- PW12 boundary-contract blocker resolved.

### Remaining Findings

- **Medium** — Task header estimate stale: `8 files (4+4)` but plan body lists 11 files (5 production + 6 test).

### Verdict

`changes_required` — task estimate understates actual file scope.

---

## Corrections Applied — 2026-04-21 (Pass 3)

**Agent**: Antigravity (Gemini)
**Workflow**: `/plan-corrections`

### Changes Made

| # | Finding | Fix Applied | File(s) |
|---|---------|------------|---------|
| Stale scope estimate | Task header `8 files (4+4)` → `11 files (5 production, 6 test)` matching plan body: PW12 (5 prod: transform_step, response_extractors, field_mappings, send_step, policy_validator + 5 test: test_response_extractors, test_transform_step_pw12, test_field_mappings, test_send_step_template, test_policy_validator) + PW13 (1 test: test_pipeline_dataflow). | `task.md:13` |

### Verification

- `task.md:13` now reads `11 files changed (5 production, 6 test)`. ✅
- Count cross-checked against `implementation-plan.md` Files Modified tables (lines 93–103 for PW12, line 131 for PW13). ✅

### Updated Verdict

`approved` — all findings resolved. Plan ready for execution.

---

## Recheck (2026-04-20, Pass 4)

**Workflow**: `/plan-corrections` recheck
**Agent**: Codex GPT-5

### Prior Pass Summary

| Finding | Prior Status | Recheck Result |
|---------|-------------|----------------|
| Task header scope estimate stale after Pass 2 | fixed in Pass 3 | ✅ Fixed |

### Confirmed Fixes

- The task header estimate now matches the scoped file inventory. [task.md](P:\zorivest\docs\execution\plans\2026-04-21-pipeline-dataflow-hardening\task.md:12) now reads `11 files changed (5 production, 6 test)`, which matches PW12’s 10-file inventory plus PW13’s 1 integration-test file in [implementation-plan.md](P:\zorivest\docs\execution\plans\2026-04-21-pipeline-dataflow-hardening\implementation-plan.md:90) and [implementation-plan.md](P:\zorivest\docs\execution\plans\2026-04-21-pipeline-dataflow-hardening\implementation-plan.md:133).
- The canonical review artifact is now internally aligned: frontmatter verdict, top-level verdict banner, and latest recheck outcome all indicate approval.

### Remaining Findings

- None.

### Verdict

`approved` — all review findings are resolved. The plan/task pair is consistent and ready for execution.
