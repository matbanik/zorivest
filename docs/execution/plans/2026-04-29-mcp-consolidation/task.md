---
project: "2026-04-29-mcp-consolidation"
source: "docs/execution/plans/2026-04-29-mcp-consolidation/implementation-plan.md"
meus: ["MC0", "MC1", "MC2", "MC3", "MC4", "MC5", "SEC-1"]
status: "complete"
template_version: "2.0"
---

# Task — MCP Tool Consolidation (P2.5f)

> **Project:** `2026-04-29-mcp-consolidation`
> **Type:** MCP
> **Estimate:** ~30 files changed

## Task Table

| # | Task | Owner | Deliverable | Validation | Status |
|---|------|-------|-------------|------------|--------|
| 1 | **MC0**: Add P2.5f section to BUILD_PLAN.md (6 MEU rows, fix P2.5e status, update Phase 9 tracker, add summary row) | orchestrator | Updated `docs/BUILD_PLAN.md` | `rg "P2.5f" docs/BUILD_PLAN.md *> C:\Temp\zorivest\mc0-bp.txt; Get-Content C:\Temp\zorivest\mc0-bp.txt` → 3+ matches | `[x]` |
| 2 | **MC0**: Register MC0–MC5 in meu-registry.md | orchestrator | Updated `.agent/context/meu-registry.md` | `rg "MC0\|MC1\|MC2\|MC3\|MC4\|MC5" .agent/context/meu-registry.md *> C:\Temp\zorivest\mc0-reg.txt; Get-Content C:\Temp\zorivest\mc0-reg.txt` → 6 matches | `[x]` |
| 3 | **MC0**: Update [MCP-TOOLPROLIFERATION] to "In Progress" in known-issues.md | orchestrator | Updated `.agent/context/known-issues.md` | `rg "In Progress" .agent/context/known-issues.md *> C:\Temp\zorivest\mc0-ki.txt; Get-Content C:\Temp\zorivest\mc0-ki.txt` → matches TOOLPROLIFERATION | `[x]` |
| 4 | **MC0**: Update 05-mcp-server.md §5.11, create mcp-tool-index.md, update build-priority-matrix.md | orchestrator | 3 doc files updated/created | `Test-Path .agent/context/MCP/mcp-tool-index.md *> C:\Temp\zorivest\mc0-idx.txt; Test-Path docs/build-plan/05-mcp-server.md *>> C:\Temp\zorivest\mc0-idx.txt; Test-Path docs/build-plan/build-priority-matrix.md *>> C:\Temp\zorivest\mc0-idx.txt; Get-Content C:\Temp\zorivest\mc0-idx.txt` → 3× True | `[x]` |
| 5 | **MC1**: Implement CompoundToolRouter in `mcp-server/src/compound/router.ts` | coder | Router class with `dispatch()`, per-action strict Zod validation | `cd mcp-server; npx vitest run tests/compound/router.test.ts *> C:\Temp\zorivest\router-test.txt; Get-Content C:\Temp\zorivest\router-test.txt \| Select-Object -Last 20` | `[x]` |
| 6 | **MC1**: Create `zorivest_system` compound tool (9 actions), remove 9 old registrations | coder | `zorivest_system` tool in `compound/system-tool.ts` | `cd mcp-server; npx vitest run *> C:\Temp\zorivest\mc1-vitest.txt; Get-Content C:\Temp\zorivest\mc1-vitest.txt \| Select-Object -Last 30` | `[x]` |
| 7 | **MC1**: Verify tools/list count = 77 after MC1 | tester | Count verified via vitest assertion | `cd mcp-server; npx vitest run tests/compound/system-tool.test.ts *> C:\Temp\zorivest\mc1-count.txt; Get-Content C:\Temp\zorivest\mc1-count.txt \| Select-Object -Last 20` | `[x]` |
| 8 | **MC1**: Build dist/ | coder | Clean build | `cd mcp-server; npm run build *> C:\Temp\zorivest\mc1-build.txt; Get-Content C:\Temp\zorivest\mc1-build.txt \| Select-Object -Last 10` | `[x]` |
| 9 | **MC2**: Create `zorivest_trade` (6 actions), `zorivest_report` (2 actions), `zorivest_analytics` (13 actions); remove 21 old registrations | coder | 3 compound tools in `compound/` | `cd mcp-server; npx vitest run *> C:\Temp\zorivest\mc2-vitest.txt; Get-Content C:\Temp\zorivest\mc2-vitest.txt \| Select-Object -Last 30` | `[x]` |
| 10 | **MC2**: Verify tools/list count = 59, destructive gates preserved | tester | Count + confirmation tests | `cd mcp-server; npx vitest run tests/compound/trade-tool.test.ts tests/compound/analytics-tool.test.ts *> C:\Temp\zorivest\mc2-count.txt; Get-Content C:\Temp\zorivest\mc2-count.txt \| Select-Object -Last 20` | `[x]` |
| 11 | **MC2**: Build dist/ | coder | Clean build | `cd mcp-server; npm run build *> C:\Temp\zorivest\mc2-build.txt; Get-Content C:\Temp\zorivest\mc2-build.txt \| Select-Object -Last 10` | `[x]` |
| 12 | **MC3**: Create `zorivest_account` (9), `zorivest_market` (7), `zorivest_watchlist` (5), `zorivest_import` (7), `zorivest_tax` (4 stubs); remove 32 old registrations | coder | 5 compound tools in `compound/` | `cd mcp-server; npx vitest run *> C:\Temp\zorivest\mc3-vitest.txt; Get-Content C:\Temp\zorivest\mc3-vitest.txt \| Select-Object -Last 30` | `[x]` |
| 13 | **MC3**: Verify tools/list count = 32, destructive gates preserved, 501 stubs preserved | tester | Count + confirmation + 501 tests | `cd mcp-server; npx vitest run tests/compound/account-tool.test.ts tests/compound/import-tool.test.ts *> C:\Temp\zorivest\mc3-count.txt; Get-Content C:\Temp\zorivest\mc3-count.txt \| Select-Object -Last 20` | `[x]` |
| 14 | **MC3**: Build dist/ | coder | Clean build | `cd mcp-server; npm run build *> C:\Temp\zorivest\mc3-build.txt; Get-Content C:\Temp\zorivest\mc3-build.txt \| Select-Object -Last 10` | `[x]` |
| 15 | **MC4**: Create `zorivest_plan` (3), `zorivest_policy` (9), `zorivest_template` (6), `zorivest_db` (5); remove 23 old registrations; restructure seed.ts (10→4 toolsets) | coder | 4 compound tools + restructured seed.ts | `cd mcp-server; npx vitest run *> C:\Temp\zorivest\mc4-vitest.txt; Get-Content C:\Temp\zorivest\mc4-vitest.txt \| Select-Object -Last 30` | `[x]` |
| 16 | **MC4**: Add startup Zod shape assertion for all 13 tools | coder | Assertion in `registration.ts` | `cd mcp-server; npx vitest run *> C:\Temp\zorivest\mc4-assert.txt; Get-Content C:\Temp\zorivest\mc4-assert.txt \| Select-Object -Last 20` | `[x]` |
| 17 | **MC4**: Add CI gate test `tool_count ≤ 13` | coder | `tests/tool-count-gate.test.ts` | `cd mcp-server; npx vitest run tests/tool-count-gate.test.ts *> C:\Temp\zorivest\gate.txt; Get-Content C:\Temp\zorivest\gate.txt \| Select-Object -Last 20` | `[x]` |
| 18 | **MC4**: Verify empirical tools/list counts: defaults=4, data=6, all=13, toolset_enable(ops)=5 | tester | 5 count assertions in vitest | `cd mcp-server; npx vitest run tests/tool-count-gate.test.ts *> C:\Temp\zorivest\mc4-empirical.txt; Get-Content C:\Temp\zorivest\mc4-empirical.txt \| Select-Object -Last 20` | `[x]` |
| 19 | **MC4**: Build dist/ | coder | Clean build | `cd mcp-server; npm run build *> C:\Temp\zorivest\mc4-build.txt; Get-Content C:\Temp\zorivest\mc4-build.txt \| Select-Object -Last 10` | `[x]` |
| 20 | **MC5**: Regenerate `baseline-snapshot.json` (85→13) | coder | Updated snapshot with 13 entries | `rg "\"name\":" mcp-server/tests/baseline-snapshot.json *> C:\Temp\zorivest\mc5-snap.txt; Get-Content C:\Temp\zorivest\mc5-snap.txt \| Measure-Object \| Select-Object Count` → 13 | `[x]` |
| 21 | **MC5**: Update `serverInstructions` in `client-detection.ts` with 13-tool action summaries | coder | Updated server instructions | `rg "zorivest_" mcp-server/src/client-detection.ts *> C:\Temp\zorivest\mc5-instr.txt; Get-Content C:\Temp\zorivest\mc5-instr.txt \| Measure-Object \| Select-Object Count` → 13+ | `[x]` |
| 22 | **MC5**: Archive [MCP-TOOLPROLIFERATION] in known-issues.md | orchestrator | Entry moved to archive table | `rg "MCP-TOOLPROLIFERATION" .agent/context/known-issues.md *> C:\Temp\zorivest\mc5-ki.txt; Get-Content C:\Temp\zorivest\mc5-ki.txt` → in Archived table | `[x]` |
| 23 | **MC5**: Verify MCP Resources (6) unchanged in pipeline-security-tools.ts | tester | 6 resources still registered | `rg "server.resource" mcp-server/src/tools/pipeline-security-tools.ts *> C:\Temp\zorivest\mc5-res.txt; Get-Content C:\Temp\zorivest\mc5-res.txt \| Measure-Object \| Select-Object Count` → 6 | `[x]` |
| 24 | **MC5**: Run anti-placeholder scan | tester | 0 matches | `rg "TODO\|FIXME\|NotImplementedError" mcp-server/src/ *> C:\Temp\zorivest\placeholder.txt; Get-Content C:\Temp\zorivest\placeholder.txt` | `[x]` |
| 25 | **MC5**: Full vitest + tsc + build | tester | All pass | `cd mcp-server; npx vitest run *> C:\Temp\zorivest\mc5-vitest.txt; npx tsc --noEmit *> C:\Temp\zorivest\mc5-tsc.txt; npm run build *> C:\Temp\zorivest\mc5-build.txt; Get-Content C:\Temp\zorivest\mc5-vitest.txt \| Select-Object -Last 20` | `[x]` |
| 26 | **MC5**: Run MEU quality gate | tester | validate_codebase.py passes | `uv run python tools/validate_codebase.py --scope meu *> C:\Temp\zorivest\validate.txt; Get-Content C:\Temp\zorivest\validate.txt \| Select-Object -Last 50` | `[x]` |
| 27 | Audit `docs/BUILD_PLAN.md` for stale refs | orchestrator | P2.5f section verified, P2.5e status corrected | `rg "P2.5f" docs/BUILD_PLAN.md *> C:\Temp\zorivest\bp-audit.txt; Get-Content C:\Temp\zorivest\bp-audit.txt` (expect 3+ matches) | `[x]` |
| 28 | Run verification plan (vitest + tsc + build + placeholder + MEU gate) | tester | All checks pass | `cd mcp-server; npx vitest run *> C:\Temp\zorivest\final-vitest.txt; npx tsc --noEmit *> C:\Temp\zorivest\final-tsc.txt; npm run build *> C:\Temp\zorivest\final-build.txt; Get-Content C:\Temp\zorivest\final-vitest.txt \| Select-Object -Last 20` | `[x]` |
| 29 | Save session state to pomera_notes | orchestrator | `Memory/Session/Zorivest-mcp-consolidation-2026-04-29` | `pomera_notes` MCP call: `action="search", search_term="Zorivest-mcp-consolidation*"` → verify ≥1 result returned. Fallback: `Test-Path C:\Temp\zorivest\pomera-save.txt` after manual receipt. | `[x]` |
| 30 | Create handoff | reviewer | `.agent/context/handoffs/2026-04-29-mcp-consolidation-handoff.md` | `Test-Path .agent/context/handoffs/2026-04-29-mcp-consolidation-handoff.md` | `[x]` |
| 31 | Create reflection | orchestrator | `docs/execution/reflections/2026-04-29-mcp-consolidation-reflection.md` | `Test-Path docs/execution/reflections/2026-04-29-mcp-consolidation-reflection.md` | `[x]` |
| 32 | Append metrics row | orchestrator | Row appended to `docs/execution/metrics.md` | `Get-Content docs/execution/metrics.md *> C:\Temp\zorivest\metrics-check.txt; Get-Content C:\Temp\zorivest\metrics-check.txt \| Select-Object -Last 3` | `[x]` |
| 33 | **SEC-1**: Harden `POST /policies/{id}/run` with CSRF approval token gate — prevent MCP confirmation bypass via direct API calls | coder | `validate_approval_token` dependency added to `trigger_pipeline` + regression test | `uv run pytest tests/unit/test_api_scheduling.py -x --tb=short -v -k "csrf" *> C:\Temp\zorivest\csrf-test.txt; Get-Content C:\Temp\zorivest\csrf-test.txt \| Select-Object -Last 10` → 1 passed | `[x]` |

### Status Legend

| Symbol | Meaning |
|--------|---------|
| `[ ]` | Not started |
| `[/]` | In progress |
| `[x]` | Complete |
| `[B]` | Blocked (must link follow-up) |
