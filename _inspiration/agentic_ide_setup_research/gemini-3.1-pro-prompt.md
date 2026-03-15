

## Research Mission: Landscape Survey of Agentic IDE Workspace Scaffolding

You are conducting a comprehensive landscape survey of tools, MCP servers, extensions, CLI utilities, and frameworks that scaffold agentic/AI IDE configurations for developer workspaces. Your strength in broad information synthesis across many sources makes you ideal for mapping the full ecosystem.

---

## Context: What We're Building

**Zorivest** is a trading portfolio management desktop application (Electron + React + Python FastAPI) with a TypeScript MCP (Model Context Protocol) server. We want to add an MCP tool that, when called by an AI agent, bootstraps a `.agent/` folder in the user's project directory with:

1. **Context files** — contextual information about the project for AI agents
2. **Workflows** — step-by-step workflow definitions (markdown files)
3. **Roles** — role definitions for multi-agent patterns (orchestrator, coder, tester, reviewer, guardrail, researcher)
4. **Rules** — project rules and constraints
5. **Docs** — help documentation, architecture docs, domain model reference, testing strategy
6. **Skills** — reusable skill packages with SKILL.md instruction files
7. **Root-level IDE files** — `AGENTS.md` (universal), plus IDE-specific variants: `GEMINI.md`, `CLAUDE.md`, `CURSOR.md`, `CODEX.md`, `CODY.md`, etc.

The MCP tool would detect the calling IDE (already have client detection via MCP protocol inspection) and generate the appropriate files. The tool must be idempotent (safe to run multiple times), handle existing files gracefully, and ship templates as static assets with the MCP server package.

**Current architecture:**
- MCP Server: TypeScript, 9 toolsets, toolset registry with pre-connect-all/post-connect-filter pattern
- Client detection: Already identifies Anthropic Claude, VS Code/Copilot, Cursor, Gemini, Codex, and other IDE clients
- Build plan slot: MEU-165 (`mcp-ide-config`, Item 5.H, "IDE config templates, Tier 2")

---

## Research Tasks

### Task 1: Map the Entire Agentic IDE Configuration Ecosystem

Find and analyze every tool, extension, CLI, or MCP server that scaffolds agentic/AI configuration for developer workspaces. For each, document:

- **Name and type** (CLI, MCP server, VS Code extension, framework plugin, etc.)
- **What it generates** (files, folders, config snippets)
- **How it's triggered** (command, MCP tool call, IDE action, `npx` command, etc.)
- **Idempotency** (can it run multiple times safely?)
- **IDE specificity** (single IDE or cross-IDE support?)
- **Open source?** (license, repo URL)
- **Adoption level** (GitHub stars, npm downloads, marketplace installs)

**Specifically investigate:**

1. **MCP-native scaffolding:**
   - Any MCP servers that create/modify workspace configuration files
   - MCP servers that generate their own instruction files or agent context
   - MCP server init/setup commands that create config files

2. **IDE-specific agent configuration:**
   - `.cursorrules`, `.cursor/` folder generation tools
   - GitHub Copilot workspace setup / `.github/copilot-instructions.md`
   - Continue.dev `config.json` and context providers
   - Cody (Sourcegraph) context file generators
   - Windsurf rules/configuration generators
   - Cline MCP configuration tools
   - Aider conventions file generators (`.aider*`)
   - JetBrains AI configuration
   - Amazon Q Developer configuration

3. **Cross-IDE agent configuration:**
   - Tools that generate for multiple IDEs simultaneously
   - Any standard/convention attempts for universal agent configuration
   - The `.clinerules` / `.cursorrules` / AGENTS.md convergence efforts
   - `AGENTS.md` specification and adoption (Google's standard)
   - `CLAUDE.md` convention and adoption (Anthropic's standard)

4. **Project scaffolding CLIs that include AI configuration:**
   - `npx create-*` generators that include agent config
   - Yeoman generators with AI config templates
   - Cookiecutter templates with agent configuration
   - Any framework starters (Next.js, Astro, etc.) that bundle AI config

### Task 2: Adjacent Domain Analysis — Scaffolding Patterns

Analyze scaffolding/init patterns from adjacent domains that we can learn from, even if they're not AI-specific:

1. **Package manager init patterns:**
   - `npm init`, `cargo init`, `poetry init` — interactive vs. non-interactive
   - How they handle existing files (skip, merge, overwrite, ask)
   - Template resolution and customization

2. **Dev tool setup patterns:**
   - `eslint --init`, `prettier --init`, `husky init`
   - `docker init`, `terraform init`
   - `git init` and how it handles `.gitignore` templates
   - VS Code workspace settings generators

3. **Infrastructure-as-Code init:**
   - Terraform/Pulumi workspace initialization
   - How they handle state, versions, and provider configuration
   - Template registries and version pinning

4. **Multi-environment configuration:**
   - `.env` file generators and managers
   - Config file templating systems (dotenv-vault, 1Password CLI)
   - How tools handle "settings that should exist but shouldn't be committed"

### Task 3: Emerging Standards and Conventions

Research the current state of standardization efforts:

1. **MCP configuration convergence:**
   - The unofficial MCP config standard across IDEs
   - How different IDEs store MCP server configurations
   - Is there a `mcp.json` standard emerging?

2. **Agent instructions convergence:**
   - `AGENTS.md` (Google/DeepMind) — scope, structure, adoption
   - `CLAUDE.md` (Anthropic) — scope, structure, adoption
   - `.cursorrules` (Cursor) — format, migration to `.cursor/rules/`
   - `.github/copilot-instructions.md` (GitHub) — format, scope
   - `.clinerules` (Cline) — format, scope
   - Any Draft RFCs, proposals, or discussions about unifying these

3. **Folder structure conventions:**
   - `.agent/`, `.ai/`, `.agentic/` — which convention is gaining traction?
   - Where do different tools expect their configs?
   - Nested vs. flat configuration approaches

### Task 4: Comparative Matrix

Create a structured comparison matrix with:

| Tool/Standard | Type | Generated Files | IDE Support | Idempotent | Merge Strategy | Active Maintenance | Stars/Downloads |
|---|---|---|---|---|---|---|---|

Include at least 15-20 entries covering the most relevant tools and standards.

### Task 5: Gaps and Opportunities

Based on your landscape survey:

1. What is **nobody doing yet** that Zorivest could pioneer?
2. What are the **most common failure modes** in existing scaffolding tools?
3. What **developer experience anti-patterns** should we avoid?
4. What **conventions are most likely to become standard** in 12 months?
5. Are there any **security concerns** with MCP tools that write to the filesystem?

---

## Output Format

Structure your response as a comprehensive research report with:

1. **Executive Summary** (300 words max)
2. **Ecosystem Map** (categorized list of all discoveries)
3. **Comparative Matrix** (structured table)
4. **Adjacent Domain Patterns** (key takeaways)
5. **Standards Convergence Analysis** (what's emerging)
6. **Gaps & Opportunities** (what we can uniquely offer)
7. **Recommendations** (top 5 actionable insights for Zorivest)
8. **Sources** (URLs and references for all findings)

Be exhaustive. Cite specific GitHub repos, npm packages, marketplace links, blog posts, and documentation pages. Prefer primary sources over secondary analysis.
