/**
 * FIC tests for TokenRefreshManager (MEU-PH14).
 *
 * Covers AC-1 through AC-10. Written BEFORE implementation (TDD Red phase).
 * All tests must FAIL until the manager is implemented.
 *
 * Source: implementation-plan.md §MEU-PH14
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

// ── AC-1: Singleton + ITokenProvider interface ─────────────────────────

describe("AC-1: Singleton + ITokenProvider", () => {
    it("exports a singleton getInstance() that returns the same instance", async () => {
        const { TokenRefreshManager } = await import(
            "../src/utils/token-refresh-manager.js"
        );
        const a = TokenRefreshManager.getInstance();
        const b = TokenRefreshManager.getInstance();
        expect(a).toBe(b);
    });

    it("getValidAccessToken() returns a Promise<string>", async () => {
        const { TokenRefreshManager } = await import(
            "../src/utils/token-refresh-manager.js"
        );
        const mgr = TokenRefreshManager.getInstance();
        // Must be a function returning a promise — will reject without init,
        // but we verify the interface shape
        expect(typeof mgr.getValidAccessToken).toBe("function");
    });
});

// ── AC-2: Proactive expiry with 30s skew ───────────────────────────────

describe("AC-2: Proactive expiry (30s skew)", () => {
    beforeEach(() => {
        vi.useFakeTimers();
    });
    afterEach(() => {
        vi.useRealTimers();
        vi.restoreAllMocks();
    });

    it("triggers refresh when token has ≤30s remaining", async () => {
        const { TokenRefreshManager } = await import(
            "../src/utils/token-refresh-manager.js"
        );

        // Reset singleton for test isolation
        TokenRefreshManager.resetForTesting();

        const mockFetch = vi.fn().mockResolvedValue({
            ok: true,
            json: async () => ({
                session_token: "tok_fresh",
                role: "admin",
                expires_in: 3600,
            }),
        });
        vi.stubGlobal("fetch", mockFetch);

        const mgr = TokenRefreshManager.getInstance();
        mgr.initialize("test-api-key");

        // First call — bootstraps
        await mgr.getValidAccessToken();
        expect(mockFetch).toHaveBeenCalledTimes(1);

        // Advance to 29s before expiry (3600s - 29s = 3571s)
        vi.advanceTimersByTime(3571 * 1000);

        // Second call — should trigger refresh (29s < 30s skew)
        await mgr.getValidAccessToken();
        expect(mockFetch).toHaveBeenCalledTimes(2);
    });

    it("does NOT refresh when token has >30s remaining", async () => {
        const { TokenRefreshManager } = await import(
            "../src/utils/token-refresh-manager.js"
        );

        TokenRefreshManager.resetForTesting();

        const mockFetch = vi.fn().mockResolvedValue({
            ok: true,
            json: async () => ({
                session_token: "tok_valid",
                role: "admin",
                expires_in: 3600,
            }),
        });
        vi.stubGlobal("fetch", mockFetch);

        const mgr = TokenRefreshManager.getInstance();
        mgr.initialize("test-api-key");

        // First call — bootstraps
        await mgr.getValidAccessToken();
        expect(mockFetch).toHaveBeenCalledTimes(1);

        // Advance to 31s before expiry (3600s - 31s = 3569s)
        vi.advanceTimersByTime(3569 * 1000);

        // Second call — should NOT refresh (31s > 30s skew)
        await mgr.getValidAccessToken();
        expect(mockFetch).toHaveBeenCalledTimes(1);
    });
});

// ── AC-3: Promise coalescing (N concurrent → 1 fetch) ──────────────────

describe("AC-3: Promise coalescing", () => {
    beforeEach(() => {
        vi.useFakeTimers();
    });
    afterEach(() => {
        vi.useRealTimers();
        vi.restoreAllMocks();
    });

    it("10 concurrent getValidAccessToken() calls produce exactly 1 fetch", async () => {
        const { TokenRefreshManager } = await import(
            "../src/utils/token-refresh-manager.js"
        );

        TokenRefreshManager.resetForTesting();

        let resolveAuth: ((v: Response) => void) | null = null;
        const mockFetch = vi.fn().mockImplementation(
            () =>
                new Promise<Response>((resolve) => {
                    resolveAuth = resolve;
                }),
        );
        vi.stubGlobal("fetch", mockFetch);

        const mgr = TokenRefreshManager.getInstance();
        mgr.initialize("test-api-key");

        // Launch 10 concurrent calls
        const promises = Array.from({ length: 10 }, () =>
            mgr.getValidAccessToken(),
        );

        // Resolve the single auth call
        resolveAuth!({
            ok: true,
            json: async () => ({
                session_token: "tok_shared",
                role: "admin",
                expires_in: 3600,
            }),
        } as Response);

        const results = await Promise.all(promises);

        // Exactly 1 fetch call
        expect(mockFetch).toHaveBeenCalledTimes(1);

        // All 10 got the same token (AC-4)
        for (const token of results) {
            expect(token).toBe("tok_shared");
        }
    });
});

// ── AC-4: All waiters receive same token (covered by AC-3 test above) ──

describe("AC-4: All waiters receive same token", () => {
    afterEach(() => {
        vi.restoreAllMocks();
    });

    it("concurrent callers all resolve to identical token value", async () => {
        const { TokenRefreshManager } = await import(
            "../src/utils/token-refresh-manager.js"
        );

        TokenRefreshManager.resetForTesting();

        const mockFetch = vi.fn().mockResolvedValue({
            ok: true,
            json: async () => ({
                session_token: "tok_identical",
                role: "admin",
                expires_in: 3600,
            }),
        });
        vi.stubGlobal("fetch", mockFetch);

        const mgr = TokenRefreshManager.getInstance();
        mgr.initialize("test-api-key");

        const [t1, t2, t3] = await Promise.all([
            mgr.getValidAccessToken(),
            mgr.getValidAccessToken(),
            mgr.getValidAccessToken(),
        ]);

        expect(t1).toBe("tok_identical");
        expect(t2).toBe("tok_identical");
        expect(t3).toBe("tok_identical");
    });
});

// ── AC-5: Failure clears in-flight + propagates; next call retries ─────

describe("AC-5: Failure propagation + recovery", () => {
    afterEach(() => {
        vi.restoreAllMocks();
    });

    it("refresh failure propagates to all waiters, next call retries", async () => {
        const { TokenRefreshManager } = await import(
            "../src/utils/token-refresh-manager.js"
        );

        TokenRefreshManager.resetForTesting();

        let callCount = 0;
        const mockFetch = vi.fn().mockImplementation(async () => {
            callCount++;
            if (callCount === 1) {
                // First call fails
                return {
                    ok: false,
                    status: 500,
                    json: async () => ({ detail: "server error" }),
                };
            }
            // Second call succeeds
            return {
                ok: true,
                json: async () => ({
                    session_token: "tok_recovered",
                    role: "admin",
                    expires_in: 3600,
                }),
            };
        });
        vi.stubGlobal("fetch", mockFetch);

        const mgr = TokenRefreshManager.getInstance();
        mgr.initialize("test-api-key");

        // First call should fail
        await expect(mgr.getValidAccessToken()).rejects.toThrow();

        // Second call should retry (not stuck on rejected promise)
        const token = await mgr.getValidAccessToken();
        expect(token).toBe("tok_recovered");
        expect(mockFetch).toHaveBeenCalledTimes(2);
    });
});

// ── AC-6: Sequential calls reuse valid token ───────────────────────────

describe("AC-6: Sequential reuse without re-auth", () => {
    afterEach(() => {
        vi.restoreAllMocks();
    });

    it("two sequential calls with valid token produce 0 refresh calls", async () => {
        const { TokenRefreshManager } = await import(
            "../src/utils/token-refresh-manager.js"
        );

        TokenRefreshManager.resetForTesting();

        const mockFetch = vi.fn().mockResolvedValue({
            ok: true,
            json: async () => ({
                session_token: "tok_reused",
                role: "admin",
                expires_in: 3600,
            }),
        });
        vi.stubGlobal("fetch", mockFetch);

        const mgr = TokenRefreshManager.getInstance();
        mgr.initialize("test-api-key");

        // First call — initial auth
        const t1 = await mgr.getValidAccessToken();
        expect(mockFetch).toHaveBeenCalledTimes(1);

        // Second call — should reuse (3600s remaining > 30s skew)
        const t2 = await mgr.getValidAccessToken();
        expect(mockFetch).toHaveBeenCalledTimes(1); // No additional call
        expect(t1).toBe(t2);
    });
});

// ── AC-7: No direct bootstrapAuth imports in compound tools ────────────
// (This is a grep-based check, not a unit test — covered by V6 validation command)

// ── AC-8: fetchApi/fetchApiBinary delegate to TokenRefreshManager ──────

describe("AC-8: fetchApi uses TokenRefreshManager", () => {
    afterEach(() => {
        vi.restoreAllMocks();
    });

    it("getAuthHeaders() returns Authorization header from manager", async () => {
        const { TokenRefreshManager } = await import(
            "../src/utils/token-refresh-manager.js"
        );

        TokenRefreshManager.resetForTesting();

        const mockFetch = vi.fn().mockResolvedValue({
            ok: true,
            json: async () => ({
                session_token: "tok_auth_header",
                role: "admin",
                expires_in: 3600,
            }),
        });
        vi.stubGlobal("fetch", mockFetch);

        const mgr = TokenRefreshManager.getInstance();
        mgr.initialize("test-api-key");

        // Import getAuthHeaders AFTER manager init
        const { getAuthHeaders } = await import(
            "../src/utils/api-client.js"
        );

        const headers = await getAuthHeaders();
        expect(headers).toEqual({
            Authorization: "Bearer tok_auth_header",
        });
    });
});

// ── AC-9: Existing tests continue to pass (regression) ────────────────
// (Covered by V4 — full vitest run)

// ── AC-10: Integration proof — sentinel token in all call sites ────────

describe("AC-10: Integration proof — sentinel token propagation", () => {
    afterEach(() => {
        vi.restoreAllMocks();
    });

    it("fetchApi() includes manager token in Authorization header", async () => {
        const { TokenRefreshManager } = await import(
            "../src/utils/token-refresh-manager.js"
        );

        TokenRefreshManager.resetForTesting();

        // Mock: manager auth returns sentinel
        const managerFetch = vi.fn();
        // First call = auth unlock → sentinel token
        managerFetch.mockResolvedValueOnce({
            ok: true,
            json: async () => ({
                session_token: "SENTINEL_TOKEN_AC10",
                role: "admin",
                expires_in: 3600,
            }),
        });
        // Second call = the actual fetchApi call
        managerFetch.mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: async () => ({ data: "test" }),
        });
        vi.stubGlobal("fetch", managerFetch);

        const mgr = TokenRefreshManager.getInstance();
        mgr.initialize("test-api-key");

        const { fetchApi } = await import("../src/utils/api-client.js");

        await fetchApi("/test-endpoint");

        // The second fetch call (actual API call) should have the sentinel
        const apiCallArgs = managerFetch.mock.calls[1];
        const apiHeaders = apiCallArgs[1]?.headers as Record<string, string>;
        expect(apiHeaders?.Authorization).toBe("Bearer SENTINEL_TOKEN_AC10");
    });

    it("fetchApiBinary() includes manager token in Authorization header", async () => {
        const { TokenRefreshManager } = await import(
            "../src/utils/token-refresh-manager.js"
        );

        TokenRefreshManager.resetForTesting();

        const managerFetch = vi.fn();
        // First call = auth unlock → sentinel token
        managerFetch.mockResolvedValueOnce({
            ok: true,
            json: async () => ({
                session_token: "SENTINEL_BINARY_AC10",
                role: "admin",
                expires_in: 3600,
            }),
        });
        // Second call = the actual fetchApiBinary call (binary response)
        managerFetch.mockResolvedValueOnce({
            ok: true,
            status: 200,
            headers: new Headers({ "content-type": "image/webp" }),
            arrayBuffer: async () => new ArrayBuffer(8),
        });
        vi.stubGlobal("fetch", managerFetch);

        const mgr = TokenRefreshManager.getInstance();
        mgr.initialize("test-api-key");

        const { fetchApiBinary } = await import("../src/utils/api-client.js");

        await fetchApiBinary("/screenshots/1");

        // The second fetch call (binary API call) should have the sentinel
        const apiCallArgs = managerFetch.mock.calls[1];
        const apiHeaders = apiCallArgs[1]?.headers as Record<string, string>;
        expect(apiHeaders?.Authorization).toBe("Bearer SENTINEL_BINARY_AC10");
    });

    it("guardCheck() includes manager token in Authorization header", async () => {
        const { TokenRefreshManager } = await import(
            "../src/utils/token-refresh-manager.js"
        );

        TokenRefreshManager.resetForTesting();

        const managerFetch = vi.fn();
        // First call = auth unlock → sentinel token
        managerFetch.mockResolvedValueOnce({
            ok: true,
            json: async () => ({
                session_token: "SENTINEL_GUARD_AC10",
                role: "admin",
                expires_in: 3600,
            }),
        });
        // Second call = the guard check POST
        managerFetch.mockResolvedValueOnce({
            ok: true,
            json: async () => ({ allowed: true }),
        });
        vi.stubGlobal("fetch", managerFetch);

        const mgr = TokenRefreshManager.getInstance();
        mgr.initialize("test-api-key");

        const { guardCheck } = await import("../src/middleware/mcp-guard.js");

        await guardCheck();

        // The second fetch call (guard check) should have the sentinel
        const guardCallArgs = managerFetch.mock.calls[1];
        const guardHeaders = guardCallArgs[1]?.headers as Record<string, string>;
        expect(guardHeaders?.Authorization).toBe("Bearer SENTINEL_GUARD_AC10");
    });

    it("startup initialization calls getValidAccessToken() via TokenRefreshManager", async () => {
        const { TokenRefreshManager } = await import(
            "../src/utils/token-refresh-manager.js"
        );

        TokenRefreshManager.resetForTesting();

        const managerFetch = vi.fn().mockResolvedValue({
            ok: true,
            json: async () => ({
                session_token: "SENTINEL_STARTUP_AC10",
                role: "admin",
                expires_in: 3600,
            }),
        });
        vi.stubGlobal("fetch", managerFetch);

        const mgr = TokenRefreshManager.getInstance();
        mgr.initialize("test-api-key");

        // Simulate startup sequence: initialize + eager token fetch
        const token = await mgr.getValidAccessToken();
        expect(token).toBe("SENTINEL_STARTUP_AC10");

        // The auth call should have been made to the unlock endpoint
        expect(managerFetch).toHaveBeenCalledTimes(1);
        const authCallArgs = managerFetch.mock.calls[0];
        const authUrl = authCallArgs[0] as string;
        expect(authUrl).toContain("/auth/unlock");
    });
});
