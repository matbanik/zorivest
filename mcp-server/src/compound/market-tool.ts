/**
 * zorivest_market — Compound tool for market data operations.
 *
 * Absorbs 7 individual tools from market-data-tools.ts:
 *   get_stock_quote         → action: "quote"
 *   get_market_news         → action: "news"
 *   search_ticker           → action: "search"
 *   get_sec_filings         → action: "filings"
 *   list_market_providers   → action: "providers"
 *   disconnect_market_provider → action: "disconnect"
 *   test_market_provider    → action: "test_provider"
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
        content: [{ type: "text" as const, text: JSON.stringify(data, null, 2) }],
    };
}

// ── Router definition ──────────────────────────────────────────────────

const marketRouter = new CompoundToolRouter({
    quote: {
        schema: z.object({
            ticker: z.string(),
        }).strict(),
        handler: async (params): Promise<ToolResult> => {
            return textResult(await fetchApi(
                `/market-data/quote?ticker=${encodeURIComponent(params.ticker)}`,
            ));
        },
    },

    news: {
        schema: z.object({
            ticker: z.string().optional(),
            count: z.number().int().min(1).max(50).default(5),
        }).strict(),
        handler: async (params): Promise<ToolResult> => {
            let query = `/market-data/news?count=${params.count}`;
            if (params.ticker) query += `&ticker=${encodeURIComponent(params.ticker)}`;
            return textResult(await fetchApi(query));
        },
    },

    search: {
        schema: z.object({
            query: z.string(),
        }).strict(),
        handler: async (params): Promise<ToolResult> => {
            return textResult(await fetchApi(
                `/market-data/search?query=${encodeURIComponent(params.query)}`,
            ));
        },
    },

    filings: {
        schema: z.object({
            ticker: z.string(),
        }).strict(),
        handler: async (params): Promise<ToolResult> => {
            return textResult(await fetchApi(
                `/market-data/sec-filings?ticker=${encodeURIComponent(params.ticker)}`,
            ));
        },
    },

    providers: {
        schema: z.object({}).strict(),
        handler: async (): Promise<ToolResult> => {
            return textResult(await fetchApi("/market-data/providers"));
        },
    },

    disconnect: {
        schema: z.object({
            provider_name: z.string(),
            confirm_destructive: z.literal(true),
        }).strict(),
        handler: async (params): Promise<ToolResult> => {
            return textResult(await fetchApi(
                `/market-data/providers/${encodeURIComponent(params.provider_name)}/key`,
                { method: "DELETE" },
            ));
        },
    },

    test_provider: {
        schema: z.object({
            provider_name: z.string(),
        }).strict(),
        handler: async (params): Promise<ToolResult> => {
            return textResult(await fetchApi(
                `/market-data/providers/${encodeURIComponent(params.provider_name)}/test`,
                { method: "POST" },
            ));
        },
    },
});

// ── Registration ───────────────────────────────────────────────────────

const MARKET_ACTIONS = [
    "quote", "news", "search", "filings",
    "providers", "disconnect", "test_provider",
] as const;

export function registerMarketTool(server: McpServer): RegisteredToolHandle[] {
    return [
        server.registerTool(
            "zorivest_market",
            {
                description:
                    "Market data — stock quotes, news, ticker search, SEC filings, provider management. " +
                    `Actions: ${MARKET_ACTIONS.join(", ")}`,
                inputSchema: z.object({
                    action: z.enum(MARKET_ACTIONS).describe("Market data action to perform"),
                    ticker: z.string().optional(),
                    query: z.string().optional(),
                    count: z.number().optional(),
                    provider_name: z.string().optional(),
                    confirm_destructive: z.literal(true).optional(),
                }).strict(),
                annotations: {
                    readOnlyHint: false,
                    destructiveHint: false,
                    idempotentHint: false,
                    openWorldHint: true,
                },
            },
            async (params) => {
                return marketRouter.dispatch(
                    params.action,
                    params as unknown as Record<string, unknown>,
                );
            },
        ),
    ];
}
