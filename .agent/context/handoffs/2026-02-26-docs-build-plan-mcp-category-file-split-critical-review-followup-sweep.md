# Follow-up Sweep — MCP Category File Split (Docs Build Plan)

Date: 2026-02-26  
Purpose: Re-review after corrective edits to confirm previous findings were addressed and identify any new mistakes introduced during fixes.

## Validation Snapshot

- Category files and tool catalog are now aligned at **64 tools** (`50 Specified + 12 Planned + 2 Future`).
- `05-mcp-server.md` is now a true hub/shared-infrastructure file (tool blocks removed).
- `08/09/10` all now mark category files as the authoritative MCP spec location.
- `mcp-planned-readiness.md` is substantially corrected (category ownership + 12-tool planned count).

## Remaining Findings (Severity Ordered)

### 1. High — `mcp-tool-index` Reference Map is still stale and now internally inconsistent with the corrected catalog

The tool catalog has been updated for the renames/splits, but the reference map was not regenerated.

Evidence:
- Reference map starts at `docs/build-plan/mcp-tool-index.md:104`.
- Catalog includes renamed/split tools:
  - `get_account_review_checklist` at `docs/build-plan/mcp-tool-index.md:72`
  - `get_quarterly_estimate` at `docs/build-plan/mcp-tool-index.md:77`
  - `record_quarterly_tax_payment` at `docs/build-plan/mcp-tool-index.md:78`
- Reference map still uses old headings:
  - `start_account_review` at `docs/build-plan/mcp-tool-index.md:540`
  - `quarterly_estimate` at `docs/build-plan/mcp-tool-index.md:562`
- Sweep check result:
  - catalog tools = **64**
  - reference-map headings = **63**
  - missing from map = `get_account_review_checklist`, `get_quarterly_estimate`, `record_quarterly_tax_payment`
  - extra stale map headings = `start_account_review`, `quarterly_estimate`

Impact:
- Agent-facing reference navigation is now inaccurate even though the catalog rows are correct.
- Future readers may follow renamed/deleted tool names.

### 2. High — `mcp-tool-index` Reference Map contains broken line references to the old monolithic `05-mcp-server.md`

The map still points to historical line numbers from the old large `05-mcp-server.md`, but the file is now a 764-line hub.

Evidence (examples):
- `docs/build-plan/mcp-tool-index.md:498` references `docs/build-plan/05-mcp-server.md:1609`
- `docs/build-plan/mcp-tool-index.md:520` references `docs/build-plan/05-mcp-server.md:1300`
- `docs/build-plan/mcp-tool-index.md:521` references `docs/build-plan/05-mcp-server.md:1543`
- `docs/build-plan/mcp-tool-index.md:522` references `docs/build-plan/05-mcp-server.md:1609`
- `docs/build-plan/05-mcp-server.md` totals/structure updated in hub table (`docs/build-plan/05-mcp-server.md:25`) and outputs (`docs/build-plan/05-mcp-server.md:741`)

Sweep check result:
- **103 out-of-range references**, all to `docs/build-plan/05-mcp-server.md`

Impact:
- Click-through references are broken.
- This undermines the stated “agent-facing” reliability of the index.

### 3. Medium — `mcp-tool-index` planned-tool catalog notes are stale for tools that now have draft `server.tool(...)` specs in category files

Several catalog notes still describe these tools as lacking MCP schema/tool blocks, but category files now contain draft registrations.

Evidence:
- Stale notes in catalog:
  - `create_report` row at `docs/build-plan/mcp-tool-index.md:69`
  - `get_report_for_trade` row at `docs/build-plan/mcp-tool-index.md:70`
  - `create_trade_plan` row at `docs/build-plan/mcp-tool-index.md:71`
- Category-file draft specs now exist:
  - `create_report` at `docs/build-plan/05c-mcp-trade-analytics.md:435`
  - `get_report_for_trade` at `docs/build-plan/05c-mcp-trade-analytics.md:475`
  - `create_trade_plan` at `docs/build-plan/05d-mcp-trade-planning.md:43`
- Readiness doc also now acknowledges category-file draft authority (`docs/build-plan/mcp-planned-readiness.md:5`)

Impact:
- Lower severity than the reference-map issue, but still misleading to readers planning implementation.

### 4. Low — `create_report` draft in `05c` still lacks explicit failure handling / standardized error signaling, while nearby tools were improved

`get_report_for_trade` and scheduling tools now use `isError: true`, but `create_report` still returns success-shape text unconditionally after `fetch`.

Evidence:
- `create_report` section starts at `docs/build-plan/05c-mcp-trade-analytics.md:435` and does not include a `!res.ok` failure path in the draft handler.
- `get_report_for_trade` does include failure signaling with `isError: true` at `docs/build-plan/05c-mcp-trade-analytics.md:489`
- Readiness doc explicitly flags this gap for `create_report` at `docs/build-plan/mcp-planned-readiness.md:28`

Impact:
- Minor compared to the index defects, but still a contract-quality gap in an otherwise improved set of drafts.

## Fixed Since Last Review (Confirmed)

These prior findings appear resolved in the current docs state:

- `05-mcp-server.md` is now clearly hub-only:
  - hub-only statement at `docs/build-plan/05-mcp-server.md:9`
  - updated totals table at `docs/build-plan/05-mcp-server.md:25`
  - only remaining `server.tool(...)` mentions are SDK compatibility text (not tool blocks)
- Authoritative spec callouts now exist in all source phases:
  - `docs/build-plan/08-market-data.md:567`
  - `docs/build-plan/09-scheduling.md:2653`
  - `docs/build-plan/10-service-daemon.md:742`
- `mcp-planned-readiness.md` ownership and counts updated:
  - 12 planned tools at `docs/build-plan/mcp-planned-readiness.md:3`
  - category-file authority note at `docs/build-plan/mcp-planned-readiness.md:5`
  - renamed/split tools present (e.g., `get_account_review_checklist`, `get_quarterly_estimate`, `record_quarterly_tax_payment`) at `docs/build-plan/mcp-planned-readiness.md:63`, `docs/build-plan/mcp-planned-readiness.md:128`, `docs/build-plan/mcp-planned-readiness.md:141`
- Tax tool split and destructive confirmations applied:
  - `get_quarterly_estimate` at `docs/build-plan/05h-mcp-tax.md:180`
  - `record_quarterly_tax_payment` with confirmation at `docs/build-plan/05h-mcp-tax.md:220` and `docs/build-plan/05h-mcp-tax.md:233`
  - `harvest_losses` now uses GET and matches dependency note at `docs/build-plan/05h-mcp-tax.md:257` and `docs/build-plan/05h-mcp-tax.md:294`
  - `disconnect_market_provider` confirmation added at `docs/build-plan/05e-mcp-market-data.md:150`, `docs/build-plan/05e-mcp-market-data.md:156`
  - `zorivest_service_restart` confirmation added at `docs/build-plan/05b-mcp-zorivest-diagnostics.md:207`
- Several `isError` improvements landed:
  - scheduling errors at `docs/build-plan/05g-mcp-scheduling.md:63`, `docs/build-plan/05g-mcp-scheduling.md:122`, `docs/build-plan/05g-mcp-scheduling.md:182`
  - `get_report_for_trade` error path at `docs/build-plan/05c-mcp-trade-analytics.md:490`

## Recommended Next Fix Order

1. Regenerate `mcp-tool-index` reference map from current docs (highest priority).
2. Add a validation check that detects:
   - catalog/reference-map heading mismatches
   - out-of-range line references
3. Refresh stale planned-tool notes in `mcp-tool-index` rows (`create_report`, `get_report_for_trade`, `create_trade_plan`).
4. Add explicit failure handling / `isError: true` pattern to `create_report` draft in `05c`.

