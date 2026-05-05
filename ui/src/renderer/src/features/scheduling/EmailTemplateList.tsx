/**
 * EmailTemplateList — sidebar list of email templates.
 *
 * Shows template name + is_default badge. Follows PolicyList pattern.
 *
 * Source: 06k-gui-email-templates.md §6K.2
 * MEU: MEU-72b (gui-email-templates)
 */

import { useState, useCallback, useMemo } from 'react'
import { SCHEDULING_TEST_IDS } from './test-ids'
import type { EmailTemplate } from './template-api'
import SelectionCheckbox from '@/components/SelectionCheckbox'
import BulkActionBar from '@/components/BulkActionBar'
import ConfirmDeleteModal from '@/components/ConfirmDeleteModal'

interface EmailTemplateListProps {
    templates: EmailTemplate[]
    selectedTemplateName: string | null
    onSelect: (template: EmailTemplate) => void
    onCreate: () => void
    onDeleteTemplates?: (names: string[]) => Promise<void>
    isLoading: boolean
    error: string | null
}

export default function EmailTemplateList({
    templates,
    selectedTemplateName,
    onSelect,
    onCreate,
    onDeleteTemplates,
    isLoading,
    error,
}: EmailTemplateListProps) {
    // MEU-203: Search + selection state
    const [searchQuery, setSearchQuery] = useState('')
    const [selectedNames, setSelectedNames] = useState<Set<string>>(new Set())
    const [showBulkConfirm, setShowBulkConfirm] = useState(false)

    const filteredTemplates = useMemo(() => {
        if (!searchQuery.trim()) return templates
        const q = searchQuery.toLowerCase()
        return templates.filter((t) => t.name.toLowerCase().includes(q))
    }, [templates, searchQuery])

    const toggleSelect = useCallback((name: string) => {
        setSelectedNames(prev => {
            const next = new Set(prev)
            if (next.has(name)) next.delete(name)
            else next.add(name)
            return next
        })
    }, [])

    const toggleSelectAll = useCallback(() => {
        setSelectedNames(prev => {
            if (prev.size === filteredTemplates.length && prev.size > 0) {
                return new Set()
            }
            return new Set(filteredTemplates.map(t => t.name))
        })
    }, [filteredTemplates])

    const handleBulkDelete = useCallback(async () => {
        await onDeleteTemplates?.(Array.from(selectedNames))
        setSelectedNames(new Set())
        setShowBulkConfirm(false)
    }, [selectedNames, onDeleteTemplates])

    return (
        <div
            data-testid={SCHEDULING_TEST_IDS.TEMPLATE_LIST}
            className="flex flex-col h-full"
        >
            {/* Header */}
            <div className="px-3 py-2.5 border-b border-bg-subtle/30 flex items-center justify-between">
                <h3 className="text-xs font-semibold text-fg-muted uppercase tracking-wider">
                    Templates
                </h3>
                <button
                    data-testid={SCHEDULING_TEST_IDS.TEMPLATE_NEW_BTN}
                    onClick={onCreate}
                    className="text-xs px-2 py-1 rounded-md bg-accent-purple/20 text-accent-purple hover:bg-accent-purple/30 transition-colors cursor-pointer"
                >
                    + New Template
                </button>
            </div>

            {/* MEU-203: Search input */}
            <div className="px-3 py-1.5 border-b border-bg-subtle/20">
                <input
                    data-testid="template-search-input"
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search templates…"
                    className="w-full px-2 py-1 text-xs rounded-md bg-bg border border-bg-subtle text-fg"
                />
            </div>

            {/* MEU-203: Select-all header */}
            {filteredTemplates.length > 0 && (
                <div className="px-3 py-1 border-b border-bg-subtle/20 flex items-center gap-2">
                    <SelectionCheckbox
                        checked={selectedNames.size === filteredTemplates.length && filteredTemplates.length > 0}
                        indeterminate={selectedNames.size > 0 && selectedNames.size < filteredTemplates.length}
                        onChange={toggleSelectAll}
                        ariaLabel="Select all templates"
                        data-testid="select-all-template-checkbox"
                    />
                    <span className="text-xs text-fg-muted">Select all</span>
                </div>
            )}

            {/* MEU-203: Bulk action bar */}
            {selectedNames.size > 0 && (
                <BulkActionBar
                    selectedCount={selectedNames.size}
                    entityLabel="template"
                    onDelete={() => setShowBulkConfirm(true)}
                    onClearSelection={() => setSelectedNames(new Set())}
                />
            )}

            {/* Content */}
            <div className="flex-1 overflow-y-auto">
                {isLoading && (
                    <div className="px-3 py-4 text-sm text-fg-muted animate-pulse">
                        Loading templates…
                    </div>
                )}

                {error && (
                    <div className="px-3 py-4 text-sm text-accent-red">
                        {error}
                    </div>
                )}

                {!isLoading && !error && filteredTemplates.length === 0 && (
                    <div className="px-3 py-4 text-sm text-fg-muted text-center">
                        No templates yet
                    </div>
                )}

                {filteredTemplates.map((template) => (
                    <button
                        key={template.name}
                        onClick={() => onSelect(template)}
                        className={`w-full text-left px-3 py-2.5 border-b border-bg-subtle/20 transition-colors cursor-pointer ${
                            selectedTemplateName === template.name
                                ? 'bg-accent-purple/10 border-l-2 border-l-accent'
                                : 'hover:bg-bg-subtle/30'
                        }`}
                    >
                        <div className="flex items-center gap-2">
                            {/* MEU-203: Row checkbox */}
                            <span onClick={(e) => e.stopPropagation()}>
                                <SelectionCheckbox
                                    checked={selectedNames.has(template.name)}
                                    onChange={() => toggleSelect(template.name)}
                                    ariaLabel={`Select ${template.name}`}
                                    data-testid={`template-row-checkbox-${template.name}`}
                                />
                            </span>
                            <span className="text-sm font-medium text-fg truncate">
                                {template.name}
                            </span>
                            {template.is_default && (
                                <span
                                    data-testid={SCHEDULING_TEST_IDS.TEMPLATE_DEFAULT_BADGE}
                                    className="text-[10px] px-1.5 py-0.5 rounded bg-accent-blue/20 text-accent-blue font-medium uppercase tracking-wide"
                                >
                                    Default
                                </span>
                            )}
                        </div>
                        {template.description && (
                            <p className="text-xs text-fg-muted mt-0.5 truncate">
                                {template.description}
                            </p>
                        )}
                    </button>
                ))}
            </div>

            {/* MEU-203: Bulk delete confirmation */}
            <ConfirmDeleteModal
                open={showBulkConfirm}
                target={{ count: selectedNames.size, type: selectedNames.size === 1 ? 'template' : 'templates' }}
                onCancel={() => setShowBulkConfirm(false)}
                onConfirm={handleBulkDelete}
            />
        </div>
    )
}
