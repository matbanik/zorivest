import { useStatusBar } from '../../hooks/useStatusBar'

/**
 * StatusFooter — bottom bar showing status messages.
 * Reads from StatusBarContext — components push messages via useStatusBar().setStatus().
 */
export default function StatusFooter() {
    const { message } = useStatusBar()
    const isReady = message === 'Ready'

    return (
        <footer className="flex items-center px-4 py-1 text-xs border-t border-bg-elevated">
            <span className={isReady ? 'text-fg-muted' : 'text-accent'}>
                {message}
            </span>
        </footer>
    )
}
