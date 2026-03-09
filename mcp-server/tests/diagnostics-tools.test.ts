/**
 * Unit tests for diagnostics MCP tools.
 *
 * Tests verify `zorivest_diagnose` tool: safe-fetch, partial availability,
 * no API key leakage, metrics stubs, unauthenticated handling, auth header
 * forwarding, and MCP metadata (annotations + _meta).
 * Uses mocked global.fetch — no live API needed.
 *
 * Source: 05b-mcp-zorivest-diagnostics.md, FIC AC-1 through AC-9
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { registerDiagnosticsTools } from "../src/tools/diagnostics-tools.js";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { InMemoryTransport } from "@modelcontextprotocol/sdk/inMemory.js";

// ── Test helpers ───────────────────────────────────────────────────────

async function createTestClient(): Promise<Client> {
    const server = new McpServer({ name: "test", version: "0.1.0" });
    registerDiagnosticsTools(server);

    const [clientTransport, serverTransport] =
        InMemoryTransport.createLinkedPair();

    const client = new Client({ name: "test-client", version: "0.1.0" });

    await Promise.all([
        client.connect(clientTransport),
        server.connect(serverTransport),
    ]);

    return client;
}

function mockHealthyBackend(): void {
    vi.stubGlobal(
        "fetch",
        vi.fn().mockImplementation((url: string) => {
            if (url.includes("/health")) {
                return Promise.resolve({
                    ok: true,
                    json: () =>
                        Promise.resolve({
                            status: "ok",
                            version: "1.0.0",
                            uptime_seconds: 120,
                            database: { unlocked: true },
                        }),
                });
            }
            if (url.includes("/version")) {
                return Promise.resolve({
                    ok: true,
                    json: () =>
                        Promise.resolve({
                            version: "1.0.0",
                            context: "dev",
                        }),
                });
            }
            if (url.includes("/mcp-guard")) {
                return Promise.resolve({
                    ok: true,
                    json: () =>
                        Promise.resolve({
                            is_enabled: true,
                            is_locked: false,
                            locked_at: null,
                            lock_reason: null,
                            calls_per_minute_limit: 60,
                            calls_per_hour_limit: 1000,
                            recent_calls_1min: 5,
                            recent_calls_1hr: 42,
                        }),
                });
            }
            if (url.includes("/market-data/providers")) {
                return Promise.resolve({
                    ok: true,
                    json: () =>
                        Promise.resolve([
                            {
                                name: "alpha_vantage",
                                is_enabled: true,
                                has_key: true,
                            },
                        ]),
                });
            }
            return Promise.reject(new Error("Unexpected URL: " + url));
        }),
    );
}

// ── Tests ──────────────────────────────────────────────────────────────

describe("zorivest_diagnose", () => {
    beforeEach(() => {
        vi.restoreAllMocks();
    });

    // AC-2: Returns full report with all expected sections + correct guard schema
    it("returns full report when backend is reachable", async () => {
        mockHealthyBackend();

        const client = await createTestClient();
        const result = await client.callTool({
            name: "zorivest_diagnose",
            arguments: { verbose: false },
        });

        const content = result.content as Array<{
            type: string;
            text: string;
        }>;
        expect(content).toHaveLength(1);
        expect(content[0].type).toBe("text");

        const report = JSON.parse(content[0].text);
        // Required top-level keys
        expect(report.backend.reachable).toBe(true);
        expect(report.backend.status).toBe("ok");
        expect(report.version).toBeDefined();
        expect(report.database.unlocked).toBe(true);
        // Guard should have live McpGuardStatus fields
        expect(report.guard.enabled).toBe(true);
        expect(report.guard.locked).toBe(false);
        expect(report.guard.lock_reason).toBe(null);
        expect(report.guard.recent_calls_1min).toBe(5);
        expect(report.guard.recent_calls_1hr).toBe(42);
        // No stale call_count field
        expect(report.guard).not.toHaveProperty("call_count");
        // Provider + server + metrics
        expect(report.providers).toBeInstanceOf(Array);
        expect(report.mcp_server.node_version).toBeDefined();
        expect(report.mcp_server.uptime_minutes).toBeDefined();
        expect(report.metrics).toBeDefined();
    });

    // AC-3: Never throws — reports unreachable
    it("reports unreachable when backend is down", async () => {
        vi.stubGlobal(
            "fetch",
            vi.fn().mockRejectedValue(new Error("ECONNREFUSED")),
        );

        const client = await createTestClient();
        const result = await client.callTool({
            name: "zorivest_diagnose",
            arguments: {},
        });

        const content = result.content as Array<{
            type: string;
            text: string;
        }>;
        const report = JSON.parse(content[0].text);

        expect(report.backend.reachable).toBe(false);
        expect(report.backend.status).toBe("unreachable");
        expect(report.database.unlocked).toBe("unknown");
    });

    // AC-4: Provider list never contains api_key
    it("never reveals API keys in provider list", async () => {
        vi.stubGlobal(
            "fetch",
            vi.fn().mockImplementation((url: string) => {
                if (url.includes("/market-data/providers")) {
                    return Promise.resolve({
                        ok: true,
                        json: () =>
                            Promise.resolve([
                                {
                                    name: "polygon",
                                    is_enabled: true,
                                    has_key: true,
                                    api_key: "SECRET_KEY_123",
                                },
                            ]),
                    });
                }
                return Promise.resolve({
                    ok: true,
                    json: () => Promise.resolve({}),
                });
            }),
        );

        const client = await createTestClient();
        const result = await client.callTool({
            name: "zorivest_diagnose",
            arguments: {},
        });

        const content = result.content as Array<{
            type: string;
            text: string;
        }>;
        const text = content[0].text;

        expect(text).not.toContain("SECRET_KEY_123");
        const report = JSON.parse(text);
        expect(report.providers[0].name).toBe("polygon");
        expect(report.providers[0].has_key).toBe(true);
        expect(report.providers[0]).not.toHaveProperty("api_key");
    });

    // AC-8: Returns providers: [] when endpoint returns 404
    it("returns providers: [] when provider endpoint returns 404", async () => {
        vi.stubGlobal(
            "fetch",
            vi.fn().mockImplementation((url: string) => {
                if (url.includes("/market-data/providers")) {
                    return Promise.resolve({
                        ok: false,
                        status: 404,
                        json: () =>
                            Promise.resolve({ detail: "Not Found" }),
                    });
                }
                return Promise.resolve({
                    ok: true,
                    json: () =>
                        Promise.resolve({
                            status: "ok",
                            database: { unlocked: true },
                        }),
                });
            }),
        );

        const client = await createTestClient();
        const result = await client.callTool({
            name: "zorivest_diagnose",
            arguments: {},
        });

        const content = result.content as Array<{
            type: string;
            text: string;
        }>;
        const report = JSON.parse(content[0].text);

        expect(report.providers).toEqual([]);
    });

    // AC-7: verbose=true includes per-tool metrics
    it("includes per-tool metrics section when verbose=true", async () => {
        mockHealthyBackend();

        const client = await createTestClient();
        const result = await client.callTool({
            name: "zorivest_diagnose",
            arguments: { verbose: true },
        });

        const content = result.content as Array<{
            type: string;
            text: string;
        }>;
        const report = JSON.parse(content[0].text);

        expect(report.metrics).toBeDefined();
        expect(report.metrics.session_uptime_minutes).toBeDefined();
        expect(report.metrics.total_tool_calls).toBeDefined();
        expect(report.metrics).toHaveProperty("per_tool");
    });

    // AC-7: verbose=false returns summary only
    it("returns summary-only metrics when verbose=false", async () => {
        mockHealthyBackend();

        const client = await createTestClient();
        const result = await client.callTool({
            name: "zorivest_diagnose",
            arguments: { verbose: false },
        });

        const content = result.content as Array<{
            type: string;
            text: string;
        }>;
        const report = JSON.parse(content[0].text);

        expect(report.metrics).toBeDefined();
        expect(report.metrics.session_uptime_minutes).toBeDefined();
        expect(report.metrics).not.toHaveProperty("per_tool");
    });

    // AC-9: Auth-dependent fields report "unavailable" when unauthenticated
    it('returns "unavailable" for auth-dependent fields when guard endpoint fails', async () => {
        vi.stubGlobal(
            "fetch",
            vi.fn().mockImplementation((url: string) => {
                if (url.includes("/health")) {
                    return Promise.resolve({
                        ok: true,
                        json: () =>
                            Promise.resolve({
                                status: "ok",
                                database: { unlocked: true },
                            }),
                    });
                }
                if (
                    url.includes("/mcp-guard") ||
                    url.includes("/market-data/providers")
                ) {
                    return Promise.resolve({
                        ok: false,
                        status: 401,
                        json: () =>
                            Promise.resolve({
                                detail: "Not authenticated",
                            }),
                    });
                }
                return Promise.resolve({
                    ok: true,
                    json: () => Promise.resolve({}),
                });
            }),
        );

        const client = await createTestClient();
        const result = await client.callTool({
            name: "zorivest_diagnose",
            arguments: {},
        });

        const content = result.content as Array<{
            type: string;
            text: string;
        }>;
        const report = JSON.parse(content[0].text);

        expect(report.guard.status).toBe("unavailable");
        expect(report.providers).toEqual([]);
    });

    // AC-10: Auth headers forwarded to auth-dependent endpoints
    it("passes auth headers to mcp-guard and market-data endpoints", async () => {
        mockHealthyBackend();

        const client = await createTestClient();
        await client.callTool({
            name: "zorivest_diagnose",
            arguments: {},
        });

        // getAuthHeaders() returns {} when unauthenticated, so headers
        // should be present in the fetch options (even if empty object)
        const mock = fetch as ReturnType<typeof vi.fn>;
        const guardCall = mock.mock.calls.find(
            (c: unknown[]) => (c[0] as string).includes("/mcp-guard/status"),
        );
        const providerCall = mock.mock.calls.find(
            (c: unknown[]) =>
                (c[0] as string).includes("/market-data/providers"),
        );
        const healthCall = mock.mock.calls.find(
            (c: unknown[]) => (c[0] as string).includes("/health"),
        );

        // Auth-dependent endpoints should have options with headers
        expect(guardCall?.[1]).toBeDefined();
        expect(guardCall?.[1]).toHaveProperty("headers");
        expect(providerCall?.[1]).toBeDefined();
        expect(providerCall?.[1]).toHaveProperty("headers");
        // Public endpoints should NOT have options
        expect(healthCall?.[1]).toBeUndefined();
    });

    // Metadata tests: annotations and _meta
    it("registers tool with correct annotations and _meta", async () => {
        const client = await createTestClient();
        const { tools } = await client.listTools();

        const diag = tools.find((t) => t.name === "zorivest_diagnose");
        expect(diag).toBeDefined();
        expect(diag!.description).toContain("Runtime diagnostics");

        // Annotations per spec
        expect(diag!.annotations?.readOnlyHint).toBe(true);
        expect(diag!.annotations?.destructiveHint).toBe(false);
        expect(diag!.annotations?.idempotentHint).toBe(true);

        // _meta per FIC (vendor extension — cast to access)
        const meta = (diag as Record<string, unknown>)._meta as
            | Record<string, unknown>
            | undefined;
        expect(meta).toBeDefined();
        expect(meta!.toolset).toBe("core");
        expect(meta!.alwaysLoaded).toBe(true);
    });
});
