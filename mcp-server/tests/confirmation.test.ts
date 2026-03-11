/**
 * Unit tests for confirmation middleware.
 *
 * Tests verify: withConfirmation() wraps destructive tools on static
 * clients with token check, passes through on dynamic/anthropic clients.
 * Token lifecycle: createConfirmationToken → withConfirmation round-trip.
 *
 * Source: §5.13 L877-889, §5.14 L964, FIC AC-8
 * MEU: 42 (toolset-registry)
 */

import { describe, it, expect, vi, beforeEach } from "vitest";

// Module under test
import {
    withConfirmation,
    setConfirmationMode,
    createConfirmationToken,
    isDestructiveTool,
} from "../src/middleware/confirmation.js";

describe("withConfirmation", () => {
    const mockHandler = vi.fn(async (_params: any, _extra: any) => ({
        content: [{ type: "text" as const, text: "success" }],
    }));

    beforeEach(() => {
        mockHandler.mockClear();
    });

    // AC-8: pass-through on dynamic clients
    describe("dynamic/anthropic mode (pass-through)", () => {
        beforeEach(() => {
            setConfirmationMode("dynamic");
        });

        it("passes through without requiring confirmation_token", async () => {
            const wrapped = withConfirmation("create_trade", mockHandler);
            const result = await wrapped(
                { exec_id: "test" },
                {} as any,
            );
            expect(mockHandler).toHaveBeenCalledOnce();
            expect(result.content[0].text).toBe("success");
        });
    });

    // AC-8: requires token on static clients
    describe("static mode (confirmation required)", () => {
        beforeEach(() => {
            setConfirmationMode("static");
        });

        it("rejects destructive tool without confirmation_token", async () => {
            const wrapped = withConfirmation(
                "zorivest_emergency_stop",
                mockHandler,
            );
            const result = await wrapped(
                { /* no confirmation_token */ },
                {} as any,
            );
            expect(mockHandler).not.toHaveBeenCalled();
            // Should return error indicating confirmation required
            const text = JSON.parse(result.content[0].text);
            expect(text.error).toBeDefined();
        });

        it("allows destructive tool with valid token from createConfirmationToken", async () => {
            const { token } = createConfirmationToken("zorivest_emergency_stop");
            const wrapped = withConfirmation(
                "zorivest_emergency_stop",
                mockHandler,
            );
            const result = await wrapped(
                { confirmation_token: token },
                {} as any,
            );
            expect(mockHandler).toHaveBeenCalledOnce();
        });

        it("rejects arbitrary truthy string as token", async () => {
            const wrapped = withConfirmation(
                "zorivest_emergency_stop",
                mockHandler,
            );
            const result = await wrapped(
                { confirmation_token: "arbitrary-string" },
                {} as any,
            );
            expect(mockHandler).not.toHaveBeenCalled();
            const text = JSON.parse(result.content[0].text);
            expect(text.error).toContain("Invalid or expired");
        });

        it("rejects token issued for a different action", async () => {
            const { token } = createConfirmationToken("create_trade");
            const wrapped = withConfirmation(
                "sync_broker", // different action!
                mockHandler,
            );
            const result = await wrapped(
                { confirmation_token: token },
                {} as any,
            );
            expect(mockHandler).not.toHaveBeenCalled();
            const text = JSON.parse(result.content[0].text);
            expect(text.error).toContain("Invalid or expired");
        });

        it("rejects token used a second time (single-use)", async () => {
            const { token } = createConfirmationToken("create_trade");
            const wrapped = withConfirmation("create_trade", mockHandler);

            // First use: should succeed
            await wrapped({ confirmation_token: token }, {} as any);
            expect(mockHandler).toHaveBeenCalledOnce();

            // Second use: should fail
            mockHandler.mockClear();
            const result = await wrapped({ confirmation_token: token }, {} as any);
            expect(mockHandler).not.toHaveBeenCalled();
            const text = JSON.parse(result.content[0].text);
            expect(text.error).toContain("Invalid or expired");
        });

        it("passes through for non-destructive tools even on static mode", async () => {
            const wrapped = withConfirmation(
                "list_trades",
                mockHandler,
            );
            const result = await wrapped(
                { /* no confirmation_token */ },
                {} as any,
            );
            expect(mockHandler).toHaveBeenCalledOnce();
        });
    });

    // AC-8: destructive tools list
    describe("destructive tools list", () => {
        const destructiveTools = [
            "zorivest_emergency_stop",
            "create_trade",
            "sync_broker",
            "disconnect_market_provider",
            "zorivest_service_restart",
        ];

        it.each(destructiveTools)(
            "%s requires confirmation on static clients",
            async (toolName) => {
                setConfirmationMode("static");
                const wrapped = withConfirmation(toolName, mockHandler);
                const result = await wrapped({}, {} as any);
                expect(mockHandler).not.toHaveBeenCalled();
            },
        );
    });
});

describe("createConfirmationToken", () => {
    it("generates a token starting with ctk_ prefix", () => {
        const { token, expires_in_seconds } = createConfirmationToken("create_trade");
        expect(token).toMatch(/^ctk_[0-9a-f]{32}$/);
        expect(expires_in_seconds).toBe(60);
    });

    it("throws for unknown destructive action", () => {
        expect(() => createConfirmationToken("list_trades")).toThrow(
            "Unknown destructive action",
        );
    });
});

describe("isDestructiveTool", () => {
    it("returns true for destructive tools", () => {
        expect(isDestructiveTool("create_trade")).toBe(true);
        expect(isDestructiveTool("sync_broker")).toBe(true);
    });

    it("returns false for non-destructive tools", () => {
        expect(isDestructiveTool("list_trades")).toBe(false);
        expect(isDestructiveTool("get_portfolio")).toBe(false);
    });
});
