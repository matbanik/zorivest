---
project: "2026-04-30-mcp-discoverability-audit"
date: "2026-04-30"
source: "docs/build-plan/05j-mcp-discovery.md, docs/build-plan/05-mcp-server.md §5.11"
meus: ["TD1"]
status: "draft"
template_version: "2.0"
---

# Implementation Plan: MCP Tool Discoverability Audit

> **Project**: `2026-04-30-mcp-discoverability-audit`
> **Build Plan Section(s)**: 05j (MCP Discovery), 05-mcp-server §5.11 (Toolset Configuration)
> **Status**: `draft`

---

## Goal

AI agents using the Zorivest MCP server cannot discover multi-step workflows from tool descriptions alone. The scheduling toolset is the documented worst case: `run_pipeline` doesn't mention the approval prerequisite, `create_policy` has no example of the expected `policy_json` structure, and server instructions say only "Automated task scheduling" with no workflow guidance. This problem affects all 4 toolsets (core, trade, data, ops) across 13 compound tools.

MEU-TD1 audits all 13 compound tool descriptions and server instructions against the M7 checklist, enriching each with workflow context, prerequisite state, return shapes, error conditions, and MCP resource references. It also strengthens M7 to mandate discoverability compliance for all future MCP MEUs.

---

## User Review Required

> [!IMPORTANT]
> 1. **No external boundary surfaces** — This MEU modifies only `.description` strings and `getServerInstructions()`. No REST endpoints, Zod schemas, or handler logic change. No boundary inventory is required.
> 2. **Timing decision** — Approved by user: execute now against 13 existing compound tools, with M7 enforcement gate for future tools (no separate follow-up MEU).
> 3. **Test scope (Human-approved TDD exception)** — Per AGENTS.md §231-236, every AC should become at least one test assertion. This MEU applies a **scoped exception** (approved by user in conversation `0b93626a-3c9d-4014-bc8d-3a06692e9edb` on 2026-04-30, `/plan-corrections` Pass 2 approval): AC-1 through AC-11 describe static `.description` string content with no runtime behavior, no branching logic, and no external inputs. Writing vitest assertions that duplicate grep checks on string literals provides no additional defect-detection value beyond the M7 grep validation. Verification strategy: (a) existing `tool-count-gate.test.ts` (structural — asserts 13 tools, 4 toolsets), (b) M7 marker grep validation (`rg -i "workflow:|prerequisite:|returns:|errors:" mcp-server/src/compound/ --count` — each file ≥3 markers), (c) TypeScript compilation (`npx tsc --noEmit`), (d) full vitest regression (376 tests). AC-12 and AC-13 are verified by standard build/test commands. This exception is scoped to metadata-only MEUs and does not set precedent for MEUs with runtime behavior.

---

## Proposed Changes

### MEU-TD1: MCP Tool Discoverability Audit

#### Scope

This MEU is **documentation-in-code** — it modifies TypeScript string literals (`.description` fields) and the `getServerInstructions()` function. No handler logic, Zod schemas, or API endpoints change.

#### Boundary Inventory

No external input surfaces are modified by this MEU. All changes are to read-only metadata strings consumed by MCP clients during tool listing. Not applicable.

#### Acceptance Criteria

| AC | Description | Source | Content Assertion |
|----|-------------|--------|-------------------|
| AC-1 | `getServerInstructions()` includes per-toolset workflow summaries (not just tool lists) | Local Canon: known-issues.md [MCP-TOOLDISCOVERY] | `rg "Workflow:\|lifecycle\|→" mcp-server/src/client-detection.ts` |
| AC-2 | `zorivest_policy` description includes the `create → emulate → run` lifecycle and `policy_json` example shape | Local Canon: emerging-standards.md §M7 — Tool Description Workflow Context | `rg "lifecycle\|→\|policy_json" mcp-server/src/compound/policy-tool.ts` |
| AC-3 | `zorivest_policy` description references MCP resources (`pipeline://policies/schema`, `pipeline://step-types`) | Local Canon: emerging-standards.md §M7 + known-issues.md [MCP-TOOLDISCOVERY] | `rg "pipeline://" mcp-server/src/compound/policy-tool.ts` |
| AC-4 | Every compound tool's top-level `.description` includes: (a) prerequisite state if any, (b) return shape hint, (c) error conditions | Local Canon: emerging-standards.md §M7 checklist | M7 grep: each file ≥3 of 4 markers |
| AC-5 | `zorivest_system` description documents the discovery workflow: `toolsets_list → toolset_describe → toolset_enable` | Local Canon: emerging-standards.md §M7 checklist #1 | `rg "toolsets_list.*toolset_describe" mcp-server/src/compound/system-tool.ts` |
| AC-6 | `zorivest_trade` description mentions confirmation gate requirement for `delete` action | Local Canon: emerging-standards.md §M3 | `rg "confirmation.*delete\|delete.*confirmation" mcp-server/src/compound/trade-tool.ts` |
| AC-7 | `zorivest_import` description includes guidance for CSV column mapping and supported broker formats | Local Canon: 05f-mcp-accounts.md §18-19,26 (import tools: broker_csv, broker_pdf, bank_statement) | `rg "CSV\|broker\|format" mcp-server/src/compound/import-tool.ts` |
| AC-8 | `zorivest_tax` description clearly states all actions return 501 (not implemented) | Local Canon: 05h-mcp-tax.md + Human-approved: stub-only per current phase | `rg "501" mcp-server/src/compound/tax-tool.ts` |
| AC-9 | `zorivest_analytics` description includes at least 3 example action workflows (e.g., position sizing → round trips → drawdown) | Local Canon: emerging-standards.md §M7 checklist #1 | `rg "→" mcp-server/src/compound/analytics-tool.ts` |
| AC-10 | M7 standard updated with mandatory enforcement gate for future MCP MEUs | Human-approved: user timing decision | `rg "enforcement.*mandatory\|mandatory.*exit" .agent/docs/emerging-standards.md` |
| AC-11 | All 13 compound tool `.description` strings pass M7 5-point checklist | Local Canon: emerging-standards.md §M7 | `rg -i "workflow:\|prerequisite:\|returns:\|errors:" mcp-server/src/compound/ --count` (each ≥3) |
| AC-12 | `npm run build` succeeds with no TypeScript errors after description changes | Local Canon: emerging-standards.md §M4 | `npx tsc --noEmit` |
| AC-13 | Existing vitest tests pass (no regressions from string changes) | Local Canon: testing-strategy.md | `npx vitest run` |

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| What content belongs in tool descriptions | Local Canon | M7 checklist (emerging-standards.md) — 5-point checklist with examples |
| How verbose should descriptions be | Research-backed | MCP SDK specification (https://modelcontextprotocol.io/specification/2025-06-18/server/tools): descriptions are the primary discovery mechanism for AI agents |
| Server instructions format | Local Canon | Current `getServerInstructions()` in `client-detection.ts` — expand, don't restructure |
| Whether to add per-action descriptions inside compound tools | Research-backed | MCP SDK convention: top-level description covers all actions; action enum `.describe()` provides per-action hints |
| Whether to reference MCP resources from descriptions | Local Canon | emerging-standards.md §M7 checklist + known-issues.md [MCP-TOOLDISCOVERY]: "MCP resources are referenced from the tools that consume them" |
| M7 enforcement mechanism | Human-approved | User approved: add enforcement gate to M7 standard, no separate follow-up MEU |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `mcp-server/src/compound/system-tool.ts` | modify | Enrich `zorivest_system` description with discovery workflow, action prerequisites |
| `mcp-server/src/compound/trade-tool.ts` | modify | Add confirmation gate info, return shapes, screenshot workflow |
| `mcp-server/src/compound/analytics-tool.ts` | modify | Add example workflows, return shape hints |
| `mcp-server/src/compound/report-tool.ts` | modify | Add prerequisite (trade must exist), return shape |
| `mcp-server/src/compound/plan-tool.ts` | modify | Add return shape, pagination info |
| `mcp-server/src/compound/account-tool.ts` | modify | Add lifecycle workflow, archive implications |
| `mcp-server/src/compound/market-tool.ts` | modify | Add provider prerequisite, quote return shape |
| `mcp-server/src/compound/watchlist-tool.ts` | modify | Add CRUD workflow, return shape |
| `mcp-server/src/compound/import-tool.ts` | modify | Add CSV format guidance, broker list reference |
| `mcp-server/src/compound/tax-tool.ts` | modify | Add 501 stub status, future implementation note |
| `mcp-server/src/compound/policy-tool.ts` | modify | Major: add lifecycle workflow, `policy_json` example, resource references |
| `mcp-server/src/compound/template-tool.ts` | modify | Add template variable contract, preview workflow |
| `mcp-server/src/compound/db-tool.ts` | modify | Add query validation guidance, available tables |
| `mcp-server/src/client-detection.ts` | modify | Expand `getServerInstructions()` with per-toolset workflow summaries |
| `.agent/docs/emerging-standards.md` | modify | Add M7 enforcement gate for future MCP MEUs |

---

## Out of Scope

- Handler logic changes (no behavior changes, only description strings)
- New MCP tools or actions
- Zod schema modifications
- REST API changes
- Tax/behavioral tool implementation (future phases)
- MCP resource creation (resources already exist — we reference them)

---

## BUILD_PLAN.md Audit

This project updates MEU-TD1 status from `⬜` to `✅` in `docs/BUILD_PLAN.md`. One row change expected.

```powershell
rg "MEU-TD1" docs/BUILD_PLAN.md  # Expected: 2 matches (MEU table row + phase row)
```

---

## Verification Plan

### 1. TypeScript Compilation
```powershell
cd mcp-server; npx tsc --noEmit *> C:\Temp\zorivest\tsc.txt; Get-Content C:\Temp\zorivest\tsc.txt | Select-Object -Last 10
```

### 2. Vitest (MCP tests)
```powershell
cd mcp-server; npx vitest run *> C:\Temp\zorivest\vitest.txt; Get-Content C:\Temp\zorivest\vitest.txt | Select-Object -Last 40
```

### 3. M7 Checklist Validation (per compound tool)
```powershell
# Verify every compound tool description mentions at least one action workflow or prerequisite
rg "workflow|prerequisite|Prerequisite|Actions:|lifecycle|Returns" mcp-server/src/compound/*-tool.ts *> C:\Temp\zorivest\m7-check.txt; Get-Content C:\Temp\zorivest\m7-check.txt | Select-Object -Last 30
```

### 4. Server Instructions Validation
```powershell
# Verify server instructions include per-toolset workflow summaries
rg "Workflow:|lifecycle|→" mcp-server/src/client-detection.ts *> C:\Temp\zorivest\si-check.txt; Get-Content C:\Temp\zorivest\si-check.txt
```

### 5. Build Dist
```powershell
cd mcp-server; npm run build *> C:\Temp\zorivest\build.txt; Get-Content C:\Temp\zorivest\build.txt | Select-Object -Last 10
```

### 6. Anti-Placeholder Scan
```powershell
rg "TODO|FIXME|NotImplementedError" mcp-server/src/compound/ *> C:\Temp\zorivest\placeholder.txt; Get-Content C:\Temp\zorivest\placeholder.txt
```

---

## Open Questions

> [!WARNING]
> None. All design decisions resolved:
> - Timing: execute now (user-approved)
> - M7 enforcement: built-in gate (user-approved)
> - Scope: 13 compound tools + server instructions (complete current surface)

---

## Ad-Hoc GUI Changes (Session 2026-04-30)

The following GUI polish changes were applied during this session at user direction, outside the formal MEU-TD1 scope:

| # | Change | File | Rationale |
|---|--------|------|-----------|
| AH-1 | Email Templates button text `+ New` → `+ New Template`, color matched to Report Policies (`accent-purple`) | `ui/src/renderer/src/features/scheduling/EmailTemplateList.tsx` | Visual consistency with Policy tab |
| AH-2 | NavRail: Settings moved above divider line, Collapse button left-aligned to match Settings | `ui/src/renderer/src/components/layout/NavRail.tsx` | Alignment/layout polish |
| AH-3 | Settings page: section heading `Data Sources` → `External Providers` | `ui/src/renderer/src/features/settings/SettingsLayout.tsx` | User-requested rename |

---

## Research References

- [Emerging Standard M7](file:///p:/zorivest/.agent/docs/emerging-standards.md#m7) — Tool Description Workflow Context
- [Known Issue MCP-TOOLDISCOVERY](file:///p:/zorivest/.agent/context/known-issues.md) — Original pain point documentation
- [Build Plan 05j](file:///p:/zorivest/docs/build-plan/05j-mcp-discovery.md) — Discovery tools specification
- [MCP Tool Audit Report](file:///p:/zorivest/.agent/context/MCP/mcp-tool-audit-report.md) — P2.5f consolidation findings
