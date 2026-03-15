import { describe, it, expect, vi, beforeEach } from 'vitest'

// Mock window.api from contextBridge
const mockBaseUrl = 'http://127.0.0.1:54321'
const mockToken = 'a'.repeat(64)

Object.defineProperty(globalThis, 'window', {
    value: {
        api: {
            baseUrl: mockBaseUrl,
            token: mockToken,
        },
    },
    writable: true,
})

// Import after window mock is set up
import { apiFetch } from '../api'

describe('apiFetch', () => {
    beforeEach(() => {
        vi.restoreAllMocks()
    })

    it('should include Bearer token in Authorization header', async () => {
        const fetchMock = vi.fn().mockResolvedValue({
            ok: true,
            json: () => Promise.resolve({ data: 'test' }),
        })
        global.fetch = fetchMock

        await apiFetch('/test')

        expect(fetchMock).toHaveBeenCalledWith(
            `${mockBaseUrl}/test`,
            expect.objectContaining({
                headers: expect.objectContaining({
                    Authorization: `Bearer ${mockToken}`,
                }),
            }),
        )
    })

    it('should set Content-Type to application/json', async () => {
        const fetchMock = vi.fn().mockResolvedValue({
            ok: true,
            json: () => Promise.resolve({}),
        })
        global.fetch = fetchMock

        await apiFetch('/test')

        expect(fetchMock).toHaveBeenCalledWith(
            expect.any(String),
            expect.objectContaining({
                headers: expect.objectContaining({
                    'Content-Type': 'application/json',
                }),
            }),
        )
    })

    it('should throw on non-ok response', async () => {
        global.fetch = vi.fn().mockResolvedValue({
            ok: false,
            status: 500,
            text: () => Promise.resolve('Internal Server Error'),
        })

        await expect(apiFetch('/fail')).rejects.toThrow('API 500')
    })

    it('should return parsed JSON on success', async () => {
        const payload = { accounts: [{ id: 1, name: 'Test' }] }
        global.fetch = vi.fn().mockResolvedValue({
            ok: true,
            json: () => Promise.resolve(payload),
        })

        const result = await apiFetch('/accounts')
        expect(result).toEqual(payload)
    })

    it('should merge custom headers with defaults', async () => {
        const fetchMock = vi.fn().mockResolvedValue({
            ok: true,
            json: () => Promise.resolve({}),
        })
        global.fetch = fetchMock

        await apiFetch('/test', {
            headers: { 'X-Custom': 'value' },
        })

        const callHeaders = fetchMock.mock.calls[0][1].headers
        expect(callHeaders['X-Custom']).toBe('value')
        expect(callHeaders['Authorization']).toContain('Bearer')
    })
})
