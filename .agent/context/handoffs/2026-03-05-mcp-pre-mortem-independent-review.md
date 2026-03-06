# Task Handoff Template

## Task

- **Date:** 2026-03-05
- **Task slug:** mcp-pre-mortem-independent-review
- **Owner role:** reviewer
- **Scope:** Independent review of 5 MCP friction research documents, then comparison against `.agent/context/known-issues.md` and `docs/build-plan/friction-inventory.md`.

## Inputs

- User request:
  - Review five research papers in `_inspiration/pre-mortem_risk_mining_research/`
  - Review `.agent/context/known-issues.md`
  - Review `docs/build-plan/friction-inventory.md`
  - Produce independent comparison report in `.agent/context/handoffs/`
- Specs/docs referenced:
  - `_inspiration/pre-mortem_risk_mining_research/1 - gemini - Python MCP Friction Analysis.md`
  - `_inspiration/pre-mortem_risk_mining_research/2 - chatgpt - TypeScript MCP Server Friction Analysis for @modelcontextprotocol-sdk v1.x.md`
  - `_inspiration/pre-mortem_risk_mining_research/3 - claude - Friction inventory for large-scale MCP servers.md`
  - `_inspiration/pre-mortem_risk_mining_research/4 - gemini - MCP Architecture Friction Research.md`
  - `_inspiration/pre-mortem_risk_mining_research/5 - claude - Pre-mortem risk analysis for a 68-tool MCP server.md`
  - `.agent/context/known-issues.md`
  - `docs/build-plan/friction-inventory.md`
- Constraints:
  - Independent conclusion first, then compare with existing reviewer conclusions.

## Role Plan

1. orchestrator
2. researcher
3. reviewer

## Coder Output

- Changed files:
  - `.agent/context/handoffs/2026-03-05-mcp-pre-mortem-independent-review.md`
- Design notes:
  - Review-only session; no product code/docs modified outside this handoff.
- Commands run:
  - `Get-Content -Raw` on all 7 input markdown files
  - Context bootstrap reads: `SOUL.md`, `.agent/context/current-focus.md`, `.agent/context/known-issues.md`
  - `pomera_notes search` for `Zorivest`
- Results:
  - Independent findings established and compared to current known issue/friction artifacts.

## Tester Output

- Commands run:
  - Document reads only (no code execution/tests required for this task).
- Pass/fail matrix:
  - Source coverage: 7/7 target docs reviewed
  - Independent-vs-existing comparison produced: yes
  - Implementation/test execution required: no
- Repro failures:
  - None
- Coverage/test gaps:
  - This is a qualitative architecture risk review; no runtime validation performed.

## Reviewer Output

- Findings by severity:
  - **Critical-1:** Tool-surface strategy is a hard architectural blocker, not a tuning issue. A flat 68-tool registration will fail in at least Cursor-class clients due to hard caps and tool-selection degradation. Independent conclusion: adopt a tiered exposure model (static constrained mode + dynamic mode + full mode), with safe fallback when client detection is uncertain.
  - **Critical-2:** Tool registration/schema failure modes are currently the highest implementation-risk zone (silent argument stripping via `server.tool` shape mismatch, `$ref/$defs` client breakage, Zod conversion edge cases). Independent conclusion: enforce a single schema authoring contract plus startup/CI invariants on emitted `tools/list`.
  - **Critical-3:** Auth lifecycle failures are systemic across MCP clients. Independent conclusion: treat token lifecycle as server-owned state machine with proactive refresh window + refresh mutex + retry discipline; never rely on client refresh behavior.
  - **Critical-4:** Transport reliability remains unstable across Streamable HTTP and stdio edge cases (session lifecycle misuse, async timeout behavior, EPIPE/disconnect crashes). Independent conclusion: production baseline should be stdio-first where possible with strict transport lifecycle tests and explicit disconnect handling.
  - **Critical-5:** Trade execution safety cannot rely on conversational HITL prompts. Independent conclusion: destructive tools need server-side confirmation semantics (nonce/token + second-step commit), independent of client UI support for annotations.

  - **High-1:** Cross-platform process management is under-specified for Windows detachment/orphan prevention relative to known Node limitations. Independent conclusion: require platform-specific process supervision strategy and cleanup guarantees before rollout.
  - **High-2:** Type drift between TS (Zod) and Python (Pydantic/FastAPI) is a realistic failure source in a proxy architecture. Independent conclusion: schema source-of-truth + normalization layer (null/undefined, enum case, datetime format) is needed to prevent 422 churn and model confusion.
  - **High-3:** Response-shape and payload-size constraints need explicit contract rules (root object envelope, paging thresholds, binary/image size policy), otherwise clients will truncate/drop content in inconsistent ways.

  - **Medium-1:** Dynamic toolset approaches depend on `list_changed` support that is inconsistent across clients; this should be treated as opportunistic optimization, not guaranteed behavior.
  - **Medium-2:** SDK v2 migration risk is material and should be isolated behind adapter boundaries now to avoid coupling business logic to changing SDK surfaces.

- Agreement with `.agent/context/known-issues.md`:
  - **Strong agreement (5/5 active issues):**
  - `MCP-TOOLCAP`: independent conclusion matches; hard caps are structurally blocking for flat 68-tool mode.
  - `MCP-ZODSTRIP`: independent conclusion matches; silent schema/argument failure is critical.
  - `MCP-AUTHRACE`: independent conclusion matches; refresh race is high-likelihood/high-impact.
  - `MCP-WINDETACH`: independent conclusion matches; Windows detach/process lifecycle is unresolved risk.
  - `MCP-HTTPBROKEN`: independent conclusion aligns on instability and need for conservative transport posture.

- Agreement with `docs/build-plan/friction-inventory.md`:
  - **Strong agreement:** The inventory correctly prioritizes tool caps, schema fragility, auth lifecycle, transport failure modes, and process management as top risks.
  - **Strong agreement:** Added areas (REST proxy network friction, type-system drift, trade-safety gap, SDK migration) are directionally correct and relevant for Zorivest’s hybrid architecture.
  - **Strong agreement:** Three-tier client strategy and server-side confirmation are valid differentiators.

- Divergences / independent perspective differences:
  - **Divergence-1 (Scope discipline):** Current inventory is very broad (14 friction areas) with mixed evidence quality. Independent view: convert to a tighter implementation gate set with explicit "must-have before coding" controls:
  - (a) tool exposure tiering + fallback
  - (b) schema contract gate (startup + CI)
  - (c) token state machine with mutex
  - (d) transport lifecycle test suite
  - (e) process supervision per OS
  - (f) destructive-action confirmation contract
  - **Divergence-2 (Confidence weighting):** Some sections rely heavily on forum/blog evidence; those should be marked as directional until reproduced in-house. Independent view: split each friction item into `externally-reported` vs `internally-verified` status to avoid overfitting design to unverified incidents.
  - **Divergence-3 (Dynamic toolset dependency):** Inventory treats dynamic toolsets as a central mitigation. Independent view: for immediate reliability, static constrained mode should be the default safe baseline, and dynamic mode should be additive where client support is proven.
  - **Divergence-4 (Prioritization order):** Independent ordering for implementation risk burn-down:
  - (1) schema/registration guardrails
  - (2) auth/token lifecycle correctness
  - (3) process/transport reliability
  - (4) tool-tiering UX optimization
  - (5) migration hardening and advanced ergonomics

- Open questions:
  - What is the authoritative initial client support matrix for day-1 release (exact clients, versions, and required capabilities)?
  - Is Zorivest willing to make static constrained mode (<=40) the default until dynamic behavior is verified per-client?
  - Which destructive trade actions require two-phase confirmation versus single-phase execution with guardrails?

- Verdict:
  - **approved with conditions**
  - Existing conclusions are largely correct; no major contradiction found.
  - Recommend converting the broad inventory into a smaller set of implementation gates and verification checkpoints before execution.

- Residual risk:
  - Without in-house reproduction tests, externally-reported SDK/client failures may be mis-prioritized.
  - Client behavior drift (especially around tool limits/notifications) can invalidate assumptions quickly.

## Guardrail Output (If Required)

- Safety checks:
  - Verified that the independent review does not relax financial-action safeguards.
- Blocking risks:
  - Server-side confirmation workflow remains a pre-release blocker for live/destructive trade tools.
- Verdict:
  - Guardrail concerns acknowledged; no additional blocker beyond findings above.

## Approval Gate

- **Human approval required for merge/release/deploy:** yes
- **Approval status:** pending
- **Approver:**
- **Timestamp:**

## Final Summary

- Status:
  - Independent review completed; conclusions substantially align with prior reviewer artifacts.
- Next steps:
  1. Convert friction inventory into a "release gate checklist" with pass/fail criteria per gate.
  2. Add an internal reproduction matrix for top 10 critical/high frictions (client × transport × schema × auth).
  3. Update `known-issues.md` statuses after first reproduction pass (`externally-reported` → `internally-verified` or `deferred`).
