/**
 * MCP tools — Discovery & Safety meta-tools.
 *
 * Provides dynamic toolset management:
 * - list_available_toolsets: List all toolset groups
 * - describe_toolset: Get tool details for a toolset
 * - enable_toolset: Activate a deferred toolset
 * - get_confirmation_token: Generate token for destructive operations
 *
 * All tools are always-loaded (discovery category).
 *
 * Source: 05j-mcp-discovery.md
 * MEU: 41 (mcp-discovery)
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import { toolsetRegistry } from "../toolsets/registry.js";
import { getAuthHeaders } from "../utils/api-client.js";
import { guardCheck } from "../middleware/mcp-guard.js";

const API_BASE =
    process.env.ZORIVEST_API_URL ?? "http://localhost:8765/api/v1";

// ── Registration ───────────────────────────────────────────────────────

export function registerDiscoveryTools(server: McpServer): void {
    // ── list_available_toolsets ─────────────────────────────────────────

    server.registerTool(
        "list_available_toolsets",
        {
            description:
                "List all available toolset groups with tool counts and load status. Use this to discover what categories of tools are available.",
            inputSchema: {},
            annotations: {
                readOnlyHint: true,
                destructiveHint: false,
                idempotentHint: true,
                openWorldHint: false,
            },
            _meta: {
                toolset: "discovery",
                alwaysLoaded: true,
            },
        },
        async () => {
            const toolsets = toolsetRegistry.getAll();
            const result = {
                success: true,
                data: {
                    toolsets: toolsets.map((ts) => ({
                        name: ts.name,
                        description: ts.description,
                        tool_count: ts.tools.length,
                        loaded: ts.loaded,
                        always_loaded: ts.alwaysLoaded,
                    })),
                    total_tools: toolsets.reduce(
                        (sum, ts) => sum + ts.tools.length,
                        0,
                    ),
                },
            };
            return {
                content: [
                    {
                        type: "text" as const,
                        text: JSON.stringify(result, null, 2),
                    },
                ],
            };
        },
    );

    // ── describe_toolset ───────────────────────────────────────────────

    server.registerTool(
        "describe_toolset",
        {
            description:
                "Get detailed information about a specific toolset including all tool names and descriptions.",
            inputSchema: {
                toolset_name: z
                    .string()
                    .describe("Name of the toolset to describe"),
            },
            annotations: {
                readOnlyHint: true,
                destructiveHint: false,
                idempotentHint: true,
                openWorldHint: false,
            },
            _meta: {
                toolset: "discovery",
                alwaysLoaded: true,
            },
        },
        async ({ toolset_name }) => {
            const ts = toolsetRegistry.get(toolset_name);
            if (!ts) {
                return {
                    content: [
                        {
                            type: "text" as const,
                            text: JSON.stringify({
                                success: false,
                                error: `Unknown toolset '${toolset_name}'. Use list_available_toolsets to see all available toolsets.`,
                            }),
                        },
                    ],
                    isError: true,
                };
            }

            return {
                content: [
                    {
                        type: "text" as const,
                        text: JSON.stringify(
                            {
                                success: true,
                                data: {
                                    name: ts.name,
                                    description: ts.description,
                                    loaded: ts.loaded,
                                    always_loaded: ts.alwaysLoaded,
                                    tools: ts.tools.map((t) => ({
                                        name: t.name,
                                        description: t.description,
                                    })),
                                },
                            },
                            null,
                            2,
                        ),
                    },
                ],
            };
        },
    );

    // ── enable_toolset ─────────────────────────────────────────────────

    server.registerTool(
        "enable_toolset",
        {
            description:
                "Dynamically enable a deferred toolset, registering its tools with the server. Requires dynamic client mode (tools.listChanged capability).",
            inputSchema: {
                toolset_name: z
                    .string()
                    .describe("Name of the toolset to enable"),
            },
            annotations: {
                readOnlyHint: false,
                destructiveHint: false,
                idempotentHint: true,
                openWorldHint: false,
            },
            _meta: {
                toolset: "discovery",
                alwaysLoaded: true,
            },
        },
        async ({ toolset_name }) => {
            // AC-11: Block when MCP Guard is locked (testing-strategy L374)
            const guard = await guardCheck();
            if (!guard.allowed) {
                return {
                    content: [
                        {
                            type: "text" as const,
                            text: JSON.stringify({
                                success: false,
                                error: `MCP guard blocked enable_toolset: ${guard.reason}. Unlock via GUI → Settings → MCP Guard, or via zorivest_emergency_unlock tool.`,
                            }),
                        },
                    ],
                    isError: true,
                };
            }

            const ts = toolsetRegistry.get(toolset_name);
            if (!ts) {
                return {
                    content: [
                        {
                            type: "text" as const,
                            text: JSON.stringify({
                                success: false,
                                error: `Unknown toolset '${toolset_name}'. Use list_available_toolsets to see available toolsets.`,
                            }),
                        },
                    ],
                    isError: true,
                };
            }

            if (ts.loaded) {
                return {
                    content: [
                        {
                            type: "text" as const,
                            text: JSON.stringify({
                                success: true,
                                data: {
                                    status: "already_loaded",
                                    toolset: ts.name,
                                    tool_count: ts.tools.length,
                                },
                            }),
                        },
                    ],
                };
            }

            // AC-6: Reject static clients that don't support dynamic tool loading.
            // The MCP protocol has no clientSupportsNotification() API (05j L152
            // is aspirational). We use toolsetRegistry.dynamicLoadingEnabled as
            // the configuration point — MEU-42 wires --toolsets CLI to set this
            // false for static clients.
            if (!toolsetRegistry.dynamicLoadingEnabled) {
                return {
                    content: [
                        {
                            type: "text" as const,
                            text: JSON.stringify({
                                success: false,
                                data: null,
                                error: `Dynamic tool loading is not supported by your IDE. Restart the MCP server with --toolsets ${toolset_name} to include this category.`,
                            }),
                        },
                    ],
                    isError: true,
                };
            }

            // Register the toolset's tools with the server
            ts.register(server);
            toolsetRegistry.markLoaded(toolset_name);

            // Notify client of tool list change (safety belt — SDK also
            // auto-sends via McpServer._createRegisteredTool L651).
            try {
                server.sendToolListChanged();
            } catch {
                // Swallow — if notification fails, tools are still registered
            }

            return {
                content: [
                    {
                        type: "text" as const,
                        text: JSON.stringify({
                            success: true,
                            data: {
                                status: "enabled",
                                toolset: ts.name,
                                tool_count: ts.tools.length,
                                tools: ts.tools.map((t) => t.name),
                            },
                        }),
                    },
                ],
            };
        },
    );

    // ── get_confirmation_token ─────────────────────────────────────────

    server.registerTool(
        "get_confirmation_token",
        {
            description:
                "Generate a confirmation token for destructive operations. Required for annotation-unaware clients that cannot display human-in-the-loop prompts. The token must be passed back to the destructive tool within 60 seconds.",
            inputSchema: {
                action: z
                    .string()
                    .describe(
                        "Tool name of the destructive action (e.g. zorivest_emergency_stop)",
                    ),
                params_summary: z
                    .string()
                    .describe(
                        "Human-readable summary of what will be done",
                    ),
            },
            annotations: {
                readOnlyHint: true,
                destructiveHint: false,
                idempotentHint: false,
                openWorldHint: false,
            },
            _meta: {
                toolset: "discovery",
                alwaysLoaded: true,
            },
        },
        async ({ action, params_summary }) => {
            try {
                const res = await fetch(
                    `${API_BASE}/confirmation-tokens`,
                    {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                            ...getAuthHeaders(),
                        },
                        body: JSON.stringify({
                            action,
                            params_summary,
                        }),
                    },
                );

                if (!res.ok) {
                    const errBody = await res.text();
                    return {
                        content: [
                            {
                                type: "text" as const,
                                text: JSON.stringify({
                                    success: false,
                                    error: `Failed to generate token: ${res.status} ${errBody}`,
                                }),
                            },
                        ],
                        isError: true,
                    };
                }

                const data = (await res.json()) as {
                    token: string;
                };

                return {
                    content: [
                        {
                            type: "text" as const,
                            text: JSON.stringify({
                                token: data.token,
                                action,
                                params_summary,
                                expires_in_seconds: 60,
                                instruction:
                                    "Pass this token as 'confirmation_token' parameter to the target tool within 60 seconds.",
                            }),
                        },
                    ],
                };
            } catch (err) {
                const message =
                    err instanceof Error
                        ? err.message
                        : "Unknown error";
                return {
                    content: [
                        {
                            type: "text" as const,
                            text: JSON.stringify({
                                success: false,
                                error: `Token generation failed: ${message}`,
                            }),
                        },
                    ],
                    isError: true,
                };
            }
        },
    );
}
