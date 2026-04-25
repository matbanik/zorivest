# Deep Research Prompts: Agent Instruction Usage Tracking & Optimization

## Research Objective

Design a system where an AI coding agent **records which sections of its instruction set it actually uses** during each execution session, producing a reflection document. The accumulated data enables:
1. **Reordering** — move most-used instruction lines to the top of files (primacy bias optimization)
2. **Pruning** — remove instructions that are never triggered across N sessions
3. **Continuous refinement** — data-driven instruction set evolution

---

## Background: Model Capabilities (April 2026)

| Platform | Model | Deep Research Feature | Key Strengths |
|----------|-------|----------------------|---------------|
| **Gemini** | Gemini 3.1 Pro via `deep-research-max` | Interactions API, collaborative planning, MCP connectors, native charts | Multi-source web synthesis, plan editing, BYOD file upload |
| **ChatGPT** | GPT-5 (unified reasoning) | Deep Research mode, integrated connectors (Gmail, files, calendar) | Smart reasoning routing, conversational precision, zero-shot capability |
| **Claude** | Opus 4.6 (extended thinking) | Adaptive thinking, 128K thinking budget, web search (research action) | Contract-style prompting, XML semantic boundaries, long-context placement |

### 2026 Prompting Paradigm Shift

The field has moved from **"prompt engineering"** to **"context engineering"**:

- **Stop scripting reasoning** — models have built-in CoT; don't say "think step-by-step"
- **Write specs, not conversations** — treat prompts as technical contracts
- **Use semantic boundaries** — XML tags (`<context>`, `<data>`, `<instructions>`) or Markdown headers
- **Placement matters** — critical instructions at top and bottom; bury nothing important in the middle
- **Reactive prompting** — start minimal, add rules only when specific failures are observed
- **Test absence** — if removing a rule doesn't degrade performance, it was noise

---

## Prompt 1: Gemini Deep Research Max

> **Where to use:** Gemini → Deep Research Max mode  
> **Why this model:** Best at multi-source web synthesis with plan editing. Will search 50+ sources, synthesize patterns across GitHub repos, blog posts, and documentation, and produce a structured report with citations.  
> **How to use:** Paste the prompt below. When Gemini shows the research plan, review and edit it to ensure it covers all subtopics. Upload AGENTS.md as a reference file.

```
<role>
You are a senior AI infrastructure researcher specializing in LLM agent observability, prompt optimization, and instruction-set lifecycle management.
</role>

<context>
I maintain a complex AI coding agent instruction set for a Python/TypeScript monorepo called Zorivest. The instructions are distributed across multiple files:

INSTRUCTION SURFACE AREA:
├── AGENTS.md (root — ~9,000 words, primary system prompt injected via IDE)
├── .agent/
│   ├── workflows/ (15 files — slash-command-invoked procedural guides)
│   │   ├── create-plan.md, execution-session.md, tdd-implementation.md
│   │   ├── plan-critical-review.md, execution-critical-review.md
│   │   ├── meu-handoff.md, orchestrated-delivery.md, pre-build-research.md
│   │   ├── validation-review.md, e2e-testing.md, gui-integration-testing.md
│   │   ├── plan-corrections.md, execution-corrections.md
│   │   ├── security-audit.md, session-meta-review.md
│   ├── roles/ (6 files — behavioral specs adopted inline by the agent)
│   │   ├── orchestrator.md, coder.md, tester.md
│   │   ├── reviewer.md, researcher.md, guardrail.md
│   ├── skills/ (8 directories — on-demand capability extensions)
│   │   ├── terminal-preflight/, git-workflow/, quality-gate/
│   │   ├── backend-startup/, ci-troubleshooting/, e2e-testing/
│   │   ├── pre-handoff-review/, session-meta-review/
│   ├── docs/ (8 files — architecture, testing strategy, domain model, etc.)
│   ├── context/ (session state, handoffs, MEU registry, known issues)
│   └── rules/ (currently empty — rules live in AGENTS.md)

PROBLEM:
Over months of iterative development, these files have grown organically. I suspect:
- Many rules in AGENTS.md are redundant (the model already behaves that way)
- Some workflow steps are never invoked
- Instruction ordering doesn't reflect actual usage frequency
- Some rules contradict each other or create unnecessary cognitive load
- The total instruction budget (~50K+ tokens when all files are loaded) may be causing attention dilution

I want to build a system where the AI agent RECORDS which instructions it references during each execution session, producing a reflection log. Over time, this data will drive reordering (most-used to top) and pruning (remove never-used rules).
</context>

<task>
Conduct comprehensive research on the following questions, synthesizing findings from academic papers, GitHub repositories, blog posts, official AI company documentation, and community discussions:

1. INSTRUCTION COVERAGE TRACKING
   - What methods exist for tracking which system prompt instructions an AI agent actually uses during execution?
   - How are teams implementing "instruction reflection" or "rule citation" in agentic coding workflows?
   - What observability platforms (Langfuse, LangSmith, Helicone, Braintrust, etc.) support instruction-level tracing?
   - Are there any open-source projects that implement instruction usage logging for AGENTS.md or similar config files?
   - How does DSPy or similar frameworks handle automated instruction optimization?

2. INSTRUCTION REORDERING & PRUNING
   - What research exists on positional bias in LLM instruction following (primacy/recency effects)?
   - What are proven strategies for reordering system prompt sections to maximize adherence?
   - How do teams identify and safely remove unused instructions without regression?
   - What is the "golden test set" approach and how is it applied to prompt regression testing?
   - What is the optimal instruction density (tokens per rule) before attention dilution occurs?

3. SELF-REFLECTION DOCUMENT DESIGN
   - What schema or format should the reflection document use? (JSON, YAML, structured markdown?)
   - How should instruction references be granular enough to be useful but not so verbose they waste tokens?
   - What metadata should accompany each citation (timestamp, task type, mode, confidence)?
   - How can multiple sessions' reflection data be aggregated for trend analysis?

4. IMPLEMENTATION PATTERNS
   - What are concrete examples of teams adding "instruction tracing" to their AI coding agents?
   - How do Cursor, Windsurf, Cline, Aider, or similar tools handle instruction optimization?
   - Are there meta-prompting techniques where the model audits its own instruction set?
   - What role does A/B testing play in instruction optimization?

5. RISKS AND FAILURE MODES
   - What are the risks of aggressive instruction pruning (Goodhart's Law applied to prompts)?
   - How do you prevent the model from gaming the reflection log (reporting rules it didn't actually use)?
   - What safeguards prevent removing a rarely-used but critical safety rule?
</task>

<output_format>
Produce a structured research report with:
- Executive summary (key findings and recommendations)
- Detailed findings per research question (with citations)
- A recommended reflection document schema
- A step-by-step implementation roadmap
- A comparison table of observability tools for instruction tracing
- Risks and mitigation strategies
</output_format>
```

---

## Prompt 2: ChatGPT GPT-5 Deep Research

> **Where to use:** ChatGPT → Deep Research mode (or GPT-5 with web browsing)  
> **Why this model:** GPT-5's unified reasoning engine excels at synthesizing practical implementation patterns. Its smart routing automatically determines research depth. Best for actionable, engineering-focused output.  
> **How to use:** Paste into Deep Research mode. No need to say "think step-by-step" — GPT-5 routes automatically. Be conversational but precise about deliverables.

```
I'm building an instruction optimization system for my AI coding agent. The agent uses a hierarchical instruction set:

- **AGENTS.md** (~9K words): Root system prompt with P0-P3 priority rules, session discipline, TDD protocol, execution contracts, testing requirements, and safety guardrails
- **15 workflow files**: Step-by-step procedures invoked via slash commands (e.g., /create-plan, /tdd-implementation, /execution-critical-review)
- **6 role files**: Behavioral specifications the agent adopts inline (orchestrator, coder, tester, reviewer, researcher, guardrail)
- **8 skill directories**: On-demand capability extensions (terminal-preflight, git-workflow, quality-gate, etc.)
- **8 doc files**: Architecture references, testing strategy, domain model, context compression rules
- **Context files**: Session state, handoffs, MEU registry, known issues

### The Problem
After months of organic growth, the instruction set has become bloated. I need empirical data on which instructions the agent actually references during execution. The goal is to:
1. **Track**: Have the agent produce a structured reflection document after each session listing which instruction sections it used
2. **Reorder**: Move high-frequency instructions to the top of each file (exploiting primacy bias)
3. **Prune**: Remove instructions that are never triggered across N sessions
4. **Validate**: Use a regression test suite to ensure pruning doesn't degrade behavior

### What I Need You to Research

**Part 1: State of the Art**
- How are AI coding agent teams (Cursor, Cline, Aider, Windsurf, Claude Code, Gemini CLI) currently handling instruction set optimization?
- What does the academic literature say about positional effects in long system prompts?
- Are there any open-source tools or frameworks (DSPy, DSPY, PromptBreeder, EvoPrompt, TextGrad) that automate instruction pruning?
- What do Anthropic, OpenAI, and Google officially recommend for system prompt organization and length?

**Part 2: Reflection Document Design**
- Design a concrete schema for an "instruction coverage report" that an AI agent would produce after each execution session
- What granularity level works best? (file-level, section-level, rule-level, line-level?)
- How should the agent cite instructions without wasting execution tokens on the reflection itself?
- How to aggregate data across sessions for trend analysis (heatmaps, frequency tables, decay curves?)

**Part 3: Implementation Roadmap**
- Step-by-step plan for adding instruction tracking to my existing AGENTS.md-based system
- How to build a regression test suite (golden test set) for validating prompt changes
- How to handle the "rarely used but critical" problem (safety rules that fire once a quarter)
- What metrics define success? (instruction density, adherence rate, token efficiency, task completion rate?)

**Part 4: Anti-Patterns and Risks**
- Goodhart's Law for prompts — how pruning optimizes for measurement artifacts
- The "silent rule" problem — instructions that prevent bad behavior through their presence alone
- Model-specific placement strategies (Claude prefers XML tags, GPT-5 prefers delimiters, Gemini prefers markdown)

### Output Requirements
- Structured report with clear sections matching the parts above
- Include specific tool recommendations with pros/cons
- Provide a concrete reflection document schema I can implement immediately
- Include at least one worked example of how an instruction coverage report would look for a typical coding session
- Cite all sources with URLs
```

---

## Prompt 3: Claude Opus 4.6 Extended Thinking (via Research Action)

> **Where to use:** Claude → Opus 4 with extended thinking enabled, or via `research` action on Anthropic API  
> **Why this model:** Claude's contract-style prompting and XML boundary parsing make it ideal for designing precise schemas and protocols. Its adaptive thinking will naturally calibrate depth. Best for the structural design aspects.  
> **How to use:** Use the `research` action with `thinking_budget: 64000` for maximum depth. Claude responds best to constraint-driven, specification-style prompts with XML semantic boundaries.

```xml
<purpose>
Design a production-grade "Instruction Coverage Analysis" system for a complex AI coding agent instruction set. The system must enable empirical, data-driven optimization of the agent's instruction files through continuous reflection logging and trend analysis.
</purpose>

<context>
<instruction_architecture>
The agent operates in a Python/TypeScript monorepo (Zorivest) and uses a hierarchical instruction set totaling ~50K+ tokens when fully loaded:

LAYER 1 — ALWAYS LOADED (injected by IDE as system prompt):
- AGENTS.md: ~9,000 words containing P0-P3 priority hierarchy, Windows shell patterns, architecture overview, session discipline, TDD protocol, FIC-based workflow, execution contract, planning contract, testing strategy, pre-handoff self-review checklist, and context compression rules

LAYER 2 — LOADED ON DEMAND (read via view_file when slash commands invoked):
- 15 workflow files (create-plan, tdd-implementation, execution-session, etc.)
- 6 role files (orchestrator, coder, tester, reviewer, researcher, guardrail)
- 8 skill directories with SKILL.md entry points

LAYER 3 — REFERENCE ONLY (read when agent needs architectural context):
- 8 doc files (architecture, testing-strategy, domain-model, etc.)
- Context files (current-focus, known-issues, MEU registry, handoffs)
</instruction_architecture>

<known_problems>
1. AGENTS.md has grown organically over 4+ months; suspected redundancy ~20-30%
2. Some rules may be "silent guards" — preventing bad behavior by their presence alone, making them appear unused
3. Instruction ordering doesn't reflect empirical usage frequency
4. No mechanism exists to measure instruction adherence or coverage
5. Model attention may be diluting across the full token budget
6. Some workflows (e.g., security-audit, gui-integration-testing) may be rarely or never invoked
</known_problems>

<constraints>
- The reflection system must NOT significantly increase execution token usage (budget: <500 tokens per session for the reflection log)
- Must work across multiple AI models (Claude Opus, GPT-5, Gemini 3.1 Pro)
- Must handle the "rarely used but critical" problem (safety rules, guardrail role)
- Must support both automated aggregation and human review
- Must not create perverse incentives (agent gaming the log to keep rules it "likes")
</constraints>
</context>

<research_questions>
1. EXISTING PRACTICES:
   - How do production AI coding agent teams currently track instruction adherence?
   - What patterns exist in Cursor rules, Cline memory, Aider conventions, Claude Code CLAUDE.md for instruction lifecycle management?
   - What does Anthropic's own documentation recommend for system prompt organization, length limits, and placement strategy?
   - What does OpenAI's prompt engineering guide say about instruction density and ordering?
   - What does Google's Gemini prompt documentation say about structured instructions?

2. POSITIONAL EFFECTS:
   - What peer-reviewed research exists on primacy/recency bias in LLM instruction following?
   - At what token count does instruction adherence measurably degrade?
   - How does instruction placement interact with prompt caching (Anthropic's cache, OpenAI's cached prefixes)?

3. AUTOMATED OPTIMIZATION:
   - How do DSPy, TextGrad, PromptBreeder, and EvoPrompt approach instruction optimization?
   - Can these be adapted for system prompt optimization (not just task prompts)?
   - What role does LLM-as-judge play in evaluating instruction adherence?

4. REFLECTION DOCUMENT DESIGN:
   - What schema maximizes signal-to-noise for instruction coverage data?
   - How should coverage be measured: binary (used/not-used), frequency (count), or weighted (criticality × frequency)?
   - What aggregation strategies work for cross-session trend analysis?
   - How to detect "silent guard" rules that prevent bad behavior without being explicitly cited?

5. REGRESSION TESTING:
   - How to build a "golden test set" for validating instruction set changes?
   - What metrics define instruction set health? (adherence rate, conflict count, token efficiency, task completion rate)
   - How to implement A/B testing for prompt variants?
</research_questions>

<deliverables>
1. RESEARCH SYNTHESIS: Comprehensive findings organized by research question, with citations to primary sources

2. REFLECTION SCHEMA: A concrete, production-ready schema for the instruction coverage report. Include:
   - Field definitions with types and examples
   - Granularity recommendations (section-level vs rule-level)
   - Token budget analysis (must fit in <500 tokens)
   - Cross-model compatibility notes

3. AGGREGATION PROTOCOL: How to combine N session reports into actionable insights:
   - Frequency heatmap generation
   - Decay curve analysis (instructions that were used heavily then stopped)
   - "Silent guard" detection methodology
   - Pruning safety gates

4. IMPLEMENTATION ROADMAP: Step-by-step plan for adding instruction tracking to the Zorivest agent system, including:
   - Phase 1: Manual reflection (agent produces report via meta-prompt)
   - Phase 2: Automated aggregation (script to merge reports and generate heatmaps)
   - Phase 3: Optimization loop (A/B testing instruction variants)

5. ANTI-PATTERNS CATALOG: Documented risks and mitigations for instruction pruning

6. WORKED EXAMPLE: A realistic instruction coverage report for a typical "TDD implementation" session, showing which AGENTS.md sections, workflows, roles, and skills were referenced
</deliverables>

<evaluation_criteria>
- Actionability: Can I implement the recommendations within 1-2 sessions?
- Cross-model compatibility: Works for Claude, GPT-5, and Gemini
- Token efficiency: Reflection overhead must stay under 500 tokens/session
- Safety: Must not enable removing critical safety rules
- Evidence quality: Prefer peer-reviewed research and official docs over blog posts
</evaluation_criteria>
```

---

## How to Use These Prompts

### Execution Order (Recommended)

| Step | Model | Why |
|------|-------|-----|
| 1 | **Gemini Deep Research Max** | Cast the widest net — searches 50+ sources, finds GitHub repos, blog posts, and papers you'd never find manually. Best for discovering what others are doing. |
| 2 | **ChatGPT GPT-5 Deep Research** | Synthesize Gemini's findings into a practical implementation plan. GPT-5 excels at engineering-focused, actionable output. Feed it Gemini's report as context. |
| 3 | **Claude Opus 4.6 Extended Thinking** | Design the precise schema and protocol. Claude's contract-style reasoning produces the tightest specifications. Feed it both prior reports for maximum context. |

### Cross-Pollination Strategy

After each model produces its report:
1. **Extract novel insights** from each report
2. **Feed findings forward** — paste key sections from Model N's output into Model N+1's prompt as additional context
3. **Identify contradictions** — where models disagree, that's where the interesting design decisions live
4. **Synthesize** — combine the best elements from all three into your final implementation

### File Upload Strategy

For each model, upload these files as context:
- `AGENTS.md` (always — this is the primary subject)
- One representative workflow file (e.g., `tdd-implementation.md`)  
- One representative role file (e.g., `coder.md`)
- One representative skill file (e.g., `terminal-preflight/SKILL.md`)

This gives the model concrete examples of your instruction architecture without overwhelming the context window.

---

## Appendix: Model-Specific Prompting Notes

### Gemini Deep Research Max
- **Edit the plan** — Gemini generates a research outline before executing. Review and refine subtopics.
- **Upload files** — Use BYOD to attach AGENTS.md as a reference document.
- **Expect 10-20 min** — Deep Research Max runs asynchronously and may take time.
- **Check citations** — Gemini provides source URLs; verify critical claims.

### ChatGPT GPT-5 Deep Research
- **Don't say "think step-by-step"** — GPT-5 routes reasoning automatically; explicit CoT phrases can interfere.
- **Be conversational but precise** — Define the goal, output format, and constraints clearly.
- **Use delimiters** — `###` or `"""` to separate sections of the prompt.
- **Zero-shot first** — GPT-5 is powerful enough that few-shot examples are rarely needed.
- **Iterate** — If the initial research isn't deep enough, ask follow-up questions rather than re-prompting.

### Claude Opus 4.6 Extended Thinking
- **XML tags are preferred** — Claude parses `<context>`, `<task>`, `<constraints>` tags better than markdown for structured prompts.
- **Don't script reasoning** — Extended thinking handles CoT internally; let it think.
- **Place data at top, query at bottom** — For long-context tasks, put reference material first.
- **Constraint-driven** — Claude excels when you tell it what NOT to do (inhibition principle).
- **Set thinking budget** — 64K tokens for research tasks; 32K for schema design.
