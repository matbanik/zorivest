# Task Handoff Template

## Task

- **Date:** 2026-02-27
- **Task slug:** build-plan-04-rest-api-split-recheck-after-q
- **Owner role:** reviewer
- **Scope:** Re-check `docs/build-plan/04*.md` split quality after user decisions:
  - Q1: `04-rest-api.md` must be exhaustive for router includes
  - Q2: follow established cross-doc patterns
  - Q3: minimize duplication (optimize, not copy)

## Inputs

- User request: "run re-check to see what issues are still present" with Q1/Q2/Q3 decisions.
- Files reviewed:
  - `docs/build-plan/04-rest-api.md`
  - `docs/build-plan/04a-api-trades.md`
  - `docs/build-plan/04b-api-accounts.md`
  - `docs/build-plan/04c-api-auth.md`
  - `docs/build-plan/04d-api-settings.md`
  - `docs/build-plan/04e-api-analytics.md`
  - `docs/build-plan/04f-api-tax.md`
  - `docs/build-plan/04g-api-system.md`
  - `docs/build-plan/05a-mcp-zorivest-settings.md`
  - `docs/build-plan/05b-mcp-zorivest-diagnostics.md`
  - `docs/build-plan/05c-mcp-trade-analytics.md`
  - `docs/build-plan/05d-mcp-trade-planning.md`
  - `docs/build-plan/05e-mcp-market-data.md`
  - `docs/build-plan/05f-mcp-accounts.md`
  - `docs/build-plan/05h-mcp-tax.md`
  - `docs/build-plan/06f-gui-settings.md`
  - `docs/build-plan/10-service-daemon.md`

## Role Plan

1. orchestrator
2. tester
3. reviewer

## Coder Output

- Changed files:
  - `.agent/context/handoffs/2026-02-27-build-plan-04-rest-api-split-recheck-after-q.md`
- Design notes:
  - Review-only session, no product-doc edits.
- Commands run:
  - `git status --short -- docs/build-plan .agent/context/handoffs`
  - Router parity sweep (`APIRouter` defs vs `include_router(...)` manifest)
  - 04-link existence sweep via `Test-Path`
  - Endpoint namespace consistency sweeps (`/health`, `/service/*`, `/system/*`)
  - Tool-name parity sweeps between 04 Consumer Notes and 05 tool specs
  - Residual stale section reference sweeps (`Step 4.*`, `§4.*`)

## Tester Output

- Pass/fail matrix:
  - Q1 exhaustive router includes: **PASS**
    - `04-rest-api.md` include list now matches all routers defined in `04a`-`04g`.
  - Broken links in `04*.md`: **PASS**
    - No missing local markdown targets in the 04 file set.
  - Q3 minimal-duplication handling for Phase 2A routes: **PASS**
    - `04d` now has delegated route inventory table that references `02a` schemas.
  - Stale `Step 4.x` / `§4.x` references: **PASS**
    - No residual matches in reviewed files.
  - Q2 pattern consistency (cross-doc endpoint conventions): **FAIL**
    - `04g` now uses `/api/v1/system/*`, but rest of plan remains on `/api/v1/health` + `/api/v1/service/*`.
  - Consumer Notes mapping accuracy: **FAIL**
    - Several 04 Consumer Notes list wrong tool names and/or wrong 05 file ownership.
  - Round-trip contract completeness in 04 files: **FAIL**
    - Round-trips are claimed and consumed in Phase 5, but no concrete Phase 4 route spec exists.

## Reviewer Output

- Findings by severity:

  - **High:** System endpoint namespace drift remains unresolved across plan.
    - `04g` specifies `GET /api/v1/system/health`, `GET /api/v1/system/status`, `POST /api/v1/system/graceful-shutdown` (`04g-api-system.md:212`, `224`, `232`, tests at `238`, `244`, `250`).
    - Core consumers still use old pattern:
      - `05b-mcp-zorivest-diagnostics.md:54`, `169-170`, `235`, `245` use `/health` and `/service/*`.
      - `06f-gui-settings.md:735`, `737`, `782` uses `GET /health`, `GET /service/status`, `POST /service/graceful-shutdown`.
      - `10-service-daemon.md:734-736` defines canonical `/api/v1/health` + `/api/v1/service/*`.
    - With Q2 (“follow pattern from other docs”), `04g` is the outlier.

  - **High:** Consumer Notes tool mapping is still inconsistent with actual Phase 5 tool specs.
    - Trades: `04a-api-trades.md:256` maps `create_trade/list_trades/attach_screenshot` to `[05a]`; actual specs are in `05c-mcp-trade-analytics.md:9`, `62`, `95`.
    - Accounts: `04b-api-accounts.md:154` lists `disconnect_market_provider` under `[05f]`; actual spec is in `05e-mcp-market-data.md:191`.
    - Analytics: `04e-api-analytics.md:149` lists `get_expectancy`, `get_drawdown`, `get_pfof_report`; canonical tool names are `get_expectancy_metrics`, `simulate_drawdown`, `estimate_pfof_impact` (`05c-mcp-trade-analytics.md:363`, `392`, `334`).
    - Tax: `04f-api-tax.md:217` lists `record_quarterly_payment`; canonical name is `record_quarterly_tax_payment` (`05h-mcp-tax.md:258`).
    - System: `04g-api-system.md:308` links `zorivest_service_restart` to `[05a]`; actual spec is `05b-mcp-zorivest-diagnostics.md:221`.

  - **Medium:** Round-trip endpoint remains underspecified in Phase 4 despite active downstream use.
    - Phase 4 claims round-trips (`04a-api-trades.md:5`, `04-rest-api.md:152`), but no `APIRouter` route in `04a`/`04-rest-api` defines `/api/v1/round-trips`.
    - MCP tool uses it directly (`05c-mcp-trade-analytics.md:222-235`, `fetchApi('/round-trips')`).

  - **Medium:** Pre-unlock access contract for MCP Guard is still contradictory.
    - `04-rest-api.md:78` says MCP guard status is available before unlock.
    - `04g-api-system.md:81` and tests (`148-152`) require unlocked session and return 403 when unauthenticated.

- Open questions:
  - Should 04g align back to existing canonical pattern (`/health` + `/service/*`) or trigger a coordinated repo-wide migration to `/system/*`?
  - For Consumer Notes, should the policy be strict canonical tool IDs + owning 05-file only (no aliases)?

- Verdict:
  - **changes_required**

- Residual risk:
  - Endpoint namespace drift and tool-name drift can cause implementation to satisfy one phase while breaking another (04 vs 05/06/10).

## Approval Gate

- **Human approval required for merge/release/deploy:** yes
- **Approval status:** pending
- **Approver:**
- **Timestamp:**

## Final Summary

- What is now good:
  - Router manifest exhaustiveness fixed (Q1 satisfied).
  - 04-file link integrity fixed.
  - Step/section stale references fixed.
  - Phase 2A delegation table added in 04d (good minimal-duplication move).

- Remaining actions:
  1. Resolve `/system/*` vs `/health` + `/service/*` contract divergence.
  2. Normalize Consumer Notes tool names and file ownership to canonical 05 specs.
  3. Add explicit round-trip route contract in Phase 4 or remove claim/downstream dependency.
  4. Resolve MCP Guard pre-unlock contradiction between `04-rest-api` and `04g`.

- Q3 optimization proposal (minimal duplication):
  - Add one canonical **Route Contract Registry** table in `04-rest-api.md` (route id, method, path, owner sub-file, consuming 05 tool IDs, consuming 06 page IDs).
  - Keep sub-files focused on local route schemas/tests.
  - In `04d`, keep current delegated Phase 2A inventory table as pointer-only (no schema duplication).