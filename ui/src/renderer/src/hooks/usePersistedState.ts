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

    const { data, isFetching } = useQuery({
        queryKey,
        queryFn: async () => {
            try {
                const result = await apiFetch<{ value: unknown }>(`/api/v1/settings/${key}`)
                const raw = result.value
                // The settings API stores JSON-type values as strings (e.g. "[]", "null").
                // When the caller expects an array or object type, we need to JSON-parse
                // the string back to the expected type.
                if (typeof raw === 'string' && (Array.isArray(defaultValue) || (typeof defaultValue === 'object' && defaultValue !== null))) {
                    try {
                        return JSON.parse(raw) as T
                    } catch {
                        return defaultValue
                    }
                }
                return raw as T
            } catch {
                return defaultValue
            }
        },
        initialData: defaultValue,
    })

    const mutation = useMutation({
        mutationFn: async (value: T) => {
            // The settings API always expects { value: string }.
            // For array/object values (e.g. MRU list), we must JSON-stringify
            // before sending, matching the JSON.parse on the read path.
            const serialized = (typeof value === 'object' && value !== null)
                ? JSON.stringify(value)
                : value
            await apiFetch(`/api/v1/settings/${key}`, {
                method: 'PUT',
                body: JSON.stringify({ value: serialized }),
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

    return [data ?? defaultValue, setValue, isFetching] as const
}
