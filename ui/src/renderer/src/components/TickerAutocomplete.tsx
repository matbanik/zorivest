import { useState, useCallback, useRef, useEffect } from 'react'
import { apiFetch } from '@/lib/api'

// ── Types ────────────────────────────────────────────────────────────────

interface TickerSearchResult {
    symbol: string
    name: string
    exchange?: string
    currency?: string
    provider: string
}

interface TickerAutocompleteProps {
    value: string
    onChange: (ticker: string) => void
    onSelect?: (result: TickerSearchResult) => void
    placeholder?: string
    'data-testid'?: string
    className?: string
    disabled?: boolean
}

// ── Component ────────────────────────────────────────────────────────────

/**
 * Shared ticker autocomplete input with debounced search.
 * Calls GET /api/v1/market-data/search?query=... and shows dropdown results.
 * Works with the stub (returns []) and will show real results when MEU-65 wires a provider.
 *
 * Used by: Calculator (C4), TradePlan ticker (T1), Watchlist add-ticker (W1).
 */
export default function TickerAutocomplete({
    value,
    onChange,
    onSelect,
    placeholder = 'Search ticker...',
    'data-testid': testId = 'ticker-autocomplete',
    className = '',
    disabled = false,
}: TickerAutocompleteProps) {
    const [results, setResults] = useState<TickerSearchResult[]>([])
    const [isOpen, setIsOpen] = useState(false)
    const [isLoading, setIsLoading] = useState(false)
    const [highlightIndex, setHighlightIndex] = useState(-1)
    const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)
    const containerRef = useRef<HTMLDivElement>(null)

    // Debounced search (300ms)
    const handleInputChange = useCallback(
        (newValue: string) => {
            onChange(newValue)
            setHighlightIndex(-1)

            if (debounceRef.current) clearTimeout(debounceRef.current)

            if (newValue.trim().length < 1) {
                setResults([])
                setIsOpen(false)
                return
            }

            debounceRef.current = setTimeout(async () => {
                try {
                    setIsLoading(true)
                    const data = await apiFetch<TickerSearchResult[]>(
                        `/api/v1/market-data/search?query=${encodeURIComponent(newValue.trim())}`,
                    )
                    setResults(data ?? [])
                    setIsOpen((data ?? []).length > 0)
                } catch {
                    setResults([])
                    setIsOpen(false)
                } finally {
                    setIsLoading(false)
                }
            }, 300)
        },
        [onChange],
    )

    // Select a result
    const handleSelect = useCallback(
        (result: TickerSearchResult) => {
            onChange(result.symbol)
            onSelect?.(result)
            setIsOpen(false)
            setResults([])
        },
        [onChange, onSelect],
    )

    // Keyboard navigation
    const handleKeyDown = useCallback(
        (e: React.KeyboardEvent) => {
            if (!isOpen || results.length === 0) return

            if (e.key === 'ArrowDown') {
                e.preventDefault()
                setHighlightIndex((prev) => Math.min(prev + 1, results.length - 1))
            } else if (e.key === 'ArrowUp') {
                e.preventDefault()
                setHighlightIndex((prev) => Math.max(prev - 1, 0))
            } else if (e.key === 'Enter' && highlightIndex >= 0) {
                e.preventDefault()
                handleSelect(results[highlightIndex])
            } else if (e.key === 'Escape') {
                setIsOpen(false)
            }
        },
        [isOpen, results, highlightIndex, handleSelect],
    )

    // Click outside to close
    useEffect(() => {
        const handler = (e: MouseEvent) => {
            if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
                setIsOpen(false)
            }
        }
        document.addEventListener('mousedown', handler)
        return () => document.removeEventListener('mousedown', handler)
    }, [])

    // Cleanup debounce on unmount
    useEffect(() => {
        return () => {
            if (debounceRef.current) clearTimeout(debounceRef.current)
        }
    }, [])

    return (
        <div ref={containerRef} className="relative" data-testid={testId}>
            <input
                type="text"
                value={value}
                onChange={(e) => handleInputChange(e.target.value)}
                onKeyDown={handleKeyDown}
                onFocus={() => results.length > 0 && setIsOpen(true)}
                placeholder={placeholder}
                disabled={disabled}
                data-testid={`${testId}-input`}
                className={`w-full px-3 py-1.5 text-sm rounded-md bg-bg border border-bg-subtle text-fg ${className}`}
            />
            {isLoading && (
                <span
                    className="absolute right-2 top-1/2 -translate-y-1/2 text-xs text-fg-muted"
                    data-testid={`${testId}-loading`}
                >
                    ⏳
                </span>
            )}

            {/* Dropdown results */}
            {isOpen && results.length > 0 && (
                <ul
                    className="absolute z-50 w-full mt-1 max-h-48 overflow-y-auto rounded-md border border-bg-subtle bg-bg-elevated shadow-lg"
                    data-testid={`${testId}-dropdown`}
                    role="listbox"
                >
                    {results.map((result, idx) => (
                        <li
                            key={`${result.symbol}-${result.provider}`}
                            role="option"
                            aria-selected={idx === highlightIndex}
                            data-testid={`${testId}-option-${result.symbol}`}
                            className={`px-3 py-2 text-sm cursor-pointer transition-colors ${idx === highlightIndex
                                    ? 'bg-accent/20 text-fg'
                                    : 'text-fg hover:bg-bg-subtle'
                                }`}
                            onMouseDown={() => handleSelect(result)}
                            onMouseEnter={() => setHighlightIndex(idx)}
                        >
                            <div className="flex items-center justify-between">
                                <span className="font-medium">{result.symbol}</span>
                                {result.exchange && (
                                    <span className="text-xs text-fg-muted">{result.exchange}</span>
                                )}
                            </div>
                            <div className="text-xs text-fg-muted truncate">{result.name}</div>
                        </li>
                    ))}
                </ul>
            )}
        </div>
    )
}
