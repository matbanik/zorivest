/**
 * Toolset Registry — in-memory registry for MCP toolset management.
 *
 * Groups MCP tools into named categories (toolsets) for selective loading.
 * Provides lookup, listing, and load-state tracking.
 *
 * Full --toolsets CLI, client detection, and adaptive patterns
 * are deferred to MEU-42 (toolset-registry).
 *
 * Source: 05j-mcp-discovery.md §Toolset Registry, 05-mcp-server.md §5.11
 * MEU: 41 (mcp-discovery)
 */

import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";

// ── Types ──────────────────────────────────────────────────────────────

export interface ToolSpec {
    name: string;
    description: string;
    annotations?: Record<string, unknown>;
}

export interface ToolsetDefinition {
    name: string;
    description: string;
    tools: ToolSpec[];
    register: (server: McpServer) => void;
    loaded: boolean;
    alwaysLoaded: boolean;
}

// ── ToolsetRegistry ────────────────────────────────────────────────────

export class ToolsetRegistry {
    private toolsets = new Map<string, ToolsetDefinition>();

    /**
     * Whether dynamic tool loading is enabled for the current session.
     *
     * When false, `enable_toolset` rejects with guidance to restart with
     * `--toolsets`. Defaults to true (all runtime clients assumed dynamic).
     * MEU-42 wires `--toolsets` CLI to set this false for static clients.
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
     * Get all registered toolset definitions.
     */
    getAll(): ToolsetDefinition[] {
        return Array.from(this.toolsets.values());
    }

    /**
     * Get a specific toolset by name.
     */
    get(name: string): ToolsetDefinition | undefined {
        return this.toolsets.get(name);
    }

    /**
     * Mark a toolset as loaded (active in current session).
     */
    markLoaded(name: string): void {
        const ts = this.toolsets.get(name);
        if (ts) ts.loaded = true;
    }

    /**
     * Get default toolset names (non-deferred, non-alwaysLoaded).
     * Full implementation in MEU-42.
     */
    getDefaults(): string[] {
        return Array.from(this.toolsets.values())
            .filter((ts) => !ts.alwaysLoaded && !ts.loaded)
            .map((ts) => ts.name);
    }
}

// ── Singleton ──────────────────────────────────────────────────────────

export const toolsetRegistry = new ToolsetRegistry();
