# Composite Synthesis: Contribution Documentation Research

> **Sources**: Gemini Deep Research (445 lines, 50+ repo survey), ChatGPT Deep Research (424 lines, friction analysis + checklists), Claude Deep Research (964 lines, architecture + draft templates)
>
> **Date**: 2026-05-14
>
> **Purpose**: Unified action plan for building Zorivest's contribution documentation suite

---

## 1. Executive Consensus

All three research providers independently converged on these conclusions:

### 1.1 Universal Truths (All 3 Agree)

| Finding | Gemini | ChatGPT | Claude |
|:--------|:------:|:-------:|:------:|
| CONTRIBUTING.md is the #1 file that reduces PR rejection | ✅ | ✅ | ✅ |
| SECURITY.md is **critical** for financial-domain projects | ✅ | ✅ | ✅ |
| AI-generated contributions need mandatory disclosure | ✅ | ✅ | ✅ |
| AGENTS.md should be canonical; per-tool files are redirects | ✅ | — | ✅ |
| PR templates reduce reviewer burden more than any other automation | ✅ | ✅ | ✅ |
| TDD policy is a competitive differentiator for contribution quality | — | ✅ | ✅ |
| Monorepos need "hub and spoke" docs, not one monolithic file | ✅ | ✅ | ✅ |
| `llms.txt` is premature for Zorivest (no public docs site) | ✅ | — | ✅ |
| CODE_OF_CONDUCT should use Contributor Covenant 2.1 verbatim | ✅ | — | ✅ |
| BDFL governance is honest; document evolution path explicitly | — | — | ✅ |

### 1.2 Top 5 Surprising Findings

1. **AGENTS.md length has a sweet spot of 100–150 lines** — beyond 200 lines, performance *reverses* (Claude, citing Augment Code study). This is counterintuitive given Zorivest's existing `.agent/AGENTS.md` is extensive.

2. **~50% of Ghostty PRs self-disclosed AI use** after the January 2026 policy change (Claude). Mandatory disclosure doesn't kill contributions — it normalizes them.

3. **Only ~30% of occasional contributors make more than one PR** (ChatGPT, citing Count.co benchmarks). The "contribution cliff" is the #1 retention problem, not onboarding.

4. **Django is the only major framework with mandatory AI disclosure in its PR template** (Gemini). Most projects are still figuring this out — Zorivest can lead here.

5. **Heuristic AI-code detection is unreliable on short snippets** — Overchat reports ~85-90% accuracy on <20 lines; Pangram misses ~20% of AI code (Claude). Self-disclosure is the only reliable mechanism.

---

## 2. File Inventory: Unified Decision Matrix

Synthesized from all three reports into a single prioritized inventory:

### P0 — Ship Before First External Contributor

| File | Purpose | Primary Source | Length |
|:-----|:--------|:---------------|:-------|
| `CONTRIBUTING.md` | Human contribution guide — values, process, TDD policy, AI disclosure | Claude draft (§5.1) — most complete | ~390 lines |
| `SECURITY.md` | Vulnerability scope, GitHub PVR reporting, response SLAs | Claude draft (§5.2) + ChatGPT SECURITY.md analysis | ~85 lines |
| `CODE_OF_CONDUCT.md` | Contributor Covenant 2.1 verbatim | Claude instructions (§5.3) | Standard |
| `AGENTS.md` (root) | Machine-actionable build/test/verify; ≤200 lines | Claude (§3.3) — follows Augment Code sizing guidance | ≤200 lines |
| `docs/DEVELOPMENT.md` | Full dev setup: Python + Node + SQLCipher | Claude draft (§5.6) — includes troubleshooting table | ~200 lines |
| `.github/PULL_REQUEST_TEMPLATE.md` | Unified template: AI disclosure, security checklist, TDD evidence, MEU link | Claude draft (§5.5) — most comprehensive | ~100 lines |
| `.github/ISSUE_TEMPLATE/bug_report.yml` | Structured bug report form | All three agree | Short |
| `.github/ISSUE_TEMPLATE/feature_request.yml` | Structured feature request form | All three agree | Short |
| `.github/ISSUE_TEMPLATE/config.yml` | Disable blank issues; redirect security to PVR | Claude | Trivial |

### P1 — Within 30 Days

| File | Purpose | Primary Source | Length |
|:-----|:--------|:---------------|:-------|
| `GOVERNANCE.md` | BDFL today, documented evolution trigger | Claude draft (§5.4) | ~110 lines |
| `docs/AI_POLICY.md` | Long-form AI assistance policy | Claude (§2.1) + ChatGPT AI-disclosure analysis | ~150 lines |
| `docs/ARCHITECTURE.md` | Dependency rule, layer boundaries, MEU concept | Gemini ("Architecture Map" is high-value at <40%) | ~200 lines |
| `CLAUDE.md` | Thin redirect: `@AGENTS.md` + Claude-specific notes | Claude (§3.3) | ≤10 lines |
| `GEMINI.md`, `.windsurfrules` | Symlinks to `AGENTS.md` | Claude (§3.3) | Trivial |
| Per-package `AGENTS.md` (×5) | Package-scoped AI rules (core, infra, api, ui, mcp) | Claude (§2.4) — follows openai/codex nested pattern | ≤60 lines each |
| `.github/ISSUE_TEMPLATE/docs_improvement.yml` | Docs improvement form | Claude | Short |

### P2 — Within 90 Days

| File | Purpose | Primary Source | Length |
|:-----|:--------|:---------------|:-------|
| `.github/copilot-instructions.md` | Native Copilot rules with `applyTo:` | Claude (§3.1 — VS Code survey) | ~50 lines |
| `.cursor/rules/dependency-rule.mdc` | Glob-scoped: `packages/core/**/*.py` no-infra-imports | Claude (§3.1 — Supabase survey) | ≤30 lines |
| `.cursor/rules/tdd-policy.mdc` | Glob-scoped: `tests/**/*.py` immutability rule | Claude | ≤30 lines |
| `CODEOWNERS` | Auto-assign security reviewers for sensitive paths | ChatGPT + Claude | Short |
| `.github/ISSUE_TEMPLATE/agent_issue.yml` | "AGENTS.md told my AI the wrong thing" feedback | Claude (novel) | Short |
| `tools/validate_agent_files.py` | AGENTS.md drift detection, redirect integrity | Claude (§3.4) | N/A |
| `CONTRIBUTORS.md` + all-contributors bot | Recognition automation | Claude (§5.1 §11) | Automated |

---

## 3. PR Friction: The Top 10 Rejection Reasons

Ranked by frequency across ChatGPT's evidence-based analysis, with Zorivest-specific mitigations synthesized from all three reports:

| # | Rejection Reason | Mitigation | File(s) |
|:--|:-----------------|:-----------|:--------|
| 1 | **Style/quality violations** | Document ruff + ESLint + Prettier; `make check` command | CONTRIBUTING §6, DEVELOPMENT §5 |
| 2 | **Insufficient/failing tests** | TDD mandate: tests first, tests immutable | CONTRIBUTING §7, PR template |
| 3 | **Poor PR description** | PR template with mandatory sections | PR_TEMPLATE.md |
| 4 | **Out-of-scope contributions** | MEU model with `meu/available` labels; BUILD_PLAN.md link | CONTRIBUTING §5 |
| 5 | **Duplicate/stale work** | "Search issues first" instruction; rebase requirement | CONTRIBUTING §8 |
| 6 | **No prior discussion** | "Issue-first for large changes" policy | CONTRIBUTING §4 |
| 7 | **Oversized PRs** | "One logical change per PR" guideline | CONTRIBUTING §8 |
| 8 | **License/CLA issues** | License agreement in PR template footer | CONTRIBUTING §12, PR template |
| 9 | **Unresolved feedback** | "Respond within 7 days or PR is stale" policy | CONTRIBUTING §8 |
| 10 | **Missing documentation** | Checklist item: "Updated AGENTS.md if commands changed" | PR template |

---

## 4. Security Architecture

### 4.1 Consensus Security Stack

All three reports converge on a layered security model:

```
┌─────────────────────────────────────────────┐
│  Layer 1: SECURITY.md (Scope + Reporting)   │  ← P0
├─────────────────────────────────────────────┤
│  Layer 2: PR Template Security Checklist    │  ← P0
├─────────────────────────────────────────────┤
│  Layer 3: CODEOWNERS for sensitive paths    │  ← P2
├─────────────────────────────────────────────┤
│  Layer 4: CI Security Scans (gitleaks,      │
│           bandit, semgrep, pip-audit)       │  ← P2
├─────────────────────────────────────────────┤
│  Layer 5: 24-hour cooldown on security PRs  │  ← P2
└─────────────────────────────────────────────┘
```

### 4.2 SECURITY.md: Best-in-Class Elements

From ChatGPT's analysis of 10+ real SECURITY.md files:

| Element | Source Example | Included in Claude Draft? |
|:--------|:--------------|:------------------------:|
| Supported versions | Actual Budget, Firefly III | ❌ (add) |
| Private reporting channel | All; GitHub PVR preferred | ✅ |
| Required information checklist | Rust-finance (description, steps, impact, fix) | ✅ |
| Response SLA table | Filo Sottile (1 week), Rust-finance (48h/5d/30d) | ✅ |
| CVE handling | Firefly III (MITRE coordination) | ✅ |
| No bounty statement | age ("I do not offer bug bounties") | ❌ (add) |
| In-scope / out-of-scope | Rust-finance, OpenSSL | ✅ |
| Confidentiality reminder | Actual Budget | ✅ |

**Action**: Enhance Claude's SECURITY.md draft with supported-versions table and explicit no-bounty statement.

---

## 5. AI Contribution Strategy

### 5.1 The Dual-Document Architecture

Claude's core insight, validated by Gemini's survey:

```
CONTRIBUTING.md                    AGENTS.md
(Human values & process)           (Machine commands & constraints)
┌────────────────────┐             ┌────────────────────┐
│ § Vision & values  │             │ § Build commands    │
│ § TDD mandate      │◄───────────►│ § Test commands     │
│ § AI disclosure    │  cross-ref  │ § Dependency rule   │
│ § PR process       │  (one each) │ § Architecture      │
│ § Security policy  │             │ § Per-package refs   │
└────────────────────┘             └────────────────────┘
         │                                   │
         ▼                                   ▼
   Humans read this               AI agents read this
   first, then AGENTS.md          first, then CONTRIBUTING
   for details                    for context
```

### 5.2 Per-Tool File Strategy

Claude's survey of 5 projects produced the definitive answer:

| Tool | File | Strategy | Justification |
|:-----|:-----|:---------|:-------------|
| Claude Code | `CLAUDE.md` | **Redirect** (`@AGENTS.md`) | No unique capabilities over AGENTS.md |
| Gemini CLI | `GEMINI.md` | **Symlink** to `AGENTS.md` | No unique capabilities |
| Windsurf | `.windsurfrules` | **Symlink** to `AGENTS.md` | No unique capabilities |
| GitHub Copilot | `.github/copilot-instructions.md` | **Native** (~50 lines) | Unique: `applyTo:` filters, `tools:` arrays, custom agents |
| Cursor | `.cursor/rules/*.mdc` | **Native** (2 files, ≤30 lines each) | Unique: `globs:` scoping for dependency-rule enforcement |

### 5.3 Preventing "Plausible but Wrong" AI Code

Claude's 5-layer prevention model, augmented by ChatGPT's security addendum:

| Layer | Gate | Catches | Provider |
|:------|:-----|:--------|:---------|
| 1. TDD immutability | Tests are specs; can't be modified to pass | AI deleting/weakening tests | Claude |
| 2. Anti-placeholder scan | Rejects `TODO`, `FIXME`, `NotImplementedError` | Vibe-coded stubs | Claude, ChatGPT |
| 3. Dependency-rule scan | Parses imports in `packages/core/` | Architecture violations | Claude |
| 4. Anti-fabrication checks | `pip-audit`/`pnpm audit` + lockfile diff | Hallucinated package names | Claude |
| 5. AI-disclosure tagging | Commit trailers + PR body scanning | Undisclosed AI use | Claude, Gemini |

---

## 6. Contributor Retention: Bridging the Cliff

ChatGPT's unique contribution — the "contribution cliff" analysis:

### 6.1 The Problem
- Only ~30% of first-time contributors make a second contribution
- "Good first issue" to "regular contributor" is the biggest drop-off

### 6.2 Zorivest-Specific Solution: MEU Progression

| Stage | Label | Task Type | Support |
|:------|:------|:----------|:--------|
| **First contribution** | `meu/good-first-issue` | Documentation, test additions | Pre-written acceptance tests; bounded scope |
| **Second contribution** | `meu/good-second-issue` | Small bug fix, minor refactor | Mentorship via PR review comments |
| **Regular contributor** | `meu/available` | Full MEU implementation | Architecture context in DEVELOPMENT.md |
| **Sustained contributor** | `regular-contributor` label | Architecture proposals, RFC discussions | Governance participation rights |

### 6.3 Recognition Pipeline (Claude)
- Every merged PR → added to `CONTRIBUTORS.md`
- ≥3 merged PRs across ≥6 weeks → `regular-contributor` label + discussion channel invite
- 3 sustained contributors at 6 months → governance evolution trigger fires

---

## 7. Maturity Model

Gemini's 4-level model, enhanced with Claude's file inventory:

| Level | Name | Files | Zorivest Target |
|:------|:-----|:------|:----------------|
| **1 — Minimal** | README only | README, LICENSE | ❌ Past this |
| **2 — Standard** | Basic contribution guide | + CONTRIBUTING, CODE_OF_CONDUCT, issue templates | ❌ Past this |
| **3 — Comprehensive** | Security + CI docs + PR templates | + SECURITY, PR template, GOVERNANCE, CI docs | ✅ **P0 target** |
| **4 — Enterprise/Hybrid** | AI-native, monorepo-aware, per-tool files | + AGENTS.md hierarchy, per-package docs, DevContainer, AI detection | ✅ **P1-P2 target** |

---

## 8. CONTRIBUTING.md Structure: Unified Outline

Merging Gemini's chronological onboarding model with ChatGPT's friction-reduction priorities and Claude's draft:

| # | Section | Source | Purpose |
|:--|:--------|:-------|:--------|
| 1 | Vision & values | Claude §1 | 3 principles: correctness > speed; locality + encryption; architecture as guardrail |
| 2 | Quick start (5 min) | Claude §2, Gemini | `git clone` → `uv sync && pytest` → `pnpm install && test` |
| 3 | Development environment | Claude §3 → DEVELOPMENT.md link | Avoid overwhelming CONTRIBUTING; hub-and-spoke to DEVELOPMENT.md |
| 4 | Types of contributions | Claude §4 | Bug reports, docs, tests, bug fixes, features, MEUs, security |
| 5 | MEU model & where to start | Claude §5, ChatGPT cliff analysis | Good-first-issue → good-second-issue → regular contributor |
| 6 | Code style | Claude §6, ChatGPT style-guide friction | ruff, mypy strict, ESLint, Prettier; dependency rule |
| 7 | Testing policy (TDD mandatory) | Claude §7, ChatGPT #2 rejection | Tests first, tests immutable, property tests for financial math |
| 8 | Pull request process | Claude §8, ChatGPT PR-rejection top 10 | Fork → branch → `make check` → PR template → CI green → review |
| 9 | Security-sensitive contributions | Claude §9, ChatGPT security guardrails | `security-impact` label, extra CI, no public exploit details |
| 10 | AI-assisted contributions | Claude §10, Gemini AI-disclosure survey | Disclose when, how, rejection criteria; "you own every line" |
| 11 | Recognition | Claude §11, ChatGPT retention | CONTRIBUTORS.md, regular-contributor label, governance rights |
| 12 | Governance | Claude §12 → GOVERNANCE.md link | BDFL today; evolution trigger |

---

## 9. Actionable Checklists (from ChatGPT)

### 9.1 Contributor Friction Scorecard

Rate 1-5 on each dimension. Target: 4+ across all after P0 phase.

| Dimension | Score Target | File That Addresses It |
|:----------|:------------|:----------------------|
| Clarity of project scope | 4-5 | README, BUILD_PLAN.md |
| Issue guidance (easy tasks findable) | 4-5 | Issue labels, CONTRIBUTING §5 |
| Onboarding instructions | 4-5 | DEVELOPMENT.md |
| Contribution workflow | 4-5 | CONTRIBUTING §8 |
| Coding standards | 4-5 | CONTRIBUTING §6 |
| Testing requirements | 4-5 | CONTRIBUTING §7 |
| Communication channels | 3-4 | GitHub Discussions |
| Review expectations | 4-5 | CONTRIBUTING §8, GOVERNANCE |
| Release process | 3-4 | CONTRIBUTING (brief mention) |
| Security guidance | 4-5 | SECURITY.md, CONTRIBUTING §9 |

### 9.2 Security PR Review Addendum

For PRs touching auth, encryption, financial calculations, or IPC boundary:

- [ ] Threat analysis: does the change introduce new vectors?
- [ ] Input validation: all inputs validated/sanitized?
- [ ] Auth/authz: permissions enforced on new endpoints?
- [ ] Encryption: no hardcoded keys, correct algorithms (AES-256, not MD5)?
- [ ] SQL safety: parameterized queries only, no raw SQL concatenation?
- [ ] Error handling: no sensitive data in error messages/logs?
- [ ] Logging: no passwords/tokens/account data logged?
- [ ] Dependency audit: new security libraries vetted?
- [ ] Static analysis: Bandit + ESLint-security pass?
- [ ] Compliance: no plaintext financial data at rest?
- [ ] IPC boundary: Electron main↔renderer channel validated?
- [ ] Localhost binding: `127.0.0.1` constraint not loosened?

### 9.3 First-Time Contributor Onboarding Checklist

1. Read README and CONTRIBUTING.md
2. Find a `meu/good-first-issue` or `help-wanted` issue
3. Ask questions early (comment on issue or open Discussion)
4. Fork, clone, `uv sync && pnpm install`, run `make check`
5. Create branch (`fix/issue-123` or `feat/your-feature`)
6. Write tests first (TDD), then implement
7. Run `make check` locally — fix all failures
8. Push and open PR using template; fill every applicable section
9. Respond to review comments promptly
10. Once merged, check CONTRIBUTORS.md — celebrate 🎉

---

## 10. Unique-to-Provider Insights

### From Gemini Only

- **AI "slop" is now a named anti-pattern** — maintainers actively complain about it on HN/Reddit. Contributors who submit AI-generated code without understanding the logic shift the cognitive burden onto the maintainer.
- **CCXT's transpilation guard** — a cautionary tale where editing generated files (instead of the source) causes immediate rejection. Relevant for any code-generation pipelines in Zorivest.
- **60,000+ repos** now use AGENTS.md format (per agents.md website, directional not audited).
- **DevContainer** is <30% prevalent but extremely high-value for SQLCipher cross-platform setup.

### From ChatGPT Only

- **PR acceptance rates measurably improve** with contribution docs, though hard numbers are scarce — "projects with thorough newcomer docs often see first-timer PRs landed within days."
- **Reviewer time per PR drops significantly** when CI checks are documented — eliminates "stop and explain" cycles.
- **"Lazy consensus"** model (from Feast project) — if a contributor has an idea, they can open a draft PR and work forward without lengthy sign-off. Useful for small features.
- **Dependency update policy** should be explicitly documented — how Dependabot/Renovate works, batching strategy, human vs bot PRs.
- **Drive-by refactoring** prevention requires explicit policy: separate PRs for refactors, backwards compatibility mandate, incremental approach.

### From Claude Only

- **Augment Code's 100-150 line AGENTS.md sweet spot** — data-backed sizing guidance.
- **openai/codex's nested AGENTS.md pattern** — per-crate files, closest-file-wins, optional `AGENTS.override.md`.
- **trigger.dev's `@import` pattern** for CLAUDE.md — keeps Claude-specific while pulling in shared AGENTS.md content.
- **Supabase's `.cursor/rules/*.mdc` with YAML frontmatter** — `globs:` and `alwaysApply:` for directory-scoped rules.
- **VS Code Copilot `git.addAICoAuthor` controversy** (April–May 2026) — Microsoft flipped defaults, then reversed. Zorivest should treat trailers as informational, not authoritative.
- **Two-stage AI detection**: Stage 1 (self-disclosure, authoritative) + Stage 2 (heuristic, signal only). Never use heuristic detection as basis for rejection.
- **24-hour cooldown** on security-impact PRs via bot label — prevents rushed merges.
- **AGENTS.md drift check in CI** — validates file doesn't exceed 200 lines, redirect stubs resolve, native files don't duplicate.

---

## 11. Template Sources: Best Exemplars

| File | Best Exemplar(s) | What to Emulate |
|:-----|:-----------------|:----------------|
| CONTRIBUTING.md | **Rust-lang/rust** (overall quality), **Claude draft §5.1** (Zorivest-specific) | TDD mandate, AI disclosure, MEU progression |
| SECURITY.md | **Firefly III** (financial domain), **Filo Sottile/age** (concise + timelines) | Scope definition, PVR, CVE handling, no-bounty statement |
| PR Template | **Django** (AI disclosure checkbox), **Claude draft §5.5** (comprehensive) | AI section, security checklist, TDD evidence, dependency rule |
| AGENTS.md | **openai/codex** (nested pattern), **agents.md spec** (format) | ≤200 lines root, per-package nested, closest-file-wins |
| GOVERNANCE.md | **Python PEP 13** (BDFL→council), **Django DEP 10** (team evolution) | Honest BDFL, measurable trigger, time-boxed transition |
| DEVELOPMENT.md | **n8n-io/n8n** (hybrid monorepo setup), **Claude draft §5.6** | Troubleshooting table, Windows SQLCipher guidance |
| `.cursor/rules/` | **supabase/supabase** (glob-scoped rules) | YAML frontmatter with `globs:` for layered architecture |
| Copilot instructions | **microsoft/vscode** (native with `applyTo:`) | Custom agent definitions, per-language routing |

---

## 12. Implementation Roadmap

### Week 1: P0 (Before First External Contributor)

```
 1. Enable GitHub Private Vulnerability Reporting in repo settings
 2. Create SECURITY.md (from Claude draft + ChatGPT enhancements)
 3. Create .github/PULL_REQUEST_TEMPLATE.md (from Claude draft)
 4. Create .github/ISSUE_TEMPLATE/ (bug_report.yml, feature_request.yml, config.yml)
 5. Create CODE_OF_CONDUCT.md (Contributor Covenant 2.1 verbatim)
 6. Create docs/DEVELOPMENT.md (from Claude draft)
 7. Create root AGENTS.md (≤200 lines, global workspace rules)
 8. Create CONTRIBUTING.md (from Claude draft + this synthesis's unified outline)
 9. Update README.md with links to all new docs
10. CI: ensure validate_codebase.py covers anti-placeholder + dependency-rule
```

### Month 1: P1

```
11. Create GOVERNANCE.md
12. Create docs/AI_POLICY.md
13. Create docs/ARCHITECTURE.md
14. Create CLAUDE.md (@import redirect)
15. Create GEMINI.md + .windsurfrules (symlinks)
16. Create per-package AGENTS.md (×5)
17. Add docs_improvement.yml issue template
18. CI: add AI-disclosure check + ai-assisted labeling
```

### Quarter 1: P2

```
19. Create .github/copilot-instructions.md (native)
20. Create .cursor/rules/dependency-rule.mdc
21. Create .cursor/rules/tdd-policy.mdc
22. Create CODEOWNERS for security paths
23. Create agent_issue.yml template
24. Add tools/validate_agent_files.py
25. Add CONTRIBUTORS.md + all-contributors bot
26. CI: gitleaks + bandit + semgrep on security-impact PRs
```

### Triggers That Accelerate the Roadmap

| Event | Response |
|:------|:---------|
| ≥10 PRs/month for 2 months | Promote P2 items; consider co-maintainer |
| 3 sustained contributors at 6 months | Fire governance trigger |
| AI PRs >30% of merged | Re-evaluate disclosure strictness |
| First security advisory | Post-incident retro; update SLAs |
| 1k stars + docs site exists | Adopt llms.txt |

---

## 13. Open Questions for Human Decision

1. **AI disclosure threshold**: Claude recommends "more than a single function or test" requires disclosure. ChatGPT is less specific. Ghostty's "drive-by AI PRs closed without question" is the strict end. **Pick a threshold.**

2. **DevContainer priority**: Gemini and Claude both recommend it for SQLCipher cross-platform pain. Currently P2. **Promote to P1?**

3. **Commit message format**: ChatGPT mentions Conventional Commits. Not in Claude's draft. **Adopt or skip?**

4. **PR review SLA**: Claude draft says 7 days (14 for security). **Realistic for a solo maintainer?**

5. **Coverage targets**: ChatGPT warns that enforcing coverage "causes trivial test writing." Claude's draft says "meaningful tests beat coverage targets." **Keep advisory-only?**

---

## Appendix A: Source Reports

| Report | File | Lines | Primary Contribution |
|:-------|:-----|:------|:---------------------|
| Gemini | `_gemini-Open-Source Contribution Guide Research.md` | 445 | 50+ repo survey, feature matrix, maturity model |
| ChatGPT | `_chatgpt-deep-research-report.md` | 424 | Friction analysis, checklists, security addendum |
| Claude | `_claude-Zorivest Contribution Documentation Suite.md` | 964 | File architecture, AI strategy, 6 draft templates |

## Appendix B: Combined Source Count

- **Gemini**: 66 sources cited (GitHub repos, blog posts, conference talks)
- **ChatGPT**: 15 primary source categories with sub-citations
- **Claude**: ~50 sources cited (repos, specs, vendor studies, policy documents)
- **Estimated unique sources after dedup**: ~100+ across all three
