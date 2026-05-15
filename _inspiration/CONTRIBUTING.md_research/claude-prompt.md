# Claude Deep Research — Architecture & AI-Agent Contribution Design Prompt

> **Optimized for**: Claude Deep Research (Opus 4.7 + extended thinking + web search)  
> **Leverages**: Multi-agent orchestrator-worker architecture, extended thinking with interleaved reasoning between tool calls, deep code-level analysis, ability to reason about file interdependencies  
> **Expected output**: Architectural design for the contribution documentation suite, draft templates, AI-agent guidance strategy

---

## Prompt

I need you to architect the **complete contribution documentation suite** for an open-source trading portfolio management application. This requires deep reasoning about how multiple documentation files interact, how to serve both human developers and AI coding agents, and how to handle the unique challenges of a financial-domain hybrid monorepo.

### Project: Zorivest

**Repository**: https://github.com/matbanik/zorivest

**Architecture** (hybrid monorepo):
```
zorivest/
├── packages/
│   ├── core/          # Python — Domain entities, value objects, ports, calculators
│   ├── infrastructure/# Python — SQLAlchemy, SQLCipher, repos, Unit of Work
│   └── api/           # Python — FastAPI REST API on localhost
├── ui/                # TypeScript — Electron + React + Vite GUI
├── mcp-server/        # TypeScript — MCP (Model Context Protocol) server for AI agents
├── .agent/            # AI agent instructions (roles, workflows, skills, context)
│   ├── AGENTS.md      # Master instruction file for AI coding assistants
│   ├── roles/         # orchestrator, coder, tester, reviewer, researcher, guardrail
│   ├── workflows/     # create-plan, tdd-implementation, execution-session, etc.
│   └── skills/        # terminal-preflight, git-workflow, e2e-testing, etc.
├── docs/
│   ├── build-plan/    # Detailed build specifications
│   └── BUILD_PLAN.md  # Master build plan with 200+ MEUs (Manageable Execution Units)
└── tools/             # Validation scripts (validate_codebase.py)
```

**Key constraints**:
- Financial data handling — SQLCipher encrypted database, real brokerage imports
- Strict TDD policy — tests written before implementation, tests are immutable specs
- AI-agent-first design — the `.agent/` directory already has 15+ workflow files and 12+ skills
- Solo maintainer scaling to community — currently 1 developer, planning for open contributions
- Dependency rule: Domain → Application → Infrastructure (never import infra from core)

### Research Task 1: AI-Agent Contribution Guidance Design

This is Claude's unique strength area. Research and reason about:

1. **How should AGENTS.md and CONTRIBUTING.md coexist?**
   - Search for projects that have both files. How do they avoid duplication?
   - What belongs in AGENTS.md (machine instructions) vs. CONTRIBUTING.md (human guidance)?
   - Should there be a third file — `CONTRIBUTING-AI.md` — for humans who use AI agents to contribute?

2. **Survey the AGENTS.md ecosystem:**
   - Find all projects with `AGENTS.md` files on GitHub. Analyze their structure.
   - What about `.cursor/rules`, `.windsurfrules`, `.github/copilot-instructions.md`?
   - How do projects like LangChain, Anthropic's SDK, and OpenAI Cookbook handle AI-assisted contributions?
   - What is `llms.txt` and should Zorivest adopt it?

3. **Design the AI contribution workflow:**
   - How should a developer using Claude Code, Cursor, or GitHub Copilot Workspace contribute to Zorivest?
   - What context files should be surfaced to their AI agent automatically?
   - How do we prevent AI agents from making "plausible but wrong" contributions?
   - What guardrails should exist in CI specifically for AI-generated code?

### Research Task 2: Companion File Architecture

Using extended thinking, reason through the **complete set of documentation files** that should exist and how they reference each other:

1. **File dependency graph** — design the interconnections:
   ```
   CONTRIBUTING.md → references → CODE_OF_CONDUCT.md
   CONTRIBUTING.md → references → SECURITY.md
   CONTRIBUTING.md → references → docs/DEVELOPMENT.md
   CONTRIBUTING.md → references → .github/PULL_REQUEST_TEMPLATE.md
   AGENTS.md → references → CONTRIBUTING.md (for context)
   ```
   Complete this graph for all files.

2. **For each file, determine:**
   - Purpose (1 sentence)
   - Primary audience (humans, AI agents, both)
   - Approximate length (short: <100 lines, medium: 100-300, long: 300+)
   - Priority (P0: must have before first external contribution, P1: needed within first month, P2: nice to have)
   - Best example from the open-source ecosystem (link to a specific file in a specific repo)

3. **Monorepo-specific files:**
   - Should there be per-package CONTRIBUTING guides? (e.g., `packages/core/CONTRIBUTING.md`)
   - How do monorepos handle different languages having different dev setup requirements?
   - How do projects like VS Code, Nx, or Turborepo handle this?

### Research Task 3: GitHub Templates & Automation

Research and design the `.github/` directory structure:

1. **Issue templates** — design templates for:
   - Bug report (what fields minimize back-and-forth?)
   - Feature request (how to link to build plan MEUs?)
   - Security vulnerability (private reporting via GitHub Security Advisories)
   - Documentation improvement
   - AI agent issue (for issues discovered by AI agents)

2. **PR template** — design a template that:
   - Works for both human and AI-generated PRs
   - Includes a security impact checklist
   - Links to the relevant MEU from the build plan
   - Has separate sections for what was changed, how it was tested, and screenshots

3. **GitHub Actions workflows** that should be documented:
   - What checks should run on every PR?
   - What checks should run only on security-tagged PRs?
   - How to document these for contributors?

### Research Task 4: Draft Templates

Using all research findings, produce **draft templates** for the following files. Each draft should be production-ready quality, not just outlines:

1. **CONTRIBUTING.md** (~300-500 lines) covering:
   - Welcome & vision statement
   - Quick start (3 steps to first contribution)
   - Development environment setup (Python + Node.js)
   - Contribution types and workflows (bug fix, feature, docs, refactor)
   - Code style and standards
   - Testing requirements (TDD policy)
   - PR process and review expectations
   - Security-sensitive contribution guidelines
   - AI-assisted contribution guidelines
   - Recognition and attribution

2. **SECURITY.md** (~100-150 lines) covering:
   - Scope (what's in scope for security reports)
   - Reporting process (private reporting preferred)
   - Response timeline commitments
   - Disclosure policy
   - Security-related contribution guidelines

3. **CODE_OF_CONDUCT.md** — recommend the best base template (Contributor Covenant, etc.) and any customizations for a financial-domain project

4. **GOVERNANCE.md** (~50-100 lines) covering:
   - Decision-making process (solo maintainer → benevolent dictator → council)
   - How MEU priority is determined
   - How contributions are accepted/rejected
   - Roadmap transparency

5. **.github/PULL_REQUEST_TEMPLATE.md** — a universal template that serves both humans and AI agents

6. **DEVELOPMENT.md** (~200-300 lines) covering:
   - Prerequisites (Python 3.12+, Node.js 22+, uv, pnpm)
   - Repository setup
   - Running the backend API
   - Running the Electron UI
   - Running tests (Python + TypeScript)
   - Running type checks and linters
   - Database setup and encryption
   - Architecture overview with package dependency rules

### Output Format

Structure your response as:

1. **Reasoning Summary** — your key insights from extended thinking about the file architecture
2. **File Architecture Decision Record** — the complete file inventory with dependency graph
3. **Draft Templates** — all 6 templates in full, ready to paste into the repository
4. **AI-Agent Strategy** — how AGENTS.md and CONTRIBUTING.md should evolve together
5. **Implementation Roadmap** — which files to create first (P0) through last (P2)
6. **Sources** — all repositories and articles referenced during research

### What Makes This Research Unique

I'm specifically interested in the **interplay between human contribution docs and AI agent instructions**. Most projects treat these as separate concerns. I want Zorivest to be a model for how they can work together:

- A human reads CONTRIBUTING.md to understand the project's values and process
- Their AI agent reads AGENTS.md to understand the project's technical constraints
- Both documents reference each other, creating a unified contribution experience
- The CI pipeline validates contributions regardless of whether a human or AI authored them

Think deeply about this dual-audience design challenge. It's the core innovation I want in Zorivest's contribution docs.
