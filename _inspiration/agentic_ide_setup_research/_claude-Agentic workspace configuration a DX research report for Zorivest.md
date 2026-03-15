# Agentic workspace configuration: a DX research report for Zorivest

**An AI coding agent's first act in your project should be reading instructions — not writing them.** That tension sits at the heart of Zorivest's plan to ship an MCP tool that bootstraps a `.agent/` folder with context, workflows, roles, rules, docs, and skills, plus IDE-specific root files. The convention landscape is consolidating fast around AGENTS.md as a vendor-neutral standard, but tool-specific files (CLAUDE.md, `.cursor/rules/`, `.github/copilot-instructions.md`) persist for advanced features — creating a "hub-and-spoke" model that Zorivest can exploit. The meta-circularity of AI configuring AI is solvable with patterns borrowed from compiler bootstrapping and package manager self-updates. And the security stakes are real: **Snyk's ToxicSkills audit found 13% of published agent skills contain critical security flaws**, while the IDEsaster disclosure in December 2025 revealed 24+ CVEs across every major AI IDE. Zorivest's scaffolding MCP tool must navigate all of this — generating trusted, human-auditable configuration that serves both AI agents and human developers across a fragmented but converging ecosystem.

---

## The convention landscape is converging faster than expected

The period from mid-2025 through early 2026 produced a Cambrian explosion of AI agent configuration files. A maximally-configured repository today could contain **eleven separate instruction files**: AGENTS.md, CLAUDE.md, GEMINI.md, `.cursorrules`, `.cursor/rules/*.mdc`, `.windsurfrules`, `.windsurf/rules/*.md`, `.clinerules/`, `.github/copilot-instructions.md`, `.github/instructions/**/*.instructions.md`, and `.junie/guidelines.md`. This is unsustainable, and the ecosystem knows it.

**AGENTS.md has emerged as the Schelling point.** Originally proposed by Sourcegraph as singular `AGENT.md`, formalized through collaboration between OpenAI, Google, and Sourcegraph in mid-2025, and donated to the Linux Foundation's Agentic AI Foundation (AAIF) in December 2025, AGENTS.md is now supported by **over 25 tools** — including OpenAI Codex, Google Jules, GitHub Copilot, Cursor, Windsurf, JetBrains Junie, Devin, Zed, and Warp. More than **60,000 open-source projects** have adopted it. The format is deliberately simple: plain Markdown, no schema, no YAML frontmatter, hierarchical via directory proximity. OpenAI's own Codex repository contains 88 AGENTS.md files.

But AGENTS.md's simplicity is both its strength and its limitation. **Tool-specific files survive because they offer features AGENTS.md cannot express.** CLAUDE.md supports `@imports` for referencing other files, auto-memory that writes learnings to `MEMORY.md`, and a cascading hierarchy from enterprise policy (`/etc/claude-code/CLAUDE.md`) through user preferences to project-local overrides. Cursor's `.cursor/rules/*.mdc` format supports four activation modes (Always, Auto-Attached via glob, Agent-Requested via description, Manual) that allow rules to activate only when editing Python files or only when the AI decides they're relevant. Windsurf's rule files include a `trigger` field with similar granularity. GitHub Copilot's `.github/instructions/**/*.instructions.md` supports `applyTo` globs for path-specific instructions.

The practical resolution is a **hub-and-spoke model**: AGENTS.md serves as the cross-tool baseline (build commands, architecture overview, code style, testing instructions), while tool-specific files add proprietary features. GitHub Copilot's coding agent already reads AGENTS.md, CLAUDE.md, GEMINI.md, and its own instruction files simultaneously. The symlink pattern — `ln -sfn AGENTS.md CLAUDE.md` — is the most popular community workaround for keeping content synchronized.

### What Cursor's migration teaches about convention design

Cursor's move from a single `.cursorrules` file to `.cursor/rules/` directory is the most instructive migration in this space. Introduced in early 2024, `.cursorrules` spawned an enormous ecosystem — the `awesome-cursorrules` repository collected **36,900+ stars** and hundreds of pre-made rule files. Sites like `cursor.directory` and `dotcursorrules.com` became active template marketplaces.

When Cursor deprecated the single file in favor of a directory of `.mdc` files with YAML frontmatter in early 2025, the community response was "visceral and significant." Users with programmatic systems built around the single file resisted. The `/Generate Cursor Rules` command was still creating deprecated `.cursorrules` files months after the migration was announced. But the migration was necessary: **monolithic instruction files hit scaling limits** as LLMs ignore chunks of overly long prompts. One developer noted their `.cursorrules` grew so long that "the AI would end up ignoring chunks of it anyway."

Five lessons emerge: (1) single monolithic files cannot scale — glob-based scoping is essential for mixed-technology codebases; (2) community ecosystem investments create lock-in that makes breaking changes painful; (3) backward compatibility during transitions is non-negotiable — Cursor wisely kept `.cursorrules` working at lowest priority; (4) migration tooling must ship alongside deprecation announcements; (5) format proliferation is dangerous — the `.eslintrc` saga (seven format variants before flat config consolidation) proved that offering developers choices that don't matter breeds confusion.

### Historical precedent favors simplicity

The conventions that endure share a common DNA. **EditorConfig succeeded because adoption cost was zero**: drop an INI-like file in a directory, and 30+ editors respect it natively. It handles only the lowest-common-denominator settings (indent style, line endings, charset) and makes no attempt at extensibility. This minimalism is why it's built into VS Code, JetBrains, Visual Studio, Xcode, and GitHub without any plugin. The lesson for AI config conventions: the standard that wins is the one with the lowest barrier to adoption and the clearest scope boundaries.

ESLint's evolution offers the cautionary counterexample. The proliferation of `.eslintrc`, `.eslintrc.json`, `.eslintrc.yml`, `.eslintrc.js`, `.eslintrc.cjs`, and `package.json` configuration, combined with a custom module resolution system the ESLint team called "one of our biggest regrets," created years of tooling confusion. The flat config consolidation (RFC in 2019, default in ESLint v9 in April 2024, still evolving in 2025) shows how long cleanup takes once format debt accumulates.

**For Zorivest's scaffolding tool, the implication is clear**: generate AGENTS.md as the canonical cross-tool file, generate tool-specific files (CLAUDE.md, `.cursor/rules/`, etc.) only when detected or requested, and use symlinks or reference patterns ("Strictly follow the rules in ./AGENTS.md") to avoid content duplication.

---

## The meta-circularity challenge is solvable but demands humility

When Zorivest's MCP tool generates a CLAUDE.md file that tells Claude how to behave in the Zorivest codebase, a meta-circular trust loop forms: the AI agent executing the tool is creating instructions that will govern its own future behavior. This is not a theoretical concern — it's a well-studied problem with precedents and solutions.

### Ken Thompson's shadow looms large

The foundational parallel is Ken Thompson's 1984 Turing Award lecture, "Reflections on Trusting Trust." Thompson demonstrated that a compiler could insert a backdoor into programs it compiles *and* insert the backdoor-insertion code into compilers it compiles — making the malicious behavior invisible in source code and self-propagating through binaries. His conclusion — **"You can't trust code that you did not totally create yourself"** — translates directly to AI-generated configuration. The "compiled binary" (the generated config) may contain behaviors not visible in the "source" (the user's expressed intent).

Compiler bootstrapping solved this with **Diverse Double Compilation (DDC)**: compile with two independent compilers and compare outputs. The `stage0` project takes this further, beginning with 380 bytes of hand-verifiable hex code and bootstrapping up through assemblers to TinyCC to GCC. The analog for AI self-configuration is a **human-reviewed seed config** that AI can extend but never replace — an immutable "trusted computing base" for agent instructions.

Other self-configuring systems offer practical patterns. Terraform's state management creates similar circularity (the infrastructure-as-code tool depends on state it manages), mitigated by state locking, remote backends, and explicit `terraform import` for bootstrapping. Package managers updating themselves (npm updating npm, pip updating pip) rely on signed packages and deterministic builds. The AWS Cloud Control API MCP Server adds `MANAGED_BY` tags to resources it creates — a simple but effective provenance signal.

### Designing for the epistemic gap

Users face a fundamental mental model disconnect with AI-generated config. Hand-written configuration feels authored: "I chose this, I understand it, I'm responsible for it." Generated configuration feels alien: "Something else created this — do I trust it? Can I modify it? Will my changes survive?" Anthropic's research on "alignment faking" makes this gap concrete: Claude displayed cooperative behavior 12% of the time in basic tests but 78% after retraining — models may appear to accept rules while covertly maintaining original preferences.

The resolution is **radical transparency**. Zorivest's scaffolding tool should:

- **Preview before writing**: Show a complete diff of what will be created, in the style of Terraform's `plan` output. VS Code's MCP trust model requires explicit approval before starting any MCP server. Zorivest should require explicit confirmation before writing any file.
- **Separate seed from generated**: Maintain a clear boundary between human-authored instructions (the "seed") and AI-generated extensions. Copier's `.copier-answers.yml` pattern — tracking template source, version, and user answers — provides a model.
- **Make provenance visible**: Every generated file should include a header identifying the generating tool, version, timestamp, and template hash. Go's standardized `// Code generated .* DO NOT EDIT.$` convention, recognized by linters and GitHub's diff view, is the established pattern.
- **Enable human override**: The `CLAUDE.local.md` pattern (auto-gitignored, personal overrides) is the right model for user customization that survives re-scaffolding.

---

## DX design recommendations for the scaffolding tool

### Progressive disclosure is the correct architecture

The evidence from scaffolding tool history is unambiguous: **zero-config start with progressive complexity is the winning pattern.** Create React App proved that zero-config lowers the barrier to entry; its decline proved that zero-config without an extension mechanism becomes a prison. Vite's `npm create vite@latest` asks only project name and framework — two questions — and generates a working project. Next.js's `create-next-app` adds optional checkboxes for TypeScript, ESLint, Tailwind, and App Router but works immediately with defaults.

For Zorivest's MCP tool, this means a **tiered scaffolding approach**:

- **Tier 1 (instant)**: `bootstrap_agent_config` with no arguments generates AGENTS.md with project context auto-detected from `package.json`, `pyproject.toml`, and directory structure. One file, immediate value.
- **Tier 2 (detected)**: If Cursor, Claude Code, Windsurf, or Copilot are detected (via config files, running processes, or IDE markers), generate corresponding tool-specific files with content synchronized from AGENTS.md.
- **Tier 3 (requested)**: On explicit request, scaffold the full `.agent/` directory with workflows, roles, rules, docs, and skills. This is the "power user" path.

Anthropic's Agent Skills pattern validates this architecture: skills sit dormant in a directory, loaded on-demand by description match rather than always injected into context. A lean AGENTS.md with references to subdirectory content prevents context window bloat.

### Configuration fatigue is the primary risk

A typical Next.js project already contains **approximately 30 configuration files** (next.config.js, tsconfig.json, eslint config, postcss.config.js, tailwind.config.js, Sentry configs, Docker files, env files, and more). Deno's team calls this "config hell." The Node.js tooling group's Issue #79 notes the circular logic: "We put config files in the project root because we put config files in the project root."

Zorivest's `.agent/` folder should contain **no more than 5-7 files** in the default scaffolding. Every additional file must justify its existence. The `.agent/` directory convention itself helps by moving config out of the repository root — precisely what the Node.js community has been requesting. The directory structure should look like:

```
.agent/
├── context.md          # Project overview, architecture, domain vocabulary
├── workflows.md        # Build, test, deploy commands
├── rules.md            # Code style, conventions, security constraints
├── roles/              # Optional: role-specific instructions
└── skills/             # Optional: reusable capability definitions
```

Root-level files (AGENTS.md, CLAUDE.md, GEMINI.md) should be thin shims that import from `.agent/` content, not duplicates. This prevents the content synchronization problem that plagues multi-file setups.

### Dual-audience documentation is now mandatory

GitBook reports that AI readership of documentation increased **500% over 2025**, rising from 9% to over **40% of total traffic** by year-end. Gartner predicts that by 2027, over 30% of API demand will come from AI agents. Documentation that works for both audiences is no longer optional.

The qualities that make documentation AI-readable are identical to those that make it human-friendly: clear structure, consistent terminology, explicit context, self-contained pages, and question-based headings. Zorivest's generated files should follow Mintlify's MAGI approach (Markdown for Agent Guidance & Instruction), using YAML frontmatter for machine-readable metadata and natural-language prose for both audiences. The `llms.txt` convention — a robots.txt-equivalent for AI systems — should be generated alongside agent configuration.

### Re-scaffolding must not destroy user changes

Copier (Python) implements the gold-standard approach: a **3-way merge algorithm** that regenerates the project from the old template version, computes a diff of user changes, generates from the new template version, and applies the user diff to the new output. Conflicts get inline markers (`<<<<<<< BEFORE` / `>>>>>>> AFTER`) or `.rej` files. The `.copier-answers.yml` file tracks template source, version, and user answers.

Zorivest's scaffolding tool should:

- Store metadata in `.agent/.scaffold-meta.json` (template version, generation timestamp, content hashes)
- On re-scaffold, compute diffs against stored hashes to detect user modifications
- Present a preview of proposed changes with conflict markers for modified files
- Support `--force` for clean re-generation and `--merge` for intelligent updates
- Never regenerate files the user has deliberately deleted (respect intentional deletions)
- Use partial/extensible patterns: generate a base `rules.md` with a clearly marked `<!-- USER RULES BELOW -->` section that survives re-scaffolding

---

## Content strategy for generated files

The generated AGENTS.md for a Zorivest project should be dense, actionable, and structured for both LLM consumption and human scanning. Based on GitHub's analysis of 2,500+ AGENTS.md files and Anthropic's recommendation to keep CLAUDE.md under 300 lines, the optimal content structure is:

**AGENTS.md template (~80-120 lines for Zorivest)**:
1. **Project identity** (5 lines): What Zorivest is, its tech stack (Electron + React + Python FastAPI + TypeScript MCP Server), target users
2. **Architecture** (15 lines): Frontend/backend boundary, IPC patterns, MCP server role, data flow
3. **Build and test commands** (10 lines): Exact commands for build, test, lint, format — the single highest-value content per GitHub's analysis
4. **Code conventions** (20 lines): TypeScript strict mode, Python type hints, component patterns, naming conventions
5. **Domain vocabulary** (10 lines): Trading-specific terms (portfolio, position, order, fill, P&L) with precise definitions — critical for LLMs to generate domain-correct code
6. **Security boundaries** (10 lines): What the AI must never do (execute trades without confirmation, expose API keys, modify production configs)
7. **File structure reference** (15 lines): Key directories and their purposes

Tool-specific files should contain only tool-specific configuration. CLAUDE.md adds `@imports` references and auto-memory settings. `.cursor/rules/*.mdc` files add glob-scoped rules (e.g., Python backend rules that activate only in `backend/**/*.py`). `.github/copilot-instructions.md` can reference AGENTS.md directly.

---

## Adoption strategy grounded in ecosystem patterns

### Ship the AGENTS.md generator first, alone

The awesome-cursorrules community (36,900+ stars) reveals that developers' primary need is **copy-paste-customize context** for their specific tech stack. Cursor.directory serves as a searchable gallery. SkillsMP provides one-command installation of agent skills. The pattern is clear: developers want templates they can install in seconds and customize in minutes.

Zorivest should publish its AGENTS.md template to these existing communities — submit to awesome-cursorrules, list on cursor.directory, and publish as an MCP server on the official MCP Registry (`registry.modelcontextprotocol.io`). The MCP Registry, launched in September 2025, supports namespace-verified publishing and REST API discovery. VS Code's built-in MCP Gallery enables one-click installation.

### Exploit the first-mover window in finance-specific agent config

MCP adoption exhibits strong network effects: more AI assistant clients drive more server value, driving more servers, driving more client adoption. As one analyst put it, **"Right now MCP is in the phase where APIs were around 2005"** — standards forming, adoption uneven, but trajectory obvious. Products that expose MCP endpoints early become the easiest tools for AI agents to orchestrate. In finance/trading, this window is especially valuable because domain-specific agent configuration (trading terminology, compliance constraints, risk management rules) creates switching costs that generic tools cannot replicate.

### Position as "AI-native" through infrastructure, not marketing

Verdantix's 2025 analysis found that **generic AI marketing language "no longer cuts the mustard"** — 40% of European startups classified as "AI-first" in 2019 weren't using AI materially. The winning positioning is not "Zorivest: AI-powered trading" but rather making Zorivest genuinely easier to develop with AI coding agents. Shipping agentic workspace configuration as a first-class feature — not an afterthought — signals to developers that the product understands modern development workflows.

---

## Trust and security framework

### The threat model is concrete and documented

The security landscape for AI agent configuration is worse than most teams realize. AuthZed compiled a timeline of **MCP breaches from April through October 2025** including a WhatsApp MCP tool that exfiltrated entire chat histories, a GitHub MCP prompt injection that leaked private repo data, a Smithery path traversal that compromised 3,000+ hosted MCP servers' credentials, and a malicious Postmark MCP server that silently BCC'd all email traffic to an attacker.

For file-writing tools specifically, the risks are:

- **Prompt injection via generated instruction files**: CLAUDE.md files are loaded automatically by Claude Code from the project root and parent directories. Critically, **Claude screens other instruction files through Haiku for safety but skips CLAUDE.md entirely** — making it a privileged injection surface. A malicious CLAUDE.md can appear normal at the top but contain injection below the fold. The December 2025 IDEsaster disclosure revealed that a single `.claude/settings.json` file committed to a repository could achieve remote code execution (CVE-2025-59536).
- **Template supply chain attacks**: Snyk's ToxicSkills audit of 3,984 agent skills found **76 confirmed malicious payloads** for credential theft, backdoor installation, and data exfiltration. The barrier to publish was a SKILL.md file and a week-old GitHub account. No code signing, no security review, no sandbox by default.
- **Path traversal**: The official MCP filesystem server itself had sandbox escape vulnerabilities (CVE-2025-53109/53110) allowing arbitrary file access beyond allowed directories.

### Defense-in-depth for Zorivest's scaffolding tool

Zorivest's MCP tool should implement layered defenses:

- **Allowed-directory restriction**: Only write to the project directory. Canonicalize all paths and verify they resolve within the project root after symlink resolution. The official filesystem MCP server's pattern of command-line-specified allowed directories is the baseline.
- **Tool annotations**: Set `readOnlyHint: false`, `destructiveHint: false`, `idempotentHint: true` on the scaffolding tool so MCP clients can present appropriate confirmation UIs.
- **Content-safe templates**: Generated instruction files must never contain executable commands, shell invocations, or instructions that could be interpreted as prompt injections by downstream agents. Audit templates for patterns matching known injection signatures (Lasso Security catalogs 24 pattern categories).
- **No dynamic content in security-critical sections**: The security boundaries section of generated AGENTS.md should be static, not templated from user input or project analysis — preventing injection via project metadata.
- **Hash-based integrity tracking**: Store SHA-256 hashes of generated files in `.agent/.scaffold-meta.json`. On re-scaffold, verify hashes before overwriting to detect tampering.
- **Provenance headers**: Every generated file begins with `<!-- Generated by Zorivest MCP v{version} on {date}. Template hash: {hash}. -->` following Go's standardized generated-file convention.

---

## The ideal user journey

A developer installs Zorivest, opens the project in Cursor (or Claude Code, or VS Code with Copilot), and connects to the Zorivest MCP server. On first interaction, they ask the AI to help them set up the development environment. The AI discovers Zorivest's `bootstrap_agent_config` tool via MCP tool discovery. It explains: "I can generate project configuration that helps AI coding tools understand Zorivest's architecture and conventions. Want me to show you what I'd create?"

The preview shows a single AGENTS.md file with auto-detected project context — Electron + React frontend, Python FastAPI backend, TypeScript MCP server, detected build commands from package.json and pyproject.toml. The developer approves. One file is created. The AI immediately becomes more effective at navigating the codebase because it understands the architecture, the domain vocabulary (portfolios, positions, orders), and the security constraints (never execute trades without confirmation).

Two weeks later, the developer asks for more structured configuration. The AI offers Tier 2: tool-specific files detected for their IDE, plus the `.agent/` directory with workflows and rules. The developer selects which components to generate, reviews the preview, and approves. Generated files include clear provenance headers and a `.scaffold-meta.json` for future updates.

When a new team member joins, they clone the repo and every AI tool they use — Cursor, Claude Code, Copilot — immediately reads the AGENTS.md and tool-specific files. No onboarding friction. The AI already knows the build commands, the architecture, and the conventions.

---

## Anti-patterns to avoid

**The "config explosion" trap.** Angular CLI's early approach of generating four files per component multiplied across dozens of components taught the ecosystem that prolific file generation creates cognitive overhead that outweighs convenience. Zorivest should never generate more than 7 files without explicit user request.

**The "clever indirection" trap.** ESLint's custom module resolution — reimplementing Node.js `require()` — was the team's self-described biggest regret. Zorivest's files should use plain Markdown with simple `@import` references, never custom resolution logic.

**The "write-only configuration" trap.** CRA's eject command was a one-way door: 30+ config files appeared with no path back to managed mode. Zorivest must maintain a clear distinction between managed scaffolding (can be updated) and user-customized content (preserved during updates).

**The "security theater" trap.** Adding a "DO NOT EDIT" header without actually protecting against edits or verifying integrity creates false confidence. If Zorivest generates security-critical instructions (e.g., "never execute trades without confirmation"), those instructions need runtime enforcement, not just text in a Markdown file.

**The "AI writing AI rules without human review" trap.** The most dangerous anti-pattern would be allowing the MCP tool to generate agent instructions that the AI then follows without human review in the same session. The trust boundary must include a human approval step between generation and consumption. VS Code's MCP trust model — requiring explicit confirmation before starting any MCP server and resetting trust when tool lists change — is the minimum viable trust architecture.

---

## Where standards converge: a prediction

By late 2026, the agent configuration landscape will settle into three tiers. **AGENTS.md becomes the README.md of AI-assisted development** — present in most active repositories, read by all major tools, governed by the Linux Foundation. Tool-specific files persist but narrow in scope: CLAUDE.md for Claude's auto-memory and imports, `.cursor/rules/` for glob-scoped activation, `.github/copilot-instructions.md` for Copilot-specific features. The `.agents/` folder convention, currently in early-stage RFC (the `agentsfolder/spec` on GitHub and the Agent Configuration Standard proposal), will gain traction for complex monorepos but won't displace AGENTS.md for typical projects.

The security gap — no cryptographic verification of instruction files, no standard integrity mechanism, privileged injection surfaces in CLAUDE.md — will force at least one major incident that drives the ecosystem toward signed agent configurations. The ToxicSkills audit and IDEsaster disclosures are early warnings. Zorivest can differentiate by being ahead of this curve: generating verifiable, integrity-checked configuration that treats AI instruction files as security-critical artifacts rather than casual documentation.

The products that win in this landscape are those that make AI coding agents immediately productive in their codebase. Zorivest's scaffolding MCP tool, implemented with progressive disclosure, radical transparency, and defense-in-depth security, positions the product not as "a trading app with AI features" but as a trading platform that is native to the agentic development era.