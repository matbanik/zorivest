# Task Handoff Template

## Task

- **Date:** 2026-03-26
- **Task slug:** 2026-03-27-account-gui-plan-critical-review
- **Owner role:** reviewer
- **Scope:** Plan review only for `docs/execution/plans/2026-03-27-account-gui/`

## Inputs

- User request: Review `critical-review-feedback.md` against `docs/execution/plans/2026-03-27-account-gui/task.md` and `docs/execution/plans/2026-03-27-account-gui/implementation-plan.md`
- Specs/docs referenced:
  - `docs/execution/plans/2026-03-27-account-gui/implementation-plan.md`
  - `docs/execution/plans/2026-03-27-account-gui/task.md`
  - `.agent/workflows/critical-review-feedback.md`
  - `.agent/workflows/create-plan.md`
  - `docs/build-plan/06d-gui-accounts.md`
  - `docs/build-plan/06-gui.md`
  - `docs/build-plan/06a-gui-shell.md`
  - `.agent/docs/emerging-standards.md`
  - `ui/package.json`
  - `ui/vitest.config.ts`
  - `ui/playwright.config.ts`
  - `ui/src/renderer/src/registry/commandRegistry.ts`
- Constraints:
  - Review-only workflow; no product or plan-file edits allowed
  - Canonical output path only

## Role Plan

1. orchestrator
2. tester
3. reviewer
- Optional roles: researcher, guardrail

## Coder Output

- No product changes; review-only

## Tester Output

- Commands run:
  - `Get-Content SOUL.md`
  - `Get-Content .agent/context/current-focus.md`
  - `Get-Content .agent/context/known-issues.md`
  - `Get-Content .agent/skills/terminal-preflight/SKILL.md`
  - `Get-Content .agent/workflows/critical-review-feedback.md`
  - `Get-Content docs/execution/plans/2026-03-27-account-gui/task.md`
  - `Get-Content docs/execution/plans/2026-03-27-account-gui/implementation-plan.md`
  - `rg -n "007-2026-03-27-account-gui-bp06ds35a1|MEU-71a|account-gui" .agent/context/handoffs docs/execution/plans .agent/context/meu-registry.md`
  - `Get-ChildItem .agent/context/handoffs/*.md | Where-Object { $_.Name -notmatch '(critical-review|corrections|recheck)' } | Sort-Object LastWriteTime -Descending | Select-Object -First 20 FullName,LastWriteTime,Name`
  - `git status --short -- docs/execution/plans/2026-03-27-account-gui .agent/context/handoffs`
  - `rg -n "accounts-page|account-list|add-account-btn|AccountContext|usePersistedState|useCreateAccount|useUpdateAccount|useDeleteAccount|useBalanceHistory|BalanceHistory|AccountReviewWizard" ui/src`
  - `rg --files ui/src/renderer/src`
  - `rg --files ui/tests`
  - `rg -n "Account Review|start-review|account dropdown|selected account|activeAccountId|Select account|accounts dropdown|Trade Planner" docs/build-plan ui/src/renderer/src`
  - `Get-Content ui/package.json`
  - `Get-Content ui/playwright.config.ts`
  - `Get-Content ui/vitest.config.ts`
  - `"root package.json exists: $(Test-Path package.json)"`
- Pass/fail matrix:
  - Mode detection: PASS (`task.md` unchecked, no correlated work handoff in scope)
  - Canon correlation: PASS (explicit user-provided plan folder)
  - Plan/task contract check: FAIL
  - Validation realism check: FAIL
  - Source-traceability check: FAIL
  - Handoff naming check: FAIL
- Repro failures:
  - Root JS workspace absent (`package.json` missing at repo root), while plan commands are written as root-relative JS commands
- Coverage/test gaps:
  - Plan does not schedule command-palette/AppShell verification for Account Review
  - Task list omits E2E/build execution needed for Wave 2 evidence
- Evidence bundle location:
  - This handoff plus cited file/line references below
- FAIL_TO_PASS / PASS_TO_PASS result:
  - Not applicable; review-only
- Mutation score:
  - Not applicable; review-only
- Contract verification status:
  - `changes_required`

## Reviewer Output

- Scope reviewed:
  - Plan review mode for `docs/execution/plans/2026-03-27-account-gui/`
  - Reviewed `implementation-plan.md` + `task.md` against canonical planning rules and cited GUI canon
  - No implementation handoff exists yet; `task.md` is fully unchecked, so this remains a pre-execution plan review
- Findings by severity:
  - **High:** The plan omits required command-palette/AppShell wiring for Account Review, so it does not cover the full documented contract. The spec says the wizard "can be triggered from the Accounts page, command palette (`Account Review` action), or programmatically via MCP" in `docs/build-plan/06d-gui-accounts.md:83-85`, and the shell spec defines `action:review` as `openAccountReview()` in `docs/build-plan/06a-gui-shell.md:220-221`. The emerging GUI standard requires modal-opening global actions to route through `AppShell` via custom events in `.agent/docs/emerging-standards.md:162-188`. But the plan only adds `AccountReviewWizard.tsx` and a `"Start Review"` button inside `AccountsHome.tsx` with no `commandRegistry.ts` or `AppShell.tsx` work item in `docs/execution/plans/2026-03-27-account-gui/implementation-plan.md:83-139`, while the current registry still leaves `action:review` as a console stub in `ui/src/renderer/src/registry/commandRegistry.ts:94-100`. Executing this plan as written would still leave the command-palette entry broken.
  - **Medium:** The validation commands are not reproducible as written because they target the wrong working directory and omit the required E2E build step. The plan’s verification block runs `npx vitest run src/features/accounts/ src/context/__tests__/`, `npx playwright test persistence.test.ts`, and `npx tsc --noEmit` from the repo root in `docs/execution/plans/2026-03-27-account-gui/implementation-plan.md:201-220`, but the actual JS workspace lives under `ui/`, with scripts/config in `ui/package.json:1-16`, `ui/vitest.config.ts:1-21`, and `ui/playwright.config.ts:1-36`; there is no root `package.json` (`Test-Path package.json -> False`). `06-gui.md` also explicitly requires a build before every E2E run in `docs/build-plan/06-gui.md:413-417`, but neither the verification plan nor `task.md` includes `npm run build` or an E2E execution step. As written, the plan’s validation section is not strong enough to prove Wave 2 completion.
  - **Medium:** `task.md` does not satisfy the planning contract required by `create-plan.md`. The workflow requires a task table with `task`, `owner_role`, `deliverable`, `validation`, and `status`, plus an explicit `docs/BUILD_PLAN.md` review/update task in both plan files in `.agent/workflows/create-plan.md:116-129`. Instead, `docs/execution/plans/2026-03-27-account-gui/task.md:1-27` is only a checkbox list, with no owner role, no deliverable column, and no exact validation commands for the `BUILD_PLAN.md` update. That means the execution artifact cannot be audited against the required planning schema before implementation begins.
  - **Low:** The planned handoff filename uses a stale sequence number and will break the repo’s sequencing convention. The plan hard-codes `007-2026-03-27-account-gui-bp06ds35a1.md` in `docs/execution/plans/2026-03-27-account-gui/implementation-plan.md:156` and `docs/execution/plans/2026-03-27-account-gui/task.md:25`, but the current sequenced handoffs already run through `093-2026-03-26-calculator-accounts-bp06hs1.md` in the handoff listing. Per `.agent/workflows/create-plan.md:211-227`, the next handoff must increment from the highest existing sequence, so this plan should not ship with a hard-coded `007` filename.
- Open questions:
  - None. The required fixes are local to the plan and canonical docs already resolve the missing behavior.
- Verdict:
  - `changes_required`
- Residual risk:
  - If the plan enters execution unchanged, the team is likely to deliver a working Accounts page but still miss the command-palette review flow, produce weak or non-reproducible validation evidence, and create an incorrectly sequenced handoff artifact.
- Anti-deferral scan result:
  - No placeholder TODO/FIXME issues inside the reviewed plan files, but required planning metadata is missing.

## Guardrail Output (If Required)

- Safety checks:
  - Review-only scope honored
- Blocking risks:
  - Missing command-palette/AppShell scope would leave documented GUI behavior incomplete
- Verdict:
  - `changes_required`

## Approval Gate

- **Human approval required for merge/release/deploy:** yes
- **Approval status:** pending
- **Approver:**
- **Timestamp:**

## Final Summary

- Status:
  - `changes_required`
- Next steps:
  - Apply fixes through `/planning-corrections`
  - Update the plan to include Account Review global-action wiring, executable UI validation commands, a contract-compliant `task.md`, and a correct handoff sequence
