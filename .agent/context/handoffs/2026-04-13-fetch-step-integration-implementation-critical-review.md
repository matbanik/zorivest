---
date: "2026-04-13"
review_mode: "handoff"
target_plan: "docs/execution/plans/2026-04-13-fetch-step-integration/implementation-plan.md"
verdict: "approved"
findings_count: 0
template_version: "2.1"
requested_verbosity: "standard"
agent: "Codex (GPT-5.4)"
---

# Critical Review: 2026-04-13-fetch-step-integration

> **Review Mode**: `handoff`
> **Verdict**: `approved`

---

## Scope

**Target**: `.agent/context/handoffs/114-2026-04-13-fetch-step-integration-bp09s49.5.md`
**Review Type**: handoff review
**Checklist Applied**: IR + DR

### Correlation Rationale

- The user supplied an explicit work handoff path, so this was reviewed in implementation mode rather than auto-discovery mode.
- The handoff correlates directly to `docs/execution/plans/2026-04-13-fetch-step-integration/` by matching date + slug.
- No sibling PW2 work handoffs were present, so scope stayed single-handoff plus the correlated plan, changed source/tests, and shared closeout artifacts (`docs/BUILD_PLAN.md`, `.agent/context/meu-registry.md`, `docs/execution/metrics.md`, `docs/execution/reflections/2026-04-13-fetch-step-integration-reflection.md`).

### Commands Executed

```powershell
git status --short *> C:\Temp\zorivest\git-status-short.txt
git diff -- docs/BUILD_PLAN.md .agent/context/meu-registry.md docs/execution/metrics.md .agent/context/current-focus.md packages/core/src/zorivest_core/pipeline_steps/fetch_step.py packages/infrastructure/src/zorivest_infra/market_data/market_data_adapter.py tests/integration/test_pipeline_fetch_e2e.py tests/unit/test_market_data_adapter.py *> C:\Temp\zorivest\pw2-artifacts-diff.txt
rg -n "FetchAdapterResult|MarketDataAdapterPort|cached_content|cached_etag|cached_last_modified|_check_cache|_fetch_from_provider|fetch_cache_repo|provider_adapter|warnings|entity_key|is_market_closed" packages tests docs/execution/plans/2026-04-13-fetch-step-integration .agent/context/handoffs/114-2026-04-13-fetch-step-integration-bp09s49.5.md *> C:\Temp\zorivest\pw2-focused-rg.txt
rg -n "test_AC_F11_fetch_step_cache_hit|test_PW2_AC7_etag_revalidation_304|test_PW2_AC4_market_closed_extends_ttl_for_ohlcv|test_PW2_AC4_market_open_uses_standard_ttl|test_AC6_etag_headers_passed_to_fetch_with_cache|test_AC6_last_modified_headers_passed|def _is_market_closed|def is_market_closed|def _check_cache|async def fetch\(|entity_key = _compute_entity_key\(|resolved_criteria = resolver.resolve|adapter_result = await self._fetch_from_provider" packages tests *> C:\Temp\zorivest\pw2-line-refs.txt
uv run pytest tests/unit/test_market_data_adapter.py tests/unit/test_fetch_step.py tests/unit/test_pipeline_runner_constructor.py tests/integration/test_pipeline_wiring.py tests/integration/test_pipeline_fetch_e2e.py -x --tb=short -v *> C:\Temp\zorivest\pw2-targeted-pytest.txt
uv run pyright packages/ *> C:\Temp\zorivest\pw2-pyright.txt
uv run ruff check packages/ tests/ *> C:\Temp\zorivest\pw2-ruff.txt
uv run python tools/validate_codebase.py --scope meu *> C:\Temp\zorivest\pw2-meu-gate.txt
uv run python -c "from zorivest_core.pipeline_steps.fetch_step import _compute_entity_key; from zorivest_core.services.criteria_resolver import CriteriaResolver; raw={'date_range': {'type': 'relative', 'expr': '-30d'}, 'symbol': 'AAPL'}; resolved=CriteriaResolver().resolve(raw); print(_compute_entity_key(raw)); print(_compute_entity_key(resolved))" *> C:\Temp\zorivest\pw2-entitykey-proof.txt
uv run python -c "from datetime import datetime, timezone; from zorivest_core.pipeline_steps.fetch_step import FetchStep; from zorivest_core.domain.pipeline import is_market_closed; dt=datetime(2026,3,16,21,0,tzinfo=timezone.utc); print(FetchStep._is_market_closed(dt)); print(is_market_closed(dt))" *> C:\Temp\zorivest\pw2-market-closed-proof.txt
```

---

## Findings

| # | Severity | Finding | File:Line | Recommendation | Status |
|---|----------|---------|-----------|----------------|--------|
| 1 | High | The fetch-step revalidation path is not wired end-to-end. `FetchStep.execute()` falls through to `_fetch_from_provider()` without forwarding stale cache metadata, so the adapter never receives `cached_content` / `cached_etag` / `cached_last_modified` during normal step execution. The AC-7 "ETag revalidation" coverage bypasses that gap by calling `adapter.fetch()` directly, and the test comments explicitly acknowledge the missing fetch-step wiring. The handoff and registry therefore overstate "HTTP cache revalidation" / "5/5 steps operational". | `packages/core/src/zorivest_core/pipeline_steps/fetch_step.py:96-101,158-166`; `tests/integration/test_pipeline_fetch_e2e.py:180-227`; `.agent/context/handoffs/114-2026-04-13-fetch-step-integration-bp09s49.5.md:14,54-56`; `.agent/context/meu-registry.md:134,199` | Preserve stale cache entry metadata through the execute path and add a regression that proves `FetchStep.execute()` passes `cached_*` kwargs into the adapter on stale-cache revalidation. | open |
| 2 | High | Cache lookup and cache write use different entity-key inputs. `execute()` resolves criteria first and saves with `_compute_entity_key(resolved_criteria)`, but `_check_cache()` reads with `_compute_entity_key(params.criteria)`. For relative or incremental criteria these hashes diverge, so the step can populate cache entries it will never hit later. Reproduced with the current code: the raw criteria and resolved criteria hashes differ (`696aa1cb33a1b700` vs `fd68d967598c0718`). | `packages/core/src/zorivest_core/pipeline_steps/fetch_step.py:80,115,183`; `tests/unit/test_fetch_step.py:644-746`; `C:\Temp\zorivest\pw2-entitykey-proof.txt:1-2` | Use the same normalized/resolved criteria basis for both cache read and cache write, then add a regression using relative or incremental criteria rather than empty/static criteria only. | open |
| 3 | High | The market-closed TTL extension regressed to weekend-only logic. `FetchStep._is_market_closed()` returns `True` only on Saturday/Sunday, while the canonical phase-9 helper marks weekdays outside 9:30 AM-4:00 PM ET as closed too. Reproduced on 2026-03-16 21:00 UTC: `FetchStep._is_market_closed()` returned `False` while `zorivest_core.domain.pipeline.is_market_closed()` returned `True`. Current AC-4 coverage checks Saturday and a market-open weekday, but never weekday after-hours, so the regression ships green. | `packages/core/src/zorivest_core/pipeline_steps/fetch_step.py:218-224`; `packages/core/src/zorivest_core/domain/pipeline.py:253-274`; `tests/unit/test_fetch_step.py:770-842`; `docs/BUILD_PLAN.md:323`; `C:\Temp\zorivest\pw2-market-closed-proof.txt:1-2` | Reuse the canonical `domain.pipeline.is_market_closed()` helper or match its weekday after-hours semantics, and add a weekday after-hours regression test. | open |
| 4 | Medium | The verification bundle creates more confidence than the underlying evidence supports. The handoff and reflection both claim `ruff` was green, but `ruff check packages/ tests/` fails on changed test files; the MEU gate advisory also reports the handoff is missing `Evidence/FAIL_TO_PASS`, `Pass-fail/Commands`, and `Commands/Codex Report`. Separately, `test_AC_F11_fetch_step_cache_hit()` patches the private `_check_cache()` method, which is exactly why the real cache integration bugs above escaped. | `.agent/context/handoffs/114-2026-04-13-fetch-step-integration-bp09s49.5.md:35-41`; `docs/execution/reflections/2026-04-13-fetch-step-integration-reflection.md:32`; `tests/unit/test_fetch_step.py:279-304`; `C:\Temp\zorivest\pw2-ruff.txt:1-37`; `C:\Temp\zorivest\pw2-meu-gate.txt:15-18` | Correct the evidence sections, lint the changed tests, and replace private-method patching with execute-path assertions against real cache-repo behavior. | open |

---

## Checklist Results

### Implementation Review

| Check | Result | Evidence |
|-------|--------|----------|
| IR-1 Live runtime evidence | fail | The targeted suite is green (`60 passed`), but no test proves stale-cache revalidation through `FetchStep.execute()`; the AC-7 revalidation test bypasses the step and calls `adapter.fetch()` directly. |
| IR-2 Stub behavioral compliance | pass | No new silent `__getattr__` / stub-behavior regressions were introduced in PW2 scope. |
| IR-3 Error mapping completeness | n/a | PW2 does not add write-adjacent REST/MCP boundary surfaces. |
| IR-4 Fix generalization | fail | The implementation added cache + market-hours behavior, but did not generalize checks across resolved-criteria cache keys or weekday after-hours semantics. |
| IR-5 Test rigor audit | fail | See per-file audit below; two scope files are weak enough to let broken behavior pass green. |
| IR-6 Boundary validation coverage | n/a | No new external-input schema boundary was added in this MEU. |

### IR-5 Test Rigor Audit

| Test File | Rating | Evidence |
|-----------|--------|----------|
| `tests/unit/test_market_data_adapter.py` | Adequate | Validates adapter contract and adapter-local cache headers, but does not prove `FetchStep` forwards stale-cache metadata into the adapter. |
| `tests/unit/test_fetch_step.py` | Weak | `test_AC_F11_fetch_step_cache_hit()` patches private `_check_cache()` (`tests/unit/test_fetch_step.py:279-304`), and PW2 cache tests never cover resolved-criteria key drift or weekday after-hours closure. |
| `tests/integration/test_pipeline_fetch_e2e.py` | Weak | `test_PW2_AC7_etag_revalidation_304()` documents the missing fetch-step wiring and calls `adapter.fetch()` directly instead of asserting `FetchStep.execute()` behavior (`tests/integration/test_pipeline_fetch_e2e.py:180-227`). |
| `tests/unit/test_pipeline_runner_constructor.py` | Strong | Exact injected-key and identity assertions across all 9 deps. |
| `tests/integration/test_pipeline_wiring.py` | Strong | Uses real app lifespan and `runner.run()` to verify dependency flow into `context.outputs`. |
| `tests/unit/test_ports.py` | Adequate | Sanity-check coverage for the new protocol/TypedDict presence only. |

### Docs / Evidence Review

| Check | Result | Evidence |
|-------|--------|----------|
| DR-1 Claim-to-state match | fail | The handoff/meu-registry/BUILD_PLAN all claim HTTP cache revalidation + market-hours extension are delivered, but the implementation still drops stale-cache metadata and only treats weekends as closed. |
| DR-4 Verification robustness | fail | The passing suite does not contain an end-to-end stale-cache revalidation assertion through `FetchStep.execute()`. |
| DR-7 Evidence freshness | fail | Handoff/reflection say `ruff` is green, but `C:\Temp\zorivest\pw2-ruff.txt` shows 3 lint errors in changed test files. |
| PR Evidence bundle complete | fail | `tools/validate_codebase.py --scope meu` reports missing `Evidence/FAIL_TO_PASS`, `Pass-fail/Commands`, and `Commands/Codex Report` sections for this handoff. |

---

## Follow-Up Actions

1. Route fixes through `/planning-corrections`; do not patch product code from this review workflow.
2. Fix `FetchStep` so stale cache metadata survives the miss path into `adapter.fetch(...)`, then add a regression proving 304 revalidation through `FetchStep.execute()`.
3. Normalize cache key computation to one criteria representation on both read and write, with a regression using relative or incremental criteria.
4. Replace the weekend-only `_is_market_closed()` helper with the canonical after-hours-aware logic and add a weekday after-hours TTL regression.
5. Repair the evidence bundle: lint changed tests, add the missing FAIL_TO_PASS / command sections, and remove the private-method cache-hit shortcut from test coverage.

---

## Verdict

`changes_required` — The runner wiring and adapter surface exist, but the handoff currently overclaims the two hardest parts of PW2: end-to-end HTTP revalidation and market-hours-aware cache behavior. The green suite did not exercise those paths strongly enough, and the evidence bundle is incomplete.

---

## Recheck (2026-04-13)

**Workflow**: `/critical-review-feedback` recheck
**Agent**: Codex (GPT-5.4)

### Prior Pass Summary

| Finding | Prior Status | Recheck Result |
|---------|-------------|----------------|
| Stale cache metadata was not forwarded through `FetchStep.execute()` | open | ✅ Fixed |
| Cache read/write entity keys diverged for resolved criteria | open | ✅ Fixed |
| Market-closed TTL logic was weekend-only | open | ✅ Fixed |
| Evidence bundle and test-rigor issues overstated confidence | open | ❌ Still open in part |

### Confirmed Fixes

- `FetchStep.execute()` now resolves criteria before cache lookup, preserves stale metadata, and forwards `cached_content` / `cached_etag` / `cached_last_modified` into `_fetch_from_provider()` and the adapter path. See [fetch_step.py](/P:/zorivest/packages/core/src/zorivest_core/pipeline_steps/fetch_step.py:90), [fetch_step.py](/P:/zorivest/packages/core/src/zorivest_core/pipeline_steps/fetch_step.py:102), [fetch_step.py](/P:/zorivest/packages/core/src/zorivest_core/pipeline_steps/fetch_step.py:186), [test_pipeline_fetch_e2e.py](/P:/zorivest/tests/integration/test_pipeline_fetch_e2e.py:180).
- Cache lookup and cache save now both use `_compute_entity_key(resolved_criteria)`, and a dedicated regression covers that behavior. See [fetch_step.py](/P:/zorivest/packages/core/src/zorivest_core/pipeline_steps/fetch_step.py:127), [fetch_step.py](/P:/zorivest/packages/core/src/zorivest_core/pipeline_steps/fetch_step.py:213), [test_fetch_step.py](/P:/zorivest/tests/unit/test_fetch_step.py:972).
- The TTL extension now uses the canonical `is_market_closed(now)` helper instead of the weekend-only local helper, and weekday after-hours coverage was added. See [fetch_step.py](/P:/zorivest/packages/core/src/zorivest_core/pipeline_steps/fetch_step.py:234), [test_fetch_step.py](/P:/zorivest/tests/unit/test_fetch_step.py:922).
- The prior lint/test-rigor subissues are closed: `ruff check packages/ tests/` now passes, `test_AC_F11_fetch_step_cache_hit()` no longer patches private `_check_cache()`, and the full regression reproduces the claimed test count. Evidence: [test_fetch_step.py](/P:/zorivest/tests/unit/test_fetch_step.py:279), `C:\Temp\zorivest\recheck-ruff.txt:1`, `C:\Temp\zorivest\recheck-full-pytest.txt:67`.

### Remaining Findings

| # | Severity | Finding | File:Line | Recommendation | Status |
|---|----------|---------|-----------|----------------|--------|
| 1 | Low | The remaining gap is the handoff evidence structure, not runtime behavior. The MEU gate still flags the handoff as missing `Evidence/FAIL_TO_PASS` and `Commands/Codex Report`. The handoff now contains `## Evidence`, `### Commands Executed`, and `### FAIL_TO_PASS`, but it still does not satisfy the validator's required artifact shape, so the evidence bundle remains non-compliant. | [114-2026-04-13-fetch-step-integration-bp09s49.5.md](/P:/zorivest/.agent/context/handoffs/114-2026-04-13-fetch-step-integration-bp09s49.5.md:43), [114-2026-04-13-fetch-step-integration-bp09s49.5.md](/P:/zorivest/.agent/context/handoffs/114-2026-04-13-fetch-step-integration-bp09s49.5.md:51), [114-2026-04-13-fetch-step-integration-bp09s49.5.md](/P:/zorivest/.agent/context/handoffs/114-2026-04-13-fetch-step-integration-bp09s49.5.md:60), `C:\Temp\zorivest\recheck-meu-gate.txt:18` | Align the handoff headings/content to the validator's expected section names and add the missing `Codex Report` section so `validate_codebase.py --scope meu` no longer reports advisory evidence gaps. | ✅ Fixed |

### Verdict

`changes_required` — The three runtime correctness findings are closed, and the targeted plus full regression checks are green (`62 passed` in scope; `1928 passed, 15 skipped` full suite). The remaining issue is auditability: the work handoff still does not satisfy the repo's evidence-bundle shape expected by the MEU gate.

---

## Recheck (2026-04-13 Evidence Closeout)

**Workflow**: `/critical-review-feedback` recheck
**Agent**: Codex (GPT-5.4)

### Prior Pass Summary

| Finding | Prior Status | Recheck Result |
|---------|-------------|----------------|
| Handoff evidence bundle shape did not satisfy the MEU gate | open | ✅ Fixed |

### Confirmed Fixes

- The work handoff now contains the evidence headings the validator expects: `### FAIL_TO_PASS Evidence` and `### Codex Validation Report`. See [114-2026-04-13-fetch-step-integration-bp09s49.5.md](/P:/zorivest/.agent/context/handoffs/114-2026-04-13-fetch-step-integration-bp09s49.5.md:60), [114-2026-04-13-fetch-step-integration-bp09s49.5.md](/P:/zorivest/.agent/context/handoffs/114-2026-04-13-fetch-step-integration-bp09s49.5.md:68).
- The validator now excludes review artifacts from work-handoff evidence checks, which removes the false-positive audit path against `*-critical-review.md` files. Evidence: [validate_codebase.py](/P:/zorivest/tools/validate_codebase.py:271).
- The MEU gate now reports the evidence bundle as complete: `All evidence fields present in 114-2026-04-13-fetch-step-integration-bp09s49.5.md`. Evidence: `C:\Temp\zorivest\recheck2-meu-gate.txt:18`.

### Remaining Findings

- None.

### Verdict

`approved` — The prior runtime findings remain closed, and the remaining evidence-bundle gap is now resolved. Current verification reproduced cleanly: `validate_codebase.py --scope meu` reports all evidence fields present, with all 8 blocking checks passing.

---

## Corrections Applied (2026-04-13)

**Workflow**: `/planning-corrections`

### Changes

1. **`tools/validate_codebase.py:270`** — Added `and not f.name.endswith("-critical-review.md")` filter to `_evidence_check()` so the validator only examines work handoffs, not review artifacts.
2. **`114-2026-04-13-fetch-step-integration-bp09s49.5.md:60`** — Renamed `### FAIL_TO_PASS` → `### FAIL_TO_PASS Evidence` to match validator pattern 1.
3. **`114-2026-04-13-fetch-step-integration-bp09s49.5.md:68`** — Added `### Codex Validation Report` section to match validator pattern 3.

### Verification

```
uv run python tools/validate_codebase.py --scope meu
# [A3] Evidence Bundle: All evidence fields present in 114-2026-04-13-fetch-step-integration-bp09s49.5.md
# 8/8 blocking checks pass, exit code 0
```

### Verdict

`approved` — All 4 original findings and the recheck finding are now resolved. The MEU gate reports all evidence fields present.
