import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

// Mock electron app module
vi.mock('electron', () => ({
    app: {
        isPackaged: false,
        on: vi.fn(),
        whenReady: vi.fn().mockResolvedValue(undefined),
        quit: vi.fn(),
    },
    BrowserWindow: vi.fn(),
    ipcMain: { handle: vi.fn(), on: vi.fn() },
}))

// Partial mock for child_process — keep real exports, override spawn
const mockChildProcess = {
    pid: 12345,
    on: vi.fn(),
    kill: vi.fn(),
    stdout: { on: vi.fn() },
    stderr: { on: vi.fn() },
}

vi.mock('child_process', async (importOriginal) => {
    const actual = await importOriginal<typeof import('child_process')>()
    return {
        ...actual,
        spawn: vi.fn(() => mockChildProcess),
    }
})

// Partial mock for net — override createServer
vi.mock('net', async (importOriginal) => {
    const actual = await importOriginal<typeof import('net')>()
    return {
        ...actual,
        createServer: vi.fn(() => ({
            listen: vi.fn(function (this: any, _port: number, cb: () => void) {
                this.address = () => ({ port: 54321 })
                cb()
            }),
            close: vi.fn((cb: () => void) => cb()),
            address: vi.fn(() => ({ port: 54321 })),
        })),
    }
})

// Import after mocks
import { PythonManager } from '../python-manager'

describe('PythonManager', () => {
    let pm: PythonManager

    beforeEach(() => {
        pm = new PythonManager()
    })

    afterEach(() => {
        vi.restoreAllMocks()
    })

    describe('generateToken', () => {
        it('should generate a 64-character hex string', () => {
            const token = pm.generateToken()
            expect(token).toMatch(/^[0-9a-f]{64}$/)
        })

        it('should generate different tokens each time', () => {
            const token1 = pm.generateToken()
            const token2 = pm.generateToken()
            expect(token1).not.toBe(token2)
        })
    })

    describe('allocatePort', () => {
        it('should return a valid port number (>= 1024)', async () => {
            const port = await pm.allocatePort()
            expect(port).toBeGreaterThanOrEqual(1024)
        })

        it('should return a number', async () => {
            const port = await pm.allocatePort()
            expect(typeof port).toBe('number')
            // Value: verify port is a finite integer
            expect(Number.isFinite(port)).toBe(true)
            expect(port % 1).toBe(0)
        })
    })

    describe('waitForReady', () => {
        it('should return false when health check times out', async () => {
            global.fetch = vi.fn().mockRejectedValue(new Error('ECONNREFUSED'))

            const result = await pm.waitForReady(500) // Short timeout for test speed
            expect(result).toBe(false)
        }, 10000)

        it('should return true when health check succeeds', async () => {
            global.fetch = vi.fn().mockResolvedValue({ ok: true })
            pm.generateToken()
            await pm.allocatePort()

            const result = await pm.waitForReady(5000)
            expect(result).toBe(true)
        })

        it('should send Authorization header with Bearer token', async () => {
            const fetchMock = vi.fn()
                .mockRejectedValueOnce(new Error('not ready'))
                .mockResolvedValue({ ok: true })

            global.fetch = fetchMock
            pm.generateToken()
            await pm.allocatePort()

            await pm.waitForReady(10000)
            expect(fetchMock).toHaveBeenCalledWith(
                expect.stringContaining('http://127.0.0.1:'),
                expect.objectContaining({
                    headers: expect.objectContaining({
                        Authorization: expect.stringContaining('Bearer '),
                    }),
                }),
            )
        })
    })

    describe('stop', () => {
        it('should attempt graceful shutdown via /shutdown endpoint', async () => {
            const fetchMock = vi.fn().mockResolvedValue({ ok: true })
            global.fetch = fetchMock

            // Make mock process fire 'exit' immediately when listener is registered
            // so stop() doesn't hang waiting for process exit
            mockChildProcess.on.mockImplementation((event: string, cb: () => void) => {
                if (event === 'exit') {
                    setTimeout(() => cb(), 0)
                }
            })

            pm.generateToken()
            await pm.allocatePort()
            await pm.start()
            await pm.stop()

            expect(fetchMock).toHaveBeenCalledWith(
                expect.stringContaining('/shutdown'),
                expect.objectContaining({ method: 'POST' }),
            )
        }, 10_000)
    })

    describe('getters', () => {
        it('should expose baseUrl', async () => {
            await pm.allocatePort()
            expect(pm.baseUrl).toMatch(/^http:\/\/127\.0\.0\.1:\d+$/)
        })

        it('should expose authToken', () => {
            const token = pm.generateToken()
            expect(pm.authToken).toBe(token)
        })
    })

    describe('setExternalUrl', () => {
        it('should override baseUrl when set', () => {
            pm.setExternalUrl('http://127.0.0.1:8765')
            expect(pm.baseUrl).toBe('http://127.0.0.1:8765')
        })

        it('should take priority over allocated port', async () => {
            await pm.allocatePort()
            pm.setExternalUrl('http://localhost:9999')
            expect(pm.baseUrl).toBe('http://localhost:9999')
        })

        it('should return allocated port URL when not set', async () => {
            await pm.allocatePort()
            expect(pm.baseUrl).not.toBe('http://127.0.0.1:0')
        })
    })
})
