---
date: "2026-04-25"
review_mode: "plan"
target_plan: "docs/execution/plans/2026-04-25-pipeline-capabilities/implementation-plan.md"
verdict: "changes_required"
findings_count: 5
template_version: "2.1"
requested_verbosity: "standard"
agent: "GPT-5 Codex"
---

# Critical Review: 2026-04-25-pipeline-capabilities

> **Review Mode**: `plan`
> **Verdict**: `changes_required`

---

## Scope

**Target**: `docs/execution/plans/2026-04-25-pipeline-capabilities/implementation-plan.md`, `docs/execution/plans/2026-04-25-pipeline-capabilities/task.md`
**Review Type**: plan review
**Checklist Applied**: PR + DR

Canonical sources reviewed:

- `docs/build-plan/09d-pipeline-step-extensions.md`
- `docs/build-plan/09e-template-database.md`
- `docs/execution/plans/TASK-TEMPLATE.md`
- `docs/execution/plans/2026-04-25-pipeline-security-hardening/p2.5c_security_hardening_analysis.md`
- Current code shape for `StepContext`, `SendStep`, `step_registry.py`, and `pipeline_steps/__init__.py`

---

## Findings

| # | Severity | Finding | File:Line | Recommendation | Status |
|---|----------|---------|-----------|----------------|--------|
| 1 | High | `task.md` does not use the required task table contract. The canonical task template requires `Task`, `Owner`, `Deliverable`, `Validation`, and `Status` columns, but this task file is a nested checklist with no per-task owner, exact validation command, or deliverable cell. That violates the plan creation contract and prevents evidence-first completion tracking. | `docs/execution/plans/TASK-TEMPLATE.md:15`, `docs/execution/plans/2026-04-25-pipeline-capabilities/task.md:11` | Rewrite `task.md` into the canonical task table, with one row per executable task and exact validation commands/status cells. | open |
| 2 | High | PH6 explicitly defers the `email_templates` Alembic migration even though 09E requires a migration that creates the table and seeds two default templates, and the PH6/PH10 combined exit criteria still includes the migration. The carry-forward analysis also lists the migration as a PH6 infra file. This is silent scope narrowing that leaves the repository/UoW work unbacked by a real schema. | `docs/execution/plans/2026-04-25-pipeline-capabilities/implementation-plan.md:261`, `docs/build-plan/09e-template-database.md:125`, `docs/build-plan/09e-template-database.md:129`, `docs/build-plan/09e-template-database.md:380`, `docs/execution/plans/2026-04-25-pipeline-security-hardening/p2.5c_security_hardening_analysis.md:92` | Include the Alembic migration and seed behavior in PH6, or obtain/document an explicit source-backed decision that supersedes 09E. | open |
| 3 | High | PH7 defers `PolicyValidator` schema-v2 gating to PH9, but 09D says the `PolicyDocument` model, `policy_validator`, and all consumers must handle v1/v2 during the migration period. The spec also lists concrete `PolicyValidator` v1/v2 behavior and says `PolicyValidator` uses `schema_version` to gate step types and ref patterns. | `docs/execution/plans/2026-04-25-pipeline-capabilities/implementation-plan.md:262`, `docs/build-plan/09d-pipeline-step-extensions.md:317`, `docs/build-plan/09d-pipeline-step-extensions.md:350`, `docs/build-plan/09d-pipeline-step-extensions.md:367` | Move `PolicyValidator` updates and tests into PH7, or document a human-approved/spec update that changes the 09D migration contract. | open |
| 4 | High | PH6 plans `SendStep._resolve_body()` DB lookup without defining the injection path for `EmailTemplatePort`/repository into core runtime. Current `SendStep` resolves hardcoded templates by importing infra from core and reads only `template_engine` from `context.outputs`; the plan adds a core port and UoW property but does not specify how the port reaches `SendStep`, what context key is used, or fallback/error behavior when unavailable. The coder would have to invent architecture at implementation time. | `docs/execution/plans/2026-04-25-pipeline-capabilities/implementation-plan.md:157`, `docs/execution/plans/2026-04-25-pipeline-capabilities/implementation-plan.md:183`, `docs/execution/plans/2026-04-25-pipeline-capabilities/implementation-plan.md:188`, `packages/core/src/zorivest_core/pipeline_steps/send_step.py:241`, `packages/core/src/zorivest_core/pipeline_steps/send_step.py:269`, `packages/core/src/zorivest_core/pipeline_steps/send_step.py:280` | Add a source-backed design for dependency injection into `SendStep` and tests for DB hit, DB miss, missing port, and no core-to-infra import regression. | open |
| 5 | Medium | PH7 marks `PolicyDocument JSON` as an external boundary but sets extra-field policy to `No extra="forbid" (existing design)` without a source-backed exception. AGENTS.md requires `extra="forbid"` or a documented exception for external-input MEUs; preserving the existing default is not enough unless the plan names the source and tests the behavior. | `docs/execution/plans/2026-04-25-pipeline-capabilities/implementation-plan.md:204` | Either set `PolicyDocument` to forbid unknown top-level fields and add tests, or document a source-backed exception with explicit unknown-field behavior. | open |

---

## Checklist Results

### Plan Review (PR)

| Check | Result | Evidence |
|-------|--------|----------|
| PR-1 Plan/task alignment | fail | Same MEU order, but `task.md` lacks the required task table/validation columns. |
| PR-2 Not-started confirmation | pass | `task.md` is unchecked; file-state sweep found planned new code/test files absent; `git status --short` shows only the untracked plan folder. |
| PR-3 Task contract completeness | fail | `TASK-TEMPLATE.md:15-20` requires table columns; target `task.md` uses nested checklist entries. |
| PR-4 Validation realism | fail | Implementation plan has exact command blocks, but task rows do not carry exact validation commands per task. |
| PR-5 Source-backed planning | fail | PH6 migration deferral and PH7 `PolicyValidator` deferral conflict with cited specs; PH7 extra-field exception is unsourced. |
| PR-6 Handoff/corrections readiness | pass | Post-MEU deliverables name four handoffs and route plan fixes through `/plan-corrections`. |

### Docs Review (DR)

| Check | Result | Evidence |
|-------|--------|----------|
| DR-1 Claim-to-state match | fail | Plan claims all behaviors are resolved from Spec/Local Canon, but migration and `PolicyValidator` deferrals contradict source docs. |
| DR-2 Residual old terms | pass | No rename/move term migration was in scope. |
| DR-3 Downstream references updated | fail | Task contract format is not aligned with `TASK-TEMPLATE.md`; PH6/PH7 scope does not align with 09E/09D. |
| DR-4 Verification robustness | fail | Missing `PolicyValidator` tests, migration tests, and template-port injection tests would not catch the main contract gaps. |
| DR-5 Evidence auditability | pass | Review sweeps used line-numbered `rg` output and targeted file reads. |
| DR-6 Cross-reference integrity | fail | 09D/09E cross-references conflict with plan out-of-scope section. |
| DR-7 Evidence freshness | pass | File-state and git status sweeps were run during this review. |
| DR-8 Completion vs residual risk | pass | Plan is draft/unstarted and makes no completion claim. |

---

## Commands Executed

```powershell
rg -n "Alembic|migration|PolicyValidator|Registered in|step_registry|__init__|All 11 tests|All 8 tests|PH6 \||17 tests|20 tests|41 tests|Template Database|template CRUD" docs\execution\plans\2026-04-25-pipeline-capabilities\implementation-plan.md docs\execution\plans\2026-04-25-pipeline-capabilities\task.md docs\build-plan\09d-pipeline-step-extensions.md docs\build-plan\09e-template-database.md docs\execution\plans\2026-04-25-pipeline-security-hardening\p2.5c_security_hardening_analysis.md *> C:\Temp\zorivest\plan-review-rg.txt; Get-Content C:\Temp\zorivest\plan-review-rg.txt
```

```powershell
& { foreach ($p in @('docs/execution/plans/2026-04-25-pipeline-capabilities/task.md','.agent/context/handoffs/2026-04-25-pipeline-capabilities-plan-critical-review.md','packages/core/src/zorivest_core/pipeline_steps/query_step.py','packages/core/src/zorivest_core/pipeline_steps/compose_step.py','tests/unit/test_query_step.py','tests/unit/test_compose_step.py','tests/unit/test_secure_jinja.py','tests/unit/test_schema_v2_migration.py','alembic/versions/xxxx_add_email_templates_table.py')) { "$p`t$(Test-Path $p)" } } *> C:\Temp\zorivest\plan-review-file-state.txt; Get-Content C:\Temp\zorivest\plan-review-file-state.txt
```

Result summary: target `task.md` exists; canonical review handoff did not exist before this review; planned new code/test/migration files checked in the sweep were absent.

```powershell
git status --short *> C:\Temp\zorivest\plan-review-git-status.txt; Get-Content C:\Temp\zorivest\plan-review-git-status.txt
```

Result summary: only `?? docs/execution/plans/2026-04-25-pipeline-capabilities/`.

```powershell
rg -n 'def _resolve_body|EMAIL_TEMPLATES|template_engine|body_template|SqlAlchemyUnitOfWork|email_template|template_port|model_config|extra="forbid"|PolicyDocument JSON' packages\core\src\zorivest_core\pipeline_steps\send_step.py packages\core\src\zorivest_core\domain\pipeline.py docs\execution\plans\2026-04-25-pipeline-capabilities\implementation-plan.md docs\execution\plans\2026-04-25-pipeline-capabilities\task.md *> C:\Temp\zorivest\plan-review-injection-boundary.txt; Get-Content C:\Temp\zorivest\plan-review-injection-boundary.txt
```

---

## Verdict

`changes_required` — the plan is not ready for implementation. The major blockers are unsourced scope cuts against 09D/09E, a non-compliant `task.md` contract, and an unresolved PH6 injection design that would force implementation-time invention.

---

## Follow-Up Actions

1. Run `/plan-corrections` for `docs/execution/plans/2026-04-25-pipeline-capabilities/`.
2. Convert `task.md` to the canonical task table with exact validation commands.
3. Reconcile PH6 with 09E by adding the Alembic migration/default-template seed contract or documenting an explicit superseding decision.
4. Reconcile PH7 with 09D by adding `PolicyValidator` v2 migration work/tests or documenting an explicit superseding decision.
5. Add a concrete template-port injection contract for `SendStep`.
6. Source or fix the PH7 `PolicyDocument` extra-field policy.

---

## Residual Risk

This was a plan-only review. No implementation tests were run because the workflow target is unstarted and review-only. Additional risks may appear once `/plan-corrections` updates the plan, especially around migration ordering and core/infra dependency boundaries.

---

## Recheck (2026-04-25)

**Workflow**: `/plan-critical-review` recheck
**Agent**: GPT-5 Codex
**Verdict**: `changes_required`

### Prior Findings Status

| Finding | Prior Status | Recheck Result |
|---------|--------------|----------------|
| F1 task.md missing canonical task table | open | Fixed: `task.md:15-18` now has the canonical table columns and rows 1-34 are all unchecked. |
| F2 PH6 Alembic migration deferred against 09E | open | Fixed: AC-6.21/6.22, migration file entry, and spec sufficiency rows are present at `implementation-plan.md:160-182`; stale out-of-scope migration deferral is gone. |
| F3 PH7 PolicyValidator deferred against 09D | open | Fixed: AC-7.13 through AC-7.17, `policy_validator.py`, and spec sufficiency rows are present at `implementation-plan.md:256-279`; stale out-of-scope deferral is gone. |
| F4 SendStep DB lookup lacks port injection design | open | Fixed: AC-6.23 through AC-6.25 plus a concrete `template_port` injection design are present at `implementation-plan.md:162-226`. |
| F5 PolicyDocument extra-field policy unsourced | open | Fixed: PH7 boundary inventory now sets `extra="forbid"` with AGENTS.md source and AC-7.18 covers unknown-field rejection at `implementation-plan.md:236-261`. |

### New Findings

| # | Severity | Finding | File:Line | Recommendation | Status |
|---|----------|---------|-----------|----------------|--------|
| 6 | High | Several `task.md` validation commands are not P0 redirect-safe. Rows 3, 7, 10, and 13 run `uv run python -c ...` without `*> C:\Temp\zorivest\...`; rows 15 and 33 use bare `Test-Path`; row 32 pipes `Get-ChildItem` into `Measure-Object`. The task table is now structurally compliant, but these exact validation commands would violate the mandatory redirect-to-file pattern if copied into terminal execution. | `docs/execution/plans/2026-04-25-pipeline-capabilities/task.md:21`, `docs/execution/plans/2026-04-25-pipeline-capabilities/task.md:25`, `docs/execution/plans/2026-04-25-pipeline-capabilities/task.md:28`, `docs/execution/plans/2026-04-25-pipeline-capabilities/task.md:31`, `docs/execution/plans/2026-04-25-pipeline-capabilities/task.md:33`, `docs/execution/plans/2026-04-25-pipeline-capabilities/task.md:50`, `docs/execution/plans/2026-04-25-pipeline-capabilities/task.md:51` | Rewrite validation commands so every non-skipped terminal command redirects all streams to `C:\Temp\zorivest\...` and then reads the receipt file. Avoid pipe-based measurement in the task command or wrap it in a redirected script block. | open |
| 7 | Medium | PH6 test counts are internally inconsistent: the implementation plan says "MEU-PH6 Tests (25 tests)" while the task table and file summary enumerate 24 tests (`8 + 3 + 8 + 5`). This will make red/green evidence ambiguous. | `docs/execution/plans/2026-04-25-pipeline-capabilities/implementation-plan.md:330`, `docs/execution/plans/2026-04-25-pipeline-capabilities/task.md:27`, `docs/execution/plans/2026-04-25-pipeline-capabilities/task.md:36`, `docs/execution/plans/2026-04-25-pipeline-capabilities/implementation-plan.md:202`, `docs/execution/plans/2026-04-25-pipeline-capabilities/implementation-plan.md:203` | Normalize the PH6 expected count to one value across AC/file summaries, verification plan, and task rows. | open |
| 8 | Low | Plan/task status metadata is inconsistent. `implementation-plan.md` frontmatter is `reviewed`, but the visible status line still says `draft`; `task.md` frontmatter remains `draft`. The user-facing correction note claimed `draft -> reviewed`, so the file state does not match the claim. | `docs/execution/plans/2026-04-25-pipeline-capabilities/implementation-plan.md:6`, `docs/execution/plans/2026-04-25-pipeline-capabilities/implementation-plan.md:14`, `docs/execution/plans/2026-04-25-pipeline-capabilities/task.md:5` | Set visible and frontmatter statuses consistently, or keep them draft intentionally and update the correction claim. | open |

### Checklist Results

| Check | Result | Evidence |
|-------|--------|----------|
| PR-1 Plan/task alignment | fail | Prior scope alignment issues fixed, but PH6 expected test count differs between plan and task. |
| PR-2 Not-started confirmation | pass | `task.md` rows remain `[ ]`; `git status --short` shows only the untracked review file and untracked plan folder. |
| PR-3 Task contract completeness | pass | Canonical columns exist at `task.md:17`; rows include owner, deliverable, validation, and status. |
| PR-4 Validation realism | fail | Some validation commands are not safe exact commands under the project P0 terminal contract. |
| PR-5 Source-backed planning | pass | Prior unsourced/contradictory PH6, PH7, injection, and extra-field issues were corrected. |
| PR-6 Handoff/corrections readiness | pass | Post-MEU rows include handoffs, reflection, metrics, session memory, and audits. |

### Commands Executed

```powershell
rg -n 'status:|Status|AC-6\.2[1-5]|AC-7\.1[3-8]|Alembic migration|PolicyValidator|template_port|extra="forbid"|MEU-PH6 Tests|24 tests|25 tests|test_send_step_db_lookup|test_email_template_repository|Out of Scope|deferred|task table|Task Table|uv run python -c|Test-Path|Get-ChildItem|\| Measure-Object' docs\execution\plans\2026-04-25-pipeline-capabilities\implementation-plan.md docs\execution\plans\2026-04-25-pipeline-capabilities\task.md *> C:\Temp\zorivest\plan-review-recheck-rg.txt; Get-Content C:\Temp\zorivest\plan-review-recheck-rg.txt
```

```powershell
git status --short *> C:\Temp\zorivest\plan-review-recheck-git-status.txt; Get-Content C:\Temp\zorivest\plan-review-recheck-git-status.txt
```

Result summary: implementation remains unstarted; only `.agent/context/handoffs/2026-04-25-pipeline-capabilities-plan-critical-review.md` and `docs/execution/plans/2026-04-25-pipeline-capabilities/` are untracked.

### Verdict

`changes_required` — the original five findings are fixed, but the corrected task contract still contains P0-unsafe validation commands and two consistency issues. Run `/plan-corrections` again for F6-F8 before implementation.

---

## Recheck (2026-04-25, Pass 2)

**Workflow**: `/plan-critical-review` recheck
**Agent**: GPT-5 Codex
**Verdict**: `approved`

### Prior Pass Summary

| Finding | Prior Status | Recheck Result |
|---------|--------------|----------------|
| F6 P0-unsafe validation commands | open | Fixed. Previously bare `uv run python -c`, `Test-Path`, and `Get-ChildItem` validations now write receipts under `C:\Temp\zorivest\` where required. Evidence: `task.md:21`, `task.md:25`, `task.md:28`, `task.md:31`, `task.md:33`, `task.md:50`, `task.md:51`. |
| F7 PH6 test count mismatch | open | Fixed. Implementation plan and task table now consistently use 24 PH6 tests. Evidence: `implementation-plan.md:330`, `task.md:27`, `task.md:36`. |
| F8 status metadata mismatch | open | Fixed. Plan frontmatter, visible plan status, and task frontmatter all read `reviewed`. Evidence: `implementation-plan.md:6`, `implementation-plan.md:14`, `task.md:5`. |

### New Findings

No new findings.

### Checklist Results

| Check | Result | Evidence |
|-------|--------|----------|
| PR-1 Plan/task alignment | pass | PH4-PH7 scope and PH6/PH7 test counts align between plan and task. |
| PR-2 Not-started confirmation | pass | `task.md` rows remain `[ ]`; `git status --short` shows only the review handoff and plan folder as untracked. |
| PR-3 Task contract completeness | pass | `task.md:17` has the canonical table columns, and all task rows include owner, deliverable, validation, and status. |
| PR-4 Validation realism | pass | Validation commands are specific and receipt-oriented enough for the plan stage. |
| PR-5 Source-backed planning | pass | Prior PH6/PH7 scope, port injection, and `extra="forbid"` issues remain corrected. |
| PR-6 Handoff/corrections readiness | pass | Post-MEU rows include handoffs, reflection, metrics, session memory, and audits. |

### Commands Executed

```powershell
rg -n 'status:|> \*\*Status\*\*|MEU-PH6 Tests|24 tests|25 tests|uv run pyright packages/core/|uv run ruff check packages/core/|Get-Content docs/execution/metrics.md|Test-Path|Get-ChildItem|uv run python -c|\*> C:\\Temp\\zorivest' docs\execution\plans\2026-04-25-pipeline-capabilities\implementation-plan.md docs\execution\plans\2026-04-25-pipeline-capabilities\task.md *> C:\Temp\zorivest\plan-review-recheck2-rg.txt; Get-Content C:\Temp\zorivest\plan-review-recheck2-rg.txt
```

```powershell
git status --short *> C:\Temp\zorivest\plan-review-recheck2-git-status.txt; Get-Content C:\Temp\zorivest\plan-review-recheck2-git-status.txt
```

Result summary: implementation remains unstarted; only `.agent/context/handoffs/2026-04-25-pipeline-capabilities-plan-critical-review.md` and `docs/execution/plans/2026-04-25-pipeline-capabilities/` are untracked.

### Verdict

`approved` — the plan is ready for the user approval gate before execution. Residual risk is limited to normal implementation risk; this was a plan-only review and no implementation tests were run.
