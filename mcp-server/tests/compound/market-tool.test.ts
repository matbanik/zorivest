/**
 * Behavior tests for zorivest_market compound tool.
 *
 * Verifies all 7 actions using v3.1 contract action names.
 * Source: mcp-consolidation-proposal-v3.md §5 zorivest_market
 * Phase: P2.5f corrections (Findings 2+3)
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { registerMarketTool } from "../../src/compound/market-tool.js";
import { createClient, mockFetch, getLastFetchUrl, getLastFetchMethod } from "./helpers.js";

describe("zorivest_market compound tool", () => {
    let fetchMock: ReturnType<typeof vi.fn>;

    beforeEach(() => { fetchMock = mockFetch(); });
    afterEach(() => vi.restoreAllMocks());

    it("registers exactly 1 tool named zorivest_market", async () => {
        const client = await createClient(registerMarketTool);
        const { tools } = await client.listTools();
        expect(tools).toHaveLength(1);
        expect(tools[0].name).toBe("zorivest_market");
    });

    it("exposes v3.1 action names in description", async () => {
        const client = await createClient(registerMarketTool);
        const { tools } = await client.listTools();
        const desc = tools[0].description ?? "";
        for (const action of ["quote", "news", "search", "filings", "providers", "disconnect", "test_provider"]) {
            expect(desc).toContain(action);
        }
    });

    it("routes quote to GET /market-data/quote", async () => {
        const client = await createClient(registerMarketTool);
        await client.callTool({ name: "zorivest_market", arguments: { action: "quote", ticker: "AAPL" } });
        expect(getLastFetchUrl(fetchMock)).toContain("/market-data/quote");
    });

    it("routes news to GET /market-data/news", async () => {
        const client = await createClient(registerMarketTool);
        await client.callTool({ name: "zorivest_market", arguments: { action: "news" } });
        expect(getLastFetchUrl(fetchMock)).toContain("/market-data/news");
    });

    it("routes search to GET /market-data/search", async () => {
        const client = await createClient(registerMarketTool);
        await client.callTool({ name: "zorivest_market", arguments: { action: "search", query: "Tesla" } });
        expect(getLastFetchUrl(fetchMock)).toContain("/market-data/search");
    });

    it("routes filings to GET /market-data/sec-filings", async () => {
        const client = await createClient(registerMarketTool);
        await client.callTool({ name: "zorivest_market", arguments: { action: "filings", ticker: "AAPL" } });
        expect(getLastFetchUrl(fetchMock)).toContain("/market-data/sec-filings");
    });

    it("routes providers to GET /market-data/providers", async () => {
        const client = await createClient(registerMarketTool);
        await client.callTool({ name: "zorivest_market", arguments: { action: "providers" } });
        expect(getLastFetchUrl(fetchMock)).toContain("/market-data/providers");
    });

    it("routes disconnect to DELETE /market-data/providers/:name/key", async () => {
        const client = await createClient(registerMarketTool);
        await client.callTool({
            name: "zorivest_market",
            arguments: { action: "disconnect", provider_name: "alpha_vantage", confirm_destructive: true },
        });
        expect(getLastFetchUrl(fetchMock)).toContain("/market-data/providers/alpha_vantage/key");
        expect(getLastFetchMethod(fetchMock)).toBe("DELETE");
    });

    it("routes test_provider to POST /market-data/providers/:name/test", async () => {
        const client = await createClient(registerMarketTool);
        await client.callTool({ name: "zorivest_market", arguments: { action: "test_provider", provider_name: "finnhub" } });
        expect(getLastFetchUrl(fetchMock)).toContain("/market-data/providers/finnhub/test");
        expect(getLastFetchMethod(fetchMock)).toBe("POST");
    });

    it("rejects unknown action", async () => {
        const client = await createClient(registerMarketTool);
        const result = await client.callTool({ name: "zorivest_market", arguments: { action: "nonexistent" } });
        expect(result.isError).toBe(true);
    });
});
