/**
 * Pipeline Security MCP tools — emulator, template CRUD, schema discovery.
 *
 * Source: MEU-PH9 (AC-16..AC-33m)
 * Registers: emulate_policy, validate_sql, list_db_tables, get_db_row_samples,
 *            create_email_template, get_email_template, list_email_templates,
 *            update_email_template, delete_email_template, preview_email_template,
 *            list_step_types, list_provider_capabilities
 * Resources: pipeline://db-schema, pipeline://templates,
 *            pipeline://deny-tables, pipeline://emulator/mock-data,
 *            pipeline://emulator-phases, pipeline://providers
 *
 * All tools follow M7 workflow context pattern: descriptions include
 * prerequisites, return shape, and workflow position.
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import { fetchApi } from "../utils/api-client.js";
import { withMetrics } from "../middleware/metrics.js";
import { withGuard } from "../middleware/mcp-guard.js";
import type { RegisteredToolHandle } from "../toolsets/registry.js";

/**
 * Register pipeline security MCP tools on the server.
 */
export function registerPipelineSecurityTools(
    server: McpServer,
): RegisteredToolHandle[] {
    const handles: RegisteredToolHandle[] = [];

    // ── emulate_policy ────────────────────────────────────────────────
    // AC-16: POST /scheduling/emulator/run
    handles.push(
        server.registerTool(
            "emulate_policy",
            {
                description:
                    "Dry-run a policy JSON through the 4-phase emulator (PARSE → VALIDATE → SIMULATE → RENDER). " +
                    "Returns structured errors, warnings, and mock outputs without executing side effects. " +
                    "Prerequisite: call list_policies or create_policy first to get a valid policy shape. " +
                    "Returns: {valid, phase, errors[], warnings[], mock_outputs, template_preview_hash, bytes_used}.",
                inputSchema: z.object({
                    policy_json: z
                        .record(z.unknown())
                        .describe("Full PolicyDocument JSON object"),
                    phases: z
                        .array(z.enum(["PARSE", "VALIDATE", "SIMULATE", "RENDER"]))
                        .optional()
                        .describe(
                            "Optional phase subset to run. Defaults to all 4 phases.",
                        ),
                }).strict(),
                annotations: {
                    readOnlyHint: true,
                    destructiveHint: false,
                    idempotentHint: true,
                    openWorldHint: false,
                },
                _meta: {
                    toolset: "pipeline-security",
                    alwaysLoaded: false,
                },
            },
            withMetrics(
                "emulate_policy",
                withGuard(
                    async (
                        params: {
                            policy_json: Record<string, unknown>;
                            phases?: string[];
                        },
                        _extra: unknown,
                    ) => {
                        const result = await fetchApi(
                            "/scheduling/emulator/run",
                            {
                                method: "POST",
                                headers: {
                                    "Content-Type": "application/json",
                                },
                                body: JSON.stringify({
                                    policy_json: params.policy_json,
                                    phases: params.phases,
                                }),
                            },
                        );

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
                            const decoder = new TextDecoder("utf-8", {
                                fatal: false,
                            });
                            const truncatedText =
                                decoder.decode(truncatedBytes);
                            const marker = `\n...[truncated: ${encoded.length} bytes exceeds ${MAX_EMULATOR_RESPONSE_BYTES} byte cap]`;
                            capped = truncatedText + marker;
                        } else {
                            capped = text;
                        }

                        return {
                            content: [
                                {
                                    type: "text" as const,
                                    text: capped,
                                },
                            ],
                        };
                    },
                ),
            ),
        ),
    );

    // ── validate_sql ──────────────────────────────────────────────────
    // AC-17: POST /scheduling/validate-sql
    handles.push(
        server.registerTool(
            "validate_sql",
            {
                description:
                    "Validate a SQL query against the sandbox allowlist before use in a query step. " +
                    "Checks for blocked tables, write statements, and syntax errors. " +
                    "Prerequisite: none. Use before adding SQL queries to policy steps. " +
                    "Returns: {valid: boolean, errors: string[]}.",
                inputSchema: z.object({
                    sql: z
                        .string()
                        .min(1)
                        .max(10000)
                        .describe("SQL query string to validate"),
                }).strict(),
                annotations: {
                    readOnlyHint: true,
                    destructiveHint: false,
                    idempotentHint: true,
                    openWorldHint: false,
                },
                _meta: {
                    toolset: "pipeline-security",
                    alwaysLoaded: false,
                },
            },
            withMetrics(
                "validate_sql",
                withGuard(
                    async (
                        params: { sql: string },
                        _extra: unknown,
                    ) => {
                        const result = await fetchApi(
                            "/scheduling/validate-sql",
                            {
                                method: "POST",
                                headers: {
                                    "Content-Type": "application/json",
                                },
                                body: JSON.stringify({ sql: params.sql }),
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

    // ── list_db_tables ────────────────────────────────────────────────
    // AC-19: GET /scheduling/db-schema
    handles.push(
        server.registerTool(
            "list_db_tables",
            {
                description:
                    "List database tables and columns available for query steps. " +
                    "Excludes sensitive tables (settings, credentials, MCP guard). " +
                    "Prerequisite: none. Use to discover queryable tables before writing SQL. " +
                    "Returns: [{name, columns: [{name, type, nullable}]}].",
                inputSchema: {},
                annotations: {
                    readOnlyHint: true,
                    destructiveHint: false,
                    idempotentHint: true,
                    openWorldHint: false,
                },
                _meta: {
                    toolset: "pipeline-security",
                    alwaysLoaded: false,
                },
            },
            withMetrics(
                "list_db_tables",
                withGuard(
                    async (
                        _params: Record<string, never>,
                        _extra: unknown,
                    ) => {
                        const result = await fetchApi(
                            "/scheduling/db-schema",
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

    // ── get_db_row_samples ────────────────────────────────────────────
    // AC-20: GET /scheduling/db-schema/samples/{table}
    handles.push(
        server.registerTool(
            "get_db_row_samples",
            {
                description:
                    "Fetch sample rows from a database table for query authoring. " +
                    "Restricted tables (settings, credentials) return 403. " +
                    "Prerequisite: call list_db_tables first to get available table names. " +
                    "Returns: [{column: value, ...}] (up to 5 rows by default).",
                inputSchema: z.object({
                    table: z
                        .string()
                        .min(1)
                        .describe("Table name to sample from"),
                    limit: z
                        .number()
                        .int()
                        .min(1)
                        .max(20)
                        .default(5)
                        .describe("Number of rows to return (1-20)"),
                }).strict(),
                annotations: {
                    readOnlyHint: true,
                    destructiveHint: false,
                    idempotentHint: true,
                    openWorldHint: false,
                },
                _meta: {
                    toolset: "pipeline-security",
                    alwaysLoaded: false,
                },
            },
            withMetrics(
                "get_db_row_samples",
                withGuard(
                    async (
                        params: { table: string; limit: number },
                        _extra: unknown,
                    ) => {
                        const result = await fetchApi(
                            `/scheduling/db-schema/samples/${encodeURIComponent(params.table)}?limit=${params.limit}`,
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

    // ── create_email_template ─────────────────────────────────────────
    // AC-21: POST /scheduling/templates
    handles.push(
        server.registerTool(
            "create_email_template",
            {
                description:
                    "Create a new email template for use in pipeline send steps. " +
                    "Name must be lowercase alphanumeric with hyphens/underscores. " +
                    "Prerequisite: none. Created templates can be referenced in send step body_template param. " +
                    "Returns: {name, description, body_html, body_format, required_variables, is_default}.",
                inputSchema: z.object({
                    name: z
                        .string()
                        .min(1)
                        .max(128)
                        .describe(
                            "Unique template name (lowercase, hyphens, underscores)",
                        ),
                    body_html: z
                        .string()
                        .min(1)
                        .max(65536)
                        .describe("Jinja2 HTML template body"),
                    body_format: z
                        .enum(["html", "markdown"])
                        .default("html")
                        .describe("Template format"),
                    description: z
                        .string()
                        .max(500)
                        .optional()
                        .describe("Human-readable description"),
                    subject_template: z
                        .string()
                        .max(500)
                        .optional()
                        .describe("Jinja2 subject line template"),
                    required_variables: z
                        .array(z.string())
                        .optional()
                        .describe("List of required template variable names"),
                    sample_data_json: z
                        .string()
                        .max(65536)
                        .optional()
                        .describe(
                            "JSON string of sample data for preview rendering",
                        ),
                }).strict(),
                annotations: {
                    readOnlyHint: false,
                    destructiveHint: false,
                    idempotentHint: false,
                    openWorldHint: false,
                },
                _meta: {
                    toolset: "pipeline-security",
                    alwaysLoaded: false,
                },
            },
            withMetrics(
                "create_email_template",
                withGuard(
                    async (
                        params: {
                            name: string;
                            body_html: string;
                            body_format: string;
                            description?: string;
                            subject_template?: string;
                            required_variables?: string[];
                            sample_data_json?: string;
                        },
                        _extra: unknown,
                    ) => {
                        const result = await fetchApi(
                            "/scheduling/templates",
                            {
                                method: "POST",
                                headers: {
                                    "Content-Type": "application/json",
                                },
                                body: JSON.stringify(params),
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

    // ── get_email_template ────────────────────────────────────────────
    // AC-22: GET /scheduling/templates/{name}
    handles.push(
        server.registerTool(
            "get_email_template",
            {
                description:
                    "Get a single email template by name. " +
                    "Prerequisite: call list_email_templates first to discover available names. " +
                    "Returns: {name, description, body_html, body_format, required_variables, sample_data_json, is_default}.",
                inputSchema: z.object({
                    name: z
                        .string()
                        .min(1)
                        .describe("Template name to retrieve"),
                }).strict(),
                annotations: {
                    readOnlyHint: true,
                    destructiveHint: false,
                    idempotentHint: true,
                    openWorldHint: false,
                },
                _meta: {
                    toolset: "pipeline-security",
                    alwaysLoaded: false,
                },
            },
            withMetrics(
                "get_email_template",
                withGuard(
                    async (
                        params: { name: string },
                        _extra: unknown,
                    ) => {
                        const result = await fetchApi(
                            `/scheduling/templates/${encodeURIComponent(params.name)}`,
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

    // ── list_email_templates ──────────────────────────────────────────
    // AC-23: GET /scheduling/templates
    handles.push(
        server.registerTool(
            "list_email_templates",
            {
                description:
                    "List all registered email templates. " +
                    "Prerequisite: none. Use to discover templates before referencing in send steps. " +
                    "Returns: [{name, description, body_format, is_default}].",
                inputSchema: {},
                annotations: {
                    readOnlyHint: true,
                    destructiveHint: false,
                    idempotentHint: true,
                    openWorldHint: false,
                },
                _meta: {
                    toolset: "pipeline-security",
                    alwaysLoaded: false,
                },
            },
            withMetrics(
                "list_email_templates",
                withGuard(
                    async (
                        _params: Record<string, never>,
                        _extra: unknown,
                    ) => {
                        const result = await fetchApi(
                            "/scheduling/templates",
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

    // ── update_email_template ─────────────────────────────────────────
    // AC-24: PATCH /scheduling/templates/{name}
    handles.push(
        server.registerTool(
            "update_email_template",
            {
                description:
                    "Update fields on an existing email template. " +
                    "Only provided fields are modified; others remain unchanged. " +
                    "Prerequisite: template must exist — call get_email_template first. " +
                    "Returns: updated template object.",
                inputSchema: z.object({
                    name: z
                        .string()
                        .min(1)
                        .describe("Template name to update"),
                    description: z
                        .string()
                        .max(500)
                        .optional()
                        .describe("Updated description"),
                    subject_template: z
                        .string()
                        .max(500)
                        .optional()
                        .describe("Updated subject line template"),
                    body_html: z
                        .string()
                        .min(1)
                        .max(65536)
                        .optional()
                        .describe("Updated HTML body template"),
                    body_format: z
                        .enum(["html", "markdown"])
                        .optional()
                        .describe("Updated format"),
                    required_variables: z
                        .array(z.string())
                        .optional()
                        .describe("Updated required variable names"),
                    sample_data_json: z
                        .string()
                        .max(65536)
                        .optional()
                        .describe("Updated sample data JSON string"),
                }).strict(),
                annotations: {
                    readOnlyHint: false,
                    destructiveHint: false,
                    idempotentHint: true,
                    openWorldHint: false,
                },
                _meta: {
                    toolset: "pipeline-security",
                    alwaysLoaded: false,
                },
            },
            withMetrics(
                "update_email_template",
                withGuard(
                    async (
                        params: {
                            name: string;
                            description?: string;
                            subject_template?: string;
                            body_html?: string;
                            body_format?: string;
                            required_variables?: string[];
                            sample_data_json?: string;
                        },
                        _extra: unknown,
                    ) => {
                        const { name, ...updateFields } = params;
                        const result = await fetchApi(
                            `/scheduling/templates/${encodeURIComponent(name)}`,
                            {
                                method: "PATCH",
                                headers: {
                                    "Content-Type": "application/json",
                                },
                                body: JSON.stringify(updateFields),
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

    // ── delete_email_template ─────────────────────────────────────────
    // AC-30m: DELETE /scheduling/templates/{name}
    handles.push(
        server.registerTool(
            "delete_email_template",
            {
                description:
                    "Delete a user-created email template. Default templates cannot be deleted (returns 403). " +
                    "Prerequisite: template must exist and not be a default. Call get_email_template to check is_default. " +
                    "Returns: empty body on success (204).",
                inputSchema: z.object({
                    name: z
                        .string()
                        .min(1)
                        .describe("Template name to delete"),
                }).strict(),
                annotations: {
                    readOnlyHint: false,
                    destructiveHint: true,
                    idempotentHint: true,
                    openWorldHint: false,
                },
                _meta: {
                    toolset: "pipeline-security",
                    alwaysLoaded: false,
                },
            },
            withMetrics(
                "delete_email_template",
                withGuard(
                    async (
                        params: { name: string },
                        _extra: unknown,
                    ) => {
                        await fetchApi(
                            `/scheduling/templates/${encodeURIComponent(params.name)}`,
                            { method: "DELETE" },
                        );

                        return {
                            content: [
                                {
                                    type: "text" as const,
                                    text: JSON.stringify({
                                        deleted: params.name,
                                    }),
                                },
                            ],
                        };
                    },
                ),
            ),
        ),
    );

    // ── preview_email_template ────────────────────────────────────────
    // AC-25: POST /scheduling/templates/{name}/preview
    handles.push(
        server.registerTool(
            "preview_email_template",
            {
                description:
                    "Render a template with sample or provided data and return the HTML output. " +
                    "Uses HardenedSandbox for safe Jinja2 rendering. " +
                    "Prerequisite: template must exist. Optionally provide data dict to override sample_data_json. " +
                    "Returns: {name, subject_rendered, body_rendered}.",
                inputSchema: z.object({
                    name: z
                        .string()
                        .min(1)
                        .describe("Template name to preview"),
                    data: z
                        .record(z.unknown())
                        .optional()
                        .describe(
                            "Optional data dict to render with (overrides sample data)",
                        ),
                }).strict(),
                annotations: {
                    readOnlyHint: true,
                    destructiveHint: false,
                    idempotentHint: true,
                    openWorldHint: false,
                },
                _meta: {
                    toolset: "pipeline-security",
                    alwaysLoaded: false,
                },
            },
            withMetrics(
                "preview_email_template",
                withGuard(
                    async (
                        params: {
                            name: string;
                            data?: Record<string, unknown>;
                        },
                        _extra: unknown,
                    ) => {
                        const result = await fetchApi(
                            `/scheduling/templates/${encodeURIComponent(params.name)}/preview`,
                            {
                                method: "POST",
                                headers: {
                                    "Content-Type": "application/json",
                                },
                                body: JSON.stringify({
                                    data: params.data,
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

    // ── list_step_types ────────────────────────────────────────────────
    // AC-18: GET /scheduling/step-types
    handles.push(
        server.registerTool(
            "list_step_types",
            {
                description:
                    "List available pipeline step types and their parameter schemas. " +
                    "Prerequisite: none. Use to discover what step types are available when authoring policies. " +
                    "Returns: [{type, params_schema}].",
                inputSchema: {},
                annotations: {
                    readOnlyHint: true,
                    destructiveHint: false,
                    idempotentHint: true,
                    openWorldHint: false,
                },
                _meta: {
                    toolset: "pipeline-security",
                    alwaysLoaded: false,
                },
            },
            withMetrics(
                "list_step_types",
                withGuard(
                    async (
                        _params: Record<string, never>,
                        _extra: unknown,
                    ) => {
                        const result = await fetchApi(
                            "/scheduling/step-types",
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

    // ── list_provider_capabilities ────────────────────────────────────
    // AC-26: GET /market-data/providers
    handles.push(
        server.registerTool(
            "list_provider_capabilities",
            {
                description:
                    "List market data providers and their capabilities (data types, auth methods). " +
                    "Prerequisite: none. Use to discover available providers before configuring fetch steps. " +
                    "Returns: [{name, status, data_types, auth_method}].",
                inputSchema: {},
                annotations: {
                    readOnlyHint: true,
                    destructiveHint: false,
                    idempotentHint: true,
                    openWorldHint: false,
                },
                _meta: {
                    toolset: "pipeline-security",
                    alwaysLoaded: false,
                },
            },
            withMetrics(
                "list_provider_capabilities",
                withGuard(
                    async (
                        _params: Record<string, never>,
                        _extra: unknown,
                    ) => {
                        const result = await fetchApi(
                            "/market-data/providers",
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
// AC-27: 4 read-only MCP resources

/**
 * Register pipeline security MCP resources on the server.
 */
export function registerPipelineSecurityResources(
    server: McpServer,
): void {
    // Resource: pipeline://db-schema
    server.resource(
        "pipeline://db-schema",
        "Database table schemas available for pipeline query steps (DENY_TABLES excluded)",
        async () => {
            const schema = await fetchApi("/scheduling/db-schema");
            return {
                contents: [
                    {
                        uri: "pipeline://db-schema",
                        text: JSON.stringify(schema, null, 2),
                        mimeType: "application/json",
                    },
                ],
            };
        },
    );

    // Resource: pipeline://templates
    server.resource(
        "pipeline://templates",
        "List of all registered email templates for pipeline send steps",
        async () => {
            const templates = await fetchApi("/scheduling/templates");
            return {
                contents: [
                    {
                        uri: "pipeline://templates",
                        text: JSON.stringify(templates, null, 2),
                        mimeType: "application/json",
                    },
                ],
            };
        },
    );

    // Resource: pipeline://deny-tables
    server.resource(
        "pipeline://deny-tables",
        "List of database tables blocked from query step access (credentials, auth)",
        async () => {
            // Static list from SqlSandbox.DENY_TABLES
            const denyTables = [
                "settings",
                "market_provider_settings",
                "email_provider",
                "broker_configs",
                "mcp_guard",
                "sqlite_master",
                "sqlite_schema",
                "sqlite_temp_master",
            ];
            return {
                contents: [
                    {
                        uri: "pipeline://deny-tables",
                        text: JSON.stringify(denyTables, null, 2),
                        mimeType: "application/json",
                    },
                ],
            };
        },
    );

    // Resource: pipeline://emulator/mock-data
    // AC-27 R1 correction: sample mock data sets per step type (used by SIMULATE phase)
    server.resource(
        "pipeline://emulator/mock-data",
        "Sample mock data sets for each step type (fetch, query, transform, compose, send) used by emulator SIMULATE phase",
        async () => {
            const mockData = await fetchApi("/scheduling/emulator/mock-data");
            return {
                contents: [
                    {
                        uri: "pipeline://emulator/mock-data",
                        text: JSON.stringify(mockData, null, 2),
                        mimeType: "application/json",
                    },
                ],
            };
        },
    );

    // Resource: pipeline://emulator-phases
    server.resource(
        "pipeline://emulator-phases",
        "Documentation of the 4-phase emulator pipeline (PARSE, VALIDATE, SIMULATE, RENDER)",
        async () => {
            const phases = {
                phases: [
                    {
                        name: "PARSE",
                        description:
                            "Validate policy JSON against PolicyDocument Pydantic model",
                    },
                    {
                        name: "VALIDATE",
                        description:
                            "Run 8+ validation rules, pre-parse SQL, check ref integrity, verify template existence",
                    },
                    {
                        name: "SIMULATE",
                        description:
                            "Execute step graph with mock/anonymized data",
                    },
                    {
                        name: "RENDER",
                        description:
                            "Compile templates with simulated data, return SHA-256 hash (never raw content)",
                    },
                ],
            };
            return {
                contents: [
                    {
                        uri: "pipeline://emulator-phases",
                        text: JSON.stringify(phases, null, 2),
                        mimeType: "application/json",
                    },
                ],
            };
        },
    );

    // Resource: pipeline://providers
    // AC-26/27: Market data provider capabilities for pipeline fetch step configuration
    server.resource(
        "pipeline://providers",
        "Market data providers and their capabilities (data types, auth methods, status)",
        async () => {
            const providers = await fetchApi("/market-data/providers");
            return {
                contents: [
                    {
                        uri: "pipeline://providers",
                        text: JSON.stringify(providers, null, 2),
                        mimeType: "application/json",
                    },
                ],
            };
        },
    );
}
