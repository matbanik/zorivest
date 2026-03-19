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
        // URL-aware mock: guard check returns allowed, API returns trade
        vi.stubGlobal(
            "fetch",
            vi.fn().mockImplementation((url: string) => {
                if (typeof url === "string" && url.includes("/mcp-guard/")) {
                    return Promise.resolve({
                        ok: true,
                        status: 200,
                        json: () => Promise.resolve({ allowed: true }),
                        text: () => Promise.resolve(JSON.stringify({ allowed: true })),
                    });
                }
                return Promise.resolve({
                    ok: true,
                    status: 201,
                    json: () => Promise.resolve(tradeResponse),
                    text: () => Promise.resolve(JSON.stringify(tradeResponse)),
                });
            }),
        );

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

        // Guard check + API call = 2 fetch calls
        expect(fetch).toHaveBeenCalledTimes(2);
        // Second call is the actual trade POST
        const [url, opts] = vi.mocked(fetch).mock.calls[1];
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
        // URL-aware mock for guard + API
        vi.stubGlobal(
            "fetch",
            vi.fn().mockImplementation((url: string) => {
                if (typeof url === "string" && url.includes("/mcp-guard/")) {
                    return Promise.resolve({
                        ok: true,
                        status: 200,
                        json: () => Promise.resolve({ allowed: true }),
                        text: () => Promise.resolve(JSON.stringify({ allowed: true })),
                    });
                }
                return Promise.resolve({
                    ok: true,
                    status: 201,
                    json: () => Promise.resolve({ exec_id: "TEST002" }),
                    text: () => Promise.resolve(JSON.stringify({ exec_id: "TEST002" })),
                });
            }),
        );

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

        // Second call is the API call (first is guard)
        const [, opts] = vi.mocked(fetch).mock.calls[1];
        const body = JSON.parse(opts?.body as string);
        expect(body.time).toBeDefined();
        // Must be a valid ISO-8601 string (regex catches malformed dates that new Date() silently accepts)
        expect(body.time).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/);
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

// ── Confirmation token tests (TDD Red → Green) ────────────────────────

import {
    setConfirmationMode,
    createConfirmationToken,
} from "../src/middleware/confirmation.js";

/**
 * Guard-aware fetch mock that also serves the /trades POST endpoint.
 * All guard checks return `allowed: true`, trade endpoint returns 201.
 */
function mockGuardAndTradesFetch(tradeResponse: unknown = { exec_id: "CT001" }): void {
    vi.stubGlobal(
        "fetch",
        vi.fn().mockImplementation((url: string) => {
            if (typeof url === "string" && url.includes("/mcp-guard/")) {
                return Promise.resolve({
                    ok: true,
                    status: 200,
                    json: () => Promise.resolve({ allowed: true }),
                    text: () => Promise.resolve(JSON.stringify({ allowed: true })),
                });
            }
            return Promise.resolve({
                ok: true,
                status: 201,
                json: () => Promise.resolve(tradeResponse),
                text: () => Promise.resolve(JSON.stringify(tradeResponse)),
            });
        }),
    );
}

/** Minimal valid create_trade arguments (excluding confirmation_token). */
const BASE_TRADE_ARGS = {
    exec_id: "CT001",
    instrument: "AAPL",
    action: "BOT" as const,
    quantity: 100,
    price: 150.0,
    account_id: "ACC001",
};

describe("create_trade confirmation_token", () => {
    beforeEach(() => {
        vi.restoreAllMocks();
        // Reset to default pass-through mode between tests
        setConfirmationMode("dynamic");
    });

    // AC-1: Schema accepts confirmation_token (proven via static mode)
    it("accepts confirmation_token in schema and forwards it to middleware", async () => {
        mockGuardAndTradesFetch();
        setConfirmationMode("static");
        const client = await createTestClient();
        const { token } = createConfirmationToken("create_trade");

        // Static mode requires a valid token. If Zod had stripped
        // confirmation_token from the parsed args, middleware would see
        // no token and block the call — so success here proves the
        // schema preserved the field through to the middleware layer.
        const result = await client.callTool({
            name: "create_trade",
            arguments: {
                ...BASE_TRADE_ARGS,
                confirmation_token: token,
            },
        });

        const content = result.content as Array<{ type: string; text: string }>;
        expect(content).toHaveLength(1);
        expect(content[0].type).toBe("text");
        const parsed = JSON.parse(content[0].text);
        expect(parsed.success).toBe(true);
    });

    // AC-3: confirmation_token NOT forwarded to REST API body
    it("does not include confirmation_token in the POST /trades body", async () => {
        mockGuardAndTradesFetch();
        const client = await createTestClient();

        await client.callTool({
            name: "create_trade",
            arguments: {
                ...BASE_TRADE_ARGS,
                confirmation_token: "should-not-appear-in-body",
            },
        });

        // Find the /trades POST call (not the guard call)
        const tradeCalls = vi
            .mocked(fetch)
            .mock.calls.filter(
                ([url]) => typeof url === "string" && url.includes("/trades") && !url.includes("/mcp-guard/"),
            );
        expect(tradeCalls.length).toBeGreaterThanOrEqual(1);

        const [, opts] = tradeCalls[0];
        const body = JSON.parse(opts?.body as string);
        expect(body).not.toHaveProperty("confirmation_token");
        // Verify real fields ARE present
        expect(body.exec_id).toBe("CT001");
        expect(body.instrument).toBe("AAPL");
    });

    // AC-2: Static-mode confirmation round-trip
    it("requires valid confirmation_token on static clients and rejects without one", async () => {
        mockGuardAndTradesFetch();
        setConfirmationMode("static");

        const client = await createTestClient();

        // Call WITHOUT a token — middleware should block
        const blocked = await client.callTool({
            name: "create_trade",
            arguments: BASE_TRADE_ARGS,
        });

        const blockedContent = blocked.content as Array<{ type: string; text: string }>;
        const blockedText = blockedContent[0].text;
        const blockedPayload = JSON.parse(blockedText);
        expect(blockedPayload.error).toBe("Confirmation required");
        expect(blockedPayload.tool).toBe("create_trade");

        // Verify no trade POST happened while blocked
        const tradePostCalls = vi
            .mocked(fetch)
            .mock.calls.filter(
                ([url, opts]) =>
                    typeof url === "string" &&
                    url.includes("/trades") &&
                    !url.includes("/mcp-guard/") &&
                    opts?.method === "POST",
            );
        expect(tradePostCalls).toHaveLength(0);

        // Now mint a real token and retry
        const { token } = createConfirmationToken("create_trade");

        const result = await client.callTool({
            name: "create_trade",
            arguments: {
                ...BASE_TRADE_ARGS,
                confirmation_token: token,
            },
        });

        const content = result.content as Array<{ type: string; text: string }>;
        const parsed = JSON.parse(content[0].text);
        expect(parsed.success).toBe(true);
    });

    // AC-4: Dynamic-mode backward compatibility
    it("passes through without confirmation_token on dynamic clients", async () => {
        mockGuardAndTradesFetch();
        setConfirmationMode("dynamic");

        const client = await createTestClient();

        const result = await client.callTool({
            name: "create_trade",
            arguments: BASE_TRADE_ARGS,
        });

        const content = result.content as Array<{ type: string; text: string }>;
        expect(content).toHaveLength(1);
        const parsed = JSON.parse(content[0].text);
        expect(parsed.success).toBe(true);
    });
});

// ── delete_trade ───────────────────────────────────────────────────────

describe("delete_trade", () => {
    beforeEach(() => {
        vi.restoreAllMocks();
        setConfirmationMode("dynamic");
    });

    it("calls DELETE /trades/{exec_id} and returns success envelope", async () => {
        // Guard returns allowed, DELETE returns 204 (no content → fetchApi wraps as {success:true})
        vi.stubGlobal(
            "fetch",
            vi.fn().mockImplementation((url: string, opts?: RequestInit) => {
                if (typeof url === "string" && url.includes("/mcp-guard/")) {
                    return Promise.resolve({
                        ok: true,
                        status: 200,
                        json: () => Promise.resolve({ allowed: true }),
                        text: () => Promise.resolve(JSON.stringify({ allowed: true })),
                    });
                }
                return Promise.resolve({
                    ok: true,
                    status: 204,
                    json: () => Promise.resolve(null),
                    text: () => Promise.resolve(""),
                });
            }),
        );

        const client = await createTestClient();
        const result = await client.callTool({
            name: "delete_trade",
            arguments: { exec_id: "DEL-001" },
        });

        // Find the DELETE call (not the guard call)
        const deleteCalls = vi
            .mocked(fetch)
            .mock.calls.filter(
                ([url, opts]) =>
                    typeof url === "string" &&
                    url.includes("/trades/DEL-001") &&
                    !url.includes("/mcp-guard/"),
            );
        expect(deleteCalls.length).toBe(1);
        const [delUrl, delOpts] = deleteCalls[0];
        expect(delUrl).toContain("/trades/DEL-001");
        expect(delOpts?.method).toBe("DELETE");

        const content = result.content as Array<{ type: string; text: string }>;
        expect(content).toHaveLength(1);
        const parsed = JSON.parse(content[0].text);
        expect(parsed.success).toBe(true);
    });
});
