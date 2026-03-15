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
// NOTE: turbo-all sets SafeToAutoRun=true for non-destructive commands (rg, Get-Content, etc.).
// It does NOT override AGENTS.md §Commits: "Never auto-commit." Git commit/push still requires explicit user direction.

## Prerequisites

Read these files in order:

1. `SOUL.md`
2. `AGENTS.md`
3. `.agent/context/current-focus.md`
4. `.agent/context/known-issues.md`
5. `pomera_notes` search (`Zorivest`, `Memory/Session/*`, `Memory/Decisions/*`)

---

## Auto-Discovery (No User Input Required)

The agent discovers the review findings file automatically. The user only needs to invoke the workflow.

### Discovery Steps

```powershell
# Step A: Find the most recent canonical critical-review handoff
Get-ChildItem .agent/context/handoffs/*critical-review.md |
  Sort-Object LastWriteTime -Descending | Select-Object -First 1
```

### Resolution Logic

1. **Primary target**: the most recent `*critical-review.md` file (Step A)
2. **Working context**: use the latest dated update inside that canonical review file as the current state
3. If the latest update verdict is `approved`, inform the user that no open findings remain
4. If the latest update verdict is `changes_required`, use that update's findings as the working set

> Review continuity rule: repeated rechecks stay in the same canonical critical-review file. Do not expect parallel `-recheck` or `-corrections` files for the same plan or implementation thread.

### Scope Override

If the user provides an explicit review file path, use that instead of auto-discovery.

---

## Workflow Steps

### Step 1: Parse Findings (Orchestrator)

Read the auto-discovered review file and extract a structured findings list from the latest unresolved review update:

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

### Step 2b: Categorize and Generalize (Tester)

> **Context**: The "fix-specific-not-general" meta-pattern was the single biggest multiplier of review passes. When Codex reported "this route returns 500 for NotFoundError", Opus would fix that one route but not check all other routes for the same issue.

For each verified finding:

1. **Categorize it** — assign a category label (e.g., "error mapping gap", "stale evidence", "stub inadequacy", "cross-doc reference").
2. **Search for siblings** — run `rg` for the same pattern across all similar files/routes/modules.
3. **Document siblings** — add to the findings table: "Found M additional instances of same category in files X, Y, Z."

This ensures the corrections plan addresses ALL instances, not just the cited ones.

---

### Step 3: Create Corrections Plan (Orchestrator)

For each verified finding, specify the exact fix:

- **File**: absolute path
- **What to change**: before → after (diff or description)
- **Why**: link back to finding # and severity

Group fixes by file for efficient editing.

Write the plan to the Antigravity `implementation-plan.md` artifact and request user approval via `notify_user`.

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

### Step 5b: Evidence Refresh

After ALL corrections are applied, re-run every validation command and update the handoff/task with fresh counts:

```powershell
# Refresh all evidence counts
uv run pytest tests/ --tb=no -q        # Get fresh regression total
uv run pyright <touched-packages>       # Verify type safety
uv run ruff check <touched-files>       # Verify lint
# For TS projects:
npx vitest run                          # Get fresh test total
npx tsc --noEmit                        # Verify type safety
npx eslint src/ --max-warnings 0        # Verify lint
```

Update the handoff with fresh counts — stale counts from earlier in the session are a recurring finding category.

### Step 5c: Cross-Doc Sweep

If any correction changed a contract or architectural pattern:

```powershell
# Search for old pattern across all canonical docs
rg -n -i "<old-pattern>" docs/build-plan/ docs/execution/ .agent/
```

Update all references to match the new pattern. Document: "Cross-doc sweep: N files checked, M updated."

---

### Step 6: Write Handoff (Reviewer)

Update the same canonical critical-review handoff in `.agent/context/handoffs/`:

- append a dated `Corrections Applied` or `Recheck` section
- include plan summary, diffs/changes made, verification results, and the current verdict
- keep the full review thread in that single file for the target plan or implementation review

Use the combined plan+walkthrough format inside the existing file rather than creating a parallel corrections artifact.

---

## Hard Rules

1. **Always verify findings before fixing.** Reviews can have stale line numbers or already-resolved issues.
2. **Never skip a finding without explanation.** If a finding is refuted, say why.
3. **Group multi-file edits by file.** Minimize tool calls.
4. **Verification must be slug/anchor-aware.** Phrase-only grep is insufficient when headings were renamed. Always check both space form (`foo bar`) and slug form (`foo-bar`).
5. **Build plan docs must not link into `.agent/`.** Design decisions should be self-contained in the build-plan file, not dependent on session artifacts.
6. **User approval required before execution.** Plan → approve → execute → verify.
7. **Resolve the canonical review first.** Always work from the canonical `*critical-review.md` file and update that same file as the review evolves.
8. **Fix general, not specific.** When correcting a finding, search for ALL instances of the same category across similar files. Fixing only the cited instance while leaving identical bugs elsewhere is the single biggest cause of multi-pass review loops.

---

## Output Contract

Deliver to the user via `notify_user`:

1. Auto-discovered review target (which canonical file was found and how the latest update was selected)
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
