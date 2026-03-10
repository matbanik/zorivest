/**
 * Unit tests for MCP guard middleware.
 *
 * Tests verify guardCheck() REST call and withGuard() HOF wrapper:
 * allow, block (locked), block (rate limit), and fail-closed on network error.
 *
 * Source: 05-mcp-server.md §5.6, FIC AC-1 through AC-5
 * MEU: 38 (mcp-guard)
 */

import { describe, it, expect, vi, beforeEach } from "vitest";

import { guardCheck, withGuard } from "../src/middleware/mcp-guard.js";

// ── guardCheck unit tests ──────────────────────────────────────────────

describe("guardCheck", () => {
    beforeEach(() => {
        vi.restoreAllMocks();
    });

    // AC-1: calls POST /mcp-guard/check with auth headers
    it("calls POST /mcp-guard/check and returns result", async () => {
        vi.stubGlobal(
            "fetch",
            vi.fn().mockResolvedValue({
                ok: true,
                json: () => Promise.resolve({ allowed: true }),
            }),
        );

        const result = await guardCheck();

        expect(result.allowed).toBe(true);
        expect(fetch).toHaveBeenCalledWith(
            expect.stringContaining("/mcp-guard/check"),
            expect.objectContaining({ method: "POST" }),
        );
    });

    // AC-5: network failure → fail-closed
    it("returns blocked on network failure (fail-closed)", async () => {
        vi.stubGlobal(
            "fetch",
            vi.fn().mockRejectedValue(new Error("ECONNREFUSED")),
        );

        const result = await guardCheck();

        expect(result.allowed).toBe(false);
        expect(result.reason).toContain("network");
    });
});

// ── withGuard HOF tests ────────────────────────────────────────────────

describe("withGuard", () => {
    beforeEach(() => {
        vi.restoreAllMocks();
    });

    // AC-2: passes through when allowed
    it("allows tool execution when guard returns allowed=true", async () => {
        vi.stubGlobal(
            "fetch",
            vi.fn().mockResolvedValue({
                ok: true,
                json: () => Promise.resolve({ allowed: true }),
            }),
        );

        const handler = withGuard(async () => ({
            content: [{ type: "text" as const, text: "ok" }],
        }));
        const result = await handler({});
        expect(result.content[0].text).toBe("ok");
    });

    // AC-3: blocks when locked, with reason
    it("blocks tool execution when guard is locked", async () => {
        vi.stubGlobal(
            "fetch",
            vi.fn().mockResolvedValue({
                ok: true,
                json: () =>
                    Promise.resolve({ allowed: false, reason: "manual" }),
            }),
        );

        const handler = withGuard(async () => ({
            content: [{ type: "text" as const, text: "ok" }],
        }));
        const result = await handler({});
        expect(result.isError).toBe(true);
        expect(result.content[0].text).toContain("MCP guard blocked");
        expect(result.content[0].text).toContain("manual");
    });

    // AC-3: blocks when rate limit exceeded
    it("blocks tool execution when rate limit exceeded", async () => {
        vi.stubGlobal(
            "fetch",
            vi.fn().mockResolvedValue({
                ok: true,
                json: () =>
                    Promise.resolve({
                        allowed: false,
                        reason: "rate_limit_exceeded",
                    }),
            }),
        );

        const handler = withGuard(async () => ({
            content: [{ type: "text" as const, text: "ok" }],
        }));
        const result = await handler({});
        expect(result.isError).toBe(true);
        expect(result.content[0].text).toContain("rate_limit_exceeded");
    });

    // AC-4: error message includes unlock guidance
    it("includes unlock guidance in error message", async () => {
        vi.stubGlobal(
            "fetch",
            vi.fn().mockResolvedValue({
                ok: true,
                json: () =>
                    Promise.resolve({ allowed: false, reason: "manual" }),
            }),
        );

        const handler = withGuard(async () => ({
            content: [{ type: "text" as const, text: "ok" }],
        }));
        const result = await handler({});
        expect(result.content[0].text).toContain("zorivest_emergency_unlock");
    });

    // AC-5: network failure → blocks (fail-closed)
    it("blocks on network failure (fail-closed safety)", async () => {
        vi.stubGlobal(
            "fetch",
            vi.fn().mockRejectedValue(new Error("ECONNREFUSED")),
        );

        const handler = withGuard(async () => ({
            content: [{ type: "text" as const, text: "ok" }],
        }));
        const result = await handler({});
        expect(result.isError).toBe(true);
        expect(result.content[0].text).toContain("MCP guard blocked");
    });
});
