/**
 * formatDate.ts — regression tests for UTC normalization.
 *
 * Root cause: SQLAlchemy DateTime (no tz) strips tzinfo from UTC datetimes.
 * Pydantic serializes them as naive ISO strings ("2026-04-20T18:00:00")
 * which JS Date() parses as local time, causing a timezone-offset error.
 *
 * The normalizeUtc helper appends 'Z' to naive ISO strings so they are
 * always parsed as UTC.
 *
 * @see [SCHED-TZDISPLAY-NAIVE] known-issues.md
 */

import { describe, it, expect } from 'vitest'
import { formatTimestamp, formatDate } from '../formatDate'

describe('formatTimestamp — UTC normalization', () => {
    // 18:00 UTC = 2:00 PM ET (America/New_York is UTC-4 in April/EDT)
    const tz = 'America/New_York'

    it('handles naive ISO string (no Z suffix) as UTC', () => {
        const result = formatTimestamp('2026-04-20T18:00:00', tz)
        expect(result).toMatch(/2:00PM/)
    })

    it('handles ISO string with Z suffix as UTC', () => {
        const result = formatTimestamp('2026-04-20T18:00:00Z', tz)
        expect(result).toMatch(/2:00PM/)
    })

    it('handles ISO string with +00:00 offset as UTC', () => {
        const result = formatTimestamp('2026-04-20T18:00:00+00:00', tz)
        expect(result).toMatch(/2:00PM/)
    })

    it('handles ISO string with explicit offset correctly', () => {
        // 14:00 EDT = 18:00 UTC = 2:00 PM ET
        const result = formatTimestamp('2026-04-20T14:00:00-04:00', tz)
        expect(result).toMatch(/2:00PM/)
    })

    it('naive and explicit-Z produce identical output', () => {
        const naive = formatTimestamp('2026-04-20T18:00:00', tz)
        const explicit = formatTimestamp('2026-04-20T18:00:00Z', tz)
        expect(naive).toBe(explicit)
    })

    it('returns empty string for null/undefined/empty', () => {
        expect(formatTimestamp(null)).toBe('')
        expect(formatTimestamp(undefined)).toBe('')
        expect(formatTimestamp('')).toBe('')
    })

    it('returns empty string for invalid ISO', () => {
        expect(formatTimestamp('not-a-date', tz)).toBe('')
    })
})

describe('formatDate — UTC normalization', () => {
    const tz = 'America/New_York'

    it('naive ISO string renders correct date in target timezone', () => {
        // 2026-04-21T02:00:00 UTC = Apr 20 at 10:00 PM ET
        const result = formatDate('2026-04-21T02:00:00', tz)
        expect(result).toBe('04-20-2026')
    })

    it('naive and explicit-Z produce identical output', () => {
        const naive = formatDate('2026-04-21T02:00:00', tz)
        const explicit = formatDate('2026-04-21T02:00:00Z', tz)
        expect(naive).toBe(explicit)
    })

    it('returns dash for null/undefined', () => {
        expect(formatDate(null)).toBe('—')
        expect(formatDate(undefined)).toBe('—')
    })
})
