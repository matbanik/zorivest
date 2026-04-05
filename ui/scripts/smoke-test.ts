/**
 * Smoke test — validates real GUI→API connectivity without Electron or human.
 *
 * Starts the Python API server with ZORIVEST_DEV_UNLOCK=1, waits for health,
 * then asserts all endpoints return expected shapes. Exits 0 (pass) or 1 (fail).
 *
 * Usage: npm run test:smoke
 */

/// <reference types="node" />

import { spawn, type ChildProcess } from 'child_process'
import { resolve, dirname } from 'path'
import { fileURLToPath } from 'url'

const BACKEND_PORT = 17787
const BASE_URL = `http://127.0.0.1:${BACKEND_PORT}`
const HEALTH_URL = `${BASE_URL}/api/v1/health`
const VERSION_URL = `${BASE_URL}/api/v1/version/`
const TRADES_URL = `${BASE_URL}/api/v1/trades?limit=1&offset=0`
const GUARD_URL = `${BASE_URL}/api/v1/mcp-guard/status`
const MAX_WAIT_MS = 30_000
const POLL_MS = 500

let apiProcess: ChildProcess | null = null
const failures: string[] = []

// ── Helpers ────────────────────────────────────────────────────────────

function log(msg: string) {
    console.log(`[smoke] ${msg}`)
}

function fail(msg: string) {
    console.error(`[smoke] ❌ FAIL: ${msg}`)
    failures.push(msg)
}

function pass(msg: string) {
    console.log(`[smoke] ✅ PASS: ${msg}`)
}

async function waitForHealth(timeoutMs: number): Promise<boolean> {
    const deadline = Date.now() + timeoutMs
    while (Date.now() < deadline) {
        try {
            const res = await fetch(HEALTH_URL)
            if (res.ok) return true
        } catch {
            // Not ready yet
        }
        await new Promise((r) => setTimeout(r, POLL_MS))
    }
    return false
}

function cleanup() {
    if (apiProcess && apiProcess.pid) {
        log('Stopping API server...')
        try {
            // Windows: taskkill /F /T kills the entire process tree
            // SIGTERM doesn't work reliably on Windows
            if (process.platform === 'win32') {
                spawn('taskkill', ['/F', '/T', '/PID', String(apiProcess.pid)], {
                    stdio: 'ignore',
                    shell: true,
                })
            } else {
                apiProcess.kill('SIGTERM')
            }
        } catch {
            // Process may already be dead
        }
        apiProcess = null
    }
}

// ── Start API server ───────────────────────────────────────────────────

async function startApi(): Promise<void> {
    // Check if already running
    try {
        const res = await fetch(HEALTH_URL)
        if (res.ok) {
            log('API already running, skipping spawn')
            return
        }
    } catch {
        // Not running — spawn it
    }

    const scriptDir = typeof __dirname !== 'undefined' ? __dirname : dirname(fileURLToPath(import.meta.url))
    const apiDir = resolve(scriptDir, '../../packages/api')
    log(`Starting API server from ${apiDir}...`)

    apiProcess = spawn(
        'uv',
        [
            'run', 'uvicorn',
            'zorivest_api.main:app',
            '--host', '127.0.0.1',
            '--port', String(BACKEND_PORT),
            '--no-access-log',
        ],
        {
            cwd: apiDir,
            stdio: ['ignore', 'pipe', 'pipe'],
            shell: true,
            env: { ...process.env, ZORIVEST_DEV_UNLOCK: '1' },
        },
    )

    apiProcess.stderr?.on('data', (data: Buffer) => {
        const msg = data.toString().trim()
        if (msg && !msg.includes('INFO:')) {
            console.error(`[api:err] ${msg}`)
        }
    })

    const ready = await waitForHealth(MAX_WAIT_MS)
    if (!ready) {
        cleanup()
        console.error('[smoke] ❌ API server failed to start within timeout')
        process.exit(1)
    }

    log('API server is healthy')
}

// ── Assertions ─────────────────────────────────────────────────────────

async function assertHealth(): Promise<void> {
    const res = await fetch(HEALTH_URL)
    if (!res.ok) {
        fail(`GET /api/v1/health → ${res.status} (expected 200)`)
        return
    }

    const body = await res.json() as Record<string, unknown>

    if (body.status !== 'ok') {
        fail(`health.status = "${body.status}" (expected "ok")`)
    } else {
        pass('health.status === "ok"')
    }

    if (typeof body.version !== 'string' || !body.version) {
        fail(`health.version is missing or empty`)
    } else {
        pass(`health.version = "${body.version}"`)
    }

    if (typeof body.uptime_seconds !== 'number') {
        fail(`health.uptime_seconds is not a number`)
    } else {
        pass(`health.uptime_seconds = ${body.uptime_seconds}`)
    }

    const db = body.database as Record<string, unknown> | undefined
    if (!db || typeof db.unlocked !== 'boolean') {
        fail(`health.database.unlocked is missing or not boolean (got: ${JSON.stringify(db)})`)
    } else if (!db.unlocked) {
        fail(`health.database.unlocked = false (expected true with ZORIVEST_DEV_UNLOCK=1)`)
    } else {
        pass('health.database.unlocked === true')
    }
}

async function assertVersion(): Promise<void> {
    const res = await fetch(VERSION_URL)
    if (!res.ok) {
        fail(`GET /api/v1/version/ → ${res.status} (expected 200)`)
        return
    }

    const body = await res.json() as Record<string, unknown>
    if (typeof body.version !== 'string' || !body.version) {
        fail('version.version is missing or empty')
    } else {
        pass(`version.version = "${body.version}"`)
    }
}

async function assertTrades(): Promise<void> {
    const res = await fetch(TRADES_URL)
    if (res.status === 403) {
        fail('GET /api/v1/trades → 403 Forbidden (DB not unlocked — ZORIVEST_DEV_UNLOCK not working)')
        return
    }
    if (!res.ok) {
        fail(`GET /api/v1/trades → ${res.status} (expected 200)`)
        return
    }

    pass('GET /api/v1/trades → 200 (DB is unlocked)')
}

async function assertGuard(): Promise<void> {
    const res = await fetch(GUARD_URL)
    if (!res.ok) {
        fail(`GET /api/v1/mcp-guard/status → ${res.status} (expected 200)`)
        return
    }

    const body = await res.json() as Record<string, unknown>
    if (typeof body.is_locked !== 'boolean') {
        fail('guard.is_locked is not boolean')
    } else {
        pass(`guard.is_locked = ${body.is_locked}`)
    }
}

// ── Main ──────────────────────────────────────────────────────────────

async function main() {
    log('Starting smoke test...')
    log('')

    try {
        await startApi()

        log('')
        log('── Checking endpoints ──')
        log('')

        await assertHealth()
        await assertVersion()
        await assertTrades()
        await assertGuard()

        log('')
        if (failures.length > 0) {
            console.error(`[smoke] ❌ ${failures.length} assertion(s) failed:`)
            for (const f of failures) {
                console.error(`  - ${f}`)
            }
            process.exit(1)
        } else {
            log('🎉 All smoke tests passed!')
            process.exit(0)
        }
    } catch (err) {
        console.error('[smoke] Unexpected error:', err)
        process.exit(1)
    } finally {
        cleanup()
    }
}

// Handle Ctrl+C
process.on('SIGINT', () => {
    cleanup()
    process.exit(130)
})

process.on('SIGTERM', () => {
    cleanup()
    process.exit(143)
})

main()
