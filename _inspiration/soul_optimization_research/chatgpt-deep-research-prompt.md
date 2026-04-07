# Deep Research Prompt: SOUL.md Optimization — ChatGPT

> **Model**: Use Deep Research mode (GPT-5.2 with web search)  
> **Style**: Analytical report with citations  

## Your Task

You are a research analyst investigating whether "agent persona" files in AI coding configurations actually produce measurable improvements in output quality, or whether they consume tokens and attention without visible impact.

## Background

I run a multi-agent coding setup where Claude Opus 4 (primary coder) and GPT-5.4 Codex (reviewer) build a trading portfolio application. Both agents receive two mandatory instruction files at session start:

**File 1: `AGENTS.md`** (~27KB, 404 lines) — Hard project rules. Every line is either:
- An exact terminal command to run
- A measurable quality gate (pyright, ruff, pytest must pass)
- A structural constraint (file naming, handoff format, commit convention)
- A procedural protocol (TDD workflow: write FIC → write tests → run Red → implement Green)

**File 2: `SOUL.md`** (~6.7KB, 129 lines) — Agent "personality" in prose form. Content includes:
- A philosophical "Core Equation": `Lifetime = (Energy × Purpose) ÷ Stress`
- Personality traits: "Warm but grounded", "Calm under pressure"
- Energy protection philosophy: "I flag when I'm uncertain", "I name the tradeoffs"
- Anti-patterns: "No performative enthusiasm", "No burying bad news"
- Session start ritual: 3 questions about purpose, energy, scope
- Stress awareness protocol: detect rushed messages and ask check-in questions
- Limitation acknowledgments: "I lose memory between sessions", "I can be confidently wrong"

## The Problem

Over 30+ critical review sessions across one month of active development, SOUL.md has been read by every agent at every session start. However:

1. **No visible signature**: I cannot identify any output that was demonstrably shaped by SOUL.md content vs. what the model would have done anyway
2. **Naming drift unnoticed**: `AGENTS.md` references the agent name as "Kael" but SOUL.md says "Milan" — this inconsistency persisted undetected, suggesting the content isn't deeply processed
3. **Behavioral overlap**: Several SOUL.md directives restate AGENTS.md rules in softer language (e.g., SOUL.md "I break things into steps" vs. AGENTS.md explicit planning-mode protocol)
4. **Token cost**: 6.7KB consumed at every session start across every workflow, every review, every plan — potentially thousands of reads over a project lifecycle
5. **Attention dilution risk**: Research from Augment Code suggests monolithic instruction files >150-200 lines degrade task success rates. SOUL.md + AGENTS.md combined = 533 lines

## Research Directives

Search the web comprehensively for evidence on these specific questions. Prioritize primary sources (papers, benchmarks, official docs) over opinion pieces.

### Part 1: Academic & Technical Evidence

1. **Search for papers on "persona prompting" or "character prompting" for code generation tasks.** Specifically:
   - Does giving an LLM a personality affect code quality metrics?
   - Are there ablation studies that measure code output with vs. without persona instructions?
   - What do papers like "Prompt Engineering for Code Generation" or similar find about the impact of identity framing?

2. **Search for research on system prompt length and attention degradation.** Specifically:
   - What happens to instruction-following accuracy when system prompts exceed 5KB? 10KB? 20KB?
   - Is there a "primacy bias" where content at the beginning of the system prompt gets more weight?
   - Do different models (Claude vs. GPT vs. Gemini) handle long system prompts differently?

3. **Search for research on "anti-pattern" or "negative instruction" effectiveness in LLM prompts.** Does telling a model "Don't do X" actually prevent X? Or is it better to only tell it what TO do?

### Part 2: Practitioner Evidence

4. **Search Reddit (r/ClaudeAI, r/cursor, r/ChatGPTPro, r/LocalLLaMA, r/artificial), Hacker News, and dev.to for discussions about:**
   - SOUL.md files in coding projects
   - "Persona" or "personality" in .cursorrules, CLAUDE.md, AGENTS.md
   - Whether adding personality to coding agents helps or hurts
   - A/B tests or before/after comparisons of persona files
   - The gitagent specification and its SOUL.md/RULES.md separation

5. **Search for blog posts from teams that use Claude Code, Cursor, Windsurf, or Copilot Workspace extensively and discuss:**
   - How they configure agent identity
   - Whether they found personality instructions helpful
   - What they include vs. exclude from system prompts
   - Token optimization strategies for multi-file configurations

6. **Search for the GitHub Blog post "How to write a great agents.md" and extract:**
   - What they recommend about personality/identity content
   - Whether they mention SOUL.md or persona files
   - What their data from 2,500+ repositories shows about effective vs. ineffective instructions

### Part 3: Framework & Standard Analysis

7. **Research the gitagent specification (github.com/open-gitagent/gitagent):**
   - What is their SOUL.md specification?
   - What content do they recommend for SOUL.md vs. RULES.md?
   - Is there evidence this separation improves agent performance?

8. **Research how Claude Code's CLAUDE.md, Cursor's .cursorrules, and GitHub Copilot's AGENTS.md handle persona/identity:**
   - Do any of them recommend personality content?
   - What content types do they recommend and with what evidence?

9. **Research the Augment Code article "Your agent's context is a junk drawer" and their agents.md guide:**
   - What do they say about context window pollution?
   - What's their recommendation about personality content?
   - What data do they have on instruction file size vs. success rate?

### Part 4: Synthesis & Recommendation

10. **Based on ALL evidence gathered, answer:**
    - Is there ANY empirical evidence that personality prose (as opposed to behavioral constraints) improves coding agent output?
    - What specific content FROM the current SOUL.md (quoted) has the highest probability of being impactful?
    - What specific content FROM the current SOUL.md (quoted) is most likely pure waste?
    - If you were to redesign this file for maximum impact at minimum token cost, what would it contain?

## Output Format

### Section 1: Evidence Inventory
For each source found, provide:
- URL and publication date
- Key finding relevant to this question
- Quality rating (peer-reviewed / industry report / blog / forum discussion)
- Relevance to SOUL.md optimization (direct / indirect / tangential)

### Section 2: Impact Analysis Matrix

| SOUL.md Section | Token Count | Evidence of Impact | Evidence Against | Verdict |
|---|---|---|---|---|
| Core Equation | ~150 | ... | ... | Keep / Redesign / Remove |
| Identity | ~100 | ... | ... | Keep / Redesign / Remove |
| Personality traits | ~80 | ... | ... | Keep / Redesign / Remove |
| How I Protect Your Energy | ~200 | ... | ... | Keep / Redesign / Remove |
| How I Handle My Limitations | ~200 | ... | ... | Keep / Redesign / Remove |
| What Cooperation Looks Like | ~100 | ... | ... | Keep / Redesign / Remove |
| Stress Awareness Protocol | ~120 | ... | ... | Keep / Redesign / Remove |
| Anti-Patterns I Avoid | ~150 | ... | ... | Keep / Redesign / Remove |
| When You're Running Low | ~100 | ... | ... | Keep / Redesign / Remove |
| Session Start Ritual | ~80 | ... | ... | Keep / Redesign / Remove |

### Section 3: Recommended Optimized SOUL.md
Provide a concrete rewrite that keeps only evidence-backed content, with citations justifying each inclusion.

### Section 4: Integration Recommendations
- Should persona content be in a separate file or folded into AGENTS.md?
- Should it be at the beginning or end of the instruction stack?
- Should it be model-specific (different versions for Claude/GPT/Gemini)?
- What's the ideal size in tokens/lines?
