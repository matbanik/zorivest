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

## Available Toolsets
- **core**: Settings, diagnostics, emergency controls (always loaded)
- **trade**: Trade CRUD, screenshot management, analytics reports, trade plans (default)
- **data**: Account management, market data, watchlists, import, tax (deferred)
- **ops**: Pipeline policies, email templates, DB schema discovery, SQL validation (deferred)

## Compound Tools (13 total)
- **zorivest_system** — System operations — diagnostics, settings, discovery, GUI launch, confirmation tokens, and email configuration. Actions: diagnose, settings_get, settings_update, confirm_token, toolsets_list, toolset_describe, toolset_enable, launch_gui, email_config
- **zorivest_trade** — Trade management — create, list, delete trades; attach/list/get screenshots. Actions: create, list, delete, screenshot_attach, screenshot_list, screenshot_get
- **zorivest_analytics** — Trade analytics — position sizing, round trips, excursion analysis, fee breakdown, execution quality, PFOF impact, expectancy, drawdown simulation, strategy breakdown, SQN, cost of free, AI trade review, options strategy detection. Actions: position_size, round_trips, excursion, fees, execution_quality, pfof, expectancy, drawdown, strategy, sqn, cost_of_free, ai_review, options_strategy
- **zorivest_report** — Post-trade review reports — create and retrieve trade reports with setup/execution grades, emotional state tracking, and lessons learned. Actions: create, get_for_trade
- **zorivest_plan** — Trade plan management — create structured plans, list with pagination, delete plans. Actions: create, list, delete
- **zorivest_account** — Account management — list, get, create, update, delete, archive, reassign trades, record balance, review checklist. Actions: list, get, create, update, delete, archive, reassign, balance, checklist
- **zorivest_market** — Market data — stock quotes, news, ticker search, SEC filings, provider management. Actions: quote, news, search, sec_filings, providers, disconnect_provider, test_provider
- **zorivest_watchlist** — Watchlist management — create, list, get, add/remove tickers. Actions: create, list, get, add_ticker, remove_ticker
- **zorivest_import** — Data import — CSV/PDF broker imports, bank statements, broker sync, broker listing, identifier resolution, bank account listing. Actions: broker_csv, broker_pdf, bank_statement, sync_broker, list_brokers, resolve_identifiers, list_bank_accounts
- **zorivest_tax** — Tax operations — estimate liability, find wash sales, manage lots, identify harvesting opportunities. (All actions: 501 Not Implemented) Actions: estimate, wash_sales, manage_lots, harvest
- **zorivest_policy** — Pipeline policy management — create, list, run, preview report, update schedule, view run history, delete, update content, emulate. Actions: create, list, run, preview, update_schedule, get_history, delete, update, emulate
- **zorivest_template** — Email template management — create, get, list, update, delete, preview rendered output. Actions: create, get, list, update, delete, preview
- **zorivest_db** — Database discovery and validation — validate SQL queries, list queryable tables, get sample rows, list pipeline step types, list market data provider capabilities. Actions: validate_sql, list_tables, row_samples, step_types, provider_capabilities

## Dynamic Toolset Loading
Use \`zorivest_system(action:"toolsets_list")\` to see all toolsets and their status.
Use \`zorivest_system(action:"toolset_describe")\` to see tools within a specific toolset.
Use \`zorivest_system(action:"toolset_enable")\` to dynamically load additional toolsets during your session.

## Confirmation Workflow
Destructive operations (trade deletion, account deletion, policy deletion, template deletion) require confirmation on annotation-unaware clients. Use \`zorivest_system(action:"confirm_token")\` to obtain a token, then pass it as \`confirmation_token\` parameter.`;
}
