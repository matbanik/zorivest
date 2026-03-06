# Task Handoff Template

## Task

- **Date:** 2026-03-06
- **Task slug:** docs-build-plan-friction-agentic-senior-review
- **Owner role:** reviewer
- **Scope:** Critical review of `docs/build-plan/` from the perspective of `docs/build-plan/friction-inventory.md`, with official web research on simplicity-first coding and the best starting approach for agentic implementation.

## Inputs

- User request:
  - Critically review the `docs/build-plan/` files through the lens of `friction-inventory.md`
  - Use web research to find angles not yet covered for coding approach, simplicity-first implementation, and best first steps for agentic delivery
  - Create a feedback document in `.agent/context/handoffs/`
  - Evaluate the dual-agent setup where Opus 4.6 is the implementation agent and GPT-5.4 is the reviewer/tester
  - Provide an opinion on the pre-emptive friction analysis, especially given MCP immaturity
- Specs/docs referenced:
  - `docs/BUILD_PLAN.md`
  - `docs/build-plan/00-overview.md`
  - `docs/build-plan/build-priority-matrix.md`
  - `docs/build-plan/testing-strategy.md`
  - `docs/build-plan/friction-inventory.md`
  - `docs/build-plan/01-domain-layer.md`
  - `docs/build-plan/01a-logging.md`
  - `docs/build-plan/02-infrastructure.md`
  - `docs/build-plan/02a-backup-restore.md`
  - `docs/build-plan/03-service-layer.md`
  - `docs/build-plan/04-rest-api.md`
  - `docs/build-plan/05-mcp-server.md`
  - `docs/build-plan/05j-mcp-discovery.md`
  - `docs/build-plan/mcp-tool-index.md`
  - `docs/build-plan/mcp-planned-readiness.md`
  - `docs/build-plan/06-gui.md`
  - `docs/build-plan/06a-gui-shell.md`
  - `docs/build-plan/06e-gui-scheduling.md`
  - `docs/build-plan/06f-gui-settings.md`
  - `docs/build-plan/07-distribution.md`
  - `docs/build-plan/08-market-data.md`
  - `docs/build-plan/09-scheduling.md`
  - `docs/build-plan/10-service-daemon.md`
  - `docs/build-plan/dependency-manifest.md`
  - `docs/build-plan/input-index.md`
  - `docs/build-plan/output-index.md`
  - `docs/build-plan/gui-actions-index.md`
  - `docs/build-plan/domain-model-reference.md`
- Official web research:
  - MCP introduction: `https://modelcontextprotocol.io/introduction`
  - MCP architecture: `https://modelcontextprotocol.io/specification/2025-11-05/architecture/index`
  - MCP lifecycle: `https://modelcontextprotocol.io/specification/2025-11-05/basic/lifecycle`
  - MCP tools: `https://modelcontextprotocol.io/specification/2025-06-18/server/tools`
  - MCP security best practices: `https://modelcontextprotocol.io/specification/2025-11-05/basic/security_best_practices`
  - MCP authorization: `https://modelcontextprotocol.io/specification/2025-11-05/basic/authorization`
  - MCP draft schema: `https://modelcontextprotocol.io/specification/draft/schema`
  - Anthropic effective agents: `https://www.anthropic.com/engineering/building-effective-agents`
  - Claude Code sub-agents: `https://docs.anthropic.com/en/docs/claude-code/sub-agents`
  - Claude Code hooks: `https://docs.anthropic.com/en/docs/claude-code/hooks`
  - Claude Opus 4.6 announcement: `https://www.anthropic.com/news/claude-opus-4-6`
  - OpenAI eval design: `https://platform.openai.com/docs/guides/evals-design`
  - OpenAI agents guide: `https://platform.openai.com/docs/guides/agents`
  - GPT-5.4 announcement: `https://openai.com/index/introducing-gpt-5-4/`
- Constraints:
  - Senior-software-developer perspective per major build-plan area, plus whole-plan judgment
  - Emphasize coding practicality, sequencing, and simplicity-first implementation
  - Treat Opus 4.6 as coder and GPT-5.4 as reviewer/tester
  - Review is documentation and architecture guidance only; no product implementation requested

## Role Plan

1. orchestrator
2. researcher
3. reviewer
4. guardrail

## Coder Output

- Changed files:
  - `.agent/context/handoffs/2026-03-06-docs-build-plan-friction-agentic-senior-review.md`
  - `.agent/context/current-focus.md`
- Design notes:
  - Review-only session. No product code or plan docs were modified.
  - The goal was not to re-summarize the build plan, but to pressure-test sequencing and implementation posture using the friction inventory as the governing lens.
  - Official sources were used for MCP, Anthropic agent workflow guidance, and OpenAI eval/reviewer guidance.
- Commands run:
  - `Get-Content -Raw` across the target build-plan docs
  - `rg -n "^#{1,3} " docs/build-plan`
  - `pomera_notes search` for `Zorivest`
  - Official web reads via browser tooling
- Results:
  - Produced a whole-plan senior review with concrete implementation sequencing advice
  - Converted the friction-inventory perspective into rollout guidance rather than a generic caution list
  - Added explicit advice for the Opus 4.6 -> GPT-5.4 dual-agent workflow

## Tester Output

- Commands run:
  - Document reads only; no runtime validation or code tests were applicable to this task
- Pass/fail matrix:
  - Target docs reviewed: pass
  - Official-source research completed: pass
  - Senior review handoff created: pass
  - Current session context updated: pass
- Repro failures:
  - None
- Coverage/test gaps:
  - This is a qualitative architecture review. No code execution, transport repro, or client compatibility testing was performed here.
- Evidence bundle location:
  - `.agent/context/handoffs/2026-03-06-docs-build-plan-friction-agentic-senior-review.md`
- FAIL_TO_PASS / PASS_TO_PASS result:
  - N/A
- Mutation score:
  - N/A
- Contract verification status:
  - N/A

## Reviewer Output

- Findings by severity:
  - **Critical-1:** The build plan is strong, but it still needs an explicit simplicity-first rollout rule. Without it, the friction inventory can accidentally justify building too much defensive architecture before the first usable slice exists.
  - **Critical-2:** Phase 5 MCP work should not start with the full ambition implied by the long-term plan. The safe starting point is a static, constrained, stdio-first baseline with a small tool set, capability negotiation, structured outputs, and one supported client target.
  - **Critical-3:** The plan is strongest in Phases 1 through 4 and weakest where complexity multiplies across uncertain ecosystems: Phase 5 MCP, Phase 9 scheduling, and Phase 10 service daemon. Those areas need explicit entry gates, not just good design notes.
  - **High-1:** The Opus 4.6 + GPT-5.4 dual-agent model is viable if GPT-5.4 is used as an eval-driven reviewer/tester, not as a prose critic. It should validate commands, contracts, and failure cases against artifacts, not only comment on implementation style.
  - **High-2:** MCP client behavior should be driven primarily by negotiated capabilities from initialization, not by client-name heuristics. Client detection still matters, but only as fallback behavior.
  - **High-3:** Structured tool outputs should be treated as first-class contracts from day 1. Returning JSON as free-form text is an avoidable source of tool ambiguity and review difficulty.
  - **High-4:** Logging, backup/restore, settings, and release/distribution planning are all sound, but they can steal early implementation bandwidth if treated as blockers before the first vertical slice exists.
  - **Medium-1:** Market-data breadth, scheduling flexibility, and service-daemon platform coverage are all strategically sensible, but they should be sequenced as expansion programs rather than early architecture drivers.
  - **Medium-2:** The current plan would benefit from an explicit distinction between `prototype mode`, `single-client production baseline`, and `multi-client/generalized platform mode`.
- Open questions:
  - What is the exact day-1 MCP client target matrix?
  - Which initial tool cohort is small enough to validate contracts without triggering tool-cap or discoverability problems?
  - Does the team want GPT-5.4 to formally replace GPT 5.3 as the standing reviewer baseline for the Phase 1 MEU workflow?
- Verdict:
  - **approved with conditions**
  - The plan is materially above average in rigor and foresight.
  - The next improvement is not more breadth. It is sharper sequencing and stricter simplicity gates.
- Residual risk:
  - MCP assumptions can drift quickly because the ecosystem is still changing.
  - If the first implementation slice tries to satisfy too many known frictions at once, delivery speed will collapse without reducing the highest risks.

## Detailed Review

## Executive Judgment

The build plan is better than most architecture plans because it already assumes hostile reality: flaky clients, contract drift, SDK churn, auth races, and the need for evidence-based validation. That is the correct mindset for finance software and doubly correct for MCP work.

The main weakness is not missing ideas. It is that the plan is now rich enough to tempt an overbuilt first implementation. The answer is not to remove the friction inventory. The answer is to turn it into rollout gates that control when complexity is allowed to enter the system.

## Section-by-Section Review

| Area | Senior view | Friction-inventory lens | Simplicity-first recommendation |
|---|---|---|---|
| `00-overview.md`, `build-priority-matrix.md`, `testing-strategy.md`, `dependency-manifest.md`, indexes | Strong planning spine. The repo has real delivery discipline, not just architecture prose. | Good at surfacing contract and dependency drift risk, but it still lacks a hard "what we will not build yet" rule. | Add explicit phase entry/exit gates and a `prototype mode` policy. Make early success mean "one slice works and is testable", not "framework completeness". |
| `01-domain-layer.md`, `domain-model-reference.md` | Correct starting point. The plan is right to begin in the domain. | Low friction here compared with later phases; the main risk is speculative abstraction. | Start with the calculator pilot and one minimal persistent domain slice. Keep the domain model as small as the first use cases permit. |
| `01a-logging.md` | Observability/redaction thinking is strong and finance-appropriate. | Important for agentic auditability, but easy to over-invest in before business behavior exists. | Ship the minimum: structured logging, correlation IDs, redaction policy, and deterministic test assertions. Delay fancy sinks/formatters/telemetry layers. |
| `02-infrastructure.md`, `02a-backup-restore.md` | Thoughtful and safety-conscious. Encryption, defaults, and restore concerns are real. | Many valid frictions are captured, but most do not have to block the first vertical slice. | Build the smallest persistence path that supports one real use case. Treat backup/restore and import/export as second-wave hardening unless the first slice explicitly depends on them. |
| `03-service-layer.md` | Solid boundary design. The service layer is the right place for orchestration and policy. | Risk is premature orchestration complexity before domain behavior is proven. | Keep initial application services thin and boring. Use explicit commands/results. Avoid policy engines or broad workflow abstractions at the start. |
| `04-rest-api.md` | Good separation of transport from application logic and a healthy contract mindset. | Type normalization and error-shape drift are real risks, especially with dual-language boundaries. | Start with a few endpoints and contract tests. Prove exact DTO/error behavior before expanding status codes and cross-cutting API machinery. |
| `05-mcp-server.md`, `05j-mcp-discovery.md`, `mcp-tool-index.md`, `mcp-planned-readiness.md` | This is the most strategically important and most implementation-fragile part of the plan. The analysis quality is good. | The friction inventory is most valuable here: tool caps, schema breakage, auth lifecycle bugs, transport instability, client inconsistency, and process-management issues are all real. | Start with static stdio, 8 to 12 read-only or low-risk tools, one client target, server-owned auth state, capability-first behavior, and SDK isolation behind adapters. Do not start with dynamic toolsets, HTTP transport, or a large tool catalog. |
| `06-gui.md`, `06a-gui-shell.md`, `06e-gui-scheduling.md`, `06f-gui-settings.md` | Good decomposition. The GUI plan is mature enough to avoid chaos later. | GUI parity pressure can amplify backend contract churn if it is used too early as a proving ground. | Let the GUI consume already-proven service/API behavior. Keep the first shell thin and avoid using the GUI to validate novel MCP behavior. |
| `07-distribution.md` | Release/versioning thoughtfulness is good. Many teams defer this too long. | Low immediate friction value for initial implementation throughput. | Keep the design notes, but do not spend early cycles operationalizing packaging until one backend path and one client path are stable. |
| `08-market-data.md` | Strategically useful, but broad. Provider breadth increases integration cost fast. | External API variance, rate limits, and normalization issues can easily dominate the first implementation. | Start with one provider and one narrow use case. Keep the provider abstraction, but do not implement optional breadth early. |
| `09-scheduling.md` | Deep and ambitious. It reads like a second major program, not a small extension. | High friction area because it compounds domain rules, time semantics, pipelines, rendering, and operator expectations. | Do not let this phase shape the early architecture more than necessary. If scheduling starts early, define a minimal profile with one or two safe step types and no broad pipeline engine yet. |
| `10-service-daemon.md` | Well-considered, especially for platform behavior. | Windows/Linux/macOS process lifecycle issues are real and under-validated in many agent systems. | Treat daemonization as late hardening. In development, prefer manual or foreground execution. Only formalize service mode after scheduler and MCP lifecycle behavior are stable. |

## Dual-Agent Implementation Judgment

The proposed split is sensible:

- **Opus 4.6** should own implementation throughput: test-first coding, small-scope refactors, and controlled feature delivery.
- **GPT-5.4** should act as an independent reviewer/tester: contract critic, adversarial test generator, failure-mode inspector, and anti-fake-completion verifier.

This only works if the roles stay narrow.

- Opus 4.6 should not be asked to solve broad architecture plus delivery plus audit in one pass.
- GPT-5.4 should not review by intuition alone. It should validate exact commands, exact artifacts, exact failures, and exact acceptance criteria.

The right operating model is:

1. Opus writes or updates tests first.
2. Opus implements the smallest passing change.
3. GPT-5.4 re-runs the validation commands, critiques contract gaps, adds adversarial cases, and checks whether the implementation solved the requested problem rather than only satisfying the happy path.
4. Human approval decides whether the slice is production-worthy or only prototype-worthy.

## Under-Covered Angles From Official Research

These are the main angles that should be promoted inside the plan because they directly affect implementation quality:

1. **Capability negotiation should outrank client-name heuristics.**
   The MCP spec centers initialization and negotiated capabilities. Client-name branching is still useful, but the server should behave according to declared capabilities first and vendor identity second.

2. **Structured tool outputs should be first-class contracts.**
   MCP tooling guidance and schema evolution both point toward richer structured results. Starting with `outputSchema` and stable envelopes will reduce client ambiguity and make GPT-5.4 reviews more reliable.

3. **Authorization needs stronger server-side ownership than many agent projects assume.**
   MCP security guidance explicitly warns against accepting tokens not intended for the MCP server. Validate audience and isolate token lifecycle on the server side rather than trusting client refresh behavior.

4. **Simplicity-first should be a written build rule, not just a sentiment.**
   Anthropic's public agent guidance is blunt: start with the simplest system that can work, then add complexity only when there is evidence it is needed. The build plan currently implies this, but it should say it directly.

5. **Hooks are a strong fit for the dual-agent workflow.**
   Claude Code hooks provide a practical way to enforce validation, formatting, and evidence collection automatically around Opus coding sessions. That would reduce the chance of "completed" work that was never actually validated.

6. **Reviewer quality comes from evals, not eloquence.**
   OpenAI's agent and eval guidance reinforces that agent systems need repeatable acceptance checks. GPT-5.4 should review against artifact-based evals and contract assertions, not just produce high-quality commentary.

## Recommended Start Sequence

This is the implementation order I would recommend if the goal is maximum learning with minimum architectural regret:

1. **Build the delivery harness before the platform.**
   Freeze the validation commands, evidence format, reviewer checklist, and handoff expectations.

2. **Pilot the smallest credible MEU.**
   Use the calculator plus minimal logging as the proving ground for the Opus 4.6 -> GPT-5.4 workflow.

3. **Build one thin persistent vertical slice.**
   Pick a single domain use case that crosses domain, infrastructure, service, and REST boundaries. Keep it intentionally boring.

4. **Add the first MCP slice only after the backend slice is stable.**
   Expose a small subset of already-proven application services through static stdio MCP. Keep the tool count small and risk low.

5. **Expand only by evidence gates.**
   Add dynamic toolsets, HTTP transport, scheduling complexity, market-data breadth, and service-daemon behavior only after the simpler baseline has hard evidence behind it.

## Opinion on the Pre-Emptive Friction Work

The pre-emptive friction analysis is good work. In a young field like MCP, it is not overthinking. It is appropriate engineering caution.

The important caveat is this: pre-mortems create value when they produce seams, guardrails, and rollout gates. They create drag when they become a reason to implement every mitigation before the first working path exists.

My judgment is that `friction-inventory.md` is directionally excellent. It demonstrates the right instincts for an immature ecosystem. The next step is to operationalize it as a tiered gate system:

- **Gate A: required before first MCP prototype**
  - schema/registration guardrails
  - tool-count discipline
  - stdio transport reliability
  - explicit disconnect/error handling
- **Gate B: required before multi-client support**
  - capability-matrix testing
  - dynamic toolset experiments
  - auth refresh stress tests
  - client-specific compatibility adjustments
- **Gate C: required before remote/HTTP/generalized rollout**
  - HTTP transport hardening
  - stronger authorization posture
  - process supervision per OS
  - production metrics and recovery playbooks

That framing preserves the value of the friction work without turning it into a complexity multiplier.

## Guardrail Output (If Required)

- Safety checks:
  - Review explicitly favors server-side safeguards for financial/destructive operations.
  - Review does not recommend relaxing validation, auth, or confirmation posture.
- Blocking risks:
  - None for documentation work.
  - For implementation, the main blocker is starting MCP too broadly instead of with a constrained baseline.
- Verdict:
  - Guardrail concerns are acknowledged and aligned with the review findings.

## Approval Gate

- **Human approval required for merge/release/deploy:** yes
- **Approval status:** pending
- **Approver:**
- **Timestamp:**

## Final Summary

- Status:
  - Completed. Senior review written from the friction-inventory perspective with official-source research and dual-agent implementation guidance.
- Next steps:
  1. Add an explicit simplicity-first and rollout-gates section to the build-plan overview.
  2. Freeze the first vertical slice and first constrained MCP slice before any broader implementation starts.
  3. Decide whether GPT-5.4 becomes the formal reviewer/tester baseline for the Phase 1 workflow.
