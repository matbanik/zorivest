/**
 * zorivest_analytics — Compound tool for trade analytics and calculation.
 *
 * Absorbs 13 individual tools:
 *   calculator-tools.ts: calculate_position_size → action: "position_size"
 *   analytics-tools.ts:  get_round_trips         → action: "round_trips"
 *   analytics-tools.ts:  enrich_trade_excursion   → action: "excursion"
 *   analytics-tools.ts:  get_fee_breakdown        → action: "fee_breakdown"
 *   analytics-tools.ts:  score_execution_quality  → action: "execution_quality"
 *   analytics-tools.ts:  estimate_pfof_impact     → action: "pfof_impact"
 *   analytics-tools.ts:  get_expectancy_metrics   → action: "expectancy"
 *   analytics-tools.ts:  simulate_drawdown        → action: "drawdown"
 *   analytics-tools.ts:  get_strategy_breakdown   → action: "strategy_breakdown"
 *   analytics-tools.ts:  get_sqn                  → action: "sqn"
 *   analytics-tools.ts:  get_cost_of_free         → action: "cost_of_free"
 *   analytics-tools.ts:  ai_review_trade          → action: "ai_review"
 *   analytics-tools.ts:  detect_options_strategy   → action: "options_strategy"
 *
 * Source: implementation-plan.md MC2
 * Phase: P2.5f (MCP Tool Consolidation)
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import { fetchApi } from "../utils/api-client.js";
import { CompoundToolRouter, type ToolResult } from "./router.js";
import type { RegisteredToolHandle } from "../toolsets/registry.js";

// ── Helpers ────────────────────────────────────────────────────────────

function textResult(data: unknown): ToolResult {
    return {
        content: [{ type: "text" as const, text: JSON.stringify(data) }],
    };
}

function buildQs(params: URLSearchParams): string {
    const qs = params.toString();
    return qs ? `?${qs}` : "";
}

// ── Router definition ──────────────────────────────────────────────────

const analyticsRouter = new CompoundToolRouter({
    // 1. position_size (from calculator-tools.ts)
    position_size: {
        schema: z.object({
            balance: z.number().positive(),
            risk_pct: z.number().positive().max(100),
            entry_price: z.number().positive(),
            stop_loss: z.number().positive(),
            target_price: z.number().positive(),
        }).strict(),
        handler: async (params): Promise<ToolResult> => {
            const result = await fetchApi("/calculator/position-size", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(params),
            });
            return textResult(result);
        },
    },

    // 2. round_trips
    round_trips: {
        schema: z.object({
            account_id: z.string().optional(),
            status: z.enum(["open", "closed", "all"]).default("all"),
        }).strict(),
        handler: async (params): Promise<ToolResult> => {
            const qs = new URLSearchParams();
            if (params.account_id) qs.set("account_id", params.account_id);
            if (params.status && params.status !== "all") qs.set("status", params.status);
            return textResult(await fetchApi(`/round-trips${buildQs(qs)}`));
        },
    },

    // 3. excursion
    excursion: {
        schema: z.object({
            trade_exec_id: z.string(),
        }).strict(),
        handler: async (params): Promise<ToolResult> => {
            return textResult(await fetchApi(
                `/analytics/excursion/${params.trade_exec_id}`,
                { method: "POST" },
            ));
        },
    },

    // 4. fee_breakdown
    fee_breakdown: {
        schema: z.object({
            account_id: z.string().optional(),
            period: z.string().default("ytd"),
        }).strict(),
        handler: async (params): Promise<ToolResult> => {
            const qs = new URLSearchParams();
            if (params.account_id) qs.set("account_id", params.account_id);
            if (params.period) qs.set("period", params.period);
            return textResult(await fetchApi(`/fees/summary${buildQs(qs)}`));
        },
    },

    // 5. execution_quality
    execution_quality: {
        schema: z.object({
            trade_exec_id: z.string(),
        }).strict(),
        handler: async (params): Promise<ToolResult> => {
            return textResult(await fetchApi(
                `/analytics/execution-quality?trade_id=${params.trade_exec_id}`,
            ));
        },
    },

    // 6. pfof_impact
    pfof_impact: {
        schema: z.object({
            account_id: z.string(),
            period: z.string().default("ytd"),
        }).strict(),
        handler: async (params): Promise<ToolResult> => {
            const qs = new URLSearchParams();
            qs.set("account_id", params.account_id);
            if (params.period) qs.set("period", params.period);
            return textResult(await fetchApi(`/analytics/pfof-report?${qs.toString()}`));
        },
    },

    // 7. expectancy
    expectancy: {
        schema: z.object({
            account_id: z.string().optional(),
            period: z.string().default("all"),
        }).strict(),
        handler: async (params): Promise<ToolResult> => {
            const qs = new URLSearchParams();
            if (params.account_id) qs.set("account_id", params.account_id);
            if (params.period) qs.set("period", params.period);
            return textResult(await fetchApi(`/analytics/expectancy?${qs.toString()}`));
        },
    },

    // 8. drawdown
    drawdown: {
        schema: z.object({
            account_id: z.string().optional(),
            simulations: z.number().int().min(100).max(100000).default(10000),
        }).strict(),
        handler: async (params): Promise<ToolResult> => {
            const qs = new URLSearchParams();
            if (params.account_id) qs.set("account_id", params.account_id);
            qs.set("simulations", String(params.simulations));
            return textResult(await fetchApi(`/analytics/drawdown?${qs.toString()}`));
        },
    },

    // 9. strategy_breakdown
    strategy_breakdown: {
        schema: z.object({
            account_id: z.string().optional(),
        }).strict(),
        handler: async (params): Promise<ToolResult> => {
            const qs = new URLSearchParams();
            if (params.account_id) qs.set("account_id", params.account_id);
            return textResult(await fetchApi(`/analytics/strategy-breakdown${buildQs(qs)}`));
        },
    },

    // 10. sqn
    sqn: {
        schema: z.object({
            account_id: z.string().optional(),
            period: z.string().default("all"),
        }).strict(),
        handler: async (params): Promise<ToolResult> => {
            const qs = new URLSearchParams();
            if (params.account_id) qs.set("account_id", params.account_id);
            if (params.period) qs.set("period", params.period);
            return textResult(await fetchApi(`/analytics/sqn?${qs.toString()}`));
        },
    },

    // 11. cost_of_free
    cost_of_free: {
        schema: z.object({
            account_id: z.string().optional(),
            period: z.string().default("ytd"),
        }).strict(),
        handler: async (params): Promise<ToolResult> => {
            const qs = new URLSearchParams();
            if (params.account_id) qs.set("account_id", params.account_id);
            if (params.period) qs.set("period", params.period);
            return textResult(await fetchApi(`/analytics/cost-of-free${buildQs(qs)}`));
        },
    },

    // 12. ai_review
    ai_review: {
        schema: z.object({
            trade_exec_id: z.string(),
            review_type: z.enum(["single", "weekly"]).default("single"),
            budget_cap: z.number().optional(),
        }).strict(),
        handler: async (params): Promise<ToolResult> => {
            return textResult(await fetchApi("/analytics/ai-review", {
                method: "POST",
                body: JSON.stringify(params),
                headers: { "Content-Type": "application/json" },
            }));
        },
    },

    // 13. options_strategy
    options_strategy: {
        schema: z.object({
            leg_exec_ids: z.array(z.string()).min(2),
        }).strict(),
        handler: async (params): Promise<ToolResult> => {
            return textResult(await fetchApi("/analytics/options-strategy", {
                method: "POST",
                body: JSON.stringify({ leg_exec_ids: params.leg_exec_ids }),
                headers: { "Content-Type": "application/json" },
            }));
        },
    },
});

// ── Registration ───────────────────────────────────────────────────────

const ANALYTICS_ACTIONS = [
    "position_size", "round_trips", "excursion", "fee_breakdown",
    "execution_quality", "pfof_impact", "expectancy", "drawdown",
    "strategy_breakdown", "sqn", "cost_of_free", "ai_review", "options_strategy",
] as const;

export function registerAnalyticsTool(server: McpServer): RegisteredToolHandle[] {
    return [
        server.registerTool(
            "zorivest_analytics",
            {
                description:
                    "Trade analytics — position sizing, round trips, excursion analysis, fee breakdown, " +
                    "execution quality, PFOF impact, expectancy, drawdown simulation, strategy breakdown, " +
                    "SQN, cost of free, AI trade review, options strategy detection. " +
                    `Actions: ${ANALYTICS_ACTIONS.join(", ")}`,
                inputSchema: z.object({
                    action: z.enum(ANALYTICS_ACTIONS).describe("Analytics action to perform"),
                    // Per-action optional fields — validated strictly by router
                    balance: z.number().optional(),
                    risk_pct: z.number().optional(),
                    entry_price: z.number().optional(),
                    stop_loss: z.number().optional(),
                    target_price: z.number().optional(),
                    account_id: z.string().optional(),
                    status: z.enum(["open", "closed", "all"]).optional(),
                    trade_exec_id: z.string().optional(),
                    period: z.string().optional(),
                    simulations: z.number().optional(),
                    review_type: z.enum(["single", "weekly"]).optional(),
                    budget_cap: z.number().optional(),
                    leg_exec_ids: z.array(z.string()).optional(),
                }).strict(),
                annotations: {
                    readOnlyHint: true,
                    destructiveHint: false,
                    idempotentHint: true,
                    openWorldHint: false,
                },
            },
            async (params) => {
                return analyticsRouter.dispatch(
                    params.action,
                    params as unknown as Record<string, unknown>,
                );
            },
        ),
    ];
}
