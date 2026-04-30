/**
 * Trade planning MCP tools.
 *
 * Source: 05d-mcp-trade-planning.md
 * Registers: create_trade_plan, list_trade_plans, delete_trade_plan
 *
 * Uses registerTool() for annotation metadata support.
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import { fetchApi } from "../utils/api-client.js";
import { withMetrics } from "../middleware/metrics.js";
import { withGuard } from "../middleware/mcp-guard.js";
import { withConfirmation } from "../middleware/confirmation.js";
import type { RegisteredToolHandle } from "../toolsets/registry.js";

/**
 * Register trade planning MCP tools on the server.
 */
export function registerPlanningTools(server: McpServer): RegisteredToolHandle[] {
    const handles: RegisteredToolHandle[] = [];
    // ── create_trade_plan ─────────────────────────────────────────────
    // Spec: 05d L51-84, L87-93
    handles.push(server.registerTool(
        "create_trade_plan",
        {
            description:
                "Create a forward-looking trade plan from agent research. Records the thesis, entry/stop/target levels, and strategy rationale before execution.",
            inputSchema: {
                ticker: z.string().describe("Instrument symbol"),
                direction: z.enum(["long", "short"]),
                conviction: z
                    .enum(["high", "medium", "low"])
                    .default("medium"),
                strategy_name: z
                    .string()
                    .describe(
                        'Strategy label (e.g. "breakout", "mean_reversion")',
                    ),
                strategy_description: z
                    .string()
                    .optional()
                    .describe("Free-form thesis/rationale"),
                entry: z.number().describe("Planned entry price"),
                stop: z.number().describe("Planned stop-loss price"),
                target: z
                    .number()
                    .describe("Planned target/take-profit price"),
                conditions: z
                    .string()
                    .describe("Entry conditions that must be met"),
                timeframe: z
                    .string()
                    .describe(
                        'Expected hold period (e.g. "intraday", "2-5 days", "swing")',
                    ),
                account_id: z
                    .string()
                    .optional()
                    .describe("Target account for the plan"),
                shares_planned: z
                    .number()
                    .int()
                    .optional()
                    .describe("Number of shares/contracts planned"),
                position_size: z
                    .number()
                    .optional()
                    .describe("Total dollar value of position (shares × entry_price)"),
            },
            // AC-2: annotations per spec 05d L87-93
            annotations: {
                readOnlyHint: false,
                destructiveHint: false,
                idempotentHint: false,
                openWorldHint: false,
            },
            // AC-3: toolset metadata
            _meta: {
                toolset: "trade-planning",
                alwaysLoaded: false,
            },
        },
        // AC-6: withMetrics wrapping withGuard
        withMetrics(
            "create_trade_plan",
            withGuard(async (params: {
                ticker: string;
                direction: "long" | "short";
                conviction: "high" | "medium" | "low";
                strategy_name: string;
                strategy_description?: string;
                entry: number;
                stop: number;
                target: number;
                conditions: string;
                timeframe: string;
                account_id?: string;
                shares_planned?: number;
                position_size?: number;
            }, _extra: unknown) => {
                const body = {
                    ticker: params.ticker,
                    direction: params.direction,
                    conviction: params.conviction,
                    strategy_name: params.strategy_name,
                    strategy_description: params.strategy_description,
                    entry: params.entry,
                    stop: params.stop,
                    target: params.target,
                    conditions: params.conditions,
                    timeframe: params.timeframe,
                    account_id: params.account_id,
                    shares_planned: params.shares_planned,
                    position_size: params.position_size,
                };

                // AC-4: POST to /trade-plans with JSON body
                const result = await fetchApi("/trade-plans", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(body),
                });

                return {
                    content: [
                        {
                            type: "text" as const,
                            text: JSON.stringify(result),
                        },
                    ],
                };
            }),
        ),
    ));

    // MC3: watchlist tools removed — absorbed into zorivest_watchlist compound tool
    // (create_watchlist, list_watchlists, get_watchlist, add_to_watchlist, remove_from_watchlist)

    // ── list_trade_plans ──────────────────────────────────────────────

    // TA4 AC-8/AC-9: List trade plans with pagination
    handles.push(server.registerTool(
        "list_trade_plans",
        {
            description:
                "List all trade plans with optional pagination. Returns plan details including ticker, direction, status, and entry/stop/target levels.",
            inputSchema: {
                limit: z
                    .number()
                    .int()
                    .min(1)
                    .max(1000)
                    .default(100)
                    .describe("Max results (1-1000, default 100)"),
                offset: z
                    .number()
                    .int()
                    .min(0)
                    .default(0)
                    .describe("Pagination offset"),
            },
            annotations: {
                readOnlyHint: true,
                destructiveHint: false,
                idempotentHint: true,
                openWorldHint: false,
            },
            _meta: {
                toolset: "trade-planning",
                alwaysLoaded: false,
            },
        },
        withMetrics(
            "list_trade_plans",
            withGuard(async (params: {
                limit: number;
                offset: number;
            }, _extra: unknown) => {
                const result = await fetchApi(
                    `/trade-plans?limit=${params.limit}&offset=${params.offset}`,
                );

                return {
                    content: [
                        {
                            type: "text" as const,
                            text: JSON.stringify(result),
                        },
                    ],
                };
            }),
        ),
    ));

    // ── delete_trade_plan ─────────────────────────────────────────────
    // TA4 AC-10/AC-11: Delete trade plan with M3 confirmation gate
    handles.push(server.registerTool(
        "delete_trade_plan",
        {
            description:
                "Delete a trade plan by ID. Destructive operation requiring confirmation on static clients. Enables re-creation of plans for the same ticker.",
            inputSchema: {
                plan_id: z
                    .number()
                    .int()
                    .describe("Trade plan ID to delete"),
                confirmation_token: z
                    .string()
                    .optional()
                    .describe(
                        "Confirmation token from get_confirmation_token (required on static/annotation-unaware clients)",
                    ),
            },
            annotations: {
                readOnlyHint: false,
                destructiveHint: true,
                idempotentHint: true,
                openWorldHint: false,
            },
            _meta: {
                toolset: "trade-planning",
                alwaysLoaded: false,
            },
        },
        withMetrics(
            "delete_trade_plan",
            withGuard(withConfirmation(
                "delete_trade_plan",
                async (params: {
                    plan_id: number;
                }, _extra: unknown) => {
                    const result = await fetchApi(`/trade-plans/${params.plan_id}`, {
                        method: "DELETE",
                    });

                    return {
                        content: [
                            { type: "text" as const, text: JSON.stringify(result) },
                        ],
                    };
                },
            )),
        ),
    ));

    return handles;
}
