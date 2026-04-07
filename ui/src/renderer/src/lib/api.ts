/**
 * apiFetch — authenticated fetch wrapper for the Python backend.
 *
 * Includes ephemeral Bearer token from contextBridge and
 * Content-Type: application/json by default.
 */

const getApiBase = () =>
    typeof window !== 'undefined' && window.api ? window.api.baseUrl : 'http://127.0.0.1:17787'

const getToken = () =>
    typeof window !== 'undefined' && window.api ? window.api.token : ''

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
    // When the body is FormData, omit Content-Type so the browser
    // auto-sets "multipart/form-data; boundary=..." with the correct
    // boundary string.  Setting it manually (or to undefined) breaks
    // multipart uploads.
    const isFormData = init?.body instanceof FormData

    const headers: Record<string, string> = {
        Authorization: `Bearer ${getToken()}`,
    }
    if (!isFormData) {
        headers['Content-Type'] = 'application/json'
    }
    // Allow callers to add extra headers (but NOT override Content-Type
    // for FormData — that must stay absent)
    if (init?.headers) {
        const extra = init.headers as Record<string, string>
        for (const [k, v] of Object.entries(extra)) {
            if (isFormData && k.toLowerCase() === 'content-type') continue
            if (v !== undefined) headers[k] = v
        }
    }

    const res = await fetch(`${getApiBase()}${path}`, {
        ...init,
        headers,
    })
    if (!res.ok) throw new Error(`API ${res.status}: ${await res.text()}`)
    if (res.status === 204) return undefined as T
    return res.json()
}
