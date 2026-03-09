/**
 * Unit tests for settings MCP tools.
 *
 * Tests verify correct REST endpoints, key filtering,
 * string-valued boundaries, and response envelope structure.
 * Uses mocked global.fetch — no live API needed.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { registerSettingsTools } from "../src/tools/settings-tools.js";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { InMemoryTransport } from "@modelcontextprotocol/sdk/inMemory.js";

// ── Test helpers ───────────────────────────────────────────────────────

function mockFetch(response: unknown, status = 200): void {
    vi.stubGlobal(
        "fetch",
        vi.fn().mockResolvedValue({
            ok: status >= 200 && status < 300,
            status,
            json: () => Promise.resolve(response),
            text: () => Promise.resolve(JSON.stringify(response)),
        }),
    );
}

async function createTestClient(): Promise<Client> {
    const server = new McpServer({ name: "test", version: "0.1.0" });
    registerSettingsTools(server);

    const [clientTransport, serverTransport] =
        InMemoryTransport.createLinkedPair();

    const client = new Client({ name: "test-client", version: "0.1.0" });

    await Promise.all([
        client.connect(clientTransport),
        server.connect(serverTransport),
    ]);

    return client;
}

// ── Tests ──────────────────────────────────────────────────────────────

describe("get_settings", () => {
    beforeEach(() => {
        vi.restoreAllMocks();
    });

    it("calls GET /settings when no key provided", async () => {
        const allSettings = {
            theme: "dark",
            timezone: "America/New_York",
            currency: "USD",
        };
        mockFetch(allSettings);

        const client = await createTestClient();
        const result = await client.callTool({
            name: "get_settings",
            arguments: {},
        });

        expect(fetch).toHaveBeenCalledOnce();
        const [url] = vi.mocked(fetch).mock.calls[0];
        expect(url).toMatch(/\/settings$/);

        const content = result.content as Array<{ type: string; text: string }>;
        const parsed = JSON.parse(content[0].text);
        expect(parsed.success).toBe(true);
        expect(parsed.data.theme).toBe("dark");
    });

    it("calls GET /settings/{key} when key provided", async () => {
        mockFetch({ theme: "dark" });

        const client = await createTestClient();
        await client.callTool({
            name: "get_settings",
            arguments: { key: "theme" },
        });

        expect(fetch).toHaveBeenCalledOnce();
        const [url] = vi.mocked(fetch).mock.calls[0];
        expect(url).toContain("/settings/theme");
    });
});

describe("update_settings", () => {
    beforeEach(() => {
        vi.restoreAllMocks();
    });

    it("calls PUT /settings with string-valued JSON map", async () => {
        mockFetch({ updated: 2 });

        const client = await createTestClient();
        const result = await client.callTool({
            name: "update_settings",
            arguments: {
                settings: {
                    theme: "light",
                    timezone: "UTC",
                },
            },
        });

        expect(fetch).toHaveBeenCalledOnce();
        const [url, opts] = vi.mocked(fetch).mock.calls[0];
        expect(url).toContain("/settings");
        expect(opts?.method).toBe("PUT");

        // Verify body is a string-valued map
        const body = JSON.parse(opts?.body as string);
        expect(body.theme).toBe("light");
        expect(body.timezone).toBe("UTC");
        // All values are strings (MCP boundary contract)
        Object.values(body).forEach((v) => {
            expect(typeof v).toBe("string");
        });

        const content = result.content as Array<{ type: string; text: string }>;
        const parsed = JSON.parse(content[0].text);
        expect(parsed.success).toBe(true);
    });

    it("returns error envelope on API failure", async () => {
        mockFetch({ detail: "Invalid setting key" }, 400);

        const client = await createTestClient();
        const result = await client.callTool({
            name: "update_settings",
            arguments: {
                settings: { invalid_key: "value" },
            },
        });

        const content = result.content as Array<{ type: string; text: string }>;
        const parsed = JSON.parse(content[0].text);
        expect(parsed.success).toBe(false);
        expect(parsed.error).toContain("400");
    });
});
