/**
 * Settings MCP tools — configuration CRUD.
 *
 * Source: 05a-mcp-zorivest-settings.md
 * Uses registerTool() for annotation metadata support.
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import { fetchApi } from "../utils/api-client.js";
import type { RegisteredToolHandle } from "../toolsets/registry.js";

/**
 * Register settings-related MCP tools on the server.
 */
export function registerSettingsTools(server: McpServer): RegisteredToolHandle[] {
    const handles: RegisteredToolHandle[] = [];
    // ── get_settings ─────────────────────────────────────────────────────
    handles.push(server.registerTool(
        "get_settings",
        {
            description:
                "Retrieve application settings. Returns all settings or a specific key.",
            inputSchema: {
                key: z
                    .string()
                    .optional()
                    .describe(
                        "Optional setting key. If provided, returns just that setting. If omitted, returns all.",
                    ),
            },
            annotations: {
                readOnlyHint: true,
                destructiveHint: false,
                idempotentHint: true,
                openWorldHint: false,
            },
            _meta: {
                toolset: "core",
                alwaysLoaded: true,
            },
        },
        async (params) => {
            const path = params.key
                ? `/settings/${params.key}`
                : "/settings";
            const result = await fetchApi(path);

            return {
                content: [
                    { type: "text" as const, text: JSON.stringify(result) },
                ],
            };
        },
    ));

    // ── update_settings ──────────────────────────────────────────────────
    handles.push(server.registerTool(
        "update_settings",
        {
            description:
                "Update one or more application settings. Values are strings at the MCP boundary.",
            inputSchema: {
                settings: z
                    .record(z.string())
                    .describe(
                        'Key-value map of settings to update. All values must be strings. Example: {"theme": "dark", "timezone": "America/New_York"}',
                    ),
            },
            annotations: {
                readOnlyHint: false,
                destructiveHint: false,
                idempotentHint: true,
                openWorldHint: false,
            },
            _meta: {
                toolset: "core",
                alwaysLoaded: true,
            },
        },
        async (params) => {
            const result = await fetchApi("/settings", {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(params.settings),
            });

            return {
                content: [
                    { type: "text" as const, text: JSON.stringify(result) },
                ],
            };
        },
    ));
    return handles;
}
