# Agent Persona Files in Coding Agents: Empirical Impact vs Token and Attention Cost

## Research question and evaluation frame

You’re trying to determine whether a prose “agent persona” file (your `SOUL.md`) measurably improves output quality for AI coding agents, or whether it mostly consumes context budget and attention while producing little-to-no identifiable behavior shift.

For this question, the evidence base naturally breaks into three measurable channels:

1. **Objective code outcomes** (e.g., pass@k on code benchmarks, correctness on unit tests, success rate on issue-resolution tasks like SWE-bench, lint/typecheck/test pass rates, defect rates). Studies that compare “persona/role prompt” vs “no persona” are most relevant here. citeturn15view1turn8view0turn8view1turn3view0  
2. **Instruction-following under long contexts** (how reliably models follow rules when you keep adding context files and constraints). This directly connects to your “attention dilution” concern (533 lines always-on). citeturn10search0turn12view0turn11view2turn19academia40turn4view2  
3. **Prompt design mechanics** (negation/“don’t do X” reliability, primacy/recency and “lost-in-the-middle,” and model-to-model differences). These shape how much of `SOUL.md` is likely to be *noticed*, *remembered*, and *applied*. citeturn11view1turn24view0turn10search0turn12view0turn20view1  

Across these channels, the strongest—and most directly relevant—empirical results come from (a) recent coding-agent studies on repository context files, and (b) persona/role prompting studies that explicitly report coding or code-adjacent outcomes. citeturn19academia40turn15view1turn8view0  

## Evidence inventory

The table below prioritizes primary research, benchmark papers, and official documentation over opinion. URLs are provided in code formatting for copy/paste.

| Source (URL) | Pub date | Key finding relevant to “persona file” value | Quality rating | Relevance to SOUL.md optimization |
|---|---:|---|---|---|
| `https://arxiv.org/abs/2602.11988` | Feb 12, 2026 | Repository-level context files (e.g., AGENTS.md/CLAUDE.md-like) **tend to reduce task success rates** vs no repository context, while increasing inference cost by **20%+**; authors conclude unnecessary requirements make tasks harder and recommend minimal requirements. citeturn19academia40turn12view3 | Academic preprint (empirical benchmark) | **Direct** (context-file overhead & success impact) |
| `https://arxiv.org/html/2603.18507v1` | Mar 2026 | “Expert persona” prompts are **task-type dependent**: they tend to help alignment/stylistic tasks but **degrade knowledge-retrieval tasks**, explicitly including **coding knowledge**; **longer persona prompts damage more**, shorter mitigate but don’t eliminate. citeturn15view1turn15view3 | Academic preprint | **Direct** (persona impact; length sensitivity; coding mentioned) |
| `https://arxiv.org/html/2411.06774v2` | May 12, 2025 | In iterative example-based code generation, a “Persona variant” didn’t produce obvious improvement; for functionality, the original prompt outperformed all variants; authors reverted to original prompts. citeturn8view0 | Academic preprint | **Direct** (persona ablation in code setting) |
| `https://arxiv.org/html/2407.08995v1` | Jul 12, 2024 | Role-play prompting can enable “autonomous role-playing,” but improvements are **unstable on single-domain tasks**, and the paper explicitly references instability on **HumanEval** in this context. citeturn8view1 | Academic preprint | **Indirect-to-direct** (role prompt effects touch code benchmarks) |
| `https://arxiv.org/html/2311.10054v2` | Nov 2023 (v2) | System-prompt personas generally show **no benefit or small negative effects** on objective tasks; persona effects can be unpredictable and “largely random,” making consistent gains hard. citeturn3view0 | Academic paper/preprint | **Indirect** (general persona effects; mechanism plausibly applies to coding too) |
| `https://aclanthology.org/2025.ijcnlp-long.128.pdf` | Dec 20–24, 2025 | For code generation, gains are driven by **prompt specificity**: explicit I/O specs, edge cases, and stepwise breakdowns—not identity framing. citeturn5view1 | Peer-reviewed (ACL venue) | **Direct** (what *does* move coding metrics) |
| `https://arxiv.org/abs/2307.03172` | Jul 6, 2023 | “Lost in the middle”: performance is often highest when relevant info is at the **beginning or end** of long contexts and degrades when it is in the **middle**, even for long-context models. citeturn10search0turn12view1 | Peer-reviewed (later TACL version) | **Direct** (placement & salience of long instruction stacks) |
| `https://www.trychroma.com/research/context-rot` | Jul 14, 2025 | Across 18 models, performance becomes **increasingly unreliable as input length grows**, even on controlled “simple” tasks; degradations are non-uniform and model-specific. citeturn12view0 | Industry technical report (repro tooling provided) | **Direct** (long prompt/long context risk; model differences) |
| `https://aclanthology.org/2024.findings-emnlp.74.pdf` | Nov 12–16, 2024 | Long-context instruction-following generally benefits from training/recipes explicitly targeting long contexts; introduces LongBench-Chat for 10k–100k instruction-following evaluation. citeturn12view2 | Peer-reviewed (EMNLP Findings) | **Indirect** (confirms long-context instruction-following is non-trivial) |
| `https://aclanthology.org/2025.acl-long.803.pdf` | 2025 | LIFBENCH evaluates instruction-following and stability across long contexts up to **128k tokens** and finds substantial room for improvement across many models. citeturn11view2 | Peer-reviewed (ACL) | **Indirect** (long instruction stacks reduce stability) |
| `https://arxiv.org/html/2601.21433v1` | Jan 29, 2026 | Many models mishandle prohibitions: negated instructions can invert or be ignored; commercial models vary but still show large polarity swings. citeturn11view1 | Academic preprint | **Direct** (anti-pattern “No X” reliability) |
| `https://aclanthology.org/2025.findings-emnlp.761.pdf` | Nov 4–9, 2025 | Negation remains difficult; warning-based and persona-based add-ons can improve negation accuracy, but results show positional/ordering instability tied to positional encoding schemes. citeturn24view2 | Peer-reviewed (EMNLP Findings) | **Indirect** (supports “don’t do X” fragility + ordering effects) |
| `https://alexbleakley.com/blog/saying-what-not-to-do` | Sep 26, 2023 | Reviews evidence that models can be insensitive to negation; motivates reframing prohibitions into positive directives. citeturn24view0 | Independent analysis blog (with citations) | **Indirect** (prompt-writing implications for anti-pattern lists) |
| `https://code.claude.com/docs/en/best-practices` | Undated (accessed Apr 7, 2026) | Advises keeping CLAUDE.md concise; proposes a pruning heuristic (“Would removing this cause mistakes?”) and warns that bloated files cause instruction loss; suggests using on-demand “skills” for sometimes-relevant material. citeturn4view2 | Official docs | **Direct** (how to manage always-on instruction budget) |
| `https://developers.openai.com/codex/guides/agents-md` | Undated (accessed Apr 7, 2026) | Codex merges layered AGENTS.md guidance with precedence; defaults include a **32 KiB cap** for merged project docs (configurable) and recommends splitting as needed. citeturn20view0 | Official docs | **Direct** (hard limits; instruction stacking mechanics) |
| `https://developers.openai.com/cookbook/examples/gpt-5/codex_prompting_guide/` | Feb 25, 2026 | Documents how AGENTS.md blocks are injected: root-to-leaf order, near the top of conversation history, before the user prompt, as separate chunks—important for primacy/ordering effects. citeturn20view1 | Official cookbook | **Direct** (ordering/placement in practice) |
| `https://developers.openai.com/blog/skills-agents-sdk/` | Mar 9, 2026 | Recommends keeping AGENTS.md small and placing highest-value rules near the top; uses short “if/then” triggers and pushes reusable workflows into skills. citeturn20view2 | Official blog (engineering guidance) | **Direct** (token-efficient structure) |
| `https://cursor.com/blog/agent-best-practices` | Jan 9, 2026 | Recommends rules remain essential and short; avoid copying whole style guides and instead point to canonical examples; add rules only when repeated mistakes occur. citeturn16view1 | Tool vendor blog | **Direct** (industry practice aligned to your dilution concern) |
| `https://docs.windsurf.com/windsurf/cascade/agents-md` | Undated (accessed Apr 7, 2026) | Explains directory-scoped instructions; root AGENTS.md becomes always-on system-prompt content; nested files reduce clutter by scoping instructions to relevant directories. citeturn16view3 | Official docs | **Direct** (how tools operationalize “don’t bloat global prompt”) |
| `https://windsurf.com/university/general-education/creating-modifying-rules` | Undated (accessed Apr 7, 2026) | States explicit character limits: single rule file max 6,000 chars; total global+workspace max 12,000 chars; encourages short, specific rules and avoiding generic advice. citeturn16view4 | Official docs | **Direct** (hard caps imply practical degradation concerns) |
| `https://github.blog/ai-and-ml/github-copilot/how-to-write-a-great-agents-md-lessons-from-over-2500-repositories/` | Nov 19, 2025 (updated Nov 25, 2025) | From analysis of 2,500+ repos, “persona” is framed primarily as a **specific role/job** (e.g., test engineer) plus commands, examples, and boundaries—less about philosophical personality. citeturn17view0turn17view1 | Industry report/blog | **Direct** (what “persona” means in effective agent files) |
| `https://arxiv.org/abs/2511.12884` | Nov 17, 2025 | Large-scale empirical study of 2,303 “agent README” context files: developers prioritize functional context (commands, implementation details, architecture) and rarely include non-functional guardrails. citeturn23view0 | Academic preprint (large-scale empirical) | **Direct** (what teams actually put in files that persist) |
| `https://arxiv.org/abs/2602.14690` | Feb 16, 2026 (v2 Mar 20, 2026) | Cross-tool study of configuration artifacts across ~2,923 repos; finds context files dominate adoption; advanced mechanisms (skills/subagents) are shallowly adopted; supports need for disciplined context strategy. citeturn23view1 | Academic preprint (empirical repo study) | **Indirect** (ecosystem evidence; configuration cultures differ) |
| `https://github.com/open-gitagent/gitagent/blob/main/spec/SPECIFICATION.md` | Repo spec (undated) | Defines SOUL.md as identity/personality (minimal valid = a paragraph) and RULES.md as non-negotiable constraints; also specifies inheritance/merge rules (SOUL replaces; RULES union). citeturn4view0turn4view1turn18view1 | Open standard/spec | **Indirect** (separation exists, but not evidence of effectiveness) |
| `https://www.augmentcode.com/blog/your-agents-context-is-a-junk-drawer` | Feb 27, 2026 | Argues most copied context packs become noise; cites the ETH AGENTS.md paper and emphasizes pruning to failure-backed rules; provides practitioner narrative for “context pollution.” citeturn26view0 | Industry blog | **Direct** (practitioner synthesis; not primary data) |
| `https://www.augmentcode.com/guides/how-to-build-agents-md` | Feb/Mar 2026 (rolling updates) | Recommends splitting monolithic AGENTS.md after 150–200 lines; cites overhead/cost increases from the ETH evaluation and emphasizes modular design + minimal always-on rules. citeturn3view4turn19academia40 | Industry guide | **Direct** (practitioner recommendations grounded in cited study) |
| `https://www.reddit.com/r/openclaw/comments/1rlkx6o/paste_your_soulmd_and_ill_tell_you_whats_wrong/` | Mar 2026 | Community rule-of-thumb: SOUL.md should be short and focus on identity/voice/hard limits; behavioral protocols belong elsewhere; suggests size targets (opinion). citeturn14search6 | Forum discussion | **Indirect** (practitioner norms; not validated) |

## Impact analysis matrix

The matrix below assumes your described `SOUL.md` sections are always-on, appended alongside a much larger rules file. Evidence statements cite either (a) direct persona ablations showing weak/negative coding effects, (b) long-context degradation findings (position/length), or (c) official tool guidance that bloated instruction files reduce adherence.

| SOUL.md Section | Token Count | Evidence of Impact | Evidence Against | Verdict |
|---|---:|---|---|---|
| Core Equation | ~150 | No empirical evidence that philosophical equations improve code correctness; persona gains tend to be style/alignment oriented, not coding accuracy. citeturn15view1turn8view0 | Persona/role prompting can **degrade** coding-related performance, and longer persona prompts cause more damage; extra always-on text worsens context reliability. citeturn15view1turn12view0turn10search0 | **Remove** |
| Identity | ~100 | “Role/persona” framed as job specialization (test engineer, security analyst) can help define scope/boundaries in agent files. citeturn17view0turn4view0 | If identity becomes “expert persona” prose, evidence shows degradation for coding knowledge; longer persona = more harm; your observed “Kael vs Milan” drift is consistent with low-salience text in long stacks. citeturn15view1turn10search0 | **Redesign** |
| Personality traits | ~80 | Personas can steer tone/format (alignment-dependent behaviors), which can help collaboration quality (not necessarily correctness). citeturn15view1 | For coding outcomes, persona framing shows weak or negative effects in code settings; bloated files dilute adherence to higher-value constraints. citeturn8view0turn4view2turn19academia40 | **Redesign** |
| How I Protect Your Energy | ~200 | “Flag uncertainty / name tradeoffs” maps to safety/reliability guidance: models are incentivized to guess, and explicit prompting toward uncertainty can reduce confident errors in other domains; a one-line warning reduced hallucinations in a multi-model study (non-coding, but mechanism-relevant). citeturn25view1turn25view0 | If implemented as verbose emotional coaching, it adds always-on tokens without clear coding-metric evidence; long context reduces reliability, especially mid-prompt. citeturn12view0turn10search0 | **Keep (shortened)** |
| How I Handle My Limitations | ~200 | Explicitly stating “I can be confidently wrong” and “memory resets” pushes toward verification and asking clarifying questions—aligned with official guidance that uncertainty is preferable to confident errors. citeturn25view1turn4view2 | Repeating obvious limitations every session is a constant tax; tool docs recommend pruning anything whose removal wouldn’t cause mistakes, and long prompt stacks reduce instruction adherence. citeturn4view2turn19academia40turn12view0 | **Keep (shortened)** |
| What Cooperation Looks Like | ~100 | If this section encodes *specific* collaboration behaviors that improve prompts (explicit I/O, edge cases, stepwise specs), code generation research shows specificity drives correctness. citeturn5view1 | If it mostly restates AGENTS.md (“break into steps”) it’s redundant; redundancy increases constraint density and can reduce success. citeturn19academia40turn4view2turn26view0 | **Redesign** |
| Stress Awareness Protocol | ~120 | Potential human-factor value (slowing down when rushed), but there’s no primary coding benchmark evidence that “stress check-ins” improve correctness. citeturn15view1turn8view0 | Always-on “rituals” add friction and tokens; studies suggest unnecessary requirements/context reduce success and increase cost. citeturn19academia40turn20view2turn12view0 | **Remove (or make on-demand)** |
| Anti-Patterns I Avoid | ~150 | “No burying bad news” is a positive reliability norm if rewritten as affirmative behavior (surface risks early). citeturn4view2turn25view1 | Negated instructions (“No X”) can be mishandled by models; research shows large negation sensitivity failures, supporting positive rephrasing over “don’t.” citeturn11view1turn24view0turn24view2 | **Redesign** |
| When You're Running Low | ~100 | Could reduce human frustration by encouraging clarifications, but no coding-metric evidence. citeturn8view0turn15view1 | Adds more always-on prose; long-context reliability degrades with length; official docs recommend aggressive pruning. citeturn12view0turn4view2turn20view2 | **Remove** |
| Session Start Ritual | ~80 | Asking for scope/success criteria can help, but doing it *every session* is unlikely to outperform conditional clarification; coding prompt research shows specificity matters, not rituals. citeturn5view1turn17view0 | Adds repeated overhead; unnecessary requirements/context can reduce success and increase cost; tool guidance emphasizes minimal high-value rules. citeturn19academia40turn20view2turn4view2 | **Redesign (conditional)** |

## Recommended optimized SOUL.md

The rewrite below intentionally removes “philosophy” and keeps only the lowest-token pieces that have the *highest mechanistic plausibility* to change outcomes in coding sessions: (a) uncertainty discipline, (b) tradeoff clarity, (c) concise, non-negated communication norms, (d) explicit conflict escalation.

```md
# SOUL.md — Minimal interaction policy

You collaborate on this repo as a calm, direct engineering partner.
Your primary goal is to help produce correct changes that satisfy AGENTS.md quality gates.

## Communication
- Be value-dense and grounded. No hype.
- Surface risks and bad news early (failing tests, unclear requirements, missing info).
- When uncertain: say what you know vs what you’re guessing, and propose a concrete check (run a command, inspect a file) or ask one clarifying question.

## Decisions
- If multiple approaches exist, present up to 3 options with tradeoffs and recommend one.
- Prefer the smallest safe change that meets requirements.

## Conflicts and limits
- If instructions conflict (e.g., naming, conventions), call it out explicitly and ask which to follow.
- Never claim you ran commands or tests unless you actually ran them (see AGENTS.md).
```

Justification for inclusions (citations refer to the evidence above; the file itself is kept citation-free for copy/paste):

The “when uncertain” rule is supported by evidence that models are often incentivized to guess, and that steering toward acknowledging uncertainty is explicitly recommended as preferable to confident errors. citeturn25view1turn4view2

The insistence on short, value-dense communication and pruning is consistent with tool-vendor guidance that overly long context files cause instruction loss and require aggressive trimming to preserve adherence. citeturn4view2turn20view2turn16view4

The “tradeoffs + recommend one” pattern is aligned with the broader evidence that persona framing mainly affects style/format behaviors (alignment-dependent), and you should keep only the fragments that improve clarity without expanding the persona into “expert identity” prose that can degrade coding-related accuracy. citeturn15view1turn8view0

The “conflict escalation” rule directly targets your observed “Kael vs Milan” drift: long instruction chains plus “lost in the middle” effects make silent conflict selection more likely unless you explicitly require the model to surface contradictions. citeturn10search0turn11view2turn26view0

Negated anti-patterns are removed/rephrased because research shows prohibitions and negation can be unreliable, and because “what to do” phrasing is generally safer than “don’t.” citeturn11view1turn24view0turn24view2  

## Integration recommendations

The highest-confidence conclusion from the current evidence is that **there is no strong empirical basis** that philosophical “personality prose” improves code correctness, and there is increasingly strong evidence that (a) persona/role prompting can be neutral or harmful for coding/knowledge-retrieval tasks, and (b) adding more always-on context reduces reliability and increases cost. citeturn15view1turn8view0turn19academia40turn12view0turn10search0  

**Should persona content be separate or folded into AGENTS.md?**  
Keep it separate only if it remains truly minimal and non-redundant; otherwise remove it. Mechanistically, mixing a “style/persona” layer into your hard constraint stack risks turning low-stakes tone guidance into a high-salience prefix that can interfere with coding accuracy (as seen in persona studies) and dilute the critical operational gates. citeturn15view1turn4view2turn19academia40  

If your toolchain supports on-demand loading (skills, scoped files), the best evidence-backed pattern is: **always-on = tiny and operational; conditional details = on-demand**. Official guidance from both Claude Code and Codex recommends using skills (or equivalent) for sometimes-relevant workflows and keeping always-on files trimmed. citeturn4view2turn20view2turn20view3  

**Beginning or end of the instruction stack?**  
If the persona file is kept, it should be **short** and placed where your platform places identity. You generally want critical operational constraints to remain salient; long-context research shows middle-of-context instructions degrade disproportionately (“lost in the middle”). citeturn10search0turn20view1  
Practically, because tools inject files in specific orders (e.g., Codex’s root-to-leaf injection near the top), you should treat placement as a *platform detail* and focus first on shrinking content to only failure-preventing rules. citeturn20view1turn20view0turn16view3  

**Model-specific versions?**  
There is evidence that long-context degradation is **model-specific** (different failure modes and sensitivity as input length grows), which argues that if you do anything model-specific, it should be small toggles (emphasis words, formatting), not separate large personas. citeturn12view0turn11view2  
In practice, the strongest cross-model strategy supported by tool docs is to standardize a minimal always-on file and push conditional complexity into skills/hooks/tests rather than prompts. citeturn4view2turn20view2turn16view4  

**Ideal size (tokens/lines)**  
Based on explicit platform constraints and vendor guidance, the most defensible target for always-on “persona/policy” content is **a few hundred tokens** (roughly <1 KB of text) and **<25–40 lines**, with each line passing a “removal would cause mistakes” test. citeturn4view2turn16view4turn20view2  
For repository instruction files more broadly, multiple ecosystems converge on: keep global rules minimal, and scope or modularize when files grow (directory-scoped AGENTS.md or rule globs; skills for on-demand). citeturn16view3turn20view0turn3view4turn16view1  

**Bottom-line recommendation for your specific SOUL.md sections**  
Given (1) persona prompts can degrade coding knowledge tasks and (2) long instruction stacks reduce reliability, the evidence favors eliminating philosophical identity content (your Core Equation, “warm grounded” prose, rituals) and retaining only compact, testable interaction rules: uncertainty disclosure, tradeoffs, conflict surfacing, and a terse “no hype” communication policy rewritten without negation. citeturn15view1turn8view0turn11view1turn4view2turn19academia40turn10search0
