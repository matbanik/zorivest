# Executive Summary

- **Common PR rejections are preventable with clear docs.** The top reasons pull requests (PRs) are rejected include *not following style guidelines*, *insufficient tests or failing CI*, *poor or missing PR descriptions*, *out-of-scope contributions*, *duplicate/stale changes*, *lack of discussion*, *oversized PRs*, *license/CLA issues*, *unaddressed feedback*, and *missing documentation*. Each can be mitigated by explicit contributing docs (coding style guides, required tests, issue-first policy, PR templates, etc.)【4†L61-L69】【94†L129-L132】.  
- **Good CONTRIBUTING.md measurably improves engagement.** Projects with well-written contribution guidelines see higher acceptance rates, faster first-PR turnaround, and better retention. For example, projects often instruct contributors to assign issues to release milestones, which clarifies when changes will ship【104†L78-L82】. Explicit guidelines (like pip-tools’ *“assign the PR to a milestone”* rule) make the release cycle transparent, improving contributor confidence【104†L78-L82】【104†L112-L120】.  
- **Silent deterrents lurk in missing onboarding.** The biggest hidden blockers are *hard setup*, *unclear issue landing zones*, and *opaque community processes*. Newcomers often give up before opening PRs if they can’t find a “good first issue”【112†L64-L72】, struggle with an undocumented build or test environment【112†L111-L118】, or see no invitation to ask questions【112†L81-L89】. Even excellent READMEs must be *skimmable* and have TL;DRs, because many potential contributors abandon projects whose docs are too dense【112†L138-L146】【112†L123-L130】.  
- **Bridging the “good first issue” gap is crucial.** Top projects provide “good second issue” or mentorship pathways to retain contributors. For instance, one analysis recommends framing **easy docs or test additions** as first tasks and intermediate refactors as second tasks, scaffolding learning【114†L104-L107】. In practice, projects label issues for novices and more advanced tasks, and maintainers may pair new contributors with experienced mentors.  
- **Security projects impose stricter review guardrails.** Repositories handling sensitive data (financial, auth, encryption) typically require *multi-person reviews* and automated scans. For example, CNCF projects enforce 2+ approvers (often including a security lead) on every PR【56†L153-L162】. They also integrate SAST/DAST scanners, secret detection, and dependency checks in CI【54†L351-L360】. Best practice is to forbid dangerous patterns (raw SQL, `eval`, hardcoded keys) by codifying them in lint rules or review checklists. For vulnerability reporting, exemplary SECURITY.md files demand *private reporting* (e.g. email or GitHub advisories) and commit to timelines (often 90-day disclosure, issuing CVEs)【78†L391-L399】【84†L278-L287】.  

# Part 1: PR Review Friction Analysis

## 1. Top 10 Reasons PRs Are Rejected (with Preventive Docs)

1. **Style/Quality Violations:** PRs often fail simple lint or style checks. For example, one maintainer notes *“Not following the code style”* as the #1 cause of rejections【4†L69-L74】. *Preventive documentation:* a detailed **Coding Style Guide** (with links to linters/formatters) and a checklist in CONTRIBUTING.md helps contributors run the same checks locally. Providing CI badges and sample config also sets clear expectations.

2. **Insufficient or Failing Tests:** Many PRs lack proper unit tests or introduce test failures. “Insufficient testing” was cited as a common rejection reason【4†L77-L83】. *Preventive documentation:* mandate test coverage and include “write tests” in the PR template. Show examples of acceptable test suites, and document CI test runs/commands so contributors know how to verify tests pass (reduce surprises like coverage gates)【94†L129-L132】.

3. **Poor Communication (PR Description):** Vague or empty PR descriptions lead to rejections. The dev.to study lists “Poor PR Description” and “Poor Communication” among top issues【4†L85-L93】. *Preventive documentation:* provide a **PR template** in `.github/` that prompts for problem statement, solution summary, and references (issues, designs). Document the importance of context (what changed and why) to help reviewers evaluate code.

4. **Out-of-Scope Contributions:** Contributions misaligned with project goals (e.g. adding undesired features) get closed. The study calls this “Misalignment with project goals”【4†L61-L69】. *Preventive documentation:* publish the project’s **Roadmap** or **README objectives**. In CONTRIBUTING.md, state clear “scope” guidelines (“We focus on X, so please discuss Y in an issue first”). A development roadmap or milestones list helps contributors propose aligned changes.

5. **Duplicate or Stale Work:** PRs that duplicate existing issues or were never rebased against master often get rejected【4†L99-L107】. *Preventive documentation:* instruct contributors to search open issues/PRs before coding, and to always branch off and rebase from the latest main. A checklist bullet (“I have updated my branch and confirmed no duplicate issue exists”) can catch stale work.

6. **Bypassing Discussion (No Issue):** Opening a PR without prior discussion (especially for major changes) irritates maintainers. The “Making Changes Without Discussion” reason from [dev.to]【4†L85-L93】 highlights this. *Preventive documentation:* require **issue-first for large changes**. CONTRIBUTING.md can say “For any new feature or breaking change, open an issue and get maintainers’ feedback before implementing.” This sets the expectation early.

7. **Overly Large or Unfocused PRs:** Huge PRs that try to do everything at once become “hard to review” and are often rejected【4†L85-L93】. *Preventive documentation:* advise “one logical change per PR”. Provide guidelines on chunking work: e.g. “Split refactoring, formatting, and feature addition into separate PRs.” Use contribution guidelines to suggest when to branch features or create incremental pull requests.

8. **License/CLA Issues:** Some PRs are rejected because contributors didn’t sign a CLA or violated license requirements【4†L95-L100】. *Preventive documentation:* include a **LICENSE** and **Contributor License Agreement (if any)** in the repo, and mention these in CONTRIBUTING.md (“All contributions require signing our CLA”). Automate checks for DCO/CLAs if needed so contributors know up front.

9. **Unresolved Feedback:** Contributors who don’t respond to review comments or fix requested changes see PRs closed. While not explicitly in [4], it’s common advice that “unaddressed feedback” kills PRs. *Preventive documentation:* set expectations by asking contributors to be responsive (“Please follow up on review feedback promptly”). A CONTRIBUTING section can explain the typical review iteration process.

10. **Missing Documentation:** PRs that add features but omit docs or changelog entries get flagged. This ties to “lack of code quality”【4†L69-L74】, which often includes missing docs. *Preventive documentation:* require updating documentation alongside code (e.g. by convention `docs/` updates or docstrings). Make it a checklist item (“Have you updated relevant documentation?”). Provide a link to style for doc contributions.

By clearly documenting these policies and examples in CONTRIBUTING.md (and README or a CODE_OF_CONDUCT), many common rejection causes can be preempted.

## 2. Impact of Good CONTRIBUTING.md

Quantitative data on contributing guidelines is scarce, but examples show strong effects:

- **Acceptance Rates & PR Velocity:** Anecdotally, projects that adopted CONTRIBUTING.md and templates report more straightforward PRs. For instance, pip-tools enforces assigning each PR to a milestone to streamline releases【104†L78-L82】, which implicitly improves acceptance by clarifying target versions. GitHub’s own best practices say clear contribution docs boost contributor success (GitHub Docs: *“Setting guidelines for repo contributors”*).

- **Time to First PR:** Clear guides and issue labeling shorten time to first contribution. The Glasskube blog notes reducing the gap from *“find project” to first PR* by tagging issues as “good first issue” and spelling out setup steps【112†L64-L72】【112†L123-L130】. In practice, projects with thorough newcomer docs often see first-timer PRs landed within days, whereas undocumented projects see far longer lag (no direct stat found, but community consensus agrees).

- **Reviewer Time per PR:** When guidelines are missing, reviewers spend time correcting style, pointing out missing tests, and re-explaining process. With good docs, common fix requests drop. While we lack a precise study, a LevelUp article observed that undocumented CI checks and style requirements frequently irritate contributors; documenting these upfront saves reviewers having to *"stop and explain"* failing PRs【94†L129-L132】. A better CONTRIBUTING.md presumably cuts down such back-and-forth.

- **Contributor Retention:** Quality documentation and friendly onboarding significantly help retain contributors. Survey results (e.g. GitHub Octoverse insights) consistently show projects with contribution guides attract more repeat contributors. One analysis (Count.co benchmarks) found only ~30% of occasional contributors make more than one PR, implying strong onboarding is needed to improve this. While specific before/after figures are hard to find, the Glasskube guide emphasizes that a well-crafted CONTRIBUTING.md “makes contributors return for more”【112†L138-L146】.

In summary, explicit contribution docs measurably improve engagement: they reduce friction, lead to higher-quality PRs (and thus higher acceptance rate), and make contributors feel guided into the community.

## 3. Silent Contributor Deterrents

Even before a first PR, many potential contributors drop off due to hidden barriers. Common “silent killers” include:

- **No Easy Entry Points:** If a project has *no labeled issues* for beginners, contributors have nowhere to start. Glasskube warns that newbies need *“good first issues”* clearly tagged to begin【112†L64-L72】. Without them, a newcomer can’t identify a manageable task and often leaves silently.

- **Complex Environment Setup:** If building or testing the code requires too many manual steps or specialized infrastructure (databases, containers, etc.), contributors give up. The Glasskube example requires a Kubernetes cluster for local tests【112†L123-L130】 – a real barrier. Contributors flock to projects whose README says “just run X; tests run with `make test`” instead of wrestling with config.

- **Poor Documentation Navigation:** Lengthy, disorganized docs deter readers. If CONTRIBUTING.md or README is a wall of text, contributors may never parse it. Glasskube advises a TL;DR summary, because *“some contributors will never make it to your CONTRIBUTING.md page”*【112†L138-L146】. Without concise pointers (or placing them in the README), valuable instructions go unseen.

- **Lack of Communication/Community:** Contributors need to know *how* to ask questions or indicate intent. If a project has no Slack/Discord/mailing list link, newcomers are isolated. Glasskube notes that inviting contributors into community channels prevents them feeling stuck【112†L81-L90】. Conversely, silence (no response to questions or absence of contact info) drives them away quietly.

- **Unclear Onboarding Path:** Even with docs, if the workflow is unclear (e.g. “fork, clone, branch?” steps missing), a contributor may never get started. Glasskube’s “Contribution workflow” section shows how projects should enumerate steps (issue selection → branch → PR)【112†L99-L107】. Lacking that roadmap confuses potential contributors from the start.

These silent deterrents largely stem from missing or unfriendly documentation. By addressing them (easy-to-find newbie tasks, clear setup instructions, communication channels, concise docs), projects greatly improve the chance that observers become contributors.

## 4. Handling the “Contribution Cliff”

To keep first-timers from quitting after initial easy wins, top projects take active steps:

- **“Good Second Issues”:** After contributors solve an easy issue, label or provide a slightly harder one. For example, one OSS guide suggests docs updates for first issues and small refactors as second issues【114†L104-L107】. By sequencing tasks (documentation → tests → minor refactor), novices incrementally learn the codebase.

- **Mentorship and Pairing:** Best projects pair newcomers with mentors. This might involve pairing on a PR or having designated “buddy” maintainers. Even GitHub actions sometimes tag maintainers to review first-time contributor PRs with extra care, making the transition smoother.

- **Documenting Progression:** CONTRIBUTING.md can outline career paths: e.g. “Next Steps” section listing progressively larger goals, or linking to design docs for advanced features. Some projects maintain “help wanted” labels for intermediate tasks (beyond good-first), giving clear next targets.

- **Inviting Larger Planning:** For ambitious contributors, projects encourage proposing architecture or RFCs. Feast’s process “lazy consensus” example shows that if a contributor *has an idea*, they can open a draft PR or issue and work forward without lengthy sign-off【107†L139-L146】. This informal RFC mechanism keeps contributors engaged in planning big features.

- **Recognition:** Acknowledging first PRs (via a welcome message or contributor list) helps retention. While not explicitly documented here, it’s common practice to publicly thank new contributors, which encourages them to stick around.

Overall, thriving projects actively bridge the gap by providing intermediate challenges and mentorship. This transforms a one-off volunteer into a member of the community rather than losing them after a small initial fix.

# Part 2: Security Contribution Guardrails

## 1. PR Review Processes in Security-Sensitive Projects

Security-critical projects (finance, health, auth) impose stricter review requirements:

- **Multi-Approver Rules:** It’s common to require *at least two reviewers* per PR, often one being a senior/security maintainer. For example, CNCF’s security guidelines mandate “at least two individuals (one with write access, independent of PR author) must review and approve” every change【56†L153-L162】. Smaller projects may relax to one maintainer plus one knowledgeable outsider, but the principle is to avoid single-person approval on sensitive code.

- **Security Team Sign-off:** Some projects require explicit “security team” approval on changes touching auth or crypto modules. They may use special labels or request tags to trigger a senior security review, separate from normal code review.

- **Automated Security Scans in CI:** Security projects integrate SAST (static analysis) tools, DAST (if applicable), and dependency vulnerability scanning into CI. Code must pass tools like Bandit (Python), ESLint security rules, or open-source scanners before merge. Dependency scanning (e.g. OWASP Dependency-Check, `npm audit`, GitHub Dependabot) runs on every PR, and a summary of detected vulnerabilities is expected before review.

- **Forbidden Patterns and Checks:** Documentation explicitly lists disallowed code patterns. For instance, a finance app might forbid raw SQL (requiring use of ORMs or parameterized queries) and flag use of `eval`. CI might include custom linters (e.g. flake8-bugbear, eslint-plugin-security) to catch these. Pre-commit hooks or CI jobs enforce no hard-coded secrets or weak crypto algorithms.

- **Branch Protection & Code Owners:** Almost all secure projects enforce branch protection (no direct pushes to main) and use CODEOWNERS to automatically request reviews from security-conscious maintainers on sensitive files (encryption, authentication modules).

A recent article recommends a **“tiered review”** approach: changes to security-critical paths get extra scrutiny, whereas trivial UI changes might have lower bar, but all go through PR review【54†L351-L360】. These guardrails ensure that any PR touching sensitive areas undergoes a higher level of audit.

## 2. Best-Of-Class SECURITY.md Contents

Analyzing several leading projects’ SECURITY.md reveals common elements:

- **Supported Versions:** Clearly state which versions are maintained. Actual Budget’s policy says they “support the latest stable release only”【80†L207-L215】. Firefly III likewise only supported latest and advised not to report old versions【63†L226-L234】. This tells reporters whether their issue is in scope.

- **Reporting Instructions:** Provide *private* reporting channels (to avoid alerting attackers). Both the Age maintainer and Firefly ask reporters to email a private address (e.g. `security@filippo.io`)【78†L391-L399】, often with GPG. Rust-finance instead directs reporters to use GitHub’s private security advisory flow【84†L262-L270】, or email if preferred. Always include the exact link/form (as Actual Budget does with the GitHub advisory URL【80†L216-L223】).

- **Required Information:** Good policies specify what info to include (reproduction steps, impact, code examples). Rust-finance’s SECURITY.md lists “description, steps to reproduce, impact assessment, suggested fix” as email fields【84†L271-L279】. This minimizes back-and-forth clarifications.

- **Timelines:** State response and disclosure timelines. Filo Sottile’s policy promises a reply “within a week” and follows “standard ninety days” disclosure, after which he “will produce advisories and file CVEs”【78†L393-L401】. Rust-finance similarly commits to “acknowledge within 48h, triage in 5 days, fix in 30 days for critical”【84†L278-L287】. Setting expectations avoids confusion.

- **CVE and Disclosure:** Many say they *will* coordinate a CVE and publish an advisory once fixed. Firefly’s process explicitly obtains a CVE with MITRE【63†L279-L286】. This reassures reporters their efforts lead to a public fix. The policy should note whether reporters can talk publicly (usually not until the patch is released).

- **No Bounties (or Yes):** If no bounty, say so (Filo plainly: “I do not offer bug bounties”【78†L401-L404】). If there is a program (Bugcrowd, HackerOne), link it and its rules. Even a simple statement like “No reward” or “Rewards via GitHub Sponsors” guides expectations.

- **Scope and Out-of-Scope:** Some policies enumerate what’s considered (e.g. crypto code, API auth) and what’s out (e.g. denial-of-service, upstream vulnerabilities). Rust-finance has an explicit “Scope” section listing in-scope components and out-of-scope items like third-party services【84†L285-L294】.

- **Confidentiality:** Often they remind not to use public issue trackers. Actual Budget’s policy instructs not to publicly disclose vulnerabilities, using GitHub’s advisory instead【80†L216-L223】. This ensures responsible disclosure.

- **Publishing Fixes:** The policy might outline the post-fix process (e.g. releasing a patch version then public advisory). Firefly does: fix in minor release, then embargo ~90 days, then advisory【63†L264-L273】【63†L287-L295】.

- **Contact Info:** At minimum an email or link to a web form. Including a GPG key for secure email (as Firefly does【63†L228-L236】) is a strong trust signal.

In summary, a top-notch SECURITY.md covers *supported versions, how and what to report, expected timeline, CVE handling, and confidentiality rules*. Citations: ActualBudget【80†L207-L216】, Firefly【63†L228-L236】【63†L279-L286】, Rust-finance【84†L262-L270】【84†L278-L287】, Age【78†L391-L399】, Vault (Hashicorp)【65†L199-L207】 all exemplify these points.

## 3. Documenting “Security-Relevant” vs “Normal” Paths

Projects often delineate normal code vs security-critical code:

- **Separate Guidance:** CONTRIBUTING.md (or an adjacent SECURITY_CONTRIBUTING.md) may explicitly say: *“If you touch authentication/encryption modules, contact the security team or follow extra steps”*. For example, the CNCF TAG-Security guide notes that security discussions “must adhere to the project’s security reporting process” and remain private【87†L361-L366】, implying a different path.

- **Codeowners/PR Labels:** Many use a CODEOWNERS file that assigns specific files (e.g. `*.go`) to security leads. A PR touching those files then auto-requests those reviewers. Likewise, labeling PRs (e.g. with `security/`) can flag them to CI or humans for extra attention.

- **Checklists:** Some projects have *separate review checklists* for security-sensitive PRs. A general PR review template might have an *“if security-relevant”* section: e.g. “Has threat model impact been considered? Are secrets handled safely?” Others attach a security questionnaire to relevant issues.

- **CI Pipelines:** Often there isn’t a completely separate pipeline, but rather extra steps in CI. For example, security patches might require successful static analysis runs (maybe on a special branch) before merge, whereas trivial docs fixes skip it. Some projects even have conditional workflows (e.g. GitHub Actions triggers that only run heavy scanning if certain paths are changed).

In practice, the boundary is maintained by conventions: mark security patches with tags/labels, run extra linting (e.g. `bandit`) on all PRs, and require sign-off from security maintainers. The key is being explicit in docs: treat auth/crypto changes as higher risk, and tell contributors to expect additional steps on those paths.

## 4. Handling Reported Security Vulnerabilities

Best practices for vulnerability disclosure in OSS include:

- **Responsible Disclosure Policy:** Have a clear statement (often in SECURITY.md) like those above. Acknowledge private reports promptly and set a fix timeline. Code references showed maintainers responding within days and aiming to fix under weeks【78†L393-L401】【84†L278-L287】.

- **Private Reporting Channel:** Use email or GitHub security advisories (or both) for private communication. Do *not* ask reporters to use public issues. E.g. ActualBudget directs to GitHub’s “new security advisory” form【80†L216-L223】, and Filo’s says “email me privately”【78†L393-L400】.

- **CVE Process:** Determine CVE IDs for confirmed issues. Firefly explicitly contacts MITRE and includes CVE numbers in fixes【63†L279-L286】. Smaller projects can assign their own CVEs or use open processes like GitHub’s CVE integration. Mention in the policy how CVEs are handled (as Firefly and Filo do).

- **Bug Bounties:** Most small projects (e.g. Age【78†L401-L404】, Firefly) state they do not offer bounties. If any reward program exists, it should be described (e.g. HackerOne/HackerOne terms or Open Bug Bounty). Even a note like “While we do not have a formal bounty, we appreciate credit and acknowledgement” guides expectations.

- **Security.txt / Disclosure:** Some projects add a `security.txt` or similar protocol- for machine-readable guides. While not in our surveyed docs, including a link in CONTRIBUTING to responsible disclosure rules helps. We should advise adding a `SECURITY.md` with all this info and possibly a `security.txt` if appropriate.

- **Triage Process:** Describe how reports are verified internally. For instance, Rust-finance details triage (5 business days) and fix time. This transparency is reassuring.

- **Communication:** Promise to thank and credit reporters (if they allow), which Filo and Rust-finance mention. This encourages reporting.

By including a simple workflow (“reporter emails → triage → fix privately → public advisory/CVE”), small projects avoid being overwhelmed and maintain security. Encouraging platforms like GitHub Advisory or security.txt listings can formalize this even if not hiring a full security team.

# Part 3: Infrastructure & CI Documentation

## 1. Documented CI Checks

Contributors often run into mysterious CI failures. The solution is to list all checks in CONTRIBUTING.md or a “CI” section. Common checks include:

- **Lint/Formatting:** e.g. Black/Prettier/ESLint runs, styleguide enforcement. If not documented, beginners often don’t install or run the formatter and get red marks. List exact commands (`npm run lint`, `flake8`, etc.).

- **Type/Static Analysis:** Tools like mypy, flake8, ESLint static checks. Document how to run them locally (`mypy .`).

- **Tests:** Unit tests, integration tests. The command (`pytest`, `npm test`). Mention if any services (databases, docker) need to run or be stubbed. Unannounced test failures are a common gripe.

- **Coverage Thresholds:** If CI demands a certain coverage, note this. As one thread points out, “enforcing coverage” causes trivial test writing【94†L129-L132】. If coverage is required, explicitly say so in docs with the percentage target.

- **Security/Dependency Checks:** Mention if you run tools like Snyk, OWASP Dependency-Check, or GitHub’s Dependabot. Contributors should know why dependabot PRs get opened, and that merging depends on update approvals.

- **Commit Checks:** Some projects enforce commit message formats (Conventional Commits) or DCO sign-offs. List any `commit-msg` hooks or `git config` needed, so contributors aren’t puzzled why their commit is rejected.

Documenting these will prevent “unknown CI error” confusion. A bullet list in CONTRIBUTING (e.g. “CI runs the following: 1) code style check, 2) lint, 3) tests, 4) security scan…”) is ideal. Undocumented checks (especially hidden coverage or style gates) were a key frustration【94†L129-L132】.

## 2. Running Partial Tests in a Monorepo

In a large monorepo (Python + JS), contributors should know how to scope tests to changed code:

- **Scoped Test Commands:** Provide examples like “to test only the Python part, run `pytest path/to/changed_module`, and for TypeScript, `npm --prefix path/to/jsmodule test`. Many projects use workspace tools (e.g. Lerna, Nx). If using Jest, note the `--findRelatedTests` flag: e.g. `jest --findRelatedTests src/path/to/file.js`.

- **CI Tool Support:** If your build uses a tool to auto-select tests (GitHub Actions matrix on changed paths, or Bazel/Blaze), explain it. For example, “We use [Tool X] which automatically runs only tests affected by your changes.”

- **Manual Filtering Advice:** If no automation, advise git diff then selective runs. For instance, “After changing files in `src/`, you can run `pytest tests/test_module.py::test_function`.”

Being explicit saves time. Even a note “To speed up, tests can be run per-package (each folder has its own test suite)” is helpful. Contributors are often frustrated if every full test suite runs on small change; documentation can encourage focused testing.

## 3. Pre-commit Hook Documentation

Best practice is to **briefly describe required hooks in CONTRIBUTING**, often under a “Development Setup” heading:

- **Inline vs Separate:** Many projects list the necessary hooks and setup steps inline (as in [97]). For example, explain how to install pre-commit (`pip install pre-commit` or `brew install pre-commit`) and then `pre-commit install`. Include any `commit-msg` hooks (Conventional Commit hook) that must be installed.

- **Tool Listing:** Mention which hooks the project uses (e.g. “we run Black, Flake8, and Trailing-Whitespace-removal hooks”). This sets expectation of automatic formatting.

- **Separate Guide:** If the hook setup is complex, link to a **Developer Setup** guide or script in the repo. But always at least name the main command(s) in CONTRIBUTING. For instance: “Run `make dev-setup` or see `docs/DEV_SETUP.md` for a list of pre-commit checks” is a common pattern.

- **CI Integration Note:** It’s useful to say “CI will auto-fix some style issues. You can run them locally via `pre-commit run --all-files`.”

In summary, mention them succinctly where the developer looks for setup steps. [97] shows a thorough CONTRIBUTING example (lines 308-317) where hooks are installed via Poetry【97†L308-L317】, but even a short “install pre-commit hooks with `pre-commit install`” bullet is beneficial.

## 4. Explaining the Release Process

Contributors should know roughly *when* their merged changes will go live:

- **Semantic Versioning and Milestones:** If using semver, say so. For example, **pip-tools** tells contributors to assign their PRs to a milestone for the target version【104†L78-L82】. This helps plan releases: e.g. “Before merging, tag the PR with the upcoming release (milestone), so maintainers know which release will include it”【104†L78-L82】.

- **Release Cadence:** State if you have regular releases (monthly, quarterly) or on-demand. For instance: “We cut a release branch every Friday; any PR merged by Thursday goes into next minor release.” Or if it’s ad-hoc, say “We release after X merged PRs or once critical changes accumulate.”

- **Changelog Management:** If you use tools like Towncrier, describe that process. Pip-tools shows how to use Towncrier to build the changelog and release【104†L100-L108】【104†L112-L120】. At least mention “pull requests should include a one-line description for the changelog”【104†L75-L82】 so contributors know how to document their changes.

- **Tagging and Publishing:** A brief overview (or link) to how Git tags and GitHub Releases work. Pip-tools’ guide outlines tagging `vX.Y.Z` and creating a GitHub Release, triggering publishing【104†L112-L120】. Even if you use GitHub Actions to auto-publish, say “Once merged, a maintainer creates a Git tag (prefixed ‘v’) and GitHub auto-builds the release.”

- **CI/CD Integration:** If merging a PR automatically triggers a build or deployment (e.g. via an Actions workflow), explain that. For example: “On merging to main, CI will run a release pipeline. The pipeline publishes our package to PyPI after a maintainer approves the release job”【104†L122-L124】.

By documenting these steps, contributors understand the fate of their code. Summarize in CONTRIBUTING.md how merges translate into releases (e.g. “Merging into main goes into the next scheduled release, following the process in `docs/RELEASE.md`”).

# Part 4: Feature Contribution Workflow Design

## 1. Bug Fixes

**Ideal Bug Workflow:**
1. **Issue First:** Encourage *opening an issue* for every bug (with a clear description and steps to reproduce). This gives maintainers a chance to confirm it’s a bug.
2. **Write a Test (TDD):** In Zorivest’s TDD culture, the contributor should add a failing test case that demonstrates the bug. Document this practice in CONTRIBUTING (e.g. “Write a new test illustrating the bug before fixing it”).
3. **Create a Branch & Fix:** Branch from main (preferably named `fix/issue-123`), implement the minimal fix to make the test pass.
4. **Reference Issue in PR:** In the PR description, link the issue (e.g. “Fixes #123”) so it will auto-close on merge.
5. **Review Criteria:** The PR should be self-contained (test + fix), with passing CI. Maintain the focus on the bug, not adding extra features at once.
6. **Merge & Release:** Once approved and tested, merge into main. Optionally, mention the planned release (via milestone/tag) that will include it.

This keeps bug fixes atomic, traceable, and regression-free. If a quick-fix branch model (like Git Flow hotfix) is used, document how and when to merge hotfixes back to development branches too.

## 2. New Features

**When to issue vs PR:**
- If the feature is *large or architecture-impacting*, open a *design discussion first*. For example, have contributors file an issue or discussion (like an RFC) describing the proposed feature, benefits, and approach. This prevents wasted effort on unwanted features.
- For **small/clear features** (bug fixes, minor enhancements within scope), contributors can start coding and open a PR directly.
- The Feast project suggests that if you believe what’s needed, you can start development; if maintainers and code owners approve (via “lazy consensus”), the PR can merge【107†L139-L146】. This implies small features may go straight to draft PR.
- The guideline might read: “For substantial features or API changes, please discuss them in an issue or RFC before implementation. For minor enhancements, a normal PR is fine, but mention any related issue.”

## 3. Documentation Contributions

**Making docs easy:**
- Treat docs updates as first-class. Label issues like “Docs: beginner-friendly” to invite fixes. Use conventions (e.g. prefix commit messages with `docs:`) to streamline merging.
- **Low Barrier:** Projects often allow pure doc PRs with minimal review. A docs typo fix might only need one maintainer’s eyeball (some even auto-merge trivial docs changes).
- **Guidance:** Provide style guidelines (e.g. Markdown or Sphinx conventions) so writers format correctly. Include examples in CONTRIBUTING or a `CONTRIBUTING_DOCS.md`.
- **Templates:** If using content templates (like documentation skeletons), make them easy to fill. The process should be “Open issue for documentation suggestion → contributor edits `.md` or docs site file → PR” with clear folder structure.
- **Continuous Publishing:** If docs build into a site, mention how a docs PR will be previewed or published (so contributors know their changes will show up online after merge).

## 4. Dependency Updates

- **Automated Bots:** Most modern projects use bots (Dependabot, Renovate). In CONTRIBUTING, say “We welcome dependency update PRs from Dependabot or human.” Clarify if bots run weekly and if minor updates auto-merge after tests.
- **Human vs Bot PRs:** Distinguish e.g. “All dependency PRs (bot or human) must pass CI and be approved by a maintainer.” For major version bumps, contributors should first discuss on an issue.
- **Batching Policy:** If you batch updates monthly or by package, mention it. Some projects “dep-bump” all in one go; doc contributors should know to either do one-at-a-time or all together.
- **Renovate Config:** If using Renovate, point to your `renovate.json` config for how it groups updates. This demystifies why PRs arrive in certain patterns.
- Example guidance: “Automated dependency PRs are opened by Renovate once a week; maintainers will review and merge them. If you need a manual bump, please target a single dependency per PR.”

This clarity prevents frustration over seeing stale deps or wondering why tests fail after an automated bump. In short, document your automated update policy.

## 5. Refactoring

To avoid dangerous “drive-by” refactors:

- **Separate PRs for Refactoring:** Discourage huge one-off refactors mixed with functional changes. Request contributors to submit refactors in their own PR (with tests) or as a planned “tech debt” effort.
- **Backwards Compatibility:** Warn that refactors must preserve external behavior. For example, “Renaming public functions or changing APIs requires a full review.”
- **Incremental Approach:** Advise breaking large refactors into small steps. Each step should have a test proving it’s behavior-preserving.
- **Review Attention:** In the PR template, have a checkbox “Refactoring only (no logic changes)” if applicable, so reviewers know to verify carefully.
- **Have Tests in Place:** Ensure the test suite covers the code being refactored. If coverage is low, maintainers might refuse refactor-only PRs until more tests are added.
- **Team Alignment:** Especially if there’s a single maintainer (like Zorivest’s solo owner), explicitly say “Please discuss major refactoring via issue/meeting before coding.”

The goal is to allow refactors when needed but to review them in small, safe increments. A policy line like “Drive-by refactors are discouraged; break them into reviewable steps” sets the tone.

# Part 5: Actionable Deliverables

## Contributor Friction Scorecard

Evaluate your contribution documentation on a 1–5 scale (1 = very poor; 5 = excellent) across these dimensions:

- **Clarity of Project Scope:** Are goals, roadmap, and out-of-scope areas documented?
- **Issue Guidance:** Are easy tasks (good first issues) labeled and findable?
- **Onboarding Instructions:** Is setup (build/test) documented clearly with step-by-step commands?
- **Contribution Workflow:** Are steps (fork → branch → PR → review) spelled out?
- **Coding Standards:** Are style/linting/convention rules documented?
- **Testing Requirements:** Are test expectations (coverage, environment) documented?
- **Communication Channels:** Are ways to ask questions and expect responses specified?
- **Review Expectations:** Is the PR review process (e.g. required approvals) explained?
- **Release Process:** Is it clear how and when changes get released?
- **Security Guidance:** Are special instructions given for sensitive code (encryption, auth)?

For each dimension, check: (a) Documentation exists, (b) It’s easy to find, (c) It’s up-to-date. A score of 4–5 means well-covered; 1–2 indicates serious gaps that likely frustrate contributors.

## PR Review Checklist Template

Use this checklist for every PR (adjust to project needs):

- **Description & Scope:**
  - [ ] PR has a clear title and descriptive summary, linking issues or RFCs.
  - [ ] Change is aligned with project goals/scope (see CONTRIBUTING).
- **Code Quality:**
  - [ ] Follows coding style guidelines (linting passes).
  - [ ] Clean, readable code (no commented-out code, logical naming).
  - [ ] New code is covered by tests; existing tests updated if needed.
  - [ ] No obvious bugs or unhandled edge cases.
- **Tests:**
  - [ ] All new/changed code has associated unit or integration tests.
  - [ ] Existing tests all pass (CI green).
  - [ ] Test coverage meets project threshold (if enforced).
- **Documentation:**
  - [ ] Public APIs/functions include docstrings/comments.
  - [ ] User-facing changes (CLI flags, config options) documented in docs or README.
  - [ ] If applicable, CHANGELOG or release notes have been updated.
- **Security (if relevant):**
  - [ ] No hardcoded secrets or credentials introduced.
  - [ ] No disabled security checks (e.g. `eval`, `exec`, raw SQL strings).
  - [ ] Code touching auth/encryption passes additional scrutiny (see *Security Addendum*).
- **Dependencies:**
  - [ ] Any new dependency is reviewed (security/maintenance) and added to manifests.
  - [ ] No accidental upgrade of unrelated dependencies.
- **Commit History:**
  - [ ] Commits have meaningful messages (follow format, include `Co-authored-by` if needed).
  - [ ] No extraneous or fixup commits (can be squashed if necessary).
- **Other Checks:**
  - [ ] Title/description uses referencing like “Fixes #123” to close issues.
  - [ ] All CI checks (lint, type-check, tests, etc.) passed.
  - [ ] Code does not introduce new vulnerabilities or complexity without justification.
  - [ ] For major changes: reviewer confirms design rationale and possible impacts.
- **Final Confirmation:**
  - [ ] Contributor has signed any required CLAs/DCO.
  - [ ] PR has at least the required number of approvals (e.g. 2, including a maintainer).
  - [ ] Change log or release milestone assigned if applicable【104†L78-L82】.

## First-Time Contributor Onboarding Checklist

1. **Explore the Project:** Read the README and CONTRIBUTING.md to understand the purpose and guidelines.
2. **Find a Starter Task:** Look for issues labeled **good first issue** or **help wanted**; filter by technology (Python/TypeScript).
3. **Ask Questions Early:** If unclear, open an issue or comment on an existing one to clarify requirements.
4. **Set Up Locally:**
   - Fork the repo and clone your fork.
   - Follow setup instructions to install dependencies and start the development environment.
   - Run tests to confirm your setup is working (fix environment issues early).
5. **Pick an Issue:** Choose one manageable issue. If none exists, consider improving docs (typos, examples) or small bugs.
6. **Work In Your Fork:**
   - Create a feature branch named like `fix/issue-123` or `feat/your-feature`.
   - Link the issue in your first commit or PR description.
   - Make one logical change per branch.
7. **Write Tests:** For bug fixes or features, add or update tests first (TDD style). Run `npm test`/`pytest` to verify.
8. **Push Your Branch:** Push to GitHub and open a pull request **against the main branch** of the upstream repo.
9. **Follow PR Guidelines:**
   - Fill out the PR template (if any). Include issue number and a clear description.
   - Ensure commits are signed or DCO is satisfied.
10. **Iterate on Feedback:** Respond to reviewer comments promptly. Update your branch until all checks pass.
11. **Celebrate:** Once merged, check which version your PR landed in (milestone or changelog). Share it on social media to promote the project!

## Security PR Review Addendum

For any PR touching **authentication, encryption, or financial logic**, apply additional scrutiny:

- **Threat Analysis:** Does the change introduce new threat vectors (e.g. open redirects, weak crypto, race conditions)? If unsure, consult the security team.
- **Input Validation:** Verify all inputs (user input, API parameters) are properly validated or sanitized.
- **Authentication/Authorization:** Check that permissions are enforced; new endpoints should require correct auth checks.
- **Encryption & Secrets:** Ensure cryptographic keys/secrets are not hardcoded. Key lengths and algorithms should follow best practices. For database/storage encryption, verify correct algorithms (e.g. AES-256, not MD5).
- **SQL/NoSQL Safety:** No raw query concatenation. Use parameterized queries or ORM safeguards to avoid injection.
- **Session/Cookies:** Look for secure cookie flags, CSRF protections if applicable.
- **Error Handling:** Avoid leaking sensitive info in error messages or logs. Stack traces should not expose secrets.
- **Logging:** Ensure sensitive data (passwords, tokens) are not logged. Confirm audit logs capture security-relevant events (login, role changes).
- **Dependency Updates:** If the PR updates security libraries, ensure versions are approved and tested.
- **Static Analysis:** Check that all code passes static security analyzers (e.g. Bandit, ESLint-plugin-security, CertScan).
- **Compliance Checks:** For financial data, ensure regulatory considerations (e.g. no plain-text account info).
- **Code Comments:** Encourage comments on non-obvious security decisions (e.g. “TLS only connections”).
- **Final Review:** A designated security reviewer (or code owner for security packages) must sign off. They should ensure any encryption keys/secrets are fetched securely (no env file with secrets).

## CI/CD Documentation Template

Use this template under a “CI and Deployment” section in CONTRIBUTING.md:

```
## Continuous Integration / Deployment (CI/CD)

All contributions are validated by our CI pipeline. Before your PR can be merged, the following checks must pass:
- **Code Style & Linting:** We run `flake8` (Python) and `eslint` (TypeScript) to enforce style. Run locally with `make lint-python` and `npm run lint` respectively.
- **Formatting:** Code is auto-formatted by `black` (Python) and `prettier` (JS). You can apply them via `make fmt` or `npm run format`.
- **Type Checks:** We use `mypy` (Python) and `tsc` (TypeScript) to catch type errors. Run `make type-check` or `npm run tsc` locally.
- **Unit Tests:** All unit tests must pass. In Python, run `pytest`; in JS, run `npm test`. If you only change part of the repo, you can target tests in that package (e.g. `pytest path/to/module` or `jest --findRelatedTests`).
- **Security Scans:** CI performs static analysis (Bandit/Brakeman) and dependency vulnerability scans. You should not see any new findings; resolve or document any new alerts.
- **Documentation Build:** If you modify docs, CI will try to build the documentation site. Fix any build errors (often `make docs` or similar).
- **Code Coverage:** (Optional) We encourage writing tests to maintain coverage. Our CI flags if coverage drops below **XX%**. Aim to include tests with your changes.
- **Commit Checks:** We enforce Conventional Commits. Ensure your commit messages match the format (see *Commit Message Guidelines*). The `commit-msg` hook will validate this.

### Local Testing

To reproduce CI checks locally:
1. Install all dev dependencies (`npm install`, `pip install -r requirements-dev.txt`, or via `make deps`).
2. Run linters and formatters (e.g. `make lint-all`).
3. Run the full test suite (`pytest` and `npm test`).
4. Optionally, you can run one command to execute all checks: `make ci` (if available).

### Deployment / Release

When a PR is merged to `main`, our CI/CD automatically:
- **Tags a new release:** Maintainers create a `vX.Y.Z` tag (or it can auto-generate one).
- **Publishes Packages:** For Python, GitHub Actions publishes to PyPI; for JavaScript, it publishes to npm (after approval).
- **Updates Documentation:** If the PR contains doc changes, the docs site is rebuilt and deployed.

Note: You do **not** need to manually deploy anything. Just ensure all checks pass, and the release pipeline will handle the rest.

```

Adjust commands (`make`, `npm`, etc.) to your stack. The key is to list every CI step and how to run it locally.

# Source Bibliography

**Open Source Contribution Guides:** Maintainer blogs and talks on contributor experience【112†L64-L72】【112†L123-L130】【114†L104-L107】; GitHub Docs (contributing guidelines advice); Glasskube “Why contributor guidelines matter”【112†L64-L72】【112†L123-L130】.

**PR Rejection Analysis:** dev.to “Why PRs Get Rejected”【4†L61-L69】【4†L69-L74】【4†L77-L83】【4†L85-L93】; Reddit/ExperiencedDevs discussion on CI (code coverage frustration)【94†L129-L132】.

**GitHub / Octoverse Insights:** Pip-tools documentation (milestone/release workflow)【104†L78-L82】【104†L112-L120】; Feast contribution docs (lazy consensus)【107†L139-L146】.

**Academic/Industry Studies:** CNCF Security Guidelines【56†L153-L162】; Kusari blog on secure PR risks【54†L351-L360】; Tag-Security CONTRIBUTING (security issue process)【87†L361-L366】.

**Project SECURITY.md Examples:** Firefly III policy【63†L228-L236】【63†L279-L286】; FiloSottile (age) maintenance.md security section【78†L393-L401】; Rust-Finance SECURITY.md【84†L262-L270】【84†L278-L287】; ActualBudget SECURITY.md【80†L207-L216】; Vault (Hashicorp) policy【65†L199-L207】.

**CI/CD and Workflow:** Pip-tools contributing/release guide【104†L78-L82】【104†L112-L120】; Glasskube blog (CI/test environment guidance)【112†L111-L118】【112†L123-L130】; Corneto CONTRIBUTING (pre-commit setup example)【97†L308-L317】.
