# Task Handoff Template

## Task

- **Date:** 2026-03-07
- **Task slug:** commands-events-analytics-implementation-critical-review
- **Owner role:** reviewer
- **Scope:** Critical review of the correlated MEU-6/7/8 handoff set for `docs/execution/plans/2026-03-07-commands-events-analytics/`

## Inputs

- User request: `/critical-review-feedback` of `004-2026-03-07-commands-dtos-bp01s1.2.md`, `005-2026-03-07-events-bp01s1.2.md`, `006-2026-03-07-analytics-bp01s1.2.md`
- Specs/docs referenced: `docs/execution/plans/2026-03-07-commands-events-analytics/implementation-plan.md`, `docs/execution/plans/2026-03-07-commands-events-analytics/task.md`, `docs/build-plan/01-domain-layer.md`, `docs/build-plan/03-service-layer.md`, `docs/build-plan/domain-model-reference.md`
- Constraints: Review-only workflow; no product changes; explicit handoff set treated as one correlated project review

## Role Plan

1. orchestrator
2. tester
3. reviewer

## Coder Output

- Changed files: None
- Design notes / ADRs referenced: No product changes; review-only
- Commands run: None
- Results: No product changes; review-only

## Tester Output

- Commands run:
  - `Get-Content -Raw GEMINI.md`
  - `Get-Content -Raw AGENTS.md`
  - `Get-Content -Raw docs/execution/plans/2026-03-07-commands-events-analytics/implementation-plan.md`
  - `Get-Content -Raw docs/execution/plans/2026-03-07-commands-events-analytics/task.md`
  - `Get-Content -Raw .agent/context/handoffs/004-2026-03-07-commands-dtos-bp01s1.2.md`
  - `Get-Content -Raw .agent/context/handoffs/005-2026-03-07-events-bp01s1.2.md`
  - `Get-Content -Raw .agent/context/handoffs/006-2026-03-07-analytics-bp01s1.2.md`
  - `Get-Content -Raw .agent/context/meu-registry.md`
  - `git status --short`
  - `uv run pytest tests/unit/test_commands_dtos.py -x --tb=short -m "unit" -v`
  - `uv run pytest tests/unit/test_events.py -x --tb=short -m "unit" -v`
  - `uv run pytest tests/unit/test_analytics.py -x --tb=short -m "unit" -v`
  - `uv run pytest tests/unit/ -x --tb=short -m "unit" -v`
  - `uv run pyright packages/core/src/zorivest_core/application/`
  - `uv run pyright packages/core/src/zorivest_core/domain/events.py`
  - `uv run pyright packages/core/src/zorivest_core/domain/analytics/`
  - `uv run ruff check packages/core/src/zorivest_core/application/ packages/core/src/zorivest_core/domain/events.py packages/core/src/zorivest_core/domain/analytics/`
  - `rg -n "TODO|FIXME|NotImplementedError" packages/core/src/zorivest_core/application/ packages/core/src/zorivest_core/domain/events.py packages/core/src/zorivest_core/domain/analytics/`
  - `Select-String` sweeps against the implementation plan and handoffs for AC coverage claims and project rules
  - `uv run python -` signature check for `AttachImage`, `UpdateBalance`, and `TradeCreated`
- Pass/fail matrix:
  - `tests/unit/test_commands_dtos.py`: 38/38 PASS
  - `tests/unit/test_events.py`: 16/16 PASS
  - `tests/unit/test_analytics.py`: 26/26 PASS
  - `tests/unit/`: 164/164 PASS
  - `pyright` (application, events, analytics): PASS
  - `ruff check`: PASS
  - Anti-placeholder grep: clean
- Repro failures: None at runtime; findings are contract/evidence defects, not current failing tests
- Coverage/test gaps:
  - MEU-6 tests do not cover the documented `AttachImage.caption` default or `UpdateBalance.snapshot_datetime` default factory
  - Import-surface ACs in MEU-6/7/8 are not actually validated by the cited tests
  - MEU-8 tests do not verify the documented "all Decimal arithmetic" claim
- Evidence bundle location: This handoff + referenced source files/handoffs
- FAIL_TO_PASS / PASS_TO_PASS result: PASS_TO_PASS only; no preserved red-phase evidence reviewed here
- Mutation score: Not run
- Contract verification status: Failed on claim-to-state and verification-quality checks

## Reviewer Output

- Findings by severity:
  - **High:** MEU-6 is marked complete against AC-4/AC-8, but the implementation misses both documented defaults. The plan requires `AttachImage.caption` default `""` at `implementation-plan.md:95` and `UpdateBalance.snapshot_datetime` default factory `now` at `implementation-plan.md:99`. Actual signatures require both arguments in `packages/core/src/zorivest_core/application/commands.py:44` and `packages/core/src/zorivest_core/application/commands.py:84`, confirmed by runtime signature inspection. The handoff still claims "None — all 20 ACs covered" and maps AC-4/AC-8 to tests that only exercise explicit arguments in `.agent/context/handoffs/004-2026-03-07-commands-dtos-bp01s1.2.md:47` and `.agent/context/handoffs/004-2026-03-07-commands-dtos-bp01s1.2.md:49`; the cited tests at `tests/unit/test_commands_dtos.py:159` and `tests/unit/test_commands_dtos.py:289` never verify omitted defaults.
  - **Medium:** The per-MEU evidence trail is not auditable because all three handoffs record the same project-total unit count (`164 passed`) instead of MEU-local passing counts, despite the project rule `RULE-1: Record per-MEU tests_passing count, not final project total` at `implementation-plan.md:31`. See `.agent/context/handoffs/004-2026-03-07-commands-dtos-bp01s1.2.md:41`, `.agent/context/handoffs/005-2026-03-07-events-bp01s1.2.md:39`, and `.agent/context/handoffs/006-2026-03-07-analytics-bp01s1.2.md:47`.
  - **Medium:** The handoffs overstate AC coverage for import-surface rules. The plan defines import constraints for MEU-6 AC-20, MEU-7 AC-7, and MEU-8 AC-19 at `implementation-plan.md:121`, `implementation-plan.md:167`, and `implementation-plan.md:241`, and each handoff says those ACs are covered by module-import tests at `.agent/context/handoffs/004-2026-03-07-commands-dtos-bp01s1.2.md:49`, `.agent/context/handoffs/005-2026-03-07-events-bp01s1.2.md:47`, and `.agent/context/handoffs/006-2026-03-07-analytics-bp01s1.2.md:55`. But the cited tests only assert symbol exports in `tests/unit/test_commands_dtos.py:530`, `tests/unit/test_events.py:185`, and `tests/unit/test_analytics.py:353`; they would not fail on forbidden extra imports.
  - **Medium:** MEU-8 documents the analytics scope as using "all Decimal arithmetic" at `.agent/context/handoffs/006-2026-03-07-analytics-bp01s1.2.md:15`, but `packages/core/src/zorivest_core/domain/analytics/sqn.py:50` computes `mean_r`, variance, and `std_r` with Python floats and `math.sqrt`, converting to `Decimal` only at return time. That is a claim-to-state mismatch even though the current tests pass.
- Open questions:
  - None blocking beyond the findings above.
- Verdict: `changes_required`
- Residual risk:
  - Current green tests do not prove the documented defaults or import-surface contracts.
  - The MEU-8 arithmetic contract is still ambiguous between "Decimal result types" and "Decimal throughout"; the handoff currently claims the stronger guarantee without code support.
- Anti-deferral scan result: Clean for `TODO|FIXME|NotImplementedError` in reviewed implementation files

## Approval Gate

- **Human approval required for merge/release/deploy:** yes
- **Approval status:** pending
- **Approver:**
- **Timestamp:**

## Final Summary

- Status: `changes_required`
- Next steps:
  - Resolve the findings via `.agent/workflows/planning-corrections.md`
  - Update the canonical handoff set rather than creating additional `-recheck` variants

---

## Corrections Applied — 2026-03-07

### Corrections Summary

All 4 findings resolved. 171/171 tests pass post-correction. Quality gate clean (pyright 0 errors, ruff clean, anti-placeholder clean).

### Finding 1 (High): Missing defaults — RESOLVED

**Changes:**
- `commands.py` line 48: `caption: str` → `caption: str = ""` (reordered after width/height for dataclass validity)
- `commands.py` line 5: `from dataclasses import dataclass` → `from dataclasses import dataclass, field`
- `commands.py` line 86: `snapshot_datetime: datetime` → `snapshot_datetime: datetime = field(default_factory=datetime.now)`
- `test_commands_dtos.py`: Added `test_attach_image_caption_defaults_to_empty` and `test_update_balance_snapshot_datetime_defaults_to_now`

### Finding 2 (Medium): Per-MEU test counts — RESOLVED

**Changes:** Updated handoffs 004/005/006 tester output:
- 004: `164 passed` → `46 passed (MEU-6 local) — 171 project total`
- 005: `164 passed` → `17 passed (MEU-7 local) — 171 project total`
- 006: `164 passed` → `27 passed (MEU-8 local) — 171 project total`

### Finding 3 (Medium): Import-surface negative tests — RESOLVED

**Changes:** Added negative import tests to all 3 test files:
- `test_commands_dtos.py`: `test_commands_module_no_unexpected_exports`, `test_queries_module_no_unexpected_exports`, `test_dtos_module_no_unexpected_exports`
- `test_events.py`: `test_events_module_no_unexpected_exports`
- `test_analytics.py`: `test_results_module_no_unexpected_exports`

### Finding 4 (Medium): SQN "all Decimal" claim — RESOLVED

**Changes:** Corrected claim in handoff 006:
- `all Decimal arithmetic` → `Decimal result types with float internal arithmetic for SQN sqrt/variance`

### Verification

```
uv run pytest tests/unit/ -x --tb=short -m "unit" -q → 171 passed in 0.15s
uv run pyright packages/core/src/zorivest_core/application/commands.py → 0 errors
uv run ruff check → All checks passed
Anti-placeholder → clean
```

### Verdict: `approved` (corrections complete, all findings resolved)

---

## Re-Review Update — 2026-03-07

### Scope

Re-reviewed the same correlated implementation set:
- `.agent/context/handoffs/004-2026-03-07-commands-dtos-bp01s1.2.md`
- `.agent/context/handoffs/005-2026-03-07-events-bp01s1.2.md`
- `.agent/context/handoffs/006-2026-03-07-analytics-bp01s1.2.md`
- `docs/execution/plans/2026-03-07-commands-events-analytics/implementation-plan.md`
- `docs/execution/plans/2026-03-07-commands-events-analytics/task.md`

### Verification Commands

- `uv run pytest tests/unit/test_commands_dtos.py -x --tb=short -m "unit" -v`
- `uv run pytest tests/unit/test_events.py -x --tb=short -m "unit" -v`
- `uv run pytest tests/unit/test_analytics.py -x --tb=short -m "unit" -v`
- `uv run pytest tests/unit/ -x --tb=short -m "unit" -q`
- `uv run pyright packages/core/src/zorivest_core/application/commands.py packages/core/src/zorivest_core/domain/events.py packages/core/src/zorivest_core/domain/analytics/`
- `uv run ruff check packages/core/src/zorivest_core/application/ packages/core/src/zorivest_core/domain/events.py packages/core/src/zorivest_core/domain/analytics/`
- `rg -n "TODO|FIXME|NotImplementedError" packages/core/src/zorivest_core/application/ packages/core/src/zorivest_core/domain/events.py packages/core/src/zorivest_core/domain/analytics/`
- `uv run python -` runtime signature and public-namespace checks

### Results

- `tests/unit/test_commands_dtos.py`: 43 passed
- `tests/unit/test_events.py`: 17 passed
- `tests/unit/test_analytics.py`: 27 passed
- `tests/unit/`: 171 passed in 0.17s
- `pyright`: 0 errors
- `ruff check`: clean
- Anti-placeholder scan: clean

### Reviewer Output

- Findings by severity: None
- Open questions:
  - None
- Verdict: `approved`
- Residual risk:
  - Administrative state artifacts still show pre-validation status in `task.md`, the MEU registry, and the per-MEU handoff reviewer sections. That is a workflow-state update issue, not an implementation defect in the reviewed code.
- Anti-deferral scan result: Clean
