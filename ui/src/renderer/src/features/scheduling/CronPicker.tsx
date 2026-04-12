/**
 * CronPicker — frequency-based visual cron expression builder.
 *
 * Provides preset frequency options (Daily, Weekdays, Weekly, Monthly)
 * with time selectors, plus a "Custom" mode for raw cron editing.
 * Uses cronstrue for human-readable preview of the generated expression.
 *
 * Zero external dependencies beyond cronstrue (already installed).
 *
 * Source: Implementation plan — Scheduling GUI UX Redesign
 * MEU: MEU-72 (gui-scheduling)
 */

import { useState, useMemo, useCallback, useEffect } from 'react'
import cronstrue from 'cronstrue'
import { SCHEDULING_TEST_IDS } from './test-ids'

// ── Types ──────────────────────────────────────────────────────────────

type FrequencyPreset =
    | 'daily'
    | 'weekdays'
    | 'monday'
    | 'tuesday'
    | 'wednesday'
    | 'thursday'
    | 'friday'
    | 'saturday'
    | 'sunday'
    | 'monthly_1st'
    | 'monthly_15th'
    | 'custom'

interface CronPickerProps {
    value: string
    onChange: (cron: string) => void
}

// ── Preset → Cron mapping ──────────────────────────────────────────────

const PRESET_LABELS: Record<FrequencyPreset, string> = {
    daily: 'Every Day',
    weekdays: 'Weekdays (Mon–Fri)',
    monday: 'Every Monday',
    tuesday: 'Every Tuesday',
    wednesday: 'Every Wednesday',
    thursday: 'Every Thursday',
    friday: 'Every Friday',
    saturday: 'Every Saturday',
    sunday: 'Every Sunday',
    monthly_1st: '1st of Every Month',
    monthly_15th: '15th of Every Month',
    custom: 'Custom',
}

function buildCron(preset: FrequencyPreset, hour: number, minute: number): string {
    const m = String(minute)
    const h = String(hour)
    switch (preset) {
        case 'daily':
            return `${m} ${h} * * *`
        case 'weekdays':
            return `${m} ${h} * * 1-5`
        case 'monday':
            return `${m} ${h} * * 1`
        case 'tuesday':
            return `${m} ${h} * * 2`
        case 'wednesday':
            return `${m} ${h} * * 3`
        case 'thursday':
            return `${m} ${h} * * 4`
        case 'friday':
            return `${m} ${h} * * 5`
        case 'saturday':
            return `${m} ${h} * * 6`
        case 'sunday':
            return `${m} ${h} * * 0`
        case 'monthly_1st':
            return `${m} ${h} 1 * *`
        case 'monthly_15th':
            return `${m} ${h} 15 * *`
        case 'custom':
            return '' // handled separately
    }
}

/** Attempt to detect which preset matches a cron expression */
function detectPreset(cron: string): { preset: FrequencyPreset; hour: number; minute: number } {
    const parts = cron.trim().split(/\s+/)
    if (parts.length !== 5) return { preset: 'custom', hour: 8, minute: 0 }

    const [minStr, hourStr, dom, , dow] = parts
    const minute = parseInt(minStr, 10)
    const hour = parseInt(hourStr, 10)

    if (isNaN(minute) || isNaN(hour)) return { preset: 'custom', hour: 8, minute: 0 }

    if (dom === '*' && dow === '*') return { preset: 'daily', hour, minute }
    if (dom === '*' && dow === '1-5') return { preset: 'weekdays', hour, minute }
    if (dom === '*' && dow === '1') return { preset: 'monday', hour, minute }
    if (dom === '*' && dow === '2') return { preset: 'tuesday', hour, minute }
    if (dom === '*' && dow === '3') return { preset: 'wednesday', hour, minute }
    if (dom === '*' && dow === '4') return { preset: 'thursday', hour, minute }
    if (dom === '*' && dow === '5') return { preset: 'friday', hour, minute }
    if (dom === '*' && dow === '6') return { preset: 'saturday', hour, minute }
    if (dom === '*' && dow === '0') return { preset: 'sunday', hour, minute }
    if (dom === '1' && dow === '*') return { preset: 'monthly_1st', hour, minute }
    if (dom === '15' && dow === '*') return { preset: 'monthly_15th', hour, minute }

    return { preset: 'custom', hour, minute }
}

// ── Minute options ─────────────────────────────────────────────────────

const MINUTE_OPTIONS = [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55]

// ── Component ──────────────────────────────────────────────────────────

export default function CronPicker({ value, onChange }: CronPickerProps) {
    // Intentionally mount-only: detect initial preset from the incoming value once, not on every re-render
    // eslint-disable-next-line react-hooks/exhaustive-deps
    const initial = useMemo(() => detectPreset(value), [])
    const [preset, setPreset] = useState<FrequencyPreset>(initial.preset)
    const [hour, setHour] = useState(initial.hour)
    const [minute, setMinute] = useState(initial.minute)
    const [rawCron, setRawCron] = useState(value)

    // Sync back when parent value changes (e.g. after save)
    useEffect(() => {
        const detected = detectPreset(value)
        if (detected.preset !== 'custom') {
            setPreset(detected.preset)
            setHour(detected.hour)
            setMinute(detected.minute)
        }
        setRawCron(value)
    }, [value])

    // Generate cron from preset + time
    const generatedCron = useMemo(() => {
        if (preset === 'custom') return rawCron
        return buildCron(preset, hour, minute)
    }, [preset, hour, minute, rawCron])

    // Human-readable preview via cronstrue
    const preview = useMemo(() => {
        if (!generatedCron.trim()) return null
        try {
            return cronstrue.toString(generatedCron, { verbose: true })
        } catch {
            return null
        }
    }, [generatedCron])

    // Emit changes upstream
    const emitChange = useCallback(
        (newPreset: FrequencyPreset, newHour: number, newMinute: number, newRaw: string) => {
            const cron = newPreset === 'custom' ? newRaw : buildCron(newPreset, newHour, newMinute)
            if (cron && cron !== value) {
                onChange(cron)
            }
        },
        [onChange, value],
    )

    const handlePresetChange = useCallback(
        (newPreset: FrequencyPreset) => {
            setPreset(newPreset)
            if (newPreset !== 'custom') {
                emitChange(newPreset, hour, minute, rawCron)
            }
        },
        [hour, minute, rawCron, emitChange],
    )

    const handleHourChange = useCallback(
        (h: number) => {
            setHour(h)
            emitChange(preset, h, minute, rawCron)
        },
        [preset, minute, rawCron, emitChange],
    )

    const handleMinuteChange = useCallback(
        (m: number) => {
            setMinute(m)
            emitChange(preset, hour, m, rawCron)
        },
        [preset, hour, rawCron, emitChange],
    )

    const handleRawChange = useCallback(
        (raw: string) => {
            setRawCron(raw)
        },
        [],
    )

    const handleRawBlur = useCallback(() => {
        if (rawCron.trim() && rawCron !== value) {
            onChange(rawCron.trim())
        }
    }, [rawCron, value, onChange])

    return (
        <div data-testid={SCHEDULING_TEST_IDS.CRON_PICKER} className="space-y-2">
            <div className="flex items-center gap-2 flex-wrap">
                {/* Frequency Preset */}
                <select
                    data-testid={SCHEDULING_TEST_IDS.CRON_FREQUENCY}
                    value={preset}
                    onChange={(e) => handlePresetChange(e.target.value as FrequencyPreset)}
                    className="px-2 py-1.5 text-sm rounded-md bg-bg border border-bg-subtle text-fg focus:outline-none focus:border-accent-cyan"
                >
                    <optgroup label="Daily">
                        <option value="daily">{PRESET_LABELS.daily}</option>
                        <option value="weekdays">{PRESET_LABELS.weekdays}</option>
                    </optgroup>
                    <optgroup label="Weekly">
                        <option value="monday">{PRESET_LABELS.monday}</option>
                        <option value="tuesday">{PRESET_LABELS.tuesday}</option>
                        <option value="wednesday">{PRESET_LABELS.wednesday}</option>
                        <option value="thursday">{PRESET_LABELS.thursday}</option>
                        <option value="friday">{PRESET_LABELS.friday}</option>
                        <option value="saturday">{PRESET_LABELS.saturday}</option>
                        <option value="sunday">{PRESET_LABELS.sunday}</option>
                    </optgroup>
                    <optgroup label="Monthly">
                        <option value="monthly_1st">{PRESET_LABELS.monthly_1st}</option>
                        <option value="monthly_15th">{PRESET_LABELS.monthly_15th}</option>
                    </optgroup>
                    <optgroup label="Advanced">
                        <option value="custom">{PRESET_LABELS.custom}</option>
                    </optgroup>
                </select>

                {/* Time selectors (hidden in custom mode) */}
                {preset !== 'custom' && (
                    <>
                        <span className="text-xs text-fg-muted">at</span>
                        <select
                            data-testid={SCHEDULING_TEST_IDS.CRON_HOUR}
                            value={hour}
                            onChange={(e) => handleHourChange(parseInt(e.target.value, 10))}
                            className="px-2 py-1.5 text-sm rounded-md bg-bg border border-bg-subtle text-fg font-mono focus:outline-none focus:border-accent-cyan w-16"
                        >
                            {Array.from({ length: 24 }, (_, i) => (
                                <option key={i} value={i}>
                                    {String(i).padStart(2, '0')}
                                </option>
                            ))}
                        </select>
                        <span className="text-fg-muted font-mono">:</span>
                        <select
                            data-testid={SCHEDULING_TEST_IDS.CRON_MINUTE}
                            value={minute}
                            onChange={(e) => handleMinuteChange(parseInt(e.target.value, 10))}
                            className="px-2 py-1.5 text-sm rounded-md bg-bg border border-bg-subtle text-fg font-mono focus:outline-none focus:border-accent-cyan w-16"
                        >
                            {MINUTE_OPTIONS.map((m) => (
                                <option key={m} value={m}>
                                    {String(m).padStart(2, '0')}
                                </option>
                            ))}
                        </select>
                    </>
                )}
            </div>

            {/* Custom raw input */}
            {preset === 'custom' && (
                <input
                    data-testid={SCHEDULING_TEST_IDS.CRON_RAW_INPUT}
                    type="text"
                    value={rawCron}
                    onChange={(e) => handleRawChange(e.target.value)}
                    onBlur={handleRawBlur}
                    placeholder="e.g. 0 8 * * 1-5"
                    className="w-full px-2 py-1.5 text-sm rounded-md bg-bg border border-bg-subtle text-fg font-mono focus:outline-none focus:border-accent-cyan"
                />
            )}

            {/* Generated cron + preview */}
            <div className="flex items-baseline gap-3 text-xs">
                <code
                    data-testid={SCHEDULING_TEST_IDS.CRON_GENERATED}
                    className="text-fg-muted/70 font-mono"
                >
                    cron: {generatedCron || '—'}
                </code>
                {preview && (
                    <span className="text-accent-cyan">⏰ {preview}</span>
                )}
                {!preview && generatedCron.trim() && (
                    <span className="text-accent-red">Invalid expression</span>
                )}
            </div>
        </div>
    )
}
