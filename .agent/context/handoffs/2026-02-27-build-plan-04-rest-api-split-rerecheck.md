# Task Handoff Template

## Task

- **Date:** 2026-02-27
- **Task slug:** build-plan-04-rest-api-split-rerecheck
- **Owner role:** reviewer
- **Scope:** Re-check current `docs/build-plan/04*.md` split state for remaining inconsistencies.

## Inputs

- User request: "run re-check to see what issues are still present"
- Files reviewed:
  - `docs/build-plan/04-rest-api.md`
  - `docs/build-plan/04a-api-trades.md`
  - `docs/build-plan/04b-api-accounts.md`
  - `docs/build-plan/04c-api-auth.md`
  - `docs/build-plan/04d-api-settings.md`
  - `docs/build-plan/04e-api-analytics.md`
  - `docs/build-plan/04f-api-tax.md`
  - `docs/build-plan/04g-api-system.md`
  - `docs/build-plan/05b-mcp-zorivest-diagnostics.md`
  - `docs/build-plan/05c-mcp-trade-analytics.md`
  - `docs/build-plan/05d-mcp-trade-planning.md`
  - `docs/build-plan/05e-mcp-market-data.md`
  - `docs/build-plan/05f-mcp-accounts.md`
  - `docs/build-plan/05h-mcp-tax.md`
  - `docs/build-plan/06c-gui-planning.md`
  - `docs/build-plan/06e-gui-scheduling.md`
  - `docs/build-plan/06f-gui-settings.md`
  - `docs/build-plan/10-service-daemon.md`

## Role Plan

1. orchestrator
2. tester
3. reviewer

## Coder Output

- Changed files:
  - `.agent/context/handoffs/2026-02-27-build-plan-04-rest-api-split-rerecheck.md`
- Design notes:
  - Review-only pass. No product doc edits made.
- Commands run:
  - Router parity sweep (APIRouter definitions vs include_router manifest)
  - 04-link existence sweep (`Test-Path` over markdown links)
  - Stale section reference sweep (`Step 4.*`, `§4.*`)
  - Endpoint namespace sweeps (`/health`, `/service/*`, `/system/*`)
  - Consumer Notes tool-name parity sweeps vs Phase 5 tool specs
  - Route contract table spot-checks

## Tester Output

- Pass/fail matrix:
  - Exhaustive router include manifest: **PASS**
  - 04-file link integrity: **PASS**
  - Stale section-reference drift (`Step 4.*`, `§4.*`): **PASS**
  - Endpoint namespace consistency (`/api/v1/health` + `/api/v1/service/*`): **PASS**
  - Round-trip route contract presence in Phase 4: **PASS**
  - MCP guard pre-unlock contract alignment: **PASS**
  - Consumer Notes tool-name/file parity: **FAIL**
  - Route Contract Registry row accuracy: **FAIL**

## Reviewer Output

- Findings by severity:

  - **High:** Consumer Notes still reference non-canonical/non-existent MCP tool IDs for documented ownership.
    - Trades notes list `get_trade`, `update_trade`, `delete_trade` as MCP tools in [04a-api-trades.md](../../docs/build-plan/04a-api-trades.md):303, but there are no corresponding Phase 5 tool specs (`### \`get_trade\``, `### \`update_trade\``, `### \`delete_trade\`` not found across `05*.md`).
    - Accounts notes list `import_csv`, `import_pdf` in [04b-api-accounts.md](../../docs/build-plan/04b-api-accounts.md):154, while canonical specs are `import_broker_csv` and `import_broker_pdf` in [05f-mcp-accounts.md](../../docs/build-plan/05f-mcp-accounts.md):126,158.
    - Impact: cross-phase tool mapping is still ambiguous/misleading for implementers.

  - **Medium:** Route Contract Registry has at least one concrete path mismatch versus route specs and MCP usage.
    - Registry row uses `/api/v1/analytics/pfof` in [04-rest-api.md](../../docs/build-plan/04-rest-api.md):160.
    - Actual route and MCP dependency use `/api/v1/analytics/pfof-report` in [04e-api-analytics.md](../../docs/build-plan/04e-api-analytics.md):35 and [05c-mcp-trade-analytics.md](../../docs/build-plan/05c-mcp-trade-analytics.md):346.
    - Impact: single-source registry is currently inaccurate on a live contract row.

  - **Medium:** GUI consumer mapping in Route Contract Registry is inconsistent with current Phase 6 split.
    - `plans.create` maps to GUI `06b` in [04-rest-api.md](../../docs/build-plan/04-rest-api.md):143, while trade plan CRUD is documented under Phase 6c in [06c-gui-planning.md](../../docs/build-plan/06c-gui-planning.md):90-94.
    - Analytics rows map to `06e` in [04-rest-api.md](../../docs/build-plan/04-rest-api.md):157-160, but `06e` is scheduling (`06e-gui-scheduling.md`:1).
    - Impact: registry consumer column cannot be trusted as authoritative until mapping convention is corrected.

- Open questions:
  - Should Consumer Notes list only canonical Phase 5 tool IDs, or allow endpoint-oriented operation labels when no tool exists?
  - For Route Contract Registry GUI consumer column, should values be file IDs (`06a/06b/...`) or concrete file links only?

- Verdict:
  - **changes_required**

- Residual risk:
  - The new single-source Route Contract Registry is structurally good, but incorrect rows will now propagate bad assumptions faster unless parity checks are added.

## Approval Gate

- **Human approval required for merge/release/deploy:** yes
- **Approval status:** pending
- **Approver:**
- **Timestamp:**

## Final Summary

- Remaining issues are now concentrated in naming/mapping precision, not architecture.
- Core split mechanics (router exhaustiveness, link integrity, route namespace consistency, guard contract, and round-trip presence) are all passing.