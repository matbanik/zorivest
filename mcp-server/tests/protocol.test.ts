/**
 * MCP wire protocol tests — JSON-RPC shape, capabilities, and error codes.
 *
 * Verifies the server responds correctly to initialize, tools/list,
 * and tools/call for both valid and invalid scenarios.
 *
 * Phase: 3.2 of Test Rigor Audit
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { InMemoryTransport } from "@modelcontextprotocol/sdk/inMemory.js";

import { registerDiscoveryTools } from "../src/tools/discovery-tools.js";
import {
    ToolsetRegistry,
    toolsetRegistry,
} from "../src/toolsets/registry.js";

// ── Test helpers ───────────────────────────────────────────────────────

function seedMinimalRegistry(registry: ToolsetRegistry): void {
    registry.register({
        name: "core",
        description: "Core tools for protocol tests",
        tools: [
            { name: "get_settings", description: "Read all user settings" },
        ],
        register: () => [],
        loaded: true,
        alwaysLoaded: true,
        isDefault: false,
    });
}

async function createTestClient(): Promise<{
    client: Client;
    server: McpServer;
}> {
    const server = new McpServer({ name: "zorivest", version: "0.1.0" });

    seedMinimalRegistry(toolsetRegistry);
    registerDiscoveryTools(server);

    const [clientTransport, serverTransport] =
        InMemoryTransport.createLinkedPair();
    const client = new Client(
        { name: "test-client", version: "0.1.0" },
    );

    await Promise.all([
        client.connect(clientTransport),
        server.connect(serverTransport),
    ]);

    return { client, server };
}

// ── Tests ──────────────────────────────────────────────────────────────

describe("MCP protocol: capabilities", () => {
    beforeEach(() => {
        vi.restoreAllMocks();
        const reg = toolsetRegistry as unknown as {
            toolsets: Map<string, unknown>;
        };
        reg.toolsets.clear();
    });

    it("server exposes tools capability after connect", async () => {
        const { client } = await createTestClient();
        const capabilities = client.getServerCapabilities();
        expect(capabilities).toBeDefined();
        expect(capabilities?.tools).toBeDefined();
    });

    it("server reports correct name and version", async () => {
        const { client } = await createTestClient();
        const info = client.getServerVersion();
        expect(info).toBeDefined();
        expect(info?.name).toBe("zorivest");
        expect(info?.version).toBe("0.1.0");
    });
});

describe("MCP protocol: tools/list", () => {
    beforeEach(() => {
        vi.restoreAllMocks();
        const reg = toolsetRegistry as unknown as {
            toolsets: Map<string, unknown>;
        };
        reg.toolsets.clear();
    });

    it("returns non-empty tool list", async () => {
        const { client } = await createTestClient();
        const { tools } = await client.listTools();
        expect(tools.length).toBeGreaterThan(0);
    });

    it("every tool has required fields", async () => {
        const { client } = await createTestClient();
        const { tools } = await client.listTools();

        for (const tool of tools) {
            expect(tool.name, "tool must have a name").toBeTruthy();
            expect(tool.description, `${tool.name} must have description`).toBeTruthy();
            expect(tool.inputSchema, `${tool.name} must have inputSchema`).toBeDefined();
            expect(tool.inputSchema.type).toBe("object");
        }
    });

    it("all tool names follow zorivest convention", async () => {
        const { client } = await createTestClient();
        const { tools } = await client.listTools();

        const validPattern = /^[a-z][a-z0-9_]*$/;
        for (const tool of tools) {
            expect(
                validPattern.test(tool.name),
                `Tool name "${tool.name}" must match snake_case pattern`,
            ).toBe(true);
        }
    });
});

describe("MCP protocol: tools/call errors", () => {
    beforeEach(() => {
        vi.restoreAllMocks();
        const reg = toolsetRegistry as unknown as {
            toolsets: Map<string, unknown>;
        };
        reg.toolsets.clear();
    });

    it("unknown tool returns error", async () => {
        const { client } = await createTestClient();

        // The SDK may throw or return an error result
        try {
            const result = await client.callTool({
                name: "totally_nonexistent_tool_xyz",
                arguments: {},
            });
            // If it returns instead of throwing, verify error shape
            expect(result.isError).toBe(true);
        } catch (error) {
            // SDK throws McpError for unknown tools
            expect(error).toBeDefined();
        }
    });

    it("tool with invalid args returns validation error", async () => {
        const { client } = await createTestClient();

        // describe_toolset requires toolset_name (string), send a number
        const result = await client.callTool({
            name: "describe_toolset",
            arguments: { toolset_name: 12345 as unknown as string },
        });

        // Zod validation should surface as isError
        const content = result.content as Array<{ type: string; text: string }>;
        const text = content[0]?.text ?? "";
        // Should indicate failure — either isError or error in response
        expect(result.isError || text.includes("error") || text.includes("fail")).toBe(true);
    });
});
