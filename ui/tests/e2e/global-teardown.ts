/**
 * Global teardown — kills the Python backend after all E2E tests.
 *
 * Uses tree-kill pattern on Windows (taskkill /T /F) and SIGTERM on Unix.
 */

import { execSync } from 'child_process'

export default async function globalTeardown(): Promise<void> {
    const proc = globalThis.__BACKEND_PROCESS__

    if (!proc || proc.killed) {
        console.log('[e2e] No backend process to stop')
        return
    }

    const pid = proc.pid
    if (!pid) {
        console.log('[e2e] Backend process has no PID')
        return
    }

    console.log(`[e2e] Stopping backend (PID ${pid})...`)

    try {
        if (process.platform === 'win32') {
            // Windows: kill entire process tree
            execSync(`taskkill /PID ${pid} /T /F`, { stdio: 'ignore' })
        } else {
            // Unix: SIGTERM → wait → SIGKILL fallback
            proc.kill('SIGTERM')
            await new Promise<void>((resolve) => {
                const timeout = setTimeout(() => {
                    try {
                        proc.kill('SIGKILL')
                    } catch {
                        // Already dead
                    }
                    resolve()
                }, 5_000)

                proc.on('exit', () => {
                    clearTimeout(timeout)
                    resolve()
                })
            })
        }
        console.log('[e2e] Backend stopped')
    } catch (err) {
        console.warn(`[e2e] Failed to stop backend: ${err}`)
    }
}
