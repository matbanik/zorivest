/**
 * E2E: MCP Guard + settings checks.
 *
 * Validates that the MCP Guard and settings API endpoints
 * respond with the expected shape.
 */

import { test, expect } from '@playwright/test'
import { AppPage } from './pages/AppPage'

let appPage: AppPage

test.beforeEach(async () => {
    appPage = new AppPage()
    await appPage.launch()
})

test.afterEach(async () => {
    await appPage.close()
})

test('MCP guard status endpoint responds', async () => {
    const result = await appPage.apiGet<{ is_locked: boolean }>('/mcp-guard/status')
    expect(result).toHaveProperty('is_locked')
    expect(typeof result.is_locked).toBe('boolean')
})

test('MCP guard check endpoint responds', async () => {
    const result = await appPage.apiPost<{ allowed: boolean; reason: string }>('/mcp-guard/check', {})
    expect(result).toHaveProperty('allowed')
    expect(typeof result.allowed).toBe('boolean')
    expect(result).toHaveProperty('reason')
    expect(typeof result.reason).toBe('string')
})

test('settings API returns valid configuration', async () => {
    const settings = await appPage.apiGet<Record<string, unknown>>('/settings')
    expect(settings).toBeDefined()
})
