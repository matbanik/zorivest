import { describe, it, expect, vi, beforeEach } from 'vitest'

// Mock electron-store before importing module
const mockGet = vi.fn()
const mockSet = vi.fn()

vi.mock('electron-store', () => ({
    default: class MockStore {
        get = mockGet
        set = mockSet
    },
}))

import {
    getStoredBounds,
    saveWindowBounds,
    DEFAULT_BOUNDS,
} from '../window-state'

describe('Window State Persistence', () => {
    beforeEach(() => {
        vi.clearAllMocks()
    })

    describe('DEFAULT_BOUNDS', () => {
        it('should have width 1280 and height 800', () => {
            expect(DEFAULT_BOUNDS.width).toBe(1280)
            expect(DEFAULT_BOUNDS.height).toBe(800)
        })
    })

    describe('getStoredBounds', () => {
        it('should return stored bounds when available', () => {
            const stored = { x: 100, y: 200, width: 1440, height: 900 }
            mockGet.mockReturnValue(stored)
            const result = getStoredBounds()
            expect(result).toEqual(stored)
            expect(mockGet).toHaveBeenCalledWith('windowBounds')
        })

        it('should return default bounds when no stored value', () => {
            mockGet.mockReturnValue(undefined)
            const result = getStoredBounds()
            expect(result).toEqual(DEFAULT_BOUNDS)
        })
    })

    describe('saveWindowBounds', () => {
        it('should save bounds to store', () => {
            const bounds = { x: 50, y: 50, width: 1200, height: 700 }
            saveWindowBounds(bounds)
            expect(mockSet).toHaveBeenCalledWith('windowBounds', bounds)
        })
    })
})
