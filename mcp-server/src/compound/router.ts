/**
 * CompoundToolRouter — action-based dispatch for compound MCP tools.
 *
 * Routes a top-level `action` field to the correct handler, validating
 * per-action parameters via strict Zod sub-schemas. This prevents
 * unknown field injection at the action level (mitigates [MCP-ZODSTRIP]).
 *
 * Usage:
 *   const router = new CompoundToolRouter({
 *       diagnose: {
 *           schema: z.object({ verbose: z.boolean().default(false) }).strict(),
 *           handler: async (params) => ({ content: [...] }),
 *       },
 *   });
 *   // In registerTool handler:
 *   return router.dispatch(params.action, params);
 *
 * Source: mcp-consolidation-proposal-v3.md §5
 * MEU: MC1 (compound-router-system)
 */

import type { z } from "zod";
import type { CallToolResult } from "@modelcontextprotocol/sdk/types.js";

// ── Types ──────────────────────────────────────────────────────────────

/** MCP tool result shape — re-export SDK type for compound tool handlers */
export type ToolResult = CallToolResult;

/** Per-action handler definition */
export interface ActionHandler<T extends z.ZodTypeAny = z.ZodTypeAny> {
    /** Strict Zod schema for this action's parameters (excluding `action` field) */
    schema: T;
    /** Handler function receiving validated params */
    handler: (params: z.infer<T>, extra?: unknown) => Promise<ToolResult>;
}

/** Map of action name → handler definition */
export type ActionMap = Record<string, ActionHandler>;

// ── CompoundToolRouter ─────────────────────────────────────────────────

export class CompoundToolRouter {
    private readonly actions: ActionMap;

    constructor(actions: ActionMap) {
        this.actions = actions;
    }

    /**
     * Dispatch an action with parameter validation.
     *
     * 1. Lookup action handler by name
     * 2. Strip `action` field from params, validate remaining via strict Zod schema
     * 3. Call handler with validated params
     * 4. Catch handler errors and return isError response
     */
    async dispatch(
        action: string,
        rawParams: Record<string, unknown>,
        extra?: unknown,
    ): Promise<ToolResult> {
        const def = this.actions[action];
        if (!def) {
            const valid = Object.keys(this.actions).join(", ");
            return {
                content: [
                    {
                        type: "text" as const,
                        text: JSON.stringify({
                            success: false,
                            error: `Unknown action '${action}'. Valid actions: ${valid}`,
                        }),
                    },
                ],
                isError: true,
            };
        }

        // Strip `action` from params before per-action validation
        const { action: _actionField, ...actionParams } = rawParams; // eslint-disable-line @typescript-eslint/no-unused-vars

        // Validate per-action params via strict Zod sub-schema
        const parsed = def.schema.safeParse(actionParams);
        if (!parsed.success) {
            const issues = parsed.error.issues
                .map((i) => `${i.path.join(".")}: ${i.message}`)
                .join("; ");
            return {
                content: [
                    {
                        type: "text" as const,
                        text: JSON.stringify({
                            success: false,
                            error: `Invalid parameters for action '${action}': ${issues}`,
                            details: parsed.error.issues,
                        }),
                    },
                ],
                isError: true,
            };
        }

        // Call handler with validated params
        try {
            return await def.handler(parsed.data, extra);
        } catch (err) {
            const message =
                err instanceof Error ? err.message : "Unknown error";
            return {
                content: [
                    {
                        type: "text" as const,
                        text: JSON.stringify({
                            success: false,
                            error: `Action '${action}' failed: ${message}`,
                        }),
                    },
                ],
                isError: true,
            };
        }
    }

    /**
     * Get all registered action names (sorted).
     */
    getActions(): string[] {
        return Object.keys(this.actions).sort();
    }
}
