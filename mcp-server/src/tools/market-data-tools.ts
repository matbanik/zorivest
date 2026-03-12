/**
 * Market Data MCP tools — MEU-64.
 *
 * 7 tools for stock quotes, news, search, SEC filings, and provider management.
 * Source: docs/build-plan/05e-mcp-market-data.md
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import { fetchApi } from "../utils/api-client.js";
import { withMetrics } from "../middleware/metrics.js";
import { withGuard } from "../middleware/mcp-guard.js";
import type { RegisteredToolHandle } from "../toolsets/registry.js";

/**
 * Register all market-data MCP tools on the server.
 */
export function registerMarketDataTools(
    server: McpServer,
): RegisteredToolHandle[] {
    const handles: RegisteredToolHandle[] = [];

    // ── get_stock_quote ───────────────────────────────────────────────
    handles.push(
        server.registerTool(
            "get_stock_quote",
            {
                description:
                    "Get a real-time stock quote with automatic provider fallback",
                inputSchema: {
                    ticker: z
                        .string()
                        .describe("Stock ticker symbol (e.g. AAPL, MSFT)"),
                },
                annotations: {
                    title: "Get Stock Quote",
                    readOnlyHint: true,
                    openWorldHint: true,
                    // @ts-expect-error TS2353 — _meta is non-standard extension for toolset routing
                    _meta: { toolset: "market-data", alwaysLoaded: false },
                },
            },
            withMetrics(
                "get_stock_quote",
                withGuard(async ({ ticker }) => {
                    const result = await fetchApi(
                        `/market-data/quote?ticker=${encodeURIComponent(ticker)}`,
                    );
                    return {
                        content: [
                            {
                                type: "text" as const,
                                text: JSON.stringify(result, null, 2),
                            },
                        ],
                    };
                }),
            ),
        ),
    );

    // ── get_market_news ───────────────────────────────────────────────
    handles.push(
        server.registerTool(
            "get_market_news",
            {
                description: "Get market news articles, optionally filtered by ticker",
                inputSchema: {
                    ticker: z
                        .string()
                        .optional()
                        .describe("Optional ticker filter"),
                    count: z
                        .number()
                        .int()
                        .min(1)
                        .max(50)
                        .optional()
                        .default(5)
                        .describe("Number of articles (1-50, default 5)"),
                },
                annotations: {
                    title: "Get Market News",
                    readOnlyHint: true,
                    openWorldHint: true,
                    // @ts-expect-error TS2353 — _meta is non-standard extension for toolset routing
                    _meta: { toolset: "market-data", alwaysLoaded: false },
                },
            },
            withMetrics(
                "get_market_news",
                withGuard(async ({ ticker, count }) => {
                    let query = `/market-data/news?count=${count ?? 5}`;
                    if (ticker) query += `&ticker=${encodeURIComponent(ticker)}`;
                    const result = await fetchApi(query);
                    return {
                        content: [
                            {
                                type: "text" as const,
                                text: JSON.stringify(result, null, 2),
                            },
                        ],
                    };
                }),
            ),
        ),
    );

    // ── search_ticker ─────────────────────────────────────────────────
    handles.push(
        server.registerTool(
            "search_ticker",
            {
                description:
                    "Search for stock ticker symbols by name or partial symbol",
                inputSchema: {
                    query: z.string().describe("Search query for symbols"),
                },
                annotations: {
                    title: "Search Ticker",
                    readOnlyHint: true,
                    openWorldHint: true,
                    // @ts-expect-error TS2353 — _meta is non-standard extension for toolset routing
                    _meta: { toolset: "market-data", alwaysLoaded: false },
                },
            },
            withMetrics(
                "search_ticker",
                withGuard(async ({ query }) => {
                    const result = await fetchApi(
                        `/market-data/search?query=${encodeURIComponent(query)}`,
                    );
                    return {
                        content: [
                            {
                                type: "text" as const,
                                text: JSON.stringify(result, null, 2),
                            },
                        ],
                    };
                }),
            ),
        ),
    );

    // ── get_sec_filings ───────────────────────────────────────────────
    handles.push(
        server.registerTool(
            "get_sec_filings",
            {
                description: "Get SEC filings for a company",
                inputSchema: {
                    ticker: z
                        .string()
                        .describe("Stock ticker symbol"),
                },
                annotations: {
                    title: "Get SEC Filings",
                    readOnlyHint: true,
                    openWorldHint: true,
                    // @ts-expect-error TS2353 — _meta is non-standard extension for toolset routing
                    _meta: { toolset: "market-data", alwaysLoaded: false },
                },
            },
            withMetrics(
                "get_sec_filings",
                withGuard(async ({ ticker }) => {
                    const result = await fetchApi(
                        `/market-data/sec-filings?ticker=${encodeURIComponent(ticker)}`,
                    );
                    return {
                        content: [
                            {
                                type: "text" as const,
                                text: JSON.stringify(result, null, 2),
                            },
                        ],
                    };
                }),
            ),
        ),
    );

    // ── list_market_providers ─────────────────────────────────────────
    handles.push(
        server.registerTool(
            "list_market_providers",
            {
                description:
                    "List all market data providers with their status",
                inputSchema: {},
                annotations: {
                    title: "List Market Providers",
                    readOnlyHint: true,
                    openWorldHint: false,
                    // @ts-expect-error TS2353 — _meta is non-standard extension for toolset routing
                    _meta: { toolset: "market-data", alwaysLoaded: false },
                },
            },
            withMetrics(
                "list_market_providers",
                withGuard(async () => {
                    const result = await fetchApi("/market-data/providers");
                    return {
                        content: [
                            {
                                type: "text" as const,
                                text: JSON.stringify(result, null, 2),
                            },
                        ],
                    };
                }),
            ),
        ),
    );

    // ── disconnect_market_provider ──────────────────────────────────────
    handles.push(
        server.registerTool(
            "disconnect_market_provider",
            {
                description:
                    "Remove API key and disable a market data provider. Requires explicit confirmation.",
                inputSchema: {
                    provider_name: z.string().describe("Provider name"),
                    confirm_destructive: z
                        .literal(true)
                        .describe(
                            "Must be true to confirm destructive operation",
                        ),
                },
                annotations: {
                    title: "Disconnect Market Provider",
                    readOnlyHint: false,
                    destructiveHint: true,
                    idempotentHint: true,
                    openWorldHint: false,
                    // @ts-expect-error TS2353 — _meta is non-standard extension for toolset routing
                    _meta: { toolset: "market-data", alwaysLoaded: false },
                },
            },
            withMetrics(
                "disconnect_market_provider",
                withGuard(async ({ provider_name }) => {
                    const result = await fetchApi(
                        `/market-data/providers/${encodeURIComponent(provider_name)}/key`,
                        { method: "DELETE" },
                    );
                    return {
                        content: [
                            {
                                type: "text" as const,
                                text: JSON.stringify(result, null, 2),
                            },
                        ],
                    };
                }),
            ),
        ),
    );

    // ── test_market_provider ─────────────────────────────────────────
    handles.push(
        server.registerTool(
            "test_market_provider",
            {
                description: "Test connectivity to a market data provider",
                inputSchema: {
                    provider_name: z.string().describe("Provider name to test"),
                },
                annotations: {
                    title: "Test Market Provider",
                    readOnlyHint: true,
                    openWorldHint: true,
                    // @ts-expect-error TS2353 — _meta is non-standard extension for toolset routing
                    _meta: { toolset: "market-data", alwaysLoaded: false },
                },
            },
            withMetrics(
                "test_market_provider",
                withGuard(async ({ provider_name }) => {
                    const result = await fetchApi(
                        `/market-data/providers/${encodeURIComponent(provider_name)}/test`,
                        { method: "POST" },
                    );
                    return {
                        content: [
                            {
                                type: "text" as const,
                                text: JSON.stringify(result, null, 2),
                            },
                        ],
                    };
                }),
            ),
        ),
    );

    return handles;
}
