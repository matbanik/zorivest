/**
 * Toolset seed data — populates the ToolsetRegistry with known toolsets.
 *
 * Canonical inventory: 05-mcp-server.md §5.11 L735-745 (9 toolsets including discovery).
 * All toolsets start loaded: false (runtime state, not metadata).
 * All register callbacks return RegisteredToolHandle[] for handle capture.
 *
 * Source: 05j-mcp-discovery.md, 05-mcp-server.md §5.11
 * MEU: 41 (mcp-discovery) + 42 (toolset-registry)
 */

import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import type {
    ToolsetRegistry,
    ToolsetDefinition,
    RegisteredToolHandle,
} from "./registry.js";

import { registerTradeTools } from "../tools/trade-tools.js";
import { registerCalculatorTools } from "../tools/calculator-tools.js";
import { registerSettingsTools } from "../tools/settings-tools.js";
import { registerDiagnosticsTools } from "../tools/diagnostics-tools.js";
import { registerAnalyticsTools } from "../tools/analytics-tools.js";
import { registerPlanningTools } from "../tools/planning-tools.js";
import { registerGuiTools } from "../tools/gui-tools.js";
import { registerAccountTools } from "../tools/accounts-tools.js";
import { registerDiscoveryTools } from "../tools/discovery-tools.js";
import { registerMarketDataTools } from "../tools/market-data-tools.js";

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
        register: (server: McpServer): RegisteredToolHandle[] => [
            ...registerSettingsTools(server),
            ...registerDiagnosticsTools(server),
            ...registerGuiTools(server),
        ],
        loaded: false,
        alwaysLoaded: true,
        isDefault: false,
    },
    {
        name: "discovery",
        description:
            "Meta-tools for listing, describing, and enabling additional toolsets",
        tools: [
            {
                name: "list_available_toolsets",
                description: "List all toolsets and their status",
            },
            {
                name: "describe_toolset",
                description: "Get detailed description of a toolset",
            },
            {
                name: "enable_toolset",
                description: "Dynamically enable a toolset",
            },
            {
                name: "get_confirmation_token",
                description: "Get a confirmation token for destructive operations",
            },
        ],
        register: (server: McpServer): RegisteredToolHandle[] =>
            registerDiscoveryTools(server),
        loaded: false,
        alwaysLoaded: true,
        isDefault: false,
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
        register: (server: McpServer): RegisteredToolHandle[] => [
            ...registerTradeTools(server),
            ...registerAnalyticsTools(server),
        ],
        loaded: false,
        alwaysLoaded: false,
        isDefault: true,
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
        register: (server: McpServer): RegisteredToolHandle[] => [
            ...registerPlanningTools(server),
            ...registerCalculatorTools(server),
        ],
        loaded: false,
        alwaysLoaded: false,
        isDefault: true,
    },

    // ── Deferred toolsets ──────────────────────────────────────────────
    {
        name: "market-data",
        description: "Stock quotes, news, SEC filings, ticker search, provider management",
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
                name: "search_ticker",
                description: "Search for stock tickers",
            },
            {
                name: "get_sec_filings",
                description: "Get SEC filings for a company",
            },
            {
                name: "list_market_providers",
                description: "List all market data providers",
            },
            {
                name: "disconnect_market_provider",
                description: "Remove provider API key and disable",
            },
            {
                name: "test_market_provider",
                description: "Test provider connectivity",
            },
        ],
        register: (server: McpServer): RegisteredToolHandle[] =>
            registerMarketDataTools(server),
        loaded: false,
        alwaysLoaded: false,
        isDefault: false,
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
        register: (server: McpServer): RegisteredToolHandle[] =>
            registerAccountTools(server),
        loaded: false,
        alwaysLoaded: false,
        isDefault: false,
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
        register: () => [],
        loaded: false,
        alwaysLoaded: false,
        isDefault: false,
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
        register: () => [],
        loaded: false,
        alwaysLoaded: false,
        isDefault: false,
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
        register: () => [],
        loaded: false,
        alwaysLoaded: false,
        isDefault: false,
    },
];

// ── Seed function ──────────────────────────────────────────────────────

/**
 * Populate the registry with all 9 toolset definitions.
 * Call once at startup before tool registration.
 */
export function seedRegistry(registry: ToolsetRegistry): void {
    for (const def of TOOLSET_DEFINITIONS) {
        registry.register(def);
    }
}
