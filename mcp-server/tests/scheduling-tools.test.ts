/**
 * Tests for scheduling MCP tools.
 *
 * Source: 05g-mcp-scheduling.md
 * Validates: Tool registration count, handle management,
 *            seedRegistry scheduling toolset definition.
 */

import { describe, it, expect, vi } from "vitest";

// ── Registration structure ────────────────────────────────────────────

describe("registerSchedulingTools", () => {
    it("returns 6 tool handles", async () => {
        const { registerSchedulingTools } = await import(
            "../src/tools/scheduling-tools.js"
        );

        // Create a mock McpServer with registerTool that returns fake handles
        const mockHandle = { enable: vi.fn(), disable: vi.fn() };
        const mockServer = {
            registerTool: vi.fn().mockReturnValue(mockHandle),
            resource: vi.fn(),
        };

        const handles = registerSchedulingTools(mockServer as never);
        expect(handles).toHaveLength(9);
        expect(mockServer.registerTool).toHaveBeenCalledTimes(9);
    });

    it("registers tools with correct names", async () => {
        const { registerSchedulingTools } = await import(
            "../src/tools/scheduling-tools.js"
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

        registerSchedulingTools(mockServer as never);

        expect(registeredNames).toContain("create_policy");
        expect(registeredNames).toContain("list_policies");
        expect(registeredNames).toContain("run_pipeline");
        expect(registeredNames).toContain("preview_report");
        expect(registeredNames).toContain("update_policy_schedule");
        expect(registeredNames).toContain("get_pipeline_history");
        // PH12 gap-fill tools
        expect(registeredNames).toContain("delete_policy");
        expect(registeredNames).toContain("update_policy");
        expect(registeredNames).toContain("get_email_config");
    });

    it("registers tools with scheduling toolset metadata", async () => {
        const { registerSchedulingTools } = await import(
            "../src/tools/scheduling-tools.js"
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

        registerSchedulingTools(mockServer as never);

        for (const meta of registeredMeta) {
            expect(meta).toMatchObject({
                toolset: "scheduling",
                alwaysLoaded: false,
            });
        }
    });
});

// ── Resource registration ─────────────────────────────────────────────

describe("registerSchedulingResources", () => {
    it("registers 2 resources", async () => {
        const { registerSchedulingResources } = await import(
            "../src/tools/scheduling-tools.js"
        );

        const mockServer = {
            resource: vi.fn(),
        };

        registerSchedulingResources(mockServer as never);
        expect(mockServer.resource).toHaveBeenCalledTimes(2);
    });

    it("registers correct resource URIs", async () => {
        const { registerSchedulingResources } = await import(
            "../src/tools/scheduling-tools.js"
        );

        const registeredUris: string[] = [];
        const mockServer = {
            resource: vi.fn((uri: string) => {
                registeredUris.push(uri);
            }),
        };

        registerSchedulingResources(mockServer as never);

        expect(registeredUris).toContain("pipeline://policies/schema");
        expect(registeredUris).toContain("pipeline://step-types");
    });
});

// ── Seed registry integration ─────────────────────────────────────────

describe("seedRegistry scheduling toolset", () => {
    it("scheduling toolset has 9 tools in seed definition", async () => {
        const { toolsetRegistry } = await import(
            "../src/toolsets/registry.js"
        );
        const { seedRegistry } = await import("../src/toolsets/seed.js");

        seedRegistry(toolsetRegistry);

        const scheduling = toolsetRegistry.get("scheduling");
        expect(scheduling).toBeDefined();
        expect(scheduling!.tools).toHaveLength(9);
        expect(scheduling!.alwaysLoaded).toBe(false);
        expect(scheduling!.isDefault).toBe(false);
    });

    it("scheduling register callback invokes resource registration", async () => {
        const { toolsetRegistry } = await import(
            "../src/toolsets/registry.js"
        );
        const { seedRegistry } = await import("../src/toolsets/seed.js");

        seedRegistry(toolsetRegistry);

        const scheduling = toolsetRegistry.get("scheduling");
        expect(scheduling).toBeDefined();

        // Create a mock server to capture resource registration
        const mockHandle = { enable: vi.fn(), disable: vi.fn() };
        const mockServer = {
            registerTool: vi.fn().mockReturnValue(mockHandle),
            resource: vi.fn(),
        };

        // Call the register function from seed
        scheduling!.register(mockServer as never);

        // Verify that resources were registered (via server.resource calls)
        expect(mockServer.resource).toHaveBeenCalledTimes(2);
    });
});
