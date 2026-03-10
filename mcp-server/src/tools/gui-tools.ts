/**
 * GUI launch MCP tool.
 *
 * Source: 05b-mcp-zorivest-diagnostics.md, 05-mcp-server.md §5.8
 * Registers: zorivest_launch_gui
 *
 * Unguarded — always callable even when guard is locked.
 * Uses withMetrics only (no withGuard).
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import { withMetrics } from "../middleware/metrics.js";
import { exec } from "node:child_process";
import { existsSync } from "node:fs";
import { resolve, join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

// ESM-safe __dirname equivalent
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// ── GUI discovery ──────────────────────────────────────────────────────

interface DiscoveryResult {
    found: boolean;
    method: string;
    path: string;
}

/**
 * PATH lookup via which/where. Returns the resolved path or null.
 */
function pathLookup(): Promise<string | null> {
    const cmd = process.platform === "win32" ? "where zorivest" : "which zorivest";
    return new Promise((res) => {
        exec(cmd, (err, stdout) => {
            if (err || !stdout.trim()) {
                res(null);
            } else {
                const p = stdout.trim().split(/[\r\n]/)[0];
                res(p);
            }
        });
    });
}

/**
 * Try 4 methods to discover the GUI in order:
 * 1. Packaged Electron app (standard install paths)
 * 2. Development mode (repo ui/ dir)
 * 3. PATH lookup (which/where)
 * 4. Environment variable (ZORIVEST_GUI_PATH)
 *
 * Spec: 05-mcp-server.md §5.8 L302-309
 */
async function discoverGui(): Promise<DiscoveryResult> {
    const platform = process.platform;

    // Method 1: Packaged app
    const installPaths: Record<string, string[]> = {
        win32: [
            `${process.env.LOCALAPPDATA || ""}\\Programs\\Zorivest\\Zorivest.exe`,
        ],
        darwin: ["/Applications/Zorivest.app"],
        linux: ["/usr/bin/zorivest", "/usr/local/bin/zorivest"],
    };

    const candidates = installPaths[platform] ?? installPaths.linux ?? [];
    for (const p of candidates) {
        if (existsSync(p)) {
            return { found: true, method: "packaged", path: p };
        }
    }

    // Method 2: Development mode — navigate from mcp-server to repo root/ui
    const devUiDir = resolve(__dirname, "..", "..", "ui");
    const devPkg = join(devUiDir, "package.json");
    if (existsSync(devUiDir) && existsSync(devPkg)) {
        return { found: true, method: "dev-mode", path: devUiDir };
    }

    // Method 3: PATH lookup via which/where
    const pathResult = await pathLookup();
    if (pathResult) {
        return { found: true, method: "path", path: pathResult };
    }

    // Method 4: Environment variable
    const envPath = process.env.ZORIVEST_GUI_PATH;
    if (envPath && existsSync(envPath)) {
        return { found: true, method: "env-var", path: envPath };
    }

    return { found: false, method: "not-found", path: "" };
}

// ── Cross-platform spawn ───────────────────────────────────────────────
// Spec: 05-mcp-server.md §5.8 L316-321

function launchDetached(guiPath: string): void {
    const platform = process.platform;

    if (platform === "win32") {
        exec(`start "" "${guiPath}"`);
    } else if (platform === "darwin") {
        if (guiPath.endsWith(".app")) {
            exec(`open -a "${guiPath}"`);
        } else {
            exec(`nohup "${guiPath}" > /dev/null 2>&1 &`);
        }
    } else {
        exec(`setsid "${guiPath}" > /dev/null 2>&1 &`);
    }
}

/**
 * Launch GUI and wait for process to exit.
 * Returns a promise that resolves when the spawned process closes.
 */
function launchAndWait(guiPath: string): Promise<void> {
    return new Promise((resolve, reject) => {
        exec(`"${guiPath}"`, (err) => {
            if (err) reject(err);
            else resolve();
        });
    });
}

function openReleasesPage(): void {
    const url = "https://github.com/zorivest/zorivest/releases";
    const platform = process.platform;

    if (platform === "win32") {
        exec(`start "" "${url}"`);
    } else if (platform === "darwin") {
        exec(`open "${url}"`);
    } else {
        exec(`xdg-open "${url}"`);
    }
}

// ── Tool registration ──────────────────────────────────────────────────

const RELEASES_URL = "https://github.com/zorivest/zorivest/releases";

/**
 * Register GUI launch MCP tool on the server.
 * Unguarded — always callable.
 */
export function registerGuiTools(server: McpServer): void {
    server.registerTool(
        "zorivest_launch_gui",
        {
            description:
                "Launch the Zorivest desktop GUI. If not installed, opens the download page and returns setup instructions the agent can relay to the user.",
            inputSchema: {
                wait_for_close: z
                    .boolean()
                    .default(false)
                    .describe("If true, blocks until GUI process exits"),
            },
            // AC-10: Annotations per spec 05b L135-137
            annotations: {
                readOnlyHint: false,
                destructiveHint: false,
                idempotentHint: false,
                openWorldHint: false,
            },
            // AC-11: toolset=core, alwaysLoaded=true
            _meta: {
                toolset: "core",
                alwaysLoaded: true,
            },
        },
        // AC-12: withMetrics only (no withGuard) — unguarded tool
        withMetrics(
            "zorivest_launch_gui",
            async (params: { wait_for_close: boolean }, _extra: unknown) => {
                const discovery = await discoverGui();

                if (!discovery.found) {
                    // AC-8: Open releases page + return setup_instructions
                    openReleasesPage();

                    return {
                        content: [
                            {
                                type: "text" as const,
                                text: JSON.stringify({
                                    gui_found: false,
                                    method: "not-found",
                                    message:
                                        "Zorivest GUI not found. Opening download page.",
                                    setup_instructions: `Download the latest release from ${RELEASES_URL} and install it. Then try again.`,
                                }),
                            },
                        ],
                    };
                }

                // Launch or launch-and-wait based on wait_for_close
                if (params.wait_for_close) {
                    await launchAndWait(discovery.path);
                } else {
                    launchDetached(discovery.path);
                }

                return {
                    content: [
                        {
                            type: "text" as const,
                            text: JSON.stringify({
                                gui_found: true,
                                method: discovery.method,
                                message: `Zorivest GUI launched via ${discovery.method} method.`,
                            }),
                        },
                    ],
                };
            },
        ),
    );
}
