/**
 * Shared date/time formatting — DT1/DT2 standard.
 *
 * Format: MM-DD-YYYY h:mmAM/PM (in the policy's IANA timezone)
 * No seconds in UI display. Full ISO precision preserved in data layer.
 *
 * When `timeZone` is provided, Intl.DateTimeFormat renders the instant in
 * that IANA timezone (e.g., "America/New_York"). Without it, the browser's
 * local timezone is used (same behavior as before).
 *
 * @see .agent/docs/emerging-standards.md §DT1, §DT2
 * @see [SCHED-TZDISPLAY] known-issues.md
 */

/**
 * Normalize an ISO timestamp to explicit UTC.
 *
 * The backend stores all datetimes as UTC, but SQLAlchemy's DateTime column
 * (without timezone=True) strips tzinfo. Pydantic then serializes them as
 * naive strings like "2026-04-20T18:00:00" — which JS Date() parses as
 * **local time**, not UTC. This causes a timezone-offset error (e.g., 4h in EDT).
 *
 * Fix: if the ISO string has no timezone indicator (Z, +, or -offset after the
 * time portion), append 'Z' to force UTC interpretation.
 */
function normalizeUtc(iso: string): string {
    // Already has timezone indicator: "Z", "+05:30", "-04:00"
    if (/[Zz]$/.test(iso) || /[+-]\d{2}:\d{2}$/.test(iso) || /[+-]\d{4}$/.test(iso)) {
        return iso
    }
    return iso + 'Z'
}

/**
 * Format an ISO timestamp for UI display.
 *
 * @param iso  - ISO 8601 string from the API (always UTC)
 * @param timeZone - Optional IANA timezone (e.g., "America/New_York").
 *                   Falls back to browser local timezone if omitted.
 * @returns `"MM-DD-YYYY h:mmAM/PM"` or `""` if input is falsy.
 */
export function formatTimestamp(
    iso: string | null | undefined,
    timeZone?: string,
): string {
    if (!iso) return ''
    const d = new Date(normalizeUtc(iso))
    if (isNaN(d.getTime())) return ''

    if (timeZone) {
        // Use Intl.DateTimeFormat to render in the target timezone
        const parts = new Intl.DateTimeFormat('en-US', {
            timeZone,
            month: '2-digit',
            day: '2-digit',
            year: 'numeric',
            hour: 'numeric',
            minute: '2-digit',
            hour12: true,
        }).formatToParts(d)

        const get = (type: Intl.DateTimeFormatPartTypes): string =>
            parts.find((p) => p.type === type)?.value ?? ''

        const mm = get('month')
        const dd = get('day')
        const yyyy = get('year')
        const h = get('hour')
        const min = get('minute')
        const ampm = get('dayPeriod').toUpperCase()
        return `${mm}-${dd}-${yyyy} ${h}:${min}${ampm}`
    }

    // Fallback: browser local timezone (original behavior)
    const mm = String(d.getMonth() + 1).padStart(2, '0')
    const dd = String(d.getDate()).padStart(2, '0')
    const h = d.getHours() % 12 || 12
    const minutes = String(d.getMinutes()).padStart(2, '0')
    const ampm = d.getHours() >= 12 ? 'PM' : 'AM'
    return `${mm}-${dd}-${d.getFullYear()} ${h}:${minutes}${ampm}`
}

/**
 * Format an ISO timestamp as date-only for compact display.
 *
 * @param iso - ISO 8601 string
 * @param timeZone - Optional IANA timezone
 * @returns `"MM-DD-YYYY"` or `"—"` if input is falsy.
 */
export function formatDate(
    iso: string | null | undefined,
    timeZone?: string,
): string {
    if (!iso) return '—'
    const d = new Date(normalizeUtc(iso))
    if (isNaN(d.getTime())) return '—'

    if (timeZone) {
        const parts = new Intl.DateTimeFormat('en-US', {
            timeZone,
            month: '2-digit',
            day: '2-digit',
            year: 'numeric',
        }).formatToParts(d)

        const get = (type: Intl.DateTimeFormatPartTypes): string =>
            parts.find((p) => p.type === type)?.value ?? ''

        return `${get('month')}-${get('day')}-${get('year')}`
    }

    const mm = String(d.getMonth() + 1).padStart(2, '0')
    const dd = String(d.getDate()).padStart(2, '0')
    return `${mm}-${dd}-${d.getFullYear()}`
}
