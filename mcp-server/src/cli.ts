/**
 * CLI toolset selection parsing.
 *
 * Parses --toolsets flag from process.argv and ZORIVEST_TOOLSET_CONFIG env var
 * to determine which toolsets to enable at startup.
 *
 * Source: 05-mcp-server.md §5.11 L754-769
 * MEU: 42 (toolset-registry)
 */

import { readFileSync, existsSync } from "node:fs";

// ── Types ──────────────────────────────────────────────────────────────

/**
 * Tagged union representing the user's toolset selection.
 *
 * - `all`:      --toolsets all — load every registered toolset
 * - `explicit`: --toolsets name1,name2 — load only named toolsets (+ core/discovery)
 * - `defaults`: no flag — load only default toolsets (+ core/discovery)
 */
export type ToolsetSelection =
    | { kind: "all" }
    | { kind: "explicit"; names: string[] }
    | { kind: "defaults" };

// ── Config file types ──────────────────────────────────────────────────

interface ToolsetConfig {
    defaultToolsets?: string[];
    /** Per-client toolset overrides. Deferred to MEU-42b — declared but not consumed. */
    clientOverrides?: Record<string, string[]>;
}

// ── Parser ─────────────────────────────────────────────────────────────

/**
 * Parse --toolsets from process.argv. Falls back to config file from
 * ZORIVEST_TOOLSET_CONFIG, then to { kind: 'defaults' }.
 */
export function parseToolsets(): ToolsetSelection {
    // 1. Check --toolsets flag
    const flagIdx = process.argv.indexOf("--toolsets");
    if (flagIdx !== -1 && flagIdx + 1 < process.argv.length) {
        const value = process.argv[flagIdx + 1];
        if (value === "all") {
            return { kind: "all" };
        }
        const names = value
            .split(",")
            .map((n) => n.trim())
            .filter(Boolean);
        if (names.length > 0) {
            return { kind: "explicit", names };
        }
    }

    // 2. Check ZORIVEST_TOOLSET_CONFIG env var
    const configPath = process.env.ZORIVEST_TOOLSET_CONFIG;
    if (configPath) {
        try {
            if (existsSync(configPath)) {
                const raw = readFileSync(configPath, "utf-8");
                const config: ToolsetConfig = JSON.parse(raw);
                if (
                    config.defaultToolsets &&
                    Array.isArray(config.defaultToolsets) &&
                    config.defaultToolsets.length > 0
                ) {
                    return {
                        kind: "explicit",
                        names: config.defaultToolsets,
                    };
                }
            }
        } catch {
            // Graceful fallback — file missing or invalid
        }
    }

    // 3. Default
    return { kind: "defaults" };
}
