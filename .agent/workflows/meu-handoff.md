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

> **Start from** [`.agent/context/handoffs/TEMPLATE.md`](file:///p:/zorivest/.agent/context/handoffs/TEMPLATE.md) (v2.0)
>
> Copy the template, fill all placeholder fields, and ensure:
> - YAML frontmatter `seq`, `date`, `project`, `meu`, `status`, `action_required` are populated
> - `action_required` is set to `VALIDATE_AND_APPROVE` for new handoffs
> - AC table has source labels for every criterion
> - Evidence section has FAIL_TO_PASS table and Commands Executed table
> - Codex Validation Report section is left blank for the reviewer

## Live Runtime Probe Requirements

> **Context**: In 5/7 reviewed projects, mock-based unit tests masked broken runtime behavior, causing 3-5 extra review passes per project. The rest-api-foundation project needed 11 passes largely because stubs silently violated contracts.

For any MEU that touches routes, handlers, or service wiring, the handoff MUST include live runtime evidence:

### Mandatory Probe Protocol

1. **Integration test with real stack**: Create at least one `create_app()` + `TestClient(raise_server_exceptions=False)` test that exercises the full stack _without_ dependency overrides.
2. **Minimum probe sequence** (for API work):
   - Create → Get → List consistency (entity actually persists)
   - Duplicate rejection (both dedup keys)
   - Missing-entity error mapping on all write paths
   - Filter/pagination with multiple entities
   - Owner-scoped listing (when applicable)
3. **State propagation check**: If the MEU changes auth/unlock/mode state, verify the state change propagates to all dependent guards (e.g., `app.state.db_unlocked` after unlock).

### Stub Quality Gate

Stubs used during development MUST honor the behavioral interface:

| Stub Method | Required Behavior |
|---|---|
| `save()` | Actually persists to in-memory store |
| `get()` | Returns persisted entity or `None` |
| `exists()` | Returns correct boolean based on store |
| `list_filtered()` | Actually filters by provided parameters |
| `get_for_owner()` | Filters by `owner_type` and `owner_id` |

**Prohibited patterns**:
- `__getattr__` that silently returns values (`None`, empty collections, no-op callables) for undefined methods
- `save()` that discards writes (creates false 201→404 inconsistency)
- `exists()` that always returns `False` (bypasses dedup checks)

**Permitted**: `__getattr__` that raises `AttributeError` or `NotImplementedError` with the method name is allowed (explicit-error form is safer than missing methods).

### Fix Generalization Scope

> This section is the canonical source for fix-generalization boundaries. Other documents reference this section.

Before applying a fix to "similar locations," classify each candidate:
- **Same contract** → must fix
- **Spec-divergent contract** → allowed to differ (cite spec/ADR)
- **Unknown** → stop and route to planning, do not generalize

**Search boundary**: same package + explicitly listed siblings in `meu-registry.md`. Cross-package matches → log as follow-up item, do NOT auto-fix.

**Evidence in handoff**: "Checked N locations in {scope}. Fixed M. Skipped K (spec-divergent: {cite}). Verified 0 remaining unaddressed."

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
