# Task Handoff

## Task

- **Date:** 2026-03-06
- **Task slug:** mcp-resolved-plan-preimplementation-critical-review
- **Owner role:** reviewer
- **Scope:** Pre-implementation critical review of `.agent/context/handoffs/2026-03-06-mcp-research-synthesis-resolved-plan.md` against the current `docs/build-plan/` MCP plan and current primary sources.

## Inputs

- User request:
  - Review the plan prior to implementation
  - Do web validation
  - Use senior software developer reasoning
- Target artifact:
  - `.agent/context/handoffs/2026-03-06-mcp-research-synthesis-resolved-plan.md`
- Related local files reviewed:
  - `docs/BUILD_PLAN.md`
  - `docs/build-plan/05-mcp-server.md`
  - `docs/build-plan/05j-mcp-discovery.md`
  - `docs/build-plan/build-priority-matrix.md`
  - `docs/build-plan/mcp-planned-readiness.md`
  - `docs/build-plan/testing-strategy.md`
  - `docs/build-plan/friction-inventory.md`
  - `.agent/context/current-focus.md`
  - `AGENTS.md`
  - `GEMINI.md`
- Primary web sources validated:
  - MCP lifecycle: `https://modelcontextprotocol.io/specification/2025-06-18/basic/lifecycle`
  - MCP tools: `https://modelcontextprotocol.io/specification/2025-06-18/server/tools`
  - MCP authorization: `https://modelcontextprotocol.io/specification/2025-06-18/basic/authorization`
  - Anthropic effective agents: `https://www.anthropic.com/engineering/building-effective-agents`
  - Claude Code hooks: `https://code.claude.com/docs/en/hooks`
  - OpenAI evals: `https://developers.openai.com/api/docs/guides/evals`
  - TypeScript SDK repo: `https://github.com/modelcontextprotocol/typescript-sdk`
  - TypeScript SDK issues: `#911`, `#1106`, `#1291`, `#1564`

## Role Plan

1. orchestrator
2. researcher
3. reviewer

## Coder Output

- Changed files:
  - `.agent/context/handoffs/2026-03-06-mcp-resolved-plan-preimplementation-critical-review.md`
- Design notes:
  - Review-only session. No product or build-plan docs were modified.
  - `.agent/context/current-focus.md` was already modified in the worktree, so it was not overwritten during this review-only session.
- Commands run:
  - `Get-Content -Raw SOUL.md`
  - `Get-Content -Raw .agent/context/current-focus.md`
  - `Get-Content -Raw .agent/context/known-issues.md`
  - `Get-Content -Raw .agent/workflows/critical-review-feedback.md`
  - `Get-Content -Raw .agent/context/handoffs/2026-03-06-mcp-research-synthesis-resolved-plan.md`
  - `Get-Content -Raw docs/BUILD_PLAN.md`
  - `Get-Content -Raw docs/build-plan/friction-inventory.md`
  - `Get-Content -Raw .agent/context/handoffs/2026-03-06-docs-build-plan-friction-agentic-senior-review.md`
  - `rg -n "stdio|SSE|Streamable HTTP|HTTP-only|health|outputSchema|BM25|enable_toolset|list_changed|clientInfo|toolset|withConfirmation|withGuard|withMetrics|session management|auth|OAuth|dynamic" docs/build-plan/05-mcp-server.md docs/build-plan/05j-mcp-discovery.md docs/build-plan/build-priority-matrix.md docs/build-plan/mcp-planned-readiness.md docs/build-plan/testing-strategy.md AGENTS.md`
  - `rg -n "Default active tools|37 tools|clientInfo.name|Start with default toolsets|Load only selected toolsets|Dynamic tool loading is not supported|outputSchema|withConfirmation|original header value|never stores the raw API key" docs/build-plan/05-mcp-server.md docs/build-plan/05j-mcp-discovery.md`
  - `rg -n "HTTP-only|Auth from day-1|GPT-5.4|output schemas|Cursor's 40-tool cap is last priority|Codify the 7 directives" .agent/context/handoffs/2026-03-06-mcp-research-synthesis-resolved-plan.md .agent/context/current-focus.md`
  - `git status --short -- .agent/context/current-focus.md .agent/context/handoffs`
  - `pomera_notes search --search_term Zorivest`
- Results:
  - Produced a findings-first pre-implementation review with current-source validation.
  - Identified one architectural blocker, three major sequencing/contract gaps, and one governance drift issue.

## Tester Output

- Commands run:
  - Docs reads, grep sweeps, git-status check, and primary-source web validation
- Pass/fail matrix:
  - Target artifact reviewed: pass
  - Local MCP plan cross-check completed: pass
  - Current-source web validation completed: pass
  - Review handoff created: pass
- Repro failures:
  - None
- Coverage/test gaps:
  - This was a design review. No runtime MCP transport repros or client compatibility tests were executed.

## Reviewer Output

- Findings by severity:
  - **Critical-1:** The resolved plan makes `HTTP-only` and `auth from day-1` a Phase 1 commitment without defining the actual token lifecycle contract. The target artifact moves transport/auth complexity forward at `.agent/context/handoffs/2026-03-06-mcp-research-synthesis-resolved-plan.md:13` and `.agent/context/handoffs/2026-03-06-mcp-research-synthesis-resolved-plan.md:14`, but the current MCP plan still says the server "never stores the raw API key" while also saying it re-authenticates using the original header value at `docs/build-plan/05-mcp-server.md:283`. That is not implementable as written. MCP authorization is explicitly an HTTP-transport concern, not a generic MCP concern, and the spec now requires resource-server behavior: HTTP implementations should follow the authorization spec, every request carries `Authorization`, tokens must be audience-bound, and token storage/rotation must be handled securely.[1][2] Before implementation starts, this needs a concrete ADR-level decision: where the bootstrap credential lives after startup, whether refresh is possible without retaining that secret, what gets rotated, and how audience validation is enforced.
  - **High-1:** The pre-implementation plan is still optimizing the baseline for the wrong client. The resolved plan says Cursor is last-priority at `.agent/context/handoffs/2026-03-06-mcp-research-synthesis-resolved-plan.md:31`, yet the current MCP plan sizes the default loadout to 37 tools specifically to fit Cursor's 40-tool limit at `docs/build-plan/05-mcp-server.md:747`, starts dynamic mode with the 37-tool default at `docs/build-plan/05-mcp-server.md:798`, and maps behavior primarily from `clientInfo.name` at `docs/build-plan/05-mcp-server.md:811` and `docs/build-plan/05-mcp-server.md:817`. The MCP lifecycle spec says initialization exists to exchange and negotiate capabilities first, with `clientInfo` as implementation metadata, not as the primary contract.[3] Senior recommendation: freeze one day-1 client target and a capability matrix before building `ToolsetRegistry`, dynamic loading, or IDE-template generation. Capability-first, client-name fallback.
  - **High-2:** The structured-output addition is directionally correct, but the plan overstates maturity and under-specifies compatibility fallback. The resolved plan says structured output schemas enable typed client consumption at `.agent/context/handoffs/2026-03-06-mcp-research-synthesis-resolved-plan.md:102`, while the current MCP plan still documents text-only tool output at `docs/build-plan/05-mcp-server.md:1000`. The MCP tools spec now says a tool returning `structuredContent` should also return serialized JSON in `content[].text` for backward compatibility, and official SDK issue `#911` remains open because client handling of `structuredContent` is inconsistent.[4][5] The implementation plan should therefore require dual-format responses and contract tests that assert both `structuredContent` and text envelopes, not rely on `outputSchema` alone.
  - **High-3:** The plan imports friction findings as design truth without a status gate per pinned SDK version. The target artifact still treats FR-6.x as a standing Phase 1 transport driver at `.agent/context/handoffs/2026-03-06-mcp-research-synthesis-resolved-plan.md:13`, but upstream issue status has already diverged: TypeScript SDK issue `#1106` is closed, while `#1291` and `#1564` remain open.[6][7][8] The SDK repo also states that `main` is pre-alpha v2 and that v1.x remains the recommended production line for now.[9] That means the friction inventory is still valuable, but it should become a live "pinned-version issue matrix" instead of a static architectural premise. Otherwise implementation sequencing will be driven by stale bugs and miss live ones.
  - **Medium-1:** Workflow governance is not yet in a ready-to-code state. The resolved plan says "GPT-5.4 (upgrade now)" at `.agent/context/handoffs/2026-03-06-mcp-research-synthesis-resolved-plan.md:53` and says the directive must be codified at `.agent/context/handoffs/2026-03-06-mcp-research-synthesis-resolved-plan.md:133`, but the current execution doc still says GPT 5.3 is the validation baseline and that the shift to GPT-5.4 remains undecided at `.agent/context/current-focus.md:9`, `.agent/context/current-focus.md:16`, and `.agent/context/current-focus.md:30`. OpenAI's docs now show GPT-5.4 as the latest model track, so the problem is no longer model availability; it is local governance drift.[10] Resolve the baseline in `.agent` config before the first implementation session, or the dual-agent workflow will start with conflicting operating rules.

- Open questions:
  - What is the exact day-1 MCP client target: Antigravity only, one VS Code path, or both?
  - If HTTP-only remains the decision, what is the exact bootstrap-secret lifecycle after the first `401`?
  - Are output schemas intended as a server-internal contract aid, or as a hard client-facing dependency from day 1?

- Verdict:
  - **changes_required**
  - The plan is strong in research quality and direction, but it is not implementation-ready until the day-1 transport/auth contract and client-target strategy are made explicit.

- Residual risk:
  - MCP ecosystem details are still moving. Without a pinned-version issue matrix and capability-first baseline, the first implementation slice will absorb churn that should stay in planning.

## Detailed Review

## Senior Judgment

The resolved plan is better than most pre-implementation plans because it is not naive about MCP. It correctly assumes rough edges in transport, schemas, auth, and client behavior.

The problem is not that it is too cautious. The problem is that it jumps from "known friction exists" to "several high-cost mitigations are now day-1 architecture" without first locking the minimum viable runtime contract. The missing contract is not abstract architecture. It is operational:

1. Which transport is the baseline?
2. Which client is the baseline?
3. How is auth actually persisted and rotated?
4. What is the minimum response contract every tool must satisfy?

Until those four are frozen, Phase 5 can still expand sideways faster than it moves forward.

## Recommended Pre-Implementation Changes

1. Write a short ADR named `mcp-day1-baseline.md` before coding. It should decide:
   - transport
   - day-1 client target
   - auth/bootstrap/refresh secret lifecycle
   - default tool cohort
   - response contract (`text` only vs dual `text` + `structuredContent`)

2. Update `05-mcp-server.md` before implementation starts:
   - capability-first detection
   - dual-format structured outputs
   - pinned SDK version + issue matrix
   - exact auth resource-server rules for HTTP mode

3. Resolve workflow governance before MEU-1:
   - lock reviewer baseline in `.agent` config
   - decide whether Claude hooks or an equivalent validation harness will enforce evidence collection and post-tool checks

## Web Validation Notes

- Anthropic's agent guidance still clearly favors the simplest viable system first and recommends adding complexity only when it demonstrably improves outcomes.[11]
- Anthropic's hooks model is mature enough to support session-start and post-tool validation hooks, which is directly useful if Opus is the implementation agent and reviewer evidence quality must stay high.[12]
- OpenAI's eval tooling continues to reinforce artifact-based review over prose-only review by exposing per-criterion results and regression-oriented workflows.[13]

## Approval Gate

- **Human approval required for merge/release/deploy:** yes
- **Approval status:** pending

## Final Summary

- Status:
  - Completed. Pre-implementation review finished with primary-source validation.
- Next steps:
  1. Resolve the transport/auth ADR.
  2. Re-scope the day-1 client/tool baseline around capabilities, not Cursor compatibility.
  3. Codify the reviewer baseline and only then start MCP implementation planning.

## Sources

1. MCP Authorization, protocol requirements and HTTP-vs-STDIO rules: `modelcontextprotocol.io/specification/2025-06-18/basic/authorization` (lines 95-104, 211-226, 249-256)
2. MCP Authorization, token audience binding and secure token storage: `modelcontextprotocol.io/specification/2025-06-18/basic/authorization` (lines 225-256, 282-286)
3. MCP Lifecycle, initialization and capability negotiation: `modelcontextprotocol.io/specification/2025-06-18/basic/lifecycle` (lines 87-97, 168-170)
4. MCP Tools, `structuredContent` and backward-compatible text content: `modelcontextprotocol.io/specification/2025-06-18/server/tools` (lines 320-350, 372-386)
5. TypeScript SDK issue `#911`, inconsistent `structuredContent` handling across clients: `github.com/modelcontextprotocol/typescript-sdk/issues/911` (lines 212-216)
6. TypeScript SDK issue `#1106` status: `github.com/modelcontextprotocol/typescript-sdk/issues/1106` (line 181)
7. TypeScript SDK issue `#1291` status: `github.com/modelcontextprotocol/typescript-sdk/issues/1291` (lines 171-187)
8. TypeScript SDK issue `#1564` status: `github.com/modelcontextprotocol/typescript-sdk/issues/1564` (lines 171-199)
9. TypeScript SDK repo, v2 on `main`, v1.x still recommended for production: `github.com/modelcontextprotocol/typescript-sdk` (lines 302-304)
10. OpenAI API docs nav, GPT-5.4 listed as latest and eval tooling present: `developers.openai.com/api/docs/guides/evals` (lines 34, 61-62)
11. Anthropic, "Building effective agents": `anthropic.com/engineering/building-effective-agents` (lines 17-18, 30-31, 130)
12. Claude Code hooks, `SessionStart` and `PostToolUse`: `code.claude.com/docs/en/hooks` (lines 750-792, 1099-1140)
13. OpenAI evals guide, per-criterion results and regression resources: `developers.openai.com/api/docs/guides/evals` (lines 1845-1914)
