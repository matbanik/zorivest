---
description: Plan and execute corrections from critical review findings. Provide the review findings file and this workflow applies fixes systematically.
---

# Planning Corrections Workflow

Use this workflow when a critical review has produced findings and you want to plan and execute corrections. This is the counterpart to `/critical-review-feedback` — that workflow produces findings, this one resolves them.

This is the workflow for prompts like:

- "Fix all findings in this critical review"
- "Address `<handoff path>` findings"
- "Plan corrections for `<review file>`"

## Primary Use Case

You provide:

1. A **review findings file** (from `/critical-review-feedback` or manual review)
2. Optionally: priority overrides or decisions on open questions

The workflow produces:

1. **Verification of each finding** against source files (confirm/refute)
2. **Implementation plan** with per-finding fix
3. **Executed corrections** across all affected files
4. **Updated handoff** with plan + walkthrough merged into one file

---

## Input Contract

Minimum:

- **Review file path**: the critical review handoff containing findings

Optional:

- **Design decisions**: answers to open questions from the review
- **Scope limit**: "fix High only" or "fix all"

### Example Invocation

```text
Use /planning-corrections.
Review file: .agent/context/handoffs/2026-02-26-remove-embedded-mode-critical-review.md
Fix all findings.
```

---

## Workflow Steps

// turbo-all

### Step 1: Parse Findings (Orchestrator)

Read the review file and extract a structured findings list:

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

Use `rg` and `view_file` — do not trust the review's line numbers blindly (they may have shifted since the review was written).

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

Group fixes by file for efficient editing (multiple fixes per file use `multi_replace_file_content`).

Write the plan to `implementation_plan.md` artifact and request user approval via `notify_user`.

**Do not proceed to Step 4 without user approval.**

---

### Step 4: Execute Corrections (Coder)

Apply all fixes. Rules:

1. Read the exact lines before editing (get current line numbers)
2. Apply fixes bottom-to-top within each file to avoid line shifts
3. Multiple non-adjacent edits in the same file → single `multi_replace_file_content` call
4. Single contiguous edit → `replace_file_content`

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
- **Contents**: plan summary, diffs/changes made, verification results

Use the combined plan+walkthrough format (not separate files).

---

## Hard Rules

1. **Always verify findings before fixing.** Reviews can have stale line numbers or already-resolved issues.
2. **Never skip a finding without explanation.** If a finding is refuted, say why.
3. **Group multi-file edits by file.** Minimize tool calls.
4. **Verification must be slug/anchor-aware.** Phrase-only grep is insufficient when headings were renamed. Always check both space form (`foo bar`) and slug form (`foo-bar`).
5. **Build plan docs must not link into `.agent/`.** Design decisions should be self-contained in the build-plan file, not dependent on session artifacts.
6. **User approval required before execution.** Plan → approve → execute → verify.

---

## Output Contract

Deliver to the user via `notify_user`:

1. Verified findings count (confirmed vs refuted)
2. Corrections plan (for approval)
3. After execution: verification results + handoff path

---

## When to Switch Workflows

- Use `/critical-review-feedback` first to **produce** the review findings
- Use this workflow (`/planning-corrections`) to **resolve** the findings
- Use `/orchestrated-delivery` for new feature implementation (not corrections)
