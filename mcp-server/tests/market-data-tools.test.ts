/**
 * Unit tests for market-data MCP tools — MEU-64.
 *
 * Tests verify correct REST endpoints and response structure.
 * Uses mocked global.fetch — no live API needed.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { registerMarketDataTools } from "../src/tools/market-data-tools.js";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { InMemoryTransport } from "@modelcontextprotocol/sdk/inMemory.js";

// ── Test helpers ───────────────────────────────────────────────────────

function mockFetch(response: unknown, status = 200): void {
    // withGuard calls /mcp-guard/check first, then the tool calls the actual endpoint.
    // We need to return {allowed: true} for the guard check, then the actual response.
    const guardResponse = { allowed: true };
    let callCount = 0;

    vi.stubGlobal(
        "fetch",
        vi.fn().mockImplementation(() => {
            callCount++;
            const data = callCount === 1 ? guardResponse : response;
            const responseStatus = callCount === 1 ? 200 : status;
            return Promise.resolve({
                ok: responseStatus >= 200 && responseStatus < 300,
                status: responseStatus,
                json: () => Promise.resolve(data),
                text: () => Promise.resolve(JSON.stringify(data)),
            });
        }),
    );
}

async function createTestClient(): Promise<Client> {
    const server = new McpServer({ name: "test", version: "0.1.0" });
    registerMarketDataTools(server);

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

describe("get_stock_quote", () => {
    beforeEach(() => {
        vi.restoreAllMocks();
    });

    it("calls GET /market-data/quote with ticker", async () => {
        mockFetch({ ticker: "AAPL", price: 181.18, provider: "Alpha Vantage" });

        const client = await createTestClient();
        const result = await client.callTool({
            name: "get_stock_quote",
            arguments: { ticker: "AAPL" },
        });

        expect(fetch).toHaveBeenCalledTimes(2);
        const [url] = vi.mocked(fetch).mock.calls[1];
        expect(url).toContain("/market-data/quote");
        expect(url).toContain("ticker=AAPL");

        const content = result.content as Array<{ type: string; text: string }>;
        const parsed = JSON.parse(content[0].text);
        expect(parsed.success).toBe(true);
        expect(parsed.data.ticker).toBe("AAPL");
    });
});

describe("get_market_news", () => {
    beforeEach(() => {
        vi.restoreAllMocks();
    });

    it("calls GET /market-data/news with default count", async () => {
        mockFetch([{ title: "Test", source: "Reuters", provider: "Finnhub" }]);

        const client = await createTestClient();
        await client.callTool({
            name: "get_market_news",
            arguments: {},
        });

        expect(fetch).toHaveBeenCalledTimes(2);
        const [url] = vi.mocked(fetch).mock.calls[1];
        expect(url).toContain("/market-data/news");
        expect(url).toContain("count=5");
    });

    it("includes ticker filter when provided", async () => {
        mockFetch([]);

        const client = await createTestClient();
        await client.callTool({
            name: "get_market_news",
            arguments: { ticker: "AAPL", count: 10 },
        });

        const [url] = vi.mocked(fetch).mock.calls[1];
        expect(url).toContain("ticker=AAPL");
        expect(url).toContain("count=10");
    });
});

describe("search_ticker", () => {
    beforeEach(() => {
        vi.restoreAllMocks();
    });

    it("calls GET /market-data/search with query", async () => {
        mockFetch([{ symbol: "AAPL", name: "Apple Inc." }]);

        const client = await createTestClient();
        await client.callTool({
            name: "search_ticker",
            arguments: { query: "apple" },
        });

        expect(fetch).toHaveBeenCalledTimes(2);
        const [url] = vi.mocked(fetch).mock.calls[1];
        expect(url).toContain("/market-data/search");
        expect(url).toContain("query=apple");
    });
});

describe("get_sec_filings", () => {
    beforeEach(() => {
        vi.restoreAllMocks();
    });

    it("calls GET /market-data/sec-filings with ticker", async () => {
        mockFetch([{ ticker: "AAPL", company_name: "Apple Inc." }]);

        const client = await createTestClient();
        await client.callTool({
            name: "get_sec_filings",
            arguments: { ticker: "AAPL" },
        });

        expect(fetch).toHaveBeenCalledTimes(2);
        const [url] = vi.mocked(fetch).mock.calls[1];
        expect(url).toContain("/market-data/sec-filings");
        expect(url).toContain("ticker=AAPL");
    });
});

describe("list_market_providers", () => {
    beforeEach(() => {
        vi.restoreAllMocks();
    });

    it("calls GET /market-data/providers", async () => {
        mockFetch([]);

        const client = await createTestClient();
        await client.callTool({
            name: "list_market_providers",
            arguments: {},
        });

        expect(fetch).toHaveBeenCalledTimes(2);
        const [url] = vi.mocked(fetch).mock.calls[1];
        expect(url).toContain("/market-data/providers");
    });
});

describe("disconnect_market_provider", () => {
    beforeEach(() => {
        vi.restoreAllMocks();
    });

    it("calls DELETE /market-data/providers/{name}/key", async () => {
        mockFetch({ status: "removed" });

        const client = await createTestClient();
        await client.callTool({
            name: "disconnect_market_provider",
            arguments: {
                provider_name: "Alpha Vantage",
                confirm_destructive: true,
            },
        });

        expect(fetch).toHaveBeenCalledTimes(2);
        const [url, opts] = vi.mocked(fetch).mock.calls[1];
        expect(url).toContain("/market-data/providers/Alpha%20Vantage/key");
        expect(opts?.method).toBe("DELETE");
    });
});

describe("test_market_provider", () => {
    beforeEach(() => {
        vi.restoreAllMocks();
    });

    it("calls POST /market-data/providers/{name}/test", async () => {
        mockFetch({ success: true, message: "Connection successful" });

        const client = await createTestClient();
        const result = await client.callTool({
            name: "test_market_provider",
            arguments: { provider_name: "Alpha Vantage" },
        });

        expect(fetch).toHaveBeenCalledTimes(2);
        const [url, opts] = vi.mocked(fetch).mock.calls[1];
        expect(url).toContain("/market-data/providers/Alpha%20Vantage/test");
        expect(opts?.method).toBe("POST");

        const content = result.content as Array<{ type: string; text: string }>;
        const parsed = JSON.parse(content[0].text);
        expect(parsed.success).toBe(true);
    });
});
