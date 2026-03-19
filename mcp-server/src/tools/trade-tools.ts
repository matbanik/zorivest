/**
 * Trade MCP tools — CRUD operations and screenshot management.
 *
 * Source: 05c-mcp-trade-analytics.md
 * Uses registerTool() for annotation metadata support.
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import { fetchApi, fetchApiBinary } from "../utils/api-client.js";
import { withMetrics } from "../middleware/metrics.js";
import { withGuard } from "../middleware/mcp-guard.js";
import { withConfirmation } from "../middleware/confirmation.js";
import type { RegisteredToolHandle } from "../toolsets/registry.js";

/**
 * Register all trade-related MCP tools on the server.
 */
export function registerTradeTools(server: McpServer): RegisteredToolHandle[] {
    const handles: RegisteredToolHandle[] = [];
    // ── create_trade ─────────────────────────────────────────────────────
    handles.push(server.registerTool(
        "create_trade",
        {
            description: "Create a new trade execution record",
            inputSchema: {
                exec_id: z.string().describe("Unique execution ID"),
                time: z
                    .string()
                    .optional()
                    .describe(
                        "Trade timestamp (ISO 8601). Defaults to now if omitted.",
                    ),
                instrument: z
                    .string()
                    .describe("Ticker symbol (e.g. AAPL, MSFT)"),
                action: z
                    .enum(["BOT", "SLD"])
                    .describe("Trade action: BOT or SLD"),
                quantity: z
                    .number()
                    .positive()
                    .describe("Number of shares/contracts"),
                price: z
                    .number()
                    .positive()
                    .describe("Execution price per unit"),
                account_id: z
                    .string()
                    .describe("Broker account identifier"),
                commission: z
                    .number()
                    .min(0)
                    .optional()
                    .describe("Commission paid"),
                realized_pnl: z
                    .number()
                    .optional()
                    .describe("Realized P&L for closing trades"),
                notes: z
                    .string()
                    .optional()
                    .describe("Optional trade notes"),
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
                toolset: "trade-analytics",
                alwaysLoaded: false,
            },
        },
        // Middleware order per spec L959: withMetrics → withGuard → withConfirmation → handler

        withMetrics(
            "create_trade",
            withGuard(withConfirmation(
                "create_trade",
                async (params: {
                    exec_id: string;
                    time?: string;
                    instrument: string;
                    action: "BOT" | "SLD";
                    quantity: number;
                    price: number;
                    account_id: string;
                    commission?: number;
                    realized_pnl?: number;
                    notes?: string;
                }, _extra: unknown) => {
                    const body = {
                        exec_id: params.exec_id,
                        time: params.time ?? new Date().toISOString(),
                        instrument: params.instrument,
                        action: params.action,
                        quantity: params.quantity,
                        price: params.price,
                        account_id: params.account_id,
                        commission: params.commission ?? 0,
                        realized_pnl: params.realized_pnl ?? 0,
                        notes: params.notes,
                    };

                    const result = await fetchApi("/trades", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify(body),
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

    // ── list_trades ──────────────────────────────────────────────────────
    handles.push(server.registerTool(
        "list_trades",
        {
            description:
                "List trades with optional filtering and pagination",
            inputSchema: {
                limit: z
                    .number()
                    .int()
                    .min(1)
                    .max(100)
                    .optional()
                    .describe("Max number of trades to return (default 50)"),
                offset: z
                    .number()
                    .int()
                    .min(0)
                    .optional()
                    .describe("Number of trades to skip (default 0)"),
                account_id: z
                    .string()
                    .optional()
                    .describe("Filter by broker account ID"),
                sort: z
                    .string()
                    .optional()
                    .describe(
                        'Sort field with direction prefix, e.g. "-time" (default)',
                    ),
            },
            annotations: {
                readOnlyHint: true,
                destructiveHint: false,
                idempotentHint: true,
                openWorldHint: false,
            },
            _meta: {
                toolset: "trade-analytics",
                alwaysLoaded: false,
            },
        },
        async (params) => {
            const queryParts: string[] = [];
            if (params.limit !== undefined)
                queryParts.push(`limit=${params.limit}`);
            if (params.offset !== undefined)
                queryParts.push(`offset=${params.offset}`);
            if (params.account_id)
                queryParts.push(`account_id=${params.account_id}`);
            if (params.sort) queryParts.push(`sort=${params.sort}`);

            const query =
                queryParts.length > 0 ? `?${queryParts.join("&")}` : "";
            const result = await fetchApi(`/trades${query}`);

            return {
                content: [
                    { type: "text" as const, text: JSON.stringify(result) },
                ],
            };
        },
    ));

    // ── attach_screenshot ────────────────────────────────────────────────
    handles.push(server.registerTool(
        "attach_screenshot",
        {
            description:
                "Attach a screenshot image to a trade (base64 input)",
            inputSchema: {
                exec_id: z
                    .string()
                    .describe("Trade execution ID to attach image to"),
                image_base64: z
                    .string()
                    .describe(
                        "Base64-encoded image data (PNG, JPEG, or WebP)",
                    ),
                caption: z
                    .string()
                    .optional()
                    .describe("Image caption"),
            },
            annotations: {
                readOnlyHint: false,
                destructiveHint: false,
                idempotentHint: false,
                openWorldHint: false,
            },
            _meta: {
                toolset: "trade-analytics",
                alwaysLoaded: false,
            },
        },
        async (params) => {
            // Decode base64 → binary buffer
            const binaryData = Buffer.from(params.image_base64, "base64");

            // Build multipart form data
            const formData = new FormData();
            formData.append(
                "file",
                new Blob([binaryData], { type: "image/webp" }),
                "screenshot.webp",
            );
            if (params.caption) {
                formData.append("caption", params.caption);
            }

            const result = await fetchApi(
                `/trades/${params.exec_id}/images`,
                {
                    method: "POST",
                    body: formData,
                },
            );

            return {
                content: [
                    { type: "text" as const, text: JSON.stringify(result) },
                ],
            };
        },
    ));

    // ── get_trade_screenshots ────────────────────────────────────────────
    handles.push(server.registerTool(
        "get_trade_screenshots",
        {
            description:
                "List all screenshot images attached to a trade",
            inputSchema: {
                exec_id: z
                    .string()
                    .describe("Trade execution ID"),
            },
            annotations: {
                readOnlyHint: true,
                destructiveHint: false,
                idempotentHint: true,
                openWorldHint: false,
            },
            _meta: {
                toolset: "trade-analytics",
                alwaysLoaded: false,
            },
        },
        async (params) => {
            const result = await fetchApi(
                `/trades/${params.exec_id}/images`,
            );

            return {
                content: [
                    { type: "text" as const, text: JSON.stringify(result) },
                ],
            };
        },
    ));

    // ── get_screenshot ───────────────────────────────────────────────────
    // Live API returns raw image/webp bytes at /{id}/full (not JSON).
    // image_id is int per images.py route parameter.
    handles.push(server.registerTool(
        "get_screenshot",
        {
            description:
                "Get a specific screenshot with metadata and image data",
            inputSchema: {
                image_id: z
                    .number()
                    .int()
                    .describe("Image ID to retrieve (numeric)"),
            },
            annotations: {
                readOnlyHint: true,
                destructiveHint: false,
                idempotentHint: true,
                openWorldHint: false,
            },
            _meta: {
                toolset: "trade-analytics",
                alwaysLoaded: false,
            },
        },
        async (params) => {
            // 1. Get metadata (JSON response)
            const metaResult = await fetchApi(
                `/images/${params.image_id}`,
            );
            if (!metaResult.success) {
                return {
                    content: [
                        {
                            type: "text" as const,
                            text: JSON.stringify(metaResult),
                        },
                    ],
                };
            }

            // 2. Get full image data (binary response — raw bytes)
            const imageResult = await fetchApiBinary(
                `/images/${params.image_id}/full`,
            );

            // 3. Return mixed content: text metadata + image
            const content: Array<
                | { type: "text"; text: string }
                | { type: "image"; data: string; mimeType: string }
            > = [
                    {
                        type: "text" as const,
                        text: JSON.stringify({
                            success: true,
                            data: metaResult.data,
                        }),
                    },
                ];

            if (imageResult.success && imageResult.base64) {
                content.push({
                    type: "image" as const,
                    data: imageResult.base64,
                    mimeType: imageResult.mimeType ?? "image/webp",
                });
            }

            return { content };
        },
    ));
    // ── delete_trade ─────────────────────────────────────────────────────
    handles.push(server.registerTool(
        "delete_trade",
        {
            description:
                "Delete a trade execution record by its execution ID",
            inputSchema: {
                exec_id: z
                    .string()
                    .describe("Execution ID of the trade to delete"),
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
                toolset: "trade-analytics",
                alwaysLoaded: false,
            },
        },
        withMetrics(
            "delete_trade",
            withGuard(withConfirmation(
                "delete_trade",
                async (params: {
                    exec_id: string;
                }, _extra: unknown) => {
                    const result = await fetchApi(`/trades/${params.exec_id}`, {
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
