# Claude Deep Research Prompt: Adversarial Analysis & Workflow Integration Design

> **Platform**: Anthropic Claude (Opus 4.6 with extended thinking)
> **Leverage**: Deep reasoning about system design, adversarial analysis, self-referential understanding of how Claude processes context, workflow integration expertise
> **Estimated output**: 6,000–12,000 words

---

## Context: You Are Both the Subject and the Analyst

This prompt is unique because you (Claude) are one of the two agents in the system being optimized. This gives you a privileged perspective: you can introspect on how you process context, what parts of long documents you actually use for reasoning, and where your own attention degrades.

### The System

I run a dual-agent TDD development workflow:

1. **You (Claude Opus 4.6)** — the "Implementer". You receive:
   - A build plan section (1K–3K tokens)
   - Prior handoff/review findings (2K–8K tokens)
   - Workflow instructions (1K–2K tokens of AGENTS.md rules)
   - Skill instructions (500–1K tokens per invoked skill)
   - You produce: FIC (Feature Intent Contract), tests, implementation, handoff artifact (5K–15K tokens)

2. **GPT-5.4** — the "Validator". It receives:
   - Your handoff artifact (5K–15K tokens)
   - The same build plan section
   - Review workflow instructions
   - It produces: findings document (2K–8K tokens)

3. **Cycle**: Your handoff → GPT-5.4 review → findings → you read findings + fix → new handoff → GPT-5.4 re-review → ... (averaging 4–11 passes)

### The Problem

Token usage is high and review cycles are long. I want to compress inter-agent communication without degrading:
- Review accuracy (findings must catch real issues)
- Evidence integrity (test results, code diffs must be precise)
- Handoff self-containment (each artifact must be understandable without prior context)

---

## Deep Analysis Requests

### Analysis 1: Self-Referential Context Processing

Since you *are* the agent being optimized, analyze your own processing patterns:

1. **Attention distribution**: When you receive a 10K-token handoff artifact from a prior session, what sections do you actually use for decision-making? Estimate the percentage of tokens that actively influence your output vs. those you essentially skip.

2. **Redundancy tolerance**: How much of a typical handoff is redundant with information already in your system prompt (AGENTS.md rules, workflow instructions)? If the handoff repeats rules you already have, does this help (reinforcement) or hurt (attention dilution)?

3. **Format sensitivity**: Does the format of evidence matter for your reasoning? For example:
   - Full pytest output (50 lines) vs. summary "47 passed, 0 failed" — does the verbose version actually help you catch issues, or just waste tokens?
   - Full code diff vs. description of changes — when do you need the actual diff?
   - File paths repeated 20 times in an artifact vs. defined once and referenced — does repetition affect your attention?

4. **Degradation patterns**: At what artifact length does your reasoning quality visibly degrade? Is this a gradual slope or a cliff? Does it differ between:
   - Dense code content
   - Structured tables/lists
   - Narrative prose
   - Mixed content (the typical handoff)

5. **Prompt caching implications**: Given how Anthropic's prompt caching works, if the first 3K tokens of every handoff are identical (common header + workflow context), how much does this actually speed up your processing? Does cached prefix load differently in your reasoning vs. fresh tokens?

### Analysis 2: Adversarial Compression Analysis

For each compression strategy, analyze from the adversarial perspective: what could go wrong?

#### Strategy A: Template homogenization
Making all handoffs follow an identical rigid template with fixed sections.

- **Risk**: If every handoff looks identical, does the receiving agent start "pattern-matching" instead of actually reading? Could a rigid template cause agents to miss novel issues that don't fit the template structure?
- **Mitigation**: How to maintain template consistency while allowing section-level variation?

#### Strategy B: Aggressive summarization of test output
Reducing "47 passed, 3 failed: test_a, test_b, test_c" to "50 tests, 3 failures"

- **Risk**: When does losing the specific failure names degrade the reviewer's ability to correlate failures with code changes?
- **Threshold**: What level of test output detail is the minimum viable for accurate review?

#### Strategy C: Delta-based sequential handoffs
After the first full handoff, sending only changes in subsequent passes

- **Risk**: "Accumulation drift" — after 7 delta-only passes, can the reviewer still mentally reconstruct the full state? At what point does a "rebase" (full re-send) become necessary?
- **Risk**: What if a delta-format handoff is ambiguous? E.g., "Fixed the import issue" — which import? Which file?

#### Strategy D: Headroom-style compression with CCR retrieval
Compressed summary + ability to request detail expansion

- **Risk**: If the reviewer doesn't know what to expand (doesn't know what it doesn't know), critical details could be permanently hidden behind the compression barrier
- **Risk**: The retrieval step adds latency and an additional API call — at what compression ratio does this overhead cancel out the savings?

#### Strategy E: Two-tier handoffs (summary + appendix)
Short summary (2K tokens) followed by detailed appendix (8K tokens), with instruction to read appendix only if needed

- **Risk**: Will agents actually skip the appendix, or will they read it anyway "just in case"?
- **Benefit**: This naturally separates "decision-relevant" from "evidence" content

#### Strategy F: ADOL-inspired verbosity control
Handoff includes verbosity metadata: `verbosity: summary | standard | detailed`

- **Risk**: Who decides the verbosity level? The sender might under-compress; the receiver might over-request
- **Opportunity**: Can the review workflow specify verbosity per section? E.g., "test results: summary, code changes: detailed"

### Analysis 3: Workflow Integration Design

Given the existing Zorivest workflow files, design the concrete integration points for context compression:

#### File: `tdd-implementation.md` (Opus reads, implements, produces handoff)

Current handoff production (Step 8–10):
```
8. Create handoff artifact per `/meu-handoff` with:
   - FIC with AC status
   - Changed files list  
   - Test results (full output)
   - Evidence of Red→Green progression
```

**Design Question**: How should the handoff production step be modified to produce:
1. A "compressed handoff" (summary-level, optimized for reviewer's first read)
2. An "evidence bundle" (full detail, referenced but not inline)
3. A "retrieval manifest" (tells the reviewer what detail is available to expand)

Provide the exact markdown template modifications.

#### File: `critical-review-feedback.md` (GPT-5.4 reads handoff, produces findings)

Current review consumption (various steps):
```
- Read handoff + build plan section
- Correlate against acceptance criteria
- Run targeted tests to verify claims
- Produce findings with evidence
```

**Design Question**: How should the review workflow be modified to:
1. First read the compressed handoff (2K tokens)
2. Decide which sections need detail expansion
3. Request/read the evidence bundle for those sections only
4. Produce compressed findings (optimized for Opus's consumption)

Provide the exact workflow step modifications.

#### File: `meu-handoff.md` (Handoff protocol spec)

**Design Question**: How should the handoff protocol be extended to support:
1. Compression metadata (what was compressed, what algorithm/strategy)
2. Retrieval instructions (where to find expanded detail)
3. Integrity verification (how to confirm nothing critical was lost)
4. Versioning (compressed format v1, with upgrade path)

#### File: `pre-handoff-review/SKILL.md` (Self-review before handoff)

**Design Question**: Should the pre-handoff self-review include a "compression quality check"?
1. Verify that verbatim content (code, assertions) survived compression
2. Verify that summary accurately represents the detailed content
3. Verify that the retrieval manifest is complete and accessible

### Analysis 4: The "No-Tool" Baseline

Before recommending any tool (Headroom, ADOL, etc.), analyze what can be achieved with zero infrastructure:

1. **Handoff template redesign**: What's the maximum token reduction achievable by simply restructuring the handoff format?
   - Move boilerplate to a shared "handoff schema" file that both agents reference
   - Use YAML frontmatter for structured data instead of prose
   - Implement section-level verbosity (TL;DR at top, detail below)
   - Use code diff format instead of "before/after" blocks

2. **Review findings template redesign**: Similarly for findings documents
   - Structured findings format (finding ID, severity, location, evidence, recommendation)
   - Eliminate narrative that repeats the finding in different words
   - Reference line numbers instead of quoting multi-line code blocks

3. **Workflow instruction compression**: The workflow files themselves consume tokens
   - Can workflow instructions be pre-cached as a shared prefix?
   - Can conditional inclusion reduce instruction token count? (only include MEU-relevant sections)

4. **Estimated savings**: What percentage reduction is achievable through template optimization alone?

### Analysis 5: Comparative Framework Assessment

Evaluate the following tools/frameworks specifically for the Zorivest dual-agent use case:

| Tool/Approach | Fit Score (1-10) | Why | Key Risk |
|---|---|---|---|
| Headroom proxy | | | |
| Headroom SharedContext | | | |
| ACON evaluation framework | | | |
| ADOL verbosity protocol | | | |
| ContextEvolve decomposition | | | |
| Provence pruner | | | |
| Manual template optimization | | | |
| Model-native caching | | | |

For each, assign a fit score from 1–10 and explain why.

### Analysis 6: Hybrid Strategy Recommendation

Based on all analysis above, recommend a hybrid strategy that combines the best elements:

1. **Layer 0 (Immediate, zero cost)**: Template and format optimizations
2. **Layer 1 (Low cost)**: Model-native features (prompt caching, structured outputs)
3. **Layer 2 (Medium cost)**: ADOL-inspired protocol extensions to handoff format
4. **Layer 3 (Higher cost)**: Tool integration (Headroom or similar) for automated compression

For each layer, specify:
- Expected token reduction (%)
- Implementation effort (hours)
- Quality risk level (low/medium/high)
- Dependencies on other layers
- How to measure success

---

## Output Format

Structure your response as:

1. **Self-Referential Analysis** (your honest assessment of how you process handoff content)
2. **Adversarial Risk Assessment** (what could go wrong with each strategy)
3. **Workflow Integration Design** (exact modifications to existing workflow files)
4. **No-Tool Baseline** (what's achievable with format changes alone)
5. **Comparative Assessment** (scored table)
6. **Hybrid Strategy** (layered recommendation with implementation order)
7. **Critical Warnings** (things I should absolutely NOT do)

---

## Important Constraints

Whatever you recommend must respect these existing rules:
- **Pre-Edit Guard**: Review agents must NEVER directly modify implementation files
- **Canonical Review File Rule**: Findings accumulate in a single rolling file, not multiple variants
- **Evidence Integrity**: Test results and code assertions must remain verbatim (no summarization of these)
- **Self-Containment**: Each handoff must be understandable without access to prior handoffs (no "see previous artifact" references that require sequential reading)
- **Anti-Premature-Stop**: Compression must not give agents an excuse to skip thorough review
