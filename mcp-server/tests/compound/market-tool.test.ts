/**
 * Behavior tests for zorivest_market compound tool.
 *
 * Verifies all 15 actions: 7 base (MEU-63) + 8 expansion (MEU-192).
 * Source: mcp-consolidation-proposal-v3.md §5 zorivest_market
 *         docs/build-plan/08a-market-data-expansion.md §8a.11
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

    it("exposes all 15 action names in description", async () => {
        const client = await createClient(registerMarketTool);
        const { tools } = await client.listTools();
        const desc = tools[0].description ?? "";
        for (const action of [
            "quote", "news", "search", "filings", "providers", "disconnect", "test_provider",
            "ohlcv", "fundamentals", "earnings", "dividends", "splits", "insider",
            "economic_calendar", "company_profile",
        ]) {
            expect(desc).toContain(action);
        }
    });

    // ── Base actions (7) ──────────────────────────────────────────────

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

    // ── Expansion actions (8 — MEU-192) ───────────────────────────────

    it("routes ohlcv to GET /market-data/ohlcv", async () => {
        const client = await createClient(registerMarketTool);
        await client.callTool({ name: "zorivest_market", arguments: { action: "ohlcv", ticker: "AAPL" } });
        expect(getLastFetchUrl(fetchMock)).toContain("/market-data/ohlcv");
    });

    it("routes ohlcv with interval param", async () => {
        const client = await createClient(registerMarketTool);
        await client.callTool({ name: "zorivest_market", arguments: { action: "ohlcv", ticker: "AAPL", interval: "5m" } });
        expect(getLastFetchUrl(fetchMock)).toContain("interval=5m");
    });

    it("routes fundamentals to GET /market-data/fundamentals", async () => {
        const client = await createClient(registerMarketTool);
        await client.callTool({ name: "zorivest_market", arguments: { action: "fundamentals", ticker: "MSFT" } });
        expect(getLastFetchUrl(fetchMock)).toContain("/market-data/fundamentals");
    });

    it("routes earnings to GET /market-data/earnings", async () => {
        const client = await createClient(registerMarketTool);
        await client.callTool({ name: "zorivest_market", arguments: { action: "earnings", ticker: "GOOG" } });
        expect(getLastFetchUrl(fetchMock)).toContain("/market-data/earnings");
    });

    it("routes dividends to GET /market-data/dividends", async () => {
        const client = await createClient(registerMarketTool);
        await client.callTool({ name: "zorivest_market", arguments: { action: "dividends", ticker: "JNJ" } });
        expect(getLastFetchUrl(fetchMock)).toContain("/market-data/dividends");
    });

    it("routes splits to GET /market-data/splits", async () => {
        const client = await createClient(registerMarketTool);
        await client.callTool({ name: "zorivest_market", arguments: { action: "splits", ticker: "TSLA" } });
        expect(getLastFetchUrl(fetchMock)).toContain("/market-data/splits");
    });

    it("routes insider to GET /market-data/insider", async () => {
        const client = await createClient(registerMarketTool);
        await client.callTool({ name: "zorivest_market", arguments: { action: "insider", ticker: "AAPL" } });
        expect(getLastFetchUrl(fetchMock)).toContain("/market-data/insider");
    });

    it("routes economic_calendar to GET /market-data/economic-calendar", async () => {
        const client = await createClient(registerMarketTool);
        await client.callTool({ name: "zorivest_market", arguments: { action: "economic_calendar" } });
        expect(getLastFetchUrl(fetchMock)).toContain("/market-data/economic-calendar");
    });

    it("routes company_profile to GET /market-data/company-profile", async () => {
        const client = await createClient(registerMarketTool);
        await client.callTool({ name: "zorivest_market", arguments: { action: "company_profile", ticker: "AMZN" } });
        expect(getLastFetchUrl(fetchMock)).toContain("/market-data/company-profile");
    });
});
