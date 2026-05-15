# Zorivest Contribution Documentation Suite — Design & Production Templates

## 1. Reasoning Summary

Zorivest sits at the intersection of three properties that most open-source playbooks treat in isolation: (a) it handles **real financial data** behind an encrypted SQLCipher boundary, (b) it is a **hybrid Python + TypeScript monorepo** with strict architectural layering (Domain → Application → Infrastructure), and (c) it is **AI-agent-first by construction** — the `.agent/` directory of roles, workflows, and skills is part of the product, not bolted on. The contribution suite must therefore optimize for four readers in priority order: (1) the solo BDFL maintainer who must defend the codebase from "plausible but wrong" PRs at scale, (2) human contributors learning the architecture, (3) AI coding agents (Codex, Claude Code, Cursor, Copilot, Windsurf) reading machine-targeted context, and (4) security researchers who need a safe disclosure channel.

The single most important architectural choice is that **AGENTS.md and CONTRIBUTING.md are siblings, not duplicates**, and they reference each other rather than restating each other. CONTRIBUTING.md owns *values, process, and accountability*; AGENTS.md owns *machine-actionable build/test/verify commands and architectural constraints*. When the two overlap, AGENTS.md links to CONTRIBUTING.md ("Code style: see CONTRIBUTING.md §6"); CONTRIBUTING.md links to AGENTS.md ("Agents read AGENTS.md automatically; see it for command details"). This mirrors the agents.md project's own guidance that AGENTS.md should "complement existing README and docs" rather than duplicate them. The format has broad adoption — over 60,000 open-source projects according to agents.md — and is now stewarded by the Agentic AI Foundation under the Linux Foundation, having emerged from collaboration across OpenAI Codex, Amp, Jules from Google, Cursor, and Factory. Length discipline matters: Augment Code's in-house study (augmentcode.com) reports that "The 100–150 line AGENTS.md files with a handful of focused reference documents were the top performers in our study, delivering 10–15% improvements across all metrics in mid-size modules of around 100 core files. Once the main file got longer than that, the gains started reversing."

The second most important choice is the **redirect-by-default, native-where-justified** strategy for per-tool files. The survey conducted as part of this research (Section 4) shows that the redirect/symlink approach is the most common pattern for small-to-medium projects, but specific tools — particularly Cursor's `.cursor/rules/*.mdc` with `globs:` and `alwaysApply:` frontmatter, and GitHub Copilot's `.github/instructions/*.instructions.md` with `applyTo:` filters — provide capabilities that a single AGENTS.md cannot replicate. Zorivest should ship a *minimal native footprint*: AGENTS.md is canonical; CLAUDE.md, GEMINI.md, and `.windsurfrules` are thin redirect stubs (or git-ignored symlinks); but `.github/copilot-instructions.md` and one or two `.cursor/rules/*.mdc` files are kept *native* for the specific case of layering directory-scoped rules.

Third: **llms.txt is not worth shipping for Zorivest at this stage**. The spec was proposed by Jeremy Howard (co-founder of Answer.AI and fast.ai) on September 3, 2024 in his Answer.AI post, and gained adoption via Mintlify in November 2024. But SE Ranking's analysis of 300,000 domains found that, in their words on seranking.com/blog/llms-txt/, "LLMs.txt doesn't impact how AI systems see or cite your content today." IDE agents (Cursor, Continue, Cline) do read it, but major LLM crawlers (GPTBot, ClaudeBot, Google-Extended) do not fetch it in meaningful volume. Zorivest's "documentation" is the code itself and a `docs/` tree consumed mostly by coding agents that already have AGENTS.md. Revisit when a public docs site exists.

Fourth: **governance must be honest about its current state**. Zorivest is a one-person project. Pretending otherwise creates false expectations. GOVERNANCE.md anchors on BDFL with an explicit, public, time-boxed evolution trigger — the "three sustained contributors over six months" condition — and lists what changes when that trigger fires. This is the Python pattern (Guido van Rossum stepped down as BDFL in July 2018; PEP 13 codified a five-member steering council; the inaugural January 2019 council elected was Barry Warsaw, Brett Cannon, Carol Willing, Nick Coghlan, and Guido van Rossum himself) and the Django pattern (DEP 10, adopted on March 12, 2020 — per James Bennett's announcement, "As of the adoption of DEP 10, the structure of the Django open-source project is changing in several ways. The former 'core team' is now dissolved.") compressed to a single-page commitment.

Fifth: **AI-generated contributions are welcomed, with disclosure required, and CI is the enforcement layer — not human suspicion.** Following the Apache Software Foundation's June 2023 guidance (which recommends a "Generated-by: [tool name]" commit trailer) and the Fedora Project's 2025 policy ("The contributor is always the author and is fully accountable for the entire contribution, whether a human wrote it or an AI assisted it," using an "Assisted-by:" tag), Zorivest treats AI assistance as a normal tool whose use must be disclosed in the PR body and (for substantial generation) in a commit trailer. Mitchell Hashimoto's Ghostty project is the leading model for this norm — Hashimoto escalated the policy in a January 22, 2026 X post that drew 174K views: "AI assisted PRs are now only allowed for accepted issues. Drive-by AI PRs will be closed without question." SpecStory's newsletter subsequently reported that "within weeks of the rule taking effect, about fifty percent of all Ghostty pull requests included an AI disclosure." CI then runs the same gate regardless of authorship: type check, lint, test, anti-placeholder scan, dependency-rule check; AI-tagged PRs receive additional automated review for the failure modes specific to AI code.

---

## 2. File Architecture Decision Record

### 2.1 File inventory

| File | Purpose | Audience | Length | Priority | Reference exemplar |
|---|---|---|---|---|---|
| `README.md` | Product description, install/run quickstart, links to all other docs. | Humans | Medium | P0 | bitwarden/bitwarden |
| `CONTRIBUTING.md` | Values, contribution types, TDD policy, PR process, AI disclosure, security workflow. | Humans (AI agents read on instruction from AGENTS.md) | Long | P0 | rust-lang/rust |
| `CODE_OF_CONDUCT.md` | Contributor Covenant 2.1 verbatim with contact slot filled in. | Humans | Medium | P0 | thousands of projects |
| `SECURITY.md` | Scope, GitHub Private Vulnerability Reporting channel, response SLA. | Security researchers | Short | P0 | github/securitylab template |
| `GOVERNANCE.md` | BDFL today, documented trigger to meritocracy, MEU prioritization. | Humans considering long-term commitment | Short | P1 | Python PEP 13; Django DEP 10 |
| `AGENTS.md` (root) | Machine-actionable build/test/verify commands; architectural constraints. | AI coding agents | ≤200 lines | P0 | openai/codex |
| `packages/core/AGENTS.md` | Core-specific rules: pure domain, no infra imports, Decimal arithmetic. | AI agents in core | Short | P1 | per-crate AGENTS.md in openai/codex |
| `packages/infrastructure/AGENTS.md` | SQLCipher/SQLAlchemy idioms, repo-pattern rules, unit-of-work boundary. | AI agents in infra | Short | P1 | nested AGENTS.md pattern |
| `packages/api/AGENTS.md` | FastAPI patterns, request/response schemas, localhost-binding rules. | AI agents in api | Short | P1 | nested AGENTS.md pattern |
| `ui/AGENTS.md` | Electron + React + Vite specifics; IPC boundary rules. | AI agents in ui | Short | P1 | nested AGENTS.md pattern |
| `mcp-server/AGENTS.md` | MCP server rules, tool surface, never expose raw DB. | AI agents in mcp-server | Short | P1 | nested AGENTS.md pattern |
| `.github/copilot-instructions.md` | **Native** — Copilot-specific rules with `applyTo:` instructions files. | GitHub Copilot only | ~50 lines | P2 | microsoft/vscode |
| `.cursor/rules/dependency-rule.mdc` | **Native** — Cursor rule with `globs: packages/core/**/*.py` enforcing no-infra-imports rule. | Cursor only | ≤30 lines | P2 | supabase/supabase |
| `CLAUDE.md` | Thin redirect: `@AGENTS.md` import + a few Claude-specific notes. | Claude Code | ≤10 lines | P1 | trigger.dev pattern |
| `GEMINI.md`, `.windsurfrules` | Symlinks to AGENTS.md (note Windows `core.symlinks=true` requirement). | Gemini CLI, Windsurf | Trivial | P2 | community symlink pattern |
| `docs/DEVELOPMENT.md` | Long-form prerequisites, repo setup, dev loops, troubleshooting. | New human contributors | Long | P0 | n8n-io/n8n |
| `docs/ARCHITECTURE.md` | Dependency rule, layer boundaries, MEU concept, port/adapter pattern. | Both | Medium | P1 | hashicorp/vault docs |
| `docs/AI_POLICY.md` | Detailed AI-assistance policy: what to disclose, how, what is "substantial". | Both | Medium | P1 | jellyfin LLM policy; Will McGugan AI_POLICY.md |
| `.github/PULL_REQUEST_TEMPLATE.md` | Unified template with AI-disclosure, security checklist, MEU link, TDD evidence. | Both | Short | P0 | many |
| `.github/ISSUE_TEMPLATE/bug_report.yml` | Structured bug-report form. | Humans | Short | P0 | many |
| `.github/ISSUE_TEMPLATE/feature_request.yml` | Structured feature-request form. | Humans | Short | P0 | many |
| `.github/ISSUE_TEMPLATE/docs_improvement.yml` | Docs improvement form. | Humans | Short | P1 | many |
| `.github/ISSUE_TEMPLATE/agent_issue.yml` | "My AI agent did the wrong thing because AGENTS.md said X" feedback. | Humans using AI | Short | P2 | novel |
| `.github/ISSUE_TEMPLATE/config.yml` | Disables blank issues; redirects security reports to Private Vulnerability Reporting. | All | Trivial | P0 | GitHub docs |
| `tools/validate_codebase.py` | Anti-placeholder scan, dependency-rule scan, AGENTS.md drift check. | CI | n/a | P0 | project-internal |

### 2.2 Dependency graph

```
README.md ──► CONTRIBUTING.md ──► CODE_OF_CONDUCT.md
                │                ──► SECURITY.md
                │                ──► GOVERNANCE.md
                │                ──► docs/DEVELOPMENT.md ──► docs/ARCHITECTURE.md
                │                ──► docs/AI_POLICY.md
                │                ──► AGENTS.md
                ▼
AGENTS.md ──► .agent/AGENTS.md           (existing instruction tree)
   │       ──► CONTRIBUTING.md (values + AI-disclosure rules)
   │       ──► docs/ARCHITECTURE.md (dependency rule)
   │       ──► packages/*/AGENTS.md (nested, scope-narrowed)
   │
   ▼  (resolved by tooling, not by humans)
CLAUDE.md (@import AGENTS.md)
GEMINI.md (symlink to AGENTS.md)
.windsurfrules (symlink to AGENTS.md)
.github/copilot-instructions.md (native — Copilot-specific tools/applyTo)
.cursor/rules/*.mdc (native — glob-scoped rules)

.github/PULL_REQUEST_TEMPLATE.md ──► references CONTRIBUTING.md §AI, §TDD, §Security
.github/ISSUE_TEMPLATE/config.yml ──► routes security to GitHub PVR (per SECURITY.md)
```

### 2.3 Why this graph

Two non-obvious decisions:

1. **CONTRIBUTING.md is the root of the human graph; AGENTS.md is the root of the machine graph.** They cross-reference once each (no further). This prevents the "duplicate the build commands in three places and watch them rot" problem documented as a top failure mode for AGENTS.md files.
2. **`.agent/` (the existing tree) is downstream of AGENTS.md, not parallel to it.** AGENTS.md is the entry point; it tells an agent "for the orchestrator workflow, read `.agent/workflows/create-plan.md`". This matches Anthropic's progressive-disclosure recommendation for Claude Skills and the nested pattern Codex uses.

### 2.4 Monorepo per-package strategy

Verified pattern from openai/codex (the agents.md spec author): one root AGENTS.md plus per-crate/per-package nested files where the closest AGENTS.md to the edited file wins. Zorivest adopts the same: one root file (≤200 lines) covering global workspace rules, plus a ~30–60 line file per package covering language- and layer-specific rules. Nx and Turborepo do not impose a separate CONTRIBUTING convention per package; the dominant pattern across both ecosystems is a single root CONTRIBUTING.md with a "package-specific setup" section that links into each package's README. Zorivest follows that pattern: no per-package CONTRIBUTING.md, but per-package AGENTS.md and per-package README.md.

---

## 3. AI-Agent Strategy

### 3.1 Survey of 5 notable projects' native-per-tool practices

**microsoft/vscode** maintains a 152-line native `.github/copilot-instructions.md` and a parallel `.github/agents/Reviewer.agent.md` Copilot custom-agent definition. There is no AGENTS.md, no CLAUDE.md, no `.cursor/rules/`. The Copilot file uses tool-aware instructions like `#runTasks/getTaskOutput` (a Copilot-only mechanism) and includes a custom agent declaring `tools: ['vscode/askQuestions', 'vscode/vscodeAPI', 'read', 'agent', 'search', 'web']`. **Lesson for Zorivest:** Copilot's `.github/agents/*.agent.md` and `.github/instructions/*.instructions.md` (with YAML `applyTo:` frontmatter) carry capabilities AGENTS.md cannot — declarative tool lists and file-pattern-scoped instructions. This is the strongest argument for keeping `.github/copilot-instructions.md` as a *thin native* file rather than a symlink.

**openai/codex** maintains a 219-line root AGENTS.md plus many nested per-crate AGENTS.md files. No CLAUDE.md, no `.cursor/rules`. It explicitly demonstrates the "closest file wins" pattern: the root file covers Rust workspace conventions (crate naming prefixed with `codex-`, sandbox-env-var rules, a directive to "resist adding code to codex-core"), while per-crate files carry crate-local protocol rules (e.g., `#[serde(rename_all = "camelCase")]` for the app-server protocol). The repo also supports an `AGENTS.override.md` file that *replaces* (rather than merges) parent guidance — useful for sub-projects with materially different rules. **Lesson for Zorivest:** the nested pattern works at scale, with discipline. Override semantics are not needed for Zorivest's five packages.

**triggerdotdev/trigger.dev** maintains a root `CLAUDE.md` plus subdirectory CLAUDE.md files in `apps/webapp/`, `docs/`, and `internal-packages/run-engine/`. There is no AGENTS.md and no `.cursor/rules`. The root file declares that subdirectory CLAUDE.md files provide deeper context as Claude navigates and uses Anthropic's `@import` syntax to pull in shared content. They also ship a `.claude/skills/trigger-dev-tasks/` directory using Anthropic's Skill format (progressive-disclosure SKILL.md files). **Lesson for Zorivest:** if you commit primarily to Claude Code, you can build deeply on CLAUDE.md's hierarchy plus `.claude/skills/` — but you lose portability. Zorivest's existing `.agent/skills/` directory should remain tool-agnostic, not Claude-specific.

**supabase/supabase** maintains `.cursor/rules/` natively with per-domain MDC files (database functions, RLS policies, edge functions, migrations) each carrying YAML frontmatter like:

```mdc
---
description: Guidelines for writing Supabase database functions
globs: ["**/*.sql", "supabase/migrations/**/*"]
alwaysApply: false
---
```

These rules are *auto-attached* by Cursor only when a matching file is in context — a capability AGENTS.md cannot provide. **Lesson for Zorivest:** Cursor's glob-scoped `.mdc` files are uniquely useful for *narrow, conditional* rules like "when editing `packages/core/**/*.py`, do not import from `packages/infrastructure/`". This is exactly the kind of rule Zorivest's dependency policy needs.

**continuedev/continue** maintains a `.claude/` directory at root and parallel `.continue/skills/` directories, mirroring Claude Code's skill format for their own CLI. No public AGENTS.md at root. **Lesson for Zorivest:** projects that ship their own AI coding tool tend to invest heavily in native files; Zorivest, a consumer of these tools, should not.

### 3.2 Two approaches compared

| Dimension | Redirect / single-source (AGENTS.md canonical) | Native per-tool files |
|---|---|---|
| Setup effort | Low (one file + 3 symlinks/redirects) | High (4–6 files maintained in parallel) |
| Drift risk | Low (one source of truth) | High (the symlink-recommendation industry exists *because of* this risk) |
| Tool-unique capabilities | Lost (no glob-scoped rules, no `applyTo`, no `tools:` arrays) | Preserved |
| Onboarding new tools | Trivial (new tool reads AGENTS.md or gets a new redirect) | Manual (port the rules to the new tool's format) |
| Best for | Small/medium projects, single maintainer, interchangeable tools | Large projects, dedicated tooling teams, one-tool-deep workflows |

### 3.3 Recommendation for Zorivest: hybrid, leaning redirect

Ship:

- **`AGENTS.md` (root + 5 nested)** — canonical; ≤200 lines at root, ≤60 lines per package. Augment Code's study indicates 100–150 lines is the sweet spot; treat 200 as the hard ceiling.
- **`CLAUDE.md`** — a few-line file containing `@AGENTS.md` followed by 3–4 lines of Claude-Code-specific notes (e.g., "Prefer plan mode for changes touching `packages/infrastructure/`"). This is the Anthropic-documented pattern and avoids cross-platform symlink issues on Windows.
- **`GEMINI.md`, `.windsurfrules`** — committed symlinks to `AGENTS.md`. Document the Windows `git config core.symlinks=true` requirement in DEVELOPMENT.md.
- **`.github/copilot-instructions.md`** — *native*, ~50 lines, focused on Copilot-only capabilities: a `tools:` declaration for a reviewer-agent role and `applyTo:` filters routing Python-vs-TypeScript-specific instructions. Justification: the survey shows this is the one tool where going native repays the cost in capability.
- **`.cursor/rules/dependency-rule.mdc`** and **`.cursor/rules/tdd-policy.mdc`** — *native*, each ≤30 lines, using `globs:` to scope to `packages/core/**/*.py` and `tests/**/*.py` respectively. Justification: directory-scoped rule enforcement is Cursor's killer feature for layered architectures, and Zorivest's whole point is enforcing a layered architecture. Note: per Cursor documentation and community testing, `alwaysApply: true` overrides `globs` — use one or the other.

A `tools/validate_agent_files.py` script (added to `tools/validate_codebase.py`) should run in CI and verify (a) all redirect stubs still resolve, (b) native files do not duplicate AGENTS.md beyond a small allowed overlap, and (c) AGENTS.md does not exceed 200 lines.

### 3.4 llms.txt: defer

The spec is real and adopted by Anthropic, Cursor, Cloudflare, and others for documentation *websites*. But SE Ranking's 300,000-domain analysis (seranking.com/blog/llms-txt/) concluded plainly: "LLMs.txt doesn't impact how AI systems see or cite your content today." For Zorivest today (a code repository without a public docs site), **do not adopt**. Revisit when `docs.zorivest.io` or equivalent exists.

### 3.5 Preventing "plausible but wrong" AI contributions

Five layers, ordered from prevention to detection:

1. **Specification immutability (TDD).** Tests are written before implementation and are immutable specs. An AI agent cannot "fix the failing test by changing the test"; the validation script rejects PRs that modify tests in the same commit as the implementation they cover (unless labeled `test-update` and reviewed separately).
2. **Anti-placeholder scan.** CI rejects PRs containing `TODO`, `FIXME`, `pass  # implement`, `raise NotImplementedError`, `... # rest of code`, or "// existing code here" comments outside an allowlist. This is the single most effective gate against vibe-coded PRs.
3. **Dependency-rule scan.** `tools/validate_codebase.py` parses imports in `packages/core/` and fails the PR if any infrastructure module is imported. AI agents reliably violate this rule when not constrained; the scan makes violations visible immediately.
4. **Anti-fabrication checks.** Every PR runs `pip-audit`/`pnpm audit` and the dependency lockfile diff is inspected; PRs introducing a brand-new dependency must justify it. This catches fabricated package names (hallucinated imports).
5. **AI-disclosure tagging.** PRs with a `Co-Authored-By` or `Assisted-by:` commit trailer, or with the AI-disclosure section of the PR template filled in, receive an automatic `ai-assisted` label. A second labeler reads the PR body for explicit disclosure phrases. Reviewers know to apply additional scrutiny to AI-labeled PRs.

---

## 4. GitHub Templates & Automation (Documentation Only)

### 4.1 Checks on every PR

| Check | Tool | Failure means |
|---|---|---|
| Python type check | `uv run mypy --strict packages/` | Type errors. |
| TypeScript type check | `pnpm -r typecheck` | Type errors. |
| Python lint/format | `uv run ruff check && uv run ruff format --check` | Style/lint violations. |
| TypeScript lint | `pnpm -r lint` | ESLint violations. |
| Python tests | `uv run pytest packages/ -x` | Any test failure. |
| TypeScript tests | `pnpm -r test` | Any test failure. |
| Anti-placeholder scan | `python tools/validate_codebase.py --no-placeholders` | TODO/FIXME/NotImplementedError outside allowlist. |
| Dependency rule | `python tools/validate_codebase.py --dependency-rule` | Infra imported into core. |
| AGENTS.md drift | `python tools/validate_codebase.py --agents-drift` | AGENTS.md > 200 lines; broken redirects; CLAUDE.md content not matching `@AGENTS.md` import. |
| Lockfile integrity | `uv lock --check`, `pnpm install --frozen-lockfile` | Lockfiles out of sync. |
| AI disclosure check | Custom GitHub Action reads PR body and commit trailers | If trailers like `Co-Authored-By: Claude`, `Co-Authored-By: Copilot`, or `Assisted-by:` are present but disclosure section is empty → label `disclosure-missing` and comment. |
| Build smoke | `uv run python -m packages.api --check`; `pnpm build` | Build failure. |

### 4.2 Additional checks on `security-impact`-labeled PRs

Triggered when a PR touches `packages/infrastructure/security/`, `packages/infrastructure/crypto/`, `packages/api/auth/`, or modifies SQLCipher key handling:

| Check | Tool | Why |
|---|---|---|
| Secret scan | `gitleaks` | Hardcoded secrets even in tests. |
| SAST | `bandit` (Python), `semgrep` rules | Known vulnerability patterns. |
| Dependency audit | `pip-audit`, `pnpm audit --audit-level=moderate` | Vulnerable transitive dependencies. |
| Encrypted-DB integration test | Full pytest including `tests/integration/test_encrypted_db.py` | DB encryption boundary intact. |
| Required reviewer | CODEOWNERS forces maintainer review | No auto-merge. |
| 24-hour cooldown | Bot adds `do-not-merge/cooldown` | Prevents rushed merges of security-sensitive code. |

### 4.3 AI-code labeling strategy

Two-stage detector:

**Stage 1 — Self-disclosure (authoritative).** A GitHub Action reads:
- The PR body for an "AI Assistance" section filled in.
- Commit history for trailers matching `^(Co-Authored-By|Assisted-by|Generated-by):\s*(Claude|Copilot|Cursor|Codex|Gemini|ChatGPT)\b`.
- If any match: apply `ai-assisted` label and, where named, a sub-label like `ai/claude-code`, `ai/copilot`, etc.

**Stage 2 — Heuristic detection (signal, not verdict).** An optional AI-labeler GitHub Action (modeled on `jlowin/ai-labeler`) scans the diff for AI-code signals — exhaustive comments, near-duplicate snippets, unusual import patterns. Applies `ai-suspected` (not `ai-assisted`) and posts a non-blocking comment. This is explicitly a soft signal: per Overchat's AI Code Detector documentation (overchat.ai), "On shorter code (under 10–20 lines) or less common languages like Rust or Swift, accuracy drops to around 85–90% because short code gives too few distinguishing patterns," and Pangram Labs' own published figures indicate the tool "misses about 20% of AI-generated code" on short snippets. Use as signal, never verdict.

**Policy on disclosure correctness.** If `ai-suspected` is applied but the contributor confirms no AI use, a maintainer comment `/not-ai` removes it. Honest disagreement is fine; misrepresentation is a Code of Conduct issue.

**On the VS Code Copilot `git.addAICoAuthor` controversy** (April–May 2026, when Microsoft flipped the default from "off" to "all" on April 16, 2026 and then reversed it on May 3, 2026 after backlash): Zorivest treats `Co-Authored-By: Copilot` trailers as *informational*, not authoritative. The policy in CONTRIBUTING.md explicitly states that trailers are advisory; the PR-body disclosure is what counts.

---

## 5. Draft Templates (Production-Ready)

### 5.1 `CONTRIBUTING.md`

```markdown
# Contributing to Zorivest

Welcome. Zorivest is an open-source trading-portfolio management
application designed to run locally with end-to-end encrypted storage of
real brokerage data. This document explains how to contribute — what we
value, how we work, and how we keep the project trustworthy.

If you are an AI coding agent, read `AGENTS.md` first; it gives you the
commands you need. Then come back here for the *why* and the *process*.

## Table of Contents

1. Vision & values
2. Quick start (5 minutes)
3. Development environment (full setup)
4. Types of contributions
5. The MEU model & where to start
6. Code style
7. Testing policy (TDD is mandatory)
8. Pull request process
9. Security-sensitive contributions
10. AI-assisted contributions
11. Recognition
12. Governance & decision-making

## 1. Vision & values

Zorivest's job is to be the trustworthy local home for a person's
trading history. Three principles in priority order:

1. **Correctness over speed.** A miscalculated cost basis is worse
   than no cost basis. Financial arithmetic uses `Decimal`, never
   `float`. Tests come before code.
2. **Locality and encryption.** All data stays on the user's machine.
   The API binds to `127.0.0.1`. The database is SQLCipher-encrypted at
   rest. These are non-negotiable.
3. **Architecture as a guardrail, not a preference.** Domain → Application
   → Infrastructure is enforced in CI. Code that violates this rule is
   rejected even if it works.

## 2. Quick start

\`\`\`bash
git clone https://github.com/matbanik/zorivest.git
cd zorivest
uv sync && uv run pytest packages/core
pnpm install && pnpm -r test
\`\`\`

Full setup is in [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md).

## 3. Development environment

See `docs/DEVELOPMENT.md` for the long form. Required: Python 3.12+,
Node.js 22+, `uv` (latest), `pnpm` 9+. The repository is a hybrid
monorepo: `packages/` is Python (uv workspaces), `ui/` and
`mcp-server/` are TypeScript (pnpm workspaces).

## 4. Types of contributions

- **Bug reports** — use the bug-report issue template.
- **Documentation** — typos, clarifications, missing examples; no
  prior issue required.
- **Tests** — adding tests to under-covered modules is always welcome.
- **Bug fixes** — comment on the bug-report issue saying you'll take it.
- **New features** — open a discussion (or feature-request issue)
  first.
- **MEU implementations** — `docs/BUILD_PLAN.md` lists 200+ Manageable
  Execution Units. Pick one labeled `meu/available`.
- **Security research** — see `SECURITY.md`. Do not file public issues.

## 5. The MEU model & where to start

Zorivest is built as a sequence of Manageable Execution Units. Each MEU
is small, atomic, with pre-written acceptance tests, a documented
architectural layer, and a target package. New contributors should pick
an MEU labeled `meu/good-first-issue` — work is bounded and tests
already exist.

## 6. Code style

Python: ruff (project config in `pyproject.toml`), mypy strict, type
hints required on public functions. TypeScript: ESLint + Prettier,
`strict: true`, no `any` without explicit justification.

The dependency rule is enforced in `tools/validate_codebase.py`:
`packages/core` may not import from `packages/infrastructure` or
`packages/api`. CI fails your PR if violated.

## 7. Testing policy — TDD is mandatory

This is the most important policy in the project and differs from most
open-source projects.

- **Tests are written before implementation.** The test commit must
  come before the implementation commit. The PR description must show
  this.
- **Tests are immutable specifications.** You may not modify an
  existing test in the same PR as the implementation it covers. Open a
  separate PR labeled `test-update` first.
- **Meaningful tests beat coverage targets.** A test exercising the
  happy path and three failure modes beats five tests of the same
  happy path with different inputs.
- **Property tests for financial math.** Cost-basis, FIFO/LIFO, and
  currency-conversion calculations must include `hypothesis` property
  tests.
- **Integration tests use real SQLCipher.** Mock the network, not the
  database.

## 8. Pull request process

1. Fork, branch (`feat/...`, `fix/...`, `docs/...`, `refactor/...`,
   `test/...`).
2. Run `make check` (same gates as CI).
3. Open a PR using the template. Fill every applicable section
   including AI disclosure (§10) if AI was used.
4. CI must be green. Do not request review with red CI.
5. Maintainer review within 7 days (14 for security-sensitive PRs).
6. Address comments by pushing new commits. Squash on merge.

## 9. Security-sensitive contributions

Any change touching SQLCipher key handling, authentication, the
brokerage-import path, or the IPC boundary between Electron main and
renderer is **security-sensitive**.

- Apply the `security-impact` label.
- Expect longer review and additional CI checks.
- Provide manual test evidence (screenshots/logs).
- Do not discuss exploitable details in the public PR. Move sensitive
  discussion to GitHub Private Vulnerability Reporting; see
  `SECURITY.md`.

## 10. AI-assisted contributions

We welcome AI-assisted contributions and we require disclosure. Our
policy follows the Apache Software Foundation's "Generated-by:"
guidance and Fedora's principle that the contributor is always the
author and is fully accountable.

**Disclose when:**
- An AI tool generated more than a single function or test.
- An AI tool generated documentation that you committed without
  rewriting.
- An autonomous agent (Codex, Cursor Agent, Claude Code, Copilot
  Workspace) opened the PR or wrote multiple files.

**No need to disclose** trivial autocomplete or single-line
suggestions.

**How to disclose:** Fill the "AI Assistance" section of the PR
template (tools used; scope; how you verified). Optionally add a
commit trailer: `Assisted-by: Claude Code`.

We treat `Co-Authored-By: Copilot` trailers as *informational only* —
the PR-body disclosure is authoritative. (This is in response to the
April–May 2026 VS Code default-change incident: Microsoft flipped the
default on April 16 and reversed it on May 3 after backlash.)

**We will reject PRs that:**
- Have an author who cannot explain a non-trivial section of their
  code.
- Fabricate dependencies.
- Delete or weaken tests rather than fix the code under test.
- Modify `AGENTS.md` to make the agent skip a failing test.

The bar is not "no AI." The bar is "you read every line, you understand
every line, and you take responsibility for every line."

## 11. Recognition

Every merged PR adds the contributor to `CONTRIBUTORS.md`. Sustained
contribution (≥3 merged PRs across ≥6 weeks) earns the
`regular-contributor` GitHub label and an invitation to the contributor
discussion channel. Three sustained regular contributors active for six
months triggers the governance evolution described in `GOVERNANCE.md`.

## 12. Governance & decision-making

Today: BDFL model. The maintainer makes final decisions. See
`GOVERNANCE.md` for the path to a steering committee.

---

By contributing you agree to license your contribution under the
project license (`LICENSE`) and to abide by `CODE_OF_CONDUCT.md`.
```

### 5.2 `SECURITY.md`

```markdown
# Security Policy

Zorivest handles real financial data. We take security reports
seriously and respond quickly.

## Scope

In scope:

- Anything that could expose, corrupt, or destroy a user's encrypted
  database without consent.
- Anything that lets a process other than the Zorivest UI read or
  modify portfolio data.
- Anything that bypasses the localhost-only API binding.
- Cryptographic weaknesses in key derivation, storage, or rotation.
- Supply-chain vulnerabilities in our dependencies that materially
  affect Zorivest as shipped.
- Anything in `packages/api/auth/`,
  `packages/infrastructure/crypto/`, or
  `packages/infrastructure/security/`.

Out of scope:

- Self-DoS (please file a regular bug report).
- Issues requiring root access on the user's machine.
- Theoretical weaknesses in unmodified upstream dependencies without
  demonstrated exploit.
- Bugs in optional integrations the user must manually enable, *unless*
  they allow escalation into the core app.

## How to report

**Use GitHub's Private Vulnerability Reporting.** Go to the
repository's Security tab → "Report a vulnerability". This creates a
private discussion between you and the maintainers and does not appear
in public issues until we publish an advisory.

If PVR is unavailable to you, email the maintainer at the address
listed in `CODE_OF_CONDUCT.md`.

Please include:

1. A clear description of the vulnerability.
2. Reproduction steps, including version, OS, configuration.
3. Impact assessment in your own words.
4. Suggested remediation if you have one (optional).

Please do not:

- File a public issue.
- Disclose publicly before we have published an advisory.
- Attempt exploitation against any system you do not own.

## Response timeline

| Stage | Target time |
|---|---|
| Acknowledge receipt | Within 72 hours |
| Initial severity assessment | Within 7 days |
| Patch or mitigation plan communicated | Within 30 days for high/critical |
| Public disclosure | Coordinated; default 90 days from initial report |

We will credit you in the advisory unless you ask us not to.

## Disclosure policy

We follow coordinated disclosure. Once a fix is released, we publish a
GitHub Security Advisory with a CVE, affected versions, and the fix.
Reporters are welcome to publish their own write-ups at or after our
advisory; we ask only that you not publish *before*.

## Security contribution guidelines

- For non-sensitive hardening (CI scans, dependency upgrades): open a
  regular PR with the `security-impact` label.
- For sensitive improvements (refactoring crypto code): open a Private
  Vulnerability Report describing the proposed change first.

## Out-of-band questions

For general security questions (e.g., "how does Zorivest store the
master key?"), open a GitHub Discussion in the Security category.
Opacity is not a defense.
```

### 5.3 `CODE_OF_CONDUCT.md` (Contributor Covenant 2.1 — adoption instructions)

The Contributor Covenant 2.1 is licensed under CC-BY 4.0 and is intended for verbatim adoption. Rather than re-publish the text in this design document, the Zorivest maintainer should:

1. Download the canonical Markdown file directly from `https://www.contributor-covenant.org/version/2/1/code_of_conduct/code_of_conduct.md` and commit it as `CODE_OF_CONDUCT.md` at the repository root.
2. In the **Enforcement** section, replace the `[INSERT CONTACT METHOD]` placeholder with the maintainer's preferred private contact channel. Recommended for Zorivest: `conduct@zorivest.io` (or, until that mailbox exists, the maintainer's personal email, ideally with a PGP key linked from the repo README).
3. Verify the attribution paragraph at the bottom links to `https://www.contributor-covenant.org/version/2/1/code_of_conduct.html` and credits Mozilla's enforcement ladder for the Community Impact Guidelines. The attribution paragraph must remain intact per the CC-BY 4.0 license.

Do not paraphrase or edit any other section. The version 2.1 text differs from earlier versions (which omit caste, color, and several other protected categories from the pledge), and verbatim adoption preserves the canonical interpretation and translations.

### 5.4 `GOVERNANCE.md`

```markdown
# Zorivest Governance

Zorivest is, today, a single-maintainer project. This document
describes how decisions are made now and the explicit, public
conditions under which that will change.

## Current model: Benevolent Dictator for Life (BDFL)

The maintainer has final authority on:

- Architectural direction.
- The contents of `docs/BUILD_PLAN.md` and the MEU sequence.
- PR acceptance and rejection.
- Release timing and versioning.
- Code of Conduct enforcement.
- Security advisory publication.

The maintainer commits to:

- Responding to PRs within 7 days (14 for security-sensitive).
- Public roadmap transparency — `docs/BUILD_PLAN.md` reflects current
  priorities; no parallel private roadmap exists.
- Acting in the project's long-term interest over short-term personal
  preference.
- Documenting *why* a non-trivial PR is rejected.

This model is appropriate for a single-FTE project. It is not
appropriate for a community-driven project. The next section defines
when we transition.

## Evolution trigger: when BDFL ends

The BDFL model ends and a Steering Committee is formed when **all** of
the following are true:

1. Three or more contributors (other than the maintainer) have each
   had at least 5 merged non-trivial PRs.
2. Those three contributors have sustained activity for at least six
   consecutive months (at least one merged PR per month per person).
3. No Code-of-Conduct incident has been adjudicated against any of
   them.

When the trigger fires, the maintainer commits to:

- Posting a public announcement within 30 days proposing a Steering
  Committee structure for community comment.
- Holding a 30-day comment period.
- Finalizing the structure as a `GOVERNANCE.md` revision and
  ratifying initial members within 90 days of the trigger.

Expected initial structure (subject to comment at the time):

- Five-person committee: the maintainer plus four members elected
  from regular contributors by approval voting.
- Final authority on architecture, MEU prioritization, contested PR
  decisions.
- The maintainer retains veto authority on security advisories for
  the first 12 months after the transition; this veto sunsets
  automatically.
- Decisions by simple majority; tie-breaker is the maintainer for
  the first 12 months.

This is modeled on Python's BDFL-to-steering-council path (Guido van
Rossum stepped down in July 2018; PEP 13 codified a five-member
steering council elected in January 2019) and Django's DEP 10
(adopted March 12, 2020, dissolving the "core team" in favor of a
Technical Board elected by Django Software Foundation Individual
Members), compressed into a single transition for a project at
Zorivest's scale.

## MEU prioritization

Until the trigger fires, the maintainer sets MEU priorities in
`docs/BUILD_PLAN.md`. Contributors can:

- Propose new MEUs by opening an issue with the `meu-proposal`
  label.
- Propose reprioritization by opening a discussion. Proposals with
  ≥5 reactions or ≥3 contributor comments receive a written response
  within 14 days.

## Contribution acceptance

Accepted when CI is green; at least one maintainer review approves;
the contributor has agreed to the project license; AI disclosure (if
applicable) is present.

Rejected when any of the above fails *and* the maintainer has
provided a written reason. Rejection is not personal; rejected PRs
can be revised and reopened.

## Roadmap transparency

- `docs/BUILD_PLAN.md` is authoritative.
- No private roadmap exists.
- The maintainer publishes a monthly status summary as a GitHub
  Discussion in "Announcements" once contributor activity warrants
  it.

## Trademark and brand

The project name "Zorivest" and any associated logo are reserved by
the maintainer until the project incorporates as a foundation or
transfers ownership. Forks are welcome under the project license;
commercial use of the name is not granted.

## Amendments

Today, amendments are made by the BDFL. After the trigger fires,
amendments require a two-thirds vote of the Steering Committee and a
two-week public comment period.
```

### 5.5 `.github/PULL_REQUEST_TEMPLATE.md`

```markdown
<!--
Thanks for contributing to Zorivest! Fill in the sections that apply.
Delete sections that don't. If you're using an AI agent to open this
PR, fill in the AI Assistance section. See CONTRIBUTING.md for the
full guide.
-->

## Summary

<!-- 1–3 sentences. What does this PR do and why? -->

## MEU / Issue link

<!--
e.g.:
- Implements MEU-127 (docs/build-plan/MEU-127-cost-basis-fifo.md)
- Fixes #234
-->

## Type of change

- [ ] Bug fix
- [ ] New feature (MEU implementation)
- [ ] Refactor / internal-only change
- [ ] Documentation
- [ ] Test addition or improvement
- [ ] Build / CI / tooling
- [ ] Security improvement (also check Security Impact below)

## Changes

<!-- Bullet list. Be specific. -->
-

## Testing

<!-- TDD is mandatory. Show tests were written first. -->

- [ ] Tests were written before implementation
- [ ] Tests cover happy path and at least one failure mode
- [ ] `make check` passes locally
- [ ] For financial math: includes Hypothesis property tests
- [ ] No existing tests were weakened or deleted (or, if so,
      justified in a separate paragraph)

**How to verify manually (for reviewers):**

<!-- One or two commands a reviewer can run. -->

## Screenshots / output

<!-- For UI or visible behavior changes. Delete otherwise. -->

## Security impact

- [ ] This PR touches `packages/infrastructure/crypto/`,
      `packages/infrastructure/security/`, `packages/api/auth/`, or
      SQLCipher key handling.
- [ ] If checked above, the `security-impact` label is applied.
- [ ] No secrets, keys, or production credentials are added.
- [ ] No new third-party network calls are introduced. (If a new
      brokerage-import integration is added, list the network
      endpoint below.)
- [ ] No localhost-binding constraints are loosened
      (`uvicorn` binds `127.0.0.1` only).
- [ ] Dependency lockfiles are updated and audited (`pip-audit`,
      `pnpm audit`).

## AI assistance

<!--
Required if you used AI tools for more than trivial autocomplete.
See CONTRIBUTING.md §10. If you did not use AI tools, write "None."
-->

- **Tools used:**
- **Scope of AI contribution:**
- **My verification:**

## Architecture & dependency rule

- [ ] No file in `packages/core/` imports from
      `packages/infrastructure/` or `packages/api/`.
- [ ] No file in `packages/application/` imports from
      `packages/infrastructure/`.
- [ ] If a new port (abstract class) is added in core, the
      corresponding adapter is in infrastructure.

## Documentation

- [ ] `AGENTS.md` updated if commands or constraints changed.
- [ ] `docs/ARCHITECTURE.md` updated if module boundaries changed.
- [ ] `CONTRIBUTING.md` updated if process changed.
- [ ] Inline docstrings / JSDoc updated.

## Final author checklist

- [ ] I have read every line of this diff.
- [ ] I can explain every non-trivial block.
- [ ] I have read `CONTRIBUTING.md`.
- [ ] I agree to license my contribution under the project license.
```

### 5.6 `docs/DEVELOPMENT.md`

```markdown
# Zorivest Development Guide

This is the long-form companion to `AGENTS.md` (which is terser and
targeted at AI coding agents). If you are a human setting up the
project for the first time, start here.

## 1. Prerequisites

| Tool | Version | Notes |
|---|---|---|
| Python | 3.12+ | pyenv on macOS/Linux; official installer or winget on Windows. |
| Node.js | 22 LTS+ | Volta or nvm. |
| `uv` | latest (≥0.5) | Astral's Python package manager: `curl -LsSf https://astral.sh/uv/install.sh \| sh`. |
| `pnpm` | 9+ | `corepack enable pnpm`. |
| SQLCipher | 4.5+ | macOS: `brew install sqlcipher`. Linux: `apt install libsqlcipher-dev`. Windows: see §3.3. |
| OpenSSL | 3.0+ on Linux | Required by SQLCipher. macOS via brew; Windows: see §3.3. |
| Git | modern | On Windows, enable symlinks: `git config --global core.symlinks true`. |
| Make | any | Optional but recommended. |

## 2. First-time setup

\`\`\`bash
git clone https://github.com/matbanik/zorivest.git
cd zorivest

uv sync                                  # Python workspaces
pnpm install                             # TypeScript workspaces
uv run python tools/init_dev_db.py       # Throwaway-key dev DB

make check                               # Run the full local gate
\`\`\`

`make check` runs lint, type checks, tests, anti-placeholder scan, and
dependency-rule scan — the same gates CI runs.

## 3. Running the components

### 3.1 Backend API

FastAPI in `packages/api/`. Binds to `127.0.0.1:8731`. Never exposed
externally — enforced in code.

\`\`\`bash
uv run uvicorn packages.api.app:app --reload --host 127.0.0.1 --port 8731
\`\`\`

OpenAPI docs at `http://127.0.0.1:8731/docs`.

### 3.2 Electron UI

\`\`\`bash
pnpm --filter ui dev
\`\`\`

Vite dev mode + Electron main process. UI talks to API on the default
localhost URL.

### 3.3 SQLCipher and the encrypted database

DB file: `~/.zorivest/zorivest.db` (or `%APPDATA%/Zorivest/zorivest.db`
on Windows). In dev: `./dev.db` with key `dev-key-not-secret`.

**On Windows:** SQLCipher with OpenSSL has historically been the
biggest install pain point for Electron projects. Two options:

1. **Recommended:** use the prebuilt `@journeyapps/sqlcipher` binary.
   It bundles SQLCipher 4.4.2 (based on SQLite 3.33.0) and OpenSSL
   1.1.1i on Windows / 1.1.1l on macOS; on Linux it dynamically links
   against the system OpenSSL. Supported on Node 10+ and Electron 6+.
2. If you need to build from source: install OpenSSL via vcpkg
   (`vcpkg install openssl:x64-windows-static`), then `pnpm rebuild`.

For Python, SQLCipher is accessed via `sqlcipher3`, which requires the
system SQLCipher library. On Linux, install `libsqlcipher-dev` before
`uv sync`.

### 3.4 MCP server

\`\`\`bash
pnpm --filter mcp-server dev
\`\`\`

The Model Context Protocol server exposes a read-only view of
portfolio data to AI agents. **The MCP server never has write access
to the encrypted database.**

## 4. Testing

\`\`\`bash
uv run pytest packages/                   # All Python tests
uv run pytest packages/core/              # One package
uv run pytest packages/core/tests/test_cost_basis.py::test_fifo_simple
pnpm -r test                              # All TypeScript tests
pnpm --filter ui test                     # One workspace
uv run pytest --cov=packages --cov-report=html
\`\`\`

Hypothesis property tests live alongside unit tests, identified by
`@given`. Run them with extended examples locally for financial-math
PRs:

\`\`\`bash
HYPOTHESIS_PROFILE=ci uv run pytest packages/core/tests/test_fifo.py
\`\`\`

## 5. Type checks and linters

\`\`\`bash
uv run mypy --strict packages/
uv run ruff check && uv run ruff format --check
pnpm -r typecheck
pnpm -r lint
\`\`\`

`make check` runs all of these in order and fails fast.

## 6. The architectural dependency rule

\`\`\`
        ┌──────────────────┐
        │       UI         │  ui/  (TypeScript, Electron + React)
        └────────┬─────────┘
                 │ HTTP / IPC
        ┌────────▼─────────┐
        │       API        │  packages/api/  (FastAPI)
        └────────┬─────────┘
                 │ calls
        ┌────────▼─────────┐
        │   Application    │  packages/application/  (use cases)
        └────────┬─────────┘
                 │ uses ports defined in
        ┌────────▼─────────┐         ┌────────────────────────┐
        │      Core        │◄────────│   Infrastructure       │
        │ (Domain + ports) │ adapts  │ (SQLAlchemy, SQLCipher,│
        └──────────────────┘         │   repositories)        │
                                     └────────────────────────┘
\`\`\`

In plain English: **Core (and Application) define interfaces.
Infrastructure implements them. Code never flows the other way.**

In CI: `python tools/validate_codebase.py --dependency-rule`.

In Cursor: a glob-scoped rule at `.cursor/rules/dependency-rule.mdc`
warns you in real time when editing a file under `packages/core/`.

## 7. The .agent directory

`.agent/` contains AI-agent instructions: roles, workflows, skills.
These are read by Codex, Claude Code, Cursor, etc. — typically routed
via `AGENTS.md` at the root. As a human, you do not need to read
these unless you're contributing improvements to the agent
infrastructure itself.

Entry points:

- `.agent/AGENTS.md` — top of the agent instruction tree.
- `.agent/roles/coder.md`, `tester.md`, `reviewer.md` — role
  definitions.
- `.agent/workflows/tdd-implementation.md` — the canonical TDD
  workflow.
- `.agent/skills/git-workflow.md` — git conventions in a form agents
  can execute.

If you change a CI command, update `AGENTS.md` so agents stay
aligned. The `validate_agent_files.py` check in CI catches drift.

## 8. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `sqlcipher3` import error | System SQLCipher missing | Install `libsqlcipher-dev` / `brew install sqlcipher`. |
| `electron-rebuild` fails on Windows | OpenSSL not found | Install via vcpkg or use the prebuilt binary. |
| Tests pass locally but CI fails on placeholder scan | TODO/FIXME left in code | Remove or move to an issue. |
| Type check fails after `uv sync` | Cached mypy data | `rm -rf .mypy_cache`. |
| Cursor doesn't pick up rules | Cursor version old | Update to v0.45+; check `.cursor/rules/*.mdc`. |

## 9. Getting unstuck

- `docs/ARCHITECTURE.md` — the deep dive.
- GitHub Discussions — "Development help" category.
- Agent-related questions: tag the discussion `agent-tooling`.
```

---

## 6. Implementation Roadmap

### Phase P0 — ship before the first external contributor (week 1)

These exist so a contributor showing up tomorrow has a coherent on-ramp.

- `README.md` updated with link to CONTRIBUTING.md
- `CONTRIBUTING.md` (§5.1)
- `CODE_OF_CONDUCT.md` — Contributor Covenant 2.1 copied verbatim from `contributor-covenant.org/version/2/1/code_of_conduct/code_of_conduct.md` with the contact slot filled in (§5.3)
- `SECURITY.md` (§5.2)
- `AGENTS.md` (root only, ≤200 lines per Augment Code's findings)
- `.github/PULL_REQUEST_TEMPLATE.md` (§5.5)
- `.github/ISSUE_TEMPLATE/bug_report.yml`, `feature_request.yml`, `config.yml` (disable blank, point security to PVR)
- `docs/DEVELOPMENT.md` (§5.6)
- Enable GitHub Private Vulnerability Reporting in repo settings
- CI: type check + lint + test + anti-placeholder scan + dependency-rule scan on every PR

### Phase P1 — within 30 days

- `GOVERNANCE.md` (§5.4)
- `docs/AI_POLICY.md` (long form of CONTRIBUTING §10; following the Will McGugan precedent of keeping a separate file)
- `docs/ARCHITECTURE.md`
- `CLAUDE.md` (`@AGENTS.md` import + Claude-specific notes)
- `GEMINI.md` and `.windsurfrules` as committed symlinks
- Per-package `AGENTS.md` in each `packages/*`, `ui/`, `mcp-server/`
- Issue template: `docs_improvement.yml`
- CI: AI-disclosure check and `ai-assisted` labeling action

### Phase P2 — within 90 days

- `.github/copilot-instructions.md` (native, with `applyTo:` per-language)
- `.cursor/rules/dependency-rule.mdc` (glob-scoped to `packages/core/**/*.py`)
- `.cursor/rules/tdd-policy.mdc` (glob-scoped to `tests/**/*.py`)
- `tools/validate_agent_files.py` (AGENTS.md drift detection)
- Issue template: `agent_issue.yml`
- Security CI: gitleaks + bandit + semgrep on `security-impact` PRs
- CODEOWNERS file for security-sensitive paths
- `CONTRIBUTORS.md` automation (all-contributors bot)

### Benchmarks that change the roadmap

| If this happens | Do this |
|---|---|
| ≥10 PRs/month sustained for 2 months | Promote P2 items; consider a code-review co-maintainer. |
| 3 sustained regular contributors at 6 months | Fire the GOVERNANCE.md trigger; begin steering-committee discussion. |
| AI-generated PRs >30% of merged PRs | Re-evaluate AI policy strictness; possibly require linked chat exports (the Ghostty pattern). |
| First security advisory published | Run a post-incident retrospective; update SECURITY.md SLA targets. |
| Repo hits 1k stars and a docs site exists | Reconsider `llms.txt` adoption. |

---

## 7. Caveats

- **The CONTRIBUTING.md draft assumes maximalist AI disclosure.** A more permissive stance — disclosure only when an autonomous agent opens the PR — is defensible and reduces friction; pick based on review-bandwidth reality. Ghostty's escalation in January 2026 to "drive-by AI PRs will be closed without question" represents the strict end of the spectrum and was driven by maintainer-bandwidth pressure.
- **`tools/validate_codebase.py` capabilities** (dependency-rule scan, AGENTS.md drift check, anti-placeholder scan) are referenced as if they exist. They are listed in the project context as planned validation. If any are not yet implemented, treat them as P0 implementation work rather than already-shipped gates.
- **The "three contributors at six months" governance trigger is one defensible number, not the only one.** Some projects use "one co-maintainer with commit rights" as a softer earlier trigger; others use "five contributors at twelve months" as a harder later one. Revisit once there is contributor activity to extrapolate from.
- **Heuristic AI-code detection is unreliable on short snippets.** Vendors report 95%+ accuracy on long blocks but Overchat and Pangram both document significant accuracy drops on short snippets and on less-represented languages. Use `ai-suspected` as a soft signal, never as a basis for rejection.
- **The Contributor Covenant 2.1 is released under CC-BY 4.0.** Verbatim adoption is the intended use, but the attribution paragraph must remain intact. Do not edit, paraphrase, or remove the attribution line.
- **Symlinks for GEMINI.md / `.windsurfrules` require `core.symlinks=true` on Windows.** Some Windows contributors will otherwise see plain-text files containing the path string instead of the file content. Documented in DEVELOPMENT.md §3.3. If Windows contributors become numerous, switch to `@import`-style redirect files.
- **llms.txt may become more relevant quickly.** The spec was proposed by Jeremy Howard on September 3, 2024 and is on a steep adoption curve in the docs-platform space. If a publicly hosted Zorivest docs site appears, revisit within 90 days. Today, SE Ranking's 300,000-domain analysis concluded that "LLMs.txt doesn't impact how AI systems see or cite your content today" — but the IDE-agent angle (Cursor/Continue/Cline do read it) may still justify adoption when there is content to point at.
- **The 60,000-repo AGENTS.md adoption count comes from the agents.md website itself** and is therefore not third-party-audited; treat as directional rather than precise. The agents.md count grew from "20,000+ repositories" cited by InfoQ in August 2025 to "60,000+" cited on the agents.md site by late 2025, suggesting fast continuing adoption.
- **Augment Code's 100–150-line AGENTS.md sweet-spot finding** is a single-vendor study; replicate locally with your own tooling if precise sizing matters. The directional conclusion (length discipline matters; >200 lines hurts performance) is consistent across multiple sources including Ona, Factory.ai, and the agents.md spec itself.
