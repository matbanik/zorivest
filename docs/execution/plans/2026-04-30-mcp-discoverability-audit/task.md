---
project: "2026-04-30-mcp-discoverability-audit"
source: "docs/execution/plans/2026-04-30-mcp-discoverability-audit/implementation-plan.md"
meus: ["TD1"]
status: "complete"
template_version: "2.0"
---

# Task — MCP Tool Discoverability Audit

> **Project:** `2026-04-30-mcp-discoverability-audit`
> **Type:** MCP
> **Estimate:** 15 files changed (13 compound tools + client-detection.ts + emerging-standards.md)

## Task Table

| # | Task | Owner | Deliverable | Validation | Status |
|---|------|-------|-------------|------------|--------|
| 1 | Enrich `zorivest_policy` description with `create → approve → run` lifecycle, `policy_json` example shape, resource references, return shapes, error conditions (AC-2, AC-3, AC-4) | coder | `policy-tool.ts` description updated | `rg "lifecycle\|→\|policy_json\|pipeline://" mcp-server/src/compound/policy-tool.ts *> C:\Temp\zorivest\td1-t1.txt; Get-Content C:\Temp\zorivest\td1-t1.txt` | `[x]` |
| 2 | Enrich `zorivest_system` description with discovery workflow (`toolsets_list → toolset_describe → toolset_enable`), action prerequisites, return shapes (AC-4, AC-5) | coder | `system-tool.ts` description updated | `rg "toolsets_list.*toolset_describe\|discovery\|Workflow" mcp-server/src/compound/system-tool.ts *> C:\Temp\zorivest\td1-t2.txt; Get-Content C:\Temp\zorivest\td1-t2.txt` | `[x]` |
| 3 | Enrich `zorivest_trade` description with confirmation gate for delete, screenshot workflow, return shapes (AC-4, AC-6) | coder | `trade-tool.ts` description updated | `rg "confirmation\|screenshot_attach.*screenshot_list\|Returns" mcp-server/src/compound/trade-tool.ts *> C:\Temp\zorivest\td1-t3.txt; Get-Content C:\Temp\zorivest\td1-t3.txt` | `[x]` |
| 4 | Enrich `zorivest_analytics` description with example action workflows, return shapes (AC-4, AC-9) | coder | `analytics-tool.ts` description updated | `rg "Workflow\|→\|Returns" mcp-server/src/compound/analytics-tool.ts *> C:\Temp\zorivest\td1-t4.txt; Get-Content C:\Temp\zorivest\td1-t4.txt` | `[x]` |
| 5 | Enrich `zorivest_account` description with lifecycle workflow, archive implications, return shapes (AC-4) | coder | `account-tool.ts` description updated | `rg "archive\|Workflow\|Returns" mcp-server/src/compound/account-tool.ts *> C:\Temp\zorivest\td1-t5.txt; Get-Content C:\Temp\zorivest\td1-t5.txt` | `[x]` |
| 6 | Enrich `zorivest_market` description with provider prerequisite, return shapes (AC-4) | coder | `market-tool.ts` description updated | `rg "provider\|Prerequisite\|Returns" mcp-server/src/compound/market-tool.ts *> C:\Temp\zorivest\td1-t6.txt; Get-Content C:\Temp\zorivest\td1-t6.txt` | `[x]` |
| 7 | Enrich `zorivest_import` description with CSV format guidance, broker list reference (AC-4, AC-7) | coder | `import-tool.ts` description updated | `rg "CSV\|broker\|format" mcp-server/src/compound/import-tool.ts *> C:\Temp\zorivest\td1-t7.txt; Get-Content C:\Temp\zorivest\td1-t7.txt` | `[x]` |
| 8 | Enrich `zorivest_report`, `zorivest_plan`, `zorivest_watchlist`, `zorivest_tax`, `zorivest_template`, `zorivest_db` descriptions with prerequisite state, return shapes, error conditions (AC-4, AC-8) | coder | 6 `*-tool.ts` descriptions updated | `rg "Returns\|Prerequisite\|501" mcp-server/src/compound/report-tool.ts mcp-server/src/compound/plan-tool.ts mcp-server/src/compound/watchlist-tool.ts mcp-server/src/compound/tax-tool.ts mcp-server/src/compound/template-tool.ts mcp-server/src/compound/db-tool.ts *> C:\Temp\zorivest\td1-t8.txt; Get-Content C:\Temp\zorivest\td1-t8.txt` | `[x]` |
| 9 | Expand `getServerInstructions()` with per-toolset workflow summaries (AC-1) | coder | `client-detection.ts` server instructions enriched | `rg "Workflow:\|lifecycle\|→" mcp-server/src/client-detection.ts *> C:\Temp\zorivest\td1-t9.txt; Get-Content C:\Temp\zorivest\td1-t9.txt` | `[x]` |
| 10 | Add M7 enforcement gate to `emerging-standards.md` (AC-10) | coder | M7 checklist includes mandatory exit criterion for future MCP MEUs | `rg "enforcement\|mandatory.*exit\|future MCP" .agent/docs/emerging-standards.md *> C:\Temp\zorivest\td1-t10.txt; Get-Content C:\Temp\zorivest\td1-t10.txt` | `[x]` |
| 11 | TypeScript compilation check | tester | No TS errors | `cd mcp-server; npx tsc --noEmit *> C:\Temp\zorivest\tsc.txt; Get-Content C:\Temp\zorivest\tsc.txt \| Select-Object -Last 10` | `[x]` |
| 12 | Vitest regression check | tester | All MCP tests pass (376 passed) | `cd mcp-server; npx vitest run *> C:\Temp\zorivest\vitest.txt; Get-Content C:\Temp\zorivest\vitest.txt \| Select-Object -Last 40` | `[x]` |
| 13 | Build dist | tester | `npm run build` succeeds (13 tools, 4 toolsets) | `cd mcp-server; npm run build *> C:\Temp\zorivest\build.txt; Get-Content C:\Temp\zorivest\build.txt \| Select-Object -Last 10` | `[x]` |
| 14 | M7 checklist validation across all 13 tools (AC-11) | tester | All 13 files ≥3 markers | `rg -i "workflow:\|prerequisite:\|returns:\|errors:" mcp-server/src/compound/ --count *> C:\Temp\zorivest\m7-check.txt; Get-Content C:\Temp\zorivest\m7-check.txt` | `[x]` |
| 15 | Anti-placeholder scan | tester | 0 matches | `rg "TODO\|FIXME\|NotImplementedError" mcp-server/src/compound/ *> C:\Temp\zorivest\placeholder.txt; Get-Content C:\Temp\zorivest\placeholder.txt` | `[x]` |
| 16 | Update MEU-TD1 status in `meu-registry.md` | orchestrator | Added Technical Debt section with `✅ 2026-04-30` | `rg "MEU-TD1" .agent/context/meu-registry.md *> C:\Temp\zorivest\td1-registry.txt; Get-Content C:\Temp\zorivest\td1-registry.txt` | `[x]` |
| 17 | Update MEU-TD1 status in `docs/BUILD_PLAN.md` | orchestrator | `⬜` → `✅` on BUILD_PLAN.md:359 | `rg "MEU-TD1" docs/BUILD_PLAN.md *> C:\Temp\zorivest\buildplan-td1.txt; Get-Content C:\Temp\zorivest\buildplan-td1.txt` | `[x]` |
| 18 | Audit `docs/BUILD_PLAN.md` for stale refs | orchestrator | No stale references found | `rg "mcp-discoverability-audit\|tool-discovery" docs/BUILD_PLAN.md *> C:\Temp\zorivest\buildplan-stale.txt; Get-Content C:\Temp\zorivest\buildplan-stale.txt` | `[x]` |
| 19 | Save session state to pomera_notes | orchestrator | `Memory/Session/Zorivest-mcp-discoverability-audit-2026-04-30` | pomera_notes search | `[x]` |
| 20 | Create handoff | reviewer | `.agent/context/handoffs/2026-04-30-mcp-discoverability-audit-handoff.md` | `Test-Path .agent/context/handoffs/2026-04-30-mcp-discoverability-audit-handoff.md *> C:\Temp\zorivest\td1-handoff.txt; Get-Content C:\Temp\zorivest\td1-handoff.txt` | `[x]` |
| 21 | Create reflection | orchestrator | `docs/execution/reflections/2026-04-30-mcp-discoverability-audit-reflection.md` | `Test-Path docs/execution/reflections/2026-04-30-mcp-discoverability-audit-reflection.md *> C:\Temp\zorivest\td1-reflect.txt; Get-Content C:\Temp\zorivest\td1-reflect.txt` | `[x]` |
| 22 | Append metrics row | orchestrator | Row appended to `docs/execution/metrics.md` | `Get-Content docs/execution/metrics.md *> C:\Temp\zorivest\metrics.txt; Get-Content C:\Temp\zorivest\metrics.txt \| Select-Object -Last 3` | `[x]` |
| AH-1 | (Ad-hoc) Email Templates button: `+ New` → `+ New Template`, color → `accent-purple` | coder | `EmailTemplateList.tsx` updated | Visual inspection | `[x]` |
| AH-2 | (Ad-hoc) NavRail: Settings above divider, Collapse left-aligned | coder | `NavRail.tsx` updated | Visual inspection | `[x]` |
| AH-3 | (Ad-hoc) Settings: `Data Sources` → `External Providers` | coder | `SettingsLayout.tsx` updated | Visual inspection | `[x]` |

### Status Legend

| Symbol | Meaning |
|--------|---------|
| `[ ]` | Not started |
| `[/]` | In progress |
| `[x]` | Complete |
| `[B]` | Blocked (must link follow-up) |
