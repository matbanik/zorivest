# Gemini Deep Research Prompt: LLM Context Compression for Multi-Agent Handoff Optimization

> **Platform**: Google Gemini (Deep Research mode)
> **Leverage**: Long-context window, multi-source synthesis, technical architecture evaluation, Google Scholar integration
> **Estimated output**: 8,000–15,000 words

---

## Research Request

I am building a dual-agent software development system where:
- **Agent A** (Anthropic Claude Opus 4.6) implements code using strict TDD methodology and produces structured handoff artifacts
- **Agent B** (OpenAI GPT-5.4) acts as an adversarial reviewer/validator that runs tests, reviews code, and produces findings documents

The handoff artifacts between these agents are 2,000–15,000 token structured markdown documents containing: test results, code diffs, evidence bundles, acceptance criteria verification, and architectural decisions. These flow through a file-based protocol (not API-to-API) — artifacts are written to disk and read by the next agent.

**The core problem**: Token bloat in handoff artifacts degrades reasoning quality, increases latency, and wastes budget. Both agents must process full prior context to maintain consistency, but much of this context is redundant (repeated file paths, boilerplate test output, schema definitions that don't change between MEUs).

I need a comprehensive technical analysis comparing all viable approaches to compressing and optimizing this inter-agent communication. Please research the following sources and synthesize findings:

---

## Sources to Analyze (with specific questions per source)

### 1. ACON Framework (Microsoft Research)
- **Paper**: "ACON: Evaluating and Advancing Context Compression for Long-Horizon Agents" (arXiv:2510.00615)
- **Repo**: https://github.com/microsoft/acon

**Questions**:
- What compression strategies does ACON benchmark (truncation, summarization, RAG-based, selective pruning)?
- What are the measured performance retention rates at various compression ratios for code-related tasks?
- Does ACON evaluate agent-to-agent handoff scenarios, or only single-agent trajectory compression?
- What metrics does ACON use to measure "compression quality" beyond task success rate?
- Can ACON's evaluation framework be adapted to measure handoff artifact quality in a dual-agent TDD workflow?

### 2. Headroom (Context Optimization Layer)
- **Repo**: https://github.com/chopratejas/headroom
- **Docs**: Architecture overview, SharedContext mechanism, CCR (Compress-Cache-Retrieve)

**Questions**:
- How does Headroom's proxy mode work with file-based handoffs (not API calls)?
- Can the SharedContext mechanism support cross-agent state sharing when agents run in separate processes?
- What is the CCR (Compress-Cache-Retrieve) mechanism and how does it ensure lossless retrieval of compressed details?
- What compression ratios does Headroom claim for structured data (JSON, markdown, test output)?
- How does Headroom handle domain-specific content (code snippets, file paths, test assertions) that must remain verbatim?
- What is the "Smart Crusher" component and how does it differ from generic LLM summarization?

### 3. ADOL — Agentic Data Optimization Layer (IETF Draft)
- **Spec**: draft-chang-agent-token-efficient-02 (January 2026)
- **URL**: https://datatracker.ietf.org/doc/draft-chang-agent-token-efficient/02/

**Questions**:
- ADOL targets MCP and A2A protocol token bloat. Can its four optimization dimensions (schema deduplication, adaptive optional inclusion, controllable response verbosity, context-aware tool selection) apply to file-based markdown handoffs?
- How does schema deduplication via JSON `$ref` translate to structured markdown documents with repeating sections?
- What is "controllable response verbosity" and how could it be implemented as a handoff template system?
- Does ADOL address the problem of repeated boilerplate across sequential handoffs in the same project?

### 4. ContextEvolve (Multi-Agent Context Compression)
- **Paper**: "ContextEvolve: Multi-Agent Context Compression for Systems Code Optimization" (arXiv:2602.02597)

**Questions**:
- ContextEvolve decomposes context into three orthogonal dimensions: semantic state, optimization direction, and experience distribution. How does this decomposition map to TDD handoff artifacts (test state, code changes, lessons learned)?
- Can the Summarizer/Navigator/Sampler agent pattern be adapted for a reviewer↔implementer agent loop?
- ContextEvolve claims 29% token reduction with 33% performance improvement. What is the mechanism that enables *better* performance with *less* context?

### 5. Provence (Trained Context Pruner)
- Referenced in multiple context engineering articles as achieving up to 95% compression while retaining relevant information

**Questions**:
- What is Provence's approach to identifying "relevant" vs "irrelevant" content?
- How does it handle code-specific content where a single changed character can be semantically critical?
- Is Provence available as a library/service, or is it research-only?

### 6. Microsoft Semantic Kernel — ChatHistoryReducer
- **Approach**: ChatHistorySummarizationReducer and ChatHistoryTruncationReducer

**Questions**:
- How does Semantic Kernel's approach compare to Headroom for managing conversation state compression?
- Can ChatHistoryReducer patterns be applied to file-based artifacts (not chat history)?

### 7. Context Engineering Best Practices (Production Systems, 2025–2026)
- **Sources**:
  - "Effective Context Engineering for AI Agents" (tianpan.co, Feb 2026)
  - "The LLM Context Problem in 2026" (LogRocket)
  - "Context Ranking and Token Budgeting" (Bitloops)
  - "Context Engineering for AI Agents: Token Economics" (Maxim AI)

**Questions**:
- What are the four core strategies (write, select, compress, isolate) and how do they apply to dual-agent handoffs?
- What token budget allocation ratios are recommended for different context components?
- What compression ratios are achievable in production (3:1 to 5:1 for history, 10:1 to 20:1 for tool outputs)?
- What is the "100:1 input-to-output ratio" finding and what does it imply for handoff design?
- What is "context rot" and at what token threshold does it accelerate?

---

## Synthesis Requirements

After analyzing all sources, produce:

### A. Comparative Analysis Table
Compare all approaches across these dimensions:
| Dimension | ACON | Headroom | ADOL | ContextEvolve | Provence | Semantic Kernel | Manual Template |
|---|---|---|---|---|---|---|---|
| Integration complexity | | | | | | | |
| Compression ratio (structured data) | | | | | | | |
| Domain-specificity (code/TDD) | | | | | | | |
| Lossless retrieval capability | | | | | | | |
| File-based handoff support | | | | | | | |
| Production readiness | | | | | | | |
| Cross-agent state sharing | | | | | | | |
| Cost (API calls, compute) | | | | | | | |

### B. Architecture Recommendation
For the specific use case of:
- File-based markdown handoff artifacts (2K–15K tokens)
- Two agents that don't share memory (separate processes, possibly separate machines)
- Structured content: test results, code diffs, acceptance criteria, evidence bundles
- Requirement: compressed artifacts must be self-contained (no shared database needed)
- Requirement: certain content (test assertions, file paths, code snippets) must remain verbatim

Recommend a layered approach:
1. **Transport layer**: What protocol/format optimizations apply?
2. **Content layer**: What compression strategy for each content type?
3. **Retrieval layer**: How to ensure the receiving agent can request uncompressed details?

### C. Implementation Roadmap
Phase 1 (zero infrastructure): Template-based compression using handoff format redesign
Phase 2 (lightweight tooling): Tool-assisted compression for specific content types
Phase 3 (full integration): SDK/proxy integration with compression pipeline

### D. Risk Assessment
- What are the risks of lossy compression in a TDD/code review workflow?
- At what compression ratio does task performance degrade for code-related tasks?
- What is the "information cliff" — the point where compression causes catastrophic failure?

### E. Alternative Approaches Not Covered Above
- Are there any other tools, frameworks, papers, or approaches I should consider?
- What about differential handoffs (only sending deltas between sequential artifacts)?
- What about structured logging compression (e.g., using protocol buffers or CBOR for evidence data)?
- What about model-native features (Claude's prompt caching, GPT's structured outputs) as compression mechanisms?

---

## Output Format
Please structure your response as a technical research report with:
1. Executive summary (500 words)
2. Detailed analysis per source (with citations)
3. Comparative table
4. Architecture recommendation with diagrams
5. Implementation roadmap with effort estimates
6. Risk assessment matrix
7. References with URLs
