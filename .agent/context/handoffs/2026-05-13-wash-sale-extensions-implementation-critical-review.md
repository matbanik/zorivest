---
date: "2026-05-13"
review_mode: "handoff"
target_plan: "docs/execution/plans/2026-05-13-wash-sale-extensions/implementation-plan.md"
verdict: "approved"
findings_count: 0
template_version: "2.1"
requested_verbosity: "standard"
agent: "GPT-5.5 Codex"
---

# Critical Review: 2026-05-13-wash-sale-extensions

> **Review Mode**: `handoff`
> **Verdict**: `approved`

---

## Scope

**Target**: `.agent/context/handoffs/2026-05-13-wash-sale-extensions-handoff.md`
**Correlated Plan**: `docs/execution/plans/2026-05-13-wash-sale-extensions/`
**Review Type**: implementation handoff review
**Checklist Applied**: execution-critical-review IR/DR plus implementation review checks IR-1 through IR-6

Correlation rationale: the supplied handoff and execution plan folder share the same date and slug (`2026-05-13-wash-sale-extensions`) and the same MEU set (MEU-133 through MEU-136). No sibling work handoff for this slug was found, so the seed handoff is the full work-handoff set.

Reviewed artifacts:

- `.agent/context/handoffs/2026-05-13-wash-sale-extensions-handoff.md`
- `docs/execution/plans/2026-05-13-wash-sale-extensions/implementation-plan.md`
- `docs/execution/plans/2026-05-13-wash-sale-extensions/task.md`
- `docs/execution/reflections/2026-05-13-wash-sale-extensions-reflection.md`
- Claimed changed source and test files under `packages/core`, `packages/infrastructure`, `tests/unit/domain/tax`, `tests/unit/services`, and `tests/integration`

---

## Findings

| # | Severity | Finding | File:Line | Recommendation | Status |
|---|----------|---------|-----------|----------------|--------|
| 1 | High | Service-level options-to-stock matching is not actually wired for single-lot detection. `detect_and_apply_wash_sales()` asks the repository for candidates with `ticker=loss_lot.ticker`, so option lots such as `AAPL 260420 C 200` are filtered out before `detect_wash_sales()` can apply the new CONSERVATIVE option matching. A read-only probe returned `[]` for a stock loss plus same-underlying call option, despite AC-133.5 requiring TaxService to pass the wash-sale method through to working detection. | `packages/core/src/zorivest_core/services/tax_service.py:678` | Query candidate lots broadly enough for substantially-identical matching, then let `detect_wash_sales()` filter. Add a TaxService test where a stock loss plus same-underlying option candidate creates a match in CONSERVATIVE mode and no match in AGGRESSIVE mode. | resolved — CONSERVATIVE queries `account_id` (broad); AGGRESSIVE keeps `ticker` filter; 2 tests added |
| 2 | High | Pre-trade alerts implement the wrong direction of wash-sale risk. AC-136.3 says a proposed sale should warn when the sale would realize a loss and there was a recent replacement purchase in the 30-day pre-sale window. The code instead loads recent closed losses and warns about buying after those losses; it does not require the simulated sale to be at a loss. Probe evidence: a simulated gain sale (`gain='250.000'`) still returned `warnings=1` and `wait_days=20`. | `packages/core/src/zorivest_core/services/tax_service.py:424` | In `simulate_impact()`, derive whether selected lots would be sold at a loss, inspect recent open/replacement purchases within the pre-sale window, and suppress alerts for gain-only simulations. Add tests for loss+recent purchase, gain+recent purchase, and loss+old purchase. | resolved — replaced check_conflicts() with sale-side replacement-purchase scanning; 10 tests rewritten to use purchase lots |
| 3 | Medium | `SimulationResult.wash_risk` is not backward-compatible with the new warning model. The plan states `wash_risk` should be computed from `len(wash_sale_warnings) > 0`, but the return value still uses only pre-existing lot wash adjustments. Probe evidence from Finding 2 returned `warnings=1` while `wash_risk=False`. | `packages/core/src/zorivest_core/services/tax_service.py:447` | Set `wash_risk` from existing wash adjustment OR generated warnings, and add an assertion in pre-trade tests that warnings imply `wash_risk is True`. | resolved — `wash_risk = has_wash_risk or len(pre_trade_warnings) > 0`; 2 tests added |
| 4 | Medium | Service-level spousal inclusion is not wired to `TaxProfile.include_spousal_accounts`. `TaxService.check_wash_sale_conflicts()` passes `spousal_lot_ids` but never passes `include_spousal`, so `check_conflicts()` defaults to `include_spousal=True` and cannot honor a profile-level opt-out. Existing tests cover only the pure function, not the service/profile path. | `packages/core/src/zorivest_core/services/tax_service.py:638` | Load the applicable TaxProfile or expose an explicit service parameter, pass `include_spousal` through, and add a service test for `include_spousal_accounts=False`. | resolved — profile loaded in `check_wash_sale_conflicts`, `include_spousal` passed through; 2 tests added |

---

## Evidence

Commands executed:

```text
uv run pytest tests/unit/domain/tax/ tests/unit/services/test_tax_service_wash_sale.py tests/unit/services/test_pre_trade_alerts.py -x --tb=short -q
Result: 90 passed, 1 warning

uv run pytest tests/integration/ -x --tb=short -q
Result: 257 passed, 1 skipped, 2 warnings

uv run python tools/validate_codebase.py --scope meu
Result: 8/8 blocking checks passed
Advisory: Evidence Bundle WARN - 2026-05-13-wash-sale-extensions-handoff.md missing Evidence/FAIL_TO_PASS, Pass-fail/Commands, Commands/Codex Report
```

Read-only probes:

```text
Service option probe:
stock loss AAPL + replacement "AAPL 260420 C 200" through TaxService.detect_and_apply_wash_sales()
Observed: []
Expected by AC-133.5: one match in CONSERVATIVE mode

Pre-trade gain probe:
simulate_impact(... sale_price=155, selected lot cost_basis=150, recent closed loss exists)
Observed: {'warnings': 1, 'wait_days': 20, 'wash_risk': False, 'gain': '250.000'}
Expected by AC-136.3/136.5: gain sale should not generate wash-sale warnings; generated warnings should imply wash_risk=True
```

---

## Checklist Results

### Implementation Review

| Check | Result | Evidence |
|-------|--------|----------|
| IR-1 Live runtime evidence | pass with gaps | Integration suite ran: 257 passed, 1 skipped. No live integration coverage for service-level option candidates or pre-trade warning direction. |
| IR-2 Stub behavioral compliance | n/a | No stubs in reviewed implementation path. |
| IR-3 Error mapping completeness | n/a | No REST/API route changes in this MEU set. |
| IR-4 Fix generalization | fail | New domain detector behavior was not generalized into `TaxService.detect_and_apply_wash_sales()` candidate retrieval. |
| IR-5 Test rigor audit | fail | `test_pre_trade_alerts.py` is weak for AC-136: it asserts warnings on a gain sale and does not assert `wash_risk`. `test_tax_service_wash_sale.py` is adequate for prior MEUs but misses new service-level option/profile wiring. `test_wash_sale_detector.py`, `test_wash_sale_warnings.py`, and persistence tests are mostly strong for pure-domain/persistence behavior. |
| IR-6 Boundary validation coverage | n/a | No external write boundary was added in this domain/service MEU set. |

### Documentation / Handoff Review

| Check | Result | Evidence |
|-------|--------|----------|
| Claim-to-state match | fail | Handoff claims TaxService option and pre-trade wiring is complete; file state/probes show behavioral gaps. |
| Evidence freshness | pass | Reproduced targeted tests, integration tests, and MEU gate on 2026-05-13. |
| Evidence auditability | warn | MEU gate reports the handoff is missing the structured evidence bundle sections: FAIL_TO_PASS, Pass-fail/Commands, Commands/Codex Report. |
| Completion vs residual risk | fail | Handoff says implementation complete; review found contract-level failures. |

---

## Open Questions / Assumptions

- I treated the FIC in `implementation-plan.md` as the governing contract, especially AC-133.5, AC-135.4, AC-136.3, and AC-136.5.
- I did not review or modify unrelated dirty files in the working tree.
- No external tax-law browsing was needed for this pass because the failures are internal contract/wiring mismatches against the local FIC.

---

## Verdict

`changes_required` - blocking behavioral gaps remain in service-level option matching and pre-trade alert semantics. The targeted tests and MEU gate pass, but they do not cover the failing service paths.

Recommended next workflow: `/execution-corrections` for the four open findings above.

---

## Recheck (2026-05-13)

**Workflow**: `/execution-critical-review` recheck  
**Agent**: GPT-5.5 Codex

### Prior Pass Summary

| Finding | Prior Status | Recheck Result |
|---------|--------------|----------------|
| F1 service-level option candidate retrieval | open | Fixed |
| F2 pre-trade alert direction | open | Still open |
| F3 `wash_risk` not derived from warnings | open | Fixed for generated-warning cases |
| F4 service spousal include flag not wired | open | Fixed |

### Confirmed Fixes

- F1 fixed at `packages/core/src/zorivest_core/services/tax_service.py:717`: CONSERVATIVE detection now retrieves same-account candidates broadly enough for option symbols. Probe result: `option_service_matches 1 ['opt']`.
- F3 fixed at `packages/core/src/zorivest_core/services/tax_service.py:452`: `wash_risk` now derives from existing wash adjustment or generated warnings.
- F4 fixed at `packages/core/src/zorivest_core/services/tax_service.py:667`: `include_spousal` is passed through from `TaxProfile.include_spousal_accounts`.
- Regression tests were added for option candidate retrieval, gain-sale suppression, wash-risk derivation, and spousal include wiring.

### Remaining Findings

- **High** — F2 remains partially open. `simulate_impact()` now suppresses warnings for gain sales, but it still loads `recent_closed = self._uow.tax_lots.list_all_filtered(ticker=ticker, is_closed=True)` at `packages/core/src/zorivest_core/services/tax_service.py:433` and delegates to `check_conflicts()` over closed losses. The FIC says the proposed loss sale should warn when there is a recent replacement purchase in the 30-day pre-sale window. Recheck probe evidence: `loss_with_recent_purchase {'warnings': 0, 'wait_days': 0, 'wash_risk': False, 'gain': '-2250.000'}`.
- **Medium** — Test coverage is still missing the exact F2 FIC case: loss-producing sale plus recent open/replacement purchase and no prior closed loss. Current tests cover gain suppression and loss plus recent closed loss, which does not prove AC-136.3.

### Commands Executed

```text
uv run pytest tests/unit/domain/tax/ tests/unit/services/test_tax_service_wash_sale.py tests/unit/services/test_pre_trade_alerts.py -x --tb=short -q
Result: 98 passed, 1 warning

uv run pytest tests/integration/ -x --tb=short -q
Result: 257 passed, 1 skipped, 2 warnings

uv run python tools/validate_codebase.py --scope meu
Result: 8/8 blocking checks passed
Advisory: Evidence Bundle WARN - 2026-05-13-wash-sale-extensions-handoff.md missing Evidence/FAIL_TO_PASS, Pass-fail/Commands, Commands/Codex Report
```

### Verdict

`changes_required` - three findings are fixed, but the core pre-trade alert contract remains wrong for loss sales with recent replacement purchases. Do not approve until AC-136.3 is tested and implemented against recent purchase lots, not recent closed losses.

---

## Corrections Applied (2026-05-13)

**Workflow**: `/execution-corrections`
**Agent**: Antigravity (Gemini)

### Root Cause

`simulate_impact()` called `check_conflicts()` — a **purchase-side** conflict checker that asks "will buying now trigger a wash sale from recent losses?" AC-136.3 requires the inverse **sale-side** question: "will selling at a loss now trigger a wash sale because of recent replacement purchases within the 30-day pre-sale window?"

### Changes

**Production**: `packages/core/src/zorivest_core/services/tax_service.py`

```diff
 # Import
+    WarningType,
     WashSaleWarning,
     check_conflicts,

 # simulate_impact() — replaced check_conflicts() with sale-side logic
-            recent_closed = self._uow.tax_lots.list_all_filtered(
+            all_ticker_lots = self._uow.tax_lots.list_all_filtered(
                 ticker=ticker,
-                is_closed=True,
             )
-            pre_trade_warnings = check_conflicts(
-                ticker=ticker,
-                recent_losses=recent_closed,
-                now=effective_now,
-            )
+            for candidate in all_ticker_lots:
+                if candidate.lot_id in selling_lot_ids:
+                    continue
+                days_since_purchase = (effective_now - candidate.open_date).days
+                if days_since_purchase < 0 or days_since_purchase >= 30:
+                    continue
+                days_remaining = 30 - days_since_purchase
+                pre_trade_warnings.append(WashSaleWarning(...))
```

**Tests**: `tests/unit/services/test_pre_trade_alerts.py`

All 8 tests in `TestSimulateImpactPreTradeAlerts`, `TestWaitDaysComputation`, `TestGainSaleSuppression`, and `TestWashRiskFromWarnings` rewritten to use **replacement purchase lots** instead of **closed loss lots**, matching AC-136.3 contract. Added `test_old_purchase_outside_window_no_alert` (new). Removed unused `Any` and `pytest` imports.

### TDD Evidence

- **RED**: 4 tests failed — `loss_sale_with_recent_purchase_warns`, `wait_days_reflects_max_remaining`, `loss_sale_with_purchase_triggers_warnings`, `warnings_imply_wash_risk_true` (all returned `warnings=[]` because `check_conflicts()` found no closed losses)
- **GREEN**: All 10 tests passed after replacing `check_conflicts()` with sale-side purchase scanning

### Quality Gates (Fresh)

```text
pytest tests/ -x --tb=short:  3323 passed, 23 skipped, 0 failed
pyright tax_service.py:        0 errors, 0 warnings
ruff tax_service.py + tests:   All checks passed
```

### Cross-Doc Sweep

`check_conflicts()` import in `tax_service.py` remains valid — used by `check_wash_sale_conflicts()` (purchase-side method at L686). No other files affected.

### Finding Status

| # | Severity | Status |
|---|----------|--------|
| F1 | High | resolved |
| F2 | High | resolved |
| F3 | Medium | resolved |
| F4 | Medium | resolved |

### Verdict

`corrections_applied` — all 4 findings resolved. Ready for re-review.

---

## Recheck (2026-05-13, Pass 2)

**Workflow**: `/execution-critical-review` recheck  
**Agent**: GPT-5.5 Codex

### Prior Pass Summary

| Finding | Prior Status | Recheck Result |
|---------|--------------|----------------|
| F1 service-level option candidate retrieval | fixed in prior recheck | Fixed |
| F2 pre-trade alert direction | still open in prior recheck | Fixed for the reported FIC scenario |
| F3 `wash_risk` not derived from warnings | fixed in prior recheck | Fixed |
| F4 service spousal include flag not wired | fixed in prior recheck | Fixed |

### Confirmed Fixes

- F2 sale-side logic is now implemented in `packages/core/src/zorivest_core/services/tax_service.py:431`: `simulate_impact()` scans recent replacement purchases when the proposed sale produces a loss, rather than delegating to purchase-side `check_conflicts()`.
- The previous failing probe is now green: `loss_with_recent_purchase {'warnings': 1, 'wait_days': 20, 'wash_risk': True, 'gain': '-2250.000', 'ids': ['recent-purchase']}`.
- Gain-sale suppression still holds: `gain_sale {'warnings': 0, 'wait_days': 0, 'wash_risk': False, 'gain': '2750.000'}`.
- Service-level options matching remains fixed: `option_service_matches 1 ['opt']`.

### Remaining Findings

- **Medium** — The 30-day pre-sale boundary is currently exclusive. `simulate_impact()` skips purchases where `days_since_purchase >= 30` at `packages/core/src/zorivest_core/services/tax_service.py:450`, so a purchase exactly 30 days before the proposed loss sale returns no warning: `loss_with_30_day_purchase {'warnings': 0, 'wait_days': 0, 'wash_risk': False}`. The FIC excludes purchases "older than 30 days" and the domain detector documents the 61-day window as "30 days before + sale day + 30 days after"; that makes the exact 30-day boundary part of the wash-sale window unless a human-approved rule says otherwise.
- **Medium** — Test coverage still lacks the exact 30-day boundary assertion for AC-136.3/AC-136.4. Existing tests cover 10-day, 5-day, 35-day, gain-sale, and no-purchase cases.

### Commands Executed

```text
uv run pytest tests/unit/domain/tax/ tests/unit/services/test_tax_service_wash_sale.py tests/unit/services/test_pre_trade_alerts.py -x --tb=short -q
Result: 99 passed, 1 warning

uv run pytest tests/integration/ -x --tb=short -q
Result: 257 passed, 1 skipped, 2 warnings

uv run python tools/validate_codebase.py --scope meu
Result: 8/8 blocking checks passed
Advisory: Evidence Bundle WARN - 2026-05-13-wash-sale-extensions-handoff.md missing Evidence/FAIL_TO_PASS, Pass-fail/Commands, Commands/Codex Report
```

### Verdict

`changes_required` — the original four findings are resolved, but the exact 30-day boundary in pre-trade sale-side alerts needs a correction or explicit human-approved exception before approval.

---

## Corrections Applied (2026-05-13, Pass 2)

**Workflow**: `/execution-corrections`
**Agent**: Antigravity (Gemini)

### Root Cause

`simulate_impact()` at L450 used `days_since_purchase >= 30` (exclusive boundary), skipping purchases exactly 30 days old. The domain detector (`wash_sale_detector.py:139`) uses inclusive `<=` boundaries. The IRS 61-day window = "30 days before + sale day + 30 days after" — day 30 is part of the window.

### Changes

**Production**: `packages/core/src/zorivest_core/services/tax_service.py:450`

```diff
-                if days_since_purchase < 0 or days_since_purchase >= 30:
+                if days_since_purchase < 0 or days_since_purchase > 30:
```

**Tests**: `tests/unit/services/test_pre_trade_alerts.py`

- Added `test_exact_30_day_boundary_warns` — purchase exactly 30 days ago → warning with `days_remaining=0`
- Added `test_purchase_31_days_ago_no_warning` — day 31 → no warning (outside window)

### TDD Evidence

- **RED**: `test_exact_30_day_boundary_warns` failed (`assert 0 == 1`); `test_purchase_31_days_ago_no_warning` passed
- **GREEN**: Both passed after changing `>= 30` to `> 30`

### Quality Gates (Fresh)

```text
pytest tests/ -x --tb=short:  3325 passed, 23 skipped, 0 failed
pyright tax_service.py:        0 errors, 0 warnings
ruff tax_service.py + tests:   All checks passed
```

### Finding Status

| # | Severity | Status |
|---|----------|--------|
| F1 | High | resolved |
| F2 | High | resolved |
| F3 | Medium | resolved |
| F4 | Medium | resolved |
| F5 | Medium | resolved (30-day boundary inclusive) |
| F6 | Medium | resolved (boundary tests added) |

### Verdict

`corrections_applied` — all 6 findings resolved across 3 passes. Ready for re-review.

---

## Recheck (2026-05-13, Pass 3)

**Workflow**: `/execution-critical-review` recheck  
**Agent**: GPT-5.5 Codex

### Prior Pass Summary

| Finding | Prior Status | Recheck Result |
|---------|--------------|----------------|
| F1 service-level option candidate retrieval | resolved in prior recheck | Fixed |
| F2 pre-trade alert direction | resolved in prior recheck | Fixed |
| F3 `wash_risk` not derived from warnings | resolved in prior recheck | Fixed |
| F4 service spousal include flag not wired | resolved in prior recheck | Fixed |
| F5 exact 30-day pre-sale boundary excluded | open in Pass 2 | Fixed |
| F6 missing exact-boundary test coverage | open in Pass 2 | Fixed |

### Confirmed Fixes

- F5 fixed at `packages/core/src/zorivest_core/services/tax_service.py:450`: `simulate_impact()` now skips purchases only when `days_since_purchase > 30`, so the exact 30-day pre-sale boundary remains included.
- F6 fixed in `tests/unit/services/test_pre_trade_alerts.py:251` and `tests/unit/services/test_pre_trade_alerts.py:293`: the test suite now asserts exact day 30 warns with `days_remaining == 0`, and day 31 does not warn.
- Direct behavioral probe confirms the edge and control cases:

```text
loss_with_30_day_purchase {'warnings': 1, 'wait_days': 0, 'wash_risk': True, 'gain': '-2250.0000', 'warning_days': [0]}
loss_with_31_day_purchase {'warnings': 0, 'wait_days': 0, 'wash_risk': False, 'gain': '-2250.0000', 'warning_days': []}
loss_with_10_day_purchase {'warnings': 1, 'wait_days': 20, 'wash_risk': True, 'gain': '-2250.0000', 'warning_days': [20]}
gain_with_10_day_purchase {'warnings': 0, 'wait_days': 0, 'wash_risk': False, 'gain': '2750.0000', 'warning_days': []}
```

Note: an initial ad hoc probe run failed because the local probe harness omitted the required `wash_sale_adjustment` constructor argument for `TaxLot`; the corrected probe above fully populated the entity and is the review evidence.

### Commands Executed

```text
uv run pytest tests/unit/domain/tax/ tests/unit/services/test_tax_service_wash_sale.py tests/unit/services/test_pre_trade_alerts.py -x --tb=short -q
Result: 101 passed, 1 warning

uv run pytest tests/integration/ -x --tb=short -q
Result: 257 passed, 1 skipped, 2 warnings

uv run python tools/validate_codebase.py --scope meu
Result: 8/8 blocking checks passed
Advisory: Evidence Bundle WARN - 2026-05-13-wash-sale-extensions-handoff.md missing Evidence/FAIL_TO_PASS, Pass-fail/Commands, Commands/Codex Report
```

### Checklist Results

| Check | Result | Evidence |
|-------|--------|----------|
| IR-1 Live runtime evidence | pass | Targeted unit suite and integration suite reproduced green. |
| IR-2 Stub behavioral compliance | n/a | No stubs in the reviewed implementation path. |
| IR-3 Error mapping completeness | n/a | No REST/API write route changes in this MEU set. |
| IR-4 Fix generalization | pass | Prior option, spousal, sale-side warning, wash-risk, and boundary defects were rechecked against direct file state and behavior. |
| IR-5 Test rigor audit | pass | Boundary tests assert exact warning counts, `days_remaining`, and no-warning behavior; existing pre-trade tests cover loss purchase, no purchase, old purchase, wait-days max, gain sale, and warning-to-risk derivation. |
| IR-6 Boundary validation coverage | n/a | No external write boundary was added in this domain/service MEU set. |

### Residual Risk

- The original work handoff still has a non-blocking evidence-bundle advisory from `validate_codebase.py`. This is auditability debt in the prior handoff structure, not a remaining implementation defect in the reviewed product behavior.
- No product files or tests were modified by this review pass.

### Verdict

`approved` - all six findings from the rolling implementation-critical review are resolved, including the exact 30-day boundary regression from Pass 2.
