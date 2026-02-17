# Task Handoff

## Task

- **Date:** 2026-02-16
- **Task slug:** build-plan-gui-mcp-input-index-review
- **Owner role:** reviewer
- **Scope:** Critical review of build-plan consistency for input index, GUI, MCP, REST, infra, and dependency/matrix alignment.

## Inputs

- User request: Critically review `docs/build-plan/` updates with focus on:
  - `build-priority-matrix.md`
  - `dependency-manifest.md`
  - `02-infrastructure.md`
  - `04-rest-api.md`
  - `05-mcp-server.md`
  - `06-gui.md`
  - `input-index.md`
- Specs/docs referenced:
  - `docs/build-plan/08-market-data.md`
  - `AGENTS.md`
  - `.agent/context/handoffs/TEMPLATE.md`
- Constraints:
  - Findings-first review style.
  - Validate input index contract completeness (GUI/MCP/API) and cross-file consistency.
  - Include questions inside findings.

## Role Plan

1. orchestrator
2. reviewer
3. coder (not used)
4. tester (not used)
- Optional roles: researcher, guardrail (not used)

## Coder Output

- Changed files:
  - `.agent/context/handoffs/2026-02-16-build-plan-gui-mcp-input-index-review.md` (new)
- Design notes:
  - No code/docs content changed outside handoff.
- Commands run:
  - `git status --short -- docs/build-plan/...`
  - `Get-Content` with line numbers for all reviewed files
  - `rg -n` cross-reference checks
  - custom markdown-link existence check
  - input-index row/status count scripts
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
  - Settings endpoints were added but Step 4.2 e2e examples do not include settings route tests.

## Reviewer Output

- Findings by severity:

  - **High:** `input-index` marks Display Mode Toggles as `🔶 Domain modeled`, but full GUI/MCP/API contracts now exist.
    - Evidence: `docs/build-plan/input-index.md:211`, `docs/build-plan/04-rest-api.md:166`, `docs/build-plan/05-mcp-server.md:224`, `docs/build-plan/06-gui.md:371`
    - **Question:** Should rows `9.1-9.3` be promoted to `✅` and include `[04]`, `[05]`, and `[06]` in Plan Files?

  - **High:** `input-index` is missing newly documented settings inputs (`ui.*`, `notification.*`) and settings MCP tool inputs (`key`, `settings` map).
    - Evidence: `docs/build-plan/02-infrastructure.md:155`, `docs/build-plan/06-gui.md:452`, `docs/build-plan/05-mcp-server.md:225`
    - **Question:** Do you want explicit per-key rows (e.g., `ui.theme`, `notification.warning.enabled`) or one wildcard/settings-namespace contract row with key-pattern constraints?

  - **High:** Market-provider key removal/disconnect is implemented in REST/MCP/GUI flows but absent from the indexed input rows.
    - Evidence: `docs/build-plan/08-market-data.md:506`, `docs/build-plan/05-mcp-server.md:192`, `docs/build-plan/06-gui.md:679`, `docs/build-plan/input-index.md:349`
    - **Question:** Should `15m` add a `Remove API key` action row (likely `15m.7`) with surfaces `🖥️🤖🔌`?

  - **High:** MCP market-data tool contract drift between Phase 5 and Phase 8.
    - Evidence: Phase 5 lists `disconnect_market_provider` (`docs/build-plan/05-mcp-server.md:192`, `docs/build-plan/05-mcp-server.md:271`) but Phase 8 tool code block defines 6 tools and omits it (`docs/build-plan/08-market-data.md:533`)
    - **Question:** Which doc is canonical for tool list parity, and should Phase 8 Step 8.5 explicitly include `disconnect_market_provider`?

  - **High:** Build order contradiction: Phase 5/6 declare dependency on Phase 8, but matrix schedules 5/6 work in P0 and Phase 8 as P1.5.
    - Evidence: `docs/build-plan/05-mcp-server.md:3`, `docs/build-plan/06-gui.md:3`, `docs/build-plan/build-priority-matrix.md:26`, `docs/build-plan/build-priority-matrix.md:51`
    - **Question:** Should this be resolved by splitting 5/6 into core vs market-data extensions, or by moving market-dependent items to run after item 30?

  - **Medium:** Settings routes were added, but Step 4.2 e2e examples still cover only trades/images while exit criteria require settings correctness.
    - Evidence: `docs/build-plan/04-rest-api.md:140`, `docs/build-plan/04-rest-api.md:214`, `docs/build-plan/build-priority-matrix.md:29`
    - **Question:** Should Step 4.2 add `GET/PUT /api/v1/settings` TestClient examples, or should the matrix/exit criterion be relaxed?

  - **Medium:** Settings value typing is ambiguous across docs (`z.record(z.string())` vs many bool/number inputs in index).
    - Evidence: `docs/build-plan/05-mcp-server.md:239`, `docs/build-plan/input-index.md:211`, `docs/build-plan/input-index.md:351`
    - **Question:** Is the canonical contract “all values serialized as strings at API/MCP boundary,” or should typed JSON values be supported end-to-end?

  - **Medium:** Dependency mapping table omits `@tanstack/react-query` even though install command includes it.
    - Evidence: `docs/build-plan/dependency-manifest.md:42`, `docs/build-plan/dependency-manifest.md:66`
    - **Question:** Should phase-6 mapping include `@tanstack/react-query` to match install commands?

  - **Medium:** `input-index` summary statistics are stale after the status/modeling updates.
    - Evidence: `docs/build-plan/input-index.md:482`
    - Current counted rows (sections 1-17): 114 total, 45 `✅`, 37 `🔶`, 32 `📋`.
    - **Question:** Should summary stats be exact (script-generated) instead of approximate `~` values?

  - **Medium:** Source links in `06-gui.md` still point to old paths, despite the `_inspiration` folder being present at repo root.
    - Evidence: `docs/build-plan/06-gui.md:128`, `docs/build-plan/06-gui.md:307`, `docs/build-plan/06-gui.md:373`, `docs/build-plan/06-gui.md:467`
    - Existing files: `_inspiration/_market_tools_architecture.md`, `_inspiration/_gui-settings-architecture.md`
    - **Question:** Should these links be updated to `../../_inspiration/...` from `docs/build-plan/06-gui.md`?

- Verdict:
  - Input index is **not yet validated/confirmed** due unresolved cross-surface and cross-phase consistency issues.

- Residual risk:
  - If unresolved, implementation may diverge on settings contracts, market-data tool parity, and build sequencing, increasing rework risk across REST/MCP/GUI.

## Guardrail Output (If Required)

- Safety checks:
  - Documentation-only review; no runtime changes.
- Blocking risks:
  - None beyond documented consistency blockers.
- Verdict:
  - Safe to proceed with doc corrections only.

## Approval Gate

- **Human approval required for merge/release/deploy:** yes
- **Approval status:** pending
- **Approver:**
- **Timestamp:**

## Final Summary

- Status:
  - Review complete; findings documented with embedded questions.
- Next steps:
  1. Resolve each embedded question (contract decisions).
  2. Apply one consistency patch across `input-index`, `05/06` prerequisites, `08` MCP tool list, and `dependency-manifest` mapping.
  3. Re-run link validation and row-count check; then mark input index confirmed.