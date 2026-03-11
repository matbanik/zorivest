/**
 * Unit tests for adaptive client mode detection.
 *
 * Tests verify: detectClientMode() returns correct ClientMode based on
 * env var override, clientInfo.name pattern matching, and safe default.
 * Also tests getResponseFormat() and getServerInstructions().
 *
 * Source: §5.12 L787-838, §5.13 L846-875, FIC AC-3, AC-5, AC-6, AC-7
 * MEU: 42 (toolset-registry)
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";

// Module under test — will fail until implemented
import {
    detectClientMode,
    getResponseFormat,
    getServerInstructions,
    type ClientMode,
} from "../src/client-detection.js";

// ── Helpers ────────────────────────────────────────────────────────────

function createMockServer(clientName?: string): McpServer {
    const server = new McpServer({ name: "test", version: "0.0.1" });
    // Mock the inner server's getClientVersion to return a specific name
    if (clientName !== undefined) {
        vi.spyOn(server.server, "getClientVersion").mockReturnValue({
            name: clientName,
            version: "1.0.0",
        });
    } else {
        vi.spyOn(server.server, "getClientVersion").mockReturnValue(undefined);
    }
    return server;
}

describe("detectClientMode", () => {
    const originalEnv = { ...process.env };

    beforeEach(() => {
        delete process.env.ZORIVEST_CLIENT_MODE;
    });

    afterEach(() => {
        process.env = originalEnv;
    });

    // AC-3 Priority 1: env var override
    describe("env var override (priority 1)", () => {
        it("returns 'anthropic' when ZORIVEST_CLIENT_MODE=anthropic", () => {
            process.env.ZORIVEST_CLIENT_MODE = "anthropic";
            const server = createMockServer("some-unknown-client");
            expect(detectClientMode(server)).toBe("anthropic");
        });

        it("returns 'dynamic' when ZORIVEST_CLIENT_MODE=dynamic", () => {
            process.env.ZORIVEST_CLIENT_MODE = "dynamic";
            const server = createMockServer("cursor");
            expect(detectClientMode(server)).toBe("dynamic");
        });

        it("returns 'static' when ZORIVEST_CLIENT_MODE=static", () => {
            process.env.ZORIVEST_CLIENT_MODE = "static";
            const server = createMockServer("claude-code");
            expect(detectClientMode(server)).toBe("static");
        });
    });

    // AC-3 Priority 2: clientInfo.name pattern matching
    describe("clientInfo.name detection (priority 2)", () => {
        it("returns 'anthropic' for claude-code", () => {
            const server = createMockServer("claude-code");
            expect(detectClientMode(server)).toBe("anthropic");
        });

        it("returns 'anthropic' for claude-desktop", () => {
            const server = createMockServer("claude-desktop");
            expect(detectClientMode(server)).toBe("anthropic");
        });

        it("returns 'dynamic' for antigravity", () => {
            const server = createMockServer("antigravity");
            expect(detectClientMode(server)).toBe("dynamic");
        });

        it("returns 'dynamic' for cline", () => {
            const server = createMockServer("cline");
            expect(detectClientMode(server)).toBe("dynamic");
        });

        it("returns 'dynamic' for roo-code", () => {
            const server = createMockServer("roo-code");
            expect(detectClientMode(server)).toBe("dynamic");
        });

        it("returns 'dynamic' for gemini-cli", () => {
            const server = createMockServer("gemini-cli");
            expect(detectClientMode(server)).toBe("dynamic");
        });
    });

    // AC-3 Priority 3: static default (§5.12 L833)
    describe("static default (priority 3)", () => {
        it("returns 'static' for cursor", () => {
            const server = createMockServer("cursor");
            expect(detectClientMode(server)).toBe("static");
        });

        it("returns 'static' for windsurf", () => {
            const server = createMockServer("windsurf");
            expect(detectClientMode(server)).toBe("static");
        });

        it("returns 'static' for unknown client names", () => {
            const server = createMockServer("some-random-ide");
            expect(detectClientMode(server)).toBe("static");
        });

        it("returns 'static' when client version is undefined", () => {
            const server = createMockServer(undefined);
            expect(detectClientMode(server)).toBe("static");
        });
    });
});

// AC-5, AC-6: response format
describe("getResponseFormat", () => {
    it("returns 'detailed' or 'concise' as ResponseFormat type", () => {
        const format = getResponseFormat();
        expect(["detailed", "concise"]).toContain(format);
    });
});

// AC-7: server instructions
describe("getServerInstructions", () => {
    it("returns non-empty string with comprehensive instructions", () => {
        const instructions = getServerInstructions();
        expect(typeof instructions).toBe("string");
        expect(instructions.length).toBeGreaterThan(50);
    });

    it("mentions toolsets in instructions", () => {
        const instructions = getServerInstructions();
        expect(instructions.toLowerCase()).toContain("toolset");
    });
});
