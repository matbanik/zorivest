---
description: Plan and execute corrections for plan-document review findings. Fixes plan files, task contracts, and workflow docs — never production code.
---

# Plan Corrections Workflow

Use this workflow when a `/plan-critical-review` has produced findings and you want to resolve them. This workflow corrects **plan documents, task contracts, and workflow docs** — it never touches production code, tests, or implementation files.

This is the workflow for prompts like:

- "Fix all findings from the plan review"
- "Apply corrections to the implementation plan"
- "Resolve the plan-critical-review findings"

// turbo-all
// NOTE: turbo-all sets SafeToAutoRun=true for non-destructive commands (rg, Get-Content, etc.).
// It does NOT override AGENTS.md §Commits: "Never auto-commit." Git commit/push still requires explicit user direction.

## Write Scope (Non-Negotiable)

This is a plan-correction workflow.

Allowed file writes:

- `docs/execution/plans/*/implementation-plan.md`
- `docs/execution/plans/*/task.md`
- `.agent/workflows/*.md`
- `.agent/docs/*.md`
- `.agent/context/*.md`
- `.agent/context/handoffs/*-plan-critical-review.md` (correction log appended)
- `AGENTS.md`
- `docs/execution/README.md`
- optional `pomera_notes` session memory

Forbidden file writes:

- production code (`packages/`, `ui/`, `mcp-server/`)
- test files (`tests/`)
- `docs/build-plan/` sections that describe runtime behavior (unless the plan review explicitly cited them as incorrect)

If a finding requires production code changes, record it as a deferred item and route to `/execution-corrections`.

---

## Prerequisites

Read these files in order:

1. `AGENTS.md`
2. `.agent/context/current-focus.md`
3. `.agent/context/known-issues.md`
4. `pomera_notes` search (`Zorivest`, `Memory/Session/*`, `Memory/Decisions/*`)

---

## Auto-Discovery (No User Input Required)

The agent discovers the review findings file automatically.

### Discovery Steps

```powershell
# Find the most recent plan-critical-review handoff
Get-ChildItem .agent/context/handoffs/*-plan-critical-review.md |
  Sort-Object LastWriteTime -Descending | Select-Object -First 1
```

### Resolution Logic

1. **Primary target**: the most recent `*-plan-critical-review.md` file
2. **Working context**: use the latest dated update inside that file as the current state
3. If the latest update verdict is `approved`, inform the user that no open findings remain
4. If the latest update verdict is `changes_required`, use that update's findings as the working set

### Scope Override

If the user provides an explicit review file path, use that instead of auto-discovery.

---

## Workflow Steps

### Step 1: Parse Findings (Orchestrator)

Read the auto-discovered review file and extract a structured findings list:

| # | Severity | Summary | File(s) | Line(s) |
|---|----------|---------|---------|---------|

For each finding, capture:
- Severity (Critical/High/Medium/Low)
- One-line summary
- Affected file(s) and line(s)
- Reviewer's suggested fix (if any)

---

### Step 2: Verify Each Finding (Tester)

For every finding, verify it against live file state:

1. **Read the exact line(s)** cited in the finding
2. **Confirm or refute** the issue still exists
3. **Check for related issues** the reviewer may have missed

Use `rg` and file reads — do not trust the review's line numbers blindly.

Output a verified findings table:

| # | Severity | Verified? | Current Line(s) | Notes |
|---|----------|-----------|-----------------|-------|

### Step 2b: Categorize and Generalize (Tester)

For each verified finding:

1. **Categorize it** — assign a category label (e.g., "task contract gap", "stale reference", "validation weakness", "source-basis missing")
2. **Search for siblings** — run `rg` for the same pattern across all similar files
3. **Document siblings** — add to the findings table

---

### Step 3: Create Corrections Plan (Orchestrator)

For each verified finding, specify the exact fix:

- **File**: absolute path
- **What to change**: before → after (diff or description)
- **Why**: link back to finding # and severity

Group fixes by file. Write the plan to the Antigravity `implementation-plan.md` artifact and request user approval.

**Do not proceed to Step 4 without user approval.**

---

### Step 4: Execute Corrections (Coder)

Apply all fixes. Rules:

1. Read the exact lines before editing (get current line numbers)
2. Apply fixes bottom-to-top within each file to avoid line shifts
3. Multiple non-adjacent edits in the same file → single edit call
4. Single contiguous edit → single edit call

---

### Step 5: Verify Corrections (Tester)

Re-run the verification commands from Step 2 to confirm all findings are resolved.

Additionally run:

```powershell
# Cross-reference check for stale terms
rg -n "<old-slug-pattern>" .agent/workflows/ .agent/docs/ AGENTS.md docs/execution/

# Phrase variant check
rg -n -i "<old-phrase>|<old-phrase-slugified>" .agent/workflows/ .agent/docs/
```

### Step 5b: Cross-Doc Sweep

If any correction changed a contract or workflow reference:

```powershell
# Search for old pattern across all canonical docs
rg -n -i "<old-pattern>" .agent/ docs/ AGENTS.md
```

Update all references. Document: "Cross-doc sweep: N files checked, M updated."

---

### Step 6: Write Handoff (Reviewer)

Update the same canonical plan-critical-review handoff in `.agent/context/handoffs/`:

- append a dated `Corrections Applied` section
- include plan summary, changes made, verification results, and the current verdict
- keep the full review thread in that single file

---

## Hard Rules

1. **Always verify findings before fixing.** Reviews can have stale line numbers.
2. **Never skip a finding without explanation.** If refuted, say why.
3. **Group multi-file edits by file.** Minimize tool calls.
4. **Verification must be slug/anchor-aware.** Check both space form and slug form.
5. **User approval required before execution.** Plan → approve → execute → verify.
6. **Resolve the canonical review first.** Work from `*-plan-critical-review.md` and update that same file.
7. **Fix general, not specific.** Search for ALL instances of the same category across similar files.
8. **Never touch production code.** If a finding requires code changes, defer to `/execution-corrections`.

---

## Output Contract

Deliver to the user:

1. Auto-discovered review target
2. Verified findings count (confirmed vs refuted)
3. Corrections plan (for approval)
4. After execution: verification results + handoff path

---

## Orchestration Flow

This workflow is part of a four-workflow orchestration cycle:

1. `/create-plan` → plan new work
2. `/plan-critical-review` → review a new plan
3. `/plan-corrections` → resolve plan-review findings (this workflow)
4. `/execution-critical-review` → review completed implementation work

When to switch:

- Use `/plan-critical-review` first to **produce** the review findings.
- Use this workflow (`/plan-corrections`) to **resolve** plan-level findings.
- Use `/execution-corrections` for production code corrections.

## HARD STOP

> [!CAUTION]
> **Do NOT autonomously chain into `/plan-critical-review`, `/execution-corrections`, or any other workflow after completing corrections.** You MUST stop here and report the canonical review handoff path to the user. The user decides what happens next.

**Workflow complete.** Report the handoff path and wait for user direction.
