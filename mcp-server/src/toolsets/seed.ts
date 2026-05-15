/**
 * Toolset seed data — populates the ToolsetRegistry with known toolsets.
 *
 * MC4 restructure: 4 toolsets (core, trade, data, ops).
 * All 85 original tools are preserved as compound tool actions across 13 tools.
 *
 * Source: implementation-plan.md MC4 (AC-4.15)
 * Phase: P2.5f (MCP Tool Consolidation)
 */

import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import type {
    ToolsetRegistry,
    ToolsetDefinition,
    RegisteredToolHandle,
} from "./registry.js";

// MC1 compound tool
import { registerSystemTool } from "../compound/system-tool.js";
// MC2 compound tools
import { registerTradeTool } from "../compound/trade-tool.js";
import { registerAnalyticsTool } from "../compound/analytics-tool.js";
import { registerReportTool } from "../compound/report-tool.js";
// MC3 compound tools
import { registerAccountTool } from "../compound/account-tool.js";
import { registerMarketTool } from "../compound/market-tool.js";
import { registerWatchlistTool } from "../compound/watchlist-tool.js";
import { registerImportTool } from "../compound/import-tool.js";
import { registerTaxTool } from "../compound/tax-tool.js";
// MC4 compound tools
import { registerPlanTool } from "../compound/plan-tool.js";
import { registerPolicyTool } from "../compound/policy-tool.js";
import { registerTemplateTool } from "../compound/template-tool.js";
import { registerDbTool } from "../compound/db-tool.js";
// MC4: Resources only — tool registrations removed
import { registerSchedulingResources } from "../tools/scheduling-tools.js";
import { registerPipelineSecurityResources } from "../tools/pipeline-security-tools.js";

// ── Toolset definitions (MC4: 4 toolsets, 13 compound tools) ───────────

export const TOOLSET_DEFINITIONS: ToolsetDefinition[] = [
    // ── core (always loaded) ──────────────────────────────────────────
    {
        name: "core",
        description:
            "System operations — diagnostics, settings, discovery, GUI launch, " +
            "confirmation tokens, and email configuration (zorivest_system compound tool)",
        tools: [
            { name: "zorivest_system", description: "System operations compound tool (9 actions)" },
        ],
        register: (server: McpServer): RegisteredToolHandle[] =>
            registerSystemTool(server),
        loaded: false,
        alwaysLoaded: true,
        isDefault: false,
    },

    // ── trade (default loaded) ────────────────────────────────────────
    {
        name: "trade",
        description:
            "Trade CRUD, screenshots, analytics, reports, position sizing " +
            "(zorivest_trade, zorivest_analytics, zorivest_report compound tools)",
        tools: [
            { name: "zorivest_trade", description: "Trade management compound tool (6 actions)" },
            { name: "zorivest_analytics", description: "Trade analytics compound tool (13 actions)" },
            { name: "zorivest_report", description: "Post-trade report compound tool (2 actions)" },
        ],
        register: (server: McpServer): RegisteredToolHandle[] => [
            ...registerTradeTool(server),
            ...registerAnalyticsTool(server),
            ...registerReportTool(server),
        ],
        loaded: false,
        alwaysLoaded: false,
        isDefault: true,
    },

    // ── data (deferred) ───────────────────────────────────────────────
    {
        name: "data",
        description:
            "Account CRUD, market data, watchlists, import, tax operations " +
            "(zorivest_account, zorivest_market, zorivest_watchlist, zorivest_import, zorivest_tax compound tools)",
        tools: [
            { name: "zorivest_account", description: "Account management compound tool (9 actions)" },
            { name: "zorivest_market", description: "Market data compound tool (7 actions)" },
            { name: "zorivest_watchlist", description: "Watchlist management compound tool (5 actions)" },
            { name: "zorivest_import", description: "Data import compound tool (7 actions)" },
            { name: "zorivest_tax", description: "Tax operations compound tool (8 actions)" },
        ],
        register: (server: McpServer): RegisteredToolHandle[] => [
            ...registerAccountTool(server),
            ...registerMarketTool(server),
            ...registerWatchlistTool(server),
            ...registerImportTool(server),
            ...registerTaxTool(server),
        ],
        loaded: false,
        alwaysLoaded: false,
        isDefault: false,
    },

    // ── ops (deferred) ────────────────────────────────────────────────
    {
        name: "ops",
        description:
            "Pipeline policies, email templates, DB schema discovery, SQL validation, trade plans " +
            "(zorivest_policy, zorivest_template, zorivest_db, zorivest_plan compound tools)",
        tools: [
            { name: "zorivest_policy", description: "Pipeline policy management compound tool (9 actions)" },
            { name: "zorivest_template", description: "Email template management compound tool (6 actions)" },
            { name: "zorivest_db", description: "DB discovery and validation compound tool (5 actions)" },
            { name: "zorivest_plan", description: "Trade plan management compound tool (3 actions)" },
        ],
        register: (server: McpServer): RegisteredToolHandle[] => {
            // Resources remain registered alongside compound tools
            registerSchedulingResources(server);
            registerPipelineSecurityResources(server);
            return [
                ...registerPolicyTool(server),
                ...registerTemplateTool(server),
                ...registerDbTool(server),
                ...registerPlanTool(server),
            ];
        },
        loaded: false,
        alwaysLoaded: false,
        isDefault: false,
    },
];

// ── Seed function ──────────────────────────────────────────────────────

/**
 * Populate the registry with all toolset definitions.
 * Call once at startup before tool registration.
 *
 * MC4: Restructured from 10 → 4 toolsets (core, trade, data, ops).
 * All 85 original tools preserved as compound actions across 13 compound tools.
 */
export function seedRegistry(registry: ToolsetRegistry): void {
    for (const def of TOOLSET_DEFINITIONS) {
        registry.register(def);
    }
}
