# Task Handoff

## Task

- **Date:** 2026-02-15
- **Task slug:** build-plan-market-data-gui-input-index-review
- **Owner role:** reviewer
- **Scope:** critical review of `docs/build-plan/` with focus on Market Data API/GUI changes and input-index GUI/MCP coverage

## Inputs

- User request: critically review `docs/build-plan/` files; validate/confirm input-field index; find missing GUI and MCP input coverage
- Specs/docs referenced: `docs/build-plan/*.md`, `.agent/context/current-focus.md`, `.agent/context/known-issues.md`, `SOUL.md`
- Constraints: review-first output with severity-ranked findings and file/line evidence

## Role Plan

1. orchestrator
2. reviewer

## Coder Output

- Changed files:
  - `.agent/context/handoffs/2026-02-15-build-plan-market-data-gui-input-index-review.md` (new)
- Design notes:
  - No product-code or build-plan edits applied in this session (review-only)
- Commands run:
  - `rg --files docs/build-plan`
  - `git status --short -- docs/build-plan`
  - `git diff -- docs/build-plan/...`
  - targeted `rg -n` and line-numbered file inspections
- Results:
  - Identified contract drift between input index and Market Data GUI/MCP/API docs

## Tester Output

- Commands run:
  - N/A (review-only task)
- Pass/fail matrix:
  - N/A
- Repro failures:
  - N/A
- Coverage/test gaps:
  - N/A

## Reviewer Output

- Findings by severity:
  - Critical: `is_enabled` provider toggle is indexed as supported but not writable via current REST/GUI contract.
  - High: ProviderSettings save flow can clear API key and overwrite provider rate limits.
  - High: Remove/disconnect workflow is documented but absent from MCP tools and GUI actions.
  - High: input-index marks multiple GUI/MCP surfaces as `✅` without corresponding GUI/MCP contracts (notably Account Review / TradePlan / Watchlist / Display toggles / Tax profile).
  - Medium: phase dependency declarations conflict after adding Phase 8 prerequisites to Phases 5 and 6.
  - Medium: market-data concurrency-guard snippet uses attribute access on `dict` return values.
  - Medium: broken source links for market-tools inspiration docs.
- Open questions:
  - Should `configure_provider` auto-enable providers on successful key save, or expose explicit `is_enabled` writes?
  - Should MCP include provider key removal (`disconnect`) to match input-index security note?
  - Should input-index `✅` mean “entity modeled” or “surface contract exists in phase docs”?
- Verdict:
  - Input index validation: **FAIL** for GUI/MCP contract fidelity.
- Residual risk:
  - Teams may assume nonexistent MCP/GUI contracts exist and build downstream dependencies on missing interfaces.

## Approval Gate

- **Human approval required for merge/release/deploy:** yes
- **Approval status:** pending
- **Approver:**
- **Timestamp:**

## Final Summary

- Status: review complete; findings ready for remediation planning
- Next steps:
  - Decide canonical status semantics for `input-index.md` (`contracted` vs `planned` vs `implemented`).
  - Patch Market Data provider config contract (`is_enabled`, remove/disconnect flow, GUI save semantics).
  - Reconcile phase dependency metadata and broken source links.
