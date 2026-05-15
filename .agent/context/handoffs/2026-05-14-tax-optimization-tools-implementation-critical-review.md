---
date: "2026-05-14"
review_mode: "handoff"
target_plan: "docs/execution/plans/2026-05-14-tax-optimization-tools/implementation-plan.md"
target_handoff: ".agent/context/handoffs/2026-05-14-tax-optimization-tools-handoff.md"
verdict: "approved"
findings_count: 4
template_version: "2.1"
requested_verbosity: "standard"
agent: "GPT-5.5 Codex"
---

# Critical Review: 2026-05-14 Tax Optimization Tools

> **Review Mode**: `handoff`
> **Verdict**: `approved`

---

## Scope

**Target**: `.agent/context/handoffs/2026-05-14-tax-optimization-tools-handoff.md`
**Correlated Plan**: `docs/execution/plans/2026-05-14-tax-optimization-tools/`
**Review Type**: implementation handoff review
**Checklist Applied**: IR-1 through IR-6, execution-critical-review workflow

Correlation rationale: the handoff frontmatter names project `2026-05-14-tax-optimization-tools` and MEU-137 through MEU-142, matching the plan folder and `task.md` frontmatter. No sibling work handoff for this slug was found; the plan does not declare a multi-handoff `Handoff Naming` set. Scope expanded to the correlated plan, `task.md`, reflection, metrics, MEU registry, claimed production modules, and claimed test files.

---

## Findings

| # | Severity | Finding | File:Line | Recommendation | Status |
|---|----------|---------|-----------|----------------|--------|
| 1 | High | `simulate_tax_impact()` does not detect wash-sale risk for the normal pre-trade path. It builds a simulated closed loss lot with `close_date=lot.close_date`; for open lots that is `None`, and the later guard skips `detect_wash_sales()` unless `simulated_lot.close_date is not None`. A focused probe with an old loss lot plus a same-ticker replacement bought 10 days ago returned `wash_warning_count=0`, so AC-137.6 is not satisfied. | `packages/core/src/zorivest_core/domain/tax/tax_simulator.py:207`, `packages/core/src/zorivest_core/domain/tax/tax_simulator.py:217`; missing positive coverage at `tests/unit/domain/tax/test_tax_simulator.py:276` | Set a source-backed hypothetical sale date for simulation, pass it as `close_date` to the simulated loss lot, and add a positive AC-137.6 test asserting a recent replacement lot produces a `WashSaleMatch`. | fixed |
| 2 | High | `scan_harvest_candidates()` claims to respect `tax_profile.wash_sale_method`, but the implementation never reads that field and filters `all_lots` to exact ticker equality before doing its own 30-day purchase scan. In conservative mode, an option on the same underlying is substantially identical according to the shared detector, but the scanner returns `wash_blocked=False`. This violates AC-138.8 and under-warns users. | `packages/core/src/zorivest_core/domain/tax/harvest_scanner.py:66`, `packages/core/src/zorivest_core/domain/tax/harvest_scanner.py:126`; detector contract at `packages/core/src/zorivest_core/domain/tax/wash_sale_detector.py:73` | Reuse `detect_wash_sales()` or the same matching helper with `tax_profile.wash_sale_method`; add conservative/aggressive tests proving option-trigger handling differs by method. | fixed |
| 3 | Medium | IR-5 test rigor gap: the test suite is mostly useful, but the two highest-risk wash-sale contracts have only negative or shallow coverage. `test_tax_simulator.py` asserts only the no-recent-purchase case for AC-137.6, and `test_harvest_scanner.py` asserts exact-ticker recent purchase blocking but has no AC-138.8 test for matching mode. Some shape tests use `hasattr`, and `test_known_ticker_returns_suggestions()` can pass on any non-empty result because of `or len(tickers) > 0`. These gaps let Findings 1 and 2 pass green. | `tests/unit/domain/tax/test_tax_simulator.py:136`, `tests/unit/domain/tax/test_tax_simulator.py:276`, `tests/unit/domain/tax/test_harvest_scanner.py:220`, `tests/unit/domain/tax/test_replacement_suggestions.py:84` | Strengthen AC mapping tests: positive wash-sale warnings for simulator, conservative/aggressive scanner behavior, exact replacement expectations without fallback disjunctions, and value-level dataclass assertions where shape matters. | fixed |
| 4 | Low | Handoff evidence is not fully auditable and is now internally stale. The handoff claims tasks 23, 25, and 26 are deferred, while `task.md` marks them complete and the reflection/metrics exist. The MEU gate advisory also reports the handoff is missing `Evidence/FAIL_TO_PASS`, `Pass-fail/Commands`, and `Commands/Codex Report` sections. This does not create a runtime defect, but it weakens review traceability. | `.agent/context/handoffs/2026-05-14-tax-optimization-tools-handoff.md:50`, `.agent/context/handoffs/2026-05-14-tax-optimization-tools-handoff.md:72`, `.agent/context/handoffs/2026-05-14-tax-optimization-tools-handoff.md:74` | Update the work handoff during corrections or add a corrections handoff with explicit FAIL_TO_PASS evidence, final command outputs, and accurate closeout status. | fixed |

---

## Checklist Results

### Implementation Review

| Check | Result | Evidence |
|-------|--------|----------|
| IR-1 Live runtime evidence | partial | Pure domain modules have unit tests; no dependency-overridden runtime surface is in scope. Focused behavioral probes found two contract failures. |
| IR-2 Stub behavioral compliance | n/a | No stubs introduced in the reviewed scope. |
| IR-3 Error mapping completeness | n/a | No API/write routes in scope. |
| IR-4 Fix generalization | fail | Wash-sale behavior was implemented separately in simulator/scanner instead of generalizing through the existing detector, causing inconsistent behavior. |
| IR-5 Test rigor audit | fail | Two weak/missing high-risk assertion areas found. Ratings: `test_lot_matcher.py` Strong; `test_rate_comparison.py` Strong/Adequate; `test_lot_reassignment.py` Adequate; `test_replacement_suggestions.py` Adequate with one weak assertion; `test_tax_simulator.py` Weak for AC-137.6; `test_harvest_scanner.py` Weak for AC-138.8. |
| IR-6 Boundary validation coverage | n/a | Domain-only pure functions; no external input boundary, Pydantic model, Zod schema, REST body, MCP input, UI form, file import, or env/config write surface added. |

### Evidence And Claims

| Check | Result | Evidence |
|-------|--------|----------|
| Handoff-plan correlation | pass | Date/slug and MEU set match between handoff and plan/task frontmatter. |
| Claimed files exist | pass | All 6 production modules, 6 test files, and `tax/__init__.py` exist. |
| Blocking gates | pass | `pyright packages/`, `ruff check packages/`, and MEU gate all passed. |
| Targeted tests | pass with gaps | 73 reviewed test functions passed, but focused probes reproduced missing asserted behavior. |
| Evidence bundle completeness | fail | MEU gate advisory reports missing handoff evidence sections. |

---

## Commands Executed

| Command / Receipt | Result |
|-------------------|--------|
| `C:\Temp\zorivest\review-discovery.txt` | Correlated seed handoff and plan; noted broad dirty worktree from prior phases. |
| `C:\Temp\zorivest\pytest-tax-opt-review.txt` | `73 passed, 1 warning in 0.40s` for the six reviewed tax optimization test files. |
| `C:\Temp\zorivest\wash-sim-probe.txt` | Reproduced Finding 1: `wash_warning_count= 0` with a loss sale and recent same-ticker replacement lot. |
| `C:\Temp\zorivest\harvest-method-probe.txt` | Reproduced Finding 2: conservative option replacement scenario returned `wash_blocked= False`. |
| `C:\Temp\zorivest\wash-detector-option-probe.txt` | Confirmed shared detector would match the same option scenario: `detector_matches= [WashSaleMatch(...)]`. |
| `C:\Temp\zorivest\static-gates-review.txt` | `pyright`: 0 errors; `ruff`: all checks passed; anti-placeholder scan had no matches. |
| `C:\Temp\zorivest\validate-review.txt` | MEU gate passed 8/8 blocking checks; advisory A3 flagged missing evidence sections in the work handoff. |

---

## Verdict

`changes_required` - The blocking quality gates pass, but two tax-contract behaviors are wrong or unimplemented on the paths users would depend on: simulator wash-sale warnings and harvest-scanner matching-mode behavior. Both need correction through `/execution-corrections`, with tests added before production changes.

Residual risk: I did not run the full `pytest tests/` regression separately because the MEU gate already ran its configured unit/TS checks and passed. The review was targeted to the Phase 3C domain modules and did not assess unrelated dirty worktree changes from prior tax phases.

---

## Corrections Applied — 2026-05-14

**Agent:** Gemini (Antigravity)
**Verdict:** `corrections_applied`

### Summary

All 4 findings corrected via TDD discipline (tests first → Red → Green → regression).

### FAIL_TO_PASS Evidence

| Finding | Test | Red Phase Failure | Green Phase |
|---------|------|-------------------|-------------|
| 1 | `test_wash_sale_warning_with_recent_purchase` | `AssertionError: assert 0 >= 1` — wash warnings empty because `close_date=None` on simulated lot caused `detect_wash_sales()` to bail out | PASSED after setting `close_date=datetime.now(utc)` |
| 2 | `test_conservative_option_blocks_harvest` | `AssertionError: assert False is True` — option on same underlying not detected because scanner used exact ticker equality | PASSED after importing `_is_substantially_identical()` from shared detector |
| 2 | `test_aggressive_option_does_not_block` | Not run (stopped at first failure) | PASSED — aggressive mode correctly ignores options |
| 3 | Assertion strengthening | N/A (not behavioral change) | All assertions pass with `isinstance` checks |

### Changes Made

| File | Change |
|------|--------|
| `packages/core/src/zorivest_core/domain/tax/tax_simulator.py` | Added `from datetime import datetime, timezone`; set `close_date=now` (hypothetical sale date) on simulated lot; removed stale `close_date is not None` guard |
| `packages/core/src/zorivest_core/domain/tax/harvest_scanner.py` | Added import of `_is_substantially_identical` from wash sale detector; replaced ticker-equality filter with shared matcher that respects `tax_profile.wash_sale_method`; updated wash reason message |
| `tests/unit/domain/tax/test_tax_simulator.py` | Added positive AC-137.6 test (`test_wash_sale_warning_with_recent_purchase`); replaced `hasattr` shape tests with `isinstance` type checks |
| `tests/unit/domain/tax/test_harvest_scanner.py` | Added AC-138.8 tests (`test_conservative_option_blocks_harvest`, `test_aggressive_option_does_not_block`); replaced `hasattr` shape tests with `isinstance` type checks |
| `tests/unit/domain/tax/test_replacement_suggestions.py` | Removed tautological `or len(tickers) > 0` fallback from `test_known_ticker_returns_suggestions` |

### Verification Results

| Check | Result |
|-------|--------|
| Tax module tests | 149 passed, 0 failed |
| Full repo regression | 3,548 passed, 23 skipped, 0 failed |
| pyright (touched files) | 0 errors, 0 warnings |
| ruff (touched files) | All checks passed |

### Cross-Doc Sweep

No contract or architectural pattern changes — the fix generalizes existing wash-sale detection to the two consumers that were bypassing it. No documentation references to update.

---

## Recheck (2026-05-14)

**Workflow**: `/execution-critical-review` recheck  
**Agent**: GPT-5.5 Codex  
**Verdict**: `approved`

### Prior Finding Recheck

| Finding | Prior Status | Recheck Result |
|---------|--------------|----------------|
| F1: `simulate_tax_impact()` wash-sale warnings skipped | fixed | Fixed. Current code sets `close_date=now` on the simulated loss lot and removed the stale `close_date is not None` guard. Focused probe returned `wash_warning_count=1` with `replacement_lot_id='RECENT'`. |
| F2: `scan_harvest_candidates()` ignores `wash_sale_method` | fixed | Fixed. Current code uses shared substantially-identical matching with `tax_profile.wash_sale_method`. Focused probe returned `conservative_blocked=True` and `aggressive_blocked=False`. |
| F3: IR-5 test rigor gaps | fixed | Fixed for the previously weak paths. Added positive simulator wash-sale warning coverage, conservative/aggressive scanner tests, type assertions in shape tests, and removed the tautological replacement-suggestion assertion fallback. |
| F4: Handoff evidence stale/incomplete | fixed for correction evidence | The canonical review file now contains FAIL_TO_PASS evidence, changed-file summaries, and recheck command evidence. The original work handoff still lacks template evidence sections, but the correction/recheck record is auditable and no longer blocks approval. |

### Commands Executed

| Receipt | Result |
|---------|--------|
| `C:\Temp\zorivest\recheck-pytest-tax-domain.txt` | `149 passed, 1 warning in 0.54s` |
| `C:\Temp\zorivest\recheck-focused-probes.txt` | Simulator probe: `wash_warning_count= 1`; scanner probe: `conservative_blocked= True`, `aggressive_blocked= False` |
| `C:\Temp\zorivest\recheck-static-gates.txt` | `pyright`: 0 errors; `ruff`: all checks passed; anti-placeholder scan had no matches |
| `C:\Temp\zorivest\recheck-validate.txt` | MEU gate passed 8/8 blocking checks; advisory A3 still flags original handoff evidence shape |
| `C:\Temp\zorivest\recheck-pytest-full-2.txt` | `3548 passed, 23 skipped, 3 warnings in 194.15s` |

### Residual Risk

No blocking residual risk found in the corrected Phase 3C scope. The scanner now imports `_is_substantially_identical`, a private helper from `wash_sale_detector.py`; it is acceptable for this domain-internal correction, but a future cleanup could expose a public matcher helper if more consumers need this contract.

### Verdict

`approved` — All four prior findings are resolved with executable evidence. No product files were modified during this recheck.
