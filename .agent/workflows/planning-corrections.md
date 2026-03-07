---
description: Plan and execute corrections from critical review findings. Auto-discovers the most recent review handoff and applies fixes systematically.
---

# Planning Corrections Workflow

Use this workflow when a critical review has produced findings and you want to plan and execute corrections. This is the counterpart to `/critical-review-feedback` — that workflow produces findings, this one resolves them. The agent automatically discovers the review file — no paths required.

This is the workflow for prompts like:

- "Fix all findings from the latest review"
- "Apply corrections"
- "Plan corrections"

// turbo-all

## Prerequisites

Read these files in order:

1. `SOUL.md`
2. `GEMINI.md`
3. `AGENTS.md`
4. `.agent/context/current-focus.md`
5. `.agent/context/known-issues.md`
6. `pomera_notes` search (`Zorivest`, `Memory/Session/*`, `Memory/Decisions/*`)

---

## Auto-Discovery (No User Input Required)

The agent discovers the review findings file automatically. The user only needs to invoke the workflow.

### Discovery Steps

```powershell
# Step A: Find the most recent originating critical-review handoff
Get-ChildItem .agent/context/handoffs/*critical-review.md |
  Sort-Object LastWriteTime -Descending | Select-Object -First 1

# Step B: Check if follow-up rechecks/corrections exist for that review
$stem = "<slug-from-step-A>"
Get-ChildItem .agent/context/handoffs/*$stem*-recheck*.md,
              .agent/context/handoffs/*$stem*-corrections*.md |
  Sort-Object LastWriteTime -Descending
```

### Resolution Logic

1. **Primary target**: the most recent `*critical-review.md` file (Step A)
2. **Chain context**: any `*-recheck*` or `*-corrections*` files that share the same task slug (Step B)
3. If the chain shows the latest recheck verdict is `approved`, inform the user that no open findings remain
4. If the chain shows `changes_required`, use the most recent recheck's findings as the working set

> The glob `*critical-review.md` (no inner wildcard) prevents matching recheck files like `*-critical-review-recheck.md`, avoiding the duplicate-rows problem.

### Scope Override

If the user provides an explicit review file path, use that instead of auto-discovery.

---

## Workflow Steps

### Step 1: Parse Findings (Orchestrator)

Read the auto-discovered review file (and chain context if present) and extract a structured findings list:

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
3. **Check for related issues** the reviewer may have missed (adjacent lines, similar patterns in other files)

Use `rg` and file reads — do not trust the review's line numbers blindly (they may have shifted since the review was written).

Output a verified findings table:

| # | Severity | Verified? | Current Line(s) | Notes |
|---|----------|-----------|-----------------|-------|

Skip any findings that are already resolved or refuted.

---

### Step 3: Create Corrections Plan (Orchestrator)

For each verified finding, specify the exact fix:

- **File**: absolute path
- **What to change**: before → after (diff or description)
- **Why**: link back to finding # and severity

Group fixes by file for efficient editing.

Write the plan to the Antigravity `implementation_plan.md` artifact and request user approval via `notify_user`.

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
# Anchor/slug check (catches heading renames that break cross-links)
rg -n "<old-slug-pattern>" docs/build-plan/

# Phrase variant check (space + hyphen + slug forms)
rg -n -i "<old-phrase>|<old-phrase-slugified>" docs/build-plan/

# Handoff link portability check (canonical docs should not link into .agent/)
rg -n "\.agent/context/handoffs" docs/build-plan/
```

---

### Step 6: Write Handoff (Reviewer)

Create or update a handoff in `.agent/context/handoffs/` that merges the plan + walkthrough:

- **File name**: `{YYYY-MM-DD}-{original-task-slug}-corrections.md`
- **Contents**: plan summary, diffs/changes made, verification results, auto-discovered source review path and chain context

Use the combined plan+walkthrough format (not separate files).

---

## Hard Rules

1. **Always verify findings before fixing.** Reviews can have stale line numbers or already-resolved issues.
2. **Never skip a finding without explanation.** If a finding is refuted, say why.
3. **Group multi-file edits by file.** Minimize tool calls.
4. **Verification must be slug/anchor-aware.** Phrase-only grep is insufficient when headings were renamed. Always check both space form (`foo bar`) and slug form (`foo-bar`).
5. **Build plan docs must not link into `.agent/`.** Design decisions should be self-contained in the build-plan file, not dependent on session artifacts.
6. **User approval required before execution.** Plan → approve → execute → verify.
7. **Resolve the canonical review first.** Always trace back to the originating `*critical-review.md` — do not start from a recheck or corrections file without understanding the full chain.

---

## Output Contract

Deliver to the user via `notify_user`:

1. Auto-discovered review target (which file was found, chain context, and resolution logic)
2. Verified findings count (confirmed vs refuted)
3. Corrections plan (for approval)
4. After execution: verification results + handoff path

---

## Orchestration Flow

This workflow is part of a three-workflow orchestration cycle:

1. `/create-plan` → plan and execute new work
2. `/critical-review-feedback` → review completed work
3. `/planning-corrections` → resolve findings (this workflow)

When to switch:

- Use `/critical-review-feedback` first to **produce** the review findings.
- Use this workflow (`/planning-corrections`) to **resolve** the findings.
- Use `/create-plan` for new feature implementation (not corrections).
