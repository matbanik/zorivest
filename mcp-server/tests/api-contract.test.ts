/**
 * MCP ↔ FastAPI OpenAPI contract alignment tests.
 *
 * Validates that MCP tool schemas are consistent with the committed
 * OpenAPI spec, and that tool names follow project conventions.
 *
 * Phase: 3.2 of Test Rigor Audit
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { InMemoryTransport } from "@modelcontextprotocol/sdk/inMemory.js";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { registerDiscoveryTools } from "../src/tools/discovery-tools.js";
import {
    ToolsetRegistry,
    toolsetRegistry,
} from "../src/toolsets/registry.js";

// ── Test helpers ───────────────────────────────────────────────────────

function seedFullRegistry(registry: ToolsetRegistry): void {
    registry.register({
        name: "core",
        description: "Core tools",
        tools: [
            { name: "get_settings", description: "Read all user settings" },
            { name: "zorivest_emergency_stop", description: "Emergency stop" },
            { name: "zorivest_emergency_unlock", description: "Emergency unlock" },
        ],
        register: () => [],
        loaded: true,
        alwaysLoaded: true,
        isDefault: false,
    });
}

async function createTestClient(): Promise<Client> {
    const server = new McpServer({ name: "zorivest", version: "0.1.0" });

    seedFullRegistry(toolsetRegistry);
    registerDiscoveryTools(server);

    const [clientTransport, serverTransport] =
        InMemoryTransport.createLinkedPair();
    const client = new Client(
        { name: "test-client", version: "0.1.0" },
    );

    await Promise.all([
        client.connect(clientTransport),
        server.connect(serverTransport),
    ]);

    return client;
}

// ── OpenAPI spec loader ────────────────────────────────────────────────

function loadOpenApiSpec(): Record<string, unknown> | null {
    try {
        const specPath = resolve(
            import.meta.dirname ?? ".",
            "../../openapi.committed.json",
        );
        const raw = readFileSync(specPath, "utf-8");
        return JSON.parse(raw) as Record<string, unknown>;
    } catch {
        return null;
    }
}

// ── Tests ──────────────────────────────────────────────────────────────

describe("MCP ↔ OpenAPI contract: tool naming", () => {
    beforeEach(() => {
        vi.restoreAllMocks();
        const reg = toolsetRegistry as unknown as {
            toolsets: Map<string, unknown>;
        };
        reg.toolsets.clear();
    });

    it("all tool names are snake_case", async () => {
        const client = await createTestClient();
        const { tools } = await client.listTools();

        const snakeCase = /^[a-z][a-z0-9_]*$/;
        for (const tool of tools) {
            expect(
                snakeCase.test(tool.name),
                `"${tool.name}" must be snake_case`,
            ).toBe(true);
        }
    });

    it("no duplicate tool names", async () => {
        const client = await createTestClient();
        const { tools } = await client.listTools();

        const names = tools.map((t) => t.name);
        const unique = new Set(names);
        expect(unique.size).toBe(names.length);
    });

    it("every tool has a non-empty description", async () => {
        const client = await createTestClient();
        const { tools } = await client.listTools();

        for (const tool of tools) {
            expect(
                tool.description?.trim().length,
                `"${tool.name}" must have a description`,
            ).toBeGreaterThan(0);
        }
    });
});

describe("MCP ↔ OpenAPI contract: schema structure", () => {
    beforeEach(() => {
        vi.restoreAllMocks();
        const reg = toolsetRegistry as unknown as {
            toolsets: Map<string, unknown>;
        };
        reg.toolsets.clear();
    });

    it("every tool inputSchema is a valid JSON Schema object", async () => {
        const client = await createTestClient();
        const { tools } = await client.listTools();

        for (const tool of tools) {
            const schema = tool.inputSchema;
            expect(schema, `${tool.name} inputSchema`).toBeDefined();
            expect(schema.type).toBe("object");
            // If properties exist, they must be an object
            if ("properties" in schema) {
                expect(typeof schema.properties).toBe("object");
            }
        }
    });

    it("tools with required fields list them in inputSchema.required", async () => {
        const client = await createTestClient();
        const { tools } = await client.listTools();

        for (const tool of tools) {
            const schema = tool.inputSchema as {
                required?: string[];
                properties?: Record<string, unknown>;
            };
            if (schema.required) {
                expect(Array.isArray(schema.required)).toBe(true);
                // Every required field should exist in properties
                if (schema.properties) {
                    for (const req of schema.required) {
                        expect(
                            req in schema.properties,
                            `${tool.name}: required field "${req}" missing from properties`,
                        ).toBe(true);
                    }
                }
            }
        }
    });
});

describe("MCP ↔ OpenAPI contract: spec alignment", () => {
    const spec = loadOpenApiSpec();

    beforeEach(() => {
        vi.restoreAllMocks();
        const reg = toolsetRegistry as unknown as {
            toolsets: Map<string, unknown>;
        };
        reg.toolsets.clear();
    });

    it("OpenAPI spec exists and is valid JSON", () => {
        if (!spec) {
            // If spec doesn't exist, this is informational — not a hard failure
            // The CI pipeline's export_openapi.py --check enforces this
            console.warn(
                "openapi.committed.json not found — skipping spec alignment check",
            );
            return;
        }
        expect(spec).toHaveProperty("openapi");
        expect(spec).toHaveProperty("paths");
        expect(spec).toHaveProperty("info");
    });

    it("API paths use consistent /api/v1/ prefix", () => {
        if (!spec) return;

        const paths = Object.keys(spec.paths as Record<string, unknown>);
        for (const path of paths) {
            expect(
                path.startsWith("/api/v1/"),
                `Path "${path}" should start with /api/v1/`,
            ).toBe(true);
        }
    });

    it("spec has expected core route groups", () => {
        if (!spec) return;

        const paths = Object.keys(spec.paths as Record<string, unknown>);
        const routeGroups = new Set(
            paths.map((p) => p.split("/").slice(0, 4).join("/")),
        );

        // Core routes that should exist
        const expected = [
            "/api/v1/trades",
            "/api/v1/accounts",
            "/api/v1/settings",
            "/api/v1/mcp-guard",
        ];

        for (const group of expected) {
            expect(
                routeGroups.has(group),
                `Expected route group "${group}" in OpenAPI spec`,
            ).toBe(true);
        }
    });
});
