---
project: "2026-05-05-api-surface-pipeline-automation"
source: "docs/execution/plans/2026-05-05-api-surface-pipeline-automation/implementation-plan.md"
meus: ["MEU-192", "MEU-193", "MEU-194", "MEU-207"]
status: "complete"
template_version: "2.0"
---

# Task — Phase 8a Layer 5–6: API Surface + Pipeline Automation + Capability Wiring

> **Project:** `2026-05-05-api-surface-pipeline-automation`
> **Type:** API + MCP + Infrastructure
> **Estimate:** ~12 files changed/created

## Task Table

| # | Task | Owner | Deliverable | Validation | Status |
|---|------|-------|-------------|------------|--------|
| **MEU-192 — Routes + MCP** | | | | |
| 1 | Write FIC for 8 REST endpoints + 8 MCP actions | orchestrator | FIC with AC-1..AC-9 in plan | `(Get-Content docs/execution/plans/2026-05-05-api-surface-pipeline-automation/implementation-plan.md)[46..58] \| Select-String 'AC-' \| Measure-Object \| Select-Object -ExpandProperty Count *> C:\Temp\zorivest\fic-192.txt; Get-Content C:\Temp\zorivest\fic-192.txt` → ≥ 9 | `[x]` |
| 2 | Write tests for 8 new route endpoints (RED) | coder | `tests/unit/test_market_routes.py` extended | `uv run pytest tests/unit/test_market_routes.py -x --tb=short *> C:\Temp\zorivest\pytest-routes.txt; Get-Content C:\Temp\zorivest\pytest-routes.txt \| Select-Object -Last 40` → all FAIL | `[x]` |
| 3 | Write tests for 8 new MCP actions (RED) | coder | `mcp-server/tests/compound/market-tool.test.ts` extended | `npx vitest run mcp-server/tests/compound/market-tool.test.ts *> C:\Temp\zorivest\vitest-mcp.txt; Get-Content C:\Temp\zorivest\vitest-mcp.txt \| Select-Object -Last 40` → FAIL | `[x]` |
| 4 | Create `MarketDataExpansionParams` Pydantic model + implement 8 route handlers (GREEN) | coder | `market_data.py` extended + 8 `@market_data_router.get(...)` handlers | `uv run pytest tests/unit/test_market_routes.py -x --tb=short *> C:\Temp\zorivest\pytest-routes.txt; Get-Content C:\Temp\zorivest\pytest-routes.txt \| Select-Object -Last 40` → all PASS | `[x]` |
| 5 | Add 8 new actions to `market-tool.ts` + update Zod schema + description (GREEN) | coder | `mcp-server/src/compound/market-tool.ts` extended | `npx vitest run *> C:\Temp\zorivest\vitest.txt; Get-Content C:\Temp\zorivest\vitest.txt \| Select-Object -Last 40` → PASS; `rg -i -e "workflow:" -e "prerequisite:" -e "returns:" -e "errors:" mcp-server/src/compound/market-tool.ts --count *> C:\Temp\zorivest\m7-check.txt; Get-Content C:\Temp\zorivest\m7-check.txt` → ≥ 3 | `[x]` |
| 6 | Rebuild MCP server | coder | `mcp-server/dist/` updated | `cd mcp-server; npm run build *> C:\Temp\zorivest\mcp-build.txt; Get-Content C:\Temp\zorivest\mcp-build.txt \| Select-Object -Last 10` exits 0 | `[x]` |
| 7 | Check OpenAPI drift + regenerate if needed (G8) | coder | `openapi.committed.json` verified or regenerated | `uv run python tools/export_openapi.py --check openapi.committed.json *> C:\Temp\zorivest\openapi-check.txt; Get-Content C:\Temp\zorivest\openapi-check.txt` → if drift: `uv run python tools/export_openapi.py -o openapi.committed.json *> C:\Temp\zorivest\openapi-regen.txt; Get-Content C:\Temp\zorivest\openapi-regen.txt` | `[x]` |
| **MEU-193 — Store Step** | | | | |
| 8 | Write FIC for MarketDataStoreStep | orchestrator | FIC with AC-1..AC-8 in plan | `(Get-Content docs/execution/plans/2026-05-05-api-surface-pipeline-automation/implementation-plan.md)[93..106] \| Select-String 'AC-' \| Measure-Object \| Select-Object -ExpandProperty Count *> C:\Temp\zorivest\fic-193.txt; Get-Content C:\Temp\zorivest\fic-193.txt` → ≥ 8 | `[x]` |
| 9 | Write tests for MarketDataStoreStep (RED) | coder | `tests/unit/test_market_data_store_step.py` | `uv run pytest tests/unit/test_market_data_store_step.py -x --tb=short *> C:\Temp\zorivest\pytest-store.txt; Get-Content C:\Temp\zorivest\pytest-store.txt \| Select-Object -Last 40` → all FAIL | `[x]` |
| 10 | Create per-data-type Pydantic validators for all 6 supported data types + implement MarketDataStoreStep + reuse DbWriteAdapter + register in step registry (GREEN) | coder | `market_data_store_step.py` + registry entry + validators for ohlcv, earnings, dividends, splits, insider, fundamentals | `uv run pytest tests/unit/test_market_data_store_step.py -x --tb=short *> C:\Temp\zorivest\pytest-store.txt; Get-Content C:\Temp\zorivest\pytest-store.txt \| Select-Object -Last 40` → all PASS | `[x]` |
| **MEU-194 — Scheduling Recipes** | | | | |
| 11 | Write FIC for 10 scheduling recipes | orchestrator | FIC with AC-1..AC-6 in plan | `(Get-Content docs/execution/plans/2026-05-05-api-surface-pipeline-automation/implementation-plan.md)[138..148] \| Select-String 'AC-' \| Measure-Object \| Select-Object -ExpandProperty Count *> C:\Temp\zorivest\fic-194.txt; Get-Content C:\Temp\zorivest\fic-194.txt` → ≥ 6 | `[x]` |
| 12 | Write tests for recipe seed script (RED) | coder | `tests/unit/test_scheduling_recipes.py` | `uv run pytest tests/unit/test_scheduling_recipes.py -x --tb=short *> C:\Temp\zorivest\pytest-recipes.txt; Get-Content C:\Temp\zorivest\pytest-recipes.txt \| Select-Object -Last 40` → all FAIL | `[x]` |
| 13 | Create `tools/seed_scheduling_recipes.py` with 10 recipe definitions (GREEN) | coder | 10 PolicyDocument definitions + idempotent seed | `uv run pytest tests/unit/test_scheduling_recipes.py -x --tb=short *> C:\Temp\zorivest\pytest-recipes.txt; Get-Content C:\Temp\zorivest\pytest-recipes.txt \| Select-Object -Last 40` → all PASS | `[x]` |
| **MEU-207 — Capability Wiring** | | | | |
| 14 | Write FIC for normalizer injection + capability enrichment | orchestrator | FIC with AC-1..AC-4 + Expected Capability Tuples table in plan | `(Get-Content docs/execution/plans/2026-05-05-api-surface-pipeline-automation/implementation-plan.md \| Select-Object -Index (186..210)) \| Select-String 'AC-' \| Measure-Object \| Select-Object -ExpandProperty Count *> C:\Temp\zorivest\fic-207.txt; Get-Content C:\Temp\zorivest\fic-207.txt` → 4 (AC-1..AC-4) | `[x]` |
| 15 | Write tests for capability wiring (RED) | coder | `tests/unit/test_capability_wiring.py` | `uv run pytest tests/unit/test_capability_wiring.py -x --tb=short *> C:\Temp\zorivest\pytest-wiring.txt; Get-Content C:\Temp\zorivest\pytest-wiring.txt \| Select-Object -Last 40` → all FAIL | `[x]` |
| 16 | Inject `normalizers=NORMALIZERS` in `main.py` + update `supported_data_types` in `provider_capabilities.py` (GREEN) | coder | 2 files modified | `uv run pytest tests/unit/test_capability_wiring.py -x --tb=short *> C:\Temp\zorivest\pytest-wiring.txt; Get-Content C:\Temp\zorivest\pytest-wiring.txt \| Select-Object -Last 40` → all PASS | `[x]` |
| 17 | Verify full test suite passes including wiring tests | tester | All unit tests green | `uv run pytest tests/unit/ -x --tb=short *> C:\Temp\zorivest\pytest-full.txt; Get-Content C:\Temp\zorivest\pytest-full.txt \| Select-Object -Last 40` → all PASS | `[x]` |
| **Post-MEU Deliverables** | | | | |
| 18 | Audit `docs/BUILD_PLAN.md` — add MEU-207 row with `30.15`, update count to `16/16` | orchestrator | BUILD_PLAN.md + build-priority-matrix.md updated | `rg "MEU-207" docs/BUILD_PLAN.md *> C:\Temp\zorivest\buildplan-check.txt; Get-Content C:\Temp\zorivest\buildplan-check.txt` → row with `30.15` | `[x]` |
| 19 | Run MEU gate | tester | All checks pass | `uv run python tools/validate_codebase.py --scope meu *> C:\Temp\zorivest\validate.txt; Get-Content C:\Temp\zorivest\validate.txt \| Select-Object -Last 50` | `[x]` |
| 20 | Update `meu-registry.md` — mark MEU-207 as ✅ | orchestrator | 1 row updated | `rg "MEU-207" .agent/context/meu-registry.md *> C:\Temp\zorivest\registry-check.txt; Get-Content C:\Temp\zorivest\registry-check.txt` → row with ✅ | `[x]` |
| 21 | Save session state to pomera_notes | orchestrator | `Memory/Session/Zorivest-capability-wiring-2026-05-05` | `pomera_notes(action="search", search_term="Zorivest-capability-wiring*")` → ≥ 1 result | `[x]` |
| 22 | Create handoff | reviewer | `.agent/context/handoffs/2026-05-05-api-surface-pipeline-automation-handoff.md` | `Test-Path .agent/context/handoffs/2026-05-05-api-surface-pipeline-automation-handoff.md *> C:\Temp\zorivest\handoff-check.txt; Get-Content C:\Temp\zorivest\handoff-check.txt` → True | `[x]` |
| 23 | Create reflection | orchestrator | `docs/execution/reflections/2026-05-05-api-surface-pipeline-automation-reflection.md` | `Test-Path docs/execution/reflections/2026-05-05-api-surface-pipeline-automation-reflection.md *> C:\Temp\zorivest\reflect-check.txt; Get-Content C:\Temp\zorivest\reflect-check.txt` → True | `[x]` |
| 24 | Append metrics row | orchestrator | Row in `docs/execution/metrics.md` | `Get-Content docs/execution/metrics.md \| Select-Object -Last 3 *> C:\Temp\zorivest\metrics-check.txt; Get-Content C:\Temp\zorivest\metrics-check.txt` → row with `capability-wiring` | `[x]` |
| **Ad-Hoc Pipeline Hardening (2026-05-05/06)** | | | | |
| 25 | ComposeStep resilience — skip missing upstream outputs (KeyError → graceful skip with warning) | coder | `compose_step.py` try/except + `test_compose_step.py` AC-5.4 | `uv run pytest tests/unit/test_compose_step.py -x --tb=short *> C:\Temp\zorivest\pytest-compose.txt; Get-Content C:\Temp\zorivest\pytest-compose.txt \| Select-Object -Last 10` → PASS | `[x]` |
| 26 | Bytes serialization fix — `_pipeline_safe_dumps()` handles bytes/datetime in Jinja2 `\|tojson` | coder | `secure_jinja.py` L107-129 + `template_engine.py` L42-44 | Pipeline run with bytes payload → no crash | `[x]` |
| 27 | API key name mismatch — `_resolve_headers()` and `_inject_query_param_key()` use registry key instead of display name | coder | `market_data_adapter.py` (4 call sites) | Polygon fetch with "Massive" display name → correct API key lookup | `[x]` |
| 28 | Alpaca connection validator — check `latestTrade`/`latestQuote` (snapshot) instead of `id` (account) | coder | `provider_connection_service.py` L203-213 | Alpaca test_connection → ✅ "Connection successful" | `[x]` |
| 29 | Alpaca test suite update — align tests with snapshot response shape | coder | `test_provider_connection_service.py` TestAlpacaValidation (4 tests) | `uv run pytest tests/unit/test_provider_connection_service.py -x --tb=short *> C:\Temp\zorivest\pytest-alpaca.txt; Get-Content C:\Temp\zorivest\pytest-alpaca.txt \| Select-Object -Last 10` → 45 PASS | `[x]` |
| 30 | Email template v3 — envelope unwrapping for Polygon/FMP/Finnhub, `is defined` guards, error cards | coder | `full-fundamentals-research` template (DB) | Pipeline email renders formatted tables, not raw JSON | `[x]` |

### Status Legend

| Symbol | Meaning |
|--------|---------|
| `[ ]` | Not started |
| `[/]` | In progress |
| `[x]` | Complete |
| `[B]` | Blocked (must link follow-up) |
