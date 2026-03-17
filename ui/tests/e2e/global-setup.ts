/**
 * Global setup — spawns the Python backend before E2E tests.
 *
 * The backend must be healthy at /api/v1/health before tests proceed.
 * PID is stored globally so global-teardown.ts can kill it.
 */

import { spawn, type ChildProcess } from 'child_process'

const BACKEND_PORT = 8765
const BACKEND_URL = `http://localhost:${BACKEND_PORT}`
const HEALTH_URL = `${BACKEND_URL}/api/v1/health`
const MAX_WAIT_MS = 30_000
const POLL_INTERVAL_MS = 500

/** Stored globally for teardown access. */
declare global {
    // eslint-disable-next-line no-var
    var __BACKEND_PROCESS__: ChildProcess | undefined
    // eslint-disable-next-line no-var
    var __BACKEND_URL__: string
}

async function waitForHealth(url: string, timeoutMs: number): Promise<boolean> {
    const deadline = Date.now() + timeoutMs
    while (Date.now() < deadline) {
        try {
            const res = await fetch(url)
            if (res.ok) return true
        } catch {
            // Backend not ready yet
        }
        await new Promise((r) => setTimeout(r, POLL_INTERVAL_MS))
    }
    return false
}

export default async function globalSetup(): Promise<void> {
    // Skip backend spawn if already running (e.g. dev mode)
    try {
        const res = await fetch(HEALTH_URL)
        if (res.ok) {
            console.log('[e2e] Backend already running, skipping spawn')
            globalThis.__BACKEND_URL__ = BACKEND_URL
            return
        }
    } catch {
        // Not running — spawn it
    }

    console.log('[e2e] Starting Python backend...')
    const proc = spawn(
        'uv',
        [
            'run',
            'uvicorn',
            'zorivest_api.main:app',
            '--host', '127.0.0.1',
            '--port', String(BACKEND_PORT),
            '--no-access-log',
        ],
        {
            cwd: process.env.ZORIVEST_ROOT || process.cwd().replace(/[\\/]ui$/, ''),
            stdio: ['ignore', 'pipe', 'pipe'],
            shell: true,
        },
    )

    proc.stdout?.on('data', (data) => {
        const msg = data.toString().trim()
        if (msg) console.log(`[backend] ${msg}`)
    })

    proc.stderr?.on('data', (data) => {
        const msg = data.toString().trim()
        if (msg) console.error(`[backend:err] ${msg}`)
    })

    globalThis.__BACKEND_PROCESS__ = proc
    globalThis.__BACKEND_URL__ = BACKEND_URL

    const ready = await waitForHealth(HEALTH_URL, MAX_WAIT_MS)
    if (!ready) {
        proc.kill('SIGTERM')
        throw new Error(
            `[e2e] Backend failed to become healthy within ${MAX_WAIT_MS}ms`,
        )
    }

    console.log('[e2e] Backend is healthy')
}
