/**
 * Shared API client utilities for MCP tools.
 *
 * Provides auth header management and fetch wrapper
 * for proxying MCP tool calls to the Python REST API.
 *
 * Auth lifecycle is delegated to TokenRefreshManager (MEU-PH14).
 * The module-level bootstrapAuth() and authState are removed —
 * all token management flows through the singleton manager.
 *
 * Source: 05-mcp-server.md §5.7, 04c-api-auth.md
 */

import { TokenRefreshManager } from "./token-refresh-manager.js";

const API_BASE =
    process.env.ZORIVEST_API_URL ?? "http://127.0.0.1:17787/api/v1";

// ── Auth headers ───────────────────────────────────────────────────────

/**
 * Returns auth headers for proxied REST API calls.
 *
 * Now async — delegates to TokenRefreshManager.getValidAccessToken().
 * Handles proactive token refresh transparently.
 *
 * Returns empty headers if the manager is not initialized
 * (graceful degradation for unauthenticated health checks etc.).
 */
export async function getAuthHeaders(): Promise<Record<string, string>> {
    try {
        const mgr = TokenRefreshManager.getInstance();
        const token = await mgr.getValidAccessToken();
        return { Authorization: `Bearer ${token}` };
    } catch {
        // Graceful degradation: return empty headers if auth not ready
        return {};
    }
}

// ── Result types ───────────────────────────────────────────────────────

export interface McpResult {
    success: boolean;
    data?: unknown;
    error?: string;
}

// ── Fetch wrapper ──────────────────────────────────────────────────────

/**
 * Fetch wrapper for proxied REST API calls.
 * Automatically includes auth headers and wraps response in McpResult envelope.
 */
export async function fetchApi(
    path: string,
    options: RequestInit = {},
): Promise<McpResult> {
    const url = `${API_BASE}${path}`;
    const headers: Record<string, string> = {
        ...(await getAuthHeaders()),
        ...(options.headers as Record<string, string> | undefined),
    };

    try {
        const res = await fetch(url, {
            ...options,
            headers,
        });

        if (!res.ok) {
            const body = await res.text();
            let detail: string = body;
            try {
                const parsed = JSON.parse(body) as { detail?: unknown };
                if (parsed.detail !== undefined) {
                    detail =
                        typeof parsed.detail === "string"
                            ? parsed.detail
                            : JSON.stringify(parsed.detail);
                }
            } catch {
                // use raw text
            }
            return { success: false, error: `${res.status}: ${detail}` };
        }

        // Handle 204 No Content
        if (res.status === 204) {
            return { success: true };
        }

        const data: unknown = await res.json();
        return { success: true, data };
    } catch (error) {
        const message =
            error instanceof Error ? error.message : "Unknown fetch error";
        return { success: false, error: message };
    }
}

// ── Binary fetch wrapper ───────────────────────────────────────────────

/**
 * Result type for binary fetch operations (e.g. image downloads).
 */
export interface BinaryResult {
    success: boolean;
    base64?: string;
    mimeType?: string;
    error?: string;
}

/**
 * Fetch wrapper for endpoints that return raw binary data (e.g. image/webp).
 * Converts response to base64 for MCP image content type.
 */
export async function fetchApiBinary(
    path: string,
    options: RequestInit = {},
): Promise<BinaryResult> {
    const url = `${API_BASE}${path}`;
    const headers: Record<string, string> = {
        ...(await getAuthHeaders()),
        ...(options.headers as Record<string, string> | undefined),
    };

    try {
        const res = await fetch(url, {
            ...options,
            headers,
        });

        if (!res.ok) {
            const body = await res.text();
            return { success: false, error: `${res.status}: ${body}` };
        }

        const buffer = await res.arrayBuffer();
        const base64 = Buffer.from(buffer).toString("base64");
        const mimeType =
            res.headers.get("content-type") ?? "application/octet-stream";

        return { success: true, base64, mimeType };
    } catch (error) {
        const message =
            error instanceof Error ? error.message : "Unknown fetch error";
        return { success: false, error: message };
    }
}

export { API_BASE };
