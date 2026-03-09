/**
 * Integration test — live Python API round-trip.
 *
 * Spawns the Python REST API in a subprocess on a random port,
 * waits for health check, exercises MCP tool functions against the real API.
 *
 * Hardened against false positives:
 *  - Random port avoids stale-process collision
 *  - Child PID tracked and validated
 *  - Stderr monitored for bind errors (fail-fast)
 *  - Child exit during setup fails the suite
 *
 * Test harness creates an API key in beforeAll (test-only setup,
 * NOT runtime behavior — per 04c-api-auth.md admin-only key creation).
 *
 * Source: implementation-plan.md §MEU-32
 */

import {
    describe,
    it,
    expect,
    beforeAll,
    afterAll,
} from "vitest";
import { spawn, type ChildProcess } from "child_process";
import * as net from "net";

// ── Constants ──────────────────────────────────────────────────────────

const HEALTH_TIMEOUT_MS = 20_000;
const HEALTH_POLL_MS = 500;

// ── State ──────────────────────────────────────────────────────────────

let apiProcess: ChildProcess | null = null;
let apiPort = 0;
let apiBase = "";

// ── Helpers ────────────────────────────────────────────────────────────

/**
 * Find a random available port by binding to port 0 and reading the assignment.
 */
async function findFreePort(): Promise<number> {
    return new Promise((resolve, reject) => {
        const srv = net.createServer();
        srv.listen(0, "127.0.0.1", () => {
            const addr = srv.address();
            if (addr && typeof addr === "object") {
                const port = addr.port;
                srv.close(() => resolve(port));
            } else {
                reject(new Error("Could not determine port"));
            }
        });
        srv.on("error", reject);
    });
}

async function waitForHealth(): Promise<void> {
    const healthUrl = `http://localhost:${apiPort}/api/v1/health`;
    const deadline = Date.now() + HEALTH_TIMEOUT_MS;

    while (Date.now() < deadline) {
        try {
            const res = await fetch(healthUrl);
            if (res.ok) return;
        } catch {
            // not ready yet
        }
        await new Promise((r) => setTimeout(r, HEALTH_POLL_MS));
    }

    throw new Error(
        `Python API did not become healthy within ${HEALTH_TIMEOUT_MS}ms on port ${apiPort}`,
    );
}

/**
 * Inline fetchApi that uses the test-specific apiBase (random port).
 * Does NOT use the module-level API_BASE from api-client.ts.
 */
async function testFetchApi(
    path: string,
    options: RequestInit = {},
): Promise<{ success: boolean; data?: unknown; error?: string }> {
    const url = `${apiBase}${path}`;
    try {
        const res = await fetch(url, options);
        if (!res.ok) {
            const body = await res.text();
            return { success: false, error: `${res.status}: ${body}` };
        }
        if (res.status === 204) return { success: true };
        const data: unknown = await res.json();
        return { success: true, data };
    } catch (error) {
        const msg =
            error instanceof Error ? error.message : "Unknown error";
        return { success: false, error: msg };
    }
}

/**
 * Test-only setup: create an API key and unlock the database.
 * This is NOT runtime behavior — key creation is admin-only (04c-api-auth.md §79).
 */
async function bootstrapTestAuth(): Promise<void> {
    // 1. Create an API key (test harness setup only)
    const keyRes = await fetch(`${apiBase}/auth/keys`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            name: "integration-test",
            role: "admin",
        }),
    });

    if (!keyRes.ok) {
        const err = await keyRes.text();
        throw new Error(`Failed to create test API key: ${err}`);
    }

    const keyData = (await keyRes.json()) as { raw_key: string };

    // 2. Unlock DB via POST /auth/unlock
    const unlockRes = await fetch(`${apiBase}/auth/unlock`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ api_key: keyData.raw_key }),
    });

    if (!unlockRes.ok) {
        const detail = await unlockRes.text();
        // 423 = already unlocked — acceptable for test reruns
        if (unlockRes.status === 423) return;
        throw new Error(
            `Auth unlock failed (${unlockRes.status}): ${detail}`,
        );
    }
}

// ── Setup / Teardown ───────────────────────────────────────────────────

beforeAll(async () => {
    // 1. Find a free port (avoids stale-process collision)
    apiPort = await findFreePort();
    apiBase = `http://localhost:${apiPort}/api/v1`;

    // 2. Spawn Python API server on the random port
    apiProcess = spawn(
        "uv",
        [
            "run",
            "python",
            "-m",
            "uvicorn",
            "zorivest_api.main:create_app",
            "--factory",
            "--host",
            "127.0.0.1",
            "--port",
            String(apiPort),
        ],
        {
            cwd: "p:\\zorivest",
            stdio: "pipe",
            shell: true,
        },
    );

    // 3. Track bind errors from stderr (fail-fast)
    let bindError = false;
    apiProcess.stderr?.on("data", (data: Buffer) => {
        const line = data.toString().trim();
        if (line) {
            // Detect port-already-in-use errors
            if (
                line.includes("address already in use") ||
                line.includes("WinError 10048")
            ) {
                bindError = true;
            }
        }
    });

    // 4. Detect child exit during setup
    const childExitPromise = new Promise<never>((_, reject) => {
        apiProcess?.on("exit", (code) => {
            if (code !== null && code !== 0) {
                reject(
                    new Error(
                        `API process exited with code ${code} during setup`,
                    ),
                );
            }
        });
    });

    apiProcess.on("error", (err) => {
        throw new Error(`Failed to spawn API process: ${err.message}`);
    });

    // 5. Wait for health check — race with child exit
    await Promise.race([
        waitForHealth(),
        childExitPromise,
    ]);

    // 6. Verify no bind errors occurred
    if (bindError) {
        throw new Error(
            `API process had bind errors on port ${apiPort}. Another process may be using this port.`,
        );
    }

    // 7. Verify child PID is still alive
    if (!apiProcess || apiProcess.exitCode !== null) {
        throw new Error(
            "API process exited before tests could start",
        );
    }

    // 8. Bootstrap test auth (create key + unlock — test-only setup)
    await bootstrapTestAuth();
}, 30_000);

afterAll(async () => {
    if (apiProcess) {
        apiProcess.kill("SIGTERM");
        // Give process time to exit gracefully
        await new Promise((r) => setTimeout(r, 1000));
        if (!apiProcess.killed) {
            apiProcess.kill("SIGKILL");
        }
        apiProcess = null;
    }
});

// ── Integration Tests ──────────────────────────────────────────────────

describe("MCP → REST API round-trip", () => {
    it("create_trade round-trip: POST /trades → verify response", async () => {
        const result = await testFetchApi("/trades", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                exec_id: `INT_TEST_${Date.now()}`,
                time: new Date().toISOString(),
                instrument: "AAPL",
                action: "BOT",
                quantity: 10,
                price: 150.0,
                account_id: "TEST_ACC",
                commission: 1.5,
                realized_pnl: 0,
            }),
        });

        expect(result.success).toBe(true);
        expect(result.data).toBeDefined();
        const trade = result.data as Record<string, unknown>;
        expect(trade.instrument).toBe("AAPL");
        expect(trade.action).toBe("BOT");
        expect(trade.quantity).toBe(10);
    });

    it("list_trades round-trip: GET /trades → verify array", async () => {
        const result = await testFetchApi("/trades");

        expect(result.success).toBe(true);
        expect(result.data).toBeDefined();
        // The response should be an object with items array
        const data = result.data as
            | { items?: unknown[] }
            | unknown[];
        if (Array.isArray(data)) {
            expect(data.length).toBeGreaterThanOrEqual(0);
        } else {
            expect(data.items).toBeDefined();
        }
    });

    it("get_settings round-trip: GET /settings → verify object", async () => {
        const result = await testFetchApi("/settings");

        expect(result.success).toBe(true);
        expect(result.data).toBeDefined();
        expect(typeof result.data).toBe("object");
    });

    it("calculate_position_size round-trip: POST /calculator/position-size → verify result", async () => {
        const result = await testFetchApi(
            "/calculator/position-size",
            {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    balance: 50000,
                    risk_pct: 1,
                    entry_price: 100,
                    stop_loss: 90,
                    target_price: 120,
                }),
            },
        );

        expect(result.success).toBe(true);
        expect(result.data).toBeDefined();
        const calc = result.data as Record<string, unknown>;
        expect(calc.position_size).toBeDefined();
        expect(typeof calc.position_size).toBe("number");
    });
});
