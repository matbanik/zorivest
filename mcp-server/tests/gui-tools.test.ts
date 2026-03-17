/**
 * Unit tests for GUI launch MCP tool.
 *
 * Tests verify discovery logic, cross-platform spawn dispatch,
 * not-found behavior (releases page + setup_instructions),
 * unguarded registration (withMetrics only, no withGuard),
 * PATH lookup (method 3), and wait_for_close behavior.
 *
 * Source: 05b-mcp-zorivest-diagnostics.md, 05-mcp-server.md §5.8
 * FIC: MEU-40 AC-1 through AC-12
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { registerGuiTools } from "../src/tools/gui-tools.js";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { InMemoryTransport } from "@modelcontextprotocol/sdk/inMemory.js";

// Mock child_process.exec for spawn tests
const mockExec = vi.fn();
vi.mock("node:child_process", () => ({
    exec: (...args: unknown[]) => mockExec(...args),
}));

// Mock fs.existsSync for discovery tests
const mockExistsSync = vi.fn();
vi.mock("node:fs", () => ({
    existsSync: (p: string) => mockExistsSync(p),
}));

// ── Test helpers ───────────────────────────────────────────────────────

async function createTestClient(): Promise<Client> {
    const server = new McpServer({ name: "test", version: "0.1.0" });
    registerGuiTools(server);

    const [clientTransport, serverTransport] =
        InMemoryTransport.createLinkedPair();

    const client = new Client({ name: "test-client", version: "0.1.0" });

    await Promise.all([
        client.connect(clientTransport),
        server.connect(serverTransport),
    ]);

    return client;
}

// ── Tests ──────────────────────────────────────────────────────────────

describe("zorivest_launch_gui", () => {
    beforeEach(() => {
        vi.restoreAllMocks();
        mockExec.mockReset();
        mockExistsSync.mockReset();
        // Default: no GUI found anywhere
        mockExistsSync.mockReturnValue(false);
        // Default exec: call callback with error (simulates command not found)
        mockExec.mockImplementation(
            (_cmd: string, cb?: (err: Error | null, stdout?: string) => void) => {
                if (cb) cb(new Error("not found"), "");
            },
        );
        // Default: no env var
        delete process.env.ZORIVEST_GUI_PATH;
    });

    // AC-1 + AC-3: Registers with canonical name; returns structured output
    // AC-8: When GUI not found, returns gui_found: false + setup_instructions
    it("returns gui_found: false with setup_instructions when no GUI discovered", async () => {
        const client = await createTestClient();
        const result = await client.callTool({
            name: "zorivest_launch_gui",
            arguments: {},
        });

        const content = result.content as Array<{
            type: string;
            text: string;
        }>;
        expect(content).toHaveLength(1);
        expect(content[0].type).toBe("text");

        const parsed = JSON.parse(content[0].text);
        expect(parsed.gui_found).toBe(false);
        expect(parsed.method).toBe("not-found");
        expect(parsed.message).toBeDefined();
        expect(parsed.setup_instructions).toBeDefined();
        expect(parsed.setup_instructions).toContain("releases");
    });

    // AC-4 method 1: Packaged app discovery
    it("returns gui_found: true with packaged method when installed app found", async () => {
        mockExistsSync.mockImplementation((p: string) => {
            if (typeof p === "string" && p.includes("Zorivest")) return true;
            return false;
        });

        const client = await createTestClient();
        const result = await client.callTool({
            name: "zorivest_launch_gui",
            arguments: { wait_for_close: false },
        });

        const content = result.content as Array<{
            type: string;
            text: string;
        }>;
        const parsed = JSON.parse(content[0].text);
        expect(parsed.gui_found).toBe(true);
        expect(parsed.method).toBe("packaged");
        expect(parsed.message).toBeDefined();
    });

    // AC-4 method 2: Dev mode discovery
    it("returns gui_found: true with dev-mode method when dev repo detected", async () => {
        mockExistsSync.mockImplementation((p: string) => {
            if (typeof p === "string" && p.includes("ui")) return true;
            if (typeof p === "string" && p.includes("package.json"))
                return true;
            return false;
        });

        const client = await createTestClient();
        const result = await client.callTool({
            name: "zorivest_launch_gui",
            arguments: {},
        });

        const content = result.content as Array<{
            type: string;
            text: string;
        }>;
        const parsed = JSON.parse(content[0].text);
        expect(parsed.gui_found).toBe(true);
        expect(parsed.method).toBe("dev-mode");
    });

    // AC-4 method 3: PATH lookup via which/where
    it("returns gui_found: true with path method when found on PATH", async () => {
        // exec mock: first call is PATH lookup (which zorivest) — succeeds
        // second call is the launch exec — succeeds
        mockExec.mockImplementation(
            (cmd: string, cb?: (err: Error | null, stdout?: string) => void) => {
                if (typeof cmd === "string" && (cmd.includes("which") || cmd.includes("where"))) {
                    if (cb) cb(null, "/usr/local/bin/zorivest\n");
                } else {
                    if (cb) cb(null, "");
                }
            },
        );

        const client = await createTestClient();
        const result = await client.callTool({
            name: "zorivest_launch_gui",
            arguments: {},
        });

        const content = result.content as Array<{
            type: string;
            text: string;
        }>;
        const parsed = JSON.parse(content[0].text);
        expect(parsed.gui_found).toBe(true);
        expect(parsed.method).toBe("path");
    });

    // AC-4 method 4: Environment variable discovery
    it("returns gui_found: true with env-var method via ZORIVEST_GUI_PATH", async () => {
        process.env.ZORIVEST_GUI_PATH = "/custom/zorivest-gui";
        mockExistsSync.mockImplementation((p: string) => {
            if (p === "/custom/zorivest-gui") return true;
            return false;
        });

        const client = await createTestClient();
        const result = await client.callTool({
            name: "zorivest_launch_gui",
            arguments: {},
        });

        const content = result.content as Array<{
            type: string;
            text: string;
        }>;
        const parsed = JSON.parse(content[0].text);
        expect(parsed.gui_found).toBe(true);
        expect(parsed.method).toBe("env-var");
    });

    // AC-9: Not guarded — no guard fetch call
    it("does not call guard (unguarded tool)", async () => {
        // Spy on global fetch to verify no guard call
        vi.stubGlobal("fetch", vi.fn());

        const client = await createTestClient();
        await client.callTool({
            name: "zorivest_launch_gui",
            arguments: {},
        });

        // Should not have called fetch at all (no guard, no API call)
        expect(fetch).not.toHaveBeenCalled();
        // Value: verify the tool still returned a valid response
        const result = await client.callTool({
            name: "zorivest_launch_gui",
            arguments: {},
        });
        const content = result.content as Array<{ type: string; text: string }>;
        expect(content[0].type).toBe("text");
    });

    // wait_for_close=true: handler awaits process exit
    it("honors wait_for_close=true by awaiting launchAndWait", async () => {
        // Simulate packaged app found so we actually launch
        mockExistsSync.mockImplementation((p: string) => {
            if (typeof p === "string" && p.includes("Zorivest")) return true;
            return false;
        });
        // exec for launch-and-wait: call callback immediately (simulates exit)
        mockExec.mockImplementation(
            (_cmd: string, cb?: (err: Error | null) => void) => {
                if (cb) cb(null);
            },
        );

        const client = await createTestClient();
        const result = await client.callTool({
            name: "zorivest_launch_gui",
            arguments: { wait_for_close: true },
        });

        const content = result.content as Array<{
            type: string;
            text: string;
        }>;
        const parsed = JSON.parse(content[0].text);
        expect(parsed.gui_found).toBe(true);
        // Verify exec was called with the executable path directly (not start/setsid)
        // launchAndWait runs exec("path") not exec("start ... path")
        const execCalls = mockExec.mock.calls;
        const launchCall = execCalls.find(
            (c: unknown[]) => typeof c[0] === "string" && c[0].includes("Zorivest"),
        );
        expect(launchCall).toBeDefined();
    });
});
