/**
 * Tests for PH12: MCP Scheduling Gap Fill tools.
 *
 * Source: 09g §9G.2b, §9G.2c
 * MEU: PH12 (mcp-scheduling-gap)
 * ACs: AC-13..AC-20, AC-25
 *
 * Tests validate registration of delete_policy, update_policy, and get_email_config
 * tools with correct schemas, annotations, and toolset metadata.
 */

import { describe, it, expect, vi } from "vitest";
import type { ZodObject, ZodRawShape } from "zod";

describe("PH12: Scheduling Gap Fill Tools", () => {
    // AC-16: delete_policy is in DESTRUCTIVE_TOOLS
    it("AC-16: delete_policy is registered as destructive", async () => {
        const { isDestructiveTool } = await import(
            "../src/middleware/confirmation.js"
        );
        expect(isDestructiveTool("delete_policy")).toBe(true);
    });

    // AC-13: delete_policy requires confirmation_token in schema
    it("AC-13: delete_policy schema includes confirmation_token field", async () => {
        const { registerSchedulingTools } = await import(
            "../src/tools/scheduling-tools.js"
        );

        const registeredSchemas: Record<string, unknown> = {};
        const mockHandle = { enable: vi.fn(), disable: vi.fn() };
        const mockServer = {
            registerTool: vi.fn(
                (name: string, opts: Record<string, unknown>) => {
                    registeredSchemas[name] = opts.inputSchema;
                    return mockHandle;
                },
            ),
            resource: vi.fn(),
        };

        registerSchedulingTools(mockServer as never);

        const schema = registeredSchemas["delete_policy"] as ZodObject<ZodRawShape>;
        expect(schema).toBeDefined();
        // z.object().strict() has shape accessible via .shape
        expect(schema.shape["confirmation_token"]).toBeDefined();
        expect(schema.shape["policy_id"]).toBeDefined();
    });

    // AC-17: update_policy tool exists with policy_id and policy_json
    it("AC-17: update_policy is registered with correct schema", async () => {
        const { registerSchedulingTools } = await import(
            "../src/tools/scheduling-tools.js"
        );

        const registeredSchemas: Record<string, unknown> = {};
        const mockHandle = { enable: vi.fn(), disable: vi.fn() };
        const mockServer = {
            registerTool: vi.fn(
                (name: string, opts: Record<string, unknown>) => {
                    registeredSchemas[name] = opts.inputSchema;
                    return mockHandle;
                },
            ),
            resource: vi.fn(),
        };

        registerSchedulingTools(mockServer as never);

        const schema = registeredSchemas["update_policy"] as ZodObject<ZodRawShape>;
        expect(schema).toBeDefined();
        expect(schema.shape["policy_id"]).toBeDefined();
        expect(schema.shape["policy_json"]).toBeDefined();
    });

    // AC-19: get_email_config tool is registered
    it("AC-19: get_email_config is registered", async () => {
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

        expect(registeredNames).toContain("get_email_config");
    });

    // AC-22: All 3 tools have _meta.toolset: "scheduling"
    it("AC-22: new tools have scheduling toolset metadata", async () => {
        const { registerSchedulingTools } = await import(
            "../src/tools/scheduling-tools.js"
        );

        const toolMeta: Record<string, Record<string, unknown>> = {};
        const mockHandle = { enable: vi.fn(), disable: vi.fn() };
        const mockServer = {
            registerTool: vi.fn(
                (name: string, opts: Record<string, unknown>) => {
                    toolMeta[name] = opts._meta as Record<string, unknown>;
                    return mockHandle;
                },
            ),
            resource: vi.fn(),
        };

        registerSchedulingTools(mockServer as never);

        for (const toolName of ["delete_policy", "update_policy", "get_email_config"]) {
            expect(toolMeta[toolName]).toBeDefined();
            expect(toolMeta[toolName]["toolset"]).toBe("scheduling");
        }
    });

    // AC-21: All 3 tools have annotations with correct hints
    it("AC-21: new tools have correct annotation hints", async () => {
        const { registerSchedulingTools } = await import(
            "../src/tools/scheduling-tools.js"
        );

        const toolAnnotations: Record<string, Record<string, unknown>> = {};
        const mockHandle = { enable: vi.fn(), disable: vi.fn() };
        const mockServer = {
            registerTool: vi.fn(
                (name: string, opts: Record<string, unknown>) => {
                    toolAnnotations[name] = opts.annotations as Record<string, unknown>;
                    return mockHandle;
                },
            ),
            resource: vi.fn(),
        };

        registerSchedulingTools(mockServer as never);

        // delete_policy: destructive, not read-only
        expect(toolAnnotations["delete_policy"]).toMatchObject({
            readOnlyHint: false,
            destructiveHint: true,
        });

        // update_policy: not read-only, not destructive
        expect(toolAnnotations["update_policy"]).toMatchObject({
            readOnlyHint: false,
            destructiveHint: false,
        });

        // get_email_config: read-only
        expect(toolAnnotations["get_email_config"]).toMatchObject({
            readOnlyHint: true,
            destructiveHint: false,
        });
    });

    // AC-25: delete_policy and update_policy schemas use strict mode
    it("AC-25: delete_policy and update_policy schemas reject extra fields", async () => {
        const { registerSchedulingTools } = await import(
            "../src/tools/scheduling-tools.js"
        );

        const registeredSchemas: Record<string, unknown> = {};
        const mockHandle = { enable: vi.fn(), disable: vi.fn() };
        const mockServer = {
            registerTool: vi.fn(
                (name: string, opts: Record<string, unknown>) => {
                    registeredSchemas[name] = opts.inputSchema;
                    return mockHandle;
                },
            ),
            resource: vi.fn(),
        };

        registerSchedulingTools(mockServer as never);

        // Verify .strict() by attempting to parse with extra fields
        const deleteSchema = registeredSchemas["delete_policy"] as ZodObject<ZodRawShape>;
        const updateSchema = registeredSchemas["update_policy"] as ZodObject<ZodRawShape>;

        expect(deleteSchema).toBeDefined();
        expect(updateSchema).toBeDefined();

        // delete_policy: extra field should fail
        const deleteResult = deleteSchema.safeParse({
            policy_id: "test-uuid",
            extra_field: "should-fail",
        });
        expect(deleteResult.success).toBe(false);

        // update_policy: extra field should fail
        const updateResult = updateSchema.safeParse({
            policy_id: "test-uuid",
            policy_json: { name: "test" },
            extra_field: "should-fail",
        });
        expect(updateResult.success).toBe(false);
    });

    // AC-23: Tool descriptions include workflow context
    it("AC-23: tool descriptions mention prerequisites and return shapes", async () => {
        const { registerSchedulingTools } = await import(
            "../src/tools/scheduling-tools.js"
        );

        const toolDescriptions: Record<string, string> = {};
        const mockHandle = { enable: vi.fn(), disable: vi.fn() };
        const mockServer = {
            registerTool: vi.fn(
                (name: string, opts: Record<string, unknown>) => {
                    toolDescriptions[name] = opts.description as string;
                    return mockHandle;
                },
            ),
            resource: vi.fn(),
        };

        registerSchedulingTools(mockServer as never);

        // delete_policy description should mention confirmation
        expect(toolDescriptions["delete_policy"]).toMatch(/confirm/i);

        // update_policy description should mention policy update
        expect(toolDescriptions["update_policy"]).toMatch(/updat/i);

        // get_email_config description should mention email or SMTP
        expect(toolDescriptions["get_email_config"]).toMatch(/email|smtp/i);
    });

    // Tool count: original 6 + 3 new = 9 total
    it("registers 9 total scheduling tools (6 existing + 3 new)", async () => {
        const { registerSchedulingTools } = await import(
            "../src/tools/scheduling-tools.js"
        );

        const mockHandle = { enable: vi.fn(), disable: vi.fn() };
        const mockServer = {
            registerTool: vi.fn().mockReturnValue(mockHandle),
            resource: vi.fn(),
        };

        const handles = registerSchedulingTools(mockServer as never);
        expect(handles).toHaveLength(9);
    });
});
