---
date: "2026-05-02"
review_mode: "handoff"
target_plan: "docs/execution/plans/2026-05-02-market-data-builders-extractors/implementation-plan.md"
verdict: "approved"
findings_count: 0
template_version: "2.1"
requested_verbosity: "standard"
agent: "GPT-5 Codex"
---

# Critical Review: 2026-05-02-market-data-builders-extractors

> **Review Mode**: `handoff`
> **Verdict**: `approved`

---

## Scope

**Target**: `.agent/context/handoffs/2026-05-02-market-data-builders-extractors-handoff.md`
**Correlated Plan**: `docs/execution/plans/2026-05-02-market-data-builders-extractors/`
**Review Type**: implementation handoff review
**Checklist Applied**: IR / DR / PR

Correlation rationale: the user provided the work handoff path explicitly. Its date and slug match the execution plan folder `2026-05-02-market-data-builders-extractors`, whose plan covers MEU-185 through MEU-188 and whose `task.md` marks all 18 rows complete. No sibling work handoff for the same slug was found; the review scope is the provided handoff plus the correlated plan, task, reflection, docs state, changed source files, and changed tests.

---

## Findings

| # | Severity | Finding | File:Line | Recommendation | Status |
|---|----------|---------|-----------|----------------|--------|
| 1 | High | POST-body builders are not wired into the runtime fetch path. The plan says POST-body builders return `RequestSpec` and the adapter selects POST via `ProviderCapabilities.builder_mode == "post_body"`, but `MarketDataProviderAdapter.fetch()` always calls `builder.build_url(...)` and then `_do_fetch(...)`; `_do_fetch()` delegates to `fetch_with_cache()`, which always executes `client.get(...)`. This means SEC API fundamentals and any future OpenFIGI adapter use still run as GET requests despite the new `build_request()` methods. It also leaves `UrlBuilder` without the planned `build_request()` protocol method. | `docs/execution/plans/2026-05-02-market-data-builders-extractors/implementation-plan.md:69`; `packages/infrastructure/src/zorivest_infra/market_data/market_data_adapter.py:110`; `packages/infrastructure/src/zorivest_infra/market_data/http_cache.py:69`; `packages/infrastructure/src/zorivest_infra/market_data/url_builders.py:17` | Add adapter/http-cache support for `RequestSpec` and POST bodies, or explicitly move runtime POST wiring out of this MEU and mark the POST-body runtime contract incomplete. Add tests that exercise adapter fetch for `SEC API` and assert `client.post` with JSON body, not only builder-level `RequestSpec` construction. | open |
| 2 | High | `FIELD_MAPPINGS` does not satisfy AC-18/AC-26 or the handoff's claimed 30+ mapping tuples. The plan requires standard mappings for the simple-GET provider surface and complex mappings for Alpha Vantage, Finnhub, and Nasdaq DL. Actual registry coverage stops at a subset: FMP only quote/ohlcv, EODHD only ohlcv, no API Ninjas mappings, no Alpaca news mapping, Alpha Vantage only quote/ohlcv, Finnhub only ohlcv, and no Nasdaq DL fundamentals mapping. The audit command found 20 missing `(provider, data_type)` mappings. | `docs/execution/plans/2026-05-02-market-data-builders-extractors/implementation-plan.md:126`; `docs/execution/plans/2026-05-02-market-data-builders-extractors/implementation-plan.md:139`; `packages/infrastructure/src/zorivest_infra/market_data/field_mappings.py:140`; `packages/infrastructure/src/zorivest_infra/market_data/field_mappings.py:204` | Add the missing mapping tuples or narrow the plan/handoff claims with source-backed scope changes. Expand tests to enumerate every supported provider/data-type pair from the Phase 8a capability matrix. | open |
| 3 | Medium | Extractor coverage is narrower than the completed MEU claims and the tests do not cover the omitted provider/data-type pairs. The registry lacks explicit extractors for FMP news/splits, EODHD news/splits, and API Ninjas insider. Some may fall through to `_generic_extract()`, but the acceptance criteria and FIC describe provider-specific extractors for those surfaces. The test file mirrors the narrowed implementation and never asserts the missing pairs. | `docs/build-plan/08a-market-data-expansion.md:290`; `packages/infrastructure/src/zorivest_infra/market_data/response_extractors.py:310`; `packages/infrastructure/src/zorivest_infra/market_data/response_extractors.py:355`; `packages/infrastructure/src/zorivest_infra/market_data/response_extractors.py:397`; `tests/unit/test_response_extractors.py:499` | Add explicit extractor registrations/tests for the missing supported pairs, or document which pairs intentionally use generic extraction and add tests proving generic extraction is correct for those exact response envelopes. | open |

---

## Checklist Results

### Information Retrieval / Implementation Review

| Check | Result | Evidence |
|-------|--------|----------|
| IR-1 Live runtime evidence | fail | Targeted unit tests pass, but no adapter-level POST runtime test exists for `SEC API`/`OpenFIGI`; current adapter uses GET-only cache path. |
| IR-2 Stub behavioral compliance | n/a | No stubs in review scope. |
| IR-3 Error mapping completeness | n/a | No API write routes in review scope. |
| IR-4 Fix generalization | fail | Yahoo OHLCV addendum was covered, but broader field mapping/extractor coverage was not generalized across claimed provider surfaces. |
| IR-5 Test rigor audit | fail | `test_url_builders.py`: mostly Strong for builder URLs and RequestSpec. `test_response_extractors.py`: Adequate overall, but Weak for omitted extractor pairs because the FIC does not enumerate all claimed pairs. `test_field_mappings.py`: Weak for AC-18/AC-26 because it checks only 7 standard mappings and 3 complex mappings while the plan claims about 45. |
| IR-6 Boundary validation coverage | n/a | No external write boundary in scope. |

### Design / Docs Review

| Check | Result | Evidence |
|-------|--------|----------|
| Claim-to-state match | fail | Handoff claims 30+ mapping tuples and complete MEU-187/188, but `FIELD_MAPPINGS` is missing 20 expected pairs from the plan-derived audit. |
| Residual old terms | pass | No stale slug issue found in reviewed market-data files. |
| Downstream references updated | mixed | `docs/BUILD_PLAN.md` marks MEU-185 through MEU-188 complete, but this should be reverted or held pending corrections because runtime POST support and mapping coverage are incomplete. |
| Verification robustness | fail | Existing green tests do not catch missing mapping/extractor pairs or POST-body runtime behavior. |
| Evidence auditability | pass | Handoff commands are reproducible; independent targeted tests and MEU gate were run during review. |
| Evidence freshness | mixed | Targeted reviewed tests now report 195 passed. Handoff reports full suite 2662 passed; reflection/metrics also mention 2654 passed. Counts are plausible across addendum timing, but the evidence bundle does not include command receipts for all intermediate claims. MEU gate advisory also reports missing handoff sections. |

### Post-Implementation Review

| Check | Result | Evidence |
|-------|--------|----------|
| Evidence bundle complete | fail | `validate_codebase.py --scope meu` advisory: `2026-05-02-market-data-builders-extractors-handoff.md missing: Pass-fail/Commands, Commands/Codex Report`. |
| FAIL_TO_PASS table present | partial | Yahoo OHLCV addendum has a concise fail-to-pass snippet; earlier MEU red-phase failures are referenced in task commands but not preserved in the handoff. |
| Commands independently runnable | pass | Targeted pytest, pyright, ruff, and MEU gate all ran successfully in review. |
| Anti-placeholder scan clean | pass | MEU gate anti-placeholder and anti-deferral scans pass. |

---

## Commands Executed

| Command | Result |
|---------|--------|
| `uv run pytest tests/unit/test_url_builders.py tests/unit/test_response_extractors.py tests/unit/test_field_mappings.py -q` | 195 passed, 1 warning |
| `uv run pyright packages/` | 0 errors, 0 warnings |
| `uv run ruff check packages/` | All checks passed |
| `uv run python tools/validate_codebase.py --scope meu` | 8/8 blocking checks passed; advisory evidence bundle warning |
| `rg -n '@_register\(' packages/infrastructure/src/zorivest_infra/market_data/response_extractors.py` | Confirmed missing explicit extractor registrations listed above |
| `rg -n '\(\"(fmp|eodhd|api_ninjas|alpaca|tradier|alpha_vantage|finnhub|nasdaq_dl|polygon|yahoo)\", \"(quote|ohlcv|fundamentals|earnings|news|dividends|splits|insider|economic_calendar)\"\)' packages/infrastructure/src/zorivest_infra/market_data/field_mappings.py` | Confirmed actual mapping keys listed above |
| `uv run python -c "...coverage audit..."` | Reported 20 missing mappings and 5 missing extractor registrations |
| `git status --short` | Confirmed touched files and untracked handoff/plan artifacts; review did not modify product files |

---

## Verdict

`changes_required` - Blocking checks are green, but the implementation does not meet the claimed runtime POST-body contract and does not satisfy the declared field mapping/extractor coverage for MEU-187/188. The current tests are too narrow to detect these gaps.

Follow-up actions should go through `/execution-corrections`:

1. Wire `RequestSpec` into runtime fetching with POST method/body support and adapter tests.
2. Complete or explicitly rescope the missing `FIELD_MAPPINGS` provider/data-type pairs.
3. Complete or explicitly justify generic fallback for missing extractor pairs, with tests for each claimed response envelope.
4. Update the handoff/evidence bundle after corrections and rerun targeted tests plus the MEU gate.

---

## Corrections Applied

**Date:** 2026-05-02
**Status:** `corrections_applied`

| # | Finding | Resolution |
|---|---------|-----------|
| 1 | POST-body not wired into adapter runtime | **Scope clarification (docs only)**: POST adapter wiring was always MEU-189 scope per `implementation-plan.md` §2 "Out of Scope". Handoff updated with explicit deferral note. No production code change. |
| 2 | 14 missing `FIELD_MAPPINGS` tuples | **Fixed (TDD)**: Added 14 field mapping tuples (9 extractor-present gaps + 5 new extractor pairs). 30 RED → 30 GREEN. |
| 3 | 5 missing extractor registrations | **Fixed (TDD)**: Added 5 explicit `@_register` extractors (FMP news/fundamentals/splits, EODHD news/splits). Tests added. |

### Corrections Evidence

- **RED phase**: 30 failures across `test_field_mappings.py` (14 registry parametrize + 14 functional + 2 MEU-188 parametrize)
- **GREEN phase**: 45 passed (all 30 previously failing + 15 pre-existing passing)
- **Full regression**: 2700 passed, 23 skipped, 0 failed (215s)
- **pyright**: 0 errors, 0 warnings
- **ruff**: all checks passed

---

## Recheck (2026-05-02)

**Workflow**: `/execution-critical-review` recheck  
**Agent**: GPT-5 Codex  
**Verdict**: `changes_required`

### Prior Pass Summary

| Finding | Prior Status | Recheck Result |
|---------|--------------|----------------|
| F1: POST-body builders not wired into runtime fetch path | open | Partially addressed. The work handoff now explicitly states that runtime POST dispatch is deferred to MEU-189 and that no runtime POST requests can be issued yet. However, the implementation plan still states that the adapter checks `ProviderCapabilities.builder_mode == "post_body"` to choose the call pattern, and Task 1 still says the `UrlBuilder` protocol should gain a `build_request()` method signature. Those plan contracts are still not true in code. |
| F2: Missing `FIELD_MAPPINGS` tuples | open | Fixed for the corrected contract. Registry audit returned `missing_mappings=[]`; targeted tests pass. |
| F3: Missing extractor registrations | open | Fixed for the corrected contract. Registry audit returned `missing_extractors=[]`; targeted tests pass. |

### Confirmed Fixes

- `field_mappings.py` now includes corrected mappings for FMP earnings/dividends/news/fundamentals/splits, EODHD fundamentals/dividends/news/splits, API Ninjas quote/earnings, Alpha Vantage earnings, Nasdaq DL fundamentals, Alpaca news, and TradingView quote/fundamentals.
- `response_extractors.py` now registers the previously missing explicit extractors for FMP news/fundamentals/splits and EODHD news/splits; the corrected audit found no missing extractor pairs.
- Targeted tests now cover 247 tests in `test_url_builders.py`, `test_response_extractors.py`, and `test_field_mappings.py`.

### Remaining Findings

| # | Severity | Finding | File:Line | Required Action |
|---|----------|---------|-----------|-----------------|
| R1 | Medium | The POST-runtime scope clarification is incomplete because the canonical implementation plan still claims adapter runtime selection that does not exist. `implementation-plan.md` says the adapter checks `builder_mode == "post_body"` to choose the call pattern, while current `MarketDataProviderAdapter.fetch()` still calls `builder.build_url(...)` and `fetch_with_cache()` still calls `client.get(...)`. The handoff correctly discloses "No runtime POST requests can be issued until MEU-189", but the plan remains contradictory. | `docs/execution/plans/2026-05-02-market-data-builders-extractors/implementation-plan.md:69`; `docs/execution/plans/2026-05-02-market-data-builders-extractors/implementation-plan.md:147`; `packages/infrastructure/src/zorivest_infra/market_data/market_data_adapter.py:110`; `packages/infrastructure/src/zorivest_infra/market_data/http_cache.py:69` | Update the implementation plan/task to make POST runtime dispatch explicitly MEU-189 scope, or implement adapter/cache POST dispatch now. Also either add `build_request()` to the `UrlBuilder` protocol as planned or correct the task/plan contract. |
| R2 | Low | The MEU gate still reports the work handoff evidence bundle as structurally incomplete: `missing: Pass-fail/Commands, Commands/Codex Report`. The handoff now contains quality gate and FAIL_TO_PASS summaries, but it still does not satisfy the validator's evidence-bundle expectations. | `.agent/context/handoffs/2026-05-02-market-data-builders-extractors-handoff.md:27`; `C:\Temp\zorivest\recheck-validate.txt` | Add the validator-required evidence sections or adjust the evidence validator if the handoff template changed intentionally. |

### Commands Executed

| Command | Result |
|---------|--------|
| `uv run python -c "...coverage audit..."` | `missing_mappings=[]`; `missing_extractors=[]` |
| `uv run pytest tests/unit/test_url_builders.py tests/unit/test_response_extractors.py tests/unit/test_field_mappings.py -q` | 247 passed, 1 warning |
| `uv run pyright packages/` | 0 errors, 0 warnings |
| `uv run ruff check packages/` | All checks passed |
| `uv run python tools/validate_codebase.py --scope meu` | 8/8 blocking checks passed; advisory evidence-bundle warning remains |

### Verdict

`changes_required` - Functional mapping/extractor corrections are verified. The remaining blocker is contract hygiene around POST runtime scope: the handoff discloses the deferral, but the implementation plan still describes runtime behavior that has not been delivered. The evidence-bundle advisory also remains open.

---

## Recheck Corrections Applied (2026-05-02)

**Date:** 2026-05-02
**Status:** `corrections_applied`

| # | Finding | Resolution |
|---|---------|-----------|
| R1 | Plan-code contract mismatch: `implementation-plan.md` claims adapter checks `builder_mode == "post_body"` and `UrlBuilder` Protocol gains `build_request()` — neither exists in code | **Deferred to `/plan-corrections`**: `docs/execution/plans/*/implementation-plan.md` is forbidden write scope per execution-corrections workflow. The handoff already correctly documents the MEU-189 deferral (line 57-61). The plan doc needs 3 line changes to align with actual implementation. |
| R2 | Evidence bundle validator reports missing `Pass-fail/Commands` and `Commands/Codex Report` headers | **Fixed**: Added `## Commands Executed` section with reproducible validation commands table. Added `## Codex Validation Report` section (pending status). Validator now reports: *"All evidence fields present"*. |

### R2 Verification Evidence

- **MEU gate (post-fix):** `uv run python tools/validate_codebase.py --scope meu` → 8/8 blocking PASS, `[A3] Evidence Bundle: All evidence fields present in 2026-05-02-market-data-builders-extractors-handoff.md`
- **No production code changes** — handoff formatting only.

### Deferred Item

| Finding | Route | What's needed |
|---------|-------|---------------|
| R1 | `/plan-corrections` | Update `implementation-plan.md:69` (remove adapter `builder_mode` claim), `:147` (clarify `build_request()` on concrete classes not Protocol), `:78` (add TradingView to `post_body` row) |

---

## Recheck 2 (2026-05-02)

**Workflow**: `/execution-critical-review` recheck  
**Agent**: GPT-5 Codex  
**Verdict**: `changes_required`

### Prior Recheck Summary

| Finding | Prior Status | Recheck Result |
|---------|--------------|----------------|
| R1: Plan-code contract mismatch around POST runtime scope | deferred to `/plan-corrections` | Still open. The handoff correctly documents MEU-189 deferral, but `implementation-plan.md:69` still says the adapter checks `ProviderCapabilities.builder_mode == "post_body"` to decide the call pattern. `implementation-plan.md:147` still says the `UrlBuilder` protocol gains `build_request()`. Current runtime code remains GET-only. |
| R2: Evidence bundle validator warning | open | Fixed. MEU gate now reports `[A3] Evidence Bundle: All evidence fields present in 2026-05-02-market-data-builders-extractors-handoff.md`. |

### Confirmed Fixes

- `.agent/context/handoffs/2026-05-02-market-data-builders-extractors-handoff.md` now has `## Commands Executed` and `## Codex Validation Report` sections.
- `uv run python tools/validate_codebase.py --scope meu` now reports 8/8 blocking checks passing and evidence bundle present.
- Targeted builder/extractor/mapping regression suite remains green: 247 passed.

### Remaining Finding

| # | Severity | Finding | File:Line | Required Action |
|---|----------|---------|-----------|-----------------|
| R1 | Medium | The canonical implementation plan still misstates delivered POST runtime behavior. It says the adapter checks `builder_mode == "post_body"` to choose POST call patterns, but `MarketDataProviderAdapter.fetch()` still calls `builder.build_url(...)` and `fetch_with_cache()` still calls `client.get(...)`. The handoff has the correct MEU-189 deferral, so this is now a plan-code contract issue rather than a hidden runtime claim. | `docs/execution/plans/2026-05-02-market-data-builders-extractors/implementation-plan.md:69`; `docs/execution/plans/2026-05-02-market-data-builders-extractors/implementation-plan.md:147`; `packages/infrastructure/src/zorivest_infra/market_data/market_data_adapter.py:110`; `packages/infrastructure/src/zorivest_infra/market_data/http_cache.py:69` | Run `/plan-corrections` to align the plan with the delivered scope, or implement POST runtime dispatch under an execution workflow. Minimum plan corrections: remove the adapter-runtime claim at line 69, clarify `build_request()` lives on concrete POST builders rather than the protocol, and add TradingView to the `post_body` builder-family row. |

### Commands Executed

| Command | Result |
|---------|--------|
| `uv run python tools/validate_codebase.py --scope meu` | 8/8 blocking checks passed; `[A3] Evidence Bundle: All evidence fields present...` |
| `uv run pytest tests/unit/test_url_builders.py tests/unit/test_response_extractors.py tests/unit/test_field_mappings.py -q` | 247 passed, 1 warning |
| `rg -n "adapter checks|builder_mode == \"post_body\"|build_request\(\) method signature|POST runtime|Commands Executed|Codex Validation Report|All evidence fields present|Evidence Bundle" ...` | Confirmed plan contradiction remains and evidence headers are present |
| `git status --short` | Review changed only the canonical implementation critical review in this recheck; broader worktree remains dirty from the implementation/corrections work |

### Verdict

`changes_required` - R2 is fixed. R1 remains open and should be resolved through `/plan-corrections` or by implementing POST runtime dispatch in an execution workflow.

---

## Plan Corrections Applied (2026-05-02)

**Workflow:** `/plan-corrections`
**Date:** 2026-05-02
**Status:** `corrections_applied`

### Changes Made

| Fix | Line | Before | After |
|-----|------|--------|-------|
| R1a | 69 | "The adapter checks `ProviderCapabilities.builder_mode == "post_body"` to decide the call pattern" | "Adapter-level runtime dispatch is deferred to MEU-189; this project delivers the builder-side contract only" |
| R1b | 147 | "Add `build_request()` method signature to `UrlBuilder` Protocol (optional, with default)" | "Add `build_request()` method to concrete POST builder classes — not on the `UrlBuilder` Protocol (runtime dispatch deferred to MEU-189)" |
| R1c | 78 | `post_body` row listed "OpenFIGI, SEC API" | Added TradingView: "OpenFIGI, SEC API, TradingView" |

### Verification

- `rg "adapter checks|builder_mode == .post_body.|build_request() method signature" implementation-plan.md` → 0 hits (all stale patterns removed)
- Cross-doc sweep: `.agent/`, `docs/`, `AGENTS.md` → 0 stale references outside review history

### Verdict

`corrections_applied` — All 3 sub-findings of R1 resolved. The implementation plan now accurately describes what was delivered (builder-side `RequestSpec` + `build_request()` on concrete classes) and explicitly defers adapter runtime dispatch to MEU-189.

---

## Recheck 3 (2026-05-02)

**Workflow**: `/execution-critical-review` recheck  
**Agent**: GPT-5 Codex  
**Verdict**: `approved`

### Prior Finding Status

| Finding | Prior Status | Recheck Result |
|---------|--------------|----------------|
| R1: Plan-code contract mismatch around POST runtime scope | open / routed to `/plan-corrections` | Fixed. `implementation-plan.md` now states POST-body builders deliver only the builder-side `RequestSpec` contract, explicitly defers adapter/runtime POST dispatch to MEU-189, keeps `build_request()` on concrete POST builder classes instead of the `UrlBuilder` Protocol, and includes TradingView in the `post_body` builder-family row. |
| R2: Evidence bundle validator warning | fixed in Recheck 2 | Still fixed. The MEU gate reports `[A3] Evidence Bundle: All evidence fields present in 2026-05-02-market-data-builders-extractors-handoff.md`. |

### Verified Current State

- `implementation-plan.md:69` now says adapter-level runtime dispatch is deferred to MEU-189 and this project delivers the builder-side contract only.
- `implementation-plan.md:78` lists `OpenFIGI, SEC API, TradingView` in the `post_body` builder family.
- `implementation-plan.md:147` scopes `build_request()` to concrete POST builder classes and explicitly says it is not on the `UrlBuilder` Protocol.
- `url_builders.py:18` confirms `UrlBuilder` still exposes only `build_url()`, consistent with the corrected plan.
- Runtime POST dispatch remains deferred: `market_data_adapter.py:238` still calls `fetch_with_cache()`, and `http_cache.py:69` still calls `client.get(...)`. This is no longer a contradiction because the plan and handoff both route runtime POST support to MEU-189.

### Commands Executed

| Command | Result |
|---------|--------|
| `uv run python tools/validate_codebase.py --scope meu` | 8/8 blocking checks passed; A3 evidence bundle present |
| `uv run pytest tests/unit/test_url_builders.py tests/unit/test_response_extractors.py tests/unit/test_field_mappings.py -q` | 247 passed, 1 warning |
| `rg -n 'adapter checks\|ProviderCapabilities\.builder_mode == "post_body"\|build_request\(\) method signature\|OpenFIGI, SEC API \|' implementation-plan.md` | 0 stale matches |
| `rg -n 'POST-body builders\|post_body\|Adapter-level runtime dispatch' implementation-plan.md` | Confirmed corrected plan lines at 69, 78, 147 |
| `rg -n 'class UrlBuilder\|def build_request\|class RequestSpec\|client\.get\|fetch_with_cache' packages/infrastructure/src/zorivest_infra/market_data/*.py` | Confirmed builder-side POST methods exist and runtime remains GET-only by documented deferral |
| `rg -n '\[ \]\|\[/\]\|\[B\]' task.md` | Only legend rows matched; no open task rows found |

### Verdict

`approved` — The previous blocker is resolved. The reviewed implementation now has aligned plan, handoff, and code contracts for this MEU set. Runtime POST dispatch remains a documented follow-up for MEU-189, not a hidden incomplete claim in this project.
