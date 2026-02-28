---
description: Validation and adversarial review workflow for GPT 5.3 Codex — verify tests, review code, generate evidence bundle.
---

# Validation Review Workflow (Codex Agent)

Use this workflow when validating a completed MEU. Codex is the **validation agent** — runs full test suite, performs adversarial review, and issues a verdict.

## Prerequisites

- Read the MEU handoff artifact at `.agent/context/handoffs/{date}-meu-{N}-{slug}.md`
- Read ALL changed files listed in the handoff (full content, not just diffs)
- Read `docs/build-plan/testing-strategy.md` for test standards
- Read `.agent/roles/reviewer.md` for adversarial checklist

## Steps

### 1. Handoff Intake

Read the handoff artifact. Verify it contains:
- [ ] MEU identifier and scope
- [ ] FIC with acceptance criteria
- [ ] Changed files list
- [ ] Test files and assertion counts
- [ ] Commands executed with output
- [ ] Status is `ready_for_review` (not `blocked`)

If handoff is incomplete or status is `blocked`, stop and report.

### 2. Run Full Test Suite

// turbo
Run the complete test suite (not just new tests):
```bash
pytest -x --tb=long -v
```

// turbo
Run type checking:
```bash
pyright packages/core/src/
```

// turbo
Run linting:
```bash
ruff check packages/core/src/
```

Record all output.

### 3. Adversarial Verification Checklist

> ⚠️ You are a **REVIEWER**, not a test author. Do NOT generate new test files or rewrite existing tests. Only report findings with `file:line` references.

For each item, record PASS or FAIL with evidence:

| # | Check | What To Look For |
|---|---|---|
| AV-1 | **Failing-then-passing proof** | A test existed (or was written) that FAILED before the change and PASSES after. If no such test exists, the "fix" is unproven. |
| AV-2 | **No bypass hacks** | No monkeypatching of test internals, no forced early exits (`return` before assertions), no mocked-out assertion functions. |
| AV-3 | **Changed paths exercised by assertions** | Changed code paths are not just executed — they are checked by explicit `assert` / `expect` statements. Code coverage alone is insufficient. |
| AV-4 | **No skipped/xfail masking** | Tests exist but are not blanket-marked `@pytest.mark.skip`, `xfail`, or `it.skip`. Any skip must have a documented reason. |
| AV-5 | **No unresolved placeholders** | No `TODO`, `FIXME`, `NotImplementedError`, `pass  # placeholder`, or skeleton stubs remain. |

### 4. Banned Pattern Scan

// turbo
Search for banned patterns in all changed files:
```bash
rg "TODO|FIXME|NotImplementedError|pass\s+#\s*placeholder" packages/ tests/
```

### 5. FIC Acceptance Criteria Verification

For each acceptance criterion in the FIC:
- Identify the test(s) that prove it
- Verify the test(s) contain explicit assertions (not just execution)
- Confirm all criteria are covered (no gaps)

### 6. Architecture Review

- [ ] No inner layer imports outer layer (Domain doesn't import Infrastructure)
- [ ] Function/class names match build plan spec exactly
- [ ] Enum values match spec exactly
- [ ] Error handling is explicit (no bare except, no swallowed exceptions)
- [ ] No unused imports or dead code

### 7. Generate Evidence Bundle

Create or append to the handoff artifact:

```markdown
## Codex Validation Report

**Date**: {YYYY-MM-DD}
**MEU**: {N} — {description}
**Verdict**: approved / changes_required

### Test Results
| Command | Result |
|---------|--------|
| `pytest -x --tb=long -v` | PASS (N tests) / FAIL (details) |
| `pyright` | PASS / FAIL (details) |
| `ruff check` | PASS / FAIL (details) |

### Adversarial Checklist
| Check | Result | Evidence |
|-------|--------|----------|
| AV-1 | PASS/FAIL | ... |
| AV-2 | PASS/FAIL | ... |
| AV-3 | PASS/FAIL | ... |
| AV-4 | PASS/FAIL | ... |
| AV-5 | PASS/FAIL | ... |

### Banned Patterns
- rg output: {results or "clean"}

### FIC Coverage
| Criterion | Test(s) | Verified |
|-----------|---------|----------|
| AC-1 | test_xxx | ✅/❌ |

### Findings (if any)
1. **[SEVERITY]** {file}:{line} — {description}

### Verdict Rationale
{Why approved or what must change}

### Verdict Confidence
- **Confidence**: HIGH / MEDIUM / LOW
- **Justification**: {1-2 sentences explaining WHY you believe this verdict is correct}
- If MEDIUM or LOW, flag for human review even if verdict is "approved"
```

## Verdict Definitions

- **approved**: All checks pass, all AV items pass, all FIC criteria verified. MEU is complete.
- **changes_required**: List specific items that must be fixed. Opus re-enters the TDD workflow to address findings, then re-submits for review.

## Escalation

If more than 2 review cycles occur for the same MEU without resolution, escalate to human orchestrator with a summary of the disagreement.
