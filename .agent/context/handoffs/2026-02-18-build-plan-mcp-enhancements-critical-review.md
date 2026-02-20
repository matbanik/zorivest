# Task Handoff

## Task

- **Date:** 2026-02-18
- **Task slug:** build-plan-mcp-enhancements-critical-review
- **Owner role:** reviewer
- **Scope:** Critical review of MCP enhancement build-plan updates across `05-mcp-server.md`, `06f-gui-settings.md`, `input-index.md`, `output-index.md`, `gui-actions-index.md`, `build-priority-matrix.md`, and `testing-strategy.md`.

## Inputs

- User request:
  - Review newly added MCP enhancement features and create a critical-review handoff in `.agent/context/handoffs`.
- Specs/docs referenced:
  - `docs/build-plan/05-mcp-server.md`
  - `docs/build-plan/06f-gui-settings.md`
  - `docs/build-plan/input-index.md`
  - `docs/build-plan/output-index.md`
  - `docs/build-plan/gui-actions-index.md`
  - `docs/build-plan/build-priority-matrix.md`
  - `docs/build-plan/testing-strategy.md`
  - `docs/build-plan/04-rest-api.md`
  - `.agent/context/handoffs/TEMPLATE.md`
- Constraints:
  - Findings-first, severity-ranked, with concrete file/line evidence.
  - Focus on contract correctness, behavioral risk, and implementation safety.

## Role Plan

1. orchestrator
2. reviewer
3. coder (handoff artifact only)
4. tester (doc consistency checks)
- Optional roles: researcher, guardrail (not used)

## Coder Output

- Changed files:
  - `.agent/context/handoffs/2026-02-18-build-plan-mcp-enhancements-critical-review.md` (new)
- Design notes:
  - Documentation-only critical review output; no runtime code changes.
- Commands run:
  - `git diff -- docs/build-plan/...` on all listed files
  - `rg -n` contract tracing for new tools/routes/params
  - Node-based row/count validation for index summary checks
- Results:
  - Multiple critical/high contract issues identified in the new MCP enhancement docs.

## Tester Output

- Commands run:
  - `rg -n "zorivest_diagnose|withMetrics|MetricsCollector|wait_for_close|mcp-guard/status|mcp-guard|/health|/version" docs/build-plan/*.md`
  - `rg -n "api/v1/mcp-guard|api/v1/version" docs/build-plan/04-rest-api.md`
  - Node check for GUI actions summary accounting (REST/client-side counts)
- Pass/fail matrix:
  - Unguarded diagnostics callability contract: **FAIL**
  - MCP guard endpoint alignment across updated docs: **FAIL**
  - `wait_for_close` parameter implementation completeness: **FAIL**
  - Metrics middleware completeness (`getSummary` implementation): **FAIL**
  - GUI actions summary accounting (REST vs client-only): **FAIL**
  - Build-priority additions (15f–15i) existence and references: **PASS**
- Repro failures:
  - Diagnostics code path currently uses auth header retrieval that throws when unauthenticated, despite "always callable" claim.
  - Diagnostics/output/testing docs use `/mcp-guard` while REST contract defines `/api/v1/mcp-guard/status`.
  - `wait_for_close` is declared but never used in launch logic.
  - Metrics collector spec still contains an explicit placeholder throw.
- Coverage/test gaps:
  - New test snippets in §5.11 remain mostly pseudo-comments and are not executable as written.

## Reviewer Output

- Findings by severity:

  - **Critical:** `zorivest_diagnose` "always callable" contract is broken by mandatory auth-header access.
    - Evidence:
      - Tool is declared unguarded/always callable: `docs/build-plan/05-mcp-server.md:589`.
      - `getAuthHeaders()` throws when session token is missing: `docs/build-plan/05-mcp-server.md:331`, `docs/build-plan/05-mcp-server.md:332`, `docs/build-plan/05-mcp-server.md:333`.
      - Diagnostics tool eagerly calls `getAuthHeaders()` for guard/provider fetches: `docs/build-plan/05-mcp-server.md:623`, `docs/build-plan/05-mcp-server.md:624`.
    - Risk:
      - In locked/unbootstrapped contexts, `zorivest_diagnose` can fail hard instead of returning partial diagnostics.
    - Recommendation:
      - Make auth-dependent fetches optional/fail-soft (lazy header retrieval inside `safeFetch`, catch header failures, return per-field `"unavailable"` state).

  - **Critical:** Guard status endpoint contract drift in new diagnostics surfaces (`/mcp-guard` vs canonical `/mcp-guard/status`).
    - Evidence:
      - Canonical REST route is `GET /api/v1/mcp-guard/status`: `docs/build-plan/04-rest-api.md:497`, `docs/build-plan/04-rest-api.md:533`.
      - New diagnostics implementation calls `/mcp-guard`: `docs/build-plan/05-mcp-server.md:623`.
      - New output-index diagnostics row also references `/mcp-guard`: `docs/build-plan/output-index.md:269`.
      - New testing note for diagnostics also references `/mcp-guard`: `docs/build-plan/testing-strategy.md:118`.
    - Risk:
      - Implementation guided by these docs can ship incorrect endpoint calls (404/contract mismatch).
    - Recommendation:
      - Normalize all guard-status references in these new sections to `/api/v1/mcp-guard/status` (or documented base + `/mcp-guard/status` shorthand consistently).

  - **High:** `wait_for_close` is documented as functional input but not implemented in launch flow.
    - Evidence:
      - Contract says if true, block until GUI exits: `docs/build-plan/05-mcp-server.md:860`, `docs/build-plan/05-mcp-server.md:962`.
      - Handler receives `wait_for_close`: `docs/build-plan/05-mcp-server.md:965`.
      - Launch path always calls detached launcher and returns immediately: `docs/build-plan/05-mcp-server.md:930`, `docs/build-plan/05-mcp-server.md:1001`.
      - Input index marks this field fully defined: `docs/build-plan/input-index.md:533`.
    - Risk:
      - Agents depending on blocking semantics will behave incorrectly (race conditions in setup workflows).
    - Recommendation:
      - Either implement foreground launch + process wait path for `wait_for_close=true`, or remove/rename the parameter until supported.

  - **High:** Metrics middleware spec is incomplete despite being marked implementation-ready.
    - Evidence:
      - `getSummary(verbose)` currently throws placeholder error: `docs/build-plan/05-mcp-server.md:753`, `docs/build-plan/05-mcp-server.md:757`.
      - Exit criteria require accurate percentile/error computations: `docs/build-plan/05-mcp-server.md:1188`, `docs/build-plan/05-mcp-server.md:1189`.
    - Risk:
      - Teams may treat step 5.9 as ready and discover late that core summary logic is undefined.
    - Recommendation:
      - Replace placeholder with concrete algorithm spec (sorting/percentile method, rounding, empty-state behavior, warning generation logic).

  - **High:** Diagnostics DB-status semantics are incorrect/inconsistent (reachability treated as unlocked).
    - Evidence:
      - Diagnostics report sets `database.unlocked` from health non-null only: `docs/build-plan/05-mcp-server.md:633`.
      - GUI status spec also derives DB state from `/health`: `docs/build-plan/06f-gui-settings.md:736`.
      - Auth route already defines dedicated auth-state endpoint: `docs/build-plan/04-rest-api.md:428`.
    - Risk:
      - "Unlocked" may be shown when DB is actually locked but backend process is reachable.
    - Recommendation:
      - Use `/api/v1/auth/status` (or explicit DB unlock signal) for DB lock state; keep `/health` strictly for process liveness.

  - **Medium:** `gui-actions-index.md` summary accounting for REST/client-only actions is stale.
    - Evidence:
      - Summary claims REST actions = 54 and client-only = 30: `docs/build-plan/gui-actions-index.md:282`, `docs/build-plan/gui-actions-index.md:285`.
      - Row-level check (`84` action rows) yields REST = `58`, client-only = `26` (Node parse by REST column value).
    - Risk:
      - Planning dashboards and implementation tracking can prioritize incorrect work buckets.
    - Recommendation:
      - Recompute summary from table rows and add a lightweight consistency check script.

  - **Medium:** MCP Server Status panel allows "hardcoded" tool count fallback in a read-only health panel.
    - Evidence:
      - Data source states tool count from diagnose response "(or hardcoded)": `docs/build-plan/06f-gui-settings.md:738`.
    - Risk:
      - Panel can present stale/non-authoritative diagnostics while appearing operational.
    - Recommendation:
      - Mark unknown state explicitly (`tool_count: unknown`) instead of hardcoding, or require dynamic source only.

- Open questions:
  - Should diagnostics intentionally support zero-auth mode with partial redacted fields, or require a session but remain callable?
  - Is `/version` intended to be canonical, or should all docs standardize on `/api/v1/version/`?
  - Should MCP Server Status refresh call REST only, or REST + MCP (`zorivest_diagnose`) with a defined precedence model?

- Verdict:
  - The enhancements are directionally strong, but current docs are **not implementation-safe yet** due two critical and multiple high-severity contract gaps.

- Residual risk:
  - If implemented as written, likely outcomes are failing diagnostics in locked sessions, route mismatches, and false status reporting in the GUI.

## Guardrail Output (If Required)

- Safety checks:
  - Documentation-only review output.
- Blocking risks:
  - No runtime code touched; blockers are design/contract defects.
- Verdict:
  - Safe to proceed after targeted doc corrections.

## Approval Gate

- **Human approval required for merge/release/deploy:** yes
- **Approval status:** pending
- **Approver:**
- **Timestamp:**

## Final Summary

- Status:
  - Critical review completed and handoff created.
- Next steps:
  1. Fix diagnostics callability + guard endpoint contracts in `05-mcp-server.md`, `output-index.md`, and `testing-strategy.md`.
  2. Resolve `wait_for_close` mismatch by implementing or removing the parameter contract.
  3. Replace metrics `getSummary` placeholder with full spec/logic.
  4. Correct GUI actions summary accounting for REST/client-only counts.
