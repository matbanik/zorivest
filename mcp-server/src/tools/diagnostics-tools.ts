/**
 * MCP tools — Zorivest Diagnostics
 *
 * Implements `zorivest_diagnose`: runtime diagnostics with safe-fetch pattern.
 * Returns backend health, DB status, guard state, provider availability,
 * and performance metrics. Never reveals API keys.
 *
 * Source: 05b-mcp-zorivest-diagnostics.md
 * MEU: 34 (mcp-diagnostics)
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import { getAuthHeaders } from "../utils/api-client.js";
import { metricsCollector } from "../middleware/metrics.js";
import type { RegisteredToolHandle } from "../toolsets/registry.js";

// ── Safe fetch utility ─────────────────────────────────────────────────

const API_BASE =
    process.env.ZORIVEST_API_URL ?? "http://localhost:8765/api/v1";

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

// ── Provider type (strip sensitive fields) ─────────────────────────────

interface RawProvider {
    name: string;
    is_enabled: boolean;
    has_key: boolean;
    api_key?: string;
    [key: string]: unknown;
}

// ── Tool registration ──────────────────────────────────────────────────

export function registerDiagnosticsTools(server: McpServer): RegisteredToolHandle[] {
    const handles: RegisteredToolHandle[] = [];
    handles.push(server.registerTool(
        "zorivest_diagnose",
        {
            description:
                "Runtime diagnostics. Returns backend health, DB status, guard state, provider availability, and performance metrics. Never reveals API keys.",
            inputSchema: {
                verbose: z
                    .boolean()
                    .default(false)
                    .describe(
                        "Include per-tool latency percentiles (p50/p95/p99) and payload sizes",
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
        async ({ verbose }) => {
            const authHeaders = getAuthHeaders();

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
                        recent_calls_1min: guardData.recent_calls_1min ?? 0,
                        recent_calls_1hr: guardData.recent_calls_1hr ?? 0,
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
                metrics: metricsCollector.getSummary(verbose),
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
    ));
    return handles;
}
