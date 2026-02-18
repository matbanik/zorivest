# Task Handoff

## Task

- **Date:** 2026-02-18
- **Task slug:** build-plan-mcp-guard-emergency-stop-critical-review
- **Owner role:** reviewer
- **Scope:** Critical review of build-plan updates for MCP circuit breaker (cost/rate/abuse prevention) and emergency stop flows.

## Inputs

- User request:
  - Review updated build-plan docs for MCP-level circuit breaker and panic button.
  - Create a critical-review handoff in `.agent/context/handoffs`.
- Specs/docs referenced:
  - `docs/build-plan/00-overview.md`
  - `docs/build-plan/02-infrastructure.md`
  - `docs/build-plan/04-rest-api.md`
  - `docs/build-plan/05-mcp-server.md`
  - `docs/build-plan/06f-gui-settings.md`
  - `docs/build-plan/input-index.md`
  - `docs/build-plan/build-priority-matrix.md`
  - `docs/build-plan/02a-backup-restore.md`
  - `.agent/context/handoffs/TEMPLATE.md`
- Constraints:
  - Findings-first, severity-ranked, with concrete file/line evidence.
  - Focus on behavioral/security/regression risk, not style.

## Role Plan

1. orchestrator
2. reviewer
3. coder (doc output only)
4. tester (doc consistency verification)
- Optional roles: researcher, guardrail (not used)

## Coder Output

- Changed files:
  - `.agent/context/handoffs/2026-02-18-build-plan-mcp-guard-emergency-stop-critical-review.md` (new)
- Design notes:
  - Documentation-only review artifact; no runtime code changes.
- Commands run:
  - `git diff -- docs/build-plan/...` for updated files
  - `rg -n` for cross-file contract tracing (`mcp-guard`, `lock`, `unlock`, `auth`)
  - `Get-Content` with line numbering for evidence capture
- Results:
  - Multiple contract and operability risks identified in current MCP guard design docs.

## Tester Output

- Commands run:
  - Documentation consistency inspection only.
- Pass/fail matrix:
  - Not applicable (no executable code changed).
- Repro failures:
  - Not applicable.
- Coverage/test gaps:
  - Missing tests for threshold auto-lock behavior and no executable test example for emergency-stop tool invocation.

## Reviewer Output

- Findings by severity:

  - **Critical:** Guard endpoint authentication contract is internally inconsistent across REST, MCP, GUI, and tests.
    - Evidence:
      - Route doc says unlock requires active session: `docs/build-plan/04-rest-api.md:512`.
      - Guard route signatures show no explicit auth dependency and tests call routes without auth: `docs/build-plan/04-rest-api.md:493`, `docs/build-plan/04-rest-api.md:535`.
      - MCP middleware always sends auth headers (`getAuthHeaders`) to `/mcp-guard/check`: `docs/build-plan/05-mcp-server.md:392`, `docs/build-plan/05-mcp-server.md:394`.
      - GUI examples call `/mcp-guard/*` without any auth header/session handling details: `docs/build-plan/06f-gui-settings.md:600`, `docs/build-plan/06f-gui-settings.md:614`.
    - Risk:
      - Teams will either (A) enforce auth and break GUI flows as documented, or (B) leave routes effectively open and undermine abuse prevention intent.
    - Recommendation:
      - Define one canonical auth model for all `/api/v1/mcp-guard/*` routes and apply it consistently in REST route dependencies, GUI request examples, MCP middleware, and e2e tests (including explicit 401/403 cases).

  - **High:** Standalone MCP mode can self-lock with no in-band MCP recovery path.
    - Evidence:
      - Standalone mode is explicitly supported: `docs/build-plan/05-mcp-server.md:271`.
      - Emergency stop tool is intentionally unguarded and always available: `docs/build-plan/05-mcp-server.md:463`.
      - Block/lock messages direct users to GUI for unlock: `docs/build-plan/05-mcp-server.md:412`, `docs/build-plan/05-mcp-server.md:447`.
      - Input index exposes lock via MCP but unlock only on GUI/REST surfaces (no MCP unlock action): `docs/build-plan/input-index.md:517`, `docs/build-plan/input-index.md:518`.
    - Risk:
      - A mistaken `zorivest_emergency_stop` call in IDE-only deployments can halt MCP workflows until an out-of-band manual action is discovered.
    - Recommendation:
      - Add a scoped `zorivest_emergency_unlock` MCP tool (admin + confirmation) or explicitly define and test a documented non-GUI recovery path in Phase 5/7.

  - **High:** Core rate-limit behavior is specified but not tested.
    - Evidence:
      - `/mcp-guard/check` contract includes counter increments and auto-lock on threshold: `docs/build-plan/04-rest-api.md:515`, `docs/build-plan/04-rest-api.md:519`.
      - REST e2e tests cover status, lock/unlock, config, reason only: `docs/build-plan/04-rest-api.md:528`, `docs/build-plan/04-rest-api.md:548`.
      - MCP vitest examples do not assert threshold-hit behavior or counter window semantics: `docs/build-plan/05-mcp-server.md:477`, `docs/build-plan/05-mcp-server.md:501`.
    - Risk:
      - The primary cost/rate control behavior can regress without detection.
    - Recommendation:
      - Add tests for: threshold exceed -> auto-lock, lock reason `rate_limit_exceeded`, window reset, and disabled-guard bypass behavior.

  - **Medium:** Emergency-stop vitest example is non-executable as written.
    - Evidence:
      - Test asserts `fetch` call but does not invoke any tool handler before assertion: `docs/build-plan/05-mcp-server.md:501`, `docs/build-plan/05-mcp-server.md:506`.
    - Risk:
      - Direct copy of the spec test will fail or provide false confidence in implementation quality.
    - Recommendation:
      - Update example to register the tool, invoke `zorivest_emergency_stop`, then assert fetch payload and returned MCP content.

  - **Medium:** `lock_reason` semantics drift across model, API, MCP, and input index.
    - Evidence:
      - Model comment constrains reason values to manual/rate-limit forms: `docs/build-plan/02-infrastructure.md:204`.
      - REST schema accepts unrestricted string reason: `docs/build-plan/04-rest-api.md:485`.
      - MCP tool default reason uses different phrasing (`Agent self-lock`): `docs/build-plan/05-mcp-server.md:436`.
      - Input index describes reason as generic auto/manual text: `docs/build-plan/input-index.md:519`.
    - Risk:
      - Inconsistent reason taxonomy complicates auditing, analytics, and policy-based unlock workflows.
    - Recommendation:
      - Canonicalize to `reason_code` enum + optional `reason_detail`, or explicitly standardize free-text policy across all docs.

  - **Medium:** Build order places MCP guard after core MCP delivery, delaying abuse controls.
    - Evidence:
      - Core MCP tool delivery is P0: `docs/build-plan/build-priority-matrix.md:32`.
      - MCP guard is scheduled as item 30a in P1.5: `docs/build-plan/build-priority-matrix.md:75`.
    - Risk:
      - Earliest MCP releases can ship without the documented circuit-breaker protections.
    - Recommendation:
      - Move item 30a earlier (P0 alongside items 13–15) or explicitly mark guard as required before enabling MCP in release criteria.

- Open questions:
  - Should `/api/v1/mcp-guard/*` use bearer session auth, GUI session auth, both, or localhost-only trust?
  - Is standalone MCP expected to be fully recoverable without launching GUI?
  - Is `lock_reason` intended for strict machine-readable policy (`enum`) or operator text (`free-form`)?

- Verdict:
  - Direction is strong, but **not implementation-safe yet** due one critical auth-contract conflict and two high-severity operational/test gaps.

- Residual risk:
  - If implemented as-is, likely outcomes are inconsistent auth behavior, accidental MCP lockouts in standalone mode, and unverified rate-limit enforcement.

## Guardrail Output (If Required)

- Safety checks:
  - Documentation-only review output.
- Blocking risks:
  - No runtime changes in this task; blockers are design-contract level only.
- Verdict:
  - Safe to proceed with targeted documentation corrections before implementation.

## Approval Gate

- **Human approval required for merge/release/deploy:** yes
- **Approval status:** pending
- **Approver:**
- **Timestamp:**

## Final Summary

- Status:
  - Critical review completed and documented.
- Next steps:
  1. Resolve auth model for `/mcp-guard/*` and align REST/MCP/GUI examples plus tests.
  2. Define and test an explicit standalone unlock recovery flow.
  3. Add missing threshold auto-lock tests and fix emergency-stop vitest example to be executable.

