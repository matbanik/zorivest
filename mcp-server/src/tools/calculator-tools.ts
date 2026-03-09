/**
 * Calculator MCP tools — position sizing and risk calculations.
 *
 * Source: 05d-mcp-trade-planning.md
 * API contract: packages/api/src/zorivest_api/routes/calculator.py
 * Uses registerTool() for annotation metadata support.
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import { fetchApi } from "../utils/api-client.js";

/**
 * Register calculator-related MCP tools on the server.
 */
export function registerCalculatorTools(server: McpServer): void {
    server.registerTool(
        "calculate_position_size",
        {
            description:
                "Calculate optimal position size based on account balance, risk percentage, entry/stop/target prices",
            inputSchema: {
                balance: z
                    .number()
                    .positive()
                    .describe(
                        "Current account balance in base currency",
                    ),
                risk_pct: z
                    .number()
                    .positive()
                    .max(100)
                    .describe(
                        "Maximum risk as percentage of account (e.g. 2 = 2%)",
                    ),
                entry_price: z
                    .number()
                    .positive()
                    .describe("Planned entry price per unit"),
                stop_loss: z
                    .number()
                    .positive()
                    .describe("Stop-loss price per unit"),
                target_price: z
                    .number()
                    .positive()
                    .describe("Target/take-profit price per unit"),
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
        async (params) => {
            const result = await fetchApi("/calculator/position-size", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    balance: params.balance,
                    risk_pct: params.risk_pct,
                    entry_price: params.entry_price,
                    stop_loss: params.stop_loss,
                    target_price: params.target_price,
                }),
            });

            return {
                content: [
                    { type: "text" as const, text: JSON.stringify(result) },
                ],
            };
        },
    );
}
