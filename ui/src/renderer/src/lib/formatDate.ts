/**
 * Shared date/time formatting — DT1/DT2 standard.
 *
 * Format: MM-DD-YYYY h:mmAM/PM
 * No seconds in UI display. Full ISO precision preserved in data layer.
 *
 * @see .agent/docs/emerging-standards.md §DT1, §DT2
 */

/**
 * Format an ISO timestamp for UI display.
 *
 * @returns `"MM-DD-YYYY h:mmAM/PM"` or `""` if input is falsy.
 */
export function formatTimestamp(iso: string | null | undefined): string {
    if (!iso) return ''
    const d = new Date(iso)
    if (isNaN(d.getTime())) return ''
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
 * @returns `"MM-DD-YYYY"` or `"—"` if input is falsy.
 */
export function formatDate(iso: string | null | undefined): string {
    if (!iso) return '—'
    const d = new Date(iso)
    if (isNaN(d.getTime())) return '—'
    const mm = String(d.getMonth() + 1).padStart(2, '0')
    const dd = String(d.getDate()).padStart(2, '0')
    return `${mm}-${dd}-${d.getFullYear()}`
}
