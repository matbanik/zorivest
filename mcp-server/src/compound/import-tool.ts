/**
 * zorivest_import — Compound tool for data import operations.
 *
 * Absorbs 7 individual tools from accounts-tools.ts:
 *   import_broker_csv     → action: "broker_csv"
 *   import_broker_pdf     → action: "broker_pdf"
 *   import_bank_statement → action: "bank_statement"
 *   sync_broker           → action: "sync_broker" (destructive, confirmation)
 *   list_brokers          → action: "list_brokers" (501 stub)
 *   resolve_identifiers   → action: "resolve_identifiers" (501 stub)
 *   list_bank_accounts    → action: "list_bank_accounts" (501 stub)
 *
 * Source: implementation-plan.md MC3
 * Phase: P2.5f (MCP Tool Consolidation)
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import { fetchApi } from "../utils/api-client.js";
import { withConfirmation } from "../middleware/confirmation.js";
import { CompoundToolRouter, type ToolResult } from "./router.js";
import type { RegisteredToolHandle } from "../toolsets/registry.js";

// ── Shared file upload helper ──────────────────────────────────────────

async function uploadFile(
    endpoint: string,
    filePath: string,
    fields: Record<string, string>,
) {
    const fs = await import("node:fs");
    const path = await import("node:path");
    const fileBuffer = fs.readFileSync(filePath);
    const fileName = path.basename(filePath);
    const formData = new FormData();
    formData.append("file", new Blob([fileBuffer]), fileName);
    for (const [k, v] of Object.entries(fields)) {
        formData.append(k, v);
    }
    return fetchApi(endpoint, { method: "POST", body: formData });
}

// ── 501 response helper ────────────────────────────────────────────────

function notImplemented(): ToolResult {
    return {
        content: [{
            type: "text" as const,
            text: JSON.stringify({
                success: false,
                error: "501: Not Implemented — This tool is planned but not yet implemented.",
            }),
        }],
    };
}

// ── Helper ─────────────────────────────────────────────────────────────

function textResult(data: unknown): ToolResult {
    return {
        content: [{ type: "text" as const, text: JSON.stringify(data) }],
    };
}

// ── Router definition ──────────────────────────────────────────────────

const importRouter = new CompoundToolRouter({
    broker_csv: {
        schema: z.object({
            file_path: z.string(),
            account_id: z.string(),
            broker_hint: z.string().default("auto"),
        }).strict(),
        handler: async (params): Promise<ToolResult> => {
            return textResult(await uploadFile("/import/csv", params.file_path, {
                account_id: params.account_id,
                broker_hint: params.broker_hint,
            }));
        },
    },

    broker_pdf: {
        schema: z.object({
            file_path: z.string(),
            account_id: z.string(),
        }).strict(),
        handler: async (params): Promise<ToolResult> => {
            return textResult(await uploadFile("/import/pdf", params.file_path, {
                account_id: params.account_id,
            }));
        },
    },

    bank_statement: {
        schema: z.object({
            file_path: z.string(),
            account_id: z.string(),
            format_hint: z.enum(["auto", "csv", "ofx", "qif"]).default("auto"),
        }).strict(),
        handler: async (params): Promise<ToolResult> => {
            return textResult(await uploadFile("/banking/import", params.file_path, {
                account_id: params.account_id,
                format_hint: params.format_hint,
            }));
        },
    },

    sync_broker: {
        schema: z.object({
            broker_id: z.string(),
            confirmation_token: z.string().optional(),
        }).strict(),
        handler: async (params): Promise<ToolResult> => {
            const handler = withConfirmation(
                "sync_broker",
                async (p: typeof params, _extra: unknown) => {
                    return textResult(await fetchApi(
                        `/brokers/${p.broker_id}/sync`,
                        { method: "POST" },
                    ));
                },
            );
            return handler(params, {}) as Promise<ToolResult>;
        },
    },

    // ── 501 stubs ────────────────────────────────────────────────────
    list_brokers: {
        schema: z.object({}).strict(),
        handler: async (): Promise<ToolResult> => notImplemented(),
    },

    resolve_identifiers: {
        schema: z.object({
            identifiers: z.array(z.object({
                id_type: z.enum(["cusip", "isin", "sedol", "figi"]),
                id_value: z.string(),
            })),
        }).strict(),
        handler: async (): Promise<ToolResult> => notImplemented(),
    },

    list_bank_accounts: {
        schema: z.object({}).strict(),
        handler: async (): Promise<ToolResult> => notImplemented(),
    },
});

// ── Registration ───────────────────────────────────────────────────────

const IMPORT_ACTIONS = [
    "broker_csv", "broker_pdf", "bank_statement", "sync_broker",
    "list_brokers", "resolve_identifiers", "list_bank_accounts",
] as const;

export function registerImportTool(server: McpServer): RegisteredToolHandle[] {
    return [
        server.registerTool(
            "zorivest_import",
            {
                description:
                    "Data import — CSV/PDF broker imports, bank statements, broker sync, " +
                    "broker listing, identifier resolution, bank account listing. " +
                    "\\n\\nWorkflow: list_brokers (find broker_id) → broker_csv or broker_pdf (import trades) → sync_broker (live sync). " +
                    "CSV import auto-detects broker format via broker_hint (default: 'auto'). Supported formats: Interactive Brokers, " +
                    "TD Ameritrade, Schwab, Fidelity, and generic CSV. " +
                    "\\n\\nPrerequisite: An account must exist before importing. Use zorivest_account(action:\"create\") first. " +
                    "Confirmation: 'sync_broker' requires a confirmation_token from zorivest_system(action:\"confirm_token\"). " +
                    "\\n\\nNote: list_brokers, resolve_identifiers, and list_bank_accounts currently return 501 Not Implemented. " +
                    "Returns: JSON with { success, data, error }. " +
                    `Actions: ${IMPORT_ACTIONS.join(", ")}`,
                inputSchema: z.object({
                    action: z.enum(IMPORT_ACTIONS).describe("Import action to perform"),
                    // Per-action optional fields — validated strictly by router
                    file_path: z.string().optional(),
                    account_id: z.string().optional(),
                    broker_hint: z.string().optional(),
                    broker_id: z.string().optional(),
                    format_hint: z.enum(["auto", "csv", "ofx", "qif"]).optional(),
                    confirmation_token: z.string().optional(),
                    identifiers: z.array(z.object({
                        id_type: z.enum(["cusip", "isin", "sedol", "figi"]),
                        id_value: z.string(),
                    })).optional(),
                }).strict(),
                annotations: {
                    readOnlyHint: false,
                    destructiveHint: false,
                    idempotentHint: false,
                    openWorldHint: false,
                },
            },
            async (params) => {
                return importRouter.dispatch(
                    params.action,
                    params as unknown as Record<string, unknown>,
                );
            },
        ),
    ];
}
