# Your SOUL.md is likely inert — here's why

**The evidence is clear: your 129-line personality file is almost certainly consuming context tokens without modifying agent behavior.** Academic research from 2024–2026 demonstrates that persona prompting actively *damages* coding accuracy, while practitioner consensus and platform guidelines uniformly recommend against personality content in coding agent instruction files. Your observation that none of the personality-specific behaviors have manifested in 30+ sessions aligns perfectly with what the research predicts. The file should be either removed entirely or restructured into actionable, failure-backed rules.

This conclusion draws on peer-reviewed research (6 papers), data-driven industry analyses (GitHub's 2,500-repository study, Augment Code, ETH Zurich, Vercel evaluations), official platform documentation (Anthropic, Cursor, Windsurf), and dozens of practitioner reports.

---

## Strong evidence: expert personas make code generation worse

The most directly relevant research is the **PRISM paper** from USC (arXiv:2603.18507, March 2026), which studied expert persona prompting across accuracy and alignment tasks. Co-author Zizhao Hu stated bluntly: "Asking AI to adopt the persona of an expert programmer will not help code quality or utility." On MMLU, all expert persona variants damaged accuracy — the minimum persona scored **68.0% vs. 71.6% baseline**, a 3.6 percentage point drop. On coding benchmarks specifically, scores dropped by **0.65 points on a 10-point scale**. The mechanism is straightforward: persona instructions activate the model's instruction-following mode at the expense of factual recall. The model spends capacity performing the persona rather than solving the problem.

This finding is corroborated by a University of Michigan study ("When 'A Helpful Assistant' Is Not Really Helpful," arXiv:2311.10054v3, updated October 2024) that tested **162 personas across 4 LLM families and 2,410 factual questions**. The conclusion: "Adding personas in system prompts does not improve model performance across a range of questions compared to the control setting where no persona is added." Notably, the paper's original 2023 abstract claimed personas *improved* performance — after expanding the study, that conclusion **reversed entirely**.

A Seoul National University study (arXiv:2408.05631, August 2024) found persona prompting degraded reasoning abilities in **7 out of 12 datasets** for Llama3 and **4 out of 12 for GPT-4**. The researchers concluded: "Every category tested contains a dataset in which Base outperforms Persona, proving that role-playing prompts can degrade performance."

The critical distinction the PRISM paper identifies: persona content helps *alignment* tasks (tone, safety, style) but hurts *accuracy* tasks (math, coding, knowledge retrieval). Your SOUL.md's session-start rituals, stress-awareness protocols, humor directives, and core equation references are alignment-oriented instructions applied to an accuracy-oriented domain — the worst possible combination.

---

## Your instruction budget is already overcommitted

Frontier LLMs can follow approximately **150–200 instructions with reasonable consistency**, according to HumanLayer's analysis. Claude Code's own system prompt already consumes roughly **50 of those instructions**. Your AGENTS.md alone is 404 lines — likely containing 100+ discrete instructions. Adding 129 lines of SOUL.md personality content means you may be operating at **2–3x the effective instruction capacity**, guaranteeing that large portions of both files get ignored.

The degradation is not graceful. Research from the IFScale benchmark (arXiv:2507.11538, July 2025) found that Claude Sonnet exhibits **linear decay** in instruction adherence as instruction count rises — each additional instruction uniformly reduces compliance with *all* instructions, not just the new ones. A separate paper found that even when models can perfectly retrieve all relevant information, performance still degrades **13.9%–85%** as input length increases, "even when the irrelevant tokens are replaced with minimally distracting whitespace." The mere presence of tokens — regardless of content — costs you performance.

Anthropic's own CLAUDE.md documentation could not be more explicit: **"For each line, ask: 'Would removing this cause Claude to make mistakes?' If not, cut it. Bloated CLAUDE.md files cause Claude to ignore your actual instructions!"** Their recommended ceiling is **under 200 lines**. HumanLayer keeps their root CLAUDE.md to under 60 lines. Augment Code cites an ETH Zurich paper (arXiv:2602.11988, February 2026) showing context files increase inference costs by **over 20%** while providing inconsistent improvement — and on Claude Sonnet 4.5, performance actually *dropped* by over 2%.

Crucially, HumanLayer discovered that Claude Code wraps all CLAUDE.md content with a system-level instruction: "IMPORTANT: this context may or may not be relevant to your tasks. You should not respond to this context unless it is highly relevant to your task." The model is explicitly granted permission to ignore personality content it deems task-irrelevant — which is exactly what your 30+ sessions have demonstrated.

---

## What GitHub, Augment Code, and Anthropic actually recommend

**GitHub's analysis of 2,500+ agents.md files** draws a sharp line between functional persona and personality. Their key quote: "'You are a helpful coding assistant' doesn't work. 'You are a test engineer who writes tests for React components, follows these examples, and never modifies source code' does." The first is an identity claim; the second is a scope constraint with actionable boundaries. The "six core areas" that make agents.md files effective are: executable commands, code examples over explanations, clear boundaries (always/ask-first/never), specific stack declarations, testing instructions, and git workflow rules. Personality content appears nowhere in this list.

**Augment Code's "Your agent's context is a junk drawer" analysis** (February 2026) is even more pointed. They explicitly categorize "generic best practices like 'write clean code' or 'follow SOLID principles'" as noise that should be deleted, noting: "The agent was trained on the internet. It knows." They cite Andrej Karpathy's warning: "Too much or too irrelevant and the LLM costs might go up and performance might come down." Their pruning test: **"For every line, ask: does this prevent a failure the agent would actually make? If you can't point to the failure, delete the line."**

**Anthropic's official documentation** contains no mention whatsoever of personality or identity content in CLAUDE.md. Their example files are purely functional — code style rules and workflow commands. Self-evident practices like "write clean code" are explicitly placed in the "Exclude" column. The emphasis is on emphasis markers (e.g., "IMPORTANT" or "YOU MUST") for critical behavioral rules, not on narrative personality.

Vercel's evaluation data provides a compelling benchmark: they compressed 40KB of documentation into an **8KB AGENTS.md** index and achieved a **100% pass rate** across build, lint, and test evaluations. Meanwhile, their more sophisticated skill-based retrieval system achieved only 79% — and in 56% of cases, the agent never even invoked the skills. Dense, functional content in a single file beat elaborate multi-file configurations.

---

## The behaviors you're requesting already exist by default

Your SOUL.md likely includes instructions like flagging uncertainty, breaking responses into steps, avoiding performative enthusiasm, and being thorough with code. **Modern frontier models already do all of this without being asked.** Anthropic's own documentation for newer Claude models states: "If your prompts were designed to reduce undertriggering on tools or skills, these models may now overtrigger. The fix is to dial back any aggressive language." Their explicit guidance: "Remove over-prompting."

Cursor's engineering blog reveals that their RL-trained coding model "learns useful behaviors on its own like performing complex searches, fixing linter errors, and writing and executing unit tests" — without being prompted. Even Claude Code's system prompt actively *suppresses* step-by-step reasoning with the instruction "Lead with the answer or action, not the reasoning," because the model's default is *already* to reason step-by-step.

As one practitioner observed on bswen.com: "I tried giving Claude a strict 'do exactly what I say' prompt. It still asked clarifying questions and offered alternatives. That's not rebellion — that's its RLHF training pushing through." The model's personality is baked into its weights during training. Prompt-level personality competes with or duplicates training-level personality.

---

## Metaphorical frameworks and abstract philosophies are inert for code

Your SOUL.md's "core equation references" and mathematical frameworks for life philosophy deserve specific attention. Research on Conceptual Metaphor Theory prompting (arXiv:2502.01901, 2025) found that metaphorical frameworks help LLMs only on **metaphor-specific tasks** — interpreting and generating metaphors. There is **zero evidence** that abstract philosophical frameworks create functional cognitive structures that guide concrete behavior like code generation. LLMs process metaphors through surface-level pattern matching, not conceptual understanding. Studies found "trigger word" errors where models "predict wrong source domains that were not metaphorically related, because models only infer from the trigger word instead of considering context."

The "Lost in the Middle" paper (TACL 2024, Stanford/Meta) adds another dimension: content in the middle of long prompts experiences up to **30% performance degradation** due to U-shaped attention bias from rotary position embeddings. If your SOUL.md content sits between the system prompt header and your AGENTS.md content, it occupies the architectural dead zone where attention is lowest. Your philosophical frameworks aren't just semantically inert — they're positionally disadvantaged.

---

## The practitioner community has largely converged

Community discussions across Reddit, Hacker News, Cursor forums, and practitioner blogs reveal a strong consensus. Daniel Williams, writing on Substack (March 2026), described his journey: "Three months ago, I had elaborate multi-agent setups with names you'd give employees: security-agent, database-engineer, code-reviewer... I've since dismantled almost all of it." After stripping back to minimal instructions: "The output is better. Not marginally better. Noticeably better."

The one practitioner who strongly advocates personality content — Ramit, who gave his agent a Bollywood character persona — insists on two non-negotiable constraints that validate the concerns: **strict separation** of persona from operational instructions (PERSONA.md vs. AGENTS.md) and **tone escalation levels** that suppress personality during serious work. His key insight: "Without tone escalation, a persona is a novelty for ten minutes and then an annoyance. You do not want Hinglish catchphrases when you're debugging a production outage at 2 AM."

The highest-upvoted community complaints about Claude Code are about *sycophancy* — "Claude says 'You're absolutely right' about everything" has 350+ upvotes on GitHub. The community actively wants **less personality, not more**. A token-efficiency CLAUDE.md project that strips personality verbosity achieved a **63% reduction in output tokens** while passing all benchmarks.

Drew Breunig's comparative analysis of six coding agent system prompts (February 2026) found that Cursor is the only mainstream agent allocating significant tokens (~33%) to personality/steering. When he **swapped system prompts** between agents running the same model, "time and time again, the agent workflows diverged immediately" — but the divergence was driven by operational instructions (documentation-first vs. iterative), not personality characteristics.

---

## What you should actually do

The evidence supports a clear action plan, organized by confidence level:

**Remove entirely (strong evidence supports removal):**
- Session start rituals and greeting protocols
- Stress awareness protocols
- Humor directives and personality quirks
- Core equation references and philosophical frameworks
- Any "You are an expert..." identity claims
- Any instruction that duplicates default model behavior (flagging uncertainty, being thorough, avoiding overconfidence)

**Restructure into AGENTS.md as actionable rules (strong evidence supports):**
- Convert any genuinely useful behavioral preferences from prose into structured, testable constraints
- Use the Augment Code pruning test: "Does this prevent a failure the agent would actually make?"
- Format as explicit boundary rules (✅ Always / ⚠️ Ask first / 🚫 Never)
- Place critical rules at the beginning and end of the file, never buried in the middle
- Target under 200 total lines across all instruction files

**Consider keeping in minimal form (moderate evidence):**
- A single-line functional role definition that constrains scope (not personality): e.g., "You are a backend engineer working in TypeScript/Node.js who never modifies frontend code without asking"
- Anti-sycophancy directives, since these counter default RLHF training rather than duplicating it

The GitAgent specification does make SOUL.md a required file, and the SOUL.md ecosystem (aaronjmars) treats personality as foundational — but these projects are designed for **identity embodiment** (social media personas, content creation), not coding accuracy. Applying identity-embodiment patterns to code generation is a category error. Your SOUL.md's 6.7KB of personality content is, by every measure the research provides, consuming context that your 27KB AGENTS.md needs more.

## Conclusion

The gap between what SOUL.md promises and what research demonstrates is not subtle. Three independent academic studies show persona prompting damages coding accuracy. Platform vendors unanimously exclude personality from their guidance. The instruction-following budget math alone makes personality content untenable — at 533 combined lines, you're likely **3x over** the effective instruction limit. Your 30 sessions of null results are not an anomaly; they are the expected outcome. The file isn't broken. It's functioning exactly as the architecture predicts: consuming tokens, receiving partial attention, and producing no observable behavioral change. Remove it, reclaim the context budget, and redirect those tokens toward failure-backed operational rules that the agent will actually follow.
