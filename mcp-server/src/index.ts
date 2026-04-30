/**
 * Zorivest MCP Server entry point.
 *
 * Bootstraps the MCP server with StdioServerTransport using
 * pre-connect-all + post-connect-filter startup strategy:
 * 1. Seed registry with all 9 toolset definitions
 * 2. Parse CLI for toolset selection
 * 3. Build McpServer with comprehensive instructions
 * 4. Register ALL toolsets pre-connect (triggers registerCapabilities once)
 * 5. Set oninitialized callback for post-connect filtering
 * 6. Connect transport
 * 7. (async) oninitialized fires → detect mode, filter tools, set flags
 *
 * Source: 05-mcp-server.md §5.1, §5.7, §5.14
 * MEU: 42 (toolset-registry)
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";

import { parseToolsets } from "./cli.js";
import {
    detectClientMode,
    getServerInstructions,
    setResponseFormat,
} from "./client-detection.js";
import { registerAllToolsets, applyModeFilter } from "./registration.js";
import { setConfirmationMode } from "./middleware/confirmation.js";
import { bootstrapAuth } from "./utils/api-client.js";
import { toolsetRegistry } from "./toolsets/registry.js";
import { seedRegistry } from "./toolsets/seed.js";

async function main(): Promise<void> {
    // 1. Seed registry with all 4 toolset definitions (core, trade, data, ops)
    seedRegistry(toolsetRegistry);

    // 2. Parse CLI for toolset selection
    const selection = parseToolsets();

    // 3. Build McpServer with comprehensive instructions
    const server = new McpServer(
        {
            name: "zorivest",
            version: "0.1.0",
        },
        {
            instructions: getServerInstructions(),
        },
    );

    // 4. Pre-connect registration: register ALL toolsets (all enabled by default)
    //    Stores RegisteredTool handles in registry for post-connect filtering
    registerAllToolsets(server, toolsetRegistry);

    // 5. Set oninitialized callback for post-connect filtering
    //    Server-side ordering guarantee: JS event loop ensures this callback
    //    completes before any tools/list request is processed (SDK-sourced)
    server.server.oninitialized = () => {
        const mode = detectClientMode(server);
        applyModeFilter(toolsetRegistry, mode, selection);
        setResponseFormat(mode);
        setConfirmationMode(mode);
    };

    // 6. Connect transport
    const transport = new StdioServerTransport();
    await server.connect(transport);

    // 7. Bootstrap auth with pre-provisioned API key from environment
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
}

main().catch((error) => {
    console.error("MCP server startup failed:", error);
    process.exit(1);
});
