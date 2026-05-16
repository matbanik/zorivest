/**
 * zorivest_tax — Compound tool for tax-related operations.
 *
 * 15 real actions proxying to the Python REST API:
 *   simulate_tax_impact       → action: "simulate"
 *   estimate_tax              → action: "estimate"
 *   find_wash_sales           → action: "wash_sales"
 *   get_tax_lots              → action: "lots"
 *   get_quarterly_estimate    → action: "quarterly"
 *   record_quarterly_payment  → action: "record_payment" (destructive)
 *   harvest_losses            → action: "harvest"
 *   get_ytd_tax_summary       → action: "ytd_summary"
 *   sync_tax_lots             → action: "sync_lots" (write)
 *   scan_wash_sales           → action: "scan_wash_sales" (write)
 *   list_profiles             → action: "list_profiles" (read)
 *   get_profile               → action: "get_profile" (read)
 *   create_profile            → action: "create_profile" (write)
 *   update_profile            → action: "update_profile" (write)
 *   delete_profile            → action: "delete_profile" (destructive)
 *
 * Source: 05h-mcp-tax.md
 * Phase: 3E/3F (Tax Engine Wiring — MEU-149, MEU-218f)
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import { fetchApi } from "../utils/api-client.js";
import { CompoundToolRouter, type ToolResult } from "./router.js";
import type { RegisteredToolHandle } from "../toolsets/registry.js";

// ── Disclaimer ─────────────────────────────────────────────────────────

const TAX_DISCLAIMER =
    "⚠️ Tax estimates are for informational purposes only and should not be " +
    "considered tax advice. Consult a qualified tax professional before " +
    "making tax-related decisions.";

// ── Helpers ────────────────────────────────────────────────────────────

function textResult(data: unknown): ToolResult {
    const payload = { ...(data as Record<string, unknown>), disclaimer: TAX_DISCLAIMER };
    return {
        content: [{ type: "text" as const, text: JSON.stringify(payload, null, 2) }],
    };
}

// ── Router definition ──────────────────────────────────────────────────

const taxRouter = new CompoundToolRouter({
    // ── simulate ──────────────────────────────────────────────────────
    simulate: {
        schema: z.object({
            ticker: z.string().min(1).max(10).describe("Instrument symbol to simulate selling"),
            action: z.enum(["sell", "cover"]).default("sell").describe("Sale type"),
            quantity: z.number().positive().describe("Number of shares to sell"),
            price: z.number().positive().describe("Expected sale price per share"),
            account_id: z.string().min(1).describe("Account holding the position"),
            cost_basis_method: z.enum(["fifo", "lifo", "specific_id", "avg_cost"])
                .default("fifo")
                .describe("Lot selection method"),
        }).strict(),
        handler: async (params): Promise<ToolResult> => {
            const body = {
                ticker: params.ticker,
                action: params.action,
                quantity: params.quantity,
                price: params.price,
                account_id: params.account_id,
                cost_basis_method: params.cost_basis_method,
            };
            return textResult(await fetchApi("/tax/simulate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(body),
            }));
        },
    },

    // ── estimate ──────────────────────────────────────────────────────
    estimate: {
        schema: z.object({
            tax_year: z.number().int().min(2000).max(2099)
                .default(new Date().getFullYear())
                .describe("Tax year to estimate"),
            account_id: z.string().optional().describe("Optional account filter"),
            filing_status: z.enum(["single", "married_joint", "married_separate", "head_of_household"])
                .optional()
                .describe("Override filing status"),
            include_unrealized: z.boolean().default(false)
                .describe("Include unrealized gains"),
        }).strict(),
        handler: async (params): Promise<ToolResult> => {
            return textResult(await fetchApi("/tax/estimate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    tax_year: params.tax_year,
                    account_id: params.account_id,
                    filing_status: params.filing_status,
                    include_unrealized: params.include_unrealized,
                }),
            }));
        },
    },

    // ── wash_sales ────────────────────────────────────────────────────
    wash_sales: {
        schema: z.object({
            account_id: z.string().min(1).optional().describe("Filter by loss lot's account (omit for all)"),
            ticker: z.string().optional().describe("Filter to specific ticker"),
            date_range_start: z.string().optional().describe("ISO date start"),
            date_range_end: z.string().optional().describe("ISO date end"),
        }).strict(),
        handler: async (params): Promise<ToolResult> => {
            return textResult(await fetchApi("/tax/wash-sales", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    account_id: params.account_id,
                    ticker: params.ticker,
                    date_range_start: params.date_range_start,
                    date_range_end: params.date_range_end,
                }),
            }));
        },
    },

    // ── lots ──────────────────────────────────────────────────────────
    lots: {
        schema: z.object({
            account_id: z.string().optional().describe("Account ID"),
            ticker: z.string().optional().describe("Filter to specific ticker"),
            status: z.enum(["open", "closed", "all"]).default("open")
                .describe("Lot status filter"),
            sort_by: z.enum(["acquired_date", "cost_basis", "gain_loss"])
                .default("acquired_date")
                .describe("Sort order"),
        }).strict(),
        handler: async (params): Promise<ToolResult> => {
            const qp = new URLSearchParams();
            if (params.account_id) qp.set("account_id", params.account_id);
            if (params.ticker) qp.set("ticker", params.ticker);
            qp.set("status", params.status);
            qp.set("sort_by", params.sort_by);
            return textResult(await fetchApi(`/tax/lots?${qp}`));
        },
    },

    // ── quarterly ────────────────────────────────────────────────────
    quarterly: {
        schema: z.object({
            quarter: z.enum(["Q1", "Q2", "Q3", "Q4"]).describe("Tax quarter"),
            tax_year: z.number().int().min(2000).max(2099)
                .default(new Date().getFullYear()),
            estimation_method: z.enum(["annualized", "actual", "prior_year"])
                .default("annualized")
                .describe("Method for computing required payment"),
        }).strict(),
        handler: async (params): Promise<ToolResult> => {
            const qp = new URLSearchParams({
                quarter: params.quarter,
                tax_year: String(params.tax_year),
                estimation_method: params.estimation_method,
            });
            return textResult(await fetchApi(`/tax/quarterly?${qp}`));
        },
    },

    // ── record_payment (destructive) ─────────────────────────────────
    record_payment: {
        schema: z.object({
            quarter: z.enum(["Q1", "Q2", "Q3", "Q4"]).describe("Tax quarter"),
            tax_year: z.number().int().min(2000).max(2099)
                .default(new Date().getFullYear()),
            payment_amount: z.number().positive().describe("Payment amount in dollars"),
            confirm: z.literal(true).describe("Must be true to confirm recording"),
        }).strict(),
        handler: async (params): Promise<ToolResult> => {
            return textResult(await fetchApi("/tax/quarterly/payment", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    quarter: params.quarter,
                    tax_year: params.tax_year,
                    payment_amount: params.payment_amount,
                    confirm: params.confirm,
                }),
            }));
        },
    },

    // ── harvest ───────────────────────────────────────────────────────
    harvest: {
        schema: z.object({
            account_id: z.string().optional().describe("Filter to specific account"),
            min_loss_threshold: z.number().default(100)
                .describe("Minimum unrealized loss ($)"),
            exclude_wash_risk: z.boolean().default(false)
                .describe("Exclude positions with wash sale risk"),
        }).strict(),
        handler: async (params): Promise<ToolResult> => {
            const qp = new URLSearchParams();
            if (params.account_id) qp.set("account_id", params.account_id);
            qp.set("min_loss_threshold", String(params.min_loss_threshold));
            qp.set("exclude_wash_risk", String(params.exclude_wash_risk));
            return textResult(await fetchApi(`/tax/harvest?${qp}`));
        },
    },

    // ── ytd_summary ──────────────────────────────────────────────────
    ytd_summary: {
        schema: z.object({
            tax_year: z.number().int().min(2000).max(2099)
                .default(new Date().getFullYear()),
            account_id: z.string().optional().describe("Filter to specific account"),
        }).strict(),
        handler: async (params): Promise<ToolResult> => {
            const qp = new URLSearchParams({
                tax_year: String(params.tax_year),
            });
            if (params.account_id) qp.set("account_id", params.account_id);
            return textResult(await fetchApi(`/tax/ytd-summary?${qp}`));
        },
    },

    // ── sync_lots (Phase 3F, MEU-218a) ───────────────────────────────
    sync_lots: {
        schema: z.object({
            account_id: z.string().optional().describe("Scope sync to a single account ID. Omit for all accounts."),
        }).strict(),
        handler: async (params): Promise<ToolResult> => {
            const qp = new URLSearchParams();
            if (params.account_id) qp.set("account_id", params.account_id);
            const qs = qp.toString();
            const url = qs ? `/tax/sync-lots?${qs}` : "/tax/sync-lots";
            return textResult(await fetchApi(url, { method: "POST" }));
        },
    },

    // ── scan_wash_sales (MEU-218c) ────────────────────────────────────
    scan_wash_sales: {
        schema: z.object({
            tax_year: z.number().int().min(2000).max(2099)
                .default(new Date().getFullYear())
                .describe("Tax year to scan for wash sale violations"),
        }).strict(),
        handler: async (params): Promise<ToolResult> => {
            return textResult(await fetchApi(`/tax/wash-sales/scan`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ tax_year: params.tax_year }),
            }));
        },
    },

    // ── MEU-218f: TaxProfile CRUD ───────────────────────────────────

    list_profiles: {
        schema: z.object({}).strict(),
        handler: async (): Promise<ToolResult> => {
            return textResult(await fetchApi("/tax/profiles"));
        },
    },

    get_profile: {
        schema: z.object({
            tax_year: z.number().int().min(2000).max(2099)
                .describe("Tax year to retrieve profile for"),
        }).strict(),
        handler: async (params): Promise<ToolResult> => {
            return textResult(await fetchApi(`/tax/profiles/${params.tax_year}`));
        },
    },

    create_profile: {
        schema: z.object({
            tax_year: z.number().int().min(2020).max(2030).describe("Tax year for the new profile"),
            filing_status: z.enum(["SINGLE", "MARRIED_JOINT", "MARRIED_SEPARATE", "HEAD_OF_HOUSEHOLD"])
                .describe("IRS filing status"),
            federal_bracket: z.number().min(0).max(1).describe("Federal marginal tax bracket (0-1)"),
            state_tax_rate: z.number().min(0).max(1).describe("State income tax rate (0-1)"),
            state: z.string().length(2).describe("2-letter state code"),
            prior_year_tax: z.number().min(0).describe("Prior year total tax liability ($)"),
            agi_estimate: z.number().min(0).describe("AGI estimate for the year ($)"),
            capital_loss_carryforward: z.number().min(0).default(0).describe("Capital loss carryforward ($)"),
            wash_sale_method: z.enum(["CONSERVATIVE", "AGGRESSIVE"]).default("CONSERVATIVE")
                .describe("Wash sale matching aggressiveness"),
            default_cost_basis: z.enum(["FIFO", "LIFO", "HIFO", "SPEC_ID", "MAX_LT_GAIN", "MAX_LT_LOSS", "MAX_ST_GAIN", "MAX_ST_LOSS"])
                .default("FIFO").describe("Default cost basis method"),
        }).strict(),
        handler: async (params): Promise<ToolResult> => {
            return textResult(await fetchApi("/tax/profiles", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(params),
            }));
        },
    },

    update_profile: {
        schema: z.object({
            tax_year: z.number().int().min(2020).max(2030).describe("Tax year of profile to update"),
            filing_status: z.enum(["SINGLE", "MARRIED_JOINT", "MARRIED_SEPARATE", "HEAD_OF_HOUSEHOLD"]).optional(),
            federal_bracket: z.number().min(0).max(1).optional(),
            state_tax_rate: z.number().min(0).max(1).optional(),
            state: z.string().length(2).optional(),
            prior_year_tax: z.number().min(0).optional(),
            agi_estimate: z.number().min(0).optional(),
            capital_loss_carryforward: z.number().min(0).optional(),
            wash_sale_method: z.enum(["CONSERVATIVE", "AGGRESSIVE"]).optional(),
            default_cost_basis: z.enum(["FIFO", "LIFO", "HIFO", "SPEC_ID", "MAX_LT_GAIN", "MAX_LT_LOSS", "MAX_ST_GAIN", "MAX_ST_LOSS"]).optional(),
        }).strict(),
        handler: async (params): Promise<ToolResult> => {
            const { tax_year, ...body } = params;
            return textResult(await fetchApi(`/tax/profiles/${tax_year}`, {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(body),
            }));
        },
    },

    delete_profile: {
        schema: z.object({
            tax_year: z.number().int().min(2020).max(2030)
                .describe("Tax year of profile to delete"),
        }).strict(),
        handler: async (params): Promise<ToolResult> => {
            return textResult(await fetchApi(`/tax/profiles/${params.tax_year}`, {
                method: "DELETE",
            }));
        },
    },
});

// ── Registration ───────────────────────────────────────────────────────

const TAX_ACTIONS = [
    "simulate", "estimate", "wash_sales", "lots",
    "quarterly", "record_payment", "harvest", "ytd_summary",
    "sync_lots", "scan_wash_sales",
    "list_profiles", "get_profile", "create_profile", "update_profile", "delete_profile",
] as const;

export function registerTaxTool(server: McpServer): RegisteredToolHandle[] {
    return [
        server.registerTool(
            "zorivest_tax",
            {
                description:
                    "Tax operations — simulate trade impact, estimate liability, find wash sales, " +
                    "manage lots, quarterly estimates, record payments, harvest losses, YTD summary, sync lots, scan wash sales. " +
                    "\\n\\nTax Profile CRUD: list_profiles, get_profile, create_profile, update_profile, delete_profile. " +
                    "Profiles are year-scoped — one profile per tax year with filing status, rates, and elections. " +
                    "\\n\\nWorkflow: sync_lots (materialize trades → lots) → simulate (pre-trade what-if) → " +
                    "estimate (overall liability) → scan_wash_sales (trigger wash sale detection) → " +
                    "wash_sales (view detected violations) → lots (view positions) → " +
                    "quarterly (payment obligations) → record_payment (record actual payment) → " +
                    "harvest (loss harvesting opportunities) → ytd_summary (dashboard data). " +
                    "\\n\\nConfirmation: 'record_payment' requires confirm:true to prevent accidental writes. " +
                    "'sync_lots' is a write operation that materializes tax lots from trade executions. " +
                    "\\n\\nReturns: JSON with { success, data, disclaimer }. All responses include a tax disclaimer. " +
                    "Errors: 404 if ticker/account not found, 422 if required fields missing, 400 if confirm!=true. " +
                    `Actions: ${TAX_ACTIONS.join(", ")}`,
                inputSchema: z.object({
                    action: z.enum(TAX_ACTIONS).describe("Tax action to perform"),
                    // Per-action optional fields — validated strictly by router
                    ticker: z.string().optional(),
                    quantity: z.number().optional(),
                    price: z.number().optional(),
                    account_id: z.string().optional(),
                    cost_basis_method: z.enum(["fifo", "lifo", "specific_id", "avg_cost"]).optional(),
                    tax_year: z.number().optional(),
                    filing_status: z.enum(["SINGLE", "MARRIED_JOINT", "MARRIED_SEPARATE", "HEAD_OF_HOUSEHOLD"]).optional(),
                    include_unrealized: z.boolean().optional(),
                    date_range_start: z.string().optional(),
                    date_range_end: z.string().optional(),
                    status: z.enum(["open", "closed", "all"]).optional(),
                    sort_by: z.enum(["acquired_date", "cost_basis", "gain_loss"]).optional(),
                    quarter: z.enum(["Q1", "Q2", "Q3", "Q4"]).optional(),
                    estimation_method: z.enum(["annualized", "actual", "prior_year"]).optional(),
                    payment_amount: z.number().optional(),
                    confirm: z.boolean().optional(),
                    min_loss_threshold: z.number().optional(),
                    exclude_wash_risk: z.boolean().optional(),
                    federal_bracket: z.number().optional(),
                    state_tax_rate: z.number().optional(),
                    state: z.string().optional(),
                    prior_year_tax: z.number().optional(),
                    agi_estimate: z.number().optional(),
                    capital_loss_carryforward: z.number().optional(),
                    wash_sale_method: z.enum(["CONSERVATIVE", "AGGRESSIVE"]).optional(),
                    default_cost_basis: z.enum(["FIFO", "LIFO", "HIFO", "SPEC_ID", "MAX_LT_GAIN", "MAX_LT_LOSS", "MAX_ST_GAIN", "MAX_ST_LOSS"]).optional(),
                }).strict(),
                annotations: {
                    readOnlyHint: false,
                    destructiveHint: true,
                    idempotentHint: false,
                    openWorldHint: false,
                },
            },
            async (params) => {
                return taxRouter.dispatch(
                    params.action,
                    params as unknown as Record<string, unknown>,
                );
            },
        ),
    ];
}
