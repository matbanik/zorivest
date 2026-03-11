/**
 * Toolset Registry — in-memory registry for MCP toolset management.
 *
 * Groups MCP tools into named categories (toolsets) for selective loading.
 * Provides lookup, listing, load-state tracking, and handle management.
 *
 * Source: 05j-mcp-discovery.md §Toolset Registry, 05-mcp-server.md §5.11
 * MEU: 41 (mcp-discovery), 42 (toolset-registry)
 */

import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";

// ── Types ──────────────────────────────────────────────────────────────

export interface ToolSpec {
    name: string;
    description: string;
    annotations?: Record<string, unknown>;
}

/**
 * RegisteredTool handle — matches the type returned by McpServer.registerTool().
 * Used for enable/disable operations post-registration.
 */
export interface RegisteredToolHandle {
    enable(): void;
    disable(): void;
}

export interface ToolsetDefinition {
    name: string;
    description: string;
    tools: ToolSpec[];
    /** Registers tools on the server and returns handles for enable/disable */
    register: (server: McpServer) => RegisteredToolHandle[];
    /** Runtime state: false = registered but disabled; true = registered AND enabled */
    loaded: boolean;
    /** Metadata: toolset is always loaded regardless of selection */
    alwaysLoaded: boolean;
    /** Metadata: toolset is included in default selection (AC-10) */
    isDefault: boolean;
}

// ── ToolsetRegistry ────────────────────────────────────────────────────

export class ToolsetRegistry {
    private toolsets = new Map<string, ToolsetDefinition>();
    private toolHandles = new Map<string, RegisteredToolHandle[]>();

    /**
     * Whether dynamic tool loading is enabled for the current session.
     *
     * When false, `enable_toolset` rejects with guidance to restart with
     * `--toolsets`. Defaults to true (all runtime clients assumed dynamic).
     *
     * Source: 05j-mcp-discovery.md L152 (clientSupportsNotification check)
     */
    dynamicLoadingEnabled = true;

    /**
     * Register a toolset definition.
     */
    register(def: ToolsetDefinition): void {
        this.toolsets.set(def.name, def);
    }

    /**
     * Store RegisteredTool handles for a toolset after registration.
     * Used by registerAllToolsets() to capture handles for later enable/disable.
     */
    storeHandles(name: string, handles: RegisteredToolHandle[]): void {
        this.toolHandles.set(name, handles);
    }

    /**
     * Retrieve stored handles for a toolset.
     * Used by applyModeFilter() and enable_toolset for handle-based operations.
     */
    getHandles(name: string): RegisteredToolHandle[] {
        return this.toolHandles.get(name) ?? [];
    }

    /**
     * Get all registered toolset definitions.
     */
    getAll(): ToolsetDefinition[] {
        return Array.from(this.toolsets.values());
    }

    /**
     * Get all registered toolset names.
     */
    getAllNames(): string[] {
        return Array.from(this.toolsets.keys());
    }

    /**
     * Get a specific toolset by name.
     */
    get(name: string): ToolsetDefinition | undefined {
        return this.toolsets.get(name);
    }

    /**
     * Mark a toolset as loaded (enabled and active in session).
     */
    markLoaded(name: string): void {
        const ts = this.toolsets.get(name);
        if (ts) ts.loaded = true;
    }

    /**
     * Get default toolset names: isDefault === true AND loaded === false.
     * Returns only toolsets that should be loaded but haven't been activated yet.
     */
    getDefaults(): string[] {
        return Array.from(this.toolsets.values())
            .filter((ts) => ts.isDefault === true && !ts.loaded)
            .map((ts) => ts.name);
    }
}

// ── Singleton ──────────────────────────────────────────────────────────

export const toolsetRegistry = new ToolsetRegistry();
