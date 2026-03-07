---
description: Handoff protocol between Opus (implementation) and Codex (validation) agents for MEU-scoped work.
---

# MEU Handoff Protocol

This document defines the handoff artifact format for passing work between agents. A handoff artifact must be **self-contained** — the receiving agent has no access to the sending agent's reasoning, context, or conversation history.

> **Target size**: 2,000–5,000 tokens per handoff. Reference files by path. Never inline full source code.
>
> **Multi-MEU sessions**: A project session produces one handoff per MEU. Each handoff is validated independently by Codex.
>
> **Project correlation rule**: In multi-MEU sessions, the correlated `docs/execution/plans/{YYYY-MM-DD}-{project-slug}/implementation-plan.md` and `task.md` must enumerate the full handoff set for the project. `/critical-review-feedback` uses those artifacts to expand review scope from the seed handoff to all sibling handoffs produced by the plan.

## Handoff Artifact Location

```
`.agent/context/handoffs/{SEQ}-{YYYY-MM-DD}-{slug}-bp{NN}s{X.Y}.md`

Where:
- `{SEQ}` = 3-digit global sequence (check highest existing in handoffs folder)
- `{YYYY-MM-DD}` = date completed
- `{slug}` = descriptive slug
- `bp{NN}s{X.Y}` = build-plan file number + section (e.g., `bp01s1.3`)
```

Example: `.agent/context/handoffs/001-2026-03-06-calculator-bp01s1.3.md`

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
- AC-1 (Source: Spec): {concrete, testable condition}
- AC-2 (Source: Local Canon / Research-backed / Human-approved): {concrete, testable condition}
- ...

### Negative Cases
- Must NOT: {what must not happen}
- Must NOT: {what must not happen}

### Test Mapping
| Criterion | Test File | Test Function |
|-----------|-----------|---------------|
| AC-1 | tests/unit/test_xxx.py | test_yyy |
| AC-2 | tests/unit/test_xxx.py | test_zzz |

> Any criterion that is not explicit in the target build-plan section must cite the exact local file path or web source used to resolve it. `Best practice` alone is not acceptable.

## Design Decisions & Known Risks

- **Decision**: {what you chose} — **Reasoning**: {why, in 1-2 sentences} — **ADR**: {ADR-NNNN if created, or "inline" if minor}
- **Source Basis**: {exact file path(s) and/or URL(s) that justify non-explicit behavior}
- **Assumption**: {only if still unresolved and the handoff status is `blocked` or `changes_required`}
- **Risk**: {any edge cases not fully covered}

> For decisions affecting cross-package boundaries or rejecting plausible alternatives, create a formal ADR at `docs/decisions/`. Reference it here by number.

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

1. **File**: `.agent/context/handoffs/{SEQ}-{date}-{slug}-bp{NN}s{X.Y}.md`
2. **pomera_notes**: `Memory/Session/Zorivest-{project-slug}-{date}`

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
