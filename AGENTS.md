# Zorivest Agent Instructions

AI-specific guidance for working with the Zorivest codebase. Vendor-neutral — works across all agents.
For Antigravity-specific rules, see `GEMINI.md`. For identity, see `SOUL.md`.

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

## Session Discipline

- **One project = one session.** Group related tasks into a coherent project by dependency order. Do NOT chain unrelated work streams.
- **Time is not a constraint** in agentic development cycles. Do not optimize for speed over quality.
- **Token usage is not a constraint** (subscription-based). Do not truncate, summarize prematurely, or skip work to save tokens.
- **Do not bring up time or token usage** in design discussions, trade-off analyses, or implementation decisions. Quality, wisdom, and expert experience are the only optimization targets.
- **At session start:** Read `SOUL.md`, check `pomera_notes` (`search_term: "Zorivest"`), read `.agent/context/current-focus.md` and `.agent/context/known-issues.md`. Verify MCP server availability when the workflow depends on `pomera`, `text-editor`, or `sequential-thinking`.
- **At session end:** Save to `pomera_notes` (`Memory/Session/Zorivest-{project-slug}-{date}`) and create/update handoff(s) at `.agent/context/handoffs/`. Update `.agent/context/current-focus.md` only when the session changes project state; review-only sessions should not overwrite unrelated focus state.
- **Handoff continuity:** For the same `docs/execution/plans/{YYYY-MM-DD}-{project-slug}/` target, keep plan review in one rolling `-plan-critical-review.md` file and project implementation critique/recheck in one rolling `-implementation-critical-review.md` file. Append updates to the same file instead of creating new `-recheck`, `-final`, or `-approved` variants.
- **Under-specified build-plan handling:** Never make silent assumptions, silent scope cuts, or silent deferrals. Resolve gaps in this order: (1) local canonical docs (`docs/build-plan/`, linked references, ADRs, approved reflections/handoffs when they establish carry-forward rules), (2) targeted web research against primary/current sources to confirm best practice, (3) explicit human decision only if materially different product behaviors remain plausible, sources conflict, or the decision is irreversible/high-risk.
- **Human approval** is mandatory before merge, release, or deploy.

## Roles & Workflows

Six deterministic roles in `.agent/roles/`: orchestrator, coder, tester, reviewer, researcher, guardrail.
Canonical workflow: `.agent/workflows/orchestrated-delivery.md`.
Skills (on-demand): `.agent/skills/` — load per task scope during PLANNING (see README inside).

Every plan task must have: `task`, `owner_role`, `deliverable`, `validation` (exact commands), `status`.
Role transitions must be explicit: `orchestrator → coder → tester → reviewer`.
Every acceptance criterion or rule that is not explicit in the target build-plan section must be tagged with its source: `Spec`, `Local Canon`, `Research-backed`, or `Human-approved`. `Best practice` by itself is not an acceptable source label.

## Testing (TDD)

- **Tests FIRST, implementation after.** Tests = specification.
- **NEVER modify tests to make them pass.** Fix the implementation.
- Run `pytest` / `vitest` after EVERY code change.
- Coverage targets (advisory): core 80–90%, infra/api/mcp 70%, UI 50–60%.
- See `.agent/docs/testing-strategy.md` for test pyramid and fixtures.

## Validation Pipeline

**MEU gate** (active implementation work): `uv run python tools/validate_codebase.py --scope meu`
**Phase gate** (only after all MEUs in a phase are complete): `uv run python tools/validate_codebase.py`

**Blocking checks** apply by scaffold and phase:
- Current scaffold: `pyright`, `ruff`, `pytest`
- When TypeScript packages are scaffolded: `tsc --noEmit`, `eslint`, `vitest`, `npm run build`

**Advisory** (report only): `pytest --cov`, `bandit`, `pip-audit`.
See `.agent/skills/quality-gate/SKILL.md` for scope selection and skipped-check behavior.

## Code Quality

**Maximum** (core, infrastructure, api, mcp-server):
- Read the ENTIRE file before modifying. Write COMPLETE implementations, not skeletons.
- Handle ALL error states explicitly — no silent failures, no empty `catch {}`.
- Every function: input validation + docstrings. No `TODO`, no `any` type, no `console.log`.
- Use structured logging (`structlog`). Re-throw with context on catch.

**Balanced** (`ui/`, when scaffolded):
- No placeholders. Basic error handling required. `TODO` only with tracked issue ref.

See `.agent/docs/code-quality.md` for full examples and forbidden patterns.

## Commits

- **Never auto-commit.** Human always reviews and approves.
- Conventional commits: `feat:`, `fix:`, `refactor:`, `test:`, `docs:`
- **Git skill:** Read `.agent/skills/git-workflow/SKILL.md` before any git operations.
  - SSH commit signing is configured — all commits are auto-signed, no GPG prompts.
  - **Always** use `git commit -m "message"` — never bare `git commit` (hangs on editor).
  - **Never** use interactive git commands (`git rebase -i`, `git commit --amend` without `--no-edit`).

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
