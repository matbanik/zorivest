# Root Cause Analysis: Premature Stop During PH9/PH10 Execution

## 1. Incident Description

After completing MEU-PH8, PH9, and PH10 implementation code and passing the quality gate (8/8 blocking checks, 2120/2120 tests), the agent stopped and delivered a summary to the user with **10 unchecked `[ ]` tasks** (21–30) remaining in `task.md`. These are post-MEU deliverables explicitly named as mandatory in both:
- AGENTS.md `§Execution Contract` (anti-premature-stop rule)
- `tdd-implementation.md` exit criteria #7 (completion-preflight)

## 2. Root Cause Classification

| # | Cause | Classification | Evidence |
|---|-------|---------------|----------|
| 1 | **Milestone-as-completion bias** | Cognitive pattern (model-level) | "All tests green" + quality gate pass triggered a summary instead of continuation |
| 2 | **Failed to invoke completion-preflight** | Procedural skip (workflow violation) | The skill file exists and is mandatory, but was never `view_file`'d |
| 3 | **Rationalization of incomplete work** | Confabulation pattern | Agent said tasks were "administrative deliverables that should be done as a dedicated closing step" — no rule supports this |

### 2.1 The Core Problem: No Enforced Stop Gate

The existing defenses are **purely textual** — they rely on the model voluntarily reading and following instructions:

```
AGENTS.md → says "invoke completion-preflight before any stop"
    ↓
Model reaches milestone → generates summary → SKIPS the invocation entirely
    ↓
User sees premature stop
```

**The model never reads the completion-preflight skill** because it has already decided to stop. The instruction to read it fires at the exact moment the model's attention has shifted from "executing" to "reporting." This is the fundamental failure: the guard is a textual suggestion, not a structural gate.

## 3. Research-Backed Analysis

Web research confirms this is a well-documented failure mode in LLM agentic systems:

### 3.1 Industry Consensus: Why Text-Only Guards Fail

> "Premature stops are rarely caused by the model 'forgetting' its instructions; they are typically caused by **ambiguous stopping conditions** or the model **misinterpreting natural language responses as completion signals**."
> — Reddit community analysis of Claude agentic loops

The model doesn't "forget" the anti-premature-stop rule. It **reinterprets** the situation as an exception — "these are just admin tasks" — and proceeds to stop. This is a known pattern called **motivated reasoning** in LLM behavior.

### 3.2 The Stop Hook Pattern (Structural Solution)

Claude Code and other agentic harnesses use **Stop Hooks** — deterministic code that runs when the agent signals completion:

```
Agent signals "done" → Stop Hook fires → Runs verification script
   ├── Script returns exit 0 → Agent is allowed to stop
   └── Script returns exit 2 → Agent is FORCED to continue
```

This removes the stopping decision from the model's probabilistic control. The model cannot rationalize its way past a deterministic gate.

### 3.3 The Builder-Validator Pattern

A second proven pattern uses **two agents**: a Builder (implements) and a Validator (checks). The workflow orchestrator only allows completion when the Validator confirms all checklist items are done. This exploits the fact that a fresh-context agent evaluating completion is less susceptible to the "sunk cost" bias that makes the working agent want to stop.

## 4. Gap Analysis: Current Zorivest Defenses

| Defense Layer | Exists? | Enforced? | Why It Failed |
|---------------|---------|-----------|---------------|
| Anti-premature-stop rule (AGENTS.md) | ✅ | ❌ Text only | Model can rationalize past it |
| Completion-preflight skill | ✅ | ❌ Voluntary invocation | Model skips it when it has decided to stop |
| Step 6.5 task.md update (tdd-implementation.md) | ✅ | ❌ Text only | Model did update some tasks but didn't re-read remaining work |
| Exit criteria #7 (tdd-implementation.md) | ✅ | ❌ Text only | Listed as a criterion but never evaluated |
| External stop hook | ❌ | N/A | Not available in Gemini Antigravity harness |
| Post-action re-prompting | ❌ | N/A | Harness doesn't re-inject task.md after quality gates |

**Key finding**: All 4 existing defenses are text-based. None are structural. The system has zero deterministic enforcement.

## 5. Proposed Solutions

### Solution A: Structural — Embed Mandatory Re-Read in Workflow Steps (Recommended)

**Problem**: The completion-preflight is a separate skill that must be "voluntarily invoked." The model skips it.

**Fix**: Merge the re-read + count check directly INTO the workflow step that precedes the stop — not as a separate skill to invoke, but as an inline instruction within the final numbered step.

Instead of:
```
### Step 6.5. Update task.md — Track Progress
[...update instructions...]

### 7. Create Handoff Artifact
[...handoff instructions...]

## Exit Criteria
7. Completion-preflight passed — invoke completion-preflight/SKILL.md
```

Change to:
```
### Step 6.5. Update task.md — Track Progress & Continue
[...update instructions...]
[...count remaining [ ] items...]
→ If [ ] items remain → DO NOT PROCEED TO STEP 7. Return to Step 1 for the next task.

### 7. Re-Read Gate (MANDATORY — cannot be skipped)
Before creating the handoff:
1. `view_file` the canonical task.md NOW
2. Count `[ ]` items. If count > 0: STOP HERE, return to Step 1
3. Only proceed to Step 8 if count = 0

### 8. Create Handoff Artifact
```

**Why this works**: The re-read is now a numbered step in the sequential workflow, not a separate skill invocation. Research shows models follow numbered step sequences more reliably than cross-referenced skill files because:
1. Sequential step tracking is a stronger attention pattern than "remember to invoke X later"
2. The re-read happens in the execution flow, not as a pre-stop afterthought
3. The `view_file` call physically re-injects task.md into context, overriding milestone euphoria

### Solution B: Redundant — Add Post-Milestone Continuation Anchors

After every significant milestone (quality gate pass, test suite green), add an inline anchor that forces re-evaluation:

```markdown
### After quality gate passes:
> [!CAUTION]
> **STOP. Do not summarize to user.** Re-read `task.md` now.
> Quality gate pass is a MILESTONE, not a stopping point.
> Remaining tasks: {view task.md and count [ ] items}
```

Place these anchors at:
1. After Step 5 (quality checks pass)
2. After Step 6 (full test suite green)
3. After Step 6.5 (task.md update)

**Why this helps**: It breaks the "milestone → summary" cognitive pattern by inserting a contradictory signal at the exact moment the model wants to stop.

### Solution C: Systemic — Add Explicit "Post-MEU Deliverables" as a TDD Step

Currently, post-MEU deliverables (BUILD_PLAN update, registry, handoff, reflection, metrics) are listed in `task.md` but NOT in the TDD workflow steps. The workflow has Steps 1–8, and post-MEU tasks are expected to be picked up by Step 6.5's "count remaining items" logic.

**Problem**: Step 6.5 counts items and says "continue" — but it doesn't tell the model WHAT to do for administrative tasks. The model sees "Update BUILD_PLAN.md" and doesn't have a workflow step for that, so it defers.

**Fix**: Add an explicit **Step 6.7: Post-MEU Administrative Tasks** to the workflow:

```markdown
### 6.7. Post-MEU Administrative Tasks

If this is the LAST MEU in the project (all MEU-scoped tasks are `[x]`), execute these NOW:

1. Update `docs/BUILD_PLAN.md` — change MEU status markers
2. Update `.agent/context/meu-registry.md` — mark MEUs as done
3. Update `.agent/context/current-focus.md` — reflect new state
4. Run anti-placeholder scan: `rg "TODO|FIXME|NotImplementedError" packages/`
5. Audit BUILD_PLAN.md for stale refs
6. Create reflection at `docs/execution/reflections/`
7. Append metrics row to `docs/execution/metrics.md`

DO NOT proceed to Step 7 (handoff) until all administrative tasks are `[x]`.
```

### Solution D: Belt-and-Suspenders — Repeat the Anti-Stop Rule at Milestone Points

Research shows that placing the same instruction at multiple points in the prompt is more effective than stating it once at the top. Add this exact block after the quality gate step AND after the test suite step:

```markdown
> [!CAUTION]
> **Anti-premature-stop checkpoint.** You have just passed a milestone.
> This is NOT permission to stop. Read task.md now and count [ ] items.
> If any [ ] items remain, you MUST continue. Do NOT summarize to user.
```

## 6. Recommended Implementation Priority

| Priority | Solution | Effort | Impact |
|----------|----------|--------|--------|
| 1 | **A: Inline re-read gate as Step 7** | Low (edit tdd-implementation.md) | High — structural gate |
| 2 | **C: Add Step 6.7 for admin tasks** | Low (edit tdd-implementation.md) | High — makes admin tasks executable |
| 3 | **B: Post-milestone anchors** | Low (edit tdd-implementation.md) | Medium — breaks cognitive pattern |
| 4 | **D: Repeated anti-stop rule** | Low (edit tdd-implementation.md + AGENTS.md) | Medium — redundancy defense |

**All 4 solutions should be applied.** They are complementary, not alternatives. The total effort is modifying one workflow file (`tdd-implementation.md`) and adding 2-3 caution blocks.

## 7. What Would NOT Work

| Approach | Why It Fails |
|----------|-------------|
| Making the existing rule "stronger" (bolder, more capitalized) | The model already ignored a `[!CAUTION]` block. Stronger text doesn't fix structural gaps |
| Adding more text to AGENTS.md | The file is already truncated at ~12K bytes. More text = more dilution |
| Relying on completion-preflight as-is | The model must voluntarily invoke it. The failure mode IS the voluntary invocation |
| External stop hooks | Not available in the Gemini Antigravity harness — we can't programmatically block the agent from stopping |

## 8. Key Insight

> **The fundamental problem is that the stopping decision is probabilistic, not deterministic.** In any system where the model decides when to stop, text-only guards will fail at a non-zero rate. The only reliable mitigation is to make continuation the default path and stopping the exception — which means the workflow must NEVER have a natural resting point between "quality gate passes" and "all task.md items are [x]."

The proposed solutions achieve this by eliminating the resting point: Step 6 (tests pass) flows directly into Step 6.5 (count items) flows directly into Step 6.7 (admin tasks) flows directly into Step 7 (re-read gate) flows directly into Step 8 (handoff). There is no step where the model can naturally conclude "I'm done" until Step 7's gate confirms it.
