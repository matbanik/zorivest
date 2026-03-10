/**
 * Toolset seed data — populates the ToolsetRegistry with known toolsets.
 *
 * This is a bridge until MEU-42 implements the full authoritative startup
 * flow (--toolsets CLI, ZORIVEST_TOOLSET_CONFIG env var, adaptive client
 * detection). For now, it provides real metadata so discovery tools
 * (list_available_toolsets, describe_toolset) return meaningful data.
 *
 * Canonical inventory: 05-mcp-server.md §5.11 L735-745 (8 toolsets + discovery).
 * Discovery is registered separately via registerDiscoveryTools(), so this
 * file seeds the other 8.
 *
 * Source: 05j-mcp-discovery.md, 05-mcp-server.md §5.11
 * MEU: 41 (mcp-discovery) — bridge for MEU-42 (toolset-registry)
 */

import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import type { ToolsetRegistry, ToolsetDefinition } from "./registry.js";

import { registerTradeTools } from "../tools/trade-tools.js";
import { registerCalculatorTools } from "../tools/calculator-tools.js";
import { registerSettingsTools } from "../tools/settings-tools.js";
import { registerDiagnosticsTools } from "../tools/diagnostics-tools.js";
import { registerAnalyticsTools } from "../tools/analytics-tools.js";

// ── Toolset definitions (canonical: 05-mcp-server.md §5.11 L735-745) ──

const TOOLSET_DEFINITIONS: ToolsetDefinition[] = [
    // ── Always-loaded ──────────────────────────────────────────────────
    {
        name: "core",
        description:
            "Settings, emergency stop/unlock, diagnostics, GUI launch, service tools",
        tools: [
            { name: "get_settings", description: "Read all user settings" },
            {
                name: "update_settings",
                description: "Update a single setting",
            },
            {
                name: "zorivest_diagnose",
                description: "System diagnostics and health check",
            },
            {
                name: "position_size_calculator",
                description: "Calculate position sizing",
            },
            {
                name: "risk_reward_calculator",
                description: "Calculate risk/reward ratio",
            },
        ],
        register: (server: McpServer) => {
            registerSettingsTools(server);
            registerDiagnosticsTools(server);
            registerCalculatorTools(server);
        },
        loaded: true,
        alwaysLoaded: true,
    },

    // ── Default-loaded ─────────────────────────────────────────────────
    {
        name: "trade-analytics",
        description: "Trade CRUD, screenshots, analytics, reports",
        tools: [
            { name: "create_trade", description: "Create a new trade" },
            {
                name: "list_trades",
                description: "List trades with filtering",
            },
            {
                name: "attach_screenshot",
                description: "Attach screenshot to trade",
            },
            {
                name: "get_trade_screenshots",
                description: "List trade screenshots",
            },
            {
                name: "get_screenshot",
                description: "Get screenshot with image data",
            },
            {
                name: "get_analytics_summary",
                description: "Trading performance analytics",
            },
            {
                name: "get_trade_streaks",
                description: "Win/loss streak analysis",
            },
        ],
        register: (server: McpServer) => {
            registerTradeTools(server);
            registerAnalyticsTools(server);
        },
        loaded: true,
        alwaysLoaded: false,
    },
    {
        name: "trade-planning",
        description:
            "Position calculator, trade plans (includes create_trade cross-tagged from 05c)",
        tools: [
            {
                name: "create_trade_plan",
                description: "Create a structured trade plan",
            },
            {
                name: "list_trade_plans",
                description: "List existing trade plans",
            },
            {
                name: "get_trade_plan",
                description: "Get trade plan by ID",
            },
        ],
        register: () => {
            /* MEU-42: trade-planning tools not yet implemented */
        },
        loaded: false,
        alwaysLoaded: false,
    },

    // ── Deferred toolsets ──────────────────────────────────────────────
    {
        name: "market-data",
        description: "Stock quotes, news, SEC filings, ticker search",
        tools: [
            {
                name: "get_stock_quote",
                description: "Get real-time stock quote",
            },
            {
                name: "get_market_news",
                description: "Get market news articles",
            },
            {
                name: "search_tickers",
                description: "Search for stock tickers",
            },
            {
                name: "get_sec_filings",
                description: "Get SEC filings for a company",
            },
        ],
        register: () => {
            /* MEU-42: market-data tools not yet implemented */
        },
        loaded: false,
        alwaysLoaded: false,
    },
    {
        name: "accounts",
        description: "Account management, broker sync, CSV import",
        tools: [
            {
                name: "list_accounts",
                description: "List trading accounts",
            },
            {
                name: "create_account",
                description: "Create a new trading account",
            },
            {
                name: "sync_broker",
                description: "Sync with broker API",
            },
            {
                name: "import_csv",
                description: "Import trades from CSV file",
            },
        ],
        register: () => {
            /* MEU-42: accounts tools not yet implemented */
        },
        loaded: false,
        alwaysLoaded: false,
    },
    {
        name: "scheduling",
        description: "Policy CRUD, pipeline execution, scheduler status",
        tools: [
            {
                name: "create_schedule",
                description: "Create a scheduled policy",
            },
            {
                name: "list_schedules",
                description: "List active schedules",
            },
            {
                name: "run_pipeline",
                description: "Execute a pipeline manually",
            },
        ],
        register: () => {
            /* MEU-42: scheduling tools not yet implemented */
        },
        loaded: false,
        alwaysLoaded: false,
    },
    {
        name: "tax",
        description: "Tax estimation, wash sales, lot management, harvesting",
        tools: [
            {
                name: "estimate_tax",
                description: "Estimate tax liability",
            },
            {
                name: "find_wash_sales",
                description: "Find wash sale violations",
            },
            {
                name: "manage_lots",
                description: "Manage tax lot assignments",
            },
            {
                name: "harvest_losses",
                description: "Identify tax-loss harvesting opportunities",
            },
        ],
        register: () => {
            /* MEU-42: tax tools not yet implemented */
        },
        loaded: false,
        alwaysLoaded: false,
    },
    {
        name: "behavioral",
        description: "Mistake tracking, expectancy, Monte Carlo",
        tools: [
            {
                name: "track_mistakes",
                description: "Track and categorize trading mistakes",
            },
            {
                name: "calculate_expectancy",
                description: "Calculate trading expectancy",
            },
            {
                name: "monte_carlo_sim",
                description: "Run Monte Carlo simulation on trade history",
            },
        ],
        register: () => {
            /* MEU-42: behavioral tools not yet implemented */
        },
        loaded: false,
        alwaysLoaded: false,
    },
];

// ── Seed function ──────────────────────────────────────────────────────

/**
 * Populate the registry with known toolset definitions.
 *
 * Call once at startup before tool registration.
 * MEU-42 will replace this with the full authoritative flow.
 */
export function seedRegistry(registry: ToolsetRegistry): void {
    for (const def of TOOLSET_DEFINITIONS) {
        registry.register(def);
    }
}
