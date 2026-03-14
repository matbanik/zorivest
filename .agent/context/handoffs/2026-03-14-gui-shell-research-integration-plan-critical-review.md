## Task

- **Date:** 2026-03-14
- **Task slug:** gui-shell-research-integration-plan-critical-review
- **Owner role:** reviewer
- **Scope:** pre-implementation critical review of `docs/execution/plans/2026-03-14-gui-shell-research-integration/implementation-plan.md` plus the required correlated plan-folder/canonical-doc scope

## Inputs

- User request: review `[critical-review-feedback.md]`, `implementation-plan.md`, and the target plan folder for `2026-03-14-gui-shell-research-integration`
- Specs/docs referenced:
  - `.agent/workflows/critical-review-feedback.md`
  - `.agent/workflows/pre-build-research.md`
  - `AGENTS.md`
  - `.agent/docs/architecture.md`
  - `docs/build-plan/dependency-manifest.md`
  - `docs/build-plan/06-gui.md`
  - `docs/build-plan/06a-gui-shell.md`
  - `_inspiration/electron_react_python_research/synthesis-final-decisions.md`
  - `docs/research/gui-shell-foundation/style-guide-zorivest.md`
- Constraints:
  - Review-only workflow: findings only, no product fixes
  - Explicit plan path provided by user, so scope override applied to the full plan folder
  - Canonical review-file continuity required for this plan folder
  - Build-plan docs had to be inspected directly because the plan folder and research folder are currently untracked

## Role Plan

1. orchestrator
2. tester
3. reviewer
- Optional roles: researcher, guardrail

## Coder Output

- Changed files:
  - `.agent/context/handoffs/2026-03-14-gui-shell-research-integration-plan-critical-review.md`
- Design notes / ADRs referenced:
  - None
- Commands run:
  - Review-only; no product edits
- Results:
  - No product changes; review-only

## Tester Output

- Commands run:
  - `Get-Content -Raw SOUL.md`
  - `Get-Content -Raw GEMINI.md`
  - `Get-Content -Raw AGENTS.md`
  - `Get-Content -Raw .agent/context/current-focus.md`
  - `Get-Content -Raw .agent/context/known-issues.md`
  - `Get-Content -Raw .agent/workflows/critical-review-feedback.md`
  - `Get-Content -Raw .agent/workflows/pre-build-research.md`
  - `pomera_diagnose`
  - `pomera_notes search "Zorivest"`
  - `pomera_notes search "Memory"` (wildcard form `Memory/Session/*` failed under FTS5 parser)
  - `pomera_notes search "Decision"` (wildcard form `Memory/Decisions/*` failed under FTS5 parser)
  - `Get-ChildItem docs/execution/plans/2026-03-14-gui-shell-research-integration`
  - `Get-Content -Raw docs/execution/plans/2026-03-14-gui-shell-research-integration/implementation-plan.md`
  - `Get-Content -Raw docs/execution/plans/2026-03-14-gui-shell-research-integration/task.md` (failed: file missing)
  - `Get-ChildItem .agent/context/handoffs/*.md -Exclude README.md,TEMPLATE.md | Where-Object { $_.Name -notmatch '(critical-review|corrections|recheck)' } | Sort-Object LastWriteTime -Descending | Select-Object -First 20`
  - `rg -n "2026-03-14|gui-shell-research-integration|Create handoff:|Handoff Naming" .agent/context/handoffs docs/execution/plans/2026-03-14-gui-shell-research-integration`
  - `git status --short -- docs/build-plan docs/research docs/execution/plans/2026-03-14-gui-shell-research-integration .agent/context/handoffs`
  - `Get-ChildItem docs/research/gui-shell-foundation`
  - `Get-Content docs/build-plan/dependency-manifest.md`
  - `Get-Content docs/build-plan/06-gui.md`
  - `Get-Content docs/build-plan/06a-gui-shell.md`
  - `Get-Content docs/research/gui-shell-foundation/style-guide-zorivest.md`
  - `Get-Content _inspiration/electron_react_python_research/synthesis-final-decisions.md`
  - `Get-Content .agent/docs/architecture.md`
  - `rg -n -i "react-router|react-router-dom|BrowserRouter|HashRouter|React\.lazy\(|createHashHistory|createRouter|TanStack Router|zustand|electron-vite|tailwindcss|shadcn|React Compiler" docs/build-plan`
  - `rg -n "synthesis-final-decisions|gui-shell-foundation|style-guide-zorivest|pre-build-research" .`
  - `rg -n "navigate\('/|Route \| `/|Ctrl\+|/planning|/plans|/scheduling|/schedules|/accounts|/watchlists|/reports" docs/build-plan/06-gui.md docs/build-plan/06a-gui-shell.md`
- Pass/fail matrix:
  - Plan-review mode detection: PASS
  - Not-started / no correlated work handoff confirmation: PASS
  - Required plan-folder completeness (`implementation-plan.md` + `task.md`): FAIL
  - Navigation/router contract consistency: FAIL
  - Architecture/security contract consistency: FAIL
  - Shared-contract / package-boundary consistency: FAIL
  - Validation specificity / evidence quality: FAIL
  - Source-traceability completeness: FAIL
- Repro failures:
  - `task.md` does not exist in the target plan folder even though the workflow requires review of both `implementation-plan.md` and `task.md`.
  - The plan says route paths stay unchanged, but current canon already disagrees between `06-gui.md` and `06a-gui-shell.md` (`/planning` vs `/plans`, `/scheduling` vs `/schedules`, `/` vs `/accounts`, plus extra `/reports` and `/watchlists` routes).
  - The plan’s `patterns.md` scope says Zod schemas are shared with the MCP server, but the adopted GUI-stack synthesis explicitly chose standalone package boundaries with REST JSON as the contract.
  - The plan adds an ephemeral Bearer token pattern but does not include the canonical architecture doc, which still says UI-to-API localhost traffic requires no authentication.
  - The verification block contains non-runnable/weak checks (`rg ... docs/build-plan/06*.md`) and does not validate all stated deliverables.
- Coverage/test gaps:
  - No implementation exists yet, so this review is PASS_TO_PASS only.
  - Because `task.md` is missing, I could not verify plan/task alignment or task-row completeness beyond the failure itself.
- Evidence bundle location:
  - This handoff
- FAIL_TO_PASS / PASS_TO_PASS result:
  - PASS_TO_PASS only; no implementation under review
- Mutation score:
  - Not applicable
- Contract verification status:
  - `changes_required`

## Reviewer Output

- Findings by severity:
  - **High** — The target plan folder is structurally incomplete: `task.md` is missing entirely, so the plan fails the repo’s basic planning contract before any content review. The critical-review workflow requires plan-review scope to include both `implementation-plan.md` and `task.md` (`.agent/workflows/critical-review-feedback.md:119-120`, `.agent/workflows/critical-review-feedback.md:154`, `.agent/workflows/critical-review-feedback.md:354-357`), and `AGENTS.md` requires every plan task to carry `task`, `owner_role`, `deliverable`, `validation`, and `status` (`AGENTS.md:64-66`). In the live folder, `Get-ChildItem` shows only `implementation-plan.md`, and `Get-Content docs/execution/plans/2026-03-14-gui-shell-research-integration/task.md` fails because the file does not exist. As written, this plan cannot satisfy PR-1 or PR-3 at all.
  - **High** — The router migration scope leaves an existing broken navigation contract unresolved. The plan says the route paths “stay the same” and that `06a-gui-shell.md` only needs a TanStack Router import/comment change in the command registry (`docs/execution/plans/2026-03-14-gui-shell-research-integration/implementation-plan.md:127-153`). But current canon already disagrees about the route map: `06-gui.md` defines `/`, `/trades/*`, `/planning/*`, `/scheduling/*`, and `/settings/*` at `docs/build-plan/06-gui.md:139-144` and the rail table repeats `/planning` / `/scheduling` at `docs/build-plan/06-gui.md:192-196`, while `06a-gui-shell.md` still registers `/plans`, `/reports`, `/watchlists`, `/accounts`, and `/schedules` at `docs/build-plan/06a-gui-shell.md:207-225`. If implementation follows this plan literally, the new TanStack Router docs will still describe mutually incompatible paths and labels.
  - **High** — The plan reintroduces shared-schema coupling that conflicts with the adopted monorepo decision and current architecture. `patterns.md` is scoped to “React Hook Form + Zod schemas shared with MCP server” at `docs/execution/plans/2026-03-14-gui-shell-research-integration/implementation-plan.md:45`, but the GUI-shell synthesis explicitly decided against a shared workspace package: `ui/` and `mcp-server/` remain standalone packages, and “REST API IS the contract” at `_inspiration/electron_react_python_research/synthesis-final-decisions.md:114-129`. The local architecture doc matches that separation in `.agent/docs/architecture.md:44-45`. Without a new shared package and updated package-layout plan, “shared with MCP server” is an unsupported contract change rather than a harmless wording tweak.
  - **High** — The security decision is not propagated to all canonical docs, so the plan would leave the repo with contradictory UI↔API contracts. The proposed changes add an “Ephemeral Bearer Token” section to `06a-gui-shell.md` (`docs/execution/plans/2026-03-14-gui-shell-research-integration/implementation-plan.md:143-149`) and describe that same security pattern in `patterns.md` (`docs/execution/plans/2026-03-14-gui-shell-research-integration/implementation-plan.md:40`). But `.agent/docs/architecture.md`, which `AGENTS.md` treats as canonical context (`AGENTS.md:120`), still says “UI ↔ API: REST over localhost:8000 ... No authentication needed (local-only)” at `.agent/docs/architecture.md:68-69`. Because this plan claims to align the project’s canonical documentation, omitting the architecture update leaves a direct contradiction on a security-sensitive contract.
  - **Medium** — The verification plan is internally inconsistent and too weak to prove the intended changes. The plan adds a fifth research deliverable (`style-guide-zorivest.md`) at `docs/execution/plans/2026-03-14-gui-shell-research-integration/implementation-plan.md:164-232`, but automated check #2 still expects only four files at `docs/execution/plans/2026-03-14-gui-shell-research-integration/implementation-plan.md:247-249`, and manual verification also tells the user to review only “the 4 new research files” at `docs/execution/plans/2026-03-14-gui-shell-research-integration/implementation-plan.md:274-276`. The same block uses `rg -i ... docs/build-plan/06*.md` at `docs/execution/plans/2026-03-14-gui-shell-research-integration/implementation-plan.md:243-245`, which is not a runnable path form for `rg` in this PowerShell environment, and check #4 only looks for `React.lazy()` in `06-gui.md` at `docs/execution/plans/2026-03-14-gui-shell-research-integration/implementation-plan.md:255-257` even though the change risk also includes stale `<Routes>/<Route>` usage and the route-path drift in `06a-gui-shell.md`. This is not strong enough evidence for PR-4 or DR-4/DR-5.
  - **Medium** — Claim-to-state matching is already off before implementation starts. The plan marks `style-guide-zorivest.md` as a `[NEW]` deliverable at `docs/execution/plans/2026-03-14-gui-shell-research-integration/implementation-plan.md:164`, but that file already exists in the working tree at `docs/research/gui-shell-foundation/style-guide-zorivest.md:1`, and `git status --short` shows the whole `docs/research/` tree is currently untracked. That means the plan’s “new file” accounting and not-started readiness signal are already muddy: either this deliverable should be treated as existing/reused scope, or the folder state needs to be cleaned up before calling this an untouched pre-implementation plan.
  - **Medium** — The plan introduces many non-spec rules without the source-tag discipline required by repo canon. Examples include the ephemeral token/nonced startup contract (`implementation-plan.md:143-149`), TanStack Query hard-coded defaults (`implementation-plan.md:145`), React Compiler `useWatch()` guidance (`implementation-plan.md:147`), production `stdio: 'ignore'` / process-tree kill behavior (`implementation-plan.md:149`), and the cognitive-load protocol / WCAG tables in the style guide (`implementation-plan.md:168-232`). `AGENTS.md` requires non-spec rules to be tagged as `Spec`, `Local Canon`, `Research-backed`, or `Human-approved` (`AGENTS.md:66`), and the plan-review checklist repeats that requirement (`.agent/workflows/critical-review-feedback.md:277-278`, `.agent/workflows/critical-review-feedback.md:358`). This plan cites inspiration in prose, but it does not provide auditable source-basis tags for the actual rules an implementer would need to follow.
- Open questions:
  - Is the intent to keep the current “REST JSON is the contract” decision between `ui/` and `mcp-server/`, or does the project now want a new shared TypeScript package for Zod schemas? The plan needs to choose one explicitly.
  - Was `docs/research/gui-shell-foundation/style-guide-zorivest.md` intentionally pre-created before this review, or should the plan reclassify it from `[NEW]` to `[MODIFY]` / “existing deliverable”?
- Verdict:
  - `changes_required`
- Residual risk:
  - This was a plan-only review; no implementation code exists yet for the target folder. The main residual risk is that if implementation starts from this plan as written, the project will encode contradictory route maps, unclear cross-package contracts, and a split security story across canonical docs before the first GUI files even exist.
- Anti-deferral scan result:
  - No product code reviewed; no implementation deferrals assessed.

## Guardrail Output (If Required)

- Safety checks:
  - Not required for docs-only plan review
- Blocking risks:
  - None beyond the reviewer findings above
- Verdict:
  - Not applicable

## Approval Gate

- **Human approval required for merge/release/deploy:** yes
- **Approval status:** pending
- **Approver:**
- **Timestamp:**

## Final Summary

- Status:
  - Plan reviewed in pre-implementation mode; corrections required before execution
- Next steps:
  - Run `/planning-corrections` against `docs/execution/plans/2026-03-14-gui-shell-research-integration/`
  - Add the missing `task.md` with exact task rows and explicit `orchestrator → coder → tester → reviewer` ownership
  - Expand the scope to reconcile route/path contracts across `06-gui.md` and `06a-gui-shell.md`, not just swap router syntax
  - Decide whether shared UI/MCP Zod schemas are actually intended; if not, remove that rule, and if yes, add the missing package-structure/dependency plan
  - Include downstream canonical updates for the security contract, especially `.agent/docs/architecture.md`
  - Rewrite the verification block into exact, PowerShell-runnable commands that validate all stated deliverables

---

## Recheck — 2026-03-14

### Discovery

- Rechecked the updated `docs/execution/plans/2026-03-14-gui-shell-research-integration/implementation-plan.md` and new `task.md` against the prior findings in this rolling handoff.
- Scope remained plan-review mode:
  - no correlated work handoffs exist yet
  - the task file is present and all rows remain `not_started`
- Recheck focus:
  - whether the prior high blockers were actually corrected in plan state
  - whether the task contract and source-traceability now satisfy repo canon

### Commands Executed

- `Get-ChildItem docs/execution/plans/2026-03-14-gui-shell-research-integration`
- `Get-Content -Raw docs/execution/plans/2026-03-14-gui-shell-research-integration/implementation-plan.md`
- `Get-Content -Raw docs/execution/plans/2026-03-14-gui-shell-research-integration/task.md`
- `Get-Content -Raw .agent/context/handoffs/2026-03-14-gui-shell-research-integration-plan-critical-review.md`
- `Get-Content -Raw docs/build-plan/06-gui.md`
- `Get-Content -Raw docs/build-plan/06a-gui-shell.md`
- `Get-Content -Raw .agent/docs/architecture.md`
- `Get-Content -Raw docs/research/gui-shell-foundation/style-guide-zorivest.md`
- `git status --short -- docs/execution/plans/2026-03-14-gui-shell-research-integration docs/build-plan docs/research/gui-shell-foundation .agent/docs/architecture.md .agent/context/handoffs/2026-03-14-gui-shell-research-integration-plan-critical-review.md`
- `rg -n "Owner \||owner_role|source-tag|Spec|Local Canon|Research-backed|Human-approved|All non-spec rules|All 6 verification commands|All 7 verification commands|Codex verdict|route map|REST JSON is the contract|No authentication needed|EXISTING" docs/execution/plans/2026-03-14-gui-shell-research-integration/implementation-plan.md docs/execution/plans/2026-03-14-gui-shell-research-integration/task.md`
- `rg -n "navigate\('/|navigate\(`/|/planning|/plans|/scheduling|/schedules|/accounts|/watchlists|/reports|React\.lazy\(|<Routes|<Route " docs/build-plan/06-gui.md docs/build-plan/06a-gui-shell.md`
- `rg -n "No authentication needed|Bearer token|nonce|REST JSON is the contract|shared TypeScript package" docs/execution/plans/2026-03-14-gui-shell-research-integration/implementation-plan.md .agent/docs/architecture.md _inspiration/electron_react_python_research/synthesis-final-decisions.md`

### Recheck Findings

- **Medium** — The new `task.md` fixes the missing-file blocker, but it still does not meet the repo’s required task-contract shape. `AGENTS.md` requires every plan task to include `task`, `owner_role`, `deliverable`, `validation`, and `status` at [AGENTS.md](/p:/zorivest/AGENTS.md#L64), and the critical-review workflow repeats that same contract at [.agent/workflows/critical-review-feedback.md](/p:/zorivest/.agent/workflows/critical-review-feedback.md#L182) through [.agent/workflows/critical-review-feedback.md](/p:/zorivest/.agent/workflows/critical-review-feedback.md#L198). The new table still uses `Owner` instead of `owner_role` and every validation cell remains prose rather than exact commands in [task.md](/p:/zorivest/docs/execution/plans/2026-03-14-gui-shell-research-integration/task.md#L5) through [task.md](/p:/zorivest/docs/execution/plans/2026-03-14-gui-shell-research-integration/task.md#L28). Examples: “File exists, covers variations and edge cases”, “Line 68 updated”, and “Review handoff filed” are check criteria, not runnable validations. That means PR-3/PR-4 are still not fully satisfied.

- **Medium** — Source-traceability is still asserted generically rather than attached to the concrete non-spec rules the plan adds. The updated plan now says non-spec rules “must” be tagged at [implementation-plan.md](/p:/zorivest/docs/execution/plans/2026-03-14-gui-shell-research-integration/implementation-plan.md#L63) and expects source tags in Codex validation at [implementation-plan.md](/p:/zorivest/docs/execution/plans/2026-03-14-gui-shell-research-integration/implementation-plan.md#L303). But the actual added rules are still untagged in the plan body: the ephemeral Bearer token contract, TanStack Query defaults, `useWatch()` guidance, `stdio: 'ignore'`, and Windows process-tree kill behavior are all specified as plan requirements in [implementation-plan.md](/p:/zorivest/docs/execution/plans/2026-03-14-gui-shell-research-integration/implementation-plan.md#L150) through [implementation-plan.md](/p:/zorivest/docs/execution/plans/2026-03-14-gui-shell-research-integration/implementation-plan.md#L158) without per-rule `Spec` / `Local Canon` / `Research-backed` / `Human-approved` labeling. Under [AGENTS.md](/p:/zorivest/AGENTS.md#L66) and the plan-review checklist at [.agent/workflows/critical-review-feedback.md](/p:/zorivest/.agent/workflows/critical-review-feedback.md#L277) through [.agent/workflows/critical-review-feedback.md](/p:/zorivest/.agent/workflows/critical-review-feedback.md#L278), that traceability is still incomplete.

- **Low** — The task file’s verification count is stale. The implementation plan now defines seven automated checks at [implementation-plan.md](/p:/zorivest/docs/execution/plans/2026-03-14-gui-shell-research-integration/implementation-plan.md#L265) through [implementation-plan.md](/p:/zorivest/docs/execution/plans/2026-03-14-gui-shell-research-integration/implementation-plan.md#L290), but task row 11 still says “All 6 verification commands pass” at [task.md](/p:/zorivest/docs/execution/plans/2026-03-14-gui-shell-research-integration/task.md#L27). This is a minor evidence-freshness defect, but it shows the task file and implementation plan are not fully synchronized yet.

### Recheck Result

- Resolved since the first pass:
  - `task.md` now exists
  - the route-map drift is now explicitly in scope, with `06-gui.md` designated as the canonical map
  - the shared-schema claim was corrected to keep REST JSON as the contract
  - the architecture doc update is now explicitly in scope
  - the style-guide deliverable is correctly treated as an existing file
  - the verification block now uses concrete PowerShell-friendly commands
- Remaining verdict:
  - `changes_required`

### Next Actions

- Change the `task.md` table to use the required `owner_role` field name and replace prose validation cells with exact commands.
- Make the task rows point to the actual verification commands already listed in `implementation-plan.md`.
- Add source-basis tags to the concrete non-spec rules introduced by the plan, not just a generic reminder that tags are required.
- Update task row 11 so its command count matches the current seven-command verification block.

---

## Recheck 2 — 2026-03-14

### Discovery

- Rechecked the latest plan revision after the previous pass narrowed the issues to task-contract rigor and source-traceability.
- Scope remained plan-review mode:
  - no correlated work handoffs exist yet
  - both `implementation-plan.md` and `task.md` are present and remain `not_started`
- Recheck focus:
  - whether `task.md` now uses the required `owner_role` + exact validation-command structure
  - whether the remaining plan-level non-spec rules now carry allowed source-basis tags

### Commands Executed

- `Get-ChildItem docs/execution/plans/2026-03-14-gui-shell-research-integration`
- `Get-Content -Raw docs/execution/plans/2026-03-14-gui-shell-research-integration/implementation-plan.md`
- `Get-Content -Raw docs/execution/plans/2026-03-14-gui-shell-research-integration/task.md`
- `Get-Content -Raw .agent/context/handoffs/2026-03-14-gui-shell-research-integration-plan-critical-review.md`
- `git status --short -- docs/execution/plans/2026-03-14-gui-shell-research-integration .agent/context/handoffs/2026-03-14-gui-shell-research-integration-plan-critical-review.md`
- `rg -n "owner_role|Validation \||returns ≥1 result|Review handoff filed|paths match|All 7 verification commands pass" docs/execution/plans/2026-03-14-gui-shell-research-integration/task.md`
- `rg -n "\[Research-backed|\[Local Canon|\[Spec|\[Human-approved|Canonical decision:|This resolves the contradiction|source-basis tagged per AGENTS.md" docs/execution/plans/2026-03-14-gui-shell-research-integration/implementation-plan.md`
- `Get-Content AGENTS.md`
- `Get-Content .agent/workflows/critical-review-feedback.md`

### Recheck 2 Findings

- **Medium** — `task.md` now uses `owner_role`, but the validation contract is still not fully exact-command based. The repo requires `validation` to be exact commands at [AGENTS.md](/p:/zorivest/AGENTS.md#L64) and [.agent/workflows/critical-review-feedback.md](/p:/zorivest/.agent/workflows/critical-review-feedback.md#L182) through [.agent/workflows/critical-review-feedback.md](/p:/zorivest/.agent/workflows/critical-review-feedback.md#L198). Several rows are now much better, but not all the way there: row 9 still ends with the prose check “paths match `06-gui.md` nav rail” after the command in [task.md](/p:/zorivest/docs/execution/plans/2026-03-14-gui-shell-research-integration/task.md#L20), and row 12 still uses “Review handoff filed at `.agent/context/handoffs/`” instead of an exact validation command in [task.md](/p:/zorivest/docs/execution/plans/2026-03-14-gui-shell-research-integration/task.md#L28). That means PR-4 is improved but not fully closed.

- **Medium** — Source-tagging is improved, but the plan still leaves at least two plan-level non-spec decisions untagged. The new 06a subsection list is properly tagged at [implementation-plan.md](/p:/zorivest/docs/execution/plans/2026-03-14-gui-shell-research-integration/implementation-plan.md#L150) through [implementation-plan.md](/p:/zorivest/docs/execution/plans/2026-03-14-gui-shell-research-integration/implementation-plan.md#L158), which resolves most of the prior traceability issue. But the route-map rule “Adopt `06-gui.md`'s nav rail as the master route map” remains untagged at [implementation-plan.md](/p:/zorivest/docs/execution/plans/2026-03-14-gui-shell-research-integration/implementation-plan.md#L137), and the architecture/security correction rationale remains untagged at [implementation-plan.md](/p:/zorivest/docs/execution/plans/2026-03-14-gui-shell-research-integration/implementation-plan.md#L175). Under [AGENTS.md](/p:/zorivest/AGENTS.md#L66) and the plan-review checklist at [.agent/workflows/critical-review-feedback.md](/p:/zorivest/.agent/workflows/critical-review-feedback.md#L277) through [.agent/workflows/critical-review-feedback.md](/p:/zorivest/.agent/workflows/critical-review-feedback.md#L278), those remaining plan-level rules still need an allowed source basis.

### Recheck 2 Result

- Resolved since the prior pass:
  - `task.md` now uses `owner_role`
  - task row 11 now matches the seven-command verification block
  - most of the 06a non-spec additions now carry explicit source-basis tags
- Remaining verdict:
  - `changes_required`

### Next Actions

- Convert the remaining mixed prose validations in `task.md` into exact validation commands.
- Add explicit source-basis tags to the route-map canonical decision and the architecture/security correction rationale in `implementation-plan.md`.

---

## Recheck 3 — 2026-03-14

### Discovery

- Rechecked the latest revision after the prior pass narrowed the issues to validation-command rigor and remaining source provenance.
- Scope remained plan-review mode:
  - no correlated work handoffs exist yet
  - both `implementation-plan.md` and `task.md` are present and remain `not_started`
- Recheck focus:
  - whether the task validations are now exact and runnable in the local PowerShell environment
  - whether the new `Human-approved` tag on the Bearer-token architecture note is backed by an explicit local user decision

### Commands Executed

- `Get-Content docs/execution/plans/2026-03-14-gui-shell-research-integration/task.md`
- `Get-Content docs/execution/plans/2026-03-14-gui-shell-research-integration/implementation-plan.md`
- `Get-Content .agent/workflows/create-plan.md`
- `Get-Content _inspiration/electron_react_python_research/synthesis-final-decisions.md`
- `Test-Path .agent\context\handoffs\*gui-shell-research-integration*`
- `rg "verdict" .agent\context\handoffs\*gui-shell*`
- `rg -n "accepted Bearer token|User confirmed|explicit user decision|Bearer token" .agent docs _inspiration -g "*.md"`

### Recheck 3 Findings

- **Medium** — The task table still does not provide fully exact, runnable validation commands. Repo canon requires `validation` to use exact commands at [AGENTS.md](/p:/zorivest/AGENTS.md#L64) and [.agent/workflows/critical-review-feedback.md](/p:/zorivest/.agent/workflows/critical-review-feedback.md#L182) through [.agent/workflows/critical-review-feedback.md](/p:/zorivest/.agent/workflows/critical-review-feedback.md#L198). Two problems remain in [task.md](/p:/zorivest/docs/execution/plans/2026-03-14-gui-shell-research-integration/task.md#L27): row 11 still uses prose instead of commands (`All 7 verification commands in implementation-plan.md §Automated Checks pass`), and row 12 includes `rg "verdict" .agent\context\handoffs\*gui-shell*`, which fails in this shell with `os error 123` rather than producing a valid check. That means the task contract is still not review-ready.

- **Medium** — The new `Human-approved` source tag on the architecture/security rationale still appears unsupported by the local evidence. The plan now states `[Research-backed: Gemini §Security Architecture; Human-approved: user accepted Bearer token in synthesis review]` at [implementation-plan.md](/p:/zorivest/docs/execution/plans/2026-03-14-gui-shell-research-integration/implementation-plan.md#L175). But the planning workflow defines `Human-approved` as a rule resolved by explicit user decision at [.agent/workflows/create-plan.md](/p:/zorivest/.agent/workflows/create-plan.md#L81). I rechecked the local synthesis artifact: [synthesis-final-decisions.md](/p:/zorivest/_inspiration/electron_react_python_research/synthesis-final-decisions.md#L56) records the Bearer token as an “Adopt Now” research recommendation, while explicit `User confirmed` markers appear for Router at [synthesis-final-decisions.md](/p:/zorivest/_inspiration/electron_react_python_research/synthesis-final-decisions.md#L102) through [synthesis-final-decisions.md](/p:/zorivest/_inspiration/electron_react_python_research/synthesis-final-decisions.md#L104), not for the Bearer-token choice. Without an independent approval artifact, that source label is still overstated.

### Recheck 3 Result

- Resolved since the prior pass:
  - the route-map canonical decision now carries an allowed `Local Canon` tag
  - the architecture-correction note is now source-tagged instead of untagged
- Remaining verdict:
  - `changes_required`

### Next Actions

- Replace task row 11 with the exact commands from `implementation-plan.md` or a single exact command wrapper that executes those checks.
- Rewrite task row 12 so it uses a PowerShell-runnable validation command instead of an `rg` wildcard path that errors on Windows.
- Either remove the `Human-approved` portion of the Bearer-token rationale or add an explicit local approval artifact that actually shows the user decision.

---

## Recheck 4 — 2026-03-14

### Discovery

- Rechecked the same plan folder after the last pass identified two remaining issues: non-runnable handoff validation and unsupported `Human-approved` provenance.
- Scope remained plan-review mode:
  - no correlated work handoffs exist yet
  - both `implementation-plan.md` and `task.md` are present and remain `not_started`
- Recheck focus:
  - whether the task-table validations are now fully exact and runnable
  - whether the architecture/security source tag is now defensible

### Commands Executed

- `Get-ChildItem docs/execution/plans/2026-03-14-gui-shell-research-integration | Select-Object Name,Length,LastWriteTime`
- `Get-Content docs/execution/plans/2026-03-14-gui-shell-research-integration/task.md`
- `Get-Content docs/execution/plans/2026-03-14-gui-shell-research-integration/implementation-plan.md`
- `Get-Content .agent/workflows/create-plan.md`
- `Get-Content _inspiration/electron_react_python_research/synthesis-final-decisions.md`
- `Test-Path .agent\context\handoffs\*gui-shell-research-integration*`
- `rg "verdict" .agent\context\handoffs\*gui-shell*`
- `Get-Content AGENTS.md`
- `Get-Content .agent/workflows/critical-review-feedback.md`

### Recheck 4 Findings

- **Medium** — The validation contract is improved but still not fully exact-command based. Repo canon requires `validation` to be exact commands at [AGENTS.md](/p:/zorivest/AGENTS.md#L64) and [.agent/workflows/critical-review-feedback.md](/p:/zorivest/.agent/workflows/critical-review-feedback.md#L182) through [.agent/workflows/critical-review-feedback.md](/p:/zorivest/.agent/workflows/critical-review-feedback.md#L198). The previous handoff-file check is now fixed in [task.md](/p:/zorivest/docs/execution/plans/2026-03-14-gui-shell-research-integration/task.md#L28), and the unsupported `Human-approved` tag is gone from [implementation-plan.md](/p:/zorivest/docs/execution/plans/2026-03-14-gui-shell-research-integration/implementation-plan.md#L175). But the route-consistency check still depends on manual interpretation rather than a deterministic command: [implementation-plan.md](/p:/zorivest/docs/execution/plans/2026-03-14-gui-shell-research-integration/implementation-plan.md#L285) through [implementation-plan.md](/p:/zorivest/docs/execution/plans/2026-03-14-gui-shell-research-integration/implementation-plan.md#L287) say `rg "navigate\(" docs\build-plan\06a-gui-shell.md` with the expected result “all navigate() paths match 06-gui.md nav rail table,” and task row 11 inherits that same non-exact check at [task.md](/p:/zorivest/docs/execution/plans/2026-03-14-gui-shell-research-integration/task.md#L27). That still leaves a reviewer to eyeball path correctness instead of relying on exact command output.

### Recheck 4 Result

- Resolved since the prior pass:
  - task row 12 now uses a runnable `Get-ChildItem` + `Select-String` handoff check instead of the failing wildcard `rg` path
  - the architecture/security rationale no longer overstates its provenance with an unsupported `Human-approved` tag
- Remaining verdict:
  - `changes_required`

### Next Actions

- Replace the route-consistency check with an exact command that proves the allowed paths and/or proves stale `/plans`, `/schedules`, `/accounts`, `/reports`, and `/watchlists` route entries are absent.
- Update task row 11 to point at that deterministic command set instead of the current human-interpreted `navigate()` dump.

---

## Recheck 5 — 2026-03-14

### Discovery

- Rechecked the same plan folder after the last pass identified only one remaining blocker: exact-command rigor in the task-table validations.
- Scope remained plan-review mode:
  - no correlated work handoffs exist yet
  - both `implementation-plan.md` and `task.md` are present and remain `not_started`
- Recheck focus:
  - whether the route-consistency validation is now deterministic
  - whether the `task.md` validation commands are actually runnable as written

### Commands Executed

- `Get-ChildItem docs/execution/plans/2026-03-14-gui-shell-research-integration | Select-Object Name,Length,LastWriteTime`
- `Get-Content docs/execution/plans/2026-03-14-gui-shell-research-integration/task.md`
- `Get-Content docs/execution/plans/2026-03-14-gui-shell-research-integration/implementation-plan.md`
- `'zustand' | rg "zustand\|foo"`
- `'zustand' | rg "zustand|foo"`

### Recheck 5 Findings

- **Medium** — The remaining blocker is now the task table’s command encoding, not the route check itself. The route-consistency validation is now deterministic in [implementation-plan.md](/p:/zorivest/docs/execution/plans/2026-03-14-gui-shell-research-integration/implementation-plan.md#L285) through [implementation-plan.md](/p:/zorivest/docs/execution/plans/2026-03-14-gui-shell-research-integration/implementation-plan.md#L287), so the prior manual-interpretation issue is resolved. But [task.md](/p:/zorivest/docs/execution/plans/2026-03-14-gui-shell-research-integration/task.md#L8), [task.md](/p:/zorivest/docs/execution/plans/2026-03-14-gui-shell-research-integration/task.md#L9), [task.md](/p:/zorivest/docs/execution/plans/2026-03-14-gui-shell-research-integration/task.md#L18), [task.md](/p:/zorivest/docs/execution/plans/2026-03-14-gui-shell-research-integration/task.md#L19), [task.md](/p:/zorivest/docs/execution/plans/2026-03-14-gui-shell-research-integration/task.md#L20), [task.md](/p:/zorivest/docs/execution/plans/2026-03-14-gui-shell-research-integration/task.md#L21), and [task.md](/p:/zorivest/docs/execution/plans/2026-03-14-gui-shell-research-integration/task.md#L27) still use markdown-escaped `\|` inside `rg` alternation patterns. Under [AGENTS.md](/p:/zorivest/AGENTS.md#L64) and [.agent/workflows/critical-review-feedback.md](/p:/zorivest/.agent/workflows/critical-review-feedback.md#L182) through [.agent/workflows/critical-review-feedback.md](/p:/zorivest/.agent/workflows/critical-review-feedback.md#L198), those are not exact commands as written. I verified the regex effect directly: `'zustand' | rg "zustand\|foo"` returns no match, while `'zustand' | rg "zustand|foo"` matches `zustand`. That means the task-table validations still change command semantics just to satisfy Markdown table escaping.

### Recheck 5 Result

- Resolved since the prior pass:
  - the route-consistency check is now deterministic and no longer depends on manual interpretation
- Remaining verdict:
  - `changes_required`

### Next Actions

- Rewrite the `task.md` validation cells so `rg` alternation commands remain literal exact commands rather than markdown-escaped variants.
- Prefer fenced command blocks or another representation that preserves raw `|` characters without changing regex behavior.

---

## Recheck 6 — 2026-03-14

### Discovery

- Rechecked the same plan folder after the last pass identified only one remaining blocker: markdown-escaped regex alternation in `task.md` validation commands.
- Scope remained plan-review mode:
  - no correlated work handoffs exist yet
  - both `implementation-plan.md` and `task.md` are present and remain `not_started`
- Recheck focus:
  - whether the task validations now preserve raw command text without Markdown-induced regex changes
  - whether any prior blocker still reproduces in the current plan state

### Commands Executed

- `Get-ChildItem docs/execution/plans/2026-03-14-gui-shell-research-integration | Select-Object Name,Length,LastWriteTime`
- `Get-Content docs/execution/plans/2026-03-14-gui-shell-research-integration/task.md`
- `Get-Content docs/execution/plans/2026-03-14-gui-shell-research-integration/implementation-plan.md`
- `'zustand' | rg "zustand|foo"`
- `'Research-backed' | rg "Research-backed|Local Canon|Spec|Human-approved"`
- `rg -n "\\\\\|" docs/execution/plans/2026-03-14-gui-shell-research-integration/task.md`

### Recheck 6 Findings

- No findings. The task list now preserves exact `rg` alternation patterns using fenced command blocks instead of Markdown-table escaping, and the previous `\|` regex corruption no longer appears in [task.md](/p:/zorivest/docs/execution/plans/2026-03-14-gui-shell-research-integration/task.md#L19) through [task.md](/p:/zorivest/docs/execution/plans/2026-03-14-gui-shell-research-integration/task.md#L165). The last reproduced blocker from Recheck 5 is resolved.

### Recheck 6 Result

- Resolved since the prior pass:
  - the remaining exact-command issue is fixed
  - no prior blocker still reproduces in the current plan/task state
- Current verdict:
  - `approved`
