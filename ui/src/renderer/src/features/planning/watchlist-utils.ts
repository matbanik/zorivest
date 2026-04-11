/**
 * Watchlist formatting utilities.
 *
 * MEU-70a Sub-MEU B — pure functions for watchlist table rendering.
 *
 * Sources:
 * - 06i §1 (column hierarchy, volume format)
 * - 06i §2 (design tokens, color values)
 * - 06i §5 (gain/loss coloring rules)
 * - 06i §6 (freshness indicator)
 * - 06i §7 (colorblind-safe palette)
 */

// ── Color tokens (06i §2) ───────────────────────────────────────────────
const COLOR_GAIN = '#26A69A'       // Green — positive change
const COLOR_LOSS = '#EF5350'       // Red — negative change
const COLOR_MUTED = '#787B86'      // Muted — zero/null change

const COLOR_CB_GAIN = '#2962FF'    // Colorblind blue — positive
const COLOR_CB_LOSS = '#FF6D00'    // Colorblind orange — negative

// ── formatVolume ────────────────────────────────────────────────────────
// AC-15: Abbreviated volume: 1.2M, 45.3K, 0 for null → "—"

export function formatVolume(volume: number | null | undefined): string {
    if (volume === null || volume === undefined) return '—'
    if (volume === 0) return '0'
    if (volume < 1_000) return String(volume)

    if (volume >= 1_000_000_000) {
        return `${(volume / 1_000_000_000).toFixed(1)}B`
    }
    if (volume >= 1_000_000) {
        return `${(volume / 1_000_000).toFixed(1)}M`
    }
    return `${(volume / 1_000).toFixed(1)}K`
}

// ── formatPrice ─────────────────────────────────────────────────────────
// Standard financial: 2 decimal places, thousands separator

export function formatPrice(price: number | null | undefined): string {
    if (price === null || price === undefined) return '—'

    return price.toLocaleString('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
    })
}

// ── getChangeColor ──────────────────────────────────────────────────────
// AC-11: green positive, red negative, muted zero
// AC-18: colorblind — blue positive, orange negative

export function getChangeColor(
    value: number | null | undefined,
    colorblind: boolean,
): string {
    if (value === null || value === undefined || value === 0) {
        return COLOR_MUTED
    }

    if (colorblind) {
        return value > 0 ? COLOR_CB_GAIN : COLOR_CB_LOSS
    }
    return value > 0 ? COLOR_GAIN : COLOR_LOSS
}

// ── formatFreshness ─────────────────────────────────────────────────────
// AC-17: "Updated Xs ago" freshness indicator

export function formatFreshness(
    isoTimestamp: string | null | undefined,
): string {
    if (!isoTimestamp) return 'No data'

    const elapsed = Date.now() - new Date(isoTimestamp).getTime()
    const seconds = Math.floor(elapsed / 1_000)

    if (seconds < 5) return 'Just now'
    if (seconds < 60) return `${seconds}s ago`

    const minutes = Math.floor(seconds / 60)
    if (minutes < 60) return `${minutes}m ago`

    const hours = Math.floor(minutes / 60)
    if (hours < 24) return `${hours}h ago`

    const days = Math.floor(hours / 24)
    return `${days}d ago`
}
