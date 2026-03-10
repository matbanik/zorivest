/**
 * MCP Guard middleware — circuit breaker for MCP tool access.
 *
 * Provides guardCheck() to call the Python REST API guard endpoint,
 * and withGuard() HOF to wrap tool handlers with guard enforcement.
 *
 * Guard bypass: Unguarded tools (zorivest_diagnose, zorivest_emergency_stop,
 * zorivest_emergency_unlock, zorivest_launch_gui) are NOT wrapped with
 * withGuard — they remain callable even when the guard is locked.
 *
 * Source: 05-mcp-server.md §5.6
 * MEU: 38 (mcp-guard)
 */

import { getAuthHeaders } from "../utils/api-client.js";

const API_BASE =
    process.env.ZORIVEST_API_URL ?? "http://localhost:8765/api/v1";

// ── Types ──────────────────────────────────────────────────────────────

interface GuardCheckResult {
    allowed: boolean;
    reason?: string;
}

import type { CallToolResult } from "@modelcontextprotocol/sdk/types.js";

// ── guardCheck ─────────────────────────────────────────────────────────

/**
 * Lightweight guard check call to the Python REST API.
 * Called before each guarded tool execution.
 *
 * Fail-closed: if the network call fails, returns blocked as a safety default.
 * This prevents tool execution when the backend is unreachable.
 */
export async function guardCheck(): Promise<GuardCheckResult> {
    try {
        const res = await fetch(`${API_BASE}/mcp-guard/check`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                ...getAuthHeaders(),
            },
        });
        return (await res.json()) as GuardCheckResult;
    } catch {
        // Fail-closed: block tool execution when guard is unreachable
        return {
            allowed: false,
            reason: "Guard check failed (network error). Backend may be unreachable.",
        };
    }
}

// ── withGuard HOF ──────────────────────────────────────────────────────

/**
 * Wraps an MCP tool handler with guard check.
 * If guard denies, returns MCP error content instead of executing.
 *
 * @param handler - MCP tool handler function
 */
export function withGuard<T>(
    handler: (args: T, extra: unknown) => Promise<CallToolResult>,
): (args: T, extra: unknown) => Promise<CallToolResult> {
    return async (args: T, extra: unknown) => {
        const check = await guardCheck();
        if (!check.allowed) {
            return {
                content: [
                    {
                        type: "text" as const,
                        text: `⛔ MCP guard blocked this call: ${check.reason}. Unlock via GUI → Settings → MCP Guard, or via zorivest_emergency_unlock tool.`,
                    },
                ],
                isError: true,
            };
        }
        return handler(args, extra);
    };
}
