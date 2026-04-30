/**
 * Behavior tests for zorivest_account compound tool.
 *
 * Verifies all 9 actions route correctly through CompoundToolRouter.
 * Source: mcp-consolidation-proposal-v3.md §6 zorivest_account
 * Phase: P2.5f corrections (Finding 3)
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { registerAccountTool } from "../../src/compound/account-tool.js";
import { createClient, mockFetch, getResultText, getLastFetchUrl, getLastFetchMethod, getFetchUrl } from "./helpers.js";

describe("zorivest_account compound tool", () => {
    let fetchMock: ReturnType<typeof vi.fn>;

    beforeEach(() => {
        fetchMock = vi.fn().mockImplementation(() =>
            Promise.resolve({
                ok: true, status: 200,
                json: () => Promise.resolve({ data: [] }),
            }),
        );
        vi.stubGlobal("fetch", fetchMock);
    });
    afterEach(() => vi.restoreAllMocks());

    it("registers exactly 1 tool named zorivest_account", async () => {
        const client = await createClient(registerAccountTool);
        const { tools } = await client.listTools();
        expect(tools).toHaveLength(1);
        expect(tools[0].name).toBe("zorivest_account");
    });

    it("routes list to GET /accounts", async () => {
        const client = await createClient(registerAccountTool);
        await client.callTool({ name: "zorivest_account", arguments: { action: "list" } });
        expect(getLastFetchUrl(fetchMock)).toContain("/accounts");
    });

    it("routes get to GET /accounts/:id", async () => {
        const client = await createClient(registerAccountTool);
        await client.callTool({ name: "zorivest_account", arguments: { action: "get", account_id: "acc-1" } });
        expect(getLastFetchUrl(fetchMock)).toContain("/accounts/acc-1");
    });

    it("routes create to POST /accounts", async () => {
        const client = await createClient(registerAccountTool);
        await client.callTool({
            name: "zorivest_account",
            arguments: { action: "create", name: "Test Account", account_type: "BROKER" },
        });
        expect(getLastFetchUrl(fetchMock)).toContain("/accounts");
        expect(getLastFetchMethod(fetchMock)).toBe("POST");
    });

    it("routes update to PUT /accounts/:id", async () => {
        const client = await createClient(registerAccountTool);
        await client.callTool({
            name: "zorivest_account",
            arguments: { action: "update", account_id: "acc-1", name: "Renamed" },
        });
        expect(getLastFetchUrl(fetchMock)).toContain("/accounts/acc-1");
        expect(getLastFetchMethod(fetchMock)).toBe("PUT");
    });

    it("routes delete to DELETE /accounts/:id (pass-through mode)", async () => {
        const client = await createClient(registerAccountTool);
        await client.callTool({
            name: "zorivest_account",
            arguments: { action: "delete", account_id: "acc-1" },
        });
        expect(getLastFetchUrl(fetchMock)).toContain("/accounts/acc-1");
        expect(getLastFetchMethod(fetchMock)).toBe("DELETE");
    });

    it("routes archive to POST /accounts/:id:archive", async () => {
        const client = await createClient(registerAccountTool);
        await client.callTool({
            name: "zorivest_account",
            arguments: { action: "archive", account_id: "acc-1" },
        });
        expect(getLastFetchUrl(fetchMock)).toContain("/accounts/acc-1:archive");
        expect(getLastFetchMethod(fetchMock)).toBe("POST");
    });

    it("routes reassign to POST /accounts/:id:reassign-trades (pass-through mode)", async () => {
        const client = await createClient(registerAccountTool);
        await client.callTool({
            name: "zorivest_account",
            arguments: { action: "reassign", account_id: "acc-1" },
        });
        expect(getLastFetchUrl(fetchMock)).toContain("/accounts/acc-1:reassign-trades");
        expect(getLastFetchMethod(fetchMock)).toBe("POST");
    });

    it("routes balance to POST /accounts/:id/balances", async () => {
        const client = await createClient(registerAccountTool);
        await client.callTool({
            name: "zorivest_account",
            arguments: { action: "balance", account_id: "acc-1", balance: 50000 },
        });
        expect(getLastFetchUrl(fetchMock)).toContain("/accounts/acc-1/balances");
        expect(getLastFetchMethod(fetchMock)).toBe("POST");
    });

    it("routes checklist to aggregated /brokers + /banking/accounts", async () => {
        const client = await createClient(registerAccountTool);
        await client.callTool({
            name: "zorivest_account",
            arguments: { action: "checklist" },
        });
        // Checklist does 2 parallel fetches
        expect(fetchMock).toHaveBeenCalledTimes(2);
        expect(getFetchUrl(fetchMock, 0)).toContain("/brokers");
        expect(getFetchUrl(fetchMock, 1)).toContain("/banking/accounts");
    });

    it("rejects unknown action", async () => {
        const client = await createClient(registerAccountTool);
        const result = await client.callTool({ name: "zorivest_account", arguments: { action: "nonexistent" } });
        expect(result.isError).toBe(true);
    });
});
