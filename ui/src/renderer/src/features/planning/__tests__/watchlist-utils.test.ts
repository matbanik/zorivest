/**
 * Unit tests for watchlist-utils.ts formatting utilities.
 *
 * MEU-70a Sub-MEU B — Red-phase TDD tests.
 *
 * Utilities: formatVolume, formatPrice, getChangeColor, formatFreshness
 * Sources: 06i §1 (columns), 06i §2 (tokens), 06i §5 (coloring), 06i §6 (freshness)
 */

import { describe, it, expect } from 'vitest'
import {
    formatVolume,
    formatPrice,
    getChangeColor,
    formatFreshness,
} from '../watchlist-utils'

// ── formatVolume ────────────────────────────────────────────────────────
// AC-15: Volume formatted as abbreviated (1.2M, 45.3K, 0 for null)

describe('formatVolume', () => {
    it('returns "—" for null', () => {
        expect(formatVolume(null)).toBe('—')
    })

    it('returns "—" for undefined', () => {
        expect(formatVolume(undefined)).toBe('—')
    })

    it('returns "0" for zero', () => {
        expect(formatVolume(0)).toBe('0')
    })

    it('formats thousands with K suffix', () => {
        expect(formatVolume(45_300)).toBe('45.3K')
    })

    it('formats millions with M suffix', () => {
        expect(formatVolume(1_200_000)).toBe('1.2M')
    })

    it('formats billions with B suffix', () => {
        expect(formatVolume(2_500_000_000)).toBe('2.5B')
    })

    it('formats exact thousands without decimal', () => {
        expect(formatVolume(1_000)).toBe('1.0K')
    })

    it('formats values under 1000 as plain numbers', () => {
        expect(formatVolume(750)).toBe('750')
    })

    it('drops trailing zero intelligently for M', () => {
        // 1,000,000 → "1.0M"
        expect(formatVolume(1_000_000)).toBe('1.0M')
    })
})

// ── formatPrice ─────────────────────────────────────────────────────────
// Standard financial formatting: 2 decimal places

describe('formatPrice', () => {
    it('returns "—" for null', () => {
        expect(formatPrice(null)).toBe('—')
    })

    it('returns "—" for undefined', () => {
        expect(formatPrice(undefined)).toBe('—')
    })

    it('formats price with 2 decimal places', () => {
        expect(formatPrice(123.4)).toBe('123.40')
    })

    it('formats whole number with 2 decimals', () => {
        expect(formatPrice(100)).toBe('100.00')
    })

    it('formats zero', () => {
        expect(formatPrice(0)).toBe('0.00')
    })

    it('formats large price', () => {
        expect(formatPrice(4523.789)).toBe('4,523.79')
    })

    it('formats negative price with minus', () => {
        expect(formatPrice(-5.5)).toBe('-5.50')
    })
})

// ── getChangeColor ──────────────────────────────────────────────────────
// AC-11: green #26A69A positive, red #EF5350 negative, muted for zero
// AC-18: colorblind-safe: blue #2962FF positive, orange #FF6D00 negative

describe('getChangeColor', () => {
    describe('normal mode (colorblind=false)', () => {
        it('returns green for positive value', () => {
            expect(getChangeColor(1.5, false)).toBe('#26A69A')
        })

        it('returns red for negative value', () => {
            expect(getChangeColor(-2.3, false)).toBe('#EF5350')
        })

        it('returns muted for zero', () => {
            const color = getChangeColor(0, false)
            // Muted color should NOT be green or red
            expect(color).not.toBe('#26A69A')
            expect(color).not.toBe('#EF5350')
        })

        it('returns muted for null', () => {
            const color = getChangeColor(null, false)
            expect(color).not.toBe('#26A69A')
            expect(color).not.toBe('#EF5350')
        })
    })

    describe('colorblind mode (colorblind=true)', () => {
        it('returns blue for positive value', () => {
            expect(getChangeColor(1.5, true)).toBe('#2962FF')
        })

        it('returns orange for negative value', () => {
            expect(getChangeColor(-2.3, true)).toBe('#FF6D00')
        })

        it('returns muted for zero', () => {
            const color = getChangeColor(0, true)
            expect(color).not.toBe('#2962FF')
            expect(color).not.toBe('#FF6D00')
        })
    })
})

// ── formatFreshness ─────────────────────────────────────────────────────
// AC-17: "Updated Xs ago" freshness indicator

describe('formatFreshness', () => {
    it('returns "No data" for null timestamp', () => {
        expect(formatFreshness(null)).toBe('No data')
    })

    it('returns "No data" for undefined timestamp', () => {
        expect(formatFreshness(undefined)).toBe('No data')
    })

    it('returns "Just now" for very recent timestamps', () => {
        const now = new Date()
        expect(formatFreshness(now.toISOString())).toBe('Just now')
    })

    it('returns "Xs ago" for seconds-old timestamps', () => {
        const tenSecondsAgo = new Date(Date.now() - 10_000)
        expect(formatFreshness(tenSecondsAgo.toISOString())).toBe('10s ago')
    })

    it('returns "Xm ago" for minutes-old timestamps', () => {
        const twoMinutesAgo = new Date(Date.now() - 2 * 60_000)
        expect(formatFreshness(twoMinutesAgo.toISOString())).toBe('2m ago')
    })

    it('returns "Xh ago" for hours-old timestamps', () => {
        const threeHoursAgo = new Date(Date.now() - 3 * 3_600_000)
        expect(formatFreshness(threeHoursAgo.toISOString())).toBe('3h ago')
    })

    it('returns "Xd ago" for days-old timestamps', () => {
        const twoDaysAgo = new Date(Date.now() - 2 * 86_400_000)
        expect(formatFreshness(twoDaysAgo.toISOString())).toBe('2d ago')
    })
})
