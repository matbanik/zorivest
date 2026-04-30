/**
 * Adaptive client mode detection.
 *
 * Detects the client's capability level from clientInfo.name or env var,
 * and provides mode-dependent configuration exports.
 *
 * Source: 05-mcp-server.md §5.12 L787-838, §5.13 L846-875
 * MEU: 42 (toolset-registry)
 */

import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";

// ── Types ──────────────────────────────────────────────────────────────

/**
 * Client capability modes:
 * - `anthropic`: Claude clients — full annotation + dynamic loading
 * - `dynamic`:   IDE clients that support tools/list_changed
 * - `static`:    Clients with no dynamic tool support
 */
export type ClientMode = "anthropic" | "dynamic" | "static";

// ── Module state ───────────────────────────────────────────────────────

let currentMode: ClientMode = "static";

// ── Detection ──────────────────────────────────────────────────────────

/** Pattern matchers for clientInfo.name → ClientMode */
const DYNAMIC_CLIENTS = new Set([
    "antigravity",
    "cline",
    "roo-code",
    "gemini-cli",
]);

/**
 * Detect client mode using priority chain:
 * 1. ZORIVEST_CLIENT_MODE env var (override)
 * 2. clientInfo.name pattern matching
 * 3. 'static' safe default (§5.12 L833)
 */
export function detectClientMode(server: McpServer): ClientMode {
    // Priority 1: env var override
    const envMode = process.env.ZORIVEST_CLIENT_MODE;
    if (envMode === "anthropic" || envMode === "dynamic" || envMode === "static") {
        currentMode = envMode;
        return envMode;
    }

    // Priority 2: clientInfo.name
    const clientName = server.server.getClientVersion()?.name;
    if (clientName) {
        // claude-* → anthropic
        if (clientName.startsWith("claude-")) {
            currentMode = "anthropic";
            return "anthropic";
        }
        // known dynamic clients
        if (DYNAMIC_CLIENTS.has(clientName)) {
            currentMode = "dynamic";
            return "dynamic";
        }
    }

    // Priority 3: safe default (cursor, windsurf, unknown)
    currentMode = "static";
    return "static";
}

// ── Response format (AC-5, AC-6) ───────────────────────────────────────

/**
 * Get the response format for the current session.
 * anthropic/dynamic → 'detailed', static → 'concise'
 */
export function getResponseFormat(): "detailed" | "concise" {
    return currentMode === "static" ? "concise" : "detailed";
}

/**
 * Set the response format based on detected mode.
 * Called after detectClientMode() in the oninitialized callback.
 */
export function setResponseFormat(mode: ClientMode): void {
    currentMode = mode;
}

// ── Server instructions (AC-7) ─────────────────────────────────────────

/**
 * Returns comprehensive server instructions covering all client modes.
 * Set at McpServer construction time (SDK _instructions are immutable post-connect).
 */
export function getServerInstructions(): string {
    return `Zorivest MCP Server — Trading Portfolio Management

This server provides toolset-based tool organization for portfolio analytics, trade management, and market data.

## Getting Started
1. Run \`zorivest_system(action:"diagnose")\` to verify backend API connectivity.
2. Run \`zorivest_system(action:"toolsets_list")\` to see loaded and deferred toolsets.
3. Enable deferred toolsets with \`zorivest_system(action:"toolset_enable")\`.

## Available Toolsets
- **core**: Settings, diagnostics, emergency controls (always loaded)
- **trade**: Trade CRUD, screenshot management, analytics reports, trade plans (default)
- **data**: Account management, market data, watchlists, import, tax (deferred)
- **ops**: Pipeline policies, email templates, DB schema discovery, SQL validation (deferred)

## Key Workflows

### Trade Lifecycle
1. \`zorivest_account(action:"list")\` — find or create an account
2. \`zorivest_import(action:"broker_csv")\` — import trades from broker CSV
3. \`zorivest_trade(action:"list")\` — view imported trades
4. \`zorivest_analytics(action:"round_trips")\` — analyze round-trip P&L
5. \`zorivest_report(action:"create")\` — grade trade execution

### Trade Planning
1. \`zorivest_market(action:"search")\` — find ticker
2. \`zorivest_market(action:"quote")\` — get current price
3. \`zorivest_analytics(action:"position_size")\` — calculate position
4. \`zorivest_plan(action:"create")\` — create structured trade plan

### Pipeline Automation
1. \`zorivest_db(action:"step_types")\` — discover available pipeline step types
2. \`zorivest_db(action:"list_tables")\` — discover queryable tables
3. \`zorivest_template(action:"create")\` — create email template
4. \`zorivest_policy(action:"create")\` — create pipeline policy
5. \`zorivest_policy(action:"emulate")\` — test policy logic
6. **User approves policy via GUI** (agents cannot approve policies)
7. \`zorivest_policy(action:"run", dry_run:true)\` — preview report
8. \`zorivest_policy(action:"run", dry_run:false)\` — execute pipeline

## Compound Tools (13 total)
- **zorivest_system** — System operations: diagnostics, settings, discovery, GUI launch, confirmation tokens, email config
- **zorivest_trade** — Trade CRUD and screenshot management
- **zorivest_analytics** — 13 analytics actions: position sizing, round trips, excursion, fees, execution quality, PFOF, expectancy, drawdown, strategy, SQN, cost of free, AI review, options strategy
- **zorivest_report** — Post-trade review reports with setup/execution grades
- **zorivest_plan** — Trade plan management with entry/stop/target levels
- **zorivest_account** — Account CRUD, archive, reassign, balance, checklist
- **zorivest_market** — Market data: quotes, news, search, SEC filings, provider management
- **zorivest_watchlist** — Watchlist CRUD with ticker management
- **zorivest_import** — CSV/PDF import, broker sync, bank statements
- **zorivest_tax** — Tax operations (all 501 Not Implemented — planned for future phase)
- **zorivest_policy** — Pipeline policy lifecycle: create, emulate, approve (GUI-only), run, schedule, history
- **zorivest_template** — Email template CRUD with Jinja2 preview
- **zorivest_db** — DB schema discovery, SQL validation, step types, provider capabilities

## Dynamic Toolset Loading
Use \`zorivest_system(action:"toolsets_list")\` to see all toolsets and their status.
Use \`zorivest_system(action:"toolset_describe")\` to see tools within a specific toolset.
Use \`zorivest_system(action:"toolset_enable")\` to dynamically load additional toolsets during your session.

## Confirmation Workflow
Destructive operations (trade deletion, account deletion, policy deletion, template deletion) require confirmation on annotation-unaware clients. Use \`zorivest_system(action:"confirm_token")\` to obtain a single-use 60-second token, then pass it as \`confirmation_token\` parameter.

## Error Handling
All tools return JSON with \`{ success, data?, error? }\`. Common error codes:
- **404**: Resource not found (invalid ID, ticker, or template name)
- **422**: Validation error (malformed input, missing required fields)
- **501**: Not Implemented (tax tools, some import stubs)
- **503**: External service unavailable (market data provider down)`;
}
