import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiFetch } from '@/lib/api'

/**
 * usePersistedState — reads/writes UI settings via REST API.
 *
 * Uses TanStack Query for server state management:
 * - Reads from GET /api/settings/{key}
 * - Writes via PUT /api/settings/{key}
 * - Optimistic updates with rollback on error
 */
export function usePersistedState<T>(key: string, defaultValue: T) {
    const queryClient = useQueryClient()
    const queryKey = ['settings', key]

    const { data, isLoading } = useQuery({
        queryKey,
        queryFn: async () => {
            try {
                const result = await apiFetch<{ value: T }>(`/api/v1/settings/${key}`)
                return result.value
            } catch {
                return defaultValue
            }
        },
        initialData: defaultValue,
    })

    const mutation = useMutation({
        mutationFn: async (value: T) => {
            await apiFetch(`/api/v1/settings/${key}`, {
                method: 'PUT',
                body: JSON.stringify({ value }),
            })
        },
        onMutate: async (newValue: T) => {
            await queryClient.cancelQueries({ queryKey })
            const previous = queryClient.getQueryData(queryKey)
            queryClient.setQueryData(queryKey, newValue)
            return { previous }
        },
        onError: (_err, _newValue, context) => {
            queryClient.setQueryData(queryKey, context?.previous)
        },
        onSettled: () => {
            queryClient.invalidateQueries({ queryKey })
        },
    })

    const setValue = (value: T) => mutation.mutate(value)

    return [data ?? defaultValue, setValue, isLoading] as const
}
