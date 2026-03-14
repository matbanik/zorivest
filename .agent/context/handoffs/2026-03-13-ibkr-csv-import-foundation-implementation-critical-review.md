# Task Handoff Template

## Task

- **Date:** 2026-03-13
- **Task slug:** ibkr-csv-import-foundation-implementation-critical-review
- **Owner role:** reviewer
- **Scope:** Correlated implementation review of `061-2026-03-13-ibkr-adapter-bpMs50e.md` and `062-2026-03-13-csv-import-bpMs53e.md`, expanded to the shared plan folder and claimed code/doc artifacts

## Inputs

- User request: Critically review `.agent/workflows/critical-review-feedback.md`, `.agent/context/handoffs/061-2026-03-13-ibkr-adapter-bpMs50e.md`, and `.agent/context/handoffs/062-2026-03-13-csv-import-bpMs53e.md`
- Specs/docs referenced: `SOUL.md`, `AGENTS.md`, `.agent/context/current-focus.md`, `.agent/context/known-issues.md`, `.agent/workflows/critical-review-feedback.md`, `docs/execution/plans/2026-03-13-ibkr-csv-import-foundation/implementation-plan.md`, `docs/execution/plans/2026-03-13-ibkr-csv-import-foundation/task.md`, `.agent/context/handoffs/TEMPLATE.md`, `docs/BUILD_PLAN.md`, `docs/build-plan/testing-strategy.md`
- Constraints: Review-only session; no product changes; use findings-first output and canonical review-file naming

## Role Plan

1. orchestrator
2. tester
3. reviewer

## Coder Output

- Changed files: No product changes; review-only
- Design notes / ADRs referenced: None added by this pass
- Commands run: None
- Results: N/A

## Tester Output

- Scope / correlation:
  - The user provided both MEU handoffs explicitly.
  - Both handoffs point to the same execution plan folder: `docs/execution/plans/2026-03-13-ibkr-csv-import-foundation/`.
  - `implementation-plan.md` also declares both handoff paths under `## Handoff Files`, so this review used the full correlated project scope rather than treating either handoff as standalone.
- Commands run:
  - `git status --short`
  - `git status --short -- packages/core/src/zorivest_core/domain/enums.py packages/core/src/zorivest_core/domain/import_types.py packages/core/src/zorivest_core/application/ports.py packages/core/src/zorivest_core/services/import_service.py packages/infrastructure/src/zorivest_infra/broker_adapters tests/conftest.py tests/unit/test_ibkr_flexquery.py tests/unit/test_ports.py tests/unit/test_csv_import.py .agent/context/meu-registry.md docs/execution/plans/2026-03-13-ibkr-csv-import-foundation`
  - `uv run pytest tests/unit/test_ibkr_flexquery.py -q`
  - `uv run pytest tests/unit/test_csv_import.py -q`
  - `uv run pytest tests/unit/test_ports.py -q`
  - `uv run pytest tests/ --tb=no -q`
  - `uv run pyright packages/core/src/zorivest_core/domain/enums.py packages/core/src/zorivest_core/domain/import_types.py packages/core/src/zorivest_core/application/ports.py packages/core/src/zorivest_core/services/import_service.py packages/infrastructure/src/zorivest_infra/broker_adapters/`
  - `uv run ruff check packages/core/src/zorivest_core/domain/enums.py packages/core/src/zorivest_core/domain/import_types.py packages/core/src/zorivest_core/application/ports.py packages/core/src/zorivest_core/services/import_service.py packages/infrastructure/src/zorivest_infra/broker_adapters/ tests/conftest.py tests/unit/test_ibkr_flexquery.py tests/unit/test_ports.py tests/unit/test_csv_import.py`
  - `uv run python tools/validate_codebase.py --scope meu`
  - `rg -n "MEU-96|MEU-99|P2.75 -- Expansion|ibkr-adapter|csv-import|60\\b|58\\b" .agent/context/meu-registry.md docs/BUILD_PLAN.md docs/execution/metrics.md`
  - `rg -n "Role Plan|Reviewer Output|Approval Gate|Evidence bundle location|FAIL_TO_PASS|Mutation score|Contract verification status" .agent/context/handoffs/061-2026-03-13-ibkr-adapter-bpMs50e.md .agent/context/handoffs/062-2026-03-13-csv-import-bpMs53e.md`
  - Inline repro: import a BOM CSV through `ImportService.import_file(...)`
  - Inline repro: `IBKRFlexQueryAdapter._normalize_symbol("AAPL  260320C00200500", "OPT")`
- Pass/fail matrix:
  - `test_ibkr_flexquery.py`: PASS (`33 passed`)
  - `test_csv_import.py`: PASS (`31 passed`)
  - `test_ports.py`: PASS (`18 passed`)
  - Full regression: PASS (`1230 passed, 1 skipped`)
  - Pyright: PASS (`0 errors, 0 warnings, 0 informations`)
  - Ruff: PASS (`All checks passed!`)
  - MEU gate: PASS on blocking checks, but advisory warning reported missing handoff evidence sections for `062-2026-03-13-csv-import-bpMs53e.md`
- Repro failures:
  - BOM fixture shape used by `tests/unit/test_csv_import.py:253-265` fails through the real import entrypoint: inline repro returned `ERR No registered CSV parser matched the file headers`
  - Fractional strike normalization repro returned `AAPL 260320 C 200` for input `AAPL  260320C00200500`
- Coverage/test gaps:
  - AC-10 evidence only exercises parser-level `parse_file()`, not the actual `ImportService.import_file()` auto-detect path
  - AC-9 tests only assert that `UnknownBrokerFormat` is raised; they never verify the promised header-bearing message
  - AC-3 tests only assert substrings in the normalized option symbol, so fractional-strike loss is not detected
- Evidence bundle location: This review handoff
- FAIL_TO_PASS / PASS_TO_PASS result: N/A (review-only)
- Mutation score: Not run
- Contract verification status: `changes_required`

## Reviewer Output

- Findings by severity:
  - **High** - The project-level handoff set overstates completion. Both handoffs conclude `Implementation complete` at `061-2026-03-13-ibkr-adapter-bpMs50e.md:72-75` and `062-2026-03-13-csv-import-bpMs53e.md:70-73`, but the correlated task still leaves every post-MEU deliverable unchecked at `docs/execution/plans/2026-03-13-ibkr-csv-import-foundation/task.md:21-29`. The canonical docs were not updated either: `docs/BUILD_PLAN.md:311` and `docs/BUILD_PLAN.md:314` still show MEU-96/99 as `⬜`, `docs/BUILD_PLAN.md:472-476` still reports P2.75 completed `0` / total completed `58`, `rg -n "MEU-96|MEU-99" .agent/context/meu-registry.md` returned no hits, and `docs/execution/reflections/2026-03-13-ibkr-csv-import-reflection.md` does not exist. Under the workflow's docs-review severity guidance, this is a false completion claim, not just a wording issue.
  - **High** - `IBKRFlexQueryAdapter` corrupts fractional option strikes. The design note in `061-2026-03-13-ibkr-adapter-bpMs50e.md:34-38` says strike conversion is `strike ÷ 1000`, but the implementation uses integer floor division at `packages/infrastructure/src/zorivest_infra/broker_adapters/ibkr_flexquery.py:237-244` (`strike_int // 1000`). Reproducing `_normalize_symbol("AAPL  260320C00200500", "OPT")` returns `AAPL 260320 C 200`, which drops the `.5` component. The existing AC-3 test only checks loose substrings at `tests/unit/test_ibkr_flexquery.py:117-125`, so this data-loss bug currently ships undetected.
  - **Medium** - AC-10 is not actually verified against the real import path. `062-2026-03-13-csv-import-bpMs53e.md:60-61` claims BOM/Latin-1 encoding is covered, but the cited BOM test at `tests/unit/test_csv_import.py:253-265` only calls `NinjaTraderCSVParser.parse_file(...)`. The actual entrypoint is `ImportService.import_file(...)`, whose auto-detect path separately reads headers at `packages/core/src/zorivest_core/services/import_service.py:94-117`. Replaying the same BOM fixture shape through `ImportService` returns `ERR No registered CSV parser matched the file headers`, so the handoff evidence does not prove the acceptance criterion it claims to close.
  - **Medium** - The implementation does not satisfy the AC-9 error-message contract, and the tests are too weak to catch it. The execution plan requires `Unknown CSV format raises UnknownBrokerFormat with headers in error message` at `docs/execution/plans/2026-03-13-ibkr-csv-import-foundation/implementation-plan.md:279`, but `ImportService.auto_detect_csv_broker()` raises a generic message with no header payload at `packages/core/src/zorivest_core/services/import_service.py:116-117`. The tests at `tests/unit/test_csv_import.py:211-237` only assert that an exception is raised, so the contract drift is currently invisible to the suite.
  - **Medium** - The handoff artifacts themselves are not template-complete and fail the repo's evidence-bundle checks. The required template sections live at `.agent/context/handoffs/TEMPLATE.md:16-22`, `.agent/context/handoffs/TEMPLATE.md:31-40`, `.agent/context/handoffs/TEMPLATE.md:42-48`, and `.agent/context/handoffs/TEMPLATE.md:56-61`, but neither `061-2026-03-13-ibkr-adapter-bpMs50e.md` nor `062-2026-03-13-csv-import-bpMs53e.md` contains `Role Plan`, `Reviewer Output`, or `Approval Gate`. This is consistent with the gate's advisory rule definitions in `tools/validate_codebase.py:38-40`, and `uv run python tools/validate_codebase.py --scope meu` reported `062-2026-03-13-csv-import-bpMs53e.md missing: Evidence/FAIL_TO_PASS, Pass-fail/Commands, Commands/Codex Report`.
- Open questions:
  - None required to confirm the current findings.
- Verdict:
  - `changes_required`
- Residual risk:
  - The code compiles and the current regression suite is green, so the remaining risk is concentrated in auditability and edge-case parsing correctness rather than broad runtime instability.
  - `ImportService` is still only unit-tested here; broader service-layer canon in `docs/build-plan/testing-strategy.md:293-318` expects integration coverage once persistence/dedup behavior is added.
- Anti-deferral scan result:
  - No hidden deferral language found in the implementation review itself. The issue is the opposite: the handoffs claim completion before the project closeout artifacts exist.

## Guardrail Output (If Required)

- Safety checks: Not required
- Blocking risks: N/A
- Verdict: N/A

## Approval Gate

- **Human approval required for merge/release/deploy:** yes
- **Approval status:** pending
- **Approver:**
- **Timestamp:**

## Final Summary

- Status: `changes_required`
- Next steps:
  - Fix fractional-strike normalization and add an exact-value regression test
  - Either strengthen AC-10 to cover the real `ImportService` auto-detect path or narrow the claim so the handoff does not overstate BOM coverage
  - Include actual headers in `UnknownBrokerFormat` errors if AC-9 remains part of the plan, and add an assertion for that message
  - Finish the post-MEU deliverables (`BUILD_PLAN.md`, `meu-registry.md`, reflection, metrics, notes/commit prep) before calling the correlated project complete
  - Reissue the MEU handoffs in template-complete form or update them so the evidence-bundle gate no longer warns

---

## Corrections Applied — 2026-03-13

### Summary

4 of 5 findings resolved. F1 (post-MEU deliverables) deferred to project closeout step.

### Changes Made

| Finding | Fix | Files Changed |
|---|---|---|
| **F2** (High) — Fractional strike floor division | `// 1000` → `/ 1000` with `.5` preservation | `ibkr_flexquery.py:237-244` |
| **F2** test — Weak substring assertions | Exact equality + fractional strike regression test | `test_ibkr_flexquery.py:117-129` |
| **F3** (Medium) — BOM only tested at parser level | Added `test_bom_csv_through_import_service` through `ImportService.import_file()` | `test_csv_import.py:266-284` |
| **F3** test fixture — Double BOM bug | Removed `\ufeff` from content when using `utf-8-sig` encoding | `test_csv_import.py:253-262` |
| **F4** (Medium) — Headers missing from error message | Include first 3 CSV lines in `UnknownBrokerFormat` message | `import_service.py:116-123` |
| **F4** test — No message assertion | Added `match="col_a"` to `pytest.raises` | `test_csv_import.py:218` |
| **F5** (Medium) — Missing handoff template sections | Added Role Plan, Reviewer Output, Approval Gate to both handoffs | `061-*.md`, `062-*.md` |
| **F1** (High) — Post-MEU deliverables | **Deferred** to project closeout step (standard workflow) | — |

### Verification Results

```
uv run pytest tests/unit/test_ibkr_flexquery.py tests/unit/test_csv_import.py -q   # 66 passed
uv run pytest tests/ --tb=no -q                                                     # 1232 passed, 1 skipped
uv run pyright .../import_service.py .../broker_adapters/                            # 0 errors
uv run ruff check <all touched files>                                                # All checks passed!
```

### Verdict

`corrections_applied` — ready for re-review. F1 (post-MEU deliverables) to be completed after Codex approval.

---

## Corrections Applied (2) — 2026-03-13

### Summary

Resolved both remaining findings from recheck: F1 (post-MEU deliverables) and F2 (stale evidence).

### Changes Made

| Finding | Fix | Files Changed |
|---|---|---|
| **F1** (High) — Post-MEU deliverables | Updated BUILD_PLAN.md (⬜→✅, 58→60), added P2.75 section to meu-registry.md, created reflection, added metrics row, marked task.md complete | `BUILD_PLAN.md`, `meu-registry.md`, `metrics.md`, `task.md`, `2026-03-13-ibkr-csv-import-reflection.md` [NEW] |
| **F2** (Low) — Stale evidence counts | Refreshed test counts: MEU-96 33→34, MEU-99 31→32, regression 1230→1232 | `061-*.md`, `062-*.md` |

### Commit Messages

```
feat(infra): add IBKR FlexQuery XML adapter (MEU-96)

- IBKRFlexQueryAdapter with defusedxml XXE prevention
- OCC symbol normalization (fractional strikes preserved)
- Multi-currency via fxRateToBase, ADR-0003 graceful degradation
- 34 unit tests covering all 8 FIC-96 acceptance criteria
```

```
feat(infra): add CSV import framework + auto-detection (MEU-99)

- CSVParserBase ABC with chardet encoding detection + BOM handling
- ThinkorSwimCSVParser (multi-section, option symbol normalization)
- NinjaTraderCSVParser (pre-paired round-trips, MFE/MAE)
- ImportService orchestrator with header-based auto-detection
- 32 unit tests covering all 10 FIC-99 acceptance criteria
```

```
docs: complete MEU-96/99 project closeout

- BUILD_PLAN.md: MEU-96/99 ✅, total 60/170
- meu-registry.md: P2.75 section added
- Reflection + metrics row added
- Handoff evidence refreshed (34+32 tests, 1232 regression)
```

### Verdict

`corrections_applied` — all findings resolved. Ready for final re-review.

---

## Recheck — 2026-03-13

### Scope

Rechecked the prior findings after the appended corrections note above. Reviewed the updated `import_service.py`, `ibkr_flexquery.py`, the affected unit tests, both MEU handoffs, the shared task file, and the canonical closeout artifacts (`BUILD_PLAN.md`, `meu-registry.md`, `metrics.md`, reflection path).

### Commands

```text
uv run pytest tests/unit/test_ibkr_flexquery.py -q
uv run pytest tests/unit/test_csv_import.py -q
uv run pytest tests/ --tb=no -q
uv run pyright packages/core/src/zorivest_core/domain/enums.py packages/core/src/zorivest_core/domain/import_types.py packages/core/src/zorivest_core/application/ports.py packages/core/src/zorivest_core/services/import_service.py packages/infrastructure/src/zorivest_infra/broker_adapters/
uv run ruff check packages/core/src/zorivest_core/domain/enums.py packages/core/src/zorivest_core/domain/import_types.py packages/core/src/zorivest_core/application/ports.py packages/core/src/zorivest_core/services/import_service.py packages/infrastructure/src/zorivest_infra/broker_adapters/ tests/conftest.py tests/unit/test_ibkr_flexquery.py tests/unit/test_ports.py tests/unit/test_csv_import.py
uv run python tools/validate_codebase.py --scope meu
rg -n "MEU-96|MEU-99|P2.75 -- Expansion|Total\\*\\*|2026-03-13 \\| MEU-96|2026-03-13 \\| MEU-99|2026-03-13 \\| MEU-96/99|ibkr-csv-import" docs/BUILD_PLAN.md .agent/context/meu-registry.md docs/execution/metrics.md
```

### Verification Snapshot

- `test_ibkr_flexquery.py`: PASS (`34 passed`)
- `test_csv_import.py`: PASS (`32 passed`)
- Full regression: PASS (`1232 passed, 1 skipped`)
- Pyright: PASS (`0 errors, 0 warnings, 0 informations`)
- Ruff: PASS (`All checks passed!`)
- MEU gate: PASS on blocking checks, advisory evidence-bundle check now passes against this canonical review file
- Inline repro: BOM CSV through `ImportService.import_file(...)` now succeeds (`ninjatrader 1`)
- Inline repro: `_normalize_symbol("AAPL  260320C00200500", "OPT")` now returns `AAPL 260320 C 200.5`
- Inline repro: unknown CSV error now includes sampled headers (`['col_a,col_b,col_c', '1,2,3']`)

### Findings

- **High** — The remaining project closeout work is still undone, so the implementation set is not yet complete enough to approve. The shared task still leaves every post-MEU deliverable unchecked at `docs/execution/plans/2026-03-13-ibkr-csv-import-foundation/task.md:21-29`. The canonical build-plan state is still stale at `docs/BUILD_PLAN.md:311`, `docs/BUILD_PLAN.md:314`, `docs/BUILD_PLAN.md:472`, and `docs/BUILD_PLAN.md:476`, and `docs/execution/reflections/2026-03-13-ibkr-csv-import-reflection.md` is still missing. Because the MEU handoffs still summarize the work as `Implementation complete`, this remains a false-completion / incomplete-closeout issue rather than a resolved follow-up.
- **Low** — The MEU handoff evidence is now stale after the correction pass. `061-2026-03-13-ibkr-adapter-bpMs50e.md:55-75` still reports `33` MEU tests and `1230` full-regression passes, and `062-2026-03-13-csv-import-bpMs53e.md:50-73` still reports `31` and `1230`, but the reproduced current state is `34`, `32`, and `1232`. This is an auditability issue, not a runtime defect.

### Verdict

`changes_required`

### Follow-Up

1. Complete the post-MEU deliverables listed in `task.md`.
2. Update `BUILD_PLAN.md`, `meu-registry.md`, and `metrics.md`, and add the missing reflection file.
3. Refresh the two MEU handoffs so their test-count/regression evidence matches the corrected code state.

---

## Final Recheck — 2026-03-13

### Scope

Rechecked the remaining closeout findings from the prior section. Reviewed `task.md`, `BUILD_PLAN.md`, `meu-registry.md`, `metrics.md`, `docs/execution/reflections/2026-03-13-ibkr-csv-import-reflection.md`, the two MEU handoffs, and the current MEU gate output. Also verified a matching Pomera session note exists for the project (`Memory/Session/IBKR-CSV-Import-Foundation-2026-03-13`, note `#517`).

### Commands

```text
git diff -- docs/BUILD_PLAN.md .agent/context/meu-registry.md docs/execution/metrics.md docs/execution/reflections/2026-03-13-ibkr-csv-import-reflection.md docs/execution/plans/2026-03-13-ibkr-csv-import-foundation/task.md .agent/context/handoffs/061-2026-03-13-ibkr-adapter-bpMs50e.md .agent/context/handoffs/062-2026-03-13-csv-import-bpMs53e.md .agent/context/handoffs/2026-03-13-ibkr-csv-import-foundation-implementation-critical-review.md
uv run python tools/validate_codebase.py --scope meu
rg -n "34 passed|32 passed|1232 passed|MEU-96/99|58→60|P2.75|Codex caught fractional strike|TDD discipline held" .agent/context/handoffs/061-2026-03-13-ibkr-adapter-bpMs50e.md .agent/context/handoffs/062-2026-03-13-csv-import-bpMs53e.md docs/execution/metrics.md docs/execution/reflections/2026-03-13-ibkr-csv-import-reflection.md .agent/context/meu-registry.md docs/BUILD_PLAN.md
pomera_notes search: ibkr
```

### Verification Snapshot

- `task.md` post-MEU checklist is now fully checked
- `BUILD_PLAN.md` now marks MEU-96/99 as `✅` and updates P2.75 / total completed counts to `2` / `60`
- `meu-registry.md` now includes a P2.75 section for MEU-96 and MEU-99
- `metrics.md` now has a `2026-03-13 | MEU-96/99` row
- `docs/execution/reflections/2026-03-13-ibkr-csv-import-reflection.md` now exists and is populated
- `061-2026-03-13-ibkr-adapter-bpMs50e.md` now reports `34 passed` and `1232 passed, 1 skipped`
- `062-2026-03-13-csv-import-bpMs53e.md` now reports `32 passed` and `1232 passed, 1 skipped`
- MEU gate still passes, and the evidence-bundle advisory now reports all required fields present in this canonical review file
- Pomera notes search found `Memory/Session/IBKR-CSV-Import-Foundation-2026-03-13` (`#517`)

### Findings

- No findings.

### Verdict

`approved`

### Residual Risk

- Low. This project is well-covered at the unit-test level and the closeout artifacts now align with the implemented state.
- Future import/persistence MEUs should still add the broader integration coverage described in `docs/build-plan/testing-strategy.md`, but that is not a blocker for MEU-96/99.
