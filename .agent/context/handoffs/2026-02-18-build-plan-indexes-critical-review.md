# Task Handoff

## Task

- **Date:** 2026-02-18
- **Task slug:** build-plan-indexes-critical-review
- **Owner role:** reviewer
- **Scope:** Critical review of updated index docs: `gui-actions-index.md`, `output-index.md`, and `input-index.md` header companion-link update.

## Inputs

- User request:
  - Review updated build-plan index documents and create a critical-review handoff in `.agent/context/handoffs`.
- Specs/docs referenced:
  - `docs/build-plan/gui-actions-index.md`
  - `docs/build-plan/output-index.md`
  - `docs/build-plan/input-index.md`
  - `docs/build-plan/05-mcp-server.md`
  - `docs/build-plan/06f-gui-settings.md`
  - `docs/build-plan/08-market-data.md`
  - `.agent/context/handoffs/TEMPLATE.md`
- Constraints:
  - Findings-first, severity-ranked, with concrete file/line evidence.
  - Focus on contract drift, regression risk, and planning-accounting accuracy.

## Role Plan

1. orchestrator
2. reviewer
3. coder (handoff artifact only)
4. tester (doc consistency verification via command checks)
- Optional roles: researcher, guardrail (not used)

## Coder Output

- Changed files:
  - `.agent/context/handoffs/2026-02-18-build-plan-indexes-critical-review.md` (new)
- Design notes:
  - Documentation-only critical review artifact; no runtime code changes.
- Commands run:
  - `rg -n` contract tracing across index docs and canonical source docs.
  - Row-count consistency checks:
    - `rg '^\\| [0-9]+\\.[0-9]+ \\|' docs/build-plan/gui-actions-index.md`
    - `rg '^\\| [0-9]+[a-z]?\\.[0-9]+ \\|' docs/build-plan/output-index.md`
  - Status/keyboard count checks via PowerShell row filtering.
- Results:
  - Multiple high-severity index-contract defects identified (market-data endpoint namespace/tool-name drift + stale summary metrics).

## Tester Output

- Commands run:
  - `rg -n 'market/providers|market-data/providers|remove_market_key|disconnect_market_provider' docs/build-plan/*.md`
  - `rg -n '^\\| [0-9]+\\.[0-9]+ \\|' docs/build-plan/gui-actions-index.md`
  - `rg -n '^\\| [0-9]+[a-z]?\\.[0-9]+ \\|' docs/build-plan/output-index.md`
  - Regex-based status distribution checks for both indexes.
- Pass/fail matrix:
  - Market-data route contract alignment: **FAIL**
  - MCP market-key tool name alignment: **FAIL**
  - GUI actions summary accounting: **FAIL**
  - Output index summary accounting: **FAIL**
  - Input-index companion links in header: **PASS**
- Repro failures:
  - Route naming drift reproduces immediately by comparing index entries against canonical `/market-data` contracts.
  - Summary count drift reproduces immediately via regex row counts.
- Coverage/test gaps:
  - No automated lint/check exists to validate index table totals or endpoint/tool-name consistency across docs.

## Reviewer Output

- Findings by severity:

  - **Critical:** Market-data endpoint namespace drift across new indexes (`/market` vs canonical `/market-data`).
    - Evidence:
      - GUI actions uses `/api/v1/market/providers/...`: `docs/build-plan/gui-actions-index.md:126`, `docs/build-plan/gui-actions-index.md:127`, `docs/build-plan/gui-actions-index.md:128`.
      - Output index uses `/market/...` paths: `docs/build-plan/output-index.md:239`, `docs/build-plan/output-index.md:240`, `docs/build-plan/output-index.md:241`, `docs/build-plan/output-index.md:242`, `docs/build-plan/output-index.md:243`.
      - Canonical market router prefix is `/api/v1/market-data`: `docs/build-plan/08-market-data.md:469`.
      - Canonical GUI/MCP fetch examples also use `/market-data/...`: `docs/build-plan/06f-gui-settings.md:85`, `docs/build-plan/06f-gui-settings.md:91`, `docs/build-plan/06f-gui-settings.md:108`, `docs/build-plan/08-market-data.md:542`, `docs/build-plan/08-market-data.md:569`, `docs/build-plan/08-market-data.md:602`.
    - Risk:
      - GUI/API implementation based on index tables will call wrong endpoints (404s and integration churn).
    - Recommendation:
      - Normalize all market-data routes in both indexes to `/api/v1/market-data/...` (or a single documented shorthand convention used everywhere).

  - **Critical:** MCP tool name drift for provider key removal (`remove_market_key` is not canonical).
    - Evidence:
      - Index uses `remove_market_key`: `docs/build-plan/gui-actions-index.md:127`.
      - Canonical tool name is `disconnect_market_provider`: `docs/build-plan/05-mcp-server.md:192`, `docs/build-plan/08-market-data.md:611`.
    - Risk:
      - MCP invocation failures for GUI-accounting workflows and incorrect implementation tickets.
    - Recommendation:
      - Replace `remove_market_key` with `disconnect_market_provider` in index docs (or formally rename tool in canonical specs and sync everywhere).

  - **High:** `gui-actions-index.md` summary statistics are stale and materially incorrect.
    - Evidence:
      - Reported totals: `Total GUI actions = 72`, `Defined = 40`, `Planned = 18`, `Keyboard = 12`: `docs/build-plan/gui-actions-index.md:268`, `docs/build-plan/gui-actions-index.md:270`, `docs/build-plan/gui-actions-index.md:272`, `docs/build-plan/gui-actions-index.md:275`.
      - Actual row-derived counts from table IDs (`^\| [0-9]+\.[0-9]+ \|`): **82 actions**, **47 defined**, **14 domain**, **21 planned**, **11 keyboard-triggered**.
    - Risk:
      - Incorrect progress/coverage accounting and bad planning decisions for GUI completion.
    - Recommendation:
      - Recompute summary metrics from the current table rows and add a lightweight validation script/check.

  - **High:** `output-index.md` summary statistics are inconsistent with its own table data.
    - Evidence:
      - Reported totals: `Total computed outputs = 134`, `Domain modeled = 4`, `Planned = 58`, `Tax outputs = 50`: `docs/build-plan/output-index.md:263`, `docs/build-plan/output-index.md:266`, `docs/build-plan/output-index.md:267`, `docs/build-plan/output-index.md:269`.
      - Actual row-derived counts from IDs (`^\| [0-9]+[a-z]?\.[0-9]+ \|`): **120 outputs**, **72 defined**, **2 domain**, **46 planned**, **46 tax outputs**.
    - Risk:
      - Inflated scope and misleading completion percentages for output-contract implementation.
    - Recommendation:
      - Regenerate summary rows directly from table entries; avoid manual totals.

  - **Medium:** Output surface legend omits the `🔗` symbol that is used in output rows.
    - Evidence:
      - Legend defines only `🖥️`, `🤖`, `🔌`: `docs/build-plan/output-index.md:14`.
      - Row `3.1` uses `🖥️🔌🔗`: `docs/build-plan/output-index.md:123`.
    - Risk:
      - Ambiguity in surface semantics (is `🔗` valid for outputs, and what exactly does it mean here?).
    - Recommendation:
      - Either add `🔗` to legend with explicit meaning or replace it with existing legend symbols.

- Open questions:
  - Should index route columns always use full canonical paths (`/api/v1/...`) instead of shorthand?
  - Should summary metrics include shell/navigation actions (currently present as numbered rows)?
  - Do you want a small script in `docs/build-plan/` to auto-verify index totals and contract names?

- Verdict:
  - Updated indexes add valuable structure, but they are **not contract-safe yet** due two critical namespace/tool-name drifts plus high-impact accounting inaccuracies.

- Residual risk:
  - If implemented as-is, teams can build against incorrect market-data routes/tools and track progress against incorrect totals.

## Guardrail Output (If Required)

- Safety checks:
  - Documentation-only review output.
- Blocking risks:
  - No runtime code touched; blockers are design-contract consistency issues.
- Verdict:
  - Safe to proceed with targeted doc corrections before implementation.

## Approval Gate

- **Human approval required for merge/release/deploy:** yes
- **Approval status:** pending
- **Approver:**
- **Timestamp:**

## Final Summary

- Status:
  - Critical review completed and handoff created.
- Next steps:
  1. Normalize market-data endpoint namespace + MCP tool names across `gui-actions-index.md` and `output-index.md`.
  2. Recompute and correct summary statistics in both indexes from live table rows.
  3. Clarify output surface legend for `🔗` (or remove its use).
