import { describe, it, expect } from 'vitest'
import { queryClient } from '../query-client'

describe('queryClient defaults', () => {
    it('should have staleTime = 0 (financial data always stale)', () => {
        const defaults = queryClient.getDefaultOptions()
        expect(defaults.queries?.staleTime).toBe(0)
    })

    it('should have gcTime = 300000 (5 minutes)', () => {
        const defaults = queryClient.getDefaultOptions()
        expect(defaults.queries?.gcTime).toBe(5 * 60 * 1000)
    })

    it('should have mutations.retry = false (never auto-retry financial transactions)', () => {
        const defaults = queryClient.getDefaultOptions()
        expect(defaults.mutations?.retry).toBe(false)
    })

    it('should have refetchOnWindowFocus = true', () => {
        const defaults = queryClient.getDefaultOptions()
        expect(defaults.queries?.refetchOnWindowFocus).toBe(true)
    })

    it('should have retry = 2 for queries', () => {
        const defaults = queryClient.getDefaultOptions()
        expect(defaults.queries?.retry).toBe(2)
    })
})
