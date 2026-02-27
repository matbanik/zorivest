# Handoff: GUI↔MCP Parity Corrections

## Task

- **Date:** 2026-02-21
- **Task slug:** gui-mcp-parity-corrections
- **Owner role:** coder
- **Scope:** Apply corrections for all 9 findings from the GUI-MCP parity critical review.

## Changes Applied

### Critical

| # | Finding | Fix | File(s) |
|---|---------|-----|---------|
| C1 | `log_trade`, `lock_mcp`/`unlock_mcp` naming drift | Replaced with `create_trade`, `zorivest_emergency_stop`/`zorivest_emergency_unlock` | `gui-actions-index.md` |
| C5 | MCP SDK unpinned | Pinned to `^1.26.0`; added SDK compatibility section with migration rules | `dependency-manifest.md`, `05-mcp-server.md` |
| C2 | Scheduling MCP contract split | Rewrote 06e MCP section: removed stale tools (`get_policy`, `approve_policy`, `get_pipeline_runs`), added canonical Phase 9 tools, clarified approval as GUI-only | `06e-gui-scheduling.md` |

### High

| # | Finding | Fix | File(s) |
|---|---------|-----|---------|
| H8 | Scheduler status endpoint `/status` vs `/scheduler/status` | Fixed to canonical `/api/v1/scheduling/scheduler/status` | `06e-gui-scheduling.md` |

### Medium

| # | Finding | Fix | File(s) |
|---|---------|-----|---------|
| M3 | `create_trade_plan` false-ready | Downgraded from ✅ to 🔶 | `input-index.md` |
| M4 | Service lifecycle non-parity undocumented | Added "GUI-only: requires OS privilege escalation" annotations | `gui-actions-index.md` |

### Low

| # | Finding | Fix | File(s) |
|---|---------|-----|---------|
| L6 | Tax MCP phase gating unclear | Added "(pending matrix item 76)" | `gui-actions-index.md` |
| L7 | Log folder semantic difference | Added "(returns content; GUI opens folder)" | `gui-actions-index.md` |
| L9 | Summary stats missing ⛔ count | Added ⛔ Superseded row; separated MCP-only params vs tool calls | `gui-actions-index.md`, `input-index.md` |

## Design Decisions Made

1. **Service start/stop:** Intentionally GUI-only (OS privilege escalation). Documented, not "fixed."
2. **Scheduling approval:** Intentionally GUI-only (human-in-the-loop security gate). Clarified in 06e.
3. **MCP SDK target:** v1.x API surface using `server.tool()` convenience method. `registerTool()` available but not adopted yet.

## Open Items

- `validate.ps1` has a pre-existing parse error on line 118 — needs separate fix
- Scheduling dry-run endpoint consolidated: removed stale `/test` endpoint, unified to `/run` with `dry_run=true`

## Evidence

- All tool name changes cross-verified against `05-mcp-server.md` outputs section
- All scheduling tools cross-verified against `09-scheduling.md` §9.11 canonical definitions
- SDK version verified via web research (npm shows v1.26.0 as of 2026-02-04)
