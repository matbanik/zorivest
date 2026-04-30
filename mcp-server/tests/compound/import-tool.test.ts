/**
 * Behavior tests for zorivest_import compound tool.
 *
 * Verifies 501 stubs and destructive action routing.
 * Source: mcp-consolidation-proposal-v3.md §7 zorivest_import
 * Phase: P2.5f corrections (Finding 3)
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { registerImportTool } from "../../src/compound/import-tool.js";
import { createClient, mockFetch, getResultText, getLastFetchUrl, getLastFetchMethod } from "./helpers.js";

describe("zorivest_import compound tool", () => {
    let fetchMock: ReturnType<typeof vi.fn>;

    beforeEach(() => { fetchMock = mockFetch(); });
    afterEach(() => vi.restoreAllMocks());

    it("registers exactly 1 tool named zorivest_import", async () => {
        const client = await createClient(registerImportTool);
        const { tools } = await client.listTools();
        expect(tools).toHaveLength(1);
        expect(tools[0].name).toBe("zorivest_import");
    });

    it("list_brokers returns 501 Not Implemented", async () => {
        const client = await createClient(registerImportTool);
        const result = await client.callTool({
            name: "zorivest_import",
            arguments: { action: "list_brokers" },
        });
        expect(getResultText(result)).toContain("501");
    });

    it("resolve_identifiers returns 501 Not Implemented", async () => {
        const client = await createClient(registerImportTool);
        const result = await client.callTool({
            name: "zorivest_import",
            arguments: {
                action: "resolve_identifiers",
                identifiers: [{ id_type: "cusip", id_value: "037833100" }],
            },
        });
        expect(getResultText(result)).toContain("501");
    });

    it("list_bank_accounts returns 501 Not Implemented", async () => {
        const client = await createClient(registerImportTool);
        const result = await client.callTool({
            name: "zorivest_import",
            arguments: { action: "list_bank_accounts" },
        });
        expect(getResultText(result)).toContain("501");
    });

    it("routes sync_broker to POST /brokers/:id/sync (pass-through mode)", async () => {
        const client = await createClient(registerImportTool);
        await client.callTool({
            name: "zorivest_import",
            arguments: { action: "sync_broker", broker_id: "ib-1" },
        });
        expect(getLastFetchUrl(fetchMock)).toContain("/brokers/ib-1/sync");
        expect(getLastFetchMethod(fetchMock)).toBe("POST");
    });

    it("broker_csv action is accepted (routes to uploadFile helper)", async () => {
        // broker_csv uses uploadFile() which reads from disk — we verify the action
        // exists in the schema by checking it dispatches (produces fs error, not schema error).
        const client = await createClient(registerImportTool);
        const result = await client.callTool({
            name: "zorivest_import",
            arguments: { action: "broker_csv", file_path: "/nonexistent/file.csv", account_id: "acc-1" },
        });
        // The action dispatches but fails on fs.readFileSync — this is expected.
        // Key: it's a runtime error, NOT "Unknown action: broker_csv"
        const text = getResultText(result);
        expect(text).not.toContain("Unknown action");
    });

    it("rejects unknown action", async () => {
        const client = await createClient(registerImportTool);
        const result = await client.callTool({ name: "zorivest_import", arguments: { action: "nonexistent" } });
        expect(result.isError).toBe(true);
    });
});
