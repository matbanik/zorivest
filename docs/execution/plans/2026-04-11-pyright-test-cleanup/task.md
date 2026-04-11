---
project: "2026-04-11-pyright-test-cleanup"
source: "docs/execution/plans/2026-04-11-pyright-test-cleanup/implementation-plan.md"
meus: ["MEU-TS2", "MEU-TS3"]
status: "complete"
template_version: "2.0"
---

# Task — Pyright Test Suite Cleanup

> **Project:** `2026-04-11-pyright-test-cleanup`
> **Type:** Infrastructure/Docs
> **Estimate:** ~14 test files modified, 0 production files

## Task Table

| # | Task | Owner | Deliverable | Validation | Status |
|---|------|-------|-------------|------------|--------|
| 1 | **MEU-TS2**: Verify 0 enum-literal pyright errors remain | tester | Evidence that BV work resolved all enum literal errors | `uv run pyright tests/ *> C:\Temp\zorivest\pyright-ts2-enum.txt; Select-String -Path C:\Temp\zorivest\pyright-ts2-enum.txt -Pattern "string.*enum","Literal.*TradeAction","Literal.*AccountType" \| Measure-Object \| Select-Object -ExpandProperty Count` — expect 0 | `[x]` |
| 2 | **MEU-TS3 Group 1**: Fix 8 entity factory return types in `test_entities.py` | coder | `_make_*` functions return typed entities, not `object` | `uv run pyright tests/unit/test_entities.py *> C:\Temp\zorivest\pyright-entities.txt; Get-Content C:\Temp\zorivest\pyright-entities.txt \| Select-Object -Last 5` — expect ≤ 1 error (is_archived) | `[x]` |
| 3 | **MEU-TS3 Group 2**: Add Optional narrowing guards across 7 files | coder | `assert is not None` before all Optional member access / subscript / operator | `uv run pyright tests/ *> C:\Temp\zorivest\pyright-g2.txt; Select-String -Path C:\Temp\zorivest\pyright-g2.txt -Pattern "reportOptionalMemberAccess","reportOptionalSubscript","reportOperatorIssue" \| Measure-Object \| Select-Object -ExpandProperty Count` — expect 0 | `[x]` |
| 4 | **MEU-TS3 Group 3**: Add SQLAlchemy `type: ignore` suppressions across 8 files | coder | 59 targeted `# type: ignore` comments on ColumnElement/attr-assign lines | `uv run pyright tests/ *> C:\Temp\zorivest\pyright-g3.txt; Select-String -Path C:\Temp\zorivest\pyright-g3.txt -Pattern "ColumnElement","reportAttributeAccessIssue" \| Measure-Object \| Select-Object -ExpandProperty Count` — expect 0 | `[x]` |
| 5 | **MEU-TS3 Group 4**: Fix constructor args + misc errors across 8 files | coder | Missing args added, type casts applied, protocol fix | `uv run pyright tests/ *> C:\Temp\zorivest\pyright-g4.txt; Select-String -Path C:\Temp\zorivest\pyright-g4.txt -Pattern "reportCallIssue","reportReturnType","reportArgumentType" \| Measure-Object \| Select-Object -ExpandProperty Count` — expect 0 | `[x]` |
| 6 | Run full Pyright verification | tester | `uv run pyright tests/` ≤ 7 errors (encryption only) | `uv run pyright tests/ *> C:\Temp\zorivest\pyright-ts3-final.txt; Get-Content C:\Temp\zorivest\pyright-ts3-final.txt \| Select-Object -Last 10` | `[x]` |
| 7 | Run unit test regression | tester | `uv run pytest tests/unit/` 0 failures (integration suite has 1 pre-existing `[TEST-ISOLATION-2]` failure unrelated to pyright changes) | `uv run pytest tests/unit/ -x --tb=short -v *> C:\Temp\zorivest\pytest-ts3.txt; Get-Content C:\Temp\zorivest\pytest-ts3.txt \| Select-Object -Last 40` | `[x]` |
| 8 | Verify production code untouched | tester | `uv run pyright packages/` 0 errors | `uv run pyright packages/ *> C:\Temp\zorivest\pyright-packages.txt; Get-Content C:\Temp\zorivest\pyright-packages.txt \| Select-Object -Last 5` | `[x]` |
| 9 | Run MEU gate | tester | Gate passes | `uv run python tools/validate_codebase.py --scope meu *> C:\Temp\zorivest\validate-ts3.txt; Get-Content C:\Temp\zorivest\validate-ts3.txt \| Select-Object -Last 50` | `[x]` |
| 10 | Audit `docs/BUILD_PLAN.md` — update MEU-TS2 + MEU-TS3 status to ✅ | orchestrator | Both rows show ✅ | `rg "MEU-TS[23]" docs/BUILD_PLAN.md` — expect 2 rows with ✅ | `[x]` |
| 11 | Update `.agent/context/meu-registry.md` | orchestrator | Both MEU rows show ✅ with date | `rg "MEU-TS[23]" .agent/context/meu-registry.md` — expect ✅ dates | `[x]` |
| 12 | Save session state to pomera_notes | orchestrator | `Memory/Session/Zorivest-pyright-test-cleanup-2026-04-11` | MCP: `pomera_notes(action="search", search_term="Zorivest-pyright*")` returns ≥1 result | `[x]` |
| 13 | Create handoff (MEU-TS2) | reviewer | `.agent/context/handoffs/108-2026-04-11-pyright-enum-literals-bpTSsB.md` | `Test-Path .agent/context/handoffs/108-2026-04-11-pyright-enum-literals-bpTSsB.md` | `[x]` |
| 14 | Create handoff (MEU-TS3) | reviewer | `.agent/context/handoffs/109-2026-04-11-pyright-entity-factories-bpTSsC.md` | `Test-Path .agent/context/handoffs/109-2026-04-11-pyright-entity-factories-bpTSsC.md` | `[x]` |
| 15 | Create reflection | orchestrator | `docs/execution/reflections/2026-04-11-pyright-test-cleanup-reflection.md` | `Test-Path docs/execution/reflections/2026-04-11-pyright-test-cleanup-reflection.md` | `[x]` |
| 16 | Append metrics row | orchestrator | Row appended to `docs/execution/metrics.md` | `Get-Content docs/execution/metrics.md \| Select-Object -Last 3` | `[x]` |

### Status Legend

| Symbol | Meaning |
|--------|---------|
| `[ ]` | Not started |
| `[/]` | In progress |
| `[x]` | Complete |
| `[B]` | Blocked (must link follow-up) |
