/**
 * zorivest_account — Compound tool for account management.
 *
 * Absorbs 9 individual tools from accounts-tools.ts:
 *   list_accounts                → action: "list"
 *   get_account                  → action: "get"
 *   create_account               → action: "create"
 *   update_account               → action: "update"
 *   delete_account               → action: "delete" (destructive, confirmation)
 *   archive_account              → action: "archive"
 *   reassign_trades              → action: "reassign" (destructive, confirmation)
 *   record_balance               → action: "balance"
 *   get_account_review_checklist → action: "checklist"
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

// ── Type helpers ───────────────────────────────────────────────────────

interface BrokerSummary {
    broker_id: string;
    name: string;
    last_sync: string | null;
}

interface BankAccountSummary {
    account_id: string;
    name: string;
    last_updated: string | null;
}

// ── Helper ─────────────────────────────────────────────────────────────

function textResult(data: unknown): ToolResult {
    return {
        content: [{ type: "text" as const, text: JSON.stringify(data) }],
    };
}

// ── Router definition ──────────────────────────────────────────────────

const accountRouter = new CompoundToolRouter({
    // ── list ──────────────────────────────────────────────────────────
    list: {
        schema: z.object({
            include_archived: z.boolean().default(false),
            include_system: z.boolean().default(false),
        }).strict(),
        handler: async (params): Promise<ToolResult> => {
            const queryParts: string[] = [];
            if (params.include_archived) queryParts.push("include_archived=true");
            if (params.include_system) queryParts.push("include_system=true");
            const query = queryParts.length > 0 ? `?${queryParts.join("&")}` : "";
            return textResult(await fetchApi(`/accounts${query}`));
        },
    },

    // ── get ───────────────────────────────────────────────────────────
    get: {
        schema: z.object({
            account_id: z.string(),
        }).strict(),
        handler: async (params): Promise<ToolResult> => {
            return textResult(await fetchApi(`/accounts/${params.account_id}`));
        },
    },

    // ── create ────────────────────────────────────────────────────────
    create: {
        schema: z.object({
            name: z.string(),
            account_type: z.enum(["BROKER", "BANK", "IRA", "K401", "ROTH_IRA", "HSA", "OTHER"]),
            institution: z.string().optional(),
            currency: z.string().default("USD"),
            is_tax_advantaged: z.boolean().default(false),
            notes: z.string().optional(),
        }).strict(),
        handler: async (params): Promise<ToolResult> => {
            const body = {
                name: params.name,
                account_type: params.account_type,
                institution: params.institution ?? "",
                currency: params.currency,
                is_tax_advantaged: params.is_tax_advantaged,
                notes: params.notes,
            };
            return textResult(await fetchApi("/accounts", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(body),
            }));
        },
    },

    // ── update ────────────────────────────────────────────────────────
    update: {
        schema: z.object({
            account_id: z.string(),
            name: z.string().optional(),
            account_type: z.enum(["BROKER", "BANK", "IRA", "K401", "ROTH_IRA", "HSA", "OTHER"]).optional(),
            institution: z.string().optional(),
            currency: z.string().optional(),
            is_tax_advantaged: z.boolean().optional(),
            notes: z.string().optional(),
        }).strict(),
        handler: async (params): Promise<ToolResult> => {
            const body: Record<string, unknown> = {};
            if (params.name !== undefined) body.name = params.name;
            if (params.account_type !== undefined) body.account_type = params.account_type;
            if (params.institution !== undefined) body.institution = params.institution;
            if (params.currency !== undefined) body.currency = params.currency;
            if (params.is_tax_advantaged !== undefined) body.is_tax_advantaged = params.is_tax_advantaged;
            if (params.notes !== undefined) body.notes = params.notes;
            return textResult(await fetchApi(`/accounts/${params.account_id}`, {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(body),
            }));
        },
    },

    // ── delete (destructive + confirmation) ───────────────────────────
    delete: {
        schema: z.object({
            account_id: z.string(),
            confirmation_token: z.string().optional(),
        }).strict(),
        handler: async (params): Promise<ToolResult> => {
            const handler = withConfirmation(
                "delete_account",
                async (p: typeof params, _extra: unknown) => {
                    return textResult(await fetchApi(`/accounts/${p.account_id}`, {
                        method: "DELETE",
                    }));
                },
            );
            return handler(params, {}) as Promise<ToolResult>;
        },
    },

    // ── archive ───────────────────────────────────────────────────────
    archive: {
        schema: z.object({
            account_id: z.string(),
        }).strict(),
        handler: async (params): Promise<ToolResult> => {
            return textResult(await fetchApi(
                `/accounts/${params.account_id}:archive`,
                { method: "POST" },
            ));
        },
    },

    // ── reassign (destructive + confirmation) ─────────────────────────
    reassign: {
        schema: z.object({
            account_id: z.string(),
            confirmation_token: z.string().optional(),
        }).strict(),
        handler: async (params): Promise<ToolResult> => {
            const handler = withConfirmation(
                "reassign_trades",
                async (p: typeof params, _extra: unknown) => {
                    return textResult(await fetchApi(
                        `/accounts/${p.account_id}:reassign-trades`,
                        { method: "POST" },
                    ));
                },
            );
            return handler(params, {}) as Promise<ToolResult>;
        },
    },

    // ── balance ───────────────────────────────────────────────────────
    balance: {
        schema: z.object({
            account_id: z.string(),
            balance: z.number(),
            snapshot_datetime: z.string().optional(),
        }).strict(),
        handler: async (params): Promise<ToolResult> => {
            const body: Record<string, unknown> = { balance: params.balance };
            if (params.snapshot_datetime) body.snapshot_datetime = params.snapshot_datetime;
            return textResult(await fetchApi(
                `/accounts/${params.account_id}/balances`,
                {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(body),
                },
            ));
        },
    },

    // ── checklist ─────────────────────────────────────────────────────
    checklist: {
        schema: z.object({
            scope: z.enum(["all", "stale_only", "broker_only", "bank_only"]).default("stale_only"),
            stale_threshold_days: z.number().default(7),
        }).strict(),
        handler: async (params): Promise<ToolResult> => {
            const [brokersResult, banksResult] = await Promise.all([
                fetchApi("/brokers"),
                fetchApi("/banking/accounts"),
            ]);

            const brokers = (brokersResult.data as BrokerSummary[]) ?? [];
            const banks = (banksResult.data as BankAccountSummary[]) ?? [];

            const now = Date.now();
            const threshold = params.stale_threshold_days * 24 * 60 * 60 * 1000;

            const allAccounts = [
                ...brokers.map((b) => ({
                    type: "broker" as const,
                    id: b.broker_id,
                    name: b.name,
                    last_updated: b.last_sync,
                })),
                ...banks.map((b) => ({
                    type: "bank" as const,
                    id: b.account_id,
                    name: b.name,
                    last_updated: b.last_updated,
                })),
            ];

            const review = allAccounts
                .filter((a) => {
                    if (params.scope === "broker_only" && a.type !== "broker") return false;
                    if (params.scope === "bank_only" && a.type !== "bank") return false;
                    if (params.scope === "stale_only") {
                        const lastDate = new Date(a.last_updated || 0).getTime();
                        return now - lastDate > threshold;
                    }
                    return true;
                })
                .map((a) => ({
                    type: a.type,
                    id: a.id,
                    name: a.name,
                    last_updated: a.last_updated,
                    is_stale: now - new Date(a.last_updated || 0).getTime() > threshold,
                    suggested_action: a.type === "broker"
                        ? `sync_broker ${a.id}`
                        : "Manual balance update needed",
                }));

            return {
                content: [{
                    type: "text" as const,
                    text: JSON.stringify({
                        review_scope: params.scope,
                        stale_threshold_days: params.stale_threshold_days,
                        total_accounts: allAccounts.length,
                        accounts_needing_review: review.length,
                        accounts: review,
                    }),
                }],
            };
        },
    },
});

// ── Registration ───────────────────────────────────────────────────────

const ACCOUNT_ACTIONS = [
    "list", "get", "create", "update", "delete",
    "archive", "reassign", "balance", "checklist",
] as const;

export function registerAccountTool(server: McpServer): RegisteredToolHandle[] {
    return [
        server.registerTool(
            "zorivest_account",
            {
                description:
                    "Account management — list, get, create, update, delete, archive, " +
                    "reassign trades, record balance, review checklist. " +
                    "\\n\\nWorkflow: create → update → (archive | delete). Archived accounts are hidden from default list but preserved. " +
                    "Use list with include_archived:true to see them. " +
                    "\\n\\nConfirmation: 'delete' and 'reassign' actions require a confirmation_token from zorivest_system(action:\"confirm_token\"). " +
                    "The checklist action identifies stale accounts needing sync or balance updates (default: stale_only with 7-day threshold). " +
                    "\\n\\nReturns: JSON with { success, data }. Account types: BROKER, BANK, IRA, K401, ROTH_IRA, HSA, OTHER. " +
                    "Errors: 404 if account_id not found, 422 if required fields missing. " +
                    `Actions: ${ACCOUNT_ACTIONS.join(", ")}`,
                inputSchema: z.object({
                    action: z.enum(ACCOUNT_ACTIONS).describe("Account action to perform"),
                    // Per-action optional fields — validated strictly by router
                    account_id: z.string().optional(),
                    name: z.string().optional(),
                    account_type: z.enum(["BROKER", "BANK", "IRA", "K401", "ROTH_IRA", "HSA", "OTHER"]).optional(),
                    institution: z.string().optional(),
                    currency: z.string().optional(),
                    is_tax_advantaged: z.boolean().optional(),
                    notes: z.string().optional(),
                    confirmation_token: z.string().optional(),
                    balance: z.number().optional(),
                    snapshot_datetime: z.string().optional(),
                    include_archived: z.boolean().optional(),
                    include_system: z.boolean().optional(),
                    scope: z.enum(["all", "stale_only", "broker_only", "bank_only"]).optional(),
                    stale_threshold_days: z.number().optional(),
                }).strict(),
                annotations: {
                    readOnlyHint: false,
                    destructiveHint: true,
                    idempotentHint: false,
                    openWorldHint: false,
                },
            },
            async (params) => {
                return accountRouter.dispatch(
                    params.action,
                    params as unknown as Record<string, unknown>,
                );
            },
        ),
    ];
}
