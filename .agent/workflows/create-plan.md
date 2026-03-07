---
description: Reason about what to build next — read handoffs, check build-plan, group related MEUs into a coherent project, then generate implementation plan.
---

# Create Plan Workflow

Use this workflow to start a new build session. Instead of reading a pre-written prompt, the agent discovers what's done, identifies what's next, and uses reasoning to scope a coherent project of related MEUs.

// turbo-all

## Prerequisites

Read these files in order:

1. `SOUL.md`
2. `GEMINI.md`
3. `AGENTS.md`
4. `.agent/context/current-focus.md`
5. `.agent/context/known-issues.md`

## Steps

### 1. Discover What's Completed

Scan these sources to build a picture of current progress:

```
# Check MEU statuses
cat .agent/context/meu-registry.md

# List completed handoffs (sequence numbers show progress)
ls .agent/context/handoffs/ | Sort-Object

# Read the most recent reflection (sort by write time, not name)
Get-ChildItem docs/execution/reflections/*.md | Sort-Object LastWriteTime -Descending | Select-Object -First 1
```

From the handoffs and registry, determine:
- Which MEUs are ✅ approved
- Which are 🟡 ready_for_review or 🔴 changes_required
- Which are ⬜ pending

If the most recent reflection has "Next Session Design Rules," apply those to today's planning.

### 2. Identify What's Next

Read the build plan files for the next pending work:

```
# Read the build priority matrix for overall ordering
cat docs/build-plan/build-priority-matrix.md

# Read the specific build-plan file for the next pending phase/section
cat docs/build-plan/{NN}-{phase}.md
```

Identify the set of pending MEUs that are unblocked (all dependencies satisfied by approved MEUs).

### 2A. Run a Spec Sufficiency Gate

Before grouping MEUs, verify whether the build plan is specific enough to support a complete implementation without guesswork.

Read, as applicable:

- The target build-plan file and its cited companion docs (`domain-model-reference.md`, `build-priority-matrix.md`, input/output indexes, testing strategy, architecture, ADRs)
- The most recent approved handoff/reflection if it establishes carry-forward rules for this area
- Known issues or previous review findings that affect the same surface

For each MEU, build a sufficiency table:

| Behavior / Contract | Source Type | Source | Resolved? | Notes |
|---|---|---|---|---|

Allowed source types:

- `Spec` — explicit in the target build-plan section
- `Local Canon` — explicit in another canonical local doc
- `Research-backed` — resolved via targeted web research against official docs, standards, or other primary/current sources
- `Human-approved` — resolved by explicit user decision

Rules:

- `Best practice` alone is never sufficient. Cite the exact file or URL.
- Do not create FIC acceptance criteria from unsourced intuition.
- Do not silently narrow the contract because the build plan is thin.
- If local docs are insufficient, run `.agent/workflows/pre-build-research.md` or equivalent targeted web research before Step 3.
- Ask the human only when materially different product behaviors remain plausible, sources conflict, or the decision is irreversible/high-risk.

### 3. Reason About Project Scope

Use sequential thinking to group the next set of pending MEUs into a coherent **project**. Apply these principles:

- **Dependency order**: foundation first, then what depends on it
- **Logical continuity**: MEUs that share context, types, or test fixtures belong together
- **Foundation to roof**: build upward continuously, don't jump across unrelated areas
- **Right-sizing**: not too small (wasted context setup) and not too large (context degradation)
- **Build-plan continuity**: stay within the same build-plan file/phase when possible
- **Completeness first**: prefer the full documented contract across canonical docs; do not introduce artificial narrowing unless the spec explicitly does so

Output a clear project scope:
- Project slug (e.g., `domain-entities-ports`)
- MEUs included, in execution order
- Build-plan sections covered
- In-scope / out-of-scope boundary

### 4. Generate Plan

Enter PLANNING mode and generate `implementation-plan.md` and `task.md` **directly in the project execution folder**:

```powershell
$projectSlug = "{YYYY-MM-DD}-{project-slug}"
New-Item -ItemType Directory -Force -Path "docs\execution\plans\$projectSlug" | Out-Null
```

Write both files to `docs/execution/plans/{YYYY-MM-DD}-{project-slug}/`:
- `implementation-plan.md`
- `task.md`

> [!IMPORTANT]
> **The project folder is the single source of truth.** All edits and revisions happen here. The Antigravity brain folder (`~/.gemini/antigravity/brain/{conversation-id}/`) may receive a copy for UI rendering, but the project folder is what Codex validates against and what gets version-controlled.

The plan must include:
- A task table with: task, owner_role, deliverable, validation, status
- A spec-sufficiency section per MEU with source-backed resolutions for any under-specified behavior
- Feature Intent Contract (FIC) per MEU with acceptance criteria annotated as `Spec`, `Local Canon`, `Research-backed`, or `Human-approved`
- Exact file paths to create or modify
- Exact validation commands
- Explicit stop conditions
- Research URLs or document paths for any behavior resolved outside the target build-plan section
- Handoff file paths using the naming convention: `{SEQ}-{YYYY-MM-DD}-{slug}-bp{NN}s{X.Y}.md`

No plan may defer required behavior merely because the build plan is thin. The planner must either resolve the behavior from sources or stop on an explicit human decision gate before execution.

### 5. Present for Approval

Present the plan to the human via `notify_user` with `BlockedOnUser: true`.

> [!CAUTION]
> **The plan files MUST exist in the project folder before Codex review.** Codex validates against `docs/execution/plans/{YYYY-MM-DD}-{project-slug}/` — if the files are missing, validation will fail. Since Step 4 writes directly to this folder, no extra copy step is needed.

### 6. Execute

Switch to EXECUTION mode. Follow:
- `.agent/workflows/tdd-implementation.md` for each MEU's TDD cycle
- `.agent/workflows/meu-handoff.md` for handoff creation per MEU
- `.agent/workflows/execution-session.md` §4–7 for execution rules, reflection, and session state

## Handoff Naming Convention

Handoffs use sequenced names that encode build-plan traceability:

```
{SEQ}-{YYYY-MM-DD}-{slug}-bp{NN}s{X.Y}.md
```

| Part | Meaning | Example |
|------|---------|---------|
| `{SEQ}` | 3-digit global sequence | `001` |
| `{YYYY-MM-DD}` | Date completed | `2026-03-06` |
| `{slug}` | Descriptive slug | `calculator` |
| `bp{NN}s{X.Y}` | Build-plan file + section | `bp01s1.3` |

For a single MEU spanning multiple build-plan sections, join with `+`:
- `bp01s1.4+1.5` = build-plan 01, sections 1.4 and 1.5

**Sequence bootstrap:** If no sequenced handoffs exist yet (legacy files use `YYYY-MM-DD-` prefix), start at `001`.
Otherwise, increment from the highest `{SEQ}` found in `.agent/context/handoffs/`.

Examples:
```
001-2026-03-06-calculator-bp01s1.3.md
002-2026-03-07-enums-bp01s1.2.md
003-2026-03-08-entities-bp01s1.4+1.5.md  ← single MEU covering sections 1.4 and 1.5
```

> **One handoff per MEU.** Each MEU in a project gets its own sequenced handoff. A multi-MEU project produces multiple handoff files (e.g., 003, 004, 005).

## Exit Criteria

- [ ] Plan written to `docs/execution/plans/{date}-{project-slug}/`
- [ ] All MEUs in the project executed via TDD
- [ ] One handoff per MEU created with sequenced naming
- [ ] MEU registry updated per MEU
- [ ] Reflection file created
- [ ] Metrics table updated
- [ ] Session state saved to pomera_notes
- [ ] Proposed commit messages presented to human
