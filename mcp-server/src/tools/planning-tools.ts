/**
 * Trade planning MCP tools.
 *
 * Source: 05d-mcp-trade-planning.md
 * Registers: create_trade_plan
 *
 * Uses registerTool() for annotation metadata support.
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import { fetchApi } from "../utils/api-client.js";
import { withMetrics } from "../middleware/metrics.js";
import { withGuard } from "../middleware/mcp-guard.js";

/**
 * Register trade planning MCP tools on the server.
 */
export function registerPlanningTools(server: McpServer): void {
    // ── create_trade_plan ─────────────────────────────────────────────
    // Spec: 05d L51-84, L87-93
    server.registerTool(
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
    );
}
