/**
 * Unit tests for trade analytics MCP tools.
 *
 * Tests verify all 14 analytics tools call correct REST endpoints,
 * forward params/body correctly, and return standard envelope.
 * Uses mocked global.fetch — no live API needed.
 *
 * Source: 05c-mcp-trade-analytics.md, FIC AC-1 through AC-7
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { registerAnalyticsTools } from "../src/tools/analytics-tools.js";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { InMemoryTransport } from "@modelcontextprotocol/sdk/inMemory.js";

// ── Test helpers ───────────────────────────────────────────────────────

async function createTestClient(): Promise<Client> {
    const server = new McpServer({ name: "test", version: "0.1.0" });
    registerAnalyticsTools(server);

    const [clientTransport, serverTransport] =
        InMemoryTransport.createLinkedPair();
    const client = new Client({ name: "test-client", version: "0.1.0" });

    await Promise.all([
        client.connect(clientTransport),
        server.connect(serverTransport),
    ]);

    return client;
}

function mockApiResponse(expectedData: unknown = { success: true }): void {
    vi.stubGlobal(
        "fetch",
        vi.fn().mockResolvedValue({
            ok: true,
            json: () => Promise.resolve(expectedData),
        }),
    );
}

function getLastFetchCall(): { url: string; init?: RequestInit } {
    const mock = fetch as ReturnType<typeof vi.fn>;
    const lastCall = mock.mock.calls[mock.mock.calls.length - 1];
    return { url: lastCall[0] as string, init: lastCall[1] as RequestInit };
}

// ── Tests ──────────────────────────────────────────────────────────────

describe("trade analytics tools", () => {
    beforeEach(() => {
        vi.restoreAllMocks();
    });

    // 1. get_round_trips
    it("get_round_trips calls GET /round-trips with query params", async () => {
        mockApiResponse({ data: [{ id: "rt-1" }] });

        const client = await createTestClient();
        const result = await client.callTool({
            name: "get_round_trips",
            arguments: { account_id: "acc-1", status: "closed" },
        });

        const { url, init } = getLastFetchCall();
        expect(url).toContain("/round-trips");
        expect(url).toContain("account_id=acc-1");
        expect(url).toContain("status=closed");
        expect(init?.method ?? "GET").toBe("GET");

        const content = result.content as Array<{
            type: string;
            text: string;
        }>;
        expect(content[0].type).toBe("text");
        expect(JSON.parse(content[0].text)).toHaveProperty("data");
    });

    // 2. enrich_trade_excursion
    it("enrich_trade_excursion calls POST /analytics/excursion/{id}", async () => {
        mockApiResponse({ mfe: 2.5, mae: -1.2 });

        const client = await createTestClient();
        await client.callTool({
            name: "enrich_trade_excursion",
            arguments: { trade_exec_id: "exec-42" },
        });

        const { url, init } = getLastFetchCall();
        expect(url).toContain("/analytics/excursion/exec-42");
        expect(init?.method).toBe("POST");
    });

    // 3. get_fee_breakdown
    it("get_fee_breakdown calls GET /fees/summary with period", async () => {
        mockApiResponse({ commission: 4.95 });

        const client = await createTestClient();
        await client.callTool({
            name: "get_fee_breakdown",
            arguments: { period: "q1" },
        });

        const { url } = getLastFetchCall();
        expect(url).toContain("/fees/summary");
        expect(url).toContain("period=q1");
    });

    // 4. score_execution_quality
    it("score_execution_quality calls GET /analytics/execution-quality with trade_id", async () => {
        mockApiResponse({ grade: "A", slippage_bps: 0.5 });

        const client = await createTestClient();
        await client.callTool({
            name: "score_execution_quality",
            arguments: { trade_exec_id: "exec-99" },
        });

        const { url } = getLastFetchCall();
        expect(url).toContain("/analytics/execution-quality");
        expect(url).toContain("trade_id=exec-99");
    });

    // 5. estimate_pfof_impact
    it("estimate_pfof_impact calls GET /analytics/pfof-report", async () => {
        mockApiResponse({ estimated_cost: 12.5 });

        const client = await createTestClient();
        await client.callTool({
            name: "estimate_pfof_impact",
            arguments: { account_id: "acc-1", period: "ytd" },
        });

        const { url } = getLastFetchCall();
        expect(url).toContain("/analytics/pfof-report");
        expect(url).toContain("account_id=acc-1");
    });

    // 6. get_expectancy_metrics
    it("get_expectancy_metrics calls GET /analytics/expectancy", async () => {
        mockApiResponse({ expectancy: 1.5, kelly_pct: 12 });

        const client = await createTestClient();
        await client.callTool({
            name: "get_expectancy_metrics",
            arguments: { period: "all" },
        });

        const { url } = getLastFetchCall();
        expect(url).toContain("/analytics/expectancy");
        expect(url).toContain("period=all");
    });

    // 7. simulate_drawdown
    it("simulate_drawdown calls GET /analytics/drawdown with simulations", async () => {
        mockApiResponse({ max_drawdown_pct: 15 });

        const client = await createTestClient();
        await client.callTool({
            name: "simulate_drawdown",
            arguments: { simulations: 5000 },
        });

        const { url } = getLastFetchCall();
        expect(url).toContain("/analytics/drawdown");
        expect(url).toContain("simulations=5000");
    });

    // 8. get_strategy_breakdown
    it("get_strategy_breakdown calls GET /analytics/strategy-breakdown", async () => {
        mockApiResponse({ strategies: [] });

        const client = await createTestClient();
        await client.callTool({
            name: "get_strategy_breakdown",
            arguments: { account_id: "acc-1" },
        });

        const { url } = getLastFetchCall();
        expect(url).toContain("/analytics/strategy-breakdown");
        expect(url).toContain("account_id=acc-1");
    });

    // 9. get_sqn
    it("get_sqn calls GET /analytics/sqn with period", async () => {
        mockApiResponse({ sqn: 2.8, grade: "excellent" });

        const client = await createTestClient();
        await client.callTool({
            name: "get_sqn",
            arguments: { period: "all" },
        });

        const { url } = getLastFetchCall();
        expect(url).toContain("/analytics/sqn");
        expect(url).toContain("period=all");
    });

    // 10. get_cost_of_free
    it("get_cost_of_free calls GET /analytics/cost-of-free", async () => {
        mockApiResponse({ hidden_cost: 45 });

        const client = await createTestClient();
        await client.callTool({
            name: "get_cost_of_free",
            arguments: { period: "ytd" },
        });

        const { url } = getLastFetchCall();
        expect(url).toContain("/analytics/cost-of-free");
        expect(url).toContain("period=ytd");
    });

    // 11. ai_review_trade
    it("ai_review_trade calls POST /analytics/ai-review with body", async () => {
        mockApiResponse({ review: "Strong entry" });

        const client = await createTestClient();
        await client.callTool({
            name: "ai_review_trade",
            arguments: { trade_exec_id: "exec-1", review_type: "single" },
        });

        const { url, init } = getLastFetchCall();
        expect(url).toContain("/analytics/ai-review");
        expect(init?.method).toBe("POST");
        const body = JSON.parse(init?.body as string);
        expect(body.trade_exec_id).toBe("exec-1");
        expect(body.review_type).toBe("single");
    });

    // 12. detect_options_strategy
    it("detect_options_strategy calls POST /analytics/options-strategy with leg_exec_ids", async () => {
        mockApiResponse({ strategy: "iron_condor" });

        const client = await createTestClient();
        await client.callTool({
            name: "detect_options_strategy",
            arguments: { leg_exec_ids: ["leg-1", "leg-2", "leg-3", "leg-4"] },
        });

        const { url, init } = getLastFetchCall();
        expect(url).toContain("/analytics/options-strategy");
        expect(init?.method).toBe("POST");
        const body = JSON.parse(init?.body as string);
        expect(body.leg_exec_ids).toEqual([
            "leg-1",
            "leg-2",
            "leg-3",
            "leg-4",
        ]);
    });

    // 13. create_report
    it("create_report calls POST /trades/{trade_id}/report with body", async () => {
        mockApiResponse({ id: 1, trade_id: "exec-5" });

        const client = await createTestClient();
        const result = await client.callTool({
            name: "create_report",
            arguments: {
                trade_id: "exec-5",
                setup_quality: "A",
                execution_quality: "B",
                followed_plan: true,
                emotional_state: "calm",
                lessons_learned: "Good patience",
                tags: ["momentum", "swing"],
            },
        });

        const { url, init } = getLastFetchCall();
        expect(url).toContain("/trades/exec-5/report");
        expect(init?.method).toBe("POST");
        const body = JSON.parse(init?.body as string);
        expect(body.trade_id).toBe("exec-5");
        expect(body.setup_quality).toBe("A");
        expect(body.execution_quality).toBe("B");
        expect(body.followed_plan).toBe(true);
        expect(body.emotional_state).toBe("calm");
        expect(body.tags).toEqual(["momentum", "swing"]);

        const content = result.content as Array<{
            type: string;
            text: string;
        }>;
        expect(content[0].type).toBe("text");
        expect(JSON.parse(content[0].text)).toHaveProperty("success");
    });

    // 14. get_report_for_trade
    it("get_report_for_trade calls GET /trades/{trade_id}/report", async () => {
        mockApiResponse({ id: 1, setup_quality: "A" });

        const client = await createTestClient();
        const result = await client.callTool({
            name: "get_report_for_trade",
            arguments: { trade_id: "exec-5" },
        });

        const { url, init } = getLastFetchCall();
        expect(url).toContain("/trades/exec-5/report");
        expect(init?.method ?? "GET").toBe("GET");

        const content = result.content as Array<{
            type: string;
            text: string;
        }>;
        expect(content[0].type).toBe("text");
        expect(JSON.parse(content[0].text)).toHaveProperty("success");
    });

    // Metadata: annotations per spec
    it("registers all 14 tools with correct annotations", async () => {
        mockApiResponse();

        const client = await createTestClient();
        const { tools } = await client.listTools();

        const expectedTools = [
            "get_round_trips",
            "enrich_trade_excursion",
            "get_fee_breakdown",
            "score_execution_quality",
            "estimate_pfof_impact",
            "get_expectancy_metrics",
            "simulate_drawdown",
            "get_strategy_breakdown",
            "get_sqn",
            "get_cost_of_free",
            "ai_review_trade",
            "detect_options_strategy",
            "create_report",
            "get_report_for_trade",
        ];

        // All 12 tools registered
        for (const name of expectedTools) {
            const tool = tools.find((t) => t.name === name);
            expect(tool, `tool '${name}' should be registered`).toBeDefined();
        }

        // Check readOnly annotation for non-mutating tools
        const readOnlyTools = tools.filter(
            (t) =>
                expectedTools.includes(t.name) &&
                t.name !== "enrich_trade_excursion" &&
                t.name !== "create_report",
        );
        for (const tool of readOnlyTools) {
            expect(
                tool.annotations?.readOnlyHint,
                `${tool.name} should be readOnly`,
            ).toBe(true);
        }

        // enrich_trade_excursion is NOT readOnly (writes excursion data)
        const excursion = tools.find(
            (t) => t.name === "enrich_trade_excursion",
        );
        expect(excursion!.annotations?.readOnlyHint).toBe(false);

        // _meta per FIC (vendor extension — cast to access)
        for (const name of expectedTools) {
            const tool = tools.find((t) => t.name === name);
            const meta = (tool as Record<string, unknown>)._meta as
                | Record<string, unknown>
                | undefined;
            expect(
                meta,
                `${name} should have _meta`,
            ).toBeDefined();
            expect(
                meta!.toolset,
                `${name} _meta.toolset should be "trade-analytics"`,
            ).toBe("trade-analytics");
            expect(
                meta!.alwaysLoaded,
                `${name} _meta.alwaysLoaded should be false`,
            ).toBe(false);
        }
    });
});
