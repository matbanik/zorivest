import React, { Suspense, useEffect } from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClientProvider } from '@tanstack/react-query'
import { RouterProvider } from '@tanstack/react-router'
import { queryClient } from './lib/query-client'
import { router } from './router'
import { NotificationProvider } from './hooks/useNotifications'
import ModuleSkeleton from './components/ModuleSkeleton'
import './globals.css'
import './styles/form-guard.css'

function App() {
    // Initialize preload bridge — fetch backend URL and auth token from main process
    useEffect(() => {
        if (window.api?.init) {
            window.api.init().catch((err: unknown) => {
                console.warn('[startup] api.init() failed:', err)
            })
        }
    }, [])

    return (
        <QueryClientProvider client={queryClient}>
            <NotificationProvider>
                <Suspense fallback={<ModuleSkeleton />}>
                    <RouterProvider router={router} />
                </Suspense>
            </NotificationProvider>
        </QueryClientProvider>
    )
}

const rootEl = document.getElementById('root')
if (rootEl) {
    createRoot(rootEl).render(
        <React.StrictMode>
            <App />
        </React.StrictMode>,
    )
}
