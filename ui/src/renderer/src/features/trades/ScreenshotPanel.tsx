import { useRef, useCallback, useState } from 'react'

interface Screenshot {
    id: string
    url: string
    caption: string
}

interface ScreenshotPanelProps {
    tradeId: string
    screenshots?: Screenshot[]
    onUpload?: (file: File) => void
}

/**
 * ScreenshotPanel — thumbnail strip with file upload and Ctrl+V paste.
 *
 * Features:
 * - File input for manual upload
 * - Ctrl+V paste from clipboard (Electron)
 * - Thumbnail grid
 * - Lightbox viewer on click
 */
export default function ScreenshotPanel({
    tradeId,
    screenshots = [],
    onUpload,
}: ScreenshotPanelProps) {
    const fileInputRef = useRef<HTMLInputElement>(null)
    const [lightboxUrl, setLightboxUrl] = useState<string | null>(null)

    const handleFileChange = useCallback(
        (e: React.ChangeEvent<HTMLInputElement>) => {
            const file = e.target.files?.[0]
            if (file) onUpload?.(file)
        },
        [onUpload],
    )

    const handlePaste = useCallback(
        (e: React.ClipboardEvent) => {
            const items = e.clipboardData?.items
            if (!items) return
            for (const item of Array.from(items)) {
                if (item.type.startsWith('image/')) {
                    const file = item.getAsFile()
                    if (file) onUpload?.(file)
                }
            }
        },
        [onUpload],
    )

    return (
        <div onPaste={handlePaste} className="space-y-3">
            <h4 className="text-sm font-medium text-fg">Screenshots</h4>

            {/* Thumbnail Grid */}
            <div className="flex flex-wrap gap-2">
                {screenshots.map((ss) => (
                    <button
                        key={ss.id}
                        onClick={() => setLightboxUrl(ss.url)}
                        className="w-20 h-20 rounded-md overflow-hidden border border-bg-subtle hover:border-accent transition-colors"
                    >
                        <img
                            src={ss.url}
                            alt={ss.caption}
                            className="w-full h-full object-cover"
                        />
                    </button>
                ))}

                {/* Upload Button */}
                <button
                    onClick={() => fileInputRef.current?.click()}
                    data-testid="screenshot-upload-btn"
                    className="w-20 h-20 rounded-md border border-dashed border-bg-subtle hover:border-accent text-fg-muted hover:text-fg flex items-center justify-center text-2xl transition-colors"
                >
                    +
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

            {/* Lightbox */}
            {lightboxUrl && (
                <div
                    className="fixed inset-0 bg-black/80 flex items-center justify-center z-50"
                    onClick={() => setLightboxUrl(null)}
                >
                    <img
                        src={lightboxUrl}
                        alt="Screenshot preview"
                        className="max-w-[90vw] max-h-[90vh] rounded-lg"
                    />
                </div>
            )}
        </div>
    )
}
