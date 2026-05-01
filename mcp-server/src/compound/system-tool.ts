/**
 * zorivest_system — compound tool for system/core/discovery actions.
 *
 * Absorbs 9 individual tools:
 *   diagnostics-tools.ts:   zorivest_diagnose    → action: "diagnose"
 *   settings-tools.ts:      get_settings          → action: "settings_get"
 *   settings-tools.ts:      update_settings       → action: "settings_update"
 *   discovery-tools.ts:     get_confirmation_token → action: "confirm_token"
 *   discovery-tools.ts:     list_available_toolsets → action: "toolsets_list"
 *   discovery-tools.ts:     describe_toolset       → action: "toolset_describe"
 *   discovery-tools.ts:     enable_toolset         → action: "toolset_enable"
 *   gui-tools.ts:           zorivest_launch_gui    → action: "launch_gui"
 *   scheduling-tools.ts:    get_email_config       → action: "email_config"
 *
 * Source: mcp-consolidation-proposal-v3.md §3 — zorivest_system (9 actions)
 * MEU: MC1 (compound-router-system)
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import type { RegisteredToolHandle } from "../toolsets/registry.js";
import { CompoundToolRouter, type ToolResult } from "./router.js";

// ── Import handler dependencies ────────────────────────────────────────

// diagnostics
import { getAuthHeaders } from "../utils/api-client.js";
import { metricsCollector } from "../middleware/metrics.js";

// settings
import { fetchApi } from "../utils/api-client.js";

// discovery
import { toolsetRegistry } from "../toolsets/registry.js";
import { guardCheck } from "../middleware/mcp-guard.js";
import { createConfirmationToken } from "../middleware/confirmation.js";


import { exec } from "node:child_process";
import { existsSync } from "node:fs";
import { resolve, join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

// ── Safe fetch (from diagnostics-tools.ts) ─────────────────────────────

const API_BASE =
    process.env.ZORIVEST_API_URL ?? "http://127.0.0.1:17787/api/v1";

async function safeFetch(
    url: string,
    opts?: RequestInit,
): Promise<unknown | null> {
    try {
        const res = await fetch(url, opts);
        if (!res.ok) return null;
        return res.json();
    } catch {
        return null;
    }
}

interface RawProvider {
    name: string;
    is_enabled: boolean;
    has_key: boolean;
    api_key?: string;
    [key: string]: unknown;
}

// ── GUI discovery (from gui-tools.ts) ──────────────────────────────────

const __filename_local = fileURLToPath(import.meta.url);
const __dirname_local = dirname(__filename_local);

interface DiscoveryResult {
    found: boolean;
    method: string;
    path: string;
}

function pathLookup(): Promise<string | null> {
    const cmd =
        process.platform === "win32" ? "where zorivest" : "which zorivest";
    return new Promise((res) => {
        exec(cmd, (err, stdout) => {
            if (err || !stdout.trim()) {
                res(null);
            } else {
                const p = stdout.trim().split(/[\r\n]/)[0];
                res(p);
            }
        });
    });
}

async function discoverGui(): Promise<DiscoveryResult> {
    const platform = process.platform;
    const installPaths: Record<string, string[]> = {
        win32: [
            `${process.env.LOCALAPPDATA || ""}\\Programs\\Zorivest\\Zorivest.exe`,
        ],
        darwin: ["/Applications/Zorivest.app"],
        linux: ["/usr/bin/zorivest", "/usr/local/bin/zorivest"],
    };

    const candidates = installPaths[platform] ?? installPaths.linux ?? [];
    for (const p of candidates) {
        if (existsSync(p)) {
            return { found: true, method: "packaged", path: p };
        }
    }

    const devUiDir = resolve(__dirname_local, "..", "..", "ui");
    const devPkg = join(devUiDir, "package.json");
    if (existsSync(devUiDir) && existsSync(devPkg)) {
        return { found: true, method: "dev-mode", path: devUiDir };
    }

    const pathResult = await pathLookup();
    if (pathResult) {
        return { found: true, method: "path", path: pathResult };
    }

    const envPath = process.env.ZORIVEST_GUI_PATH;
    if (envPath && existsSync(envPath)) {
        return { found: true, method: "env-var", path: envPath };
    }

    return { found: false, method: "not-found", path: "" };
}

function launchDetached(guiPath: string): void {
    const platform = process.platform;
    if (platform === "win32") {
        exec(`start "" "${guiPath}"`);
    } else if (platform === "darwin") {
        if (guiPath.endsWith(".app")) {
            exec(`open -a "${guiPath}"`);
        } else {
            exec(`nohup "${guiPath}" > /dev/null 2>&1 &`);
        }
    } else {
        exec(`setsid "${guiPath}" > /dev/null 2>&1 &`);
    }
}

function launchAndWait(guiPath: string): Promise<void> {
    return new Promise((resolve, reject) => {
        exec(`"${guiPath}"`, (err) => {
            if (err) reject(err);
            else resolve();
        });
    });
}

function openReleasesPage(): void {
    const url = "https://github.com/zorivest/zorivest/releases";
    const platform = process.platform;
    if (platform === "win32") {
        exec(`start "" "${url}"`);
    } else if (platform === "darwin") {
        exec(`open "${url}"`);
    } else {
        exec(`xdg-open "${url}"`);
    }
}

const RELEASES_URL = "https://github.com/zorivest/zorivest/releases";

// ── Router definition ──────────────────────────────────────────────────

const systemRouter = new CompoundToolRouter({
    // ── diagnose ──────────────────────────────────────────────────────
    diagnose: {
        schema: z
            .object({
                verbose: z
                    .boolean()
                    .default(false)
                    .describe(
                        "Include per-tool latency percentiles (p50/p95/p99) and payload sizes",
                    ),
            })
            .strict(),
        handler: async (params): Promise<ToolResult> => {
            const authHeaders = await getAuthHeaders();

            const [health, version, guard, providers] = await Promise.all([
                safeFetch(`${API_BASE}/health`),
                safeFetch(`${API_BASE}/version/`),
                safeFetch(`${API_BASE}/mcp-guard/status`, {
                    headers: authHeaders,
                }),
                safeFetch(`${API_BASE}/market-data/providers`, {
                    headers: authHeaders,
                }),
            ]);

            const healthData = health as Record<string, unknown> | null;
            const versionData = version as Record<string, unknown> | null;
            const guardData = guard as Record<string, unknown> | null;
            const providersData = providers as RawProvider[] | null;

            const report = {
                backend: {
                    reachable: healthData !== null,
                    status:
                        (healthData?.status as string | undefined) ??
                        "unreachable",
                },
                version: versionData ?? {
                    version: "unknown",
                    context: "unknown",
                },
                database: {
                    unlocked:
                        healthData?.database_unlocked ??
                        (healthData?.database as Record<string, unknown>)
                            ?.unlocked ??
                        "unknown",
                },
                guard: guardData
                    ? {
                          enabled: guardData.is_enabled,
                          locked: guardData.is_locked,
                          lock_reason: guardData.lock_reason ?? null,
                          recent_calls_1min:
                              guardData.recent_calls_1min ?? 0,
                          recent_calls_1hr:
                              guardData.recent_calls_1hr ?? 0,
                      }
                    : { status: "unavailable" as const },
                providers: providersData
                    ? providersData.map((p) => ({
                          name: p.name,
                          is_enabled: p.is_enabled,
                          has_key: p.has_key,
                      }))
                    : [],
                mcp_server: {
                    uptime_minutes: metricsCollector.getUptimeMinutes(),
                    node_version: process.version,
                },
                metrics: metricsCollector.getSummary(params.verbose),
            };

            return {
                content: [
                    {
                        type: "text" as const,
                        text: JSON.stringify(report, null, 2),
                    },
                ],
            };
        },
    },

    // ── settings_get ──────────────────────────────────────────────────
    settings_get: {
        schema: z
            .object({
                key: z
                    .string()
                    .optional()
                    .describe(
                        "Optional setting key. If provided, returns just that setting.",
                    ),
            })
            .strict(),
        handler: async (params): Promise<ToolResult> => {
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
    },

    // ── settings_update ───────────────────────────────────────────────
    settings_update: {
        schema: z
            .object({
                settings: z
                    .record(z.string())
                    .describe(
                        'Key-value map of settings to update. Example: {"theme": "dark"}',
                    ),
            })
            .strict(),
        handler: async (params): Promise<ToolResult> => {
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
    },

    // ── confirm_token ─────────────────────────────────────────────────
    confirm_token: {
        schema: z
            .object({
                tool_action: z
                    .string()
                    .describe(
                        "Tool name of the destructive action (e.g. delete_trade)",
                    ),
                params_summary: z
                    .string()
                    .describe(
                        "Human-readable summary of what will be done",
                    ),
            })
            .strict(),
        handler: async (params): Promise<ToolResult> => {
            try {
                const result = createConfirmationToken(params.tool_action);
                return {
                    content: [
                        {
                            type: "text" as const,
                            text: JSON.stringify({
                                token: result.token,
                                action: params.tool_action,
                                params_summary: params.params_summary,
                                expires_in_seconds: result.expires_in_seconds,
                                instruction: `Pass this token as 'confirmation_token' parameter to '${params.tool_action}' within ${result.expires_in_seconds} seconds.`,
                            }),
                        },
                    ],
                };
            } catch (err) {
                const message =
                    err instanceof Error ? err.message : "Unknown error";
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
    },

    // ── toolsets_list ──────────────────────────────────────────────────
    toolsets_list: {
        schema: z.object({}).strict(),
        handler: async (): Promise<ToolResult> => {
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
    },

    // ── toolset_describe ──────────────────────────────────────────────
    toolset_describe: {
        schema: z
            .object({
                toolset_name: z
                    .string()
                    .describe("Name of the toolset to describe"),
            })
            .strict(),
        handler: async (params): Promise<ToolResult> => {
            const ts = toolsetRegistry.get(params.toolset_name);
            if (!ts) {
                return {
                    content: [
                        {
                            type: "text" as const,
                            text: JSON.stringify({
                                success: false,
                                error: `Unknown toolset '${params.toolset_name}'. Use zorivest_system(action:"toolsets_list") to see all available toolsets.`,
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
    },

    // ── toolset_enable ────────────────────────────────────────────────
    toolset_enable: {
        schema: z
            .object({
                toolset_name: z
                    .string()
                    .describe("Name of the toolset to enable"),
            })
            .strict(),
        handler: async (params): Promise<ToolResult> => {
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

            const ts = toolsetRegistry.get(params.toolset_name);
            if (!ts) {
                return {
                    content: [
                        {
                            type: "text" as const,
                            text: JSON.stringify({
                                success: false,
                                error: `Unknown toolset '${params.toolset_name}'. Use zorivest_system(action:"toolsets_list") to see available toolsets.`,
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

            if (!toolsetRegistry.dynamicLoadingEnabled) {
                return {
                    content: [
                        {
                            type: "text" as const,
                            text: JSON.stringify({
                                success: false,
                                data: null,
                                error: `Dynamic tool loading is not supported by your IDE. Restart the MCP server with --toolsets ${params.toolset_name} to include this category.`,
                            }),
                        },
                    ],
                    isError: true,
                };
            }

            const handles = toolsetRegistry.getHandles(params.toolset_name);
            for (const handle of handles) {
                handle.enable();
            }
            toolsetRegistry.markLoaded(params.toolset_name);

            // Note: sendToolListChanged() needs server reference.
            // In compound tool registration, the server notifies via the
            // registerTool callback's server reference. The enable_toolset
            // handler stores a reference to the server for this purpose.
            // For now, we rely on the SDK auto-notification behavior.

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
    },

    // ── launch_gui ────────────────────────────────────────────────────
    launch_gui: {
        schema: z
            .object({
                wait_for_close: z
                    .boolean()
                    .default(false)
                    .describe("If true, blocks until GUI process exits"),
            })
            .strict(),
        handler: async (params): Promise<ToolResult> => {
            const discovery = await discoverGui();

            if (!discovery.found) {
                openReleasesPage();
                return {
                    content: [
                        {
                            type: "text" as const,
                            text: JSON.stringify({
                                gui_found: false,
                                method: "not-found",
                                message:
                                    "Zorivest GUI not found. Opening download page.",
                                setup_instructions: `Download the latest release from ${RELEASES_URL} and install it. Then try again.`,
                            }),
                        },
                    ],
                };
            }

            if (params.wait_for_close) {
                await launchAndWait(discovery.path);
            } else {
                launchDetached(discovery.path);
            }

            return {
                content: [
                    {
                        type: "text" as const,
                        text: JSON.stringify({
                            gui_found: true,
                            method: discovery.method,
                            message: `Zorivest GUI launched via ${discovery.method} method.`,
                        }),
                    },
                ],
            };
        },
    },

    // ── email_config ──────────────────────────────────────────────────
    email_config: {
        schema: z.object({}).strict(),
        handler: async (): Promise<ToolResult> => {
            const result = await fetchApi("/settings/email/status");
            return {
                content: [
                    { type: "text" as const, text: JSON.stringify(result) },
                ],
            };
        },
    },
});

// ── Server reference for toolset_enable notifications ──────────────────

// eslint-disable-next-line @typescript-eslint/no-unused-vars -- reserved for toolset_enable sendToolListChanged()
let serverRef: McpServer | null = null;

/**
 * Set the server reference for toolset_enable sendToolListChanged().
 * Called during registration.
 */
export function setSystemToolServer(server: McpServer): void {
    serverRef = server;
}

// ── Registration ───────────────────────────────────────────────────────

const SYSTEM_ACTIONS = [
    "diagnose",
    "settings_get",
    "settings_update",
    "confirm_token",
    "toolsets_list",
    "toolset_describe",
    "toolset_enable",
    "launch_gui",
    "email_config",
] as const;

/**
 * Register the zorivest_system compound tool.
 *
 * Uses registerTool() + z.object().strict() for top-level validation,
 * then CompoundToolRouter for per-action dispatch with strict sub-schemas.
 */
export function registerSystemTool(server: McpServer): RegisteredToolHandle[] {
    serverRef = server;

    const handle = server.registerTool(
        "zorivest_system",
        {
            description:
                "Zorivest system operations — diagnostics, settings, discovery, GUI launch, " +
                "confirmation tokens, and email configuration. " +
                "\\n\\nDiscovery workflow: toolsets_list → toolset_describe → toolset_enable. " +
                "Use toolsets_list first to see available toolset groups and their loaded status, " +
                "then toolset_describe to inspect tools within a group, then toolset_enable to activate deferred toolsets. " +
                "\\n\\nConfirmation tokens: Use confirm_token to generate a single-use 60s token before calling any destructive action " +
                "(trade delete, account delete, policy delete, template delete). " +
                "\\n\\nPrerequisite: diagnose, settings_get, email_config require the backend API to be running. " +
                "Discovery actions (toolsets_list, toolset_describe, toolset_enable) work without the API. " +
                "Returns: JSON with action-specific data. diagnose returns { backend, version, database, guard, providers, mcp_server, metrics }. " +
                `Actions: ${SYSTEM_ACTIONS.join(", ")}`,
            inputSchema: z
                .object({
                    action: z.enum(SYSTEM_ACTIONS).describe(
                        "System action to perform",
                    ),
                    // Per-action optional fields — validated strictly by router
                    verbose: z.boolean().optional(),
                    key: z.string().optional(),
                    settings: z.record(z.string()).optional(),
                    tool_action: z.string().optional(),
                    params_summary: z.string().optional(),
                    toolset_name: z.string().optional(),
                    wait_for_close: z.boolean().optional(),
                })
                .strict(),
            annotations: {
                readOnlyHint: false,
                destructiveHint: false,
                idempotentHint: false,
                openWorldHint: false,
            },
            _meta: {
                toolset: "core",
                alwaysLoaded: true,
            },
        },
        async (params) => {
            return systemRouter.dispatch(
                params.action,
                params as unknown as Record<string, unknown>,
            );
        },
    );

    return [handle];
}
