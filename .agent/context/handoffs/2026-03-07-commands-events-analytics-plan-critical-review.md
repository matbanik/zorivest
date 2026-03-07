# Task Handoff Template

## Task

- **Date:** 2026-03-07
- **Task slug:** commands-events-analytics-plan-critical-review
- **Owner role:** reviewer
- **Scope:** Review-only of `docs/execution/plans/2026-03-07-commands-events-analytics/implementation-plan.md` and `task.md` against current repo state, planning workflow contracts, and downstream analytics docs

## Inputs

- User request: review plan only for `commands-events-analytics`, using the explicit plan files
- Specs/docs referenced:
  - `docs/execution/plans/2026-03-07-commands-events-analytics/implementation-plan.md`
  - `docs/execution/plans/2026-03-07-commands-events-analytics/task.md`
  - `.agent/workflows/critical-review-feedback.md`
  - `.agent/workflows/create-plan.md`
  - `.agent/workflows/execution-session.md`
  - `docs/build-plan/01-domain-layer.md`
  - `docs/build-plan/03-service-layer.md`
  - `docs/build-plan/04e-api-analytics.md`
  - `docs/build-plan/05c-mcp-trade-analytics.md`
  - `docs/build-plan/build-priority-matrix.md`
  - `docs/build-plan/domain-model-reference.md`
  - `.agent/context/meu-registry.md`
  - `.agent/context/current-focus.md`
  - `AGENTS.md`
- Constraints:
  - Review only, no fixes
  - Findings-first output
  - Use file state and canonical docs as source of truth

## Role Plan

1. orchestrator
2. tester
3. reviewer
- Optional roles: researcher, guardrail

## Coder Output

- No product changes; review-only
- Changed files:
  - `.agent/context/handoffs/2026-03-07-commands-events-analytics-plan-critical-review.md`
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
  - `Get-Content -Raw docs/execution/plans/2026-03-07-commands-events-analytics/implementation-plan.md`
  - `Get-Content -Raw docs/execution/plans/2026-03-07-commands-events-analytics/task.md`
  - `git status --short -- packages/core tests/unit .agent/context/meu-registry.md docs/execution/plans/2026-03-07-commands-events-analytics`
  - `rg --files packages/core/src/zorivest_core tests/unit .agent/context | rg "application/(commands|queries|dtos)\.py|domain/events\.py|domain/analytics/|test_commands_dtos\.py|test_events\.py|test_analytics\.py|meu-registry\.md"`
  - `rg -n "CreateTrade|AttachImage|CreateAccount|UpdateBalance|GetTrade|ListTrades|TradeCreated|BalanceUpdated|ImageAttached|PlanCreated|analytics|strategy.py|expectancy|sqn|TradeReport|strategy breakdown|pure analytics|commands|queries|dtos" docs/build-plan/01-domain-layer.md docs/build-plan/domain-model-reference.md`
  - `rg -n "build-priority-matrix|Commands & DTOs|Events|Pure analytics functions|Nothing|P2.75|58e|68.3e" docs _inspiration .agent`
  - `rg -n "CreatePlan|TradePlan|PlanCreated|TradeReport|GetImage|ListImages|GetAccount|ListAccounts|CreateAccount|AttachImage|UpdateBalance|GetTrade|ListTrades" docs/build-plan/01-domain-layer.md docs/build-plan/domain-model-reference.md docs/BUILD_PLAN.md`
  - `rg -n "round-trip|expectancy|SQN|strategy breakdown|strategy name|tags|TradeReport|analytics/results|ExpectancyResult|SQNResult|StrategyResult|Kelly|Van Tharp|drawdown|cost of free" docs/build-plan/01-domain-layer.md docs/build-plan/03-service-layer.md docs/build-plan/04e-api-analytics.md docs/build-plan/05c-mcp-trade-analytics.md docs/build-plan/domain-model-reference.md`
  - `rg -n "spec-sufficiency section per MEU|A task table with: task, owner_role, deliverable, validation, status|Feature Intent Contract \(FIC\) per MEU|Best practice|Exact validation commands" .agent/workflows/create-plan.md AGENTS.md`
  - `rg -n "Role transitions must be explicit|Spec|Local Canon|Research-backed|Human-approved" AGENTS.md`
  - `rg -n "class ExpectancyResult|class SQNResult|class StrategyResult|profit_factor|kelly_fraction|trade_count|mean_r|std_r|win_rate: Decimal|strategy_name|total_pnl" docs/build-plan/03-service-layer.md`
  - `rg -n "MEU-3/4/5 dependency status|ready_for_review|Role progression per MEU|all FAIL|all PASS|anti-placeholder|Stop Conditions|Do NOT modify existing|Save session state" docs/execution/plans/2026-03-07-commands-events-analytics/implementation-plan.md docs/execution/plans/2026-03-07-commands-events-analytics/task.md .agent/context/meu-registry.md`
  - `rg -n "TODO\|FIXME\|NotImplementedError" docs/execution/plans/2026-03-07-commands-events-analytics/implementation-plan.md`
- Pass/fail matrix:
  - Explicit-target plan load: PASS
  - Not-started confirmation: PASS
  - Cross-doc analytics contract sweep: FAIL
  - Source-traceability sweep: FAIL
  - Role/validation contract sweep: FAIL
  - Repo-state freshness sweep: FAIL
- Repro failures:
  - Analytics strategy contract in the plan does not match the API/MCP/build-plan meaning of "strategy breakdown"
  - Analytics result dataclasses drift from the downstream `domain.analytics.results` contract already specified in Phase 3
  - Multiple FIC criteria use forbidden unsourced labels (`best practice`, `Pattern`, `DDD convention`, `CQRS convention`)
  - Execution roles and placeholder-scan validations are underspecified for an executable plan
  - Dependency baseline note is stale relative to the current MEU registry
- Coverage/test gaps:
  - Review-only session; no code executed or changed
- Evidence bundle location:
  - `.agent/context/handoffs/2026-03-07-commands-events-analytics-plan-critical-review.md`
- FAIL_TO_PASS / PASS_TO_PASS result:
  - Not applicable
- Mutation score:
  - Not applicable
- Contract verification status:
  - `changes_required`

## Reviewer Output

- Findings by severity:
  1. **High:** `docs/execution/plans/2026-03-07-commands-events-analytics/implementation-plan.md:188-189` defines `breakdown_by_strategy(trades)` as grouping by `instrument`, but the downstream analytics contract consistently defines this surface as strategy-name reporting sourced from review metadata/tags. Evidence: `docs/build-plan/04e-api-analytics.md:44` ("P&L breakdown by strategy name"), `docs/build-plan/05c-mcp-trade-analytics.md:425-430` ("Break P&L down by strategy tags" / "strategy name from TradeReport tags"), and `docs/build-plan/domain-model-reference.md:50-58` (TradeReport carries `tags`). If implemented as planned, MEU-8 will ship a materially different meaning for "strategy breakdown" than the later API and MCP consumers expect.
  2. **High:** `docs/execution/plans/2026-03-07-commands-events-analytics/implementation-plan.md:161-163` invents analytics result shapes that already drift from the later canonical `domain.analytics.results` contract. The plan uses `loss_rate`, `payoff_ratio`, `kelly_pct`, `sample_size`, `avg_r`, `std_r`, and `avg_pnl`, while `docs/build-plan/03-service-layer.md:89-145` specifies `profit_factor`, `kelly_fraction`, `trade_count`, `mean_r`, `std_r`, and a `StrategyResult` with no `avg_pnl`. The types also drift (`float` in the plan vs `Decimal` in Phase 3). Because Phase 3 imports these exact domain result classes, this is pre-implementation contract drift, not harmless detail.
  3. **Medium:** The plan does not satisfy the required source-backed planning contract. `implementation-plan.md:64-103`, `implementation-plan.md:124-138`, and `implementation-plan.md:154-197` go straight into FICs, but `.agent/workflows/create-plan.md:124-125` requires a spec-sufficiency section per MEU plus FIC criteria annotated as `Spec`, `Local Canon`, `Research-backed`, or `Human-approved`. Instead the plan uses forbidden labels such as `best practice` (`implementation-plan.md:75-76`, `implementation-plan.md:80`, `implementation-plan.md:132`, `implementation-plan.md:173`, `implementation-plan.md:182`, `implementation-plan.md:190`), `CQRS convention` (`implementation-plan.md:82`), `DDD convention` (`implementation-plan.md:137`), and `Pattern` (`implementation-plan.md:196-197`). That violates `.agent/workflows/create-plan.md:83-84` and `AGENTS.md:62`.
  4. **Medium:** The execution contract is incomplete for a runnable plan. `implementation-plan.md:44-58` and `task.md:1-50` do not include explicit `orchestrator` or `reviewer` tasks even though `AGENTS.md:60-61` requires plan tasks with explicit role progression `orchestrator → coder → tester → reviewer`. The verification commands also contain a false-failing placeholder scan: `implementation-plan.md:272`, `implementation-plan.md:279`, and `implementation-plan.md:286` run bare `rg "TODO|FIXME|NotImplementedError" ...`, which exits non-zero when there are no matches, so the quality gate fails on the success condition unless wrapped.
  5. **Low:** The repo-state baseline in the plan is stale. `implementation-plan.md:15` says MEU-3/4/5 are `ready_for_review`, but `.agent/context/meu-registry.md:15-17` marks all three `approved`. The plan is genuinely unstarted, but this note no longer reflects current dependency state and should be updated before execution to avoid carrying an obsolete risk assumption forward.
- Open questions:
  - Is MEU-8 intentionally redefining "strategy breakdown" to mean instrument-level grouping for Phase 1, or should the plan defer that function until strategy metadata exists and keep only result types plus clearly source-backed analytics?
  - Should Phase 1 align its analytics result dataclasses to the Phase 3 names now, or is the intention to accept a planned rename later with explicit migration notes?
- Verdict:
  - `changes_required`
- Residual risk:
  - If executed unchanged, this plan is likely to produce throwaway analytics code and handoffs that will need correction once service/API/MCP work starts, because the current plan bakes drift into both function semantics and result contracts.
- Anti-deferral scan result:
  - Findings are specific, source-backed, and actionable; no placeholder-only objections.

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
  - Route fixes through `.agent/workflows/planning-corrections.md`
  - Reconcile MEU-8 semantics with `04e-api-analytics.md`, `05c-mcp-trade-analytics.md`, and `03-service-layer.md` before implementation starts
  - Replace unsourced FIC criteria with `Spec`, `Local Canon`, `Research-backed`, or `Human-approved` provenance
  - Add explicit orchestrator/reviewer steps and correct the placeholder-scan validation commands
