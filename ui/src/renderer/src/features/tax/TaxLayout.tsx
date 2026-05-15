/**
 * TaxLayout — main tab container for the Tax feature.
 *
 * Renders 7 tabs: Dashboard, Lots, Wash Sales, Simulator, Harvesting, Quarterly, Audit
 * Follows SchedulingLayout tabbed pattern with G23 form guard.
 *
 * Source: 06g-gui-tax.md §Quick Actions L56–58
 * MEU: MEU-154 (gui-tax)
 */

import { useState, Suspense, lazy, useCallback } from 'react'
import { TAX_TEST_IDS } from './test-ids'
import TaxDisclaimer from './TaxDisclaimer'
import { useFormGuard } from '@/hooks/useFormGuard'
import UnsavedChangesModal from '@/components/UnsavedChangesModal'

// Lazy-loaded tab components
const TaxDashboard = lazy(() => import('./TaxDashboard'))
const TaxLotViewer = lazy(() => import('./TaxLotViewer'))
const WashSaleMonitor = lazy(() => import('./WashSaleMonitor'))
const WhatIfSimulator = lazy(() => import('./WhatIfSimulator'))
const LossHarvestingTool = lazy(() => import('./LossHarvestingTool'))
const QuarterlyTracker = lazy(() => import('./QuarterlyTracker'))
const TransactionAudit = lazy(() => import('./TransactionAudit'))

const TAX_TABS = [
    'Dashboard',
    'Lots',
    'Wash Sales',
    'Simulator',
    'Harvesting',
    'Quarterly',
    'Audit',
] as const

type TaxTab = typeof TAX_TABS[number]

const TAB_COMPONENTS: Record<TaxTab, React.LazyExoticComponent<React.ComponentType<{ onDirtyChange?: (dirty: boolean) => void }>>> = {
    Dashboard: TaxDashboard as React.LazyExoticComponent<React.ComponentType<{ onDirtyChange?: (dirty: boolean) => void }>>,
    Lots: TaxLotViewer as React.LazyExoticComponent<React.ComponentType<{ onDirtyChange?: (dirty: boolean) => void }>>,
    'Wash Sales': WashSaleMonitor as React.LazyExoticComponent<React.ComponentType<{ onDirtyChange?: (dirty: boolean) => void }>>,
    Simulator: WhatIfSimulator as React.LazyExoticComponent<React.ComponentType<{ onDirtyChange?: (dirty: boolean) => void }>>,
    Harvesting: LossHarvestingTool as React.LazyExoticComponent<React.ComponentType<{ onDirtyChange?: (dirty: boolean) => void }>>,
    Quarterly: QuarterlyTracker as React.LazyExoticComponent<React.ComponentType<{ onDirtyChange?: (dirty: boolean) => void }>>,
    Audit: TransactionAudit as React.LazyExoticComponent<React.ComponentType<{ onDirtyChange?: (dirty: boolean) => void }>>,
}

/** Tabs that can have dirty form state requiring G23 guard. */
const GUARDED_TABS: ReadonlySet<TaxTab> = new Set(['Simulator', 'Quarterly'])

export default function TaxLayout() {
    const [activeTab, setActiveTab] = useState<TaxTab>('Dashboard')
    const [childDirty, setChildDirty] = useState(false)

    // G23: form guard for dirty tab switching
    const onNavigate = useCallback((tab: TaxTab) => {
        setChildDirty(false)
        setActiveTab(tab)
    }, [])

    const { showModal, guardedSelect, handleCancel, handleDiscard } =
        useFormGuard<TaxTab>({
            isDirty: childDirty,
            onNavigate,
        })

    // Callback for child components to report dirty state
    const handleDirtyChange = useCallback((dirty: boolean) => {
        setChildDirty(dirty)
    }, [])

    const ActiveComponent = TAB_COMPONENTS[activeTab]
    const isGuardedTab = GUARDED_TABS.has(activeTab)

    return (
        <div data-testid={TAX_TEST_IDS.ROOT} className="flex flex-col h-full">
            {/* Tab Bar */}
            <div className="flex border-b border-bg-subtle px-4 shrink-0">
                {TAX_TABS.map((tab) => (
                    <button
                        key={tab}
                        data-testid={`${TAX_TEST_IDS.TAB}-${tab.toLowerCase().replace(/\s+/g, '-')}`}
                        onClick={() => guardedSelect(tab)}
                        className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors cursor-pointer ${
                            activeTab === tab
                                ? 'text-accent border-accent'
                                : 'text-fg-muted border-transparent hover:text-fg'
                        }`}
                    >
                        {tab}
                    </button>
                ))}
            </div>

            {/* Disclaimer */}
            <TaxDisclaimer className="mx-4 mt-3" />

            {/* Tab Content */}
            <div className="flex-1 overflow-auto p-4">
                <Suspense
                    fallback={
                        <div className="flex items-center justify-center h-32 text-fg-muted text-sm">
                            Loading…
                        </div>
                    }
                >
                    <ActiveComponent
                        onDirtyChange={isGuardedTab ? handleDirtyChange : undefined}
                    />
                </Suspense>
            </div>

            {/* G23: Unsaved changes modal */}
            <UnsavedChangesModal
                open={showModal}
                onCancel={handleCancel}
                onDiscard={handleDiscard}
            />
        </div>
    )
}
