# Token-Efficient Context Compression for a Dual-Agent, File-Based Development Workflow

## Workflow model and assumptions

Your workflow has two independent sources of inefficiency: (a) *economic scaling* (every pass re-sends the same tokens at metered rates) and (b) *cognitive scaling* (longer artifacts reduce the consistency of model reasoning, especially when the “relevant” facts are not near the beginning/end of the prompt). Empirically, long-context “position effects” (“lost in the middle”) are well-documented: models often perform best when key information is at the beginning or end of a long input, and degrade when it’s in the middle. citeturn11search0turn11search2turn11search5 That matters directly for your ~8K-token “context rot” threshold and motivates a design that keeps “need-to-reason” content *short* and places “reference” content behind retrieval or caching.

To make the quantitative modeling concrete (and editable), the spreadsheet below uses a small set of explicit assumptions. The arithmetic inside the model is faithful to the parameters you gave (8,000-token artifacts; 7 passes/MEU; 4 MEUs/project; provider token prices as supplied). Where your prompt implies additional tokens but does not specify sizes (“previous findings” and “build plan excerpt”), the model uses explicit placeholders so you can swap in your own measured values.

**Assumed per-pass prompt payload (editable):**
- Handoff artifact length **H = 8,000 tokens** (given).
- “Previous findings” included on each pass **F = 2,000 tokens** *(assumption; replace with your measured average)*.
- “Build plan excerpt” included on each pass **B = 1,000 tokens** *(assumption; replace with your measured average)*.
- Each pass triggers **two calls**: one to the implementer model and one to the reviewer model.
- Therefore, **input tokens per call** = **H + F + B = 11,000 tokens** *(in this worked example)*.

**Output tokens per call (editable):**
- Implementer outputs an updated handoff artifact: **~H tokens**.
- Reviewer outputs findings: **~F tokens**.

**Why these assumptions are conservative:** they *exclude* tool outputs (test logs, linters, stack traces, long diffs), which are often much larger than the prose handoff and are a primary target for specialized compressors. Headroom, for example, explicitly targets tool outputs, RAG retrievals, and file reads as common sources of repetitive “boilerplate” tokens. citeturn2view0

Long-context brittleness also appears even when retrieval is “perfect” (length alone can hurt), which strengthens the case for keeping your “reasoning surface” small. citeturn11academia42turn11search12


## Token economics spreadsheet model

### Deliverable 1: cost model and projections

**Token prices used for the main table (your givens):**
- Implementer model (Anthropic Opus 4.6 pricing as supplied in your prompt): **$15/M input**, **$75/M output**.
- Reviewer model (OpenAI GPT-5.4 pricing as supplied in your prompt): **$2.50/M input**, **$10/M output**.

For reference, the *current public list pricing* (as of early 2026) differs materially:
- Public Opus 4.6 list pricing is stated as **$5/M input** and **$25/M output**, with additional savings possible via prompt caching and batch. citeturn1search0turn7view4  
- Public GPT-5.4 list pricing shows separate **cached input pricing** and multiple service tiers (Standard/Batch/Flex/Priority). citeturn7view3  
The spreadsheet below uses your provided rates for the requested computations; the sensitivity section includes “swap-in” guidance.

### Cost per project at multiple compression levels

Interpretation used: “30% compression” = **30% token reduction** (keep 70% of tokens). The same reduction factor is applied to both input and output tokens for the *worked* estimate; in production, structured compression usually preserves verbatim sections (code, paths, errors) while compressing narrative, so you should expect deviations from pure proportional scaling.

Key constants (worked example):
- Passes per MEU = **7**
- MEUs per project = **4**
- Total passes per project = **28**
- Input per call = **11,000 tokens**
- Output per pass: implementer **8,000**, reviewer **2,000**

#### Spreadsheet table

| Scenario | Token reduction | Keep fraction | Cost per pass (Opus + GPT) | Cost per MEU (7 passes) | Cost per project (4 MEUs) |
|---|---:|---:|---:|---:|---:|
| Baseline (no compression) | 0% | 1.0× | $0.8125 | $5.6875 | $22.7500 |
| Template optimization (conservative) | 30% | 0.7× | $0.56875 | $3.98125 | $15.9250 |
| Tool-assisted compression | 60% | 0.4× | $0.3250 | $2.2750 | $9.1000 |
| Aggressive + retrieval fallback | 80% | 0.2× | $0.1625 | $1.1375 | $4.5500 |

**What dominates cost here:** with your rates, Opus output is the single largest term (because $75/M output). If you can reduce *output length* (not just inputs), the ROI improves disproportionately.

### Monthly savings projections at 10, 20, 50 MEUs/month

| Scenario | Cost / MEU | Monthly cost @ 10 MEUs | Monthly cost @ 20 MEUs | Monthly cost @ 50 MEUs | Monthly savings @ 10 | Monthly savings @ 20 | Monthly savings @ 50 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Baseline | $5.6875 | $56.8750 | $113.7500 | $284.3750 | $0.0000 | $0.0000 | $0.0000 |
| 30% reduction | $3.98125 | $39.8125 | $79.6250 | $199.0625 | $17.0625 | $34.1250 | $85.3125 |
| 60% reduction | $2.2750 | $22.7500 | $45.5000 | $113.7500 | $34.1250 | $68.2500 | $170.6250 |
| 80% reduction | $1.1375 | $11.3750 | $22.7500 | $56.8750 | $45.5000 | $91.0000 | $227.5000 |

### Prompt caching impact model

Prompt caching is *not* a replacement for compression; it is a way to make repeated prefixes cheaper and faster **when (and only when) the prefix bytes are identical**.

**OpenAI (GPT-5.x) prompt caching highlights**
- Caching applies automatically for prompts **≥ 1024 tokens**. citeturn8view0turn8view1  
- Cache hits require **exact prefix matches**; best practice is static content first, dynamic last. citeturn8view1turn8view6  
- In-memory retention is typically **5–10 minutes of inactivity** (sometimes up to an hour), and **extended retention up to 24 hours** is available for supported models (including gpt-5.4). citeturn8view1  
- You can influence routing and cache hit rates with `prompt_cache_key`. citeturn8view1  
- OpenAI states prompt caching can reduce latency **up to 80%** and input token costs **up to 90%** in favorable regimes. citeturn7view2  
- Pricing includes **cached input** as a distinct rate (e.g., gpt-5.4 shows $2.50/M input and $0.25/M cached input under Standard short-context). citeturn7view3  

**Anthropic (Claude) prompt caching highlights**
- Anthropic caching “caches the full prefix,” with **5-minute TTL by default**, refreshed on hits; **1-hour TTL** is available at additional cost. citeturn7view0turn7view1  
- Cache writes (5-minute TTL) cost **1.25×** base input; cache reads cost **0.1×** base input. citeturn1search17turn7view1  
- Cookbook guidance lists minimum cacheable lengths (notably **4,096 tokens** for Opus) and limits on breakpoints. citeturn7view1  

**Worked “cacheable-prefix” model (editable):**
- Suppose your “fixed structure / boilerplate” is **S = 4,000 tokens** per call (template header, schema refs, repeated path lists).
- Dynamic content is **D = 7,000 tokens** per call.
- If calls occur within the cache lifetime and your prefix is stable, most calls after the first can benefit.

Key caution: with Anthropic’s explicit caching economics, **low hit rates can cost more than no caching**, because repeated cache writes pay the 1.25× premium. citeturn1search17turn7view1 OpenAI’s caching is automatic and does **not** add an explicit write premium. citeturn8view4turn7view2

### Compression + caching interaction effects

This is where architecture matters:

- **Compounding savings (nearly additive) occurs when:**
  - You keep a large stable prefix (cached) and compress mostly the dynamic body.
  - You ensure compression is deterministic for the cached prefix (no timestamps, no reordered lists, no “creative” rewriting of the header).

- **Diminishing returns happen when:**
  - Your compression removes the very boilerplate that would have been cacheable anyway (shrinking S reduces the opportunity for caching gains).
  - Compression changes the prefix frequently, increasing cache misses (especially damaging for Anthropic due to write premium).

Headroom explicitly includes a “cache stability” orientation: its proxy offers a `cache` mode that freezes prior turns to preserve provider prefix cache reuse, while `token` mode prioritizes maximum compression. citeturn2view1turn2view0 It also includes a cache alignment stage to stabilize prefixes by extracting dynamic content, explicitly to improve caching behavior. citeturn6view6turn2view0

### Meta-cost of compression

There are two broad classes:

**Local / non-LLM compression (often the practical sweet spot)**
- Costs are mostly CPU/GPU time, not tokens.
- Headroom reports compression overhead ranging roughly **15–200ms** in typical cases, and documents larger overhead for extremely large payloads; it also provides scenario-by-scenario break-even analyses. citeturn3view0turn5view5turn5view7  
- If you enable heavier ML compressors (e.g., LLMLingua variants), Headroom documents higher per-request overhead and large cold-start/memory footprints. citeturn3view1turn2view1  

**LLM-based compression**
- Adds extra API calls and therefore latency.
- Token cost is usually small if you use a cheap compressor model (e.g., gpt-5.4-nano or gpt-5.4-mini), but must be explicitly modeled against your savings. OpenAI publishes pricing for these smaller variants and their cached-input rates. citeturn7view3  
- If your compressor call is “nearly as long as the original” and runs on an expensive model, the meta-cost can erase savings.

### Break-even analysis

Because your stated handoff sizes are moderate (8K tokens) and the model costs are per-million tokens, the *pure token-dollar* savings per MEU can be small in absolute dollars unless either (a) volume is high, or (b) the **true** prompt mass is much larger than the handoff artifact (common when test logs and large diffs are injected).

The general break-even formula:

- Let **C₀** = one-time build cost of compression infrastructure (labor + setup).
- Let **Cₘ** = recurring monthly ops cost (hosting, monitoring, maintenance).
- Let **H** = amortization horizon in months.
- Let **S** = savings per MEU.
- Then break-even monthly volume **V\*** satisfies:  
  **V\* ≥ (C₀/H + Cₘ) / S**

Using the worked example’s savings per MEU:
- 30% token reduction: **S ≈ $1.706 / MEU**
- 60% token reduction: **S ≈ $3.412 / MEU**
- 80% token reduction: **S ≈ $4.55 / MEU**

This implies that if your workload truly looks like the worked assumptions, large investments pay back only at very high MEU volume. In practice, teams justify infrastructure because:
- The real “prompt surface area” is often **5×–20×** larger than the final file artifact (tool outputs, retrieval chunks, logs). Headroom’s benchmarks and positioning are aimed at these large, repetitive payloads. citeturn2view0turn5view5  
- Quality improvements (reduced “context rot”) often translate into fewer review passes and less human intervention, which can dominate pure token dollars—consistent with long-context degradation findings. citeturn11search0turn11academia42turn11search3  

### Latency impact model

Latency typically has three components: fixed overhead (network + scheduling), input “prefill” time that scales with input tokens, and output “decode” time that scales with output tokens. Token reduction therefore tends to reduce both time-to-first-token (TTFT) and total generation time, roughly proportional to the reduction in input/output tokens (unless fixed overhead dominates).

Provider-native caching can create step-function improvements: OpenAI explicitly states prompt caching can reduce latency by up to **80%** in favorable cache-hit regimes. citeturn7view2

Compression infrastructure can *add* overhead. Headroom documents that overhead and provides per-scenario net latency calculations (sometimes net positive; sometimes net negative for very fast models). citeturn5view5turn5view7 The practical takeaway for your workflow:

- If your “handoff” is the majority of the prompt and you compress it before inference, token reduction should reduce inference time.
- If you introduce a heavyweight compression step, measure whether its overhead outweighs the inference time saved.
- If you implement caching-friendly templates, you often improve TTFT without any additional “compression compute,” because cache hits avoid re-processing the prefix. citeturn8view1turn7view0


## Production implementation patterns for file-based handoffs

This section documents production-grade patterns aligned to your “file-based markdown artifact” constraints and your four pain points (linear token costs, boilerplate waste, context rot, and lack of deltas).

### Pattern A: template-based compression with no new infrastructure

Goal: separate “fixed structure” (stable, cacheable, deduplicated) from “variable content” (the true delta you want the reviewer to reason over).

A practical template design uses:
- **YAML front matter** for structured metadata (machine-readable, easy to diff, easy to validate).
- **Stable section ordering** to preserve caching and reduce reviewer search cost.
- **“Verbosity tiers”** (summary / standard / detailed) with an explicit default.
- **Reference blocks** that define once and then refer by short IDs.

A production-friendly artifact shape (illustrative):

```markdown
---
meu_id: MEU-042
pass: 5
base_ref: refs/MEU-042/base.md
delta_ref: refs/MEU-042/deltas/pass-05.patch
tests:
  command: "pytest -q"
  result: "fail"
  failures: 2
evidence_index: evidence/MEU-042/index.json
verbosity: standard
---

# Handoff (MEU-042)

## TLDR
<short, reviewer-facing delta summary>

## What changed (delta)
<unified diff or patch references>

## Verbatim evidence
- PATHS: [ref:pathset/core]
- FAILURES: [ref:failurelog/2026-04-10T...]
- ASSERTIONS: <only minimal failing assertions>

## Rationale (summarizable)
<why the change is correct>

## Questions for reviewer
<explicit asks>
```

This structure is designed to keep the “reasoning surface” small while keeping “verbatim evidence” available in a controlled place. That directly addresses long-context brittleness (including “lost in the middle”). citeturn11search0turn11search2

To improve cache hit rates (both Anthropic and OpenAI), keep the top half of the document stable and push pass-specific material toward the end (exact-prefix matching is required for cache hits). citeturn8view1turn7view0

### Pattern B: delta-based handoffs

Goal: stop resending entire 8K–15K artifacts on every pass; send only what changed.

Three mature delta formats map well to LLM workflows:

- **Unified diff** for code and markdown: it is explicitly designed to be compact by omitting redundant context and is the de facto standard for patch exchange. citeturn12search3turn12search23  
- **JSON Patch (RFC 6902)** for structured metadata: standardized operations (`add`, `remove`, `replace`, etc.) on JSON documents. citeturn12search0turn12search24  
- **Hybrid “delta manifest”**: YAML front matter points to (a) a base artifact and (b) a delta file; the receiver rebuilds the full artifact locally.

Reconstruction requirements:
- Store an immutable **base** and deterministic **delta chain**.
- Validate the reconstructed artifact against a hash (or line count + strong checksum).
- Define **rebase rules** (send a fresh full artifact) when:
  - The delta chain exceeds a fixed length (to prevent accumulated ambiguity).
  - The receiver requests a rebase due to confusion (“too many moving parts”).
  - Compression/caching quality drops (e.g., frequent prefix changes).

### Pattern C: structured compression by “compression class”

Goal: get high compression without corrupting “verbatim” evidence.

A robust approach is to tag sections by class and apply different strategies:

- **Verbatim (never compress):** file paths, stack traces, test assertions, exact code blocks, exact error messages.
- **Summarizable (LLM ok):** rationale, explanation, design discussion.
- **Extractive (reduce to key facts):** test counts, coverage numbers, lint counts; keep only deltas and outliers.
- **Ephemeral (drop after first read):** setup boilerplate, environment reminders, repeated framework noise.

Tagging can be implemented with either:
- A YAML map that lists section IDs and their class, plus a stable “registry” of section semantics.
- Inline markers (HTML comments) that a preprocessor strips/rewrites prior to sending.

This pattern matches the ADOL draft’s diagnosis: token bloat comes from repetitive schema, excessive optional content, overly long responses, and inefficient selection—and it proposes schema deduplication, adaptive inclusion, controllable verbosity, and retrieval-based selection as systematic countermeasures. citeturn10view0

### Pattern D: Headroom SDK integration

Headroom is relevant to your system because it provides production mechanisms for:
- compressing context *without losing recoverability* (CCR),
- maintaining cache stability,
- and providing a shared compressed store for multi-agent handoffs.

Key primitives from the Headroom documentation:

- **SharedContext**: a framework-agnostic store where Agent A writes large content and Agent B reads a compressed version by default, with the option to request the full original. citeturn4view0  
- **CCR (Compress-Cache-Retrieve)**: compression is reversible; compressed output includes a marker with a hash, and the system injects a retrieval tool (`headroom_retrieve`) to fetch original data on demand. citeturn5view3turn5view4  
- **Proxy mode**: a production HTTP proxy that applies context optimization to all requests; it also supports a “cache” mode to preserve provider prefix-cache stability versus a “token” mode that maximizes compression. citeturn2view1turn2view0  
- **Performance overhead**: Headroom reports compression latency overhead (e.g., 15–200ms in typical cases; higher in extreme token payloads) and provides scenario benchmarks. citeturn3view0turn5view5  

**How to adapt Headroom to a file-based workflow:**  
Headroom’s proxy is conceptually an API-layer interceptor (LLM request/response), not a filesystem interceptor. citeturn2view0turn2view1 For your “agents write markdown files to a shared filesystem” design, the closest production mapping is:

- Use **SharedContext** as the shared store for *the heavy repeated parts* of handoffs (logs, verbose fixtures, long schema definitions), writing only compressed views into the markdown artifact.
- Keep a stable retrieval key in the markdown (hash or key), and let the receiving agent request expansions when needed (mirroring CCR behavior). citeturn5view3turn4view0

For markdown-specific content, Headroom documents a content-routing pipeline (including a cache aligner and different compressors for different content types) rather than a markdown-specialized renderer; in practice, you would treat markdown as text with protected verbatim blocks. citeturn6view6turn3view3turn2view0

### Pattern E: ADOL-inspired protocol design for markdown handoffs

The ADOL draft (IETF Internet-Draft) is directly on-point because it frames “agentic communication” as recursively consumed by LLMs, and explicitly targets redundant schema definitions and verbosity as primary drivers of token bloat. citeturn10view0

Applying its four optimization dimensions to markdown handoffs:

- **Schema deduplication**: define your handoff schema once (section headers, evidence formats, tagging rules) in a shared “schema registry” file; handoffs reference schema versions via a short ID. This follows ADOL’s “JSON references” idea but in markdown form. citeturn10view0  
- **Adaptive inclusion**: optional sections are omitted unless requested by the reviewer or triggered by heuristics (e.g., failing tests implies include minimal assertion blocks).
- **Controllable response verbosity**: the reviewer writes a “verbosity request” that specifies per-section verbosity for the next pass (e.g., “keep verbatim evidence detailed, rationale summary”). This maps to ADOL’s controllable verbosity dimension. citeturn10view0  
- **Context-aware selection**: include only the sections relevant to the current focus (e.g., failing tests only, or only the changed files). This is conceptually aligned with ADOL’s “retrieval-based selection mechanisms.” citeturn10view0  

This design also maximizes prompt caching viability because it encourages stable prefixes and predictable structure. citeturn8view1turn7view0


## Prompt caching deep dive for markdown handoffs

### Claude caching alignment

Anthropic’s prompt caching is explicitly prefix-based (“caches the full prefix”), with default 5-minute TTL and an optional 1-hour TTL. citeturn7view0 A practical engineering consequence is: anything you want cached must be *stable* and appear early, while items that change each pass must appear after cache breakpoints. Anthropic documents cache write and cache read billing multipliers (1.25× on writes for 5-minute TTL; 0.1× on reads), and provides minimum cacheable length guidance (notably 4,096 tokens for Opus in cookbook guidance). citeturn1search17turn7view1

For markdown handoffs, “cache-friendly” structuring means:
- stable template prefix,
- stable registry references,
- avoid inserting timestamps, random IDs, or reordering fixed lists inside the cacheable prefix.

### GPT-5.x caching alignment

OpenAI prompt caching requires:
- prompts ≥ 1024 tokens, citeturn8view0  
- exact prefix matches, with static content first and dynamic content last, citeturn8view1  
- and benefits from `prompt_cache_key` routing (especially when many requests share common prefixes). citeturn8view1  

Retention is defined as:
- in-memory caching that typically persists 5–10 minutes of inactivity (sometimes up to an hour), citeturn8view1turn8view4  
- plus an extended retention mode that keeps cached prefixes active longer (up to 24 hours) on supported models including gpt-5.4. citeturn8view1  

Pricing explicitly distinguishes cached input. citeturn7view3

OpenAI also notes that **structured output schemas** can be cached because the schema is treated as prefix content. citeturn8view1 Practically, if your reviewer produces standardized findings (JSON) and you keep the schema stable, you can reduce both parsing friction and costs for repeated schema tokens.

### When compression hurts caching

Compression hurts caching when it changes the prefix byte-level representation across passes, because both Anthropic and OpenAI caching require exact prefix reuse for hits. citeturn8view1turn7view0 This can happen if:
- your compressor is non-deterministic (“rewrites” headers differently each time),
- it moves content around,
- or it normalizes whitespace inconsistently.

This is why “cache mode” concepts matter. Headroom includes an explicit `cache` mode to freeze prior turns and prioritize provider prefix-cache stability, suggesting that cache preservation and token compression are sometimes competing objectives that must be tuned per workflow. citeturn2view1turn2view0


## Benchmarking protocol for compression effectiveness

### Deliverable 4: step-by-step benchmark methodology

This protocol is designed to be executable immediately within your existing file-based workflow, with minimal new tooling.

**Baseline capture**
1. For each MEU, record:
   - artifact token counts (by file) and aggregate “context sent” size,
   - number of passes to acceptance,
   - latency per model call (TTFT and total),
   - and review quality outcomes (defined below).
2. Capture provider-native token accounting:
   - For OpenAI, log `usage.prompt_tokens_details.cached_tokens` (cache hits) along with total prompt tokens and completion tokens. citeturn8view0turn8view2  
   - For Anthropic, log `usage.input_tokens`, and when caching is enabled, `cache_read_input_tokens` and `cache_creation_input_tokens` (cache reads vs writes). citeturn7view0turn1search17  

If you introduce Headroom, also log “before vs after” token counts. Headroom documents an internal metrics table design that captures tokens before/after optimization and the transforms applied. citeturn6view7turn4view2

**A/B testing**
3. Select matched MEUs (same category, similar diff size), and run:
   - A: uncompressed handoffs
   - B: compressed handoffs (one strategy at a time)
4. Keep the reviewer prompt and acceptance criteria identical; only the handoff format changes.

**Quality metrics**
5. Define findings quality in objective terms:
   - *True positive findings*: issues flagged that are confirmed and fixed before acceptance.
   - *False positives*: issues flagged that are incorrect or irrelevant (wasted cycles).
   - *Misses*: issues found later (by tests, by humans, or by later passes) that *should* have been caught earlier.
6. Operationalize “misses” with post-hoc labeling:
   - Compare the final accepted implementation vs earlier review pass findings; any later-discovered defects count as misses for earlier passes.
   - For high-signal MEUs, add a lightweight human adjudication pass to label findings.

**Degradation threshold**
7. Sweep compression ratios (e.g., 0%, 30%, 50%, 60%, 70%, 80%) and measure:
   - Δ(pass count to acceptance),
   - Δ(false positive rate),
   - Δ(miss rate),
   - and the distribution shift in “what kinds of issues are missed.”
8. Identify the highest compression level that maintains acceptable miss/FP rates (your “quality floor”). This is particularly important because long contexts can degrade performance even when the relevant evidence is present, implying that shortening prompts can *increase* quality even while aggressively dropping irrelevant tokens. citeturn11academia42turn11search0  

**Pilot selection**
9. Start with MEUs where the ground truth is easiest to validate:
   - straightforward CRUD or refactors with strong unit tests,
   - changes with deterministic failing tests (easy to measure miss rate),
   - changes with well-scoped blast radius (few files).
10. Delay “architecture change” MEUs until your compression scheme has proven it preserves nuance, because these tend to rely heavily on narrative rationale (summarizable content) and can be sensitive to over-compression.

This protocol doubles as a “prompt caching benchmark,” since you can attribute improvements to cached token proportions and retention settings. citeturn8view1turn7view0


## Alternative approaches assessment and decision matrix

### Assessment highlights

**Binary evidence formats (Protocol Buffers / CBOR)**  
Binary formats can reduce network payload and parsing overhead and are designed for compact representation. CBOR’s design goals explicitly include small message size and extensibility. citeturn12search1turn12search5 Protocol Buffers are described as “smaller and faster” than JSON and provide a defined wire format. citeturn12search6turn12search2  
However, an LLM cannot directly “read” binary as-is; if you base64-encode it into a prompt, you usually *increase* token count. So binary formats become valuable only when paired with **retrieval keys**: store large evidence blobs as CBOR/Protobuf *outside* the prompt, include only a handle in the handoff, and have a tool fetch and decode on demand.

**Git-like differential handoffs**  
Unified diffs are a mature, compact representation of changes that explicitly omits redundant context lines. citeturn12search3turn12search23 They align naturally with “delta-only” review: send a patch plus minimal narrative and let the reviewer reason over what changed, not over what stayed the same.

**Hierarchical summarization**  
This is a structured “context rot” mitigation: maintain multi-level versions of the same artifact (L0 full, L1 compressed, L2 ultra-summary). The reviewer reads L2 by default and requests expansions of L1/L0 sections as needed. This matches the general retrieval-based mitigation direction implied by both ADOL and CCR-style reversible compression. citeturn10view0turn5view3

**Model tiering for review**  
Use a cheaper model to perform a first-pass lint/review and reserve the expensive reviewer for the final pass. OpenAI’s pricing table shows large cost differences between gpt-5.4 and lighter variants (mini/nano), supporting an economic rationale for triage. citeturn7view3

**Context partitioning**  
Split one long handoff into smaller, independently processed documents (e.g., “tests & evidence,” “diff,” “rationale,” “open questions”). This reduces “lost in the middle” risk by keeping each reasoning context small. citeturn11search0

**Retrieval-augmented handoffs**  
Keep the handoff short and retrieval-keyed; store full evidence in an index (vector DB or structured store). This directly targets the “length alone hurts” effect by turning a long-context task into a short-context task. citeturn11academia42turn11search12


### Deliverable 2: implementation decision matrix

| Approach | Effort (days) | Token Savings | Quality Risk | Infrastructure Needs | Recommended Phase |
|---|---:|---|---|---|---|
| Template optimization | 1–3 | Medium (often 20–40%) | Low | None | Phase 1 |
| Delta-based handoffs | 3–7 | High on later passes (often 50%+ vs resend-full) | Medium (reconstruction mistakes) | Small (versioning + patch apply) | Phase 2 |
| Structured compression | 5–10 | High (30–70% depending on classes) | Medium (if mis-tagged) | Small (preprocessor + validators) | Phase 2 |
| Headroom SDK | 3–10 | Very high for tool outputs/logs (70–95% claimed focus) | Low–Medium (depends on reversible settings) | Moderate (proxy/SDK + observability) | Phase 3 |
| ADOL protocol | 7–20 | High (systemic dedupe + adaptive inclusion) | Medium (protocol complexity) | Moderate (registry + negotiation files) | Phase 3 |
| Prompt caching optimization | 1–5 | Medium to very high for stable prefixes (provider-dependent) | Low | Low–Moderate (prefix discipline + metrics) | Phase 1 |

Notes:
- Prompt caching has strict prefix constraints for cache hits. citeturn8view1turn7view0  
- Headroom includes explicit modes to prioritize token reduction vs cache stability, which is relevant in a multi-pass workflow where stable prefixes matter for caching. citeturn2view1turn2view0  


## Recommended architecture for the Zorivest dual-agent system

### Deliverable 3: concrete, implementable architecture

This architecture is designed to address all four pain points simultaneously: linear token costs, boilerplate waste, context rot, and delta-less updates—while also *maximizing prompt caching* and keeping expansion available via retrieval.

**Core design principle:** make the default artifact “thin,” stable, and cacheable, and push bulk into verifiable, retrievable stores.

### Phase 1: stabilize structure, unlock caching, and prevent context rot

1. **Adopt a canonical handoff template**
   - YAML front matter for IDs, pass number, base ref, delta ref, test summary, and evidence index.
   - Fixed section ordering.
   - Strict length budgets (e.g., “Reviewer TLDR must be ≤ N tokens” enforced by lint).

2. **Introduce a schema registry**
   - One file defines standard sections and evidence formats.
   - Handoffs reference schema version IDs. This is the “schema deduplication” idea from ADOL applied to markdown. citeturn10view0  

3. **Cache-aware layout**
   - Put stable instructions, schemas, and “how to read this file” text first.
   - Move all pass-specific content to the end to preserve exact prefix caching requirements. citeturn8view1turn7view0  
   - For OpenAI calls, set a consistent `prompt_cache_key` per project/MEU to improve routing stability. citeturn8view1  
   - For Anthropic calls, explicitly mark cacheable blocks and avoid dynamic content inside them; respect minimum cacheable lengths. citeturn7view1turn1search17  

**Success metrics for Phase 1**
- Reduced prompt tokens per pass.
- Increased cached token counts (OpenAI `cached_tokens`; Anthropic cache read tokens). citeturn8view0turn7view0  
- Reduced pass count variability (a proxy for reduced context rot).

### Phase 2: delta-first review loops

4. **Make deltas the first-class payload**
   - For code and markdown changes: unified diff referenced by path and hash. citeturn12search3  
   - For structured metadata: JSON Patch for machine-applied updates. citeturn12search0  
   - Handoff artifact mostly becomes “what changed + minimal rationale + evidence handles.”

5. **Deterministic reconstruction**
   - A local “reconstructor” rebuilds full artifacts from base + deltas.
   - Adds a checksum at the end of the reconstructed file to prevent drift.

**Success metrics for Phase 2**
- Median tokens sent per pass drops sharply after pass 1.
- Review quality remains stable (miss/FP rate does not increase).

### Phase 3: reversible compression and shared stores

6. **Adopt reversible compression for bulky evidence**
   - Store full evidence (logs, long tables, repeated fixtures) outside the handoff.
   - In the handoff, include:
     - a compressed slice (top failures, outliers, error rows),
     - plus a retrieval key.

This mirrors CCR behavior: compressed output includes a marker with a reference key, and the system can retrieve the full original when needed. citeturn5view3turn5view4

7. **Integrate Headroom selectively**
   - Use **SharedContext** for cross-agent handoffs where large context gets replayed; the default read returns an ~80% smaller summary with a `full=True` escape hatch. citeturn4view0  
   - If you route model calls through Headroom proxy, choose:
     - `cache` mode when cache hit rate is the bottleneck (many repeated prefixes). citeturn2view1turn2view0  
     - `token` mode when raw token volume is the bottleneck and prefix stability is less critical. citeturn2view1turn2view0  
   - Use Headroom’s latency benchmarks to validate net latency impact in your own mix of payloads. citeturn5view5turn5view7  

**Success metrics for Phase 3**
- Large reductions in “evidence tokens” (tool outputs, logs).
- Review passes decrease because the reviewer is no longer overwhelmed by non-informative boilerplate.

### Common pitfalls to avoid

- **Over-compressing verbatim evidence**: models need exact file paths, exact failing assertions, and exact error messages to avoid phantom fixes; treat those as “verbatim class.”  
- **Breaking cache prefixes unintentionally**: timestamps, nondeterministic ordering, and “pretty printing” changes can destroy cache hit rates for both Anthropic and OpenAI, which both require exact prefix alignment for hits. citeturn8view1turn7view0  
- **Anthropic cache writes without reuse**: if your per-pass cadence exceeds TTL and you keep writing caches with few reads, the 1.25× write premium can cost more than disabling caching. citeturn1search17turn7view1  
- **Letting delta chains grow unbounded**: without periodic rebases, agents can lose confidence in what the “current truth” is.
