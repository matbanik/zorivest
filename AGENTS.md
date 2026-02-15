# Zorivest Agent Instructions

AI-specific guidance for working with the Zorivest codebase. This file is vendor-neutral and works across all AI coding agents. For Antigravity-specific operating rules, see `GEMINI.md`. For agent identity and personality, see `SOUL.md`.

## Quick Commands

```bash
# Validation (blocking — must pass before proceeding)
.\validate.ps1                          # Full validation pipeline
pytest tests/unit/                      # Python unit tests
npx vitest run                          # TypeScript unit tests
pyright packages/                       # Python type check
npx tsc --noEmit                        # TypeScript type check
ruff check packages/                    # Python lint
npx eslint src/ --max-warnings 0        # TypeScript lint

# Development
uv run fastapi dev packages/api/src/zorivest_api/main.py  # Start API
npm run dev                             # Start Electron UI
pytest --cov=packages/core --cov-report=term  # Coverage (advisory)
```

## Architecture

Hybrid monorepo — read `.agent/docs/architecture.md` for full details.

| Layer | Language | Package | Purpose |
|-------|----------|---------|---------|
| Domain | Python | `packages/core` | Entities, value objects, ports, calculator |
| Infra | Python | `packages/infrastructure` | SQLAlchemy, SQLCipher, repos, UoW |
| API | Python | `packages/api` | FastAPI REST on localhost |
| UI | TypeScript | `ui/` | Electron + React GUI |
| MCP | TypeScript | `mcp-server/` | AI agent tool interface |

**Dependency rule:** Domain → Application → Infrastructure. Never import infra from core.

## Session Discipline

- **One task = one session.** Do NOT chain unrelated work streams.
- Tasks must be scoped to complete in a single session (~50–100 tool calls).
- If a task is too large, break it into sub-tasks — each gets its own session.
- **At session start:**
  1. **Read `SOUL.md`** — internalize agent identity, core equation, and interaction principles.
  2. Check `pomera_notes` for previous session state (`search_term: "Zorivest"`).
  3. Read `.agent/context/current-focus.md` for active phase.
  4. Read `.agent/context/known-issues.md` for gotchas.
- **At session end:**
  1. Save progress + next steps to `pomera_notes` with title `Memory/Session/Zorivest-{task}-{date}`.
  2. Update `.agent/context/current-focus.md` with new state.
- **Ambiguity:** ALWAYS ask before proceeding. Never make silent assumptions.

### Task Scoping

✅ Good: "Implement Trade entity + tests" (focused, completable)
✅ Good: "Add SQLAlchemy repository for Trade" (single layer)
❌ Bad: "Implement entire Phase 1" (too broad, will degrade)
❌ Bad: "Fix bug then also add new feature" (two work streams)

## Role-Based Subagents

Use deterministic role specs, not open-ended personas.

### Canonical Workflow

- `.agent/workflows/orchestrated-delivery.md`

### Role Specs

- Required: `.agent/roles/orchestrator.md`
- Required: `.agent/roles/coder.md`
- Required: `.agent/roles/tester.md`
- Required: `.agent/roles/reviewer.md`
- Optional: `.agent/roles/researcher.md`
- Optional: `.agent/roles/guardrail.md`

### Invocation Pattern

Use explicit role adoption in the prompt:

```text
Adopt role from .agent/roles/reviewer.md.
Task: review current diff for regression risk.
Follow the Output Contract exactly.
```

### Plan Creation Contract (Required)

When an agentic IDE is prompted to create a plan, it MUST assign a role to every plan task from `.agent/roles/`.

- Required plan fields per task:
  - `task`
  - `owner_role` (one of orchestrator/coder/tester/reviewer/researcher/guardrail)
  - `deliverable`
  - `validation` (exact command(s) to run)
  - `status` (`pending`, `in_progress`, `done`)
- No unowned tasks are allowed.
- If work does not map cleanly to an existing role, `orchestrator` must split/refine the task or request clarification.
- Role transitions must be explicit in the plan (`orchestrator -> coder -> tester -> reviewer`).

### Hard Gate

- **Human approval is mandatory** before merge, release, or deploy actions.

## Agent Runtime: Antigravity

When using Google Antigravity as the AI agent, the role system maps to Antigravity's three `task_boundary` modes:

| Antigravity Mode | Roles Active | What Happens |
|---|---|---|
| **PLANNING** | orchestrator, researcher | Scope task, read context, research patterns, create plan |
| **EXECUTION** | coder | Implement changes, run targeted tests |
| **VERIFICATION** | tester, reviewer, guardrail | Full validation, adversarial review, safety checks |

### MCP Server Requirements

Verify these servers are available at session start (call `pomera_diagnose`):

| Server | Purpose |
|---|---|
| `pomera` | Notes, text processing, web search, AI tools |
| `text-editor` | Hash-based conflict-safe file editing |
| `sequential-thinking` | Complex multi-step analysis |

If required servers are unavailable, report to user via `notify_user` and do not proceed.

### Workflow Invocation

- `/orchestrated-delivery` → `.agent/workflows/orchestrated-delivery.md`
- `/pre-build-research` → `.agent/workflows/pre-build-research.md`

## Planning And Execution Best Practices

- Define a single measurable objective and explicit out-of-scope items before coding.
- Break work into small, dependency-ordered tasks that can each be validated independently.
- Attach acceptance criteria and validation commands to each task before implementation begins.
- Run targeted tests after each change; run blocking full validation before declaring done.
- Log assumptions and decisions in task notes/handoffs to avoid hidden context.
- Prefer reversible changes and keep rollback notes for risky refactors.
- Require reviewer sign-off on regression risk, edge cases, and missing tests.
- End every session with: completed items, remaining risks, and next concrete step.

## Testing (TDD)

- **Tests FIRST, implementation after.** Human writes tests = specification.
- **NEVER modify tests to make them pass.** Fix the implementation.
- Run `pytest` / `vitest` after EVERY code change.
- Coverage targets (advisory): core 80–90%, infra/api/mcp 70%, UI 50–60%.

Read `.agent/docs/testing-strategy.md` for test pyramid and fixtures.

## Validation Pipeline

**Blocking** (must fix before proceeding):
- Type check: `pyright`, `tsc --noEmit`
- Lint: `ruff`, `eslint`
- Tests: `pytest`, `vitest`
- Build: `npm run build`

**Advisory** (report, don't block):
- Coverage: `pytest --cov`
- Security: `bandit`, `pip-audit`

## Code Quality (Tiered)

**Maximum** (core, infrastructure, api, mcp-server):
- Read the ENTIRE file before modifying it
- NEVER use "// rest of implementation here" or "// ... existing code ..."
- Handle ALL error states explicitly — no silent failures
- Every function must have input validation
- Write the COMPLETE implementation, not a skeleton
- No `TODO` comments — implement it or create an issue
- No `any` type in TypeScript — use proper types
- No empty `catch {}` — handle or re-throw with context
- No `console.log` — use structured logging (`structlog`)
- Docstrings on every exported function/class

**Balanced** (ui/):
- No placeholders or skeleton code
- Basic error handling required (no empty catch)
- `TODO` allowed ONLY if referencing a tracked issue (e.g., `// TODO(#42): add animation`)
- `console.warn` allowed for development debugging
- Docstrings only on complex/non-obvious components

## Forbidden Patterns

```python
# ❌ NEVER
except Exception:
    pass

# ✅ ALWAYS
except SpecificError as e:
    logger.error("operation_failed", error=str(e), context=ctx)
    raise
```

```typescript
// ❌ NEVER
catch (e) {}

// ✅ ALWAYS
catch (e: unknown) {
  logger.error('Operation failed', { error: e instanceof Error ? e.message : String(e) });
  throw;
}
```

## Commits

- **Never auto-commit.** Human always reviews and approves.
- Use conventional commits: `feat:`, `fix:`, `refactor:`, `test:`, `docs:`

## Handoff Protocol

**At session start:**
1. Search `pomera_notes` for previous session state (`search_term: "Zorivest"`).
2. Read `.agent/context/current-focus.md` for active phase.
3. Read `.agent/context/known-issues.md` for gotchas.

**At session end:**
1. Create/update handoff: `.agent/context/handoffs/{YYYY-MM-DD}-{task-slug}.md` (use TEMPLATE.md).
2. Save progress to `pomera_notes` with title `Memory/Session/Zorivest-{task}-{date}`.
3. Update `.agent/context/current-focus.md` with new state.

## Context & Docs

- **Agent identity** → `SOUL.md` (read at every session start)
- Architecture details → `.agent/docs/architecture.md`
- Antigravity mode mapping → `.agent/docs/antigravity-mode-map.md`
- Domain model → `.agent/docs/domain-model.md`
- Testing strategy → `.agent/docs/testing-strategy.md`
- Orchestrated workflow → `.agent/workflows/orchestrated-delivery.md`
- Pre-build research workflow → `.agent/workflows/pre-build-research.md`
- Role specs → `.agent/roles/`
- Task handoff template → `.agent/context/handoffs/TEMPLATE.md`
- Current work in progress → `.agent/context/current-focus.md`
- Known bugs → `.agent/context/known-issues.md`
- Full specification → `docs/BUILD_PLAN.md`
