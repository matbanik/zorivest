import { spawn, ChildProcess } from 'child_process'
import { createServer } from 'net'
import { randomBytes } from 'crypto'
import { join } from 'path'
import { app } from 'electron'

/**
 * PythonManager — manages the Python FastAPI backend lifecycle.
 *
 * Responsibilities:
 * - Generate ephemeral Bearer token for UI↔API auth
 * - Allocate a free port dynamically
 * - Spawn Python subprocess
 * - Health check with exponential backoff
 * - Graceful shutdown
 */
export class PythonManager {
    private process: ChildProcess | null = null
    private port: number = 0
    private token: string = ''

    /** Generate ephemeral Bearer token (64 hex chars = 32 random bytes) */
    generateToken(): string {
        this.token = randomBytes(32).toString('hex')
        return this.token
    }

    /** Allocate a free port dynamically via net.createServer */
    async allocatePort(): Promise<number> {
        return new Promise((resolve) => {
            const srv = createServer()
            srv.listen(0, () => {
                this.port = (srv.address() as { port: number }).port
                srv.close(() => resolve(this.port))
            })
        })
    }

    /** Spawn Python subprocess with token and port */
    async start(): Promise<void> {
        const pythonPath = app.isPackaged
            ? join(process.resourcesPath, 'python', 'zorivest.exe')
            : 'uv'

        const args = app.isPackaged
            ? ['--port', String(this.port), '--token', this.token]
            : [
                'run',
                'uvicorn',
                'zorivest.api.app:create_app',
                '--factory',
                '--port',
                String(this.port),
                '--host',
                '127.0.0.1',
            ]

        // Pass token via environment variable for dev mode
        const env = {
            ...process.env,
            ZORIVEST_AUTH_TOKEN: this.token,
        }

        this.process = spawn(pythonPath, args, {
            stdio: app.isPackaged ? 'ignore' : 'pipe',
            env,
        })

        this.process.on('error', (err) => {
            console.error('[PythonManager] spawn error:', err.message)
        })
    }

    /** Health check with exponential backoff (100ms → 5s cap) */
    async waitForReady(maxWaitMs = 30_000): Promise<boolean> {
        const startTime = Date.now()
        let delay = 100

        while (Date.now() - startTime < maxWaitMs) {
            try {
                const res = await fetch(`http://127.0.0.1:${this.port}/health`, {
                    headers: { Authorization: `Bearer ${this.token}` },
                })
                if (res.ok) return true
            } catch {
                // Python not ready yet — wait and retry
            }
            await new Promise((r) => setTimeout(r, delay))
            delay = Math.min(delay * 2, 5_000) // Cap at 5s
        }
        return false
    }

    /** Graceful shutdown: POST /shutdown then wait up to 5s */
    async stop(): Promise<void> {
        if (!this.process) return
        try {
            await fetch(`http://127.0.0.1:${this.port}/shutdown`, {
                method: 'POST',
                headers: { Authorization: `Bearer ${this.token}` },
            })
            // Wait up to 5s for graceful exit
            await new Promise<void>((resolve) => {
                const timer = setTimeout(() => {
                    this.process?.kill()
                    resolve()
                }, 5_000)
                this.process?.on('exit', () => {
                    clearTimeout(timer)
                    resolve()
                })
            })
        } catch {
            this.process?.kill()
        }
        this.process = null
    }

    get baseUrl(): string {
        return `http://127.0.0.1:${this.port}`
    }

    get authToken(): string {
        return this.token
    }
}
