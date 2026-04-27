# Agentic MCP Audit: Workflow & Skill Design

**Date**: 2026-04-27  
**Research sources**: Anthropic MCP best practices, hamel.dev agentic evals, mabl.com MCP testing patterns, community MCP QA frameworks  
**Objective**: Convert the manual MCP tool audit into a repeatable agentic workflow and skill

---

## 1. Research Summary

### What the industry recommends

Modern MCP testing has moved beyond basic connectivity to **behavioral contract testing** — validating how an LLM perceives and uses each tool, not just whether the API responds.

| Pattern | Source | Applicability |
|---------|--------|---------------|
| **LLM-as-Judge evals** | Anthropic, hamel.dev | Score tool hit rate and sequence accuracy |
| **Contract testing per tool** | Medium (MCP testing patterns) | Validate schema, params, error handling |
| **Autonomous QA agents** | mabl.com, community | Test Planner → Generator → Executor → Healer loop |
| **Transition failure matrices** | hamel.dev | Map where agents fail in multi-step workflows |
| **Sandbox isolation** | Multiple | Prevent side effects during automated testing |

### Key anti-patterns to avoid

1. **"God Tools"** — one tool with too many responsibilities *(conflicts with our consolidation proposal — we need the right granularity, not just fewer tools)*
2. **Chatty interfaces** — sequential high-latency tool calls that increase cost
3. **Monolithic servers** — keep MCP servers modular for fault isolation

### Reconciling consolidation with anti-patterns

The consolidation proposal (74→12 tools) uses **discriminated unions** — a single entry point per resource domain, but the `action` parameter routes to isolated handlers internally. This is different from a "God Tool" because:
- Each action has its own validation schema (via Zod discriminated union)
- Backend handlers remain separate functions
- The compound tool is a routing layer, not a monolith

---

## 2. Proposed Skill: `mcp-audit`

### Folder Structure

```
.agent/skills/mcp-audit/
├── SKILL.md              # Main instructions (below)
├── scripts/
│   └── audit-manifest.json   # Expected tools, categories, test scenarios
└── resources/
    └── baseline-snapshot.json # Last known-good audit results for regression
```

### SKILL.md Design

```markdown
---
name: MCP Tool Audit
description: >
  Systematic CRUD and functional testing of all Zorivest MCP tools.
  Discovers toolsets, exercises every tool, logs issues, compares against
  baseline, and produces a structured audit report.
---

# MCP Tool Audit Skill

## When to invoke
- After MCP server code changes (`mcp-server/src/`)
- After API route additions/removals (`packages/api/src/`)
- Periodically (weekly / pre-release) via `/mcp-audit` workflow
- When `known-issues.md` references [MCP-TOOLAUDIT]

## Prerequisites
- Backend API running (`uv run fastapi dev packages/api/...`)
- MCP server connected (verify via `zorivest_diagnose`)

## Execution Protocol

### Phase 1: Discovery
1. Call `list_available_toolsets` → record toolset names, tool counts, loaded status
2. For each toolset, call `describe_toolset` → record tool names and descriptions
3. Compare against `audit-manifest.json` baseline:
   - New tools added? → Flag for testing
   - Tools removed? → Flag as regression
   - Tool count mismatch? → Flag for investigation
   - Ghost tools (described but not callable)? → Flag as Issue

### Phase 2: CRUD Testing
For each resource domain that supports CRUD:

#### Accounts
1. `list_accounts` → record count
2. `create_account` (name: "MCP-Audit-{timestamp}", type: BROKER) → record ID
3. `get_account` (ID from step 2) → verify fields match
4. `update_account` (ID, name: "MCP-Audit-Updated") → verify update
5. `record_balance` (ID, balance: 99999) → verify snapshot
6. `archive_account` (ID) → verify is_archived=true
7. `get_confirmation_token` + `delete_account` (ID) → verify deletion
8. `list_accounts` → verify count restored

#### Trades (same pattern with create/delete)
#### Watchlists (same pattern)
#### Email Templates (same pattern)
#### Policies (if safe — use emulator dry-run)

### Phase 3: Functional Testing
For each non-CRUD tool:
1. Call with valid minimal params → expect success or documented error
2. Call with known-bad params → expect structured error (not 500)
3. Record: tool name, HTTP status, response shape, latency

### Phase 4: Regression Detection
1. Load `baseline-snapshot.json` (previous audit results)
2. Compare:
   - Tools that passed before but fail now → **REGRESSION**
   - Tools that failed before and still fail → **KNOWN ISSUE**
   - Tools that failed before but pass now → **FIXED** (update baseline)
   - New tools not in baseline → **NEW** (add to baseline)

### Phase 5: Report Generation
1. Write structured report to `.agent/context/MCP/mcp-tool-audit-report.md`
2. Update `known-issues.md` [MCP-TOOLAUDIT] entry with new findings
3. Update `baseline-snapshot.json` with current results
4. Calculate consolidation score: `current_tools / ideal_tools`

## Cleanup Contract
- Delete ALL test entities created during audit (accounts, trades, watchlists, templates)
- If deletion fails, log as issue and flag for manual cleanup
- Never leave test data in production database

## Output Format
Report must include:
- Scorecard table (tested/passed/failed/partial per category)
- CRUD matrix per resource
- Issues log with severity
- Regression delta from previous audit
- Consolidation score trend
```

---

## 3. Proposed Workflow: `/mcp-audit`

### Workflow File: `.agent/workflows/mcp-audit.md`

```markdown
---
name: MCP Tool Audit
description: Systematic audit of all Zorivest MCP tools for completeness, correctness, and regression detection
trigger: /mcp-audit
---

# MCP Tool Audit Workflow

## Pre-conditions
- [ ] Backend API is running
- [ ] MCP server connected (zorivest_diagnose returns ok)

## Steps

### Step 1: Load Skill
Read `.agent/skills/mcp-audit/SKILL.md` and follow its execution protocol.

### Step 2: Discovery Phase
Follow skill Phase 1. Record toolset inventory.

### Step 3: CRUD Testing
Follow skill Phase 2. Test all CRUD-capable resources.
**Cleanup is mandatory** — delete all test entities before proceeding.

### Step 4: Functional Testing
Follow skill Phase 3. Exercise all non-CRUD tools.

### Step 5: Regression Check
Follow skill Phase 4. Compare against baseline.

### Step 6: Report & Record
Follow skill Phase 5. Write report and update known-issues.

### Step 7: Consolidation Advisory
Calculate: `consolidation_score = current_tool_count / 12`
If score > 3.0, flag in report: "Tool count exceeds 3x ideal. Consolidation recommended."

## Exit Criteria
- [ ] All CRUD resources tested with full lifecycle
- [ ] All functional tools exercised
- [ ] Test data cleaned up (zero residual entities)
- [ ] Report written to `.agent/context/MCP/mcp-tool-audit-report.md`
- [ ] `known-issues.md` updated with new findings
- [ ] Baseline snapshot updated
```

---

## 4. Integration with AGENTS.md

### Add to Workflow Invocation Section

```markdown
- `/mcp-audit` → Read and follow `.agent/workflows/mcp-audit.md`
```

### Add to Skills Section

```markdown
- MCP Tool Audit (p:\zorivest\.agent\skills\mcp-audit\SKILL.md): Systematic CRUD and functional testing of all Zorivest MCP tools. Discovers toolsets, exercises every tool, logs issues, compares against baseline.
```

### Trigger Conditions for Automated Invocation

The audit should be triggered:
1. **Pre-release gate** — before any version bump
2. **Post-MCP-change** — after edits to `mcp-server/src/` or API routes
3. **Weekly cadence** — as part of session discipline (add to session-start checklist if last audit > 7 days)
4. **On-demand** — via `/mcp-audit` slash command

---

## 5. Baseline Snapshot Schema

```json
{
  "version": 1,
  "date": "2026-04-27T22:00:00Z",
  "agent": "Antigravity (Gemini)",
  "backend_version": "0.1.0",
  "toolsets": {
    "core": { "expected_count": 4, "tools": ["get_settings", "update_settings", "zorivest_diagnose", "zorivest_launch_gui"] },
    "discovery": { "expected_count": 4, "tools": ["list_available_toolsets", "describe_toolset", "enable_toolset", "get_confirmation_token"] }
  },
  "results": {
    "list_accounts": { "status": "pass", "http_code": 200, "latency_ms": 45 },
    "create_account": { "status": "pass", "http_code": 200, "latency_ms": 52 },
    "delete_trade": { "status": "fail", "http_code": 500, "error": "Internal Server Error", "issue_id": "MCP-TOOLAUDIT" },
    "list_bank_accounts": { "status": "fail", "http_code": 404, "error": "Not Found", "issue_id": "MCP-TOOLAUDIT" }
  },
  "summary": {
    "total_tools": 74,
    "tested": 65,
    "passed": 54,
    "failed": 7,
    "partial": 4,
    "consolidation_score": 6.17
  }
}
```

---

## 6. Implementation Roadmap

| Phase | Effort | Deliverable |
|-------|--------|-------------|
| **Phase 1** (Now) | 1 hour | Create `audit-manifest.json` baseline from today's audit |
| **Phase 2** (Next session) | 2 hours | Create `SKILL.md` and `mcp-audit.md` workflow files |
| **Phase 3** (After Phase 2) | 1 hour | Wire into `AGENTS.md` workflows section + session-start checklist |
| **Phase 4** (Ongoing) | Per-audit | Run `/mcp-audit` after MCP changes, update baseline |

---

## 7. Evaluation Metrics (Research-Backed)

Per the agentic eval frameworks (hamel.dev, Anthropic):

| Metric | Description | Target |
|--------|-------------|--------|
| **Tool Hit Rate** | % of tools the audit successfully exercises | > 90% |
| **CRUD Coverage** | % of CRUD-capable resources fully lifecycle-tested | 100% |
| **Regression Detection Rate** | % of regressions caught vs escaped | > 95% |
| **Cleanup Rate** | % of test entities cleaned up after audit | 100% |
| **Consolidation Score** | `current_tools / ideal_tools` (lower = better) | < 3.0 |
| **Audit Duration** | Wall-clock time for full audit | < 5 min |
| **False Positive Rate** | % of "failures" that are actually expected (e.g., no API key) | Track, don't target |
