---
description: Structured execution + meta-reflection workflow for daily build sessions. Ensures TDD discipline, handoff quality, and iterative prompt improvement.
---

# Execution Session Workflow

Use this workflow at the start of each build session. It orchestrates three phases: **Plan → Execute → Reflect** — creating a feedback loop that makes each successive session faster and higher quality.

Artifact naming conventions:

- `docs/execution/plans/{YYYY-MM-DD}-{project-slug}/implementation-plan.md`
- `docs/execution/plans/{YYYY-MM-DD}-{project-slug}/task.md`
- If a project is replanned on the same day, append `-v2`, `-v3`, etc. to the folder name.

// turbo-all

## Prerequisites

- Read `SOUL.md`, `GEMINI.md`, `AGENTS.md`
- Read `.agent/context/current-focus.md` for active phase
- Read `.agent/context/meu-registry.md` for MEU scope

## Steps

### 1. Create Project Plan

Run the `/create-plan` workflow (`.agent/workflows/create-plan.md`). This replaces per-session prompt drafting — the agent discovers what's done, identifies what's next, and uses reasoning to scope a coherent project.

### 2. Check Previous Reflections

Read the most recent reflection file from `docs/execution/reflections/` (sort by `LastWriteTime` descending to find the latest, since multiple same-day reflections sort by slug). Apply any rules from its "Next Session Design Rules" section to today's planning. Call out which rules you're applying so the human can verify.

### 3. Planning Phase (Antigravity PLANNING Mode)

> Steps 1-3 happen as part of the `/create-plan` workflow.

Antigravity (Opus 4.6) will:

1. Enter **PLANNING mode** via `task_boundary`
2. Discover progress from handoffs + meu-registry
3. Scope the next project from pending build-plan MEUs
4. Generate `implementation_plan.md` and `task.md` in the brain folder
5. Present the plan to the human via `notify_user` with `BlockedOnUser: true`

**Human Review Loop**:
- The human reviews the generated plan
- If changes are needed → provide feedback → Antigravity regenerates the plan
- If approved → proceed to Step 4

**Plan Archival** (after approval, before execution):
Copy the approved plan artifacts from the brain folder into the project's execution tracking folder:

```bash
# Copy from Antigravity brain folder to project execution/plans/
mkdir -p docs/execution/plans/{YYYY-MM-DD}-{project-slug}

cp ~/.gemini/antigravity/brain/{conversation-id}/implementation_plan.md \
   docs/execution/plans/{YYYY-MM-DD}-{project-slug}/implementation-plan.md

cp ~/.gemini/antigravity/brain/{conversation-id}/task.md \
   docs/execution/plans/{YYYY-MM-DD}-{project-slug}/task.md
```

> **Why archive?** Brain folders are per-conversation and not version-controlled. Copying plans into `docs/execution/plans/{YYYY-MM-DD}-{project-slug}/` preserves them in git and allows cross-session comparison of planning quality.

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
- **Execute all MEUs in the approved project plan**, completing each MEU's TDD cycle before starting the next
- **Do not auto-commit** — propose conventional commit messages to the human instead

### 5. Meta-Reflection (Post-Execution)

After completing all phases, create the reflection file at `docs/execution/reflections/{YYYY-MM-DD}-{project-slug}-reflection.md` using the template at `docs/execution/reflections/TEMPLATE.md`.

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

#### 5c. Next Session Design Rules
Write 3–5 concrete rules for the next session's plan, formatted as:
```
RULE-{N}: {description}
SOURCE: {which signal led to this}
EXAMPLE: {before/after}
```

#### 5d. Next Session Outline
Write a 10-line outline for the next session's plan:
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
  --title "Memory/Session/Zorivest-{project-slug}-{YYYY-MM-DD}"
  --input_content "<MEUs completed, key decisions>"
  --output_content "<reflection summary, next session outline>"
```

### 7. Notify Human

Present the human with:
1. Completion summary (MEUs done, tests passing, proposed commit messages)
2. Codex validation trigger text (Phase C from the prompt)
3. Link to the reflection file for review
4. Draft outline for the next session (used by `/create-plan` workflow)

## Session Lifecycle Summary

```
┌─────────────────────────────────────────────────────┐
│  /create-plan workflow                              │
│  → reads handoffs, meu-registry, build-plan         │
│  → scopes project, generates plan                   │
└───────────┬─────────────────────────────────────────┘
            ▼
┌─────────────────────────────────────────────────────┐
│  Human reviews plan                                 │
│  → adjusts / approves                               │
│  → plan archived to docs/execution/plans/{YYYY-MM-DD}-{project-slug}/│
└───────────┬─────────────────────────────────────────┘
            ▼
┌─────────────────────────────────────────────────────┐
│  Antigravity EXECUTION mode (per MEU)               │
│  → TDD cycle → handoff → registry update            │
│  → Codex validates each MEU handoff                 │
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

- [ ] Plan archived to `docs/execution/plans/{YYYY-MM-DD}-{project-slug}/`
- [ ] All project plan steps completed
- [ ] Handoff artifact(s) created at `.agent/context/handoffs/`
- [ ] MEU registry updated
- [ ] Reflection file created at `docs/execution/reflections/`
- [ ] Metrics table updated
- [ ] Session state saved to pomera_notes
- [ ] Proposed commit messages presented to human
