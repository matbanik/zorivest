# Deep Research Prompts — Agentic AI Artifact Standardization

> **Purpose:** Gather latest (2025–2026) best practices for standardizing execution artifacts (plans, tasks, handoffs, reflections, reviews) in multi-agent software engineering workflows. Results will inform template design for a dual-agent (Opus implementation + Codex validation) monorepo build system.
>
> **Context for all prompts:** We run a structured agentic development workflow where:
> - An "implementation agent" (Claude Opus) writes code via TDD, produces handoff artifacts
> - A "validation agent" (GPT-5.4 Codex) reviews handoffs adversarially, produces review artifacts
> - Both agents share a filesystem of markdown artifacts: implementation plans, task trackers, MEU (Manageable Execution Unit) handoffs, meta-reflections, and critical review reports
> - Artifacts serve as the sole communication channel between agents (no shared memory/context)
> - The system has produced 333 handoffs, 49 plans, 44 reflections over 30 days — consistency has degraded

---

## Prompt 1 — Gemini Deep Research

> **Angle:** Industry patterns, open-source frameworks, and Google/DeepMind research on structured agent communication

```
I'm designing a standardized template system for execution artifacts in a multi-agent
software engineering pipeline. I need a comprehensive research report covering:

## 1. Structured Agent Communication Protocols (2025-2026)

Research the latest developments in how AI coding agents communicate work state
to each other through structured artifacts. Specifically:

- How do frameworks like AutoGen, CrewAI, LangGraph, OpenHands, SWE-agent,
  Devin, and Codex structure their inter-agent handoff artifacts?
- What metadata schemas (YAML frontmatter, JSON-LD, structured headers) are
  used for machine-parseable agent artifacts?
- Are there emerging standards for "agent work products" — the equivalent of
  CI/CD pipeline artifacts but for agentic workflows?
- How do Google's Gemini agents (Jules, Gemini Code Assist) structure their
  internal work tracking and handoff documents?

## 2. Artifact Template Design Patterns

- What makes an artifact template "agent-friendly" vs "human-friendly" — and
  how do leading systems balance both?
- How do teams prevent template drift when agents produce hundreds of artifacts
  over weeks? (Our system produced 333 handoffs in 30 days and consistency degraded.)
- What validation/linting approaches exist for agent-produced markdown artifacts?
- How should templates handle appendable sections (e.g., review rechecks that
  get appended to the same document over multiple passes)?

## 3. TDD Evidence Chains in Agentic Systems

- How do agentic TDD systems capture and structure Red→Green evidence?
- What are best practices for FAIL_TO_PASS evidence formats?
- How do dual-agent review systems (builder + reviewer) structure their
  review handoff artifacts?
- What acceptance criteria formats are most effective for agents to
  verify programmatically?

## 4. Meta-Reflection and Self-Improvement Artifacts

- How do agentic systems structure post-execution reflections for continuous
  improvement?
- What patterns exist for extracting and propagating "design rules" from
  one session to the next?
- How do systems like Devin, Cursor, and Windsurf track and reuse lessons
  learned across sessions?

## 5. Scale and Organization

- At what artifact volume do flat-file approaches break down? What indexing
  or registry patterns help?
- How do systems handle artifact naming conventions that encode metadata
  (date, sequence, build-plan references)?
- What's the state of the art for agent-searchable artifact repositories?

Please provide specific examples, code/markdown snippets, and links to
repositories or papers where available. Prioritize 2025-2026 sources.
```

---

## Prompt 2 — ChatGPT Deep Research

> **Angle:** OpenAI ecosystem patterns, Codex agent workflows, practical template engineering

```
I need deep research on how modern AI coding agent systems (2025-2026)
standardize their execution artifacts for multi-agent workflows. This is
for a real production system where two agents collaborate:

- Agent A (Claude Opus 4.6) implements features via TDD and produces
  "handoff" markdown documents
- Agent B (GPT-5.4 Codex) reviews those handoffs adversarially and
  produces "critical review" documents  
- Both share only a filesystem — no shared memory or conversation context
- Artifacts must be self-contained enough for each agent to understand
  without the other's reasoning history

## Research Areas

### A. Codex and Similar Agent Handoff Formats

1. How does OpenAI's Codex agent (the autonomous coding agent, not the
   API) structure its internal work artifacts when working on tasks?
2. What artifact formats does Codex produce for task completion evidence?
3. How do Codex tasks handle the equivalent of "acceptance criteria" —
   what format are they in?
4. How does the Codex review/feedback loop work structurally — what does
   the handoff artifact between "I completed work" and "review feedback"
   look like?

### B. YAML Frontmatter Standards for Agent Artifacts

1. What YAML frontmatter schemas are emerging for AI agent work products?
2. Are there any standard field sets (status, agent, date, scope) that
   multiple frameworks converge on?
3. How do systems make frontmatter machine-queryable while keeping
   documents human-readable?
4. What field types should be enums vs free-text for optimal grep/filter?

### C. Implementation Plan Structuring

1. How do leading agentic coding systems structure implementation plans
   that agents will follow?
2. What makes a plan "executable by an agent" vs "readable by a human"?
3. How are plans decomposed into units of work (our "MEUs") and what
   metadata tracks dependencies between them?
4. What task table formats are most effective? (We use:
   `| # | Task | Owner Role | Deliverable | Validation | Status |`)

### D. Review and Audit Trail Artifacts  

1. How do AI code review systems structure their findings?
2. What severity classification schemes are used?
3. How are multi-pass reviews (initial review → recheck → recheck 2)
   structured in a single document vs multiple documents?
4. What "verdict" formats work best for downstream automation
   (approved/changes_required/blocked)?

### E. Anti-Drift Mechanisms

1. When an agent system produces 300+ artifacts, what mechanisms prevent
   structural drift from templates?
2. Are there "artifact linters" or "template validators" that check
   agent-produced documents against a schema?
3. How do systems detect when an agent is deviating from the expected
   format and course-correct?

Provide concrete examples, markdown snippets, and references to actual
implementations. Prioritize practical patterns over theoretical frameworks.
```

---

## Prompt 3 — Claude Deep Research

> **Angle:** Anthropic's perspective on agent reliability, contract-based handoffs, self-improvement loops

```
I'm building a template standardization system for a dual-agent software
engineering workflow and need research on the latest (2025-2026) practices
in agentic AI artifact design. The system has two agents that communicate
solely through markdown files on a shared filesystem:

- Implementation agent: writes code via TDD, produces structured handoff
  artifacts with acceptance criteria, test evidence, and design decisions
- Validation agent: reviews handoffs adversarially, produces structured
  review findings with severity ratings and verdicts
- A human orchestrator approves/rejects at key gates

The system has produced 333+ handoffs over 30 days and we're seeing
format drift, competing templates, and inconsistency.

## Research Questions

### 1. Contract-Based Agent Communication

How should agents structure artifacts when they are the SOLE communication
channel between two agents with no shared context?

Specifically:
- What is the minimum viable metadata an artifact needs for a receiving
  agent to understand scope, status, and required action without any
  conversation history?
- How do systems like Anthropic's internal agent pipelines, Claude Code,
  or multi-agent Claude deployments structure handoff documents?
- What are the failure modes when handoff artifacts lack structure?
  (We've observed: claim-to-state drift, evidence staleness,
  fix-specific-not-general patterns)
- How should "Feature Intent Contracts" (acceptance criteria documents)
  be structured for maximum verifiability by a reviewing agent?

### 2. Appendable vs Versioned Artifacts

Our review artifacts currently grow unbounded (up to 70KB) as rechecks
are appended. Research:
- Should review documents be append-only with dated sections, or should
  each pass be a separate versioned file?
- What are the tradeoffs of a single growing document vs a chain of
  linked documents?
- How do CI/CD and DevOps audit trail systems handle multi-pass reviews?
- At what size do single-document artifacts become counterproductive for
  agent consumption (context window efficiency)?

### 3. Self-Improving Template Systems

- How do agentic systems detect and correct template drift over time?
- What "meta-reflection" formats are most effective for extracting
  reusable rules from execution sessions?
- How should design rules propagate from reflections to future sessions?
  (We use a "Next Session Design Rules" section in reflections)
- Are there examples of agents that evolve their own template formats
  based on observed friction?

### 4. Structured Evidence and Traceability

- What formats best capture TDD Red→Green evidence chains?
- How should test mapping tables (acceptance criterion → test function)
  be structured for both human scanning and agent verification?
- What "evidence bundle" formats do CI/CD-adjacent systems use?
- How do systems handle "pre-existing failures" that are not related
  to the current work but appear in test output?

### 5. Agent-Native Document Design Principles

Research document design principles specifically for agent consumption:
- Token efficiency: how to maximize information density per token
- Scanability: what section ordering lets agents find key info fastest
- Deterministic parsing: what formatting choices enable reliable
  extraction (vs ambiguous formats that cause hallucination)
- Dual-audience: how to serve both agent parsing and human review
  in the same document

### 6. Real-World Multi-Agent Artifact Systems

Find and analyze any real-world examples of:
- Multi-agent development pipelines with documented artifact standards
- Open-source projects that use structured agent handoffs
- Research papers on agent communication via shared documents
- Industry blog posts about standardizing AI agent outputs

For each example found, describe:
- The artifact format used
- What worked well
- What failed or was abandoned
- Key design decisions and their rationale

Provide specific markdown examples, schema snippets, and citations
where available. I'm looking for practical wisdom, not theoretical
frameworks.
```

---

## Usage Instructions

1. **Gemini Deep Research**: Paste Prompt 1 into Gemini with Deep Research mode enabled. It targets industry landscape and framework patterns.

2. **ChatGPT Deep Research**: Paste Prompt 2 into ChatGPT with Deep Research / web browsing enabled. It targets practical template engineering and OpenAI ecosystem patterns.

3. **Claude Web Research**: Paste Prompt 3 into Claude with web search enabled (claude.ai extended thinking + web). It targets reliability engineering, contract design, and self-improvement loops.

The three prompts are designed to minimize overlap while maximizing coverage:
- **Gemini** → breadth across frameworks + Google ecosystem
- **ChatGPT** → depth on practical anti-drift + OpenAI/Codex patterns  
- **Claude** → depth on reliability + contract design + self-improvement

Paste all three results back and I'll synthesize them into the final template designs.
