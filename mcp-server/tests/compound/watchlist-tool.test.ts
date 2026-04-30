/**
 * Behavior tests for zorivest_watchlist compound tool.
 *
 * Verifies all 5 actions route correctly through CompoundToolRouter.
 * Source: mcp-consolidation-proposal-v3.md §8 zorivest_watchlist
 * Phase: P2.5f corrections (Finding 3)
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { registerWatchlistTool } from "../../src/compound/watchlist-tool.js";
import { createClient, mockFetch, getLastFetchUrl, getLastFetchMethod } from "./helpers.js";

describe("zorivest_watchlist compound tool", () => {
    let fetchMock: ReturnType<typeof vi.fn>;

    beforeEach(() => { fetchMock = mockFetch(); });
    afterEach(() => vi.restoreAllMocks());

    it("registers exactly 1 tool named zorivest_watchlist", async () => {
        const client = await createClient(registerWatchlistTool);
        const { tools } = await client.listTools();
        expect(tools).toHaveLength(1);
        expect(tools[0].name).toBe("zorivest_watchlist");
    });

    it("routes create to POST /watchlists/", async () => {
        const client = await createClient(registerWatchlistTool);
        await client.callTool({ name: "zorivest_watchlist", arguments: { action: "create", name: "Tech" } });
        expect(getLastFetchUrl(fetchMock)).toContain("/watchlists/");
        expect(getLastFetchMethod(fetchMock)).toBe("POST");
    });

    it("routes list to GET /watchlists/", async () => {
        const client = await createClient(registerWatchlistTool);
        await client.callTool({ name: "zorivest_watchlist", arguments: { action: "list" } });
        expect(getLastFetchUrl(fetchMock)).toContain("/watchlists/");
    });

    it("routes get to GET /watchlists/:id", async () => {
        const client = await createClient(registerWatchlistTool);
        await client.callTool({ name: "zorivest_watchlist", arguments: { action: "get", watchlist_id: 1 } });
        expect(getLastFetchUrl(fetchMock)).toContain("/watchlists/1");
    });

    it("routes add_ticker to POST /watchlists/:id/items", async () => {
        const client = await createClient(registerWatchlistTool);
        await client.callTool({
            name: "zorivest_watchlist",
            arguments: { action: "add_ticker", watchlist_id: 1, ticker: "AAPL" },
        });
        expect(getLastFetchUrl(fetchMock)).toContain("/watchlists/1/items");
        expect(getLastFetchMethod(fetchMock)).toBe("POST");
    });

    it("routes remove_ticker to DELETE /watchlists/:id/items/:ticker", async () => {
        const client = await createClient(registerWatchlistTool);
        await client.callTool({
            name: "zorivest_watchlist",
            arguments: { action: "remove_ticker", watchlist_id: 1, ticker: "AAPL" },
        });
        expect(getLastFetchUrl(fetchMock)).toContain("/watchlists/1/items/AAPL");
        expect(getLastFetchMethod(fetchMock)).toBe("DELETE");
    });

    it("rejects unknown action", async () => {
        const client = await createClient(registerWatchlistTool);
        const result = await client.callTool({ name: "zorivest_watchlist", arguments: { action: "nonexistent" } });
        expect(result.isError).toBe(true);
    });
});
