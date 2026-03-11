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
- **discovery**: Meta-tools for listing, describing, and enabling additional toolsets (always loaded)
- **trade-analytics**: Trade CRUD, screenshot management, analytics reports
- **trade-planning**: Scenario analysis, strategy backtesting
- **market-data**: Real-time market feeds, historical data
- **accounts**: Broker account management, portfolio sync
- **scheduling**: Automated task scheduling
- **tax**: Tax estimation, wash sale detection, lot management
- **behavioral**: Trading psychology analysis, pattern detection

## Dynamic Toolset Loading
Use \`list_available_toolsets\` to see all toolsets and their status.
Use \`describe_toolset\` to see tools within a specific toolset.
Use \`enable_toolset\` to dynamically load additional toolsets during your session.

## Confirmation Workflow
Destructive operations (emergency stop, trade creation, broker sync) require confirmation on annotation-unaware clients. Use \`get_confirmation_token\` to obtain a token, then pass it as \`confirmation_token\` parameter.`;
}
