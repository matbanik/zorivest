# Deep Research Prompts — AGENTS.md Optimization

> **Purpose**: Three platform-tailored prompts to generate deep research reports on optimizing AGENTS.md for Claude Opus 4.7 and GPT-5.5. After collecting all three reports, synthesize them into a unified, upgraded AGENTS.md.

---

## Research Context (attach AGENTS.md to each)

All three prompts reference the same attached file (`AGENTS.md`). Attach it as a file upload in each platform before submitting the prompt.

---

## 1. Gemini Deep Research (use Gemini 3.1 Pro)

> **Why Gemini**: Best at multi-source reasoning, structured data analysis, and real-time web retrieval. It will produce the most comprehensive cross-referenced report with cited sources.

### How to Submit
1. Open [gemini.google.com](https://gemini.google.com) → select **Deep Research** mode
2. Attach `AGENTS.md` as a file
3. Paste the prompt below
4. **Review the research plan** before it starts — add keywords like "Claude Opus 4.7 release notes", "GPT-5.5 Spud agentic capabilities", "context engineering 2026"
5. Let it run (2-5 min), then export as PDF/Markdown

### Prompt

```
You are a senior AI infrastructure architect specializing in agentic coding systems and prompt engineering. I need a comprehensive research report to modernize my AGENTS.md — the master instruction file that governs AI coding agents working on my Python/TypeScript monorepo (Zorivest).

## Attached File
- AGENTS.md — current production agent instructions (423 lines). Read it fully before researching.

## Research Objective
Produce a structured report with concrete, actionable recommendations for optimizing AGENTS.md to leverage the latest capabilities of these two frontier models:

1. **Anthropic Claude Opus 4.7** (released April 16, 2026)
2. **OpenAI GPT-5.5 "Spud"** (released April 23, 2026)

## Research Questions (investigate ALL)

### A. Model-Specific Capabilities
1. What are the confirmed new capabilities of Opus 4.7 vs Opus 4.6? (vision, effort levels, tokenizer changes, task budgets, agentic improvements)
2. What are the confirmed new capabilities of GPT-5.5 vs GPT-5.4? (reasoning effort, token efficiency, agentic planning, context window behavior)
3. What are the official prompt engineering guidelines from Anthropic and OpenAI for these specific models? Cite primary sources (anthropic.com, openai.com, docs pages).

### B. Agentic Coding Optimization (2026 State of the Art)
4. What is "context engineering" and how does it differ from prompt engineering? How should AGENTS.md adapt?
5. What are the current best practices for structuring system prompts for autonomous, multi-step coding agents? (from Anthropic's Claude Code docs, OpenAI's Codex docs, community research)
6. How should instruction hierarchy work in 2026? (system prompt vs AGENTS.md file vs inline context)
7. What is the recommended approach for effort/reasoning level control across different task types?

### C. Specific AGENTS.md Sections to Evaluate
For each section of the attached AGENTS.md, assess:
8. **Priority Hierarchy & P0 rules** — Are environment stability constraints still the right framing? Any model-specific improvements?
9. **Operating Model (PLANNING/EXECUTION/VERIFICATION)** — Does Opus 4.7 or GPT-5.5 enable a different mode structure?
10. **TDD Protocol & FIC workflow** — Any model-specific optimizations for test-first workflows?
11. **Dual-Agent Workflow** — The current reviewer is GPT-5.4. Should it upgrade to GPT-5.5? What changes?
12. **Context Compression Rules** — With updated tokenizers, should compression thresholds change?
13. **Handoff Protocol** — Any improvements for session continuity with new model features (task budgets, etc.)?

### D. Anti-Patterns to Flag
14. Identify any instructions in AGENTS.md that may be counterproductive with Opus 4.7 or GPT-5.5 (over-constraining, redundant scaffolding, deprecated patterns).
15. Are there any new failure modes these models introduce that AGENTS.md should guard against?

## Output Format
Structure the report as:
1. **Executive Summary** (300 words max)
2. **Model Capability Matrix** (table comparing Opus 4.6→4.7 and GPT-5.4→5.5)
3. **Section-by-Section Recommendations** (for each AGENTS.md section)
4. **New Sections to Add** (capabilities not currently addressed)
5. **Anti-Patterns & Deprecations** (things to remove or change)
6. **Priority Implementation Roadmap** (ordered by impact)

Cite all sources. Prefer official documentation over blog posts.
```

---

## 2. ChatGPT Deep Research (use GPT-5.5)

> **Why ChatGPT**: Best at synthesizing agentic ecosystem patterns, structured workflows, and practical implementation guidance. It will produce the most actionable, workflow-oriented recommendations.

### How to Submit
1. Open [chatgpt.com](https://chatgpt.com) → select **Deep Research** mode
2. Attach `AGENTS.md` as a file
3. Paste the prompt below
4. **Answer any clarifying questions** the research agent asks — this is high-leverage
5. Review the research plan before it begins

### Prompt

```
I need you to conduct deep research on how to optimize my AI agent instruction file (AGENTS.md, attached) for the latest frontier models: Claude Opus 4.7 and GPT-5.5.

## Context
Zorivest is a trading portfolio management application built as a Python/TypeScript hybrid monorepo. The attached AGENTS.md is the master instruction file that governs all AI coding agents working on this codebase. It covers:
- Priority hierarchy (P0 environment stability → P3 speed)
- Three operating modes: PLANNING, EXECUTION, VERIFICATION
- Six deterministic roles: orchestrator, coder, tester, reviewer, researcher, guardrail
- TDD-first workflow with Feature Intent Contracts (FICs)
- Dual-agent workflow (implementation by Claude Opus, validation by GPT Codex)
- Windows PowerShell environment constraints
- Quality gates, handoff protocols, and context compression

## What I Need

### Part 1: GPT-5.5 Optimization
Research and recommend specific changes to AGENTS.md that leverage GPT-5.5's new capabilities:
- How should reasoning effort levels (low/medium/high/xhigh) map to our PLANNING/EXECUTION/VERIFICATION modes?
- GPT-5.5 is described as "goal-oriented, not step-oriented" — which sections of AGENTS.md are over-prescriptive and should be simplified to outcome-based instructions?
- How should the Dual-Agent Workflow section change now that GPT-5.5 is available? (Currently uses GPT-5.4 as reviewer)
- What prompt caching strategies should we adopt for the recurring system prompt + AGENTS.md context?
- Are there any GPT-5.5 specific features (task budgets, improved tool use) we should explicitly reference?

### Part 2: Claude Opus 4.7 Optimization
Research and recommend specific changes for Opus 4.7:
- The new `xhigh` effort level — where should it be used in our workflow?
- Updated tokenizer (1.0-1.35x more tokens) — how should this affect our context compression rules and verbosity tiers?
- Enhanced vision capabilities — any new testing or verification opportunities?
- Task budgets (public beta) — how should we integrate them into the MEU execution workflow?
- Opus 4.7 is "more literal" — which AGENTS.md instructions need to be more precise to avoid over-constrained responses?

### Part 3: Cross-Model Architecture
- How should AGENTS.md handle model-specific instructions? Should there be conditional sections per model?
- What is the 2026 best practice for "context engineering" in agentic coding systems?
- Are there any new anti-patterns we should add to guard against?
- How do other production agentic systems (Claude Code, Cursor, Windsurf, Codex) structure their agent instructions?

## Output Requirements
- Provide specific, line-level recommendations (reference section headers from AGENTS.md)
- For each recommendation: state the source (official docs, community consensus, or your analysis)
- Include a priority ranking (Critical / High / Medium / Low)
- Include concrete "before → after" text examples for the top 5 changes
- End with a migration checklist I can follow

Search OpenAI's official documentation, Anthropic's documentation, developer forums, and recent (2026) technical blogs for the most current guidance.
```

---

## 3. Claude Research (use Opus 4.7)

> **Why Claude**: Best at precision analysis of long documents, nuanced instruction-following, and identifying subtle logical conflicts. It will produce the most thorough internal-consistency review and the most precise rewrite suggestions.

### How to Submit
1. Open [claude.ai](https://claude.ai) → activate **Research** mode (below chat input)
2. Attach `AGENTS.md` as a file
3. Paste the prompt below
4. Let it run its multi-source research loop
5. After the report, follow up: "Now identify any internal contradictions or redundancies in AGENTS.md that your recommendations would resolve"

### Prompt

```
<role>
You are an expert in AI agent system design, prompt engineering, and context engineering for autonomous coding workflows. You have deep expertise in both Anthropic's Claude model family and OpenAI's GPT model family.
</role>

<context>
I maintain AGENTS.md — the master instruction file governing AI coding agents in the Zorivest monorepo (Python domain/infra + planned TypeScript API/UI/MCP layers). The file is attached.

The system uses a dual-agent workflow:
- Primary implementor: Claude Opus (currently 4.6, upgrading to 4.7)
- Validation reviewer: OpenAI GPT (currently 5.4, evaluating upgrade to 5.5)

Key architectural patterns in AGENTS.md:
- Priority hierarchy (P0-P3) with P0 = environment stability
- Three operating modes (PLANNING → EXECUTION → VERIFICATION)
- FIC-based TDD (Feature Intent Contract → Red → Green → Refactor)
- MEU-scoped work units with quality gates
- Context compression rules for handoff artifacts
- Pre-handoff self-review protocol distilled from 37+ review passes
</context>

<task>
Conduct deep research and produce a comprehensive optimization report for AGENTS.md targeting two model upgrades:

## 1. Claude Opus 4.7 Optimization (Primary — this is the implementor model)

Research the following from Anthropic's official sources, release notes, and developer community:

a) **Effort Level Strategy**: Opus 4.7 introduces `xhigh` effort between `high` and `max`. Map each AGENTS.md operating mode to the optimal effort level:
   - PLANNING mode → ?
   - EXECUTION mode → ?
   - VERIFICATION mode → ?
   - Complex debugging → ?

b) **Tokenizer Impact**: The updated tokenizer maps text to ~1.0-1.35x more tokens. Analyze our Context Compression Rules section and recommend threshold adjustments. Currently we target:
   - Handoff verbosity: ~2,000 tokens (standard tier)
   - known-issues.md: < 100 lines
   - current-focus.md: < 30 lines

c) **Task Budgets**: Opus 4.7 has task budgets in public beta. How should this integrate with our MEU execution workflow? Should the anti-premature-stop rule be updated?

d) **Literalness Calibration**: Opus 4.7 is described as "more literal and precise." Audit the AGENTS.md for:
   - Instructions that rely on implicit understanding (may break)
   - Vague directives that should be sharpened
   - Over-specified procedures that the model will follow too rigidly

e) **Enhanced Vision**: Can we leverage improved vision capabilities for any testing or verification workflows?

## 2. GPT-5.5 Optimization (Secondary — this is the reviewer/validator model)

Research from OpenAI's official sources:

a) **Reviewer Upgrade**: Currently locked at GPT-5.4. What specific improvements does 5.5 bring to the validation/review workflow? Should the Dual-Agent Workflow section update?

b) **Reasoning Effort for Review**: GPT-5.5 has adjustable effort levels. What level is optimal for adversarial code review?

c) **Goal-Oriented Architecture**: GPT-5.5 is designed for outcome-based instructions. Which sections of AGENTS.md's reviewer/tester role specs should shift from procedural to outcome-based?

## 3. Cross-Cutting Concerns

a) **Context Engineering vs Prompt Engineering**: How should AGENTS.md evolve from a "prompt" to a "context protocol"? What structural changes are recommended?

b) **Internal Consistency Audit**: Identify any contradictions, redundancies, or stale references in the current AGENTS.md that should be resolved during this upgrade.

c) **Missing Guardrails**: Are there new failure modes introduced by Opus 4.7 or GPT-5.5 that AGENTS.md should guard against?

d) **Prompt Caching**: Both models support prompt caching. How should AGENTS.md be structured to maximize cache hits across sessions?
</task>

<output_format>
Structure your report as:

1. **Opus 4.7 Changes** — organized by AGENTS.md section, with specific text edits
2. **GPT-5.5 Changes** — organized by AGENTS.md section, with specific text edits
3. **Structural Refactoring** — cross-cutting changes to the document's architecture
4. **Internal Consistency Fixes** — contradictions and redundancies found
5. **New Sections Needed** — capabilities not currently addressed
6. **Risk Assessment** — what could break during migration

For each recommendation:
- Quote the current AGENTS.md text
- Provide the recommended replacement
- Cite the source (official docs URL, release notes, or community consensus)
- Rate priority: 🔴 Critical | 🟡 High | 🟢 Medium | ⚪ Low
</output_format>
```

---

## Post-Research Synthesis Workflow

After collecting all three reports:

1. **Save each report** to `p:\zorivest\.agent\context\` as:
   - `deep-research-gemini-agents-optimization.md`
   - `deep-research-chatgpt-agents-optimization.md`
   - `deep-research-claude-agents-optimization.md`

2. **Provide all three** to your primary coding agent with this synthesis prompt:
   > "I have three deep research reports on optimizing AGENTS.md for Opus 4.7 and GPT-5.5. Synthesize them into a unified set of changes. Where reports agree, implement directly. Where they conflict, flag for my decision. Produce a diff-based migration plan."

3. **Review and approve** the synthesized changes before applying.
