import {
    createRouter,
    createHashHistory,
    createRootRoute,
    createRoute,
    Outlet,
} from '@tanstack/react-router'
import React from 'react'
import AppShell from './components/layout/AppShell'

const hashHistory = createHashHistory()

const rootRoute = createRootRoute({
    component: () => (
        <AppShell>
            <Outlet />
        </AppShell>
    ),
})

// Lazy-loaded feature routes
const accountsRoute = createRoute({
    getParentRoute: () => rootRoute,
    path: '/',
    component: React.lazy(() => import('./features/accounts/AccountsHome')),
})

const tradesRoute = createRoute({
    getParentRoute: () => rootRoute,
    path: '/trades',
    component: React.lazy(() => import('./features/trades/TradesLayout')),
})

const planningRoute = createRoute({
    getParentRoute: () => rootRoute,
    path: '/planning',
    component: React.lazy(() => import('./features/planning/PlanningLayout')),
})

const schedulingRoute = createRoute({
    getParentRoute: () => rootRoute,
    path: '/scheduling',
    component: React.lazy(() => import('./features/scheduling/SchedulingLayout')),
})

const taxRoute = createRoute({
    getParentRoute: () => rootRoute,
    path: '/tax',
    component: React.lazy(() => import('./features/tax/TaxLayout')),
})

const settingsRoute = createRoute({
    getParentRoute: () => rootRoute,
    path: '/settings',
    component: React.lazy(() => import('./features/settings/SettingsLayout')),
})

const settingsMarketRoute = createRoute({
    getParentRoute: () => rootRoute,
    path: '/settings/market',
    component: React.lazy(
        () => import('./features/settings/MarketDataProvidersPage').then(m => ({
            default: m.MarketDataProvidersPage,
        })),
    ),
})

const settingsEmailRoute = createRoute({
    getParentRoute: () => rootRoute,
    path: '/settings/email',
    component: React.lazy(() => import('./features/settings/EmailSettingsPage')),
})

const routeTree = rootRoute.addChildren([
    accountsRoute,
    tradesRoute,
    planningRoute,
    schedulingRoute,
    taxRoute,
    settingsRoute,
    settingsMarketRoute,
    settingsEmailRoute,
])

export const router = createRouter({
    routeTree,
    history: hashHistory,
    defaultPreload: 'intent',
})

// Type-safe router declaration
declare module '@tanstack/react-router' {
    interface Register {
        router: typeof router
    }
}
