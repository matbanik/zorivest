import React from 'react'

interface SkipLinkProps {
    targetId?: string
    children?: React.ReactNode
}

/**
 * Accessible skip-to-content link.
 * Hidden by default, visible on Tab focus.
 */
export default function SkipLink({
    targetId = 'main-content',
    children = 'Skip to main content',
}: SkipLinkProps) {
    return (
        <a href={`#${targetId}`} className="skip-link">
            {children}
        </a>
    )
}
