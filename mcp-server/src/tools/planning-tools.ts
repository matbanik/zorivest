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
    ));

    // ── create_watchlist ──────────────────────────────────────────────
    // MEU-69 AC-1: Create a named watchlist
    handles.push(server.registerTool(
        "create_watchlist",
        {
            description:
                "Create a named watchlist for forward-looking research. Group tickers by theme (e.g. 'Momentum Plays', 'Earnings Watch').",
            inputSchema: {
                name: z.string().describe("Watchlist name (must be unique)"),
                description: z
                    .string()
                    .optional()
                    .describe("Optional description of the watchlist theme"),
            },
            annotations: {
                readOnlyHint: false,
                destructiveHint: false,
                idempotentHint: false,
                openWorldHint: false,
            },
            _meta: {
                toolset: "trade-planning",
                alwaysLoaded: false,
            },
        },
        withMetrics(
            "create_watchlist",
            withGuard(async (params: {
                name: string;
                description?: string;
            }, _extra: unknown) => {
                const body = {
                    name: params.name,
                    description: params.description ?? "",
                };

                const result = await fetchApi("/watchlists/", {
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

    // ── list_watchlists ──────────────────────────────────────────────
    // MEU-69 AC-1: List all watchlists with pagination
    handles.push(server.registerTool(
        "list_watchlists",
        {
            description:
                "List all watchlists with pagination. Returns name, description, and item count for each.",
            inputSchema: {
                limit: z
                    .number()
                    .default(100)
                    .describe("Max results (1-1000)"),
                offset: z
                    .number()
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
            "list_watchlists",
            withGuard(async (params: {
                limit: number;
                offset: number;
            }, _extra: unknown) => {
                const result = await fetchApi(
                    `/watchlists/?limit=${params.limit}&offset=${params.offset}`,
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

    // ── get_watchlist ────────────────────────────────────────────────
    // MEU-69 AC-1: Get a watchlist by ID with its items
    handles.push(server.registerTool(
        "get_watchlist",
        {
            description:
                "Get a watchlist by ID, including all ticker items with notes.",
            inputSchema: {
                watchlist_id: z
                    .number()
                    .describe("Watchlist ID to retrieve"),
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
            "get_watchlist",
            withGuard(async (params: {
                watchlist_id: number;
            }, _extra: unknown) => {
                const result = await fetchApi(
                    `/watchlists/${params.watchlist_id}`,
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

    // ── add_to_watchlist ─────────────────────────────────────────────
    // MEU-69 AC-1: Add a ticker to a watchlist
    handles.push(server.registerTool(
        "add_to_watchlist",
        {
            description:
                "Add a ticker symbol to a watchlist with optional research notes.",
            inputSchema: {
                watchlist_id: z
                    .number()
                    .describe("Target watchlist ID"),
                ticker: z
                    .string()
                    .describe("Ticker symbol to add (e.g. 'AAPL')"),
                notes: z
                    .string()
                    .optional()
                    .describe("Research notes for this ticker"),
            },
            annotations: {
                readOnlyHint: false,
                destructiveHint: false,
                idempotentHint: false,
                openWorldHint: false,
            },
            _meta: {
                toolset: "trade-planning",
                alwaysLoaded: false,
            },
        },
        withMetrics(
            "add_to_watchlist",
            withGuard(async (params: {
                watchlist_id: number;
                ticker: string;
                notes?: string;
            }, _extra: unknown) => {
                const body = {
                    ticker: params.ticker,
                    notes: params.notes ?? "",
                };

                const result = await fetchApi(
                    `/watchlists/${params.watchlist_id}/items`,
                    {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify(body),
                    },
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

    // ── remove_from_watchlist ────────────────────────────────────────
    // MEU-69 AC-1: Remove a ticker from a watchlist
    handles.push(server.registerTool(
        "remove_from_watchlist",
        {
            description:
                "Remove a ticker from a watchlist.",
            inputSchema: {
                watchlist_id: z
                    .number()
                    .describe("Source watchlist ID"),
                ticker: z
                    .string()
                    .describe("Ticker symbol to remove"),
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
            "remove_from_watchlist",
            withGuard(async (params: {
                watchlist_id: number;
                ticker: string;
            }, _extra: unknown) => {
                const result = await fetchApi(
                    `/watchlists/${params.watchlist_id}/items/${params.ticker}`,
                    { method: "DELETE" },
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

    return handles;
}
