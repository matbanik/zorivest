interface HeaderProps {
    onCommandPaletteToggle?: () => void
}

/**
 * Header — top bar with page title and command palette trigger.
 * Renders as <header> element for ARIA banner landmark.
 */
export default function Header({ onCommandPaletteToggle }: HeaderProps) {
    return (
        <header className="flex items-center justify-between px-4 py-2 border-b border-bg-elevated">
            <h1 className="text-sm font-semibold text-fg">Zorivest</h1>
            <div className="flex items-center gap-2">
                <button
                    onClick={onCommandPaletteToggle}
                    className="text-xs text-fg-muted px-1.5 py-0.5 border border-bg-elevated rounded hover:bg-bg-elevated hover:text-fg transition-colors cursor-pointer"
                    aria-label="Open command palette"
                >
                    <span className="text-xs text-fg-muted mr-1">Settings:</span> Ctrl+K
                </button>
            </div>
        </header>
    )
}
