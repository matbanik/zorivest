# Zorivest Agentic AI Development Methodology

> **Audience:** Human developers, software architects, business executives, and AI agents  
> **Version:** 1.0 — May 2026  
> **Source of truth:** `p:\zorivest\.agent\` — AGENTS.md, workflows, roles, skills, and context files

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Feature Research & Deep Prompt Engineering](#2-feature-research--deep-prompt-engineering)
3. [Build Planning & Decision-Tracking Indexes](#3-build-planning--decision-tracking-indexes)
4. [TDD & Anti-Practices for Agentic AI](#4-tdd--anti-practices-for-agentic-ai)
5. [The Dual-Agent Orchestration Model](#5-the-dual-agent-orchestration-model)
6. [Reflection-Driven Continuous Improvement](#6-reflection-driven-continuous-improvement)
7. [Git Commit Discipline](#7-git-commit-discipline)
8. [Why Full Automation Fails](#8-why-full-automation-between-agents-fails)
9. [Context Degradation Vigilance](#9-context-degradation-vigilance)
10. [Designing for LLM Evolution](#10-designing-for-llm-evolution)
11. [Monetization-Aware Workflow Design](#11-monetization-aware-workflow-design)

---

## 1. Executive Summary

Zorivest is a trading portfolio analysis platform built using a **human-supervised, dual-agent orchestration model**. Two frontier AI models — **Claude Opus** (Anthropic) and **ChatGPT Codex / GPT-5.5** (OpenAI) — perform complementary roles under structured workflows, with a human orchestrator maintaining oversight at every critical gate.

The methodology has delivered **200+ Manageable Execution Units (MEUs)** across 11 phases — from domain entities through REST API, MCP server, Electron GUI, pipeline engine, and market data expansion — with a disciplined TDD-first approach that prevents the common failure modes of AI-generated code.

**Key principle:** AI agents are powerful but not autonomous. They require structured instructions, adversarial review, human decision gates, and continuous calibration through reflections to produce production-quality software.

---

## 2. Feature Research & Deep Prompt Engineering

### Philosophy

Before any code is written, features go through a structured research phase. The goal is to transform engineering problems into **agentic AI problems** — gathering reference implementations and teaching AI agents *patterns* rather than hardcoding every variation.

### Multi-Provider Deep Research

Each major feature or architectural decision begins with **custom-tailored deep research prompts** sent to multiple LLM providers. The prompts are crafted differently for each model's strengths:

| Provider | Prompt Style | Strength Leveraged |
|----------|-------------|-------------------|
| **Gemini** (Google) | Broad synthesis prompts with explicit output structure | Large context window, web-grounded reasoning, multi-source synthesis |
| **ChatGPT** (OpenAI) | Analytical prompts with reasoning-effort control | Deep reasoning (`xhigh` effort), structured report output, tool-use research mode |
| **Claude** (Anthropic) | Detailed constraint-heavy prompts with adaptive thinking | Extended thinking (up to 128K tokens), 6-step decomposition protocol, web search integration |

### Research Workflow (`/pre-build-research`)

The formal research pipeline follows six steps:

1. **Define Feature Scope** — 2-3 sentence description covering data consumed/produced, variations, and edge cases
2. **Identify Sources** — Official docs first, then GitHub reference implementations, then community patterns
3. **Extract Patterns** — Schema mappings, algorithm pseudocode, API interaction patterns from real repos
4. **Create AI Instruction Set** — Transform extracted patterns into reusable prompt templates with examples, schemas, edge cases, and validation rules
5. **Build Decision** — Classify as AI-driven (5+ references), Hybrid (1-4 references), Code-first (no prior art), or Code-first-with-AI-review (security-critical)
6. **Save Research Brief** — Persist to `docs/research/{feature-slug}/` and `pomera_notes` for cross-session retrieval

### Composite Synthesis

Results from all three providers are synthesized into a **composite research brief** that captures:

- Consensus patterns (where all providers agree)
- Unique insights (where one provider found something others missed)
- Contradictions (flagged for human resolution)
- Source-backed decisions with cited URLs and document paths

This composite synthesis becomes the authoritative input for the build plan, ensuring no single model's biases dominate the architecture.

---

## 3. Build Planning & Decision-Tracking Indexes

### The Index System

Every architectural decision, feature specification, and design choice is tracked in a hierarchy of canonical documents:

```
docs/
├── BUILD_PLAN.md                    # Hub/index — links to all phase files
├── build-plan/
│   ├── build-priority-matrix.md     # MEU ordering and dependencies
│   ├── 01-domain-layer.md           # Phase 1 spec
│   ├── 02-infrastructure.md         # Phase 2 spec
│   ├── ...                          # One file per phase
│   └── 09h-pipeline-markdown.md     # Sub-phase specs
├── execution/
│   ├── plans/                       # Per-project plan + task files
│   ├── reflections/                 # Post-execution reflection files
│   └── metrics.md                   # Session performance metrics
```

### Why Indexes Matter for AI Alignment

AI agents have **no persistent memory** across sessions. Without indexes:

- Agents re-invent decisions already made, creating contradictions
- Specifications drift as each session interprets requirements differently  
- Acceptance criteria lack traceability to original design intent

The index system solves this by providing a **single source of truth** that every agent session reads before taking action. Each decision is tagged with its source basis:

| Source Type | Meaning |
|-------------|---------|
| `Spec` | Explicitly stated in the target build-plan section |
| `Local Canon` | Documented in another canonical local file |
| `Research-backed` | Confirmed via web research against official/primary sources |
| `Human-approved` | Resolved by explicit human decision |

> **Critical rule:** `Best practice` alone is never an acceptable source. Every behavioral decision must cite a specific file, URL, or human approval.

### MEU Registry

The MEU (Manageable Execution Unit) Registry (`.agent/context/meu-registry.md`) tracks every unit of work:

- **MEU ID and slug** — unique identifier
- **Build plan matrix reference** — links to the spec section
- **Description** — what the MEU delivers
- **Status** — ⬜ planned → 🟡 in-progress → ✅ approved
- **Execution order** — dependency graph per phase

With 200+ MEUs tracked, this registry is the authoritative record of what has been built and what remains.

### Emerging Standards

The `emerging-standards.md` file captures implementation standards discovered *during* development — patterns that emerged from real failures and were codified to prevent recurrence. Each standard includes:

- Severity rating and applicability scope
- The exact failure that surfaced the standard
- Bad example (what went wrong) and good example (correct approach)
- Enforcement checklist for new work

Examples: Schema field parity for MCP tools (M1), pagination response standards (P1), bug-fix TDD protocol (G19), form guard save system (G23).

---

## 4. TDD & Anti-Practices for Agentic AI

### The Core TDD Protocol

Zorivest enforces **tests-first, implementation-after** via the Feature Intent Contract (FIC) workflow:

1. **Write FIC** — Acceptance criteria (AC-1, AC-2, ...) with source labels before any code
2. **Red Phase** — Write ALL tests first. Every AC maps to at least one test. Run tests — confirm they FAIL
3. **Green Phase** — Write minimum code to make tests pass
4. **Refactor** — Clean up while keeping tests green
5. **Quality Checks** — `pyright` (type checking) + `ruff` (linting)

### Anti-Practices Codified in AGENTS.md

The `AGENTS.md` file (the master instruction file for all AI agents) codifies hard rules that prevent common AI coding failures:

#### Test Immutability
> Once tests are written in Red phase, do NOT modify test assertions or expected values in Green phase. If a test expectation is wrong, fix the *implementation*, not the *test*.

**Why:** AI agents exhibit a strong tendency to "fix" failing tests by weakening assertions rather than fixing the code. This defeats the purpose of TDD entirely.

#### Anti-Placeholder Enforcement
> Before declaring complete, run `rg "TODO|FIXME|NotImplementedError" packages/` and resolve any matches.

**Why:** AI agents frequently leave placeholder stubs and mark tasks as complete. The anti-placeholder scan is a hard gate — no MEU can be marked done with unresolved placeholders.

#### No Vacuous Tests (Standard M6)
> Tests must fail if the bug they target is reintroduced. A test that passes regardless of the fix is vacuous.

**Why:** AI-generated tests often test the wrong thing — asserting that code runs without error rather than asserting specific behavioral outcomes.

#### Bug-Fix TDD Protocol (Standard G19)
> Bug reports ALWAYS require Red→Green TDD. Write a failing test BEFORE touching production code.

**Why:** Without this rule, AI agents jump directly from "user reports bug" to "edit production code," creating fixes with no regression guard.

#### No Scope Expansion During Execution
> If the user requests features outside the approved plan scope during execution, PAUSE and ask before proceeding.

**Why:** AI agents are eager to please and will silently expand scope, causing handoff/review misalignment and wasted review cycles.

#### Boundary Input Validation
> Python `assert` and type annotations alone are NOT acceptable runtime boundary validation. Every write surface must have an explicit Pydantic/Zod schema.

**Why:** AI agents default to `assert` statements for validation, which are stripped in optimized Python builds (`-O` flag).

---

## 5. The Dual-Agent Orchestration Model

### Agent Roles

```
┌────────────────────────────────────────────────────────────┐
│  PLANNING — Claude Opus (Antigravity IDE)                  │
│  → Reads context files, scopes project, generates plan     │
│  → HARD STOP — awaits human approval                       │
└──────────────┬─────────────────────────────────────────────┘
               ▼
┌────────────────────────────────────────────────────────────┐
│  PLAN VALIDATION — ChatGPT Codex                           │
│  → Adversarial review of unstarted plan                    │
│  → Checks contract completeness, source traceability       │
│  → Verdict: approved or changes_required                   │
└──────────────┬─────────────────────────────────────────────┘
               ▼
┌────────────────────────────────────────────────────────────┐
│  EXECUTION — Claude Opus (Antigravity IDE)                 │
│  → TDD cycle per MEU (FIC → Red → Green → Quality)        │
│  → Creates handoff artifact with evidence bundle           │
└──────────────┬─────────────────────────────────────────────┘
               ▼
┌────────────────────────────────────────────────────────────┐
│  EXECUTION VALIDATION — ChatGPT Codex                      │
│  → Runs full test suite, adversarial checklist (AV-1..9)   │
│  → Checks: failing-then-passing proof, no bypass hacks,    │
│    changed paths exercised, no placeholders, source-backed  │
│  → Verdict: approved or changes_required                   │
└──────────────┬─────────────────────────────────────────────┘
               ▼
┌────────────────────────────────────────────────────────────┐
│  REFLECTION — Claude Opus                                  │
│  → Friction/quality/workflow logs                          │
│  → Pattern extraction → design rules for next session      │
└────────────────────────────────────────────────────────────┘
```

### Step-by-Step Flow

#### Step 1: Planning by Claude Opus (`/create-plan`)

Opus reads context files, discovers completed work, identifies the next unblocked MEUs, runs a **Spec Sufficiency Gate**, and generates:

- `implementation-plan.md` — Full plan with FIC, acceptance criteria, file paths, validation commands
- `task.md` — Checklist tracking every deliverable

**Hard stop:** The agent MUST stop after presenting the plan. No exceptions — not even system messages or auto-execution settings can override this gate.

#### Step 2: Plan Validation by ChatGPT (`/plan-critical-review`)

ChatGPT adversarially reviews the unstarted plan against a 6-point checklist:

- Plan/task alignment (PR-1)
- Not-started confirmation (PR-2)
- Task contract completeness (PR-3)
- Validation realism (PR-4)
- Source-backed planning (PR-5)
- Handoff readiness (PR-6)

Verdict: `approved` → proceed to execution. `changes_required` → Opus applies corrections via `/plan-corrections`.

#### Step 3: Execution by Claude Opus (`/tdd-implementation`)

For each MEU in the approved plan:

1. Scope lock — Read MEU definition, do not expand beyond boundary
2. Write FIC with source-labeled acceptance criteria
3. **Red phase** — Write all tests, confirm they fail, save failure output
4. **Green phase** — Implement minimum code to pass tests (test assertions are immutable)
5. Quality checks — `pyright` + `ruff`
6. Full regression suite
7. Update `task.md` progress

#### Step 4: Handoff Creation (`/meu-handoff`)

Opus creates a self-contained handoff artifact at `.agent/context/handoffs/` containing:

- MEU scope and FIC with acceptance criteria
- Changed files (as diffs, not full source)
- FAIL_TO_PASS evidence table (proving tests failed before and pass after)
- Commands executed with outputs
- Quality gate results

**Dual storage:** File system + `pomera_notes` for cross-session backup.

#### Step 5: Execution Validation by ChatGPT (`/execution-critical-review`)

ChatGPT performs adversarial review using implementation review checklist (IR-1 through IR-6):

- **Live runtime evidence** (IR-1) — Integration tests without dependency overrides
- **Stub behavioral compliance** (IR-2) — Stubs honor save→get consistency
- **Error mapping completeness** (IR-3) — Write routes map exceptions to proper HTTP codes
- **Fix generalization** (IR-4) — Fixes applied to all similar locations
- **Test rigor audit** (IR-5) — Every test graded 🟢 Strong / 🟡 Adequate / 🔴 Weak
- **Boundary validation coverage** (IR-6) — Schemas exist, negative tests cover malformed input

**Maximum 2 revision cycles** per MEU. After 2 cycles, escalate to human with both agents' positions.

#### Step 6: Reflection (`/execution-session` §5)

After validation, Opus creates a reflection file with:

- **Friction Log** — What was slow, ambiguous, unnecessary, missing?
- **Quality Signal Log** — Which tests caught real bugs vs. trivial assertions?
- **Workflow Signal Log** — Was FIC useful? Was handoff right-sized?
- **Pattern Extraction** — Patterns to KEEP, DROP, and ADD
- **Next Session Design Rules** — 3-5 concrete `RULE-{N}` rules
- **Metrics** — Tool calls, time to first green, tests added, handoff score

---

## 6. Reflection-Driven Continuous Improvement

### The Reflection Feedback Loop

Reflections are not post-mortems filed and forgotten. They are **active inputs** to the next session's planning:

```
Session N Execution → Reflection File → Next Session Design Rules
                                              ↓
Session N+1 Planning ← Reads latest reflection → Applies RULE-{N} set
                                              ↓
Session N+1 Execution → New Reflection → Updated Rules
```

### Periodic Meta-Reviews (Every 10-15 MEUs)

After accumulating 10-15 MEU reflections, the `/session-meta-review` workflow performs a structured retrospective:

1. **Parse** — Segment the session into labeled turns (human prompts, agent actions, tool calls)
2. **Analyze** — Sequential thinking across 5 categories: Prompt Clarity, Context Load, Tool Efficiency, Verification Gaps, Communication Quality
3. **Research** — Validate mitigations against published best practices via web search
4. **Synthesize** — Generate improvement rules with before/after examples

### What Reflections Improve

| Area | Example Improvement |
|------|-------------------|
| **Workflow rules** | Added anti-premature-stop checkpoints after discovering agents stopped with 10+ unchecked tasks |
| **AGENTS.md** | Elevated stable reflection rules into permanent conventions |
| **Template design** | Added cache boundary markers after discovering KV cache invalidation from timestamp churn |
| **Test strategy** | Added mandatory IR-5 test rigor audits after discovering vacuous tests passing review |
| **Emerging standards** | Codified 20+ standards from real session failures |

### The Improvement Flywheel

Each reflection cycle makes the next cycle faster and higher quality. Early MEUs required 4-11 review passes; after codifying patterns from those reviews, recent MEUs average 2-3 passes. The Pre-Handoff Self-Review Protocol (7 steps addressing 10 recurring patterns) was distilled from analyzing 7 critical review handoffs spanning 37+ passes.

---

## 7. Git Commit Discipline

### Policy

- **Never auto-commit.** Agents propose conventional commit messages; humans approve.
- **Never use `--no-verify`.** Pre-commit hooks are safety nets — fix the underlying issue.
- **SSH signing** is mandatory — GPG would cause interactive prompts that hang the agent terminal.

### Workflow

The agent uses a dedicated script (`.agent/skills/git-workflow/scripts/agent-commit.ps1`) that:

1. Validates SSH signing config (fails fast if GPG would hang)
2. Checks remote URL format
3. Stages all changes
4. Runs lint + unit tests (aborts on failure)
5. Commits with `-m` flag (never opens editor)
6. Pushes to origin
7. Verifies with `git log`

---

## 8. Why Full Automation Between Agents Fails

### The Case Against Unsupervised Agent Loops

A fully automated Opus↔Codex loop (plan → validate → execute → validate → repeat) without human oversight **wastes tokens, time, and produces rework.** Here is why:

#### 1. Misalignment Amplification
When Agent A misinterprets a requirement and Agent B reviews it, B may approve a *consistently wrong* implementation because both agents share similar reasoning biases. Human review catches category errors that agent-to-agent review misses.

#### 2. Infinite Revision Loops
Without a human circuit breaker, agents can enter cycles where Codex requests changes, Opus applies them, but the "fix" introduces a new finding. The 2-cycle maximum exists because this pattern was observed in practice.

#### 3. Token Waste on Ceremony
Each agent invocation consumes context tokens re-reading AGENTS.md, workflows, context files, and handoffs. A single validation cycle can consume 50-100K tokens. Unnecessary cycles (where a human glance would have caught the issue) multiply costs.

#### 4. Scope Drift Without Guardrails
Unsupervised agents expand scope to "improve" things not in the plan. Standard G20 was created after an agent set its own review verdict to `approved` — self-approval is prohibited because the corrections agent must never be its own reviewer.

#### 5. Quality vs. Speed Tradeoff
> "Quality, wisdom, and expert-level experience metrics are above all other considerations. They must never be compromised by time pressure or expedience."

Human monitoring ensures the *right* things are being built, not just *passing* things.

### The Human-in-the-Loop Gates

| Gate | What Human Reviews |
|------|-------------------|
| Plan approval | Is the scope right? Are the MEUs properly sequenced? |
| Execution spot-checks | Is the agent following the plan or drifting? |
| Codex verdict review | Does the validation verdict make sense? |
| Commit approval | Are the changes ready for version control? |
| Merge/release | Is this deployable? |

---

## 9. Context Degradation Vigilance

### The Problem

LLMs exhibit measurable accuracy degradation as context fill increases beyond ~50% capacity. In a 1M-token context window, operating above 500K tokens produces "context rot" — subtle errors in reasoning, forgotten constraints, and hallucinated state.

### Mitigations Built Into the Workflow

| Mitigation | Implementation |
|-----------|---------------|
| **Context checkpoint at 50%** | Save state to `pomera_notes`, complete current MEU handoff, notify human |
| **Post-checkpoint recovery** | Re-read `task.md` BEFORE taking any action after truncation |
| **Context compression rules** | Test output → only failures. Code → diffs only. No full file inlining. |
| **Cache boundary markers** | `<!-- CACHE BOUNDARY -->` separates stable prefix from variable content to maximize KV cache reuse |
| **Verbosity tiers** | `summary` (~500 tokens), `standard` (~2,000), `detailed` (~5,000+) — default is `standard` |
| **JIT retrieval** | Re-read files when needed rather than keeping large tool results in memory |
| **Anti-premature-stop gates** | Physical `view_file` re-read of `task.md` forced before any completion claim |

### Practical Impact

In 3 documented incidents, agents passed quality checks and generated completion summaries with **10-16 unchecked tasks remaining.** The mandatory re-read gate (Step 6.9 in TDD workflow) was added to physically re-inject the task table into context before any handoff action.

---

## 10. Designing for LLM Evolution

### The Certainty: Models Will Change

The Zorivest framework is designed with the assumption that:

- Model capabilities will improve (better reasoning, larger context, fewer hallucinations)
- Model interfaces will change (new API parameters, deprecated features)
- Model pricing will shift (new tiers, changed rate limits)
- New providers will emerge (and old ones may sunset features)

### How the Architecture Accounts for This

#### Provider-Agnostic Workflow Design
Workflows reference **roles** (orchestrator, coder, tester, reviewer), not specific models. The mapping of role→model is a configuration choice:

| Role | Current Assignment | Could Be |
|------|-------------------|----------|
| Planner/Executor | Claude Opus 4 | Any model with extended thinking |
| Validator/Reviewer | ChatGPT Codex (GPT-5.5) | Any model with code execution |
| Researcher | Multiple (Gemini, ChatGPT, Claude) | Any model with web search |

#### Instruction-First Architecture
The `.agent/` folder contains 18 workflow files, 6 role definitions, 15 skills, and 800+ lines of emerging standards — all in plain Markdown. When a new model is assigned to a role, it reads the same instructions. No model-specific code changes are required.

#### Reflection-Based Calibration
When a model upgrade changes behavior (e.g., Claude 4 → Claude 4.6's adaptive thinking), the reflection system captures:

- What worked differently
- What rules need adjustment
- What new capabilities can be leveraged

This calibration data feeds back into the AGENTS.md and workflow updates, keeping the system aligned with current model behavior.

---

## 11. Monetization-Aware Workflow Design

### The Reality of AI Agent Economics

AI agents are increasingly being fine-tuned for monetization. Even on subscription plans, providers are tightening limits:

- **Rate limits** are being introduced or reduced
- **Context windows** may be throttled under heavy load
- **Reasoning tokens** (extended thinking, deep research) often count separately
- **Tool-use calls** may be metered differently than text generation

### How Zorivest Workflows Minimize Waste

#### Token-Efficient Handoffs
The context compression system reduces handoff size by 60-80%:

- Test output: only failures, not verbose passing test output
- Code sections: unified diffs, not full file contents
- Cache boundary: stable prefix reuses KV cache (up to 90% cost reduction)

#### Right-Sized MEUs
MEUs are scoped to be "not too small (wasted context setup) and not too large (context degradation)." Each MEU invocation pays a fixed context cost (reading AGENTS.md, workflows, context files). Too-small MEUs waste this overhead; too-large ones risk context rot.

#### Avoiding Unnecessary Agent Invocations
The 2-cycle maximum on Opus↔Codex revision loops prevents token-burning infinite loops. After 2 cycles, escalation to a human (who can often resolve the disagreement in 30 seconds) is cheaper than a third agent round-trip.

#### Structured Prompts Over Conversational
Every workflow step has explicit inputs, outputs, and stop conditions. This reduces the "conversational overhead" where agents ask clarifying questions or produce verbose explanations — both of which consume tokens without advancing the task.

#### Session Discipline
> "One project = one session. Group related tasks into a coherent project by dependency order. Do NOT chain unrelated work streams."

Starting a new session for unrelated work avoids polluting the context window with irrelevant information from a previous task.

### Forward-Looking Design Principles

1. **Measure token usage per MEU** — The metrics table tracks tool calls and prompt-to-commit time. When provider pricing changes, this data enables cost optimization.
2. **Keep instructions model-agnostic** — Don't rely on model-specific features that may be deprecated or paywalled.
3. **Prefer deterministic workflows over conversational exploration** — Structured slash commands (`/create-plan`, `/tdd-implementation`) are more token-efficient than open-ended prompts.
4. **Cache aggressively** — `pomera_notes`, handoff files, and the MEU registry serve as persistent memory that is cheaper to re-read than to regenerate.
5. **Design for graceful degradation** — If a provider's rate limit is hit, the workflow's hard-stop gates and handoff protocol allow seamless continuation in a new session.

---

## Appendix: Key File Reference

| File | Purpose |
|------|---------|
| `AGENTS.md` | Master instruction file for all AI agents |
| `.agent/workflows/create-plan.md` | Planning workflow |
| `.agent/workflows/tdd-implementation.md` | TDD execution workflow |
| `.agent/workflows/meu-handoff.md` | Handoff protocol |
| `.agent/workflows/validation-review.md` | Codex validation workflow |
| `.agent/workflows/execution-critical-review.md` | Adversarial implementation review |
| `.agent/workflows/plan-critical-review.md` | Adversarial plan review |
| `.agent/workflows/pre-build-research.md` | Research-before-build workflow |
| `.agent/workflows/session-meta-review.md` | Reflection meta-review |
| `.agent/workflows/execution-session.md` | Full session lifecycle |
| `.agent/context/meu-registry.md` | MEU tracking (200+ units) |
| `.agent/docs/emerging-standards.md` | 20+ codified implementation standards |
| `.agent/docs/context-compression.md` | Token-efficient artifact rules |
| `.agent/roles/*.md` | 6 deterministic role definitions |
| `.agent/skills/git-workflow/SKILL.md` | Agent-safe git operations |
