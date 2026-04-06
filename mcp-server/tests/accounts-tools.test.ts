/**
 * Unit tests for account MCP tools.
 *
 * Tests verify correct REST endpoints called, payload forwarding,
 * multipart upload pattern, client-side aggregation, and response envelopes.
 * Uses mocked global.fetch — no live API needed.
 *
 * Source: 05f-mcp-accounts.md
 * FIC: MEU-37 AC-1 through AC-20
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { registerAccountTools } from "../src/tools/accounts-tools.js";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { InMemoryTransport } from "@modelcontextprotocol/sdk/inMemory.js";
import {
    setConfirmationMode,
    createConfirmationToken,
} from "../src/middleware/confirmation.js";

// Mock node:fs and node:path for uploadFile tests
vi.mock("node:fs", () => ({
    readFileSync: vi.fn().mockReturnValue(Buffer.from("test-file-content")),
}));

vi.mock("node:path", () => ({
    basename: vi.fn().mockImplementation((p: string) => {
        const parts = p.replace(/\\/g, "/").split("/");
        return parts[parts.length - 1];
    }),
}));

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

function mockGuardAndApi(apiResponse: unknown, apiStatus = 200): void {
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
    registerAccountTools(server);

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

// AC-1: sync_broker POSTs to /brokers/{broker_id}/sync
describe("sync_broker", () => {
    beforeEach(() => {
        vi.restoreAllMocks();
    });

    it("POSTs to /brokers/{broker_id}/sync with broker_id param", async () => {
        mockGuardAndApi({ status: "synced", trades_imported: 5 });

        const client = await createTestClient();
        const result = await client.callTool({
            name: "sync_broker",
            arguments: { broker_id: "ibkr_pro" },
        });

        expect(fetch).toHaveBeenCalledTimes(2); // guard + API
        const [url, opts] = vi.mocked(fetch).mock.calls[1];
        expect(url).toContain("/brokers/ibkr_pro/sync");
        expect(opts?.method).toBe("POST");

        const content = result.content as Array<{
            type: string;
            text: string;
        }>;
        const parsed = JSON.parse(content[0].text);
        expect(parsed.success).toBe(true);
    });
});

// AC-2: list_brokers GETs /brokers with no params
describe("list_brokers", () => {
    beforeEach(() => {
        vi.restoreAllMocks();
    });

    it("GETs /brokers with no params", async () => {
        mockFetch([
            { broker_id: "ibkr_pro", name: "IBKR", last_sync: "2026-03-01" },
        ]);

        const client = await createTestClient();
        const result = await client.callTool({
            name: "list_brokers",
            arguments: {},
        });

        expect(fetch).toHaveBeenCalledOnce();
        const [url] = vi.mocked(fetch).mock.calls[0];
        expect(url).toContain("/brokers");
        // No method specified = GET (default)

        const content = result.content as Array<{
            type: string;
            text: string;
        }>;
        const parsed = JSON.parse(content[0].text);
        expect(parsed.success).toBe(true);
    });
});

// AC-3: resolve_identifiers POSTs to /identifiers/resolve with JSON-wrapped body
describe("resolve_identifiers", () => {
    beforeEach(() => {
        vi.restoreAllMocks();
    });

    it("POSTs structured identifiers wrapped as JSON to /identifiers/resolve", async () => {
        mockFetch([
            { id_type: "cusip", id_value: "037833100", ticker: "AAPL" },
        ]);

        const client = await createTestClient();
        const result = await client.callTool({
            name: "resolve_identifiers",
            arguments: {
                identifiers: [
                    { id_type: "cusip", id_value: "037833100" },
                    { id_type: "isin", id_value: "US0378331005" },
                ],
            },
        });

        expect(fetch).toHaveBeenCalledOnce();
        const [url, opts] = vi.mocked(fetch).mock.calls[0];
        expect(url).toContain("/identifiers/resolve");
        expect(opts?.method).toBe("POST");

        // Verify Content-Type header
        const headers = opts?.headers as Record<string, string>;
        expect(headers["Content-Type"]).toBe("application/json");

        // Verify body wraps identifiers per plan: JSON.stringify({ identifiers })
        const body = JSON.parse(opts?.body as string);
        expect(body.identifiers).toHaveLength(2);
        expect(body.identifiers[0].id_type).toBe("cusip");
        expect(body.identifiers[1].id_value).toBe("US0378331005");

        const content = result.content as Array<{
            type: string;
            text: string;
        }>;
        const parsed = JSON.parse(content[0].text);
        expect(parsed.success).toBe(true);
    });
});

// AC-4: import_bank_statement uploads multipart to /banking/import
describe("import_bank_statement", () => {
    beforeEach(() => {
        vi.restoreAllMocks();
    });

    it("uploads multipart to /banking/import with file_path, account_id, format_hint", async () => {
        mockGuardAndApi({ rows_imported: 15, duplicates: 2 });

        const client = await createTestClient();
        const result = await client.callTool({
            name: "import_bank_statement",
            arguments: {
                file_path: "/tmp/statement.csv",
                account_id: "checking_001",
                format_hint: "csv",
            },
        });

        expect(fetch).toHaveBeenCalledTimes(2); // guard + API
        const [url, opts] = vi.mocked(fetch).mock.calls[1];
        expect(url).toContain("/banking/import");
        expect(opts?.method).toBe("POST");
        // Body should be FormData for multipart upload
        expect(opts?.body).toBeInstanceOf(FormData);

        const content = result.content as Array<{
            type: string;
            text: string;
        }>;
        const parsed = JSON.parse(content[0].text);
        expect(parsed.success).toBe(true);
    });
});

// AC-5: import_broker_csv uploads multipart to /import/csv
describe("import_broker_csv", () => {
    beforeEach(() => {
        vi.restoreAllMocks();
    });

    it("uploads multipart to /import/csv with file_path, account_id, broker_hint", async () => {
        mockGuardAndApi({ rows_imported: 50 });

        const client = await createTestClient();
        const result = await client.callTool({
            name: "import_broker_csv",
            arguments: {
                file_path: "/tmp/trades.csv",
                account_id: "ACC001",
                broker_hint: "ibkr",
            },
        });

        expect(fetch).toHaveBeenCalledTimes(2);
        const [url, opts] = vi.mocked(fetch).mock.calls[1];
        expect(url).toContain("/import/csv");
        expect(opts?.method).toBe("POST");
        expect(opts?.body).toBeInstanceOf(FormData);

        const content = result.content as Array<{
            type: string;
            text: string;
        }>;
        const parsed = JSON.parse(content[0].text);
        expect(parsed.success).toBe(true);
    });
});

// AC-6: import_broker_pdf uploads multipart to /import/pdf
describe("import_broker_pdf", () => {
    beforeEach(() => {
        vi.restoreAllMocks();
    });

    it("uploads multipart to /import/pdf with file_path, account_id", async () => {
        mockGuardAndApi({ rows_imported: 25 });

        const client = await createTestClient();
        const result = await client.callTool({
            name: "import_broker_pdf",
            arguments: {
                file_path: "/tmp/statement.pdf",
                account_id: "ACC002",
            },
        });

        expect(fetch).toHaveBeenCalledTimes(2);
        const [url, opts] = vi.mocked(fetch).mock.calls[1];
        expect(url).toContain("/import/pdf");
        expect(opts?.method).toBe("POST");
        expect(opts?.body).toBeInstanceOf(FormData);

        const content = result.content as Array<{
            type: string;
            text: string;
        }>;
        const parsed = JSON.parse(content[0].text);
        expect(parsed.success).toBe(true);
    });
});

// AC-7: list_bank_accounts GETs /banking/accounts with no params
describe("list_bank_accounts", () => {
    beforeEach(() => {
        vi.restoreAllMocks();
    });

    it("GETs /banking/accounts with no params", async () => {
        mockFetch([
            {
                account_id: "checking_001",
                name: "Main Checking",
                last_updated: "2026-03-01",
            },
        ]);

        const client = await createTestClient();
        const result = await client.callTool({
            name: "list_bank_accounts",
            arguments: {},
        });

        expect(fetch).toHaveBeenCalledOnce();
        const [url] = vi.mocked(fetch).mock.calls[0];
        expect(url).toContain("/banking/accounts");

        const content = result.content as Array<{
            type: string;
            text: string;
        }>;
        const parsed = JSON.parse(content[0].text);
        expect(parsed.success).toBe(true);
    });
});

// AC-8: get_account_review_checklist aggregates brokers + banks
describe("get_account_review_checklist", () => {
    beforeEach(() => {
        vi.restoreAllMocks();
    });

    it("fetches both /brokers and /banking/accounts and returns structured review", async () => {
        // Mock two sequential fetches: brokers then banks
        const brokerData = [
            { broker_id: "ibkr", name: "IBKR", last_sync: "2026-01-01" },
        ];
        const bankData = [
            {
                account_id: "checking",
                name: "Checking",
                last_updated: "2026-03-09",
            },
        ];

        let callCount = 0;
        vi.stubGlobal(
            "fetch",
            vi.fn().mockImplementation(() => {
                callCount++;
                const data = callCount === 1 ? brokerData : bankData;
                return Promise.resolve({
                    ok: true,
                    status: 200,
                    json: () => Promise.resolve(data),
                    text: () => Promise.resolve(JSON.stringify(data)),
                });
            }),
        );

        const client = await createTestClient();
        const result = await client.callTool({
            name: "get_account_review_checklist",
            arguments: { scope: "all", stale_threshold_days: 7 },
        });

        // Should have called fetch twice (brokers + banks via Promise.all)
        expect(fetch).toHaveBeenCalledTimes(2);
        const [url1] = vi.mocked(fetch).mock.calls[0];
        const [url2] = vi.mocked(fetch).mock.calls[1];
        expect(url1).toContain("/brokers");
        expect(url2).toContain("/banking/accounts");

        const content = result.content as Array<{
            type: string;
            text: string;
        }>;
        const parsed = JSON.parse(content[0].text);
        // Review checklist structure
        expect(parsed.review_scope).toBe("all");
        expect(parsed.stale_threshold_days).toBe(7);
        expect(parsed.total_accounts).toBe(2);
        expect(parsed.accounts).toBeDefined();
    });

    it("filters to stale_only by default", async () => {
        const brokerData = [
            { broker_id: "ibkr", name: "IBKR", last_sync: "2020-01-01" },
        ];
        const bankData = [
            {
                account_id: "checking",
                name: "Checking",
                last_updated: new Date().toISOString(),
            },
        ];

        let callCount = 0;
        vi.stubGlobal(
            "fetch",
            vi.fn().mockImplementation(() => {
                callCount++;
                const data = callCount === 1 ? brokerData : bankData;
                return Promise.resolve({
                    ok: true,
                    status: 200,
                    json: () => Promise.resolve(data),
                    text: () => Promise.resolve(JSON.stringify(data)),
                });
            }),
        );

        const client = await createTestClient();
        const result = await client.callTool({
            name: "get_account_review_checklist",
            arguments: {},
        });

        const content = result.content as Array<{
            type: string;
            text: string;
        }>;
        const parsed = JSON.parse(content[0].text);
        // Only the stale broker should appear (bank was updated today)
        expect(parsed.accounts_needing_review).toBe(1);
        expect(parsed.accounts[0].id).toBe("ibkr");
        expect(parsed.accounts[0].is_stale).toBe(true);
        expect(parsed.accounts[0].suggested_action).toContain("sync_broker");
    });
});

// ── CRUD Account Tools (AC-14 through AC-20) ──────────────────────────

// AC-14: list_accounts GETs /accounts with query params
describe("list_accounts", () => {
    beforeEach(() => {
        vi.restoreAllMocks();
    });

    it("GETs /accounts with no query params by default", async () => {
        mockFetch([
            { account_id: "ACC001", name: "Main Broker", account_type: "BROKER" },
        ]);

        const client = await createTestClient();
        const result = await client.callTool({
            name: "list_accounts",
            arguments: {},
        });

        expect(fetch).toHaveBeenCalledOnce();
        const [url] = vi.mocked(fetch).mock.calls[0];
        expect(url).toContain("/accounts");
        // No query params when defaults are false
        expect(url).not.toContain("include_archived");
        expect(url).not.toContain("include_system");

        const content = result.content as Array<{ type: string; text: string }>;
        const parsed = JSON.parse(content[0].text);
        expect(parsed.success).toBe(true);
    });

    it("forwards include_archived and include_system as query params", async () => {
        mockFetch([]);

        const client = await createTestClient();
        await client.callTool({
            name: "list_accounts",
            arguments: { include_archived: true, include_system: true },
        });

        const [url] = vi.mocked(fetch).mock.calls[0];
        expect(url).toContain("include_archived=true");
        expect(url).toContain("include_system=true");
    });
});

// AC-15: get_account GETs /accounts/{id}
describe("get_account", () => {
    beforeEach(() => {
        vi.restoreAllMocks();
    });

    it("GETs /accounts/{account_id} and returns enriched metrics", async () => {
        const accountResponse = {
            account_id: "ACC001",
            name: "Main Broker",
            account_type: "BROKER",
            trade_count: 42,
            win_rate: 0.65,
            realized_pnl: 1250.50,
        };
        mockFetch(accountResponse);

        const client = await createTestClient();
        const result = await client.callTool({
            name: "get_account",
            arguments: { account_id: "ACC001" },
        });

        expect(fetch).toHaveBeenCalledOnce();
        const [url] = vi.mocked(fetch).mock.calls[0];
        expect(url).toContain("/accounts/ACC001");

        const content = result.content as Array<{ type: string; text: string }>;
        const parsed = JSON.parse(content[0].text);
        expect(parsed.success).toBe(true);
        expect(parsed.data.account_id).toBe("ACC001");
    });
});

// AC-16: create_account POSTs /accounts (guarded, no confirmation)
describe("create_account", () => {
    beforeEach(() => {
        vi.restoreAllMocks();
    });

    it("POSTs to /accounts with JSON body and returns created account", async () => {
        const createdAccount = {
            account_id: "auto-uuid",
            name: "Test Broker",
            account_type: "BROKER",
        };
        mockGuardAndApi(createdAccount, 201);

        const client = await createTestClient();
        const result = await client.callTool({
            name: "create_account",
            arguments: {
                name: "Test Broker",
                account_type: "BROKER",
                institution: "Interactive Brokers",
                currency: "USD",
                is_tax_advantaged: false,
            },
        });

        // Guard check + API call = 2 fetch calls
        expect(fetch).toHaveBeenCalledTimes(2);
        const [url, opts] = vi.mocked(fetch).mock.calls[1];
        expect(url).toContain("/accounts");
        expect(opts?.method).toBe("POST");

        // Verify body
        const headers = opts?.headers as Record<string, string>;
        expect(headers["Content-Type"]).toBe("application/json");
        const body = JSON.parse(opts?.body as string);
        expect(body.name).toBe("Test Broker");
        expect(body.account_type).toBe("BROKER");
        expect(body.institution).toBe("Interactive Brokers");
        expect(body.currency).toBe("USD");
        expect(body.is_tax_advantaged).toBe(false);

        const content = result.content as Array<{ type: string; text: string }>;
        const parsed = JSON.parse(content[0].text);
        expect(parsed.success).toBe(true);
    });
});

// update_account PUTs /accounts/{id} (guarded)
describe("update_account", () => {
    beforeEach(() => {
        vi.restoreAllMocks();
    });

    it("PUTs to /accounts/{account_id} with only provided fields", async () => {
        const updatedAccount = {
            account_id: "ACC001",
            name: "Renamed Broker",
            account_type: "BROKER",
        };
        mockGuardAndApi(updatedAccount);

        const client = await createTestClient();
        const result = await client.callTool({
            name: "update_account",
            arguments: {
                account_id: "ACC001",
                name: "Renamed Broker",
            },
        });

        expect(fetch).toHaveBeenCalledTimes(2);
        const [url, opts] = vi.mocked(fetch).mock.calls[1];
        expect(url).toContain("/accounts/ACC001");
        expect(opts?.method).toBe("PUT");

        const body = JSON.parse(opts?.body as string);
        expect(body.name).toBe("Renamed Broker");
        // Fields not provided should NOT be in body
        expect(body).not.toHaveProperty("account_type");
        expect(body).not.toHaveProperty("currency");

        const content = result.content as Array<{ type: string; text: string }>;
        const parsed = JSON.parse(content[0].text);
        expect(parsed.success).toBe(true);
    });
});

// AC-17: delete_account DELETEs /accounts/{id} (destructive + confirmation)
describe("delete_account", () => {
    beforeEach(() => {
        vi.restoreAllMocks();
        setConfirmationMode("dynamic");
    });

    it("calls DELETE /accounts/{account_id} and returns success", async () => {
        mockGuardAndApi(null, 204);

        const client = await createTestClient();
        const result = await client.callTool({
            name: "delete_account",
            arguments: { account_id: "ACC-DEL" },
        });

        // Guard + API = 2 calls
        const deleteCalls = vi
            .mocked(fetch)
            .mock.calls.filter(
                ([url]) =>
                    typeof url === "string" &&
                    url.includes("/accounts/ACC-DEL") &&
                    !url.includes("/mcp-guard/"),
            );
        expect(deleteCalls.length).toBe(1);
        const [delUrl, delOpts] = deleteCalls[0];
        expect(delUrl).toContain("/accounts/ACC-DEL");
        expect(delOpts?.method).toBe("DELETE");

        const content = result.content as Array<{ type: string; text: string }>;
        const parsed = JSON.parse(content[0].text);
        expect(parsed.success).toBe(true);
    });

    it("requires confirmation_token on static clients", async () => {
        mockGuardAndApi(null, 204);
        setConfirmationMode("static");

        const client = await createTestClient();

        // Call WITHOUT token — should be blocked
        const blocked = await client.callTool({
            name: "delete_account",
            arguments: { account_id: "ACC-DEL" },
        });

        const blockedContent = blocked.content as Array<{ type: string; text: string }>;
        const blockedPayload = JSON.parse(blockedContent[0].text);
        expect(blockedPayload.error).toBe("Confirmation required");
        expect(blockedPayload.tool).toBe("delete_account");

        // Retry with valid token
        const { token } = createConfirmationToken("delete_account");
        const result = await client.callTool({
            name: "delete_account",
            arguments: { account_id: "ACC-DEL", confirmation_token: token },
        });

        const content = result.content as Array<{ type: string; text: string }>;
        const parsed = JSON.parse(content[0].text);
        expect(parsed.success).toBe(true);
    });
});

// AC-18: archive_account POSTs /accounts/{id}:archive (guarded, non-destructive)
describe("archive_account", () => {
    beforeEach(() => {
        vi.restoreAllMocks();
    });

    it("POSTs to /accounts/{account_id}:archive", async () => {
        const archiveResponse = {
            account_id: "ACC-ARCH",
            is_archived: true,
        };
        mockGuardAndApi(archiveResponse);

        const client = await createTestClient();
        const result = await client.callTool({
            name: "archive_account",
            arguments: { account_id: "ACC-ARCH" },
        });

        expect(fetch).toHaveBeenCalledTimes(2);
        const [url, opts] = vi.mocked(fetch).mock.calls[1];
        expect(url).toContain("/accounts/ACC-ARCH:archive");
        expect(opts?.method).toBe("POST");

        const content = result.content as Array<{ type: string; text: string }>;
        const parsed = JSON.parse(content[0].text);
        expect(parsed.success).toBe(true);
        expect(parsed.data.is_archived).toBe(true);
    });
});

// AC-19: reassign_trades POSTs /accounts/{id}:reassign-trades (destructive + confirmation)
describe("reassign_trades", () => {
    beforeEach(() => {
        vi.restoreAllMocks();
        setConfirmationMode("dynamic");
    });

    it("POSTs to /accounts/{account_id}:reassign-trades", async () => {
        const reassignResponse = { trades_reassigned: 5 };
        mockGuardAndApi(reassignResponse);

        const client = await createTestClient();
        const result = await client.callTool({
            name: "reassign_trades",
            arguments: { account_id: "ACC-REASS" },
        });

        const reassignCalls = vi
            .mocked(fetch)
            .mock.calls.filter(
                ([url]) =>
                    typeof url === "string" &&
                    url.includes(":reassign-trades") &&
                    !url.includes("/mcp-guard/"),
            );
        expect(reassignCalls.length).toBe(1);
        const [rUrl, rOpts] = reassignCalls[0];
        expect(rUrl).toContain("/accounts/ACC-REASS:reassign-trades");
        expect(rOpts?.method).toBe("POST");

        const content = result.content as Array<{ type: string; text: string }>;
        const parsed = JSON.parse(content[0].text);
        expect(parsed.success).toBe(true);
    });

    it("requires confirmation_token on static clients", async () => {
        mockGuardAndApi({ trades_reassigned: 5 });
        setConfirmationMode("static");

        const client = await createTestClient();

        // Call WITHOUT token — should be blocked
        const blocked = await client.callTool({
            name: "reassign_trades",
            arguments: { account_id: "ACC-REASS" },
        });

        const blockedContent = blocked.content as Array<{ type: string; text: string }>;
        const blockedPayload = JSON.parse(blockedContent[0].text);
        expect(blockedPayload.error).toBe("Confirmation required");
        expect(blockedPayload.tool).toBe("reassign_trades");

        // Retry with valid token
        const { token } = createConfirmationToken("reassign_trades");
        const result = await client.callTool({
            name: "reassign_trades",
            arguments: { account_id: "ACC-REASS", confirmation_token: token },
        });

        const content = result.content as Array<{ type: string; text: string }>;
        const parsed = JSON.parse(content[0].text);
        expect(parsed.success).toBe(true);
    });
});

// AC-20: record_balance POSTs /accounts/{id}/balances (guarded)
describe("record_balance", () => {
    beforeEach(() => {
        vi.restoreAllMocks();
    });

    it("POSTs to /accounts/{account_id}/balances with balance payload", async () => {
        const balanceResponse = {
            id: 1,
            account_id: "ACC001",
            balance: 7777.00,
            snapshot_datetime: "2026-04-06T12:00:00Z",
        };
        mockGuardAndApi(balanceResponse, 201);

        const client = await createTestClient();
        const result = await client.callTool({
            name: "record_balance",
            arguments: {
                account_id: "ACC001",
                balance: 7777.00,
                snapshot_datetime: "2026-04-06T12:00:00Z",
            },
        });

        expect(fetch).toHaveBeenCalledTimes(2);
        const [url, opts] = vi.mocked(fetch).mock.calls[1];
        expect(url).toContain("/accounts/ACC001/balances");
        expect(opts?.method).toBe("POST");

        const headers = opts?.headers as Record<string, string>;
        expect(headers["Content-Type"]).toBe("application/json");

        const body = JSON.parse(opts?.body as string);
        expect(body.balance).toBe(7777.00);
        expect(body.snapshot_datetime).toBe("2026-04-06T12:00:00Z");

        const content = result.content as Array<{ type: string; text: string }>;
        const parsed = JSON.parse(content[0].text);
        expect(parsed.success).toBe(true);
    });

    it("omits snapshot_datetime from body when not provided", async () => {
        mockGuardAndApi({ id: 2, account_id: "ACC001", balance: 5000 }, 201);

        const client = await createTestClient();
        await client.callTool({
            name: "record_balance",
            arguments: { account_id: "ACC001", balance: 5000 },
        });

        const [, opts] = vi.mocked(fetch).mock.calls[1];
        const body = JSON.parse(opts?.body as string);
        expect(body.balance).toBe(5000);
        expect(body).not.toHaveProperty("snapshot_datetime");
    });
});
