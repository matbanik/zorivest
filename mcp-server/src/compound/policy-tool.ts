/**
 * zorivest_policy — Compound tool for pipeline policy management.
 *
 * Absorbs 9 tools from scheduling-tools.ts + pipeline-security-tools.ts:
 *   create_policy         → action: "create"
 *   list_policies         → action: "list"
 *   run_pipeline          → action: "run"
 *   preview_report        → action: "preview"
 *   update_policy_schedule→ action: "update_schedule"
 *   get_pipeline_history  → action: "get_history"
 *   delete_policy         → action: "delete" (destructive, confirmation)
 *   update_policy         → action: "update"
 *   emulate_policy        → action: "emulate"
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

const policyRouter = new CompoundToolRouter({
    // ── create ────────────────────────────────────────────────────────
    create: {
        schema: z.object({
            policy_json: z.record(z.unknown()),
        }).strict(),
        handler: async (params): Promise<ToolResult> => {
            return textResult(await fetchApi("/scheduling/policies", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ policy_json: params.policy_json }),
            }));
        },
    },

    // ── list ──────────────────────────────────────────────────────────
    list: {
        schema: z.object({
            enabled_only: z.boolean().default(false),
        }).strict(),
        handler: async (params): Promise<ToolResult> => {
            return textResult(await fetchApi(
                `/scheduling/policies?enabled_only=${params.enabled_only}`,
            ));
        },
    },

    // ── run ───────────────────────────────────────────────────────────
    run: {
        schema: z.object({
            policy_id: z.string(),
            dry_run: z.boolean().default(false),
        }).strict(),
        handler: async (params): Promise<ToolResult> => {
            return textResult(await fetchApi(
                `/scheduling/policies/${params.policy_id}/run`,
                {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ dry_run: params.dry_run }),
                },
            ));
        },
    },

    // ── preview ───────────────────────────────────────────────────────
    preview: {
        schema: z.object({
            policy_id: z.string(),
        }).strict(),
        handler: async (params): Promise<ToolResult> => {
            return textResult(await fetchApi(
                `/scheduling/policies/${params.policy_id}/run`,
                {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ dry_run: true }),
                },
            ));
        },
    },

    // ── update_schedule ───────────────────────────────────────────────
    update_schedule: {
        schema: z.object({
            policy_id: z.string(),
            cron_expression: z.string().optional(),
            enabled: z.boolean().optional(),
            timezone: z.string().optional(),
        }).strict(),
        handler: async (params): Promise<ToolResult> => {
            // GET current policy, patch trigger, PUT back
            const current = await fetchApi(
                `/scheduling/policies/${params.policy_id}`,
            );
            const policy =
                typeof current === "object" && current !== null
                    ? (current as unknown as Record<string, unknown>)
                    : {};
            const policyJson =
                typeof policy.policy_json === "string"
                    ? JSON.parse(policy.policy_json)
                    : (policy.policy_json ?? {});

            if (params.cron_expression)
                policyJson.trigger.cron_expression = params.cron_expression;
            if (params.enabled !== undefined)
                policyJson.trigger.enabled = params.enabled;
            if (params.timezone)
                policyJson.trigger.timezone = params.timezone;

            return textResult(await fetchApi(
                `/scheduling/policies/${params.policy_id}`,
                {
                    method: "PUT",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ policy_json: policyJson }),
                },
            ));
        },
    },

    // ── get_history ───────────────────────────────────────────────────
    get_history: {
        schema: z.object({
            policy_id: z.string().optional(),
            limit: z.number().default(10),
        }).strict(),
        handler: async (params): Promise<ToolResult> => {
            const url = params.policy_id
                ? `/scheduling/policies/${params.policy_id}/runs?limit=${params.limit}`
                : `/scheduling/runs?limit=${params.limit}`;
            return textResult(await fetchApi(url));
        },
    },

    // ── delete (destructive + confirmation) ───────────────────────────
    delete: {
        schema: z.object({
            policy_id: z.string(),
            confirmation_token: z.string().optional(),
        }).strict(),
        handler: async (params): Promise<ToolResult> => {
            const handler = withConfirmation(
                "delete_policy",
                async (p: typeof params, _extra: unknown) => {
                    return textResult(await fetchApi(
                        `/scheduling/policies/${p.policy_id}`,
                        { method: "DELETE" },
                    ));
                },
            );
            return handler(params, {}) as Promise<ToolResult>;
        },
    },

    // ── update ────────────────────────────────────────────────────────
    update: {
        schema: z.object({
            policy_id: z.string(),
            policy_json: z.record(z.unknown()),
        }).strict(),
        handler: async (params): Promise<ToolResult> => {
            return textResult(await fetchApi(
                `/scheduling/policies/${params.policy_id}`,
                {
                    method: "PUT",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ policy_json: params.policy_json }),
                },
            ));
        },
    },

    // ── emulate ───────────────────────────────────────────────────────
    emulate: {
        schema: z.object({
            policy_json: z.record(z.unknown()),
            phases: z.array(z.enum(["PARSE", "VALIDATE", "SIMULATE", "RENDER"])).optional(),
        }).strict(),
        handler: async (params): Promise<ToolResult> => {
            const result = await fetchApi("/scheduling/emulator/run", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    policy_json: params.policy_json,
                    phases: params.phases,
                }),
            });

            const MAX_EMULATOR_RESPONSE_BYTES = 4096;
            const text = JSON.stringify(result);
            const encoder = new TextEncoder();
            const encoded = encoder.encode(text);
            let capped: string;

            if (encoded.length > MAX_EMULATOR_RESPONSE_BYTES) {
                const MARKER_BUDGET = 80;
                const truncatedBytes = encoded.slice(
                    0,
                    MAX_EMULATOR_RESPONSE_BYTES - MARKER_BUDGET,
                );
                const decoder = new TextDecoder("utf-8", { fatal: false });
                const truncatedText = decoder.decode(truncatedBytes);
                const marker = `\n...[truncated: ${encoded.length} bytes exceeds ${MAX_EMULATOR_RESPONSE_BYTES} byte cap]`;
                capped = truncatedText + marker;
            } else {
                capped = text;
            }

            return {
                content: [{ type: "text" as const, text: capped }],
            };
        },
    },
});

// ── Registration ───────────────────────────────────────────────────────

const POLICY_ACTIONS = [
    "create", "list", "run", "preview", "update_schedule",
    "get_history", "delete", "update", "emulate",
] as const;

export function registerPolicyTool(server: McpServer): RegisteredToolHandle[] {
    return [
        server.registerTool(
            "zorivest_policy",
            {
                description:
                    "Pipeline policy management — create, list, run, preview report, " +
                    "update schedule, view run history, delete, update content, emulate. " +
                    "\\n\\nWorkflow: create → (optional: emulate to test) → approve via GUI → run (dry_run:true to preview) → run (dry_run:false to execute). " +
                    "Prerequisite: Backend API must be running. Policy must be approved via GUI before any run " +
                    "(agents cannot approve policies \u2014 approval is a human-in-the-loop security gate). " +
                    "Content updates reset approval \u2014 re-approval required after changes. Unapproved runs return an approval error. " +
                    "\\n\\nThe policy_json object must include: { name, trigger: { cron_expression, enabled, timezone }, steps: [{ type, config }] }. " +
                    "Use zorivest_db(action:\"step_types\") to discover available step types before creating policies. " +
                    "MCP resources: pipeline://policies/schema (policy JSON schema), pipeline://step-types (available step configs). " +
                    "\\n\\nConfirmation: The 'delete' action requires a confirmation_token from zorivest_system(action:\"confirm_token\"). " +
                    "Returns: JSON with { success, data, error }. Errors: 404 if policy_id not found, 422 if policy_json is malformed. " +
                    `Actions: ${POLICY_ACTIONS.join(", ")}`,
                inputSchema: z.object({
                    action: z.enum(POLICY_ACTIONS).describe("Policy action to perform"),
                    // Per-action optional fields — validated strictly by router
                    policy_id: z.string().optional(),
                    policy_json: z.record(z.unknown()).optional(),
                    enabled_only: z.boolean().optional(),
                    dry_run: z.boolean().optional(),
                    cron_expression: z.string().optional(),
                    enabled: z.boolean().optional(),
                    timezone: z.string().optional(),
                    limit: z.number().optional(),
                    confirmation_token: z.string().optional(),
                    phases: z.array(z.enum(["PARSE", "VALIDATE", "SIMULATE", "RENDER"])).optional(),
                }).strict(),
                annotations: {
                    readOnlyHint: false,
                    destructiveHint: true,
                    idempotentHint: false,
                    openWorldHint: false,
                },
            },
            async (params) => {
                return policyRouter.dispatch(
                    params.action,
                    params as unknown as Record<string, unknown>,
                );
            },
        ),
    ];
}
