/**
 * Behavior tests for zorivest_db compound tool.
 *
 * Verifies all 5 actions route correctly through CompoundToolRouter.
 * Source: mcp-consolidation-proposal-v3.md §12 zorivest_db
 * Phase: P2.5f corrections (Finding 3)
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { registerDbTool } from "../../src/compound/db-tool.js";
import { createClient, mockFetch, getLastFetchUrl, getLastFetchMethod } from "./helpers.js";

describe("zorivest_db compound tool", () => {
    let fetchMock: ReturnType<typeof vi.fn>;

    beforeEach(() => { fetchMock = mockFetch(); });
    afterEach(() => vi.restoreAllMocks());

    it("registers exactly 1 tool named zorivest_db", async () => {
        const client = await createClient(registerDbTool);
        const { tools } = await client.listTools();
        expect(tools).toHaveLength(1);
        expect(tools[0].name).toBe("zorivest_db");
    });

    it("routes validate_sql to POST /scheduling/validate-sql", async () => {
        const client = await createClient(registerDbTool);
        await client.callTool({
            name: "zorivest_db",
            arguments: { action: "validate_sql", sql: "SELECT 1" },
        });
        expect(getLastFetchUrl(fetchMock)).toContain("/scheduling/validate-sql");
        expect(getLastFetchMethod(fetchMock)).toBe("POST");
    });

    it("routes list_tables to GET /scheduling/db-schema", async () => {
        const client = await createClient(registerDbTool);
        await client.callTool({ name: "zorivest_db", arguments: { action: "list_tables" } });
        expect(getLastFetchUrl(fetchMock)).toContain("/scheduling/db-schema");
    });

    it("routes row_samples to GET /scheduling/db-schema/samples/:table", async () => {
        const client = await createClient(registerDbTool);
        await client.callTool({
            name: "zorivest_db",
            arguments: { action: "row_samples", table: "trades" },
        });
        expect(getLastFetchUrl(fetchMock)).toContain("/scheduling/db-schema/samples/trades");
    });

    it("routes step_types to GET /scheduling/step-types", async () => {
        const client = await createClient(registerDbTool);
        await client.callTool({ name: "zorivest_db", arguments: { action: "step_types" } });
        expect(getLastFetchUrl(fetchMock)).toContain("/scheduling/step-types");
    });

    it("routes provider_capabilities to GET /market-data/providers", async () => {
        const client = await createClient(registerDbTool);
        await client.callTool({ name: "zorivest_db", arguments: { action: "provider_capabilities" } });
        expect(getLastFetchUrl(fetchMock)).toContain("/market-data/providers");
    });

    it("rejects unknown action", async () => {
        const client = await createClient(registerDbTool);
        const result = await client.callTool({ name: "zorivest_db", arguments: { action: "nonexistent" } });
        expect(result.isError).toBe(true);
    });
});
