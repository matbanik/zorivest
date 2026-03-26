# Handoff 003 — Workflow Amendments

**Project:** agents-terminal-optimization-infra
**MEU:** C — Workflow Amendments
**Date:** 2026-03-25
**Author:** Opus 4.6

## Changes

### [MODIFY] .agent/workflows/execution-session.md

Two amendments added:

1. **Amendment 1: Terminal Pre-Flight callout** (L70-72)
   - Inserted `> ⚠️ **P0 Terminal Pre-Flight**` block before the first shell step in §4 EXECUTION phase
   - Directs agent to invoke terminal-preflight SKILL and confirm 4 checklist items

2. **Amendment 2: Pre-Completion Sweep** (L116-120)
   - Inserted as item 7 in §4b Pre-Handoff Self-Review Protocol
   - 3 sub-steps: rg count-bearing strings, Test-Path evidence files, run pre-handoff-review SKILL
   - Catches stale evidence counts before handoff submission

Line count: 213 → 223 (+10 lines)

### [MODIFY] .agent/workflows/tdd-implementation.md

3 P0 REMINDER blocks added before existing test-run commands:

1. **Red phase** (L44-46) — before `pytest tests/unit/test_{module}.py` FAIL step
2. **Green phase** (L66-68) — before `pytest tests/unit/test_{module}.py` PASS step
3. **Full test suite** (L90-92) — before `pytest -x --tb=short -m "unit"` regression step

Each block contains the exact redirect command string for copy-paste. Line count: 120 → 132 (+12 lines)

## Acceptance Criteria Evidence

| # | Criterion | Result |
|---|-----------|--------|
| AC-1 | `rg "P0 Terminal Pre-Flight\|terminal-preflight"` execution-session.md | ✅ L70-71 |
| AC-2 | `rg "Pre-Completion Sweep"` execution-session.md | ✅ L116 |
| AC-3 | `rg -c "P0 REMINDER"` tdd-implementation.md = 3 | ✅ 3 |
| AC-4 | execution-session.md line count ≥ 213 | ✅ 223 |
| AC-5 | tdd-implementation.md line count ≥ 120 | ✅ 132 |

## Proposed Commit Message

```
docs: add P0 terminal pre-flight and pre-completion sweep to workflows

Amend execution-session.md with Terminal Pre-Flight callout (§4) and
Pre-Completion Sweep (§4b item 7). Add P0 REMINDER blocks at all 3
test-run sites in tdd-implementation.md to enforce redirect-to-file
pattern at the exact points where terminal hangs historically occur.

feat: add P0 terminal pre-flight reminders to workflows
fix: prevent terminal buffer saturation during TDD test runs
Part-of: agents-terminal-optimization-infra
```

## Verdict

Ready for Codex review.
