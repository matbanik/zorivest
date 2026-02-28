---
description: TDD-first implementation workflow for Opus 4.6 — write tests, implement, handoff to Codex for validation.
---

# TDD Implementation Workflow (Opus Agent)

Use this workflow when implementing a Manageable Execution Unit (MEU). Opus is the **implementation agent** — writes tests first, implements to pass, and creates the handoff artifact for Codex validation.

## Prerequisites

- Read `CLAUDE.md` for project config
- Read `SOUL.md` for identity
- Read `.agent/context/meu-registry.md` for MEU scope
- Read `.agent/context/current-focus.md` for active phase

## Steps

### 1. Scope Lock

// turbo
Read the MEU definition from `.agent/context/meu-registry.md`. Read the corresponding build plan section. Do NOT expand scope beyond the MEU boundary.

### 2. Feature Intent Contract (FIC)

Write FIC inline in your session notes:
- **Intent statement**: What must be true when this MEU ships
- **Acceptance criteria**: Numbered, testable conditions (AC-1, AC-2, ...)
- **Negative cases**: What must NOT happen
- **Test mapping**: Which test file/function proves each AC

### 3. Red Phase — Write Failing Tests

Write ALL tests FIRST in the appropriate `tests/unit/` file. Every AC must have at least one test. Include:
- Happy path tests
- Edge case tests (zero, negative, empty, overflow)
- Error condition tests

// turbo
Run tests to confirm they FAIL:
```bash
pytest tests/unit/test_{module}.py -x --tb=short -v
```

Save the failure output — you will include it in the handoff FAIL_TO_PASS table.

### 4. Green Phase — Implement

> ⚠️ **Test Immutability**: Once tests are written in Red phase, do NOT modify test assertions or expected values. If a test expectation is wrong, fix the *implementation*, not the *test*. Only test setup/fixture changes are allowed.

Write the minimum code to make all tests pass. Follow the build plan spec exactly — use the same function signatures, class names, and field names.

// turbo
Run tests to confirm they PASS:
```bash
pytest tests/unit/test_{module}.py -x --tb=short -v
```

### 5. Quality Checks

// turbo
Run type checking and linting:
```bash
pyright packages/core/src/
ruff check packages/core/src/
```

### 6. Full Test Suite

// turbo
Run the complete test suite to check for regressions:
```bash
pytest -x --tb=short -m "unit"
```

### 7. Create Handoff Artifact

Create the handoff file at `.agent/context/handoffs/{YYYY-MM-DD}-meu-{N}-{slug}.md` using the format from `.agent/workflows/meu-handoff.md`.

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

If stuck for more than 2 iterations on a failing test:
1. Document what was attempted
2. Mark MEU status as `blocked` in handoff
3. List specific blocking issue
4. Do NOT implement a workaround that violates the spec
