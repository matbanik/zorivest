/**
 * Unit tests for trade planning MCP tools.
 *
 * Tests verify correct REST endpoint called, payload forwarding,
 * annotation metadata, and standard response envelope structure.
 * Uses mocked global.fetch — no live API needed.
 *
 * Source: 05d-mcp-trade-planning.md
 * FIC: MEU-36 AC-1 through AC-6
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { registerPlanningTools } from "../src/tools/planning-tools.js";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { InMemoryTransport } from "@modelcontextprotocol/sdk/inMemory.js";

// ── Test helpers ───────────────────────────────────────────────────────

function mockGuardAndApi(apiResponse: unknown, apiStatus = 201): void {
    vi.stubGlobal(
        "fetch",
        vi.fn().mockImplementation((url: string) => {
            if (typeof url === "string" && url.includes("/mcp-guard/")) {
                return Promise.resolve({
                    ok: true,
                    status: 200,
                    json: () => Promise.resolve({ allowed: true }),
                    text: () =>
                        Promise.resolve(JSON.stringify({ allowed: true })),
                });
            }
            return Promise.resolve({
                ok: apiStatus >= 200 && apiStatus < 300,
                status: apiStatus,
                json: () => Promise.resolve(apiResponse),
                text: () => Promise.resolve(JSON.stringify(apiResponse)),
            });
        }),
    );
}

async function createTestClient(): Promise<Client> {
    const server = new McpServer({ name: "test", version: "0.1.0" });
    registerPlanningTools(server);

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

describe("create_trade_plan", () => {
    beforeEach(() => {
        vi.restoreAllMocks();
    });

    // AC-1: Tool registers with name `create_trade_plan` and full input schema
    it("registers with correct name and accepts full input schema", async () => {
        const planResponse = {
            id: "plan_001",
            ticker: "AAPL",
            direction: "long",
            conviction: "high",
            strategy_name: "breakout",
            strategy_description: "Breaking above resistance",
            entry: 180.0,
            stop: 175.0,
            target: 195.0,
            conditions: "Volume above 20-day average",
            timeframe: "2-5 days",
            account_id: "ACC001",
            risk_reward_ratio: 3.0,
            status: "draft",
        };
        mockGuardAndApi(planResponse);

        const client = await createTestClient();
        const result = await client.callTool({
            name: "create_trade_plan",
            arguments: {
                ticker: "AAPL",
                direction: "long",
                conviction: "high",
                strategy_name: "breakout",
                strategy_description: "Breaking above resistance",
                entry: 180.0,
                stop: 175.0,
                target: 195.0,
                conditions: "Volume above 20-day average",
                timeframe: "2-5 days",
                account_id: "ACC001",
            },
        });

        // AC-4: Handler POSTs to /trade-plans with full body
        expect(fetch).toHaveBeenCalledTimes(2); // guard + API
        const [url, opts] = vi.mocked(fetch).mock.calls[1];
        expect(url).toContain("/trade-plans");
        expect(opts?.method).toBe("POST");

        // Verify Content-Type header
        const headers = opts?.headers as Record<string, string>;
        expect(headers["Content-Type"]).toBe("application/json");

        // Verify body includes all required fields
        const body = JSON.parse(opts?.body as string);
        expect(body.ticker).toBe("AAPL");
        expect(body.direction).toBe("long");
        expect(body.conviction).toBe("high");
        expect(body.strategy_name).toBe("breakout");
        expect(body.strategy_description).toBe("Breaking above resistance");
        expect(body.entry).toBe(180.0);
        expect(body.stop).toBe(175.0);
        expect(body.target).toBe(195.0);
        expect(body.conditions).toBe("Volume above 20-day average");
        expect(body.timeframe).toBe("2-5 days");
        expect(body.account_id).toBe("ACC001");

        // AC-4: Returns JSON text content
        const content = result.content as Array<{
            type: string;
            text: string;
        }>;
        expect(content).toHaveLength(1);
        expect(content[0].type).toBe("text");
        const parsed = JSON.parse(content[0].text);
        expect(parsed.success).toBe(true);
        expect(parsed.data.id).toBe("plan_001");
        expect(parsed.data.ticker).toBe("AAPL");
    });

    // AC-1: Optional fields can be omitted
    it("accepts minimal required fields (without optional strategy_description and account_id)", async () => {
        mockGuardAndApi({ id: "plan_002", status: "draft" });

        const client = await createTestClient();
        const result = await client.callTool({
            name: "create_trade_plan",
            arguments: {
                ticker: "MSFT",
                direction: "short",
                strategy_name: "mean_reversion",
                entry: 420.0,
                stop: 430.0,
                target: 400.0,
                conditions: "RSI above 70",
                timeframe: "intraday",
            },
        });

        const [, opts] = vi.mocked(fetch).mock.calls[1];
        const body = JSON.parse(opts?.body as string);
        expect(body.ticker).toBe("MSFT");
        expect(body.direction).toBe("short");
        // conviction defaults to "medium" per spec
        expect(body.conviction).toBe("medium");

        const content = result.content as Array<{
            type: string;
            text: string;
        }>;
        const parsed = JSON.parse(content[0].text);
        expect(parsed.success).toBe(true);
    });

    // AC-5: Returns error envelope on API failure
    it("returns error envelope on API failure (non-2xx)", async () => {
        mockGuardAndApi(
            { detail: "Duplicate active plan for ticker" },
            409,
        );

        const client = await createTestClient();
        const result = await client.callTool({
            name: "create_trade_plan",
            arguments: {
                ticker: "AAPL",
                direction: "long",
                strategy_name: "breakout",
                entry: 180.0,
                stop: 175.0,
                target: 195.0,
                conditions: "Volume spike",
                timeframe: "swing",
            },
        });

        const content = result.content as Array<{
            type: string;
            text: string;
        }>;
        expect(content).toHaveLength(1);
        const parsed = JSON.parse(content[0].text);
        expect(parsed.success).toBe(false);
        expect(parsed.error).toBeDefined();
    });

    // AC-6: Wrapped with withMetrics + withGuard (guarded tool)
    it("calls guard check before API (withGuard middleware)", async () => {
        mockGuardAndApi({ id: "plan_003" });

        const client = await createTestClient();
        await client.callTool({
            name: "create_trade_plan",
            arguments: {
                ticker: "TSLA",
                direction: "long",
                strategy_name: "momentum",
                entry: 250.0,
                stop: 240.0,
                target: 280.0,
                conditions: "Earnings breakout",
                timeframe: "2-5 days",
            },
        });

        // First call should be the guard check
        expect(fetch).toHaveBeenCalledTimes(2);
        const [guardUrl] = vi.mocked(fetch).mock.calls[0];
        expect(guardUrl).toContain("/mcp-guard/");
    });
});

// ── MEU-69: Watchlist MCP tool tests ───────────────────────────────────

describe("create_watchlist", () => {
    beforeEach(() => {
        vi.restoreAllMocks();
    });

    it("POSTs to /watchlists/ with name and description", async () => {
        const wlResponse = { id: 1, name: "Momentum Plays", description: "Hot stocks", items: [] };
        mockGuardAndApi(wlResponse);

        const client = await createTestClient();
        const result = await client.callTool({
            name: "create_watchlist",
            arguments: { name: "Momentum Plays", description: "Hot stocks" },
        });

        expect(fetch).toHaveBeenCalledTimes(2);
        const [url, opts] = vi.mocked(fetch).mock.calls[1];
        expect(url).toContain("/watchlists/");
        expect(opts?.method).toBe("POST");
        const body = JSON.parse(opts?.body as string);
        expect(body.name).toBe("Momentum Plays");
        expect(body.description).toBe("Hot stocks");

        const content = result.content as Array<{ type: string; text: string }>;
        const parsed = JSON.parse(content[0].text);
        expect(parsed.success).toBe(true);
        expect(parsed.data.name).toBe("Momentum Plays");
    });

    it("returns error on duplicate name (409)", async () => {
        mockGuardAndApi({ detail: "Watchlist name already exists" }, 409);

        const client = await createTestClient();
        const result = await client.callTool({
            name: "create_watchlist",
            arguments: { name: "Duplicate" },
        });

        const content = result.content as Array<{ type: string; text: string }>;
        const parsed = JSON.parse(content[0].text);
        expect(parsed.success).toBe(false);
    });
});

describe("list_watchlists", () => {
    beforeEach(() => {
        vi.restoreAllMocks();
    });

    it("GETs /watchlists/ with pagination params", async () => {
        mockGuardAndApi([{ id: 1, name: "WL1" }], 200);

        const client = await createTestClient();
        const result = await client.callTool({
            name: "list_watchlists",
            arguments: { limit: 10, offset: 0 },
        });

        const [url] = vi.mocked(fetch).mock.calls[1];
        expect(url).toContain("/watchlists/");
        expect(url).toContain("limit=10");
        expect(url).toContain("offset=0");

        const content = result.content as Array<{ type: string; text: string }>;
        const parsed = JSON.parse(content[0].text);
        expect(parsed.success).toBe(true);
    });

    it("returns error on API failure (500)", async () => {
        mockGuardAndApi({ detail: "Internal error" }, 500);

        const client = await createTestClient();
        const result = await client.callTool({
            name: "list_watchlists",
            arguments: { limit: 10, offset: 0 },
        });

        const content = result.content as Array<{ type: string; text: string }>;
        const parsed = JSON.parse(content[0].text);
        expect(parsed.success).toBe(false);
    });
});

describe("get_watchlist", () => {
    beforeEach(() => {
        vi.restoreAllMocks();
    });

    it("GETs /watchlists/{id} with items", async () => {
        const wlResponse = { id: 42, name: "Tech", items: [{ ticker: "AAPL" }] };
        mockGuardAndApi(wlResponse, 200);

        const client = await createTestClient();
        const result = await client.callTool({
            name: "get_watchlist",
            arguments: { watchlist_id: 42 },
        });

        const [url] = vi.mocked(fetch).mock.calls[1];
        expect(url).toContain("/watchlists/42");

        const content = result.content as Array<{ type: string; text: string }>;
        const parsed = JSON.parse(content[0].text);
        expect(parsed.success).toBe(true);
        expect(parsed.data.id).toBe(42);
    });

    it("returns error when not found (404)", async () => {
        mockGuardAndApi({ detail: "Not found" }, 404);

        const client = await createTestClient();
        const result = await client.callTool({
            name: "get_watchlist",
            arguments: { watchlist_id: 999 },
        });

        const content = result.content as Array<{ type: string; text: string }>;
        const parsed = JSON.parse(content[0].text);
        expect(parsed.success).toBe(false);
    });
});

describe("add_to_watchlist", () => {
    beforeEach(() => {
        vi.restoreAllMocks();
    });

    it("POSTs to /watchlists/{id}/items with ticker and notes", async () => {
        const itemResponse = { id: 1, watchlist_id: 5, ticker: "SPY", notes: "Key level at 600" };
        mockGuardAndApi(itemResponse);

        const client = await createTestClient();
        const result = await client.callTool({
            name: "add_to_watchlist",
            arguments: { watchlist_id: 5, ticker: "SPY", notes: "Key level at 600" },
        });

        const [url, opts] = vi.mocked(fetch).mock.calls[1];
        expect(url).toContain("/watchlists/5/items");
        expect(opts?.method).toBe("POST");
        const body = JSON.parse(opts?.body as string);
        expect(body.ticker).toBe("SPY");
        expect(body.notes).toBe("Key level at 600");

        const content = result.content as Array<{ type: string; text: string }>;
        const parsed = JSON.parse(content[0].text);
        expect(parsed.success).toBe(true);
        expect(parsed.data.ticker).toBe("SPY");
    });

    it("returns error on duplicate ticker (409)", async () => {
        mockGuardAndApi({ detail: "Ticker already in watchlist" }, 409);

        const client = await createTestClient();
        const result = await client.callTool({
            name: "add_to_watchlist",
            arguments: { watchlist_id: 5, ticker: "SPY" },
        });

        const content = result.content as Array<{ type: string; text: string }>;
        const parsed = JSON.parse(content[0].text);
        expect(parsed.success).toBe(false);
    });
});

describe("remove_from_watchlist", () => {
    beforeEach(() => {
        vi.restoreAllMocks();
    });

    it("DELETEs /watchlists/{id}/items/{ticker}", async () => {
        mockGuardAndApi(null, 204);

        const client = await createTestClient();
        const result = await client.callTool({
            name: "remove_from_watchlist",
            arguments: { watchlist_id: 5, ticker: "SPY" },
        });

        const [url, opts] = vi.mocked(fetch).mock.calls[1];
        expect(url).toContain("/watchlists/5/items/SPY");
        expect(opts?.method).toBe("DELETE");

        const content = result.content as Array<{ type: string; text: string }>;
        expect(content).toHaveLength(1);
    });

    it("returns error when watchlist not found (404)", async () => {
        mockGuardAndApi({ detail: "Not found" }, 404);

        const client = await createTestClient();
        const result = await client.callTool({
            name: "remove_from_watchlist",
            arguments: { watchlist_id: 999, ticker: "SPY" },
        });

        const content = result.content as Array<{ type: string; text: string }>;
        const parsed = JSON.parse(content[0].text);
        expect(parsed.success).toBe(false);
    });
});

// ── TA4: list_trade_plans and delete_trade_plan tests ──────────────────

describe("list_trade_plans", () => {
    beforeEach(() => {
        vi.restoreAllMocks();
    });

    it("GETs /trade-plans with pagination and returns structured list", async () => {
        const plansResponse = [
            { id: 1, ticker: "AAPL", direction: "long", status: "draft" },
            { id: 2, ticker: "MSFT", direction: "short", status: "active" },
        ];
        mockGuardAndApi(plansResponse, 200);

        const client = await createTestClient();
        const result = await client.callTool({
            name: "list_trade_plans",
            arguments: { limit: 10, offset: 0 },
        });

        // Verify correct endpoint and pagination params
        const [url] = vi.mocked(fetch).mock.calls[1];
        expect(url).toContain("/trade-plans");
        expect(url).toContain("limit=10");
        expect(url).toContain("offset=0");

        const content = result.content as Array<{ type: string; text: string }>;
        expect(content).toHaveLength(1);
        const parsed = JSON.parse(content[0].text);
        expect(parsed.success).toBe(true);
        expect(parsed.data).toHaveLength(2);
        expect(parsed.data[0].ticker).toBe("AAPL");
    });

    it("returns empty array when no plans exist", async () => {
        mockGuardAndApi([], 200);

        const client = await createTestClient();
        const result = await client.callTool({
            name: "list_trade_plans",
            arguments: { limit: 50, offset: 0 },
        });

        const content = result.content as Array<{ type: string; text: string }>;
        const parsed = JSON.parse(content[0].text);
        expect(parsed.success).toBe(true);
        expect(parsed.data).toHaveLength(0);
    });

    it("returns error envelope on API failure (500)", async () => {
        mockGuardAndApi({ detail: "Internal error" }, 500);

        const client = await createTestClient();
        const result = await client.callTool({
            name: "list_trade_plans",
            arguments: { limit: 10, offset: 0 },
        });

        const content = result.content as Array<{ type: string; text: string }>;
        const parsed = JSON.parse(content[0].text);
        expect(parsed.success).toBe(false);
        expect(parsed.error).toBeDefined();
    });

});

describe("delete_trade_plan", () => {
    beforeEach(() => {
        vi.restoreAllMocks();
    });

    it("DELETEs /trade-plans/{id} and returns success", async () => {
        mockGuardAndApi(null, 204);

        const client = await createTestClient();
        const result = await client.callTool({
            name: "delete_trade_plan",
            arguments: { plan_id: 42 },
        });

        // Verify correct endpoint and method
        const [url, opts] = vi.mocked(fetch).mock.calls[1];
        expect(url).toContain("/trade-plans/42");
        expect(opts?.method).toBe("DELETE");

        const content = result.content as Array<{ type: string; text: string }>;
        expect(content).toHaveLength(1);
    });

    it("returns error when plan not found (404)", async () => {
        mockGuardAndApi({ detail: "Trade plan not found" }, 404);

        const client = await createTestClient();
        const result = await client.callTool({
            name: "delete_trade_plan",
            arguments: { plan_id: 999 },
        });

        const content = result.content as Array<{ type: string; text: string }>;
        const parsed = JSON.parse(content[0].text);
        expect(parsed.success).toBe(false);
    });

    it("calls guard check before API (withGuard middleware)", async () => {
        mockGuardAndApi(null, 204);

        const client = await createTestClient();
        await client.callTool({
            name: "delete_trade_plan",
            arguments: { plan_id: 1 },
        });

        // First call should be the guard check
        expect(fetch).toHaveBeenCalledTimes(2);
        const [guardUrl] = vi.mocked(fetch).mock.calls[0];
        expect(guardUrl).toContain("/mcp-guard/");
    });
});
