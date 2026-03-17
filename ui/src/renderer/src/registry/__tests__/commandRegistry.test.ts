import { describe, it, expect } from 'vitest'
import { createStaticEntries } from '../commandRegistry'
import type { CommandRegistryEntry } from '../types'

const staticEntries = createStaticEntries(() => { /* test stub */ })

describe('CommandRegistryEntry type contract', () => {
    it('should have all required fields on every entry', () => {
        const requiredFields: (keyof CommandRegistryEntry)[] = [
            'id',
            'label',
            'category',
            'keywords',
            'action',
        ]
        for (const entry of staticEntries) {
            for (const field of requiredFields) {
                expect(entry).toHaveProperty(field)
            }
            // Value: verify id follows naming convention
            expect(entry.id).toMatch(/^(nav:|action:|settings:)/)
        }
    })

    it('every entry.id should be a non-empty string', () => {
        for (const entry of staticEntries) {
            expect(typeof entry.id).toBe('string')
            expect(entry.id.length).toBeGreaterThan(0)
        }
    })

    it('every entry.action should be a function', () => {
        for (const entry of staticEntries) {
            expect(typeof entry.action).toBe('function')
        }
    })
})

describe('Static registry', () => {
    it('should have ≥13 entries: 5 nav + 3 action + 5 settings', () => {
        expect(staticEntries.length).toBeGreaterThanOrEqual(13)
    })

    it('all ids should be unique', () => {
        const ids = staticEntries.map((e) => e.id)
        expect(new Set(ids).size).toBe(ids.length)
    })

    it('should have 5 navigation entries matching canonical routes', () => {
        const navEntries = staticEntries.filter((e) => e.category === 'navigation')
        expect(navEntries.length).toBe(5)
        const labels = navEntries.map((e) => e.label)
        expect(labels).toContain('Accounts')
        expect(labels).toContain('Trades')
        expect(labels).toContain('Planning')
        expect(labels).toContain('Scheduling')
        expect(labels).toContain('Settings')
    })

    it('should have 3 action entries per spec (calc, import, review)', () => {
        const actionEntries = staticEntries.filter((e) => e.category === 'action')
        expect(actionEntries.length).toBe(3)
        const ids = actionEntries.map((e) => e.id)
        expect(ids).toContain('action:calc')
        expect(ids).toContain('action:import')
        expect(ids).toContain('action:review')
    })

    it('should have 5 settings entries navigating to /settings sub-routes', () => {
        const settingsEntries = staticEntries.filter((e) => e.category === 'settings')
        expect(settingsEntries.length).toBe(5)
        const ids = settingsEntries.map((e) => e.id)
        expect(ids).toContain('settings:market')
        expect(ids).toContain('settings:email')
        expect(ids).toContain('settings:display')
        expect(ids).toContain('settings:notifications')
        expect(ids).toContain('settings:logging')
    })

    it('navigation entries should have shortcut field', () => {
        const navEntries = staticEntries.filter((e) => e.category === 'navigation')
        for (const entry of navEntries) {
            expect(entry.shortcut).toBeDefined()
            // Value: verify shortcut is a non-empty string
            expect(typeof entry.shortcut).toBe('string')
            expect(entry.shortcut!.length).toBeGreaterThan(0)
        }
    })

    it('navigation entries should call navigate with correct path', () => {
        const paths: string[] = []
        const trackingNav = (path: string) => { paths.push(path) }
        const entries = createStaticEntries(trackingNav)
        const navEntries = entries.filter((e) => e.category === 'navigation')
        for (const entry of navEntries) {
            entry.action()
        }
        expect(paths).toEqual(['/', '/trades', '/planning', '/scheduling', '/settings'])
    })

    it('settings entries should call navigate with /settings sub-routes', () => {
        const paths: string[] = []
        const trackingNav = (path: string) => { paths.push(path) }
        const entries = createStaticEntries(trackingNav)
        const settingsEntries = entries.filter((e) => e.category === 'settings')
        for (const entry of settingsEntries) {
            entry.action()
        }
        expect(paths).toEqual([
            '/settings/market',
            '/settings/email',
            '/settings/display',
            '/settings/notifications',
            '/settings/logging',
        ])
    })
})
