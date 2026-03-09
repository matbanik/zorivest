/**
 * Unit tests for calculator MCP tools.
 *
 * Tests verify correct REST endpoint and payload forwarding.
 * Uses mocked global.fetch — no live API needed.
 *
 * API contract: packages/api/src/zorivest_api/routes/calculator.py
 * Fields: balance, risk_pct, entry_price, stop_loss, target_price
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { registerCalculatorTools } from "../src/tools/calculator-tools.js";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { InMemoryTransport } from "@modelcontextprotocol/sdk/inMemory.js";

// ── Test helpers ───────────────────────────────────────────────────────

function mockFetch(response: unknown, status = 200): void {
    vi.stubGlobal(
        "fetch",
        vi.fn().mockResolvedValue({
            ok: status >= 200 && status < 300,
            status,
            json: () => Promise.resolve(response),
            text: () => Promise.resolve(JSON.stringify(response)),
        }),
    );
}

async function createTestClient(): Promise<Client> {
    const server = new McpServer({ name: "test", version: "0.1.0" });
    registerCalculatorTools(server);

    const [clientTransport, serverTransport] =
        InMemoryTransport.createLinkedPair();

    const client = new Client({ name: "test-client", version: "0.1.0" });

    await Promise.all([
        client.connect(clientTransport),
        server.connect(serverTransport),
    ]);

    return client;
}

// ── Tests ──────────────────────────────────────────────────────────────

describe("calculate_position_size", () => {
    beforeEach(() => {
        vi.restoreAllMocks();
    });

    it("calls POST /calculator/position-size with all params", async () => {
        const calcResponse = {
            shares: 50,
            risk_amount: 500,
            position_size: 5000,
            position_to_account_pct: 10,
            reward_risk_ratio: 2,
            risk_per_share: 10,
            potential_profit: 1000,
        };
        mockFetch(calcResponse);

        const client = await createTestClient();
        const result = await client.callTool({
            name: "calculate_position_size",
            arguments: {
                balance: 50000,
                risk_pct: 1,
                entry_price: 100,
                stop_loss: 90,
                target_price: 120,
            },
        });

        expect(fetch).toHaveBeenCalledOnce();
        const [url, opts] = vi.mocked(fetch).mock.calls[0];
        expect(url).toContain("/calculator/position-size");
        expect(opts?.method).toBe("POST");

        // Verify all params forwarded with correct field names
        const body = JSON.parse(opts?.body as string);
        expect(body.balance).toBe(50000);
        expect(body.risk_pct).toBe(1);
        expect(body.entry_price).toBe(100);
        expect(body.stop_loss).toBe(90);
        expect(body.target_price).toBe(120);

        // Verify response envelope
        const content = result.content as Array<{ type: string; text: string }>;
        expect(content[0].type).toBe("text");
        const parsed = JSON.parse(content[0].text);
        expect(parsed.success).toBe(true);
        expect(parsed.data.position_size).toBe(5000);
        expect(parsed.data.position_to_account_pct).toBe(10);
    });

    it("returns error envelope on API failure", async () => {
        mockFetch({ detail: "Validation error" }, 422);

        const client = await createTestClient();
        const result = await client.callTool({
            name: "calculate_position_size",
            arguments: {
                balance: 50000,
                risk_pct: 1,
                entry_price: 100,
                stop_loss: 90,
                target_price: 120,
            },
        });

        const content = result.content as Array<{ type: string; text: string }>;
        const parsed = JSON.parse(content[0].text);
        expect(parsed.success).toBe(false);
        expect(parsed.error).toContain("422");
    });
});
