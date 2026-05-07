/**
 * MEU-203: Scheduling Enhancements — Red-Phase Tests
 *
 * FIC: docs/execution/plans/2026-05-03-gui-table-list-enhancements/fic-meu-203.md
 * These tests MUST fail in Red phase and pass after implementation (Green phase).
 *
 * Tests PolicyList and EmailTemplateList directly.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import '@testing-library/jest-dom/vitest'
import React from 'react'

import PolicyList from '../PolicyList'
import EmailTemplateList from '../EmailTemplateList'
import type { Policy } from '../api'
import type { EmailTemplate } from '../template-api'

// ── Test Data ───────────────────────────────────────────────────────────────

const MOCK_POLICIES: Policy[] = [
    {
        id: 'pol-1',
        name: 'Daily Report',
        schema_version: 1,
        enabled: true,
        approved: true,
        approved_at: '2026-01-01T00:00:00Z',
        policy_json: { trigger: { cron_expression: '0 8 * * *', enabled: true, timezone: 'UTC' }, steps: [] },
        content_hash: 'abc123',
        next_run: '2026-05-04T08:00:00Z',
        created_at: '2026-01-01T00:00:00Z',
        updated_at: '2026-05-03T08:00:00Z',
    },
    {
        id: 'pol-2',
        name: 'Weekly Summary',
        schema_version: 1,
        enabled: false,
        approved: true,
        approved_at: '2026-01-02T00:00:00Z',
        policy_json: { trigger: { cron_expression: '0 9 * * 1', enabled: false, timezone: 'UTC' }, steps: [] },
        content_hash: 'def456',
        next_run: null,
        created_at: '2026-01-02T00:00:00Z',
        updated_at: '2026-01-02T00:00:00Z',
    },
    {
        id: 'pol-3',
        name: 'Monthly Rebalance',
        schema_version: 1,
        enabled: true,
        approved: true,
        approved_at: '2026-01-03T00:00:00Z',
        policy_json: { trigger: { cron_expression: '0 6 1 * *', enabled: true, timezone: 'UTC' }, steps: [] },
        content_hash: 'ghi789',
        next_run: '2026-06-01T06:00:00Z',
        created_at: '2026-01-03T00:00:00Z',
        updated_at: '2026-05-01T06:00:00Z',
    },
]

const MOCK_TEMPLATES: EmailTemplate[] = [
    {
        name: 'default-report',
        subject_template: 'Daily Report: {{ date }}',
        body_html: '<h1>Report</h1>',
        body_format: 'html',
        description: 'Default report template',
        required_variables: ['date'],
        sample_data_json: '{}',
        is_default: true,
    },
    {
        name: 'weekly-digest',
        subject_template: 'Weekly Digest',
        body_html: '<h1>Digest</h1>',
        body_format: 'html',
        description: 'Weekly email digest',
        required_variables: [],
        sample_data_json: '{}',
        is_default: false,
    },
    {
        name: 'alert-notify',
        subject_template: 'Alert: {{ ticker }}',
        body_html: '<h1>Alert</h1>',
        body_format: 'html',
        description: 'Price alert notification',
        required_variables: ['ticker'],
        sample_data_json: '{}',
        is_default: false,
    },
]

// ── Helpers ──────────────────────────────────────────────────────────────────

const mockPolicySelect = vi.fn()
const mockPolicyCreate = vi.fn()
const mockTemplateSelect = vi.fn()
const mockTemplateCreate = vi.fn()

function renderPolicyList(overrides: Partial<Parameters<typeof PolicyList>[0]> = {}) {
    return render(
        <PolicyList
            policies={MOCK_POLICIES}
            selectedPolicyId={null}
            onSelect={mockPolicySelect}
            onCreate={mockPolicyCreate}
            isLoading={false}
            error={null}
            {...overrides}
        />,
    )
}

function renderTemplateList(overrides: Partial<Parameters<typeof EmailTemplateList>[0]> = {}) {
    return render(
        <EmailTemplateList
            templates={MOCK_TEMPLATES}
            selectedTemplateName={null}
            onSelect={mockTemplateSelect}
            onCreate={mockTemplateCreate}
            isLoading={false}
            error={null}
            {...overrides}
        />,
    )
}

// ── MEU-203 Red-Phase Tests ─────────────────────────────────────────────────

describe('MEU-203: Scheduling Enhancements', () => {
    beforeEach(() => {
        vi.clearAllMocks()
    })

    // ── PolicyList Enhancements ──────────────────────────────────────────

    describe('PolicyList enhancements', () => {
        describe('AC-1: Multi-select checkboxes', () => {
            it('renders a SelectionCheckbox in each policy item', () => {
                renderPolicyList()
                expect(screen.getByTestId('policy-row-checkbox-pol-1')).toBeInTheDocument()
                expect(screen.getByTestId('policy-row-checkbox-pol-2')).toBeInTheDocument()
                expect(screen.getByTestId('policy-row-checkbox-pol-3')).toBeInTheDocument()
            })

            it('renders a header SelectionCheckbox that toggles all', async () => {
                const user = userEvent.setup()
                renderPolicyList()
                const selectAll = screen.getByTestId('select-all-policy-checkbox')
                await user.click(selectAll)

                const cb1 = screen.getByTestId('policy-row-checkbox-pol-1') as HTMLInputElement
                const cb2 = screen.getByTestId('policy-row-checkbox-pol-2') as HTMLInputElement
                const cb3 = screen.getByTestId('policy-row-checkbox-pol-3') as HTMLInputElement
                expect(cb1.checked).toBe(true)
                expect(cb2.checked).toBe(true)
                expect(cb3.checked).toBe(true)
            })
        })

        describe('AC-2: Bulk delete', () => {
            it('shows BulkActionBar when ≥1 policy selected', async () => {
                const user = userEvent.setup()
                renderPolicyList()
                await user.click(screen.getByTestId('policy-row-checkbox-pol-1'))
                expect(screen.getByTestId('bulk-action-bar')).toBeInTheDocument()
            })
        })

        describe('AC-3: Search filter', () => {
            it('renders a search input', () => {
                renderPolicyList()
                expect(screen.getByTestId('policy-search-input')).toBeInTheDocument()
            })

            it('filters policies by name', async () => {
                const user = userEvent.setup()
                renderPolicyList()
                const search = screen.getByTestId('policy-search-input')
                await user.type(search, 'Daily')

                await waitFor(() => {
                    expect(screen.getByText('Daily Report')).toBeInTheDocument()
                    expect(screen.queryByText('Weekly Summary')).not.toBeInTheDocument()
                    expect(screen.queryByText('Monthly Rebalance')).not.toBeInTheDocument()
                })
            })
        })
    })

    // ── EmailTemplateList Enhancements ────────────────────────────────────

    describe('EmailTemplateList enhancements', () => {
        describe('AC-4: Multi-select checkboxes', () => {
            it('renders a SelectionCheckbox in each template item', () => {
                renderTemplateList()
                expect(screen.getByTestId('template-row-checkbox-default-report')).toBeInTheDocument()
                expect(screen.getByTestId('template-row-checkbox-weekly-digest')).toBeInTheDocument()
                expect(screen.getByTestId('template-row-checkbox-alert-notify')).toBeInTheDocument()
            })

            it('renders a header SelectionCheckbox that toggles all', async () => {
                const user = userEvent.setup()
                renderTemplateList()
                const selectAll = screen.getByTestId('select-all-template-checkbox')
                await user.click(selectAll)

                const cb1 = screen.getByTestId('template-row-checkbox-default-report') as HTMLInputElement
                const cb2 = screen.getByTestId('template-row-checkbox-weekly-digest') as HTMLInputElement
                const cb3 = screen.getByTestId('template-row-checkbox-alert-notify') as HTMLInputElement
                expect(cb1.checked).toBe(true)
                expect(cb2.checked).toBe(true)
                expect(cb3.checked).toBe(true)
            })
        })

        describe('AC-5: Bulk delete', () => {
            it('shows BulkActionBar when ≥1 template selected', async () => {
                const user = userEvent.setup()
                renderTemplateList()
                await user.click(screen.getByTestId('template-row-checkbox-weekly-digest'))
                expect(screen.getByTestId('bulk-action-bar')).toBeInTheDocument()
            })
        })

        describe('AC-6: Search filter', () => {
            it('renders a search input', () => {
                renderTemplateList()
                expect(screen.getByTestId('template-search-input')).toBeInTheDocument()
            })

            it('filters templates by name', async () => {
                const user = userEvent.setup()
                renderTemplateList()
                const search = screen.getByTestId('template-search-input')
                await user.type(search, 'alert')

                await waitFor(() => {
                    expect(screen.queryByText('default-report')).not.toBeInTheDocument()
                    expect(screen.queryByText('weekly-digest')).not.toBeInTheDocument()
                    expect(screen.getByText('alert-notify')).toBeInTheDocument()
                })
            })
        })
    })
})
