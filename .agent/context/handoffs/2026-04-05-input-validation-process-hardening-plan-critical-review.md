# Task Handoff Template

## Task

- **Date:** 2026-04-05
- **Task slug:** input-validation-process-hardening-plan-critical-review
- **Owner role:** reviewer
- **Scope:** Plan review of `docs/execution/plans/2026-04-05-input-validation-process-hardening/` triggered from `/critical-review-feedback`

## Inputs

- User request: Review the linked workflow, `implementation-plan.md`, and `task.md`
- Specs/docs referenced:
  - `AGENTS.md`
  - `.agent/workflows/critical-review-feedback.md`
  - `.agent/workflows/planning-corrections.md`
  - `.agent/skills/quality-gate/SKILL.md`
  - `docs/execution/plans/2026-04-05-input-validation-process-hardening/implementation-plan.md`
  - `docs/execution/plans/2026-04-05-input-validation-process-hardening/task.md`
  - `.agent/context/handoffs/096-2026-04-05-create-update-input-validation-review-bp04+05+06+08+09.md`
- Constraints:
  - Review-only pass; no corrections to plan or instruction files in this session
  - Canonical review file for this plan folder
  - Findings must be evidence-backed and severity-ranked

## Role Plan

1. orchestrator
2. tester
3. reviewer

## Coder Output

- Changed files:
  - `.agent/context/handoffs/2026-04-05-input-validation-process-hardening-plan-critical-review.md`
- Design notes / ADRs referenced:
  - None
- Commands run:
  - `rg --files .agent/context/handoffs`
- Results:
  - No product or process-document changes; review-only

## Tester Output

- Commands run:
  - `rg --files .agent/context/handoffs`
- Additional evidence gathered:
  - Read `AGENTS.md`, the target `implementation-plan.md`, `task.md`, `.agent/workflows/planning-corrections.md`, and `.agent/skills/quality-gate/SKILL.md`
  - Verified current repo state against the plan's claimed corrections
- Pass/fail matrix:
  - Presence of claimed `.agent` edits: PASS
  - Build-plan portability / no-`.agent` link rule: FAIL
  - Boundary-enforcement strength vs claimed hardening: FAIL
  - Task artifact contract compliance: FAIL
- Repro failures:
  - `implementation-plan.md` still embeds `file:///p:/zorivest/.agent/...` links inside a build-plan artifact
  - The quality-gate "boundary validation audit" is only a narrow grep and does not enforce the broader contract the plan claims
  - `task.md` remains a checklist rather than a task contract with `task`, `owner_role`, `deliverable`, `validation`, and `status`
- Coverage/test gaps:
  - The review verified documentation state only; no executable validation proves that the new process catches weak create/update boundary handling end-to-end
- Evidence bundle location:
  - Inline in this handoff
- FAIL_TO_PASS / PASS_TO_PASS result:
  - Not applicable; review-only
- Mutation score:
  - Not run
- Contract verification status:
  - `changes_required`

## Reviewer Output

- Findings by severity:
  - **High:** The plan artifact violates the repo's own cross-doc portability rule by linking build-plan content into `.agent/`. `implementation-plan.md` uses `file:///p:/zorivest/.agent/...` links for the source handoff and for most modified instruction files, for example the source link at `docs/execution/plans/2026-04-05-input-validation-process-hardening/implementation-plan.md:6` and the workflow/skill/doc links throughout `docs/execution/plans/2026-04-05-input-validation-process-hardening/implementation-plan.md:31`, `docs/execution/plans/2026-04-05-input-validation-process-hardening/implementation-plan.md:39`, `docs/execution/plans/2026-04-05-input-validation-process-hardening/implementation-plan.md:51`, `docs/execution/plans/2026-04-05-input-validation-process-hardening/implementation-plan.md:70`, and `docs/execution/plans/2026-04-05-input-validation-process-hardening/implementation-plan.md:82`. That conflicts with the hard rule in `planning-corrections.md` that "Build plan docs must not link into `.agent/`" (`.agent/workflows/planning-corrections.md:198`). The plan should restate the governing decisions in portable plan text instead of depending on agent-workspace links.
  - **High:** The plan overstates enforcement of boundary hardening. It says future MEUs will "automatically enforce boundary validation through the updated workflows, skills, and checklists" (`docs/execution/plans/2026-04-05-input-validation-process-hardening/implementation-plan.md:17`) and presents quality-gate check #11 as a "boundary validation audit for touched write surfaces" (`docs/execution/plans/2026-04-05-input-validation-process-hardening/implementation-plan.md:72`). But the actual quality-gate implementation is only `rg "dict\[str, Any\].*request\|Body\(\)" <touched-route-files>` (`.agent/skills/quality-gate/SKILL.md:53`). That grep can catch one narrow raw-dict route pattern, but it does not enforce the create/update parity, extra-field rejection, constrained write-schema coverage, or unvalidated update-path checks that the same plan claims to harden at `docs/execution/plans/2026-04-05-input-validation-process-hardening/implementation-plan.md:20` through `docs/execution/plans/2026-04-05-input-validation-process-hardening/implementation-plan.md:24` and `docs/execution/plans/2026-04-05-input-validation-process-hardening/implementation-plan.md:76`. The quality gate therefore does not yet match the contract the plan says is now encoded.
  - **Medium:** `task.md` does not satisfy the project task-artifact contract. Project rules require every plan task to have `task`, `owner_role`, `deliverable`, `validation`, and `status` (`AGENTS.md:154`), but the reviewed file remains a flat checklist with `[x]` bullets only (`docs/execution/plans/2026-04-05-input-validation-process-hardening/task.md:3` through `docs/execution/plans/2026-04-05-input-validation-process-hardening/task.md:30`). That weakens ownership and evidence traceability, especially because the same file marks all twelve corrections complete without a per-task deliverable or validation field.
- Open questions:
  - Should this project keep a separate `task.md` at all for docs-only process hardening, or should it be converted into the standard contract-table format used by other plan folders?
  - Should boundary validation enforcement remain workflow/checklist-based only, or should the quality gate gain stronger concrete checks for extra-field policy, negative tests, and create/update parity claims?
- Verdict:
  - `changes_required`
- Residual risk:
  - If accepted as written, this plan will appear to have hardened create/update boundary handling more than it actually has. Future work could satisfy the new wording while still missing the same runtime validation gaps identified in the underlying review.
- Anti-deferral scan result:
  - No product-code placeholders introduced in this review. Findings require `/planning-corrections` on the plan artifacts before approval.

## Guardrail Output (If Required)

- Safety checks:
  - Review-only session; no destructive operations
- Blocking risks:
  - None beyond the findings above
- Verdict:
  - Not required

## Approval Gate

- **Human approval required for merge/release/deploy:** yes
- **Approval status:** pending
- **Approver:** human
- **Timestamp:** pending

## Final Summary

- Status:
  - `changes_required`
- Next steps:
  - Remove `.agent` links from the build-plan artifact and restate the governing rules in portable plan text
  - Strengthen the quality-gate boundary audit so it actually checks the contract this plan claims to enforce
  - Convert `task.md` into the required task-contract format or explicitly align the workflow to allow a different format

---

## Recheck Update — 2026-04-05

### Scope

- Rechecked the revised `implementation-plan.md`, `task.md`, and `quality-gate/SKILL.md` against the three findings from the initial review.
- Verified file state rather than relying on the prior `Corrections Applied` claim in this handoff.

### Resolved Since Prior Pass

- The build-plan artifact no longer links into `.agent/`. `implementation-plan.md` now cites the source handoff as plain text and uses plain basenames for the modified instruction files instead of `file:///p:/zorivest/.agent/...` links.
- The quality-gate boundary audit is now materially stronger and the plan language is narrower. `implementation-plan.md` now says future MEUs are subject to mandatory boundary validation review and explicitly states runtime enforcement still requires Category A code changes. `quality-gate/SKILL.md` now documents a four-pattern audit covering raw dict params, reconstruction/update bypass patterns, missing `extra="forbid"`, and kwargs bypass.
- `task.md` now uses contract tables with `Task`, `Owner Role`, `Deliverable`, `Validation`, and `Status` columns, which resolves the prior checklist-only structure issue.

### Findings

- No remaining findings from the prior pass.

### Verdict

`approved`

### Residual Risk

- This plan now accurately presents itself as process hardening, not runtime remediation. The underlying Category A boundary-validation defects remain deferred to implementation work, so approval here does not imply the codebase write paths are fixed.

---

## Corrections Applied — 2026-04-05

### Findings Resolved

| # | Finding | Fix Applied | Verification |
|---|---------|-------------|-------------|
| F1 (High) | `implementation-plan.md` uses 12 `file:///p:/zorivest/.agent/...` links | Rewrote entire file — all `.agent/` links replaced with plain basenames, source link converted to inline text description | `rg "file:///p:/zorivest/\.agent" implementation-plan.md` → 0 matches |
| F2 (High) | Quality-gate check #11 is only a narrow grep | Expanded to 4-pattern multi-check audit (11a–11d): raw dict params, unvalidated reconstruction, missing `extra="forbid"`, kwargs bypass. Tempered plan claim from "automatically enforce" to "subject to mandatory review" | `rg "Check 11\|11a:\|11b:\|11c:\|11d:" .agent/skills/quality-gate/SKILL.md` → 5 matches |
| F3 (Medium) | `task.md` is flat checklist, not contract-table format | Converted to 3 tables with `Task`, `Owner Role`, `Deliverable`, `Validation`, `Status` columns per `AGENTS.md:154` | `rg "Owner Role" task.md` → 3 matches (3 table sections) |

### Verdict

All 3 findings resolved. Corrections complete.
