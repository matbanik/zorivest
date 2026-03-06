# Task Handoff Template

## Task

- **Date:** 2026-03-06
- **Task slug:** docs-build-plan-agentic-continuity-review
- **Owner role:** reviewer
- **Scope:** Senior software architect continuity review of `docs/build-plan/*` plus `.agent` workflow/role/rule files, with targeted official web validation for startup prompting and agentic execution guidance.

## Inputs

- User request:
  - Review how each build-plan stage connects to the next
  - Look for inconsistencies, reasoning gaps, and clarity issues in `docs/build-plan/*`
  - Review `.agent` workflow, roles, and rules with focus on how initial agentic coding starts and is prompted
  - Provide feedback on iterative improvements between runs
  - Review how much work is bundled into each agentic execution and validation cycle
  - Create a feedback document in `.agent/context/handoffs/`
- Specs/docs referenced:
  - `docs/BUILD_PLAN.md`
  - `docs/build-plan/00-overview.md`
  - `docs/build-plan/01-domain-layer.md`
  - `docs/build-plan/01a-logging.md`
  - `docs/build-plan/02-infrastructure.md`
  - `docs/build-plan/02a-backup-restore.md`
  - `docs/build-plan/03-service-layer.md`
  - `docs/build-plan/04-rest-api.md`
  - `docs/build-plan/05-mcp-server.md`
  - `docs/build-plan/05b-mcp-zorivest-diagnostics.md`
  - `docs/build-plan/05j-mcp-discovery.md`
  - `docs/build-plan/06-gui.md`
  - `docs/build-plan/06e-gui-scheduling.md`
  - `docs/build-plan/06f-gui-settings.md`
  - `docs/build-plan/07-distribution.md`
  - `docs/build-plan/08-market-data.md`
  - `docs/build-plan/09-scheduling.md`
  - `docs/build-plan/10-service-daemon.md`
  - `docs/build-plan/build-priority-matrix.md`
  - `docs/build-plan/dependency-manifest.md`
  - `docs/build-plan/testing-strategy.md`
  - `docs/build-plan/friction-inventory.md`
  - `docs/build-plan/mcp-tool-index.md`
  - `docs/build-plan/mcp-planned-readiness.md`
  - `docs/build-plan/input-index.md`
  - `.agent/workflows/orchestrated-delivery.md`
  - `.agent/workflows/tdd-implementation.md`
  - `.agent/workflows/validation-review.md`
  - `.agent/workflows/meu-handoff.md`
  - `.agent/roles/orchestrator.md`
  - `.agent/roles/coder.md`
  - `.agent/roles/tester.md`
  - `.agent/roles/reviewer.md`
  - `.agent/roles/guardrail.md`
  - `.agent/roles/researcher.md`
  - `.agent/docs/prompt-templates.md`
  - `.agent/docs/architecture.md`
  - `.agent/docs/testing-strategy.md`
  - `.agent/docs/code-quality.md`
  - `.agent/docs/antigravity-mode-map.md`
  - `.agent/context/meu-registry.md`
  - `AGENTS.md`
  - `GEMINI.md`
  - `SOUL.md`
- Official web research:
  - OpenAI Codex: `https://openai.com/index/introducing-codex/`
  - OpenAI Codex upgrades / research preview: `https://openai.com/index/introducing-codex-upgrades-research-preview/`
  - Anthropic Claude Code memory: `https://docs.anthropic.com/en/docs/claude-code/memory`
  - Anthropic Claude Code sub-agents: `https://docs.anthropic.com/en/docs/claude-code/sub-agents`
  - MCP lifecycle spec: `https://modelcontextprotocol.io/specification/2025-11-05/basic/lifecycle`
- Constraints:
  - Documentation and workflow review only; no product implementation requested
  - Findings should be practical for upcoming agentic implementation, especially the first coding runs
  - Use line-referenced evidence from the actual file state

## Role Plan

1. orchestrator
2. researcher
3. reviewer
- Optional roles: guardrail

## Coder Output

- Changed files:
  - `.agent/context/handoffs/2026-03-06-docs-build-plan-agentic-continuity-review.md`
- Design notes:
  - Review-only session. No product code or plan files were changed.
  - The objective was to identify continuity defects that would cause an agent to start the wrong work, in the wrong order, with the wrong prompt or validation contract.
  - Official web sources were used only where current agent tooling behavior or prompting guidance materially affected the review.
- Commands run:
  - `Get-ChildItem -Name`
  - `rg --files -g "SOUL.md" -g ".agent/context/current-focus.md" -g ".agent/context/known-issues.md" -g "docs/BUILD_PLAN.md" -g "docs/build-plan/**" -g ".agent/workflows/**" -g ".agent/roles/**" -g ".agent/docs/**"`
  - `Get-Content` / structured file reads across target docs
  - `rg -n` continuity sweeps for prerequisites, outputs, MEU references, validation commands, and workflow invocations
  - `git status --short -- .agent/context/current-focus.md .agent/context/handoffs`
  - Official web reads for Codex, Claude Code memory/sub-agents, and MCP lifecycle
- Results:
  - Produced a findings-first continuity review with startup, iteration, and validation recommendations
  - Identified several cross-doc contradictions that still make first-run agentic execution non-deterministic beyond the current Phase 1 pilot

## Tester Output

- Commands run:
  - Document inspection only; no code tests were applicable to this task
- Pass/fail matrix:
  - Target docs reviewed: pass
  - Workflow/role/rule docs reviewed: pass
  - Official-source research completed: pass
  - Feedback handoff created: pass
- Repro failures:
  - None runtime-related; findings are documentation/workflow continuity defects
- Coverage/test gaps:
  - No live tool/client execution was performed against Antigravity, Codex, or MCP clients in this session
  - Findings are based on the current documentation state plus official guidance, not live end-to-end agent rehearsal
- Evidence bundle location:
  - `.agent/context/handoffs/2026-03-06-docs-build-plan-agentic-continuity-review.md`
- FAIL_TO_PASS / PASS_TO_PASS result:
  - N/A
- Mutation score:
  - N/A
- Contract verification status:
  - N/A

## Reviewer Output

- Findings by severity:
  - **Critical-1:** The startup workflow for the first implementation run is internally inconsistent. `.agent/workflows/tdd-implementation.md:11` tells the implementation agent to read `CLAUDE.md`, but the repo uses `GEMINI.md` and no `CLAUDE.md` exists. `.agent/docs/prompt-templates.md:14` and `.agent/docs/prompt-templates.md:26` instruct agents to invoke `/tdd-implementation` and `/validation-review`, but `GEMINI.md:118-119` only defines `/orchestrated-delivery` and `/pre-build-research`. At the same time, `GEMINI.md:17-18` says every implementation task must begin in PLANNING mode and only enter EXECUTION after plan approval, while the "Start a New MEU" prompt jumps directly into implementation. For the very first run, this is not a style problem; it is an operating-contract break.
  - **Critical-2:** Phase 5 still has a contradictory day-1 baseline. `docs/build-plan/00-overview.md:106-111` and `docs/build-plan/05-mcp-server.md:752` both say Stage 1 starts with 8-12 tools, but `docs/build-plan/05-mcp-server.md:803-805` and `docs/build-plan/05-mcp-server.md:838` still route the day-1 client into dynamic mode with all default toolsets loaded. Cross-index docs amplify the drift: `docs/build-plan/mcp-tool-index.md:127` still frames the 37-tool default around Cursor's cap, while `docs/build-plan/mcp-planned-readiness.md:161-169` still says only `core` is always-loaded. This means the plan does not yet tell the implementation agent one unambiguous answer to "what do I load on day 1?"
  - **High-1:** The hub documents do not present a stable stage map. `docs/BUILD_PLAN.md:22-30` still lists only phases 0-8 and says Phase 8 has 9 providers, while `docs/build-plan/00-overview.md:65`, `docs/build-plan/00-overview.md:67`, and `docs/build-plan/00-overview.md:73-75` include phases 1A, 2A, 9, and 10 and describe 12 providers. There is also a direct dependency mismatch: `docs/build-plan/00-overview.md:75` says Phase 10 depends on Phases 4 and 7, but `docs/build-plan/10-service-daemon.md:3` says Phase 10 also depends on Phase 9. Any agent or human starting from `docs/BUILD_PLAN.md` gets an incomplete and partly stale roadmap.
  - **High-2:** Phase 6 sub-files understate their prerequisites, which breaks stage-to-stage continuity. `docs/build-plan/06e-gui-scheduling.md:3` says it only depends on Phase 4, but the file itself says its MCP tools and REST endpoints are defined in Phase 9 at `docs/build-plan/06e-gui-scheduling.md:170` and `docs/build-plan/06e-gui-scheduling.md:194`, and Phase 9 explicitly names 06e as its consumer at `docs/build-plan/09-scheduling.md:3`. `docs/build-plan/06f-gui-settings.md:3` lists only Phases 4 and 2A, but its market-data page consumes Phase 8 at `docs/build-plan/06f-gui-settings.md:17` and its outputs include the Phase 10 `ServiceManagerPage` at `docs/build-plan/06f-gui-settings.md:778`. `docs/build-plan/06-gui.md:3` still frames GUI as Phase-4-first even though its exit criteria require scheduling and service-manager behavior at `docs/build-plan/06-gui.md:370` and `docs/build-plan/06-gui.md:375`.
  - **High-3:** The validation contract is not tiered and therefore not portable beyond the current core-only pilot. Repo policy says the blocking pipeline is `pyright`, `tsc`, `ruff`, `eslint`, `pytest`, `vitest`, and `npm run build` at `AGENTS.md:72`, and `GEMINI.md:13` and `GEMINI.md:57` reinforce full validation via `.\\validate.ps1`. But the MEU implementation and review workflows are hard-coded to core-only checks: `.agent/workflows/tdd-implementation.md:63-64`, `.agent/workflows/validation-review.md:35`, `.agent/workflows/validation-review.md:41`, `.agent/workflows/validation-review.md:47`, and `.agent/context/meu-registry.md:68-70`. That is acceptable for Phase 1 + 1A only. It is not sufficient as the standing workflow once MEUs cross Python packages, TypeScript surfaces, or mixed-language boundaries.
  - **High-4:** Work-unit sizing is disciplined only for the current pilot, not for the broader roadmap. `.agent/context/meu-registry.md:1` defines MEUs only for Phase 1 + 1A, while `docs/build-plan/build-priority-matrix.md:20`, `docs/build-plan/build-priority-matrix.md:31`, `docs/build-plan/build-priority-matrix.md:32`, `docs/build-plan/build-priority-matrix.md:123`, and `docs/build-plan/build-priority-matrix.md:138` still package later work into very large slices such as "Service layer", "FastAPI routes", "TypeScript MCP tools", "Scheduling REST API + MCP tools", and "Service Manager GUI + installer hooks". The docs say "one MEU per session" (`GEMINI.md:93`), but only Phase 1 currently enforces what "one MEU" actually means.
  - **Medium-1:** Phase 1 has a specific implementation-contract drift that should be cleaned up before MEU-6. `docs/build-plan/01-domain-layer.md:9` and `docs/build-plan/dependency-manifest.md:15` both say Phase 1 commands/DTOs use dataclasses with manual validation and that Pydantic is added in Phase 4, but `docs/build-plan/build-priority-matrix.md:19` still describes the same Phase 1 item as "Pydantic validation". This is localized, but it undermines confidence in the very section the first implementation phases depend on.
  - **Medium-2:** Phase 5 and Phase 10 are still coupled in a way that blurs when service-control tooling should enter the system. `docs/build-plan/05b-mcp-zorivest-diagnostics.md:5` says service tools were originally specified in Phase 10, `docs/build-plan/10-service-daemon.md:3` says Phase 10 depends on 7 and 9, but `docs/build-plan/05-mcp-server.md:737` places diagnostics/service tools inside the always-loaded `core` toolset. That may be a defensible design choice, but it needs to be explicit whether Phase 5 ships degraded service tools first or whether those tools are deferred until Phase 10.
- Open questions:
  - Is the intended first implementation path now "MEU planning packet -> plan approval -> MEU execution" or "direct `/tdd-implementation` with no separate plan artifact"?
  - Should service-control MCP tools be part of the Phase 5 prototype, or should they be deferred from `core` until Phase 10 endpoints exist?
  - Do you want `docs/BUILD_PLAN.md` to be the canonical roadmap spine again, or only a minimal index that explicitly defers to `00-overview.md` for the real phase graph?
- Verdict:
  - **changes_required before scaling agentic implementation beyond the calculator pilot**
  - The plan is strong enough to start MEU-1.
  - It is not yet clean enough to scale the workflow confidently across later phases without prompt drift, dependency drift, or validation ambiguity.
- Residual risk:
  - If implementation starts from the current mixed instructions, the first agent may still succeed on the calculator pilot, but later runs will begin diverging in scope, prompt style, and validation rigor.
  - The biggest risk is not incorrect code. It is inconsistent operating behavior across sessions and across agents.

## Executive Summary

The plan has good depth and mostly sound architectural direction. The main problem is not missing content. The problem is that the plan now exists at three different abstraction levels that are not yet fully reconciled:

1. `docs/BUILD_PLAN.md` as a hub
2. `docs/build-plan/*` as the real implementation spec
3. `.agent/*` as the execution machinery

For Phase 1 + 1A, the system is nearly ready because `current-focus.md` and `meu-registry.md` narrow the work. Beyond that pilot, the continuity breaks reappear:

- the hub file is stale relative to the real roadmap
- some phase headers understate dependencies on later phases
- the startup prompt chain is not deterministic
- validation scope is mixed between "full repo gate" and "core-only MEU checks"
- later-phase work is still too large to be a safe single-run unit

The practical conclusion is:

- **Ready now:** calculator pilot and the Phase 1 + 1A dual-agent proof-of-workflow
- **Needs normalization before broader implementation:** MCP startup baseline, GUI dependency headers, workflow invocation contract, and per-phase work decomposition

## Continuity Review

### Stage-to-Stage Assessment

| Stage | Connection to Next Stage | Current State | Review |
|---|---|---|---|
| Phase 1 -> 2 | Mostly clear | `01-domain-layer.md` and `02-infrastructure.md` connect cleanly | Good starting seam |
| Phase 1A -> all phases | Clear in concept | Logging is documented as parallel, cross-cutting infrastructure | Good, but keep implementation minimal |
| Phase 2 -> 2A -> 3 | Clear | Backup/defaults/settings are properly shown as feeding services | Strong continuity |
| Phase 3 -> 4 | Clear | Thin transport over service layer is consistent | Strong continuity |
| Phase 4 -> 5 | Partly broken | Core idea is clear, but Phase 5 startup baseline is contradictory | Needs correction before Phase 5 work starts |
| Phase 4/8/9/10 -> 6 | Under-specified | GUI sub-files consume later phases but headers mostly say Phase 4 | Needs header/phase-exit repair |
| Phase 7 -> 10 | Inconsistent | Overview and Phase 10 disagree on whether 9 is a prerequisite | Needs canonical dependency fix |
| Full roadmap -> execution workflow | Incomplete | Phase 1 has MEUs; later phases do not | Needs decomposition rule before scaling |

### What Is Already Strong

- The dependency-rule spine is correct.
- The plan generally keeps domain/service/API layering coherent.
- The FIC and FAIL_TO_PASS/PASS_TO_PASS additions are the right verification model.
- The current Phase 1 pilot strategy is disciplined and materially better than trying to start with a broad layer-sized task.

### What Still Causes Drift

- Canonical source-of-truth is unclear between `docs/BUILD_PLAN.md` and `docs/build-plan/00-overview.md`.
- "Phase complete" and "MEU complete" are not yet clearly separated as different gates.
- Some sub-files describe downstream consumers accurately, but their header prerequisites still read like they can start earlier than they actually can.

## Startup Prompt Review

### Current Startup Weaknesses

1. The implementation workflow points to a missing file (`CLAUDE.md`) instead of the actual repo runtime doc (`GEMINI.md`).
2. The prompt templates rely on slash commands that are not actually documented in `GEMINI.md`.
3. The planning requirement in `GEMINI.md` is not reflected in the "Start a New MEU" prompt.
4. The prompt templates tell the agent which files to read, but they do not force a complete execution packet:
   - exact in-scope behavior
   - explicit out-of-scope list
   - FIC skeleton
   - exact validation commands for this run
   - handoff path to write
   - stop conditions

### Recommended Startup Packet

Every implementation run should begin from a prompt shaped like this:

```text
Read SOUL.md, AGENTS.md, GEMINI.md, .agent/context/current-focus.md, .agent/context/known-issues.md, and .agent/context/meu-registry.md.
Read docs/build-plan/{file}.md at the exact section for MEU-{N}.

Task: implement MEU-{N} only.
In scope: {one behavior slice}.
Out of scope: {explicit exclusions}.

Before coding:
1. Write the FIC for this MEU.
2. Write failing tests first.
3. Confirm the exact validation commands for this MEU.
4. State the handoff file path you will update.

Do not expand scope without stopping.
```

That prompt is more deterministic because it forces the agent to materialize scope, evidence, and stop boundaries before it touches code.

### Why This Matches Current Tooling Guidance

- Anthropic's Claude Code memory guidance says memory files are loaded recursively and work best when they are specific and local. That argues for small, task-local prompt packets instead of relying on one broad root instruction file.
- Anthropic's sub-agent guidance says subagents get separate context windows. That reinforces keeping each run narrow enough that the handoff artifact, not ambient session context, remains the source of truth.
- OpenAI's Codex guidance says Codex is guided by `AGENTS.md`, can run tests named there, works best on well-scoped tasks, and should provide verifiable evidence of actions. That is aligned with a MEU-sized startup packet and explicit evidence contract.
- The MCP lifecycle spec centers the `initialize` handshake and negotiated capabilities, which supports capability-first startup decisions in Phase 5 rather than client-name-first heuristics.

## Iteration Model Between Runs

### Recommended Loop

After every run, classify what was learned into one of four buckets:

1. **Spec defect**
   - The build plan or workflow doc was wrong or ambiguous.
   - Action: patch docs before the next MEU starts.
2. **Prompt defect**
   - The agent had enough code context but not enough execution context.
   - Action: update the startup packet/template.
3. **Decomposition defect**
   - The work unit was too large or crossed too many surfaces.
   - Action: split the next unit before implementation starts.
4. **Implementation defect**
   - The plan and prompt were fine; the code/test execution was the issue.
   - Action: fix code only, do not churn docs unnecessarily.

### Mandatory Between-Run Retro

Each approved MEU should append a short retro block to its handoff:

- What instruction was missing?
- What assumption caused drift?
- What validation step caught the issue?
- What should be tightened before the next run?

This keeps the system improving through the workflow itself instead of only through occasional large documentation sweeps.

### What To Improve First Between Runs

1. Normalize the startup contract (`CLAUDE.md` -> `GEMINI.md`, slash-command map, planning gate).
2. Add a per-phase MEU registry before implementing that phase.
3. Parameterize validation by touched surface.
4. Only then broaden the active phase scope.

## Work Size Per Agentic Execution

### Current Assessment

Right now, the work sizing is good only where the project has explicit MEUs. Everywhere else, the matrix still contains tasks that are too large for a single reliable agentic execution.

Examples that are too broad as single-run units:

- `docs/build-plan/build-priority-matrix.md:20` — service layer
- `docs/build-plan/build-priority-matrix.md:31` — FastAPI routes
- `docs/build-plan/build-priority-matrix.md:32` — TypeScript MCP tools
- `docs/build-plan/build-priority-matrix.md:123` — Scheduling REST API + MCP tools
- `docs/build-plan/build-priority-matrix.md:138` — Service Manager GUI + installer hooks

Each of those should become multiple execution units before implementation starts.

### Recommended Sizing Rule

A single run should usually satisfy all of these:

- one primary behavior slice
- one dominant package or one already-frozen cross-package seam
- one main test module or small family of tightly related tests
- one handoff artifact
- one clear rollback point

If a run needs both Python backend behavior and new TypeScript client behavior, split it unless the API contract is already frozen and proven.

### Suggested Validation Tiers

Do not use one validation tier for every run. Define three:

1. **MEU gate**
   - FAIL_TO_PASS proof
   - touched-package unit/integration tests
   - touched-package lint/type checks
   - banned-pattern scan
2. **Phase checkpoint**
   - full repo blocking suite
   - contract tests for the phase seam
   - updated phase-exit evidence
3. **Release gate**
   - full blocking + advisory suite
   - packaging/build validation
   - evidence manifest completeness

This is not about saving time. It is about preventing tiny units from being judged by unrelated failures while still keeping strong phase and release gates.

## Recommended Documentation Corrections

### Highest Priority

1. Make the startup path deterministic:
   - fix `.agent/workflows/tdd-implementation.md` to reference `GEMINI.md`
   - either document `/tdd-implementation` and `/validation-review` in `GEMINI.md` or remove them from prompt templates
   - align prompt templates with the PLANNING -> EXECUTION approval rule
2. Repair the Phase 5 day-1 baseline:
   - choose one source of truth for Stage 1 loading behavior
   - update `05-mcp-server.md`, `mcp-tool-index.md`, and `mcp-planned-readiness.md` together
3. Repair the roadmap spine:
   - either expand `docs/BUILD_PLAN.md` to include 1A, 2A, 9, and 10
   - or explicitly mark it as a lightweight index and defer roadmap authority to `00-overview.md`

### Next Priority

4. Fix GUI prerequisite headers to reflect actual dependencies on 8, 9, and 10.
5. Define a standing rule that no phase beyond the active pilot may begin until its MEU registry exists.
6. Split validation guidance into MEU gate vs phase checkpoint vs release gate.

### Lower Priority but Worth Cleaning Up

7. Normalize the Commands/DTOs Phase 1 contract around dataclasses vs Pydantic.
8. Decide whether service-control tools belong to the Phase 5 prototype or Phase 10 rollout, and state that explicitly.

## Final Summary

- Status:
  - Review completed
  - Feedback handoff created
  - No product docs modified in this session
- Next steps:
  1. Normalize the startup workflow before any implementation run beyond MEU-1
  2. Treat MEU-1 as the workflow pilot, not just the calculator pilot
  3. Before Phase 2 starts, create Phase 2 MEUs and a phase-specific validation matrix
  4. Before Phase 5 starts, resolve the Stage 1 MCP baseline contradiction completely
