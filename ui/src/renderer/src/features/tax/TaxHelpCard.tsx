/**
 * TaxHelpCard — Collapsible "How It Works" info card for Tax feature tabs.
 *
 * Implements the WAI-ARIA disclosure pattern with localStorage persistence.
 * Users can collapse (toggle body) or dismiss (hide entirely) the card.
 * A small "ℹ️" button re-shows the card when dismissed.
 *
 * Pattern: Progressive disclosure — expanded on first visit, remembers state.
 * Accessibility: aria-expanded, aria-controls, aria-label, aria-labelledby.
 *
 * MEU: MEU-218i (Tax Help Cards)
 */

import { useState, useCallback, useId } from 'react'
import type { TaxHelpContent } from './tax-help-content'

// ── localStorage helpers ──────────────────────────────────────────

type CardState = 'expanded' | 'collapsed' | 'dismissed'

function getStoredState(tabKey: string): CardState {
    try {
        const raw = localStorage.getItem(`zorivest:tax-help:${tabKey}:state`)
        if (raw === 'expanded' || raw === 'collapsed' || raw === 'dismissed') return raw
    } catch {
        // localStorage unavailable (SSR, permissions) — fail open
    }
    return 'expanded' // First visit default
}

function setStoredState(tabKey: string, state: CardState): void {
    try {
        localStorage.setItem(`zorivest:tax-help:${tabKey}:state`, state)
    } catch {
        // Silently fail — cosmetic preference only
    }
}

// ── Component ─────────────────────────────────────────────────────

interface TaxHelpCardProps {
    content: TaxHelpContent
}

export default function TaxHelpCard({ content }: TaxHelpCardProps) {
    const [state, setState] = useState<CardState>(() => getStoredState(content.tabKey))
    const uid = useId()

    const titleId = `tax-help-title-${uid}`
    const contentId = `tax-help-content-${uid}`

    const isExpanded = state === 'expanded'
    const isDismissed = state === 'dismissed'

    const handleToggle = useCallback(() => {
        const next: CardState = isExpanded ? 'collapsed' : 'expanded'
        setState(next)
        setStoredState(content.tabKey, next)
    }, [isExpanded, content.tabKey])

    const handleDismiss = useCallback(() => {
        setState('dismissed')
        setStoredState(content.tabKey, 'dismissed')
    }, [content.tabKey])

    const handleReshow = useCallback(() => {
        setState('expanded')
        setStoredState(content.tabKey, 'expanded')
    }, [content.tabKey])

    // ── Dismissed state: small re-show button ──
    if (isDismissed) {
        return (
            <div className="mb-4">
                <button
                    onClick={handleReshow}
                    aria-label="Show feature help"
                    className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs text-fg-muted hover:text-fg bg-bg-elevated border border-bg-subtle rounded-md transition-colors cursor-pointer"
                >
                    <span aria-hidden="true">ℹ️</span>
                    <span>How it works</span>
                </button>
            </div>
        )
    }

    // ── Visible card (expanded or collapsed) ──
    return (
        <section
            aria-labelledby={titleId}
            data-testid={`tax-help-card-${content.tabKey}`}
            className="mb-5 rounded-lg border border-accent/20 bg-accent/5 overflow-hidden"
        >
            {/* Header — always visible */}
            <div className="flex items-center justify-between px-4 py-2.5">
                <button
                    onClick={handleToggle}
                    aria-expanded={isExpanded}
                    aria-controls={contentId}
                    className="flex items-center gap-2 text-sm font-medium text-fg hover:text-accent transition-colors cursor-pointer"
                >
                    <span aria-hidden="true">ℹ️</span>
                    <h3 id={titleId} className="text-sm font-medium">How This Works</h3>
                    <svg
                        className={`w-3.5 h-3.5 text-fg-muted transition-transform duration-200 ${isExpanded ? 'rotate-180' : ''}`}
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                        strokeWidth={2}
                        aria-hidden="true"
                    >
                        <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
                    </svg>
                </button>
                <button
                    onClick={handleDismiss}
                    aria-label="Dismiss help card"
                    className="text-fg-muted hover:text-fg text-xs px-1.5 py-0.5 rounded transition-colors cursor-pointer"
                >
                    ✕
                </button>
            </div>

            {/* Body — collapsible */}
            {isExpanded && (
                <div id={contentId} className="px-4 pb-4 space-y-3">
                    <div>
                        <dt className="text-xs font-semibold text-fg-muted uppercase tracking-wider mb-0.5">
                            What this shows
                        </dt>
                        <dd className="text-sm text-fg leading-relaxed">
                            {content.what}
                        </dd>
                    </div>
                    <div>
                        <dt className="text-xs font-semibold text-fg-muted uppercase tracking-wider mb-0.5">
                            Where data comes from
                        </dt>
                        <dd className="text-sm text-fg leading-relaxed">
                            {content.source}
                        </dd>
                    </div>
                    <div>
                        <dt className="text-xs font-semibold text-fg-muted uppercase tracking-wider mb-0.5">
                            How values are calculated
                        </dt>
                        <dd className="text-sm text-fg leading-relaxed">
                            {content.calculation}
                        </dd>
                    </div>
                    {content.learnMoreUrl && (
                        <div className="pt-1">
                            <button
                                onClick={() => window.electron.openExternal(content.learnMoreUrl)}
                                className="inline-flex items-center gap-1 text-xs text-accent hover:text-accent/80 transition-colors cursor-pointer bg-transparent border-none p-0"
                            >
                                <span aria-hidden="true">📚</span>
                                {content.learnMoreLabel}
                                <svg
                                    className="w-3 h-3"
                                    fill="none"
                                    viewBox="0 0 24 24"
                                    stroke="currentColor"
                                    strokeWidth={2}
                                    aria-hidden="true"
                                >
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                                </svg>
                            </button>
                        </div>
                    )}
                </div>
            )}
        </section>
    )
}
