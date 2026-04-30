/**
 * Unit tests for CompoundToolRouter.
 *
 * AC-1.1: CompoundToolRouter class exists with dispatch() method
 * AC-1.2: Router validates per-action params via strict Zod sub-schemas;
 *          unknown action-specific fields → InvalidParams
 *
 * Source: implementation-plan.md MC1 AC-1.1, AC-1.2
 * Phase: RED — tests written before implementation
 */

import { describe, it, expect } from "vitest";
import { z } from "zod";
import { CompoundToolRouter } from "../../src/compound/router.js";

describe("CompoundToolRouter", () => {
    // ── AC-1.1: Class exists with dispatch() ──────────────────────────

    it("can be instantiated with action handlers", () => {
        const router = new CompoundToolRouter({
            ping: {
                schema: z.object({}),
                handler: async () => ({
                    content: [{ type: "text" as const, text: "pong" }],
                }),
            },
        });
        expect(router).toBeDefined();
        expect(typeof router.dispatch).toBe("function");
    });

    it("dispatch() routes to the correct action handler", async () => {
        const router = new CompoundToolRouter({
            greet: {
                schema: z.object({
                    name: z.string(),
                }),
                handler: async (params) => ({
                    content: [
                        {
                            type: "text" as const,
                            text: `Hello, ${params.name}`,
                        },
                    ],
                }),
            },
        });

        const result = await router.dispatch("greet", { name: "World" });
        const text = (result.content as Array<{ type: string; text: string }>)[0]
            .text;
        expect(text).toBe("Hello, World");
    });

    // ── AC-1.2: Unknown action → error ────────────────────────────────

    it("returns InvalidParams error for unknown action", async () => {
        const router = new CompoundToolRouter({
            ping: {
                schema: z.object({}),
                handler: async () => ({
                    content: [{ type: "text" as const, text: "pong" }],
                }),
            },
        });

        const result = await router.dispatch("nonexistent", {});
        expect(result.isError).toBe(true);
        const text = (result.content as Array<{ type: string; text: string }>)[0]
            .text;
        expect(text).toContain("Unknown action");
        expect(text).toContain("nonexistent");
    });

    // ── AC-1.2: Unknown action-specific fields → InvalidParams ────────

    it("rejects unknown fields in per-action params via strict Zod", async () => {
        const router = new CompoundToolRouter({
            diagnose: {
                schema: z
                    .object({
                        verbose: z.boolean().default(false),
                    })
                    .strict(),
                handler: async (params) => ({
                    content: [
                        {
                            type: "text" as const,
                            text: JSON.stringify({ verbose: params.verbose }),
                        },
                    ],
                }),
            },
        });

        const result = await router.dispatch("diagnose", {
            verbose: true,
            bogus_field: "x",
        });
        expect(result.isError).toBe(true);
        const text = (result.content as Array<{ type: string; text: string }>)[0]
            .text;
        // Should mention the unrecognized key
        expect(text).toContain("bogus_field");
    });

    // ── AC-1.2: Valid params pass through ─────────────────────────────

    it("passes valid params through strict Zod validation", async () => {
        const router = new CompoundToolRouter({
            diagnose: {
                schema: z
                    .object({
                        verbose: z.boolean().default(false),
                    })
                    .strict(),
                handler: async (params) => ({
                    content: [
                        {
                            type: "text" as const,
                            text: JSON.stringify({ verbose: params.verbose }),
                        },
                    ],
                }),
            },
        });

        const result = await router.dispatch("diagnose", { verbose: true });
        expect(result.isError).toBeUndefined();
        const parsed = JSON.parse(
            (result.content as Array<{ type: string; text: string }>)[0].text,
        );
        expect(parsed.verbose).toBe(true);
    });

    it("applies Zod defaults for missing optional params", async () => {
        const router = new CompoundToolRouter({
            diagnose: {
                schema: z
                    .object({
                        verbose: z.boolean().default(false),
                    })
                    .strict(),
                handler: async (params) => ({
                    content: [
                        {
                            type: "text" as const,
                            text: JSON.stringify({ verbose: params.verbose }),
                        },
                    ],
                }),
            },
        });

        const result = await router.dispatch("diagnose", {});
        expect(result.isError).toBeUndefined();
        const parsed = JSON.parse(
            (result.content as Array<{ type: string; text: string }>)[0].text,
        );
        expect(parsed.verbose).toBe(false);
    });

    // ── Action listing ────────────────────────────────────────────────

    it("getActions() returns all registered action names", () => {
        const router = new CompoundToolRouter({
            alpha: {
                schema: z.object({}),
                handler: async () => ({
                    content: [{ type: "text" as const, text: "a" }],
                }),
            },
            beta: {
                schema: z.object({}),
                handler: async () => ({
                    content: [{ type: "text" as const, text: "b" }],
                }),
            },
        });

        const actions = router.getActions();
        expect(actions).toEqual(["alpha", "beta"]);
    });

    // ── Handler errors are caught ─────────────────────────────────────

    it("catches handler errors and returns isError response", async () => {
        const router = new CompoundToolRouter({
            failing: {
                schema: z.object({}),
                handler: async () => {
                    throw new Error("Handler exploded");
                },
            },
        });

        const result = await router.dispatch("failing", {});
        expect(result.isError).toBe(true);
        const text = (result.content as Array<{ type: string; text: string }>)[0]
            .text;
        expect(text).toContain("Handler exploded");
    });
});
