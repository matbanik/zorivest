/**
 * Account MCP tools.
 *
 * Source: 05f-mcp-accounts.md
 * Registers: sync_broker, list_brokers, resolve_identifiers,
 *   import_bank_statement, import_broker_csv, import_broker_pdf,
 *   list_bank_accounts, get_account_review_checklist
 *
 * Uses registerTool() for annotation metadata support.
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import { fetchApi } from "../utils/api-client.js";
import { withMetrics } from "../middleware/metrics.js";
import { withGuard } from "../middleware/mcp-guard.js";
import { withConfirmation } from "../middleware/confirmation.js";
import type { RegisteredToolHandle } from "../toolsets/registry.js";

// ── Shared helper: file upload ─────────────────────────────────────────
// AC-11: uploadFile constructs FormData with file blob and fields

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

// ── Type helpers for get_account_review_checklist ───────────────────────

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

/**
 * Register all account MCP tools on the server.
 */
export function registerAccountTools(server: McpServer): RegisteredToolHandle[] {
    const handles: RegisteredToolHandle[] = [];
    // ── sync_broker ───────────────────────────────────────────────────
    // AC-1: POSTs to /brokers/{broker_id}/sync
    handles.push(server.registerTool(
        "sync_broker",
        {
            description:
                "Sync account data and import trades from a configured broker",
            inputSchema: {
                broker_id: z
                    .string()
                    .describe('Broker ID, e.g. "ibkr_pro", "alpaca_paper"'),
            },
            annotations: {
                readOnlyHint: false,
                destructiveHint: true,
                idempotentHint: false,
                openWorldHint: false,
            },
            _meta: {
                toolset: "accounts",
                alwaysLoaded: false,
            },
        },
        // Middleware order per spec L959: withMetrics → withGuard → withConfirmation → handler
        withMetrics(
            "sync_broker",
            withGuard(withConfirmation(
                "sync_broker",
                async (params: { broker_id: string }, _extra: unknown) => {
                    const result = await fetchApi(
                        `/brokers/${params.broker_id}/sync`,
                        { method: "POST" },
                    );
                    return {
                        content: [
                            {
                                type: "text" as const,
                                text: JSON.stringify(result),
                            },
                        ],
                    };
                },
            )),
        ),
    ));

    // AC-2: GETs /brokers with no params
    handles.push(server.registerTool(
        "list_brokers",
        {
            description: "List configured broker adapters with sync status",
            inputSchema: {},
            annotations: {
                readOnlyHint: true,
                destructiveHint: false,
                idempotentHint: true,
                openWorldHint: false,
            },
            _meta: {
                toolset: "accounts",
                alwaysLoaded: false,
            },
        },
        async () => {
            const result = await fetchApi("/brokers");
            return {
                content: [
                    { type: "text" as const, text: JSON.stringify(result) },
                ],
            };
        },
    ));

    // ── resolve_identifiers ───────────────────────────────────────────
    // AC-3: POSTs to /identifiers/resolve with JSON-wrapped body
    handles.push(server.registerTool(
        "resolve_identifiers",
        {
            description:
                "Batch resolve CUSIP/ISIN/SEDOL to ticker symbols",
            inputSchema: {
                identifiers: z.array(
                    z.object({
                        id_type: z.enum(["cusip", "isin", "sedol", "figi"]),
                        id_value: z.string(),
                    }),
                ),
            },
            annotations: {
                readOnlyHint: true,
                destructiveHint: false,
                idempotentHint: true,
                openWorldHint: false,
            },
            _meta: {
                toolset: "accounts",
                alwaysLoaded: false,
            },
        },
        async (params: {
            identifiers: Array<{ id_type: string; id_value: string }>;
        }) => {
            // Bridge 05f structured input to 04b REST contract:
            // handler wraps as {"identifiers": identifiers}
            const result = await fetchApi("/identifiers/resolve", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ identifiers: params.identifiers }),
            });
            return {
                content: [
                    { type: "text" as const, text: JSON.stringify(result) },
                ],
            };
        },
    ));

    // ── import_bank_statement ─────────────────────────────────────────
    // AC-4: uploads multipart to /banking/import
    handles.push(server.registerTool(
        "import_bank_statement",
        {
            description:
                "Import a bank statement file (CSV, OFX, QIF). Provide file path.",
            inputSchema: {
                file_path: z.string(),
                account_id: z.string(),
                format_hint: z
                    .enum(["auto", "csv", "ofx", "qif"])
                    .default("auto"),
            },
            annotations: {
                readOnlyHint: false,
                destructiveHint: false,
                idempotentHint: false,
                openWorldHint: false,
            },
            _meta: {
                toolset: "accounts",
                alwaysLoaded: false,
            },
        },

        withMetrics(
            "import_bank_statement",
            withGuard(
                async (params: {
                    file_path: string;
                    account_id: string;
                    format_hint: string;
                }) => {
                    const result = await uploadFile(
                        "/banking/import",
                        params.file_path,
                        {
                            account_id: params.account_id,
                            format_hint: params.format_hint,
                        },
                    );
                    return {
                        content: [
                            {
                                type: "text" as const,
                                text: JSON.stringify(result),
                            },
                        ],
                    };
                },
            ),
        ),
    ));

    // ── import_broker_csv ─────────────────────────────────────────────
    // AC-5: uploads multipart to /import/csv
    handles.push(server.registerTool(
        "import_broker_csv",
        {
            description:
                "Import broker trade CSV with auto-detection of broker format",
            inputSchema: {
                file_path: z.string(),
                account_id: z.string(),
                broker_hint: z.string().default("auto"),
            },
            annotations: {
                readOnlyHint: false,
                destructiveHint: false,
                idempotentHint: false,
                openWorldHint: false,
            },
            _meta: {
                toolset: "accounts",
                alwaysLoaded: false,
            },
        },

        withMetrics(
            "import_broker_csv",
            withGuard(
                async (params: {
                    file_path: string;
                    account_id: string;
                    broker_hint: string;
                }) => {
                    const result = await uploadFile(
                        "/import/csv",
                        params.file_path,
                        {
                            account_id: params.account_id,
                            broker_hint: params.broker_hint,
                        },
                    );
                    return {
                        content: [
                            {
                                type: "text" as const,
                                text: JSON.stringify(result),
                            },
                        ],
                    };
                },
            ),
        ),
    ));

    // ── import_broker_pdf ─────────────────────────────────────────────
    // AC-6: uploads multipart to /import/pdf
    handles.push(server.registerTool(
        "import_broker_pdf",
        {
            description:
                "Import broker PDF statement. Extracts tables via pdfplumber.",
            inputSchema: {
                file_path: z.string(),
                account_id: z.string(),
            },
            annotations: {
                readOnlyHint: false,
                destructiveHint: false,
                idempotentHint: false,
                openWorldHint: false,
            },
            _meta: {
                toolset: "accounts",
                alwaysLoaded: false,
            },
        },

        withMetrics(
            "import_broker_pdf",
            withGuard(
                async (params: {
                    file_path: string;
                    account_id: string;
                }) => {
                    const result = await uploadFile(
                        "/import/pdf",
                        params.file_path,
                        { account_id: params.account_id },
                    );
                    return {
                        content: [
                            {
                                type: "text" as const,
                                text: JSON.stringify(result),
                            },
                        ],
                    };
                },
            ),
        ),
    ));

    // ── list_bank_accounts ────────────────────────────────────────────
    // AC-7: GETs /banking/accounts with no params
    handles.push(server.registerTool(
        "list_bank_accounts",
        {
            description:
                "List bank accounts with current balance and last updated timestamp",
            inputSchema: {},
            annotations: {
                readOnlyHint: true,
                destructiveHint: false,
                idempotentHint: true,
                openWorldHint: false,
            },
            _meta: {
                toolset: "accounts",
                alwaysLoaded: false,
            },
        },
        async () => {
            const result = await fetchApi("/banking/accounts");
            return {
                content: [
                    { type: "text" as const, text: JSON.stringify(result) },
                ],
            };
        },
    ));

    // ── get_account_review_checklist ──────────────────────────────────
    // AC-8: aggregates brokers + banks data, filters by scope/staleness
    handles.push(server.registerTool(
        "get_account_review_checklist",
        {
            description:
                "Generate a read-only account staleness checklist. Returns accounts with stale balances and suggested update actions.",
            inputSchema: {
                scope: z
                    .enum(["all", "stale_only", "broker_only", "bank_only"])
                    .default("stale_only")
                    .describe("Which accounts to include in the review"),
                stale_threshold_days: z
                    .number()
                    .default(7)
                    .describe(
                        "Consider balances older than this many days as stale",
                    ),
            },
            annotations: {
                readOnlyHint: true,
                destructiveHint: false,
                idempotentHint: true,
                openWorldHint: false,
            },
            _meta: {
                toolset: "accounts",
                alwaysLoaded: false,
            },
        },
        async (params: { scope: string; stale_threshold_days: number }) => {
            // Fetch all accounts with their last-updated timestamps
            const [brokersResult, banksResult] = await Promise.all([
                fetchApi("/brokers"),
                fetchApi("/banking/accounts"),
            ]);

            const brokers = brokersResult.data as BrokerSummary[] ?? [];
            const banks = banksResult.data as BankAccountSummary[] ?? [];

            const now = Date.now();
            const threshold =
                params.stale_threshold_days * 24 * 60 * 60 * 1000;

            // Build unified account list
            const allAccounts = [
                ...brokers.map((b) => ({
                    type: "broker" as const,
                    id: b.broker_id,
                    name: b.name,
                    last_sync: b.last_sync,
                    last_updated: b.last_sync,
                })),
                ...banks.map((b) => ({
                    type: "bank" as const,
                    id: b.account_id,
                    name: b.name,
                    last_sync: b.last_updated,
                    last_updated: b.last_updated,
                })),
            ];

            // Filter based on scope and staleness
            const review = allAccounts
                .filter((a) => {
                    if (
                        params.scope === "broker_only" &&
                        a.type !== "broker"
                    )
                        return false;
                    if (params.scope === "bank_only" && a.type !== "bank")
                        return false;
                    if (params.scope === "stale_only") {
                        const lastDate = new Date(
                            a.last_updated || 0,
                        ).getTime();
                        return now - lastDate > threshold;
                    }
                    return true;
                })
                .map((a) => ({
                    type: a.type,
                    id: a.id,
                    name: a.name,
                    last_updated: a.last_updated,
                    is_stale:
                        now -
                        new Date(a.last_updated || 0).getTime() >
                        threshold,
                    suggested_action:
                        a.type === "broker"
                            ? `sync_broker ${a.id}`
                            : "Manual balance update needed",
                }));

            return {
                content: [
                    {
                        type: "text" as const,
                        text: JSON.stringify({
                            review_scope: params.scope,
                            stale_threshold_days:
                                params.stale_threshold_days,
                            total_accounts: allAccounts.length,
                            accounts_needing_review: review.length,
                            accounts: review,
                        }),
                    },
                ],
            };
        },
    ));

    // ════════════════════════════════════════════════════════════════════
    // MEU-37: Account CRUD + Integrity MCP Tools (AC-14 through AC-20)
    // ════════════════════════════════════════════════════════════════════

    // ── list_accounts (AC-14) ─────────────────────────────────────────
    handles.push(server.registerTool(
        "list_accounts",
        {
            description:
                "List financial accounts with optional filtering. By default, archived and system accounts are excluded.",
            inputSchema: {
                include_archived: z
                    .boolean()
                    .default(false)
                    .describe("Include archived (soft-deleted) accounts"),
                include_system: z
                    .boolean()
                    .default(false)
                    .describe("Include system accounts (e.g. SYSTEM_DEFAULT)"),
            },
            annotations: {
                readOnlyHint: true,
                destructiveHint: false,
                idempotentHint: true,
                openWorldHint: false,
            },
            _meta: {
                toolset: "accounts",
                alwaysLoaded: false,
            },
        },
        async (params: { include_archived: boolean; include_system: boolean }) => {
            const queryParts: string[] = [];
            if (params.include_archived) queryParts.push("include_archived=true");
            if (params.include_system) queryParts.push("include_system=true");
            const query = queryParts.length > 0 ? `?${queryParts.join("&")}` : "";
            const result = await fetchApi(`/accounts${query}`);
            return {
                content: [
                    { type: "text" as const, text: JSON.stringify(result) },
                ],
            };
        },
    ));

    // ── get_account (AC-15) ───────────────────────────────────────────
    handles.push(server.registerTool(
        "get_account",
        {
            description:
                "Get a single account with computed metrics (trade count, win rate, realized PnL)",
            inputSchema: {
                account_id: z.string().describe("Account ID to retrieve"),
            },
            annotations: {
                readOnlyHint: true,
                destructiveHint: false,
                idempotentHint: true,
                openWorldHint: false,
            },
            _meta: {
                toolset: "accounts",
                alwaysLoaded: false,
            },
        },
        async (params: { account_id: string }) => {
            const result = await fetchApi(`/accounts/${params.account_id}`);
            return {
                content: [
                    { type: "text" as const, text: JSON.stringify(result) },
                ],
            };
        },
    ));

    // ── create_account (AC-16) — guarded, no confirmation ─────────────
    handles.push(server.registerTool(
        "create_account",
        {
            description:
                "Create a new financial account. Account ID is auto-generated if omitted.",
            inputSchema: {
                name: z.string().describe("Account display name"),
                account_type: z
                    .enum(["BROKER", "BANK", "IRA", "K401", "ROTH_IRA", "HSA", "OTHER"])
                    .describe("Account type"),
                institution: z
                    .string()
                    .optional()
                    .describe("Financial institution name"),
                currency: z
                    .string()
                    .default("USD")
                    .describe("Currency code (default: USD)"),
                is_tax_advantaged: z
                    .boolean()
                    .default(false)
                    .describe("Whether account is tax-advantaged"),
                notes: z
                    .string()
                    .optional()
                    .describe("Optional notes"),
            },
            annotations: {
                readOnlyHint: false,
                destructiveHint: false,
                idempotentHint: false,
                openWorldHint: false,
            },
            _meta: {
                toolset: "accounts",
                alwaysLoaded: false,
            },
        },
        withMetrics(
            "create_account",
            withGuard(
                async (params: {
                    name: string;
                    account_type: string;
                    institution?: string;
                    currency: string;
                    is_tax_advantaged: boolean;
                    notes?: string;
                }) => {
                    const body = {
                        name: params.name,
                        account_type: params.account_type,
                        institution: params.institution ?? "",
                        currency: params.currency,
                        is_tax_advantaged: params.is_tax_advantaged,
                        notes: params.notes,
                    };
                    const result = await fetchApi("/accounts", {
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
            ),
        ),
    ));

    // ── update_account ────────────────────────────────────────────────
    handles.push(server.registerTool(
        "update_account",
        {
            description:
                "Update account fields. Cannot modify system accounts.",
            inputSchema: {
                account_id: z.string().describe("Account ID to update"),
                name: z.string().optional().describe("New display name"),
                account_type: z
                    .enum(["BROKER", "BANK", "IRA", "K401", "ROTH_IRA", "HSA", "OTHER"])
                    .optional()
                    .describe("New account type"),
                institution: z
                    .string()
                    .optional()
                    .describe("New institution name"),
                currency: z
                    .string()
                    .optional()
                    .describe("New currency code"),
                is_tax_advantaged: z
                    .boolean()
                    .optional()
                    .describe("New tax-advantaged status"),
                notes: z.string().optional().describe("New notes"),
            },
            annotations: {
                readOnlyHint: false,
                destructiveHint: false,
                idempotentHint: true,
                openWorldHint: false,
            },
            _meta: {
                toolset: "accounts",
                alwaysLoaded: false,
            },
        },
        withMetrics(
            "update_account",
            withGuard(
                async (params: {
                    account_id: string;
                    name?: string;
                    account_type?: string;
                    institution?: string;
                    currency?: string;
                    is_tax_advantaged?: boolean;
                    notes?: string;
                }) => {
                    // Build body with only provided fields
                    const body: Record<string, unknown> = {};
                    if (params.name !== undefined) body.name = params.name;
                    if (params.account_type !== undefined) body.account_type = params.account_type;
                    if (params.institution !== undefined) body.institution = params.institution;
                    if (params.currency !== undefined) body.currency = params.currency;
                    if (params.is_tax_advantaged !== undefined)
                        body.is_tax_advantaged = params.is_tax_advantaged;
                    if (params.notes !== undefined) body.notes = params.notes;

                    const result = await fetchApi(`/accounts/${params.account_id}`, {
                        method: "PUT",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify(body),
                    });
                    return {
                        content: [
                            { type: "text" as const, text: JSON.stringify(result) },
                        ],
                    };
                },
            ),
        ),
    ));

    // ── delete_account (AC-17) — destructive + confirmation ───────────
    handles.push(server.registerTool(
        "delete_account",
        {
            description:
                "Delete an account. Block-only: fails with 409 if trades exist. Use archive_account or reassign_trades for accounts with trades.",
            inputSchema: {
                account_id: z.string().describe("Account ID to delete"),
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
                toolset: "accounts",
                alwaysLoaded: false,
            },
        },
        withMetrics(
            "delete_account",
            withGuard(withConfirmation(
                "delete_account",
                async (params: { account_id: string }, _extra: unknown) => {
                    const result = await fetchApi(`/accounts/${params.account_id}`, {
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

    // ── archive_account (AC-18) — guarded, non-destructive ────────────
    handles.push(server.registerTool(
        "archive_account",
        {
            description:
                "Soft-delete an account by setting is_archived=True. Trades remain unchanged. The account will no longer appear in default listings.",
            inputSchema: {
                account_id: z.string().describe("Account ID to archive"),
            },
            annotations: {
                readOnlyHint: false,
                destructiveHint: false,
                idempotentHint: true,
                openWorldHint: false,
            },
            _meta: {
                toolset: "accounts",
                alwaysLoaded: false,
            },
        },
        withMetrics(
            "archive_account",
            withGuard(
                async (params: { account_id: string }) => {
                    const result = await fetchApi(
                        `/accounts/${params.account_id}:archive`,
                        { method: "POST" },
                    );
                    return {
                        content: [
                            { type: "text" as const, text: JSON.stringify(result) },
                        ],
                    };
                },
            ),
        ),
    ));

    // ── reassign_trades (AC-19) — destructive + confirmation ──────────
    handles.push(server.registerTool(
        "reassign_trades",
        {
            description:
                "Move all trades from this account to SYSTEM_DEFAULT, then hard-delete the account. Returns count of reassigned trades.",
            inputSchema: {
                account_id: z.string().describe("Account ID to reassign and delete"),
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
                idempotentHint: false,
                openWorldHint: false,
            },
            _meta: {
                toolset: "accounts",
                alwaysLoaded: false,
            },
        },
        withMetrics(
            "reassign_trades",
            withGuard(withConfirmation(
                "reassign_trades",
                async (params: { account_id: string }, _extra: unknown) => {
                    const result = await fetchApi(
                        `/accounts/${params.account_id}:reassign-trades`,
                        { method: "POST" },
                    );
                    return {
                        content: [
                            { type: "text" as const, text: JSON.stringify(result) },
                        ],
                    };
                },
            )),
        ),
    ));

    // ── record_balance (AC-20) ────────────────────────────────────────
    handles.push(server.registerTool(
        "record_balance",
        {
            description:
                "Record a balance snapshot for an account. Used for portfolio tracking and performance calculation.",
            inputSchema: {
                account_id: z.string().describe("Account ID"),
                balance: z.number().describe("Current balance amount"),
                snapshot_datetime: z
                    .string()
                    .optional()
                    .describe("Snapshot timestamp (ISO 8601). Defaults to now."),
            },
            annotations: {
                readOnlyHint: false,
                destructiveHint: false,
                idempotentHint: false,
                openWorldHint: false,
            },
            _meta: {
                toolset: "accounts",
                alwaysLoaded: false,
            },
        },
        withMetrics(
            "record_balance",
            withGuard(
                async (params: {
                    account_id: string;
                    balance: number;
                    snapshot_datetime?: string;
                }) => {
                    const body: Record<string, unknown> = {
                        balance: params.balance,
                    };
                    if (params.snapshot_datetime) {
                        body.snapshot_datetime = params.snapshot_datetime;
                    }
                    const result = await fetchApi(
                        `/accounts/${params.account_id}/balances`,
                        {
                            method: "POST",
                            headers: { "Content-Type": "application/json" },
                            body: JSON.stringify(body),
                        },
                    );
                    return {
                        content: [
                            { type: "text" as const, text: JSON.stringify(result) },
                        ],
                    };
                },
            ),
        ),
    ));

    return handles;
}
