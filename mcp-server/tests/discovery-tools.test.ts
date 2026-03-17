/**
 * Unit tests for discovery MCP meta-tools.
 *
 * Tests verify: list_available_toolsets, describe_toolset, enable_toolset,
 * get_confirmation_token. Uses InMemoryTransport for real MCP protocol.
 *
 * Source: 05j-mcp-discovery.md, FIC AC-1 through AC-11
 * MEU: 41 (mcp-discovery)
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
        name: "trade-analytics",
        description: "Trade CRUD, screenshots, analytics, reports",
        tools: [
            { name: "create_trade", description: "Create a new trade" },
            { name: "list_trades", description: "List all trades" },
            { name: "get_trade", description: "Get trade by ID" },
        ],
        register: () => { },
        loaded: true,
        alwaysLoaded: false,
    });
    registry.register({
        name: "tax",
        description: "Tax estimation, wash sales, lot management",
        tools: [
            {
                name: "estimate_tax",
                description: "Estimate tax liability",
            },
            {
                name: "find_wash_sales",
                description: "Find wash sale violations",
            },
        ],
        register: () => { },
        loaded: false,
        alwaysLoaded: false,
    });
    registry.register({
        name: "core",
        description: "Settings, emergency stop/unlock, diagnostics",
        tools: [
            {
                name: "get_settings",
                description: "Read all user settings",
            },
        ],
        register: () => { },
        loaded: true,
        alwaysLoaded: true,
    });
}

async function createTestClient(): Promise<Client> {
    const server = new McpServer({ name: "test", version: "0.1.0" });

    // Seed registry before registering tools
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

// ── Tests ──────────────────────────────────────────────────────────────

describe("list_available_toolsets", () => {
    beforeEach(() => {
        vi.restoreAllMocks();
        // Clear registry between tests
        const reg = toolsetRegistry as unknown as {
            toolsets: Map<string, unknown>;
        };
        reg.toolsets.clear();
    });

    // AC-2: returns all toolsets with metadata
    it("returns all registered toolsets with counts", async () => {
        const client = await createTestClient();
        const result = await client.callTool({
            name: "list_available_toolsets",
            arguments: {},
        });

        const content = result.content as Array<{
            type: string;
            text: string;
        }>;
        const data = JSON.parse(content[0].text);
        expect(data.success).toBe(true);
        expect(data.data.toolsets).toHaveLength(3);
        expect(data.data.total_tools).toBe(6); // 3 + 2 + 1

        const analytics = data.data.toolsets.find(
            (ts: { name: string }) => ts.name === "trade-analytics",
        );
        expect(analytics.tool_count).toBe(3);
        expect(analytics.loaded).toBe(true);
    });
});

describe("describe_toolset", () => {
    beforeEach(() => {
        vi.restoreAllMocks();
        const reg = toolsetRegistry as unknown as {
            toolsets: Map<string, unknown>;
        };
        reg.toolsets.clear();
    });

    // AC-3: returns tool details for known toolset
    it("returns tool details for known toolset", async () => {
        const client = await createTestClient();
        const result = await client.callTool({
            name: "describe_toolset",
            arguments: { toolset_name: "trade-analytics" },
        });

        const content = result.content as Array<{
            type: string;
            text: string;
        }>;
        const data = JSON.parse(content[0].text);
        expect(data.success).toBe(true);
        expect(data.data.name).toBe("trade-analytics");
        expect(data.data.tools).toHaveLength(3);
        expect(data.data.tools[0].name).toBe("create_trade");
    });

    // AC-4: returns isError for unknown toolset
    it("returns isError for unknown toolset", async () => {
        const client = await createTestClient();
        const result = await client.callTool({
            name: "describe_toolset",
            arguments: { toolset_name: "nonexistent" },
        });

        const content = result.content as Array<{
            type: string;
            text: string;
        }>;
        const data = JSON.parse(content[0].text);

        expect(result.isError).toBe(true);
        expect(data.success).toBe(false);
        expect(data.error).toContain("list_available_toolsets");
    });
});

describe("enable_toolset", () => {
    beforeEach(() => {
        vi.restoreAllMocks();
        const reg = toolsetRegistry as unknown as {
            toolsets: Map<string, unknown>;
        };
        reg.toolsets.clear();
    });

    // AC-7: returns already_loaded info
    it("returns info if toolset already loaded", async () => {
        // Guard must allow for enable_toolset to proceed
        vi.stubGlobal(
            "fetch",
            vi.fn().mockResolvedValue({
                ok: true,
                json: () => Promise.resolve({ allowed: true }),
            }),
        );

        const client = await createTestClient();
        const result = await client.callTool({
            name: "enable_toolset",
            arguments: { toolset_name: "trade-analytics" },
        });

        const content = result.content as Array<{
            type: string;
            text: string;
        }>;
        const data = JSON.parse(content[0].text);
        expect(data.success).toBe(true);
        expect(data.data.status).toBe("already_loaded");
    });

    // AC-4: unknown toolset
    it("returns error for unknown toolset", async () => {
        // Guard must allow for enable_toolset to proceed past guard check
        vi.stubGlobal(
            "fetch",
            vi.fn().mockResolvedValue({
                ok: true,
                json: () => Promise.resolve({ allowed: true }),
            }),
        );

        const client = await createTestClient();
        const result = await client.callTool({
            name: "enable_toolset",
            arguments: { toolset_name: "nonexistent" },
        });

        const content = result.content as Array<{
            type: string;
            text: string;
        }>;
        const data = JSON.parse(content[0].text);
        expect(result.isError).toBe(true);
        expect(data.success).toBe(false);
    });

    // AC-5: enables unloaded toolset on dynamic client
    it("enables unloaded toolset and returns enabled status", async () => {
        // Guard must allow for enable_toolset to proceed
        vi.stubGlobal(
            "fetch",
            vi.fn().mockResolvedValue({
                ok: true,
                json: () => Promise.resolve({ allowed: true }),
            }),
        );

        const client = await createTestClient();
        const result = await client.callTool({
            name: "enable_toolset",
            arguments: { toolset_name: "tax" },
        });

        const content = result.content as Array<{
            type: string;
            text: string;
        }>;
        const data = JSON.parse(content[0].text);
        expect(data.success).toBe(true);
        expect(data.data.status).toBe("enabled");
        expect(data.data.tool_count).toBe(2);

        // Verify registry state updated
        const ts = toolsetRegistry.get("tax");
        expect(ts?.loaded).toBe(true);
    });

    // AC-6: sendToolListChanged called after successful enable
    it("calls sendToolListChanged after enabling toolset", async () => {
        vi.stubGlobal(
            "fetch",
            vi.fn().mockResolvedValue({
                ok: true,
                json: () => Promise.resolve({ allowed: true }),
            }),
        );

        // Create server with spy on sendToolListChanged
        const server = new McpServer({ name: "test", version: "0.1.0" });
        seedRegistry(toolsetRegistry);
        registerDiscoveryTools(server);

        const spy = vi.spyOn(server, "sendToolListChanged");

        const [clientTransport, serverTransport] =
            InMemoryTransport.createLinkedPair();
        const client = new Client(
            { name: "test-client", version: "0.1.0" },
        );
        await Promise.all([
            client.connect(clientTransport),
            server.connect(serverTransport),
        ]);

        await client.callTool({
            name: "enable_toolset",
            arguments: { toolset_name: "tax" },
        });

        // sendToolListChanged is called by SDK's registerTool() AND by our explicit call
        expect(spy).toHaveBeenCalled();
        // Value: verify notification was sent at least once
        expect(spy.mock.calls.length).toBeGreaterThanOrEqual(1);
    });

    // AC-6: rejects when dynamic loading is disabled (static client)
    it("rejects when dynamicLoadingEnabled is false", async () => {
        vi.stubGlobal(
            "fetch",
            vi.fn().mockResolvedValue({
                ok: true,
                json: () => Promise.resolve({ allowed: true }),
            }),
        );

        // Simulate static client
        toolsetRegistry.dynamicLoadingEnabled = false;

        const client = await createTestClient();
        const result = await client.callTool({
            name: "enable_toolset",
            arguments: { toolset_name: "tax" },
        });

        const content = result.content as Array<{
            type: string;
            text: string;
        }>;
        const data = JSON.parse(content[0].text);
        expect(result.isError).toBe(true);
        expect(data.success).toBe(false);
        expect(data.error).toContain("Dynamic tool loading is not supported");
        expect(data.error).toContain("--toolsets tax");

        // Restore
        toolsetRegistry.dynamicLoadingEnabled = true;
    });

    // AC-11: blocked when MCP Guard is locked (testing-strategy L374)
    it("blocks when MCP Guard is locked", async () => {
        vi.stubGlobal(
            "fetch",
            vi.fn().mockResolvedValue({
                ok: true,
                json: () =>
                    Promise.resolve({ allowed: false, reason: "manual" }),
            }),
        );

        const client = await createTestClient();
        const result = await client.callTool({
            name: "enable_toolset",
            arguments: { toolset_name: "tax" },
        });

        const content = result.content as Array<{
            type: string;
            text: string;
        }>;
        const data = JSON.parse(content[0].text);
        expect(result.isError).toBe(true);
        expect(data.success).toBe(false);
        expect(data.error).toContain("MCP guard blocked");
    });
});

describe("get_confirmation_token", () => {
    beforeEach(() => {
        vi.restoreAllMocks();
        const reg = toolsetRegistry as unknown as {
            toolsets: Map<string, unknown>;
        };
        reg.toolsets.clear();
    });

    // AC-8: generates MCP-layer token for destructive action
    it("generates token locally for destructive action", async () => {
        const client = await createTestClient();
        const result = await client.callTool({
            name: "get_confirmation_token",
            arguments: {
                action: "zorivest_emergency_stop",
                params_summary:
                    "Lock all tools due to suspected loop",
            },
        });

        const content = result.content as Array<{
            type: string;
            text: string;
        }>;
        const data = JSON.parse(content[0].text);
        expect(data.token).toMatch(/^ctk_[0-9a-f]{32}$/);
        expect(data.expires_in_seconds).toBe(60);
        expect(data.action).toBe("zorivest_emergency_stop");
        expect(data.params_summary).toBe(
            "Lock all tools due to suspected loop",
        );
    });

    // AC-10: returns isError for non-destructive/unknown action
    it("returns isError for non-destructive action", async () => {
        const client = await createTestClient();
        const result = await client.callTool({
            name: "get_confirmation_token",
            arguments: {
                action: "list_trades",
                params_summary: "List all trades",
            },
        });

        const content = result.content as Array<{
            type: string;
            text: string;
        }>;
        const data = JSON.parse(content[0].text);
        expect(result.isError).toBe(true);
        expect(data.success).toBe(false);
        expect(data.error).toContain("Unknown destructive action");
    });
});

// ── Metadata tests ─────────────────────────────────────────────────────

describe("discovery tool metadata", () => {
    beforeEach(() => {
        vi.restoreAllMocks();
        const reg = toolsetRegistry as unknown as {
            toolsets: Map<string, unknown>;
        };
        reg.toolsets.clear();
    });

    // AC-9: all tools have correct annotations and _meta
    it("registers all 4 tools with correct annotations", async () => {
        const client = await createTestClient();
        const { tools } = await client.listTools();

        const discoveryTools = [
            "list_available_toolsets",
            "describe_toolset",
            "enable_toolset",
            "get_confirmation_token",
        ];

        for (const toolName of discoveryTools) {
            const tool = tools.find((t) => t.name === toolName);
            expect(tool, `Tool ${toolName} should be registered`).toBeDefined();

            // All discovery tools are idempotent and non-destructive
            expect(tool!.annotations?.destructiveHint).toBe(false);

            // _meta vendor extension
            const meta = (tool as Record<string, unknown>)._meta as
                | Record<string, unknown>
                | undefined;
            expect(
                meta,
                `Tool ${toolName} should have _meta`,
            ).toBeDefined();
            expect(meta!.toolset).toBe("discovery");
            expect(meta!.alwaysLoaded).toBe(true);
        }

        // Verify read-only hints specifically
        const listTool = tools.find(
            (t) => t.name === "list_available_toolsets",
        );
        expect(listTool!.annotations?.readOnlyHint).toBe(true);
        expect(listTool!.annotations?.idempotentHint).toBe(true);

        const enableTool = tools.find(
            (t) => t.name === "enable_toolset",
        );
        expect(enableTool!.annotations?.readOnlyHint).toBe(false);

        const tokenTool = tools.find(
            (t) => t.name === "get_confirmation_token",
        );
        expect(tokenTool!.annotations?.readOnlyHint).toBe(true);
        expect(tokenTool!.annotations?.idempotentHint).toBe(false);
    });
});
