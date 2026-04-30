/**
 * CI gate test — enforces 13-tool registry ceiling.
 *
 * MC4 AC-4.17: CI gate that prevents tool creep above 13 registered tools.
 * MC4 AC-4.18: Empirical verification of tools/list counts under different
 *              toolset configurations (defaults, data, all, ops dynamic enable).
 *
 * Source: implementation-plan.md MC4
 * Phase: P2.5f (MCP Tool Consolidation)
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { InMemoryTransport } from "@modelcontextprotocol/sdk/inMemory.js";
import { ToolsetRegistry } from "../src/toolsets/registry.js";
import { seedRegistry, TOOLSET_DEFINITIONS } from "../src/toolsets/seed.js";
import { registerAllToolsets, applyModeFilter } from "../src/registration.js";
import type { ToolsetSelection } from "../src/cli.js";

// ── Helpers ────────────────────────────────────────────────────────────

/** Create a connected server+client pair with real toolset registration */
async function createConfiguredPair(
    selection: ToolsetSelection,
): Promise<{ client: Client; registry: ToolsetRegistry }> {
    const server = new McpServer({
        name: "zorivest-gate-test",
        version: "0.1.0",
    });

    const registry = new ToolsetRegistry();
    seedRegistry(registry);
    registerAllToolsets(server, registry);

    // Apply the mode filter synchronously — same as oninitialized callback
    applyModeFilter(registry, "dynamic", selection);

    const [clientTransport, serverTransport] = InMemoryTransport.createLinkedPair();
    const client = new Client({ name: "gate-test-client", version: "0.1.0" });

    await Promise.all([
        client.connect(clientTransport),
        server.connect(serverTransport),
    ]);

    return { client, registry };
}

// ── 1. CI gate: total tool count ≤ 13 ─────────────────────────────────

describe("tool-count CI gate", () => {
    it("total registered tools ≤ 13 (all toolsets loaded)", async () => {
        const { client } = await createConfiguredPair({ kind: "all" });
        const { tools } = await client.listTools();

        expect(tools.length).toBeLessThanOrEqual(13);
        expect(tools.length).toBe(13);
    });

    it("seed definitions contain exactly 4 toolsets", () => {
        expect(TOOLSET_DEFINITIONS).toHaveLength(4);
        const names = TOOLSET_DEFINITIONS.map((d) => d.name);
        expect(names).toEqual(["core", "trade", "data", "ops"]);
    });

    it("seed definitions sum to exactly 13 tool entries", () => {
        const totalTools = TOOLSET_DEFINITIONS.reduce(
            (sum, d) => sum + d.tools.length,
            0,
        );
        expect(totalTools).toBe(13);
    });
});

// ── 2. Empirical tools/list counts per configuration ──────────────────

describe("empirical tools/list counts", () => {
    beforeEach(() => {
        vi.restoreAllMocks();
    });

    it("defaults selection: core(1) + trade(3) = 4 tools visible", async () => {
        const { client } = await createConfiguredPair({ kind: "defaults" });
        const { tools } = await client.listTools();

        // core (always loaded): zorivest_system = 1
        // trade (isDefault: true): zorivest_trade, zorivest_analytics, zorivest_report = 3
        // data (deferred, not default): not loaded
        // ops (deferred, not default): not loaded
        expect(tools.length).toBe(4);
        expect(tools.map((t) => t.name).sort()).toEqual([
            "zorivest_analytics",
            "zorivest_report",
            "zorivest_system",
            "zorivest_trade",
        ]);
    });

    it("explicit data selection: core(1) + data(5) = 6 tools visible", async () => {
        const { client } = await createConfiguredPair({
            kind: "explicit",
            names: ["data"],
        });
        const { tools } = await client.listTools();

        // core (always loaded): 1
        // data (explicit): zorivest_account, zorivest_market, zorivest_watchlist, zorivest_import, zorivest_tax = 5
        expect(tools.length).toBe(6);
        expect(tools.some((t) => t.name === "zorivest_account")).toBe(true);
        expect(tools.some((t) => t.name === "zorivest_market")).toBe(true);
        expect(tools.some((t) => t.name === "zorivest_watchlist")).toBe(true);
        expect(tools.some((t) => t.name === "zorivest_import")).toBe(true);
        expect(tools.some((t) => t.name === "zorivest_tax")).toBe(true);
    });

    it("all selection: 13 tools visible", async () => {
        const { client } = await createConfiguredPair({ kind: "all" });
        const { tools } = await client.listTools();

        expect(tools.length).toBe(13);
    });

    it("explicit ops selection: core(1) + ops(4) = 5 tools visible", async () => {
        const { client } = await createConfiguredPair({
            kind: "explicit",
            names: ["ops"],
        });
        const { tools } = await client.listTools();

        // core (always loaded): 1
        // ops (explicit): zorivest_policy, zorivest_template, zorivest_db, zorivest_plan = 4
        expect(tools.length).toBe(5);
        expect(tools.some((t) => t.name === "zorivest_system")).toBe(true);
        expect(tools.some((t) => t.name === "zorivest_policy")).toBe(true);
        expect(tools.some((t) => t.name === "zorivest_template")).toBe(true);
        expect(tools.some((t) => t.name === "zorivest_db")).toBe(true);
        expect(tools.some((t) => t.name === "zorivest_plan")).toBe(true);
    });

    it("dynamic toolset_enable(ops) after defaults: 4+4 = 8 tools visible", async () => {
        const { client, registry } = await createConfiguredPair({ kind: "defaults" });

        // Verify initial state: 4 tools (core + trade)
        const { tools: beforeTools } = await client.listTools();
        expect(beforeTools.length).toBe(4);

        // Simulate toolset_enable("ops") — enable handles and mark loaded
        const opsHandles = registry.getHandles("ops");
        for (const h of opsHandles) {
            h.enable();
        }
        registry.markLoaded("ops");

        // After enabling ops: 4 + 4 = 8
        const { tools: afterTools } = await client.listTools();
        expect(afterTools.length).toBe(8);
        expect(afterTools.some((t) => t.name === "zorivest_policy")).toBe(true);
        expect(afterTools.some((t) => t.name === "zorivest_template")).toBe(true);
        expect(afterTools.some((t) => t.name === "zorivest_db")).toBe(true);
        expect(afterTools.some((t) => t.name === "zorivest_plan")).toBe(true);
    });
});

// ── 3. Startup schema assertion ───────────────────────────────────────

describe("startup Zod shape assertion", () => {
    it("registerAllToolsets does NOT throw for valid seed definitions", () => {
        const server = new McpServer({ name: "test", version: "0.1.0" });
        const registry = new ToolsetRegistry();
        seedRegistry(registry);

        // Should complete without throwing
        expect(() => registerAllToolsets(server, registry)).not.toThrow();
    });
});
