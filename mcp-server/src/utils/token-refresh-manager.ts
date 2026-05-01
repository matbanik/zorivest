/**
 * TokenRefreshManager — singleton, concurrent-safe auth token provider.
 *
 * Resolves [MCP-AUTHRACE]: centralized token lifecycle with proactive
 * expiry (30s skew) and promise coalescing for concurrent deduplication.
 *
 * Design: Option A+B hybrid — in-process singleton implementing
 * ITokenProvider interface for future distributed replacement.
 *
 * Source: known-issues.md [MCP-AUTHRACE], implementation-plan.md §MEU-PH14
 */

// ── Interface ──────────────────────────────────────────────────────────

/**
 * Abstraction for token providers. The singleton manager implements this,
 * but the interface enables future distributed token providers (e.g.,
 * external token service, Redis-backed coordination).
 */
export interface ITokenProvider {
    getValidAccessToken(): Promise<string>;
}

// ── Constants ──────────────────────────────────────────────────────────

const API_BASE =
    process.env.ZORIVEST_API_URL ?? "http://127.0.0.1:17787/api/v1";

/** Proactive expiry skew — refresh this many ms before actual expiry. */
const EXPIRY_SKEW_MS = 30_000;

// ── TokenRefreshManager ────────────────────────────────────────────────

export class TokenRefreshManager implements ITokenProvider {
    private static instance: TokenRefreshManager | null = null;

    private apiKey: string | null = null;
    private sessionToken: string | null = null;
    private expiresAt: number = 0;
    private refreshPromise: Promise<string> | null = null;

    // Private constructor enforces singleton pattern
    private constructor() {}

    /**
     * Get the singleton instance. Creates one if it doesn't exist.
     */
    static getInstance(): TokenRefreshManager {
        if (!TokenRefreshManager.instance) {
            TokenRefreshManager.instance = new TokenRefreshManager();
        }
        return TokenRefreshManager.instance;
    }

    /**
     * Reset singleton for testing only. Clears all state.
     */
    static resetForTesting(): void {
        TokenRefreshManager.instance = null;
    }

    /**
     * Initialize the manager with the API key for re-authentication.
     * Must be called before getValidAccessToken().
     */
    initialize(apiKey: string): void {
        this.apiKey = apiKey;
        // Clear any stale state
        this.sessionToken = null;
        this.expiresAt = 0;
        this.refreshPromise = null;
    }

    /**
     * Get a valid access token, refreshing proactively if needed.
     *
     * Promise coalescing: if a refresh is already in-flight, all concurrent
     * callers share the same promise. On failure, the in-flight promise is
     * cleared via .finally() so subsequent calls can retry.
     */
    async getValidAccessToken(): Promise<string> {
        if (!this.apiKey) {
            throw new Error(
                "TokenRefreshManager not initialized. Call initialize(apiKey) first.",
            );
        }

        // Fast path: token is valid and not approaching expiry
        if (this.sessionToken && Date.now() + EXPIRY_SKEW_MS < this.expiresAt) {
            return this.sessionToken;
        }

        // Slow path: need refresh — deduplicate via promise coalescing
        if (!this.refreshPromise) {
            this.refreshPromise = this.doRefresh().finally(() => {
                // Clear in-flight promise regardless of success/failure
                // This prevents deadlock: failed refresh doesn't block future attempts
                this.refreshPromise = null;
            });
        }

        return this.refreshPromise;
    }

    /**
     * Perform the actual token refresh by calling POST /auth/unlock.
     * The stored API key is used as the credential.
     */
    private async doRefresh(): Promise<string> {
        const res = await fetch(`${API_BASE}/auth/unlock`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ api_key: this.apiKey }),
        });

        if (!res.ok) {
            const err = (await res.json()) as { detail?: unknown };
            const detail =
                typeof err.detail === "string"
                    ? err.detail
                    : JSON.stringify(err.detail ?? "unknown");
            throw new Error(`Auth refresh failed (${res.status}): ${detail}`);
        }

        const data = (await res.json()) as {
            session_token: string;
            role: string;
            expires_in: number;
        };

        this.sessionToken = data.session_token;
        this.expiresAt = Date.now() + data.expires_in * 1000;

        return this.sessionToken;
    }
}
