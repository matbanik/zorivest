import { contextBridge, ipcRenderer } from 'electron'

/**
 * Preload bridge — exposes safe APIs to the renderer process.
 * Security: contextIsolation=true, sandbox=true, nodeIntegration=false
 */

// Internal storage for IPC-fetched values
let __baseUrl = 'http://127.0.0.1:8765'
let __token = ''

contextBridge.exposeInMainWorld('api', {
    get baseUrl(): string {
        return __baseUrl
    },
    get token(): string {
        return __token
    },
    /** Initialize the bridge by fetching backend URL and token from main process */
    async init(): Promise<void> {
        __baseUrl = await ipcRenderer.invoke('get-backend-url')
        __token = await ipcRenderer.invoke('get-auth-token')
    },
})

contextBridge.exposeInMainWorld('electronStore', {
    get(key: string): unknown {
        return ipcRenderer.invoke('electron-store-get', key)
    },
    set(key: string, value: unknown): void {
        ipcRenderer.invoke('electron-store-set', key, value)
    },
})

contextBridge.exposeInMainWorld('startupMetrics', {
    async getMetrics(): Promise<{ processStart: string; electronReady: number }> {
        return ipcRenderer.invoke('get-startup-metrics')
    },
    logRendererReady(): void {
        ipcRenderer.invoke('log-renderer-ready', Date.now())
    },
})
