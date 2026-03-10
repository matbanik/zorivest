/**
 * Zorivest MCP Server entry point.
 *
 * Bootstraps the MCP server with StdioServerTransport,
 * registers all tool handlers, and starts listening.
 *
 * Source: 05-mcp-server.md §5.1, §5.7
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";

import { registerTradeTools } from "./tools/trade-tools.js";
import { registerCalculatorTools } from "./tools/calculator-tools.js";
import { registerSettingsTools } from "./tools/settings-tools.js";
import { registerDiagnosticsTools } from "./tools/diagnostics-tools.js";
import { registerAnalyticsTools } from "./tools/analytics-tools.js";
import { registerDiscoveryTools } from "./tools/discovery-tools.js";
import { bootstrapAuth } from "./utils/api-client.js";
import { toolsetRegistry } from "./toolsets/registry.js";
import { seedRegistry } from "./toolsets/seed.js";

async function main(): Promise<void> {
    const server = new McpServer({
        name: "zorivest",
        version: "0.1.0",
    });

    // Seed the toolset registry with known toolset metadata.
    // Bridge until MEU-42 implements full registerToolsForClient() startup.
    seedRegistry(toolsetRegistry);

    // AC-6: Disable dynamic tool loading for static clients.
    // Set ZORIVEST_STATIC_CLIENT=1 (or pass --toolsets via MEU-42) to reject
    // enable_toolset at runtime with guidance to restart with --toolsets flag.
    // Source: 05j-mcp-discovery.md L152 (clientSupportsNotification check)
    if (process.env.ZORIVEST_STATIC_CLIENT) {
        toolsetRegistry.dynamicLoadingEnabled = false;
    }

    // Register all tool handlers
    registerTradeTools(server);
    registerCalculatorTools(server);
    registerSettingsTools(server);
    registerDiagnosticsTools(server);
    registerAnalyticsTools(server);
    registerDiscoveryTools(server);

    // Bootstrap auth with pre-provisioned API key from environment
    const apiKey = process.env.ZORIVEST_API_KEY;
    if (apiKey) {
        try {
            await bootstrapAuth(apiKey);
        } catch (error) {
            console.error(
                "Auth bootstrap failed (tools will not work until API is unlocked):",
                error,
            );
        }
    }

    // Connect via stdio transport
    const transport = new StdioServerTransport();
    await server.connect(transport);
}

main().catch((error) => {
    console.error("MCP server startup failed:", error);
    process.exit(1);
});
