# Deep Research Prompt — GPT-5.4

## Research Mission: Engineering Patterns for MCP Workspace Scaffolding

You are conducting a deep engineering analysis of implementation patterns, architectural tradeoffs, and best practices for building a file-system scaffolding tool delivered as an MCP (Model Context Protocol) tool. Your strength in deep reasoning, code architecture analysis, and implementation pattern recognition makes you ideal for this technical deep-dive.

---

## Context: What We're Building

**Zorivest** is a trading portfolio management desktop application (Electron + React + Python FastAPI + TypeScript MCP Server). We want to add an MCP tool called `zorivest_setup_workspace` that, when called by an AI agent, bootstraps a `.agent/` folder in the user's project directory.

**The tool generates:**

```
{project_root}/
├── .agent/
│   ├── context/        # Project context files for AI agents
│   ├── workflows/      # Step-by-step workflow definitions (.md)
│   ├── roles/          # Role definitions (orchestrator, coder, tester, reviewer, guardrail, researcher)
│   ├── rules/          # Project rules and constraints
│   ├── docs/           # Help docs, architecture, domain model, testing strategy
│   └── skills/         # Reusable skill packages with SKILL.md
├── AGENTS.md           # Universal AI agent instructions
├── GEMINI.md           # (if Gemini IDE detected) — IDE-specific variant
├── CLAUDE.md           # (if Claude/Cline detected) — IDE-specific variant
├── CURSOR.md           # (if Cursor detected) — IDE-specific variant
└── CODEX.md            # (if Codex detected) — IDE-specific variant
```

**Current MCP server architecture:**
- TypeScript MCP server (`mcp-server/src/`) with 9 toolsets and a `ToolsetRegistry`
- Pre-connect-all + post-connect-filter initialization pattern
- `client-detection.ts` already identifies: Anthropic Claude, VS Code/Copilot, Cursor, Gemini, Codex clients
- Planned slot: MEU-165 (`mcp-ide-config`, Item 5.H) in the `core` toolset (always-loaded)
- Templates would ship as static assets in `mcp-server/templates/agent/`
- All tool implementations follow pattern: accept input → call REST API or perform operation → return structured result

**The tool would live in the `core` toolset**, alongside:
- `zorivest_diagnose` — system diagnostics
- `zorivest_launch_gui` — GUI launcher

---

## Research Tasks

### Task 1: File System Operation Patterns for MCP Tools

Analyze how existing MCP servers and similar tools handle file system operations:

1. **MCP servers that write files:**
   - Which MCP servers create, modify, or scaffold files on the user's filesystem?
   - How do they handle path resolution (relative vs absolute, platform differences)?
   - What permission models do they use? How do they handle write failures?
   - How do they handle path traversal attacks or symlink vulnerabilities?

2. **Directory creation patterns:**
   - Recursive directory creation (ensure parent directories exist)
   - Atomic operations vs. partial failure recovery
   - What happens if the process is interrupted mid-scaffold?
   - Transactions/rollback for multi-file operations

3. **Template resolution approaches:**
   - **Static bundled templates** vs. **dynamically generated content** vs. **remote template registry**
   - How do production MCP servers ship static assets with their npm package?
   - Template variable substitution engines (Handlebars, Mustache, simple string replacement)
   - Binary vs. text file handling in templates

### Task 2: Idempotency Engineering

Deep-dive into making the scaffolding operation idempotent:

1. **File conflict strategies:**
   - **Skip**: Don't overwrite any existing file (safest, least useful on updates)
   - **Overwrite**: Always replace (dangerous, user loses customizations)
   - **Merge**: Three-way merge of template changes + user changes (complex)
   - **Backup + Replace**: Copy existing to `.agent.bak/` then write new (recoverable)
   - **Interactive**: Ask user per-file (not feasible in MCP tool context)
   - **Versioned header**: Files contain a `# Template version: 2.4` header; only overwrite if template is newer

2. **Recommended pattern analysis:**
   - What do `eslint --init`, `docker init`, `terraform init` do with existing configs?
   - What does `npm init` do when `package.json` already exists?
   - What pattern minimizes user surprise while maximizing update capability?

3. **State tracking:**
   - Should the tool create a `.agent/.meta.json` with scaffold timestamp, version, generated files list?
   - How to distinguish user-created files from scaffold-generated files?
   - Version tracking for template updates

### Task 3: Template Architecture for Multi-IDE Support

Analyze the engineering of generating IDE-specific variants from a common base:

1. **Template inheritance patterns:**
   - Base template (AGENTS.md) → IDE-specific overlays
   - Shared sections vs. IDE-specific sections
   - How to handle IDE-specific conventions (e.g., Cursor expects `.cursorrules`, Gemini expects `GEMINI.md`)

2. **Client detection integration:**
   - We already detect the IDE via MCP protocol fields. How to map this to file generation?
   - Should we generate ALL IDE files (GEMINI.md + CLAUDE.md + CURSOR.md) or only the detected one?
   - What if the user uses multiple IDEs? (Generate all? Generate on-demand?)

3. **File content generation:**
   - Should IDE-specific files be exact copies of AGENTS.md, or contain IDE-specific instructions?
   - How to structure shared content so it's DRY across IDE files?
   - What IDE-specific sections add value? (e.g., Gemini mode mappings, Claude thinking patterns)

### Task 4: Security Analysis

Analyze security considerations for an MCP tool that writes to the filesystem:

1. **Path validation:**
   - How to prevent writing outside the project directory?
   - Symlink resolution and traversal attack prevention
   - What existing MCP servers do for path validation

2. **Content injection:**
   - Can template content be manipulated to include malicious payloads?
   - Should generated files be signed or have integrity checks?

3. **Permission model:**
   - Should the tool require explicit user confirmation before writing?
   - How does the MCP confirmation middleware work with file writes?
   - Can we leverage the existing `get_confirmation_token` pattern?

4. **MCP Guard integration:**
   - Should file writes be rate-limited?
   - Should the MCP Guard circuit breaker apply to setup operations?

### Task 5: Existing Implementations — Code-Level Analysis

Find and analyze the source code of tools that do similar scaffolding:

1. **MCP server implementations that scaffold configs:**
   - Link to specific GitHub repos and code files
   - Analyze their error handling, platform compatibility, and edge cases
   - What patterns did they get right? What are their bugs/limitations?

2. **VS Code extension APIs for workspace setup:**
   - How do extensions create workspace files programmatically?
   - What APIs exist for detecting workspace state?

3. **CLI scaffolding tools (source analysis):**
   - `create-react-app` / `create-vite` — how they handle template copying
   - Yeoman — how it handles file conflicts and template resolution
   - How they ship and update templates

### Task 6: Distribution and Updates

How to handle template versioning and updates:

1. **Version pinning:**
   - Templates are bundled with the npm package version
   - How to notify users when new templates are available?
   - Should auto-update be supported?

2. **Diff-based updates:**
   - When templates change between versions, how to apply updates without losing user modifications?
   - Git-style three-way merge for markdown files?
   - Patch-based updates?

3. **Packaging:**
   - How do TypeScript/npm packages ship static non-code assets?
   - `package.json` `files` field best practices for template inclusion
   - Impact on package size

---

## Output Format

Structure your response as a technical engineering report with:

1. **Executive Summary** (300 words)
2. **File System Operation Patterns** (with code examples)
3. **Idempotency Strategy Recommendation** (with decision matrix)
4. **Template Architecture Design** (with diagram)
5. **Security Analysis** (threat model)
6. **Implementation Analysis** (specific repos and code)
7. **Distribution & Update Strategy** (recommended approach)
8. **Architecture Recommendation** (concrete proposal for Zorivest)
9. **References** (links to code, docs, specs)

Include concrete TypeScript code snippets where relevant. Reference specific files and line numbers in open-source implementations. Focus on engineering precision over breadth.
