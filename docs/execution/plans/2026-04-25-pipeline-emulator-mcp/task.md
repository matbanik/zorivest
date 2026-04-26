---
project: "2026-04-25-pipeline-emulator-mcp"
source: "docs/execution/plans/2026-04-25-pipeline-emulator-mcp/implementation-plan.md"
meus: ["MEU-PH8", "MEU-PH9", "MEU-PH10"]
status: "done"
template_version: "2.1"
---

# Task — Pipeline Emulator + MCP + Default Template

> **Project:** `2026-04-25-pipeline-emulator-mcp`
> **Type:** Domain + API + MCP
> **Estimate:** ~16 files changed/created

## Task Table

| # | Task | Owner | Deliverable | Validation | Status |
|---|------|-------|-------------|------------|--------|
| | **MEU-PH8: Policy Emulator** | | | | |
| 1 | Write FIC for PH8 — acceptance criteria from plan AC-1..AC-15 | orchestrator | FIC inline in session notes | `rg "AC-1\|AC-2\|AC-3\|AC-4\|AC-5\|AC-6\|AC-7\|AC-8\|AC-9\|AC-10\|AC-11\|AC-12\|AC-13\|AC-14\|AC-15" docs/execution/plans/2026-04-25-pipeline-emulator-mcp/implementation-plan.md *> C:\Temp\zorivest\fic-ph8-check.txt; Get-Content C:\Temp\zorivest\fic-ph8-check.txt \| Select-Object -Last 20` | `[x]` |
| 2 | Write `test_emulator_budget.py` — 4 budget tests (RED) | tester | `tests/unit/test_emulator_budget.py` | `uv run pytest tests/unit/test_emulator_budget.py -x --tb=short -v *> C:\Temp\zorivest\pytest-budget-red.txt; Get-Content C:\Temp\zorivest\pytest-budget-red.txt \| Select-Object -Last 20` → all FAIL | `[x]` |
| 3 | Write `test_policy_emulator.py` — 11 emulator tests (RED) | tester | `tests/unit/test_policy_emulator.py` | `uv run pytest tests/unit/test_policy_emulator.py -x --tb=short -v *> C:\Temp\zorivest\pytest-emu-red.txt; Get-Content C:\Temp\zorivest\pytest-emu-red.txt \| Select-Object -Last 20` → all FAIL | `[x]` |
| 4 | Write `emulator_models.py` — `EmulatorError` + `EmulatorResult` Pydantic models (GREEN support) | coder | `packages/core/src/zorivest_core/domain/emulator_models.py` | `uv run pyright packages/core/src/zorivest_core/domain/emulator_models.py *> C:\Temp\zorivest\pyright-models.txt; Get-Content C:\Temp\zorivest\pyright-models.txt \| Select-Object -Last 10` | `[x]` |
| 5 | Write `emulator_budget.py` — `SessionBudget` (GREEN for task 2) | coder | `packages/core/src/zorivest_core/services/emulator_budget.py` | `uv run pytest tests/unit/test_emulator_budget.py -x --tb=short -v *> C:\Temp\zorivest\pytest-budget-green.txt; Get-Content C:\Temp\zorivest\pytest-budget-green.txt \| Select-Object -Last 20` → 4 passed | `[x]` |
| 6 | Write `policy_emulator.py` — 4-phase engine (GREEN for task 3) | coder | `packages/core/src/zorivest_core/services/policy_emulator.py` | `uv run pytest tests/unit/test_policy_emulator.py -x --tb=short -v *> C:\Temp\zorivest\pytest-emu-green.txt; Get-Content C:\Temp\zorivest\pytest-emu-green.txt \| Select-Object -Last 20` → 11 passed | `[x]` |
| 7 | PH8 quality checks — pyright + ruff | tester | 0 errors | `uv run pyright packages/core/ *> C:\Temp\zorivest\pyright-ph8.txt; Get-Content C:\Temp\zorivest\pyright-ph8.txt \| Select-Object -Last 15` then `uv run ruff check packages/core/ *> C:\Temp\zorivest\ruff-ph8.txt; Get-Content C:\Temp\zorivest\ruff-ph8.txt \| Select-Object -Last 10` | `[x]` |
| | **MEU-PH9: REST Endpoints + MCP Tools** | | | | |
| 8 | Write FIC for PH9 — acceptance criteria AC-16..AC-33m | orchestrator | FIC inline in session notes | `rg "AC-16\|AC-17\|AC-18\|AC-19\|AC-20\|AC-21\|AC-22\|AC-23\|AC-24\|AC-25\|AC-26\|AC-27\|AC-28\|AC-29\|AC-30m\|AC-31m\|AC-32m\|AC-33m" docs/execution/plans/2026-04-25-pipeline-emulator-mcp/implementation-plan.md *> C:\Temp\zorivest\fic-ph9-check.txt; Get-Content C:\Temp\zorivest\fic-ph9-check.txt \| Select-Object -Last 25` | `[x]` |
| 9 | Write `template_schemas.py` — Pydantic request/response models | coder | `packages/api/src/zorivest_api/schemas/template_schemas.py` | `uv run pyright packages/api/src/zorivest_api/schemas/template_schemas.py *> C:\Temp\zorivest\pyright-schemas.txt; Get-Content C:\Temp\zorivest\pyright-schemas.txt \| Select-Object -Last 10` | `[x]` |
| 10 | Write `test_emulator_api.py` — REST endpoint tests for emulator + template CRUD + db-schema + validate-sql (RED) | tester | `tests/unit/test_emulator_api.py` | `uv run pytest tests/unit/test_emulator_api.py -x --tb=short -v *> C:\Temp\zorivest\pytest-api-red.txt; Get-Content C:\Temp\zorivest\pytest-api-red.txt \| Select-Object -Last 30` → all FAIL | `[x]` |
| 11 | Write REST endpoints in `scheduling.py` — emulator/run, template CRUD, db-schema, validate-sql, samples, mock-data, preview (GREEN for task 10) | coder | Routes in `packages/api/src/zorivest_api/routes/scheduling.py` | `uv run pytest tests/unit/test_emulator_api.py -x --tb=short -v *> C:\Temp\zorivest\pytest-api-green.txt; Get-Content C:\Temp\zorivest\pytest-api-green.txt \| Select-Object -Last 30` → all pass | `[x]` |
| 12 | Wire `PolicyEmulator` + `SessionBudget` + `EmailTemplateRepository` into FastAPI lifespan | coder | Dependencies wired in `app.state` | `uv run pyright packages/api/ *> C:\Temp\zorivest\pyright-api.txt; Get-Content C:\Temp\zorivest\pyright-api.txt \| Select-Object -Last 15` | `[x]` |
| 13 | Regenerate OpenAPI spec | coder | `openapi.committed.json` updated | `uv run python tools/export_openapi.py --check openapi.committed.json *> C:\Temp\zorivest\openapi-check.txt; Get-Content C:\Temp\zorivest\openapi-check.txt` | `[x]` |
| 14 | Write `test_mcp_pipeline_security.py` — MCP protocol tests for 12 tools + 6 resources (RED) | tester | `tests/unit/test_mcp_pipeline_security.py` (6 proxy tests) + `mcp-server/tests/pipeline-security-tools.test.ts` (30 behavior tests) | `uv run pytest tests/unit/test_mcp_pipeline_security.py -x --tb=short -v` → 6 passed; `npx vitest run tests/pipeline-security-tools.test.ts` → 30 passed | `[x]` |
| 15 | Write `pipeline-security-tools.ts` — 12 MCP tools + 6 MCP resources (GREEN for task 14) | coder | `mcp-server/src/tools/pipeline-security-tools.ts` | `Set-Location p:\zorivest\mcp-server; npm run build *> C:\Temp\zorivest\mcp-build.txt; Get-Content C:\Temp\zorivest\mcp-build.txt \| Select-Object -Last 20` → success | `[x]` |
| 16 | Register pipeline security tools in `index.ts` | coder | Import + registration call added | `Set-Location p:\zorivest\mcp-server; npm run build *> C:\Temp\zorivest\mcp-build2.txt; Get-Content C:\Temp\zorivest\mcp-build2.txt \| Select-Object -Last 20` → success | `[x]` |
| 17 | Verify M7 workflow context in all tool descriptions | reviewer | All 12 tools have prerequisite/return shape info | `rg "prerequisite\|workflow\|return.*shape\|Returns\|Requires" mcp-server/src/tools/pipeline-security-tools.ts *> C:\Temp\zorivest\m7-check.txt; Get-Content C:\Temp\zorivest\m7-check.txt \| Select-Object -Last 30` | `[x]` |
| 18 | PH9 quality checks — pyright + ruff (Python) + MCP build (TypeScript) | tester | 0 errors | `uv run pyright packages/ *> C:\Temp\zorivest\pyright-ph9.txt; Get-Content C:\Temp\zorivest\pyright-ph9.txt \| Select-Object -Last 15` then `uv run ruff check packages/ *> C:\Temp\zorivest\ruff-ph9.txt; Get-Content C:\Temp\zorivest\ruff-ph9.txt \| Select-Object -Last 10` then `Set-Location p:\zorivest\mcp-server; npm run build *> C:\Temp\zorivest\mcp-build-ph9.txt; Get-Content C:\Temp\zorivest\mcp-build-ph9.txt \| Select-Object -Last 15` | `[x]` |
| | **MEU-PH10: Default Template Seed** | | | | |
| 19 | Write `test_default_template.py` — 2 template tests (RED) | tester | `tests/unit/test_default_template.py` | `uv run pytest tests/unit/test_default_template.py -x --tb=short -v *> C:\Temp\zorivest\pytest-tpl-red.txt; Get-Content C:\Temp\zorivest\pytest-tpl-red.txt \| Select-Object -Last 15` → FAIL | `[x]` |
| 20 | Write Alembic migration to seed `morning-check-in` template (GREEN for task 19) | coder | `alembic/versions/xxxx_seed_morning_checkin.py` | `uv run pytest tests/unit/test_default_template.py -x --tb=short -v *> C:\Temp\zorivest\pytest-tpl-green.txt; Get-Content C:\Temp\zorivest\pytest-tpl-green.txt \| Select-Object -Last 15` → 2 passed | `[x]` |
| | **Post-MEU Deliverables** | | | | |
| 21 | Update `docs/BUILD_PLAN.md` — PH8/PH9/PH10 → ✅, P2.5c count 7→10 | orchestrator | Status column updated | `rg "⬜" docs/BUILD_PLAN.md *> C:\Temp\zorivest\bp-check.txt; Get-Content C:\Temp\zorivest\bp-check.txt` → no PH8/PH9/PH10 | `[x]` |
| 22 | Update `.agent/context/meu-registry.md` — PH8/PH9/PH10 → done | orchestrator | Registry rows updated | `rg "MEU-PH8\|MEU-PH9\|MEU-PH10" .agent/context/meu-registry.md *> C:\Temp\zorivest\registry-check.txt; Get-Content C:\Temp\zorivest\registry-check.txt` | `[x]` |
| 23 | Update `.agent/context/current-focus.md` | orchestrator | Reflects P2.5c complete | `Get-Content .agent/context/current-focus.md` | `[x]` |
| 24 | Run MEU gate | tester | All checks pass | `uv run python tools/validate_codebase.py --scope meu *> C:\Temp\zorivest\validate.txt; Get-Content C:\Temp\zorivest\validate.txt \| Select-Object -Last 50` | `[x]` |
| 25 | Run full regression | tester | All tests pass | `uv run pytest tests/ -x --tb=short -v *> C:\Temp\zorivest\pytest-full.txt; Get-Content C:\Temp\zorivest\pytest-full.txt \| Select-Object -Last 40` | `[x]` |
| 26 | Anti-placeholder scan | tester | No residual TODOs | `rg "TODO\|FIXME\|NotImplementedError" packages/ *> C:\Temp\zorivest\placeholders.txt; Get-Content C:\Temp\zorivest\placeholders.txt \| Select-Object -Last 20` | `[x]` |
| 27 | Audit `docs/BUILD_PLAN.md` for stale refs | orchestrator | No stale refs | `rg "pipeline-emulator-mcp" docs/BUILD_PLAN.md *> C:\Temp\zorivest\stale-check.txt; Get-Content C:\Temp\zorivest\stale-check.txt` → 0 matches | `[x]` |
| 28 | Create handoff | reviewer | `.agent/context/handoffs/2026-04-25-pipeline-emulator-mcp-ph8-ph10-handoff.md` | `Test-Path .agent/context/handoffs/2026-04-25-pipeline-emulator-mcp-ph8-ph10-handoff.md` | `[x]` |
| 29 | Create reflection | orchestrator | `docs/execution/reflections/2026-04-25-pipeline-emulator-mcp-reflection.md` | `Test-Path docs/execution/reflections/2026-04-25-pipeline-emulator-mcp-reflection.md` | `[x]` |
| 30 | Append metrics row | orchestrator | Row appended to `docs/execution/metrics.md` | `Get-Content docs/execution/metrics.md \| Select-Object -Last 3` | `[x]` |

### Status Legend

| Symbol | Meaning |
|--------|---------|
| `[ ]` | Not started |
| `[/]` | In progress |
| `[x]` | Complete |
| `[B]` | Blocked (must link follow-up) |
