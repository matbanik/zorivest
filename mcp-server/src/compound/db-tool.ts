/**
 * zorivest_db — Compound tool for database schema discovery and validation.
 *
 * Absorbs 5 individual tools from pipeline-security-tools.ts:
 *   validate_sql             → action: "validate_sql"
 *   list_db_tables           → action: "list_tables"
 *   get_db_row_samples       → action: "row_samples"
 *   list_step_types          → action: "step_types"
 *   list_provider_capabilities → action: "provider_capabilities"
 *
 * Source: implementation-plan.md MC4
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

const dbRouter = new CompoundToolRouter({
    // ── validate_sql ─────────────────────────────────────────────────
    validate_sql: {
        schema: z.object({
            sql: z.string().min(1).max(10000),
        }).strict(),
        handler: async (params): Promise<ToolResult> => {
            return textResult(await fetchApi("/scheduling/validate-sql", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ sql: params.sql }),
            }));
        },
    },

    // ── list_tables ──────────────────────────────────────────────────
    list_tables: {
        schema: z.object({}).strict(),
        handler: async (): Promise<ToolResult> => {
            return textResult(await fetchApi("/scheduling/db-schema"));
        },
    },

    // ── row_samples ──────────────────────────────────────────────────
    row_samples: {
        schema: z.object({
            table: z.string().min(1),
            limit: z.number().int().min(1).max(20).default(5),
        }).strict(),
        handler: async (params): Promise<ToolResult> => {
            return textResult(await fetchApi(
                `/scheduling/db-schema/samples/${encodeURIComponent(params.table)}?limit=${params.limit}`,
            ));
        },
    },

    // ── step_types ───────────────────────────────────────────────────
    step_types: {
        schema: z.object({}).strict(),
        handler: async (): Promise<ToolResult> => {
            return textResult(await fetchApi("/scheduling/step-types"));
        },
    },

    // ── provider_capabilities ────────────────────────────────────────
    provider_capabilities: {
        schema: z.object({}).strict(),
        handler: async (): Promise<ToolResult> => {
            return textResult(await fetchApi("/market-data/providers"));
        },
    },
});

// ── Registration ───────────────────────────────────────────────────────

const DB_ACTIONS = [
    "validate_sql", "list_tables", "row_samples",
    "step_types", "provider_capabilities",
] as const;

export function registerDbTool(server: McpServer): RegisteredToolHandle[] {
    return [
        server.registerTool(
            "zorivest_db",
            {
                description:
                    "Database discovery and validation — validate SQL queries, list queryable tables, " +
                    "get sample rows, list pipeline step types, list market data provider capabilities. " +
                    "\\n\\nWorkflow: list_tables (discover schema) → row_samples (preview data) → validate_sql (check query before use in pipeline). " +
                    "Use step_types before creating pipeline policies to discover available step types and their config schemas. " +
                    "\\n\\nAll actions are read-only and safe to call at any time. " +
                    "validate_sql checks syntax only — it does not execute the query. SQL max length: 10,000 characters. " +
                    "Returns: JSON with { success, data }. " +
                    "Errors: 422 if SQL syntax is invalid, 404 if table name not found for row_samples. " +
                    `Actions: ${DB_ACTIONS.join(", ")}`,
                inputSchema: z.object({
                    action: z.enum(DB_ACTIONS).describe("DB action to perform"),
                    // Per-action optional fields — validated strictly by router
                    sql: z.string().optional(),
                    table: z.string().optional(),
                    limit: z.number().optional(),
                }).strict(),
                annotations: {
                    readOnlyHint: true,
                    destructiveHint: false,
                    idempotentHint: true,
                    openWorldHint: false,
                },
            },
            async (params) => {
                return dbRouter.dispatch(
                    params.action,
                    params as unknown as Record<string, unknown>,
                );
            },
        ),
    ];
}
