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

Read and internalize `SOUL.md` at session start. This file defines your identity (Kael), core equation (`Lifetime = (Energy × Purpose) ÷ Stress`), personality, and interaction principles. It is agent-scoped — it governs *who you are* across all conversations, while `AGENTS.md` and this file govern *how you work* on this project.

**Separation of concerns:**
- `SOUL.md` → Identity, values, personality, stress awareness (agent-scoped)
- `AGENTS.md` → Project rules, architecture, testing, code quality (project-scoped)
- `GEMINI.md` → Antigravity-specific mode mapping and workflows (runtime-scoped)

## Session Preflight (Required)

At the start of every new task:

1. **Read `SOUL.md`** — internalize identity, core equation, and interaction principles.
2. Read `.agent/context/current-focus.md` for active phase and priorities.
3. Read `.agent/context/known-issues.md` for known gotchas.
4. Search `pomera_notes` for previous session state (`search_term: "Zorivest"`).
5. Verify MCP servers are available by calling `pomera_diagnose`.

If required MCP servers (`pomera`, `text-editor`) are not connected, report to user via `notify_user` and do not proceed.

## Planning Contract (Required)

When creating a plan, every task must include:
- `task`
- `owner_role` (`orchestrator`, `coder`, `tester`, `reviewer`, `researcher`, `guardrail`)
- `deliverable`
- `validation` (exact command(s))
- `status` (`pending`, `in_progress`, `done`)

Rules:
- No unowned tasks.
- Use explicit transitions: `orchestrator -> coder -> tester -> reviewer`.
- If a task does not map to a role, split/refine first or ask clarification.

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

## Handoff Protocol

At session end, create or update a handoff file:

- Path: `.agent/context/handoffs/{YYYY-MM-DD}-{task-slug}.md`
- Template: `.agent/context/handoffs/TEMPLATE.md`
- Also save to `pomera_notes` for cross-session searchability

## Workflow Invocation

When the user invokes a workflow via slash command:

- `/orchestrated-delivery` → Read and follow `.agent/workflows/orchestrated-delivery.md`
- `/pre-build-research` → Read and follow `.agent/workflows/pre-build-research.md`

## MCP Tool Usage

Required MCP servers for this project:

| Server | Purpose | Verify With |
|---|---|---|
| `pomera` | Notes, text processing, web search, AI tools | `pomera_diagnose` |
| `text-editor` | Hash-based conflict-safe file editing | `get_text_file_contents` |
| `sequential-thinking` | Complex multi-step analysis | `sequentialthinking` |
