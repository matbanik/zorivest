import { useState, useCallback } from 'react'
import type { Trade } from './TradesTable'

// ── Types ────────────────────────────────────────────────────────────────

const EMOTIONAL_STATES = [
    'Calm',
    'Confident',
    'Anxious',
    'FOMO',
    'Frustrated',
    'Euphoric',
    'Revenge',
    'Indifferent',
] as const

type EmotionalState = (typeof EMOTIONAL_STATES)[number]

interface TradeReport {
    setupQuality: number
    executionQuality: number
    followedPlan: 'yes' | 'no' | 'partial'
    emotionalState: EmotionalState
    lessons: string
    tags: string[]
}

// ── Star Rating ──────────────────────────────────────────────────────────

function StarRating({
    value,
    onChange,
    label,
}: {
    value: number
    onChange: (n: number) => void
    label: string
}) {
    return (
        <div>
            <label className="block text-xs text-fg-muted mb-1">{label}</label>
            <div className="flex gap-1">
                {[1, 2, 3, 4, 5].map((star) => (
                    <button
                        key={star}
                        type="button"
                        onClick={() => onChange(star)}
                        className={`text-lg transition-colors ${star <= value ? 'text-yellow-400' : 'text-fg-muted/30'
                            }`}
                        aria-label={`${star} star${star > 1 ? 's' : ''}`}
                    >
                        ★
                    </button>
                ))}
            </div>
        </div>
    )
}

// ── Tag Chips ────────────────────────────────────────────────────────────

function TagChipInput({
    tags,
    onChange,
}: {
    tags: string[]
    onChange: (tags: string[]) => void
}) {
    const [input, setInput] = useState('')

    const addTag = useCallback(() => {
        const tag = input.trim()
        if (tag && !tags.includes(tag)) {
            onChange([...tags, tag])
        }
        setInput('')
    }, [input, tags, onChange])

    const removeTag = useCallback(
        (tag: string) => {
            onChange(tags.filter((t) => t !== tag))
        },
        [tags, onChange],
    )

    return (
        <div>
            <label className="block text-xs text-fg-muted mb-1">Tags</label>
            <div className="flex flex-wrap gap-1 mb-2">
                {tags.map((tag) => (
                    <span
                        key={tag}
                        className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-accent/20 text-accent"
                    >
                        {tag}
                        <button
                            type="button"
                            onClick={() => removeTag(tag)}
                            className="hover:text-fg"
                        >
                            ×
                        </button>
                    </span>
                ))}
            </div>
            <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                        e.preventDefault()
                        addTag()
                    }
                }}
                placeholder="Add tag…"
                className="w-full px-3 py-1.5 text-sm rounded-md bg-bg border border-bg-subtle text-fg"
                data-testid="trade-tag-input"
            />
        </div>
    )
}

// ── Component ────────────────────────────────────────────────────────────

interface TradeReportFormProps {
    trade: Trade
    onSave?: (report: TradeReport) => void
    onClose?: () => void
}

/**
 * TradeReportForm — Journal tab with star ratings, emotional state,
 * followed-plan select, lessons textarea, and tag chips.
 */
export default function TradeReportForm({ trade, onSave, onClose }: TradeReportFormProps) {
    const [report, setReport] = useState<TradeReport>({
        setupQuality: 0,
        executionQuality: 0,
        followedPlan: 'yes',
        emotionalState: 'Calm',
        lessons: '',
        tags: [],
    })

    const update = <K extends keyof TradeReport>(key: K, value: TradeReport[K]) => {
        setReport((prev) => ({ ...prev, [key]: value }))
    }

    return (
        <div className="space-y-4" data-testid="trade-report-form">
            {/* Star Ratings */}
            <StarRating
                label="Setup Quality"
                value={report.setupQuality}
                onChange={(n) => update('setupQuality', n)}
            />
            <StarRating
                label="Execution Quality"
                value={report.executionQuality}
                onChange={(n) => update('executionQuality', n)}
            />

            {/* Followed Plan */}
            <div>
                <label className="block text-xs text-fg-muted mb-1">Followed Plan</label>
                <select
                    value={report.followedPlan}
                    onChange={(e) => update('followedPlan', e.target.value as any)}
                    className="w-full px-3 py-1.5 text-sm rounded-md bg-bg border border-bg-subtle text-fg"
                    data-testid="trade-followed-plan"
                >
                    <option value="yes">Yes</option>
                    <option value="no">No</option>
                    <option value="partial">Partial</option>
                </select>
            </div>

            {/* Emotional State */}
            <div>
                <label className="block text-xs text-fg-muted mb-1">
                    Emotional State
                </label>
                <select
                    value={report.emotionalState}
                    onChange={(e) => update('emotionalState', e.target.value as EmotionalState)}
                    className="w-full px-3 py-1.5 text-sm rounded-md bg-bg border border-bg-subtle text-fg"
                    data-testid="trade-emotional-state"
                >
                    {EMOTIONAL_STATES.map((state) => (
                        <option key={state} value={state}>
                            {state}
                        </option>
                    ))}
                </select>
            </div>

            {/* Lessons */}
            <div>
                <label className="block text-xs text-fg-muted mb-1">Lessons Learned</label>
                <textarea
                    value={report.lessons}
                    onChange={(e) => update('lessons', e.target.value)}
                    rows={4}
                    placeholder="What did you learn from this trade?"
                    className="w-full px-3 py-1.5 text-sm rounded-md bg-bg border border-bg-subtle text-fg resize-y"
                    data-testid="trade-lessons"
                />
            </div>

            {/* Tags */}
            <TagChipInput
                tags={report.tags}
                onChange={(tags) => update('tags', tags)}
            />

            {/* Buttons */}
            <div className="flex gap-2 pt-2">
                <button
                    type="button"
                    onClick={() => onSave?.(report)}
                    className="px-4 py-1.5 text-sm rounded-md bg-accent text-accent-fg hover:bg-accent/90 border border-accent"
                    data-testid="trade-report-save"
                >
                    Save Journal
                </button>
                <button
                    type="button"
                    onClick={onClose}
                    className="px-4 py-1.5 text-sm rounded-md bg-bg text-fg-muted hover:text-fg border border-bg-subtle"
                >
                    Cancel
                </button>
            </div>
        </div>
    )
}
