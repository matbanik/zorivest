/**
 * EmailTemplatePreview — sandboxed iframe for template preview.
 *
 * Renders preview HTML in an <iframe srcDoc> with sandbox attribute.
 * Always visible below editor (UX2).
 *
 * Source: 06k-gui-email-templates.md §6K.6
 * MEU: MEU-72b (gui-email-templates)
 */

import { SCHEDULING_TEST_IDS } from './test-ids'

interface EmailTemplatePreviewProps {
    renderedHtml: string | null
    isLoading: boolean
    error?: string | null
}

export default function EmailTemplatePreview({
    renderedHtml,
    isLoading,
    error,
}: EmailTemplatePreviewProps) {
    if (isLoading) {
        return (
            <div className="border border-bg-subtle/30 rounded p-4 text-sm text-fg-muted animate-pulse">
                Loading preview…
            </div>
        )
    }

    if (error) {
        return (
            <div className="border border-accent-red/30 rounded p-4 text-sm text-accent-red bg-accent-red/5">
                <span className="font-medium">Preview failed:</span> {error}
            </div>
        )
    }

    if (!renderedHtml) {
        return (
            <div className="border border-bg-subtle/30 rounded p-4 text-sm text-fg-muted text-center">
                Click <span className="font-medium text-fg">Preview</span> to render the template
            </div>
        )
    }

    return (
        <div className="border border-bg-subtle/30 rounded overflow-hidden">
            <div className="px-3 py-1.5 border-b border-bg-subtle/20 bg-bg-subtle/10">
                <span className="text-xs font-medium text-fg-muted uppercase tracking-wider">
                    Preview
                </span>
            </div>
            <iframe
                data-testid={SCHEDULING_TEST_IDS.TEMPLATE_PREVIEW_IFRAME}
                srcDoc={renderedHtml}
                sandbox=""
                className="w-full min-h-[200px] bg-white"
                title="Template Preview"
            />
        </div>
    )
}
