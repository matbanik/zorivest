/**
 * zorivest_template — Compound tool for email template management.
 *
 * Absorbs 6 individual tools from pipeline-security-tools.ts:
 *   create_email_template  → action: "create"
 *   get_email_template     → action: "get"
 *   list_email_templates   → action: "list"
 *   update_email_template  → action: "update"
 *   delete_email_template  → action: "delete" (destructive, confirmation)
 *   preview_email_template → action: "preview"
 *
 * Source: implementation-plan.md MC4
 * Phase: P2.5f (MCP Tool Consolidation)
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import { fetchApi } from "../utils/api-client.js";
import { withConfirmation } from "../middleware/confirmation.js";
import { CompoundToolRouter, type ToolResult } from "./router.js";
import type { RegisteredToolHandle } from "../toolsets/registry.js";

// ── Helper ─────────────────────────────────────────────────────────────

function textResult(data: unknown): ToolResult {
    return {
        content: [{ type: "text" as const, text: JSON.stringify(data) }],
    };
}

// ── Router definition ──────────────────────────────────────────────────

const templateRouter = new CompoundToolRouter({
    // ── create ────────────────────────────────────────────────────────
    create: {
        schema: z.object({
            name: z.string().min(1).max(128),
            body_html: z.string().min(1).max(65536),
            body_format: z.enum(["html", "markdown"]).default("html"),
            description: z.string().max(500).optional(),
            subject_template: z.string().max(500).optional(),
            required_variables: z.array(z.string()).optional(),
            sample_data_json: z.string().max(65536).optional(),
        }).strict(),
        handler: async (params): Promise<ToolResult> => {
            return textResult(await fetchApi("/scheduling/templates", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(params),
            }));
        },
    },

    // ── get ───────────────────────────────────────────────────────────
    get: {
        schema: z.object({
            name: z.string().min(1),
        }).strict(),
        handler: async (params): Promise<ToolResult> => {
            return textResult(await fetchApi(
                `/scheduling/templates/${encodeURIComponent(params.name)}`,
            ));
        },
    },

    // ── list ──────────────────────────────────────────────────────────
    list: {
        schema: z.object({}).strict(),
        handler: async (): Promise<ToolResult> => {
            return textResult(await fetchApi("/scheduling/templates"));
        },
    },

    // ── update ────────────────────────────────────────────────────────
    update: {
        schema: z.object({
            name: z.string().min(1),
            description: z.string().max(500).optional(),
            subject_template: z.string().max(500).optional(),
            body_html: z.string().min(1).max(65536).optional(),
            body_format: z.enum(["html", "markdown"]).optional(),
            required_variables: z.array(z.string()).optional(),
            sample_data_json: z.string().max(65536).optional(),
        }).strict(),
        handler: async (params): Promise<ToolResult> => {
            const { name, ...updateFields } = params;
            return textResult(await fetchApi(
                `/scheduling/templates/${encodeURIComponent(name)}`,
                {
                    method: "PATCH",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(updateFields),
                },
            ));
        },
    },

    // ── delete (destructive + confirmation) ───────────────────────────
    delete: {
        schema: z.object({
            name: z.string().min(1),
            confirmation_token: z.string().optional(),
        }).strict(),
        handler: async (params): Promise<ToolResult> => {
            const handler = withConfirmation(
                "delete_email_template",
                async (p: typeof params, _extra: unknown) => {
                    await fetchApi(
                        `/scheduling/templates/${encodeURIComponent(p.name)}`,
                        { method: "DELETE" },
                    );
                    return textResult({ deleted: p.name });
                },
            );
            return handler(params, {}) as Promise<ToolResult>;
        },
    },

    // ── preview ───────────────────────────────────────────────────────
    preview: {
        schema: z.object({
            name: z.string().min(1),
            data: z.record(z.unknown()).optional(),
        }).strict(),
        handler: async (params): Promise<ToolResult> => {
            return textResult(await fetchApi(
                `/scheduling/templates/${encodeURIComponent(params.name)}/preview`,
                {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ data: params.data }),
                },
            ));
        },
    },
});

// ── Registration ───────────────────────────────────────────────────────

const TEMPLATE_ACTIONS = [
    "create", "get", "list", "update", "delete", "preview",
] as const;

export function registerTemplateTool(server: McpServer): RegisteredToolHandle[] {
    return [
        server.registerTool(
            "zorivest_template",
            {
                description:
                    "Email template management — create, get, list, update, delete, " +
                    "preview rendered output. " +
                    "\\n\\nWorkflow: create (define template with Jinja2 variables) → preview (render with sample data to verify) → " +
                    "reference from pipeline policy email steps. Templates use body_format 'html' or 'markdown'. " +
                    "\\n\\nConfirmation: 'delete' requires a confirmation_token from zorivest_system(action:\"confirm_token\"). " +
                    "Returns: JSON with { success, data }. preview returns rendered HTML output. " +
                    "Errors: 404 if template name not found, 422 if body_html exceeds 64KB limit. " +
                    `Actions: ${TEMPLATE_ACTIONS.join(", ")}`,
                inputSchema: z.object({
                    action: z.enum(TEMPLATE_ACTIONS).describe("Template action to perform"),
                    // Per-action optional fields — validated strictly by router
                    name: z.string().optional(),
                    body_html: z.string().optional(),
                    body_format: z.enum(["html", "markdown"]).optional(),
                    description: z.string().optional(),
                    subject_template: z.string().optional(),
                    required_variables: z.array(z.string()).optional(),
                    sample_data_json: z.string().optional(),
                    data: z.record(z.unknown()).optional(),
                    confirmation_token: z.string().optional(),
                }).strict(),
                annotations: {
                    readOnlyHint: false,
                    destructiveHint: true,
                    idempotentHint: false,
                    openWorldHint: false,
                },
            },
            async (params) => {
                return templateRouter.dispatch(
                    params.action,
                    params as unknown as Record<string, unknown>,
                );
            },
        ),
    ];
}
