/**
 * apiFetch — authenticated fetch wrapper for the Python backend.
 *
 * Includes ephemeral Bearer token from contextBridge and
 * Content-Type: application/json by default.
 */

const getApiBase = () =>
    typeof window !== 'undefined' && window.api ? window.api.baseUrl : 'http://127.0.0.1:8000'

const getToken = () =>
    typeof window !== 'undefined' && window.api ? window.api.token : ''

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
    const res = await fetch(`${getApiBase()}${path}`, {
        ...init,
        headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${getToken()}`,
            ...init?.headers,
        },
    })
    if (!res.ok) throw new Error(`API ${res.status}: ${await res.text()}`)
    return res.json()
}
