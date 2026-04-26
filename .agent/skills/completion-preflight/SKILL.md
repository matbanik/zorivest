---
name: Completion Pre-Flight
description: Mandatory pre-flight checklist before any stop, report, or summary to the user during execution. Prevents premature stop by enforcing a deterministic re-read of the project task.md.
---

# Completion Pre-Flight

**Trigger:** MUST be invoked before any stop, summary, or "implementation complete" report to the user during EXECUTION or VERIFICATION mode.

**Objective:** Prevent premature stop by ensuring all task.md items are complete before yielding control to the user. This is the procedural enforcement of the anti-premature-stop rule in AGENTS.md §Execution Contract.

> This skill was created after root cause analysis of a premature stop incident where context truncation caused 16 unchecked task items to be silently dropped. See `premature_stop_analysis.md` in conversation `9986e441` for full RCA.

## Pre-Flight Checklist

Satisfy ALL before any stop/report event:

- [ ] **Canonical task.md read**: `view_file` the project task.md at `docs/execution/plans/{project-slug}/task.md` — NOT the agent workspace copy
- [ ] **Unchecked count**: count `[ ]` items in the task table. If any remain that are not `[B]` blocked → **do NOT stop** — continue execution
- [ ] **Source of truth check**: confirm you updated the PROJECT task.md, not only the agent workspace copy
- [ ] **Pomera save**: confirm session state was saved to `pomera_notes` (or will be before stop)
- [ ] **Post-MEU deliverables**: verify all post-MEU rows (registry, BUILD_PLAN, handoffs, reflection) are addressed or explicitly deferred as `[B]`
- [ ] **Artifact structural compliance**: for each artifact created this session, verify required structural markers via `rg` (see §Structural Marker Checklist below)

> These items are the single source of truth — they enforce AGENTS.md §Execution Contract anti-premature-stop rule.

## SOP: Standard Operating Procedure

Follow this 4-step sequence before every stop/report:

### Step 1 — Read Canonical Task File

```
view_file: docs/execution/plans/{project-slug}/task.md
```

This re-injects the full task table into context, overriding any narrowed scope from checkpoint summaries.

### Step 2 — Count Remaining Work

Scan every row in the task table. Count:
- `[ ]` = not started (must be completed before stop)
- `[/]` = in progress (must be completed or checkpointed)
- `[B]` = blocked (acceptable to leave — must have linked follow-up)
- `[x]` = complete

**Decision gate:**
- If `[ ]` count > 0 → **CONTINUE EXECUTION**, do not stop
- If `[ ]` count = 0 (only `[x]` and `[B]` remain) → proceed to Step 3

### Step 3 — Verify Source of Truth

Confirm that:
1. The PROJECT task.md (`docs/execution/plans/...`) has been updated with current status
2. The agent workspace task.md (if it exists) mirrors the project copy
3. No task was marked `[x]` only in the agent workspace copy

### Step 4 — Final Gate

Before composing the stop/summary message:
- [ ] All `[ ]` items resolved (completed or moved to `[B]`)
- [ ] Project task.md updated
- [ ] Pomera session save done or queued
- [ ] Evidence bundle references actual command output, not memory

Only after all gates pass → report to user.

## Structural Marker Checklist

When Step 6 (artifact structural compliance) fires, run these checks on each artifact created this session:

### Reflection files (`docs/execution/reflections/{date}-{slug}-reflection.md`)

Required markers — grep the file for each. If missing, the reflection is non-compliant:

```powershell
rg "Friction Log|Execution Trace" <reflection-file>        # §5a
rg "Pattern Extraction|Patterns to KEEP" <reflection-file>  # §5b
rg "Next Session Design Rules|RULE-" <reflection-file>      # §5c
rg "Rule Adherence" <reflection-file>                       # Efficiency Metrics table
rg "Instruction Coverage|schema: v1" <reflection-file>      # YAML coverage block
rg "sections:" <reflection-file>                            # Per-section usage entries
rg "loaded:" <reflection-file>                              # Loaded workflows/roles/skills
rg "decisive_rules:" <reflection-file>                      # Top 5 decisive rules
```

> [!CAUTION]
> **If `rg "sections:" <reflection-file>` returns 0 matches, the Instruction Coverage YAML is missing.** This means Step 7.5 of `tdd-implementation.md` was skipped. Execute it now: `view_file .agent/schemas/reflection.v1.yaml`, then emit the YAML block in the reflection file.

If ANY marker is missing → `view_file: docs/execution/reflections/TEMPLATE.md` and rewrite the reflection using the template structure.

### Handoff files (`.agent/context/handoffs/{date}-{slug}-handoff.md`)

Required markers:

```powershell
rg "Acceptance Criteria|AC-" <handoff-file>                 # AC table
rg "CACHE BOUNDARY" <handoff-file>                          # Cache marker
rg "Evidence|FAIL_TO_PASS" <handoff-file>                   # Evidence section
rg "Changed Files" <handoff-file>                           # File delta section
```

If ANY marker is missing → `view_file: .agent/context/handoffs/TEMPLATE.md` and fix the handoff.

### Review files (`.agent/context/handoffs/{date}-{slug}-*-critical-review.md`)

Required markers:

```powershell
rg "verdict:" <review-file>                                 # YAML verdict
rg "findings_count:" <review-file>                          # YAML findings count
rg "Finding|Severity" <review-file>                         # Findings section
```

> **Fail-safe**: If you cannot find the artifact to grep (e.g., you haven't created it yet), that is itself a compliance failure — create the artifact from its template before proceeding.

## Post-Truncation Recovery Sequence

**When resuming after context truncation (checkpoint message):**

This is the highest-priority procedure after truncation. Execute it BEFORE addressing any specific issue mentioned in the checkpoint summary.

1. `view_file` the project `task.md` at `docs/execution/plans/{project-slug}/task.md`
2. Count unchecked `[ ]` items — this is the remaining work queue
3. Only then address the specific issue from the checkpoint summary
4. After resolving the immediate issue, continue the task table sequentially
5. Before stopping, re-execute this skill's full checklist (Steps 1–4 above)

> The checkpoint summary is a convenience aid, NOT a scope definition. The project task.md is the scope definition.

## Anti-Patterns (Never Do These)

```
# ❌ Update only the agent workspace task.md
write_to_file: C:\Users\Mat\.gemini\antigravity\brain\{id}\task.md  # WRONG source

# ❌ Treat "all tests green" as completion
"2299 passed, 0 failed → report to user"  # WRONG — tests green is a milestone, not a stopping point

# ❌ Jump to regression fix after truncation without reading task.md first
"Checkpoint says fix test_api_scheduling.py → do that → report done"  # WRONG — read task.md first

# ❌ Stop after fixing the immediate issue from checkpoint
"Fixed the regression → updated walkthrough → done"  # WRONG — check for remaining [ ] items
```

## When to Skip

This skill may be skipped ONLY for:
- **Human-directed stops**: User explicitly says "stop here" or "pause"
- **Context window checkpoint**: At 50% capacity, the checkpoint protocol in AGENTS.md applies instead (save state + notify human)
- **Codex handoff**: Handing off to Codex is an allowed decision gate per AGENTS.md

All other stop events — especially after "tests pass", after fixing regressions, after context truncation — MUST use this checklist.
