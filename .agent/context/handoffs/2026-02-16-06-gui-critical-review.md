# Task Handoff

## Task

- **Date:** 2026-02-16
- **Task slug:** 06-gui-critical-review
- **Owner role:** reviewer
- **Scope:** Critical review of `docs/build-plan/06-gui.md` for contract drift, implementation risk, and acceptance clarity.

## Inputs

- User request: Critically review `docs/build-plan/06-gui.md` and provide feedback in `.agent/context/handoff`.
- Specs/docs referenced:
  - `docs/build-plan/06-gui.md`
  - `docs/build-plan/06a-gui-shell.md`
  - `docs/build-plan/06b-gui-trades.md`
  - `docs/build-plan/04-rest-api.md`
  - `docs/build-plan/05-mcp-server.md`
  - `.agent/context/handoffs/TEMPLATE.md`
- Constraints:
  - Findings-first, severity-ranked review.
  - Use concrete file/line evidence.
  - Keep focus on defects/regression risk, not style.

## Role Plan

1. orchestrator
2. reviewer
3. coder (not used)
4. tester (not used)
- Optional roles: researcher, guardrail (not used)

## Coder Output

- Changed files:
  - `.agent/context/handoffs/2026-02-16-06-gui-critical-review.md` (new)
- Design notes:
  - Documentation-only review; no product code changed.
- Commands run:
  - `Get-Content` (full file with line numbers)
  - `rg -n` cross-file endpoint and contract checks
- Results:
  - Review completed; findings captured below.

## Tester Output

- Commands run:
  - None (doc review only).
- Pass/fail matrix:
  - Not applicable.
- Repro failures:
  - Not applicable.
- Coverage/test gaps:
  - No explicit test plan is defined for startup-metric logging contract changes introduced in `06-gui.md`.

## Reviewer Output

- Findings by severity:

  - **Critical:** Trades surface is required but not reachable in the phase-level navigation and route map.
    - Evidence: `docs/build-plan/06-gui.md:16` (Trades module listed), `docs/build-plan/06-gui.md:125` and `docs/build-plan/06-gui.md:139` (routes include planning/scheduling/settings/tax, no trades), `docs/build-plan/06-gui.md:185` and `docs/build-plan/06-gui.md:190` (nav rail omits Trades), `docs/build-plan/06-gui.md:350` (Trades table exit criterion), `docs/build-plan/06b-gui-trades.md:9` (Trades page described as primary data surface).
    - Risk: Implementation can satisfy sub-file 6b but still ship with no discoverable entry point.
    - Recommendation: Define canonical access path now (top-level `/trades` route or explicit nested route under another module) and reflect it in nav, route snippet, and module map.

  - **Critical:** MRU "last trade" query contract in GUI is not supported by the current REST spec.
    - Evidence: `docs/build-plan/06-gui.md:336` expects `GET /api/v1/trades?account_id={id}&limit=1&sort=-date`; `docs/build-plan/04-rest-api.md:57` exposes only `limit` and `offset` in `list_trades`.
    - Risk: Accounts Home MRU cards cannot reliably render "Last trade" as specified.
    - Recommendation: Add `account_id` and sort semantics to Phase 4 trade list contract (plus tests), or change GUI contract to use a supported endpoint.

  - **High:** Startup performance logging depends on an undocumented REST endpoint.
    - Evidence: `docs/build-plan/06-gui.md:64` and `docs/build-plan/06-gui.md:90` use `POST /api/v1/logs`; Phase 4 only specifies trades/images/settings routers (`docs/build-plan/04-rest-api.md:24`, `docs/build-plan/04-rest-api.md:115`, `docs/build-plan/04-rest-api.md:178`).
    - Risk: Startup metrics silently drop because endpoint contract is missing from prerequisite phase.
    - Recommendation: Add an explicit logging route contract in Phase 4 (or change design to IPC/file logging) and include acceptance tests.

  - **High:** Settings type contract is ambiguous for MRU account list.
    - Evidence: `docs/build-plan/06-gui.md:280` models `ui.accounts.mru` as array-like data; `docs/build-plan/06-gui.md:337` labels endpoint return as MRU list; REST schema defines `value: str` (`docs/build-plan/04-rest-api.md:183`); MCP convention says settings are strings at boundary (`docs/build-plan/05-mcp-server.md:253`).
    - Risk: Runtime parse/serialization bugs (array vs string) and cross-surface drift.
    - Recommendation: Specify canonical encoding (`JSON.stringify` array in setting value) and decoding responsibility in the hook contract.

  - **Medium:** Example code uses an empty error handler in main-process logging path.
    - Evidence: `docs/build-plan/06-gui.md:99` uses `.catch(() => {})`.
    - Risk: Diagnostics disappear exactly when startup telemetry path fails.
    - Recommendation: Replace with structured warning/error handling and optional retry queue so failures are observable.

  - **Medium:** Account context nullability is internally inconsistent with persistence hook contract.
    - Evidence: `docs/build-plan/06-gui.md:295` declares `activeAccountId: string | null`; `docs/build-plan/06-gui.md:303` initializes with empty string; `docs/build-plan/06a-gui-shell.md:127` defines `usePersistedState<T extends string>`.
    - Risk: Sentinel mismatch (`null` vs `''`) can cause logic drift across modules consuming account context.
    - Recommendation: Standardize on one representation and align hook typing/examples.

  - **Medium:** Startup background color is hardcoded to dark theme despite persisted theme requirement.
    - Evidence: `docs/build-plan/06-gui.md:37` sets `backgroundColor: '#1a1a2e'`; `docs/build-plan/06-gui.md:365` requires theme persistence across sessions.
    - Risk: Light-theme users see a dark flash at launch and inconsistent startup experience.
    - Recommendation: Resolve theme value before window creation and set `BrowserWindow` background accordingly.

- Open questions:
  - Should Trades be a first-class nav rail destination, or intentionally nested under Planning/Accounts?
  - Do you want Phase 4 to formally include `POST /api/v1/logs`, or should startup metrics remain local-only until logging API exists?
  - For `ui.accounts.mru`, should the REST/API contract stay string-only with JSON serialization, or evolve to typed JSON values?

- Verdict:
  - `06-gui.md` is directionally strong, but **not implementation-safe yet** due unresolved route and API contract gaps.

- Residual risk:
  - If unresolved, Phase 6 implementation will accumulate ad hoc API changes during UI work, increasing rework across Phase 4/5/6.

## Guardrail Output (If Required)

- Safety checks:
  - Documentation-only changes.
- Blocking risks:
  - None beyond recorded design/contract blockers.
- Verdict:
  - Safe to proceed with doc corrections.

## Approval Gate

- **Human approval required for merge/release/deploy:** yes
- **Approval status:** pending
- **Approver:**
- **Timestamp:**

## Final Summary

- Status:
  - Critical review complete; findings and remediation targets documented.
- Next steps:
  1. Resolve the three open contract decisions (trades routing, logs endpoint, settings typing).
  2. Patch `06-gui.md` and dependent docs (`04-rest-api.md`, optionally `06a/06b`) in one consistency pass.
  3. Re-review exit criteria after contract updates.
