# Zorivest Agent Instructions

AI-specific guidance for working with the Zorivest codebase. Single source of truth for all AI coding assistants.
For agent identity, see `SOUL.md`.

## Quick Commands

```bash
# Validation (current scaffold: Python-only)
uv run python tools/validate_codebase.py --scope meu  # MEU gate during active implementation
uv run python tools/validate_codebase.py              # Full phase gate after all phase MEUs complete
pytest tests/unit/                                    # Python unit tests
pyright packages/                                     # Python type check
ruff check packages/                                  # Python lint

# Development (current scaffold)
pytest --cov=packages/core --cov-report=term            # Coverage (advisory)

# Planned scaffold commands (run only after the package exists)
# uv run fastapi dev packages/api/src/zorivest_api/main.py  # API
# npx tsc --noEmit                                          # TypeScript type check
# npx vitest run                                            # TypeScript unit tests
# npx eslint <ts-package>/src --max-warnings 0              # TypeScript lint
# npm run dev                                               # Electron UI
```

## Architecture

Hybrid monorepo — see `.agent/docs/architecture.md` for the target-state architecture. Current scaffold status is below.

| Layer | Language | Package | Status | Purpose |
|-------|----------|---------|--------|---------|
| Domain | Python | `packages/core` | Active | Entities, value objects, ports, calculator |
| Infra | Python | `packages/infrastructure` | Active | SQLAlchemy, SQLCipher, repos, UoW |
| API | Python | `packages/api` | Planned | FastAPI REST on localhost |
| UI | TypeScript | `ui/` | Planned | Electron + React GUI |
| MCP | TypeScript | `mcp-server/` | Planned | AI agent tool interface |

**Dependency rule:** Domain → Application → Infrastructure. Never import infra from core.

## Project Context

> [!IMPORTANT]
> **Zorivest does NOT execute trades — it plans and evaluates.** The software imports trade results from execution platforms (Interactive Brokers, etc.), analyzes performance, and generates trade plans. It never places, modifies, or cancels orders. All references to "trade confirmation" or "execution safety" apply to data-destructive operations (e.g., deleting trade records), NOT financial execution.

## Agent Identity

Read and internalize `SOUL.md` at session start — identity (Kael), core equation, personality.
`SOUL.md` = who you are. `AGENTS.md` = project rules.

## Session Discipline

> [!IMPORTANT]
> **Quality-First Policy.** Quality, wisdom, and expert-level experience metrics are above all other considerations. They must never be compromised by time pressure or expedience. If a task requires extended analysis, deeper research, or more comprehensive testing, do it without hesitation.

- **One project = one session.** Group related tasks into a coherent project by dependency order. Do NOT chain unrelated work streams.
- **Time is not a constraint** in agentic development cycles. Do not optimize for speed over quality.
- **Token usage is not a constraint** (subscription-based). Do not truncate, summarize prematurely, or skip work to save tokens.
- **Do not bring up time or token usage** in design discussions, trade-off analyses, or implementation decisions. Quality, wisdom, and expert experience are the only optimization targets.
- **At session start:** Read `SOUL.md`, check `pomera_notes` (`search_term: "Zorivest"`), read `.agent/context/current-focus.md` and `.agent/context/known-issues.md`. Verify MCP server availability (`pomera_diagnose`). If `pomera` or `text-editor` unavailable, report and stop.
- **At session end:** Save to `pomera_notes` (`Memory/Session/Zorivest-{project-slug}-{date}`) and create/update handoff(s) at `.agent/context/handoffs/`. Update `.agent/context/current-focus.md` only when the session changes project state; review-only sessions should not overwrite unrelated focus state.
- **Handoff continuity:** For the same `docs/execution/plans/{YYYY-MM-DD}-{project-slug}/` target, keep plan review in one rolling `-plan-critical-review.md` file and project implementation critique/recheck in one rolling `-implementation-critical-review.md` file. Append updates to the same file instead of creating new `-recheck`, `-final`, or `-approved` variants.
- **Under-specified build-plan handling:** Never make silent assumptions, silent scope cuts, or silent deferrals. Resolve gaps in this order: (1) local canonical docs (`docs/build-plan/`, linked references, ADRs, approved reflections/handoffs when they establish carry-forward rules), (2) targeted web research against primary/current sources to confirm best practice, (3) explicit human decision only if materially different product behaviors remain plausible, sources conflict, or the decision is irreversible/high-risk.
- **Human approval** is mandatory before merge, release, or deploy.

## Operating Model

Three modes map to six project roles:

| Mode | Roles Active | What Happens |
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

## Roles & Workflows

Six deterministic roles in `.agent/roles/`: orchestrator, coder, tester, reviewer, researcher, guardrail.
Canonical workflow: `.agent/workflows/orchestrated-delivery.md`.
Skills (on-demand): `.agent/skills/` — load per task scope during PLANNING (see README inside).

Every plan task must have: `task`, `owner_role`, `deliverable`, `validation` (exact commands), `status`.
Role transitions must be explicit: `orchestrator → coder → tester → reviewer`.
Every acceptance criterion or rule that is not explicit in the target build-plan section must be tagged with its source: `Spec`, `Local Canon`, `Research-backed`, or `Human-approved`. `Best practice` by itself is not an acceptable source label.

### Workflow Invocation

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

## Planning Contract

> [!CAUTION]
> **Plan files go to the project, not the agent workspace.** Per `create-plan.md` Step 4, `implementation-plan.md` and `task.md` MUST be written to `docs/execution/plans/{YYYY-MM-DD}-{project-slug}/`. The agent workspace may receive a copy for UI rendering, but the project folder is the single source of truth — it is what gets validated and version-controlled. Never write plan files only to the agent workspace.

### Spec Sufficiency Gate

Before approving any plan or starting TDD:

1. Read the target build-plan section and the local canonical docs it points to or depends on.
2. Classify each required behavior as `Spec`, `Local Canon`, `Research-backed`, or `Human-approved`.
3. If the build plan is not specific enough to support a complete implementation, run targeted web research against official docs, standards, or other primary/current sources before writing acceptance criteria.
4. Ask the human only when materially different product behaviors remain plausible, the sources conflict, or the choice is irreversible/high-risk.

Under-specified specs are not permission to narrow scope, invent behavior, or defer work.

## Testing & TDD Protocol

- **Tests FIRST, implementation after.** Tests = specification.
- **NEVER modify tests to make them pass.** Fix the implementation.
- Run `pytest` / `vitest` after EVERY code change.
- Coverage targets (advisory): core 80–90%, infra/api/mcp 70%, UI 50–60%.
- See `.agent/docs/testing-strategy.md` for test pyramid and fixtures.

### FIC-Based TDD Workflow (Mandatory)

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

## Execution Contract

- **Git commit policy**: See `.agent/skills/git-workflow/SKILL.md` §Commit Policy. Never auto-commit.
- Run targeted tests after each change.
- **MEU gate** (per-MEU): `uv run python tools/validate_codebase.py --scope meu` — targeted `pyright`, `ruff`, `pytest`, anti-placeholder scan scoped to touched packages/files.
- **Phase gate** (phase exit only): `uv run python tools/validate_codebase.py` when ALL MEUs in a phase are complete. Do NOT run it as a MEU-level gate — it validates the full repo and will fail until later phases are scaffolded.
- **Evidence-first completion:** `task.md` items may never be marked `[x]` unless the handoff or walkthrough contains a complete evidence bundle (changed files + commands executed + test results + artifact references).
- **No-deferral rule:** Items containing `TODO`, `FIXME`, `NotImplementedError`, or placeholder stubs may not be marked `[x]`. Blocked items must use status `[B]` with a linked follow-up task in the handoff.
- **Anti-placeholder enforcement:** Before declaring complete, run `rg "TODO|FIXME|NotImplementedError" packages/` and resolve any matches. Extend the search to `ui/` or `mcp-server/` once those packages are scaffolded.
- A thin spec is not a valid reason to ship a narrower implementation. Resolve the gap in planning/research, update the plan/FIC with the source-backed rule, then implement the full resolved contract.

> [!CAUTION]
> **Anti-premature-stop rule.** Do NOT stop or report to the user during execution unless blocked by an unresolvable error or a human decision gate. Complete ALL workflow exit criteria in a single continuous pass — including post-MEU deliverables (MEU gate, registry update, BUILD_PLAN.md update, reflection, metrics, pomera session save, commit messages). Before reporting completion, re-read `task.md` and verify every item is `[x]`.
>
> **Lifecycle escape hatch**: "Trigger Codex validation" IS classified as an allowed human decision gate. The anti-premature-stop rule permits handing off to Codex. Post-validation artifacts (reflection, metrics) are created in the NEXT session after Codex returns its verdict.
>
> **Context window checkpoint**: If context window exceeds ~80% capacity, save state to `pomera_notes`, complete the current MEU's handoff, and notify human with remaining work. This is a planned checkpoint, not early termination.

## Pre-Handoff Self-Review (Mandatory)

> Before any completion claim or handoff submission, adopt the reviewer mindset. This protocol was distilled from analysis of 7 critical review handoffs (37+ passes) where 10 recurring patterns caused 4-11 passes per project.

1. For each AC, verify the claim against actual file state (quote `file:line`, not memory).
2. Re-run all validation commands and compare counts to what the handoff says.
3. If you fixed one instance of a bug category, `rg` for all instances of the same category.
4. If you changed architecture, `rg` canonical docs for the old pattern.
5. Never say "implementation complete" if residual risk acknowledges known gaps.
6. Stubs must honor behavioral contracts, not just compile.
7. Follow the full protocol in `.agent/skills/pre-handoff-review/SKILL.md`.

## Dual-Agent Workflow

| Aspect | Decision |
|---|---|
| **Reviewer model** | **GPT-5.4** (locked as baseline — do not downgrade) |
| **Reviewer capability** | Run commands, execute tests, check builds, create handoff docs with test improvements |
| **Validation priority** | 1. Contract tests pass/fail → 2. Security posture → 3. Adversarial edge cases → 4. Code style consistency → 5. Documentation accuracy |

> The reviewer (GPT-5.4 Codex) runs commands and creates handoff docs for findings. It is not limited to prose-only review — it produces executable evidence.

## Validation Pipeline

**MEU gate** (active implementation work): `uv run python tools/validate_codebase.py --scope meu`
**Phase gate** (only after all MEUs in a phase are complete): `uv run python tools/validate_codebase.py`

**Blocking checks** apply by scaffold and phase:
- Current scaffold: `pyright`, `ruff`, `pytest`
- When TypeScript packages are scaffolded: `tsc --noEmit`, `eslint`, `vitest`, `npm run build`

**Advisory** (report only): `pytest --cov`, `bandit`, `pip-audit`, `semgrep`.
See `.agent/skills/quality-gate/SKILL.md` for scope selection and skipped-check behavior.

## Testing Requirements

### Testing Decision Framework

When implementing a new feature or bug fix, select test categories by dependency layer:

| Layer | Required Tests | Optional Tests |
|-------|---------------|----------------|
| **Domain** (entities, VOs, calculator) | Unit tests (IR-5 compliant) | Hypothesis property-based |
| **Infrastructure** (repos, UoW, encryption) | Unit + repository contract tests | Encryption verify |
| **Service** (services, validators) | Unit + integration tests | Property-based invariants |
| **API** (routes, middleware) | Unit + OpenAPI contract tests | Schemathesis fuzzing |
| **MCP** (tools, server) | Protocol + adversarial tests | Schema validation |
| **GUI** (React components) | Vitest unit + E2E wave tests | Axe-core accessibility |

### Test Naming Convention

```
tests/
├── unit/          # Isolated tests, mocked dependencies
├── integration/   # Real database, cross-layer
├── security/      # Encryption, log redaction audit
├── property/      # Hypothesis property-based invariants
├── contract/      # OpenAPI + repository contract
└── e2e/           # Playwright Electron (in ui/tests/e2e/)
```

### Coverage Expectations

- **New domain code**: ≥ 90% branch coverage
- **New service code**: ≥ 80% branch coverage
- **New API routes**: ≥ 1 contract test per route + unit tests
- **New GUI pages**: E2E wave tests + axe-core scan (see `docs/build-plan/06-gui.md` §E2E Waves)
- **Bug fixes**: Add regression test before fixing

### E2E Wave Activation

E2E tests activate incrementally as GUI pages are built. When implementing a GUI MEU, check `ui/tests/e2e/test-ids.ts` for required `data-testid` attributes and ensure the wave's tests pass. See `docs/build-plan/06-gui.md` §E2E Waves.

## Code Quality

**Maximum** (core, infrastructure, api, mcp-server):
- Read the ENTIRE file before modifying. Write COMPLETE implementations, not skeletons.
- Handle ALL error states explicitly — no silent failures, no empty `catch {}`.
- Every function: input validation + docstrings. No `TODO`, no `any` type, no `console.log`.
- Use structured logging (`structlog`). Re-throw with context on catch.

**Balanced** (`ui/`, when scaffolded):
- No placeholders. Basic error handling required. `TODO` only with tracked issue ref.

See `.agent/docs/code-quality.md` for full examples and forbidden patterns.

### Anti-Slop Checklist (verify before handoff)

- [ ] Every public function has explicit error handling (no implicit passes)
- [ ] All type annotations are precise (no `Any`, no `# type: ignore` without justification)
- [ ] Edge cases identified in FIC are actually handled in code (not just tested)
- [ ] No inline `# TODO` or commented-out alternatives left behind
- [ ] Code was NOT copied verbatim from build plan — adapt to actual FIC and project structure

## Commits

- **Never auto-commit.** Only `git commit` or `git push` when (a) the user explicitly directs it, or (b) it is a defined step in the approved plan/task. Human always reviews and approves.
- Conventional commits: `feat:`, `fix:`, `refactor:`, `test:`, `docs:`
- **Git skill:** Read `.agent/skills/git-workflow/SKILL.md` (§Commit Policy + §The One Rule) before any git operations.
  - SSH commit signing is configured — all commits are auto-signed, no GPG prompts.
  - **Always** use `git commit -m "message"` — never bare `git commit` (hangs on editor).
  - **Never** use interactive git commands (`git rebase -i`, `git commit --amend` without `--no-edit`).

## Handoff Protocol

At session end, create or update a handoff file:

- Path: `.agent/context/handoffs/{SEQ}-{YYYY-MM-DD}-{slug}-bp{NN}s{X.Y}.md`
- Template: `.agent/context/handoffs/TEMPLATE.md`

## Skills

| Skill | Path | Purpose |
|-------|------|---------|
| Git Workflow | `.agent/skills/git-workflow/SKILL.md` | Agent-safe git operations with SSH commit signing. Prevents interactive prompt hangs. |
| Codebase Quality Gate | `.agent/skills/quality-gate/SKILL.md` | Validation pipeline: type checks, linting, tests, anti-placeholder scans, evidence checks. Supports phase-level and MEU-scoped runs. |
| Pre-Handoff Review | `.agent/skills/pre-handoff-review/SKILL.md` | Self-review protocol addressing 10 recurring patterns from critical review analysis. Reduces average review passes from 4-11 to 3-5. |

## MCP Servers

| Server | Purpose | Verify With |
|--------|---------|-------------|
| `pomera` | Notes, text processing, web search | `pomera_diagnose` |
| `text-editor` | Hash-based conflict-safe editing | `get_text_file_contents` |
| `sequential-thinking` | Complex multi-step analysis | `sequentialthinking` |

## Context & Docs

- Architecture → `.agent/docs/architecture.md`
- Domain model → `.agent/docs/domain-model.md`
- Testing strategy → `.agent/docs/testing-strategy.md`
- Code quality examples → `.agent/docs/code-quality.md`
- Role specs → `.agent/roles/`
- Handoff template → `.agent/context/handoffs/TEMPLATE.md`
- Current focus → `.agent/context/current-focus.md`
- Known issues → `.agent/context/known-issues.md`
- Full specification → `docs/BUILD_PLAN.md`
