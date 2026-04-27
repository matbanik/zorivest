---
name: MCP Tool Audit
description: Systematic audit of all Zorivest MCP tools for completeness, correctness, and regression detection
trigger: /mcp-audit
---

# MCP Tool Audit Workflow

> Invoke via `/mcp-audit`. Runs the full MCP tool audit skill against the live backend.

## Pre-conditions

- [ ] Backend API is running (`npm run dev` in `ui/` or `uv run fastapi dev packages/api/...`)
- [ ] MCP server connected — `zorivest_diagnose` returns `backend.reachable: true`
- [ ] No other audit in progress

## Steps

### Step 1: Load Skill

Read `.agent/skills/mcp-audit/SKILL.md` and follow its execution protocol exactly.

### Step 2: Discovery Phase

Follow skill §Phase 1. Record toolset inventory.

- Call `list_available_toolsets` and `describe_toolset` for each
- Compare against `baseline-snapshot.json`
- Flag regressions, ghost tools, new tools

### Step 3: CRUD Testing

Follow skill §Phase 2. Test all CRUD-capable resources:

- Accounts: Create → Read → Update → Balance → Archive → Delete
- Trades: Create → Report → Delete
- Watchlists: Create → Add → Get → Remove
- Email Templates: Create → Read → Preview → Update → Delete

> [!CAUTION]
> **Cleanup is mandatory.** Delete all test entities before proceeding to Phase 3.
> If deletion fails, log the failure as an issue and flag for manual cleanup.

### Step 4: Functional Testing

Follow skill §Phase 3. Exercise all non-CRUD tools with valid minimal params.

- Market Data tools
- Analytics / Behavioral tools
- Planning tools
- Scheduling tools (read-only — do not create/run policies)
- Pipeline Security tools (include SQL injection test with `DROP TABLE`)
- Core / System tools

### Step 5: Regression Check

Follow skill §Phase 4. Load baseline and compare:

| Previous → Current | Classification |
|--------------------|----------------|
| PASS → FAIL | **REGRESSION** — flag immediately |
| FAIL → FAIL | **KNOWN ISSUE** — reference existing ID |
| FAIL → PASS | **FIXED** — update baseline |
| N/A → any | **NEW** — add to baseline |

### Step 6: Report & Record

Follow skill §Phase 5:

1. Write audit report to `.agent/context/MCP/mcp-tool-audit-report.md` (overwrite)
2. Update `known-issues.md` `[MCP-TOOLAUDIT]` entry
3. Update `baseline-snapshot.json`
4. Calculate consolidation score: `current_tools / 12`

### Step 7: Consolidation Advisory

If `consolidation_score > 3.0`:
- Add warning to report header: "⚠️ Tool count exceeds 3× ideal. Consolidation recommended."
- Reference audit report §Tool Consolidation Reflection for implementation plan

## Exit Criteria

- [ ] All CRUD resources tested with full lifecycle
- [ ] All functional tools exercised (or documented as untestable)
- [ ] Test data cleaned up (zero residual audit entities)
- [ ] Report written to `.agent/context/MCP/mcp-tool-audit-report.md`
- [ ] `known-issues.md` `[MCP-TOOLAUDIT]` updated with findings
- [ ] `baseline-snapshot.json` updated with current results
- [ ] Consolidation score calculated and logged
