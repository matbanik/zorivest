/**
 * Scheduling MCP tools.
 *
 * Source: 05g-mcp-scheduling.md
 * Registers: create_policy, list_policies, run_pipeline,
 *            preview_report, update_policy_schedule, get_pipeline_history
 * Resources: pipeline://policies/schema, pipeline://step-types
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

/**
 * Register scheduling MCP tools on the server.
 */
export function registerSchedulingTools(
    server: McpServer,
): RegisteredToolHandle[] {
    const handles: RegisteredToolHandle[] = [];

    // ── create_policy ─────────────────────────────────────────────────
    // Spec: 05g L9-82
    handles.push(
        server.registerTool(
            "create_policy",
            {
                description:
                    "Create a new pipeline policy from a JSON document. Validates structure, step types, ref integrity, and cron expression.",
                inputSchema: {
                    policy_json: z
                        .record(z.unknown())
                        .describe("Full PolicyDocument JSON object"),
                },
                annotations: {
                    readOnlyHint: false,
                    destructiveHint: false,
                    idempotentHint: false,
                    openWorldHint: false,
                },
                _meta: {
                    toolset: "scheduling",
                    alwaysLoaded: false,
                },
            },
            withMetrics(
                "create_policy",
                withGuard(
                    async (
                        params: { policy_json: Record<string, unknown> },
                        _extra: unknown,
                    ) => {
                        const result = await fetchApi(
                            "/scheduling/policies",
                            {
                                method: "POST",
                                headers: {
                                    "Content-Type": "application/json",
                                },
                                body: JSON.stringify({
                                    policy_json: params.policy_json,
                                }),
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
        ),
    );

    // ── list_policies ─────────────────────────────────────────────────
    // Spec: 05g L85-115
    handles.push(
        server.registerTool(
            "list_policies",
            {
                description:
                    "List all pipeline policies with their schedule status, approval state, and next run time.",
                inputSchema: {
                    enabled_only: z
                        .boolean()
                        .default(false)
                        .describe("Filter to enabled policies only"),
                },
                annotations: {
                    readOnlyHint: true,
                    destructiveHint: false,
                    idempotentHint: true,
                    openWorldHint: false,
                },
                _meta: {
                    toolset: "scheduling",
                    alwaysLoaded: false,
                },
            },
            withMetrics(
                "list_policies",
                withGuard(
                    async (
                        params: { enabled_only: boolean },
                        _extra: unknown,
                    ) => {
                        const result = await fetchApi(
                            `/scheduling/policies?enabled_only=${params.enabled_only}`,
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
        ),
    );

    // ── run_pipeline ──────────────────────────────────────────────────
    // Spec: 05g L118-157
    handles.push(
        server.registerTool(
            "run_pipeline",
            {
                description:
                    "Trigger a manual pipeline run for an approved policy. Returns run_id and initial status.",
                inputSchema: {
                    policy_id: z
                        .string()
                        .describe("Policy UUID to execute"),
                    dry_run: z
                        .boolean()
                        .default(false)
                        .describe(
                            "If true, skip steps with side effects",
                        ),
                },
                annotations: {
                    readOnlyHint: false,
                    destructiveHint: false,
                    idempotentHint: false,
                    openWorldHint: false,
                },
                _meta: {
                    toolset: "scheduling",
                    alwaysLoaded: false,
                },
            },
            withMetrics(
                "run_pipeline",
                withGuard(
                    async (
                        params: { policy_id: string; dry_run: boolean },
                        _extra: unknown,
                    ) => {
                        const result = await fetchApi(
                            `/scheduling/policies/${params.policy_id}/run`,
                            {
                                method: "POST",
                                headers: {
                                    "Content-Type": "application/json",
                                },
                                body: JSON.stringify({
                                    dry_run: params.dry_run,
                                }),
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
        ),
    );

    // ── preview_report ────────────────────────────────────────────────
    // Spec: 05g L160-194
    handles.push(
        server.registerTool(
            "preview_report",
            {
                description:
                    "Dry-run a pipeline and return the rendered HTML preview without sending emails or saving files.",
                inputSchema: {
                    policy_id: z
                        .string()
                        .describe("Policy UUID to preview"),
                },
                annotations: {
                    readOnlyHint: true,
                    destructiveHint: false,
                    idempotentHint: true,
                    openWorldHint: false,
                },
                _meta: {
                    toolset: "scheduling",
                    alwaysLoaded: false,
                },
            },
            withMetrics(
                "preview_report",
                withGuard(
                    async (
                        params: { policy_id: string },
                        _extra: unknown,
                    ) => {
                        const result = await fetchApi(
                            `/scheduling/policies/${params.policy_id}/run`,
                            {
                                method: "POST",
                                headers: {
                                    "Content-Type": "application/json",
                                },
                                body: JSON.stringify({ dry_run: true }),
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
        ),
    );

    // ── update_policy_schedule ─────────────────────────────────────────
    // Spec: 05g L197-245
    handles.push(
        server.registerTool(
            "update_policy_schedule",
            {
                description:
                    "Update a policy's schedule (cron expression, enable/disable, timezone).",
                inputSchema: {
                    policy_id: z
                        .string()
                        .describe("Policy UUID to update"),
                    cron_expression: z
                        .string()
                        .optional()
                        .describe("New 5-field cron expression"),
                    enabled: z
                        .boolean()
                        .optional()
                        .describe("Enable or disable the schedule"),
                    timezone: z
                        .string()
                        .optional()
                        .describe(
                            'IANA timezone (e.g. "America/New_York")',
                        ),
                },
                annotations: {
                    readOnlyHint: false,
                    destructiveHint: false,
                    idempotentHint: true,
                    openWorldHint: false,
                },
                _meta: {
                    toolset: "scheduling",
                    alwaysLoaded: false,
                },
            },
            withMetrics(
                "update_policy_schedule",
                withGuard(
                    async (
                        params: {
                            policy_id: string;
                            cron_expression?: string;
                            enabled?: boolean;
                            timezone?: string;
                        },
                        _extra: unknown,
                    ) => {
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
                            policyJson.trigger.cron_expression =
                                params.cron_expression;
                        if (params.enabled !== undefined)
                            policyJson.trigger.enabled = params.enabled;
                        if (params.timezone)
                            policyJson.trigger.timezone = params.timezone;

                        const result = await fetchApi(
                            `/scheduling/policies/${params.policy_id}`,
                            {
                                method: "PUT",
                                headers: {
                                    "Content-Type": "application/json",
                                },
                                body: JSON.stringify({
                                    policy_json: policyJson,
                                }),
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
        ),
    );

    // ── get_pipeline_history ──────────────────────────────────────────
    // Spec: 05g L248-282
    handles.push(
        server.registerTool(
            "get_pipeline_history",
            {
                description:
                    "Get recent pipeline execution history with step-level detail.",
                inputSchema: {
                    policy_id: z
                        .string()
                        .optional()
                        .describe(
                            "Filter to a specific policy (optional)",
                        ),
                    limit: z
                        .number()
                        .default(10)
                        .describe(
                            "Number of recent runs to return",
                        ),
                },
                annotations: {
                    readOnlyHint: true,
                    destructiveHint: false,
                    idempotentHint: true,
                    openWorldHint: false,
                },
                _meta: {
                    toolset: "scheduling",
                    alwaysLoaded: false,
                },
            },
            withMetrics(
                "get_pipeline_history",
                withGuard(
                    async (
                        params: {
                            policy_id?: string;
                            limit: number;
                        },
                        _extra: unknown,
                    ) => {
                        const url = params.policy_id
                            ? `/scheduling/policies/${params.policy_id}/runs?limit=${params.limit}`
                            : `/scheduling/runs?limit=${params.limit}`;
                        const result = await fetchApi(url);

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
        ),
    );

    // ── delete_policy ──────────────────────────────────────────────────
    // PH12: Spec 09g §9G.2b — destructive + confirmation gate
    handles.push(
        server.registerTool(
            "delete_policy",
            {
                description:
                    "Delete a scheduling policy by ID. This is a destructive operation that requires confirmation on static clients. " +
                    "Prerequisites: Use list_policies to find the policy_id. Returns 404 if the policy does not exist. " +
                    "The policy's scheduled job is also removed.",
                inputSchema: z.object({
                    policy_id: z.string().describe("Policy UUID to delete"),
                    confirmation_token: z
                        .string()
                        .optional()
                        .describe(
                            "Confirmation token from get_confirmation_token (required on static/annotation-unaware clients)",
                        ),
                }).strict(),
                annotations: {
                    readOnlyHint: false,
                    destructiveHint: true,
                    idempotentHint: true,
                    openWorldHint: false,
                },
                _meta: {
                    toolset: "scheduling",
                    alwaysLoaded: false,
                },
            },
            withMetrics(
                "delete_policy",
                withGuard(
                    withConfirmation(
                        "delete_policy",
                        async (
                            params: { policy_id: string },
                            _extra: unknown,
                        ) => {
                            const result = await fetchApi(
                                `/scheduling/policies/${params.policy_id}`,
                                { method: "DELETE" },
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
            ),
        ),
    );

    // ── update_policy ─────────────────────────────────────────────────
    // PH12: Spec 09g §9G.2b — in-place update, resets approval
    handles.push(
        server.registerTool(
            "update_policy",
            {
                description:
                    "Update an existing scheduling policy. Replaces the policy_json with the provided content. " +
                    "This resets the policy's approval status — the policy must be re-approved before execution. " +
                    "Prerequisites: Use list_policies or get_policy to confirm the policy exists. " +
                    "Returns the updated policy object or 422 on validation errors.",
                inputSchema: z.object({
                    policy_id: z
                        .string()
                        .describe("Policy UUID to update"),
                    policy_json: z
                        .record(z.unknown())
                        .describe("Updated PolicyDocument JSON object"),
                }).strict(),
                annotations: {
                    readOnlyHint: false,
                    destructiveHint: false,
                    idempotentHint: true,
                    openWorldHint: false,
                },
                _meta: {
                    toolset: "scheduling",
                    alwaysLoaded: false,
                },
            },
            withMetrics(
                "update_policy",
                withGuard(
                    async (
                        params: {
                            policy_id: string;
                            policy_json: Record<string, unknown>;
                        },
                        _extra: unknown,
                    ) => {
                        const result = await fetchApi(
                            `/scheduling/policies/${params.policy_id}`,
                            {
                                method: "PUT",
                                headers: {
                                    "Content-Type": "application/json",
                                },
                                body: JSON.stringify({
                                    policy_json: params.policy_json,
                                }),
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
        ),
    );

    // ── get_email_config ──────────────────────────────────────────────
    // PH12: Spec 09g §9G.2c L255 — SMTP readiness without credentials
    handles.push(
        server.registerTool(
            "get_email_config",
            {
                description:
                    "Check email/SMTP configuration readiness. Returns {configured: bool, provider: string|null, host: string|null}. " +
                    "No credentials are exposed. Use this to verify SMTP is configured before " +
                    "creating policies with email send steps.",
                inputSchema: {},
                annotations: {
                    readOnlyHint: true,
                    destructiveHint: false,
                    idempotentHint: true,
                    openWorldHint: false,
                },
                _meta: {
                    toolset: "scheduling",
                    alwaysLoaded: false,
                },
            },
            withMetrics(
                "get_email_config",
                withGuard(
                    async (_params: unknown, _extra: unknown) => {
                        const result = await fetchApi(
                            "/settings/email/status",
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
        ),
    );

    return handles;
}

// ── MCP Resources ─────────────────────────────────────────────────────
// Spec: 05g L291-314

/**
 * Register scheduling MCP resources on the server.
 */
export function registerSchedulingResources(server: McpServer): void {
    server.resource(
        "pipeline://policies/schema",
        "JSON Schema for valid PolicyDocument objects",
        async () => {
            const schema = await fetchApi("/scheduling/policies/schema");
            return {
                contents: [
                    {
                        uri: "pipeline://policies/schema",
                        text: JSON.stringify(schema, null, 2),
                        mimeType: "application/json",
                    },
                ],
            };
        },
    );

    server.resource(
        "pipeline://step-types",
        "List of registered pipeline step types with their parameter schemas",
        async () => {
            const types = await fetchApi("/scheduling/step-types");
            return {
                contents: [
                    {
                        uri: "pipeline://step-types",
                        text: JSON.stringify(types, null, 2),
                        mimeType: "application/json",
                    },
                ],
            };
        },
    );
}
