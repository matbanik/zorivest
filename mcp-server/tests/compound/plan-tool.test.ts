/**
 * Behavior tests for zorivest_plan compound tool.
 *
 * Verifies all 3 actions route correctly through CompoundToolRouter.
 * Source: mcp-consolidation-proposal-v3.md §12 zorivest_plan
 * Phase: P2.5f corrections (Finding 3)
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { registerPlanTool } from "../../src/compound/plan-tool.js";
import { createClient, mockFetch, getLastFetchUrl, getLastFetchMethod } from "./helpers.js";

describe("zorivest_plan compound tool", () => {
    let fetchMock: ReturnType<typeof vi.fn>;

    beforeEach(() => { fetchMock = mockFetch(); });
    afterEach(() => vi.restoreAllMocks());

    it("registers exactly 1 tool named zorivest_plan", async () => {
        const client = await createClient(registerPlanTool);
        const { tools } = await client.listTools();
        expect(tools).toHaveLength(1);
        expect(tools[0].name).toBe("zorivest_plan");
    });

    it("routes list to GET /trade-plans", async () => {
        const client = await createClient(registerPlanTool);
        await client.callTool({ name: "zorivest_plan", arguments: { action: "list" } });
        expect(getLastFetchUrl(fetchMock)).toContain("/trade-plans");
    });

    it("routes create to POST /trade-plans", async () => {
        const client = await createClient(registerPlanTool);
        await client.callTool({
            name: "zorivest_plan",
            arguments: {
                action: "create", ticker: "AAPL", direction: "long",
                strategy_name: "breakout", entry: 150, stop: 145, target: 165,
                conditions: "Above 200 MA", timeframe: "daily",
            },
        });
        expect(getLastFetchUrl(fetchMock)).toContain("/trade-plans");
        expect(getLastFetchMethod(fetchMock)).toBe("POST");
    });

    it("routes delete to DELETE /trade-plans/:id (pass-through mode)", async () => {
        const client = await createClient(registerPlanTool);
        await client.callTool({
            name: "zorivest_plan",
            arguments: { action: "delete", plan_id: 42 },
        });
        expect(getLastFetchUrl(fetchMock)).toContain("/trade-plans/42");
        expect(getLastFetchMethod(fetchMock)).toBe("DELETE");
    });

    it("rejects unknown action", async () => {
        const client = await createClient(registerPlanTool);
        const result = await client.callTool({ name: "zorivest_plan", arguments: { action: "nonexistent" } });
        expect(result.isError).toBe(true);
    });
});
