---
date: "2026-04-11"
review_mode: "plan"
target_plan: "docs/execution/plans/2026-04-11-pyright-test-cleanup/implementation-plan.md"
verdict: "approved"
findings_count: 3
template_version: "2.1"
requested_verbosity: "standard"
agent: "GPT-5.4 Codex"
---

# Critical Review: 2026-04-11-pyright-test-cleanup

> **Review Mode**: `plan`
> **Verdict**: `approved`

---

## Scope

**Target**: `docs/execution/plans/2026-04-11-pyright-test-cleanup/implementation-plan.md` and `docs/execution/plans/2026-04-11-pyright-test-cleanup/task.md`
**Review Type**: Plan review
**Checklist Applied**: PR-1 through PR-6, with supporting source-traceability and command-readiness checks

Correlation rationale:
- The user provided the execution-plan files directly, so the workflow used scope override rather than auto-discovery.
- No correlated implementation handoff exists yet for this slug (`rg -n 'pyright-test-cleanup|pyright-enum-literals|pyright-entity-factories' .agent/context/handoffs` returned no matches), so this remains a plan-review pass.
- Canonical review target for this mode is `.agent/context/handoffs/2026-04-11-pyright-test-cleanup-plan-critical-review.md`.

---

## Commands Executed

| Command | Purpose | Result |
|---|---|---|
| `uv run pyright tests/` with redirect receipt | Reproduce current baseline and verify the stated `205`-error starting point | `205 errors, 0 warnings, 0 informations` |
| `uv run pyright tests/unit/test_entities.py` with redirect receipt | Verify the stated Group 1 baseline in `test_entities.py` | `105 errors, 0 warnings, 0 informations` |
| `rg -n '2>&1\|Select-String|status: "draft"|MEU-TS2|MEU-TS3|TS\.B|TS\.C' ...` | Check plan/task status, command cells, and source references | Confirmed task lines 19-23 and plan/header references |
| `rg -n 'Group 2|Group 3|Group 4|reportOptionalMemberAccess|reportOptionalSubscript|reportOperatorIssue|attribute assignment|reportCallIssue|type mismatch|SqlAlchemyUnitOfWork' implementation-plan.md` | Verify each group's declared scope against its task validation cell | Confirmed scope mismatch in Groups 2-4 |
| `rg -n 'pyright-test-cleanup|pyright-enum-literals|pyright-entity-factories' .agent/context/handoffs` | Confirm no work handoff exists yet | No matches |

---

## Findings

| # | Severity | Finding | File:Line | Recommendation | Status |
|---|----------|---------|-----------|----------------|--------|
| 1 | High | Several validation commands are not executable under the repo's P0 shell contract. Task items 1, 4, and 5 still use forbidden `2>&1 \| Select-String` pipelines, and items 2-3 use unredirected `uv run pyright ...` commands. This makes the plan unsafe to execute as written in PowerShell. | `docs/execution/plans/2026-04-11-pyright-test-cleanup/task.md:19-23` | Rewrite every terminal validation cell to the mandatory redirect-to-file pattern under `C:\Temp\zorivest\`, and remove all direct `2>&1 \| Select-String` usage. | open |
| 2 | Medium | Multiple validation cells do not actually prove the deliverables they are attached to. Task 1 claims to verify all enum-literal errors, but its grep pattern only mentions `TradeAction` while the spec row also names `AccountType`. Task 3 covers only 3 files even though Group 2 spans 7 files. Task 4 checks only `ColumnElement`, but Group 3 also includes attribute-assignment suppressions. Task 5 checks only `reportCallIssue`, but Group 4 also includes type-mismatch and protocol errors. | `docs/execution/plans/2026-04-11-pyright-test-cleanup/task.md:19-23`, `docs/execution/plans/2026-04-11-pyright-test-cleanup/implementation-plan.md:98-154`, `docs/BUILD_PLAN.md:489-490` | Make each validation command cover the full stated scope, or split the groups so each task validates exactly the files and error classes it changes. | open |
| 3 | Low | The plan header blurs primary spec vs supporting canon. `Build Plan Section(s): TS.B (testing-strategy, 01 §1.2), TS.C (testing-strategy, 01 §1.4)` makes the testing-strategy and domain-layer sections look like the authoritative execution spec, but the actual MEU contract for this project lives in the `MEU-TS2` and `MEU-TS3` rows in `docs/BUILD_PLAN.md` and `.agent/context/meu-registry.md`. | `docs/execution/plans/2026-04-11-pyright-test-cleanup/implementation-plan.md:13`, `docs/BUILD_PLAN.md:489-490`, `.agent/context/meu-registry.md:225-226` | Cite the `docs/BUILD_PLAN.md` MEU rows as the primary spec basis, and list `testing-strategy` / `01-domain-layer.md` as supporting canon only. | open |

---

## Checklist Results

### Plan Review (PR)

| Check | Result | Evidence |
|---|---|---|
| PR-1 Plan/task alignment | pass | Both files target `2026-04-11-pyright-test-cleanup` and the same MEUs (`MEU-TS2`, `MEU-TS3`). |
| PR-2 Not-started confirmation | pass | Plan status remains `draft`, task status remains `pending`, and no correlated implementation handoff exists yet. |
| PR-3 Task contract completeness | pass | Every task row includes task, owner, deliverable, validation, and status fields. |
| PR-4 Validation realism | fail | Findings 1-2: several commands are shell-invalid, and several others under-validate their stated work. |
| PR-5 Source-backed planning | pass | ACs and spec-sufficiency entries use allowed source labels; the remaining issue is source citation precision, not unsourced behavior invention. |
| PR-6 Handoff/corrections readiness | pass | Task rows 13-16 define handoff/reflection/metrics outputs, and corrections can route through `/planning-corrections`. |

### Design Review (DR)

| Check | Result | Evidence |
|---|---|---|
| Naming convention followed | pass | Plan folder, task file, and planned handoff names are consistent with project slug and date. |
| Template version present | pass | `template_version: "2.0"` present in both plan and task frontmatter. |
| YAML frontmatter well-formed | pass | Required frontmatter keys are present and syntactically valid. |

---

## Verdict

`approved` — All 3 findings resolved. Plan is ready for execution.

---

## Corrections Applied (2026-04-11)

| # | Finding | Resolution | Verified |
|---|---------|------------|----------|
| 1 | 5 task validation cells used forbidden `2>&1 \| Select-String` or bare commands | Rewrote all 5 cells to redirect-to-file pattern (`*> C:\Temp\zorivest\...`) | `rg "2>&1" task.md` → 0 matches |
| 2 | 4 validation cells under-validated scope | Widened search patterns: row 1 added `AccountType`, row 3 scans all 3 error classes across full `tests/`, row 4 added `reportAttributeAccessIssue`, row 5 added `reportReturnType`+`reportArgumentType` | Each cell now covers full declared scope |
| 3 | Plan header cited supporting canon as primary spec | Changed to `docs/BUILD_PLAN.md MEU-TS2 + MEU-TS3 rows (supporting canon: testing-strategy §1.2, §1.4; 01-domain-layer.md)` | `rg "Build Plan Section" implementation-plan.md` confirms |

**Files modified**: `task.md` (lines 19–23), `implementation-plan.md` (lines 6, 13–14).
**Cross-doc sweep**: No other files reference this plan's old header format — 0 cross-doc updates needed.

---

## Recheck (2026-04-11)

**Workflow**: `/planning-corrections` recheck
**Agent**: GPT-5.4 Codex

### Prior Pass Summary

| Finding | Prior Status | Recheck Result |
|---------|-------------|----------------|
| P0-invalid validation commands in `task.md` | fixed | ✅ Fixed |
| Under-scoped validation cells for Groups 2-4 and enum verification | fixed | ✅ Fixed |
| Header blurred primary spec vs supporting canon | fixed | ✅ Fixed |

### Commands Executed

| Command | Result |
|---------|--------|
| `rg -n '2>&1|Select-String|Measure-Object|Get-Content|\*>' docs/execution/plans/2026-04-11-pyright-test-cleanup/task.md` | Task rows 1-9 now use redirect-to-file commands; no `2>&1` usage remains |
| `rg -n '2>&1' docs/execution/plans/2026-04-11-pyright-test-cleanup/task.md` | 0 matches |
| `rg -n 'Build Plan Section|Status|source:|MEU-TS2|MEU-TS3|testing-strategy|01 §1.2|01 §1.4' docs/execution/plans/2026-04-11-pyright-test-cleanup/implementation-plan.md` | Header now cites `docs/BUILD_PLAN.md` MEU rows as primary spec and supporting canon separately |
| `rg -n 'Group 2|Group 3|Group 4|reportOptionalMemberAccess|reportOptionalSubscript|reportOperatorIssue|reportAttributeAccessIssue|reportCallIssue|reportReturnType|reportArgumentType|ColumnElement|SqlAlchemyUnitOfWork' docs/execution/plans/2026-04-11-pyright-test-cleanup/implementation-plan.md docs/execution/plans/2026-04-11-pyright-test-cleanup/task.md` | Validation cells now cover the error classes declared by Groups 2-4 |
| `rg -n -g '!*-critical-review.md' -g '!*-corrections*.md' -g '!*-recheck*.md' 'pyright-test-cleanup|pyright-enum-literals|pyright-entity-factories' .agent/context/handoffs` | No correlated implementation handoff exists; target remains in plan-review mode |

### Confirmed Fixes

- Finding 1 is resolved. [task.md](</P:/zorivest/docs/execution/plans/2026-04-11-pyright-test-cleanup/task.md:19>) through [task.md](</P:/zorivest/docs/execution/plans/2026-04-11-pyright-test-cleanup/task.md:27>) now use the redirect-to-file pattern, and `rg '2>&1'` returns no matches.
- Finding 2 is resolved. [task.md](</P:/zorivest/docs/execution/plans/2026-04-11-pyright-test-cleanup/task.md:19>) now checks both `TradeAction` and `AccountType`, while [task.md](</P:/zorivest/docs/execution/plans/2026-04-11-pyright-test-cleanup/task.md:21>) through [task.md](</P:/zorivest/docs/execution/plans/2026-04-11-pyright-test-cleanup/task.md:23>) cover the error classes declared in [implementation-plan.md](</P:/zorivest/docs/execution/plans/2026-04-11-pyright-test-cleanup/implementation-plan.md:98>), [implementation-plan.md](</P:/zorivest/docs/execution/plans/2026-04-11-pyright-test-cleanup/implementation-plan.md:122>), and [implementation-plan.md](</P:/zorivest/docs/execution/plans/2026-04-11-pyright-test-cleanup/implementation-plan.md:141>).
- Finding 3 is resolved. [implementation-plan.md](</P:/zorivest/docs/execution/plans/2026-04-11-pyright-test-cleanup/implementation-plan.md:13>) now distinguishes the `docs/BUILD_PLAN.md` MEU rows as primary spec from the supporting canon references.

### Remaining Findings

- None.

### Verdict

`approved` — The plan corrections are now backed by current file state. The target remains an unstarted execution plan, and the prior blocking review findings are closed.
