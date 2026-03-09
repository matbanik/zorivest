/**
 * MCP tools — Trade Analytics
 *
 * Implements 12 analytics tools, all proxying to existing REST API endpoints.
 * All tools use `fetchApi()` for consistent envelope handling.
 *
 * Source: 05c-mcp-trade-analytics.md §Analytics Tools
 * MEU: 35 (mcp-trade-analytics)
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import { fetchApi } from "../utils/api-client.js";

// ── Shared annotations ─────────────────────────────────────────────────

const ANALYTICS_META = {
    toolset: "trade-analytics",
    alwaysLoaded: false,
};

const READ_ONLY_ANNOTATIONS = {
    readOnlyHint: true,
    destructiveHint: false,
    idempotentHint: true,
    openWorldHint: false,
};

// ── Tool registration ──────────────────────────────────────────────────

export function registerAnalyticsTools(server: McpServer): void {
    // 1. get_round_trips → GET /round-trips
    server.registerTool(
        "get_round_trips",
        {
            description: "List round-trips (entry→exit pairs) for an account",
            inputSchema: {
                account_id: z.string().optional().describe("Filter by account"),
                status: z
                    .enum(["open", "closed", "all"])
                    .default("all")
                    .describe("Filter by status"),
            },
            annotations: READ_ONLY_ANNOTATIONS,
            _meta: ANALYTICS_META,
        },
        async (args) => {
            const params = new URLSearchParams();
            if (args.account_id) params.set("account_id", args.account_id);
            if (args.status && args.status !== "all")
                params.set("status", args.status);
            const qs = params.toString();
            const result = await fetchApi(
                `/round-trips${qs ? `?${qs}` : ""}`,
            );
            return {
                content: [
                    { type: "text" as const, text: JSON.stringify(result) },
                ],
            };
        },
    );

    // 2. enrich_trade_excursion → POST /analytics/excursion/{id}
    server.registerTool(
        "enrich_trade_excursion",
        {
            description:
                "Calculate MFE/MAE/BSO metrics for a trade using historical bar data",
            inputSchema: {
                trade_exec_id: z.string().describe("Trade execution ID"),
            },
            annotations: {
                readOnlyHint: false,
                destructiveHint: false,
                idempotentHint: true,
                openWorldHint: false,
            },
            _meta: ANALYTICS_META,
        },
        async ({ trade_exec_id }) => {
            const result = await fetchApi(
                `/analytics/excursion/${trade_exec_id}`,
                { method: "POST" },
            );
            return {
                content: [
                    { type: "text" as const, text: JSON.stringify(result) },
                ],
            };
        },
    );

    // 3. get_fee_breakdown → GET /fees/summary
    server.registerTool(
        "get_fee_breakdown",
        {
            description:
                "Decompose trade fees by type (commission, exchange, regulatory, ECN)",
            inputSchema: {
                account_id: z.string().optional().describe("Filter by account"),
                period: z.string().default("ytd").describe("Time period"),
            },
            annotations: READ_ONLY_ANNOTATIONS,
            _meta: ANALYTICS_META,
        },
        async (args) => {
            const params = new URLSearchParams();
            if (args.account_id) params.set("account_id", args.account_id);
            if (args.period) params.set("period", args.period);
            const qs = params.toString();
            const result = await fetchApi(
                `/fees/summary${qs ? `?${qs}` : ""}`,
            );
            return {
                content: [
                    { type: "text" as const, text: JSON.stringify(result) },
                ],
            };
        },
    );

    // 4. score_execution_quality → GET /analytics/execution-quality
    server.registerTool(
        "score_execution_quality",
        {
            description:
                "Grade trade execution quality vs NBBO. Gated on NBBO data availability.",
            inputSchema: {
                trade_exec_id: z.string().describe("Trade execution ID"),
            },
            annotations: READ_ONLY_ANNOTATIONS,
            _meta: ANALYTICS_META,
        },
        async ({ trade_exec_id }) => {
            const result = await fetchApi(
                `/analytics/execution-quality?trade_id=${trade_exec_id}`,
            );
            return {
                content: [
                    { type: "text" as const, text: JSON.stringify(result) },
                ],
            };
        },
    );

    // 5. estimate_pfof_impact → GET /analytics/pfof-report
    server.registerTool(
        "estimate_pfof_impact",
        {
            description:
                "Estimate PFOF cost impact. Labeled as ESTIMATE — not auditable.",
            inputSchema: {
                account_id: z.string().describe("Account ID"),
                period: z.string().default("ytd").describe("Time period"),
            },
            annotations: READ_ONLY_ANNOTATIONS,
            _meta: ANALYTICS_META,
        },
        async (args) => {
            const params = new URLSearchParams();
            params.set("account_id", args.account_id);
            if (args.period) params.set("period", args.period);
            const result = await fetchApi(
                `/analytics/pfof-report?${params.toString()}`,
            );
            return {
                content: [
                    { type: "text" as const, text: JSON.stringify(result) },
                ],
            };
        },
    );

    // 6. get_expectancy_metrics → GET /analytics/expectancy
    server.registerTool(
        "get_expectancy_metrics",
        {
            description:
                "Win rate, avg win/loss, expectancy per trade, Kelly %, edge metrics",
            inputSchema: {
                account_id: z.string().optional().describe("Filter by account"),
                period: z.string().default("all").describe("Time period"),
            },
            annotations: READ_ONLY_ANNOTATIONS,
            _meta: ANALYTICS_META,
        },
        async (args) => {
            const params = new URLSearchParams();
            if (args.account_id) params.set("account_id", args.account_id);
            if (args.period) params.set("period", args.period);
            const result = await fetchApi(
                `/analytics/expectancy?${params.toString()}`,
            );
            return {
                content: [
                    { type: "text" as const, text: JSON.stringify(result) },
                ],
            };
        },
    );

    // 7. simulate_drawdown → GET /analytics/drawdown
    server.registerTool(
        "simulate_drawdown",
        {
            description:
                "Monte Carlo drawdown probability table with recommended risk %",
            inputSchema: {
                account_id: z.string().optional().describe("Filter by account"),
                simulations: z
                    .number()
                    .int()
                    .min(100)
                    .max(100000)
                    .default(10000)
                    .describe("Number of simulations"),
            },
            annotations: READ_ONLY_ANNOTATIONS,
            _meta: ANALYTICS_META,
        },
        async (args) => {
            const params = new URLSearchParams();
            if (args.account_id) params.set("account_id", args.account_id);
            params.set("simulations", String(args.simulations));
            const result = await fetchApi(
                `/analytics/drawdown?${params.toString()}`,
            );
            return {
                content: [
                    { type: "text" as const, text: JSON.stringify(result) },
                ],
            };
        },
    );

    // 8. get_strategy_breakdown → GET /analytics/strategy-breakdown
    server.registerTool(
        "get_strategy_breakdown",
        {
            description: "P&L breakdown by strategy name from TradeReport tags",
            inputSchema: {
                account_id: z.string().optional().describe("Filter by account"),
            },
            annotations: READ_ONLY_ANNOTATIONS,
            _meta: ANALYTICS_META,
        },
        async (args) => {
            const params = new URLSearchParams();
            if (args.account_id) params.set("account_id", args.account_id);
            const qs = params.toString();
            const result = await fetchApi(
                `/analytics/strategy-breakdown${qs ? `?${qs}` : ""}`,
            );
            return {
                content: [
                    { type: "text" as const, text: JSON.stringify(result) },
                ],
            };
        },
    );

    // 9. get_sqn → GET /analytics/sqn
    server.registerTool(
        "get_sqn",
        {
            description:
                "System Quality Number (SQN) — Van Tharp metric with grade classification",
            inputSchema: {
                account_id: z.string().optional().describe("Filter by account"),
                period: z.string().default("all").describe("Time period"),
            },
            annotations: READ_ONLY_ANNOTATIONS,
            _meta: ANALYTICS_META,
        },
        async (args) => {
            const params = new URLSearchParams();
            if (args.account_id) params.set("account_id", args.account_id);
            if (args.period) params.set("period", args.period);
            const result = await fetchApi(
                `/analytics/sqn?${params.toString()}`,
            );
            return {
                content: [
                    { type: "text" as const, text: JSON.stringify(result) },
                ],
            };
        },
    );

    // 10. get_cost_of_free → GET /analytics/cost-of-free
    server.registerTool(
        "get_cost_of_free",
        {
            description:
                '"Cost of Free" report — hidden costs of PFOF routing + fee impact',
            inputSchema: {
                account_id: z.string().optional().describe("Filter by account"),
                period: z.string().default("ytd").describe("Time period"),
            },
            annotations: READ_ONLY_ANNOTATIONS,
            _meta: ANALYTICS_META,
        },
        async (args) => {
            const params = new URLSearchParams();
            if (args.account_id) params.set("account_id", args.account_id);
            if (args.period) params.set("period", args.period);
            const qs = params.toString();
            const result = await fetchApi(
                `/analytics/cost-of-free${qs ? `?${qs}` : ""}`,
            );
            return {
                content: [
                    { type: "text" as const, text: JSON.stringify(result) },
                ],
            };
        },
    );

    // 11. ai_review_trade → POST /analytics/ai-review
    server.registerTool(
        "ai_review_trade",
        {
            description:
                "Multi-persona AI trade review. Opt-in with budget cap. Personas: Risk Manager, Trend Analyst, Contrarian.",
            inputSchema: {
                trade_exec_id: z.string().describe("Trade execution ID"),
                review_type: z
                    .enum(["single", "weekly"])
                    .default("single")
                    .describe("Review scope"),
                budget_cap: z
                    .number()
                    .optional()
                    .describe("Max spend in cents"),
            },
            annotations: READ_ONLY_ANNOTATIONS,
            _meta: ANALYTICS_META,
        },
        async (args) => {
            const result = await fetchApi("/analytics/ai-review", {
                method: "POST",
                body: JSON.stringify(args),
                headers: { "Content-Type": "application/json" },
            });
            return {
                content: [
                    { type: "text" as const, text: JSON.stringify(result) },
                ],
            };
        },
    );

    // 12. detect_options_strategy → POST /analytics/options-strategy
    server.registerTool(
        "detect_options_strategy",
        {
            description:
                "Auto-detect multi-leg options strategy type from execution IDs",
            inputSchema: {
                leg_exec_ids: z
                    .array(z.string())
                    .min(2)
                    .describe("Execution IDs of option legs"),
            },
            annotations: READ_ONLY_ANNOTATIONS,
            _meta: ANALYTICS_META,
        },
        async ({ leg_exec_ids }) => {
            const result = await fetchApi("/analytics/options-strategy", {
                method: "POST",
                body: JSON.stringify({ leg_exec_ids }),
                headers: { "Content-Type": "application/json" },
            });
            return {
                content: [
                    { type: "text" as const, text: JSON.stringify(result) },
                ],
            };
        },
    );
}
