/**
 * Unit tests for toolset registration orchestrator.
 *
 * Tests verify: registerAllToolsets() pre-connect registration and handle
 * storage, applyModeFilter() post-connect filtering for each selection kind.
 *
 * Source: §5.14 L893-933, FIC AC-4, AC-9, AC-10
 * MEU: 42 (toolset-registry)
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";

// Modules under test — will fail until implemented
import {
    registerAllToolsets,
    applyModeFilter,
} from "../src/registration.js";

import {
    ToolsetRegistry,
    type ToolsetDefinition,
} from "../src/toolsets/registry.js";

import type { ClientMode } from "../src/client-detection.js";
import type { ToolsetSelection } from "../src/cli.js";

// ── Helpers ────────────────────────────────────────────────────────────

/** Create a mock RegisteredTool handle */
function mockHandle() {
    return {
        enable: vi.fn(),
        disable: vi.fn(),
        update: vi.fn(),
        remove: vi.fn(),
    };
}

/** Create a minimal toolset definition with mock register callback */
function makeDef(
    name: string,
    opts: {
        alwaysLoaded?: boolean;
        isDefault?: boolean;
        loaded?: boolean;
    } = {},
): ToolsetDefinition {
    const handles = [mockHandle(), mockHandle()];
    return {
        name,
        description: `${name} toolset`,
        tools: [{ name: `${name}_tool`, description: `A ${name} tool` }],
        register: vi.fn(() => handles as any),
        loaded: opts.loaded ?? false,
        alwaysLoaded: opts.alwaysLoaded ?? false,
        isDefault: opts.isDefault ?? false,
    };
}

describe("registerAllToolsets", () => {
    let server: McpServer;
    let registry: ToolsetRegistry;

    beforeEach(() => {
        server = new McpServer({ name: "test", version: "0.0.1" });
        registry = new ToolsetRegistry();
    });

    // AC-4: registers ALL toolsets pre-connect
    it("calls register() on every toolset in the registry", () => {
        const core = makeDef("core", { alwaysLoaded: true });
        const trade = makeDef("trade-analytics", { isDefault: true });
        const tax = makeDef("tax");
        registry.register(core);
        registry.register(trade);
        registry.register(tax);

        registerAllToolsets(server, registry);

        expect(core.register).toHaveBeenCalledWith(server);
        expect(trade.register).toHaveBeenCalledWith(server);
        expect(tax.register).toHaveBeenCalledWith(server);
    });

    // AC-4: stores handles in registry
    it("stores returned handles in registry via storeHandles()", () => {
        const core = makeDef("core", { alwaysLoaded: true });
        registry.register(core);

        registerAllToolsets(server, registry);

        const handles = registry.getHandles("core");
        expect(handles).toBeDefined();
        expect(handles.length).toBe(2);
    });
});

describe("applyModeFilter", () => {
    let registry: ToolsetRegistry;

    beforeEach(() => {
        registry = new ToolsetRegistry();
    });

    // AC-4: 'all' selection enables everything
    it("enables all toolsets when selection is { kind: 'all' }", () => {
        const core = makeDef("core", { alwaysLoaded: true });
        const trade = makeDef("trade-analytics", { isDefault: true });
        const tax = makeDef("tax");
        registry.register(core);
        registry.register(trade);
        registry.register(tax);

        // Simulate handle storage
        registry.storeHandles("core", core.register(null as any));
        registry.storeHandles("trade-analytics", trade.register(null as any));
        registry.storeHandles("tax", tax.register(null as any));

        const selection: ToolsetSelection = { kind: "all" };
        applyModeFilter(registry, "dynamic", selection);

        // All should be marked loaded
        expect(registry.get("core")?.loaded).toBe(true);
        expect(registry.get("trade-analytics")?.loaded).toBe(true);
        expect(registry.get("tax")?.loaded).toBe(true);
    });

    // AC-4: 'explicit' enables named + alwaysLoaded
    it("disables non-named, non-alwaysLoaded toolsets for explicit selection", () => {
        const core = makeDef("core", { alwaysLoaded: true });
        const trade = makeDef("trade-analytics", { isDefault: true });
        const tax = makeDef("tax");
        registry.register(core);
        registry.register(trade);
        registry.register(tax);

        const coreHandles = [mockHandle(), mockHandle()];
        const tradeHandles = [mockHandle(), mockHandle()];
        const taxHandles = [mockHandle(), mockHandle()];
        registry.storeHandles("core", coreHandles as any);
        registry.storeHandles("trade-analytics", tradeHandles as any);
        registry.storeHandles("tax", taxHandles as any);

        const selection: ToolsetSelection = {
            kind: "explicit",
            names: ["trade-analytics"],
        };
        applyModeFilter(registry, "dynamic", selection);

        // core is alwaysLoaded — should remain enabled
        expect(registry.get("core")?.loaded).toBe(true);
        // trade-analytics is explicitly named — should remain enabled
        expect(registry.get("trade-analytics")?.loaded).toBe(true);
        // tax is NOT named and NOT alwaysLoaded — should be disabled
        expect(registry.get("tax")?.loaded).toBe(false);
        // tax handles should have disable() called
        expect(taxHandles[0].disable).toHaveBeenCalled();
        expect(taxHandles[1].disable).toHaveBeenCalled();
    });

    // AC-4: 'defaults' enables defaults + alwaysLoaded
    it("enables only default and alwaysLoaded toolsets for defaults selection", () => {
        const core = makeDef("core", { alwaysLoaded: true });
        const trade = makeDef("trade-analytics", { isDefault: true });
        const tax = makeDef("tax", { isDefault: false });
        registry.register(core);
        registry.register(trade);
        registry.register(tax);

        const coreHandles = [mockHandle()];
        const tradeHandles = [mockHandle()];
        const taxHandles = [mockHandle()];
        registry.storeHandles("core", coreHandles as any);
        registry.storeHandles("trade-analytics", tradeHandles as any);
        registry.storeHandles("tax", taxHandles as any);

        const selection: ToolsetSelection = { kind: "defaults" };
        applyModeFilter(registry, "dynamic", selection);

        expect(registry.get("core")?.loaded).toBe(true);
        expect(registry.get("trade-analytics")?.loaded).toBe(true);
        expect(registry.get("tax")?.loaded).toBe(false);
        expect(taxHandles[0].disable).toHaveBeenCalled();
    });

    // AC-4: static mode disables dynamicLoadingEnabled
    it("sets dynamicLoadingEnabled to false for static mode", () => {
        const core = makeDef("core", { alwaysLoaded: true });
        registry.register(core);
        registry.storeHandles("core", [mockHandle()] as any);

        const selection: ToolsetSelection = { kind: "defaults" };
        applyModeFilter(registry, "static", selection);

        expect(registry.dynamicLoadingEnabled).toBe(false);
    });

    // AC-4: dynamic/anthropic mode keeps dynamicLoadingEnabled
    it("keeps dynamicLoadingEnabled true for dynamic mode", () => {
        const core = makeDef("core", { alwaysLoaded: true });
        registry.register(core);
        registry.storeHandles("core", [mockHandle()] as any);

        const selection: ToolsetSelection = { kind: "defaults" };
        applyModeFilter(registry, "dynamic", selection);

        expect(registry.dynamicLoadingEnabled).toBe(true);
    });
});
