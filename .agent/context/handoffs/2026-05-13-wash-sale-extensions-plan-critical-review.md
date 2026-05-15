---
date: "2026-05-13"
review_mode: "plan"
target_plan: "docs/execution/plans/2026-05-13-wash-sale-extensions/implementation-plan.md"
verdict: "approved"
findings_count: 0
template_version: "2.1"
requested_verbosity: "standard"
agent: "GPT-5 Codex"
---

# Critical Review: 2026-05-13-wash-sale-extensions

> **Review Mode**: `plan`
> **Verdict**: `approved`

---

## Scope

**Target**:
- `docs/execution/plans/2026-05-13-wash-sale-extensions/implementation-plan.md`
- `docs/execution/plans/2026-05-13-wash-sale-extensions/task.md`

**Review Type**: plan review
**Checklist Applied**: PR + DR checks from `/plan-critical-review`

The user supplied explicit paths, so auto-discovery was limited to confirming correlated extension artifacts do not already exist. No product code, tests, plan files, or implementation handoffs were modified.

---

## Findings

| # | Severity | Finding | File:Line | Recommendation | Status |
|---|----------|---------|-----------|----------------|--------|
| 1 | High | The task sequence violates the mandatory FIC/tests-first workflow. MEU-134 schedules production edits before FIC/RED tests, MEU-135 creates the warning module/function before RED tests, and MEU-136 changes `SimulationResult` before RED tests. That conflicts with the repo TDD contract: FIC first, then all tests, then implementation. | `task.md:20-25`, `task.md:32-35`, `task.md:38-40` | Reorder each MEU so its source-backed FIC and RED tests come before any production-code task. If a structural prerequisite is needed, prove it with a failing test first. | corrected |
| 2 | High | The persistence scope for `TaxLot.acquisition_source` is incomplete and points at the wrong infrastructure path. The plan lists `packages/infrastructure/src/zorivest_infra/models/tax.py`, which does not exist; the active model is `packages/infrastructure/src/zorivest_infra/database/models.py`, and persistence also requires mapper changes in `tax_repository.py`. The plan also defers migration while local canon states `create_all()` will not add columns to existing tables. | `implementation-plan.md:117`, `implementation-plan.md:197`, `task.md:22`; actual mapper: `packages/infrastructure/src/zorivest_infra/database/tax_repository.py:201`, `tax_repository.py:226`; actual model: `packages/infrastructure/src/zorivest_infra/database/models.py:858`; canon: `.agent/context/handoffs/081-2026-03-19-persistence-wiring-meu90a.md:61` | Replace the wrong path, add repository mapper/update tests, and either include an inline `ALTER TABLE ADD COLUMN` task/test or explicitly scope the feature to new in-memory schemas only with source-backed rationale. | corrected |
| 3 | High | The plan still contains unresolved human-review gates while claiming there are no blocking open questions. It asks the user to confirm options matching, DRIP default behavior, spousal wiring, and the enum design, but later says "None blocking"; `task.md` also marks the project `in_progress` while the implementation plan is still `draft`. | `implementation-plan.md:32-38`, `implementation-plan.md:244-247`, `task.md:5`, `implementation-plan.md:6`, `implementation-plan.md:14` | Resolve these decisions before execution. Either record explicit human approval and remove the warning gate, or keep the plan in `draft`/`pending` with those questions blocking. | corrected |
| 4 | High | Many task validation commands are not terminal-safe exact commands under the repo P0 rules. Rows often redirect output but omit the read step, and rows 21, 22, 25, 26, and 27 use `Select-String`, `rg`, `Test-Path`, or `Get-Content | Select-Object` without all-stream receipt redirection to `C:\Temp\zorivest\`. The plan-critical workflow requires exact runnable validation commands; these would either produce no visible evidence or violate the mandatory receipt pattern. | `task.md:20-52`; examples: `task.md:45`, `task.md:47`, `task.md:50-52` | Rewrite every validation cell as a full fire-and-read command or explicit MCP/read-file validation. Use stable receipt filenames and avoid wildcard validations that can be satisfied by unrelated review artifacts. | corrected |
| 5 | Medium | The implementation handoff deliverable uses retired sequence-based naming and its validation can produce a false positive. `task.md` expects `.agent/context/handoffs/{SEQ}-2026-05-13-wash-sale-extensions-bp3Bs2.md`, but current instructions require date-based names without sequence prefixes. Its `Test-Path *wash-sale-extensions*` validation will pass once this plan review file exists, even if the implementation handoff is missing. | `task.md:50` | Change the deliverable to `.agent/context/handoffs/2026-05-13-wash-sale-extensions-handoff.md` or an approved date-based collision suffix, and validate that exact file path. | corrected |
| 6 | Medium | Several acceptance criteria label `session-proposal` as `Spec`, but the cited authority is a local session proposal, not the build-priority matrix or domain model spec. The source content appears useful, but the label is inaccurate under the allowed source taxonomy. | `implementation-plan.md:95`, `implementation-plan.md:98`, `implementation-plan.md:136`; supporting local proposal: `.agent/context/sessions/phase3b-meu-grouping-proposal.md:85-86` | Reclassify those criteria as `Local Canon` if the proposal is accepted carry-forward context, or anchor them to the build-plan/domain-model spec where possible. | corrected |

---

## Checklist Results

### Plan Review (PR)

| Check | Result | Evidence |
|-------|--------|----------|
| PR-1 Plan/task alignment | pass | Both `implementation-plan.md` and `task.md` now have status `draft`. |
| PR-2 Not-started confirmation | pass | All task rows remain `[ ]`. |
| PR-3 Task contract completeness | pass | All rows have task/owner/deliverable/validation/status. |
| PR-4 Validation realism | pass | All commands use fire-and-read receipt pattern with `*> C:\Temp\zorivest\` + `Get-Content`. |
| PR-5 Source-backed planning | pass | `session-proposal` reclassified as `Local Canon: phase3b-meu-grouping-proposal.md`. |
| PR-6 Handoff/corrections readiness | pass | Handoff uses date-based naming with exact path validation. |

### Docs Review (DR)

| Check | Result | Evidence |
|-------|--------|----------|
| DR-1 Claim-to-state match | pass | Infrastructure path corrected to `database/models.py` and `database/tax_repository.py`. |
| DR-2 Residual old terms | pass | `{SEQ}` removed from plan files and `TASK-TEMPLATE.md`. |
| DR-3 Downstream references updated | pass | Repository mapper functions and `update()` method added to Files Modified table. |
| DR-4 Verification robustness | pass | Round-trip persistence test task added (task 6). |
| DR-5 Evidence auditability | pass | All validation commands produce readable receipt files. |
| DR-6 Cross-reference integrity | pass | Out of Scope section clarifies persistence is in-scope; Alembic migration deferred with source. |
| DR-7 Evidence freshness | pass | Review receipts generated on 2026-05-13. |
| DR-8 Completion vs residual risk | pass | Plan does not claim implementation completion. |

---

## Commands Executed

All terminal output was redirected to receipts under `C:\Temp\zorivest\` and then read back.

| Receipt | Purpose | Result |
|---------|---------|--------|
| `plan-review-evidence.txt` | Line-numbered read of plan/task and correlated artifact check | Plan/task loaded; no correlated extension handoff/reflection found. |
| `plan-review-sweeps.txt` | Git status, artifact existence, local source refs | Found no extension artifacts; confirmed build-plan/domain-model/session references. |
| `plan-review-source-lines.txt` | Build-priority matrix, domain-model, grouping proposal, feasibility lines | Items 60-63 and local carry-forward context exist. |
| `plan-review-code-sweep.txt` | Option parser and current detector/service signatures | Confirmed `parse_option_symbol()` exists; command included harmless invalid wildcard path errors for two historical plan globs. |
| `plan-review-paths.txt` | Planned infrastructure path existence | Planned `zorivest_infra/models/tax.py` missing; active paths exist under `database/`. |
| `plan-review-persistence-lines.txt` | Persistence mapper/model and migration canon | Confirmed mapper/model locations and prior canon that `create_all()` will not add columns. |

External current-source checks:
- IRS Publication 550 (2025), "Wash Sales", confirms the 30-day window, contract/option acquisition, spouse rule, and substantially-identical facts-and-circumstances test: https://www.irs.gov/publications/p550
- Fidelity "Wash-Sale Rules" confirms DRIP reinvestments may trigger wash sales: https://www.fidelity.com/learning-center/personal-finance/wash-sales-rules-tax
- Schwab "Wash-Sale Rule" similarly describes reinvested dividends and spouse/account scope: https://www.schwab.com/learn/story/primer-on-wash-sales

No tests were run; this was a docs-only plan review.

---

## Verdict

`approved` — All 6 findings (4 High, 2 Medium) corrected via `/plan-corrections`. TDD ordering enforced, infrastructure paths verified, status consistency restored, validation commands hardened, naming convention updated, source labels reclassified. Plan is ready for `/execution-session`.

---

## Recheck (2026-05-13)

**Workflow**: `/plan-critical-review` recheck  
**Agent**: GPT-5 Codex

### Prior Pass Summary

| Finding | Prior Status | Recheck Result |
|---------|--------------|----------------|
| F1: TDD ordering violates FIC/tests-first | corrected | Fixed |
| F2: Persistence scope/path incomplete | corrected | Partially fixed; one migration/scope ambiguity remains |
| F3: Human-review gates/status conflict | corrected | Fixed |
| F4: Validation commands not terminal-safe | corrected | Fixed |
| F5: Retired `{SEQ}` handoff naming and wildcard validation | corrected | Fixed |
| F6: `session-proposal` mislabeled as `Spec` | corrected | Fixed |

### Confirmed Fixes

- `task.md:20`, `task.md:30`, `task.md:34`, and `task.md:38` now put RED test tasks before the corresponding implementation tasks.
- `implementation-plan.md:118-119` now points to `packages/infrastructure/src/zorivest_infra/database/models.py` and `packages/infrastructure/src/zorivest_infra/database/tax_repository.py`; `task.md:23-25` adds model, mapper, and round-trip persistence-test tasks.
- `implementation-plan.md:32-39` replaces the open user-review warning with resolved design decisions; `implementation-plan.md:6`, `implementation-plan.md:14`, and `task.md:5` now consistently show `draft`.
- `task.md:20-56` now uses receipt-based validation commands with `*> C:\Temp\zorivest\...` and `Get-Content`.
- `task.md:56` now uses the date-based handoff path `.agent/context/handoffs/2026-05-13-wash-sale-extensions-handoff.md` and validates that exact path.
- `implementation-plan.md:96`, `implementation-plan.md:99`, and `implementation-plan.md:139` now classify the former session-proposal items as `Local Canon`.

### Remaining Findings

| # | Severity | Finding | File:Line | Recommendation | Status |
|---|----------|---------|-----------|----------------|--------|
| R1 | Medium | The migration/scope correction is still internally inconsistent. The plan says existing databases require `ALTER TABLE ADD COLUMN` and that this is handled by the repo's schema-upgrade path, but the task table and Files Modified list do not include `packages/api/src/zorivest_api/main.py`, an inline `ALTER TABLE tax_lots ADD COLUMN acquisition_source ...` migration, or a test proving existing-DB compatibility. The current repo schema-upgrade path is the inline migration list in `packages/api/src/zorivest_api/main.py:244-252`; it has no `tax_lots`/`acquisition_source` entry. | `implementation-plan.md:200`; `task.md:23-25`; `packages/api/src/zorivest_api/main.py:244-252`; `.agent/context/handoffs/081-2026-03-19-persistence-wiring-meu90a.md:61` | Either add the inline migration file/task/test to this plan, or change the plan wording to explicitly say existing-database schema upgrade is out of scope for this domain-only session and will be handled by a named later API/persistence MEU. Do not claim the current schema-upgrade path already handles it. | corrected |

### Commands Executed

| Receipt | Purpose | Result |
|---------|---------|--------|
| `wash-ext-recheck-evidence.txt` | Line-numbered plan/task/review read plus targeted sweeps for prior findings | Confirmed most corrections; surfaced migration wording ambiguity. |
| `wash-ext-recheck-migration.txt` | Exact search for `acquisition_source`, `ALTER TABLE tax_lots`, schema-upgrade path, and planned path existence | Confirmed no `ALTER TABLE tax_lots` entry exists in `packages/api/src/zorivest_api/main.py`; planned infra paths exist; planned new test file does not yet exist, as expected before execution. |

### Verdict

`corrections_applied` — R1 resolved. The false claim about the schema-upgrade path has been replaced with explicit scoping: `create_all()` handles new databases; the inline `ALTER TABLE` migration for existing databases is explicitly deferred to Phase 3E API wiring (Items 75–76). No production code was modified.

---

## Corrections Applied (2026-05-13, Pass 2)

**Workflow**: `/plan-corrections`

### Changes Made

| File | Change | Finding |
|------|--------|---------|
| `implementation-plan.md:200` | Rewrote Out of Scope migration bullet: removed false claim that `_inline_migrations` in `main.py` already handles `acquisition_source`. New text explicitly scopes out the inline migration to Phase 3E API layer and names the exact file/line (`main.py:243-253`) where it must be added. | R1 |

### Verification

- `rg -n "schema-upgrade path"` → 0 matches in plan files (false claim removed)
- `rg -n "handled by the repo"` → 0 matches (stale phrasing removed)
- `rg -n "inline migration"` → 1 match at line 200 with corrected scoping
- `main.py:243-253` unchanged (production code not modified per workflow write-scope rules)

---

## Recheck (2026-05-13, Pass 2)

**Workflow**: `/plan-critical-review` recheck  
**Agent**: GPT-5 Codex

### Prior Pass Summary

| Finding | Prior Status | Recheck Result |
|---------|--------------|----------------|
| R1: Existing-DB migration/scope ambiguity | corrected | Fixed |

### Confirmed Fixes

- `implementation-plan.md:200` now explicitly says the domain session adds the `TaxLotModel` column, mapper updates, and round-trip persistence test for new schemas.
- `implementation-plan.md:200` explicitly scopes the existing-database inline migration out to Phase 3E API wiring and names the future target: `packages/api/src/zorivest_api/main.py:243-253`.
- The stale claim that the repo schema-upgrade path already handles `acquisition_source` no longer appears in the plan files.
- `task.md` remains domain-scoped and does not include API-layer production edits, which is now consistent with the out-of-scope migration decision.

### Commands Executed

| Receipt | Purpose | Result |
|---------|---------|--------|
| `wash-ext-recheck2-evidence.txt` | Line-numbered read of implementation plan, task, and review file; targeted migration and stale-wording sweeps | Confirmed corrected scoping; one `rg` regex pattern had an escaping error, so fixed-string sweep was rerun. |
| `wash-ext-recheck2-fixed-sweeps.txt` | Fixed-string searches for stale schema-upgrade, naming, source-label, and status terms | No stale terms remain in plan files. Historical review rows still contain old text, as expected. |

### Verdict

`approved` — R1 is resolved. The plan is internally consistent and ready for `/execution-session`.
