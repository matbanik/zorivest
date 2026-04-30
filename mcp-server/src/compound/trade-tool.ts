/**
 * zorivest_trade — Compound tool for trade CRUD and screenshot management.
 *
 * Absorbs 6 individual tools from trade-tools.ts:
 *   create_trade        → action: "create"
 *   list_trades          → action: "list"
 *   delete_trade         → action: "delete"
 *   attach_screenshot    → action: "screenshot_attach"
 *   get_trade_screenshots → action: "screenshot_list"
 *   get_screenshot       → action: "screenshot_get"
 *
 * Source: implementation-plan.md MC2
 * Phase: P2.5f (MCP Tool Consolidation)
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import { fetchApi, fetchApiBinary } from "../utils/api-client.js";
import { withConfirmation } from "../middleware/confirmation.js";
import { CompoundToolRouter, type ToolResult } from "./router.js";
import type { RegisteredToolHandle } from "../toolsets/registry.js";

// ── Router definition ──────────────────────────────────────────────────

const tradeRouter = new CompoundToolRouter({
    // ── create ────────────────────────────────────────────────────────
    create: {
        schema: z.object({
            exec_id: z.string(),
            time: z.string().optional(),
            instrument: z.string(),
            trade_action: z.enum(["BOT", "SLD"]),
            quantity: z.number().positive(),
            price: z.number().positive(),
            account_id: z.string(),
            commission: z.number().min(0).optional(),
            realized_pnl: z.number().optional(),
            notes: z.string().optional(),
            confirmation_token: z.string().optional(),
        }).strict(),
        handler: async (params): Promise<ToolResult> => {
            const handler = withConfirmation(
                "create_trade",
                async (p: typeof params, _extra: unknown) => {
                    const body = {
                        exec_id: p.exec_id,
                        time: p.time ?? new Date().toISOString(),
                        instrument: p.instrument,
                        action: p.trade_action,
                        quantity: p.quantity,
                        price: p.price,
                        account_id: p.account_id,
                        commission: p.commission ?? 0,
                        realized_pnl: p.realized_pnl ?? 0,
                        notes: p.notes,
                    };
                    const result = await fetchApi("/trades", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify(body),
                    });
                    return {
                        content: [{ type: "text" as const, text: JSON.stringify(result) }],
                    };
                },
            );
            return handler(params, {}) as Promise<ToolResult>;
        },
    },

    // ── list ──────────────────────────────────────────────────────────
    list: {
        schema: z.object({
            limit: z.number().int().min(1).max(100).optional(),
            offset: z.number().int().min(0).optional(),
            account_id: z.string().optional(),
            sort: z.string().optional(),
        }).strict(),
        handler: async (params): Promise<ToolResult> => {
            const queryParts: string[] = [];
            if (params.limit !== undefined) queryParts.push(`limit=${params.limit}`);
            if (params.offset !== undefined) queryParts.push(`offset=${params.offset}`);
            if (params.account_id) queryParts.push(`account_id=${params.account_id}`);
            if (params.sort) queryParts.push(`sort=${params.sort}`);
            const query = queryParts.length > 0 ? `?${queryParts.join("&")}` : "";
            const result = await fetchApi(`/trades${query}`);
            return {
                content: [{ type: "text" as const, text: JSON.stringify(result) }],
            };
        },
    },

    // ── delete ────────────────────────────────────────────────────────
    delete: {
        schema: z.object({
            exec_id: z.string(),
            confirmation_token: z.string().optional(),
        }).strict(),
        handler: async (params): Promise<ToolResult> => {
            const handler = withConfirmation(
                "delete_trade",
                async (p: typeof params, _extra: unknown) => {
                    const result = await fetchApi(`/trades/${p.exec_id}`, {
                        method: "DELETE",
                    });
                    return {
                        content: [{ type: "text" as const, text: JSON.stringify(result) }],
                    };
                },
            );
            return handler(params, {}) as Promise<ToolResult>;
        },
    },

    // ── screenshot_attach ────────────────────────────────────────────
    screenshot_attach: {
        schema: z.object({
            exec_id: z.string(),
            image_base64: z.string(),
            caption: z.string().optional(),
        }).strict(),
        handler: async (params): Promise<ToolResult> => {
            const binaryData = Buffer.from(params.image_base64, "base64");
            const formData = new FormData();
            formData.append(
                "file",
                new Blob([binaryData], { type: "image/webp" }),
                "screenshot.webp",
            );
            if (params.caption) {
                formData.append("caption", params.caption);
            }
            const result = await fetchApi(`/trades/${params.exec_id}/images`, {
                method: "POST",
                body: formData,
            });
            return {
                content: [{ type: "text" as const, text: JSON.stringify(result) }],
            };
        },
    },

    // ── screenshot_list ──────────────────────────────────────────────
    screenshot_list: {
        schema: z.object({
            exec_id: z.string(),
        }).strict(),
        handler: async (params): Promise<ToolResult> => {
            const result = await fetchApi(`/trades/${params.exec_id}/images`);
            return {
                content: [{ type: "text" as const, text: JSON.stringify(result) }],
            };
        },
    },

    // ── screenshot_get ───────────────────────────────────────────────
    screenshot_get: {
        schema: z.object({
            image_id: z.number().int(),
        }).strict(),
        handler: async (params): Promise<ToolResult> => {
            const metaResult = await fetchApi(`/images/${params.image_id}`);
            if (!metaResult.success) {
                return {
                    content: [{ type: "text" as const, text: JSON.stringify(metaResult) }],
                };
            }
            const imageResult = await fetchApiBinary(`/images/${params.image_id}/full`);
            const content: Array<
                | { type: "text"; text: string }
                | { type: "image"; data: string; mimeType: string }
            > = [
                {
                    type: "text" as const,
                    text: JSON.stringify({ success: true, data: metaResult.data }),
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
    },
});

// ── Registration ───────────────────────────────────────────────────────

const TRADE_ACTIONS = [
    "create", "list", "delete",
    "screenshot_attach", "screenshot_list", "screenshot_get",
] as const;

export function registerTradeTool(server: McpServer): RegisteredToolHandle[] {
    return [
        server.registerTool(
            "zorivest_trade",
            {
                description:
                    "Trade management — create, list, delete trades; attach/list/get screenshots. " +
                    `Actions: ${TRADE_ACTIONS.join(", ")}`,
                inputSchema: z.object({
                    action: z.enum(TRADE_ACTIONS).describe("Trade action to perform"),
                    // Per-action optional fields — validated strictly by router
                    exec_id: z.string().optional(),
                    time: z.string().optional(),
                    instrument: z.string().optional(),
                    trade_action: z.enum(["BOT", "SLD"]).optional(),
                    quantity: z.number().optional(),
                    price: z.number().optional(),
                    account_id: z.string().optional(),
                    commission: z.number().optional(),
                    realized_pnl: z.number().optional(),
                    notes: z.string().optional(),
                    confirmation_token: z.string().optional(),
                    limit: z.number().optional(),
                    offset: z.number().optional(),
                    sort: z.string().optional(),
                    image_base64: z.string().optional(),
                    caption: z.string().optional(),
                    image_id: z.number().optional(),
                }).strict(),
                annotations: {
                    readOnlyHint: false,
                    destructiveHint: true,
                    idempotentHint: false,
                    openWorldHint: false,
                },
            },
            async (params) => {
                return tradeRouter.dispatch(
                    params.action,
                    params as unknown as Record<string, unknown>,
                );
            },
        ),
    ];
}
