---
description: Reason about what to build next — read handoffs, check build-plan, group related MEUs into a coherent project, then generate implementation plan.
---

# Create Plan Workflow

Use this workflow to start a new build session. Instead of reading a pre-written prompt, the agent discovers what's done, identifies what's next, and uses reasoning to scope a coherent project of related MEUs.

// turbo-all
// NOTE: turbo-all sets SafeToAutoRun=true for non-destructive commands (rg, Get-Content, etc.).
// It does NOT override AGENTS.md §Commits: "Never auto-commit." Git commit/push still requires explicit user direction.

## Prerequisites

Read these files in order:

1. `AGENTS.md`
2. `.agent/context/current-focus.md`
3. `.agent/context/known-issues.md`
4. `.agent/docs/emerging-standards.md` — scan for standards applicable to the MEUs being planned. Add matching standards as explicit subtasks in Step 4.

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

Also inspect `docs/BUILD_PLAN.md` as the build-plan hub/index and determine whether the planned project will require hub-level updates (for example: stale execution-plan references, phase-status notes, moved/renamed plan links, or summary text that would become inaccurate once the project is executed). This check is mandatory during planning; do not leave `docs/BUILD_PLAN.md` maintenance to memory.

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

For any MEU that accepts external input, the sufficiency table must include a **Boundary Inventory Row** per write surface:

| Boundary | Schema Owner | Extra-Field Policy | Invalid-Input Error Code | Create/Update Parity | Source |
|----------|-------------|--------------------|--------------------------|---------------------|--------|

The plan is not approvable until it identifies every external input surface and documents expected rejection behavior for malformed, missing, out-of-range, and unexpected fields.

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
- `implementation-plan.md` — start from [`docs/execution/plans/PLAN-TEMPLATE.md`](file:///p:/zorivest/docs/execution/plans/PLAN-TEMPLATE.md) (v2.0)
- `task.md` — start from [`docs/execution/plans/TASK-TEMPLATE.md`](file:///p:/zorivest/docs/execution/plans/TASK-TEMPLATE.md) (v2.0)

> [!CAUTION]
> **Template Pre-Flight (mandatory before writing):**
> 1. `view_file` → `docs/execution/plans/PLAN-TEMPLATE.md`
> 2. `view_file` → `docs/execution/plans/TASK-TEMPLATE.md`
> 3. Only then write `implementation-plan.md` and `task.md`, using the template structure as the skeleton and filling in project-specific content.

> [!IMPORTANT]
> **The project folder is the single source of truth.** All edits and revisions happen here. The Antigravity brain folder (`~/.gemini/antigravity/brain/{conversation-id}/`) may receive a copy for UI rendering, but the project folder is what Codex validates against and what gets version-controlled.

The plan must include:
- A task table with: task, owner_role, deliverable, validation, status
- A spec-sufficiency section per MEU with source-backed resolutions for any under-specified behavior
- Feature Intent Contract (FIC) per MEU with acceptance criteria annotated as `Spec`, `Local Canon`, `Research-backed`, or `Human-approved`
- An explicit task to review and update `docs/BUILD_PLAN.md` for any hub/index drift caused or revealed by the project. This task must appear in both `implementation-plan.md` and `task.md`, with exact validation commands. If the planner finds no required `docs/BUILD_PLAN.md` change, the task must still exist and say so explicitly (for example: validate that no stale references remain, then mark the task complete with evidence).
- Exact file paths to create or modify
- Exact validation commands
- Explicit stop conditions
- Research URLs or document paths for any behavior resolved outside the target build-plan section
- Handoff file paths using the naming convention: `{YYYY-MM-DD}-{project-slug}-handoff.md`

No plan may defer required behavior merely because the build plan is thin. The planner must either resolve the behavior from sources or stop on an explicit human decision gate before execution.

For `docs/BUILD_PLAN.md` specifically, do not use vague wording like "clean up BUILD_PLAN later" or bury the work in prose. The planner must create a concrete task row with owner, deliverable, validation, and status just like any other project task.

### 5. Present for Approval

Present the plan to the human via `notify_user` with `BlockedOnUser: true`.

> [!CAUTION]
> **The plan files MUST exist in the project folder before Codex review.** Codex validates against `docs/execution/plans/{YYYY-MM-DD}-{project-slug}/` — if the files are missing, validation will fail. Since Step 4 writes directly to this folder, no extra copy step is needed.

### 6. Execute

Switch to EXECUTION mode. Follow:
- `.agent/workflows/tdd-implementation.md` for each MEU's TDD cycle
- `.agent/workflows/meu-handoff.md` for handoff creation per MEU
- `.agent/workflows/execution-session.md` §4–7 for execution rules, reflection, and session state

> [!CAUTION]
> **Anti-premature-stop rule.** Do NOT call `notify_user` during Step 6 unless blocked by an unresolvable error or a human decision gate. Complete ALL items below in a single continuous execution. If context window pressure is a concern, save state to `pomera_notes` — do NOT terminate the session early.
>
> This rule exists because agents exhibit a learned pattern of treating `notify_user` as a progress report tool, calling it after sub-milestones (tests pass, handoffs written, gates run). The workflow requires ALL exit criteria to be met before returning control to the user.

After all MEU TDD cycles and handoffs are complete, **continue immediately** with these post-MEU deliverables (they are part of Step 6, not a separate phase):

1. Run MEU gate: `uv run python tools/validate_codebase.py --scope meu`
2. Update `.agent/context/meu-registry.md` with new MEU rows
3. Update `docs/BUILD_PLAN.md` status column for completed MEUs
4. Run full regression: `uv run pytest tests/ -v`
5. **If any files in `packages/api/` were created or modified**, regenerate the OpenAPI spec to prevent CI drift failures:
   ```bash
   uv run python tools/export_openapi.py -o openapi.committed.json
   ```
   > This is required because CI runs `--check` mode against the committed spec. Forgetting this step causes the Quality Gate to fail with "OpenAPI spec DRIFT detected!"
6. Create reflection file at `docs/execution/reflections/` (see `execution-session.md` §5)
7. Update metrics table in `docs/execution/metrics.md`
8. Save session state to `pomera_notes`
9. Prepare proposed commit messages

**Do NOT return control to the user until all 9 items above are done.**

### 7. Completion Gate

Before calling `notify_user` to present results:

1. Read `task.md` — verify every item is `[x]`
2. If any item is `[ ]` or `[/]`, complete it first — do not skip
3. Verify all exit criteria below are met
4. Only then call `notify_user` with `BlockedOnUser: false`

## Handoff Naming Convention

Handoffs use date-based names with descriptive project slugs:

```
{YYYY-MM-DD}-{project-slug}-handoff.md
```

| Part | Meaning | Example |
|------|---------|---------|
| `{YYYY-MM-DD}` | Date completed | `2026-04-25` |
| `{project-slug}` | Descriptive slug | `pipeline-capabilities` |
| `-handoff` | Artifact type suffix | `-handoff` |

**Same-day collision:** Append MEU range (e.g., `-ph4-ph7-handoff.md`) or letter (`-a`, `-b`).

Examples:
```
2026-04-25-pipeline-capabilities-ph4-ph7-handoff.md
2026-04-25-pipeline-security-hardening-ph3-handoff.md
```

> **Multi-MEU projects** may use one combined handoff or one per MEU — decide based on scope.

## Exit Criteria

> [!IMPORTANT]
> The agent MUST NOT call `notify_user` until every item below is checked. See Step 7 (Completion Gate).

- [ ] Plan written to `docs/execution/plans/{date}-{project-slug}/`
- [ ] All MEUs in the project executed via TDD
- [ ] One handoff per MEU created with sequenced naming
- [ ] MEU gate passed: `uv run python tools/validate_codebase.py --scope meu`
- [ ] MEU registry updated per MEU
- [ ] `docs/BUILD_PLAN.md` status updated for completed MEUs
- [ ] OpenAPI spec regenerated (if `packages/api/` was modified)
- [ ] Reflection file created
- [ ] Metrics table updated
- [ ] Session state saved to pomera_notes
- [ ] Proposed commit messages presented to human
