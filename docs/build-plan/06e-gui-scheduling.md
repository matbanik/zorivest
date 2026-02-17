# Phase 6e: GUI — Scheduling & Pipelines

> Part of [Phase 6: GUI](06-gui.md) | Prerequisites: [Phase 4](04-rest-api.md) | Outputs: [Phase 7](07-distribution.md)

---

## Goal

Build the scheduling and pipeline management surface. This system is **primarily MCP-driven** — AI agents create and manage JSON policy documents that define data aggregation, report generation, and email delivery pipelines. The GUI provides a read/edit view for inspection, manual overrides, and pipeline monitoring.

> **Design Note**: Scheduled jobs use **policy files** — fully generated JSON documents processed by the scheduling engine. The AI agent (via MCP) is the primary author of these policies, composing the logic that aggregates data from APIs, copies data into report tables, applies email templates, and defines recipients. The GUI is the secondary interface for human review and manual triggering.

---

## Schedule Management Page

> **Source**: [Input Index §17](input-index.md). Follows the list+detail split layout pattern from the [Notes Architecture](../_notes-architecture.md).

### Layout

```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│  Scheduled Jobs                                                [+ New Schedule]     │
├──────────────────────────────────┬───────────────────────────────────────────────────┤
│  SCHEDULE LIST (left pane)       │  SCHEDULE DETAIL (right pane)                    │
│  ┌────────────────────────────┐  │                                                  │
│  │ ✅ Daily Performance Report│◄─│─ selected                                       │
│  │    0 8 * * 1-5 (Weekdays)  │  │  ── Schedule Info ────────────────────────       │
│  │    Next: Mon 8:00 AM       │  │                                                  │
│  │                            │  │  Name:    [ Daily Performance Report   ]         │
│  │ ✅ Weekly Portfolio Sync   │  │  Enabled: [■]                                    │
│  │    0 18 * * 5 (Fridays)    │  │                                                  │
│  │    Next: Fri 6:00 PM       │  │  ── Scheduling Trigger ──────────────────       │
│  │                            │  │                                                  │
│  │ ⏸️ Monthly Tax Summary    │  │  Cron Expression: [ 0 8 * * 1-5       ]          │
│  │    0 9 1 * * (1st of month)│  │  ⏰ "Every weekday at 8:00 AM"                   │
│  │    Next: (paused)          │  │  Timezone: [ America/New_York ▼ ]                │
│  │                            │  │  Next Run: Mon Jan 20, 2025 8:00 AM EST         │
│  │ ✅ Data Refresh            │  │                                                  │
│  │    */15 * * * * (every 15m)│  │  ── Execution Options ───────────────────       │
│  │    Next: 14:45             │  │                                                  │
│  └────────────────────────────┘  │  Skip if running: [■]                            │
│                                  │  Misfire grace:   [ 3600    ] seconds             │
│  Legend:                         │                                                  │
│  ✅ = Enabled                    │  ── Pipeline Policy (JSON) ───────────────       │
│  ⏸️ = Paused                    │                                                  │
│                                  │  ┌──────────────────────────────────────────┐   │
│                                  │  │ {                                        │   │
│                                  │  │   "version": "1.0",                      │   │
│                                  │  │   "pipeline": [                          │   │
│                                  │  │     {                                    │   │
│                                  │  │       "step": "fetch_market_data",       │   │
│                                  │  │       "tickers": ["SPY","QQQ","AAPL"],   │   │
│                                  │  │       "provider": "alpha_vantage"        │   │
│                                  │  │     },                                   │   │
│                                  │  │     {                                    │   │
│                                  │  │       "step": "aggregate_positions",     │   │
│                                  │  │       "account_ids": ["DU123","U456"],   │   │
│                                  │  │       "output_table": "daily_report"     │   │
│                                  │  │     },                                   │   │
│                                  │  │     {                                    │   │
│                                  │  │       "step": "render_template",         │   │
│                                  │  │       "template": "daily_performance",   │   │
│                                  │  │       "format": "html"                   │   │
│                                  │  │     },                                   │   │
│                                  │  │     {                                    │   │
│                                  │  │       "step": "send_email",              │   │
│                                  │  │       "recipients": [                    │   │
│                                  │  │         "user@example.com"               │   │
│                                  │  │       ],                                 │   │
│                                  │  │       "subject": "Daily Performance"     │   │
│                                  │  │     }                                    │   │
│                                  │  │   ]                                      │   │
│                                  │  │ }                                        │   │
│                                  │  └──────────────────────────────────────────┘   │
│                                  │  (JSON editor with syntax highlighting)          │
│                                  │                                                  │
│                                  │  ── Actions ──────────────────────────────       │
│                                  │                                                  │
│                                  │  [Save]  [Test Run]  [Run Now]  [Delete]         │
│                                  │                                                  │
├──────────────────────────────────┴───────────────────────────────────────────────────┤
│  ── Pipeline Run History ────────────────────────────────────────────────────       │
│                                                                                      │
│  ┌──────────────────┬──────────┬──────────┬──────────────────────────────────────┐  │
│  │ Timestamp        │ Status   │ Duration │ Details                              │  │
│  ├──────────────────┼──────────┼──────────┼──────────────────────────────────────┤  │
│  │ Jan 17 08:00 AM  │ ✅ OK    │ 12.3s    │ 3 steps completed, email sent       │  │
│  │ Jan 16 08:00 AM  │ ✅ OK    │ 11.8s    │ 3 steps completed, email sent       │  │
│  │ Jan 15 08:00 AM  │ ❌ FAIL  │ 4.1s     │ Step 1 failed: API rate limit       │  │
│  │ Jan 14 08:00 AM  │ ✅ OK    │ 13.0s    │ 3 steps completed, email sent       │  │
│  └──────────────────┴──────────┴──────────┴──────────────────────────────────────┘  │
│                                                                                      │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

### Schedule List Card Fields

Each item in the left pane shows:
- Enabled/paused icon (✅ or ⏸️)
- Schedule name
- Cron expression in parentheses (human-readable)
- Next run time (or "paused")

### Schedule Detail Fields

| Field | Type | Source | Notes |
|-------|------|--------|-------|
| `schedule_name` | `text` | user input or MCP | Human-readable name |
| `enabled` | `toggle` | user input | Active / paused |
| `cron_expression` | `text` | user input or MCP | 5-field cron with live human-readable preview |
| `timezone` | `select` | dropdown | Default UTC, common US/EU timezones |
| `skip_if_running` | `checkbox` | user input | Prevent overlapping runs |
| `misfire_grace` | `number` | user input | Grace period in seconds (default 3600) |
| `policy` | `code editor` | MCP-generated JSON | Full pipeline policy — syntax-highlighted JSON textarea |

### Pipeline Policy Structure

The policy is a JSON document with a `pipeline` array of steps. Each step has a `step` type and step-specific parameters. The scheduling engine processes steps sequentially.

> **Future Work**: The exact step types, their parameters, and the scheduling engine implementation need further research and detailing. The current design provides the GUI surface for viewing and editing policies.

#### Known Step Types (Initial)

| Step Type | Purpose | Key Parameters |
|-----------|---------|----------------|
| `fetch_market_data` | Pull market data from providers | `tickers`, `provider`, `data_type` |
| `aggregate_positions` | Query trades/balances into report table | `account_ids`, `output_table`, `date_range` |
| `run_query` | Execute arbitrary SQL on report tables | `query`, `output_table` |
| `render_template` | Apply email template to report data | `template`, `format` (html/text) |
| `send_email` | Send rendered report via SMTP | `recipients`, `subject`, `attach_csv` |

### Action Buttons

| Button | Behavior |
|--------|----------|
| **Save** | Persists schedule config + policy to database |
| **Test Run** | Executes the pipeline in dry-run mode (no email sent, results logged) |
| **Run Now** | Triggers immediate pipeline execution (sends email if configured) |
| **Delete** | Removes the schedule (with confirmation dialog) |

### Cron Expression Preview

The cron field includes a live human-readable preview using a simple cron parser:

| Cron | Preview |
|------|---------|
| `0 8 * * 1-5` | Every weekday at 8:00 AM |
| `0 18 * * 5` | Every Friday at 6:00 PM |
| `0 9 1 * *` | 1st of every month at 9:00 AM |
| `*/15 * * * *` | Every 15 minutes |

### Run History Table

| Column | Description |
|--------|-------------|
| Timestamp | When the run started |
| Status | ✅ OK / ❌ FAIL / ⏳ Running |
| Duration | Total execution time |
| Details | Summary of steps completed / error message |

Clicking a failed run expands to show the full error traceback and which pipeline step failed.

---

## MCP-First Design

The scheduling system is designed for **MCP-first interaction**. The GUI is the secondary interface.

### MCP Tools (defined in [Phase 5](05-mcp-server.md))

| Tool | Description |
|------|-------------|
| `create_schedule` | Create a new scheduled job with policy |
| `update_schedule` | Update schedule config or policy |
| `list_schedules` | List all schedules with status |
| `run_pipeline_now` | Trigger immediate pipeline execution |
| `get_pipeline_runs` | Get run history for a schedule |
| `delete_schedule` | Remove a scheduled job |

### Typical MCP Workflow

1. AI agent researches what data the user wants in their daily report
2. Agent composes a pipeline policy JSON with appropriate steps
3. Agent calls `create_schedule` with the policy and cron expression
4. User can review/edit the policy in the GUI if needed
5. Pipeline runs on schedule, agent can monitor via `get_pipeline_runs`

### REST Endpoints Consumed

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/api/v1/schedules` | List all schedules |
| `POST` | `/api/v1/schedules` | Create schedule |
| `GET` | `/api/v1/schedules/{id}` | Get schedule detail + policy |
| `PUT` | `/api/v1/schedules/{id}` | Update schedule |
| `DELETE` | `/api/v1/schedules/{id}` | Delete schedule |
| `POST` | `/api/v1/schedules/{id}/run` | Trigger immediate run |
| `POST` | `/api/v1/schedules/{id}/test` | Dry-run (no side effects) |
| `GET` | `/api/v1/schedules/{id}/runs` | Get run history |

---

## Exit Criteria

- Schedule list displays all jobs with enabled/paused status and next run time
- Cron expression field shows live human-readable preview
- Policy JSON editor renders with syntax highlighting
- Test Run executes pipeline in dry-run mode
- Run Now triggers immediate execution
- Run history table shows status, duration, and expandable error details
- MCP tools can create/update/trigger schedules end-to-end

## Outputs

- React components: `SchedulePage`, `ScheduleDetailPanel`, `PipelineRunHistory`, `CronPreview`
- JSON policy editor with syntax highlighting (Monaco or CodeMirror lite)
- Pipeline run history table with expandable error details
- Schedule CRUD consuming REST endpoints
- MCP tool integration for policy authoring workflow
