# Gemini Deep Research Max — CONTRIBUTING.md Survey Prompt

> **Optimized for**: Gemini Deep Research Max (Gemini 3.1 Pro)  
> **Leverages**: Autonomous multi-step web browsing, plan-refine loop, structured reports with native visualizations, ability to crawl 100+ sources iteratively  
> **Expected output**: Comprehensive survey report with comparative tables, pattern taxonomy, and visual diagrams

---

## Prompt

I'm building a **CONTRIBUTING.md and companion documentation suite** for an open-source trading portfolio management application called **Zorivest** (https://github.com/matbanik/zorivest). The project is a hybrid monorepo with:

- **Python backend** (FastAPI + SQLAlchemy + SQLCipher, domain-driven design)
- **TypeScript/Electron frontend** (React + Vite)
- **MCP server** (TypeScript, Model Context Protocol for AI agent integration)
- **AI agent instructions** (`.agent/` directory with roles, workflows, and skills)

I need you to conduct exhaustive research across the open-source ecosystem to understand **how the best projects structure their contribution guidance** and what companion files live alongside CONTRIBUTING.md. This research will directly inform the files we create for Zorivest.

### Research Plan — Phase 1: Broad Survey (50+ repositories)

Crawl and analyze the contribution documentation of **at least 50 well-maintained open-source projects** across these categories:

1. **High-profile foundations** (CNCF, Apache, Linux Foundation) — e.g., Kubernetes, Envoy, Apache Kafka, OpenTelemetry, Prometheus
2. **Developer tools & frameworks** — e.g., Next.js, Vite, FastAPI, Django, Rails, Remix, Astro, SvelteKit
3. **Fintech & trading** — e.g., Zipline, Lean (QuantConnect), ccxt, Hummingbot, Firefly III, GnuCash, Maybe Finance
4. **Electron desktop apps** — e.g., VS Code, Hyper, Insomnia, Postman (open parts), Signal Desktop, Obsidian (community plugins)
5. **Monorepo projects** — e.g., Nx, Turborepo, Rush, Lerna, pnpm (the monorepo itself)
6. **AI/ML projects** — e.g., LangChain, LlamaIndex, Hugging Face Transformers, OpenAI Cookbook, Anthropic SDK
7. **Security-conscious projects** — e.g., age, wireguard, signal-protocol, OpenSSL, Vault (HashiCorp)

For each project, extract:
- [ ] File inventory: what files exist at the repo root? (`CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, `AGENTS.md`, `GOVERNANCE.md`, `DEVELOPMENT.md`, `ARCHITECTURE.md`, `STYLE_GUIDE.md`, `llms.txt`, `.github/` templates, etc.)
- [ ] CONTRIBUTING.md structure: what sections does it contain? What order? Approximate word count?
- [ ] PR template contents (`PULL_REQUEST_TEMPLATE.md`)
- [ ] Issue templates (bug report, feature request, security vulnerability)
- [ ] CI/CD mentions in contribution docs (what checks are described?)
- [ ] How they handle first-time contributors vs. experienced contributors
- [ ] How they handle AI-generated contributions (any policies?)

### Research Plan — Phase 2: Pattern Extraction

From the survey data, identify and categorize:

1. **Universal sections** — sections that appear in >80% of surveyed CONTRIBUTING.md files
2. **High-value optional sections** — sections in <50% but that correlate with higher contributor satisfaction or lower PR rejection rates
3. **Companion file patterns** — which files always appear together? What's the minimum viable set vs. the premium set?
4. **Anti-patterns** — what do projects explicitly warn against? What common mistakes do maintainers complain about?
5. **Monorepo-specific patterns** — how do monorepos handle "which package should I contribute to?" and "how do I run tests for just my change?"
6. **Security contribution patterns** — how do projects handle security-related PRs differently from feature PRs? What guardrails exist?
7. **AI agent compatibility** — what projects have AGENTS.md, llms.txt, or similar? What instructions do they give AI agents?

### Research Plan — Phase 3: Comparative Analysis

Create visual comparisons:

1. **Feature matrix table**: rows = projects, columns = files/sections present (✅/❌)
2. **Taxonomy diagram**: hierarchical classification of CONTRIBUTING.md section types
3. **Maturity model**: define 3-4 levels of contribution documentation maturity (Minimal → Standard → Comprehensive → Enterprise)
4. **File dependency graph**: which files reference each other and how they interconnect

### Research Plan — Phase 4: Practical Recommendations

For a project like Zorivest (Python + TypeScript + Electron monorepo, solo maintainer scaling to community, financial domain with security sensitivity, AI-agent-friendly):

1. **Recommended file inventory** with rationale for each file
2. **Recommended CONTRIBUTING.md outline** with section names and 1-2 sentence descriptions
3. **Priority ordering**: what to create first vs. what can wait until the community grows
4. **Template sources**: link to the best example of each recommended file from the surveyed projects
5. **Hybrid monorepo considerations**: how to handle Python vs. TypeScript contribution differences in a single file vs. separate guides

### Output Format

Produce a structured report with:
- Executive summary (1 page)
- Detailed findings organized by research phase
- All comparison tables and visualizations
- Full source list with URLs for every repository analyzed
- Appendix: raw data table of all 50+ repos surveyed with their file inventories

### Important Context

- The project already has an extensive `.agent/AGENTS.md` for AI coding assistants — the CONTRIBUTING.md needs to complement this without duplicating it
- The project handles sensitive financial data (encrypted with SQLCipher) — security contribution guidelines are critical
- We want to attract developers AND AI agent operators who use tools like Claude Code, Cursor, Windsurf, GitHub Copilot Workspace
- The GitHub repo is at: https://github.com/matbanik/zorivest
