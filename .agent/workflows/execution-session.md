---
description: Structured execution + meta-reflection workflow for daily build sessions. Ensures TDD discipline, handoff quality, and iterative prompt improvement.
---

# Execution Session Workflow

Use this workflow at the start of each build session. It orchestrates four phases: **Prompt → Plan → Execute → Reflect** — creating a feedback loop that makes each successive session faster and higher quality.

All files use **`{YYYY-MM-DD}-{slug}`** naming, consistent with `.agent/context/handoffs/`. Prompts use **`{YYYY-MM-DD}-meu-{N}-{slug}.md`** to scope each session to a single MEU.

// turbo-all

## Prerequisites

- Read `SOUL.md`, `GEMINI.md`, `AGENTS.md`
- Read `.agent/context/current-focus.md` for active phase
- Read `.agent/context/meu-registry.md` for MEU scope

## Steps

### 1. Load Session Prompt

Read the session's execution prompt from `docs/execution/prompts/{YYYY-MM-DD}-meu-{N}-{slug}.md`.

If no prompt exists for today, inform the user and stop. Agent A (GPT-5.4) drafts prompts; the human may tune them before execution.

### 2. Check Previous Reflections

Read the most recent reflection file from `docs/execution/reflections/` (if any exist). Apply any rules from its "Next Prompt Design Rules" section to today's execution. Call out which rules you're applying so the human can verify.

### 3. Planning Phase (Antigravity PLANNING Mode)

> This step happens automatically when Antigravity enters PLANNING mode.

When a prompt is submitted, Antigravity (Opus 4.6) will:

1. Enter **PLANNING mode** via `task_boundary`
2. Generate an `implementation_plan.md` in the Antigravity brain folder at:
   ```
   ~/.gemini/antigravity/brain/{conversation-id}/implementation_plan.md
   ```
3. Also generate `task.md` (the execution checklist) in the same brain folder
4. Present the plan to the human via `notify_user` with `BlockedOnUser: true`

**Human Review Loop**:
- The human reviews the generated plan
- If changes are needed → provide feedback → Antigravity regenerates the plan
- If approved → proceed to Step 4

**Plan Archival** (after approval, before execution):
Copy the approved plan artifacts from the brain folder into the project's execution tracking folder:

```bash
# Copy from Antigravity brain folder to project execution/plans/
cp ~/.gemini/antigravity/brain/{conversation-id}/implementation_plan.md \
   docs/execution/plans/{YYYY-MM-DD}-implementation-plan.md

cp ~/.gemini/antigravity/brain/{conversation-id}/task.md \
   docs/execution/plans/{YYYY-MM-DD}-task.md
```

> **Why archive?** Brain folders are per-conversation and not version-controlled. Copying plans into `docs/execution/plans/` preserves them in git and allows cross-session comparison of planning quality.

### 4. Execute the Approved Plan

Follow the plan **exactly**. The prompt contains:
- **Session Goal** — what success looks like
- **Phase A** — any scaffold or infrastructure setup
- **Phase B** — MEU TDD work (FIC → Red → Green → Quality → Handoff)
- **Phase C** — Codex validation trigger (output to human)
- **Guardrails** — hard scope limits

Key rules during execution:
- Follow `.agent/workflows/tdd-implementation.md` for all TDD work
- Follow `.agent/workflows/meu-handoff.md` for handoff creation
- **ONE MEU per session** unless the prompt explicitly batches multiple
- **Do not auto-commit** — propose conventional commit messages to the human instead

### 5. Meta-Reflection (Post-Execution)

After completing all phases, create the reflection file at `docs/execution/reflections/{YYYY-MM-DD}-reflection.md` using the template at `docs/execution/reflections/TEMPLATE.md`.

Structure the reflection with these sections:

#### 5a. Execution Trace
Answer 11 structured questions across three logs:
- **Friction Log** (5 questions): What was slow, ambiguous, unnecessary, missing, improvised?
- **Quality Signal Log** (3 questions): Which tests caught real bugs, which were trivial, did static analysis add value?
- **Workflow Signal Log** (3 questions): Was the FIC useful, was the handoff right-sized, how many tool calls?

#### 5b. Pattern Extraction
From the friction log, categorize findings into:
- **Patterns to KEEP** — 2–3 practices that worked well
- **Patterns to DROP** — 1–2 practices that were ceremony without payoff
- **Patterns to ADD** — 1–2 gaps that caused problems
- **Calibration Adjustment** — was the time estimate accurate?

#### 5c. Next Prompt Design Rules
Write 3–5 concrete rules for the next session's prompt, formatted as:
```
RULE-{N}: {description}
SOURCE: {which signal led to this}
EXAMPLE: {before/after}
```

#### 5d. Next Session Outline
Write a 10-line outline for the next session's prompt:
- Which MEUs to target
- What scaffold changes are needed
- Which patterns from today's reflection to bake in
- Codex validation scope

#### 5e. Update Metrics

Append a row to `docs/execution/metrics.md` using the existing table format:

```markdown
| {YYYY-MM-DD} | MEU-{N} | {count} | {duration} | {count} | {count} | {X}/7 | {N}% | {duration} | {notes} |
```

The columns are: Date, MEU(s), Tool Calls, Time to First Green, Tests Added, Codex Findings, Handoff Score (X/7), Rule Adherence (%), Prompt→Commit (min), Notes.

### 6. Save Session State

Save to pomera_notes:
```
pomera_notes save
  --title "Memory/Session/Zorivest-{YYYY-MM-DD}-{slug}"
  --input_content "<MEUs completed, key decisions>"
  --output_content "<reflection summary, next session outline>"
```

### 7. Notify Human

Present the human with:
1. Completion summary (MEUs done, tests passing, proposed commit messages)
2. Codex validation trigger text (Phase C from the prompt)
3. Link to the reflection file for review
4. Draft outline for next session's prompt (use `docs/execution/prompts/TEMPLATE.md` as the base)

## Session Lifecycle Summary

```
┌─────────────────────────────────────────────────────┐
│  Agent A drafts MEU prompt; human tunes           │
└───────────┬─────────────────────────────────────────┘
            ▼
┌─────────────────────────────────────────────────────┐
│  Antigravity PLANNING mode                          │
│  → generates implementation_plan.md + task.md       │
│  → in ~/.gemini/antigravity/brain/{conv-id}/        │
│  → presents plan to human via notify_user           │
└───────────┬─────────────────────────────────────────┘
            ▼
┌─────────────────────────────────────────────────────┐
│  Human reviews plan                                 │
│  → adjusts / approves                               │
│  → plan archived to docs/execution/plans/           │
└───────────┬─────────────────────────────────────────┘
            ▼
┌─────────────────────────────────────────────────────┐
│  Antigravity EXECUTION mode                         │
│  → follows approved plan step-by-step               │
│  → creates handoff → updates MEU registry           │
└───────────┬─────────────────────────────────────────┘
            ▼
┌─────────────────────────────────────────────────────┐
│  Meta-reflection                                    │
│  → friction/quality/workflow logs                   │
│  → pattern extraction → design rules                │
│  → reflection saved to docs/execution/reflections/  │
│  → metrics updated                                  │
└─────────────────────────────────────────────────────┘
```

## Exit Criteria

- [ ] Plan archived to `docs/execution/plans/`
- [ ] All prompt phases completed
- [ ] Handoff artifact(s) created at `.agent/context/handoffs/`
- [ ] MEU registry updated
- [ ] Reflection file created at `docs/execution/reflections/`
- [ ] Metrics table updated
- [ ] Session state saved to pomera_notes
- [ ] Proposed commit messages presented to human
