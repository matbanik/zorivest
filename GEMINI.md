# GEMINI.md — Zorivest (Antigravity Agent Configuration)

Antigravity-specific operating rules. For vendor-neutral agent instructions, see `AGENTS.md`.

## Antigravity Operating Model

Antigravity uses three modes via `task_boundary`. Map the six project roles to these modes:

| Antigravity Mode | Roles Active | What Happens |
|---|---|---|
| **PLANNING** | orchestrator, researcher | Scope task, read context files, research patterns, create `implementation_plan.md` |
| **EXECUTION** | coder | Implement changes, run targeted tests after each change |
| **VERIFICATION** | tester, reviewer, guardrail | Run full validation (`.\validate.ps1`), adversarial review, safety checks |

### Mode Transitions

- Start every implementation task in **PLANNING** mode.
- Switch to **EXECUTION** only after the user approves the plan.
- Switch to **VERIFICATION** after all implementation is complete.
- If verification reveals design flaws, return to **PLANNING** with a new TaskName.
- If verification reveals minor bugs, stay in the current TaskName, switch to **EXECUTION** to fix, then resume **VERIFICATION**.

### Role Adoption

Instead of subagent invocation, adopt roles inline by following the role spec's **Must Do**, **Must Not Do**, and **Output Contract** sections:

- During PLANNING: follow `.agent/roles/orchestrator.md` — scope one task, plan role sequence
- During EXECUTION: follow `.agent/roles/coder.md` — read full files, no placeholders, handle errors
- During VERIFICATION: follow `.agent/roles/tester.md` then `.agent/roles/reviewer.md`
- For high-risk changes: also follow `.agent/roles/guardrail.md` before completion

## Agent Identity

Read and internalize `SOUL.md` at session start — identity (Kael), core equation, personality.
`SOUL.md` = who you are. `AGENTS.md` = project rules. `GEMINI.md` = Antigravity runtime.

## Session Preflight

Follow `AGENTS.md` Session Discipline, plus verify MCP servers (`pomera_diagnose`). If `pomera` or `text-editor` unavailable, report via `notify_user` and stop.

## Planning Contract

Follow `AGENTS.md` Roles & Workflows section for plan task fields and role transitions.

## Execution Contract

- One task per session; do not combine unrelated work streams.
- Run targeted tests after each change.
- Run full blocking validation before declaring complete:
  - `.\validate.ps1`
- **Evidence-first completion:** `task.md` items may never be marked `[x]` unless the handoff or walkthrough contains a complete evidence bundle (changed files + commands executed + test results + artifact references).
- **No-deferral rule:** Items containing `TODO`, `FIXME`, `NotImplementedError`, or placeholder stubs may not be marked `[x]`. Blocked items must use status `[B]` with a linked follow-up task in the handoff.
- **Anti-placeholder enforcement:** Before declaring complete, run `rg "TODO|FIXME|NotImplementedError" packages/ src/` and resolve any matches.
- Save session summary and next steps to `pomera_notes` with title `Memory/Session/Zorivest-{task}-{date}`.
- Update `.agent/context/current-focus.md` with new state.
- Human approval is required before merge/release/deploy.

## TDD-First Protocol (Implementation Agent — MANDATORY)

When implementing a Manageable Execution Unit (MEU):

1. **Read** the build plan spec section for this MEU (in `docs/build-plan/`)
2. **Write FIC** — Feature Intent Contract with acceptance criteria (AC-1, AC-2, ...) before any code
3. **Write ALL tests FIRST** — every AC becomes at least one test assertion
4. **Run tests** — confirm they FAIL (Red phase). **Save failure output for FAIL_TO_PASS evidence.**
5. **Implement** — write just enough code to make tests pass (Green phase)
6. **Refactor** — clean up while keeping tests green
7. **Run checks**: `pytest -x --tb=short -m "unit"`, `pyright`, `ruff check`
8. **Create handoff** at `.agent/context/handoffs/{YYYY-MM-DD}-meu-{N}-{slug}.md`
9. **Save state** to `pomera_notes` with title `Memory/Session/Zorivest-MEU-{N}-{date}`

> ⚠️ **Test Immutability**: Once tests are written in Red phase, do NOT modify test assertions or expected values in Green phase. If a test expectation is wrong, fix the *implementation*, not the *test*. The only acceptable test modification in Green phase is fixing test setup/fixtures, never assertions.

### MEU Boundaries

- One MEU per session. Do not expand scope.
- Each MEU maps to exactly one section of `docs/build-plan/build-priority-matrix.md`.
- See `.agent/context/meu-registry.md` for the full MEU list.
- Prefer real objects over mocks when feasible. Heavy mocking masks real failures.

### Anti-Slop Checklist (verify before handoff)

- [ ] Every public function has explicit error handling (no implicit passes)
- [ ] All type annotations are precise (no `Any`, no `# type: ignore` without justification)
- [ ] Edge cases identified in FIC are actually handled in code (not just tested)
- [ ] No inline `# TODO` or commented-out alternatives left behind
- [ ] Code was NOT copied verbatim from build plan — adapt to actual FIC and project structure

## Handoff Protocol

At session end, create or update a handoff file:

- Path: `.agent/context/handoffs/{YYYY-MM-DD}-{task-slug}.md`
- Template: `.agent/context/handoffs/TEMPLATE.md`
- Also save to `pomera_notes` for cross-session searchability

## Workflow Invocation

When the user invokes a workflow via slash command:

- `/orchestrated-delivery` → Read and follow `.agent/workflows/orchestrated-delivery.md`
- `/pre-build-research` → Read and follow `.agent/workflows/pre-build-research.md`

## MCP Servers

See `AGENTS.md` MCP Servers table. Verify with `pomera_diagnose` at session start.
