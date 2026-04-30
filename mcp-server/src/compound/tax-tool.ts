/**
 * zorivest_tax — Compound tool for tax-related operations (all 501 stubs).
 *
 * Absorbs 4 individual stub tools from tax-tools.ts:
 *   estimate_tax   → action: "estimate"
 *   find_wash_sales → action: "wash_sales"
 *   manage_lots    → action: "manage_lots"
 *   harvest_losses → action: "harvest"
 *
 * All actions return 501 Not Implemented.
 * Source: implementation-plan.md MC3
 * Phase: P2.5f (MCP Tool Consolidation)
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import { CompoundToolRouter, type ToolResult } from "./router.js";
import type { RegisteredToolHandle } from "../toolsets/registry.js";

// ── 501 response helper ────────────────────────────────────────────────

function notImplemented(): ToolResult {
    return {
        content: [{
            type: "text" as const,
            text: JSON.stringify({
                success: false,
                error: "501: Not Implemented — This tool is planned but not yet implemented.",
            }),
        }],
    };
}

// ── Router definition ──────────────────────────────────────────────────

const taxRouter = new CompoundToolRouter({
    estimate: {
        schema: z.object({
            account_id: z.string().optional(),
            period: z.string().default("ytd"),
        }).strict(),
        handler: async (): Promise<ToolResult> => notImplemented(),
    },
    wash_sales: {
        schema: z.object({
            account_id: z.string().optional(),
        }).strict(),
        handler: async (): Promise<ToolResult> => notImplemented(),
    },
    manage_lots: {
        schema: z.object({
            account_id: z.string().optional(),
        }).strict(),
        handler: async (): Promise<ToolResult> => notImplemented(),
    },
    harvest: {
        schema: z.object({
            account_id: z.string().optional(),
        }).strict(),
        handler: async (): Promise<ToolResult> => notImplemented(),
    },
});

// ── Registration ───────────────────────────────────────────────────────

const TAX_ACTIONS = ["estimate", "wash_sales", "manage_lots", "harvest"] as const;

export function registerTaxTool(server: McpServer): RegisteredToolHandle[] {
    return [
        server.registerTool(
            "zorivest_tax",
            {
                description:
                    "Tax operations — estimate liability, find wash sales, manage lots, " +
                    "identify harvesting opportunities. (All actions: 501 Not Implemented) " +
                    "\n\nWorkflow: estimate (tax liability for period) → wash_sales (detect wash sale violations) → " +
                    "manage_lots (view/reassign cost basis lots) → harvest (identify loss harvesting opportunities). " +
                    "\\n\\nReturns: { success: false, error: '501: Not Implemented' } for all actions. " +
                    "Errors: 501 Not Implemented for all actions. These tools are planned for a future build phase. " +
                    "Do not use in production workflows. " +
                    `Actions: ${TAX_ACTIONS.join(", ")}`,
                inputSchema: z.object({
                    action: z.enum(TAX_ACTIONS).describe("Tax action to perform"),
                    account_id: z.string().optional(),
                    period: z.string().optional(),
                }).strict(),
                annotations: {
                    readOnlyHint: true,
                    destructiveHint: false,
                    idempotentHint: true,
                    openWorldHint: false,
                },
            },
            async (params) => {
                return taxRouter.dispatch(
                    params.action,
                    params as unknown as Record<string, unknown>,
                );
            },
        ),
    ];
}
