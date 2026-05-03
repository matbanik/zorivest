---
date: "2026-05-02"
review_mode: "handoff"
target_plan: "docs/execution/plans/2026-05-02-post-body-runtime-wiring/implementation-plan.md"
target_handoff: ".agent/context/handoffs/2026-05-02-post-body-runtime-wiring-handoff.md"
verdict: "approved"
findings_count: 0
template_version: "2.1"
requested_verbosity: "standard"
agent: "GPT-5 Codex"
---

# Critical Review: 2026-05-02-post-body-runtime-wiring

> **Review Mode**: `handoff`
> **Verdict**: `approved`

---

## Scope

**Target**: `.agent/context/handoffs/2026-05-02-post-body-runtime-wiring-handoff.md`

**Correlation rationale**: The explicit handoff path matches plan folder `docs/execution/plans/2026-05-02-post-body-runtime-wiring/` and project slug `2026-05-02-post-body-runtime-wiring`. The plan/task identify one MEU: MEU-189.

**Expanded review set**:
- `.agent/context/handoffs/2026-05-02-post-body-runtime-wiring-handoff.md`
- `docs/execution/plans/2026-05-02-post-body-runtime-wiring/implementation-plan.md`
- `docs/execution/plans/2026-05-02-post-body-runtime-wiring/task.md`
- `docs/execution/reflections/2026-05-02-post-body-runtime-wiring-reflection.md`
- Changed production/test files named by the handoff
- Registry/status artifacts touched by the handoff claims

**Checklist Applied**: IR, PR, DR

---

## Findings

| # | Severity | Finding | File:Line | Recommendation | Status |
|---|----------|---------|-----------|----------------|--------|
| 1 | High | OpenFIGI adapter runtime builds `https://api.openfigi.com/v3/v3/mapping`, so the new POST adapter path calls a malformed URL. The provider registry already includes `/v3` in `base_url`, while `OpenFIGIUrlBuilder` appends `/v3/mapping` again. The focused runtime probe logged `url=https://api.openfigi.com/v3/v3/mapping`. | `packages/infrastructure/src/zorivest_infra/market_data/provider_registry.py:105`, `packages/infrastructure/src/zorivest_infra/market_data/url_builders.py:544`, `packages/infrastructure/src/zorivest_infra/market_data/url_builders.py:558` | Make OpenFIGI URL construction single-source: either set the registry base URL to `https://api.openfigi.com` or change the builder paths to `/mapping`. Add exact URL assertions for adapter POST dispatch. | fixed |
| 2 | High | AC-8 is not implemented for POST providers. `_fetch_multi_ticker()` always calls `builder.build_url(...)` and then `_do_fetch()` with default `method="GET"` and no JSON body. For OpenFIGI multi-ticker input, the probe produced `post_calls=0` and `get_calls=2`. | `packages/infrastructure/src/zorivest_infra/market_data/market_data_adapter.py:178` | Route multi-ticker POST providers through `build_request()` and pass `method` plus `json_body`, or intentionally collapse POST-capable multi-ticker requests into a single RequestSpec. Add an OpenFIGI multi-ticker regression test. | fixed |
| 3 | Medium | Test rigor gap: `test_adapter_post_dispatch.py` does not cover the AC-8 multi-ticker POST contract, and the OpenFIGI URL check only asserts `"/v3/mapping" in url_called`, which permits the broken `/v3/v3/mapping` URL. This allowed Findings 1 and 2 to pass with `24 passed`. | `tests/unit/test_adapter_post_dispatch.py:69`, `tests/unit/test_adapter_post_dispatch.py:72`, `tests/unit/test_adapter_post_dispatch.py:102` | Strengthen adapter tests to assert exact URLs, exact method dispatch, and multi-ticker POST body contents. AC-8 should be represented by a test that fails on GET fallback. | fixed |
| 4 | Low | Completion/status artifacts conflict. `task.md` says `[MKTDATA-OPENFIGI405]` was already archived, but `known-issues.md` still has the issue in active/mitigated content. `meu-registry.md` also contains duplicate MEU-189 rows with both planned and completed statuses. | `docs/execution/plans/2026-05-02-post-body-runtime-wiring/task.md:34`, `.agent/context/known-issues.md:63`, `.agent/context/meu-registry.md:112`, `.agent/context/meu-registry.md:417` | After runtime fixes, reconcile known issue and registry state so only one MEU-189 status remains and the issue status matches the verified outcome. | fixed |

---

## Commands Executed

| Command | Result |
|---------|--------|
| `git status --short` | Working tree contains the claimed MEU-189 changes plus untracked handoff/plan/test artifacts. |
| `git diff --stat` | 12 tracked files changed, 195 insertions, 74 deletions. |
| `rg -n "MEU-189\|post-body-runtime\|POST-Body Runtime" docs/BUILD_PLAN.md .agent/context/meu-registry.md docs/execution/metrics.md` | Found MEU-189 status in `docs/BUILD_PLAN.md`, duplicate registry entries, and metrics row. |
| `uv run pytest tests/unit/test_http_cache.py tests/unit/test_adapter_post_dispatch.py tests/unit/test_openfigi_connection.py -q` | `24 passed, 1 warning in 0.40s`. |
| `uv run pyright packages/` | `0 errors, 0 warnings, 0 informations`. |
| `uv run ruff check packages/` | `All checks passed!` |
| Focused Python runtime probe for OpenFIGI multi-ticker adapter path | Logged `https://api.openfigi.com/v3/v3/mapping`, `post_calls=0`, `get_calls=2`, `rate_limiter_calls=2`. |

---

## Checklist Results

### Implementation Review

| Check | Result | Evidence |
|-------|--------|----------|
| IR-1 Live runtime evidence | fail | No integration-style adapter test caught the malformed OpenFIGI URL or GET fallback. Focused probe reproduced both. |
| IR-2 Stub behavioral compliance | not_applicable | No stubs were part of MEU-189 runtime wiring. |
| IR-3 Error mapping completeness | not_applicable | No REST write route or error mapper changed. |
| IR-4 Fix generalization | fail | POST dispatch was added to the single-request adapter path but not generalized to `_fetch_multi_ticker()`. |
| IR-5 Test rigor audit | fail | `test_http_cache.py`: strong. `test_openfigi_connection.py`: adequate. `test_adapter_post_dispatch.py`: weak for URL exactness and missing AC-8 multi-ticker coverage. |
| IR-6 Boundary validation coverage | not_applicable | MEU-189 does not introduce external write-boundary schema changes. |

### Post-Implementation Review

| Check | Result | Evidence |
|-------|--------|----------|
| Evidence bundle complete | partial | Targeted test/static evidence is reproducible, but runtime probe contradicts AC-8 and OpenFIGI adapter URL claims. |
| FAIL_TO_PASS table present | partial | Handoff summarizes red/green tests but does not include a detailed FAIL_TO_PASS table. |
| Commands independently runnable | pass | Verification commands ran with receipt files under `C:\Temp\zorivest\`. |
| Anti-placeholder scan clean | not_rerun | Handoff claims clean; this review prioritized runtime contract checks after finding blocking behavior. |

### Design/Docs Review

| Check | Result | Evidence |
|-------|--------|----------|
| Naming convention followed | pass | Handoff and plan folder use date-based slug naming. |
| Template version present | pass | Handoff has frontmatter and verbosity; review uses template v2.1. |
| YAML frontmatter well-formed | pass | Files loaded successfully through the text editor MCP. |
| Status artifacts consistent | fail | `meu-registry.md` contains duplicate MEU-189 rows with conflicting statuses; known issue state conflicts with task claim. |

---

## Verdict

`changes_required` - The implementation proves the `fetch_with_cache()` POST primitive, but the adapter wiring is not correct for OpenFIGI runtime use. The malformed `/v3/v3/mapping` URL and GET fallback in `_fetch_multi_ticker()` are runtime contract failures for the MEU-189 acceptance criteria.

## Follow-Up Actions

1. Fix OpenFIGI URL construction so adapter dispatch targets exactly `https://api.openfigi.com/v3/mapping`.
2. Implement AC-8 for POST-capable multi-ticker requests or revise the plan with a source-backed exception.
3. Add regression tests that fail on `/v3/v3/mapping`, fail on GET fallback for multi-ticker POST providers, and assert exact POST body contents.
4. Reconcile MEU-189 status in `.agent/context/meu-registry.md` and `[MKTDATA-OPENFIGI405]` state after the runtime fix is verified.

## Residual Risk

SEC API and TradingView POST adapter paths were not independently probed beyond static inspection and the green targeted suite. Once the OpenFIGI URL and multi-ticker issues are fixed, those providers should get exact URL/body regression coverage as well.

---

## Recheck (2026-05-02)

**Workflow**: `/execution-critical-review` recheck
**Agent**: GPT-5 Codex

### Prior Pass Summary

| Finding | Prior Status | Recheck Result |
|---------|--------------|----------------|
| F1: OpenFIGI adapter URL double-path `/v3/v3/mapping` | open | Fixed. Builder now appends `/mapping` to the registry base URL, producing `https://api.openfigi.com/v3/mapping`. |
| F2: Multi-ticker POST providers fell back to GET | open | Fixed. `_fetch_multi_ticker()` now uses `build_request()` for POST-capable builders and dispatches a single POST batch. |
| F3: Adapter tests missed exact URL and multi-ticker POST coverage | open | Fixed. Tests now assert exact OpenFIGI/SEC URLs and include OpenFIGI plus SEC multi-ticker POST regression coverage. |
| F4: MEU-189 status artifacts conflicted | open | Fixed for blocking scope. MEU registry now has a single MEU-189 row, and `[MKTDATA-OPENFIGI405]` is archived as resolved. |

### Commands Executed

| Command | Result |
|---------|--------|
| `uv run pytest tests/unit/test_http_cache.py tests/unit/test_adapter_post_dispatch.py tests/unit/test_openfigi_connection.py -q` | `26 passed, 1 warning in 0.39s` |
| `uv run pyright packages/` | `0 errors, 0 warnings, 0 informations` |
| `uv run ruff check packages/` | `All checks passed!` |
| `rg "TODO\|FIXME\|NotImplementedError" packages/infrastructure/src/zorivest_infra/market_data/ packages/core/src/zorivest_core/services/provider_connection_service.py` | 0 matches |
| Focused runtime probe: OpenFIGI, SEC API, TradingView multi-ticker adapter paths | All three providers used `post_calls=1`, `get_calls=0`, `rate_limiter_calls=1` with exact expected URLs. |
| `uv run python tools/validate_codebase.py --scope meu` | All 8 blocking checks passed. Advisory: original handoff evidence-bundle markers remain incomplete. |

### Confirmed Fixes

- OpenFIGI URL construction fixed: [url_builders.py](p:/zorivest/packages/infrastructure/src/zorivest_infra/market_data/url_builders.py:544) and [url_builders.py](p:/zorivest/packages/infrastructure/src/zorivest_infra/market_data/url_builders.py:558).
- Multi-ticker POST batch dispatch fixed: [market_data_adapter.py](p:/zorivest/packages/infrastructure/src/zorivest_infra/market_data/market_data_adapter.py:180).
- Exact URL regression coverage added: [test_adapter_post_dispatch.py](p:/zorivest/tests/unit/test_adapter_post_dispatch.py:72).
- Multi-ticker POST regression coverage added: [test_adapter_post_dispatch.py](p:/zorivest/tests/unit/test_adapter_post_dispatch.py:232) and [test_adapter_post_dispatch.py](p:/zorivest/tests/unit/test_adapter_post_dispatch.py:271).
- OpenFIGI issue archived as resolved: `.agent/context/known-issues-archive.md:233`.
- Single MEU-189 registry row remains: `.agent/context/meu-registry.md:399`.

### Remaining Findings

None blocking.

### Non-Blocking Advisory

`.agent/context/known-issues.md` still contains stale TradingView planning text that says POST runtime wiring is a remaining MEU-189 blocker (`known-issues.md:164`, `known-issues.md:168`, `known-issues.md:174`). The runtime probe confirms TradingView is now POST-callable, so this should be cleaned up in the next context-maintenance pass. It does not block MEU-189 approval because the canonical registry, OpenFIGI archive state, and runtime evidence are now correct.

### Verdict

`approved` - The four prior findings are fixed, targeted tests and static checks pass, direct runtime probes verify OpenFIGI/SEC API/TradingView POST dispatch, and the MEU gate passes all blocking checks.
