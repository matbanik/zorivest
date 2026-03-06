# Zorivest Agent Instructions

AI-specific guidance for working with the Zorivest codebase. Vendor-neutral — works across all agents.
For Antigravity-specific rules, see `GEMINI.md`. For identity, see `SOUL.md`.

## Quick Commands

```bash
# Validation (blocking — must pass before proceeding)
.\tools\validate.ps1                    # Full validation pipeline
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

Hybrid monorepo — see `.agent/docs/architecture.md` for full details.

| Layer | Language | Package | Purpose |
|-------|----------|---------|---------|
| Domain | Python | `packages/core` | Entities, value objects, ports, calculator |
| Infra | Python | `packages/infrastructure` | SQLAlchemy, SQLCipher, repos, UoW |
| API | Python | `packages/api` | FastAPI REST on localhost |
| UI | TypeScript | `ui/` | Electron + React GUI |
| MCP | TypeScript | `mcp-server/` | AI agent tool interface |

**Dependency rule:** Domain → Application → Infrastructure. Never import infra from core.

## Project Context

> [!IMPORTANT]
> **Zorivest does NOT execute trades — it plans and evaluates.** The software imports trade results from execution platforms (Interactive Brokers, etc.), analyzes performance, and generates trade plans. It never places, modifies, or cancels orders. All references to "trade confirmation" or "execution safety" apply to data-destructive operations (e.g., deleting trade records), NOT financial execution.

## Session Discipline

- **One task = one session.** Do NOT chain unrelated work streams.
- **Time is not a constraint** in agentic development cycles. Do not optimize for speed over quality.
- **Token usage is not a constraint** (subscription-based). Do not truncate, summarize prematurely, or skip work to save tokens.
- **Do not bring up time or token usage** in design discussions, trade-off analyses, or implementation decisions. Quality, wisdom, and expert experience are the only optimization targets.
- **At session start:** Read `SOUL.md`, check `pomera_notes` (`search_term: "Zorivest"`), read `.agent/context/current-focus.md` and `known-issues.md`.
- **At session end:** Save to `pomera_notes` (`Memory/Session/Zorivest-{task}-{date}`), update `current-focus.md`, create/update handoff at `.agent/context/handoffs/`.
- **Ambiguity:** ALWAYS ask before proceeding. Never make silent assumptions.
- **Human approval** is mandatory before merge, release, or deploy.

## Roles & Workflows

Six deterministic roles in `.agent/roles/`: orchestrator, coder, tester, reviewer, researcher, guardrail.
Canonical workflow: `.agent/workflows/orchestrated-delivery.md`.
Skills (on-demand): `.agent/skills/` — load per task scope during PLANNING (see README inside).

Every plan task must have: `task`, `owner_role`, `deliverable`, `validation` (exact commands), `status`.
Role transitions must be explicit: `orchestrator → coder → tester → reviewer`.

## Testing (TDD)

- **Tests FIRST, implementation after.** Tests = specification.
- **NEVER modify tests to make them pass.** Fix the implementation.
- Run `pytest` / `vitest` after EVERY code change.
- Coverage targets (advisory): core 80–90%, infra/api/mcp 70%, UI 50–60%.
- See `.agent/docs/testing-strategy.md` for test pyramid and fixtures.

## Validation Pipeline

**Blocking** (must fix): `pyright`, `tsc --noEmit`, `ruff`, `eslint`, `pytest`, `vitest`, `npm run build`.
**Advisory** (report only): `pytest --cov`, `bandit`, `pip-audit`.

## Code Quality

**Maximum** (core, infrastructure, api, mcp-server):
- Read the ENTIRE file before modifying. Write COMPLETE implementations, not skeletons.
- Handle ALL error states explicitly — no silent failures, no empty `catch {}`.
- Every function: input validation + docstrings. No `TODO`, no `any` type, no `console.log`.
- Use structured logging (`structlog`). Re-throw with context on catch.

**Balanced** (ui/):
- No placeholders. Basic error handling required. `TODO` only with tracked issue ref.

See `.agent/docs/code-quality.md` for full examples and forbidden patterns.

## Commits

- **Never auto-commit.** Human always reviews and approves.
- Conventional commits: `feat:`, `fix:`, `refactor:`, `test:`, `docs:`

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
