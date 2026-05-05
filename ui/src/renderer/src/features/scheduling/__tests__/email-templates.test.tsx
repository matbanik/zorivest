/**
 * Tests for Email Templates feature (MEU-72b).
 *
 * Feature Intent Contract (FIC)
 * =============================
 *
 * AC-72b-1 [Spec §6K.1]: SchedulingLayout has tab bar with "Report Policies"
 *          (default) + "Email Templates" tabs.
 * AC-72b-2 [Spec §6K.2]: EmailTemplateList renders list with name + is_default
 *          badge, uses refetchInterval: 5_000 (G5).
 * AC-72b-3 [Spec §6K.3]: EmailTemplateDetail renders all fields (name, description,
 *          format, subject, required_variables, body).
 * AC-72b-4 [Spec §6K.4]: Default templates show read-only editor + protection banner.
 * AC-72b-5 [Spec §6K.5]: Save/Duplicate/Delete/Preview buttons present.
 *          Delete disabled for defaults (G2).
 * AC-72b-6 [Spec §6K.6]: EmailTemplatePreview renders sandboxed iframe via POST preview.
 * AC-72b-7 [Spec §6K.9]: All 11 test IDs are assigned.
 * AC-72b-8 [Local Canon]: Template hooks follow canonical React Query pattern
 *          with key factory and cache invalidation.
 * AC-72b-9 [Spec §6K.5 G22]: "New Template" provides valid default body (not empty).
 *
 * Test pattern follows scheduling.test.tsx (vi.hoisted mock, QueryClient wrapper).
 * MEU: MEU-72b (gui-email-templates)
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom/vitest'
import React from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { renderHook, act } from '@testing-library/react'

// ─── Mocks ────────────────────────────────────────────────────────────────────

const { mockApiFetch } = vi.hoisted(() => ({
    mockApiFetch: vi.fn(),
}))

vi.mock('@/lib/api', () => ({
    apiFetch: (...args: any[]) => mockApiFetch(...args),
}))

vi.mock('@/hooks/useStatusBar', () => ({
    useStatusBar: () => ({ message: 'Ready', setStatus: vi.fn() }),
    StatusBarProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}))

// ─── Test Data ────────────────────────────────────────────────────────────────

interface EmailTemplate {
    name: string
    description: string
    body_html: string
    body_format: 'html' | 'markdown'
    subject_template: string
    required_variables: string[]
    is_default: boolean
    sample_data_json: string | null
}

const MOCK_DEFAULT_TEMPLATE: EmailTemplate = {
    name: 'daily-report',
    description: 'Default daily report template',
    body_html: '<h1>{{ report_name }}</h1><p>{{ summary }}</p>',
    body_format: 'html',
    subject_template: 'Daily Report - {{ date }}',
    required_variables: ['report_name', 'summary', 'date'],
    is_default: true,
    sample_data_json: '{"report_name": "Test", "summary": "Summary", "date": "2026-04-28"}',
}

const MOCK_CUSTOM_TEMPLATE: EmailTemplate = {
    name: 'my-custom-report',
    description: 'Custom weekly report',
    body_html: '<h1>Weekly {{ ticker }}</h1>',
    body_format: 'html',
    subject_template: 'Weekly Report',
    required_variables: ['ticker'],
    is_default: false,
    sample_data_json: null,
}

const MOCK_TEMPLATES_LIST = [MOCK_DEFAULT_TEMPLATE, MOCK_CUSTOM_TEMPLATE]

// ─── Helpers ──────────────────────────────────────────────────────────────────

function createWrapper() {
    const queryClient = new QueryClient({
        defaultOptions: { queries: { retry: false } },
    })
    return function Wrapper({ children }: { children: React.ReactNode }) {
        return (
            <QueryClientProvider client={queryClient}>
                {children}
            </QueryClientProvider>
        )
    }
}

// ═══════════════════════════════════════════════════════════════════════════════
// AC-72b-8: Template Hook Tests
// ═══════════════════════════════════════════════════════════════════════════════

import {
    useEmailTemplates,
    useCreateTemplate,
    useUpdateTemplate,
    useDeleteTemplate,
    useDuplicateTemplate,
    usePreviewTemplate,
    templateKeys,
} from '../template-hooks'

describe('templateKeys', () => {
    it('AC-72b-8: key factory produces consistent keys', () => {
        expect(templateKeys.all).toEqual(['email-templates'])
        expect(templateKeys.detail('daily-report')).toEqual(['email-templates', 'daily-report'])
        expect(templateKeys.preview('daily-report')).toEqual(['email-template-preview', 'daily-report'])
    })
})

describe('useEmailTemplates', () => {
    beforeEach(() => {
        mockApiFetch.mockReset()
    })

    it('AC-72b-2: fetches typed template list with refetchInterval', async () => {
        mockApiFetch.mockResolvedValueOnce(MOCK_TEMPLATES_LIST)

        const { result } = renderHook(() => useEmailTemplates(), {
            wrapper: createWrapper(),
        })

        expect(result.current.isLoading).toBe(true)

        await waitFor(() => {
            expect(result.current.isLoading).toBe(false)
        })

        expect(result.current.templates).toHaveLength(2)
        expect(result.current.templates[0].name).toBe('daily-report')
        expect(result.current.templates[0].is_default).toBe(true)
        expect(result.current.templates[1].name).toBe('my-custom-report')
        expect(result.current.error).toBeNull()
    })
})

describe('useCreateTemplate', () => {
    beforeEach(() => {
        mockApiFetch.mockReset()
    })

    it('AC-72b-8: invalidates cache on create', async () => {
        mockApiFetch.mockResolvedValueOnce(MOCK_CUSTOM_TEMPLATE)

        const queryClient = new QueryClient({
            defaultOptions: { queries: { retry: false } },
        })
        const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries')

        const wrapper = ({ children }: { children: React.ReactNode }) => (
            <QueryClientProvider client={queryClient}>
                {children}
            </QueryClientProvider>
        )

        const { result } = renderHook(() => useCreateTemplate(), { wrapper })

        await act(async () => {
            result.current.mutate({
                name: 'my-custom-report',
                body_html: '<h1>Custom</h1>',
            })
        })

        await waitFor(() => {
            expect(result.current.isSuccess).toBe(true)
        })

        expect(invalidateSpy).toHaveBeenCalledWith(
            expect.objectContaining({ queryKey: templateKeys.all }),
        )
    })
})

describe('useUpdateTemplate', () => {
    beforeEach(() => {
        mockApiFetch.mockReset()
    })

    it('AC-72b-8: invalidates list + detail on update', async () => {
        mockApiFetch.mockResolvedValueOnce(MOCK_CUSTOM_TEMPLATE)

        const queryClient = new QueryClient({
            defaultOptions: { queries: { retry: false } },
        })
        const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries')

        const wrapper = ({ children }: { children: React.ReactNode }) => (
            <QueryClientProvider client={queryClient}>
                {children}
            </QueryClientProvider>
        )

        const { result } = renderHook(() => useUpdateTemplate(), { wrapper })

        await act(async () => {
            result.current.mutate({
                name: 'my-custom-report',
                payload: { body_html: '<h1>Updated</h1>' },
            })
        })

        await waitFor(() => {
            expect(result.current.isSuccess).toBe(true)
        })

        expect(invalidateSpy).toHaveBeenCalledWith(
            expect.objectContaining({ queryKey: templateKeys.all }),
        )
        expect(invalidateSpy).toHaveBeenCalledWith(
            expect.objectContaining({ queryKey: templateKeys.detail('my-custom-report') }),
        )
    })
})

describe('useDeleteTemplate', () => {
    beforeEach(() => {
        mockApiFetch.mockReset()
    })

    it('AC-72b-8: invalidates cache on delete', async () => {
        mockApiFetch.mockResolvedValueOnce(undefined)

        const queryClient = new QueryClient({
            defaultOptions: { queries: { retry: false } },
        })
        const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries')

        const wrapper = ({ children }: { children: React.ReactNode }) => (
            <QueryClientProvider client={queryClient}>
                {children}
            </QueryClientProvider>
        )

        const { result } = renderHook(() => useDeleteTemplate(), { wrapper })

        await act(async () => {
            result.current.mutate('my-custom-report')
        })

        await waitFor(() => {
            expect(result.current.isSuccess).toBe(true)
        })

        expect(invalidateSpy).toHaveBeenCalledWith(
            expect.objectContaining({ queryKey: templateKeys.all }),
        )
    })
})

// ═══════════════════════════════════════════════════════════════════════════════
// AC-72b-1: SchedulingLayout Tab Bar Tests
// ═══════════════════════════════════════════════════════════════════════════════

import { SCHEDULING_TEST_IDS } from '../test-ids'

describe('SchedulingLayout Tabs', () => {
    beforeEach(() => {
        mockApiFetch.mockReset()
        // Mock all possible API calls
        mockApiFetch.mockImplementation((url: string) => {
            if (url.includes('/templates')) {
                return Promise.resolve(MOCK_TEMPLATES_LIST)
            }
            if (url.includes('/policies')) {
                return Promise.resolve({ policies: [], total: 0 })
            }
            if (url.includes('/scheduler/status')) {
                return Promise.resolve({ running: true, job_count: 0, jobs: [] })
            }
            return Promise.resolve({})
        })
    })

    it('AC-72b-1: renders tab bar with both tabs', async () => {
        const { default: SchedulingLayout } = await import('../SchedulingLayout')

        render(<SchedulingLayout />, { wrapper: createWrapper() })

        expect(screen.getByTestId(SCHEDULING_TEST_IDS.TAB_REPORT_POLICIES)).toBeInTheDocument()
        expect(screen.getByTestId(SCHEDULING_TEST_IDS.TAB_EMAIL_TEMPLATES)).toBeInTheDocument()
    })

    it('AC-72b-1: "Report Policies" is the default active tab', async () => {
        const { default: SchedulingLayout } = await import('../SchedulingLayout')

        render(<SchedulingLayout />, { wrapper: createWrapper() })

        const policiesTab = screen.getByTestId(SCHEDULING_TEST_IDS.TAB_REPORT_POLICIES)
        expect(policiesTab.className).toContain('text-accent')
    })

    it('AC-72b-1: clicking "Email Templates" tab shows template content', async () => {
        const { default: SchedulingLayout } = await import('../SchedulingLayout')

        render(<SchedulingLayout />, { wrapper: createWrapper() })

        const templatesTab = screen.getByTestId(SCHEDULING_TEST_IDS.TAB_EMAIL_TEMPLATES)
        fireEvent.click(templatesTab)

        await waitFor(() => {
            expect(screen.getByTestId(SCHEDULING_TEST_IDS.TEMPLATE_LIST)).toBeInTheDocument()
        })
    })
})

// ═══════════════════════════════════════════════════════════════════════════════
// AC-72b-2: EmailTemplateList Tests
// ═══════════════════════════════════════════════════════════════════════════════

import EmailTemplateList from '../EmailTemplateList'

describe('EmailTemplateList', () => {
    const defaultProps = {
        templates: MOCK_TEMPLATES_LIST,
        selectedTemplateName: null as string | null,
        onSelect: vi.fn(),
        onCreate: vi.fn(),
        isLoading: false,
        error: null as string | null,
    }

    it('AC-72b-2: renders template list with data-testid', () => {
        render(<EmailTemplateList {...defaultProps} />, { wrapper: createWrapper() })

        expect(screen.getByTestId(SCHEDULING_TEST_IDS.TEMPLATE_LIST)).toBeInTheDocument()
    })

    it('AC-72b-2: renders template names', () => {
        render(<EmailTemplateList {...defaultProps} />, { wrapper: createWrapper() })

        expect(screen.getByText('daily-report')).toBeInTheDocument()
        expect(screen.getByText('my-custom-report')).toBeInTheDocument()
    })

    it('AC-72b-2: shows is_default badge for default templates', () => {
        render(<EmailTemplateList {...defaultProps} />, { wrapper: createWrapper() })

        expect(screen.getByTestId(SCHEDULING_TEST_IDS.TEMPLATE_DEFAULT_BADGE)).toBeInTheDocument()
    })

    it('AC-72b-2: calls onSelect when template clicked', () => {
        const onSelect = vi.fn()
        render(
            <EmailTemplateList {...defaultProps} onSelect={onSelect} />,
            { wrapper: createWrapper() },
        )

        fireEvent.click(screen.getByText('my-custom-report'))
        expect(onSelect).toHaveBeenCalledWith(MOCK_CUSTOM_TEMPLATE)
    })

    it('AC-72b-9: New Template button present with test-id', () => {
        render(<EmailTemplateList {...defaultProps} />, { wrapper: createWrapper() })

        expect(screen.getByTestId(SCHEDULING_TEST_IDS.TEMPLATE_NEW_BTN)).toBeInTheDocument()
    })

    it('AC-72b-9: clicking New Template calls onCreate', () => {
        const onCreate = vi.fn()
        render(
            <EmailTemplateList {...defaultProps} onCreate={onCreate} />,
            { wrapper: createWrapper() },
        )

        fireEvent.click(screen.getByTestId(SCHEDULING_TEST_IDS.TEMPLATE_NEW_BTN))
        expect(onCreate).toHaveBeenCalled()
    })
})

// ═══════════════════════════════════════════════════════════════════════════════
// AC-72b-3, AC-72b-4, AC-72b-5: EmailTemplateDetail Tests
// ═══════════════════════════════════════════════════════════════════════════════

import EmailTemplateDetail from '../EmailTemplateDetail'

describe('EmailTemplateDetail', () => {
    const defaultHandlers = {
        onSave: vi.fn(),
        onDuplicate: vi.fn(),
        onDelete: vi.fn(),
        onPreview: vi.fn(),
        onRename: vi.fn(),
        isSaving: false,
    }

    beforeEach(() => {
        vi.clearAllMocks()
    })

    it('AC-72b-3: renders detail pane with data-testid', () => {
        render(
            <EmailTemplateDetail template={MOCK_CUSTOM_TEMPLATE} {...defaultHandlers} />,
            { wrapper: createWrapper() },
        )

        expect(screen.getByTestId(SCHEDULING_TEST_IDS.TEMPLATE_DETAIL)).toBeInTheDocument()
    })

    it('AC-72b-3: shows template name', () => {
        render(
            <EmailTemplateDetail template={MOCK_CUSTOM_TEMPLATE} {...defaultHandlers} />,
            { wrapper: createWrapper() },
        )

        expect(screen.getByText('my-custom-report')).toBeInTheDocument()
    })

    it('AC-72b-3: shows description field', () => {
        render(
            <EmailTemplateDetail template={MOCK_CUSTOM_TEMPLATE} {...defaultHandlers} />,
            { wrapper: createWrapper() },
        )

        expect(screen.getByDisplayValue('Custom weekly report')).toBeInTheDocument()
    })

    it('AC-72b-3: shows subject template field', () => {
        render(
            <EmailTemplateDetail template={MOCK_CUSTOM_TEMPLATE} {...defaultHandlers} />,
            { wrapper: createWrapper() },
        )

        expect(screen.getByDisplayValue('Weekly Report')).toBeInTheDocument()
    })

    it('AC-72b-4: default template shows read-only banner', () => {
        render(
            <EmailTemplateDetail template={MOCK_DEFAULT_TEMPLATE} {...defaultHandlers} />,
            { wrapper: createWrapper() },
        )

        expect(screen.getByText(/Default templates cannot be modified/)).toBeInTheDocument()
    })

    it('AC-72b-4: default template name has no pencil-edit icon', () => {
        render(
            <EmailTemplateDetail template={MOCK_DEFAULT_TEMPLATE} {...defaultHandlers} />,
            { wrapper: createWrapper() },
        )

        // Default template name is shown but no pencil icon for renaming
        expect(screen.getByText('daily-report')).toBeInTheDocument()
        expect(screen.queryByText('✏️')).not.toBeInTheDocument()
    })

    it('AC-72b-5: Save button present with test-id', () => {
        render(
            <EmailTemplateDetail template={MOCK_CUSTOM_TEMPLATE} {...defaultHandlers} />,
            { wrapper: createWrapper() },
        )

        expect(screen.getByTestId(SCHEDULING_TEST_IDS.TEMPLATE_SAVE_BTN)).toBeInTheDocument()
    })

    it('AC-72b-5: Duplicate button present with test-id', () => {
        render(
            <EmailTemplateDetail template={MOCK_CUSTOM_TEMPLATE} {...defaultHandlers} />,
            { wrapper: createWrapper() },
        )

        expect(screen.getByTestId(SCHEDULING_TEST_IDS.TEMPLATE_DUPLICATE_BTN)).toBeInTheDocument()
    })

    it('AC-72b-5: Delete button present with test-id', () => {
        render(
            <EmailTemplateDetail template={MOCK_CUSTOM_TEMPLATE} {...defaultHandlers} />,
            { wrapper: createWrapper() },
        )

        expect(screen.getByTestId(SCHEDULING_TEST_IDS.TEMPLATE_DELETE_BTN)).toBeInTheDocument()
    })

    it('AC-72b-5: Delete button disabled for default templates (G2)', () => {
        render(
            <EmailTemplateDetail template={MOCK_DEFAULT_TEMPLATE} {...defaultHandlers} />,
            { wrapper: createWrapper() },
        )

        expect(screen.getByTestId(SCHEDULING_TEST_IDS.TEMPLATE_DELETE_BTN)).toBeDisabled()
    })

    it('AC-72b-5: Duplicate button enabled for default templates', () => {
        render(
            <EmailTemplateDetail template={MOCK_DEFAULT_TEMPLATE} {...defaultHandlers} />,
            { wrapper: createWrapper() },
        )

        expect(screen.getByTestId(SCHEDULING_TEST_IDS.TEMPLATE_DUPLICATE_BTN)).not.toBeDisabled()
    })

    it('AC-72b-5: Save button disabled for default templates', () => {
        render(
            <EmailTemplateDetail template={MOCK_DEFAULT_TEMPLATE} {...defaultHandlers} />,
            { wrapper: createWrapper() },
        )

        expect(screen.getByTestId(SCHEDULING_TEST_IDS.TEMPLATE_SAVE_BTN)).toBeDisabled()
    })

    it('AC-72b-5: clicking Save calls onSave with updated template data', () => {
        const onSave = vi.fn()
        render(
            <EmailTemplateDetail template={MOCK_CUSTOM_TEMPLATE} {...defaultHandlers} onSave={onSave} />,
            { wrapper: createWrapper() },
        )

        // Make the form dirty first (Save is disabled when pristine)
        const descInput = screen.getByDisplayValue('Custom weekly report')
        fireEvent.change(descInput, { target: { value: 'Updated description' } })

        fireEvent.click(screen.getByTestId(SCHEDULING_TEST_IDS.TEMPLATE_SAVE_BTN))
        expect(onSave).toHaveBeenCalled()
    })

    it('AC-72b-5: clicking Duplicate calls onDuplicate', () => {
        const onDuplicate = vi.fn()
        render(
            <EmailTemplateDetail template={MOCK_CUSTOM_TEMPLATE} {...defaultHandlers} onDuplicate={onDuplicate} />,
            { wrapper: createWrapper() },
        )

        fireEvent.click(screen.getByTestId(SCHEDULING_TEST_IDS.TEMPLATE_DUPLICATE_BTN))
        expect(onDuplicate).toHaveBeenCalled()
    })

    it('AC-72b-5: Preview button present with test-id', () => {
        render(
            <EmailTemplateDetail template={MOCK_CUSTOM_TEMPLATE} {...defaultHandlers} />,
            { wrapper: createWrapper() },
        )

        expect(screen.getByTestId(SCHEDULING_TEST_IDS.TEMPLATE_PREVIEW_BTN)).toBeInTheDocument()
    })

    it('F5: template name displayed as inline header with pencil-edit for custom templates', () => {
        render(
            <EmailTemplateDetail template={MOCK_CUSTOM_TEMPLATE} {...defaultHandlers} />,
            { wrapper: createWrapper() },
        )

        // Name is shown as a heading, not an input
        expect(screen.getByText('my-custom-report')).toBeInTheDocument()
        // Pencil icon is present for custom templates
        expect(screen.getByText('✏️')).toBeInTheDocument()
    })

    it('F1: clicking Delete opens confirmation modal', () => {
        render(
            <EmailTemplateDetail template={MOCK_CUSTOM_TEMPLATE} {...defaultHandlers} />,
            { wrapper: createWrapper() },
        )

        fireEvent.click(screen.getByTestId(SCHEDULING_TEST_IDS.TEMPLATE_DELETE_BTN))

        expect(screen.getByTestId('confirm-delete-modal')).toBeInTheDocument()
        expect(screen.getByText(/Are you sure you want to delete/)).toBeInTheDocument()
    })

    it('F1: clicking Cancel in delete modal closes it without calling onDelete', () => {
        const onDelete = vi.fn()
        render(
            <EmailTemplateDetail template={MOCK_CUSTOM_TEMPLATE} {...defaultHandlers} onDelete={onDelete} />,
            { wrapper: createWrapper() },
        )

        fireEvent.click(screen.getByTestId(SCHEDULING_TEST_IDS.TEMPLATE_DELETE_BTN))
        expect(screen.getByTestId('confirm-delete-modal')).toBeInTheDocument()

        fireEvent.click(screen.getByTestId('confirm-delete-cancel-btn'))
        expect(screen.queryByTestId('confirm-delete-modal')).not.toBeInTheDocument()
        expect(onDelete).not.toHaveBeenCalled()
    })

    it('F1: clicking Confirm in delete modal calls onDelete', () => {
        const onDelete = vi.fn()
        render(
            <EmailTemplateDetail template={MOCK_CUSTOM_TEMPLATE} {...defaultHandlers} onDelete={onDelete} />,
            { wrapper: createWrapper() },
        )

        fireEvent.click(screen.getByTestId(SCHEDULING_TEST_IDS.TEMPLATE_DELETE_BTN))
        // Use the standardized data-testid from ConfirmDeleteModal
        const confirmBtn = screen.getByTestId('confirm-delete-confirm-btn')
        fireEvent.click(confirmBtn)

        expect(onDelete).toHaveBeenCalled()
    })

    it('F1: delete error message is displayed when deleteError is set', () => {
        render(
            <EmailTemplateDetail
                template={MOCK_CUSTOM_TEMPLATE}
                {...defaultHandlers}
                deleteError="Forbidden: default templates cannot be deleted"
            />,
            { wrapper: createWrapper() },
        )

        expect(screen.getByText(/Forbidden: default templates cannot be deleted/)).toBeInTheDocument()
    })

    // F3: Rename-while-dirty passes current form payload, not stale selectedTemplate
    it('F3: rename while dirty passes current form state to onRename', () => {
        const onRename = vi.fn()
        render(
            <EmailTemplateDetail template={MOCK_CUSTOM_TEMPLATE} {...defaultHandlers} onRename={onRename} />,
            { wrapper: createWrapper() },
        )

        // Modify the body to create dirty state
        const bodyTextarea = screen.getByDisplayValue(MOCK_CUSTOM_TEMPLATE.body_html)
        fireEvent.change(bodyTextarea, { target: { value: '<h1>Updated body</h1>' } })

        // Click pencil to enter rename mode
        fireEvent.click(screen.getByText('✏️'))

        // Change the name
        const nameInput = screen.getByDisplayValue(MOCK_CUSTOM_TEMPLATE.name)
        fireEvent.change(nameInput, { target: { value: 'renamed-template' } })
        fireEvent.blur(nameInput)

        // onRename should be called with the new name AND the current form payload
        expect(onRename).toHaveBeenCalledWith(
            'renamed-template',
            expect.objectContaining({
                body_html: '<h1>Updated body</h1>',
            }),
        )
    })

    // F4: Variable autocomplete — detects {{ variable }} from template body
    it('F4: variable suggestions include detected template variables', () => {
        const templateWithVars: EmailTemplate = {
            ...MOCK_CUSTOM_TEMPLATE,
            body_html: '<h1>{{ report_name }}</h1><p>{{ custom_field }}</p>',
            required_variables: [],
        }
        render(
            <EmailTemplateDetail template={templateWithVars} {...defaultHandlers} />,
            { wrapper: createWrapper() },
        )

        // Focus the variable input to trigger dropdown
        const varInput = screen.getByPlaceholderText(/Add variable/i)
        fireEvent.focus(varInput)
        fireEvent.change(varInput, { target: { value: 'cust' } })

        // 'custom_field' should appear as a detected suggestion
        expect(screen.getByText('custom_field')).toBeInTheDocument()
    })

    // F4: Variable autocomplete — duplicate suppression (already-added vars not in list)
    it('F4: already-added variables are excluded from suggestions', () => {
        const templateWithAddedVars: EmailTemplate = {
            ...MOCK_CUSTOM_TEMPLATE,
            body_html: '<h1>{{ report_name }}</h1>',
            required_variables: ['report_name'],
        }
        render(
            <EmailTemplateDetail template={templateWithAddedVars} {...defaultHandlers} />,
            { wrapper: createWrapper() },
        )

        const varInput = screen.getByPlaceholderText(/Add variable/i)
        fireEvent.focus(varInput)
        fireEvent.change(varInput, { target: { value: 'report' } })

        // 'report_name' should NOT appear — already in required_variables
        const suggestions = screen.queryAllByText('report_name')
        // It may appear as a tag/chip, but not in the dropdown suggestions
        const dropdownSuggestions = suggestions.filter(el => el.closest('[role="option"]') || el.closest('[data-suggestion]'))
        expect(dropdownSuggestions).toHaveLength(0)
    })

    // F4: Variable autocomplete — dotted reference detection
    it('F4: detects dotted Jinja references like {{ quote.symbol }}', () => {
        const templateWithDotted: EmailTemplate = {
            ...MOCK_CUSTOM_TEMPLATE,
            body_html: '<p>{{ quote.symbol }} at {{ quote.price }}</p>',
            required_variables: [],
        }
        render(
            <EmailTemplateDetail template={templateWithDotted} {...defaultHandlers} />,
            { wrapper: createWrapper() },
        )

        const varInput = screen.getByPlaceholderText(/Add variable/i)
        fireEvent.focus(varInput)
        fireEvent.change(varInput, { target: { value: 'quote' } })

        // Should detect 'quote.symbol' and/or 'quote.price' as suggestions
        expect(screen.getByText('quote.symbol')).toBeInTheDocument()
    })
})

// ═══════════════════════════════════════════════════════════════════════════════
// AC-72b-6: EmailTemplatePreview Tests
// ═══════════════════════════════════════════════════════════════════════════════

import EmailTemplatePreview from '../EmailTemplatePreview'

describe('EmailTemplatePreview', () => {
    it('AC-72b-6: renders sandboxed iframe with data-testid', () => {
        render(
            <EmailTemplatePreview
                renderedHtml="<h1>Preview Content</h1>"
                isLoading={false}
            />,
            { wrapper: createWrapper() },
        )

        const iframe = screen.getByTestId(SCHEDULING_TEST_IDS.TEMPLATE_PREVIEW_IFRAME)
        expect(iframe).toBeInTheDocument()
        expect(iframe.tagName).toBe('IFRAME')
        expect(iframe).toHaveAttribute('sandbox')
    })

    it('AC-72b-6: shows loading state when preview is loading', () => {
        render(
            <EmailTemplatePreview
                renderedHtml={null}
                isLoading={true}
            />,
            { wrapper: createWrapper() },
        )

        expect(screen.getByText(/Loading preview/i)).toBeInTheDocument()
    })

    it('AC-72b-6: shows empty state when no content', () => {
        render(
            <EmailTemplatePreview
                renderedHtml={null}
                isLoading={false}
            />,
            { wrapper: createWrapper() },
        )

        expect(screen.getByText(/Click/i)).toBeInTheDocument()
        expect(screen.getByText(/Preview/i)).toBeInTheDocument()
    })
})

// ═══════════════════════════════════════════════════════════════════════════════
// AC-72b-7: Test ID Presence
// ═══════════════════════════════════════════════════════════════════════════════

describe('Test IDs', () => {
    it('AC-72b-7: all 11 template test IDs are defined', () => {
        const requiredIds = [
            'TAB_REPORT_POLICIES',
            'TAB_EMAIL_TEMPLATES',
            'TEMPLATE_LIST',
            'TEMPLATE_DETAIL',
            'TEMPLATE_PREVIEW_BTN',
            'TEMPLATE_PREVIEW_IFRAME',
            'TEMPLATE_NEW_BTN',
            'TEMPLATE_SAVE_BTN',
            'TEMPLATE_DUPLICATE_BTN',
            'TEMPLATE_DELETE_BTN',
            'TEMPLATE_DEFAULT_BADGE',
        ]

        for (const id of requiredIds) {
            expect(SCHEDULING_TEST_IDS).toHaveProperty(id)
            expect((SCHEDULING_TEST_IDS as any)[id]).toBeTruthy()
        }
    })
})
