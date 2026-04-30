/**
 * Behavior tests for zorivest_report compound tool.
 *
 * Verifies all 2 actions using v3.1 contract action names.
 * Source: mcp-consolidation-proposal-v3.md §3 zorivest_report
 * Phase: P2.5f corrections (Findings 2+3)
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { registerReportTool } from "../../src/compound/report-tool.js";
import { createClient, mockFetch, getLastFetchUrl, getLastFetchMethod } from "./helpers.js";

describe("zorivest_report compound tool", () => {
    let fetchMock: ReturnType<typeof vi.fn>;

    beforeEach(() => { fetchMock = mockFetch(); });
    afterEach(() => vi.restoreAllMocks());

    it("registers exactly 1 tool named zorivest_report", async () => {
        const client = await createClient(registerReportTool);
        const { tools } = await client.listTools();
        expect(tools).toHaveLength(1);
        expect(tools[0].name).toBe("zorivest_report");
    });

    it("exposes v3.1 action names (create, get) in description", async () => {
        const client = await createClient(registerReportTool);
        const { tools } = await client.listTools();
        const desc = tools[0].description ?? "";
        expect(desc).toContain("create");
        expect(desc).toContain("get");
    });

    it("routes create to POST /trades/:id/report", async () => {
        const client = await createClient(registerReportTool);
        await client.callTool({
            name: "zorivest_report",
            arguments: {
                action: "create", trade_id: "trade-1",
                setup_quality: "A", execution_quality: "B", followed_plan: true,
            },
        });
        expect(getLastFetchUrl(fetchMock)).toContain("/trades/trade-1/report");
        expect(getLastFetchMethod(fetchMock)).toBe("POST");
    });

    it("routes get to GET /trades/:id/report", async () => {
        const client = await createClient(registerReportTool);
        await client.callTool({
            name: "zorivest_report",
            arguments: { action: "get", trade_id: "trade-1" },
        });
        expect(getLastFetchUrl(fetchMock)).toContain("/trades/trade-1/report");
        expect(getLastFetchMethod(fetchMock)).toBe("GET");
    });

    it("rejects unknown action", async () => {
        const client = await createClient(registerReportTool);
        const result = await client.callTool({
            name: "zorivest_report",
            arguments: { action: "nonexistent" },
        });
        expect(result.isError).toBe(true);
    });
});
