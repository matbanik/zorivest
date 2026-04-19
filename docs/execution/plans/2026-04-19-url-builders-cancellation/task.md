---
project: "2026-04-19-url-builders-cancellation"
source: "docs/execution/plans/2026-04-19-url-builders-cancellation/implementation-plan.md"
meus: ["MEU-PW6", "MEU-PW7"]
status: "complete-with-corrections"
template_version: "2.0"
---

# Task — Provider URL Builders + Pipeline Cancellation

> **Project:** `2026-04-19-url-builders-cancellation`
> **Type:** Infrastructure | Domain | API
> **Estimate:** 8 files changed, 2 new

## Task Table

| # | Task | Owner | Deliverable | Validation | Status |
|---|------|-------|-------------|------------|--------|
| 1 | Write FIC + Red-phase tests for `url_builders.py` (AC-PW6-1 through AC-PW6-6) | coder | `tests/unit/test_url_builders.py` | `uv run pytest tests/unit/test_url_builders.py -v *> C:\Temp\zorivest\pytest-pw6-red.txt; Get-Content C:\Temp\zorivest\pytest-pw6-red.txt \| Select-Object -Last 30` (expect FAIL) | `[x]` |
| 2 | Implement `url_builders.py` — builders + registry + `_resolve_tickers()` | coder | `packages/infrastructure/src/zorivest_infra/market_data/url_builders.py` | `uv run pytest tests/unit/test_url_builders.py -v *> C:\Temp\zorivest\pytest-pw6-green.txt; Get-Content C:\Temp\zorivest\pytest-pw6-green.txt \| Select-Object -Last 30` | `[x]` |
| 3 | Write Red-phase tests for adapter refactor (AC-PW6-7, AC-PW6-8, AC-PW6-9) | coder | Updated `tests/unit/test_market_data_adapter.py` | `uv run pytest tests/unit/test_market_data_adapter.py -v *> C:\Temp\zorivest\pytest-pw6-adapter-red.txt; Get-Content C:\Temp\zorivest\pytest-pw6-adapter-red.txt \| Select-Object -Last 30` (expect FAIL) | `[x]` (completed in corrections) |
| 4 | Refactor `market_data_adapter.py` + `http_cache.py` for builder dispatch + header forwarding | coder | Modified adapter + cache | `uv run pytest tests/unit/test_market_data_adapter.py -v *> C:\Temp\zorivest\pytest-pw6-adapter-green.txt; Get-Content C:\Temp\zorivest\pytest-pw6-adapter-green.txt \| Select-Object -Last 30` | `[x]` (completed in corrections) |
| 5 | Write FIC + Red-phase tests for cancellation infrastructure (AC-PW7-1 through AC-PW7-5) | coder | `tests/unit/test_pipeline_cancellation.py` | `uv run pytest tests/unit/test_pipeline_cancellation.py -v *> C:\Temp\zorivest\pytest-pw7-red.txt; Get-Content C:\Temp\zorivest\pytest-pw7-red.txt \| Select-Object -Last 30` (expect FAIL) | `[x]` |
| 6 | Add `CANCELLING` to `PipelineStatus` enum | coder | Modified `enums.py` | `uv run pytest tests/unit/test_pipeline_cancellation.py -k cancelling -v *> C:\Temp\zorivest\pytest-pw7-enum-green.txt; Get-Content C:\Temp\zorivest\pytest-pw7-enum-green.txt \| Select-Object -Last 20` | `[x]` |
| 7 | Implement `_active_tasks`, `cancel_run()` in `PipelineRunner` | coder | Modified `pipeline_runner.py` | `uv run pytest tests/unit/test_pipeline_cancellation.py -k cancel -v *> C:\Temp\zorivest\pytest-pw7-cancel-green.txt; Get-Content C:\Temp\zorivest\pytest-pw7-cancel-green.txt \| Select-Object -Last 30` | `[x]` |
| 8 | Implement `SchedulingService.cancel_run()` | coder | Modified `scheduling_service.py` | `uv run pytest tests/unit/test_pipeline_cancellation.py -k scheduling -v *> C:\Temp\zorivest\pytest-pw7-svc-green.txt; Get-Content C:\Temp\zorivest\pytest-pw7-svc-green.txt \| Select-Object -Last 20` | `[x]` |
| 9 | Implement `POST /runs/{run_id}/cancel` endpoint with UUID validation | coder | Modified `scheduling.py` routes | `uv run pytest tests/unit/test_pipeline_cancellation.py -k endpoint -v *> C:\Temp\zorivest\pytest-pw7-api-green.txt; Get-Content C:\Temp\zorivest\pytest-pw7-api-green.txt \| Select-Object -Last 20` | `[x]` |
| 10 | Update existing `test_pipeline_enums.py` for new CANCELLING member | coder | Modified enum tests | `uv run pytest tests/unit/test_pipeline_enums.py -v *> C:\Temp\zorivest\pytest-enums.txt; Get-Content C:\Temp\zorivest\pytest-enums.txt \| Select-Object -Last 20` | `[x]` |
| 11 | Run full regression + type check + lint | tester | All pass | `uv run pytest tests/ -v *> C:\Temp\zorivest\pytest-full.txt; Get-Content C:\Temp\zorivest\pytest-full.txt \| Select-Object -Last 40`; `uv run pyright packages/ *> C:\Temp\zorivest\pyright.txt; Get-Content C:\Temp\zorivest\pyright.txt \| Select-Object -Last 30`; `uv run ruff check packages/ *> C:\Temp\zorivest\ruff.txt; Get-Content C:\Temp\zorivest\ruff.txt \| Select-Object -Last 20` | `[x]` |
| 12 | Check + regenerate OpenAPI spec (G8 compliance) | coder | `openapi.committed.json` updated | `uv run python tools/export_openapi.py --check openapi.committed.json *> C:\Temp\zorivest\openapi-check.txt; Get-Content C:\Temp\zorivest\openapi-check.txt`; `uv run python tools/export_openapi.py -o openapi.committed.json *> C:\Temp\zorivest\openapi-regen.txt; Get-Content C:\Temp\zorivest\openapi-regen.txt` | `[x]` |
| 13 | Audit `docs/BUILD_PLAN.md` for stale refs | orchestrator | MEU-PW6/PW7 not in BUILD_PLAN — refs in meu-registry only | N/A — refs exist only in meu-registry.md (updated ✅) | `[x]` |
| 14 | Run MEU gate | tester | All checks pass | `uv run python tools/validate_codebase.py --scope meu *> C:\Temp\zorivest\validate.txt; Get-Content C:\Temp\zorivest\validate.txt \| Select-Object -Last 50` | `[x]` |
| 15 | Save session state to pomera_notes | orchestrator | `Memory/Session/Zorivest-url-builders-cancellation-2026-04-19` | MCP: `pomera_notes(action="search", search_term="Zorivest-url-builders*")` returns ≥1 result | `[x]` |
| 16 | Create handoff for MEU-PW6 + MEU-PW7 | reviewer | `.agent/context/handoffs/119-2026-04-19-url-builders-cancellation-bp09bs9B.4-5.md` | `Test-Path .agent/context/handoffs/119-2026-04-19-url-builders-cancellation-bp09bs9B.4-5.md` | `[x]` |
| 17 | Create reflection | orchestrator | `docs/execution/reflections/2026-04-19-url-builders-cancellation-reflection.md` | `Test-Path docs/execution/reflections/2026-04-19-url-builders-cancellation-reflection.md` | `[x]` |
| 18 | Append metrics row | orchestrator | Row appended to `docs/execution/metrics.md` | `Get-Content docs/execution/metrics.md \| Select-Object -Last 3` | `[x]` |

### Status Legend

| Symbol | Meaning |
|--------|--------|
| `[ ]` | Not started |
| `[/]` | In progress |
| `[x]` | Complete |
| `[B]` | Blocked (must link follow-up) |
