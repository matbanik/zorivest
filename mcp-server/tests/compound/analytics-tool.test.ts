/**
 * Behavior tests for zorivest_analytics compound tool.
 *
 * Verifies all 13 actions route correctly through CompoundToolRouter,
 * using v3.1 contract action names (Finding 2 correction).
 *
 * Source: mcp-consolidation-proposal-v3.md §4 zorivest_analytics
 * Phase: P2.5f corrections (Findings 2+3)
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { registerAnalyticsTool } from "../../src/compound/analytics-tool.js";
import { createClient, mockFetch, getResultText, getLastFetchUrl, getLastFetchMethod } from "./helpers.js";

describe("zorivest_analytics compound tool", () => {
    let fetchMock: ReturnType<typeof vi.fn>;

    beforeEach(() => { fetchMock = mockFetch(); });
    afterEach(() => vi.restoreAllMocks());

    it("registers exactly 1 tool named zorivest_analytics", async () => {
        const client = await createClient(registerAnalyticsTool);
        const { tools } = await client.listTools();
        expect(tools).toHaveLength(1);
        expect(tools[0].name).toBe("zorivest_analytics");
    });

    it("exposes v3.1 action names in description", async () => {
        const client = await createClient(registerAnalyticsTool);
        const { tools } = await client.listTools();
        const desc = tools[0].description ?? "";
        for (const action of [
            "position_size", "round_trips", "excursion", "fee_breakdown",
            "execution_quality", "pfof_impact", "expectancy", "drawdown",
            "strategy_breakdown", "sqn", "cost_of_free", "ai_review", "options_strategy",
        ]) {
            expect(desc).toContain(action);
        }
    });

    it("routes position_size to POST /calculator/position-size", async () => {
        const client = await createClient(registerAnalyticsTool);
        await client.callTool({
            name: "zorivest_analytics",
            arguments: {
                action: "position_size", balance: 10000, risk_pct: 2,
                entry_price: 100, stop_loss: 95, target_price: 110,
            },
        });
        expect(getLastFetchUrl(fetchMock)).toContain("/calculator/position-size");
        expect(getLastFetchMethod(fetchMock)).toBe("POST");
    });

    it("routes round_trips to GET /round-trips", async () => {
        const client = await createClient(registerAnalyticsTool);
        await client.callTool({
            name: "zorivest_analytics",
            arguments: { action: "round_trips" },
        });
        expect(getLastFetchUrl(fetchMock)).toContain("/round-trips");
    });

    it("routes excursion to POST /analytics/excursion/:id", async () => {
        const client = await createClient(registerAnalyticsTool);
        await client.callTool({
            name: "zorivest_analytics",
            arguments: { action: "excursion", trade_exec_id: "exec-1" },
        });
        expect(getLastFetchUrl(fetchMock)).toContain("/analytics/excursion/exec-1");
        expect(getLastFetchMethod(fetchMock)).toBe("POST");
    });

    it("routes fee_breakdown to GET /fees/summary", async () => {
        const client = await createClient(registerAnalyticsTool);
        await client.callTool({
            name: "zorivest_analytics",
            arguments: { action: "fee_breakdown" },
        });
        expect(getLastFetchUrl(fetchMock)).toContain("/fees/summary");
    });

    it("routes execution_quality to GET /analytics/execution-quality", async () => {
        const client = await createClient(registerAnalyticsTool);
        await client.callTool({
            name: "zorivest_analytics",
            arguments: { action: "execution_quality", trade_exec_id: "exec-1" },
        });
        expect(getLastFetchUrl(fetchMock)).toContain("/analytics/execution-quality");
    });

    it("routes pfof_impact to GET /analytics/pfof-report", async () => {
        const client = await createClient(registerAnalyticsTool);
        await client.callTool({
            name: "zorivest_analytics",
            arguments: { action: "pfof_impact", account_id: "acc-1" },
        });
        expect(getLastFetchUrl(fetchMock)).toContain("/analytics/pfof-report");
    });

    it("routes expectancy to GET /analytics/expectancy", async () => {
        const client = await createClient(registerAnalyticsTool);
        await client.callTool({
            name: "zorivest_analytics",
            arguments: { action: "expectancy" },
        });
        expect(getLastFetchUrl(fetchMock)).toContain("/analytics/expectancy");
    });

    it("routes drawdown to GET /analytics/drawdown", async () => {
        const client = await createClient(registerAnalyticsTool);
        await client.callTool({
            name: "zorivest_analytics",
            arguments: { action: "drawdown" },
        });
        expect(getLastFetchUrl(fetchMock)).toContain("/analytics/drawdown");
    });

    it("routes strategy_breakdown to GET /analytics/strategy-breakdown", async () => {
        const client = await createClient(registerAnalyticsTool);
        await client.callTool({
            name: "zorivest_analytics",
            arguments: { action: "strategy_breakdown" },
        });
        expect(getLastFetchUrl(fetchMock)).toContain("/analytics/strategy-breakdown");
    });

    it("routes sqn to GET /analytics/sqn", async () => {
        const client = await createClient(registerAnalyticsTool);
        await client.callTool({
            name: "zorivest_analytics",
            arguments: { action: "sqn" },
        });
        expect(getLastFetchUrl(fetchMock)).toContain("/analytics/sqn");
    });

    it("routes cost_of_free to GET /analytics/cost-of-free", async () => {
        const client = await createClient(registerAnalyticsTool);
        await client.callTool({
            name: "zorivest_analytics",
            arguments: { action: "cost_of_free" },
        });
        expect(getLastFetchUrl(fetchMock)).toContain("/analytics/cost-of-free");
    });

    it("routes ai_review to POST /analytics/ai-review", async () => {
        const client = await createClient(registerAnalyticsTool);
        await client.callTool({
            name: "zorivest_analytics",
            arguments: { action: "ai_review", trade_exec_id: "exec-1" },
        });
        expect(getLastFetchUrl(fetchMock)).toContain("/analytics/ai-review");
        expect(getLastFetchMethod(fetchMock)).toBe("POST");
    });

    it("routes options_strategy to POST /analytics/options-strategy", async () => {
        const client = await createClient(registerAnalyticsTool);
        await client.callTool({
            name: "zorivest_analytics",
            arguments: { action: "options_strategy", leg_exec_ids: ["l1", "l2"] },
        });
        expect(getLastFetchUrl(fetchMock)).toContain("/analytics/options-strategy");
        expect(getLastFetchMethod(fetchMock)).toBe("POST");
    });

    it("rejects unknown action", async () => {
        const client = await createClient(registerAnalyticsTool);
        const result = await client.callTool({
            name: "zorivest_analytics",
            arguments: { action: "nonexistent" },
        });
        expect(result.isError).toBe(true);
    });
});
