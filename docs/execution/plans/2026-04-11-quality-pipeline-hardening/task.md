---
project: "2026-04-11-quality-pipeline-hardening"
source: "docs/execution/plans/2026-04-11-quality-pipeline-hardening/implementation-plan.md"
meus: ["CI-FIX-1", "CI-FIX-2", "MEU-TS2", "MEU-TS4"]
status: "complete"
template_version: "2.0"
---

# Task — Quality Pipeline Hardening

> **Project:** `2026-04-11-quality-pipeline-hardening`
> **Type:** Infrastructure/Test
> **Estimate:** 7 files changed

## Task Table

| # | Task | Owner | Deliverable | Validation | Status |
|---|------|-------|-------------|------------|--------|
| 1 | CI-FIX-2: Add `useArchiveAccount` + `useArchivedAccounts` mocks to `AccountDetailPanel.test.tsx` | coder | 2 mock hooks added | `npx vitest run *> C:\Temp\zorivest\vitest.txt; Get-Content C:\Temp\zorivest\vitest.txt \| Select-Object -Last 10` | `[x]` |
| 2 | CI-FIX-2: Add same 2 mocks to `AccountsHome.test.tsx` | coder | 2 mock hooks added | `npx vitest run *> C:\Temp\zorivest\vitest.txt; Get-Content C:\Temp\zorivest\vitest.txt \| Select-Object -Last 10` | `[x]` |
| 3 | CI-FIX-2: Verify vitest | tester | 23 files, 307 tests pass | `npx vitest run` — 307 passed | `[x]` |
| 4 | CI-FIX-1: Run `tools/export_openapi.py -o openapi.committed.json` | coder | Regenerated spec file | `uv run python tools/export_openapi.py --check openapi.committed.json` — exits 0 | `[x]` |
| 5 | CI-FIX-1: Copy to `packages/api/src/zorivest_api/` | coder | Both copies in sync | `Get-FileHash openapi.committed.json, packages/api/src/zorivest_api/openapi.committed.json *> C:\Temp\zorivest\hash-cmp.txt; Get-Content C:\Temp\zorivest\hash-cmp.txt` | `[x]` |
| 6 | CI-FIX-1: Verify `--check` mode | tester | "OpenAPI spec matches committed snapshot." | `uv run python tools/export_openapi.py --check openapi.committed.json` | `[x]` |
| 7 | MEU-TS4: Add `@patch.object` to `TestGetQuote` (5 methods) | coder | Class-level decorator patching `_yahoo_quote` | `uv run pytest tests/unit/test_market_data_service.py -x --tb=short -v` — 13 passed | `[x]` |
| 8 | MEU-TS4: Add `@patch.object` to `TestRateLimiting` | coder | Class-level decorator patching `_yahoo_quote` | `uv run pytest tests/unit/test_market_data_service.py -x --tb=short -v *> C:\Temp\zorivest\pytest-mds.txt; Get-Content C:\Temp\zorivest\pytest-mds.txt \| Select-Object -Last 10` | `[x]` |
| 9 | MEU-TS4: Verify all 13 MDS tests pass | tester | 13 passed, 0 failed | `uv run pytest tests/unit/test_market_data_service.py` | `[x]` |
| 10 | MEU-TS2: Identify actual Tier 2 errors | researcher | Error list by file | `uv run pyright tests/ *> C:\Temp\zorivest\pyright-t2-scan.txt; (Select-String -Path C:\Temp\zorivest\pyright-t2-scan.txt -Pattern "reportArgumentType").Count` — expect 0 | `[x]` |
| 11 | MEU-TS2: Fix `test_repo_contracts.py` — import enums, replace 3 constructor args + 1 `replace()` | coder | 0 Tier 2 errors in file | `Select-String -Path C:\Temp\zorivest\pyright-t2-scan.txt -Pattern "test_repo_contracts.*reportArgumentType"` — expect 0 matches | `[x]` |
| 12 | MEU-TS2: Fix `test_repositories.py` — import enums, replace 15 constructor args + 1 `replace()` | coder | 0 Tier 2 errors in file | `Select-String -Path C:\Temp\zorivest\pyright-t2-scan.txt -Pattern "test_repositories.*reportArgumentType"` — expect 0 matches | `[x]` |
| 13 | MEU-TS2: Fix `test_report_service.py` — import enums, replace 21 constructor args | coder | 0 Tier 2 errors in file | `Select-String -Path C:\Temp\zorivest\pyright-t2-scan.txt -Pattern "test_report_service.*reportArgumentType"` — expect 0 matches | `[x]` |
| 14 | MEU-TS2: Verify pyright error count reduction | tester | 241 → 205 (36 Tier 2 eliminated) | `Get-Content C:\Temp\zorivest\pyright-t2-scan.txt \| Select-Object -Last 3` — expect "205 errors" | `[x]` |
| 15 | MEU-TS2: Verify 87 affected tests pass | tester | 87 passed, 0 failed | `uv run pytest tests/unit/test_report_service.py tests/integration/test_repo_contracts.py tests/integration/test_repositories.py -x --tb=short -v *> C:\Temp\zorivest\pytest-t2.txt; Get-Content C:\Temp\zorivest\pytest-t2.txt \| Select-Object -Last 5` | `[x]` |
| 16 | Run MEU validation gate | tester | All 8 blocking checks pass | `uv run python tools/validate_codebase.py --scope meu` | `[x]` |
| 17 | Audit `docs/BUILD_PLAN.md` for stale refs | orchestrator | No changes expected — project is test infra, not build-plan tracked | `rg "quality-pipeline-hardening" docs/BUILD_PLAN.md` (expect 0 matches) | `[x]` |
| 18 | Save session state to pomera_notes | orchestrator | `Memory/Session/Zorivest-quality-pipeline-hardening-2026-04-11` | MCP: `pomera_notes(action="search", search_term="Zorivest-quality*")` returns ≥1 result | `[x]` |
| 19 | Create handoff | reviewer | `.agent/context/handoffs/{SEQ}-2026-04-11-quality-pipeline-hardening-ci.md` | `Test-Path .agent/context/handoffs/{filename}` | `[x]` |
| 20 | Create reflection | orchestrator | `docs/execution/reflections/2026-04-11-quality-pipeline-hardening-reflection.md` | `Test-Path docs/execution/reflections/{filename}` | `[x]` |
| 21 | Append metrics row | orchestrator | Row appended to `docs/execution/metrics.md` | `Get-Content docs/execution/metrics.md \| Select-Object -Last 3` | `[x]` |

### Status Legend

| Symbol | Meaning |
|--------|---------|
| `[ ]` | Not started |
| `[/]` | In progress |
| `[x]` | Complete |
| `[B]` | Blocked (must link follow-up) |
