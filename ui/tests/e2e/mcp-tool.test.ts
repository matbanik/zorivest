/**
 * E2E: MCP tool execution from simulated IDE.
 *
 * Tests the MCP tool endpoint directly via HTTP to verify the
 * MCP server responds correctly when accessed through the API.
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

test('MCP guard check endpoint responds', async () => {
    const result = await appPage.apiGet<{ is_locked: boolean }>('/mcp-guard/check')
    expect(result).toHaveProperty('is_locked')
    expect(typeof result.is_locked).toBe('boolean')
})

test('settings API returns valid configuration', async () => {
    const settings = await appPage.apiGet<Record<string, unknown>>('/settings')
    expect(settings).toBeDefined()
    expect(typeof settings).toBe('object')
})
