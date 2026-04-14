---
project: "2026-04-13-fetch-step-integration"
source: "docs/execution/plans/2026-04-13-fetch-step-integration/implementation-plan.md"
meus: ["MEU-PW2"]
status: "execution"
template_version: "2.0"
---

# Task — Fetch Step Integration (MEU-PW2)

> **Project:** `2026-04-13-fetch-step-integration`
> **Type:** Infrastructure/Domain
> **Estimate:** 7 modified + 2 new = 9 files across 3 packages

## Task Table

| # | Task | Owner | Deliverable | Validation | Status |
|---|------|-------|-------------|------------|--------|
| 0 | Write source-backed FIC (Feature Intent Contract) | orchestrator | FIC section in implementation-plan.md with AC-1..AC-8, each labeled Spec/Local Canon/Research-backed | `rg "AC-[0-9]" docs/execution/plans/2026-04-13-fetch-step-integration/implementation-plan.md *> C:\Temp\zorivest\fic-check.txt` (expect ≥8 matches) | `[x]` |
| 1 | Write Red-phase tests — `test_market_data_adapter.py` (AC-1/2/5/6) | tester | `tests/unit/test_market_data_adapter.py` | `uv run pytest tests/unit/test_market_data_adapter.py --tb=short -v *> C:\Temp\zorivest\pytest-pw2-adapter-red.txt; Get-Content C:\Temp\zorivest\pytest-pw2-adapter-red.txt \| Select-Object -Last 20` (expect all FAILED/ERROR — no implementation yet) | `[x]` |
| 2 | Write Red-phase tests — PW2 cache tests in `test_fetch_step.py` (AC-3/4) | tester | New test functions in existing file | `uv run pytest tests/unit/test_fetch_step.py -k "PW2" --tb=short -v *> C:\Temp\zorivest\pytest-pw2-cache-red.txt; Get-Content C:\Temp\zorivest\pytest-pw2-cache-red.txt \| Select-Object -Last 20` (expect FAILED) | `[x]` |
| 3 | Write Red-phase tests — `test_pipeline_fetch_e2e.py` (AC-7) | tester | `tests/integration/test_pipeline_fetch_e2e.py` | `uv run pytest tests/integration/test_pipeline_fetch_e2e.py --tb=short -v *> C:\Temp\zorivest\pytest-pw2-e2e-red.txt; Get-Content C:\Temp\zorivest\pytest-pw2-e2e-red.txt \| Select-Object -Last 20` (expect FAILED/ERROR) | `[x]` |
| 4 | Save FAIL evidence — run all Red tests and capture output | tester | Failure output in `C:\Temp\zorivest\pytest-pw2-red.txt` | `uv run pytest tests/unit/test_market_data_adapter.py tests/unit/test_fetch_step.py -k "PW2" --tb=short -v *> C:\Temp\zorivest\pytest-pw2-red.txt` | `[x]` |
| 5 | Fix `fetch_with_cache()` — add `timeout` param (F2 prerequisite) | coder | Updated `http_cache.py` with `timeout: int = 30` | `uv run pyright packages/infrastructure/ *> C:\Temp\zorivest\pyright-pw2.txt` | `[x]` |
| 6 | Add `FetchAdapterResult` TypedDict + `MarketDataAdapterPort` to `ports.py` | coder | `MarketDataAdapterPort` Protocol + `FetchAdapterResult` TypedDict | `uv run pyright packages/core/ *> C:\Temp\zorivest\pyright-pw2.txt` | `[x]` |
| 7 | Create `MarketDataProviderAdapter` in infra | coder | `packages/infrastructure/src/zorivest_infra/market_data/market_data_adapter.py` | `uv run pyright packages/infrastructure/ *> C:\Temp\zorivest\pyright-pw2.txt` | `[x]` |
| 8 | Add `warnings` field to `FetchResult` | coder | Updated dataclass in `domain/pipeline.py` | `uv run pytest tests/unit/test_fetch_step.py -x --tb=short *> C:\Temp\zorivest\pytest-pw2.txt` | `[x]` |
| 9 | Implement `FetchStep._check_cache()` with TTL + market-hours (AC-3/4) | coder | Cache check logic in `pipeline_steps/fetch_step.py` | `uv run pytest tests/unit/test_fetch_step.py -k "PW2" -x --tb=short *> C:\Temp\zorivest\pytest-pw2.txt` | `[x]` |
| 10 | Add cache upsert after successful fetch | coder | Cache-save logic in `fetch_step.py` execute() | `uv run pytest tests/unit/test_fetch_step.py -x --tb=short *> C:\Temp\zorivest\pytest-pw2.txt` | `[x]` |
| 11 | Add `fetch_cache_repo` to `PipelineRunner` constructor (8→9 kwargs) | coder | Updated constructor + context injection | `uv run pyright packages/core/ *> C:\Temp\zorivest\pyright-pw2.txt` | `[x]` |
| 12 | Update PW1 contract tests — `test_pipeline_runner_constructor.py` (F5) | coder | 8→9 keys, add `fetch_cache_repo` to expected sets | `uv run pytest tests/unit/test_pipeline_runner_constructor.py -x --tb=short -v *> C:\Temp\zorivest\pytest-pw2.txt` | `[x]` |
| 13 | Update PW1 contract tests — `test_pipeline_wiring.py` (F5) | coder | `provider_adapter` is not None, add `fetch_cache_repo` check, update key counts | `uv run pytest tests/integration/test_pipeline_wiring.py -x --tb=short -v *> C:\Temp\zorivest\pytest-pw2.txt` | `[x]` |
| 14 | Wire adapter, rate limiter, cache repo in `main.py` | coder | Updated `main.py` PipelineRunner construction | `uv run pytest tests/unit/test_api_scheduling.py -x --tb=short *> C:\Temp\zorivest\pytest-pw2.txt` | `[x]` |
| 15 | Run quality checks (pyright + ruff) | tester | Zero errors | `uv run pyright packages/ *> C:\Temp\zorivest\pyright-pw2.txt; uv run ruff check packages/ *> C:\Temp\zorivest\ruff-pw2.txt` | `[x]` |
| 16 | Run MEU gate | tester | MEU gate passes | `uv run python tools/validate_codebase.py --scope meu *> C:\Temp\zorivest\validate-pw2.txt` | `[x]` |
| 17 | Run full regression suite | tester | All existing tests pass | `uv run pytest tests/ -x --tb=short -v *> C:\Temp\zorivest\pytest-pw2-full.txt` | `[x]` |
| 18 | Add MEU-PW2 row to `docs/BUILD_PLAN.md` P2.5b table (F3) | orchestrator | New row added with ✅ | `rg "MEU-PW2" docs/BUILD_PLAN.md *> C:\Temp\zorivest\buildplan-check.txt` (expect ≥1 match) | `[x]` |
| 19 | Regenerate OpenAPI spec (api/ modified) | coder | Updated `openapi.committed.json` | `uv run python tools/export_openapi.py -o openapi.committed.json *> C:\Temp\zorivest\openapi.txt` | `[x]` |
| 20 | Update `.agent/context/meu-registry.md` | orchestrator | MEU-PW2 row → ✅ | `rg "MEU-PW2" .agent/context/meu-registry.md` | `[x]` |
| 21 | Save session state to pomera_notes | orchestrator | `Memory/Session/Zorivest-fetch-step-integration-2026-04-13` | MCP: `pomera_notes(action="search", search_term="Zorivest-fetch*")` returns ≥1 | `[x]` |
| 22 | Create handoff | reviewer | `.agent/context/handoffs/114-2026-04-13-fetch-step-integration-bp09s49.5.md` | `Test-Path .agent/context/handoffs/114-2026-04-13-fetch-step-integration-bp09s49.5.md` | `[x]` |
| 23 | Create reflection | orchestrator | `docs/execution/reflections/2026-04-13-fetch-step-integration-reflection.md` | `Test-Path docs/execution/reflections/2026-04-13-fetch-step-integration-reflection.md` | `[x]` |
| 24 | Append metrics row | orchestrator | Row appended to `docs/execution/metrics.md` | `Get-Content docs/execution/metrics.md \| Select-Object -Last 3` | `[x]` |
| 25 | Prepare proposed commit messages | orchestrator | Commit messages for user approval | N/A | `[x]` |

### Status Legend

| Symbol | Meaning |
|--------|---------|
| `[ ]` | Not started |
| `[/]` | In progress |
| `[x]` | Complete |
| `[B]` | Blocked (must link follow-up) |

### Task Order Rationale (F4 + Recheck Compliance)

Per AGENTS.md §TDD Protocol and §FIC-Based TDD Workflow, the task order follows:
0. **FIC** (Task 0): Source-backed Feature Intent Contract — already embedded in implementation-plan.md AC tables
1. **Red phase** (Tasks 1–4): Write all tests first, run them to confirm FAIL, save evidence
2. **Green phase** (Tasks 5–14): Fix prerequisite (Task 5), then implement in dependency order (port → adapter → domain → step → runner → tests → wiring)
3. **Quality gates** (Tasks 15–17): pyright, ruff, MEU gate, regression
4. **Close-out** (Tasks 18–25): BUILD_PLAN, OpenAPI, registry, pomera, handoff, reflection, metrics, commits

> **State note**: `status: in_planning` reflects that only Task 0 (FIC) was completed during planning. The `http_cache.py` prerequisite fix (Task 5) was reverted to restore a clean pre-execution state per reviewer directive. Task 5 will be the first Green-phase action after user approval.

## Corrections (Codex Review Findings)

| # | Task | Finding | Status |
|---|------|---------|--------|
| C1 | Forward stale cache metadata through execute() for ETag revalidation | F1 (High) | `[x]` |
| C2 | Normalize entity key to use resolved_criteria for both cache read/write | F2 (High) | `[x]` |
| C3 | Replace `_is_market_closed()` with canonical `is_market_closed()` | F3 (High) | `[x]` |
| C4 | Fix 3 ruff errors, rewrite `test_AC_F11` with real cache repo | F4 (Med) | `[x]` |
| C5 | Add regression test: weekday after-hours TTL extension | F3-reg | `[x]` |
| C6 | Add regression test: entity key uses resolved criteria | F2-reg | `[x]` |
| C7 | Rewrite e2e revalidation test to go through step.execute() | F1-reg | `[x]` |
| C8 | Run full validation: pyright 0, ruff 0, pytest 1928/0, MEU gate 8/8 | verify | `[x]` |
| C9 | Update handoff evidence bundle | docs | `[x]` |
