---
description: TDD-first implementation workflow for Opus 4.6 — write tests, implement, handoff to Codex for validation.
---

# TDD Implementation Workflow (Opus Agent)

Use this workflow when implementing a Manageable Execution Unit (MEU). Opus is the **implementation agent** — writes tests first, implements to pass, and creates the handoff artifact for Codex validation.

## Prerequisites

- Read `AGENTS.md` for project config
- Read `.agent/context/meu-registry.md` for MEU scope
- Read `.agent/context/current-focus.md` for active phase
- Read `.agent/docs/emerging-standards.md` — verify applicable standards are covered. If the MEU involves MCP tools or GUI components, the matching standards are mandatory subtasks.

## Steps

### 1. Scope Lock

// turbo
Read the MEU definition from `.agent/context/meu-registry.md`. Read the corresponding build plan section and any canonical local docs it references. Do NOT expand scope beyond the MEU boundary, but do implement the full documented contract.

If the spec is not specific enough to support concrete acceptance criteria without guesswork, stop here and return to PLANNING / `.agent/workflows/pre-build-research.md`. Do not start Red phase on unsourced assumptions.

### 2. Feature Intent Contract (FIC)

Write FIC inline in your session notes:
- **Intent statement**: What must be true when this MEU ships
- **Acceptance criteria**: Numbered, testable conditions (AC-1, AC-2, ...) with a source label for each: `Spec`, `Local Canon`, `Research-backed`, or `Human-approved`
- **Negative cases**: What must NOT happen
- **Boundary contract**: For write-adjacent MEUs, list each input boundary and its schema owner
- **Negative input cases**: Required classes — blank required strings, invalid enums, malformed format fields, non-positive/out-of-range numerics, unexpected/extra fields, create vs update parity
- **Test mapping**: Which test file/function proves each AC

`Best practice` is not a valid acceptance-criterion source unless it is backed by a cited local doc or web source.

### 3. Red Phase — Write Failing Tests

Write ALL tests FIRST in the appropriate `tests/unit/` file. Every AC must have at least one test. Include:
- Happy path tests
- Edge case tests (zero, negative, empty, overflow)
- Error condition tests

For write-adjacent MEUs, the Red phase MUST include negative input tests:
- Blank/empty required string → 422
- Invalid enum value → 422
- Non-positive numeric where positive required → 422
- Unexpected/extra fields → 422 (when `extra="forbid"`)
- Partial update bypassing create invariants → same validation error as create

> Handlers/services may NOT accept raw `dict` or `**kwargs` from external input unless those values have already passed boundary schema validation.

// turbo

> **P0 REMINDER:** Use the redirect-to-file pattern for this command.
> `pytest tests/unit/test_{module}.py -x --tb=short -v *> C:\Temp\zorivest\pytest.txt; Get-Content C:\Temp\zorivest\pytest.txt | Select-Object -Last 40`

Run tests to confirm they FAIL:
```bash
pytest tests/unit/test_{module}.py -x --tb=short -v
```

Save the failure output — you will include it in the handoff FAIL_TO_PASS table.

### 4. Green Phase — Implement

> ⚠️ **Test Immutability**: Once tests are written in Red phase, do NOT modify test assertions or expected values. If a test expectation is wrong, fix the *implementation*, not the *test*. Only test setup/fixture changes are allowed.

> [!CAUTION]
> **Scope Expansion Gate.** If the user requests features outside the approved plan scope during execution (e.g., "also add a delete tool" or "add a refresh button"), PAUSE and ask: "This is outside the current plan. Should I (a) update the plan first, (b) treat this as a separate ad-hoc fix, or (c) defer to a follow-up MEU?" Proceeding without updating plan artifacts causes handoff/review misalignment (ref: emerging-standards.md, 2026-03-19 session F14).

Write the minimum code to make all tests pass. Follow the build plan spec exactly — use the same function signatures, class names, and field names.

Do not invent new product behavior in code. If a gap appears during implementation, route it back to planning/research and update the FIC before continuing.

// turbo

> **P0 REMINDER:** Use the redirect-to-file pattern for this command.
> `pytest tests/unit/test_{module}.py -x --tb=short -v *> C:\Temp\zorivest\pytest.txt; Get-Content C:\Temp\zorivest\pytest.txt | Select-Object -Last 40`

Run tests to confirm they PASS:
```bash
pytest tests/unit/test_{module}.py -x --tb=short -v
```

### 5. Quality Checks

// turbo
Run type checking and linting:
```bash
# Scope to touched packages (expand as phases grow):
# Phase 1+1A: packages/core/src/
# Phase 2+:   packages/core/src/ packages/infrastructure/src/
# Phase 4+:   packages/core/src/ packages/infrastructure/src/ packages/api/src/
# Phase 5+:   add mcp-server/ (tsc --noEmit, vitest, eslint)
pyright packages/core/src/    # ← adjust per active phase
ruff check packages/core/src/ # ← adjust per active phase
```

### 6. Full Test Suite

// turbo

> **P0 REMINDER:** Use the redirect-to-file pattern for this command.
> `pytest -x --tb=short -m "unit" *> C:\Temp\zorivest\pytest.txt; Get-Content C:\Temp\zorivest\pytest.txt | Select-Object -Last 40`

Run the complete test suite to check for regressions:
```bash
pytest -x --tb=short -m "unit"
```

### 7. Create Handoff Artifact

Create the handoff file at `.agent/context/handoffs/{SEQ}-{YYYY-MM-DD}-{slug}-bp{NN}s{X.Y}.md` using the format from `.agent/workflows/meu-handoff.md`.

### 8. Save Session State

Save progress to pomera_notes for cross-session recovery:
```
pomera_notes save
  --title "Memory/Session/Zorivest-MEU-{N}-{YYYY-MM-DD}"
  --input_content "<MEU scope and FIC>"
  --output_content "<files changed, test results, next steps>"
```

## Exit Criteria

1. All tests pass (Green)
2. No banned patterns in deliverables (TODO, FIXME, NotImplementedError)
3. Type checking passes (pyright)
4. Linting passes (ruff)
5. Handoff artifact created with evidence
6. Session state saved to pomera_notes

## Failure Protocol

If stuck for more than 2 iterations on a failing test, or if a spec gap is discovered mid-MEU:
1. Document what was attempted
2. Route the issue back to planning/research for a source-backed resolution
3. Mark MEU status as `blocked` in handoff if the issue still cannot be resolved
4. List the specific blocking issue or unresolved decision
5. Do NOT implement a workaround that violates the spec or silently narrows the contract
