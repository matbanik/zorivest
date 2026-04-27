import { app, BrowserWindow, ipcMain, Menu, shell } from 'electron'

// Runtime guard: detect if running under Node.js instead of Electron
if (typeof app === 'undefined') {
    console.error(
        '\n[FATAL] This script must be run with the Electron binary, not Node.js.\n' +
        '  Correct:   npx electron ./out/main/index.js\n' +
        '  Incorrect: node ./out/main/index.js\n' +
        '\nIf npx electron also fails, ensure the electron npm package is properly\n' +
        'installed and has a valid binary at node_modules/electron/dist/electron.exe.\n'
    )
    process.exit(1)
}

import { join } from 'path'
import Store from 'electron-store'
import { PythonManager } from './python-manager'
import { getStoredBounds, saveWindowBounds } from './window-state'
import {
    generateApprovalToken,
    validateCallbackPayload,
    startCleanupInterval,
} from './approval-token-manager'

/** Build custom application menu with Zorivest-specific Help links */
function createAppMenu(): void {
    const template: Electron.MenuItemConstructorOptions[] = [
        { role: 'fileMenu' },
        { role: 'editMenu' },
        { role: 'viewMenu' },
        { role: 'windowMenu' },
        {
            role: 'help',
            submenu: [
                {
                    label: 'Zorivest on GitHub',
                    click: () => shell.openExternal('https://github.com/matbanik/zorivest'),
                },
                {
                    label: 'Report an Issue',
                    click: () => shell.openExternal('https://github.com/matbanik/zorivest/issues'),
                },
                {
                    label: 'Discord Community',
                    click: () => shell.openExternal('https://discord.gg/aW5RS8g6D7'),
                },
            ],
        },
    ]
    Menu.setApplicationMenu(Menu.buildFromTemplate(template))
}

const pythonManager = new PythonManager()
let mainWindow: BrowserWindow | null = null
let splashWindow: BrowserWindow | null = null
let cleanupTimer: ReturnType<typeof setInterval> | null = null
let validationServer: import('node:http').Server | null = null

/** Create the splash window shown during startup */
function createSplashWindow(): BrowserWindow {
    const splash = new BrowserWindow({
        width: 400,
        height: 300,
        frame: false,
        transparent: false,
        resizable: false,
        show: true,
        icon: join(__dirname, '../../build/icon.ico'),
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
        },
    })

    splash.loadFile(join(__dirname, 'splash.html'))
    return splash
}

/** Create the main application window */
function createMainWindow(): BrowserWindow {
    const storedBounds = getStoredBounds()

    const win = new BrowserWindow({
        width: storedBounds.width,
        height: storedBounds.height,
        ...(storedBounds.x !== undefined && { x: storedBounds.x }),
        ...(storedBounds.y !== undefined && { y: storedBounds.y }),
        minWidth: 1024,
        minHeight: 600,
        show: false,
        backgroundColor: '#282a36',
        icon: join(__dirname, '../../build/icon.ico'),
        webPreferences: {
            preload: join(__dirname, '../preload/index.js'),
            nodeIntegration: false,
            contextIsolation: true,
            sandbox: true,
            webSecurity: true,
        },
    })

    // Debounced save of window bounds on resize/move (500ms)
    let boundsTimer: ReturnType<typeof setTimeout> | null = null
    const debouncedSaveBounds = () => {
        if (boundsTimer) clearTimeout(boundsTimer)
        boundsTimer = setTimeout(() => {
            if (!win.isDestroyed()) {
                const bounds = win.getBounds()
                saveWindowBounds(bounds)
            }
        }, 500)
    }
    win.on('resize', debouncedSaveBounds)
    win.on('move', debouncedSaveBounds)

    // Block external navigation
    win.webContents.on('will-navigate', (event, url) => {
        if (!url.startsWith('file://')) {
            event.preventDefault()
        }
    })

    // Block new window creation
    win.webContents.setWindowOpenHandler(() => ({ action: 'deny' as const }))

    return win
}

/** IPC: Startup performance metrics + preload bridge handlers */
function registerIpcHandlers(): void {
    ipcMain.handle('get-startup-metrics', () => ({
        processStart: process.hrtime.bigint().toString(),
        electronReady: Date.now(),
    }))

    ipcMain.handle('get-backend-url', () => pythonManager.baseUrl)
    ipcMain.handle('get-auth-token', () => pythonManager.authToken)

    // electron-store bridge (renderer → main)
    const rendererStore = new Store({ name: 'zorivest-renderer' })
    ipcMain.handle('electron-store-get', (_event, key: string) => rendererStore.get(key))
    ipcMain.handle('electron-store-set', (_event, key: string, value: unknown) => {
        rendererStore.set(key, value)
    })

    // Renderer startup timing
    ipcMain.handle('log-renderer-ready', (_event, timestamp: number) => {
        console.log(`[startup] renderer ready at ${timestamp}ms`)
    })

    // Open external URLs in the system browser (http/https only)
    ipcMain.handle('open-external', (_event, url: string) => {
        if (typeof url === 'string' && /^https?:\/\//.test(url)) {
            shell.openExternal(url)
        }
    })

    // Approval token IPC (PH11: CSRF approval tokens)
    ipcMain.handle('generate-approval-token', (_event, policyId: string) => {
        return generateApprovalToken(policyId)
    })
}

/** App startup sequence */
app.whenReady().then(async () => {
    registerIpcHandlers()
    createAppMenu()

    // Start approval token cleanup and internal validation HTTP server
    cleanupTimer = startCleanupInterval()
    validationServer = await startApprovalValidationServer()

    const isDev = !!process.env.ELECTRON_RENDERER_URL

    // 1. Show splash immediately
    splashWindow = createSplashWindow()

    // 2. Create main window (hidden)
    mainWindow = createMainWindow()

    let ready: boolean

    if (process.env.ZORIVEST_BACKEND_URL) {
        // External backend: dev mode (concurrently), E2E, or explicit override.
        // Override PythonManager so IPC get-backend-url returns the correct URL.
        pythonManager.setExternalUrl(process.env.ZORIVEST_BACKEND_URL)
        await new Promise((r) => setTimeout(r, 500))
        ready = true
    } else if (isDev) {
        // Dev mode without explicit backend URL — warn but proceed.
        // Use dev:ui-only script or set ZORIVEST_BACKEND_URL for backend access.
        console.warn(
            '[startup] Dev mode: no ZORIVEST_BACKEND_URL set. ' +
            'Backend will be unreachable. Use "npm run dev" to start both processes.',
        )
        await new Promise((r) => setTimeout(r, 1000))
        ready = true
    } else {
        // Production: start Python backend and wait for health check
        pythonManager.generateToken()
        await pythonManager.allocatePort()
        await pythonManager.start()
        ready = await pythonManager.waitForReady(30_000)
    }

    if (ready) {
        // Show main window, hide splash
        if (process.env.ELECTRON_RENDERER_URL) {
            mainWindow.loadURL(process.env.ELECTRON_RENDERER_URL)
        } else {
            mainWindow.loadFile(join(__dirname, '../renderer/index.html'))
        }

        mainWindow.once('ready-to-show', () => {
            splashWindow?.close()
            splashWindow = null
            mainWindow?.show()
        })
    } else {
        // On timeout: show error in splash, do NOT show main window
        splashWindow?.webContents.executeJavaScript(`
      document.getElementById('loading').style.display = 'none';
      document.getElementById('status').style.display = 'none';
      document.getElementById('error-container').style.display = 'flex';
    `)
    }
})

// Quit when all windows closed (Windows/Linux)
app.on('window-all-closed', () => {
    pythonManager.stop()
    app.quit()
})

// Graceful shutdown
app.on('before-quit', async () => {
    if (cleanupTimer) clearInterval(cleanupTimer)
    if (validationServer) validationServer.close()
    await pythonManager.stop()
})

// ── Internal Approval Token Validation HTTP Server ──────────────────────

/** Default port for the internal approval token validation server (127.0.0.1 only). */
const APPROVAL_CALLBACK_DEFAULT_PORT = 17788

async function startApprovalValidationServer(): Promise<import('node:http').Server> {
    const http = await import('node:http')

    const server = http.createServer((req, res) => {
        if (req.method === 'POST' && req.url === '/internal/validate-token') {
            let body = ''
            req.on('data', (chunk: Buffer) => { body += chunk.toString() })
            req.on('end', () => {
                try {
                    const parsed = JSON.parse(body)
                    const result = validateCallbackPayload(parsed)
                    const statusCode = result.valid || result.reason !== 'EXTRA_FIELDS' && result.reason !== 'INVALID_TYPES' ? 200 : 400
                    res.writeHead(statusCode, { 'Content-Type': 'application/json' })
                    res.end(JSON.stringify(result))
                } catch {
                    res.writeHead(400, { 'Content-Type': 'application/json' })
                    res.end(JSON.stringify({ valid: false, reason: 'PARSE_ERROR' }))
                }
            })
        } else {
            res.writeHead(404)
            res.end()
        }
    })

    // Use well-known port so the API process can find us in dev mode
    // (concurrently starts API and Electron as sibling processes, so
    // process.env changes in Electron don't reach the API).
    const port = parseInt(
        process.env.ZORIVEST_APPROVAL_CALLBACK_PORT || String(APPROVAL_CALLBACK_DEFAULT_PORT),
        10,
    )

    return new Promise((resolve, reject) => {
        server.on('error', (err: NodeJS.ErrnoException) => {
            if (err.code === 'EADDRINUSE') {
                console.warn(`[approval] Port ${port} in use — falling back to random port`)
                server.listen(0, '127.0.0.1', () => {
                    const addr = server.address() as import('node:net').AddressInfo
                    process.env.ZORIVEST_APPROVAL_CALLBACK_PORT = String(addr.port)
                    console.log(`[approval] Internal validation server on 127.0.0.1:${addr.port}`)
                    resolve(server)
                })
            } else {
                reject(err)
            }
        })
        server.listen(port, '127.0.0.1', () => {
            process.env.ZORIVEST_APPROVAL_CALLBACK_PORT = String(port)
            console.log(`[approval] Internal validation server on 127.0.0.1:${port}`)
            resolve(server)
        })
    })
}
