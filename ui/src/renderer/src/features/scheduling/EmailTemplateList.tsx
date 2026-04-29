/**
 * EmailTemplateList — sidebar list of email templates.
 *
 * Shows template name + is_default badge. Follows PolicyList pattern.
 *
 * Source: 06k-gui-email-templates.md §6K.2
 * MEU: MEU-72b (gui-email-templates)
 */

import { SCHEDULING_TEST_IDS } from './test-ids'
import type { EmailTemplate } from './template-api'

interface EmailTemplateListProps {
    templates: EmailTemplate[]
    selectedTemplateName: string | null
    onSelect: (template: EmailTemplate) => void
    onCreate: () => void
    isLoading: boolean
    error: string | null
}

export default function EmailTemplateList({
    templates,
    selectedTemplateName,
    onSelect,
    onCreate,
    isLoading,
    error,
}: EmailTemplateListProps) {
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
                    className="text-xs px-2 py-1 rounded bg-accent/20 text-accent hover:bg-accent/30 transition-colors cursor-pointer"
                >
                    + New
                </button>
            </div>

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

                {!isLoading && !error && templates.length === 0 && (
                    <div className="px-3 py-4 text-sm text-fg-muted text-center">
                        No templates yet
                    </div>
                )}

                {templates.map((template) => (
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
        </div>
    )
}
