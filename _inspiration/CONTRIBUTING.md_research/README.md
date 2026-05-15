# CONTRIBUTING.md Research Prompts

This folder contains **three deep research prompts**, each tailored to the unique strengths of a specific AI deep research provider. Together, they provide comprehensive coverage of how to create world-class contribution guidelines for the Zorivest open-source project.

## Provider Capabilities & Prompt Strategy

| Provider | Model/Mode | Strengths | Prompt Focus |
|:---------|:-----------|:----------|:-------------|
| **Gemini** | Deep Research Max (Gemini 3.1 Pro) | Autonomous multi-step web browsing, plan-refine loop, structured reports with native visualizations, Google Workspace integration | **Breadth**: Crawl 100+ repos, extract patterns, build comparative tables. Export as Google Doc for team review. |
| **ChatGPT** | Deep Research (GPT-5.2/o3) | Iterative synthesis across hundreds of sources, PDF/image interpretation, export to Word/PDF, real-time progress tracking | **Depth**: Analyze friction points in PR review workflows, extract anti-patterns from post-mortems, produce actionable checklists. |
| **Claude** | Deep Research (Opus + extended thinking + web search) | Multi-agent orchestrator-worker architecture, extended thinking with interleaved reasoning, deep code-level analysis | **Architecture**: Design the file structure, evaluate AI-agent guidance patterns (AGENTS.md, llms.txt), produce draft templates. |

## How to Use

1. **Start with Gemini** — it will produce the broadest survey across many repositories
2. **Then ChatGPT** — it will dive deeper into review friction, security practices, and checklists  
3. **Finally Claude** — it will synthesize findings and produce draft file templates

Each prompt is self-contained and can be used independently.

## Files

- `gemini-prompt.md` — Broad survey prompt optimized for Gemini Deep Research Max
- `chatgpt-prompt.md` — Deep analysis prompt optimized for ChatGPT Deep Research  
- `claude-prompt.md` — Architecture & synthesis prompt optimized for Claude Deep Research
