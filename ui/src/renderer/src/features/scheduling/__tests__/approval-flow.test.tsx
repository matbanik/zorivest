/**
 * Tests for renderer approval flow — IPC token injection into approve calls.
 *
 * Source: 09g §9G.1c, flow diagram L24–35
 * MEU: PH11 (approval-csrf-token)
 * ACs: AC-10, AC-11
 *
 * These tests validate that:
 * 1. approvePolicy() calls the preload IPC to get a token and injects it as a header
 * 2. If the IPC returns null/undefined, the approve call fails gracefully
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

// We mock apiFetch to intercept the actual HTTP call and verify headers
vi.mock('@/lib/api', () => ({
    apiFetch: vi.fn(),
}))

import { apiFetch } from '@/lib/api'
import { approvePolicy } from '../api.js'

const mockedApiFetch = vi.mocked(apiFetch)

describe('Renderer Approval Flow', () => {
    beforeEach(() => {
        mockedApiFetch.mockReset()
        // Set up the global electronAPI mock (preload exposes this)
        ;(globalThis as any).window = {
            ...(globalThis as any).window,
            electronAPI: {
                generateApprovalToken: vi.fn(),
            },
        }
    })

    afterEach(() => {
        vi.restoreAllMocks()
        delete (globalThis as any).window?.electronAPI
    })

    // AC-10: approvePolicy() calls IPC for token and injects X-Approval-Token header
    it('AC-10: calls IPC to generate token and sends X-Approval-Token header', async () => {
        const fakeToken = 'a'.repeat(64)
        const fakeExpiresAt = Date.now() + 300_000
        ;(globalThis as any).window.electronAPI.generateApprovalToken = vi.fn().mockResolvedValue({
            token: fakeToken,
            expiresAt: fakeExpiresAt,
        })

        mockedApiFetch.mockResolvedValue({ id: 'policy-123', approved: true })

        await approvePolicy('policy-123')

        // Verify IPC was called with the policy ID
        expect((globalThis as any).window.electronAPI.generateApprovalToken).toHaveBeenCalledWith('policy-123')

        // Verify apiFetch was called with the X-Approval-Token header
        expect(mockedApiFetch).toHaveBeenCalledTimes(1)
        const callArgs = mockedApiFetch.mock.calls[0]
        expect(callArgs[0]).toContain('/policies/policy-123/approve')
        expect(callArgs[1]).toBeDefined()

        const options = callArgs[1] as RequestInit
        expect(options.method).toBe('POST')

        // The X-Approval-Token header must be present
        const headers = options.headers as Record<string, string> | undefined
        expect(headers).toBeDefined()
        expect(headers?.['X-Approval-Token']).toBe(fakeToken)
    })

    // AC-11: If IPC returns null, approve call fails (does not silently proceed without token)
    it('AC-11: rejects when IPC returns null token', async () => {
        ;(globalThis as any).window.electronAPI.generateApprovalToken = vi.fn().mockResolvedValue(null)

        await expect(approvePolicy('policy-123')).rejects.toThrow()

        // apiFetch should NOT be called if the token is null
        expect(mockedApiFetch).not.toHaveBeenCalled()
    })
})
