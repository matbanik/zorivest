# Deep Research Prompts: Multi-IDE Agentic Cooperation

> **Purpose**: Three deep research prompts — one each for Gemini, ChatGPT, and Claude — targeting each platform's research strengths. The goal is to find inspiration, patterns, and automation strategies for a dual-IDE agentic coding workflow.
>
> **Date**: 2026-03-06

---

## Context Summary (Include with All Prompts)

We operate a **dual-IDE agentic coding workflow** for a Python/TypeScript monorepo called Zorivest (a trade planning & analytics platform). The workflow uses two subscription-based IDE agents — no API access due to cost:

- **Agent A** — VS Code + Codex (GPT-5.4): orchestrator, reviewer, prompt creator
- **Agent B** — Antigravity (Opus 4.6): planner, implementer, TDD executor

### Current Workflow (What We Want to Improve)

```
┌─────────────────────────────────────────────────────────┐
│ 1. Agent A (GPT-5.4) creates execution prompt           │
│    → prompt written to docs/execution/prompts/           │
│    → follows .agent/ roles, workflows, SOUL.md identity  │
└───────────┬─────────────────────────────────────────────┘
            ▼  (HUMAN copies prompt to other IDE)
┌─────────────────────────────────────────────────────────┐
│ 2. Agent B (Opus 4.6) reads prompt, enters PLANNING      │
│    → generates implementation_plan.md + task.md           │
│    → writes plan to brain folder + archives to project    │
└───────────┬─────────────────────────────────────────────┘
            ▼  (HUMAN copies plan handoff to other IDE)
┌─────────────────────────────────────────────────────────┐
│ 3. Agent A (GPT-5.4) validates the plan                  │
│    → approves OR sends correction findings                │
│    → writes validation verdict to handoff file            │
└───────────┬─────────────────────────────────────────────┘
            ▼  (LOOP until approved — HUMAN relays)
┌─────────────────────────────────────────────────────────┐
│ 4. Agent B (Opus 4.6) implements via TDD                 │
│    → FIC → Red → Green → Quality checks → Handoff        │
│    → writes implementation handoff artifact               │
└───────────┬─────────────────────────────────────────────┘
            ▼  (HUMAN copies implementation handoff)
┌─────────────────────────────────────────────────────────┐
│ 5. Agent A (GPT-5.4) validates implementation            │
│    → runs adversarial checks, banned patterns, FIC audit  │
│    → approves OR sends findings → Agent B fixes → LOOP    │
└───────────┬─────────────────────────────────────────────┘
            ▼
┌─────────────────────────────────────────────────────────┐
│ 6. Agent A creates next MEU prompt (cycle repeats)       │
│ 7. Meta-reflection on the full session                   │
└─────────────────────────────────────────────────────────┘
```

### Our Infrastructure

- `.agent/` folder with: 6 deterministic roles (orchestrator, coder, tester, reviewer, researcher, guardrail), 8 workflows, context files, docs, handoff templates
- `SOUL.md` — agent identity and operating principles
- `AGENTS.md` — vendor-neutral project conventions
- `GEMINI.md` — Antigravity-specific runtime rules
- MEU (Manageable Execution Unit) scoping system with a registry
- Handoff artifacts for inter-agent communication
- `pomera_notes` MCP server for persistent memory across sessions

### Key Constraints

- **No API access** — both agents are subscription-based IDE agents only
- **Human is the relay** between IDEs — we want to minimize human input to just "continue" commands
- **Each agent has its own brain/memory** that is not directly shared
- **The `.agent/` folder and git repo are the shared medium** — both IDEs see the same filesystem

### What We Want to Learn

1. Has anyone built a similar dual-agent, dual-IDE loop?
2. How can the human relay be minimized or automated?
3. What `.agent/` or similar standards work across different models/IDEs?
4. What rules/roles/workflows/skills patterns produce the best autonomous agent behavior?
5. How should handoff artifacts be structured for maximum inter-agent comprehension?
6. What meta-reflection and prompt-improvement loops have proven effective?

---

## Prompt 1: Gemini Deep Research

> **Platform strengths**: Google Search integration, multi-source synthesis, broad web coverage, ability to process and compare many sources simultaneously.

### Prompt

```
Use Deep Research to investigate the following topic comprehensively.

# Research Topic: Multi-IDE Agentic Cooperation Patterns (2025-2026)

## Background

[Paste the Context Summary above here]

## Research Questions

Research each of the following in depth. For each, find multiple real-world examples, open-source projects, blog posts, conference talks, and GitHub repositories.

### 1. Dual-Agent Coding Workflows Across IDEs

Find implementations where two or more AI coding agents collaborate across different IDEs or platforms. Specifically:

- Projects using VS Code + another IDE (Cursor, Windsurf, Antigravity, JetBrains AI) with different models in each
- Agent-to-agent handoff protocols that use the filesystem (not API) as the communication layer
- Any implementation of a "prompt creator agent" that generates prompts for a separate "executor agent"
- The "inner loop / outer loop" pattern where one agent reviews and another implements
- Real examples of TDD-first agent workflows where the test writer and implementer are different agents or sessions

### 2. Minimizing Human Relay Between Agents

Find approaches for reducing human involvement between two agents that cannot directly communicate via API:

- File-watching or filesystem event triggers that one IDE can use to detect when the other agent has finished
- Clipboard automation, shell scripts, or OS-level tools that shuttle text between IDE windows
- Agent-native "continue" or "auto-approve" mechanisms in VS Code Codex and/or Antigravity
- Any projects using tmux, screen, PowerShell jobs, or task schedulers to orchestrate multi-IDE sessions
- MCP servers or other tool protocols that could bridge two IDE agents through shared state
- Projects that use a shared SQLite database, Redis, or file-based queue as a message bus between agents

### 3. Universal Agent Configuration Standards

Find standards, conventions, and emerging patterns for configuring AI agents that work across multiple models and IDEs:

- The `.agent/`, `.cursor/`, `.claude/`, `.github/copilot/`, `.gemini/` folder conventions — what files go where, which are model-specific vs universal
- AGENTS.md, CLAUDE.md, GEMINI.md, .cursorrules, copilot-instructions.md — compare their structures and what each IDE actually reads
- Role-based agent systems (orchestrator, coder, reviewer, tester patterns) — who has implemented these and how
- Workflow definition formats that agents can follow deterministically (YAML frontmatter + markdown steps, JSON schemas, etc.)
- "Skill" systems where agents can discover and follow pre-written instruction sets
- Projects that use the same `.agent/` config across Claude Code, Cursor, VS Code Copilot, and/or Antigravity simultaneously

### 4. Handoff Artifact Design for Inter-Agent Communication

Research best practices for structured handoff documents between AI agents:

- What fields/sections make a handoff artifact maximally useful to the receiving agent
- Evidence bundles, test result embedding, diff inclusion — what should a handoff carry
- Feature Intent Contracts (FIC), Acceptance Criteria mapping, FAIL_TO_PASS tables — are others using these
- How to structure validation verdicts (approved / changes_required / blocked) for unambiguous agent consumption
- Serialization formats: markdown vs JSON vs YAML for agent-readable handoffs

### 5. Meta-Reflection and Prompt Evolution

Find examples of agents or humans running structured improvement loops on their prompt engineering:

- Meta-cognitive reflection protocols for AI agents (friction logs, pattern extraction, design rules)
- Prompt versioning and prompt registries — tracking which prompt produced which outcome
- Self-improving agent systems that adjust their own rules based on performance metrics
- "Prompt-to-prompt" pipelines where one session's output directly shapes the next session's input
- Quantitative prompt scoring — what metrics have proven useful (tool calls, time-to-green, findings count)

### 6. Rules, Roles, Workflows, and Skills Architecture

Research the best emerging patterns for structuring agent instructions:

- How to write effective agent rules that actually change behavior (not just aspirational guidelines)
- Role specification formats that make agents follow deterministic processes
- Workflow definition patterns that work across different AI models
- Skill discovery and invocation systems (how agents find and use pre-written capabilities)
- Guard rails and safety checks built into agent workflows
- Compare: Anthropic's tool_use patterns vs OpenAI's function calling vs Google's grounding for workflow enforcement

## Output Format

Organize your research report with these sections:

1. **Executive Summary** — 5-10 key findings and actionable takeaways
2. **Pattern Catalog** — For each pattern found, provide: Name, Source (URL), Description, Applicability to our workflow (High/Medium/Low), Implementation complexity
3. **Tool and Project Directory** — Table of all tools, projects, and frameworks discovered with links
4. **Recommended Architecture** — Based on all findings, propose an improved version of our dual-agent workflow
5. **Automation Playbook** — Specific scripts, tools, or configurations that could minimize human relay
6. **Standards Comparison Matrix** — Compare .agent/, .cursor/, .claude/, etc. conventions
7. **Further Reading** — Prioritized list of the most valuable sources for deeper exploration
```

---

## Prompt 2: ChatGPT Deep Research

> **Platform strengths**: Structured reasoning, tool-use during research (browsing + code analysis), strong at producing actionable implementation plans, good at comparing technical approaches.

### Prompt

```
I need deep research on a specific agentic coding workflow pattern.
Do extensive web browsing to find real-world examples, GitHub repos,
blog posts, and technical discussions from 2025-2026.

# Topic: Automated Dual-Agent TDD Pipeline Across Two IDE Platforms

## My Current Setup

[Paste the Context Summary above here]

## What I Need You to Research

### Part 1: Find Real Implementations (Priority)

Search for and analyze actual projects, repos, and documented workflows where:

1. **Two different AI models collaborate on the same codebase** — one creates/reviews, the other implements. Find at least 5 real examples. For each, document:
   - What models were used
   - How they communicated (API, filesystem, clipboard, shared DB)
   - What was the human's role
   - What worked well and what failed
   - Link to source

2. **Agent-to-agent handoff systems using files** — not API-based communication. Look for:
   - Projects using git as the message bus between agents
   - Markdown-based handoff protocols
   - Structured verdict files (approve/reject/fix) between agents
   - Any "agent inbox/outbox" filesystem patterns

3. **TDD workflows driven by AI agents** — specifically where:
   - Tests are written first by one agent/session, then implementation by another
   - Feature Intent Contracts or similar spec-first patterns are used
   - Red→Green evidence is captured and transferred between sessions
   - The test-writer and implementer may be different models

### Part 2: Automation Between IDEs

Search for tools, scripts, and techniques for:

1. **File-watcher based triggers** — when Agent B writes a handoff file, Agent A's IDE picks it up automatically
2. **Cross-IDE orchestration scripts** — PowerShell/bash scripts that:
   - Open a new Codex session with a specific prompt
   - Detect when an Antigravity session has produced output
   - Copy specific files between IDE brain folders
3. **MCP (Model Context Protocol) for agent bridging** — can an MCP server be the bridge between two IDE agents running on the same machine?
4. **Shared persistent memory** — solutions for two agents to read/write the same memory store (like our pomera_notes) across IDE boundaries
5. **"Continue" automation** — ways to auto-send the continue/proceed command in VS Code Codex or Antigravity without manual typing

### Part 3: Agent Configuration Best Practices

Research and compare how leading teams configure their AI agents:

1. **Agent rules that actually work** — find examples where specific rules demonstrably changed agent behavior. What format works best?
2. **Role systems** — compare approaches to role-based agent behavior:
   - Single-agent role switching (adopt orchestrator, then coder, then reviewer)
   - Multi-agent specialized roles (each agent has one role)
   - Hybrid approaches
3. **Workflow definitions** — what format do agents follow most reliably:
   - YAML frontmatter + markdown steps
   - JSON task graphs
   - Natural language with checkboxes
   - Mermaid/graph-based flow definitions
4. **Skills/capabilities** — systems where agents discover and follow instruction files:
   - Slash command conventions (/workflow-name → reads file)
   - Auto-discovery of skill files
   - Skill composition (combining multiple skills)

### Part 4: The Improvement Loop

Find approaches for:

1. **Session-over-session improvement** — systems where each build session measurably improves on the last
2. **Prompt evolution** — tracking, versioning, and iterating prompts with metrics
3. **Agent self-assessment** — structured reflection protocols that agents perform on their own work
4. **Efficiency metrics** — what numbers to track for dual-agent workflows (not just test pass rates)
5. **Human oversight optimization** — how to give humans maximum signal with minimum interaction time

## Output Requirements

Structure your report as:

1. **Top 10 Findings** — actionable, ranked by impact on our workflow
2. **Implementation Comparison Table** — for each real example found:

   | Project | Models | Communication | Human Role | TDD? | What Worked | What Failed | Link |
   |---------|--------|---------------|------------|------|-------------|-------------|------|

3. **Automation Toolkit** — specific tools, scripts, and configurations with code snippets where possible
4. **Agent Config Patterns** — comparison matrix of rules/roles/workflows/skills across different projects
5. **Proposed Improved Workflow** — given everything you found, redesign our dual-agent loop with specific improvements
6. **Quick Wins** — things we can implement today with < 1 hour of work
7. **Strategic Improvements** — things that require more effort but offer significant improvement
```

---

## Prompt 3: Claude Deep Research

> **Platform strengths**: Nuanced technical analysis, ability to identify subtle patterns and failure modes, strong at reasoning about system design trade-offs, excellent at synthesizing qualitative insights.

### Prompt

```
Use your research capabilities to investigate multi-agent cooperation
patterns in AI-assisted software development. I need a deep, nuanced
analysis — not just a list of tools, but an understanding of WHY
certain patterns work and others fail.

# Research Topic: Design Patterns for Dual-IDE Agentic Cooperation

## Context

[Paste the Context Summary above here]

## Research Directions

### Direction 1: The Communication Problem

The fundamental challenge in our workflow is that two AI agents
(GPT-5.4 in VS Code Codex and Opus 4.6 in Antigravity) need to
collaborate but cannot directly communicate. They share a filesystem
(git repo) and a human relay.

Research and analyze:

1. **Information theory of agent handoffs** — What is the minimum
   information that must cross the boundary for the receiving agent to
   act effectively? What do current handoff artifacts carry that's
   unnecessary? What's typically missing?

2. **Lossy vs lossless handoffs** — When Agent A summarizes its work
   for Agent B, what information is lost? How do teams compensate?
   Find examples of handoff formats that preserve:
   - Decision rationale (not just decisions)
   - Rejected alternatives (not just chosen paths)
   - Confidence levels (not just binary pass/fail)
   - Context that was in the agent's "head" but not in the files

3. **The "fresh context" problem** — Every time we switch IDEs, the
   receiving agent starts with zero context and must rebuild from
   files. Research:
   - Optimal "memory loading" sequences for agents starting a new session
   - Pre-loading strategies (what to read first to maximize comprehension)
   - Whether there's a measurable degradation in agent quality based on
     how context is presented (file vs inline vs system prompt)

4. **Failure modes in dual-agent systems** — Look for documented cases
   where multi-agent collaboration broke down:
   - Agents "talking past each other" due to different interpretations
   - Review loops that never converge (ping-pong findings)
   - Context drift over many handoffs
   - One agent undoing the other's work
   - Quality degradation in long chains of agent interactions

### Direction 2: The Automation Spectrum

We currently use a human relay between IDEs. Research the full spectrum
from fully manual to fully automated:

1. **Level 0: Manual relay** (our current state) — human copies
   prompts and findings between IDE windows. What practices minimize
   friction at this level?

2. **Level 1: Scripted relay** — file watchers, clipboard automation,
   shell scripts. What exists? What's reliable on Windows?

3. **Level 2: Orchestrated relay** — a coordinator process that
   monitors both IDEs and triggers actions. Has anyone built this?
   What orchestration tools work with IDE agents?

4. **Level 3: Protocol-based relay** — MCP servers, language server
   protocol extensions, or VS Code extensions that enable agent-to-
   agent communication. What's emerging?

5. **Level 4: Unified platform** — single IDEs or platforms that
   natively support multi-model collaboration within one interface.
   What exists in 2025-2026? Is this where the industry is heading?

For each level, assess: reliability, setup complexity, maintenance
burden, and whether it actually reduces human time or just shifts it.

### Direction 3: Agent Behavior Architecture

Research the emerging science of structuring agent behavior through
configuration files:

1. **Rules that stick** — What makes an agent rule actually effective?
   Research:
   - Positive rules ("do X") vs negative rules ("never do Y")
   - Specificity level (vague principles vs exact procedures)
   - Rule placement (system prompt vs file vs inline) and its effect
   - Rule fatigue — do agents stop following rules as conversations get long?
   - Which rules survive across model versions?

2. **Role effectiveness** — Compare role-based agent systems:
   - Do specialized roles actually improve output quality?
   - How many roles can one agent effectively adopt in a session?
   - What's the optimal role transition pattern?
   - "Role bleed" — when agents break character mid-role

3. **Workflow fidelity** — How reliably do agents follow structured
   workflows?
   - Step-by-step markdown instructions vs freeform goals
   - Workflow length limits (at what point do agents start skipping steps?)
   - Checkpointing and verification between workflow steps
   - Self-healing workflows (agent detects it went off-track and corrects)

4. **Skills and capabilities discovery** — Research patterns for:
   - Agent-discoverable instruction sets (skills in folders)
   - Parameterized workflows (templates with fill-in-the-blank sections)
   - Composable capabilities (combining simple skills into complex workflows)
   - Cross-model skill compatibility (does a skill written for Claude work for GPT?)

### Direction 4: The Meta-Learning Loop

Research how to make the dual-agent system improve over time:

1. **Prompt evolution patterns** — Systems where prompts measurably
   improve session after session. Find:
   - Quantitative evidence of prompt improvement
   - What metrics correlate with prompt quality
   - How many iterations until diminishing returns
   - Whether prompt improvements transfer across different models

2. **Friction log analysis** — Structured self-assessment methods:
   - Which reflection questions actually surface actionable insights?
   - Optimal reflection depth (too shallow = useless, too deep = navel-gazing)
   - How to turn reflections into concrete rule updates

3. **Dual-agent quality metrics** — What should we measure?
   - First-pass acceptance rate (Agent B's work accepted by Agent A without changes)
   - Handoff comprehension score (does Agent B understand Agent A's intent?)
   - Finding convergence rate (how quickly do review loops close?)
   - Context loading efficiency (how much does Agent B read before it can act?)

4. **Human oversight metrics** — Measuring the cost of human relay:
   - Human time per MEU session
   - Decision density (how many human decisions vs rubber-stamp continues)
   - Error introduction by human relay (typos, missing context, wrong files)

## Output Format

I want a research report structured as a design analysis, not a
feature comparison. For each direction:

1. **Current state of the art** — What exists, what works, what doesn't
2. **Trade-off analysis** — For each approach, explicit pros/cons/risks
3. **Applicability assessment** — How each finding maps to our specific
   dual-IDE, subscription-only, filesystem-mediated workflow
4. **Design recommendations** — Concrete suggestions ranked by impact/effort
5. **Open questions** — What remains unknown or under-explored

End with a **Synthesis** section that draws connections across all four
directions and proposes a coherent architecture for our dual-agent
system that balances automation, quality, and practical constraints.
```

---

## Usage Guide

### How to Use These Prompts

1. **Gemini** (breadth-focused): Use [Gemini Deep Research](https://gemini.google.com) with the full prompt. Gemini will search extensively across many sources and produce a comprehensive catalog. Best for discovering tools, repos, and patterns you didn't know existed.

2. **ChatGPT** (implementation-focused): Use [ChatGPT Deep Research](https://chatgpt.com) mode. ChatGPT will browse, analyze, and produce actionable implementation plans. Best for specific automation scripts, configuration patterns, and "do this today" recommendations.

3. **Claude** (analysis-focused): Use [Claude Research](https://claude.ai) with extended thinking. Claude will produce nuanced analysis of trade-offs, failure modes, and design principles. Best for understanding WHY patterns work and making architectural decisions.

### Combining Results

After running all three, create a synthesis document by:

1. Extract Gemini's **tool/project catalog** — the broadest net of sources
2. Take ChatGPT's **implementation recommendations** — the most actionable items
3. Use Claude's **design analysis** — the deepest understanding of trade-offs
4. Cross-reference findings that appear in 2+ research reports (high confidence)
5. Flag contradictions between reports (areas needing human judgment)

### Key Context to Paste

When pasting the Context Summary into each prompt, also attach or reference:
- This workflow diagram (the ASCII art from the Context Summary above)
- A representative handoff artifact (e.g., the MEU-1 calculator handoff)
- The `.agent/` folder listing (roles, workflows, docs)
- The execution session workflow (`execution-session.md`)
