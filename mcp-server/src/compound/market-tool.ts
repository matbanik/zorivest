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
 * Plus 8 expansion actions (MEU-192, §8a.11):
 *   ohlcv, fundamentals, earnings, dividends, splits,
 *   insider, economic_calendar, company_profile
 *
 * Source: implementation-plan.md MC3 + §8a.11
 * Phase: P2.5f (MCP Tool Consolidation) + P8a (Market Data Expansion)
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

/** Build query string from key-value pairs, skipping undefined values. */
function buildQuery(params: Record<string, unknown>): string {
    const parts: string[] = [];
    for (const [key, val] of Object.entries(params)) {
        if (val !== undefined && val !== null) {
            parts.push(`${key}=${encodeURIComponent(String(val))}`);
        }
    }
    return parts.length > 0 ? `?${parts.join("&")}` : "";
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

    // ── Expansion actions (MEU-192, §8a.11) ────────────────────────────

    ohlcv: {
        schema: z.object({
            ticker: z.string(),
            interval: z.string().optional(),
            start_date: z.string().optional(),
            end_date: z.string().optional(),
            limit: z.number().int().min(1).max(1000).optional(),
            provider: z.string().optional(),
        }).strict(),
        handler: async (params): Promise<ToolResult> => {
            const query = buildQuery({
                ticker: params.ticker,
                interval: params.interval,
                start_date: params.start_date,
                end_date: params.end_date,
                limit: params.limit,
                provider: params.provider,
            });
            return textResult(await fetchApi(`/market-data/ohlcv${query}`));
        },
    },

    fundamentals: {
        schema: z.object({
            ticker: z.string(),
        }).strict(),
        handler: async (params): Promise<ToolResult> => {
            return textResult(await fetchApi(
                `/market-data/fundamentals?ticker=${encodeURIComponent(params.ticker)}`,
            ));
        },
    },

    earnings: {
        schema: z.object({
            ticker: z.string(),
        }).strict(),
        handler: async (params): Promise<ToolResult> => {
            return textResult(await fetchApi(
                `/market-data/earnings?ticker=${encodeURIComponent(params.ticker)}`,
            ));
        },
    },

    dividends: {
        schema: z.object({
            ticker: z.string(),
        }).strict(),
        handler: async (params): Promise<ToolResult> => {
            return textResult(await fetchApi(
                `/market-data/dividends?ticker=${encodeURIComponent(params.ticker)}`,
            ));
        },
    },

    splits: {
        schema: z.object({
            ticker: z.string(),
        }).strict(),
        handler: async (params): Promise<ToolResult> => {
            return textResult(await fetchApi(
                `/market-data/splits?ticker=${encodeURIComponent(params.ticker)}`,
            ));
        },
    },

    insider: {
        schema: z.object({
            ticker: z.string(),
        }).strict(),
        handler: async (params): Promise<ToolResult> => {
            return textResult(await fetchApi(
                `/market-data/insider?ticker=${encodeURIComponent(params.ticker)}`,
            ));
        },
    },

    economic_calendar: {
        schema: z.object({
            country: z.string().optional(),
            start_date: z.string().optional(),
            end_date: z.string().optional(),
            limit: z.number().int().min(1).max(1000).optional(),
        }).strict(),
        handler: async (params): Promise<ToolResult> => {
            const query = buildQuery({
                country: params.country,
                start_date: params.start_date,
                end_date: params.end_date,
                limit: params.limit,
            });
            return textResult(await fetchApi(`/market-data/economic-calendar${query}`));
        },
    },

    company_profile: {
        schema: z.object({
            ticker: z.string(),
        }).strict(),
        handler: async (params): Promise<ToolResult> => {
            return textResult(await fetchApi(
                `/market-data/company-profile?ticker=${encodeURIComponent(params.ticker)}`,
            ));
        },
    },
});

// ── Registration ───────────────────────────────────────────────────────

const MARKET_ACTIONS = [
    "quote", "news", "search", "filings",
    "providers", "disconnect", "test_provider",
    "ohlcv", "fundamentals", "earnings", "dividends", "splits",
    "insider", "economic_calendar", "company_profile",
] as const;

export function registerMarketTool(server: McpServer): RegisteredToolHandle[] {
    return [
        server.registerTool(
            "zorivest_market",
            {
                description:
                    "Market data — stock quotes, news, ticker search, SEC filings, provider management. " +
                    "\\n\\nPhase 8a expansion: OHLCV candles, fundamentals, earnings, dividends, splits, " +
                    "insider transactions, economic calendar, company profiles. " +
                    "\\n\\nPrerequisite: At least one market data provider must be configured and enabled. " +
                    "Use 'providers' action to check configured providers, 'test_provider' to verify connectivity. " +
                    "\\n\\nWorkflow: search (find ticker) → quote (get price) → news (get headlines) → filings (SEC documents). " +
                    "The 'disconnect' action requires confirm_destructive:true and removes the provider's API key. " +
                    "\\n\\nReturns: JSON with { success, data }. quote returns { ticker, price, change, volume, ... }. " +
                    "Errors: 404 if ticker not found, 503 if provider unreachable. " +
                    `Actions: ${MARKET_ACTIONS.join(", ")}`,
                inputSchema: z.object({
                    action: z.enum(MARKET_ACTIONS).describe("Market data action to perform"),
                    ticker: z.string().optional(),
                    query: z.string().optional(),
                    count: z.number().optional(),
                    provider_name: z.string().optional(),
                    confirm_destructive: z.literal(true).optional(),
                    interval: z.string().optional(),
                    start_date: z.string().optional(),
                    end_date: z.string().optional(),
                    limit: z.number().optional(),
                    country: z.string().optional(),
                    provider: z.string().optional(),
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
