/**
 * Approval Token Manager — CSRF challenge tokens for policy approval.
 *
 * Generates single-use, time-limited, policy-scoped tokens that the GUI
 * includes in the X-Approval-Token header when approving policies. The
 * FastAPI server validates tokens via an internal HTTP callback to prevent
 * AI agents from self-approving policies.
 *
 * Security properties:
 *   - Single-use: token deleted after successful validation
 *   - Time-limited: 5-minute TTL
 *   - Policy-scoped: token bound to specific policy_id
 *   - Process-bound: generated in Electron main process only
 *
 * Source: 09g §9G.1c, §9G.1d
 * MEU: PH11 (approval-csrf-token)
 */

import crypto from 'node:crypto'

// ── Constants ──────────────────────────────────────────────────────────

const TOKEN_TTL_MS = 5 * 60 * 1000 // 5 minutes

// ── Token Store ────────────────────────────────────────────────────────

interface TokenEntry {
    policyId: string
    expiresAt: number
}

const tokenStore = new Map<string, TokenEntry>()

// ── Public API (exported for testability) ──────────────────────────────

export interface GenerateResult {
    token: string
    expiresAt: number
}

export interface ValidateResult {
    valid: boolean
    reason?: 'TOKEN_NOT_FOUND' | 'TOKEN_EXPIRED' | 'POLICY_MISMATCH'
}

/**
 * Generate a single-use approval token for a specific policy.
 *
 * @param policyId - The policy UUID this token is scoped to
 * @returns Token string (64-char hex) and expiration timestamp
 */
export function generateApprovalToken(policyId: string): GenerateResult {
    if (typeof policyId !== 'string' || policyId.length === 0) {
        throw new TypeError('policyId must be a non-empty string')
    }

    const token = crypto.randomBytes(32).toString('hex')
    const expiresAt = Date.now() + TOKEN_TTL_MS

    tokenStore.set(token, { policyId, expiresAt })

    return { token, expiresAt }
}

/**
 * Validate and consume an approval token.
 *
 * Single-use: the token is deleted after successful validation.
 * Checks expiry and policy scope before consuming.
 *
 * @param token - The token string to validate
 * @param policyId - The policy UUID to validate against
 * @returns Validation result with reason on failure
 */
export function validateApprovalToken(token: string, policyId: string): ValidateResult {
    if (typeof token !== 'string' || token.length === 0) {
        throw new TypeError('token must be a non-empty string')
    }
    if (typeof policyId !== 'string' || policyId.length === 0) {
        throw new TypeError('policyId must be a non-empty string')
    }

    const entry = tokenStore.get(token)

    if (!entry) {
        return { valid: false, reason: 'TOKEN_NOT_FOUND' }
    }

    if (Date.now() > entry.expiresAt) {
        tokenStore.delete(token)
        return { valid: false, reason: 'TOKEN_EXPIRED' }
    }

    if (entry.policyId !== policyId) {
        return { valid: false, reason: 'POLICY_MISMATCH' }
    }

    // Single-use: consume the token
    tokenStore.delete(token)
    return { valid: true }
}

/**
 * Reset the token store. FOR TESTING ONLY.
 */
export function _resetStoreForTesting(): void {
    tokenStore.clear()
}

// ── Callback Payload Validation ────────────────────────────────────────

/**
 * Validate and process a callback payload from the /internal/validate-token
 * HTTP endpoint. Encapsulates boundary validation (extra-field rejection,
 * type checks) and delegates to {@link validateApprovalToken} on success.
 *
 * Extracted from the HTTP handler for direct testability (R1).
 *
 * @param parsed - Raw parsed JSON body from the HTTP request
 * @returns Validation result with reason on failure
 */
export function validateCallbackPayload(
    parsed: Record<string, unknown>,
): ValidateResult & { fields?: string[] } {
    // Reject extra fields
    const allowedKeys = new Set(['token', 'policy_id'])
    const extraKeys = Object.keys(parsed).filter(k => !allowedKeys.has(k))
    if (extraKeys.length > 0) {
        return { valid: false, reason: 'EXTRA_FIELDS', fields: extraKeys }
    }

    const { token, policy_id } = parsed

    // Type checks
    if (typeof token !== 'string' || typeof policy_id !== 'string') {
        return { valid: false, reason: 'INVALID_TYPES' }
    }

    return validateApprovalToken(token, policy_id)
}

// ── Periodic Cleanup ───────────────────────────────────────────────────

/**
 * Start periodic cleanup of expired tokens to prevent memory leaks.
 * Called once during Electron main process startup.
 *
 * @returns The interval timer (for cleanup on app quit)
 */
export function startCleanupInterval(): ReturnType<typeof setInterval> {
    return setInterval(() => {
        const now = Date.now()
        for (const [token, entry] of tokenStore) {
            if (now > entry.expiresAt) {
                tokenStore.delete(token)
            }
        }
    }, 60_000)
}
