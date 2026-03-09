/**
 * Unit tests for trade MCP tools.
 *
 * Tests verify correct REST endpoints called, payload forwarding,
 * and standard response envelope structure.
 * Uses mocked global.fetch — no live API needed.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { registerTradeTools } from "../src/tools/trade-tools.js";
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
    registerTradeTools(server);

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

describe("create_trade", () => {
    beforeEach(() => {
        vi.restoreAllMocks();
    });

    it("calls POST /trades with correct payload and returns envelope", async () => {
        const tradeResponse = {
            exec_id: "TEST001",
            time: "2026-01-15T10:30:00Z",
            instrument: "AAPL",
            action: "BOT",
            quantity: 100,
            price: 150.5,
            account_id: "ACC001",
            commission: 1.0,
            realized_pnl: 0,
        };
        mockFetch(tradeResponse, 201);

        const client = await createTestClient();
        const result = await client.callTool({
            name: "create_trade",
            arguments: {
                exec_id: "TEST001",
                time: "2026-01-15T10:30:00Z",
                instrument: "AAPL",
                action: "BOT",
                quantity: 100,
                price: 150.5,
                account_id: "ACC001",
                commission: 1.0,
            },
        });

        // Verify fetch called with correct URL and method
        expect(fetch).toHaveBeenCalledOnce();
        const [url, opts] = vi.mocked(fetch).mock.calls[0];
        expect(url).toContain("/trades");
        expect(opts?.method).toBe("POST");

        // Verify body includes time field
        const body = JSON.parse(opts?.body as string);
        expect(body.time).toBe("2026-01-15T10:30:00Z");
        expect(body.exec_id).toBe("TEST001");
        expect(body.instrument).toBe("AAPL");

        // Verify response envelope
        const content = result.content as Array<{
            type: string;
            text: string;
        }>;
        expect(content).toHaveLength(1);
        expect(content[0].type).toBe("text");
        const parsed = JSON.parse(content[0].text);
        expect(parsed.success).toBe(true);
        expect(parsed.data.exec_id).toBe("TEST001");
    });

    it("defaults time to current ISO string when omitted", async () => {
        mockFetch({ exec_id: "TEST002" }, 201);

        const client = await createTestClient();
        await client.callTool({
            name: "create_trade",
            arguments: {
                exec_id: "TEST002",
                instrument: "MSFT",
                action: "SLD",
                quantity: 50,
                price: 300.0,
                account_id: "ACC001",
            },
        });

        const [, opts] = vi.mocked(fetch).mock.calls[0];
        const body = JSON.parse(opts?.body as string);
        expect(body.time).toBeDefined();
        // Should be a valid ISO string
        expect(() => new Date(body.time)).not.toThrow();
    });
});

describe("list_trades", () => {
    beforeEach(() => {
        vi.restoreAllMocks();
    });

    it("calls GET /trades with query params and returns envelope", async () => {
        const listResponse = {
            items: [{ exec_id: "T1" }, { exec_id: "T2" }],
            total: 2,
            limit: 10,
            offset: 0,
        };
        mockFetch(listResponse);

        const client = await createTestClient();
        const result = await client.callTool({
            name: "list_trades",
            arguments: { limit: 10, offset: 0, sort: "-time" },
        });

        expect(fetch).toHaveBeenCalledOnce();
        const [url] = vi.mocked(fetch).mock.calls[0];
        expect(url).toContain("/trades?");
        expect(url).toContain("limit=10");
        expect(url).toContain("offset=0");
        expect(url).toContain("sort=-time");

        const content = result.content as Array<{
            type: string;
            text: string;
        }>;
        const parsed = JSON.parse(content[0].text);
        expect(parsed.success).toBe(true);
        expect(parsed.data.items).toHaveLength(2);
    });

    it("calls GET /trades without query when no params given", async () => {
        mockFetch({ items: [], total: 0, limit: 50, offset: 0 });

        const client = await createTestClient();
        await client.callTool({ name: "list_trades", arguments: {} });

        const [url] = vi.mocked(fetch).mock.calls[0];
        expect(url).toMatch(/\/trades$/);
    });
});

describe("attach_screenshot", () => {
    beforeEach(() => {
        vi.restoreAllMocks();
    });

    it("decodes base64, sends multipart POST to /trades/{id}/images", async () => {
        mockFetch({ image_id: "img_001" }, 201);

        const client = await createTestClient();
        // Small 1x1 white PNG as base64
        const testBase64 =
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAF/AL+hc2rNAAAAABJRU5ErkJggg==";

        const result = await client.callTool({
            name: "attach_screenshot",
            arguments: {
                exec_id: "TEST001",
                image_base64: testBase64,
                caption: "Entry chart",
            },
        });

        expect(fetch).toHaveBeenCalledOnce();
        const [url, opts] = vi.mocked(fetch).mock.calls[0];
        expect(url).toContain("/trades/TEST001/images");
        expect(opts?.method).toBe("POST");
        // Body should be FormData
        expect(opts?.body).toBeInstanceOf(FormData);

        const content = result.content as Array<{
            type: string;
            text: string;
        }>;
        const parsed = JSON.parse(content[0].text);
        expect(parsed.success).toBe(true);
    });
});

describe("get_trade_screenshots", () => {
    beforeEach(() => {
        vi.restoreAllMocks();
    });

    it("calls GET /trades/{id}/images and returns envelope", async () => {
        mockFetch([
            { id: 1, caption: "Entry", mime_type: "image/webp" },
        ]);

        const client = await createTestClient();
        const result = await client.callTool({
            name: "get_trade_screenshots",
            arguments: { exec_id: "TEST001" },
        });

        expect(fetch).toHaveBeenCalledOnce();
        const [url] = vi.mocked(fetch).mock.calls[0];
        expect(url).toContain("/trades/TEST001/images");

        const content = result.content as Array<{
            type: string;
            text: string;
        }>;
        const parsed = JSON.parse(content[0].text);
        expect(parsed.success).toBe(true);
    });
});

describe("get_screenshot", () => {
    beforeEach(() => {
        vi.restoreAllMocks();
    });

    it("fetches metadata (JSON) then full image (binary), returns mixed content", async () => {
        // Mock two sequential fetches:
        // 1. metadata → JSON response
        // 2. full image → binary response (ArrayBuffer)
        const metadataResponse = {
            id: 1,
            caption: "Entry chart",
            mime_type: "image/webp",
        };

        // Small binary payload (simulates raw image bytes)
        const fakeImageBytes = new Uint8Array([
            0x52, 0x49, 0x46, 0x46,
        ]);

        const fetchMock = vi
            .fn()
            // First call: metadata endpoint (JSON)
            .mockResolvedValueOnce({
                ok: true,
                status: 200,
                json: () => Promise.resolve(metadataResponse),
                text: () =>
                    Promise.resolve(JSON.stringify(metadataResponse)),
            })
            // Second call: full image endpoint (binary)
            .mockResolvedValueOnce({
                ok: true,
                status: 200,
                arrayBuffer: () =>
                    Promise.resolve(fakeImageBytes.buffer),
                headers: new Headers({
                    "content-type": "image/webp",
                }),
            });
        vi.stubGlobal("fetch", fetchMock);

        const client = await createTestClient();
        const result = await client.callTool({
            name: "get_screenshot",
            arguments: { image_id: 1 },
        });

        // Should have called fetch twice (metadata + full)
        expect(fetchMock).toHaveBeenCalledTimes(2);
        const [url1] = fetchMock.mock.calls[0];
        const [url2] = fetchMock.mock.calls[1];
        expect(url1).toContain("/images/1");
        expect(url2).toContain("/images/1/full");

        // Should return mixed content: text + image
        const content = result.content as Array<{
            type: string;
            [key: string]: unknown;
        }>;
        expect(content.length).toBe(2);
        expect(content[0].type).toBe("text");
        expect(content[1].type).toBe("image");
        expect(content[1].mimeType).toBe("image/webp");
        // Verify base64 encoding of fakeImageBytes
        expect(content[1].data).toBe(
            Buffer.from(fakeImageBytes).toString("base64"),
        );
    });
});
