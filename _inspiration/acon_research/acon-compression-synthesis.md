# Context Compression for Zorivest Dual-Agent Workflow — Synthesis & Verdict

> Three independent deep-research runs (ChatGPT/GPT-5.4, Claude/Opus 4.6, Gemini/2.5 Pro) were commissioned on the same topic: whether LLM context compression is worth integrating into the Zorivest Opus ↔ Codex review loop. This document synthesizes the convergent findings, surfaces the disagreements, and delivers a practical recommendation.

---

## 1. Where All Three Sources Agree

These are high-confidence findings — independently validated across all three research pipelines.

### 1.1 Context Rot Is Real and Measurable

| Claim | ChatGPT | Claude | Gemini |
|-------|---------|--------|--------|
| "Lost in the middle" U-shaped accuracy curve | ✅ Cites Liu et al. TACL 2024 | ✅ Cites Liu et al. + Chroma 2025 | ✅ Cites same + attention decay |
| Every tested frontier model degrades with length | ✅ | ✅ (18 models tested) | ✅ |
| Effective window is far below advertised max | ✅ | ✅ ("up to 99% below") | ✅ |
| Compression can *improve* reasoning quality | ✅ | ✅ (LLMLingua: +21.4% at 4×) | ✅ |

> [!IMPORTANT]
> **This is the strongest argument for compression** — it's not just about cost savings. Shorter, denser context can produce *better review output* from both Opus and GPT-5.4. The 7-pass average per MEU may partly be a symptom of context rot in later passes.

### 1.2 Prevention > Compression > Caching (Layered Priority)

All three independently converge on the same three-layer stack:

| Layer | Function | Expected Impact |
|-------|----------|-----------------|
| **L1 — Prevention** | Don't generate bloat in the first place (template discipline, test output summarization, delta-only diffs) | 30–50% reduction, ~0 effort |
| **L2 — Compression** | AST-aware code compression, statistical masking of test logs, structured pruning | 40–70% additional reduction |
| **L3 — Caching** | Exploit provider KV cache discounts via stable prefixes | Cost multiplier on top (45–90% on cached portions) |

### 1.3 Headroom Is the Only Production-Ready Tool

| Source | Assessment |
|--------|-----------|
| ChatGPT | Detailed analysis of SharedContext, CCR, CacheAligner, proxy modes |
| Claude | "The only production-ready option" — all others are research or don't exist |
| Gemini | Production-ready, low integration complexity, highest suitability score |

All three rate Headroom's **Compressed Context Retrieval (CCR)** as the critical differentiator: compress aggressively, but never lose data — the agent can retrieve originals on demand.

### 1.4 LLM-Based Summarization Is Dangerous for Code

Every source warns against using LLM summarization on source code, stack traces, or test assertions. The failure mode is not "slightly wrong" — it's "confidently hallucinated with cascading downstream breakage."

> Deterministic methods only: AST pruning, regex masking, statistical variance isolation, unified diffs.

### 1.5 Prompt Caching Requires Architectural Discipline

| Provider | Cache Mechanism | Discount | Key Constraint |
|----------|----------------|----------|----------------|
| Anthropic | Prefix-based, explicit breakpoints | 90% on reads (but 1.25× write premium) | 4,096 token minimum for Opus; 5-min TTL |
| OpenAI | Automatic prefix matching | Up to 50% (90% on GPT-4.1) | ≥1,024 tokens; exact byte-level prefix match |

All three warn: **compression can sabotage caching** if it mutates the prefix (timestamps, reordered sections, non-deterministic rewrites). Headroom addresses this with an explicit `cache` vs `token` mode toggle.

---

## 2. Where the Sources Diverge

### 2.1 ADOL's Existence

| Source | Assessment |
|--------|-----------|
| ChatGPT | Treats ADOL as a real IETF draft, analyzes its 4 optimization dimensions |
| Claude | "ADOL — does not appear to exist" (extensive search found nothing) |
| Gemini | Cites `draft-chang-agent-token-efficient-02` from IETF Datatracker as the ADOL specification |

> **Resolution:** ADOL exists as an IETF Internet-Draft (`draft-chang-agent-token-efficient`). Claude's search likely missed it because "ADOL" is an informal label. The principles (schema deduplication, adaptive inclusion, controllable verbosity) are valid and applicable regardless of the draft's maturity status.

### 2.2 ContextEvolve Applicability

| Source | Assessment |
|--------|-----------|
| ChatGPT | Brief mention — "intellectually interesting but not directly applicable" |
| Claude | "Not directly applicable as a general-purpose tool" |
| Gemini | Enthusiastic — maps its 3-dimensional decomposition (Summarizer/Navigator/Sampler) directly to TDD workflow |

> **Resolution:** Gemini overstates applicability. ContextEvolve is a research framework for systems code optimization, not a drop-in tool. However, its *conceptual model* (separate state/intent/history into orthogonal channels) is genuinely useful as a design principle for structuring handoff templates.

### 2.3 Cost Savings Magnitude

| Source | Baseline Cost/MEU | At 60% Compression |
|--------|-------------------|---------------------|
| ChatGPT | $5.69 (7 passes, 11K tokens/call) | $2.28 → saves $3.41/MEU |
| Claude | Not modeled numerically | Claims 80–95% total reduction across all layers |
| Gemini | Not modeled numerically | Claims 80% peak token reduction at Phase 3 |

> ChatGPT is the most rigorous here. The others cite impressive percentages but don't ground them in Zorivest's actual workflow parameters.

---

## 3. The Honest Cost-Benefit for Zorivest

### 3.1 Current Scale Reality

Based on the ChatGPT spreadsheet model using your actual pricing:

| Metric | Value |
|--------|-------|
| Passes per MEU | ~7 |
| MEUs per project | ~4 |
| Input tokens per call | ~11,000 (handoff + findings + build plan) |
| **Cost per MEU (baseline)** | **~$5.69** |
| **Cost per project (baseline)** | **~$22.75** |
| Monthly MEU volume (estimated) | 10–20 |
| **Monthly baseline spend** | **~$57–$114** |

### 3.2 Savings at Each Compression Level

| Approach | Effort | Monthly Savings (@ 15 MEUs) | Annual Savings | Payback Period |
|----------|--------|----------------------------|----------------|----------------|
| **L1: Template optimization** | 1–3 days | ~$25 | ~$300 | Immediate |
| **L2: Tool-assisted compression** | 2–4 weeks | ~$50 | ~$600 | 1–2 months |
| **L3: Full CCR + Headroom** | 4–8 weeks | ~$65 | ~$780 | 3–6 months |

> [!WARNING]
> **The pure dollar savings are modest at current scale.** At 15 MEUs/month, even 60% compression saves ~$50/month. The infrastructure effort for L2/L3 is measured in *weeks of engineering time*, which has a much higher opportunity cost than $600/year.

### 3.3 But Cost Isn't the Real Story

The dollar model misses the two biggest benefits:

1. **Reduced pass count** — If context rot is contributing to the 7-pass average, shorter/denser artifacts could reduce it to 4–5 passes. That's a **30–40% reduction in calendar time per MEU**, which dwarfs the token savings in value.

2. **Quality improvement** — The "lost in the middle" research strongly suggests that GPT-5.4 is missing findings in later passes because the handoff has grown long enough to trigger attention degradation. Compression could improve *first-pass catch rate*, reducing total cycle time.

Neither of these benefits is easy to measure *in advance* — they require A/B testing within the actual workflow.

---

## 4. Recommendation: Phased Approach with a Hard Gate

### Phase 1 — Do Now (1–3 days, zero infrastructure)

This is pure ROI. No tools, no dependencies, no risk.

| Action | Expected Impact |
|--------|-----------------|
| **Restructure handoff template** — YAML front matter, fixed section order, stable prefix for caching | 15–25% token reduction + cache enablement |
| **Enforce test output summarization** — System prompt rule: "Only output failing test names, assertion messages, and relevant stack frames. Never output passing test details." | 90–95% reduction on test output sections |
| **Delta-only code sections** — Send unified diffs instead of full file contents for code state | 50–70% reduction on code sections |
| **Pin timestamps/dynamic content to end of artifact** — Preserve prefix stability for KV cache | Improved cache hit rates (up to 90% discount) |
| **Add verbosity tiers** — reviewer can request `summary | standard | detailed` per section | Prevents boilerplate re-reading |

> [!TIP]
> **This is the only phase I recommend committing to unconditionally.** It's the "prevention" layer — highest ROI, lowest risk, directly aligned with existing template standardization work already underway in Zorivest.

### Phase 2 — Measure Before Building (1–2 weeks instrumentation, then decide)

Before investing in middleware:

1. **Instrument current artifact sizes** — Log token counts per handoff section (code, tests, rationale, evidence, boilerplate) across 10–15 MEUs.
2. **Track pass-to-acceptance correlation** — Does artifact size predict pass count? If no correlation, compression won't reduce passes.
3. **Measure cache hit rates** — After Phase 1 restructuring, check `cached_tokens` in API responses. If already high, caching is working and L3 adds less.
4. **Run a manual A/B** — For 4 matched MEUs, manually compress the handoff to ~40% size and compare pass count + finding quality.

> [!IMPORTANT]
> **Gate rule:** Only proceed to Phase 3 if measurement shows (a) artifact sizes regularly exceed 8K tokens AND (b) pass count correlates with artifact size AND (c) manual compression demonstrably reduces passes or improves finding quality.

### Phase 3 — Selective Automation (2–4 weeks, only if gate passes)

If measurement justifies it:

| Component | Implementation |
|-----------|---------------|
| **Test output compressor** | Regex/statistical — collapse `PASS` blocks, preserve `FAIL` traces |
| **Code diff normalizer** | Tree-sitter or difftastic for AST-aware diff generation |
| **Headroom SDK integration** (optional) | SharedContext for cross-agent handoffs, CCR for on-demand retrieval |
| **Telemetry** | Track compression ratio, pass count, retrieval fallback frequency |

I would **not** recommend the full CCR/retrieval architecture unless you're consistently hitting >15K tokens per handoff AND the review workflow is fully automated (no human in the loop between passes).

---

## 5. Verdict

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   Phase 1 (template discipline): YES — do it now.           │
│   Phase 2 (instrumentation):     YES — measure first.       │
│   Phase 3 (middleware/Headroom):  CONDITIONAL — only if      │
│     measurement proves quality/pass-count improvement.       │
│                                                             │
│   Full ADOL/CCR/middleware stack: NOT YET.                   │
│   The dollar savings don't justify the engineering           │
│   investment at current scale (15 MEUs/month).              │
│   The quality argument might, but must be proven first.      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Why Not Just Build It All?

The three research papers paint an impressive picture of 80–95% compression with maintained quality. But:

1. **Your handoffs are already moderate-sized** (~8K tokens). The research targets 20K–100K+ payloads.
2. **Your volume is modest** (10–20 MEUs/month). Break-even formulas show infrastructure only pays back at high volume.
3. **You already have template standardization in progress** — the highest-ROI work is already partially done.
4. **Opportunity cost is real** — weeks building compression middleware is weeks not building P2 features.

The right move is: **lock in the free wins (Phase 1), measure whether the problem is as bad as the research suggests it might be (Phase 2), and only then decide whether the engineering investment is warranted (Phase 3).**

---

## Appendix: Tool & Framework Quick Reference

| Tool | Type | Status | Zorivest Fit |
|------|------|--------|-------------|
| [Headroom](https://github.com/chopratejas/headroom) | SDK/Proxy | Production beta | ⭐ Best fit if L3 needed |
| [RTK](https://github.com/rtk-ai/rtk) | CLI proxy | Production | ⭐ Quick win for CLI output |
| [LLMLingua](https://github.com/microsoft/LLMLingua) | Prompt compressor | Production | Medium — NL text only |
| [ACON](https://arxiv.org/abs/2510.00615) | Research framework | Experimental | Low — trajectory compression |
| [ContextEvolve](https://arxiv.org/abs/2602.02597) | Research framework | Experimental | Low — concept inspiration only |
| [Provence](https://arxiv.org/abs/2501.16214) | Context pruner | Open-source | Low — wrong domain (NL, not code) |
| ADOL | IETF draft | Maturing | Medium — principles applicable |
| [OPTIMA](https://github.com/thunlp/Optima) | Fine-tuning framework | Research | Low — requires model fine-tuning |
| [Caveman-lang](https://github.com/StealthyLabsHQ/caveman-lang) | Verbosity controller | Open-source | Low — extreme brevity, fragile |

---

## Appendix: Key Metrics to Track Post-Phase 1

| Metric | How to Capture | Decision Signal |
|--------|----------------|-----------------|
| Tokens per handoff section | Log before API call | Identifies bloat sources |
| `cached_tokens` / total prompt tokens | OpenAI API response `usage` field | Cache effectiveness |
| `cache_read_input_tokens` ratio | Anthropic API response | Cache effectiveness |
| Passes to acceptance per MEU | Existing workflow tracking | Compression → quality signal |
| Time-to-first-token per call | API response timing | Latency impact |
| False positive rate in review findings | Post-hoc labeling | Quality floor detection |
