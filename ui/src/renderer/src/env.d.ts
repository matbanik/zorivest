/// <reference types="vite/client" />

interface ElectronStoreAPI {
    get(key: string): unknown
    set(key: string, value: unknown): void
}

interface ElectronAPI {
    baseUrl: string
    token: string
    init(): Promise<void>
}

interface StartupMetricsAPI {
    getMetrics(): Promise<{ processStart: string; electronReady: number }>
    logRendererReady(): void
}

interface Window {
    api: ElectronAPI
    electronStore: ElectronStoreAPI
    startupMetrics: StartupMetricsAPI
}
