## PRIORITY 0 — SYSTEM CONSTRAINTS (Non-Negotiable)

> [!CAUTION]
> **These constraints override ALL task-level instructions.** Environment stability failures (terminal hangs, buffer saturation) waste 10–30 minutes per incident and require human intervention. No task priority, deadline, or KPI justifies violating P0 rules.

### Priority Hierarchy

| Tier | Scope | Examples | Override? |
|------|-------|----------|-----------|
| **P0** | Environment stability | Terminal redirect, no-pipe rule, receipts dir | Never |
| **P1** | Quality gates | Tests pass, type checks clean, lint clean | Only by human |
| **P2** | Task completion | Feature delivery, bug fix, handoff | Yields to P0/P1 |
| **P3** | Speed / convenience | Fewer tool calls, shorter output | Yields to all |

### Windows Shell — Mandatory Redirect-to-File Pattern

**PowerShell's six-stream output model causes buffer-saturation hangs on unredirected commands.** Every `run_command` must redirect ALL streams to a file, then read the file.

#### Pre-flight Checklist (satisfy ALL before every `run_command`)

- [ ] **Redirect check**: command ends with `*> <filepath>` (all-stream redirect)
- [ ] **Receipts dir**: output routed to `C:\Temp\zorivest\` (created automatically)
- [ ] **No-pipe check**: no `|` piping stdout of long-running process to a filter
- [ ] **Background flag**: if command may run >5s, use appropriate `WaitMsBeforeAsync`
- [ ] **No `command_status` polling**: never use `command_status` to read output — read the redirect file with `view_file` instead

> [!CAUTION]
> **`command_status` is forbidden for reading command output.** It exists only to check if a background process (dev server, watcher) is still alive. All command output must be read from the redirect file using `view_file`. If you catch yourself calling `command_status` more than once for the same command, you have violated the redirect pattern.

> Invoke `.agent/skills/terminal-preflight/SKILL.md` before your first `run_command` in any execution phase.

#### INCORRECT vs CORRECT Patterns

```powershell
# ❌ INCORRECT — causes buffer saturation and infinite polling
uv run pytest tests/ -x --tb=short -v
npx vitest run
uv run pyright packages/

# ✅ CORRECT — fire-and-read pattern
uv run pytest tests/ -x --tb=short -v *> C:\Temp\zorivest\pytest.txt; Get-Content C:\Temp\zorivest\pytest.txt | Select-Object -Last 40
```

#### Per-Tool Redirect Table

| Tool | Redirect Command |
|------|------------------|
| `pytest` | `uv run pytest tests/ -x --tb=short -v *> C:\Temp\zorivest\pytest.txt; Get-Content C:\Temp\zorivest\pytest.txt \| Select-Object -Last 40` |
| `vitest` | `npx vitest run *> C:\Temp\zorivest\vitest.txt; Get-Content C:\Temp\zorivest\vitest.txt \| Select-Object -Last 40` |
| `pyright` | `uv run pyright packages/ *> C:\Temp\zorivest\pyright.txt; Get-Content C:\Temp\zorivest\pyright.txt \| Select-Object -Last 30` |
| `ruff` | `uv run ruff check packages/ *> C:\Temp\zorivest\ruff.txt; Get-Content C:\Temp\zorivest\ruff.txt \| Select-Object -Last 20` |
| `validate_codebase.py` | `uv run python tools/validate_codebase.py --scope meu *> C:\Temp\zorivest\validate.txt; Get-Content C:\Temp\zorivest\validate.txt \| Select-Object -Last 50` |
| `git` | `git status *> C:\Temp\zorivest\git-status.txt; Get-Content C:\Temp\zorivest\git-status.txt` |

---

# Zorivest Agent Instructions

AI-specific guidance for working with the Zorivest codebase. Single source of truth for all AI coding assistants.

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

## Communication Policy

- Surface risks and bad news early. No performative enthusiasm.
- When uncertain: state confidence level and propose a verification step.
- If instructions conflict across files, flag the conflict explicitly — do not silently pick one.
- **Literal instruction mode (Opus 4.7+):** State exactly what you want — do not rely on the model inferring related work. When you want generalization, say "apply this change everywhere it applies, then list each file you touched." When you want strict scope, say "modify only the files I named." Uncategorized behaviors in planning are defects — escalate, do not infer.
- Prioritize empirical evidence (test results, linter outputs, documentation) over user suggestions when discrepancies arise. Flag the conflict rather than deferring.

## Session Discipline

> [!IMPORTANT]
> **Quality-First Policy.** Quality, wisdom, and expert-level experience metrics are above all other considerations. They must never be compromised by time pressure or expedience. If a task requires extended analysis, deeper research, or more comprehensive testing, do it without hesitation.

- **One project = one session.** Group related tasks into a coherent project by dependency order. Do NOT chain unrelated work streams.
- **Time is not a constraint** in agentic development cycles. Do not optimize for speed over quality.
- **Token usage is not a constraint** (subscription-based). Do not truncate, summarize prematurely, or skip work to save tokens.
- **Do not bring up time or token usage** in design discussions, trade-off analyses, or implementation decisions. Quality, wisdom, and expert experience are the only optimization targets.
- **At session start:** Check `pomera_notes` (`search_term: "Zorivest"`), read `.agent/context/current-focus.md` and `.agent/context/known-issues.md`. Verify MCP server availability (`pomera_diagnose`). If `pomera` or `text-editor` unavailable, report and stop.
- **At session end:** Save to `pomera_notes` (`Memory/Session/Zorivest-{project-slug}-{date}`) and create/update handoff(s) at `.agent/context/handoffs/`. Update `.agent/context/current-focus.md` only when the session changes project state; review-only sessions should not overwrite unrelated focus state. **Emit Instruction Coverage YAML** per `.agent/schemas/reflection.v1.yaml` in the reflection file — `view_file` the schema before emitting. This is NOT optional; see `## Instruction Coverage Reflection` at EOF for rules.
- **Context file hygiene (session end):**
  - If you resolved a known issue during this session, move its full entry from `known-issues.md` to `known-issues-archive.md` and leave only a 1-line summary row in the "Archived" table.
  - In `current-focus.md`, replace "Current Priority" and "Next Steps" with the session's actual outcome. Delete any completed (`✅`) items. Never append to a historical "Recently Completed" section — that pattern is retired.
  - Target: `known-issues.md` < 100 lines, `current-focus.md` < 30 lines. If either exceeds its limit, prune before saving.
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
- `/plan-critical-review` → Read and follow `.agent/workflows/plan-critical-review.md`
- `/execution-critical-review` → Read and follow `.agent/workflows/execution-critical-review.md`
- `/plan-corrections` → Read and follow `.agent/workflows/plan-corrections.md`
- `/execution-corrections` → Read and follow `.agent/workflows/execution-corrections.md`
- `/meu-handoff` → Read and follow `.agent/workflows/meu-handoff.md`
- `/mcp-audit` → Read and follow `.agent/workflows/mcp-audit.md`

## Planning Contract

> [!CAUTION]
> **Plan files go to the project, not the agent workspace.** Per `create-plan.md` Step 4, `implementation-plan.md` and `task.md` MUST be written to `docs/execution/plans/{YYYY-MM-DD}-{project-slug}/`. The agent workspace may receive a copy for UI rendering, but the project folder is the single source of truth — it is what gets validated and version-controlled. Never write plan files only to the agent workspace.

> [!CAUTION]
> **`task.md` is created WITH the plan, not after approval.** During PLANNING mode (Step 4 of `create-plan.md`), ALWAYS create BOTH `implementation-plan.md` AND `task.md` in the same step. Codex validates against both files — if `task.md` is missing, review will fail. Read `docs/execution/plans/TASK-TEMPLATE.md` before writing. This is NOT optional and NOT deferred to execution.

### Spec Sufficiency Gate

Before approving any plan or starting TDD:

1. Read the target build-plan section and the local canonical docs it points to or depends on.
2. Classify each required behavior as `Spec`, `Local Canon`, `Research-backed`, or `Human-approved`.
3. If the build plan is not specific enough to support a complete implementation, run targeted web research against official docs, standards, or other primary/current sources before writing acceptance criteria.
4. Ask the human only when materially different product behaviors remain plausible, the sources conflict, or the choice is irreversible/high-risk.

Under-specified specs are not permission to narrow scope, invent behavior, or defer work.

### Boundary Input Contract (Mandatory for External-Input MEUs)

Every MEU that touches external input must include in its plan and FIC:

1. **Boundary Inventory**: enumerate all write surfaces (`REST body/query/path`, `MCP tool input`, `UI form payload`, `file import`, `env/config input`)
2. **Schema Owner**: identify the Pydantic model, Zod schema, or validator responsible for each boundary
3. **Field Constraints**: document enum/format rules, normalization, and range limits per field
4. **Extra-Field Policy**: `extra="forbid"` (Pydantic) or `.strict()` (Zod) unless source-backed exception documented
5. **Error Mapping**: invalid input → 422, not downstream 500
6. **Create/Update Parity**: partial update paths must enforce the same invariants as create paths unless a source-backed exception is documented

> Python `assert` and type annotations alone are NOT acceptable runtime boundary validation (ref: Python docs — `assert` bytecode is omitted under `-O`).

## Testing & TDD Protocol

- **Tests FIRST, implementation after.** Tests = specification.
- **This applies to bug fixes too.** User-reported defects require a failing test reproducing the bug BEFORE any production code change. See `tdd-implementation.md` §Bug-Fix TDD Protocol and emerging standard **G19**.
- **NEVER modify tests to make them pass.** Fix the implementation.
- Run `pytest` / `vitest` after EVERY code change.
- Coverage targets (advisory): core 80–90%, infra/api/mcp 70%, UI 50–60%.
- See `.agent/docs/testing-strategy.md` for test pyramid and fixtures.

> [!CAUTION]
> **Never use `browser_subagent` for GUI verification.** Zorivest is an Electron app — the browser tool cannot launch or interact with it. All GUI verification must go through Playwright E2E tests (`ui/tests/e2e/`). If a GUI fix needs verification, **write an E2E test** that asserts the correct behavior. See `/e2e-testing` workflow and `.agent/skills/e2e-testing/SKILL.md`.

### FIC-Based TDD Workflow (Mandatory)

> FIC = **Feature Intent Contract** — the acceptance-criteria document written before any code.

When implementing a Manageable Execution Unit (MEU):

1. **Read** the build plan spec section for this MEU and the local canonical docs it references (in `docs/build-plan/`, indexes, ADRs, reflections if applicable)
2. **Write source-backed FIC** — Feature Intent Contract with acceptance criteria (AC-1, AC-2, ...) before any code. Each AC must be labeled `Spec`, `Local Canon`, `Research-backed`, or `Human-approved`.
3. **Write ALL tests FIRST** — every AC becomes at least one test assertion
4. **Run tests** — confirm they FAIL (Red phase). **Save failure output for FAIL_TO_PASS evidence.**
5. **Implement** — write just enough code to make tests pass (Green phase)
6. **Refactor** — clean up while keeping tests green
7. **Run checks**: `pytest -x --tb=short -m "unit"`, `pyright`, `ruff check`
8. **Create handoff** at `.agent/context/handoffs/{YYYY-MM-DD}-{project-slug}-handoff.md`

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
> **Context window checkpoint**: If context window exceeds ~50% capacity (~500k tokens on a 1M window), save state to `pomera_notes`, complete the current MEU's handoff, and notify human with remaining work. This is a planned checkpoint, not early termination. The 50% threshold guards against "context rot" — accuracy degradation observed in frontier models operating above 50% context fill.
>
> **Post-checkpoint continuity:** When resuming from a context checkpoint or truncation, re-read `task.md` BEFORE taking any action. If unchecked `[ ]` items remain, you are mid-workflow — do NOT stop after resolving the first issue. Continue executing the task table sequentially until blocked or complete. "All tests green" is a milestone, not a stopping point.

> Invoke `.agent/skills/completion-preflight/SKILL.md` before any stop, summary, or "implementation complete" report. This is the procedural enforcement of the re-read gate. After context truncation, invoke the skill's §Post-Truncation Recovery Sequence BEFORE addressing any checkpoint issue.

### Context Compression Rules

All handoff artifacts, review artifacts, and evidence bundles must follow the compression rules in [`.agent/docs/context-compression.md`](file:///p:/zorivest/.agent/docs/context-compression.md):

1. **Test Output Compression** — Only output failing test names, assertion messages, and relevant stack frames. Summarize passing tests as `{N} passed`. Never include full verbose output of passing tests.
2. **Delta-Only Code Sections** — Use unified diff blocks (` ```diff `) instead of full file contents in Changed Files sections. Do not inline full source code.
3. **Cache Boundary** — Do not place dynamic content (timestamps, test results, quality gate numbers) above the `<!-- CACHE BOUNDARY -->` marker in handoff templates.
4. **Verbosity Tiers** — Respect the `verbosity` field in handoff YAML and `requested_verbosity` in review YAML. Default is `standard` (~2,000 tokens). Note: the Opus 4.7 tokenizer may inflate this to ~2,400–2,700 tokens — accept inflation or re-tune.
5. **Tool-result clearing** — Prefer JIT retrieval (re-read files when needed) over keeping large tool results in context. Clear tool outputs that won't be referenced again.

## Pre-Handoff Self-Review (Mandatory)

> Before any completion claim or handoff submission, adopt the reviewer mindset. This protocol was distilled from analysis of 7 critical review handoffs (37+ passes) where 10 recurring patterns caused 4-11 passes per project.

1. For each AC, verify the claim against actual file state (quote `file:line`, not memory).
2. Re-run all validation commands and compare counts to what the handoff says.
3. If you fixed one instance of a bug category, `rg` for all instances of the same category.
4. If you changed architecture, `rg` canonical docs for the old pattern.
5. Never say "implementation complete" if residual risk acknowledges known gaps.
6. Stubs must honor behavioral contracts, not just compile.
7. State the exact verification command you ran. For failing or ambiguous output, paste the last 20 lines. For passing suites, summarize as `{N} passed` per §Context Compression Rules. "I ran the tests" without output is not acceptable — produce actual evidence.
8. Before asserting a file exists or a test passes, programmatically verify it. Do not defend claims from memory when contradicted by tool output.
9. Follow the full protocol in `.agent/skills/pre-handoff-review/SKILL.md`.

## Dual-Agent Workflow

| Aspect | Decision |
|---|---|
| **Implementor model** | **Claude Opus 4.7** — primary executor for PLANNING and EXECUTION; performs implementor self-verification and pre-handoff checks in VERIFICATION mode |
| **Reviewer model** | **GPT-5.5** (default) — performs independent validation in VERIFICATION mode; escalate to **GPT-5.5-Pro** for adversarial review of security-sensitive changes. Baseline floor = GPT-5.4 — do not downgrade below it. |
| **Reviewer capability** | Run commands, execute tests, check builds, create handoff docs with test improvements |
| **Validation priority** | 1. Contract tests pass/fail → 2. Security posture → 3. Adversarial edge cases → 4. Code style consistency → 5. Documentation accuracy |

> The reviewer (GPT-5.5 Codex) runs commands and creates handoff docs for findings. It is not limited to prose-only review — it produces executable evidence.

### Cross-Vendor Handoff Protocol

When handing off from implementor (Opus 4.7) to reviewer (GPT-5.5), the handoff payload must include:
1. **Changed files** — list of absolute paths with line-level diff summaries
2. **FIC reference** — the acceptance criteria being validated
3. **Test results** — compressed output (passing count + any failures)
4. **Structured verdict request** — reviewer returns findings using the hybrid YAML+freeform format defined in the `/meu-handoff` and `/validation-review` workflows

> Cross-vendor diversity is the point of dual-agent review — the implementor and reviewer have different training distributions, catching different failure modes.

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

## Windows Shell (PowerShell)

> See **§PRIORITY 0** above for the authoritative redirect-to-file pattern (`*>`) and per-tool command table. The P0 block is the single source of truth for all terminal execution rules.

> [!IMPORTANT]
> **Never pipe long-running commands through filters in PowerShell.** Piping `vitest`, `pytest`, `npm run`, or any process that exits after producing output into `| Select-String`, `| findstr`, or `| Where-Object` causes the pipeline to hang indefinitely — the outer process keeps stdin open waiting for more data even after the child process exits.

**Also avoid:**
- `npm run dev` exit code 1 — this is always expected when `concurrently` terminates (Electron window closes), not a build failure.

## Commits

- **Never auto-commit.** Only `git commit` or `git push` when (a) the user explicitly directs it, or (b) it is a defined step in the approved plan/task. Human always reviews and approves.
- Conventional commits: `feat:`, `fix:`, `refactor:`, `test:`, `docs:`
- **Git skill:** Read `.agent/skills/git-workflow/SKILL.md` (§Commit Policy + §The One Rule) before any git operations.
  - SSH commit signing is configured — all commits are auto-signed, no GPG prompts.
  - **Always** use `git commit -m "message"` — never bare `git commit` (hangs on editor).
  - **Never** use interactive git commands (`git rebase -i`, `git commit --amend` without `--no-edit`).

## Artifact Naming Convention

> [!IMPORTANT]
> **Date-based naming (going forward).** All new handoffs and reflections use date-based naming. Legacy files (001–125) with sequence prefixes remain untouched. Do NOT use sequence numbers on new artifacts.

### Handoffs

```
{YYYY-MM-DD}-{project-slug}-handoff.md
```

- **Path**: `.agent/context/handoffs/`
- **Template**: `.agent/context/handoffs/TEMPLATE.md`
- **Same-day collision**: append MEU range suffix (e.g., `-ph4-ph7-handoff.md`) or letter (`-a`, `-b`)
- **Review files**: `{YYYY-MM-DD}-{project-slug}-plan-critical-review.md` or `-implementation-critical-review.md`

### Reflections

```
{YYYY-MM-DD}-{project-slug}-reflection.md
```

- **Path**: `docs/execution/reflections/`
- **Template**: `docs/execution/reflections/TEMPLATE.md`

### Template-First Rule (Mandatory)

> [!CAUTION]
> **Before creating ANY handoff, reflection, or review file, `view_file` its canonical template.** Do NOT write artifacts from memory. This is not optional.

Required `view_file` calls before artifact creation:

- **Handoff** → `view_file: .agent/context/handoffs/TEMPLATE.md`
- **Reflection** → `view_file: docs/execution/reflections/TEMPLATE.md`
- **Plan review** → `view_file: .agent/context/handoffs/REVIEW-TEMPLATE.md`
- **Implementation review** → `view_file: .agent/context/handoffs/REVIEW-TEMPLATE.md`

If you skip the template read, `completion-preflight` will catch the structural non-compliance and force a rewrite. Read it first to avoid rework.

### Rationale (Research-backed)

Date-based naming is preferred for review artifacts because: (1) temporal context is the primary metadata for reviewers, (2) it eliminates global state dependency that causes naming collisions across agents/sessions, (3) the project slug already disambiguates same-day files. Sequential numbering adds no semantic value when the slug carries the ordering signal.

## Skills

| Skill | Path | Purpose |
|-------|------|---------|
| Backend Startup | `.agent/skills/backend-startup/SKILL.md` | Canonical port (8765), env vars (`ZORIVEST_DEV_UNLOCK`), and start commands for local dev. |
| Git Workflow | `.agent/skills/git-workflow/SKILL.md` | Agent-safe git operations with SSH commit signing. Prevents interactive prompt hangs. |
| Codebase Quality Gate | `.agent/skills/quality-gate/SKILL.md` | Validation pipeline: type checks, linting, tests, anti-placeholder scans, evidence checks. Supports phase-level and MEU-scoped runs. |
| Pre-Handoff Review | `.agent/skills/pre-handoff-review/SKILL.md` | Self-review protocol addressing 10 recurring patterns from critical review analysis. Reduces average review passes from 4-11 to 3-5. |
| Terminal Pre-Flight | `.agent/skills/terminal-preflight/SKILL.md` | Mandatory pre-flight checklist for terminal commands. Enforces the redirect-to-file pattern to prevent PowerShell buffer saturation and session hangs. |
| Completion Pre-Flight | `.agent/skills/completion-preflight/SKILL.md` | Mandatory pre-flight checklist before stop/report events. Enforces task.md re-read gate and post-truncation recovery sequence to prevent premature stop. |

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
- **Emerging standards** → `.agent/docs/emerging-standards.md` — living checklist of MCP/GUI/API standards discovered during development. **Read before planning any MCP or GUI MEU.**
- Role specs → `.agent/roles/`
- Handoff template → `.agent/context/handoffs/TEMPLATE.md`
- Current focus → `.agent/context/current-focus.md`
- Known issues → `.agent/context/known-issues.md`
- Full specification → `docs/BUILD_PLAN.md`

## Instruction Coverage Reflection

<!-- instruction_coverage_reflection: meta-prompt v1 -->
<!-- Placement: EOF recency zone (Liu et al.; Anthropic "queries at end" guidance) -->

At the end of every session, before yielding control, emit a single
fenced YAML block matching `.agent/schemas/reflection.v1.yaml`.

Rules:
- Mark a section `cited: true` only if you actually consulted that
  section's text to make a decision this session.
- Set `influence` honestly: 0 if you did not consider it, 1 if you
  read it but it did not change your output, 2 if it shaped output
  phrasing or structure, 3 if it determined a yes/no decision.
- Listing more than 5 entries in `decisive_rules` is a violation.
- Free-form `note` field is at most one sentence. Do not add fields
  not in the schema.
- Do not flatter the instruction set. If a section was useless,
  set influence: 0. If a rule was wrong, log it under `conflicts`.

Output exactly one ```yaml ... ``` block in the `## Instruction Coverage` section.
No prose around the YAML block itself. The reflection file MUST still follow
the full template structure from `docs/execution/reflections/TEMPLATE.md` —
the YAML block is section 7 of 7, not the entire file.
