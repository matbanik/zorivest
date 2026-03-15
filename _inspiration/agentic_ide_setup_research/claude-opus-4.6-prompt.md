# Deep Research Prompt — Claude Opus 4.6

## Research Mission: Developer Experience & Convention Design for Agentic Workspace Setup

You are conducting a nuanced analysis of developer experience (DX) design, convention choices, adoption patterns, and trust/security considerations for an MCP tool that scaffolds agentic IDE configurations. Your strength in philosophical nuance, convention analysis, and developer empathy makes you ideal for understanding the human side of this engineering problem.

---

## Context: What We're Building

**Zorivest** is a trading portfolio management desktop application (Electron + React + Python FastAPI + TypeScript MCP Server). We want to add an MCP tool that bootstraps a `.agent/` folder with context, workflows, roles, rules, docs, and skills — plus IDE-specific root files (AGENTS.md, GEMINI.md, CLAUDE.md, etc.).

**Key design tension:** This tool is an MCP server tool that generates configuration files _for the AI agent itself_. The AI agent calls a tool that creates the instructions the AI agent should follow. This creates interesting trust, recursion, and DX dynamics that we need to think through carefully.

**Current architecture:**
- TypeScript MCP server with 9 toolsets, client detection for multiple IDEs
- Planned slot: MEU-165 (`mcp-ide-config`) in the `core` toolset (always-loaded)
- Templates shipped as static assets in `mcp-server/templates/agent/`
- The `.agent/` folder contains: context/, workflows/, roles/, rules/, docs/, skills/
- Root-level files: AGENTS.md (universal base), plus IDE-specific variants

**The files this tool generates include:**
- **Workflows** — step-by-step workflow definitions like `/create-plan`, `/execution-session`, `/tdd-implementation`
- **Roles** — orchestrator, coder, tester, reviewer, guardrail, researcher (multi-agent patterns)
- **Skills** — git-workflow, quality-gate, pre-handoff-review (with SKILL.md instructions)
- **Docs** — architecture, domain model, testing strategy, help documentation for the Zorivest product
- **Context** — handoffs, MEU registry, known issues, recent changes

---

## Research Tasks

### Task 1: The Meta-Circularity Problem — AI Configuring AI

Analyze the unique DX challenges of an AI agent tool that configures the AI agent's own workspace:

1. **Trust dynamics:**
   - When an AI agent calls `zorivest_setup_workspace`, it's generating its own instruction files. What are the trust implications?
   - Should the tool explain what it's generating and why, before creating files?
   - How do other self-configuring systems handle this (e.g., package managers updating themselves)?
   - What's the user's mental model when an AI tool creates AI agent instructions?

2. **First-run experience:**
   - When a user first installs Zorivest's MCP server, what should the AI agent say/do?
   - Should the agent proactively suggest running setup, or wait for the user to ask?
   - What information does the user need to make an informed decision about running the tool?
   - What's the ideal "zero to productive" time for a new user?

3. **Ongoing relationship:**
   - After initial setup, when should the agent suggest re-running setup? (new version, missing files, etc.)
   - How should the agent reference the generated files? ("I see you have workflows configured, let me use them")
   - Should the agent validate its own configuration on startup?

### Task 2: Convention Design Analysis — Cross-IDE Agent Configuration

Analyze the current state and trajectory of AI agent configuration conventions:

1. **Current conventions landscape:**
   - `AGENTS.md` — Who created it? What's the spec? Who uses it? Is it gaining traction?
   - `CLAUDE.md` — How does it differ from AGENTS.md? Can they coexist? What's Anthropic's official stance?
   - `.cursorrules` → `.cursor/rules/` — The migration story. Lessons for convention design.
   - `.github/copilot-instructions.md` — GitHub's approach. Integration with Copilot Workspace.
   - `.clinerules` — Cline's convention. Community adoption.
   - `.windsurfrules` — Windsurf's approach.
   - `CODY.md` or Cody context — Sourcegraph's approach.

2. **Convention convergence analysis:**
   - Are these converging toward a standard? Evidence for and against.
   - What role does the `.agent/` or `.ai/` folder convention play?
   - Is there a "Schelling point" — a natural convergence target?
   - What can we learn from the history of `.editorconfig`, `.prettierrc`, etc.?

3. **Multi-convention coexistence:**
   - Users often use multiple AI tools. How should configurations coexist?
   - Should AGENTS.md be the "source of truth" with IDE-specific files as views/overlays?
   - Import/include patterns (can CLAUDE.md say "extends AGENTS.md"?)
   - What happens when conventions conflict?

4. **Convention design principles:**
   - What makes a convention stick? (Simplicity? Tooling support? First-mover advantage?)
   - Analysis of `.editorconfig` success: cross-IDE, simple, focused
   - Analysis of `.eslintrc` evolution: too many formats → eventual standardization
   - What can Zorivest learn from these histories?

### Task 3: Developer Experience Design Patterns

Analyze DX patterns for scaffolding tools:

1. **Progressive disclosure:**
   - How should the tool handle different user expertise levels?
   - Should there be a "minimal" vs. "full" setup option?
   - What files are essential vs. advanced?

2. **Customization vs. convention:**
   - How much should users customize the generated files?
   - What signaling tells users "edit this" vs. "don't edit this"?
   - Header comments? `.gitkeep`? README files in each folder?
   - How do other tools signal "managed by tool" vs. "user-editable"?

3. **Discovery and documentation:**
   - How should the generated docs help users understand Zorivest's MCP capabilities?
   - Should the docs be agent-focused (for AI agents to read) or user-focused (for humans)?
   - Dual-audience documentation patterns

4. **Error states and edge cases:**
   - What could go wrong? (No write permission, path too long on Windows, disk full, etc.)
   - How should the agent communicate errors to the user?
   - Partial failure recovery (some files created, some not)
   - What if the user manually deletes some files but not others?

### Task 4: Content Design for Generated Files

Analyze what should go into each generated file category:

1. **Workflows:**
   - What Zorivest-specific workflows should be shipped? (trade entry, analysis, reporting?)
   - How should workflows reference Zorivest MCP tools?
   - What's the right level of specificity? (Generic patterns vs. Zorivest-tailored)

2. **Roles:**
   - Are 6 roles (orchestrator, coder, tester, reviewer, guardrail, researcher) the right set for a trading portfolio app?
   - Should roles be Zorivest-specific or generic agentic roles?
   - How do roles interact with IDE-specific agent behaviors?

3. **Help documentation:**
   - What does a user need to know to effectively use Zorivest via MCP tools?
   - Tool discovery guides? Usage examples? Troubleshooting?
   - How do other MCP servers document their capabilities for users?

4. **Skills:**
   - What reusable skills make sense for a Zorivest user?
   - Trade analysis skill? Portfolio review skill? Tax planning skill?
   - How should skills differ from workflows?

### Task 5: Adoption and Ecosystem Analysis

How similar tools have succeeded or failed in getting users to adopt scaffolded configurations:

1. **Success stories:**
   - Which scaffolding tools have high adoption? Why?
   - What role does the "first run" experience play?
   - How important is IDE integration vs. standalone CLI?

2. **Failure modes:**
   - Tools that generated too many files (configuration fatigue)
   - Tools that required too much manual editing after scaffolding
   - Tools that couldn't update without losing user changes
   - Over-opinionated configs that didn't match user workflows

3. **Community patterns:**
   - Sharing agent configurations between team members
   - `.cursorrules` sharing communities and what they reveal about user needs
   - Template marketplaces or galleries

4. **Competitive positioning:**
   - If Zorivest ships this first (before other trading tools), what's the advantage?
   - How does agentic workspace support differentiate a product?
   - What's the message? "AI-native trading tool" vs. "trading tool with AI support"

### Task 6: Security and Trust Considerations

Deep analysis of the trust model for this feature:

1. **File creation trust:**
   - MCP tools writing files is relatively novel. What trust signals do users need?
   - Should the tool show a preview of files before creating them?
   - How do other MCP servers handle write operations? (filesystem MCP server pattern)

2. **Content trust:**
   - The generated files contain instructions that the AI will follow. Could this be a vector for prompt injection?
   - Template supply chain concerns (if templates are fetched from a server)
   - How to ensure template integrity?

3. **Permission boundaries:**
   - Should the tool only write to a specific subdirectory?
   - What path validation is needed?
   - Platform-specific concerns (Windows ACLs, macOS sandboxing, Linux permissions)

---

## Output Format

Structure your response as a DX research report with:

1. **Executive Summary** (300 words)
2. **The Meta-Circularity Challenge** (analysis of AI-configuring-AI dynamics)
3. **Convention Landscape & Trajectory** (where standards are heading)
4. **DX Design Recommendations** (actionable patterns)
5. **Content Strategy** (what to generate, for whom, at what level)
6. **Adoption Strategy** (how to maximize uptake)
7. **Trust & Security Framework** (practical recommendations)
8. **The Ideal User Journey** (narrative walkthrough of first-time and repeat usage)
9. **Anti-Patterns to Avoid** (specific warnings from failed predecessors)
10. **Sources** (URLs, repos, discussions, blog posts)

Focus on insight depth over breadth. Use concrete examples and analogies. When analyzing conventions, provide evidence-based predictions about where standards will converge. Think about the human factors — what makes a developer WANT to use this tool?
