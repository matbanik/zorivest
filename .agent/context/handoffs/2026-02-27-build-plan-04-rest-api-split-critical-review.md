# Task Handoff Template

## Task

- **Date:** 2026-02-27
- **Task slug:** build-plan-04-rest-api-split-critical-review
- **Owner role:** reviewer
- **Scope:** Critical review of `docs/build-plan/04*.md` split from monolith `04-rest-api.md`, including cross-file consistency in `docs/build-plan/`.

## Inputs

- User request: "use critical-review-feedback workflow for docs/build-plan, validate 04 monolith split, consistency, structure, and reasoning"
- Specs/docs reviewed:
  - `docs/build-plan/04-rest-api.md`
  - `docs/build-plan/04a-api-trades.md`
  - `docs/build-plan/04b-api-accounts.md`
  - `docs/build-plan/04c-api-auth.md`
  - `docs/build-plan/04d-api-settings.md`
  - `docs/build-plan/04e-api-analytics.md`
  - `docs/build-plan/04f-api-tax.md`
  - `docs/build-plan/04g-api-system.md`
  - `docs/build-plan/05c-mcp-trade-analytics.md`
  - `docs/build-plan/05d-mcp-trade-planning.md`
  - `docs/build-plan/05h-mcp-tax.md`
  - `docs/build-plan/05j-mcp-discovery.md`
  - `docs/build-plan/mcp-planned-readiness.md`
  - `docs/build-plan/input-index.md`
  - `docs/build-plan/06f-gui-settings.md`
- Historical baseline:
  - `pomera_notes` Note #220 (`Code/04-rest-api.md/Pre-Split-Original-2026-02-27`)

## Role Plan

1. orchestrator
2. tester
3. reviewer

## Coder Output

- Changed files:
  - `.agent/context/handoffs/2026-02-27-build-plan-04-rest-api-split-critical-review.md`
- Design notes:
  - Review-only session. No product docs modified.
- Commands run:
  - `git status --short -- docs/build-plan`
  - `git diff -- docs/build-plan/04-rest-api.md docs/build-plan/04a-api-trades.md ... docs/build-plan/04g-api-system.md`
  - `rg -n "^#|^##|^###" docs/build-plan -g "04*.md"`
  - `rg -n "Step 4\.|§4\.[0-9]" docs/build-plan`
  - `rg -n "include_router\(|broker_router|banking_router|import_router|mistakes_router|fees_router|calculator_router" ...`
  - `rg -n "05a-mcp-core\.md|05b-mcp-settings\.md|06c-gui-auth\.md|06e-gui-analytics\.md|06h-gui-system\.md" docs/build-plan -g "04*.md"`
  - link existence sweep via PowerShell `Test-Path` over markdown links in `04*.md`
- Results:
  - Split structure is mostly coherent, but there are multiple contract/navigation regressions and unresolved completeness gaps.

## Tester Output

- Evidence highlights:
  - `git status` shows `04a`-`04g` are newly added and `04-rest-api.md` rewritten summary + manifest.
  - Router definition vs include-router sweep shows six defined routers are omitted from manifest include list.
  - Link existence sweep shows several broken intra-plan links introduced in consumer notes.
  - Cross-doc sweep shows stale references to removed Step/section numbering (`Step 4.9`, `§4.6`, etc.) after split.
- Pass/fail matrix:
  - Monolith decomposition into domain sub-files: **PASS** (content distributed across 04a-04g)
  - Router manifest completeness vs sub-files: **FAIL**
  - Consumer notes link integrity in 04 sub-files: **FAIL**
  - Cross-file section-reference consistency after split: **FAIL**
  - Phase 2A route implementation traceability in 04d: **FAIL**
  - 04 system scope completeness (health/service lifecycle specs): **FAIL**
- Coverage/test gaps:
  - No automated markdown link/anchor checker in docs pipeline.
  - No docs contract parity check for `04` router inventory vs `05/06` dependencies.

## Reviewer Output

- Findings by severity:

  - **High:** Broken and incorrect consumer-note references were introduced in split files.
    - `04a-api-trades.md:256` links to non-existent `05a-mcp-core.md`.
    - `04c-api-auth.md:177-178` links to non-existent `05a-mcp-core.md` and `06c-gui-auth.md`.
    - `04d-api-settings.md:156` links to non-existent `05b-mcp-settings.md`.
    - `04e-api-analytics.md:150` links to non-existent `06e-gui-analytics.md`.
    - `04g-api-system.md:238-239` links to non-existent `05a-mcp-core.md` and `06h-gui-system.md`.
    - Impact: broken navigation + incorrect ownership mapping for MCP/GUI consumers.

  - **High:** `04-rest-api.md` router manifest is incomplete relative to split sub-files.
    - Manifest includes only: trades/plan/images/accounts/auth/confirmation/settings/analytics/tax/guard/log/version (`04-rest-api.md:97-108`).
    - Missing routers that are explicitly defined in sub-files:
      - `broker_router` (`04b-api-accounts.md:72`)
      - `banking_router` (`04b-api-accounts.md:95`)
      - `import_router` (`04b-api-accounts.md:128`)
      - `mistakes_router` (`04e-api-analytics.md:92`)
      - `fees_router` (`04e-api-analytics.md:112`)
      - `calculator_router` (`04e-api-analytics.md:132`)
    - Impact: top-level Phase 4 implementation map is internally inconsistent.

  - **Medium:** Post-split cross-doc references still point to removed Step/section numbering from old monolith.
    - `mcp-planned-readiness.md:78,89,100,111,122,133,144,155` still reference `04-rest-api.md ... Step 4.9`.
    - `input-index.md:228,351,542` and `06f-gui-settings.md:550` still reference `Phase 4 §4.x` / `§4.6`.
    - Impact: traceability and reviewability regress after split; references no longer map cleanly.

  - **Medium:** Phase 2A implementation claim in `04-rest-api.md` is not substantiated in `04d-api-settings.md` route specs.
    - Claim: `04-rest-api.md:5` says Phase 2A routes are implemented in `04d-api-settings.md`.
    - `04d-api-settings.md` only specifies `GET /settings`, `GET /settings/{key}`, `PUT /settings` (`04d-api-settings.md:39,45,54`) plus a response class mentioning `/settings/resolved` (`04d-api-settings.md:31-32`), but no explicit resolver/reset/backup/config-export-import route specs.
    - Impact: implementation contract is incomplete/implicit.

  - **Medium:** System scope claims include health/service lifecycle, but no concrete route spec is present in 04 files.
    - Claim lines: `04-rest-api.md:72,78,171` and `04g-api-system.md:1-5`.
    - Actual 04g sections only: Logging, MCP Guard, Version (`04g-api-system.md:9,50,184`); no `/health`, `/service/status`, `/service/graceful-shutdown` route snippets.
    - Impact: declared API surface is only partially specified.

  - **Low:** Tag/package consistency drift remains inside split files.
    - Most snippets use `packages/api/src/zorivest_api/...`; account/calculator snippets use `packages/server/src/zorivest_server/...` (`04b-api-accounts.md:14`, `04e-api-analytics.md:127`).
    - Main OpenAPI tag metadata is lowercase (`accounts`, `analytics`) (`04-rest-api.md:21-27`) while snippets use `tags=["Accounts"]` and `tags=["Calculator"]` (`04b-api-accounts.md:20`, `04e-api-analytics.md:132`).
    - Impact: documentation style and generated OpenAPI tag grouping become inconsistent.

- Open questions:
  - Should `04-rest-api.md` include every concrete router include, or stay intentionally high-level and mark omissions as delegated?
  - Which Phase 6 files are canonical consumers for auth/system/analytics in this plan (`06a/06f/06h` split vs planned future files)?
  - Should Phase 2A route specs be copied into 04d or linked by explicit route inventory table?

- Verdict:
  - **changes_required**

- Residual risk:
  - Without link/anchor and router-parity checks, future docs edits can silently reintroduce these cross-phase contract drifts.

## Approval Gate

- **Human approval required for merge/release/deploy:** yes
- **Approval status:** pending
- **Approver:**
- **Timestamp:**

## Final Summary

- Status:
  - Review complete; split is directionally correct but not yet consistent enough for approval.
- Next steps:
  1. Fix broken/misdirected links in 04 consumer notes.
  2. Reconcile router manifest with actual 04b/04e routers.
  3. Update stale `§4.x` / `Step 4.9` references across build-plan docs.
  4. Explicitly document Phase 2A + system health/service routes in the relevant 04 sub-files.