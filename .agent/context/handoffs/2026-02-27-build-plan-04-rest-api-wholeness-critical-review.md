# Task Handoff Template

## Task

- **Date:** 2026-02-27
- **Task slug:** build-plan-04-rest-api-wholeness-critical-review
- **Owner role:** orchestrator
- **Scope:** Critical review of `docs/build-plan/04-rest-api.md` completeness against Phase 03 service contracts and Phase 05 MCP tool contracts.

## Inputs

- User request: Verify that Phase 04 is complete for upstream/downstream calls (Phase 03 -> Phase 04 -> Phase 05) and identify missing components that will break arrival at this layer.
- Specs/docs referenced:
  - `docs/build-plan/03-service-layer.md`
  - `docs/build-plan/04-rest-api.md`
  - `docs/build-plan/05-mcp-server.md`
  - `docs/build-plan/05a-mcp-zorivest-settings.md`
  - `docs/build-plan/05b-mcp-zorivest-diagnostics.md`
  - `docs/build-plan/05c-mcp-trade-analytics.md`
  - `docs/build-plan/05d-mcp-trade-planning.md`
  - `docs/build-plan/05h-mcp-tax.md`
  - `docs/build-plan/05j-mcp-discovery.md`
  - `docs/build-plan/mcp-planned-readiness.md`
  - `docs/build-plan/mcp-tool-index.md`
  - `.agent/workflows/critical-review-feedback.md`
- Constraints:
  - Review-only session (no product fixes).
  - Findings-first output with line-referenced evidence.
  - Do not revert unrelated existing local edits.

## Role Plan

1. orchestrator
2. tester
3. reviewer
4. coder (not used; no fix request)
- Optional roles: researcher, guardrail

## Coder Output

- Changed files:
  - `.agent/context/handoffs/2026-02-27-build-plan-04-rest-api-wholeness-critical-review.md` (this review artifact only)
- Design notes:
  - No product/documentation contract changes applied in this session.
- Commands run:
  - `git status --short -- docs/build-plan`
  - `rg --files docs/build-plan`
  - `rg -n ...` sweeps for `/api/v1/`, `fetch(...)`, route headings, service classes
  - Targeted line-range reads for Phase 03/04/05 docs
- Results:
  - Evidence collected for contract drift and missing route coverage.

## Tester Output

- Commands run:
  - `rg -n "\b(GET|POST|PUT|PATCH|DELETE)\s+/api/v1/" docs/build-plan`
  - `rg -o -I '/api/v1/[A-Za-z0-9_{}\-/\?=&]+' docs/build-plan/04-rest-api.md | Sort-Object -Unique`
  - `rg -o -I '/api/v1/[A-Za-z0-9_{}\-/\?=&]+' docs/build-plan/05*.md | Sort-Object -Unique`
  - `rg -n "confirmation-tokens|excursion|options-strategy|trade-plans|tax/lots|auth/unlock|mcp-guard" docs/build-plan/*.md`
  - Targeted file line reads for evidence sections
- Pass/fail matrix:
  - Claim-to-state checks: **FAIL** (multiple cross-file drifts)
  - Residual reference checks: **FAIL** (`confirmation-tokens` architecture contradiction)
  - Cross-file consistency checks: **FAIL** (schema/method mismatches)
  - Verification quality checks: **FAIL** (`mcp-planned-readiness` overstates completion)
- Repro failures:
  - Not runtime-executed; failures are specification-level mismatches with deterministic line evidence.
- Coverage/test gaps:
  - No explicit contract verification sweeps in docs ensuring 05 tool schemas match 04 request schemas/methods.
  - No explicit Phase 04 route stubs/tests for some Phase 05 analytics tool endpoints.
- Evidence bundle location:
  - Terminal command history + this handoff references.
- FAIL_TO_PASS / PASS_TO_PASS result:
  - Not applicable (review-only session).
- Mutation score:
  - Not applicable (review-only session).
- Contract verification status:
  - **Failed**.

## Reviewer Output

- Findings by severity:
  - **High:** Tax tool HTTP method mismatch will fail at runtime.
    - `get_tax_lots` sends `POST` in [05h-mcp-tax.md](p:/zorivest/docs/build-plan/05h-mcp-tax.md:184) while dependency text says `GET` in [05h-mcp-tax.md](p:/zorivest/docs/build-plan/05h-mcp-tax.md:208) and Phase 04 defines `GET /tax/lots` in [04-rest-api.md](p:/zorivest/docs/build-plan/04-rest-api.md:982).
  - **High:** Tax request-schema drift between Phase 05 and Phase 04 causes 422/contract break risk.
    - Action/cost-basis enums differ: [05h-mcp-tax.md](p:/zorivest/docs/build-plan/05h-mcp-tax.md:22), [05h-mcp-tax.md](p:/zorivest/docs/build-plan/05h-mcp-tax.md:26) vs [04-rest-api.md](p:/zorivest/docs/build-plan/04-rest-api.md:925), [04-rest-api.md](p:/zorivest/docs/build-plan/04-rest-api.md:929).
    - Filing status enum differs: [05h-mcp-tax.md](p:/zorivest/docs/build-plan/05h-mcp-tax.md:80) vs [04-rest-api.md](p:/zorivest/docs/build-plan/04-rest-api.md:934).
    - Quarterly estimation enum differs: [05h-mcp-tax.md](p:/zorivest/docs/build-plan/05h-mcp-tax.md:224) vs [04-rest-api.md](p:/zorivest/docs/build-plan/04-rest-api.md:997).
    - `find_wash_sales` treats `account_id` as optional in Phase 05: [05h-mcp-tax.md](p:/zorivest/docs/build-plan/05h-mcp-tax.md:130), but Phase 04 requires it: [04-rest-api.md](p:/zorivest/docs/build-plan/04-rest-api.md:938).
    - `sort_by` value set differs (`date_acquired`/`holding_period` vs `acquired_date`/`gain_loss` set): [05h-mcp-tax.md](p:/zorivest/docs/build-plan/05h-mcp-tax.md:179), [04-rest-api.md](p:/zorivest/docs/build-plan/04-rest-api.md:986).
  - **High:** Trade plan schema drift between Phase 05 and Phase 04.
    - Phase 05 uses uppercase enums and array conditions: [05d-mcp-trade-planning.md](p:/zorivest/docs/build-plan/05d-mcp-trade-planning.md:64), [05d-mcp-trade-planning.md](p:/zorivest/docs/build-plan/05d-mcp-trade-planning.md:65), [05d-mcp-trade-planning.md](p:/zorivest/docs/build-plan/05d-mcp-trade-planning.md:71), [05d-mcp-trade-planning.md](p:/zorivest/docs/build-plan/05d-mcp-trade-planning.md:72).
    - Phase 04 expects lowercase enums, string `conditions`, required `timeframe`: [04-rest-api.md](p:/zorivest/docs/build-plan/04-rest-api.md:169), [04-rest-api.md](p:/zorivest/docs/build-plan/04-rest-api.md:170), [04-rest-api.md](p:/zorivest/docs/build-plan/04-rest-api.md:175), [04-rest-api.md](p:/zorivest/docs/build-plan/04-rest-api.md:176).
  - **High:** Two Phase 05 specified analytics tools target endpoints not specified in Phase 04.
    - `enrich_trade_excursion` calls `/analytics/excursion/{trade_exec_id}` in [05c-mcp-trade-analytics.md](p:/zorivest/docs/build-plan/05c-mcp-trade-analytics.md:261); no corresponding route in Phase 04 analytics routes list [04-rest-api.md](p:/zorivest/docs/build-plan/04-rest-api.md:760) through [04-rest-api.md](p:/zorivest/docs/build-plan/04-rest-api.md:809).
    - `detect_options_strategy` calls `/analytics/options-strategy` in [05c-mcp-trade-analytics.md](p:/zorivest/docs/build-plan/05c-mcp-trade-analytics.md:552); no corresponding Phase 04 route in the same section.
    - This also breaks expected lift from existing service-layer contracts (`ExcursionService`, `OptionsGroupingService`) in [03-service-layer.md](p:/zorivest/docs/build-plan/03-service-layer.md:162) and [03-service-layer.md](p:/zorivest/docs/build-plan/03-service-layer.md:208).
  - **High:** Discovery confirmation-token architecture is self-contradictory across phases.
    - Phase 04 explicitly says discovery/toolset tools do **not** call Python REST endpoints in [04-rest-api.md](p:/zorivest/docs/build-plan/04-rest-api.md:659).
    - Phase 05j and Phase 05 hub claim/use a REST endpoint `POST /api/v1/confirmation-tokens` in [05j-mcp-discovery.md](p:/zorivest/docs/build-plan/05j-mcp-discovery.md:210), [05j-mcp-discovery.md](p:/zorivest/docs/build-plan/05j-mcp-discovery.md:249), [05-mcp-server.md](p:/zorivest/docs/build-plan/05-mcp-server.md:875).
  - **Medium:** Completion/readiness documents currently provide false confidence.
    - `mcp-planned-readiness.md` asserts full completion in [mcp-planned-readiness.md](p:/zorivest/docs/build-plan/mcp-planned-readiness.md:3) and [mcp-planned-readiness.md](p:/zorivest/docs/build-plan/mcp-planned-readiness.md:5), but conflicts above are still present.

- Open questions:
  - Should `get_confirmation_token` be fully MCP-local (TypeScript-only), or should Phase 04 add a canonical REST endpoint?
  - For excursion/options strategy: should Phase 04 add endpoints now, or should those Phase 05 tools be downgraded from `Specified` until routes are added?
  - Which schema is canonical for tax/trade-plan contracts: current Phase 04 Pydantic models or current Phase 05 Zod specs?

- Verdict:
  - **changes_required**

- Residual risk:
  - If unresolved, expected immediate failures at Phase 05 integration: `405 Method Not Allowed`, `422 validation errors`, and missing-route failures for specified tools.

- Anti-deferral scan result:
  - Found premature “complete/specified” declarations while required cross-layer contracts are still inconsistent.

## Guardrail Output (If Required)

- Safety checks:
  - Not required for this docs-only review.
- Blocking risks:
  - Contract-level drift in destructive-operation confirmation and financial-tool request schemas.
- Verdict:
  - Not executed.

## Approval Gate

- **Human approval required for merge/release/deploy:** yes
- **Approval status:** pending
- **Approver:**
- **Timestamp:**

## Final Summary

- Status:
  - Review completed; no product changes applied.
- Next steps:
  - Align canonical contracts (Phase 04 routes/schemas vs Phase 05 tool schemas).
  - Resolve confirmation-token architecture contradiction.
  - Update readiness/index docs after contract fixes so status claims match file state.
