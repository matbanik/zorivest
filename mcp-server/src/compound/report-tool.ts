/**
 * zorivest_report — Compound tool for post-trade review reports.
 *
 * Absorbs 2 individual tools from analytics-tools.ts:
 *   create_report       → action: "create"
 *   get_report_for_trade → action: "get"
 *
 * Source: implementation-plan.md MC2
 * Phase: P2.5f (MCP Tool Consolidation)
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import { fetchApi } from "../utils/api-client.js";
import { CompoundToolRouter, type ToolResult } from "./router.js";
import type { RegisteredToolHandle } from "../toolsets/registry.js";

// ── Router definition ──────────────────────────────────────────────────

const reportRouter = new CompoundToolRouter({
    // ── create ────────────────────────────────────────────────────────
    create: {
        schema: z.object({
            trade_id: z.string(),
            setup_quality: z.enum(["A", "B", "C", "D", "F"]),
            execution_quality: z.enum(["A", "B", "C", "D", "F"]),
            followed_plan: z.boolean(),
            emotional_state: z
                .enum(["calm", "anxious", "fearful", "greedy", "frustrated", "confident", "neutral"])
                .default("neutral"),
            lessons_learned: z.string().optional(),
            tags: z.array(z.string()).default([]),
        }).strict(),
        handler: async (params): Promise<ToolResult> => {
            const result = await fetchApi(
                `/trades/${params.trade_id}/report`,
                {
                    method: "POST",
                    body: JSON.stringify(params),
                    headers: { "Content-Type": "application/json" },
                },
            );
            return {
                content: [{ type: "text" as const, text: JSON.stringify(result) }],
            };
        },
    },

    // ── get ─────────────────────────────────────────────────────────
    get: {
        schema: z.object({
            trade_id: z.string(),
        }).strict(),
        handler: async (params): Promise<ToolResult> => {
            const result = await fetchApi(`/trades/${params.trade_id}/report`);
            return {
                content: [{ type: "text" as const, text: JSON.stringify(result) }],
            };
        },
    },
});

// ── Registration ───────────────────────────────────────────────────────

const REPORT_ACTIONS = ["create", "get"] as const;

export function registerReportTool(server: McpServer): RegisteredToolHandle[] {
    return [
        server.registerTool(
            "zorivest_report",
            {
                description:
                    "Post-trade review reports — create and retrieve trade reports with " +
                    "setup/execution grades, emotional state tracking, and lessons learned. " +
                    `Actions: ${REPORT_ACTIONS.join(", ")}`,
                inputSchema: z.object({
                    action: z.enum(REPORT_ACTIONS).describe("Report action to perform"),
                    // Per-action optional fields — validated strictly by router
                    trade_id: z.string().optional(),
                    setup_quality: z.enum(["A", "B", "C", "D", "F"]).optional(),
                    execution_quality: z.enum(["A", "B", "C", "D", "F"]).optional(),
                    followed_plan: z.boolean().optional(),
                    emotional_state: z
                        .enum(["calm", "anxious", "fearful", "greedy", "frustrated", "confident", "neutral"])
                        .optional(),
                    lessons_learned: z.string().optional(),
                    tags: z.array(z.string()).optional(),
                }).strict(),
                annotations: {
                    readOnlyHint: false,
                    destructiveHint: false,
                    idempotentHint: false,
                    openWorldHint: false,
                },
            },
            async (params) => {
                return reportRouter.dispatch(
                    params.action,
                    params as unknown as Record<string, unknown>,
                );
            },
        ),
    ];
}
