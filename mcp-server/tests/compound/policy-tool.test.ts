/**
 * Behavior tests for zorivest_policy compound tool.
 *
 * Verifies all 9 actions route correctly through CompoundToolRouter.
 * Source: mcp-consolidation-proposal-v3.md §10 zorivest_policy
 * Phase: P2.5f corrections (Finding 3)
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { registerPolicyTool } from "../../src/compound/policy-tool.js";
import { createClient, mockFetch, getLastFetchUrl, getLastFetchMethod } from "./helpers.js";

describe("zorivest_policy compound tool", () => {
    let fetchMock: ReturnType<typeof vi.fn>;

    beforeEach(() => { fetchMock = mockFetch(); });
    afterEach(() => vi.restoreAllMocks());

    it("registers exactly 1 tool named zorivest_policy", async () => {
        const client = await createClient(registerPolicyTool);
        const { tools } = await client.listTools();
        expect(tools).toHaveLength(1);
        expect(tools[0].name).toBe("zorivest_policy");
    });

    it("routes create to POST /scheduling/policies", async () => {
        const client = await createClient(registerPolicyTool);
        await client.callTool({
            name: "zorivest_policy",
            arguments: { action: "create", policy_json: { name: "test" } },
        });
        expect(getLastFetchUrl(fetchMock)).toContain("/scheduling/policies");
        expect(getLastFetchMethod(fetchMock)).toBe("POST");
    });

    it("routes list to GET /scheduling/policies", async () => {
        const client = await createClient(registerPolicyTool);
        await client.callTool({ name: "zorivest_policy", arguments: { action: "list" } });
        expect(getLastFetchUrl(fetchMock)).toContain("/scheduling/policies");
    });

    it("routes run to POST /scheduling/policies/:id/run", async () => {
        const client = await createClient(registerPolicyTool);
        await client.callTool({
            name: "zorivest_policy",
            arguments: { action: "run", policy_id: "pol-1" },
        });
        expect(getLastFetchUrl(fetchMock)).toContain("/scheduling/policies/pol-1/run");
        expect(getLastFetchMethod(fetchMock)).toBe("POST");
    });

    it("routes preview to POST /scheduling/policies/:id/run (dry_run)", async () => {
        const client = await createClient(registerPolicyTool);
        await client.callTool({
            name: "zorivest_policy",
            arguments: { action: "preview", policy_id: "pol-1" },
        });
        expect(getLastFetchUrl(fetchMock)).toContain("/scheduling/policies/pol-1/run");
    });

    it("routes get_history to GET /scheduling/policies/:id/runs", async () => {
        const client = await createClient(registerPolicyTool);
        await client.callTool({
            name: "zorivest_policy",
            arguments: { action: "get_history", policy_id: "pol-1" },
        });
        expect(getLastFetchUrl(fetchMock)).toContain("/scheduling/policies/pol-1/runs");
    });

    it("routes delete to DELETE /scheduling/policies/:id (pass-through mode)", async () => {
        const client = await createClient(registerPolicyTool);
        await client.callTool({
            name: "zorivest_policy",
            arguments: { action: "delete", policy_id: "pol-1" },
        });
        expect(getLastFetchUrl(fetchMock)).toContain("/scheduling/policies/pol-1");
        expect(getLastFetchMethod(fetchMock)).toBe("DELETE");
    });

    it("routes update to PUT /scheduling/policies/:id", async () => {
        const client = await createClient(registerPolicyTool);
        await client.callTool({
            name: "zorivest_policy",
            arguments: { action: "update", policy_id: "pol-1", policy_json: { name: "updated" } },
        });
        expect(getLastFetchUrl(fetchMock)).toContain("/scheduling/policies/pol-1");
        expect(getLastFetchMethod(fetchMock)).toBe("PUT");
    });

    it("routes emulate to POST /scheduling/emulator/run", async () => {
        const client = await createClient(registerPolicyTool);
        await client.callTool({
            name: "zorivest_policy",
            arguments: { action: "emulate", policy_json: { steps: [] } },
        });
        expect(getLastFetchUrl(fetchMock)).toContain("/scheduling/emulator/run");
        expect(getLastFetchMethod(fetchMock)).toBe("POST");
    });

    it("rejects unknown action", async () => {
        const client = await createClient(registerPolicyTool);
        const result = await client.callTool({ name: "zorivest_policy", arguments: { action: "nonexistent" } });
        expect(result.isError).toBe(true);
    });

    it("description includes GUI-only approval gate (M7/AC-2)", async () => {
        // The policy tool description must mention the GUI-only approval requirement
        // per emerging-standards.md §M7 and canonical docs 05g/06e.
        // This assertion would have caught the original discoverability gap.
        const client = await createClient(registerPolicyTool);
        const { tools } = await client.listTools();
        const desc = tools[0].description ?? "";
        expect(desc).toContain("approve");
        expect(desc).toContain("GUI");
        expect(desc).toContain("agents cannot");
    });
});
