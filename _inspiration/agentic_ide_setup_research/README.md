# Agentic IDE Setup — Research Directory

## Purpose

Research and synthesis for the `zorivest_setup_workspace` MCP tool (MEU-165 expansion).

## Files

### Research Prompts (→ sent to each platform)

| File | Platform | Focus |
|------|----------|-------|
| `gemini-3.1-pro-prompt.md` | Gemini 3.1 Pro | Landscape survey |
| `gpt-5.4-prompt.md` | GPT-5.4 | Engineering patterns |
| `claude-opus-4.6-prompt.md` | Claude Opus 4.6 | DX & convention design |

### Research Reports (← received from each platform)

| File | Platform | Lines | Key Contributions |
|------|----------|:-----:|-------------------|
| `_gemini-Agentic IDE Scaffolding Landscape Survey.md` | Gemini 3.1 Pro | 288 | Ecosystem map, 54 citations, AST merge gap, CVE-2025-54136 |
| `_chatgpt-zorivest_setup_workspace_research.md` | GPT-5.4 | 308 | Safe write patterns, backup+replace, TypeScript snippets |
| `_claude-Agentic workspace configuration...` | Claude Opus 4.6 | 204 | Progressive tiers, hub-and-spoke model, ToxicSkills audit |

### Synthesis

| File | Description |
|------|-------------|
| **`research-synthesis.md`** | ⭐ **Unified synthesis** — 3-way agreement matrix, resolved architecture, implementation roadmap |

## Architecture Decision

Feature maps to **expanded MEU-165** (`mcp-ide-config`) in the `core` toolset, implemented as `zorivest_setup_workspace` in `mcp-server/src/tools/setup-tools.ts` with static templates in `mcp-server/templates/agent/`.
