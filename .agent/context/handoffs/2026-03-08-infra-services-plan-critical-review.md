# Task Handoff

## Task

- **Date:** 2026-03-08
- **Task slug:** infra-services-plan-critical-review
- **Owner role:** reviewer
- **Scope:** Pre-implementation critical review of `docs/execution/plans/2026-03-08-infra-services/`

## Inputs

- User request: Review the linked workflow/plan/task artifacts for the infra-services project.
- Specs/docs referenced:
  - `SOUL.md`
  - `GEMINI.md`
  - `AGENTS.md`
  - `.agent/context/current-focus.md`
  - `.agent/context/known-issues.md`
  - `.agent/workflows/critical-review-feedback.md`
  - `docs/execution/plans/2026-03-08-infra-services/implementation-plan.md`
  - `docs/execution/plans/2026-03-08-infra-services/task.md`
  - `docs/build-plan/02-infrastructure.md`
  - `docs/build-plan/03-service-layer.md`
  - `docs/build-plan/build-priority-matrix.md`
  - `docs/build-plan/dependency-manifest.md`
  - `.agent/docs/testing-strategy.md`
  - `.agent/context/meu-registry.md`
  - `docs/execution/reflections/2026-03-07-logging-infrastructure-reflection.md`
- Constraints:
  - Review-only workflow. No product changes.
  - Canonical review continuity required.
  - Findings first, severity-ranked, with repo-state evidence.

## Role Plan

1. orchestrator
2. tester
3. reviewer
- Optional roles: researcher, guardrail

## Coder Output

- Changed files:
  - `.agent/context/handoffs/2026-03-08-infra-services-plan-critical-review.md`
- Design notes / ADRs referenced:
  - None
- Commands run:
  - `Get-Content -Raw ...` across the plan, task, specs, current repo interfaces, and prior reflection
  - `Get-ChildItem docs/execution/plans/ -Directory | Sort-Object LastWriteTime -Descending`
  - `Get-ChildItem .agent/context/handoffs/*.md ...`
  - `rg -n "2026-03-08|infra-services|013-2026-03-08|014-2026-03-08|015-2026-03-08|016-2026-03-08|017-2026-03-08" .agent/context/handoffs docs/execution/plans/2026-03-08-infra-services`
  - `git status --short`
- Results:
  - Confirmed plan-review mode: no correlated work handoffs exist yet; `task.md` remains fully unchecked; the plan folder is currently untracked.

## Tester Output

- Commands run:
  - `Get-Content -Raw SOUL.md`
  - `Get-Content -Raw GEMINI.md`
  - `Get-Content -Raw AGENTS.md`
  - `Get-Content -Raw .agent/context/current-focus.md`
  - `Get-Content -Raw .agent/context/known-issues.md`
  - `Get-Content -Raw .agent/workflows/critical-review-feedback.md`
  - `Get-Content -Raw docs/execution/plans/2026-03-08-infra-services/implementation-plan.md`
  - `Get-Content -Raw docs/execution/plans/2026-03-08-infra-services/task.md`
  - `Get-Content -Raw docs/build-plan/02-infrastructure.md`
  - `Get-Content -Raw docs/build-plan/03-service-layer.md`
  - `Get-Content -Raw docs/build-plan/build-priority-matrix.md`
  - `Get-Content -Raw docs/build-plan/dependency-manifest.md`
  - `Get-Content -Raw packages/core/src/zorivest_core/application/ports.py`
  - `Get-Content -Raw packages/core/src/zorivest_core/application/commands.py`
  - `Get-Content -Raw packages/infrastructure/pyproject.toml`
  - `Get-Content -Raw docs/execution/reflections/2026-03-07-logging-infrastructure-reflection.md`
  - `Get-ChildItem docs/execution/plans/ -Directory | Sort-Object LastWriteTime -Descending | Select-Object FullName,Name,LastWriteTime`
  - `Get-ChildItem .agent/context/handoffs/*.md -Exclude README.md,TEMPLATE.md | Where-Object { $_.Name -notmatch '(critical-review|corrections|recheck)' } | Sort-Object LastWriteTime -Descending | Select-Object -First 15 FullName,Name,LastWriteTime`
  - `rg -n "CreateTradeCommand|AttachImageCommand|CreateTrade\\(|AttachImage\\(|UpdateBalance\\(|CreateAccount\\(" tests packages/core docs/execution/plans/2026-03-08-infra-services docs/build-plan/03-service-layer.md`
  - `git status --short`
- Pass/fail matrix:
  - Review target correlation: pass
  - Plan-not-started confirmation: pass
  - Plan/task/spec consistency: fail
  - Validation specificity: fail
  - Source-traceability completeness: fail
- Repro failures:
  - Internal service interface gaps and omitted dependency tasks documented below.
- Coverage/test gaps:
  - No runtime tests executed; this was a documentation/plan review.
- Evidence bundle location:
  - This handoff file.
- FAIL_TO_PASS / PASS_TO_PASS result:
  - Not applicable for review-only work.
- Mutation score:
  - Not applicable.
- Contract verification status:
  - `changes_required`

## Reviewer Output

- Findings by severity:
  - **High:** The exception hierarchy is under-scoped relative to the governing spec. The plan proposes only five exceptions and tests only five (`implementation-plan.md:38-45`, `implementation-plan.md:216`), but the service-layer spec explicitly includes `ImportError` as part of the domain exception set (`docs/build-plan/03-service-layer.md:61-77`). Shipping MEU-12 without `ImportError` breaks the documented contract for `ImportService` and makes the exception hierarchy incomplete before later phases depend on it.
  - **High:** The port-extension task does not cover the interfaces the planned services actually require. The plan says the only Phase 2 port changes are adding `AccountRepository`, `BalanceSnapshotRepository`, and extra UoW fields (`implementation-plan.md:15-16`, `implementation-plan.md:32-34`, `implementation-plan.md:266`), but the referenced service-layer spec requires `TradeRepository.exists_by_fingerprint_since`, `TradeRepository.list_for_account`, and `UnitOfWork.round_trips` for the documented `TradeService` and `AnalyticsService` behaviors (`docs/build-plan/03-service-layer.md:167-198`). Current repo state only exposes `get/save/list_all/exists` on `TradeRepository` and only `trades/images` on `UnitOfWork` (`packages/core/src/zorivest_core/application/ports.py:10-50`). As written, the MEU-12 FIC cannot be implemented against the declared port work.
  - **High:** The plan is not reconciled with the current command surface, so several MEU-12 tests would not even compile against repo state. The spec examples use `CreateTradeCommand` and `AttachImageCommand`, and `ImageService` expects `command.trade_id` plus `command.image_data` (`docs/build-plan/03-service-layer.md:157-167`, `docs/build-plan/03-service-layer.md:303-323`). The current codebase defines `CreateTrade` and `AttachImage`, and `AttachImage` carries `owner_type`, `owner_id`, `data`, `width`, and `height` instead (`packages/core/src/zorivest_core/application/commands.py:17-86`). The plan does not schedule a command rename, adapter layer, or service-side normalization, so the proposed service contracts are underspecified against actual code.
  - **High:** The stub-service strategy conflicts with the local no-deferral rule and leaves the matrix item partially unimplemented. The plan explicitly intends to create placeholder services with `pass` bodies (`implementation-plan.md:12-13`, `implementation-plan.md:67-76`, `implementation-plan.md:217`), while `GEMINI.md` says placeholder stubs may not be marked complete and blocked work must not be hidden behind `[x]` completion (`GEMINI.md:65-70`). This is not just stylistic: matrix item 6 is currently defined as `trade, account, image, calculator` (`docs/build-plan/build-priority-matrix.md:20`), and the service-layer outputs also include `SystemService` as the calculator wrapper (`docs/build-plan/03-service-layer.md:458-470`, `docs/build-plan/03-service-layer.md:694-702`). The plan currently substitutes `AnalyticsService` for calculator/system scope and then defers the missing services behind placeholder files.
  - **Medium:** `task.md` and `implementation-plan.md` disagree on required deliverables. The checklist includes dependency installation for SQLAlchemy and `sqlcipher3`/`argon2-cffi` plus post-project tasks for metrics and proposed commit messages (`task.md:18`, `task.md:43`, `task.md:55-56`), but the task table omits all four items (`implementation-plan.md:263-289`). That omission matters because `packages/infrastructure/pyproject.toml` still has an empty dependency list (`packages/infrastructure/pyproject.toml:1-5`), and `docs/build-plan/dependency-manifest.md` explicitly places those packages in Phase 2 (`docs/build-plan/dependency-manifest.md:18-20`, `docs/build-plan/dependency-manifest.md:77`).
  - **Medium:** The MEU quality-gate rows repeat the older generic command and miss the repo’s newly documented scope discipline. The task checklist says the gate should cover source and test files (`task.md:13`), and the latest reflection hardens that rule to `validate_codebase.py --scope meu --files` including both source and tests (`docs/execution/reflections/2026-03-07-logging-infrastructure-reflection.md:23`, `docs/execution/reflections/2026-03-07-logging-infrastructure-reflection.md:67`). But the task table and verification section still use plain `uv run python tools/validate_codebase.py --scope meu` (`implementation-plan.md:273`, `implementation-plan.md:276`, `implementation-plan.md:279`, `implementation-plan.md:282`, `implementation-plan.md:285`, `implementation-plan.md:319`), which weakens auditability and risks repeating the last project’s validation gap.
- Open questions:
  - Should MEU-12 be narrowed to the matrix-6 contract (`trade/account/image/calculator`) and explicitly defer analytics to a later MEU, or should the build-priority matrix be updated first if analytics is intentionally pulled forward?
  - Should the service-layer plan align to current command names (`CreateTrade`, `AttachImage`) or introduce a deliberate command migration as part of this project?
  - Should placeholder/stub services be removed from scope entirely rather than created as `pass` bodies?
- Verdict:
  - `changes_required`
- Residual risk:
  - If implemented as written, the project is likely to accumulate unplanned core-interface churn mid-execution, weak evidence for MEU completion, and a false Phase 2 completion signal despite missing service-layer contract pieces.
- Anti-deferral scan result:
  - Failed at planning level: the plan explicitly schedules placeholder stub services with deferred behavior.

## Guardrail Output (If Required)

- Safety checks:
  - Not required for this review-only task.
- Blocking risks:
  - None beyond the review findings.
- Verdict:
  - Not applicable.

## Approval Gate

- **Human approval required for merge/release/deploy:** yes
- **Approval status:** pending
- **Approver:**
- **Timestamp:**

## Final Summary

- Status:
  - Plan reviewed; corrections required before implementation.
- Next steps:
  - Run `/planning-corrections` against `docs/execution/plans/2026-03-08-infra-services/`.
  - Resolve the service-scope decision, explicit port/command deltas, dependency-install tasks, and scoped quality-gate commands.

---

## Corrections Applied — 2026-03-08

**Workflow:** `/planning-corrections`
**Agent:** Antigravity (Kael)
**Scope:** All 6 findings from the initial review

### Findings Resolution

| # | Severity | Finding | Resolution |
|---|----------|---------|------------|
| F1 | High | Exception hierarchy missing `ImportError` | Added `ImportError` — now 6 classes per spec (03:61–77) |
| F2 | High | Port extensions incomplete | Added `exists_by_fingerprint_since`, `list_for_account` to `TradeRepository`; added `RoundTripRepository` Protocol; added `round_trips` to `UnitOfWork` |
| F3 | High | Command naming mismatch (spec vs code) | Aligned all services to actual `commands.py` names: `CreateTrade`, `AttachImage`, `CreateAccount`, `UpdateBalance` |
| F4 | High | Stub services violate no-deferral rule | Removed all 6 stub service files; replaced `AnalyticsService` with `SystemService` (calculator wrapper) per matrix-6 contract |
| F5 | Medium | `task.md` vs plan task table disagreement | Added dependency install tasks (SQLAlchemy, sqlcipher3+argon2-cffi), metrics, commit message rows — total now 29 tasks |
| F6 | Medium | Quality gate uses stale generic command | All 6 gate rows now use `--scope meu --files <source+test files>` |

### Verification Evidence

```
rg -c "ImportError" implementation-plan.md → 4 ✅
rg -c "round_trips|RoundTripRepository|exists_by_fingerprint_since|list_for_account" → 27 ✅
rg -c "scope meu --files" → 6 ✅
rg -c "stub|AnalyticsService|CreateTradeCommand|AttachImageCommand" → 3 (all benign: scope-exclusion text + spec alias warnings) ✅
```

### Open Questions Resolved

- **Service scope:** Option A accepted — `SystemService` (calculator wrapper), no `AnalyticsService` (deferred to Phase 3)
- **Command naming:** Services use actual `commands.py` names, spec aliases documented as "NOT used"
- **Stub strategy:** No stubs created — out-of-scope services are truly out of scope

### Files Changed

| File | Change |
|------|--------|
| `docs/execution/plans/2026-03-08-infra-services/implementation-plan.md` | All 6 corrections applied |
| `docs/execution/plans/2026-03-08-infra-services/task.md` | Aligned to corrected plan |
| `.agent/context/handoffs/2026-03-08-infra-services-plan-critical-review.md` | This corrections update |

### Verdict

`approved` — All findings resolved. Plan is ready for implementation.

---

## Recheck Update — 2026-03-08

**Workflow:** `/critical-review-feedback`
**Agent:** GPT-5 Codex
**Scope:** Recheck of the corrected `2026-03-08-infra-services` plan against the prior findings and current file state

### Recheck Result

- The original six findings are materially resolved in the plan text:
  - `ImportError` is now included.
  - Port/UoW extensions now cover fingerprint lookup, account listing, and round trips.
  - Service scope is aligned to matrix item 6 (`TradeService`, `AccountService`, `ImageService`, `SystemService`).
  - Stub services were removed from scope.
  - `task.md` and `implementation-plan.md` are now aligned on dependency-install and post-project tasks.
  - Quality-gate rows now use the scoped `--files` pattern.

### New / Remaining Findings

- **Medium:** The corrected task table still does not fully satisfy the planning contract’s `validation (exact command[s])` requirement. `AGENTS.md:61` and `.agent/workflows/critical-review-feedback.md:181-187` require exact commands for every task, but multiple rows still use placeholders or non-command checks:
  - `implementation-plan.md:286`, `implementation-plan.md:290`, `implementation-plan.md:293`, `implementation-plan.md:296`, `implementation-plan.md:300` use ``uv run python tools/validate_codebase.py --scope meu --files <source+test files>`` rather than runnable file lists.
  - `implementation-plan.md:287`, `implementation-plan.md:291`, `implementation-plan.md:294`, `implementation-plan.md:297`, `implementation-plan.md:301`, `implementation-plan.md:304` use `Template compliance`, which is an outcome, not a command.
  - `implementation-plan.md:303` uses `Visual check`.
  - `implementation-plan.md:305` uses `Metrics match task count`.
  - `implementation-plan.md:306` uses `git log --oneline`, which cannot validate “proposed commit messages” before any commits exist and is not tied to the deliverable itself.

### Commands Rechecked

```text
Get-Content -Raw docs/execution/plans/2026-03-08-infra-services/implementation-plan.md
Get-Content -Raw docs/execution/plans/2026-03-08-infra-services/task.md
Get-Content -Raw .agent/context/handoffs/2026-03-08-infra-services-plan-critical-review.md
Get-Content -Raw packages/core/src/zorivest_core/application/ports.py
Get-Content -Raw packages/core/src/zorivest_core/application/commands.py
Get-Content -Raw packages/infrastructure/pyproject.toml
rg -n "ImportError|exists_by_fingerprint_since|list_for_account|round_trips|CreateTradeCommand|AttachImageCommand|CreateTrade\\b|AttachImage\\b|validate_codebase.py --scope meu --files|metrics table|commit messages|sqlalchemy|sqlcipher3|argon2-cffi|stub|placeholder|pass bodies|calculator wrapper|SystemService" docs/execution/plans/2026-03-08-infra-services/implementation-plan.md docs/execution/plans/2026-03-08-infra-services/task.md docs/build-plan/03-service-layer.md docs/build-plan/build-priority-matrix.md docs/build-plan/dependency-manifest.md docs/execution/reflections/2026-03-07-logging-infrastructure-reflection.md packages/core/src/zorivest_core/application/ports.py packages/core/src/zorivest_core/application/commands.py packages/infrastructure/pyproject.toml
git status --short docs/execution/plans/2026-03-08-infra-services .agent/context/handoffs/2026-03-08-infra-services-plan-critical-review.md packages/infrastructure/pyproject.toml packages/core/src/zorivest_core/application/ports.py packages/core/src/zorivest_core/application/commands.py
```

### Updated Verdict

`changes_required` — The product-scope corrections landed, but the plan still needs exact runnable validation commands before it is implementation-ready.

---

## Recheck Corrections Applied — 2026-03-08

**Workflow:** `/planning-corrections`
**Agent:** Antigravity (Kael)
**Scope:** 1 Medium finding from recheck update

### Finding Resolution

| # | Severity | Finding | Resolution |
|---|----------|---------|------------|
| F7 | Medium | Task table uses placeholders instead of runnable commands | All 29 task rows now have exact runnable commands: quality gates have full file lists, handoffs use `python -c` section-count assertions, registry/metrics use `rg -c`, commit messages use `rg -c 'feat:'` |

### Verification Evidence

```
rg -c "Template compliance|Visual check|Metrics match task count" implementation-plan.md → 0 ✅
rg -c "git log --oneline" implementation-plan.md → 0 ✅
rg -c "<source+test files>" implementation-plan.md → 0 ✅ (verification section uses cross-ref to task table)
```

### Verdict

`approved` — All findings resolved. Plan is implementation-ready.

---

## Approval Recheck Update — 2026-03-08

**Workflow:** `/critical-review-feedback`
**Agent:** GPT-5 Codex
**Scope:** Final recheck after Task 29 validation correction

### Recheck Result

- Task 29 is now deliverable-bound:
  - deliverable changed to `docs/execution/plans/2026-03-08-infra-services/commit-messages.md`
  - validation now asserts that file contains at least five `feat:` lines
- This closes the last remaining validation-realism gap from the prior recheck.

### Commands Rechecked

```text
Get-Content -Raw docs/execution/plans/2026-03-08-infra-services/implementation-plan.md
Get-Content -Raw docs/execution/plans/2026-03-08-infra-services/task.md
Get-Content -Raw .agent/context/handoffs/2026-03-08-infra-services-plan-critical-review.md
rg -n -- "Git commit message per MEU|feat:|docs/execution/plans/2026-03-08-infra-services/commit-messages.md|Proposed commit messages" docs/execution/plans/2026-03-08-infra-services/implementation-plan.md docs/execution/plans/2026-03-08-infra-services/task.md .agent/context/handoffs/2026-03-08-infra-services-plan-critical-review.md
git status --short docs/execution/plans/2026-03-08-infra-services .agent/context/handoffs/2026-03-08-infra-services-plan-critical-review.md
```

### Final Verdict

`approved` — The plan now satisfies the reviewed planning-contract requirements and is implementation-ready.

---

## Final Recheck Update — 2026-03-08

**Workflow:** `/critical-review-feedback`
**Agent:** GPT-5 Codex
**Scope:** Recheck of the post-correction plan with focus on validation realism

### Recheck Result

- The previous planning-contract issue is almost fully resolved:
  - quality-gate rows now use concrete file lists
  - handoff/reflection rows now use runnable assertions
  - registry/metrics rows now use concrete `rg` checks

### Remaining Finding

- **Medium:** Task 29 still uses a validation command that does not verify its stated deliverable. The deliverable is `Git commit message per MEU`, but the validation command at `implementation-plan.md:306` is ``rg -c 'feat:' docs/execution/plans/2026-03-08-infra-services/task.md``. That only checks whether the plan file contains the string `feat:`; it does not verify that proposed commit messages were actually produced anywhere. This still falls short of the “exact commands” and validation-realism standard in `AGENTS.md:61`.

### Commands Rechecked

```text
Get-Content -Raw docs/execution/plans/2026-03-08-infra-services/implementation-plan.md
Get-Content -Raw docs/execution/plans/2026-03-08-infra-services/task.md
Get-Content -Raw .agent/context/handoffs/2026-03-08-infra-services-plan-critical-review.md
rg -n -- "<source\+test files>|Template compliance|Visual check|Metrics match task count|git log --oneline|validate_codebase.py --scope meu --files" docs/execution/plans/2026-03-08-infra-services/implementation-plan.md docs/execution/plans/2026-03-08-infra-services/task.md
rg -n -- "feat:" docs/execution/plans/2026-03-08-infra-services/task.md docs/execution/plans/2026-03-08-infra-services/implementation-plan.md .agent/context/handoffs/2026-03-08-infra-services-plan-critical-review.md
git status --short docs/execution/plans/2026-03-08-infra-services .agent/context/handoffs/2026-03-08-infra-services-plan-critical-review.md
```

### Updated Verdict

`changes_required` — The plan is close, but Task 29 still needs a validation command tied to an actual proposed-commit-message artifact.

---

## Final Corrections Applied — 2026-03-08

**Workflow:** `/planning-corrections`
**Agent:** Antigravity (Kael)
**Scope:** 1 Medium finding from final recheck

### Finding Resolution

| # | Severity | Finding | Resolution |
|---|----------|---------|------------|
| F8 | Medium | Task 29 validation doesn't verify deliverable | Changed deliverable to `commit-messages.md` file, validation to `python -c` assertion checking `>=5` lines starting with `feat:` |

### Verdict

`approved` — All findings resolved. Plan is implementation-ready.
