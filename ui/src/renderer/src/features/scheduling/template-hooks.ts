/**
 * React Query hooks for Email Template management.
 *
 * Follows the canonical hook pattern from hooks.ts:
 * - Query key factory for structured invalidation
 * - Mutations invalidate parent queries on success
 * - Typed return values matching template-api.ts types
 *
 * Source: 06k-gui-email-templates.md §6K.8 (G5: refetchInterval 5_000)
 * MEU: MEU-72b (gui-email-templates)
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import type {
    EmailTemplate,
    CreateTemplatePayload,
    UpdateTemplatePayload,
    TemplatePreviewResponse,
    PreviewTemplatePayload,
} from './template-api'
import {
    fetchTemplates,
    fetchTemplate,
    createTemplate,
    updateTemplate,
    deleteTemplate,
    previewTemplate,
} from './template-api'

// ── Query Keys ─────────────────────────────────────────────────────────

export const templateKeys = {
    all: ['email-templates'] as const,
    detail: (name: string) => ['email-templates', name] as const,
    preview: (name: string) => ['email-template-preview', name] as const,
}

// ── Query Hooks ────────────────────────────────────────────────────────

/** Fetch all email templates. Auto-refreshes every 5s (G5: MCP can create externally). */
export function useEmailTemplates() {
    const { data, isLoading, isFetching, error, refetch } = useQuery<EmailTemplate[]>({
        queryKey: templateKeys.all,
        queryFn: fetchTemplates,
        staleTime: 0,
        refetchInterval: 5_000,
        refetchOnWindowFocus: true,
    })

    return {
        templates: data ?? [],
        isLoading,
        isFetching,
        error: error ? (error instanceof Error ? error.message : 'Failed to fetch templates') : null,
        refetch,
    }
}

/** Fetch a single template by name. */
export function useEmailTemplate(name: string | null) {
    return useQuery<EmailTemplate | null>({
        queryKey: name ? templateKeys.detail(name) : ['email-templates', 'no-name'],
        queryFn: async () => {
            if (!name) return null
            return fetchTemplate(name)
        },
        enabled: !!name,
    })
}

// ── Mutation Hooks ─────────────────────────────────────────────────────

/** Create a new template. Invalidates template list on success. */
export function useCreateTemplate() {
    const queryClient = useQueryClient()

    return useMutation({
        mutationFn: (payload: CreateTemplatePayload) => createTemplate(payload),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: templateKeys.all })
        },
    })
}

/** Update an existing template. Invalidates list + detail on success. */
export function useUpdateTemplate() {
    const queryClient = useQueryClient()

    return useMutation({
        mutationFn: ({ name, payload }: { name: string; payload: UpdateTemplatePayload }) =>
            updateTemplate(name, payload),
        onSuccess: (_data, variables) => {
            queryClient.invalidateQueries({ queryKey: templateKeys.all })
            queryClient.invalidateQueries({ queryKey: templateKeys.detail(variables.name) })
        },
    })
}

/** Delete a template. Invalidates template list on success. */
export function useDeleteTemplate() {
    const queryClient = useQueryClient()

    return useMutation({
        mutationFn: (name: string) => deleteTemplate(name),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: templateKeys.all })
        },
    })
}

/** Duplicate a template (create with modified name). Invalidates list on success. */
export function useDuplicateTemplate() {
    const queryClient = useQueryClient()

    return useMutation({
        mutationFn: (payload: CreateTemplatePayload) => createTemplate(payload),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: templateKeys.all })
        },
    })
}

/** Preview a template's rendered output. */
export function usePreviewTemplate() {
    const queryClient = useQueryClient()

    return useMutation<TemplatePreviewResponse, Error, { name: string; payload?: PreviewTemplatePayload }>({
        mutationFn: ({ name, payload }) => previewTemplate(name, payload),
        onSuccess: (data, variables) => {
            // Cache the preview result for display
            queryClient.setQueryData(templateKeys.preview(variables.name), data)
        },
    })
}
