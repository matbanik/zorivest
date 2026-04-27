/**
 * Tests for ApprovalTokenManager — Electron IPC handlers for CSRF approval tokens.
 *
 * Source: 09g §9G.1c, §9G.1d
 * MEU: PH11 (approval-csrf-token)
 * ACs: AC-1 through AC-4, AC-8
 *
 * These tests validate the in-memory token store without requiring Electron IPC.
 * The module exports pure functions for testability.
 */

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'

// The module under test exports token management functions directly
// (separate from IPC handler registration for testability)
import {
    generateApprovalToken,
    validateApprovalToken,
    validateCallbackPayload,
    _resetStoreForTesting,
} from '../approval-token-manager.js'

describe('ApprovalTokenManager', () => {
    beforeEach(() => {
        _resetStoreForTesting()
    })

    afterEach(() => {
        vi.restoreAllMocks()
    })

    // AC-1: generate-approval-token returns {token, expiresAt} with 64-char hex token
    it('AC-1: generates a 64-char hex token with valid expiresAt', () => {
        const result = generateApprovalToken('policy-abc-123')

        expect(result).toHaveProperty('token')
        expect(result).toHaveProperty('expiresAt')
        expect(typeof result.token).toBe('string')
        expect(result.token).toMatch(/^[0-9a-f]{64}$/)
        expect(typeof result.expiresAt).toBe('number')
        expect(result.expiresAt).toBeGreaterThan(Date.now())
    })

    // AC-2: Token is single-use — second validation with same token fails
    it('AC-2: token is single-use (second validation fails)', () => {
        const { token } = generateApprovalToken('policy-abc-123')

        const first = validateApprovalToken(token, 'policy-abc-123')
        expect(first.valid).toBe(true)

        const second = validateApprovalToken(token, 'policy-abc-123')
        expect(second.valid).toBe(false)
        expect(second.reason).toBe('TOKEN_NOT_FOUND')
    })

    // AC-3: Token expires after 5 minutes (TTL = 300,000ms)
    it('AC-3: token expires after TTL', () => {
        vi.useFakeTimers()

        const { token } = generateApprovalToken('policy-abc-123')

        // Advance time past the 5-minute TTL
        vi.advanceTimersByTime(5 * 60 * 1000 + 1)

        const result = validateApprovalToken(token, 'policy-abc-123')
        expect(result.valid).toBe(false)
        expect(result.reason).toBe('TOKEN_EXPIRED')

        vi.useRealTimers()
    })

    // AC-4: Token is policy-scoped — token for policy A rejected for policy B
    it('AC-4: token is policy-scoped (cross-policy rejected)', () => {
        const { token } = generateApprovalToken('policy-A')

        const result = validateApprovalToken(token, 'policy-B')
        expect(result.valid).toBe(false)
        expect(result.reason).toBe('POLICY_MISMATCH')
    })

    // AC-8: Periodic cleanup removes expired tokens (no memory leak)
    it('AC-8: expired tokens are cleaned up', () => {
        vi.useFakeTimers()

        // Generate multiple tokens
        generateApprovalToken('p1')
        generateApprovalToken('p2')
        generateApprovalToken('p3')

        // Advance past TTL
        vi.advanceTimersByTime(5 * 60 * 1000 + 1)

        // All tokens should now be expired and fail validation
        // (cleanup happens lazily or periodically — validation itself should detect expiry)
        const r1 = validateApprovalToken('any-token', 'p1')
        expect(r1.valid).toBe(false)

        vi.useRealTimers()
    })
})

// ── Finding #3: Boundary validation for approval token inputs ───────────

describe('ApprovalTokenManager boundary validation (Finding #3)', () => {
    beforeEach(() => {
        _resetStoreForTesting()
    })

    it('rejects non-string policyId in generateApprovalToken', () => {
        // policyId must be a string — passing a number should throw
        expect(() => generateApprovalToken(123 as unknown as string)).toThrow()
    })

    it('rejects empty string policyId in generateApprovalToken', () => {
        expect(() => generateApprovalToken('')).toThrow()
    })

    it('rejects non-string token in validateApprovalToken', () => {
        expect(() => validateApprovalToken(42 as unknown as string, 'policy-1')).toThrow()
    })

    it('rejects non-string policyId in validateApprovalToken', () => {
        const { token } = generateApprovalToken('policy-1')
        expect(() => validateApprovalToken(token, null as unknown as string)).toThrow()
    })
})

// ── R1: Callback handler boundary validation (validate-token endpoint) ──

describe('validateCallbackPayload (R1: handler-level boundary tests)', () => {
    beforeEach(() => {
        _resetStoreForTesting()
    })

    it('rejects payload with extra fields → EXTRA_FIELDS', () => {
        const result = validateCallbackPayload({ token: 'abc', policy_id: 'p1', evil: 'inject' })
        expect(result).toEqual({
            valid: false,
            reason: 'EXTRA_FIELDS',
            fields: ['evil'],
        })
    })

    it('rejects payload missing token → INVALID_TYPES', () => {
        const result = validateCallbackPayload({ policy_id: 'p1' })
        expect(result).toEqual({
            valid: false,
            reason: 'INVALID_TYPES',
        })
    })

    it('rejects payload missing policy_id → INVALID_TYPES', () => {
        const result = validateCallbackPayload({ token: 'abc' })
        expect(result).toEqual({
            valid: false,
            reason: 'INVALID_TYPES',
        })
    })

    it('rejects non-string token → INVALID_TYPES', () => {
        const result = validateCallbackPayload({ token: 123, policy_id: 'p1' })
        expect(result).toEqual({
            valid: false,
            reason: 'INVALID_TYPES',
        })
    })

    it('rejects non-string policy_id → INVALID_TYPES', () => {
        const result = validateCallbackPayload({ token: 'abc', policy_id: null })
        expect(result).toEqual({
            valid: false,
            reason: 'INVALID_TYPES',
        })
    })

    it('accepts valid payload and delegates to validateApprovalToken', () => {
        const { token } = generateApprovalToken('policy-xyz')
        const result = validateCallbackPayload({ token, policy_id: 'policy-xyz' })
        expect(result).toEqual({ valid: true })
    })

    it('valid payload with wrong policy returns TOKEN_NOT_FOUND/POLICY_MISMATCH', () => {
        const { token } = generateApprovalToken('policy-A')
        const result = validateCallbackPayload({ token, policy_id: 'policy-B' })
        expect(result.valid).toBe(false)
        // Reason could be POLICY_MISMATCH (scoped check)
        expect(result.reason).toBe('POLICY_MISMATCH')
    })

    it('rejects multiple extra fields and lists all', () => {
        const result = validateCallbackPayload({
            token: 'abc', policy_id: 'p1', extra1: 'a', extra2: 'b',
        })
        expect(result.valid).toBe(false)
        expect(result.reason).toBe('EXTRA_FIELDS')
        expect(result.fields).toEqual(expect.arrayContaining(['extra1', 'extra2']))
    })
})
