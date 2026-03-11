# GEMINI.md — Zorivest (Antigravity Agent Configuration)

Antigravity-specific operating rules. For vendor-neutral agent instructions, see `AGENTS.md`.

## Antigravity Operating Model

Antigravity uses three modes via `task_boundary`. Map the six project roles to these modes:

| Antigravity Mode | Roles Active | What Happens |
|---|---|---|
| **PLANNING** | orchestrator, researcher | Scope task, read context files, research patterns, create `implementation-plan.md` |
| **EXECUTION** | coder | Implement changes, run targeted tests after each change |
| **VERIFICATION** | tester, reviewer, guardrail | Run full validation (`uv run python tools/validate_codebase.py`), adversarial review, safety checks |

### Mode Transitions

- Start every implementation task in **PLANNING** mode.
- Switch to **EXECUTION** only after the user approves the plan.
- Switch to **VERIFICATION** after all implementation is complete.
- If verification reveals design flaws, return to **PLANNING** with a new TaskName.
- If verification reveals minor bugs, stay in the current TaskName, switch to **EXECUTION** to fix, then resume **VERIFICATION**.

### Role Adoption

Instead of subagent invocation, adopt roles inline by following the role spec's **Must Do**, **Must Not Do**, and **Output Contract** sections:

- During PLANNING: follow `.agent/roles/orchestrator.md` — scope the project, plan role sequence
- During EXECUTION: follow `.agent/roles/coder.md` — read full files, no placeholders, handle errors
- During VERIFICATION: follow `.agent/roles/tester.md` then `.agent/roles/reviewer.md`
- For high-risk changes: also follow `.agent/roles/guardrail.md` before completion

## Agent Identity

Read and internalize `SOUL.md` at session start — identity (Kael), core equation, personality.
`SOUL.md` = who you are. `AGENTS.md` = project rules. `GEMINI.md` = Antigravity runtime.

## Session Preflight

Follow `AGENTS.md` Session Discipline, plus verify MCP servers (`pomera_diagnose`). If `pomera` or `text-editor` unavailable, report via `notify_user` and stop.

## Quality-First Policy

> [!IMPORTANT]
> Quality, wisdom, and expert-level experience metrics are above all other considerations. They must never be compromised by time pressure or expedience. If a task requires extended analysis, deeper research, or more comprehensive testing, do it without hesitation.

## Planning Contract

Follow `AGENTS.md` Roles & Workflows section for plan task fields and role transitions.

### Spec Sufficiency Gate

Before approving any plan or starting TDD:

1. Read the target build-plan section and the local canonical docs it points to or depends on.
2. Classify each required behavior as `Spec`, `Local Canon`, `Research-backed`, or `Human-approved`.
3. If the build plan is not specific enough to support a complete implementation, run targeted web research against official docs, standards, or other primary/current sources before writing acceptance criteria.
4. Ask the human only when materially different product behaviors remain plausible, the sources conflict, or the choice is irreversible/high-risk.

Under-specified specs are not permission to narrow scope, invent behavior, or defer work.

## Execution Contract

- Follow `AGENTS.md` §Session Discipline for session rules, time/token policy, and session end protocol.
- **Git commit policy**: See `.agent/skills/git-workflow/SKILL.md` §Commit Policy. Never auto-commit.
- Run targeted tests after each change.
- **MEU gate** (per-MEU): `uv run python tools/validate_codebase.py --scope meu` — targeted `pyright`, `ruff`, `pytest`, anti-placeholder scan scoped to touched packages/files.
- **Phase gate** (phase exit only): `uv run python tools/validate_codebase.py` when ALL MEUs in a phase are complete. Do NOT run it as a MEU-level gate — it validates the full repo and will fail until later phases are scaffolded.
- **Evidence-first completion:** `task.md` items may never be marked `[x]` unless the handoff or walkthrough contains a complete evidence bundle (changed files + commands executed + test results + artifact references).
- **No-deferral rule:** Items containing `TODO`, `FIXME`, `NotImplementedError`, or placeholder stubs may not be marked `[x]`. Blocked items must use status `[B]` with a linked follow-up task in the handoff.
- **Anti-placeholder enforcement:** Before declaring complete, run `rg "TODO|FIXME|NotImplementedError" packages/` and resolve any matches. Extend the search to `ui/` or `mcp-server/` once those packages are scaffolded.
- A thin spec is not a valid reason to ship a narrower implementation. Resolve the gap in planning/research, update the plan/FIC with the source-backed rule, then implement the full resolved contract.

### Pre-Handoff Self-Review (Mandatory)

> Before any completion claim or handoff submission, adopt the reviewer mindset. This protocol was distilled from analysis of 7 critical review handoffs (37+ passes) where 10 recurring patterns caused 4-11 passes per project.

1. For each AC, verify the claim against actual file state (quote `file:line`, not memory).
2. Re-run all validation commands and compare counts to what the handoff says.
3. If you fixed one instance of a bug category, `rg` for all instances of the same category.
4. If you changed architecture, `rg` canonical docs for the old pattern.
5. Never say "implementation complete" if residual risk acknowledges known gaps.
6. Stubs must honor behavioral contracts, not just compile.
7. Follow the full protocol in `.agent/skills/pre-handoff-review/SKILL.md`.

> [!CAUTION]
> **Anti-premature-stop rule.** Do NOT call `notify_user` during execution unless blocked by an unresolvable error or a human decision gate. Complete ALL workflow exit criteria in a single continuous pass — including post-MEU deliverables (MEU gate, registry update, BUILD_PLAN.md update, reflection, metrics, pomera session save, commit messages). Before any `notify_user` call, re-read `task.md` and verify every item is `[x]`.
>
> **Lifecycle escape hatch**: "Trigger Codex validation" IS classified as an allowed human decision gate. The anti-premature-stop rule permits calling `notify_user` to hand off to Codex. Post-validation artifacts (reflection, metrics) are created in the NEXT session after Codex returns its verdict.
>
> **Context window checkpoint**: If context window exceeds ~80% capacity, save state to `pomera_notes`, complete the current MEU's handoff, and notify human with remaining work. This is a planned checkpoint, not early termination.

## Dual-Agent Workflow

| Aspect | Decision |
|---|---|
| **Reviewer model** | **GPT-5.4** (locked as baseline — do not downgrade) |
| **Reviewer capability** | Run commands, execute tests, check builds, create handoff docs with test improvements |
| **Validation priority** | 1. Contract tests pass/fail → 2. Security posture → 3. Adversarial edge cases → 4. Code style consistency → 5. Documentation accuracy |

> The reviewer (GPT-5.4 Codex) runs commands and creates handoff docs for findings. It is not limited to prose-only review — it produces executable evidence.

## TDD-First Protocol (Implementation Agent — MANDATORY)

When implementing a Manageable Execution Unit (MEU):

1. **Read** the build plan spec section for this MEU and the local canonical docs it references (in `docs/build-plan/`, indexes, ADRs, reflections if applicable)
2. **Write source-backed FIC** — Feature Intent Contract with acceptance criteria (AC-1, AC-2, ...) before any code. Each AC must be labeled `Spec`, `Local Canon`, `Research-backed`, or `Human-approved`.
3. **Write ALL tests FIRST** — every AC becomes at least one test assertion
4. **Run tests** — confirm they FAIL (Red phase). **Save failure output for FAIL_TO_PASS evidence.**
5. **Implement** — write just enough code to make tests pass (Green phase)
6. **Refactor** — clean up while keeping tests green
7. **Run checks**: `pytest -x --tb=short -m "unit"`, `pyright`, `ruff check`
8. **Create handoff** at `.agent/context/handoffs/{SEQ}-{YYYY-MM-DD}-{slug}-bp{NN}s{X.Y}.md`

> ⚠️ **Test Immutability**: Once tests are written in Red phase, do NOT modify test assertions or expected values in Green phase. If a test expectation is wrong, fix the *implementation*, not the *test*. The only acceptable test modification in Green phase is fixing test setup/fixtures, never assertions.

> ⚠️ **No unsourced best-practice rules**: If you cannot write a concrete AC without inventing behavior, return to planning/research. Do not smuggle product decisions into the FIC under a generic "best practice" label.

### MEU Boundaries

- Group related MEUs into a **project** based on dependency order and logical flow. A session executes one project — building continuously from foundation to roof.
- Use reasoning to determine which MEUs belong together: shared context, sequential dependencies, and logical continuity maximize productivity.
- Individual MEU TDD discipline (FIC → Red → Green → Quality) is preserved — complete each MEU's cycle before starting the next.
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

- Path: `.agent/context/handoffs/{SEQ}-{YYYY-MM-DD}-{slug}-bp{NN}s{X.Y}.md`
- Template: `.agent/context/handoffs/TEMPLATE.md`

## Workflow Invocation

When the user invokes a workflow via slash command:

- `/create-plan` → Read and follow `.agent/workflows/create-plan.md`
- `/execution-session` → Read and follow `.agent/workflows/execution-session.md`
- `/orchestrated-delivery` → Read and follow `.agent/workflows/orchestrated-delivery.md`
- `/pre-build-research` → Read and follow `.agent/workflows/pre-build-research.md`
- `/tdd-implementation` → Read and follow `.agent/workflows/tdd-implementation.md`
- `/validation-review` → Read and follow `.agent/workflows/validation-review.md`
- `/planning-corrections` → Read and follow `.agent/workflows/planning-corrections.md`
- `/critical-review-feedback` → Read and follow `.agent/workflows/critical-review-feedback.md`
- `/meu-handoff` → Read and follow `.agent/workflows/meu-handoff.md`

## Skills

| Skill | Path | Purpose |
|-------|------|---------|
| Git Workflow | `.agent/skills/git-workflow/SKILL.md` | Agent-safe git operations with SSH commit signing. Prevents interactive prompt hangs. |
| Codebase Quality Gate | `.agent/skills/quality-gate/SKILL.md` | Validation pipeline: type checks, linting, tests, anti-placeholder scans, evidence checks. Supports phase-level and MEU-scoped runs. |
| Pre-Handoff Review | `.agent/skills/pre-handoff-review/SKILL.md` | Self-review protocol addressing 10 recurring patterns from critical review analysis. Reduces average review passes from 4-11 to 3-5. |

## MCP Servers

See `AGENTS.md` MCP Servers table. Verify with `pomera_diagnose` at session start.
