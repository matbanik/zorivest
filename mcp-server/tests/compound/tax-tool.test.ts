/**
 * Behavior tests for zorivest_tax compound tool.
 *
 * All 4 actions return 501 Not Implemented.
 * Source: mcp-consolidation-proposal-v3.md §13 zorivest_tax
 * Phase: P2.5f corrections (Finding 3)
 */

import { describe, it, expect, vi, afterEach } from "vitest";
import { registerTaxTool } from "../../src/compound/tax-tool.js";
import { createClient, getResultText } from "./helpers.js";

describe("zorivest_tax compound tool", () => {
    afterEach(() => vi.restoreAllMocks());

    it("registers exactly 1 tool named zorivest_tax", async () => {
        const client = await createClient(registerTaxTool);
        const { tools } = await client.listTools();
        expect(tools).toHaveLength(1);
        expect(tools[0].name).toBe("zorivest_tax");
    });

    for (const action of ["estimate", "wash_sales", "manage_lots", "harvest"] as const) {
        it(`${action} returns 501 Not Implemented`, async () => {
            const client = await createClient(registerTaxTool);
            const result = await client.callTool({
                name: "zorivest_tax",
                arguments: { action },
            });
            expect(getResultText(result)).toContain("501");
        });
    }

    it("rejects unknown action", async () => {
        const client = await createClient(registerTaxTool);
        const result = await client.callTool({ name: "zorivest_tax", arguments: { action: "nonexistent" } });
        expect(result.isError).toBe(true);
    });
});
