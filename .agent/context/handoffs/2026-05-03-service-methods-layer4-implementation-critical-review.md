---
date: "2026-05-04"
review_mode: "handoff"
target_plan: "docs/execution/plans/2026-05-03-service-methods-layer4/implementation-plan.md"
verdict: "changes_required"
findings_count: 4
template_version: "2.1"
requested_verbosity: "standard"
agent: "gpt-5.4"
---

# Critical Review: 2026-05-03-service-methods-layer4

> **Review Mode**: `handoff`
> **Verdict**: `changes_required` after recheck on `2026-05-04`

---

## Scope

**Target**: [`2026-05-03-service-methods-layer4-handoff.md`](.agent/context/handoffs/2026-05-03-service-methods-layer4-handoff.md), [`implementation-plan.md`](docs/execution/plans/2026-05-03-service-methods-layer4/implementation-plan.md), [`task.md`](docs/execution/plans/2026-05-03-service-methods-layer4/task.md), [`2026-05-03-service-methods-layer4-reflection.md`](docs/execution/reflections/2026-05-03-service-methods-layer4-reflection.md), [`metrics.md`](docs/execution/metrics.md), [`BUILD_PLAN.md`](docs/BUILD_PLAN.md)

**Review Type**: handoff review of the single correlated implementation handoff for project `2026-05-03-service-methods-layer4`

**Checklist Applied**: IR + DR + PR + implementation-review workflow IR-1 through IR-6

**Correlation Rationale**: the user supplied the workflow file and the seed handoff directly; repository search found one correlated work handoff for this slug plus a separate plan-review artifact, so scope did not expand to additional sibling work handoffs.

**Evidence Sweeps**:
- repo context reads for [`current-focus.md`](.agent/context/current-focus.md) and [`known-issues.md`](.agent/context/known-issues.md)
- handoff/plan/task correlation search across [`.agent/context/handoffs/`](.agent/context/handoffs/) and [`docs/execution/plans/2026-05-03-service-methods-layer4/`](docs/execution/plans/2026-05-03-service-methods-layer4/)
- implementation inspection of [`market_data_service.py`](packages/core/src/zorivest_core/services/market_data_service.py), [`provider_registry.py`](packages/infrastructure/src/zorivest_infra/market_data/provider_registry.py), [`url_builders.py`](packages/infrastructure/src/zorivest_infra/market_data/url_builders.py), [`provider_connection_service.py`](packages/core/src/zorivest_core/services/provider_connection_service.py), [`provider_status.py`](packages/core/src/zorivest_core/application/provider_status.py), and [`MarketDataProvidersPage.tsx`](ui/src/renderer/src/features/settings/MarketDataProvidersPage.tsx)
- test-rigor audit of [`test_service_methods.py`](tests/unit/test_service_methods.py), [`test_expansion_normalizers.py`](tests/unit/test_expansion_normalizers.py), [`test_provider_registry.py`](tests/unit/test_provider_registry.py), [`test_provider_connection_service.py`](tests/unit/test_provider_connection_service.py), [`test_url_builders.py`](tests/unit/test_url_builders.py), and [`MarketDataProvidersPage.test.tsx`](ui/src/renderer/src/features/settings/__tests__/MarketDataProvidersPage.test.tsx)

---

## Findings

| # | Severity | Finding | File:Line | Recommendation | Status |
|---|----------|---------|-----------|----------------|--------|
| 1 | High | Layer 4 runtime wiring is incomplete. [`MarketDataService._generic_api_fetch()`](packages/core/src/zorivest_core/services/market_data_service.py:520) ignores provider-specific URL builders, request shapes, and query-param auth, and instead issues a generic `base_url?ticker=...` GET for every API-key provider. That contradicts the claimed provider-specific chains in [`implementation-plan.md`](docs/execution/plans/2026-05-03-service-methods-layer4/implementation-plan.md:96), [`implementation-plan.md`](docs/execution/plans/2026-05-03-service-methods-layer4/implementation-plan.md:97), [`implementation-plan.md`](docs/execution/plans/2026-05-03-service-methods-layer4/implementation-plan.md:98), [`implementation-plan.md`](docs/execution/plans/2026-05-03-service-methods-layer4/implementation-plan.md:143), [`implementation-plan.md`](docs/execution/plans/2026-05-03-service-methods-layer4/implementation-plan.md:145), and [`implementation-plan.md`](docs/execution/plans/2026-05-03-service-methods-layer4/implementation-plan.md:147). It also leaves [`get_economic_calendar()`](packages/core/src/zorivest_core/services/market_data_service.py:442) calling the same generic fetch path with an empty ticker. | [`market_data_service.py:442`](packages/core/src/zorivest_core/services/market_data_service.py:442), [`market_data_service.py:520`](packages/core/src/zorivest_core/services/market_data_service.py:520) | Rewire Layer 4 methods through the provider-specific builder/request path already introduced in [`url_builders.py`](packages/infrastructure/src/zorivest_infra/market_data/url_builders.py:98), including auth injection and any provider-specific POST/GET behavior, then add runtime-oriented regression tests. | open |
| 2 | High | Fallback priority is implemented incorrectly. [`_get_enabled_providers()`](packages/core/src/zorivest_core/services/market_data_service.py:732) sorts provider names alphabetically, which changes the declared order for most new data types. Example mismatches: fundamentals become Alpha Vantage → EODHD → FMP instead of FMP → EODHD → AV, dividends/splits become EODHD → FMP → Polygon instead of Polygon → EODHD → FMP, and insider/calendar/profile are similarly reordered. | [`market_data_service.py:742`](packages/core/src/zorivest_core/services/market_data_service.py:742), [`normalizers.py:792`](packages/infrastructure/src/zorivest_infra/market_data/normalizers.py:792), [`normalizers.py:802`](packages/infrastructure/src/zorivest_infra/market_data/normalizers.py:802), [`normalizers.py:812`](packages/infrastructure/src/zorivest_infra/market_data/normalizers.py:812), [`implementation-plan.md:96`](docs/execution/plans/2026-05-03-service-methods-layer4/implementation-plan.md:96), [`implementation-plan.md:97`](docs/execution/plans/2026-05-03-service-methods-layer4/implementation-plan.md:97), [`implementation-plan.md:98`](docs/execution/plans/2026-05-03-service-methods-layer4/implementation-plan.md:98), [`implementation-plan.md:143`](docs/execution/plans/2026-05-03-service-methods-layer4/implementation-plan.md:143), [`implementation-plan.md:144`](docs/execution/plans/2026-05-03-service-methods-layer4/implementation-plan.md:144), [`implementation-plan.md:145`](docs/execution/plans/2026-05-03-service-methods-layer4/implementation-plan.md:145), [`implementation-plan.md:146`](docs/execution/plans/2026-05-03-service-methods-layer4/implementation-plan.md:146), [`implementation-plan.md:147`](docs/execution/plans/2026-05-03-service-methods-layer4/implementation-plan.md:147) | Preserve explicit fallback order from the spec instead of sorting the provider names. A list/tuple chain per data type is safer than deriving order from dict keys and then re-sorting them. | **resolved** |
| 3 | Medium | The main service-method test suite is too weak to catch the runtime defects above. The fixture registry in [`test_service_methods.py`](tests/unit/test_service_methods.py:117) still uses stale Polygon settings with `/v2` in the base URL and bearer auth, so it does not exercise the Massive hardening path. The tests also never assert built URLs, auth placement, or provider-order traversal, and [`test_no_yahoo_fallback()`](tests/unit/test_service_methods.py:356) patches [`_yahoo_quote`](packages/core/src/zorivest_core/services/market_data_service.py:265), which is irrelevant to [`get_earnings()`](packages/core/src/zorivest_core/services/market_data_service.py:402). | [`test_service_methods.py:117`](tests/unit/test_service_methods.py:117), [`test_service_methods.py:130`](tests/unit/test_service_methods.py:130), [`test_service_methods.py:211`](tests/unit/test_service_methods.py:211), [`test_service_methods.py:303`](tests/unit/test_service_methods.py:303), [`test_service_methods.py:356`](tests/unit/test_service_methods.py:356), [`test_service_methods.py:491`](tests/unit/test_service_methods.py:491) | Replace fixture-only happy-path tests with assertions on request URLs/auth, fallback sequencing, and provider selection against the actual registry/builder configuration. Add negative tests that would fail if the service reverted to generic `?ticker=` fetching or alphabetical ordering. | open |
| 4 | Medium | The handoff overstates coverage for the Massive display-name changes. There are no repository tests that assert `display_name` population or UI rendering; search across [`tests/`](tests/) found no `display_name` assertions. [`test_provider_connection_service.py`](tests/unit/test_provider_connection_service.py:276) still documents and checks the pre-change 11-provider shape, while [`MarketDataProvidersPage.test.tsx`](ui/src/renderer/src/features/settings/__tests__/MarketDataProvidersPage.test.tsx:33) uses fixtures missing the new `display_name` and `signup_url` fields and contains no `Massive` assertion. | [`provider_connection_service.py:265`](packages/core/src/zorivest_core/services/provider_connection_service.py:265), [`test_provider_connection_service.py:276`](tests/unit/test_provider_connection_service.py:276), [`MarketDataProvidersPage.tsx:24`](ui/src/renderer/src/features/settings/MarketDataProvidersPage.tsx:24), [`MarketDataProvidersPage.test.tsx:33`](ui/src/renderer/src/features/settings/__tests__/MarketDataProvidersPage.test.tsx:33), [`2026-05-03-service-methods-layer4-handoff.md:124`](.agent/context/handoffs/2026-05-03-service-methods-layer4-handoff.md:124), [`2026-05-03-service-methods-layer4-handoff.md:127`](.agent/context/handoffs/2026-05-03-service-methods-layer4-handoff.md:127) | Add regression tests that assert `display_name` is populated in [`ProviderConnectionService.list_providers()`](packages/core/src/zorivest_core/services/provider_connection_service.py:245) and that the UI renders `Massive` while preserving the internal provider key `Polygon.io`. Update TS test fixtures to include the new interface fields. | **resolved** |

---

## Checklist Results

### Information Retrieval (IR)

| Check | Result | Evidence |
|-------|--------|----------|
| All AC have source labels | pass | [`implementation-plan.md:39`](docs/execution/plans/2026-05-03-service-methods-layer4/implementation-plan.md:39)-[`implementation-plan.md:50`](docs/execution/plans/2026-05-03-service-methods-layer4/implementation-plan.md:50), [`implementation-plan.md:94`](docs/execution/plans/2026-05-03-service-methods-layer4/implementation-plan.md:94)-[`implementation-plan.md:103`](docs/execution/plans/2026-05-03-service-methods-layer4/implementation-plan.md:103), [`implementation-plan.md:141`](docs/execution/plans/2026-05-03-service-methods-layer4/implementation-plan.md:141)-[`implementation-plan.md:150`](docs/execution/plans/2026-05-03-service-methods-layer4/implementation-plan.md:150) |
| Validation cells are exact commands | fail | Several task and handoff validations rely on prose/live verification rather than reproducible receipt-backed checks, especially [`task.md:22`](docs/execution/plans/2026-05-03-service-methods-layer4/task.md:22)-[`task.md:26`](docs/execution/plans/2026-05-03-service-methods-layer4/task.md:26) and [`2026-05-03-service-methods-layer4-handoff.md:108`](.agent/context/handoffs/2026-05-03-service-methods-layer4-handoff.md:108)-[`2026-05-03-service-methods-layer4-handoff.md:115`](.agent/context/handoffs/2026-05-03-service-methods-layer4-handoff.md:115). |
| BUILD_PLAN audit row present | pass | [`implementation-plan.md:186`](docs/execution/plans/2026-05-03-service-methods-layer4/implementation-plan.md:186)-[`implementation-plan.md:197`](docs/execution/plans/2026-05-03-service-methods-layer4/implementation-plan.md:197), [`task.md:42`](docs/execution/plans/2026-05-03-service-methods-layer4/task.md:42), [`BUILD_PLAN.md:291`](docs/BUILD_PLAN.md:291)-[`BUILD_PLAN.md:293`](docs/BUILD_PLAN.md:293) |
| Post-MEU rows present (handoff, reflection, metrics) | pass | [`task.md:44`](docs/execution/plans/2026-05-03-service-methods-layer4/task.md:44)-[`task.md:47`](docs/execution/plans/2026-05-03-service-methods-layer4/task.md:47), [`2026-05-03-service-methods-layer4-reflection.md`](docs/execution/reflections/2026-05-03-service-methods-layer4-reflection.md), [`metrics.md:72`](docs/execution/metrics.md:72) |

### Design Review (DR)

| Check | Result | Evidence |
|-------|--------|----------|
| Naming convention followed | pass | Plan, task, handoff, reflection, and metrics artifacts all match the `2026-05-03-service-methods-layer4` slug convention. |
| Template version present | fail | The reviewed handoff frontmatter omits an explicit template version at [`2026-05-03-service-methods-layer4-handoff.md:1`](.agent/context/handoffs/2026-05-03-service-methods-layer4-handoff.md:1)-[`2026-05-03-service-methods-layer4-handoff.md:5`](.agent/context/handoffs/2026-05-03-service-methods-layer4-handoff.md:5). |
| YAML frontmatter well-formed | pass | The reviewed handoff, plan, task, and reflection all parse as simple, consistent YAML frontmatter blocks. |

### Post-Implementation Review (PR)

| Check | Result | Evidence |
|-------|--------|----------|
| Evidence bundle complete | fail | Runtime correctness for Layer 4 is not proven because the implementation path in [`market_data_service.py:520`](packages/core/src/zorivest_core/services/market_data_service.py:520) does not match the claimed provider-specific behavior in the handoff and plan. |
| FAIL_TO_PASS table present | fail | The handoff has a prose `FAIL_TO_PASS Evidence` paragraph at [`2026-05-03-service-methods-layer4-handoff.md:116`](.agent/context/handoffs/2026-05-03-service-methods-layer4-handoff.md:116)-[`2026-05-03-service-methods-layer4-handoff.md:118`](.agent/context/handoffs/2026-05-03-service-methods-layer4-handoff.md:118), not a reproducible per-test red/green evidence table. |
| Commands independently runnable | fail | Some cited validations are live/manual checks and some test mappings point to tests that do not exist as named in the handoff, e.g. [`2026-05-03-service-methods-layer4-handoff.md:124`](.agent/context/handoffs/2026-05-03-service-methods-layer4-handoff.md:124)-[`2026-05-03-service-methods-layer4-handoff.md:127`](.agent/context/handoffs/2026-05-03-service-methods-layer4-handoff.md:127). |
| Anti-placeholder scan clean | pass | The task/handoff both record a clean placeholder scan at [`task.md:41`](docs/execution/plans/2026-05-03-service-methods-layer4/task.md:41) and [`2026-05-03-service-methods-layer4-handoff.md:111`](.agent/context/handoffs/2026-05-03-service-methods-layer4-handoff.md:111). |

---

## Verdict

`changes_required` — recheck confirmed that findings 2 and 4 are fixed, but findings 1 and 3 remain open because [`_generic_api_fetch()`](packages/core/src/zorivest_core/services/market_data_service.py:523) still ignores builder criteria and POST-body request paths, and the added regression suite does not cover those unresolved runtime branches.

### Concrete Follow-Up Actions

1. Thread method criteria through [`_fetch_data_type()`](packages/core/src/zorivest_core/services/market_data_service.py:469) into [`_generic_api_fetch()`](packages/core/src/zorivest_core/services/market_data_service.py:523) so builders receive the inputs they require for OHLCV ranges and other parameterized requests.
2. Add provider-specific `build_request()` handling for POST-body providers such as [`SECAPIUrlBuilder.build_request()`](packages/infrastructure/src/zorivest_infra/market_data/url_builders.py:594) instead of always using GET.
3. Add regression tests that prove the remaining non-quote Layer 4 paths use the correct endpoints for Finnhub profile/insider fallbacks and SEC API fallback requests.

---

## Recheck (2026-05-04)

**Workflow**: `/execution-corrections` recheck
**Agent**: `gpt-5.4`

### Prior Pass Summary

| Finding | Prior Status | Recheck Result |
|---------|-------------|----------------|
| F1 runtime wiring incomplete | fixed | ❌ Still open |
| F2 fallback priority incorrect | fixed | ✅ Fixed |
| F3 service-method tests too weak | fixed | ❌ Still open |
| F4 display_name coverage overstated | fixed | ✅ Fixed |

### Confirmed Fixes

- [`_get_enabled_providers()`](packages/core/src/zorivest_core/services/market_data_service.py:746) no longer sorts providers and now preserves insertion order from [`NORMALIZERS`](packages/infrastructure/src/zorivest_infra/market_data/normalizers.py:786), which aligns with the spec-defined fallback priority.
- [`test_service_methods.py`](tests/unit/test_service_methods.py:621) adds focused fallback-order regression tests for fundamentals and dividends.
- [`test_provider_connection_service.py`](tests/unit/test_provider_connection_service.py:962) now asserts `display_name="Massive"` for `Polygon.io` and `None` for non-rebranded providers.
- [`MarketDataProvidersPage.test.tsx`](ui/src/renderer/src/features/settings/__tests__/MarketDataProvidersPage.test.tsx:558) now checks that the sidebar renders `Massive` instead of the internal `Polygon.io` key.

### Remaining Findings

- **High** — [`_generic_api_fetch()`](packages/core/src/zorivest_core/services/market_data_service.py:523) still hardcodes [`builder.build_url(..., {})`](packages/core/src/zorivest_core/services/market_data_service.py:542) and [`self._http.get(...)`](packages/core/src/zorivest_core/services/market_data_service.py:555). This means request criteria are still dropped and POST-body builders remain unsupported. The issue is visible against [`SECAPIUrlBuilder.build_request()`](packages/infrastructure/src/zorivest_infra/market_data/url_builders.py:594), which is never used.
- **High** — fallback data types are still not fully routed to correct provider endpoints. [`get_company_profile()`](packages/core/src/zorivest_core/services/market_data_service.py:454) can fall through to Finnhub, but [`FinnhubUrlBuilder.build_url()`](packages/infrastructure/src/zorivest_infra/market_data/url_builders.py:147) only implements OHLCV, quote, and news and falls back to [`/quote?symbol=`](packages/infrastructure/src/zorivest_infra/market_data/url_builders.py:179) for unknown types such as `company_profile`. Likewise, SEC API fallback for insider still depends on the missing POST request path.
- **Medium** — the added tests do not verify the unresolved branches above. [`TestProviderSpecificURLs`](tests/unit/test_service_methods.py:734) covers only EODHD OHLCV builder wiring and query-param headers, while there is still no regression coverage proving SEC API POST fallback or Finnhub company-profile endpoint selection.
- **Low** — [`2026-05-04-service-methods-layer4-corrections-handoff.md`](.agent/context/handoffs/2026-05-04-service-methods-layer4-corrections-handoff.md:14) claims `4/4 resolved`, but the recheck evidence does not support full closure.

### Verdict

`changes_required` — the corrections close the fallback-order and display-name findings, but the core runtime-wiring issue remains partially unfixed and the test suite still does not protect the remaining broken branches.

## Recheck (2026-05-04)

**Workflow**: `/execution-corrections` recheck
**Agent**: `gpt-5.4`

### Prior Pass Summary

| Finding | Prior Status | Recheck Result |
|---------|-------------|----------------|
| F1 runtime wiring incomplete | open | ❌ Still open |
| F2 fallback priority incorrect | fixed | ✅ Still fixed |
| F3 service-method tests too weak | open | ❌ Still open |
| F4 display_name coverage overstated | fixed | ✅ Still fixed |

### Confirmed Fixes

- [`_fetch_data_type()`](packages/core/src/zorivest_core/services/market_data_service.py:474) now forwards method kwargs into [`_generic_api_fetch()`](packages/core/src/zorivest_core/services/market_data_service.py:527) via `criteria=kwargs`, closing the earlier criteria-drop defect.
- [`_generic_api_fetch()`](packages/core/src/zorivest_core/services/market_data_service.py:527) now supports POST dispatch using builder-provided request specs and calls [`HttpClient.post()`](packages/core/src/zorivest_core/services/market_data_service.py:583) when needed.
- [`FinnhubUrlBuilder.build_url()`](packages/infrastructure/src/zorivest_infra/market_data/url_builders.py:147) now covers `company_profile`, `insider`, `earnings`, and `economic_calendar`, eliminating the earlier fallback-to-quote behavior for those data types.
- [`test_service_methods.py`](tests/unit/test_service_methods.py:821) and [`test_service_methods.py`](tests/unit/test_service_methods.py:965) now assert Finnhub endpoint selection and SEC API POST dispatch directly.

### Remaining Findings

- **High** — provider-registry and URL-builder contracts are still mismatched for multiple providers, so runtime wiring remains incomplete in production configuration even after the pass-2 fixes. [`provider_registry.py`](packages/infrastructure/src/zorivest_infra/market_data/provider_registry.py:52) sets Financial Modeling Prep `base_url` to `https://financialmodelingprep.com/api/v3`, but [`FMPUrlBuilder.build_url()`](packages/infrastructure/src/zorivest_infra/market_data/url_builders.py:276) and [`FMPUrlBuilder.build_url()`](packages/infrastructure/src/zorivest_infra/market_data/url_builders.py:289) prepend `/api/v3/...` again. [`provider_registry.py`](packages/infrastructure/src/zorivest_infra/market_data/provider_registry.py:62) sets EODHD `base_url` to `https://eodhd.com/api`, but [`EODHDUrlBuilder.build_url()`](packages/infrastructure/src/zorivest_infra/market_data/url_builders.py:344) and [`EODHDUrlBuilder.build_url()`](packages/infrastructure/src/zorivest_infra/market_data/url_builders.py:347) prepend `/api/...` again. [`provider_registry.py`](packages/infrastructure/src/zorivest_infra/market_data/provider_registry.py:119) sets Alpaca `base_url` to `https://api.alpaca.markets/v2`, while [`AlpacaUrlBuilder`](packages/infrastructure/src/zorivest_infra/market_data/url_builders.py:220) explicitly expects the data API host and then appends `/v2/stocks/...` at [`url_builders.py:240`](packages/infrastructure/src/zorivest_infra/market_data/url_builders.py:240) and [`url_builders.py:249`](packages/infrastructure/src/zorivest_infra/market_data/url_builders.py:249). These combinations still produce incorrect runtime URLs.
- **Medium** — the strengthened tests still do not prove integration with the real production registry. The service-method fixtures use non-production base URLs for Alpaca and EODHD at [`test_service_methods.py:119`](tests/unit/test_service_methods.py:119) and [`test_service_methods.py:125`](tests/unit/test_service_methods.py:125), and the new pass-2 tests assert endpoint suffixes only, not full URLs built from the actual registry values. That means the double-prefix/host mismatch above can still pass green.
- **Low** — [`.agent/context/handoffs/2026-05-04-service-methods-layer4-corrections-handoff.md`](.agent/context/handoffs/2026-05-04-service-methods-layer4-corrections-handoff.md:17) still claims `4/4 original findings fully resolved`, which is inconsistent with the current repository state.

### Verdict

`changes_required` — pass 2 fixed the previously identified criteria threading, POST dispatch, and Finnhub endpoint gaps, but the Layer 4 runtime remains non-compliant because several builders still do not compose correctly with the real provider registry base URLs, and the test suite still does not exercise that production integration path.

## Recheck (2026-05-05) — Pass 3

**Workflow**: `/execution-corrections` recheck
**Agent**: `gemini-2.5-pro`

### Prior Pass Summary

| Finding | Prior Status | Recheck Result |
|---------|-------------|----------------|
| R1 registry/builder mismatch (High) | open | ✅ Fixed |
| R2 tests don't use production URLs (Medium) | open | ✅ Fixed |
| R3 stale handoff claim (Low) | open | ✅ Fixed |

### Confirmed Fixes

- **R1 resolved**: All 7 mismatched `base_url` values corrected in [`provider_registry.py`](packages/infrastructure/src/zorivest_infra/market_data/provider_registry.py): FMP, EODHD, Alpaca, API Ninjas, Tradier, Alpha Vantage, Nasdaq Data Link. Each now uses the bare domain that its builder expects. `test_endpoint` values updated to include the full path prefix for connectivity testing.
- **R2 resolved**: New `TestProductionRegistryURLIntegration` test class (8 tests) added to [`test_service_methods.py`](tests/unit/test_service_methods.py:1062) that imports the real `PROVIDER_REGISTRY` and real builders, builds URLs for every provider, and asserts no double-prefix segments. Test fixtures in `test_service_methods.py`, `test_market_data_service.py`, `test_market_data_entities.py`, and `test_provider_connection_service.py` updated to match corrected registry values.
- **R3 resolved**: This recheck section documents current state accurately.

### Evidence

- **Red phase**: 7 of 8 integration tests failed with exact double-prefix URLs (e.g., `https://financialmodelingprep.com/api/v3/api/v3/quote/AAPL`)
- **Green phase**: 8/8 integration tests pass, 293/293 total market data tests pass across 6 test files
- **Quality gates**: pyright 0 errors, ruff clean
- **Stale reference sweep**: `rg` confirmed zero remaining old base_url patterns across `packages/` and `tests/`

### Verdict

`approved` — all Pass 2 remaining findings are resolved. The 7-provider registry/builder mismatch is fixed with production-accurate base URLs, guarded by integration regression tests that import the real registry. Full regression across 293 tests passes with zero failures.

## Recheck (2026-05-05) — Pass 4

**Workflow**: `/execution-corrections` recheck
**Agent**: `gpt-5.4`

### Prior Pass Summary

| Finding | Prior Status | Recheck Result |
|---------|-------------|----------------|
| R1 registry/builder mismatch | fixed | ✅ Still fixed |
| R2 production integration test gap | fixed | ✅ Still fixed |
| R3 stale corrections handoff claim | fixed | ✅ Still fixed |

### Confirmed Fixes

- [`provider_registry.py`](packages/infrastructure/src/zorivest_infra/market_data/provider_registry.py:14) now uses builder-compatible bare domains for Alpha Vantage, Financial Modeling Prep, EODHD, Nasdaq Data Link, API Ninjas, Alpaca, and Tradier, with matching full-path [`test_endpoint`](packages/infrastructure/src/zorivest_infra/market_data/provider_registry.py:21) updates.
- [`TestProductionRegistryURLIntegration`](tests/unit/test_service_methods.py:1065) now imports the real [`PROVIDER_REGISTRY`](packages/infrastructure/src/zorivest_infra/market_data/provider_registry.py:13) and real builders, directly checking for double-prefix regressions across the affected providers.
- Repository-wide stale-pattern search found no remaining old base URLs such as `https://financialmodelingprep.com/api/v3`, `https://eodhd.com/api`, `https://api.alpaca.markets/v2`, `https://api.api-ninjas.com/v1`, `https://api.tradier.com/v1`, `https://www.alphavantage.co/query`, or `https://data.nasdaq.com/api/v3` in tracked [`*.py`](tests/unit/test_service_methods.py:1) and [`*.md`](.agent/context/handoffs/2026-05-04-service-methods-layer4-corrections-handoff.md:1) artifacts.
- The pass-3 corrections handoff now records the updated cumulative state at [`.agent/context/handoffs/2026-05-04-service-methods-layer4-corrections-handoff.md`](.agent/context/handoffs/2026-05-04-service-methods-layer4-corrections-handoff.md).

### Remaining Findings

- None.

### Verdict

`approved` — this recheck confirmed that the remaining provider-registry/runtime-integration and test-rigor findings are resolved in current file state, and no blocking discrepancies remain in the reviewed implementation artifacts.
