/**
 * generate-tools-manifest.ts — Static manifest generator for MCP tool metadata.
 *
 * Reads TOOLSET_DEFINITIONS from seed.ts and writes zorivest-tools.json
 * with tool/toolset counts for consumption by the Python API.
 *
 * Run: npx tsx scripts/generate-tools-manifest.ts
 * Hooked: "prebuild" script in package.json
 *
 * Source: MEU-46a (mcp-rest-proxy), [PD-46a]
 */

import { writeFileSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

// Import the seed data — we need the TOOLSET_DEFINITIONS array.
// Since seed.ts exports a function (seedToolsets) that registers into a registry,
// and the definitions are a module-level const, we need to extract them.
// The cleanest approach: export the definitions from seed.ts and import here.
// For now, we re-read the same data by importing the registry and calling getAll()
// after seeding. But that requires an McpServer instance which is heavy.
//
// Better approach: extract TOOLSET_DEFINITIONS into its own file, or add
// an export. We'll add a named export to seed.ts.

import { TOOLSET_DEFINITIONS } from "../src/toolsets/seed.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

interface ToolsetManifestEntry {
    name: string;
    description: string;
    tool_count: number;
    always_loaded: boolean;
    tools: string[];
}

interface ToolsManifest {
    total_tools: number;
    toolset_count: number;
    toolsets: ToolsetManifestEntry[];
    generated_at: string;
}

const toolsets: ToolsetManifestEntry[] = TOOLSET_DEFINITIONS.map((ts) => ({
    name: ts.name,
    description: ts.description,
    tool_count: ts.tools.length,
    always_loaded: ts.alwaysLoaded,
    tools: ts.tools.map((t) => t.name),
}));

const manifest: ToolsManifest = {
    total_tools: toolsets.reduce((sum, ts) => sum + ts.tool_count, 0),
    toolset_count: toolsets.length,
    toolsets,
    generated_at: new Date().toISOString(),
};

const outputPath = join(__dirname, "..", "zorivest-tools.json");
writeFileSync(outputPath, JSON.stringify(manifest, null, 2) + "\n");

console.log(
    `[generate-tools-manifest] Written ${manifest.total_tools} tools across ${manifest.toolset_count} toolsets to zorivest-tools.json`,
);
