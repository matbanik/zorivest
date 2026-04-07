# SOUL.md Decision Document

> Synthesized from independent deep research by ChatGPT (GPT-5.2) and Claude (Opus 4.6), conducted April 6, 2026. Combined evidence base: 6 academic papers, 3 large-scale repo studies (2,500+ repos each), 5 platform vendor guidelines, and dozens of practitioner reports.

---

## Executive Verdict

> [!CAUTION]
> **Both research reports independently conclude that SOUL.md is inert and should be either removed or radically reduced.** The convergence is striking — despite different research approaches, both reached the same conclusion through overlapping but distinct evidence paths.

| Dimension | ChatGPT Finding | Claude Finding | Agreement |
|-----------|----------------|----------------|-----------|
| Persona helps coding? | No — degrades accuracy | No — damages by 0.65 pts on 10-pt scale | ✅ Full |
| Current file is too long? | Yes — 533 lines exceeds 150-200 limit | Yes — 3x over effective instruction cap | ✅ Full |
| Core Equation has value? | Remove | Remove (metaphors are inert for code) | ✅ Full |
| Anti-pattern negation works? | No — reframe as positive | No — "large negation sensitivity failures" | ✅ Full |
| Session Start Ritual useful? | Redesign as conditional | Remove entirely | ⚠️ Partial |
| Stress Awareness Protocol? | Remove or make on-demand | Remove entirely | ✅ Full |
| Default models already do this? | Not explicitly addressed | Yes — RLHF training covers most SOUL.md content | N/A |
| Optimal replacement size? | <25-40 lines, ~1KB | Under 200 total lines across ALL files | ✅ Full |

---

## The Three Key Findings

### 1. Persona Prompting Actively Hurts Coding

Three independent academic studies measured this directly:

- **PRISM (USC, March 2026)**: Expert personas dropped coding scores by 0.65/10. Quote: *"Asking AI to adopt the persona of an expert programmer will not help code quality or utility."*
- **U. Michigan (arXiv:2311.10054, updated Oct 2024)**: 162 personas × 4 LLM families × 2,410 questions. Original paper claimed benefit, expanded study **reversed the conclusion entirely**.
- **Seoul National (Aug 2024)**: Persona degraded reasoning in 7/12 datasets for Llama3, 4/12 for GPT-4.

**Mechanism**: Persona instructions activate instruction-following mode at the expense of factual recall. The model spends computational capacity *performing the persona* rather than *solving the problem*.

### 2. The Instruction Budget Is Overcommitted

- LLMs follow ~150-200 instructions with reasonable consistency
- Claude Code's own system prompt consumes ~50 instructions
- AGENTS.md alone: ~404 lines (100+ instructions)
- Adding SOUL.md: 129 more lines = **3x the effective capacity**
- IFScale benchmark (July 2025): Claude exhibits **linear decay** — each added instruction reduces compliance with ALL instructions

> Anthropic's own docs: *"For each line, ask: 'Would removing this cause Claude to make mistakes?' If not, cut it. Bloated CLAUDE.md files cause Claude to ignore your actual instructions!"*

### 3. The Observed Null Results Are Predicted by Research

Your month of evidence (no Session Start Ritual used, no Stress Protocol invoked, "Kael"/"Milan" drift unnoticed, no personality fingerprints in output) is **exactly what the research predicts** for personality prose in a coding context. The file isn't broken — it's functioning as architecture dictates: consuming tokens, receiving partial attention, producing zero behavioral change.

---

## Section-by-Section Verdict

Both reports evaluated every SOUL.md section. Here's the synthesized verdict:

| Section | Lines | ChatGPT | Claude | Combined Verdict |
|---------|-------|---------|--------|-----------------|
| Core Equation | ~15 | ❌ Remove | ❌ Remove (metaphors inert) | **REMOVE** |
| Identity | ~8 | 🔄 Redesign | ❌ Remove (identity claims don't help) | **REMOVE or 1-line scope constraint** |
| Personality traits | ~7 | 🔄 Redesign | ❌ Remove (duplicates RLHF defaults) | **REMOVE** |
| How I Protect Your Energy | ~15 | ✅ Keep (shortened) | ❌ Mostly remove (defaults cover it) | **KEEP 2 lines: uncertainty + tradeoffs** |
| How I Handle My Limitations | ~12 | ✅ Keep (shortened) | ❌ Mostly remove (obvious to model) | **KEEP 1 line: conflict escalation** |
| What Cooperation Looks Like | ~8 | 🔄 Redesign | ❌ Remove (restates AGENTS.md) | **REMOVE** |
| Stress Awareness Protocol | ~8 | ❌ Remove | ❌ Remove | **REMOVE** |
| Anti-Patterns I Avoid | ~8 | 🔄 Redesign (positive framing) | ❌ Remove (negation unreliable) | **REFRAME 1-2 as positive rules** |
| When You're Running Low | ~8 | ❌ Remove | ❌ Remove | **REMOVE** |
| Session Start Ritual | ~8 | 🔄 Redesign (conditional) | ❌ Remove | **REMOVE** (AGENTS.md planning mode handles this) |

**Score: 7 sections REMOVE, 2 sections KEEP (drastically shortened), 1 section REFRAME**

---

## Three Options for Decision

### Option A: Optimized SOUL.md (~15 lines)

Keep a separate file with only evidence-backed behavioral rules. Based on ChatGPT's proposed rewrite, enhanced with Claude's pruning criteria.

```markdown
# Milan

You collaborate on this repo as a calm, direct engineering partner.
Your primary goal is to help produce correct changes that satisfy AGENTS.md quality gates.

## Communication
- Be value-dense and grounded. No hype, no filler.
- Surface risks and bad news early — failing tests, unclear requirements, missing information.
- When uncertain: state what you know vs. what you're guessing, and propose a concrete check or one clarifying question.

## Decisions
- If multiple approaches exist, present up to 3 options with tradeoffs and recommend one.
- Prefer the smallest correct change that meets requirements.

## Conflicts
- If instructions conflict (naming, conventions, specs), call it out explicitly and ask which to follow.
```

**Token cost**: ~200 tokens (down from ~1,700)  
**Evidence basis**: Uncertainty disclosure, tradeoff surfacing, and conflict escalation all have mechanistic support. Anti-sycophancy framing ("no hype") counters RLHF rather than duplicating it.

---

### Option B: Fold into AGENTS.md (~5 lines added)

Remove SOUL.md entirely. Add a small "Communication" section to AGENTS.md:

```markdown
## Communication Policy
- Surface risks and bad news early. No performative enthusiasm.
- When uncertain: state confidence level and propose a verification step.
- If instructions conflict across files, flag the conflict explicitly — do not silently pick one.
```

**Token cost**: ~80 tokens added to AGENTS.md (net savings: ~1,620 tokens per session)  
**Evidence basis**: Same as Option A. Eliminates file-separation overhead and the "lost in the middle" risk of a separate identity file.

---

### Option C: Remove Entirely

Delete SOUL.md. Remove all references from AGENTS.md and workflow files. The hypothesis: modern frontier models already exhibit the useful behaviors (flagging uncertainty, breaking into steps, avoiding performative enthusiasm) via RLHF training. The AGENTS.md quality gates, planning modes, and TDD protocols already constrain all observable behavior.

**Token cost**: 0 (savings: ~1,700 tokens per session)  
**Risk**: Minimal. Claude's research found that models already suppress sycophancy, flag uncertainty, and break tasks into steps without being asked. The one practitioner who successfully uses personality content (Ramit with Bollywood persona) uses it for creative engagement, not code quality — and still suppresses personality during serious work via "tone escalation."

---

## Recommendation

> [!IMPORTANT]
> **Recommended: Option B (fold 3-5 lines into AGENTS.md).**

**Why not Option A (keep separate file)?**
- Research shows persona files in the "middle" of instruction stacks suffer up to 30% attention degradation ("Lost in the Middle," Stanford/Meta)
- Separate files create maintenance burden (the Kael/Milan drift proves this)
- Every workflow must mandate reading it, adding procedural overhead for near-zero return

**Why not Option C (remove entirely)?**
- The conflict-escalation rule has strong mechanistic support — the Kael/Milan drift *should* have been caught, and an explicit "flag conflicts" rule is the fix
- Anti-sycophancy ("no hype") actively counters RLHF defaults rather than duplicating them
- These 3-5 lines pass the Augment Code pruning test: *"Does this prevent a failure the agent would actually make?"* Yes — silent assumption selection and performative compliance are real failure modes

**Implementation steps if approved:**
1. Add "Communication Policy" section to AGENTS.md (3-5 lines from Option B)
2. Delete `SOUL.md` from repository root (save backup to pomera_notes first per file deletion policy)
3. Remove all `SOUL.md` references from:
   - AGENTS.md §Agent Identity (lines 102-105)
   - AGENTS.md §Session Discipline (line 116)  
   - All workflow files (5 files reference it)
4. Update any workflow/handoff templates that list SOUL.md as mandatory reading
5. Commit with: `docs: remove SOUL.md, fold useful rules into AGENTS.md communication policy`

---

## Evidence Quality Assessment

| Evidence Type | Sources | Confidence |
|--------------|---------|------------|
| Academic papers on persona + code quality | 3 papers (PRISM, Michigan, Seoul National) | **High** — independent replication across models |
| Long-context attention degradation | 4 papers + industry reports (Lost in Middle, Context Rot, IFScale, LIFBENCH) | **High** — well-established finding |
| Platform vendor guidance (Anthropic, Cursor, Windsurf) | 5 official docs | **High** — vendors have internal telemetry |
| GitHub 2,500-repo analysis | 1 large-scale study | **High** — large sample, persona not in effective categories |
| ETH Zurich agent README study | 1 paper (2,303 files) | **High** — context files reduce success + increase cost |
| Practitioner reports | ~15 forum/blog sources | **Moderate** — anecdotal but consistent direction |
| Negation/prohibition reliability | 3 papers | **High** — models struggle with "don't do X" |
| Metaphor/philosophy effectiveness | 1 paper (CMT prompting) | **Moderate** — specific to metaphor tasks, no code evidence |

---

## Source Documents

- [ChatGPT Research](file:///p:/zorivest/_inspiration/soul_optimization_research/chatgpt-Agent%20Persona%20Files%20in%20Coding%20Agents%20Empirical%20Impact%20vs%20Token%20and%20Attention%20Cost.md) — 28 sources, impact matrix, proposed rewrite
- [Claude Research](file:///p:/zorivest/_inspiration/soul_optimization_research/claud-Your%20SOUL.md%20is%20likely%20inert%20%E2%80%94%20heres%20why.md) — 6 academic papers, platform docs, practitioner synthesis, section-by-section verdict
