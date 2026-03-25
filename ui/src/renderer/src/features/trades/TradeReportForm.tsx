import { useState, useCallback, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiFetch } from '@/lib/api'
import { useStatusBar } from '@/hooks/useStatusBar'
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

// API response shape from GET /api/v1/trades/{exec_id}/report
interface ReportResponse {
    id: number
    trade_id: string
    setup_quality: string    // Letter grade A-F
    execution_quality: string
    followed_plan: boolean
    emotional_state: string
    lessons_learned: string
    tags: string[]
    created_at: string
}

// Local form state — stars are 1-5
interface TradeReport {
    setupQuality: number
    executionQuality: number
    followedPlan: boolean
    emotionalState: string
    lessons: string
    tags: string[]
}

// ── Grade ↔ Star Conversion ──────────────────────────────────────────────

const GRADE_TO_STAR: Record<string, number> = { A: 5, B: 4, C: 3, D: 2, F: 1 }
const STAR_TO_GRADE: Record<number, string> = { 5: 'A', 4: 'B', 3: 'C', 2: 'D', 1: 'F' }

function gradeToStar(grade: string): number {
    return GRADE_TO_STAR[grade] ?? 3
}

function starToGrade(star: number): string {
    return STAR_TO_GRADE[star] ?? 'C'
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
            <div className="flex gap-1" data-testid={`star-rating-${label.toLowerCase().replace(/\s+/g, '-')}`}>
                {[1, 2, 3, 4, 5].map((n) => (
                    <button
                        key={n}
                        type="button"
                        onClick={() => onChange(n)}
                        className={`text-lg cursor-pointer ${n <= value ? 'text-yellow-400' : 'text-fg-muted/30'
                            }`}
                        aria-label={`${n} star${n > 1 ? 's' : ''}`}
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
        const trimmed = input.trim()
        if (trimmed && !tags.includes(trimmed)) {
            onChange([...tags, trimmed])
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
            <div className="flex flex-wrap gap-1 mb-2" data-testid="trade-tags">
                {tags.map((tag) => (
                    <span
                        key={tag}
                        className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-bg-elevated text-fg"
                    >
                        {tag}
                        <button
                            type="button"
                            onClick={() => removeTag(tag)}
                            className="text-fg-muted hover:text-fg cursor-pointer"
                        >
                            ×
                        </button>
                    </span>
                ))}
            </div>
            <input
                value={input}
                onChange={(e) => {
                    const val = e.target.value
                    // Auto-add on comma
                    if (val.includes(',')) {
                        const parts = val.split(',').map((s) => s.trim()).filter(Boolean)
                        const newTags = parts.filter((p) => !tags.includes(p))
                        if (newTags.length) onChange([...tags, ...newTags])
                        setInput('')
                    } else {
                        setInput(val)
                    }
                }}
                onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                        e.preventDefault()
                        addTag()
                    }
                }}
                onBlur={() => addTag()}
                placeholder="Add tag (Enter or comma)..."
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

const EMPTY_REPORT: TradeReport = {
    setupQuality: 0,
    executionQuality: 0,
    followedPlan: true,
    emotionalState: 'Calm',
    lessons: '',
    tags: [],
}

/**
 * TradeReportForm — Journal tab with API wiring per 06b §Report.
 *
 * - Fetches existing report via GET /api/v1/trades/{exec_id}/report
 * - Saves via POST (new) or PUT (existing)
 * - Star ratings 1-5 ↔ letter grades A-F
 * - followed_plan as bool toggle
 * - emotional_state as free string dropdown
 */
export default function TradeReportForm({ trade, onSave, onClose }: TradeReportFormProps) {
    const queryClient = useQueryClient()
    const { setStatus } = useStatusBar()

    const isNewTrade = trade.exec_id === '(new)'

    // Fetch existing report (AC-1, AC-2, AC-6)
    const { data: existingReport, isLoading, isError } = useQuery<ReportResponse | null>({
        queryKey: ['trade-report', trade.exec_id],
        queryFn: async () => {
            if (isNewTrade) return null
            try {
                return await apiFetch<ReportResponse>(
                    `/api/v1/trades/${trade.exec_id}/report`
                )
            } catch (err) {
                // R4: Only 404 means "no report yet" (AC-2).
                // All other errors (5xx, auth, transport) are real failures — re-throw
                // so React Query can expose the error state instead of silently
                // converting server errors into a "create new report" flow.
                if (err instanceof Error && err.message.includes('API 404')) return null
                throw err
            }
        },
        enabled: !isNewTrade,
    })

    // Initialize form state from API data or empty defaults
    const [report, setReport] = useState<TradeReport>(EMPTY_REPORT)
    const [isExisting, setIsExisting] = useState(false)

    useEffect(() => {
        if (existingReport) {
            setReport({
                setupQuality: gradeToStar(existingReport.setup_quality),
                executionQuality: gradeToStar(existingReport.execution_quality),
                followedPlan: existingReport.followed_plan,
                emotionalState: existingReport.emotional_state,
                lessons: existingReport.lessons_learned,
                tags: existingReport.tags,
            })
            setIsExisting(true)
        } else {
            setReport(EMPTY_REPORT)
            setIsExisting(false)
        }
    }, [existingReport])

    const update = <K extends keyof TradeReport>(key: K, value: TradeReport[K]) => {
        setReport((prev) => ({ ...prev, [key]: value }))
    }

    // Save mutation (AC-3, AC-4a-c, AC-5)
    const handleSave = useCallback(async () => {
        if (isNewTrade) return

        const payload = {
            setup_quality: starToGrade(report.setupQuality),
            execution_quality: starToGrade(report.executionQuality),
            followed_plan: report.followedPlan,
            emotional_state: report.emotionalState,
            lessons_learned: report.lessons,
            tags: report.tags,
        }

        try {
            if (isExisting) {
                setStatus('Updating journal...')
                await apiFetch(`/api/v1/trades/${trade.exec_id}/report`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload),
                })
            } else {
                setStatus('Saving journal...')
                await apiFetch(`/api/v1/trades/${trade.exec_id}/report`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload),
                })
            }
            setStatus('Journal saved')
            await queryClient.invalidateQueries({ queryKey: ['trade-report', trade.exec_id] })
            onSave?.(report)
        } catch (err) {
            setStatus(`Error: ${err instanceof Error ? err.message : 'Failed to save journal'}`)
        }
    }, [report, isExisting, isNewTrade, trade.exec_id, queryClient, setStatus, onSave])

    if (isLoading) {
        return (
            <div className="p-4 text-sm text-fg-muted" data-testid="trade-report-loading">
                Loading journal...
            </div>
        )
    }

    if (isError) {
        return (
            <div className="p-4 text-sm text-red-400" data-testid="trade-report-error">
                Failed to load trade report. Please try again.
            </div>
        )
    }

    return (
        <div className="space-y-4" data-testid="trade-report-form">
            {/* Star Ratings (AC-4a) */}
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

            {/* Followed Plan — bool toggle (AC-4b) */}
            <div>
                <label className="block text-xs text-fg-muted mb-1">Followed Plan</label>
                <div className="flex gap-2" data-testid="trade-followed-plan">
                    <button
                        type="button"
                        onClick={() => update('followedPlan', true)}
                        className={`px-3 py-1 text-sm rounded-md border cursor-pointer ${report.followedPlan
                            ? 'bg-green-500/20 text-green-400 border-green-500/40'
                            : 'bg-bg text-fg-muted border-bg-subtle'
                            }`}
                    >
                        Yes
                    </button>
                    <button
                        type="button"
                        onClick={() => update('followedPlan', false)}
                        className={`px-3 py-1 text-sm rounded-md border cursor-pointer ${!report.followedPlan
                            ? 'bg-red-500/20 text-red-400 border-red-500/40'
                            : 'bg-bg text-fg-muted border-bg-subtle'
                            }`}
                    >
                        No
                    </button>
                </div>
            </div>

            {/* Emotional State — free string dropdown (AC-4c) */}
            <div>
                <label className="block text-xs text-fg-muted mb-1">
                    Emotional State
                </label>
                <select
                    value={report.emotionalState}
                    onChange={(e) => update('emotionalState', e.target.value)}
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
                    onClick={handleSave}
                    disabled={isNewTrade}
                    className="px-4 py-1.5 text-sm rounded-md bg-accent text-accent-fg hover:bg-accent/90 border border-accent disabled:opacity-50"
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
