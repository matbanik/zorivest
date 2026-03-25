// AccountTypeBadge — Color-coded chip for account types per 06b-gui-trades.md
// MEU-54: Multi-Account UI

interface AccountTypeBadgeProps {
    accountType: string
}

const BADGE_STYLES: Record<string, { bg: string; text: string; label: string }> = {
    broker: { bg: 'bg-blue-500/20', text: 'text-blue-400', label: 'Broker' },
    bank: { bg: 'bg-green-500/20', text: 'text-green-400', label: 'Bank' },
    revolving: { bg: 'bg-orange-500/20', text: 'text-orange-400', label: 'Revolving' },
    installment: { bg: 'bg-purple-500/20', text: 'text-purple-400', label: 'Installment' },
    ira: { bg: 'bg-yellow-500/20', text: 'text-yellow-400', label: 'IRA' },
    '401k': { bg: 'bg-teal-500/20', text: 'text-teal-400', label: '401k' },
}

export default function AccountTypeBadge({ accountType }: AccountTypeBadgeProps) {
    const style = BADGE_STYLES[accountType.toLowerCase()] ?? {
        bg: 'bg-gray-500/20',
        text: 'text-gray-400',
        label: accountType,
    }

    return (
        <span
            data-testid="account-type-badge"
            className={`inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium ${style.bg} ${style.text}`}
        >
            {style.label}
        </span>
    )
}
