/**
 * Registration orchestrator — pre-connect-all + post-connect-filter.
 *
 * Implements the two-phase registration strategy required by MCP SDK constraints:
 * 1. registerAllToolsets(): Pre-connect, registers ALL tools (triggers registerCapabilities once)
 * 2. applyModeFilter(): Post-connect (in oninitialized), disables non-selected toolsets
 *
 * Source: 05-mcp-server.md §5.14 L893-933
 * MEU: 42 (toolset-registry)
 */

import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import type { ToolsetRegistry } from "./toolsets/registry.js";
import type { ClientMode } from "./client-detection.js";
import type { ToolsetSelection } from "./cli.js";

// ── Pre-connect phase ──────────────────────────────────────────────────

/**
 * Register ALL toolsets pre-connect (all enabled by default).
 *
 * Iterates registry, calls each toolset's register() callback,
 * and stores returned RegisteredToolHandle[] in registry.storeHandles().
 * This triggers SDK registerCapabilities({tools:{listChanged:true}}) once.
 */
export function registerAllToolsets(
    server: McpServer,
    registry: ToolsetRegistry,
): void {
    for (const ts of registry.getAll()) {
        const handles = ts.register(server);
        registry.storeHandles(ts.name, handles);
    }
}

// ── Post-connect phase ─────────────────────────────────────────────────

/**
 * Filter toolsets based on client mode and selection.
 *
 * Called inside Server.oninitialized callback, BEFORE any tools/list request.
 * Disables non-selected toolsets via handle.disable() and marks active ones loaded.
 *
 * Server-side ordering guarantee (SDK-sourced):
 * - Protocol._onnotification dispatches handlers via Promise.resolve().then()
 * - oninitialized runs synchronously within that handler
 * - JS event loop ensures next onmessage fires only after completion
 * - Therefore, tools/list ALWAYS sees post-filter state
 */
export function applyModeFilter(
    registry: ToolsetRegistry,
    mode: ClientMode,
    selection: ToolsetSelection,
): void {
    // Determine which toolsets should be active
    const allDefs = registry.getAll();

    for (const ts of allDefs) {
        const shouldEnable = isToolsetEnabled(ts.name, ts.alwaysLoaded, ts.isDefault, selection);

        if (shouldEnable) {
            // Mark as loaded (enabled and active)
            registry.markLoaded(ts.name);
        } else {
            // Disable all handles for this toolset
            const handles = registry.getHandles(ts.name);
            for (const handle of handles) {
                handle.disable();
            }
            // loaded stays false (registered but disabled)
        }
    }

    // Set dynamic loading based on mode
    registry.dynamicLoadingEnabled = mode !== "static";
}

// ── Selection logic ────────────────────────────────────────────────────

/**
 * Determine if a toolset should be enabled based on selection.
 */
function isToolsetEnabled(
    name: string,
    alwaysLoaded: boolean,
    isDefault: boolean,
    selection: ToolsetSelection,
): boolean {
    // Always-loaded toolsets (core, discovery) are always enabled
    if (alwaysLoaded) return true;

    switch (selection.kind) {
        case "all":
            return true;
        case "explicit":
            return selection.names.includes(name);
        case "defaults":
            return isDefault;
    }
}
