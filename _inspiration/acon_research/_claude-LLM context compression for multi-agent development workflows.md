# LLM context compression for multi-agent development workflows

**Only one of the five named tools — Headroom — is production-ready and directly suited for compressing inter-agent handoff artifacts in a TDD workflow.** Two others (ACON, Provence) exist as research projects, ContextEvolve is an academic framework for a different problem, and ADOL does not appear to exist at all. The broader ecosystem of context compression, prompt caching, and multi-agent communication optimization has matured substantially in 2024–2026, with practical tools like LLMLingua, RTK, and prompt caching delivering **2×–20× token reductions** without significant reasoning quality loss.

The core insight from the research: **prevention beats compression**. Structured context objects (200–500 tokens per handoff vs. 5,000–20,000 for full context forwarding), targeted information retrieval, and strategic prompt caching yield 3–4× more context life than post-hoc compression alone. For TDD workflows specifically, test result summarization is the highest-ROI quick win — reducing 300 lines of test output to a single status line saves **95%+ tokens** with zero meaningful information loss.

---

## The five named tools: one winner, one ghost, three researchers

### Headroom — the only production-ready option

Headroom is an actively maintained context optimization layer (Apache-2.0, Python 3.10+, beta) that works as a transparent proxy, Python/TypeScript SDK, or framework integration with LangChain, LiteLLM, Agno, Strands, and MCP. Its GitHub repo lives at `github.com/chopratejas/headroom`, and it installs via `pip install headroom-ai` or `npm install headroom-ai`.

The architecture is built around a **ContentRouter** that auto-detects content types and routes to specialized compressors. JSON arrays go to SmartCrusher (statistical compression), code goes through an **AST-aware CodeCompressor** supporting Python, JS, Go, Rust, Java, and C++, text hits Kompress (ModernBERT-based), and logs get their own compressor. Claims **40–90% token reduction** with zero LLM calls.

Three features make Headroom uniquely suitable for TDD inter-agent handoffs:

- **SharedContext**: `from headroom import SharedContext` enables cross-agent persistent memory with agent provenance tracking and auto-dedup. One agent writes compressed research; another reads it. This directly solves the inter-agent artifact passing problem.
- **CCR (Compress-Cache-Retrieve)**: A lossless architecture that compresses aggressively, stores originals locally, and gives the LLM a `headroom_retrieve()` tool to fetch full details on demand. No data is permanently lost.
- **CacheAligner**: Stabilizes message prefixes to maximize KV cache hits, exploiting Anthropic's **90% cached token discount**. This is a multiplier on top of content compression.

For TDD workflows, test results (JSON), code diffs, and log outputs all route automatically to appropriate compressors. When compressing 500 test items down to 20, it tells the model what was omitted ("87 passed, 2 failed, 1 error") so the model knows when to request more detail.

### ADOL — does not appear to exist

Extensive searching for "ADOL" as an LLM verbosity control protocol yielded no matching results. The closest matches — ADOL-C (automatic differentiation library), AD-LLM (anomaly detection benchmark), ADLM (diffusion language model) — are entirely unrelated. This name may be fabricated, confused with something else, or refers to an internal/unpublished project.

Tools that **do** address LLM verbosity control include **Codespeak AI Protocol** (`github.com/Codespeak-AI-Protocol/Codespeak-AI-Protocol-v1.0`), a token-efficient shorthand protocol, and **Caveman-lang** (`github.com/StealthyLabsHQ/caveman-lang`), which forces LLMs to respond with **60–90% fewer tokens** through extreme brevity constraints. The OPTIMA research (Tsinghua University, ACL 2025) demonstrated that training agents specifically for communication efficiency achieves **2.8× performance gain with less than 10% of the tokens** — showing that verbosity control through fine-tuning dramatically outperforms prompt-level approaches.

### ACON — promising Microsoft research, not production-ready

ACON (Agent Context Optimization) is a gradient-free framework from Microsoft researchers for compressing both environment observations and interaction histories in long-horizon LLM agents. Paper: `arxiv.org/abs/2510.00615`, code at `github.com/microsoft/acon`.

Its core method is **failure-driven compression guideline optimization**: given paired trajectories where full context succeeds but compressed context fails, an LLM analyzes the failure cause and updates compression guidelines in natural language. Two variants exist — ACON UT (utility maximization) and ACON UTCO (utility + compression maximization). It reduces peak tokens by **26–54%** while preserving task performance and supports distillation into smaller models (Qwen3-14B, Phi-4) that preserve **95%+ accuracy**.

For TDD handoffs, ACON's methodology could inspire custom compression guideline optimization, but it requires significant integration work. It's a research framework, not a drop-in tool.

### ContextEvolve — code optimization framework, not general decomposition

ContextEvolve (`arxiv.org/abs/2602.02597`, February 2026) is a multi-agent framework for systems code optimization that uses context compression as a mechanism, not a standalone decomposition tool. It decomposes optimization context into three orthogonal dimensions via a Summarizer agent (condenses semantic state), Navigator agent (distills optimization direction), and Sampler agent (curates experience distribution). On the ADRS benchmark it outperforms baselines by **33.3%** while reducing token consumption by **29.0%**. The three-dimensional decomposition concept is intellectually interesting but not directly applicable as a general-purpose tool for inter-agent communication.

### Provence — high-quality RAG pruner, wrong domain

Provence (Pruning and Reranking Of retrieVEd relevaNt ContExts) is a sentence-level context pruner for RAG pipelines, accepted at **ICLR 2025** and developed by Naver Labs Europe. Paper: `arxiv.org/abs/2501.16214`. Models available on HuggingFace at `naver/provence-reranker-debertav3-v1`. An open-source implementation exists at `github.com/hotchpotch/open_provence` (MIT license, 30M–310M params).

Built on DeBERTa-v3 with a dual-head architecture (pruning head for token-level binary masks, reranking head for passage relevance scoring), it achieves **50–80% compression** with minimal QA performance drop. Training uses silver labels from LLaMA-3-8B. However, it operates on natural language passages in question-context pair format — not on code, test results, or structured development artifacts. **Low suitability** for TDD workflows without substantial adaptation.

---

## Prompt caching turns shared context into a cost multiplier

Anthropic's prompt caching is the single highest-impact optimization for multi-agent systems sharing common context. Cache reads cost **only 10% of base input price** — a 90% discount on cached tokens. For Claude Sonnet 4.5, that means cached input drops from the base rate to a fraction of the cost.

The mechanism is prefix-based: the system checks whether a prompt prefix (up to a specified cache breakpoint) is already cached, then reuses the cached KV computation. Two modes exist — automatic (single `cache_control` field, system manages breakpoints) and explicit (fine-grained control over up to **4 breakpoints** per request). Default cache TTL is **5 minutes** (refreshed on each hit); extended TTL of **1 hour** is available at additional cost on newer models.

The critical constraint is that caching is prefix-based: any change in the middle invalidates everything after it. This means **prompt architecture matters enormously**. The optimal structure for multi-agent systems:

1. Place static content first (system prompts, tool definitions, shared instructions)
2. Push dynamic/volatile content to the end
3. Avoid timestamps or request-specific data in system prompts
4. Share system prompt caches across agents running the same role

A PwC study (`arxiv.org/abs/2601.06007`) found prompt caching reduces API costs by **45–80%** and improves time-to-first-token by **13–31%** across providers. Critically, **full context caching can paradoxically increase latency** by caching dynamic tool results — strategic boundary control outperforms naive approaches. ProjectDiscovery's Neo agent (a multi-agent security testing platform) achieved **59% cost reduction** with 90%+ cache hit rates on optimized paths.

OpenAI's prompt caching is fully automatic (no code changes), offering up to **50% discount** (90% on GPT-4.1). Google's Gemini provides implicit caching (75% discount on 2.5+ models) and explicit caching (up to **90% discount** with configurable TTL). Headroom's CacheAligner specifically optimizes for these discounts by stabilizing message prefixes.

---

## Delta-based handoffs are the production consensus

The multi-agent community has converged on **structured context objects** as the practical sweet spot between full-state forwarding and aggressive compression. This approach maintains a typed context object (customer_id, detected_intent, extracted_entities) and passes only relevant fields — typically **200–500 tokens** vs. 5,000–20,000 for full forwarding. LangGraph uses typed state channels, CrewAI uses shared memory objects, and Google ADK explicitly scopes sub-agent context.

Microsoft's AG-UI protocol implements a formal delta pattern using JSON Patch format:
```json
{"type": "STATE_DELTA", "delta": [{"op": "replace", "path": "/recipe", "value": {...}}]}
```
STATE_DELTA events stream in real-time during generation, with a final STATE_SNAPSHOT emitted on completion. This two-phase approach (generate structured update, then generate user-friendly summary) separates machine-readable state from human-readable output.

A foundational research paper from Tsinghua University ("Augmenting Multi-Agent Communication with State Delta Trajectory," `arxiv.org/abs/2506.19209`) demonstrated that natural language communication introduces **inevitable information loss** as continuous state vectors are downsampled to discrete tokens. Their approach transfers both tokens and token-wise hidden state changes between agents, outperforming NL-only communication on complex reasoning tasks. However, this requires model internal access and isn't feasible for black-box API models.

Google ADK's architecture articulates the clearest production principle: **sessions are durable ground truth (full state); working context is a computed projection (delta/filtered view) shipped to the LLM per invocation**. Context is built through named, ordered processors — not ad-hoc string concatenation. This is effectively a delta approach at the architecture level.

For TDD workflows, the practical pattern is: maintain full state in an orchestrator, compute minimal context views per agent invocation, and use Factory.ai-style **anchored iterative summarization** (structured sections: completed work, current state, pending tasks, file modifications, key decisions) to compress conversation history at handoff boundaries. This scored **4.04/5** on accuracy in evaluations of 36K+ messages.

---

## Token reduction for development artifacts yields 60–95% savings

The highest-ROI techniques for TDD artifacts, ordered by impact:

**Test results** are the easiest win. A test suite running 80+ integration tests produces ~300 lines of output (~2,000+ tokens). Replacing this with "All 80 integration tests passed. Suites: Consumer (13), HealthChecker (8), Producer (7)" saves **95%+ tokens** with zero information loss for the passing case. For failures, include only the failing test name, assertion message, and relevant stack frame.

**CLI and shell output** benefits from RTK (`github.com/rtk-ai/rtk`), a Rust CLI proxy that reduces token consumption by **60–90%**. `rtk git diff` returns condensed diffs; `rtk git status` returns compact status; `rtk json config.json` shows structure without values. Works with Claude Code, Cursor, Codex, and Gemini CLI with <10ms overhead.

**Code diffs** benefit from syntax-aware diffing via Difftastic (understands code grammar) combined with Tree-Sitter (incremental ASTs). Morph's Fast Apply uses compact diffs instead of full file rewrites at **10,500 tokens/second**. For inter-agent handoffs, sending only the changed functions rather than full files is the single most effective structural optimization.

**Structured data** benefits from format optimization. TOON (Token-Oriented Object Notation) replaces verbose JSON with CSV-style schema-driven format, declaring field names once instead of repeating per object, achieving **40–50% token reduction**. Headroom's SmartCrusher automates this for JSON arrays.

**Conversation history** is best compressed via Morph's verbatim compaction (50–70% reduction, zero hallucination risk) rather than LLM summarization, which corrupts file paths, line numbers, and error messages. The TDAD research (Test-Driven Agentic Development) found a critical paradox: adding verbose TDD procedural instructions without targeted test context actually **increased regressions** from 6.08% to 9.94%. Surfacing contextual information outperforms prescribing procedural workflows.

---

## Long context degrades reasoning — compression can actually help

The "Lost in the Middle" paper (Liu et al., TACL 2024) established that LLM performance follows a **U-shaped curve**: accuracy is highest when relevant information sits at the beginning or end of the context and drops **30%+ when information is in the middle**. This was observed across GPT-3.5 Turbo, GPT-4, Claude 1.3, and LLaMA-2 variants. The root cause is architectural: Rotary Position Embedding (RoPE) introduces a decay effect favoring sequence boundaries.

Chroma's "Context Rot" research (July 2025) tested 18 frontier models including GPT-4.1, Claude Opus 4, and Gemini 2.5, finding that **every single model** performed worse as input length increased. The degradation wasn't gradual — models maintained near-perfect accuracy up to a threshold, then performance **dropped off a cliff**. Models scoring 95% on shorter inputs collapsed to **60%** at longer inputs. Critically, semantically similar but irrelevant content (distractors) caused degradation **beyond what context length alone explains**.

The effective context window often falls **far below the advertised maximum — by up to 99%** on complex tasks. A 1M-token window can exhibit significant degradation at 50K tokens.

This means context compression can **improve** reasoning quality by:
1. Removing distractor content that triggers lost-in-the-middle effects
2. Increasing key information density in remaining tokens
3. Reducing the model's attention burden (transformer attention is quadratic)

LLMLingua benchmarks confirm this. On NaturalQuestions, LongLLMLingua achieved **21.4% performance improvement** using only **1/4 of the tokens** at 4× compression with GPT-3.5-Turbo. On code completion (RepoBench), LLMLingua achieved a **1.4 point improvement** at 6× compression. The safe compression ranges, based on accumulated benchmarks:

- **2×–4× compression**: Generally safe with minimal loss across all tasks and methods
- **4×–6× compression**: Achievable with question-aware methods (LongLLMLingua); may actually improve RAG performance
- **10×–20× compression**: Achievable on reasoning tasks with ~1.5 percentage point loss
- **Beyond 20×**: Requires soft-prompt methods with model fine-tuning; loses cross-model portability

---

## Practical implementation recommendations for TDD agent workflows

The most effective stack for compressing inter-agent handoffs in a TDD development workflow combines three layers:

**Layer 1 — Prevention (highest impact).** Use RTK for CLI output compression (60–90% savings), AST-aware code diffing instead of full file transfers, and test result summarization (95% savings on passing suites). Structure your orchestrator to maintain full state but compute minimal context projections per agent invocation. Adopt the TDAD pattern of surfacing targeted test context rather than prescribing verbose procedures.

**Layer 2 — Compression (medium impact).** Deploy Headroom as a transparent proxy for automatic content-type detection and compression. Use SharedContext for cross-agent artifact passing with auto-dedup. The CCR architecture ensures agents can retrieve full details on demand, preventing information loss. For natural language context, LLMLingua-2 (`github.com/microsoft/LLMLingua`) provides **3–6× faster compression** than the original at BERT-level encoder costs.

**Layer 3 — Caching (cost multiplier).** Architect prompts to maximize Anthropic prompt caching hits: static tool definitions and system prompts first, dynamic content last. Use 1-hour extended TTL for shared agent role definitions. Headroom's CacheAligner automates prefix stabilization. Expected savings: **45–80% cost reduction** on top of compression savings.

The key tools and repositories worth implementing:

- **Headroom**: `github.com/chopratejas/headroom` — most complete solution for the described use case
- **RTK**: `github.com/rtk-ai/rtk` — CLI proxy for dev command token optimization
- **LLMLingua**: `github.com/microsoft/LLMLingua` — proven prompt compression with 4K+ GitHub stars
- **OPTIMA**: `github.com/thunlp/Optima` — if fine-tuning agents for communication efficiency is feasible
- **PCToolkit**: unified toolkit integrating 5 compression methods for benchmarking
- **Prompt Compression Survey**: `github.com/ZongqianLi/Prompt-Compression-Survey` — comprehensive paper collection (NAACL 2025 selected oral)

## Conclusion

The landscape has shifted from "how do we fit more into the context window" to "how do we send less while preserving reasoning quality." The evidence is clear that **leaner context often produces better results** than stuffing the full window, because attention degradation and distractor interference are real architectural constraints in every frontier model tested. For a TDD dual-agent workflow, the combination of structured context objects at the orchestration layer, Headroom for automatic content-aware compression, prompt caching for cost multiplication, and aggressive test output summarization represents the most practical, implementable approach available today. The total token reduction across all layers is conservatively **80–95%** compared to naive full-context forwarding, with reasoning quality that is maintained or improved.
