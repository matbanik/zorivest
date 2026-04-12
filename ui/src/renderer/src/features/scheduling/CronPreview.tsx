/**
 * CronPreview — human-readable cron expression preview.
 *
 * Uses cronstrue library to convert cron expressions to plain English.
 * Displays inline below the cron input field.
 *
 * Source: 06e-gui-scheduling.md §Schedule Detail Fields
 * MEU: MEU-72 (gui-scheduling)
 */

import { useMemo } from 'react'
import cronstrue from 'cronstrue'
import { SCHEDULING_TEST_IDS } from './test-ids'

interface CronPreviewProps {
    expression: string
}

export default function CronPreview({ expression }: CronPreviewProps) {
    const preview = useMemo(() => {
        if (!expression.trim()) return null
        try {
            return cronstrue.toString(expression, { verbose: true })
        } catch {
            return null
        }
    }, [expression])

    if (!expression.trim()) return null

    return (
        <div data-testid={SCHEDULING_TEST_IDS.POLICY_CRON_PREVIEW} className="text-xs mt-1">
            {preview ? (
                <span className="text-accent-cyan">⏰ {preview}</span>
            ) : (
                <span className="text-accent-red">Invalid cron expression</span>
            )}
        </div>
    )
}
