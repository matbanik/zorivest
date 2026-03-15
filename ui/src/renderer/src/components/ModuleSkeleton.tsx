/**
 * ModuleSkeleton — placeholder for lazy-loaded feature modules.
 * Displayed while route content is loading.
 */
export default function ModuleSkeleton() {
    return (
        <div
            role="status"
            aria-label="Loading module"
            className="flex items-center justify-center h-full"
        >
            <div className="animate-pulse text-fg-muted text-sm">Loading…</div>
        </div>
    )
}
