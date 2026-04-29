/**
 * Email Template API types and client functions.
 *
 * Types mirror Python Pydantic response models from scheduling.py template endpoints.
 * API functions use the canonical apiFetch wrapper from @/lib/api.
 *
 * Source: 06k-gui-email-templates.md §6K.7
 * MEU: MEU-72b (gui-email-templates)
 */

import { apiFetch } from '@/lib/api'

// ── Response Types ─────────────────────────────────────────────────────

/** Matches Python TemplateResponse. */
export interface EmailTemplate {
    name: string
    description: string
    body_html: string
    body_format: 'html' | 'markdown'
    subject_template: string
    required_variables: string[]
    is_default: boolean
    sample_data_json: string | null
}

/** Preview render response. */
export interface TemplatePreviewResponse {
    name: string
    subject_rendered: string
    body_rendered: string
}

// ── Request Types ──────────────────────────────────────────────────────

export interface CreateTemplatePayload {
    name: string
    body_html: string
    description?: string
    body_format?: 'html' | 'markdown'
    subject_template?: string
    required_variables?: string[]
    sample_data_json?: string
}

export interface UpdateTemplatePayload {
    body_html?: string
    description?: string
    body_format?: 'html' | 'markdown'
    subject_template?: string
    required_variables?: string[]
    sample_data_json?: string
}

export interface PreviewTemplatePayload {
    data?: Record<string, unknown>
}

// ── API Client Functions ───────────────────────────────────────────────

const BASE = '/api/v1/scheduling/templates'

export function fetchTemplates(): Promise<EmailTemplate[]> {
    return apiFetch<EmailTemplate[]>(BASE)
}

export function fetchTemplate(name: string): Promise<EmailTemplate> {
    return apiFetch<EmailTemplate>(`${BASE}/${encodeURIComponent(name)}`)
}

export function createTemplate(payload: CreateTemplatePayload): Promise<EmailTemplate> {
    return apiFetch<EmailTemplate>(BASE, {
        method: 'POST',
        body: JSON.stringify(payload),
    })
}

export function updateTemplate(name: string, payload: UpdateTemplatePayload): Promise<EmailTemplate> {
    return apiFetch<EmailTemplate>(`${BASE}/${encodeURIComponent(name)}`, {
        method: 'PATCH',
        body: JSON.stringify(payload),
    })
}

export function deleteTemplate(name: string): Promise<void> {
    return apiFetch<void>(`${BASE}/${encodeURIComponent(name)}`, {
        method: 'DELETE',
    })
}

export function previewTemplate(
    name: string,
    payload?: PreviewTemplatePayload,
): Promise<TemplatePreviewResponse> {
    return apiFetch<TemplatePreviewResponse>(`${BASE}/${encodeURIComponent(name)}/preview`, {
        method: 'POST',
        body: JSON.stringify(payload ?? {}),
    })
}
