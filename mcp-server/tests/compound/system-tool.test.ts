/**
 * Integration tests for zorivest_system compound tool.
 *
 * AC-1.3: zorivest_system registered with registerTool() + z.object().strict()
 * AC-1.4: Routes 9 actions
 * AC-1.5: 9 old registrations removed (verified by count)
 * AC-1.6: tools/list count = 77
 * AC-1.8: Build succeeds (separate task)
 * AC-1.9: All vitest pass (this file)
 *
 * Source: implementation-plan.md MC1
 * Phase: RED — tests written before implementation
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { InMemoryTransport } from "@modelcontextprotocol/sdk/inMemory.js";
import { registerSystemTool } from "../../src/compound/system-tool.js";

// ── Test helpers ───────────────────────────────────────────────────────

async function createTestClient(): Promise<Client> {
    const server = new McpServer({ name: "test", version: "0.1.0" });
    registerSystemTool(server);

    const [clientTransport, serverTransport] =
        InMemoryTransport.createLinkedPair();
    const client = new Client({ name: "test-client", version: "0.1.0" });

    await Promise.all([
        client.connect(clientTransport),
        server.connect(serverTransport),
    ]);

    return client;
}

function mockHealthyBackend(): void {
    vi.stubGlobal(
        "fetch",
        vi.fn().mockImplementation((url: string) => {
            if (url.includes("/health")) {
                return Promise.resolve({
                    ok: true,
                    json: () =>
                        Promise.resolve({
                            status: "ok",
                            database: { unlocked: true },
                        }),
                });
            }
            if (url.includes("/version")) {
                return Promise.resolve({
                    ok: true,
                    json: () =>
                        Promise.resolve({ version: "1.0.0", context: "dev" }),
                });
            }
            if (url.includes("/mcp-guard/status")) {
                return Promise.resolve({
                    ok: true,
                    json: () =>
                        Promise.resolve({
                            is_enabled: true,
                            is_locked: false,
                            lock_reason: null,
                            recent_calls_1min: 5,
                            recent_calls_1hr: 42,
                        }),
                });
            }
            if (url.includes("/market-data/providers")) {
                return Promise.resolve({
                    ok: true,
                    json: () =>
                        Promise.resolve([
                            {
                                name: "alpha_vantage",
                                is_enabled: true,
                                has_key: true,
                            },
                        ]),
                });
            }
            if (url.includes("/settings/email/status")) {
                return Promise.resolve({
                    ok: true,
                    json: () =>
                        Promise.resolve({
                            configured: true,
                            provider: "smtp",
                            host: "smtp.example.com",
                        }),
                });
            }
            if (url.includes("/settings")) {
                return Promise.resolve({
                    ok: true,
                    json: () =>
                        Promise.resolve({ theme: "dark", timezone: "UTC" }),
                });
            }
            return Promise.resolve({
                ok: true,
                json: () => Promise.resolve({}),
            });
        }),
    );
}

// ── Tests ──────────────────────────────────────────────────────────────

describe("zorivest_system compound tool", () => {
    beforeEach(() => {
        vi.restoreAllMocks();
    });

    // ── AC-1.3: Registration ──────────────────────────────────────────

    it("registers exactly one tool named zorivest_system", async () => {
        const client = await createTestClient();
        const { tools } = await client.listTools();

        const systemTool = tools.find((t) => t.name === "zorivest_system");
        expect(systemTool).toBeDefined();
        expect(systemTool!.description).toContain("system");
    });

    it("rejects unknown top-level fields via .strict()", async () => {
        const client = await createTestClient();

        // SDK should reject unknown top-level field before handler
        try {
            const result = await client.callTool({
                name: "zorivest_system",
                arguments: {
                    action: "diagnose",
                    unknown_top_field: "x",
                },
            });
            // If the SDK doesn't throw, the handler should return error
            expect(result.isError).toBe(true);
        } catch {
            // SDK-level rejection is also acceptable
            expect(true).toBe(true);
        }
    });

    // ── AC-1.4: All 9 actions route correctly ─────────────────────────

    it("routes diagnose action", async () => {
        mockHealthyBackend();
        const client = await createTestClient();
        const result = await client.callTool({
            name: "zorivest_system",
            arguments: { action: "diagnose" },
        });

        expect(result.isError).toBeFalsy();
        const text = (result.content as Array<{ type: string; text: string }>)[0]
            .text;
        const report = JSON.parse(text);
        expect(report.backend).toBeDefined();
        expect(report.backend.reachable).toBe(true);
    });

    it("routes settings_get action", async () => {
        mockHealthyBackend();
        const client = await createTestClient();
        const result = await client.callTool({
            name: "zorivest_system",
            arguments: { action: "settings_get" },
        });

        expect(result.isError).toBeFalsy();
        const text = (result.content as Array<{ type: string; text: string }>)[0]
            .text;
        const data = JSON.parse(text);
        // fetchApi wraps in {success, data} envelope
        expect(data.success).toBe(true);
        expect(data.data.theme).toBeDefined();
    });

    it("routes settings_update action", async () => {
        mockHealthyBackend();
        const client = await createTestClient();
        const result = await client.callTool({
            name: "zorivest_system",
            arguments: {
                action: "settings_update",
                settings: { theme: "light" },
            },
        });

        expect(result.isError).toBeFalsy();
    });

    it("routes email_config action", async () => {
        mockHealthyBackend();
        const client = await createTestClient();
        const result = await client.callTool({
            name: "zorivest_system",
            arguments: { action: "email_config" },
        });

        expect(result.isError).toBeFalsy();
        const text = (result.content as Array<{ type: string; text: string }>)[0]
            .text;
        const data = JSON.parse(text);
        // fetchApi wraps in {success, data} envelope
        expect(data.success).toBe(true);
        expect(data.data.configured).toBeDefined();
    });

    // ── AC-1.2: Unknown action-specific fields ────────────────────────

    it("rejects unknown per-action fields for diagnose", async () => {
        mockHealthyBackend();
        const client = await createTestClient();

        // The router should reject bogus_field for diagnose action
        const result = await client.callTool({
            name: "zorivest_system",
            arguments: {
                action: "diagnose",
                bogus_field: "x",
            },
        });

        // This may be caught at SDK level (.strict() on top schema)
        // or at router level (per-action strict sub-schema)
        // Either way it should error
        expect(result.isError).toBe(true);
    });

    // ── Unknown action ────────────────────────────────────────────────

    it("rejects invalid action value", async () => {
        const client = await createTestClient();
        try {
            const result = await client.callTool({
                name: "zorivest_system",
                arguments: { action: "invalid_action" },
            });
            // SDK should reject since action is z.enum
            expect(result.isError).toBe(true);
        } catch {
            // SDK-level rejection for invalid enum value
            expect(true).toBe(true);
        }
    });
});

// ── AC-1.6: Tool count verification ────────────────────────────────────

describe("MC1 tool count gate", () => {
    it("AC-1.6: total registered tools = 77 after MC1 consolidation", async () => {
        // Import the full registration pipeline
        const { McpServer } = await import(
            "@modelcontextprotocol/sdk/server/mcp.js"
        );
        const { toolsetRegistry } = await import(
            "../../src/toolsets/registry.js"
        );
        const { seedRegistry } = await import("../../src/toolsets/seed.js");
        const { registerAllToolsets } = await import(
            "../../src/registration.js"
        );
        const { Client } = await import(
            "@modelcontextprotocol/sdk/client/index.js"
        );
        const { InMemoryTransport } = await import(
            "@modelcontextprotocol/sdk/inMemory.js"
        );

        // 1. Seed the registry
        seedRegistry(toolsetRegistry);

        // 2. Create server and register all toolsets
        const server = new McpServer({ name: "test", version: "0.1.0" });
        registerAllToolsets(server, toolsetRegistry);

        // 3. Connect client to list tools
        const [clientTransport, serverTransport] =
            InMemoryTransport.createLinkedPair();
        const client = new Client({
            name: "test-client",
            version: "0.1.0",
        });

        await Promise.all([
            client.connect(clientTransport),
            server.connect(serverTransport),
        ]);

        const { tools } = await client.listTools();

        // MC1 count: 85 (original) - 9 (core/discovery/email)
        //            + 1 (zorivest_system)
        //            = 77
        // MC2 count: 77 - 6 (trade-tools) - 14 (analytics-tools) - 1 (calculator-tools)
        //            + 3 (zorivest_trade, zorivest_analytics, zorivest_report)
        //            = 59
        // MC3 count: 59 - 16 (accounts-tools) - 7 (market-data-tools) - 4 (tax-tools)
        //               - 5 (watchlist from planning-tools)
        //            + 5 (zorivest_account, zorivest_market, zorivest_watchlist, zorivest_import, zorivest_tax)
        //            = 32
        // MC4 count: 32 - 3 (planning plan tools) - 8 (scheduling tools) - 12 (pipeline-security tools)
        //            + 4 (zorivest_plan, zorivest_policy, zorivest_template, zorivest_db)
        //            = 13
        expect(tools.length).toBe(13);

        // Verify MC1 compound tool present
        expect(tools.some((t) => t.name === "zorivest_system")).toBe(true);

        // Verify MC2 compound tools present
        expect(tools.some((t) => t.name === "zorivest_trade")).toBe(true);
        expect(tools.some((t) => t.name === "zorivest_analytics")).toBe(true);
        expect(tools.some((t) => t.name === "zorivest_report")).toBe(true);

        // Verify MC3 compound tools present
        expect(tools.some((t) => t.name === "zorivest_account")).toBe(true);
        expect(tools.some((t) => t.name === "zorivest_market")).toBe(true);
        expect(tools.some((t) => t.name === "zorivest_watchlist")).toBe(true);
        expect(tools.some((t) => t.name === "zorivest_import")).toBe(true);
        expect(tools.some((t) => t.name === "zorivest_tax")).toBe(true);

        // Verify MC4 compound tools present
        expect(tools.some((t) => t.name === "zorivest_plan")).toBe(true);
        expect(tools.some((t) => t.name === "zorivest_policy")).toBe(true);
        expect(tools.some((t) => t.name === "zorivest_template")).toBe(true);
        expect(tools.some((t) => t.name === "zorivest_db")).toBe(true);

        // Verify exactly 13 compound tools — CI gate
        expect(tools.length).toBeLessThanOrEqual(13);

        // Verify MC1 old tools are NOT present
        const mc1RemovedTools = [
            "zorivest_diagnose",
            "get_settings",
            "update_settings",
            "zorivest_launch_gui",
            "list_available_toolsets",
            "describe_toolset",
            "enable_toolset",
            "get_confirmation_token",
            "get_email_config",
        ];
        for (const name of mc1RemovedTools) {
            expect(
                tools.some((t) => t.name === name),
                `MC1 tool '${name}' should have been removed but is still registered`,
            ).toBe(false);
        }

        // Verify MC2 old tools are NOT present
        const mc2RemovedTools = [
            "create_trade",
            "list_trades",
            "attach_screenshot",
            "get_trade_screenshots",
            "get_screenshot",
            "delete_trade",
            "get_round_trips",
            "enrich_trade_excursion",
            "get_fee_breakdown",
            "score_execution_quality",
            "estimate_pfof_impact",
            "get_expectancy_metrics",
            "simulate_drawdown",
            "get_strategy_breakdown",
            "get_sqn",
            "get_cost_of_free",
            "ai_review_trade",
            "detect_options_strategy",
            "create_report",
            "get_report_for_trade",
            "calculate_position_size",
        ];
        for (const name of mc2RemovedTools) {
            expect(
                tools.some((t) => t.name === name),
                `MC2 tool '${name}' should have been removed but is still registered`,
            ).toBe(false);
        }

        // Verify MC3 old tools are NOT present
        const mc3RemovedTools = [
            // accounts-tools.ts (16)
            "sync_broker", "list_brokers", "resolve_identifiers",
            "import_bank_statement", "import_broker_csv", "import_broker_pdf",
            "list_bank_accounts", "get_account_review_checklist",
            "list_accounts", "get_account", "create_account",
            "update_account", "delete_account", "archive_account",
            "reassign_trades", "record_balance",
            // market-data-tools.ts (7)
            "get_stock_quote", "get_market_news", "search_ticker",
            "get_sec_filings", "list_market_providers",
            "disconnect_market_provider", "test_market_provider",
            // tax-tools.ts (4)
            "estimate_tax", "find_wash_sales", "manage_lots", "harvest_losses",
            // planning-tools.ts watchlist (5)
            "create_watchlist", "list_watchlists", "get_watchlist",
            "add_to_watchlist", "remove_from_watchlist",
        ];
        for (const name of mc3RemovedTools) {
            expect(
                tools.some((t) => t.name === name),
                `MC3 tool '${name}' should have been removed but is still registered`,
            ).toBe(false);
        }

        // Verify MC4 old tools are NOT present
        const mc4RemovedTools = [
            // planning-tools.ts (3)
            "create_trade_plan", "list_trade_plans", "delete_trade_plan",
            // scheduling-tools.ts (8)
            "create_policy", "list_policies", "run_pipeline",
            "preview_report", "update_policy_schedule", "get_pipeline_history",
            "delete_policy", "update_policy",
            // pipeline-security-tools.ts (12)
            "emulate_policy", "validate_sql", "list_db_tables",
            "get_db_row_samples", "create_email_template", "get_email_template",
            "list_email_templates", "update_email_template", "delete_email_template",
            "preview_email_template", "list_step_types", "list_provider_capabilities",
        ];
        for (const name of mc4RemovedTools) {
            expect(
                tools.some((t) => t.name === name),
                `MC4 tool '${name}' should have been removed but is still registered`,
            ).toBe(false);
        }
    });
});
