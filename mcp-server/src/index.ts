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
import { bootstrapAuth } from "./utils/api-client.js";

async function main(): Promise<void> {
    const server = new McpServer({
        name: "zorivest",
        version: "0.1.0",
    });

    // Register all tool handlers
    registerTradeTools(server);
    registerCalculatorTools(server);
    registerSettingsTools(server);
    registerDiagnosticsTools(server);
    registerAnalyticsTools(server);

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
