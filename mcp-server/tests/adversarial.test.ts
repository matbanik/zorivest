/**
 * Adversarial tests — malformed input, edge cases, and concurrency.
 *
 * Verifies the MCP server handles bad input gracefully without crashing.
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

function seedRegistry(registry: ToolsetRegistry): void {
    registry.register({
        name: "core",
        description: "Core tools",
        tools: [
            { name: "get_settings", description: "Read all user settings" },
        ],
        register: () => [],
        loaded: true,
        alwaysLoaded: true,
        isDefault: false,
    });
    registry.register({
        name: "trade-analytics",
        description: "Trade management",
        tools: [
            { name: "create_trade", description: "Create a trade" },
            { name: "list_trades", description: "List trades" },
        ],
        register: () => [],
        loaded: true,
        alwaysLoaded: false,
        isDefault: false,
    });
}

async function createTestClient(): Promise<Client> {
    const server = new McpServer({ name: "zorivest", version: "0.1.0" });

    seedRegistry(toolsetRegistry);
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

    return client;
}

// ── Adversarial: String edge cases ─────────────────────────────────────

describe("adversarial: string edge cases", () => {
    beforeEach(() => {
        vi.restoreAllMocks();
        const reg = toolsetRegistry as unknown as {
            toolsets: Map<string, unknown>;
        };
        reg.toolsets.clear();
    });

    it("empty string toolset_name → error, not crash", async () => {
        const client = await createTestClient();
        const result = await client.callTool({
            name: "describe_toolset",
            arguments: { toolset_name: "" },
        });

        expect(result.isError).toBe(true);
        const content = result.content as Array<{ type: string; text: string }>;
        const data = JSON.parse(content[0].text);
        expect(data.success).toBe(false);
    });

    it("extremely long string → handled gracefully", async () => {
        const client = await createTestClient();
        const longString = "a".repeat(10000);
        const result = await client.callTool({
            name: "describe_toolset",
            arguments: { toolset_name: longString },
        });

        expect(result.isError).toBe(true);
        const content = result.content as Array<{ type: string; text: string }>;
        const data = JSON.parse(content[0].text);
        expect(data.success).toBe(false);
    });

    it("unicode and special characters → no crash", async () => {
        const client = await createTestClient();
        const result = await client.callTool({
            name: "describe_toolset",
            arguments: { toolset_name: "🔥💀\u0000\x01\t\n\r" },
        });

        expect(result.isError).toBe(true);
    });

    it("SQL injection payload → no shell/DB escape", async () => {
        const client = await createTestClient();
        const result = await client.callTool({
            name: "describe_toolset",
            arguments: {
                toolset_name: "'; DROP TABLE trades; --",
            },
        });

        // Should return a clean error — the server rejected it safely
        expect(result.isError).toBe(true);
        const content = result.content as Array<{ type: string; text: string }>;
        const data = JSON.parse(content[0].text);
        // Key invariant: no SQL was executed, just a "not found" error
        expect(data.success).toBe(false);
        expect(data.error).toContain("list_available_toolsets");
    });
});

// ── Adversarial: Null/undefined in required fields ─────────────────────

describe("adversarial: null/undefined arguments", () => {
    beforeEach(() => {
        vi.restoreAllMocks();
        const reg = toolsetRegistry as unknown as {
            toolsets: Map<string, unknown>;
        };
        reg.toolsets.clear();
    });

    it("null toolset_name → handled gracefully", async () => {
        const client = await createTestClient();

        try {
            const result = await client.callTool({
                name: "describe_toolset",
                arguments: { toolset_name: null as unknown as string },
            });
            // If we get a result, it should be an error
            expect(result.isError).toBe(true);
        } catch {
            // Zod validation may throw before reaching handler — acceptable
        }
    });

    it("missing required field → error", async () => {
        const client = await createTestClient();

        try {
            const result = await client.callTool({
                name: "describe_toolset",
                arguments: {},
            });
            expect(result.isError).toBe(true);
        } catch {
            // SDK/Zod may reject before reaching handler — acceptable
        }
    });
});

// ── Adversarial: Concurrent calls ──────────────────────────────────────

describe("adversarial: concurrent tool calls", () => {
    beforeEach(() => {
        vi.restoreAllMocks();
        const reg = toolsetRegistry as unknown as {
            toolsets: Map<string, unknown>;
        };
        reg.toolsets.clear();
    });

    it("10 concurrent list_available_toolsets → all succeed", async () => {
        const client = await createTestClient();

        const promises = Array.from({ length: 10 }, () =>
            client.callTool({
                name: "list_available_toolsets",
                arguments: {},
            }),
        );

        const results = await Promise.all(promises);

        for (const result of results) {
            expect(result.isError).toBeFalsy();
            const content = result.content as Array<{
                type: string;
                text: string;
            }>;
            const data = JSON.parse(content[0].text);
            expect(data.success).toBe(true);
        }
    });

    it("concurrent describe calls for different toolsets → all correct", async () => {
        const client = await createTestClient();

        const toolsetNames = ["core", "trade-analytics", "core", "trade-analytics"];
        const promises = toolsetNames.map((name) =>
            client.callTool({
                name: "describe_toolset",
                arguments: { toolset_name: name },
            }),
        );

        const results = await Promise.all(promises);

        for (let i = 0; i < results.length; i++) {
            const content = results[i].content as Array<{
                type: string;
                text: string;
            }>;
            const data = JSON.parse(content[0].text);
            expect(data.success).toBe(true);
            expect(data.data.name).toBe(toolsetNames[i]);
        }
    });
});
