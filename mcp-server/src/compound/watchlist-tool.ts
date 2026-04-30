/**
 * zorivest_watchlist — Compound tool for watchlist operations.
 *
 * Absorbs 5 individual tools from planning-tools.ts:
 *   create_watchlist     → action: "create"
 *   list_watchlists      → action: "list"
 *   get_watchlist         → action: "get"
 *   add_to_watchlist      → action: "add_ticker"
 *   remove_from_watchlist → action: "remove_ticker"
 *
 * Source: implementation-plan.md MC3
 * Phase: P2.5f (MCP Tool Consolidation)
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import { fetchApi } from "../utils/api-client.js";
import { CompoundToolRouter, type ToolResult } from "./router.js";
import type { RegisteredToolHandle } from "../toolsets/registry.js";

// ── Helper ─────────────────────────────────────────────────────────────

function textResult(data: unknown): ToolResult {
    return {
        content: [{ type: "text" as const, text: JSON.stringify(data) }],
    };
}

// ── Router definition ──────────────────────────────────────────────────

const watchlistRouter = new CompoundToolRouter({
    create: {
        schema: z.object({
            name: z.string(),
            description: z.string().optional(),
        }).strict(),
        handler: async (params): Promise<ToolResult> => {
            return textResult(await fetchApi("/watchlists/", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    name: params.name,
                    description: params.description ?? "",
                }),
            }));
        },
    },

    list: {
        schema: z.object({
            limit: z.number().default(100),
            offset: z.number().default(0),
        }).strict(),
        handler: async (params): Promise<ToolResult> => {
            return textResult(await fetchApi(
                `/watchlists/?limit=${params.limit}&offset=${params.offset}`,
            ));
        },
    },

    get: {
        schema: z.object({
            watchlist_id: z.number(),
        }).strict(),
        handler: async (params): Promise<ToolResult> => {
            return textResult(await fetchApi(`/watchlists/${params.watchlist_id}`));
        },
    },

    add_ticker: {
        schema: z.object({
            watchlist_id: z.number(),
            ticker: z.string(),
            notes: z.string().optional(),
        }).strict(),
        handler: async (params): Promise<ToolResult> => {
            return textResult(await fetchApi(
                `/watchlists/${params.watchlist_id}/items`,
                {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        ticker: params.ticker,
                        notes: params.notes ?? "",
                    }),
                },
            ));
        },
    },

    remove_ticker: {
        schema: z.object({
            watchlist_id: z.number(),
            ticker: z.string(),
        }).strict(),
        handler: async (params): Promise<ToolResult> => {
            return textResult(await fetchApi(
                `/watchlists/${params.watchlist_id}/items/${params.ticker}`,
                { method: "DELETE" },
            ));
        },
    },
});

// ── Registration ───────────────────────────────────────────────────────

const WATCHLIST_ACTIONS = [
    "create", "list", "get", "add_ticker", "remove_ticker",
] as const;

export function registerWatchlistTool(server: McpServer): RegisteredToolHandle[] {
    return [
        server.registerTool(
            "zorivest_watchlist",
            {
                description:
                    "Watchlist management — create, list, get, add/remove tickers. " +
                    "\\n\\nWorkflow: create (name a new watchlist) → add_ticker (add symbols with optional notes) → get (view full watchlist with tickers). " +
                    "Use zorivest_market(action:\"search\") to find valid tickers before adding. " +
                    "\\n\\nReturns: JSON with { success, data }. get returns watchlist details including all ticker items. " +
                    "Errors: 404 if watchlist_id not found, 409 if ticker already in watchlist. " +
                    `Actions: ${WATCHLIST_ACTIONS.join(", ")}`,
                inputSchema: z.object({
                    action: z.enum(WATCHLIST_ACTIONS).describe("Watchlist action to perform"),
                    name: z.string().optional(),
                    description: z.string().optional(),
                    limit: z.number().optional(),
                    offset: z.number().optional(),
                    watchlist_id: z.number().optional(),
                    ticker: z.string().optional(),
                    notes: z.string().optional(),
                }).strict(),
                annotations: {
                    readOnlyHint: false,
                    destructiveHint: false,
                    idempotentHint: false,
                    openWorldHint: false,
                },
            },
            async (params) => {
                return watchlistRouter.dispatch(
                    params.action,
                    params as unknown as Record<string, unknown>,
                );
            },
        ),
    ];
}
