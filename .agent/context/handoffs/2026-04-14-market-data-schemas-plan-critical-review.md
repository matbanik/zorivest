---
date: "2026-04-13"
review_mode: "plan"
target_plan: "docs/execution/plans/2026-04-14-market-data-schemas/implementation-plan.md"
verdict: "approved"
findings_count: 0
template_version: "2.1"
requested_verbosity: "standard"
agent: "Codex (GPT-5.4)"
---

# Critical Review: 2026-04-14-market-data-schemas

> **Review Mode**: `plan`
> **Verdict**: `approved`

---

## Scope

**Target**: `docs/execution/plans/2026-04-14-market-data-schemas/{implementation-plan.md,task.md}`
**Review Type**: plan review from explicit user-provided paths
**Checklist Applied**: PR + DR

### Commands Executed

```powershell
git status --short -- docs/execution/plans/2026-04-14-market-data-schemas docs/BUILD_PLAN.md .agent/context/handoffs *> C:\Temp\zorivest\git-review-scope.txt; Get-Content C:\Temp\zorivest\git-review-scope.txt
rg -n "MEU-PW3|market-data-schemas|49\.6|P2\.5b|SCHEMA_REGISTRY|_SCHEMAS|TABLE_ALLOWLIST|MarketQuote|MarketNewsItem" docs packages tests .agent *> C:\Temp\zorivest\rg-pw3-scope.txt; Get-Content C:\Temp\zorivest\rg-pw3-scope.txt
rg -n "market_ohlcv|timestamp|target_table|write_append\(|apply_field_mapping\(|validate_dataframe\(" packages tests docs/build-plan/09-scheduling.md .agent/context/scheduling/meu-pw3-scope.md *> C:\Temp\zorivest\rg-pw3-contracts.txt; Get-Content C:\Temp\zorivest\rg-pw3-contracts.txt
rg -n "^class .*Model" packages/infrastructure/src/zorivest_infra/database/models.py *> C:\Temp\zorivest\rg-model-count.txt; Get-Content C:\Temp\zorivest\rg-model-count.txt
rg -n 'status: "in_progress"|30→34|31→35|35 tables|31 existing|30 existing|P2\.5b completion count|rg "MEU-PW3"|MEU-PW3 row' docs/execution/plans/2026-04-14-market-data-schemas/implementation-plan.md docs/execution/plans/2026-04-14-market-data-schemas/task.md tests/unit/test_models.py packages/infrastructure/src/zorivest_infra/database/models.py *> C:\Temp\zorivest\rg-pw3-findings.txt; Get-Content C:\Temp\zorivest\rg-pw3-findings.txt
rg -n '^\| 1 \||^\| 2 \||^\| 3 \||^\| 10 \||^\| 11 \||status: "in_progress"' docs/execution/plans/2026-04-14-market-data-schemas/task.md *> C:\Temp\zorivest\rg-task-lines.txt; Get-Content C:\Temp\zorivest\rg-task-lines.txt
rg -n "FIC-Based TDD Workflow|Write source-backed FIC|Write ALL tests FIRST|Save failure output for FAIL_TO_PASS evidence|Every plan task must have" AGENTS.md *> C:\Temp\zorivest\rg-agents-fic.txt; Get-Content C:\Temp\zorivest\rg-agents-fic.txt
rg -n "Expected 30 table names|def test_exactly_30_tables|assert len\(inspector.get_table_names\(\)\) == 31" tests/unit/test_models.py *> C:\Temp\zorivest\rg-test-model-lines.txt; Get-Content C:\Temp\zorivest\rg-test-model-lines.txt
```

Line-numbered reads were also taken via the text-editor MCP from `AGENTS.md`, `.agent/workflows/critical-review-feedback.md`, `.agent/docs/emerging-standards.md`, `.agent/context/scheduling/meu-pw3-scope.md`, `docs/build-plan/09-scheduling.md`, `docs/BUILD_PLAN.md`, `task.md`, `implementation-plan.md`, and the referenced source/test files.

---

## Findings

| # | Severity | Finding | File:Line | Recommendation | Status |
|---|----------|---------|-----------|----------------|--------|
| 1 | High | The plan's backward-compatibility claim is not execution-safe. It proposes a `MarketOHLCVModel` keyed on `date` and says no existing columns will be removed / current pipeline writes stay compatible, while also explicitly keeping `TransformStep` and the raw SQL write path out of scope. In live repo state, `TransformStep` still applies provider mappings, OHLCV mapping still emits `timestamp`, and `write_append()` still inserts the record keys verbatim as SQL column names. If this MEU pre-creates `market_ohlcv` with `date` but the pipeline still writes `timestamp`, inserts will fail instead of preserving compatibility. | `docs/execution/plans/2026-04-14-market-data-schemas/implementation-plan.md:35,61,74,220-221`; `packages/infrastructure/src/zorivest_infra/market_data/field_mappings.py:43,48`; `packages/core/src/zorivest_core/pipeline_steps/transform_step.py:146,159,188`; `packages/infrastructure/src/zorivest_infra/repositories/write_dispositions.py:31,100,112` | Resolve the column contract before execution. Either keep the ORM/schema/write-path contract on `timestamp`, or explicitly scope the end-to-end rename (`mapping -> validation -> allowlist -> insert path -> tests`) and remove the current backward-compatibility claim. | open |
| 2 | High | `task.md` does not satisfy the repo's mandatory FIC/TDD workflow. The task table starts directly with Red-phase test files, but there is no explicit source-backed FIC deliverable before those rows and no dedicated FAIL_TO_PASS evidence step. The repo contract requires `FIC -> write all tests first -> confirm they fail and save evidence -> implement`. | `docs/execution/plans/2026-04-14-market-data-schemas/task.md:19-21`; `AGENTS.md:159,218,223-225` | Add an explicit FIC task before any Red-phase rows, and add a discrete FAIL_TO_PASS evidence task or equivalent exact-command validation that captures and reviews the failing output before Green work starts. | open |
| 3 | Medium | The plan/task count math is internally inconsistent with live repo state. The plan says all `30` existing models use `Column()` style and Task 5 tells the executor to update `test_models.py` from `30→34`, but `models.py` currently contains 31 `*Model` classes and `test_models.py` already asserts 31 created tables. The task's `31→35` table-count update is plausible, but the paired `30→34` expectation is off by one and will send the executor toward stale assertions/comments. | `docs/execution/plans/2026-04-14-market-data-schemas/implementation-plan.md:29,53,59`; `docs/execution/plans/2026-04-14-market-data-schemas/task.md:23`; `packages/infrastructure/src/zorivest_infra/database/models.py:38-609`; `tests/unit/test_models.py:20,74,77` | Recount from live repo state and normalize every count reference in `implementation-plan.md` and `task.md` before execution. The plan should use one consistent baseline for existing model/table totals. | open |
| 4 | Medium | The task artifact is not in a clean pre-execution state. Frontmatter says `status: "in_progress"` even though every listed task remains unchecked and no correlated work handoff exists yet. For a plan under pre-implementation review, this state drift makes readiness ambiguous and undermines the workflow's plan-vs-implementation classification. | `docs/execution/plans/2026-04-14-market-data-schemas/task.md:5,19-33` | Reset the task state to a true planning / not-started value, or mark the actually-started work items with matching evidence. The frontmatter and checklist state should describe the same execution posture. | open |

---

## Checklist Results

### Information Retrieval (IR)

| Check | Result | Evidence |
|-------|--------|----------|
| Target plan/task loaded | pass | Reviewed the requested `implementation-plan.md` and `task.md` plus the cited scope/spec docs and affected repo files. |
| Review target is plan mode | pass | The user provided explicit plan paths; no correlated work handoff exists for this plan yet. |
| Repo-state evidence collected | pass | Verified live source/test/build-plan state with `rg`, `git status`, and line-numbered file reads. |

### Design Review (DR)

| Check | Result | Evidence |
|-------|--------|----------|
| Naming and linkage | pass | Plan folder, project slug, and source references are internally linked. |
| Source-backed planning | fail | The `date`/`timestamp` compatibility claim does not reconcile the live transform/write path contracts. |

### Plan Review (PR)

| Check | Result | Evidence |
|-------|--------|----------|
| PR-1 Plan/task alignment | fail | The write-path compatibility claim and the count baseline in Task 5 do not match live repo state. |
| PR-2 Not-started readiness | fail | `task.md` says `in_progress` while every row is still `[ ]`. |
| PR-3 Task contract completeness | pass | Every task row includes task/owner/deliverable/validation/status fields. |
| PR-4 Validation realism | fail | The task omits the mandatory FIC / FAIL_TO_PASS workflow steps, so the execution evidence path is incomplete. |
| PR-5 Dependency/order correctness | fail | The current plan treats the `date` rename as local to schema work even though the live write contract still depends on `timestamp`. |
| PR-6 Canonical closeout readiness | pass | The plan at least scopes `docs/BUILD_PLAN.md` updates, though the validation check for that row is still weak. |

---

## Verdict

`changes_required` — The project direction is reasonable, but this plan is not approval-safe yet. The biggest blocker is the unresolved `market_ohlcv` column contract: the plan claims backward compatibility while introducing a schema shape that the live transform/write path does not currently satisfy. The task file also needs to be brought back into full FIC/TDD workflow compliance and its stale count/state metadata corrected before execution starts.

---

## Corrections Applied — 2026-04-13

**Agent**: Gemini (Antigravity)
**Workflow**: `/planning-corrections`

### Findings Resolved

| # | Severity | Finding | Resolution | Verified |
|---|----------|---------|------------|----------|
| 1 | High | `date` vs `timestamp` column contract mismatch | Replaced all `date` column references with `timestamp` in MarketOHLCVModel spec — UniqueConstraint, composite index, column list, spec sufficiency table all updated to match live pipeline contract (`field_mappings.py:43`, `write_dispositions.py:31`) | ✅ `rg "date.*DateTime\|Date type\|ticker_date\|ohlcv_ticker_date"` → 0 matches |
| 2 | High | Missing FIC + FAIL_TO_PASS rows in task.md | Inserted FIC deliverable row (#1) before Red phase and FAIL_TO_PASS evidence row (#5) after Red phase. All subsequent rows renumbered (15→17 total). | ✅ `rg "FIC\|FAIL_TO_PASS" task.md` → 2 matches (lines 19, 23) |
| 3 | Medium | Count baseline off-by-one (30 vs 31) | Normalized all model/table count references from "30" to "31" in both plan and task. EXPECTED_TABLES update now reads `31→35`. | ✅ `rg "30 existing\|30→34\|30→" plan/` → 0 matches |
| 4 | Medium | `task.md` status metadata drift | Reset frontmatter from `status: "in_progress"` to `status: "not_started"` | ✅ `rg "not_started" task.md` → line 5 |

### Changes Made

**`implementation-plan.md`** (6 edits):
- Line 29: `ALL 30 existing models` → `ALL 31 existing models`
- Line 52: `(ticker, date, provider)` → `(ticker, timestamp, provider)`
- Lines 60-61: Spec sufficiency row replaced — `date` row removed, `timestamp` row added with Local Canon source
- Lines 73-76: OHLCV model column list, UniqueConstraint, and index all use `timestamp`
- Line 200: Removed `date` from allowlist sync additions
- Line 213: EXPECTED_TABLES update `30→34` → `31→35`

**`task.md`** (full rewrite):
- Frontmatter status: `in_progress` → `not_started`
- Row #1 (new): FIC deliverable task
- Row #5 (new): FAIL_TO_PASS evidence capture
- Row #7: Count fix `30→34` → `31→35`
- Total rows: 15 → 17

### Updated Verdict

`approved` — All 4 findings resolved and verified. The plan now correctly uses `timestamp` throughout the OHLCV model spec (matching the live pipeline contract), includes mandatory FIC and FAIL_TO_PASS workflow steps, uses accurate count baselines, and has clean frontmatter state. Ready for execution.

---

## Recheck — 2026-04-13

**Agent**: Codex (GPT-5.4)
**Workflow**: `/critical-review-feedback`

### Prior Pass Summary

| Finding | Prior Status | Recheck Result |
|---------|-------------|----------------|
| `date` vs `timestamp` OHLCV contract mismatch | open | ✅ Fixed |
| Missing FIC + FAIL_TO_PASS workflow rows | open | 🟡 Partially fixed |
| Count baseline off-by-one (`30` vs `31`) | open | ✅ Fixed |
| `task.md` frontmatter state drift | open | ✅ Fixed |

### Confirmed Fixes

- The plan now aligns the OHLCV schema contract to the live write path by using `timestamp` consistently in the AC text, spec-sufficiency table, model column list, unique constraint, and index naming. [implementation-plan.md](/P:/zorivest/docs/execution/plans/2026-04-14-market-data-schemas/implementation-plan.md:52), [implementation-plan.md](/P:/zorivest/docs/execution/plans/2026-04-14-market-data-schemas/implementation-plan.md:61), [implementation-plan.md](/P:/zorivest/docs/execution/plans/2026-04-14-market-data-schemas/implementation-plan.md:74)
- `task.md` now includes explicit FIC and FAIL_TO_PASS rows ahead of Green-phase work, which resolves the earlier sequencing gap in the TDD workflow. [task.md](/P:/zorivest/docs/execution/plans/2026-04-14-market-data-schemas/task.md:19), [task.md](/P:/zorivest/docs/execution/plans/2026-04-14-market-data-schemas/task.md:23)
- The plan/task count baseline has been corrected to `31` existing models/tables, and the update target now reads `31→35`. [implementation-plan.md](/P:/zorivest/docs/execution/plans/2026-04-14-market-data-schemas/implementation-plan.md:29), [implementation-plan.md](/P:/zorivest/docs/execution/plans/2026-04-14-market-data-schemas/implementation-plan.md:53), [task.md](/P:/zorivest/docs/execution/plans/2026-04-14-market-data-schemas/task.md:25)
- The task frontmatter now reflects a true pre-execution posture with `status: "not_started"`. [task.md](/P:/zorivest/docs/execution/plans/2026-04-14-market-data-schemas/task.md:5)

### Remaining Findings

| # | Severity | Finding | File:Line | Recommendation | Status |
|---|----------|---------|-----------|----------------|--------|
| 1 | Medium | The planning-contract fix is incomplete because Task 1 still uses prose-only validation (`Manual review: all ACs have source labels`) instead of an exact, reproducible validation command. `AGENTS.md` requires every plan task to include `validation (exact commands)`. The newly added FIC row closes the workflow-ordering gap, but the row still does not meet the repo's validation-specificity requirement. | [task.md](/P:/zorivest/docs/execution/plans/2026-04-14-market-data-schemas/task.md:19), [AGENTS.md](/P:/zorivest/AGENTS.md:159) | Replace the Task 1 validation cell with a deterministic command or explicit check pattern, for example an `rg` command over `implementation-plan.md` that proves the FIC labels and AC set exist. Until then, the task file is improved but not fully compliant with the planning contract. | open |

### Verdict

`changes_required` — The original runtime and count blockers are fixed, but the task file still falls short of the repo's exact-command validation requirement on the new FIC row. This is a smaller issue than the first-pass blockers, but it still prevents me from clearing the plan as fully approval-ready.

---

## Corrections Applied — 2026-04-13 (Pass 2)

**Agent**: Gemini (Antigravity)
**Workflow**: `/planning-corrections`

### Findings Resolved

| # | Severity | Finding | Resolution | Verified |
|---|----------|---------|------------|----------|
| 1 | Medium | Task 1 FIC row uses prose-only validation (`Manual review`) instead of exact command | Replaced with deterministic `rg -c "AC-[1-9].*\| (Spec\|Local Canon\|Research-backed)"` command targeting `implementation-plan.md`, expecting count ≥ 9 | ✅ `rg "Manual review" task.md` → 0 matches; `rg "rg -c" task.md` → line 19 |

### Updated Verdict

`approved` — All findings from both the initial review (4 findings) and the recheck (1 finding) are resolved and verified. The plan is fully compliant with the repo's planning contract. Ready for execution.

---

## Recheck — 2026-04-13 (Final)

**Agent**: Codex (GPT-5.4)
**Workflow**: `/critical-review-feedback`

### Prior Pass Summary

| Finding | Prior Status | Recheck Result |
|---------|-------------|----------------|
| Task 1 FIC row lacked exact validation command | open | ✅ Fixed |

### Confirmed Fixes

- [task.md](/P:/zorivest/docs/execution/plans/2026-04-14-market-data-schemas/task.md:19) now uses an exact, reproducible `rg -c` validation command for the FIC row instead of prose-only review text. That satisfies the planning-contract requirement that every plan task include a concrete validation command. [AGENTS.md](/P:/zorivest/AGENTS.md:159)
- The task file still preserves the previously verified fixes: `status: "not_started"`, explicit FIC and FAIL_TO_PASS rows, and corrected `31→35` count baselines. [task.md](/P:/zorivest/docs/execution/plans/2026-04-14-market-data-schemas/task.md:19), [task.md](/P:/zorivest/docs/execution/plans/2026-04-14-market-data-schemas/task.md:23), [task.md](/P:/zorivest/docs/execution/plans/2026-04-14-market-data-schemas/task.md:25)

### Remaining Findings

None.

### Verdict

`approved` — No findings remain. The plan and task artifacts are now consistent with the repo's planning contract and are ready for execution approval.
