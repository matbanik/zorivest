# Phase 12: Contributor Documentation Suite

> **Priority:** P0 (foundation) → P1 (governance & AI) → P2 (advanced tooling)
> **Depends on:** Nothing — pure documentation; parallel with all code phases
> **Blocks:** Phase 7 (Distribution) — contributor docs must exist before public release
> **Research source:** [COMPOSITE-SYNTHESIS.md](../../_inspiration/CONTRIBUTING.md_research/COMPOSITE-SYNTHESIS.md) (3-model deep research → unified action plan)

---

## Overview

This phase creates the complete contributor documentation suite for the Zorivest monorepo. It bridges the gap between human developers and AI coding agents using a "Hub and Spoke" architecture:

- **CONTRIBUTING.md** is the human root (values, process, TDD mandate)
- **AGENTS.md** (root) is the machine root (build commands, constraints, architecture)
- Both cross-reference each other; neither duplicates the other

### Key Architectural Decisions

| Decision | Choice | Source |
|:---------|:-------|:-------|
| Documentation model | Hub and spoke (not monolithic) | All 3 research reports |
| AI disclosure policy | Mandatory self-disclosure per PR | Claude + Gemini survey |
| AGENTS.md sizing | ≤200 lines root; per-package nested files | Augment Code study (Claude) |
| Code of Conduct | Contributor Covenant 2.1 verbatim | Community standard |
| Governance model | BDFL with documented evolution trigger | Claude |
| Per-tool AI files | AGENTS.md canonical; redirects/symlinks for others | Claude survey |

### Dual AGENTS.md Architecture

> [!IMPORTANT]
> There are **two** AGENTS.md files serving different audiences:
>
> - **`.agent/AGENTS.md`** — Internal AI agent instructions for dedicated coding agents (Opus, Codex). Extensive, detailed, session-management-aware. **Unchanged by this phase.**
> - **`AGENTS.md` (root)** — Public-facing, external-contributor-oriented. ≤200 lines. Build/test/verify commands and core constraints. **Created in this phase.**
>
> External contributors' AI tools (Claude Code, Copilot, Cursor, Windsurf) read the root file. Zorivest's dedicated agents read `.agent/AGENTS.md` via user rules injection.

---

## §12.1 — Security Vulnerability Reporting (MEU-208)

### Deliverable: `SECURITY.md`

**Purpose:** Define vulnerability scope, reporting channel, response SLAs, and handling process. Financial-domain projects require explicit security documentation.

**Content requirements** (from COMPOSITE-SYNTHESIS §4.2):

1. **Supported versions table** — which releases receive security patches
2. **Private reporting channel** — GitHub Private Vulnerability Reporting (PVR) preferred; email fallback
3. **Required information checklist** — description, reproduction steps, impact assessment, suggested fix
4. **Response SLA table** — acknowledgment (48h), triage (5 business days), fix timeline (30 days for critical)
5. **In-scope / out-of-scope** — clearly define what constitutes a security issue
6. **CVE handling** — coordination with MITRE for critical issues
7. **No-bounty statement** — explicit: "Zorivest does not offer bug bounties at this time"
8. **Confidentiality reminder** — "Do not file public issues for security vulnerabilities"

**Prerequisite step:** Enable GitHub Private Vulnerability Reporting in repo settings (Settings → Code security → Private vulnerability reporting → Enable).

**Best exemplars:** Firefly III (financial domain), age/filippo.io (concise + SLA table)

---

## §12.2 — GitHub Templates (MEU-209)

### Deliverables

| File | Purpose |
|:-----|:--------|
| `.github/PULL_REQUEST_TEMPLATE.md` | Unified PR template with AI disclosure, security checklist, TDD evidence |
| `.github/ISSUE_TEMPLATE/bug_report.yml` | Structured bug report form (YAML-based) |
| `.github/ISSUE_TEMPLATE/feature_request.yml` | Structured feature request form (YAML-based) |
| `.github/ISSUE_TEMPLATE/config.yml` | Disable blank issues; redirect security to PVR |

### PR Template Requirements

The PR template must include these sections (from COMPOSITE-SYNTHESIS §3, §5.5):

1. **Description** — what changed and why
2. **Related issue** — `Closes #NNN` or `Part of #NNN`
3. **MEU reference** — which MEU this PR implements (if applicable)
4. **Type of change** — checkboxes: bug fix, feature, breaking change, docs, refactor
5. **AI Assistance Disclosure** (mandatory section):
   - [ ] This PR was written entirely by a human
   - [ ] AI tools assisted (specify: Copilot/Claude/ChatGPT/other)
   - If AI-assisted: describe scope (boilerplate, test generation, full implementation)
   - "You own every line — AI-generated code that breaks tests or violates architecture will be rejected regardless of disclosure"
6. **Testing** — what tests were added/changed, `make check` output
7. **TDD Evidence** — for feature PRs: Red→Green screenshot or test output diff
8. **Security Impact** — does this touch auth, encryption, financial calc, IPC, or localhost binding?
9. **Security Checklist** (conditional, if security-impacting):
   - [ ] Input validation on all new inputs
   - [ ] No hardcoded keys or secrets
   - [ ] Parameterized queries only (no raw SQL)
   - [ ] No sensitive data in error messages or logs
   - [ ] Dependency audit on new security libraries
10. **Checklist** — standard items: tests pass, linter clean, docs updated

### Issue Template Requirements

**bug_report.yml:**
- Bug description (required)
- Steps to reproduce (required)
- Expected vs actual behavior (required)
- Environment (OS, Python version, Node version, Electron version)
- Screenshots/logs (optional)

**feature_request.yml:**
- Problem description (required)
- Proposed solution (required)
- Alternative approaches considered (optional)
- MEU reference (optional — link to BUILD_PLAN.md if relevant)

**config.yml:**
```yaml
blank_issues_enabled: false
contact_links:
  - name: 🔒 Security Vulnerability
    url: https://github.com/matbanik/zorivest/security/advisories/new
    about: Report security vulnerabilities through GitHub's private reporting channel
  - name: 💬 Questions & Discussion
    url: https://github.com/matbanik/zorivest/discussions
    about: Ask questions and discuss ideas
```

---

## §12.3 — Contributor Guide (MEU-210)

### Deliverables

| File | Purpose |
|:-----|:--------|
| `CONTRIBUTING.md` | Main contribution guide (~390 lines) — human root |
| `CODE_OF_CONDUCT.md` | Contributor Covenant 2.1 verbatim |

### CONTRIBUTING.md Structure

From COMPOSITE-SYNTHESIS §8 (unified outline):

| # | Section | Content |
|:--|:--------|:--------|
| 1 | Vision & Values | 3 principles: correctness > speed; locality + encryption; architecture as guardrail |
| 2 | Quick Start (5 min) | `git clone` → `uv sync && pytest` → `pnpm install && pnpm test` |
| 3 | Development Environment | Brief intro → link to `docs/DEVELOPMENT.md` (hub-and-spoke) |
| 4 | Types of Contributions | Bug reports, docs, tests, bug fixes, features, MEUs, security |
| 5 | MEU Model & Where to Start | Good-first-issue → good-second-issue → regular contributor (retention pipeline) |
| 6 | Code Style | ruff (`select = ["ALL"]`), pyright strict, ESLint + Prettier; dependency rule: domain never imports infra |
| 7 | Testing Policy | TDD mandatory: tests first, tests immutable; property tests for financial math; `make check` |
| 8 | Pull Request Process | Fork → branch → make check → PR template → CI green → review; "one logical change per PR" |
| 9 | Security Contributions | `security-impact` label, extra CI, 24-hour cooldown, no public exploit details |
| 10 | AI-Assisted Contributions | Disclosure when, how, scope; rejection criteria; "you own every line"; commit trailer format |
| 11 | Recognition | CONTRIBUTORS.md, regular-contributor label (≥3 PRs over ≥6 weeks), governance rights |
| 12 | Governance | Link to GOVERNANCE.md; BDFL today, evolution trigger documented |

### CODE_OF_CONDUCT.md

Use [Contributor Covenant v2.1](https://www.contributor-covenant.org/version/2/1/code_of_conduct/) verbatim. Set enforcement contact to `matbanik` GitHub profile or a dedicated email.

---

## §12.4 — Development Setup & Public AGENTS.md (MEU-211)

### Deliverables

| File | Purpose |
|:-----|:--------|
| `docs/DEVELOPMENT.md` | Full development environment setup (~200 lines) |
| `AGENTS.md` (root) | Public AI agent instructions (≤200 lines) |
| `README.md` (update) | Add links to all new contributor docs |

### DEVELOPMENT.md Structure

From COMPOSITE-SYNTHESIS §8 item 3, Claude draft §5.6:

1. **Prerequisites** — Python 3.12+, Node 20+, pnpm, uv, SQLCipher (optional)
2. **Clone & Install** — step-by-step commands for each package
3. **Running the Application** — backend API, Electron GUI, MCP server
4. **Running Tests** — pytest, vitest, pyright, ruff, full validation
5. **Database** — SQLCipher setup (optional, graceful degradation), Alembic migrations
6. **Troubleshooting Table** — common issues with solutions:
   - SQLCipher not found → fallback to plain SQLite
   - Port 17787 in use → check for zombie processes
   - `electron-store` CJS error → pin to v8
   - Windows charmap error → structlog UTF-8 config
7. **Canonical Ports** — `17787` (API), `5173` (Vite dev)
8. **Makefile / pyproject.toml scripts** — document `make check`, `make test`, `make lint`

### Root AGENTS.md

≤200 lines. Global workspace rules for external contributors' AI tools. Must include:

1. **Project identity** — Zorivest is a trading portfolio management tool (plans and evaluates, never executes trades)
2. **Build commands** — `uv sync`, `pnpm install`, `uv run pytest`, `npx vitest run`
3. **Test commands** — full validation: `uv run python tools/validate_codebase.py`
4. **Dependency rule** — Domain → Application → Infrastructure; never import infra from core
5. **Architecture summary** — Python backend (core/infra/api) + TypeScript frontend (Electron/React) + MCP server
6. **Canonical port** — `17787` for all API references
7. **TDD mandate** — tests first, tests immutable, never modify tests to make them pass
8. **Anti-placeholder** — no TODO/FIXME/NotImplementedError in submitted code
9. **Cross-references** — link to CONTRIBUTING.md, docs/DEVELOPMENT.md

> **Do NOT duplicate `.agent/AGENTS.md` content.** The root file is a slim, public-facing summary. The internal agent file is for dedicated AI coding agents with session management, handoff protocols, etc.

---

## §12.5 — Governance, AI Policy & Architecture (MEU-212)

### Deliverables

| File | Purpose |
|:-----|:--------|
| `GOVERNANCE.md` | Decision-making model (~110 lines) |
| `docs/AI_POLICY.md` | Long-form AI assistance policy (~150 lines) |
| `docs/ARCHITECTURE.md` | Dependency rule, layer boundaries, MEU concept (~200 lines) |

### GOVERNANCE.md

From COMPOSITE-SYNTHESIS §6, Claude §5.4:

1. **Current model:** BDFL (Benevolent Dictator For Life) — @matbanik
2. **Decision authority:** All merge, release, and architecture decisions
3. **Evolution trigger:** 3 sustained contributors (≥3 PRs each over ≥6 weeks) → governance discussion opens
4. **Evolution path:** BDFL → Core Team (2-3 committers with merge rights) → Foundation (if adoption warrants)
5. **RFC process:** Major changes require issue discussion before PR; no "lazy consensus" for architecture-level changes

### AI_POLICY.md

From COMPOSITE-SYNTHESIS §5:

1. **Disclosure requirement:** Any PR where AI assisted beyond single-line autocomplete must disclose
2. **Threshold:** "More than a single function or test" → mandatory disclosure
3. **Detection stance:** Self-disclosure is authoritative; heuristic detection is a signal, not proof
4. **Rejection criteria:** Undisclosed AI code discovered post-merge → revert + contributor conversation (not ban)
5. **Commit trailer format:** `AI-Assisted-By: Claude 4 (boilerplate generation)`
6. **Ownership:** "You own every line. AI-generated code that violates architecture, breaks tests, or introduces security issues will be rejected — the tool is not an excuse"

### ARCHITECTURE.md

From existing `.agent/docs/architecture.md` + COMPOSITE-SYNTHESIS §8 item 3:

1. **Layer diagram** — Domain → Infrastructure → Services → API → MCP → GUI
2. **Dependency rule** — inner layers never import from outer layers
3. **Package map** — packages/core, packages/infrastructure, packages/api, ui/, mcp-server/
4. **MEU concept** — what is a Manageable Execution Unit, how to find available ones
5. **Testing pyramid** — unit → integration → E2E; coverage targets (advisory)

---

## §12.6 — AI Tool Configuration Files (MEU-213)

### Deliverables

| File | Purpose |
|:-----|:--------|
| `CLAUDE.md` | Thin redirect to root `AGENTS.md` + Claude-specific notes |
| `.windsurfrules` | Symlink to `AGENTS.md` |
| `packages/core/AGENTS.md` | Per-package AI rules: domain layer constraints |
| `packages/infrastructure/AGENTS.md` | Per-package AI rules: infra layer constraints |
| `packages/api/AGENTS.md` | Per-package AI rules: API layer constraints |
| `ui/AGENTS.md` | Per-package AI rules: UI layer constraints |
| `mcp-server/AGENTS.md` | Per-package AI rules: MCP server constraints |
| `.github/ISSUE_TEMPLATE/docs_improvement.yml` | Documentation improvement form |

### Per-Package AGENTS.md Pattern

Following openai/codex nested pattern (closest-file-wins):

Each per-package file is ≤60 lines and contains:
- Package-specific build/test commands
- Layer-specific constraints (e.g., core: "no SQLAlchemy imports")
- Key files and their purpose
- Package-specific testing notes

### CLAUDE.md

```markdown
# Claude Code Instructions — Zorivest

Read and follow `AGENTS.md` as the primary source of truth.
For detailed contribution guidelines, see `CONTRIBUTING.md`.
```

### GEMINI.md Update

The existing `GEMINI.md` currently redirects to `.agent/AGENTS.md` (internal). It should be updated to reference both:
- Root `AGENTS.md` for contribution guidelines (external)
- `.agent/AGENTS.md` for internal agent protocols (preserved as-is)

### .windsurfrules

Symlink to `AGENTS.md` (root). On Windows, create as a text file with identical content if symlinks are problematic.

---

## §12.7 — Native AI Tool Rules (MEU-214)

### Deliverables

| File | Purpose |
|:-----|:--------|
| `.github/copilot-instructions.md` | GitHub Copilot native rules with `applyTo:` filters |
| `.cursor/rules/dependency-rule.mdc` | Cursor glob-scoped: no infra imports in core |
| `.cursor/rules/tdd-policy.mdc` | Cursor glob-scoped: test immutability in tests/ |
| `CODEOWNERS` | Auto-assign security reviewers for sensitive paths |

### Copilot Instructions

~50 lines. Uses Copilot's native `applyTo:` syntax for per-language routing:

```markdown
## Python Guidelines
applyTo: **/*.py
- Follow ruff linting rules
- Use type hints on all function signatures
- Domain layer (packages/core/) must not import from infrastructure

## TypeScript Guidelines  
applyTo: **/*.ts, **/*.tsx
- Follow ESLint + Prettier configuration
- Use strict TypeScript (no `any`)
```

### Cursor Rules

**dependency-rule.mdc:**
```yaml
---
description: Domain layer must not import from infrastructure
globs: packages/core/**/*.py
alwaysApply: true
---
Do not import from packages/infrastructure or packages/api.
Domain layer is pure Python with no external dependencies except Pydantic.
```

**tdd-policy.mdc:**
```yaml
---
description: Test immutability — never modify test assertions to make them pass
globs: tests/**/*.py
alwaysApply: true
---
Tests are specifications. Fix the implementation, not the tests.
Never weaken assertions, delete test cases, or modify expected values.
```

### CODEOWNERS

```
# Security-sensitive paths require maintainer review
packages/core/src/zorivest_core/services/encryption* @matbanik
packages/infrastructure/src/zorivest_infra/database/sqlcipher* @matbanik
packages/api/src/zorivest_api/routes/auth* @matbanik
mcp-server/src/auth/ @matbanik
SECURITY.md @matbanik
.github/workflows/ @matbanik
```

---

## §12.8 — Contributor CI & Recognition (MEU-215)

### Deliverables

| File | Purpose |
|:-----|:--------|
| `tools/validate_agent_files.py` | CI script: AGENTS.md drift detection, redirect integrity |
| `.github/ISSUE_TEMPLATE/agent_issue.yml` | "AGENTS.md told my AI wrong" feedback template |
| `CONTRIBUTORS.md` | Contributor recognition file |

### validate_agent_files.py

Validation checks:
1. Root `AGENTS.md` is ≤200 lines
2. `CLAUDE.md` contains `@AGENTS.md` redirect reference
3. `.windsurfrules` content matches `AGENTS.md` (or is symlink)
4. Per-package `AGENTS.md` files exist for all 5 packages
5. No package AGENTS.md exceeds 60 lines
6. Root AGENTS.md contains required sections (build commands, test commands, dependency rule)

### agent_issue.yml

```yaml
name: 🤖 AI Agent Issue
description: Report when AGENTS.md gave your AI tool incorrect instructions
labels: ["agents-md", "bug"]
body:
  - type: dropdown
    id: tool
    attributes:
      label: Which AI tool?
      options:
        - Claude Code
        - GitHub Copilot
        - Cursor
        - Windsurf
        - Gemini CLI
        - Other
    validations:
      required: true
  - type: textarea
    id: instruction
    attributes:
      label: What instruction was wrong?
      description: Quote the specific line or section from AGENTS.md
    validations:
      required: true
  - type: textarea
    id: expected
    attributes:
      label: What should it say instead?
    validations:
      required: true
```

### CONTRIBUTORS.md

Initial content lists the maintainer. Future contributors are added automatically via all-contributors bot or manually after merged PRs.

---

## Phase Exit Criteria

### P0 Exit (MEU-208 → MEU-211)
- [ ] SECURITY.md exists with PVR link, SLAs, scope, no-bounty
- [ ] PR template exists with AI disclosure section
- [ ] 3 issue templates exist (bug, feature, config)
- [ ] CONTRIBUTING.md exists with all 12 sections
- [ ] CODE_OF_CONDUCT.md exists (Contributor Covenant 2.1)
- [ ] docs/DEVELOPMENT.md exists with troubleshooting table
- [ ] Root AGENTS.md exists (≤200 lines)
- [ ] README.md updated with links to all new docs

### P1 Exit (MEU-212 → MEU-213)
- [ ] GOVERNANCE.md exists with BDFL model + evolution trigger
- [ ] docs/AI_POLICY.md exists with disclosure requirements
- [ ] docs/ARCHITECTURE.md exists with layer diagram
- [ ] CLAUDE.md exists as redirect
- [ ] .windsurfrules exists as symlink/copy
- [ ] Per-package AGENTS.md exists for all 5 packages
- [ ] docs_improvement.yml issue template exists

### P2 Exit (MEU-214 → MEU-215)
- [ ] .github/copilot-instructions.md exists with `applyTo:` syntax
- [ ] .cursor/rules/ contains 2 `.mdc` files
- [ ] CODEOWNERS exists for security-sensitive paths
- [ ] tools/validate_agent_files.py passes
- [ ] agent_issue.yml template exists
- [ ] CONTRIBUTORS.md exists
