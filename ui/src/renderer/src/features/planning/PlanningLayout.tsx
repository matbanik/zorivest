import { useState } from 'react'
import TradePlanPage from './TradePlanPage'
import WatchlistPage from './WatchlistPage'

const TABS = ['Trade Plans', 'Watchlists'] as const
type Tab = typeof TABS[number]

export default function PlanningLayout() {
    const [activeTab, setActiveTab] = useState<Tab>('Trade Plans')

    const handleOpenCalculator = () => {
        window.dispatchEvent(new CustomEvent('zorivest:open-calculator'))
    }

    return (
        <div className="h-full flex flex-col" data-testid="planning-layout">
            {/* Tab Bar */}
            <div className="flex border-b border-bg-subtle px-4" data-testid="planning-tabs">
                {TABS.map((tab) => (
                    <button
                        key={tab}
                        data-testid={`planning-tab-${tab.toLowerCase().replace(' ', '-')}`}
                        onClick={() => setActiveTab(tab)}
                        className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors cursor-pointer ${activeTab === tab
                            ? 'text-accent border-accent'
                            : 'text-fg-muted border-transparent hover:text-fg'
                            }`}
                    >
                        {tab}
                    </button>
                ))}
            </div>

            {/* Tab Content */}
            <div className="flex-1 overflow-hidden">
                {activeTab === 'Trade Plans' && (
                    <TradePlanPage onOpenCalculator={handleOpenCalculator} />
                )}
                {activeTab === 'Watchlists' && <WatchlistPage />}
            </div>
        </div>
    )
}
