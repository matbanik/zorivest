# Task Handoff Template

## Task

- **Date:** 2026-03-07
- **Task slug:** domain-entities-ports-plan-critical-review
- **Owner role:** reviewer
- **Scope:** Review-only of `docs/execution/plans/2026-03-07-domain-entities-ports/implementation-plan.md` and `task.md` against workflow contracts, current MEU state, and Phase 1 source specs

## Inputs

- User request: Critically review the archived implementation plan and task using `.agent/workflows/critical-review-feedback.md`
- Specs/docs referenced:
  - `docs/execution/plans/2026-03-07-domain-entities-ports/implementation-plan.md`
  - `docs/execution/plans/2026-03-07-domain-entities-ports/task.md`
  - `.agent/workflows/critical-review-feedback.md`
  - `.agent/workflows/create-plan.md`
  - `.agent/workflows/execution-session.md`
  - `.agent/workflows/meu-handoff.md`
  - `docs/build-plan/01-domain-layer.md`
  - `docs/build-plan/domain-model-reference.md`
  - `docs/build-plan/build-priority-matrix.md`
  - `.agent/context/current-focus.md`
  - `.agent/context/meu-registry.md`
  - `AGENTS.md`
- Constraints:
  - Review only, no product fixes
  - Findings-first output
  - Use file state and workflow docs as source of truth

## Role Plan

1. orchestrator
2. tester
3. reviewer
4. coder
- Optional roles: researcher, guardrail

## Coder Output

- No product changes; review-only
- Changed files:
  - `.agent/context/handoffs/2026-03-07-domain-entities-ports-plan-critical-review.md`
- Commands run:
  - `apply_patch` to add this handoff
- Results:
  - Review handoff created

## Tester Output

- Commands run:
  - `Get-Content -Raw SOUL.md`
  - `Get-Content -Raw .agent/context/current-focus.md`
  - `Get-Content -Raw .agent/context/known-issues.md`
  - `Get-Content -Raw .agent/workflows/critical-review-feedback.md`
  - `Get-Content -Raw docs/execution/plans/2026-03-07-domain-entities-ports/implementation-plan.md`
  - `Get-Content -Raw docs/execution/plans/2026-03-07-domain-entities-ports/task.md`
  - `git status --short -- docs/execution/plans/2026-03-07-domain-entities-ports .agent/context/meu-registry.md .agent/workflows/create-plan.md docs/build-plan/01-domain-layer.md`
  - `rg -n "MEU-3|MEU-4|MEU-5|no tests needed|Type definitions only|bp01" .agent docs/execution/plans docs/build-plan tests packages`
  - `rg -n "^## Step 1\.2|^## Step 1\.4|^## Step 1\.5|^## Exit Criteria" docs/build-plan/01-domain-layer.md`
  - `rg -n "Money|PositionSize|Ticker|Conviction|ImageData|TradeRepository|ImageRepository|UnitOfWork|BrokerPort|BankImportPort|IdentifierResolverPort" docs/build-plan/01-domain-layer.md docs/build-plan/domain-model-reference.md`
  - Numbered `Get-Content` sweeps for:
    - `docs/build-plan/01-domain-layer.md`
    - `docs/build-plan/domain-model-reference.md`
    - `docs/build-plan/build-priority-matrix.md`
    - `.agent/workflows/create-plan.md`
    - `.agent/workflows/execution-session.md`
    - `.agent/workflows/validation-review.md`
    - `AGENTS.md`
    - `.agent/context/meu-registry.md`
    - `.agent/context/current-focus.md`
    - `docs/execution/reflections/2026-03-07-reflection.md`
    - `docs/execution/README.md`
- Pass/fail matrix:
  - Session-context load: PASS
  - Workflow/source-spec load: PASS
  - Claim-to-source alignment sweep: FAIL
  - Role/workflow contract sweep: FAIL
  - Artifact-path exactness sweep: FAIL
- Repro failures:
  - Dependency gating violated: plan starts downstream MEUs while `MEU-2` is still `ready_for_review`
  - Entity contract drifts from `domain-model-reference.md`
  - Plan/task omit explicit tester/reviewer role transitions
  - Post-project checklist puts archive step in the wrong phase and leaves key artifact paths implicit
- Coverage/test gaps:
  - Review-only session; no executable code changed
- Evidence bundle location:
  - `.agent/context/handoffs/2026-03-07-domain-entities-ports-plan-critical-review.md`
- FAIL_TO_PASS / PASS_TO_PASS result:
  - Not applicable
- Mutation score:
  - Not applicable
- Contract verification status:
  - `changes_required`

## Reviewer Output

- Findings by severity:
  1. **High:** `docs/execution/plans/2026-03-07-domain-entities-ports/implementation-plan.md:15-18`, `.agent/workflows/create-plan.md:57`, `.agent/context/current-focus.md:23-25`, `.agent/context/meu-registry.md:14-17` — the project is scoped off an unapproved dependency. The create-plan workflow only allows pending MEUs whose dependencies are satisfied by **approved** MEUs, but this plan knowingly proceeds while `MEU-2` is still `ready_for_review`. That makes the project invalid per workflow and risks cascading churn across entities, value objects, and ports if Codex sends enums back with changes.
  2. **High:** `docs/execution/plans/2026-03-07-domain-entities-ports/implementation-plan.md:50-55`, `docs/build-plan/domain-model-reference.md:16-33`, `docs/build-plan/domain-model-reference.md:100-111`, `docs/build-plan/01-domain-layer.md:150`, `docs/build-plan/01-domain-layer.md:412-449` — the MEU-3 FIC narrows core entity contracts below the domain model the build plan points to. `Account` is reduced to four fields, while the domain model includes `institution`, `currency`, `is_tax_advantaged`, `notes`, `sub_accounts`, `balance_source`, and `balance_snapshots`. `ImageAttachment` omits `id`, `owner_type`, `owner_id`, and `thumbnail`, and it weakens the `mime_type` contract from “always image/webp” to any string. If implemented as planned, Phase 1 will ship entities that do not match the documented domain model foundation.
  3. **Medium:** `docs/execution/plans/2026-03-07-domain-entities-ports/implementation-plan.md:77-83`, `docs/build-plan/01-domain-layer.md:29`, `docs/build-plan/01-domain-layer.md:521-526`, `AGENTS.md:51` — the MEU-4 FIC invents behavioral requirements that are not sourced in the build plan: negative-money rejection, ticker uppercasing, and specific immutability/normalization semantics. The current docs name the value objects but do not define these behaviors. Given the repo rule to ask on ambiguity, these should be explicit human decisions or sourced references, not silently promoted into acceptance criteria.
  4. **Medium:** `docs/execution/plans/2026-03-07-domain-entities-ports/implementation-plan.md:26-38`, `docs/execution/plans/2026-03-07-domain-entities-ports/task.md:5-37`, `AGENTS.md:60-61`, `docs/execution/README.md:25-29` — the plan drops the required role transition structure. Every task is owned by `coder`, with no explicit `orchestrator → coder → tester → reviewer` progression and no task for Codex validation trigger / reviewer handoff. That violates the documented plan contract and weakens execution accountability.
  5. **Medium:** `docs/execution/plans/2026-03-07-domain-entities-ports/implementation-plan.md:38`, `docs/execution/plans/2026-03-07-domain-entities-ports/task.md:32-36`, `.agent/workflows/create-plan.md:81-86`, `.agent/workflows/create-plan.md:93-106`, `.agent/workflows/execution-session.md:83-133` — several required post-project artifacts are underspecified or placed in the wrong phase. The plan never gives exact paths for the reflection file, metrics target, or `pomera_notes` title, despite the workflow requiring exact file paths and validation commands. The task checklist also tells the executor to “Archive plan to `docs/execution/plans/`” after project completion, but archival is supposed to happen immediately after approval and before execution; these artifacts are already archived in that location.
- Open questions:
  - For MEU-3, is `docs/build-plan/domain-model-reference.md` intended to be the authoritative field contract for `Account`, `BalanceSnapshot`, and `ImageAttachment`, or should Phase 1 intentionally ship a narrower subset with an explicit deferral note?
  - For MEU-4, which value-object behaviors are actually approved requirements versus planner assumptions?
- Verdict:
  - `changes_required`
- Residual risk:
  - If executed unchanged, the session can produce three kinds of avoidable drift at once: downstream rework from the unapproved enums dependency, domain-model mismatch in the entities layer, and audit/workflow drift because the execution artifacts are not fully specified.
- Anti-deferral scan result:
  - Findings are actionable and tied to specific workflow/spec lines; no placeholder-only objections.

## Guardrail Output (If Required)

- Safety checks:
  - Not required for this review-only docs task
- Blocking risks:
  - None beyond the review findings above
- Verdict:
  - Not applicable

## Approval Gate

- **Human approval required for merge/release/deploy:** yes
- **Approval status:** pending
- **Approver:**
- **Timestamp:**

## Final Summary

- Status:
  - Review complete; verdict is `changes_required`
- Next steps:
  - Re-scope the project only after `MEU-2` is validated or explicitly override the dependency rule with human approval
  - Re-derive the MEU-3 entity contract from `domain-model-reference.md` instead of the minimal example block alone
  - Either source or explicitly approve the MEU-4 value-object semantics before turning them into ACs
  - Revise plan/task artifacts to include explicit role transitions, exact artifact paths, and remove the already-completed archive step from post-project execution
