# Task Handoff Template

## Task

- **Date:** 2026-02-28
- **Task slug:** docs-build-plan-service-layer-recheck-validation
- **Owner role:** orchestrator
- **Scope:** Validation re-check to confirm whether prior service-layer docs issues were corrected across `docs/build-plan`.

## Inputs

- User request: "run re-check to validate that the issues have been corrected"
- Specs/docs referenced:
  - `.agent/workflows/critical-review-feedback.md`
  - Previous review handoff: `.agent/context/handoffs/2026-02-28-docs-build-plan-service-layer-recheck-critical-review.md`
  - `docs/build-plan/04-rest-api.md`, `04a..04g`, `05f-mcp-accounts.md`, `03-service-layer.md`, `mcp-planned-readiness.md`
- Constraints:
  - Review-only (no fixes)
  - Deterministic parity checks with line evidence

## Role Plan

1. orchestrator
2. coder
3. tester
4. reviewer
- Optional roles: researcher, guardrail

## Coder Output

- Changed files:
  - `.agent/context/handoffs/2026-02-28-docs-build-plan-service-layer-recheck-validation.md` (new review handoff)
- Design notes:
  - No product doc edits applied.
- Commands run:
  - N/A (review-only)
- Results:
  - Re-check evidence captured.

## Tester Output

- Commands run:
  - `git status --short -- docs/build-plan`
  - `rg -n "TradePlanService\.create\(\)|TradePlanService|get_trade_plan_service|get_trade_report_service|get_round_trip_service|get_expectancy_service|get_drawdown_service|get_eq_service|get_pfof_service|get_strategy_service|get_sqn_service|get_cost_service|get_ai_review_service|get_excursion_service|get_options_grouping_service|get_mistake_service|get_ledger_service" docs/build-plan`
  - `rg -n "identifiers/resolve|identifiers_router|resolve_identifiers" docs/build-plan/04-rest-api.md docs/build-plan/04b-api-accounts.md docs/build-plan/05f-mcp-accounts.md`
  - `rg -n "APIRouter\(|app\.include_router\(|Route Contract Registry|single source of truth|every REST endpoint" docs/build-plan/04-rest-api.md docs/build-plan/04a-api-trades.md docs/build-plan/04b-api-accounts.md docs/build-plan/04c-api-auth.md docs/build-plan/04d-api-settings.md docs/build-plan/04e-api-analytics.md docs/build-plan/04f-api-tax.md docs/build-plan/04g-api-system.md`
  - `rg -n "GET /api/v1/settings/resolved|POST /api/v1/settings/reset|GET /api/v1/config/export|POST /api/v1/config/import|POST /api/v1/backups|GET /api/v1/backups|POST /api/v1/backups/verify|POST /api/v1/backups/restore|DELETE /api/v1/settings/\{key\}" docs/build-plan/04-rest-api.md docs/build-plan/04d-api-settings.md docs/build-plan/02a-backup-restore.md`
  - Endpoint parity script (`04a..04g` decorators vs `04-rest-api` registry): `defined=78 registry=88 missing_after_param_normalization=0`
  - Delegated route parity script (`04d` delegated table vs `04-rest-api` registry): `delegated_rows=9 missing_in_04_registry=0`
  - Include/definition parity script: `defined_count=21 included_count=22 missing_defs_count=1` (`identifiers_router`)
  - Registry unmatched-to-subfile/delegated script: `unmatched_not_in_subfiles_or_delegated=1` (`identifiers.resolve`)

- Pass/fail matrix:
  - DR-1 Claim-to-state match: **PASS (major prior gaps corrected)**
  - DR-2 Residual old terms: **PARTIAL**
  - DR-3 Downstream references updated: **PASS (for previously flagged route/delegation gaps)**
  - DR-4 Verification robustness: **PASS**
  - DR-5 Evidence auditability: **PASS**

- Repro failures:
  - `identifiers_router` included in `04-rest-api.md` but not defined in split owner files.
  - `identifiers.resolve` registry row has no corresponding route decorator in `04a..04g` and is not in delegated `04d` list.

- Coverage/test gaps:
  - Docs-level validation only; no markdown linter/link checker executed.

- Evidence bundle location:
  - Inline command outputs + this handoff.

- FAIL_TO_PASS / PASS_TO_PASS result:
  - Not applicable (review-only).

- Mutation score:
  - Not applicable (review-only).

- Contract verification status:
  - **Mostly passed** with one unresolved endpoint ownership/spec gap and one naming-consistency gap.

## Reviewer Output

- Findings by severity:

  - **Medium — `identifiers.resolve` remains incompletely specified in split Phase 04 docs.**
    - Included/imported in hub: `docs/build-plan/04-rest-api.md:103`, `:116`, registry row at `:176`.
    - But split owner file only provides a one-line table mention, no router code block/decorator:
      - `docs/build-plan/04b-api-accounts.md:146-150`
    - Parity evidence:
      - `included_without_definition: identifiers_router`
      - `unmatched_not_in_subfiles_or_delegated=1` (`identifiers.resolve`)

  - **Low — Two non-consolidated dependency names remain in analytics routes.**
    - `docs/build-plan/04e-api-analytics.md:63` uses `get_ai_review_service`
    - `docs/build-plan/04e-api-analytics.md:82` uses `get_options_grouping_service`
    - This is minor drift versus consolidated naming direction from `docs/build-plan/03-service-layer.md:27-36`.

- Corrections confirmed (previous blockers closed):
  - Phase 04 registry now includes all route decorators from `04a..04g` (0 missing).
  - Delegated Phase 2A settings/config/backup routes are now present in Phase 04 registry (0 missing).
  - `TradePlanService.create()` stale reference removed from `mcp-planned-readiness.md`.
  - Path parameter naming drift in core registry rows has been corrected (`{exec_id}`, `{broker_id}`, etc.).

- Open questions:
  - Should `identifiers.resolve` be fully specified with a concrete `identifiers_router` code block in `04b-api-accounts.md`, or moved to a dedicated new split file (for example `04h-api-identifiers.md`)?

- Verdict:
  - **changes_required (minor follow-up)**

- Residual risk:
  - Low-to-medium documentation risk: one endpoint currently lacks a full owner-spec block despite being treated as canonical in registry and MCP dependencies.

- Anti-deferral scan result:
  - Only small, targeted follow-up remains.

## Guardrail Output (If Required)

- Safety checks: N/A
- Blocking risks: N/A
- Verdict: N/A

## Approval Gate

- **Human approval required for merge/release/deploy:** yes
- **Approval status:** pending
- **Approver:**
- **Timestamp:**

## Final Summary

- Status:
  - Re-check complete. Most previously reported issues are corrected.
- Next steps:
  - 1) Add explicit `identifiers_router` route spec (code block + endpoint decorator) in Phase 04 split docs and keep it reflected in `04-rest-api.md` registry.
  - 2) Optionally normalize remaining `get_ai_review_service` / `get_options_grouping_service` dependency names to consolidated service naming.
