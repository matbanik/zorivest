/**
 * zorivest_plan — Compound tool for trade plan management.
 *
 * Absorbs 3 individual tools from planning-tools.ts:
 *   create_trade_plan → action: "create"
 *   list_trade_plans  → action: "list"
 *   delete_trade_plan → action: "delete" (destructive, confirmation)
 *
 * Source: implementation-plan.md MC4
 * Phase: P2.5f (MCP Tool Consolidation)
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import { fetchApi } from "../utils/api-client.js";
import { withConfirmation } from "../middleware/confirmation.js";
import { CompoundToolRouter, type ToolResult } from "./router.js";
import type { RegisteredToolHandle } from "../toolsets/registry.js";

// ── Helper ─────────────────────────────────────────────────────────────

function textResult(data: unknown): ToolResult {
    return {
        content: [{ type: "text" as const, text: JSON.stringify(data) }],
    };
}

// ── Router definition ──────────────────────────────────────────────────

const planRouter = new CompoundToolRouter({
    // ── create ────────────────────────────────────────────────────────
    create: {
        schema: z.object({
            ticker: z.string(),
            direction: z.enum(["long", "short"]),
            conviction: z.enum(["low", "medium", "high"]).default("medium"),
            strategy_name: z.string(),
            strategy_description: z.string().optional(),
            entry: z.number(),
            stop: z.number(),
            target: z.number(),
            conditions: z.string(),
            timeframe: z.string(),
            account_id: z.string().optional(),
        }).strict(),
        handler: async (params): Promise<ToolResult> => {
            const body = {
                ticker: params.ticker,
                direction: params.direction,
                conviction: params.conviction,
                strategy_name: params.strategy_name,
                strategy_description: params.strategy_description ?? "",
                entry: params.entry,
                stop: params.stop,
                target: params.target,
                conditions: params.conditions,
                timeframe: params.timeframe,
                account_id: params.account_id,
            };
            return textResult(await fetchApi("/trade-plans", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(body),
            }));
        },
    },

    // ── list ──────────────────────────────────────────────────────────
    list: {
        schema: z.object({
            limit: z.number().int().min(1).max(1000).default(100),
            offset: z.number().int().min(0).default(0),
        }).strict(),
        handler: async (params): Promise<ToolResult> => {
            return textResult(await fetchApi(
                `/trade-plans?limit=${params.limit}&offset=${params.offset}`,
            ));
        },
    },

    // ── delete (destructive + confirmation) ───────────────────────────
    delete: {
        schema: z.object({
            plan_id: z.number().int(),
            confirmation_token: z.string().optional(),
        }).strict(),
        handler: async (params): Promise<ToolResult> => {
            const handler = withConfirmation(
                "delete_trade_plan",
                async (p: typeof params, _extra: unknown) => {
                    return textResult(await fetchApi(`/trade-plans/${p.plan_id}`, {
                        method: "DELETE",
                    }));
                },
            );
            return handler(params, {}) as Promise<ToolResult>;
        },
    },
});

// ── Registration ───────────────────────────────────────────────────────

const PLAN_ACTIONS = ["create", "list", "delete"] as const;

export function registerPlanTool(server: McpServer): RegisteredToolHandle[] {
    return [
        server.registerTool(
            "zorivest_plan",
            {
                description:
                    "Trade plan management — create structured plans, list with pagination, " +
                    "delete plans. " +
                    "\\n\\nWorkflow: Use zorivest_analytics(action:\"position_size\") to calculate position → create plan with entry/stop/target levels. " +
                    "Plans capture strategy thesis (name, description), risk levels (entry, stop, target), " +
                    "conviction (low/medium/high), conditions, and timeframe. " +
                    "\\n\\nConfirmation: 'delete' requires a confirmation_token from zorivest_system(action:\"confirm_token\"). " +
                    "Returns: JSON with { success, data }. " +
                    "Errors: 404 if plan_id not found, 422 if required fields missing. " +
                    `Actions: ${PLAN_ACTIONS.join(", ")}`,
                inputSchema: z.object({
                    action: z.enum(PLAN_ACTIONS).describe("Plan action to perform"),
                    // Per-action optional fields — validated strictly by router
                    ticker: z.string().optional(),
                    direction: z.enum(["long", "short"]).optional(),
                    conviction: z.enum(["low", "medium", "high"]).optional(),
                    strategy_name: z.string().optional(),
                    strategy_description: z.string().optional(),
                    entry: z.number().optional(),
                    stop: z.number().optional(),
                    target: z.number().optional(),
                    conditions: z.string().optional(),
                    timeframe: z.string().optional(),
                    account_id: z.string().optional(),
                    limit: z.number().optional(),
                    offset: z.number().optional(),
                    plan_id: z.number().optional(),
                    confirmation_token: z.string().optional(),
                }).strict(),
                annotations: {
                    readOnlyHint: false,
                    destructiveHint: true,
                    idempotentHint: false,
                    openWorldHint: false,
                },
            },
            async (params) => {
                return planRouter.dispatch(
                    params.action,
                    params as unknown as Record<string, unknown>,
                );
            },
        ),
    ];
}
