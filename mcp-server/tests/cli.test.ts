/**
 * Unit tests for CLI toolset selection parsing.
 *
 * Tests verify: parseToolsets() returns correct ToolsetSelection tagged union
 * for --toolsets flag variations, env var config, and defaults.
 *
 * Source: §5.11 L754-769, FIC AC-1, AC-2
 * MEU: 42 (toolset-registry)
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

// Module under test — will fail until implemented
import { parseToolsets, type ToolsetSelection } from "../src/cli.js";

describe("parseToolsets", () => {
    const originalArgv = process.argv;
    const originalEnv = { ...process.env };

    beforeEach(() => {
        process.argv = ["node", "index.js"];
        delete process.env.ZORIVEST_TOOLSET_CONFIG;
    });

    afterEach(() => {
        process.argv = originalArgv;
        process.env = originalEnv;
    });

    // AC-1: --toolsets all
    it("returns { kind: 'all' } when --toolsets all is passed", () => {
        process.argv = ["node", "index.js", "--toolsets", "all"];
        const result = parseToolsets();
        expect(result).toEqual({ kind: "all" });
    });

    // AC-1: --toolsets with explicit names
    it("returns { kind: 'explicit', names } when --toolsets has comma-separated names", () => {
        process.argv = [
            "node",
            "index.js",
            "--toolsets",
            "trade-analytics,tax",
        ];
        const result = parseToolsets();
        expect(result).toEqual({
            kind: "explicit",
            names: ["trade-analytics", "tax"],
        });
    });

    // AC-1: single toolset name
    it("handles single toolset name without comma", () => {
        process.argv = ["node", "index.js", "--toolsets", "core"];
        const result = parseToolsets();
        expect(result).toEqual({ kind: "explicit", names: ["core"] });
    });

    // AC-1: defaults when no --toolsets flag
    it("returns { kind: 'defaults' } when no --toolsets flag is present", () => {
        process.argv = ["node", "index.js"];
        const result = parseToolsets();
        expect(result).toEqual({ kind: "defaults" });
    });

    // AC-1: core and discovery always loaded regardless
    it("type ToolsetSelection has kind discriminant", () => {
        const sel: ToolsetSelection = { kind: "defaults" };
        expect(sel.kind).toBe("defaults");

        const all: ToolsetSelection = { kind: "all" };
        expect(all.kind).toBe("all");

        const explicit: ToolsetSelection = {
            kind: "explicit",
            names: ["tax"],
        };
        expect(explicit.kind).toBe("explicit");
    });

    // AC-2: ZORIVEST_TOOLSET_CONFIG env var (graceful fallback)
    it("falls back to defaults when ZORIVEST_TOOLSET_CONFIG points to missing file", () => {
        process.argv = ["node", "index.js"];
        process.env.ZORIVEST_TOOLSET_CONFIG = "/nonexistent/path.json";
        const result = parseToolsets();
        expect(result).toEqual({ kind: "defaults" });
    });

    // Edge: --toolsets flag takes precedence over config file
    it("--toolsets flag takes precedence over ZORIVEST_TOOLSET_CONFIG", () => {
        process.argv = ["node", "index.js", "--toolsets", "all"];
        process.env.ZORIVEST_TOOLSET_CONFIG = "/some/config.json";
        const result = parseToolsets();
        expect(result).toEqual({ kind: "all" });
    });
});
