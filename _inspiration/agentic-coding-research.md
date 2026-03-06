# Agentic Coding Best Practices — Opus 4.6 in IDE

> Research findings from Feb 2026 + pre-answered questionnaire from Zorivest docs.

---

## 1. Key Best Practices Summary

### AGENTS.md / CLAUDE.md

| Rule | Detail |
|------|--------|
| **≤150 lines** | Bloated files cause agents to ignore instructions |
| **Executable commands** | Backtick commands: `pytest`, `npm test`, `./validate.sh` |
| **Progressive disclosure** | Root file says HOW TO FIND docs, not duplicates them |
| **Show real examples** | Actual code snippets, not abstract descriptions |
| **Treat as code** | Review/prune regularly based on observed behavior |
| **Nest for monorepos** | Subdirectory files override root |

### .agent/ Directory

```
.agent/
├── docs/          # Deep-dive reference (architecture, API, testing)
├── workflows/     # Step-by-step procedures (slash commands)
├── context/       # Living state (current-focus, known-issues)
└── templates/     # Boilerplate for new files
```

### TDD with AI Agents

1. **Human writes tests, AI writes implementation** — design intent comes from you
2. **Never let AI modify tests to pass** — tests are the specification
3. **Context isolation** — write tests in separate turn from implementation
4. **Run tests after every change** — immediate red/green feedback
5. **Edge cases in tests** — force null/empty/boundary/error handling

### Anti-Laziness Strategies (from community research)

The "lazy code" problem is well-documented with Opus 4.5/4.6. These are the **5 proven strategies**:

#### Strategy 1: Explicit AGENTS.md Rules (most common)
```markdown
- Read the ENTIRE file before modifying it
- NEVER use "// rest of implementation here" or "// ... existing code ..."
- Handle ALL error states explicitly — no silent failures
- Every function must have input validation
- Write the COMPLETE implementation, not a skeleton
- No TODO comments — implement now or create a tracked issue
```

#### Strategy 2: State Freezing (advanced)
When context gets polluted, extract the "Decision State" — active plan, constraints, rules — compress it into a block, then inject into a fresh session. Eliminates laziness from history decay.

#### Strategy 3: Stop Hooks
Scripts that **prevent the AI from finishing** until conditions are met (e.g., all tests pass). Forces the agent to keep working until genuinely complete. In Antigravity, the validation pipeline serves this role.

#### Strategy 4: Adversarial Review Prompting
Instead of "review this code," use: *"Find problems in this code. Assume there are at least 3 bugs."* Forces active hunting rather than rubber-stamping.

#### Strategy 5: TDD as Anti-Laziness
Tests are the ultimate guard — if the test asserts `result.risk_per_share == 1.00`, the AI can't skip the implementation. The test fails. This is Zorivest's primary defense.

#### Tiered Strictness (Zorivest decision)

| Layer | Level | Rules |
|-------|-------|-------|
| `packages/core` | **Maximum** | No TODOs, no placeholders, no `any`, no empty catch, complete error handling, full docstrings |
| `packages/infrastructure` | **Maximum** | Same — data integrity is critical |
| `packages/api` | **Maximum** | Same — API is the security boundary |
| `ui/` | **Balanced** | No placeholders, basic error handling, TODOs allowed if referencing a tracked issue |
| `mcp-server/` | **Maximum** | AI tools must be robust |

### Continuous Validation Script

```bash
#!/bin/bash
set -e
echo "=== Type Check ===" && npx tsc --noEmit
echo "=== Lint ===" && npx eslint src/ --max-warnings 0
echo "=== Python Lint ===" && ruff check packages/
echo "=== Python Types ===" && pyright packages/
echo "=== Unit Tests ===" && pytest tests/python/unit/ && npx vitest run
echo "=== Build ===" && npm run build
echo "✅ All checks passed"
```

---

## 2. Pre-Answered Questionnaire (from Zorivest docs)

I reviewed all 5 docs files. Below, ✅ = answered from docs, ❓ = needs your input.

### A. Project Architecture

| # | Question | Answer from Docs |
|---|----------|-----------------|
| 1 | **Primary tech stack?** | ✅ **Hybrid**: TypeScript (Electron + React) for UI + Python (FastAPI + SQLCipher + ibapi) for backend. MCP server in TypeScript. Connected via REST on localhost. |
| 2 | **Monorepo or single-package?** | ✅ **Monorepo**: `uv` workspaces for Python (`packages/core`, `packages/infrastructure`, `packages/api`), npm/pnpm workspaces for TypeScript (`ui/`, `mcp-server/`). |
| 3 | **How many modules?** | ✅ **6+**: core, infrastructure, api (Python) + ui, mcp-server (TypeScript) + tests. Medium-large. |

### B. Testing Strategy

| # | Question | Answer from Docs |
|---|----------|-----------------|
| 4 | **Coverage target?** | ✅ **Tiered advisory**: core 80–90%, infra/api/mcp 70%, UI 50–60%. Advisory (reported but not blocking) — TDD naturally yields good coverage. |
| 5 | **Test types?** | ✅ **All**: Unit (domain, calculator), Integration (repos, UoW, DB), E2E (API endpoints via TestClient), TypeScript (vitest for MCP + React Testing Library for UI + Playwright for E2E). |
| 6 | **Who writes tests vs implementation?** | ✅ **Tests first (TDD)**: BUILD_PLAN explicitly says "WRITE THIS FIRST" for tests, implementation follows. Human defines spec via tests. |
| 7 | **Tests before or after?** | ✅ **Before**: Classic TDD. "The golden rule: run `pytest` and have all tests pass before moving to the next phase." |

### C. Validation Pipeline

| # | Question | Answer from Docs |
|---|----------|-----------------|
| 8 | **Which validators?** | ✅ **All of the above**: Type checker (`tsc --noEmit`, `pyright`), Linter (`eslint`, `ruff`), Unit tests (`pytest`, `vitest`), Build verification, plus `bandit` for security, `pip-audit` for vulnerabilities. |
| 9 | **Blocking or advisory?** | ✅ **Hybrid**: type+lint+test+build = blocking (must fix before proceeding). Coverage+security = advisory (reported, not gating). |
| 10 | **Design-spec validator?** | ✅ **Skipped**: TDD test suite serves as the design-spec validator — if tests exist and pass, the feature is implemented. No extra script needed. |

### D. Context Management

| # | Question | Answer from Docs |
|---|----------|-----------------|
| 11 | **Context window limits?** | ✅ **One task = one session**. Antigravity provides 1M tokens per session (Opus 4.6) with auto-compression. Progressive disclosure via `.agent/docs/`. Each task scoped to complete in a single session (~50–100 tool calls). New task = new session = fresh context. |
| 12 | **Docs always accessible?** | ✅ **Progressive disclosure**: DESIGN_PROPOSAL §AI agent workflow says "Keep CLAUDE.md minimal, tell Claude how to find information rather than dumping everything." Points to `docs/decisions/` for ADRs. |
| 13 | **Session handoff?** | ✅ **pomera_notes protocol**: At session end, save progress + next steps to notes. At session start, check notes for previous session state. Conversation logs also available for recovery. |

### E. Code Quality Enforcement

| # | Question | Answer from Docs |
|---|----------|-----------------|
| 14 | **Anti-laziness strictness?** | ✅ **Tiered**: Maximum for `packages/core`, `packages/infrastructure`, `packages/api`, `mcp-server/`. Balanced for `ui/` (TODOs allowed if referencing tracked issue). See §1 for 5 community strategies. |
| 15 | **Forbidden patterns?** | ✅ Partially: Docs specify Pydantic strict mode, input validation, bandit static analysis, no hardcoded secrets. **Recommend** adding: no TODOs, no `any`, no `catch {}`, no console.log. |
| 16 | **JSDoc/docstrings?** | ✅ **Tiered**: Every exported function/class in `packages/core`, `packages/infrastructure`, `packages/api`, `mcp-server/`. Only complex/non-obvious functions in `ui/` (React components are self-documenting via props). |

### F. Workflow Preferences

| # | Question | Answer from Docs |
|---|----------|-----------------|
| 17 | **Slash command workflows?** | ✅ **Deferred** — create organically as patterns emerge during development. Candidates for later: `/implement-feature`, `/add-test`, `/validate`, `/refactor`. |
| 18 | **Plan before coding?** | ✅ **Yes**: BUILD_PLAN establishes Plan→Implement→Test→Validate cycle. ADRs required for architectural decisions. |
| 19 | **Auto-commit?** | ✅ **Never** — human always approves commits. AI proposes changes, user reviews and commits. |

### G. IDE Integration

| # | Question | Answer from Docs |
|---|----------|-----------------|
| 20 | **Primary IDE?** | ✅ **Antigravity** — Google DeepMind agentic IDE with Opus 4.6, 1M token context, auto-compression. |
| 21 | **MCP server integration?** | ✅ **Maximum**: TypeScript MCP server is P0 in the architecture. Full tool access (create trades, plans, reviews, calculator, screenshots). |
| 22 | **Handle ambiguity?** | ✅ **Always ask**: When encountering unclear requirements, naming conventions, or multiple valid approaches — stop and ask before proceeding. Never make silent assumptions. |

---

## 3. Questionnaire Complete

> [!TIP]
> All 22 questions answered. Ready to generate the final `AGENTS.md` and `.agent/` structure.

**Already decided:** Primary IDE = Antigravity. Auto-commit = never. Slash commands = TBD during `.agent/workflows/` creation.

---

## 4. Recommended AGENTS.md Structure

```
zorivest/
├── AGENTS.md          # ≤150 lines — setup, test, style, boundaries
├── .agent/
│   ├── docs/
│   │   ├── architecture.md          # → derived from DESIGN_PROPOSAL.md
│   │   ├── domain-model.md          # → extracted from BUILD_PLAN.md
│   │   ├── api-contracts.md         # REST endpoints, schemas
│   │   ├── testing-strategy.md      # Test pyramid, tools, commands
│   │   └── mcp-tools.md             # MCP tool definitions
│   ├── workflows/
│   │   ├── feature-workflow.md      # Plan → Test → Implement → Validate
│   │   ├── testing-workflow.md      # Write test → Run → Cover edge cases
│   │   ├── validation-workflow.md   # Full validation pipeline
│   │   └── phase-workflow.md        # BUILD_PLAN phases as checklist
│   ├── context/
│   │   ├── current-focus.md         # Active phase, current task
│   │   ├── known-issues.md          # Bugs, limitations
│   │   └── recent-changes.md        # Change log
│   └── templates/
│       ├── entity.template.py       # New domain entity boilerplate
│       ├── service.template.py      # New service boilerplate
│       ├── test.template.py         # New pytest test file
│       └── mcp-tool.template.ts     # New MCP tool boilerplate
├── docs/
│   ├── APPLICATION_PURPOSE.md       # ✓ already here
│   ├── DESIGN_PROPOSAL.md           # ✓ already here
│   ├── BUILD_PLAN.md                # ✓ already here
│   └── decisions/                   # ADRs (ADR-0001.md, etc.)
└── validate.ps1                     # Windows PowerShell validation script
```

---

## 5. Draft AGENTS.md Content

> Copy-paste ready. Combines all answered questionnaire items into the actual file.

```markdown
# AGENTS.md — Zorivest

AI-specific guidance for working with the Zorivest codebase.

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
- Tasks must be scoped to complete within a single session (~50–100 tool calls).
- If a task is too large, break it into sub-tasks — each gets its own session.
- **At session end:** Save progress + next steps to pomera_notes.
- **At session start:** Check pomera_notes for previous session state.

### Task Scoping

✅ Good: "Implement Trade entity + tests" (focused, completable)
✅ Good: "Add SQLAlchemy repository for Trade" (single layer)
❌ Bad: "Implement entire Phase 1" (too broad, will degrade)
❌ Bad: "Fix bug then also add new feature" (two work streams)

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

**Balanced** (ui/):
- No placeholders or skeleton code
- Basic error handling required (no empty catch)
- `TODO` allowed ONLY if referencing a tracked issue (e.g., `// TODO(#42): add animation`)
- `console.warn` allowed for development debugging

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

## Context & Docs

- For architecture details → `.agent/docs/architecture.md`
- For domain model → `.agent/docs/domain-model.md`
- For API contracts → `.agent/docs/api-contracts.md`
- For testing strategy → `.agent/docs/testing-strategy.md`
- For MCP tool definitions → `.agent/docs/mcp-tools.md`
- For current work in progress → `.agent/context/current-focus.md`
- For known bugs → `.agent/context/known-issues.md`
```

---

## Sources

- [agents.md](https://agents.md) — Official standard (60k+ projects)
- [agentsmd.io](https://agentsmd.io) — Templates and examples
- [GitHub Blog](https://github.blog) — AI coding agent context best practices
- [Anthropic Docs](https://docs.anthropic.com) — Claude Code / CLAUDE.md
- [humanlayer.dev](https://humanlayer.dev) — CLAUDE.md guide
- [Cursor Docs](https://docs.cursor.com) — Agent harness and rules
