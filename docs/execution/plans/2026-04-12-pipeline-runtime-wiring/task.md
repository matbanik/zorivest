---
project: "2026-04-12-pipeline-runtime-wiring"
source: "docs/execution/plans/2026-04-12-pipeline-runtime-wiring/implementation-plan.md"
meus: ["MEU-PW1"]
status: "in_progress"
template_version: "2.0"
---

# Task — Pipeline Runtime Wiring

> **Project:** `2026-04-12-pipeline-runtime-wiring`
> **Type:** Infrastructure/API
> **Estimate:** 10 files (7 modified/new production + 4 new test + stubs cleanup)

## Task Table

| # | Task | Owner | Deliverable | Validation | Status |
|---|------|-------|-------------|------------|--------|
| 1 | Write unit tests for PipelineRunner constructor expansion (AC-1, AC-2) | coder | `tests/unit/test_pipeline_runner_constructor.py` | `uv run pytest tests/unit/test_pipeline_runner_constructor.py -x --tb=short -v *> C:\Temp\zorivest\pytest-pw1-ctor.txt; Get-Content C:\Temp\zorivest\pytest-pw1-ctor.txt \| Select-Object -Last 30` | `[x]` |
| 2 | Expand PipelineRunner `__init__` with 6 new kwargs + `initial_outputs` | coder | Modified `pipeline_runner.py` | `uv run pytest tests/unit/test_pipeline_runner_constructor.py -x --tb=short -v *> C:\Temp\zorivest\pytest-pw1-ctor.txt; Get-Content C:\Temp\zorivest\pytest-pw1-ctor.txt \| Select-Object -Last 30` | `[x]` |
| 3 | Write unit tests for `get_smtp_runtime_config()` (AC-3) | coder | `tests/unit/test_smtp_runtime_config.py` | `uv run pytest tests/unit/test_smtp_runtime_config.py -x --tb=short -v *> C:\Temp\zorivest\pytest-pw1-smtp.txt; Get-Content C:\Temp\zorivest\pytest-pw1-smtp.txt \| Select-Object -Last 30` | `[x]` |
| 4 | Add `get_smtp_runtime_config()` to EmailProviderService | coder | Modified `email_provider_service.py` | `uv run pytest tests/unit/test_smtp_runtime_config.py -x --tb=short -v *> C:\Temp\zorivest\pytest-pw1-smtp.txt; Get-Content C:\Temp\zorivest\pytest-pw1-smtp.txt \| Select-Object -Last 30` | `[x]` |
| 5 | Write unit tests for DbWriteAdapter (AC-4) | coder | `tests/unit/test_db_write_adapter.py` | `uv run pytest tests/unit/test_db_write_adapter.py -x --tb=short -v *> C:\Temp\zorivest\pytest-pw1-dbw.txt; Get-Content C:\Temp\zorivest\pytest-pw1-dbw.txt \| Select-Object -Last 30` | `[x]` |
| 6 | Create DbWriteAdapter | coder | `packages/infrastructure/src/zorivest_infra/adapters/db_write_adapter.py` | `uv run pytest tests/unit/test_db_write_adapter.py -x --tb=short -v *> C:\Temp\zorivest\pytest-pw1-dbw.txt; Get-Content C:\Temp\zorivest\pytest-pw1-dbw.txt \| Select-Object -Last 30` | `[x]` |
| 7 | Wire 7 runtime kwargs into PipelineRunner in main.py (`provider_adapter` remains `None` until PW2) | coder | Modified `main.py` L241 block | `uv run python tools/export_openapi.py --check openapi.committed.json *> C:\Temp\zorivest\openapi-pw1.txt; Get-Content C:\Temp\zorivest\openapi-pw1.txt` | `[x]` |
| 8 | Delete dead stubs + update test (AC-5) | coder | Modified `stubs.py`, `test_provider_service_wiring.py` | `rg "StubMarketDataService\|StubProviderConnectionService" packages/ tests/` → 0 matches | `[x]` |
| 9 | Write integration test (AC-6) | coder | `tests/integration/test_pipeline_wiring.py` | `uv run pytest tests/integration/test_pipeline_wiring.py -x --tb=short -v *> C:\Temp\zorivest\pytest-pw1-integ.txt; Get-Content C:\Temp\zorivest\pytest-pw1-integ.txt \| Select-Object -Last 30` | `[x]` |
| 10 | Run full test suite (AC-7) | tester | All existing tests pass | `uv run pytest tests/ -x --tb=short -v *> C:\Temp\zorivest\pytest-pw1-full.txt; Get-Content C:\Temp\zorivest\pytest-pw1-full.txt \| Select-Object -Last 40` | `[x]` |
| 11 | Run MEU gate | tester | pyright + ruff + pytest + anti-placeholder clean | `uv run python tools/validate_codebase.py --scope meu *> C:\Temp\zorivest\validate-pw1.txt; Get-Content C:\Temp\zorivest\validate-pw1.txt \| Select-Object -Last 50` | `[x]` |
| 12 | Check OpenAPI spec drift | tester | No drift detected | `uv run python tools/export_openapi.py --check openapi.committed.json *> C:\Temp\zorivest\openapi-pw1-drift.txt; Get-Content C:\Temp\zorivest\openapi-pw1-drift.txt` | `[x]` |
| 13 | Audit `docs/BUILD_PLAN.md` — correct PW1 description + update status | orchestrator | Description matches refined scope; status `⬜` → `✅` | `rg "MEU-PW1" docs/BUILD_PLAN.md *> C:\Temp\zorivest\buildplan-pw1.txt; Get-Content C:\Temp\zorivest\buildplan-pw1.txt` | `[x]` |
| 14 | Update `.agent/context/meu-registry.md` | orchestrator | MEU-PW1 status → `✅ 2026-04-12` | `rg "MEU-PW1" .agent/context/meu-registry.md *> C:\Temp\zorivest\registry-pw1.txt; Get-Content C:\Temp\zorivest\registry-pw1.txt` | `[x]` |
| 15 | Update `.agent/context/known-issues.md` — resolve `[SCHED-PIPELINE-WIRING]` partial + `[STUB-RETIRE]` partial | orchestrator | Issues updated with PW1 resolution | `rg "SCHED-PIPELINE-WIRING\|STUB-RETIRE" .agent/context/known-issues.md *> C:\Temp\zorivest\ki-pw1.txt; Get-Content C:\Temp\zorivest\ki-pw1.txt` | `[x]` |
| 16 | Save session state to pomera_notes | orchestrator | `Memory/Session/Zorivest-pipeline-runtime-wiring-2026-04-12` | MCP: `pomera_notes(action="search", search_term="Zorivest-pipeline*")` returns ≥1 result | `[x]` |
| 17 | Create handoff | reviewer | `.agent/context/handoffs/113-2026-04-12-pipeline-runtime-wiring-bp09s49.4.md` | `Test-Path .agent/context/handoffs/113-2026-04-12-pipeline-runtime-wiring-bp09s49.4.md` | `[x]` |
| 18 | Create reflection | orchestrator | `docs/execution/reflections/2026-04-12-pipeline-runtime-wiring-reflection.md` | `Test-Path docs/execution/reflections/2026-04-12-pipeline-runtime-wiring-reflection.md` | `[x]` |
| 19 | Append metrics row | orchestrator | Row appended to `docs/execution/metrics.md` | `Get-Content docs/execution/metrics.md \\| Select-Object -Last 3` | `[x]` |

### Status Legend

| Symbol | Meaning |
|--------|---------|
| `[ ]` | Not started |
| `[/]` | In progress |
| `[x]` | Complete |
| `[B]` | Blocked (must link follow-up) |
