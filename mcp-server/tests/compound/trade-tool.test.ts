/**
 * Behavior tests for zorivest_trade compound tool.
 *
 * Verifies all 6 actions route correctly through CompoundToolRouter.
 * Source: mcp-consolidation-proposal-v3.md §2 zorivest_trade
 * Phase: P2.5f corrections (Finding 3)
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { registerTradeTool } from "../../src/compound/trade-tool.js";
import { createClient, mockFetch, getLastFetchUrl, getLastFetchMethod } from "./helpers.js";

describe("zorivest_trade compound tool", () => {
    let fetchMock: ReturnType<typeof vi.fn>;

    beforeEach(() => { fetchMock = mockFetch(); });
    afterEach(() => vi.restoreAllMocks());

    it("registers exactly 1 tool named zorivest_trade", async () => {
        const client = await createClient(registerTradeTool);
        const { tools } = await client.listTools();
        expect(tools).toHaveLength(1);
        expect(tools[0].name).toBe("zorivest_trade");
    });

    it("routes list to GET /trades", async () => {
        const client = await createClient(registerTradeTool);
        await client.callTool({ name: "zorivest_trade", arguments: { action: "list" } });
        expect(getLastFetchUrl(fetchMock)).toContain("/trades");
    });

    it("routes create to POST /trades (pass-through mode)", async () => {
        const client = await createClient(registerTradeTool);
        await client.callTool({
            name: "zorivest_trade",
            arguments: {
                action: "create", exec_id: "exec-1", instrument: "AAPL",
                trade_action: "BOT", quantity: 100, price: 150.0, account_id: "acc-1",
            },
        });
        // In default (dynamic) mode, confirmation is bypassed
        expect(getLastFetchUrl(fetchMock)).toContain("/trades");
        expect(getLastFetchMethod(fetchMock)).toBe("POST");
    });

    it("routes delete to DELETE /trades/:id (pass-through mode)", async () => {
        const client = await createClient(registerTradeTool);
        await client.callTool({
            name: "zorivest_trade",
            arguments: { action: "delete", exec_id: "exec-1" },
        });
        expect(getLastFetchUrl(fetchMock)).toContain("/trades/exec-1");
        expect(getLastFetchMethod(fetchMock)).toBe("DELETE");
    });

    it("routes screenshot_list to GET /trades/:id/images", async () => {
        const client = await createClient(registerTradeTool);
        await client.callTool({
            name: "zorivest_trade",
            arguments: { action: "screenshot_list", exec_id: "exec-1" },
        });
        expect(getLastFetchUrl(fetchMock)).toContain("/trades/exec-1/images");
    });

    it("routes screenshot_attach to POST /trades/:id/images", async () => {
        const client = await createClient(registerTradeTool);
        await client.callTool({
            name: "zorivest_trade",
            arguments: {
                action: "screenshot_attach", exec_id: "exec-1",
                image_base64: "aGVsbG8=", caption: "Entry chart",
            },
        });
        expect(getLastFetchUrl(fetchMock)).toContain("/trades/exec-1/images");
        expect(getLastFetchMethod(fetchMock)).toBe("POST");
    });

    it("rejects unknown action", async () => {
        const client = await createClient(registerTradeTool);
        const result = await client.callTool({ name: "zorivest_trade", arguments: { action: "nonexistent" } });
        expect(result.isError).toBe(true);
    });
});
