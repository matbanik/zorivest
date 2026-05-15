# ChatGPT Deep Research — PR Review Friction & Contributor Workflow Prompt

> **Optimized for**: ChatGPT Deep Research (GPT-5.2 / o3 reasoning)  
> **Leverages**: Iterative synthesis across hundreds of sources, deep reasoning chains, PDF/document interpretation, structured export (Word/PDF/Markdown), mid-run redirection  
> **Expected output**: Actionable checklists, friction analysis report, anti-pattern catalog with evidence

---

## Prompt

I'm designing the **contribution documentation suite** for an open-source financial portfolio management app called **Zorivest** (https://github.com/matbanik/zorivest). Before writing any files, I need deep analysis of **what actually causes friction during code review** and **what documentation practices measurably reduce PR rejection rates**.

This is a hybrid Python + TypeScript + Electron monorepo with financial data handling (encrypted SQLCipher database), so security and code quality are paramount.

### Part 1: PR Review Friction Analysis

Research and synthesize findings from:
- Open-source maintainer blog posts, conference talks, and post-mortems about contributor friction
- GitHub's annual Octoverse reports and studies on PR review times
- Academic research on code review effectiveness (e.g., from Microsoft Research, Google's engineering practices)
- Discussions on HackerNews, Reddit (r/opensource, r/programming), and dev.to about PR rejection frustrations

Answer these questions with evidence:

1. **What are the top 10 reasons PRs get rejected** in well-maintained open-source projects? Rank by frequency. For each, describe what documentation could have prevented it.

2. **What is the measurable impact of having good CONTRIBUTING.md documentation?** Find any data on:
   - PR acceptance rates before vs. after adding contribution guidelines
   - Time-to-first-PR for new contributors
   - Reviewer time spent per PR
   - Contributor retention rates

3. **What are the most common "silent" contributor deterrents?** (Things that make potential contributors leave without ever opening a PR)

4. **How do the best projects handle the "contribution cliff"?** — the gap between "good first issue" and becoming a regular contributor

### Part 2: Security Contribution Guardrails

For projects that handle sensitive data (financial, medical, auth), research:

1. **How do security-sensitive projects structure their PR review process differently?**
   - Extra review requirements (2+ approvals, security team sign-off)
   - Automated security scanning in CI (SAST, DAST, dependency scanning)
   - Forbidden patterns (e.g., no raw SQL, no eval, no hardcoded secrets)

2. **What do the best SECURITY.md files contain?** Analyze 10+ examples from:
   - Financial projects (Maybe Finance, Firefly III, GnuCash, Actual Budget)
   - Encryption/auth projects (age, Vault, signal-protocol)
   - CNCF projects (they have a standardized security process)

3. **How do projects document "security-relevant" vs. "normal" contribution paths?** Do they have separate review checklists? Separate CI pipelines?

4. **What are the best practices for handling security vulnerabilities reported by contributors?** Include:
   - Responsible disclosure policies
   - Bug bounty program structures (even informal ones)
   - CVE assignment processes for small projects

### Part 3: Infrastructure & CI Documentation

Research how projects document their CI/CD pipeline for contributors:

1. **What CI checks should be documented in CONTRIBUTING.md?** Analyze which checks frustrate contributors most when undocumented (based on GitHub issue complaints)

2. **How do monorepo projects explain "how to run tests for just my change"?** Especially Python + JS hybrid repos.

3. **What pre-commit hook documentation patterns work best?** Do projects list hooks inline or link to a separate dev setup guide?

4. **How do projects explain their release process** to help contributors understand when their change will ship?

### Part 4: Feature Contribution Workflow Design

Research optimal workflows for different contribution types:

1. **Bug fixes** — what's the ideal workflow from issue → PR → merge?
2. **New features** — when should contributors propose via RFC/discussion vs. just PR?
3. **Documentation** — what makes doc contributions low-friction?
4. **Dependency updates** — how do projects handle bot PRs vs. human dependency PRs?
5. **Refactoring** — how do projects prevent "drive-by refactoring" that introduces regressions?

### Part 5: Actionable Deliverables

Based on all research, produce:

1. **Contributor Friction Scorecard** — a rubric I can use to evaluate our own contribution docs (score 1-5 on 10 dimensions)
2. **PR Review Checklist Template** — a reusable checklist for reviewers that covers code quality, security, testing, and documentation
3. **First-Time Contributor Onboarding Checklist** — step-by-step from "I found this project" to "my first PR is merged"
4. **Security PR Review Addendum** — extra review items for PRs touching auth, encryption, or financial calculations
5. **CI/CD Documentation Template** — a template for the "How CI Works" section of CONTRIBUTING.md

### Output Format

Structure the report as:
- **Executive Summary** with the 5 most surprising/important findings
- **Detailed Sections** for each Part (1-5) with evidence citations
- **All checklists and templates** in copy-paste-ready Markdown format
- **Source Bibliography** organized by category

### Context About Zorivest

- Solo maintainer transitioning to community contributions
- Handles real brokerage account data encrypted with SQLCipher
- Has extensive AI agent instructions (`.agent/AGENTS.md`) — contributors may be AI agents
- Uses TDD with strict test-first policy
- Has a build plan with 200+ Manageable Execution Units (MEUs) — contributors need to understand where to help
- GitHub repo: https://github.com/matbanik/zorivest
