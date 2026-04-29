---
project: "2026-04-29-mcp-tool-remediation"
source: "docs/execution/plans/2026-04-29-mcp-tool-remediation/implementation-plan.md"
meus: ["MEU-TA1", "MEU-TA2", "MEU-TA3", "MEU-TA4"]
status: "complete"
template_version: "2.0"
---

# Task — MCP Tool Remediation (P2.5e)

> **Project:** `2026-04-29-mcp-tool-remediation`
> **Type:** MCP + API
> **Estimate:** ~10 files changed

## Task Table

| # | Task | Owner | Deliverable | Validation | Status |
|---|------|-------|-------------|------------|--------|
| 1 | **TA1**: Write FIC + regression tests for `delete_trade` 404 handling | coder | `tests/unit/test_api_trades.py` with AC-0..AC-4 | `uv run pytest tests/unit/test_api_trades.py -x --tb=short -v *> C:\Temp\zorivest\pytest-ta1.txt; Get-Content C:\Temp\zorivest\pytest-ta1.txt \| Select-Object -Last 20` | `[x]` |
| 2 | **TA1**: Fix `trade_service.delete_trade` to raise `NotFoundError` on miss | coder | Modified `trade_service.py` | `uv run pytest tests/unit/test_api_trades.py -k "test_delete" -x --tb=short *> C:\Temp\zorivest\pytest-ta1-svc.txt; Get-Content C:\Temp\zorivest\pytest-ta1-svc.txt \| Select-Object -Last 10` | `[x]` |
| 3 | **TA1**: Fix `trades.py` route to catch `NotFoundError` → 404 | coder | Modified `trades.py` | `uv run pytest tests/unit/test_api_trades.py -x --tb=short *> C:\Temp\zorivest\pytest-ta1-route.txt; Get-Content C:\Temp\zorivest\pytest-ta1-route.txt \| Select-Object -Last 10` | `[x]` |
| 4 | **TA1**: Run MEU gate | tester | All quality checks pass | `uv run python tools/validate_codebase.py --scope meu *> C:\Temp\zorivest\validate-ta1.txt; Get-Content C:\Temp\zorivest\validate-ta1.txt \| Select-Object -Last 20` | `[x]` |
| 5 | **TA2**: Write FIC + test for `fetchApi` error detail serialization | coder | `mcp-server/tests/settings-tools.test.ts` | `cd mcp-server; npx vitest run tests/settings-tools.test.ts *> C:\Temp\zorivest\vitest-ta2.txt; Get-Content C:\Temp\zorivest\vitest-ta2.txt \| Select-Object -Last 20` | `[x]` |
| 6 | **TA2**: Fix `api-client.ts` to stringify non-string error details | coder | Modified `api-client.ts` | `cd mcp-server; npx vitest run tests/settings-tools.test.ts *> C:\Temp\zorivest\vitest-ta2-fix.txt; Get-Content C:\Temp\zorivest\vitest-ta2-fix.txt \| Select-Object -Last 20` | `[x]` |
| 7 | **TA2**: Build check | tester | Clean tsc | `cd mcp-server; npx tsc --noEmit *> C:\Temp\zorivest\tsc-ta2.txt; Get-Content C:\Temp\zorivest\tsc-ta2.txt \| Select-Object -Last 10` | `[x]` |
| 8 | **TA4**: Add `list_trade_plans` tool to `planning-tools.ts` | coder | New tool registration | `cd mcp-server; npx vitest run tests/planning-tools.test.ts *> C:\Temp\zorivest\vitest-ta4.txt; Get-Content C:\Temp\zorivest\vitest-ta4.txt \| Select-Object -Last 20` | `[x]` |
| 9 | **TA4**: Add `delete_trade_plan` tool with confirmation gate to `planning-tools.ts` | coder | New tool registration | `cd mcp-server; npx vitest run tests/planning-tools.test.ts *> C:\Temp\zorivest\vitest-ta4-del.txt; Get-Content C:\Temp\zorivest\vitest-ta4-del.txt \| Select-Object -Last 20` | `[x]` |
| 10 | **TA4**: Update `seed.ts` trade-planning toolset with new tools | coder | Modified `seed.ts` | `cd mcp-server; npx vitest run tests/seed.test.ts *> C:\Temp\zorivest\vitest-seed.txt; Get-Content C:\Temp\zorivest\vitest-seed.txt \| Select-Object -Last 20` | `[x]` |
| 11 | **TA4**: Build check + MCP audit of trade plan CRUD | tester | Clean tsc, `create_trade_plan` verified live | `cd mcp-server; npx tsc --noEmit *> C:\Temp\zorivest\tsc-ta4.txt; Get-Content C:\Temp\zorivest\tsc-ta4.txt \| Select-Object -Last 10` | `[x]` |
| 12 | **TA3**: Replace 3 accounts-tools handlers with 501 stubs | coder | Modified `accounts-tools.ts` | `cd mcp-server; npx vitest run tests/accounts-tools.test.ts *> C:\Temp\zorivest\vitest-ta3.txt; Get-Content C:\Temp\zorivest\vitest-ta3.txt \| Select-Object -Last 20` | `[x]` |
| 13 | **TA3**: Create `tax-tools.ts` with 4 tax tool 501 stubs | coder | New `tax-tools.ts` | `cd mcp-server; npx tsc --noEmit *> C:\Temp\zorivest\tsc-ta3.txt; Get-Content C:\Temp\zorivest\tsc-ta3.txt \| Select-Object -Last 10` | `[x]` |
| 14 | **TA3**: Wire tax toolset register in `seed.ts` | coder | Modified `seed.ts` | `cd mcp-server; npx vitest run tests/seed.test.ts *> C:\Temp\zorivest\vitest-seed-ta3.txt; Get-Content C:\Temp\zorivest\vitest-seed-ta3.txt \| Select-Object -Last 20` | `[x]` |
| 15 | **TA3**: Build check | tester | Clean tsc, 247/247 MCP tests pass | `cd mcp-server; npx vitest run *> C:\Temp\zorivest\vitest-full.txt; Get-Content C:\Temp\zorivest\vitest-full.txt \| Select-Object -Last 30` | `[x]` |
| 16 | Run `/mcp-audit` full audit | tester | Audit report updated, regressions checked | Invoke `/mcp-audit` workflow after IDE restart loads rebuilt `dist/` | `[x]` Targeted audit: 404 ✅, 501 stubs ✅, trade plan CRUD ✅. Cascade-delete 500 is pre-existing infra bug (not regression). |
| 17 | Update `meu-registry.md` TA1-TA4 → ✅ done | orchestrator | Registry updated | `rg "MEU-TA[1-4]" .agent/context/meu-registry.md *> C:\Temp\zorivest\registry-check.txt; Get-Content C:\Temp\zorivest\registry-check.txt` | `[x]` |
| 18 | Update `BUILD_PLAN.md` TA1-TA4 → ✅ | orchestrator | Build plan updated | `rg "MEU-TA[1-4]" docs/BUILD_PLAN.md *> C:\Temp\zorivest\buildplan-check.txt; Get-Content C:\Temp\zorivest\buildplan-check.txt` | `[x]` |
| 19 | Update `known-issues.md` [MCP-TOOLAUDIT] → archived | orchestrator | Issues archived | `rg "MCP-TOOLAUDIT" .agent/context/known-issues-archive.md *> C:\Temp\zorivest\ki-archive.txt; Get-Content C:\Temp\zorivest\ki-archive.txt` | `[x]` |
| 20 | Save session state to pomera_notes | orchestrator | `Memory/Session/Zorivest-mcp-remediation-2026-04-29` | MCP: `pomera_notes(action="search", search_term="Zorivest-mcp-remediation*")` returns ≥1 result | `[B]` pomera_notes tool not available in session toolset |
| 21 | Create handoff | reviewer | `.agent/context/handoffs/2026-04-29-mcp-tool-remediation-handoff.md` | `Test-Path .agent/context/handoffs/2026-04-29-mcp-tool-remediation-handoff.md` | `[x]` |
| 22 | Create reflection | orchestrator | `docs/execution/reflections/2026-04-29-mcp-tool-remediation-reflection.md` | `Test-Path docs/execution/reflections/2026-04-29-mcp-tool-remediation-reflection.md` | `[x]` |
| 23 | Append metrics row | orchestrator | Row appended to `docs/execution/metrics.md` | `Get-Content docs/execution/metrics.md \| Select-Object -Last 3` | `[x]` |

### Status Legend

| Symbol | Meaning |
|--------|---------|
| `[ ]` | Not started |
| `[/]` | In progress |
| `[x]` | Complete |
| `[B]` | Blocked (must link follow-up) |
