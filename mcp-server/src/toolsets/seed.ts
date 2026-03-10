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
import { registerPlanningTools } from "../tools/planning-tools.js";
import { registerGuiTools } from "../tools/gui-tools.js";
import { registerAccountTools } from "../tools/accounts-tools.js";

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
                name: "zorivest_launch_gui",
                description: "Launch desktop GUI or guide installation",
            },
        ],
        register: (server: McpServer) => {
            registerSettingsTools(server);
            registerDiagnosticsTools(server);
            registerGuiTools(server);
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
                name: "calculate_position_size",
                description: "Calculate position sizing",
            },
            {
                name: "create_trade_plan",
                description: "Create a structured trade plan",
            },
            {
                name: "create_trade",
                description: "Create a new trade (cross-tagged from 05c)",
            },
        ],
        register: (server: McpServer) => {
            registerPlanningTools(server);
            registerCalculatorTools(server);
        },
        loaded: true,
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
        description:
            "Broker sync, identifier resolution, bank/CSV/PDF import, account review",
        tools: [
            { name: "sync_broker", description: "Sync with broker API" },
            { name: "list_brokers", description: "List configured brokers" },
            {
                name: "resolve_identifiers",
                description: "Batch resolve CUSIP/ISIN/SEDOL",
            },
            {
                name: "import_bank_statement",
                description: "Import bank statement file",
            },
            {
                name: "import_broker_csv",
                description: "Import broker trade CSV",
            },
            {
                name: "import_broker_pdf",
                description: "Import broker PDF statement",
            },
            {
                name: "list_bank_accounts",
                description: "List bank accounts with balances",
            },
            {
                name: "get_account_review_checklist",
                description: "Account staleness review checklist",
            },
        ],
        register: (server: McpServer) => {
            registerAccountTools(server);
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
