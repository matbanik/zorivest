/**
 * Shared API client utilities for MCP tools.
 *
 * Provides auth bootstrap, header management, and fetch wrapper
 * for proxying MCP tool calls to the Python REST API.
 *
 * Source: 05-mcp-server.md §5.7, 04c-api-auth.md
 */

const API_BASE =
    process.env.ZORIVEST_API_URL ?? "http://127.0.0.1:17787/api/v1";

// ── Auth state ─────────────────────────────────────────────────────────

interface AuthState {
    sessionToken: string | null;
    role: string | null;
    expiresAt: number | null;
}

const authState: AuthState = {
    sessionToken: null,
    role: null,
    expiresAt: null,
};

/**
 * Bootstrap authentication with a pre-provisioned API key.
 *
 * Exchanges the key for a session token via POST /auth/unlock.
 * Does NOT create keys — key creation is admin-only (04c-api-auth.md §79).
 * Called once at MCP server startup with key from env (ZORIVEST_API_KEY).
 *
 * @param apiKey Pre-provisioned API key (e.g. "zrv_sk_...")
 */
export async function bootstrapAuth(apiKey: string): Promise<void> {
    const res = await fetch(`${API_BASE}/auth/unlock`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ api_key: apiKey }),
    });

    if (!res.ok) {
        const err = (await res.json()) as { detail?: unknown };
        const detail =
            typeof err.detail === "string"
                ? err.detail
                : JSON.stringify(err.detail ?? "unknown");
        throw new Error(`Auth failed (${res.status}): ${detail}`);
    }

    const data = (await res.json()) as {
        session_token: string;
        role: string;
        expires_in: number;
    };
    authState.sessionToken = data.session_token;
    authState.role = data.role;
    authState.expiresAt = Date.now() + data.expires_in * 1000;
}

/**
 * Returns auth headers for proxied REST API calls.
 * Throws if not yet authenticated via bootstrapAuth().
 */
export function getAuthHeaders(): Record<string, string> {
    if (!authState.sessionToken) {
        return {};
    }
    return { Authorization: `Bearer ${authState.sessionToken}` };
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
        ...getAuthHeaders(),
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
        ...getAuthHeaders(),
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
