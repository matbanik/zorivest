/**
 * Tests for pipeline security MCP tools + resources.
 *
 * Source: 05g-mcp-scheduling.md, AC-33m
 * Validates: Tool registration count and names, resource registration count
 *            and URIs, seedRegistry pipeline-security toolset definition,
 *            Zod strict rejection of unknown fields, M7 description content.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";

// ── Registration structure ────────────────────────────────────────────

describe("registerPipelineSecurityTools", () => {
    it("returns 12 tool handles", async () => {
        const { registerPipelineSecurityTools } = await import(
            "../src/tools/pipeline-security-tools.js"
        );

        const mockHandle = { enable: vi.fn(), disable: vi.fn() };
        const mockServer = {
            registerTool: vi.fn().mockReturnValue(mockHandle),
            resource: vi.fn(),
        };

        const handles = registerPipelineSecurityTools(mockServer as never);
        expect(handles).toHaveLength(12);
        expect(mockServer.registerTool).toHaveBeenCalledTimes(12);
    });

    it("registers tools with correct names", async () => {
        const { registerPipelineSecurityTools } = await import(
            "../src/tools/pipeline-security-tools.js"
        );

        const registeredNames: string[] = [];
        const mockHandle = { enable: vi.fn(), disable: vi.fn() };
        const mockServer = {
            registerTool: vi.fn((name: string) => {
                registeredNames.push(name);
                return mockHandle;
            }),
            resource: vi.fn(),
        };

        registerPipelineSecurityTools(mockServer as never);

        // AC-16..AC-26: 12 tools per spec
        const expectedTools = [
            "emulate_policy",
            "validate_sql",
            "list_db_tables",
            "get_db_row_samples",
            "create_email_template",
            "get_email_template",
            "list_email_templates",
            "update_email_template",
            "delete_email_template",
            "preview_email_template",
            "list_step_types",
            "list_provider_capabilities",
        ];

        for (const name of expectedTools) {
            expect(registeredNames).toContain(name);
        }
    });

    it("registers tools with pipeline-security toolset metadata", async () => {
        const { registerPipelineSecurityTools } = await import(
            "../src/tools/pipeline-security-tools.js"
        );

        const registeredMeta: Array<Record<string, unknown>> = [];
        const mockHandle = { enable: vi.fn(), disable: vi.fn() };
        const mockServer = {
            registerTool: vi.fn(
                (_name: string, opts: Record<string, unknown>) => {
                    registeredMeta.push(
                        opts._meta as Record<string, unknown>,
                    );
                    return mockHandle;
                },
            ),
            resource: vi.fn(),
        };

        registerPipelineSecurityTools(mockServer as never);

        for (const meta of registeredMeta) {
            expect(meta).toMatchObject({
                toolset: "pipeline-security",
                alwaysLoaded: false,
            });
        }
    });

    it("all tool descriptions include M7 workflow context", async () => {
        const { registerPipelineSecurityTools } = await import(
            "../src/tools/pipeline-security-tools.js"
        );

        const toolDescriptions: Array<{ name: string; description: string }> = [];
        const mockHandle = { enable: vi.fn(), disable: vi.fn() };
        const mockServer = {
            registerTool: vi.fn(
                (name: string, opts: Record<string, unknown>) => {
                    toolDescriptions.push({
                        name,
                        description: (opts.description as string) ?? "",
                    });
                    return mockHandle;
                },
            ),
            resource: vi.fn(),
        };

        registerPipelineSecurityTools(mockServer as never);

        // M7: descriptions must include return shape or workflow context
        for (const { name, description } of toolDescriptions) {
            expect(
                description.length,
                `${name}: description too short for M7 compliance`,
            ).toBeGreaterThan(50);
            // M7 requires at least one of: Returns, Requires, Workflow, Prerequisite
            const hasWorkflowContext =
                /returns|requires|workflow|prerequisite/i.test(description);
            expect(
                hasWorkflowContext,
                `${name}: missing M7 workflow context (Returns/Requires/Workflow/Prerequisite)`,
            ).toBe(true);
        }
    });
});

// ── Resource registration ─────────────────────────────────────────────

describe("registerPipelineSecurityResources", () => {
    it("registers 6 resources", async () => {
        const { registerPipelineSecurityResources } = await import(
            "../src/tools/pipeline-security-tools.js"
        );

        const mockServer = {
            resource: vi.fn(),
        };

        registerPipelineSecurityResources(mockServer as never);
        expect(mockServer.resource).toHaveBeenCalledTimes(6);
    });

    it("registers correct resource URIs", async () => {
        const { registerPipelineSecurityResources } = await import(
            "../src/tools/pipeline-security-tools.js"
        );

        const registeredUris: string[] = [];
        const mockServer = {
            resource: vi.fn((uri: string) => {
                registeredUris.push(uri);
            }),
        };

        registerPipelineSecurityResources(mockServer as never);

        // AC-27: 6 resources per spec + implementation
        expect(registeredUris).toContain("pipeline://db-schema");
        expect(registeredUris).toContain("pipeline://templates");
        expect(registeredUris).toContain("pipeline://deny-tables");
        expect(registeredUris).toContain("pipeline://emulator/mock-data");
        expect(registeredUris).toContain("pipeline://emulator-phases");
        expect(registeredUris).toContain("pipeline://providers");
    });
});

// ── Seed registry integration ─────────────────────────────────────────

describe("seedRegistry pipeline-security toolset", () => {
    beforeEach(async () => {
        const { toolsetRegistry } = await import(
            "../src/toolsets/registry.js"
        );
        const reg = toolsetRegistry as unknown as {
            toolsets: Map<string, unknown>;
        };
        reg.toolsets.clear();
    });

    it("pipeline-security toolset has 12 tools in seed definition", async () => {
        const { toolsetRegistry } = await import(
            "../src/toolsets/registry.js"
        );
        const { seedRegistry } = await import("../src/toolsets/seed.js");

        seedRegistry(toolsetRegistry);

        const pipelineSecurity = toolsetRegistry.get("pipeline-security");
        expect(pipelineSecurity).toBeDefined();
        expect(pipelineSecurity!.tools).toHaveLength(12);
        expect(pipelineSecurity!.alwaysLoaded).toBe(false);
        expect(pipelineSecurity!.isDefault).toBe(false);
    });

    it("pipeline-security register callback invokes resource registration", async () => {
        const { toolsetRegistry } = await import(
            "../src/toolsets/registry.js"
        );
        const { seedRegistry } = await import("../src/toolsets/seed.js");

        seedRegistry(toolsetRegistry);

        const pipelineSecurity = toolsetRegistry.get("pipeline-security");
        expect(pipelineSecurity).toBeDefined();

        const mockHandle = { enable: vi.fn(), disable: vi.fn() };
        const mockServer = {
            registerTool: vi.fn().mockReturnValue(mockHandle),
            resource: vi.fn(),
        };

        pipelineSecurity!.register(mockServer as never);

        // Verify resources were registered (6 resources)
        expect(mockServer.resource).toHaveBeenCalledTimes(6);
    });

    it("pipeline-security seed tools match registered tool names", async () => {
        const { toolsetRegistry } = await import(
            "../src/toolsets/registry.js"
        );
        const { seedRegistry } = await import("../src/toolsets/seed.js");

        seedRegistry(toolsetRegistry);

        const pipelineSecurity = toolsetRegistry.get("pipeline-security");
        expect(pipelineSecurity).toBeDefined();

        const seedToolNames = pipelineSecurity!.tools.map(
            (t: { name: string }) => t.name,
        );

        // Register actual tools and collect names
        const registeredNames: string[] = [];
        const mockHandle = { enable: vi.fn(), disable: vi.fn() };
        const mockServer = {
            registerTool: vi.fn((name: string) => {
                registeredNames.push(name);
                return mockHandle;
            }),
            resource: vi.fn(),
        };

        pipelineSecurity!.register(mockServer as never);

        // Every seed tool name must appear in registered names
        for (const name of seedToolNames) {
            expect(
                registeredNames,
                `Seed tool '${name}' not found in registered tools`,
            ).toContain(name);
        }
    });
});

// ── Behavior-level tests (R5: AC-33m protocol coverage) ───────────────

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { InMemoryTransport } from "@modelcontextprotocol/sdk/inMemory.js";
import {
    registerPipelineSecurityTools,
    registerPipelineSecurityResources,
} from "../src/tools/pipeline-security-tools.js";

// ── Test helpers ───────────────────────────────────────────────────────

/** Guard-aware fetch mock: guard returns allowed, API returns response */
function mockGuardAndApiFetch(apiResponse: unknown = {}): void {
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
                ok: true,
                status: 200,
                json: () => Promise.resolve(apiResponse),
                text: () => Promise.resolve(JSON.stringify(apiResponse)),
            });
        }),
    );
}

async function createPipelineClient(): Promise<Client> {
    const server = new McpServer({ name: "test", version: "0.1.0" });
    registerPipelineSecurityTools(server);
    registerPipelineSecurityResources(server);

    const [clientTransport, serverTransport] =
        InMemoryTransport.createLinkedPair();
    const client = new Client({ name: "test-client", version: "0.1.0" });

    await Promise.all([
        client.connect(clientTransport),
        server.connect(serverTransport),
    ]);

    return client;
}

// ── 1. Endpoint target invocation ─────────────────────────────────────

describe("pipeline-security tools: endpoint targets", () => {
    beforeEach(() => {
        vi.restoreAllMocks();
    });

    it("emulate_policy calls POST /scheduling/emulator/run", async () => {
        mockGuardAndApiFetch({ valid: true, phase: "RENDER", errors: [] });
        const client = await createPipelineClient();

        await client.callTool({
            name: "emulate_policy",
            arguments: {
                policy_json: { name: "test", steps: [] },
            },
        });

        const apiCalls = vi
            .mocked(fetch)
            .mock.calls.filter(
                ([url]) =>
                    typeof url === "string" &&
                    !url.includes("/mcp-guard/"),
            );
        expect(apiCalls.length).toBeGreaterThanOrEqual(1);
        const [url, opts] = apiCalls[0];
        expect(url).toContain("/scheduling/emulator/run");
        expect(opts?.method).toBe("POST");
    });

    it("validate_sql calls POST /scheduling/validate-sql", async () => {
        mockGuardAndApiFetch({ valid: true, errors: [] });
        const client = await createPipelineClient();

        await client.callTool({
            name: "validate_sql",
            arguments: { sql: "SELECT * FROM trades LIMIT 5" },
        });

        const apiCalls = vi
            .mocked(fetch)
            .mock.calls.filter(
                ([url]) =>
                    typeof url === "string" &&
                    !url.includes("/mcp-guard/"),
            );
        expect(apiCalls.length).toBeGreaterThanOrEqual(1);
        const [url, opts] = apiCalls[0];
        expect(url).toContain("/scheduling/validate-sql");
        expect(opts?.method).toBe("POST");
    });

    it("list_db_tables calls GET /scheduling/db-schema", async () => {
        mockGuardAndApiFetch({ tables: ["trades", "accounts"] });
        const client = await createPipelineClient();

        await client.callTool({
            name: "list_db_tables",
            arguments: {},
        });

        const apiCalls = vi
            .mocked(fetch)
            .mock.calls.filter(
                ([url]) =>
                    typeof url === "string" &&
                    !url.includes("/mcp-guard/"),
            );
        expect(apiCalls.length).toBeGreaterThanOrEqual(1);
        expect(apiCalls[0][0]).toContain("/scheduling/db-schema");
    });

    it("list_step_types calls GET /scheduling/step-types", async () => {
        mockGuardAndApiFetch({ step_types: ["fetch", "query"] });
        const client = await createPipelineClient();

        await client.callTool({
            name: "list_step_types",
            arguments: {},
        });

        const apiCalls = vi
            .mocked(fetch)
            .mock.calls.filter(
                ([url]) =>
                    typeof url === "string" &&
                    !url.includes("/mcp-guard/"),
            );
        expect(apiCalls.length).toBeGreaterThanOrEqual(1);
        expect(apiCalls[0][0]).toContain("/scheduling/step-types");
    });

    it("list_provider_capabilities calls GET /market-data/providers", async () => {
        mockGuardAndApiFetch({ providers: [] });
        const client = await createPipelineClient();

        await client.callTool({
            name: "list_provider_capabilities",
            arguments: {},
        });

        const apiCalls = vi
            .mocked(fetch)
            .mock.calls.filter(
                ([url]) =>
                    typeof url === "string" &&
                    !url.includes("/mcp-guard/"),
            );
        expect(apiCalls.length).toBeGreaterThanOrEqual(1);
        expect(apiCalls[0][0]).toContain("/market-data/providers");
    });
});

// ── 2. Denied-table URL construction ──────────────────────────────────

describe("pipeline-security tools: denied-table behavior", () => {
    beforeEach(() => {
        vi.restoreAllMocks();
    });

    it("get_db_row_samples constructs correct URL with table and limit", async () => {
        mockGuardAndApiFetch([{ id: 1, name: "test" }]);
        const client = await createPipelineClient();

        await client.callTool({
            name: "get_db_row_samples",
            arguments: { table: "trades", limit: 3 },
        });

        const apiCalls = vi
            .mocked(fetch)
            .mock.calls.filter(
                ([url]) =>
                    typeof url === "string" &&
                    !url.includes("/mcp-guard/"),
            );
        expect(apiCalls.length).toBeGreaterThanOrEqual(1);
        const [url] = apiCalls[0];
        expect(url).toContain("/scheduling/db-schema/samples/trades");
        expect(url).toContain("limit=3");
    });

    it("get_db_row_samples encodes special characters in table name", async () => {
        mockGuardAndApiFetch([]);
        const client = await createPipelineClient();

        await client.callTool({
            name: "get_db_row_samples",
            arguments: { table: "my table/name", limit: 1 },
        });

        const apiCalls = vi
            .mocked(fetch)
            .mock.calls.filter(
                ([url]) =>
                    typeof url === "string" &&
                    !url.includes("/mcp-guard/"),
            );
        expect(apiCalls.length).toBeGreaterThanOrEqual(1);
        const [url] = apiCalls[0];
        // Must be URL-encoded, not raw
        expect(url).toContain("my%20table%2Fname");
        expect(url).not.toContain("my table/name");
    });
});

// ── 3. Resource handler JSON shape ────────────────────────────────────

describe("pipeline-security resources: handler JSON shape", () => {
    beforeEach(() => {
        vi.restoreAllMocks();
    });

    it("pipeline://deny-tables returns valid JSON array with correct shape", async () => {
        const mockServer = {
            resource: vi.fn(),
        };

        registerPipelineSecurityResources(mockServer as never);

        // Find the deny-tables handler (3rd resource call)
        const denyTablesCall = mockServer.resource.mock.calls.find(
            (call: unknown[]) => call[0] === "pipeline://deny-tables",
        );
        expect(denyTablesCall).toBeDefined();

        // Handler is the 3rd argument
        const handler = denyTablesCall![2] as () => Promise<{
            contents: Array<{ uri: string; text: string; mimeType: string }>;
        }>;
        const result = await handler();

        expect(result.contents).toHaveLength(1);
        expect(result.contents[0].uri).toBe("pipeline://deny-tables");
        expect(result.contents[0].mimeType).toBe("application/json");

        // text must be valid JSON array
        const parsed = JSON.parse(result.contents[0].text);
        expect(Array.isArray(parsed)).toBe(true);
        expect(parsed.length).toBeGreaterThan(0);
        // Must include known deny tables
        expect(parsed).toContain("settings");
        expect(parsed).toContain("sqlite_master");
    });

    it("pipeline://emulator-phases returns valid JSON with 4 phases", async () => {
        const mockServer = {
            resource: vi.fn(),
        };

        registerPipelineSecurityResources(mockServer as never);

        const phasesCall = mockServer.resource.mock.calls.find(
            (call: unknown[]) => call[0] === "pipeline://emulator-phases",
        );
        expect(phasesCall).toBeDefined();

        const handler = phasesCall![2] as () => Promise<{
            contents: Array<{ uri: string; text: string; mimeType: string }>;
        }>;
        const result = await handler();

        expect(result.contents).toHaveLength(1);
        expect(result.contents[0].uri).toBe("pipeline://emulator-phases");
        expect(result.contents[0].mimeType).toBe("application/json");

        const parsed = JSON.parse(result.contents[0].text) as {
            phases: Array<{ name: string; description: string }>;
        };
        expect(parsed.phases).toHaveLength(4);
        const phaseNames = parsed.phases.map((p) => p.name);
        expect(phaseNames).toEqual([
            "PARSE",
            "VALIDATE",
            "SIMULATE",
            "RENDER",
        ]);
        // Each phase must have a description
        for (const phase of parsed.phases) {
            expect(phase.description.length).toBeGreaterThan(10);
        }
    });
});

// ── 4. Zod-derived inputSchema structure ──────────────────────────────

describe("pipeline-security tools: inputSchema structure", () => {
    it("get_db_row_samples has table (required string) and limit (optional with default)", async () => {
        mockGuardAndApiFetch([]);
        const client = await createPipelineClient();
        const { tools } = await client.listTools();

        const samples = tools.find((t) => t.name === "get_db_row_samples");
        expect(samples).toBeDefined();

        const schema = samples!.inputSchema as {
            type: string;
            properties: Record<string, Record<string, unknown>>;
            required?: string[];
        };
        expect(schema.type).toBe("object");
        expect(schema.properties).toHaveProperty("table");
        expect(schema.properties).toHaveProperty("limit");
        // table must be required
        expect(schema.required).toContain("table");
        // limit has a default so should NOT be required
        expect(schema.required).not.toContain("limit");
    });

    it("validate_sql has sql as required string with maxLength", async () => {
        mockGuardAndApiFetch({});
        const client = await createPipelineClient();
        const { tools } = await client.listTools();

        const validateSql = tools.find((t) => t.name === "validate_sql");
        expect(validateSql).toBeDefined();

        const schema = validateSql!.inputSchema as {
            type: string;
            properties: Record<string, Record<string, unknown>>;
            required?: string[];
        };
        expect(schema.properties).toHaveProperty("sql");
        expect(schema.required).toContain("sql");
        // Zod .max(10000) should produce maxLength
        expect(schema.properties.sql.maxLength).toBe(10000);
    });

    it("emulate_policy has policy_json as required and phases as optional", async () => {
        mockGuardAndApiFetch({});
        const client = await createPipelineClient();
        const { tools } = await client.listTools();

        const emulate = tools.find((t) => t.name === "emulate_policy");
        expect(emulate).toBeDefined();

        const schema = emulate!.inputSchema as {
            type: string;
            properties: Record<string, Record<string, unknown>>;
            required?: string[];
        };
        expect(schema.properties).toHaveProperty("policy_json");
        expect(schema.required).toContain("policy_json");
        // phases is optional
        expect(schema.required).not.toContain("phases");
    });
});

// ── 5. Response content envelope format ───────────────────────────────

describe("pipeline-security tools: response content format", () => {
    beforeEach(() => {
        vi.restoreAllMocks();
    });

    it("validate_sql returns content envelope with valid JSON text", async () => {
        const apiResult = { valid: true, errors: [] };
        mockGuardAndApiFetch(apiResult);
        const client = await createPipelineClient();

        const result = await client.callTool({
            name: "validate_sql",
            arguments: { sql: "SELECT 1" },
        });

        const content = result.content as Array<{
            type: string;
            text: string;
        }>;
        expect(content).toHaveLength(1);
        expect(content[0].type).toBe("text");
        // text must be valid JSON
        const parsed = JSON.parse(content[0].text);
        expect(parsed).toBeDefined();
    });

    it("list_db_tables returns content envelope with valid JSON text", async () => {
        mockGuardAndApiFetch({ tables: ["trades"] });
        const client = await createPipelineClient();

        const result = await client.callTool({
            name: "list_db_tables",
            arguments: {},
        });

        const content = result.content as Array<{
            type: string;
            text: string;
        }>;
        expect(content).toHaveLength(1);
        expect(content[0].type).toBe("text");
        const parsed = JSON.parse(content[0].text);
        expect(parsed).toBeDefined();
    });

    it("get_db_row_samples returns content envelope with valid JSON text", async () => {
        mockGuardAndApiFetch([{ id: 1 }]);
        const client = await createPipelineClient();

        const result = await client.callTool({
            name: "get_db_row_samples",
            arguments: { table: "trades", limit: 1 },
        });

        const content = result.content as Array<{
            type: string;
            text: string;
        }>;
        expect(content).toHaveLength(1);
        expect(content[0].type).toBe("text");
        const parsed = JSON.parse(content[0].text);
        expect(parsed).toBeDefined();
    });
});

// ── 6. AC-31m: Strict schema rejection of unknown fields ──────────────

describe("pipeline-security tools: strict unknown-field rejection (AC-31m)", () => {
    beforeEach(() => {
        vi.restoreAllMocks();
    });

    it("validate_sql rejects unknown extra fields", async () => {
        mockGuardAndApiFetch({ valid: true, errors: [] });
        const client = await createPipelineClient();

        const result = await client.callTool({
            name: "validate_sql",
            arguments: { sql: "SELECT 1", extraField: "should-reject" },
        });

        // Must be an error — unknown field should trigger INVALID_PARAMS
        expect(result.isError).toBe(true);
        const text = (result.content as Array<{ text: string }>)[0].text;
        expect(text.toLowerCase()).toContain("unrecognized");
    });

    it("emulate_policy rejects unknown extra fields", async () => {
        mockGuardAndApiFetch({ valid: true, phase: "RENDER", errors: [] });
        const client = await createPipelineClient();

        const result = await client.callTool({
            name: "emulate_policy",
            arguments: {
                policy_json: { name: "test", steps: [] },
                unknownProp: true,
            },
        });

        expect(result.isError).toBe(true);
        const text = (result.content as Array<{ text: string }>)[0].text;
        expect(text.toLowerCase()).toContain("unrecognized");
    });

    it("get_db_row_samples rejects unknown extra fields", async () => {
        mockGuardAndApiFetch([{ id: 1 }]);
        const client = await createPipelineClient();

        const result = await client.callTool({
            name: "get_db_row_samples",
            arguments: { table: "trades", limit: 5, bogus: "field" },
        });

        expect(result.isError).toBe(true);
        const text = (result.content as Array<{ text: string }>)[0].text;
        expect(text.toLowerCase()).toContain("unrecognized");
    });
});

// ── 7. AC-28: Emulator MCP response cap (4 KiB) ──────────────────────

describe("pipeline-security tools: emulator 4 KiB response cap (AC-28)", () => {
    beforeEach(() => {
        vi.restoreAllMocks();
    });

    it("caps oversized emulator response to 4096 bytes", async () => {
        // Create a response that serializes to >4096 bytes
        const largeResult = {
            valid: true,
            phase: "RENDER",
            errors: [],
            mock_outputs: Array.from({ length: 200 }, (_, i) => ({
                step: `step_${i}`,
                data: "x".repeat(50),
                result: { ok: true, detail: `detail for step ${i}` },
            })),
        };
        mockGuardAndApiFetch(largeResult);
        const client = await createPipelineClient();

        const result = await client.callTool({
            name: "emulate_policy",
            arguments: { policy_json: { name: "big", steps: [] } },
        });

        const content = result.content as Array<{ text: string }>;
        expect(content).toHaveLength(1);
        // Response text must not exceed 4096 bytes
        const textBytes = new TextEncoder().encode(content[0].text).length;
        expect(textBytes).toBeLessThanOrEqual(4096);
        // Should contain truncation marker
        expect(content[0].text).toContain("[truncated");
    });

    it("preserves small emulator response unchanged", async () => {
        const smallResult = { valid: true, phase: "RENDER", errors: [] };
        mockGuardAndApiFetch(smallResult);
        const client = await createPipelineClient();

        const result = await client.callTool({
            name: "emulate_policy",
            arguments: { policy_json: { name: "small", steps: [] } },
        });

        const content = result.content as Array<{ text: string }>;
        expect(content).toHaveLength(1);
        // fetchApi wraps response in { success, data } envelope
        const parsed = JSON.parse(content[0].text) as {
            success: boolean;
            data: { valid: boolean };
        };
        expect(parsed.success).toBe(true);
        expect(parsed.data.valid).toBe(true);
        expect(content[0].text).not.toContain("[truncated");
    });

    it("caps non-ASCII oversized response to 4096 encoded bytes", async () => {
        // "é" is 2 bytes in UTF-8 — creates a payload where
        // string.length != encoded byte length
        const multiByteResult = {
            valid: true,
            phase: "RENDER",
            errors: [],
            data: "é".repeat(5000), // ~10,000 UTF-8 bytes
        };
        mockGuardAndApiFetch(multiByteResult);
        const client = await createPipelineClient();

        const result = await client.callTool({
            name: "emulate_policy",
            arguments: { policy_json: { name: "multibyte", steps: [] } },
        });

        const content = result.content as Array<{ text: string }>;
        expect(content).toHaveLength(1);
        // Encoded byte length must respect the 4096-byte cap
        const textBytes = new TextEncoder().encode(content[0].text).length;
        expect(textBytes).toBeLessThanOrEqual(4096);
        expect(content[0].text).toContain("[truncated");
    });
});
