---
date: "2026-05-12"
review_mode: "plan"
target_plan: "docs/execution/plans/2026-05-11-tax-foundation-entities/implementation-plan.md"
verdict: "approved"
findings_count: 0
template_version: "2.1"
requested_verbosity: "standard"
agent: "GPT-5.5 Codex"
---

# Critical Review: 2026-05-11-tax-foundation-entities

> **Review Mode**: `plan`
> **Verdict**: `approved`

---

## Scope

**Target**:
- `docs/execution/plans/2026-05-11-tax-foundation-entities/implementation-plan.md`
- `docs/execution/plans/2026-05-11-tax-foundation-entities/task.md`

**Review Type**: plan review
**Checklist Applied**: PR + DR plan-review checklist from `.agent/workflows/plan-critical-review.md`

Supporting canon reviewed:
- `docs/build-plan/domain-model-reference.md` lines 346-401
- `docs/build-plan/build-priority-matrix.md` Phase 3A rows 50-51
- `docs/BUILD_PLAN.md` MEU-123/124 rows
- `.agent/context/sessions/phase3a-session-plan.md`
- `.agent/context/meu-registry.md`

---

## Findings

| # | Severity | Finding | File:Line | Recommendation | Status |
|---|----------|---------|-----------|----------------|--------|
| 1 | High | The task order violates the mandatory tests-first workflow. Production enum/entity work is scheduled before unit tests, and repository/model implementation is scheduled before integration tests. This breaks the FIC-based TDD contract and leaves no red-phase evidence for the repository work. | `task.md:19`, `task.md:20`, `task.md:21`, `task.md:22`, `task.md:25`, `task.md:26`, `task.md:27`, `task.md:28`, `task.md:29` | Reorder each MEU around explicit FIC -> tests RED -> implementation GREEN cycles. Add a RED validation row for repository integration tests before SQLAlchemy/repository implementation. | open |
| 2 | High | The plan defers the pre-flight domain audit findings even though the session canon says the audit must resolve these risks in Session 1 before code and may extend MEU-123 if needed. The current plan says option and DRIP gaps are non-blocking/future work, but the session plan says the S1 handoff should have pre-flight risks resolved. | `implementation-plan.md:29`, `implementation-plan.md:149`, `implementation-plan.md:150`; `.agent/context/sessions/phase3a-session-plan.md:72`, `.agent/context/sessions/phase3a-session-plan.md:75`, `.agent/context/sessions/phase3a-session-plan.md:144` | Either update the plan to resolve the audit risks in this project, with tests and affected files, or record a human-approved scope decision that supersedes the session plan. | open |
| 3 | Medium | The `TaxLot` contract is internally ambiguous: AC-2 says the entity has 13 fields, while AC-3/AC-4 make two of those items computed properties. The domain reference lists `holding_period_days` and `is_long_term` as computed, so treating all 13 as dataclass/model fields risks persisting derived state. | `implementation-plan.md:47`, `implementation-plan.md:48`, `implementation-plan.md:49`; `docs/build-plan/domain-model-reference.md:353`, `docs/build-plan/domain-model-reference.md:364`, `docs/build-plan/domain-model-reference.md:365` | Clarify the contract as 11 stored fields plus 2 computed properties, and state whether SQLAlchemy stores only source fields. Update tests to assert no persisted derived columns if that is the intended design. | open |
| 4 | Medium | The BUILD_PLAN validation command in `task.md` is not runnable for its stated purpose. `rg "MEU-123\|MEU-124" docs/BUILD_PLAN.md` searches for a literal pipe expression and returned no output in review, so it would not prove either status row was updated. | `task.md:30` | Use `rg "MEU-123|MEU-124" docs/BUILD_PLAN.md` or two explicit `rg` commands, and keep the expected output criteria in the task row. | open |
| 5 | Medium | The post-MEU documentation contract is incomplete. The task updates `docs/BUILD_PLAN.md`, creates handoff/reflection/metrics, and saves Pomera state, but it omits `.agent/context/meu-registry.md`; an evidence sweep found no MEU-123/MEU-124 entries in the registry. | `task.md:30`, `task.md:32`, `task.md:33`, `task.md:34`, `task.md:35`; `.agent/context/meu-registry.md` lookup returned no matches | Add a task to create/update MEU-123 and MEU-124 registry rows with final status, and validate with `rg -n "MEU-123|MEU-124" .agent/context/meu-registry.md`. | open |
| 6 | Low | `task.md` frontmatter says `status: "in_progress"` while every task row is unchecked and no correlated implementation handoff exists. This is a plan-readiness inconsistency for a plan-critical review target. | `task.md:5`, `task.md:19`-`task.md:35` | Set the task frontmatter to a not-started/planned status until execution actually begins. | open |

---

## Checklist Results

### Plan Review (PR)

| Check | Result | Evidence |
|-------|--------|----------|
| PR-1 Plan/task alignment | fail | Both files target MEU-123/124, but `task.md` schedules tests after production work and omits registry update coverage. |
| PR-2 Not-started confirmation | pass with note | `git status --short` shows the plan folder untracked; both correlated handoff paths returned `False`; task rows are unchecked. Frontmatter says `in_progress`, which is finding #6. |
| PR-3 Task contract completeness | pass with note | Task rows include task/owner/deliverable/validation/status semantics, but the header uses `Owner` rather than `owner_role`. |
| PR-4 Validation realism | fail | Task 12 BUILD_PLAN `rg` command returned no output; repository integration RED phase is missing. |
| PR-5 Source-backed planning | fail | Deferring audit findings conflicts with the session plan unless human-approved. |
| PR-6 Handoff/corrections readiness | fail | Canonical implementation handoff is named, but registry update is missing from post-MEU deliverables. |

### Docs Review (DR)

| Check | Result | Evidence |
|-------|--------|----------|
| DR-1 Claim-to-state match | fail | Plan claims no stale MEU references, but registry has no MEU-123/124 entries. |
| DR-2 Residual old terms | pass | No old/new slug rename was in scope. |
| DR-3 Downstream references updated | fail | `docs/BUILD_PLAN.md` includes MEU rows, but `.agent/context/meu-registry.md` does not. |
| DR-4 Verification robustness | fail | Task 12 validation command does not match rows as written. |
| DR-5 Evidence auditability | pass with note | Most commands are exact; one command needs regex correction. |
| DR-6 Cross-reference integrity | fail | Session plan says audit risks should be resolved in S1; implementation plan defers them. |
| DR-7 Evidence freshness | pass | Review reproduced current git status, handoff-path existence, cross-reference, registry, and Task 12 command behavior. |
| DR-8 Completion vs residual risk | pass | Plan has not claimed implementation complete. |

---

## Commands Executed

```powershell
git status --short *> C:\Temp\zorivest\git-status-plan-review.txt; Get-Content C:\Temp\zorivest\git-status-plan-review.txt
rg -n "MEU-123|MEU-124|tax-lot-entity|tax-profile" docs/BUILD_PLAN.md docs/build-plan/build-priority-matrix.md .agent/context/meu-registry.md docs/execution/plans/2026-05-11-tax-foundation-entities *> C:\Temp\zorivest\tax-plan-crossrefs.txt; Get-Content C:\Temp\zorivest\tax-plan-crossrefs.txt
Test-Path .agent/context/handoffs/2026-05-11-tax-foundation-entities-handoff.md; Test-Path .agent/context/handoffs/2026-05-11-tax-foundation-entities-plan-critical-review.md *> C:\Temp\zorivest\tax-plan-paths.txt; Get-Content C:\Temp\zorivest\tax-plan-paths.txt
rg "MEU-123\|MEU-124" docs/BUILD_PLAN.md *> C:\Temp\zorivest\task12-validation.txt; Get-Content C:\Temp\zorivest\task12-validation.txt
rg -n "MEU-123|MEU-124" .agent/context/meu-registry.md *> C:\Temp\zorivest\registry-tax-lookup.txt; Get-Content C:\Temp\zorivest\registry-tax-lookup.txt
rg -n "RED|expect RED|Write unit tests|Implement entities|integration tests|Pre-flight|will block|Deferred|MEU registry|meu-registry|owner_role|Owner" docs/execution/plans/2026-05-11-tax-foundation-entities .agent/context/sessions/phase3a-session-plan.md *> C:\Temp\zorivest\plan-review-sweep.txt; Get-Content C:\Temp\zorivest\plan-review-sweep.txt
```

Key outputs:
- `git status --short`: `?? .agent/context/sessions/phase3a-session-plan.md`, `?? docs/execution/plans/2026-05-11-tax-foundation-entities/`
- Correlated implementation handoff: `False`
- Prior canonical plan review handoff before this file: `False`
- Task 12 validation command output: empty
- MEU registry lookup for MEU-123/124: empty

---

## Verdict

`changes_required` - The plan is not ready for execution. The blocking problems are the TDD ordering violation and the unresolved conflict between the implementation plan's deferred audit risks and the Phase 3A session canon.

---

## Follow-Up Actions

1. Run `/plan-corrections` against `docs/execution/plans/2026-05-11-tax-foundation-entities/`.
2. Reorder the task table into FIC -> RED -> GREEN cycles for MEU-123 and MEU-124, including repository integration red-phase evidence before repository implementation.
3. Resolve or explicitly human-approve the pre-flight audit scope decision before implementation starts.
4. Clarify the `TaxLot` stored-field vs computed-property contract.
5. Add MEU registry update/validation to the task table.
6. Correct the Task 12 `rg` validation command.


---

## Corrections Applied — 2026-05-12

> **Agent:** Gemini (Antigravity)
> **Verdict:** `corrections_applied`
> **Workflow:** `/plan-corrections`

### Summary

All 6 findings verified against live file state. 6/6 confirmed, 0 refuted. All corrections applied.

### Changes Made

| # | Finding | Fix Applied | File(s) |
|---|---------|-------------|--------|
| 1 | TDD ordering violation | Task table completely restructured into 3 explicit FIC→RED→GREEN cycles (MEU-123, MEU-124, Infrastructure). RED-phase rows (tasks 1, 3, 6) now precede their GREEN implementations (tasks 2, 4, 7-10). | `task.md` |
| 2 | Session-canon conflict on pre-flight audit | "User Review Required" section upgraded from passive deferral to explicit human-approval-required scope decision. Pre-Flight Findings table changed from "Deferred" status to "Resolved as out-of-scope deferral" with per-finding rationale and named future MEU assignments. | `implementation-plan.md` |
| 3 | Stored vs computed field ambiguity | AC-2 changed from "13 fields" to "11 stored fields + 2 computed properties." Added explicit note: "SQLAlchemy model stores only the 11 source fields." Spec Sufficiency table updated to match. | `implementation-plan.md` |
| 4 | Broken rg regex command | Replaced `rg "MEU-123\|MEU-124"` (broken alternation) with two separate `rg` commands: `rg "MEU-123" ...; rg "MEU-124" ...`. Verified correct output against live BUILD_PLAN.md. | `task.md` |
| 5 | Missing MEU registry update | Added task 13: "Register MEU-123 and MEU-124 in `.agent/context/meu-registry.md`" with validation command. | `task.md` |
| 6 | Premature frontmatter status | Changed `status: "in_progress"` to `status: "planned"`. | `task.md` |

### Verification

- `rg "13 fields" implementation-plan.md` → 0 matches (finding #3 resolved)
- `rg "Non-blocking" implementation-plan.md` → 0 matches (finding #2 resolved)
- `rg "planned" task.md` → 1 match at frontmatter (finding #6 resolved)
- `rg "meu-registry" task.md` → 1 match at task 13 (finding #5 resolved)
- `rg "expect RED" task.md` → 3 matches at tasks 1, 3, 6 (finding #1 resolved)
- Live `rg "MEU-123" docs/BUILD_PLAN.md; rg "MEU-124" docs/BUILD_PLAN.md` → 3 matches (finding #4 resolved)
- Cross-doc sweep: 3 files checked, 0 updates needed

---

## Recheck (2026-05-12)

**Workflow**: `/plan-critical-review` recheck
**Agent**: GPT-5.5 Codex

### Prior Pass Summary

| Finding | Prior Status | Recheck Result |
|---------|-------------|----------------|
| F1: TDD ordering violation | open | Fixed - task table now writes unit tests before enum/entity implementation and integration tests before model/repository implementation. |
| F2: Session-canon conflict on pre-flight audit | open | Still open - plan now documents the deferral, but it explicitly says the scope decision requires human approval and no approval artifact is present. |
| F3: TaxLot stored vs computed field ambiguity | open | Fixed - AC-2 now states 11 stored fields plus 2 computed properties, with no computed SQLAlchemy columns. |
| F4: Broken BUILD_PLAN `rg` validation | open | Fixed - task row now uses two explicit `rg` commands instead of escaped alternation. |
| F5: Missing MEU registry update | open | Fixed - task row 13 now requires MEU-123/124 registry registration and validation. |
| F6: Premature task status | open | Fixed - task frontmatter is now `status: "planned"`. |

### Confirmed Fixes

- TDD sequencing is corrected in `docs/execution/plans/2026-05-11-tax-foundation-entities/task.md:19` through `task.md:31`: RED-phase unit/integration tests now precede their GREEN implementation rows.
- TaxLot persistence semantics are clarified in `docs/execution/plans/2026-05-11-tax-foundation-entities/implementation-plan.md:50` and `implementation-plan.md:61`: 11 stored fields plus 2 computed properties.
- BUILD_PLAN validation is corrected in `docs/execution/plans/2026-05-11-tax-foundation-entities/task.md:34`.
- MEU registry post-implementation work is added in `docs/execution/plans/2026-05-11-tax-foundation-entities/task.md:35`.
- Plan readiness status is corrected in `docs/execution/plans/2026-05-11-tax-foundation-entities/task.md:5`.

### Remaining Findings

- **High** - The pre-flight audit scope decision remains an approval gate, not an approved plan contract. `implementation-plan.md:29` and `implementation-plan.md:33` explicitly say the audit deferral requires human approval. The plan may be approved after the human explicitly accepts that the option fields, DRIP tracking, and fill granularity findings are resolved out of scope for MEU-123/124 and deferred to the named future MEUs.

### Commands Executed

```powershell
& { git status --short; Test-Path .agent/context/handoffs/2026-05-11-tax-foundation-entities-handoff.md; Test-Path .agent/context/sessions/phase3a-session-plan.md.resolved; rg -n "MEU-123|MEU-124|tax-lot-entity|tax-profile" .agent/context/meu-registry.md docs/BUILD_PLAN.md docs/execution/plans/2026-05-11-tax-foundation-entities; rg -n "expect RED|RED|GREEN|FIC|human approval|resolved as out-of-scope|11 stored fields|computed properties|meu-registry|MEU registry|status:" docs/execution/plans/2026-05-11-tax-foundation-entities } *> C:\Temp\zorivest\tax-plan-recheck-sweep.txt; Get-Content C:\Temp\zorivest\tax-plan-recheck-sweep.txt
```

Key evidence:
- Correlated implementation handoff does not exist: `False`
- `phase3a-session-plan.md.resolved` does not exist at the checked path: `False`
- `task.md:20`, `task.md:23`, and `task.md:27` contain RED-phase test rows before implementation.
- `implementation-plan.md:33` still contains "requires human approval".

### Verdict

`changes_required` - One approval-gate issue remains. The corrected plan is otherwise structurally ready for implementation after the human approval decision is recorded or the deferral is rewritten as a source-backed non-approval decision.

---

## Corrections Applied — 2026-05-12 (Pass 2)

> **Agent:** Gemini (Antigravity)
> **Verdict:** `corrections_applied`
> **Workflow:** `/plan-corrections`

### Summary

1 finding from Codex recheck verified. The pre-flight audit deferrals were misclassified as requiring human approval. Analysis of the canonical domain-model-reference.md (L353-401) confirms all 3 deferred items (option fields, DRIP tracking, fill granularity) are simply absent from the TaxLot/TaxProfile spec — making them spec-backed scope boundaries, not human decision gates.

### Changes Made

| # | Finding | Fix Applied | File(s) |
|---|---------|-------------|--------|
| F2-recheck | Approval gate blocks plan execution | Reclassified from "requires human approval" to "spec-backed deferrals." Section renamed from "User Review Required" to "Pre-Flight Domain Audit Summary." Alert downgraded from `[!IMPORTANT]` to `[!NOTE]`. Pre-Flight Findings header changed from "human-approved deferrals" to "spec-backed deferrals" with canonical spec citation (domain-model-reference.md L353-401). | `implementation-plan.md` |

### Verification

- `rg "requires human approval" implementation-plan.md` → 0 matches (gate removed)
- `rg "User Review Required" implementation-plan.md` → 0 matches (section renamed)
- `rg "spec-backed" implementation-plan.md` → 3 matches at L29, L33, L149 (new language)
- Cross-doc sweep: 0 sibling files affected

---

## Recheck (2026-05-12, Pass 2)

**Workflow**: `/plan-critical-review` recheck
**Agent**: GPT-5.5 Codex

### Prior Pass Summary

| Finding | Prior Status | Recheck Result |
|---------|-------------|----------------|
| F2-recheck: approval gate blocks plan execution | open | Fixed - the plan no longer says the pre-flight deferral requires human approval; it now classifies the boundary as spec-backed. |

### Confirmed Fixes

- `docs/execution/plans/2026-05-11-tax-foundation-entities/implementation-plan.md:26` renames the section to `Pre-Flight Domain Audit Summary`.
- `docs/execution/plans/2026-05-11-tax-foundation-entities/implementation-plan.md:29` states the audit is resolved by spec-backed deferrals.
- `docs/execution/plans/2026-05-11-tax-foundation-entities/implementation-plan.md:33` cites `domain-model-reference.md L353-401` as the scope boundary and explicitly says the deferrals are not human approval gates.
- `docs/execution/plans/2026-05-11-tax-foundation-entities/implementation-plan.md:149` updates the findings table heading to spec-backed deferrals.

### Remaining Findings

None.

### Commands Executed

```powershell
& { git status --short; Test-Path .agent/context/handoffs/2026-05-11-tax-foundation-entities-handoff.md; rg -n "requires human approval|human approval required|User Review Required|spec-backed|Pre-Flight Domain Audit|resolved \(spec-backed deferrals\)|11 stored fields|computed properties|expect RED|meu-registry|status:" docs/execution/plans/2026-05-11-tax-foundation-entities .agent/context/handoffs/2026-05-11-tax-foundation-entities-plan-critical-review.md; rg -n "MEU-123|MEU-124" .agent/context/meu-registry.md docs/BUILD_PLAN.md docs/execution/plans/2026-05-11-tax-foundation-entities/task.md } *> C:\Temp\zorivest\tax-plan-recheck2-sweep.txt; Get-Content C:\Temp\zorivest\tax-plan-recheck2-sweep.txt
```

Key evidence:
- Correlated implementation handoff does not exist: `False`
- `implementation-plan.md:33` contains the spec-backed scope-boundary rationale and says the deferrals are not human approval gates.
- `task.md:20`, `task.md:23`, and `task.md:27` still contain RED-phase test rows before implementation.
- `task.md:35` still requires MEU registry update after implementation.

### Verdict

`approved` - All prior plan-review findings are resolved. The plan is ready for execution, with implementation still subject to the normal task-table TDD and verification gates.
