/**
 * Behavior tests for zorivest_tax compound tool.
 *
 * Verifies all 8 actions route correctly through CompoundToolRouter
 * to the correct REST endpoints with proper HTTP methods.
 *
 * Source: Phase 3E tax-engine-wiring corrections (Finding 5)
 * Pattern: matches account-tool.test.ts dispatch pattern
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { registerTaxTool } from "../../src/compound/tax-tool.js";
import {
    createClient,
    mockFetch,
    getResultText,
    getLastFetchUrl,
    getLastFetchMethod,
} from "./helpers.js";

describe("zorivest_tax compound tool", () => {
    let fetchMock: ReturnType<typeof vi.fn>;

    beforeEach(() => {
        fetchMock = vi.fn().mockImplementation(() =>
            Promise.resolve({
                ok: true,
                status: 200,
                json: () => Promise.resolve({ success: true, data: {} }),
            }),
        );
        vi.stubGlobal("fetch", fetchMock);
    });
    afterEach(() => vi.restoreAllMocks());

    // ── Registration ─────────────────────────────────────────────────

    it("registers exactly 1 tool named zorivest_tax", async () => {
        const client = await createClient(registerTaxTool);
        const { tools } = await client.listTools();
        expect(tools).toHaveLength(1);
        expect(tools[0].name).toBe("zorivest_tax");
    });

    // ── 8 action dispatch ────────────────────────────────────────────

    it("routes simulate to POST /tax/simulate", async () => {
        const client = await createClient(registerTaxTool);
        await client.callTool({
            name: "zorivest_tax",
            arguments: {
                action: "simulate",
                ticker: "AAPL",
                quantity: 100,
                price: 150.0,
                account_id: "DU123",
            },
        });
        expect(getLastFetchUrl(fetchMock)).toContain("/tax/simulate");
        expect(getLastFetchMethod(fetchMock)).toBe("POST");
    });

    it("routes estimate to POST /tax/estimate", async () => {
        const client = await createClient(registerTaxTool);
        await client.callTool({
            name: "zorivest_tax",
            arguments: { action: "estimate", tax_year: 2026 },
        });
        expect(getLastFetchUrl(fetchMock)).toContain("/tax/estimate");
        expect(getLastFetchMethod(fetchMock)).toBe("POST");
    });

    it("routes wash_sales to POST /tax/wash-sales", async () => {
        const client = await createClient(registerTaxTool);
        await client.callTool({
            name: "zorivest_tax",
            arguments: { action: "wash_sales", account_id: "DU123" },
        });
        expect(getLastFetchUrl(fetchMock)).toContain("/tax/wash-sales");
        expect(getLastFetchMethod(fetchMock)).toBe("POST");
    });

    it("routes lots to GET /tax/lots", async () => {
        const client = await createClient(registerTaxTool);
        await client.callTool({
            name: "zorivest_tax",
            arguments: { action: "lots" },
        });
        expect(getLastFetchUrl(fetchMock)).toContain("/tax/lots");
        expect(getLastFetchMethod(fetchMock)).toBe("GET");
    });

    it("routes quarterly to GET /tax/quarterly", async () => {
        const client = await createClient(registerTaxTool);
        await client.callTool({
            name: "zorivest_tax",
            arguments: { action: "quarterly", quarter: "Q1" },
        });
        expect(getLastFetchUrl(fetchMock)).toContain("/tax/quarterly");
        expect(getLastFetchMethod(fetchMock)).toBe("GET");
    });

    it("routes record_payment to POST /tax/quarterly/payment", async () => {
        const client = await createClient(registerTaxTool);
        await client.callTool({
            name: "zorivest_tax",
            arguments: {
                action: "record_payment",
                quarter: "Q1",
                tax_year: 2026,
                payment_amount: 5000,
                confirm: true,
            },
        });
        expect(getLastFetchUrl(fetchMock)).toContain("/tax/quarterly/payment");
        expect(getLastFetchMethod(fetchMock)).toBe("POST");
    });

    it("routes harvest to GET /tax/harvest", async () => {
        const client = await createClient(registerTaxTool);
        await client.callTool({
            name: "zorivest_tax",
            arguments: { action: "harvest" },
        });
        expect(getLastFetchUrl(fetchMock)).toContain("/tax/harvest");
        expect(getLastFetchMethod(fetchMock)).toBe("GET");
    });

    it("routes ytd_summary to GET /tax/ytd-summary", async () => {
        const client = await createClient(registerTaxTool);
        await client.callTool({
            name: "zorivest_tax",
            arguments: { action: "ytd_summary" },
        });
        expect(getLastFetchUrl(fetchMock)).toContain("/tax/ytd-summary");
        expect(getLastFetchMethod(fetchMock)).toBe("GET");
    });

    // ── Tax disclaimer ───────────────────────────────────────────────

    it("includes tax disclaimer in response text", async () => {
        const client = await createClient(registerTaxTool);
        const result = await client.callTool({
            name: "zorivest_tax",
            arguments: { action: "lots" },
        });
        const text = getResultText(result);
        expect(text).toContain("Tax estimates are for informational purposes only");
    });

    // ── Error handling ───────────────────────────────────────────────

    it("rejects unknown action", async () => {
        const client = await createClient(registerTaxTool);
        const result = await client.callTool({
            name: "zorivest_tax",
            arguments: { action: "nonexistent" },
        });
        expect(result.isError).toBe(true);
    });

    // ── AC-149.4: Required field parity ──────────────────────────────

    it("rejects simulate without required account_id", async () => {
        const client = await createClient(registerTaxTool);
        const result = await client.callTool({
            name: "zorivest_tax",
            arguments: {
                action: "simulate",
                ticker: "AAPL",
                quantity: 100,
                price: 150.0,
                // account_id intentionally omitted
            },
        });
        expect(result.isError).toBe(true);
    });

    it("accepts wash_sales without optional account_id", async () => {
        const client = await createClient(registerTaxTool);
        const result = await client.callTool({
            name: "zorivest_tax",
            arguments: {
                action: "wash_sales",
                // account_id intentionally omitted — it is optional in schema
            },
        });
        // Should succeed since account_id is .optional()
        expect(result.isError).toBeFalsy();
        expect(getLastFetchUrl(fetchMock)).toContain("/tax/wash-sales");
    });

    // ── Destructive hint ─────────────────────────────────────────────

    it("tool has destructiveHint=true annotation", async () => {
        const client = await createClient(registerTaxTool);
        const { tools } = await client.listTools();
        const tax = tools.find((t) => t.name === "zorivest_tax");
        expect(tax?.annotations?.destructiveHint).toBe(true);
    });
});
