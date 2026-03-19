import React, { useState, useRef, useEffect, useMemo, useCallback } from 'react'
import Fuse from 'fuse.js'
import { useNavigate } from '@tanstack/react-router'
import { createStaticEntries } from '../registry/commandRegistry'
import { useDynamicEntries } from '../registry/useDynamicEntries'
import type { CommandRegistryEntry } from '../registry/types'

interface CommandPaletteProps {
    open: boolean
    onClose: () => void
}

const categoryLabels: Record<string, string> = {
    navigation: 'Navigation',
    action: 'Actions',
    settings: 'Settings',
    search: 'Search',
}

/**
 * CommandPalette — overlay with fuzzy search, keyboard navigation, category grouping.
 * Per 06a-gui-shell.md §CommandPalette Component.
 */
export default function CommandPalette({ open, onClose }: CommandPaletteProps) {
    const [query, setQuery] = useState('')
    const [selectedIndex, setSelectedIndex] = useState(-1)
    const inputRef = useRef<HTMLInputElement>(null)
    const listRef = useRef<HTMLDivElement>(null)

    const navigate = useNavigate()
    const navCallback = useCallback((path: string) => navigate({ to: path }), [navigate])
    const staticEntries = useMemo(() => createStaticEntries(navCallback), [navCallback])
    const dynamicEntries = useDynamicEntries(navCallback)
    const allEntries = useMemo(
        () => [...staticEntries, ...dynamicEntries],
        [staticEntries, dynamicEntries],
    )

    const fuse = useMemo(
        () =>
            new Fuse(allEntries, {
                keys: ['label', 'keywords'],
                threshold: 0.4,
            }),
        [allEntries],
    )

    // Filter results
    const results = useMemo(() => {
        if (!query.trim()) return allEntries
        return fuse.search(query).map((r) => r.item)
    }, [query, fuse, allEntries])

    // Group by category for display
    const grouped = useMemo(() => {
        const groups = new Map<string, CommandRegistryEntry[]>()
        for (const entry of results) {
            const list = groups.get(entry.category) ?? []
            list.push(entry)
            groups.set(entry.category, list)
        }
        return groups
    }, [results])

    // Flat list for keyboard navigation
    const flatResults = useMemo(() => {
        const items: CommandRegistryEntry[] = []
        for (const [, entries] of grouped) {
            items.push(...entries)
        }
        return items
    }, [grouped])

    // Focus input when opened
    useEffect(() => {
        if (open) {
            setQuery('')
            setSelectedIndex(-1)
            setTimeout(() => inputRef.current?.focus(), 50)
        }
    }, [open])

    // Scroll selected item into view
    useEffect(() => {
        if (selectedIndex >= 0 && listRef.current) {
            const item = listRef.current.querySelector(`[data-index="${selectedIndex}"]`)
            if (item && typeof item.scrollIntoView === 'function') {
                item.scrollIntoView({ block: 'nearest' })
            }
        }
    }, [selectedIndex])

    const executeEntry = useCallback(
        (entry: CommandRegistryEntry) => {
            entry.action()
            onClose()
        },
        [onClose],
    )

    // Use ref to avoid stale closure in handleKeyDown
    const selectedIndexRef = useRef(selectedIndex)
    selectedIndexRef.current = selectedIndex

    const flatResultsRef = useRef(flatResults)
    flatResultsRef.current = flatResults

    const handleKeyDown = useCallback(
        (e: React.KeyboardEvent) => {
            switch (e.key) {
                case 'Escape':
                    e.preventDefault()
                    onClose()
                    break
                case 'ArrowDown':
                    e.preventDefault()
                    setSelectedIndex((i) => Math.min(i + 1, flatResultsRef.current.length - 1))
                    break
                case 'ArrowUp':
                    e.preventDefault()
                    setSelectedIndex((i) => Math.max(i - 1, 0))
                    break
                case 'Enter': {
                    e.preventDefault()
                    const idx = selectedIndexRef.current
                    const entry = flatResultsRef.current[idx]
                    if (idx >= 0 && entry) {
                        executeEntry(entry)
                    }
                    break
                }
            }
        },
        [executeEntry, onClose],
    )

    if (!open) return null

    let flatIndex = -1

    return (
        <div
            role="dialog"
            aria-label="Command Palette"
            className="fixed inset-0 z-50 flex items-start justify-center pt-[20vh]"
            onClick={onClose}
        >
            {/* Backdrop */}
            <div className="absolute inset-0 bg-black/50" />

            {/* Palette */}
            <div
                className="relative w-[520px] max-h-[60vh] bg-bg-elevated border border-bg-subtle rounded-lg shadow-2xl overflow-hidden flex flex-col"
                onClick={(e) => e.stopPropagation()}
            >
                {/* Search input */}
                <div className="p-3 border-b border-bg-subtle">
                    <input
                        ref={inputRef}
                        type="search"
                        role="searchbox"
                        placeholder="Type a command…"
                        value={query}
                        onChange={(e) => {
                            setQuery(e.target.value)
                            setSelectedIndex(-1)
                        }}
                        onKeyDown={handleKeyDown}
                        className="w-full bg-transparent text-fg text-sm outline-none placeholder:text-fg-muted"
                    />
                </div>

                {/* Results */}
                <div
                    ref={listRef}
                    role="listbox"
                    className="overflow-y-auto p-1"
                >
                    {Array.from(grouped.entries()).map(([category, entries]) => (
                        <div key={category}>
                            <div className="px-3 py-1.5 text-xs font-semibold text-fg-muted uppercase tracking-wider">
                                {categoryLabels[category] ?? category}
                            </div>
                            {entries.map((entry) => {
                                flatIndex++
                                const idx = flatIndex
                                const isSelected = idx === selectedIndex
                                const Icon = entry.icon
                                return (
                                    <div
                                        key={entry.id}
                                        role="option"
                                        aria-selected={isSelected}
                                        data-index={idx}
                                        onClick={() => executeEntry(entry)}
                                        className={`flex items-center gap-3 px-3 py-2 rounded-md cursor-pointer text-sm transition-colors
                      ${isSelected ? 'bg-accent-cyan/20 text-fg' : 'text-fg-muted hover:bg-bg-subtle/50 hover:text-fg'}`}
                                    >
                                        {Icon && <Icon size={16} aria-hidden="true" />}
                                        <span className="flex-1">{entry.label}</span>
                                        {entry.shortcut && (
                                            <kbd className="text-xs text-fg-muted px-1 py-0.5 border border-bg-subtle rounded">
                                                {entry.shortcut}
                                            </kbd>
                                        )}
                                    </div>
                                )
                            })}
                        </div>
                    ))}
                    {flatResults.length === 0 && (
                        <div className="px-3 py-4 text-sm text-fg-muted text-center">
                            No commands found
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}
