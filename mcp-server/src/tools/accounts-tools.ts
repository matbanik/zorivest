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
export function registerAccountTools(server: McpServer): void {
    // ── sync_broker ───────────────────────────────────────────────────
    // AC-1: POSTs to /brokers/{broker_id}/sync
    server.registerTool(
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
        withMetrics(
            "sync_broker",
            withGuard(async (params: { broker_id: string }, _extra: unknown) => {
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
            }),
        ),
    );

    // ── list_brokers ──────────────────────────────────────────────────
    // AC-2: GETs /brokers with no params
    server.registerTool(
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
    );

    // ── resolve_identifiers ───────────────────────────────────────────
    // AC-3: POSTs to /identifiers/resolve with JSON-wrapped body
    server.registerTool(
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
    );

    // ── import_bank_statement ─────────────────────────────────────────
    // AC-4: uploads multipart to /banking/import
    server.registerTool(
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
    );

    // ── import_broker_csv ─────────────────────────────────────────────
    // AC-5: uploads multipart to /import/csv
    server.registerTool(
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
    );

    // ── import_broker_pdf ─────────────────────────────────────────────
    // AC-6: uploads multipart to /import/pdf
    server.registerTool(
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
    );

    // ── list_bank_accounts ────────────────────────────────────────────
    // AC-7: GETs /banking/accounts with no params
    server.registerTool(
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
    );

    // ── get_account_review_checklist ──────────────────────────────────
    // AC-8: aggregates brokers + banks data, filters by scope/staleness
    server.registerTool(
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
    );
}
