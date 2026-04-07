import { useRef, useCallback, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiFetch } from '@/lib/api'

/**
 * Image metadata from the REST API.
 *
 * Source: 04a-api-trades.md §Image Routes
 */
interface ImageMeta {
    id: number
    caption: string
    mime_type: string
    file_size: number | null
    width: number | null
    height: number | null
    created_at: string | null
}

interface ScreenshotPanelProps {
    tradeId: string
}

/**
 * ScreenshotPanel — API-wired thumbnail strip with upload, delete,
 * lightbox, drag-and-drop, and Ctrl+V paste.
 *
 * Source: 06b-gui-trades.md §ScreenshotPanel
 *
 * Features (AC-4 through AC-13):
 * - useQuery fetches images via GET /trades/{exec_id}/images
 * - useMutation uploads via POST /trades/{exec_id}/images (FormData)
 * - useMutation deletes via DELETE /images/{id}
 * - Content-Type override for multipart/form-data upload
 * - Cache invalidation after upload/delete
 * - Lightbox viewer on thumbnail click
 * - Drag-and-drop via onDrop handler
 * - Clipboard paste via ClipboardEvent.clipboardData (web-standard)
 * - Loading and error states
 */
export default function ScreenshotPanel({ tradeId }: ScreenshotPanelProps) {
    const queryClient = useQueryClient()
    const fileInputRef = useRef<HTMLInputElement>(null)
    const [lightboxImageId, setLightboxImageId] = useState<number | null>(null)
    const [isDragOver, setIsDragOver] = useState(false)

    // ── AC-4: Fetch trade images ─────────────────────────────────────────

    const {
        data: images = [],
        isLoading,
        isError,
    } = useQuery<ImageMeta[]>({
        queryKey: ['trade-images', tradeId],
        queryFn: () => apiFetch(`/api/v1/trades/${tradeId}/images`),
        enabled: !!tradeId,
    })

    // ── AC-6: Upload mutation ────────────────────────────────────────────

    const uploadMutation = useMutation({
        mutationFn: (file: File) => {
            const formData = new FormData()
            formData.append('file', file)
            return apiFetch(`/api/v1/trades/${tradeId}/images`, {
                method: 'POST',
                body: formData,
            })
        },
        onSuccess: () => {
            // AC-7: Invalidate query cache to refetch
            queryClient.invalidateQueries({ queryKey: ['trade-images', tradeId] })
        },
    })

    // ── AC-8: Delete mutation ────────────────────────────────────────────

    const deleteMutation = useMutation({
        mutationFn: (imageId: number) =>
            apiFetch(`/api/v1/images/${imageId}`, { method: 'DELETE' }),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['trade-images', tradeId] })
        },
    })

    // ── Upload handler (shared by file input, paste, and drop) ───────────

    const handleUpload = useCallback(
        (file: File) => {
            if (!file.type.startsWith('image/')) return
            uploadMutation.mutate(file)
        },
        [uploadMutation],
    )

    // ── File input change ────────────────────────────────────────────────

    const handleFileChange = useCallback(
        (e: React.ChangeEvent<HTMLInputElement>) => {
            const file = e.target.files?.[0]
            if (file) handleUpload(file)
            // Reset input so same file can be re-selected
            if (e.target) e.target.value = ''
        },
        [handleUpload],
    )

    // ── AC-12: Clipboard paste ───────────────────────────────────────────

    const handlePaste = useCallback(
        (e: React.ClipboardEvent) => {
            const items = e.clipboardData?.items
            if (!items) return
            for (const item of Array.from(items)) {
                if (item.type.startsWith('image/')) {
                    const file = item.getAsFile()
                    if (file) handleUpload(file)
                }
            }
        },
        [handleUpload],
    )

    // ── AC-13: Drag and drop ─────────────────────────────────────────────

    const handleDragOver = useCallback((e: React.DragEvent) => {
        e.preventDefault()
        setIsDragOver(true)
    }, [])

    const handleDragLeave = useCallback(() => {
        setIsDragOver(false)
    }, [])

    const handleDrop = useCallback(
        (e: React.DragEvent) => {
            e.preventDefault()
            setIsDragOver(false)
            const files = e.dataTransfer?.files
            if (!files) return
            for (const file of Array.from(files)) {
                if (file.type.startsWith('image/')) {
                    handleUpload(file)
                }
            }
        },
        [handleUpload],
    )

    // ── AC-10: Loading state ─────────────────────────────────────────────

    if (isLoading) {
        return (
            <div data-testid="screenshot-panel" className="space-y-3">
                <h4 className="text-sm font-medium text-fg">Screenshots</h4>
                <div data-testid="screenshot-loading" className="flex items-center gap-2 text-fg-muted text-sm">
                    <span className="animate-spin">⏳</span>
                    Loading screenshots…
                </div>
            </div>
        )
    }

    // ── AC-11: Error state ───────────────────────────────────────────────

    if (isError) {
        return (
            <div data-testid="screenshot-panel" className="space-y-3">
                <h4 className="text-sm font-medium text-fg">Screenshots</h4>
                <div data-testid="screenshot-error" className="text-red-400 text-sm">
                    Failed to load screenshots.
                </div>
            </div>
        )
    }

    // ── Build thumbnail URL ──────────────────────────────────────────────

    const getApiBase = () =>
        typeof window !== 'undefined' && window.api ? window.api.baseUrl : 'http://127.0.0.1:17787'

    const thumbnailUrl = (imageId: number) =>
        `${getApiBase()}/api/v1/images/${imageId}/thumbnail`

    const fullUrl = (imageId: number) =>
        `${getApiBase()}/api/v1/images/${imageId}/full`

    // ── Render ───────────────────────────────────────────────────────────

    return (
        <div
            data-testid="screenshot-panel"
            tabIndex={0}
            role="region"
            aria-label="Screenshot panel — paste, drag, or click to upload images"
            onPaste={handlePaste}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className={`space-y-3 outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:rounded-lg ${isDragOver ? 'ring-2 ring-accent rounded-lg' : ''}`}
        >
            <h4 className="text-sm font-medium text-fg">Screenshots</h4>

            {/* Thumbnail Grid */}
            <div className="flex flex-wrap gap-2">
                {images.map((img) => (
                    <div key={img.id} className="relative group">
                        <button
                            data-testid="screenshot-thumbnail"
                            onClick={() => setLightboxImageId(img.id)}
                            className="w-20 h-20 rounded-md overflow-hidden border border-bg-subtle hover:border-accent transition-colors"
                        >
                            <img
                                src={thumbnailUrl(img.id)}
                                alt={img.caption || `Screenshot ${img.id}`}
                                className="w-full h-full object-cover"
                            />
                        </button>
                        {/* AC-8: Delete button */}
                        <button
                            data-testid="screenshot-delete-btn"
                            onClick={() => deleteMutation.mutate(img.id)}
                            className="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-red-600 text-white text-xs flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
                            title="Delete screenshot"
                        >
                            ×
                        </button>
                    </div>
                ))}

                {/* Upload Button */}
                <button
                    onClick={() => fileInputRef.current?.click()}
                    data-testid="screenshot-upload-btn"
                    disabled={uploadMutation.isPending}
                    className="w-20 h-20 rounded-md border border-dashed border-bg-subtle hover:border-accent text-fg-muted hover:text-fg flex items-center justify-center text-2xl transition-colors disabled:opacity-50"
                >
                    {uploadMutation.isPending ? '⏳' : '+'}
                </button>
            </div>

            {/* Hidden file input */}
            <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                onChange={handleFileChange}
                className="hidden"
                data-testid="screenshot-file-input"
            />

            <p className="text-xs text-fg-muted">
                Drag files, click +, or press Ctrl+V to paste from clipboard
            </p>

            {/* AC-9: Lightbox */}
            {lightboxImageId !== null && (
                <div
                    data-testid="screenshot-lightbox"
                    className="fixed inset-0 bg-black/80 flex items-center justify-center z-50"
                    onClick={() => setLightboxImageId(null)}
                >
                    <img
                        src={fullUrl(lightboxImageId)}
                        alt="Screenshot preview"
                        className="max-w-[90vw] max-h-[90vh] rounded-lg"
                    />
                </div>
            )}
        </div>
    )
}
