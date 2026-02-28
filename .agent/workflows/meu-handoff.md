---
description: Handoff protocol between Opus (implementation) and Codex (validation) agents for MEU-scoped work.
---

# MEU Handoff Protocol

This document defines the handoff artifact format for passing work between agents. A handoff artifact must be **self-contained** — the receiving agent has no access to the sending agent's reasoning, context, or conversation history.

> **Target size**: 2,000–5,000 tokens. Reference files by path. Never inline full source code.

## Handoff Artifact Location

```
.agent/context/handoffs/{YYYY-MM-DD}-meu-{N}-{slug}.md
```

Example: `.agent/context/handoffs/2026-03-01-meu-1-calculator.md`

## Template

```markdown
---
meu: {N}
slug: {slug}
phase: {1/1A/2/2A/3/...}
priority: {P0/P1/P2/P3}
status: ready_for_review
agent: opus-4.6
iteration: 1
files_changed: {count}
tests_added: {count}
tests_passing: {count}
---

# MEU-{N}: {Title}

## Scope

{One paragraph: what this MEU covers, what build plan section it implements}

Build plan reference: [link to docs/build-plan/XX-section.md]

## Feature Intent Contract

### Intent Statement
{What must be true for users when this MEU ships}

### Acceptance Criteria
- AC-1: {concrete, testable condition}
- AC-2: {concrete, testable condition}
- ...

### Negative Cases
- Must NOT: {what must not happen}
- Must NOT: {what must not happen}

### Test Mapping
| Criterion | Test File | Test Function |
|-----------|-----------|---------------|
| AC-1 | tests/unit/test_xxx.py | test_yyy |
| AC-2 | tests/unit/test_xxx.py | test_zzz |

## Changed Files

| File | Action | Description |
|------|--------|-------------|
| `path/to/file.py` | Created / Modified | {what changed} |

## Commands Executed

| Command | Result | Notes |
|---------|--------|-------|
| `pytest tests/unit/test_xxx.py -x -v` | PASS (N tests) | All green |
| `pyright packages/core/src/` | PASS | No errors |
| `ruff check packages/core/src/` | PASS | No warnings |

## Design Decisions & Known Risks

- **Decision**: {what you chose} — **Reasoning**: {why, in 1-2 sentences}
- **Assumption**: {any assumption made during implementation}
- **Risk**: {any edge cases not fully covered}

## FAIL_TO_PASS Evidence

| Test | Before | After |
|------|--------|-------|
| `test_xxx` | FAIL (not implemented) | PASS |
| `test_yyy` | FAIL (not implemented) | PASS |

---
## Codex Validation Report
{Left blank — Codex fills this section during validation-review workflow}
```

## Dual Storage

Every handoff is stored in two places for redundancy:

1. **File**: `.agent/context/handoffs/{date}-meu-{N}-{slug}.md`
2. **pomera_notes**: `Memory/Session/Zorivest-MEU-{N}-{date}`

The file is the primary artifact. pomera_notes is the backup for cross-session search.

## Status Transitions

```
ready_for_review  →  approved          (Codex validates, all checks pass)
ready_for_review  →  changes_required  (Codex finds issues)
changes_required  →  ready_for_review  (Opus fixes and resubmits)
blocked           →  ready_for_review  (Blocker resolved)
approved          →  (terminal)        (MEU complete, mark in meu-registry)
```

## Max Revision Cycles

Maximum 2 revision cycles (Opus→Codex→Opus→Codex) per MEU. After 2 cycles, escalate to human orchestrator with:
- Summary of disagreement
- Both agents' positions
- Recommended resolution
