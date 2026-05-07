import { useState, useCallback, useMemo, useEffect } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { apiFetch } from '@/lib/api'
import { useStatusBar } from '@/hooks/useStatusBar'
import { useFormGuard } from '@/hooks/useFormGuard'
import { useAccounts } from '@/hooks/useAccounts'
import UnsavedChangesModal from '@/components/UnsavedChangesModal'
import ConfirmDeleteModal from '@/components/ConfirmDeleteModal'
import { useConfirmDelete } from '@/hooks/useConfirmDelete'
import TickerAutocomplete from '@/components/TickerAutocomplete'
import SelectionCheckbox from '@/components/SelectionCheckbox'
import BulkActionBar from '@/components/BulkActionBar'
import TableFilterBar from '@/components/TableFilterBar'

// ── Types (G6: exact API field names) ────────────────────────────────────

export interface TradePlan {
    id: number
    ticker: string
    direction: string
    conviction: string
    strategy_name: string
    strategy_description: string
    entry_price: number
    stop_loss: number
    target_price: number
    entry_conditions: string
    exit_conditions: string
    timeframe: string
    risk_reward_ratio: number
    status: string
    linked_trade_id: string | null
    account_id: string | null
    created_at: string
    updated_at: string
    // T5: status timestamps
    executed_at?: string | null
    cancelled_at?: string | null
    shares_planned?: number | null
    position_size?: number | null
}

// T3: Account type imported from useAccounts hook (provides latest_balance)

// T4: Minimal trade shape for the link picker — real API fields
interface Trade {
    exec_id: string   // e.g. "IB-20260320-001"
    time: string      // ISO 8601 datetime
    instrument: string // ticker symbol
    action: string    // "BOT" | "SLD"
    quantity: number
    price: number
}

// ── Conviction + Status helpers ──────────────────────────────────────────

const CONVICTION_ICONS: Record<string, string> = {
    high: '🟢',
    medium: '🟡',
    low: '🔴',
}

const STATUS_OPTIONS = ['draft', 'active', 'executed', 'cancelled'] as const
const CONVICTION_OPTIONS = ['high', 'medium', 'low'] as const
const DIRECTION_OPTIONS = ['BOT', 'SLD'] as const
const TIMEFRAME_OPTIONS = ['scalp', 'intraday', 'swing', 'position'] as const

function convictionIcon(conviction: string): string {
    return CONVICTION_ICONS[conviction.toLowerCase()] ?? '⚪'
}

// ── Empty plan template ────────────────────────────────────────────────

const NEW_PLAN: Partial<TradePlan> = {
    id: 0,
    ticker: '',
    direction: 'BOT',
    conviction: 'medium',
    strategy_name: '',
    strategy_description: '',
    entry_price: 0,
    stop_loss: 0,
    target_price: 0,
    entry_conditions: '',
    exit_conditions: '',
    timeframe: 'intraday',
    status: 'draft',
    linked_trade_id: null,
    account_id: null,
    shares_planned: null,
    position_size: null,
}

// ── R:R and Risk Computation ─────────────────────────────────────────────

function computeRiskReward(entry: number, stop: number, target: number) {
    const riskPerShare = Math.abs(entry - stop)
    const rewardPerShare = Math.abs(target - entry)
    const ratio = riskPerShare > 0 ? rewardPerShare / riskPerShare : 0
    return { riskPerShare, rewardPerShare, ratio: Math.round(ratio * 100) / 100 }
}

// ── T5: Format timestamp helper ──────────────────────────────────────────

// T4-UX-1 / T5: Formats as MM-DD-YYYY h:mmAM/PM (e.g. 03-20-2026 2:35PM)
function formatTimestamp(iso: string | null | undefined): string {
    if (!iso) return ''
    try {
        const d = new Date(iso)
        const mm = String(d.getMonth() + 1).padStart(2, '0')
        const dd = String(d.getDate()).padStart(2, '0')
        const yyyy = d.getFullYear()
        const hours = d.getHours()
        const minutes = String(d.getMinutes()).padStart(2, '0')
        const ampm = hours >= 12 ? 'PM' : 'AM'
        const h = hours % 12 || 12
        return `${mm}-${dd}-${yyyy} ${h}:${minutes}${ampm}`
    } catch {
        return iso
    }
}

// ── Component ────────────────────────────────────────────────────────────

interface TradePlanPageProps {
    onOpenCalculator?: () => void
}

export default function TradePlanPage({ onOpenCalculator }: TradePlanPageProps) {
    const [selectedPlan, setSelectedPlan] = useState<TradePlan | null>(null)
    const [isCreating, setIsCreating] = useState(false)
    const [statusFilter, setStatusFilter] = useState<string>('')
    const [convictionFilter, setConvictionFilter] = useState<string>('')
    const [form, setForm] = useState<Partial<TradePlan>>(NEW_PLAN)
    const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({})
    const queryClient = useQueryClient()
    const { setStatus } = useStatusBar()

    // MEU-201: Multi-select state
    const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set())
    const [searchQuery, setSearchQuery] = useState('')
    const [showBulkConfirm, setShowBulkConfirm] = useState(false)

    // All Accounts default resolution message (shown when Calculator sends __ALL__)
    const [allAccountsDefaultInfo, setAllAccountsDefaultInfo] = useState<string | null>(null)

    // Fetch plans (G5: 5s auto-refresh)
    const { data: plans = [] } = useQuery<TradePlan[]>({
        queryKey: ['trade-plans'],
        queryFn: async () => {
            try {
                const result = await apiFetch<TradePlan[]>('/api/v1/trade-plans?limit=200')
                return result
            } catch {
                return []
            }
        },
        refetchInterval: 5_000,
    })

    // T3: Accounts via useAccounts hook — provides latest_balance for dropdown
    const { accounts, portfolioTotal } = useAccounts()

    // T6: Extract distinct strategy names from existing plans
    const strategyNames = useMemo(() => {
        const names = new Set(plans.map((p) => p.strategy_name).filter(Boolean))
        return Array.from(names).sort()
    }, [plans])

    // T4: Fetch trades for linking picker — always fetch when ticker is set (shown disabled until executed)
    const [linkedTradeId, setLinkedTradeId] = useState<string>('')
    const [tradePickerSearch, setTradePickerSearch] = useState<string>('')
    const [tradePickerLabel, setTradePickerLabel] = useState<string>('')  // MEU-70b: selected label display
    const isExecutedStatus = form.status === 'executed'
    const planTicker = form.ticker ?? ''
    const { data: linkableTrades = [] } = useQuery<Trade[]>({
        queryKey: ['trades-for-link', planTicker],
        queryFn: async () => {
            try {
                // R2: use 'search' param — 'ticker' is not accepted by GET /api/v1/trades
                const result = await apiFetch<{ items: Trade[] }>(`/api/v1/trades?search=${encodeURIComponent(planTicker)}&limit=50`)
                return result.items ?? []
            } catch {
                return []
            }
        },
        enabled: planTicker.length > 0,  // MEU-70b: always fetch when ticker set; picker is shown disabled
    })

    // Client-side filtering (AC-6) + MEU-201: text search
    const filteredPlans = useMemo(() => {
        let result = plans
        if (statusFilter) result = result.filter((p) => p.status === statusFilter)
        if (convictionFilter) result = result.filter((p) => p.conviction === convictionFilter)
        if (searchQuery.trim()) {
            const q = searchQuery.toLowerCase()
            result = result.filter((p) =>
                p.ticker.toLowerCase().includes(q) ||
                p.strategy_name.toLowerCase().includes(q)
            )
        }
        return result
    }, [plans, statusFilter, convictionFilter, searchQuery])

    // Select plan and populate form
    const handleSelectPlan = useCallback((plan: TradePlan) => {
        setSelectedPlan(plan)
        setIsCreating(false)
        setForm({ ...plan })
        setLinkedTradeId(plan.linked_trade_id ?? '')
        setTradePickerLabel(plan.linked_trade_id ?? '')
        setFieldErrors({})
    }, [])

    // ── Dirty state computation ───────────────────────────────────────────
    const isDirty = useMemo(() => {
        if (isCreating) {
            // For new plans, dirty if any field has been filled
            return !!form.ticker || !!form.strategy_name || !!form.strategy_description ||
                !!form.entry_conditions || !!form.exit_conditions ||
                (form.entry_price ?? 0) !== 0 || (form.stop_loss ?? 0) !== 0 || (form.target_price ?? 0) !== 0
        }
        if (!selectedPlan) return false
        // Compare mutable fields against server state
        return (
            form.ticker !== selectedPlan.ticker ||
            form.direction !== selectedPlan.direction ||
            form.conviction !== selectedPlan.conviction ||
            form.strategy_name !== selectedPlan.strategy_name ||
            form.strategy_description !== selectedPlan.strategy_description ||
            form.entry_price !== selectedPlan.entry_price ||
            form.stop_loss !== selectedPlan.stop_loss ||
            form.target_price !== selectedPlan.target_price ||
            form.entry_conditions !== selectedPlan.entry_conditions ||
            form.exit_conditions !== selectedPlan.exit_conditions ||
            form.timeframe !== selectedPlan.timeframe ||
            form.account_id !== selectedPlan.account_id ||
            form.shares_planned !== selectedPlan.shares_planned ||
            form.position_size !== selectedPlan.position_size
        )
    }, [form, selectedPlan, isCreating])

    // ── Unsaved changes guard (3-button: parent-owned form) ─────────────
    const handleNewPlan = useCallback(() => {
        setSelectedPlan(null)
        setIsCreating(true)
        setForm({ ...NEW_PLAN })
        setLinkedTradeId('')
        setTradePickerLabel('')
        setFieldErrors({})
    }, [])

    const doNavigate = useCallback((target: TradePlan | '__new__' | null) => {
        if (target === '__new__') {
            handleNewPlan()
        } else if (target) {
            handleSelectPlan(target)
        }
    }, [handleSelectPlan, handleNewPlan])

    const { showModal, guardedSelect, handleCancel, handleDiscard, handleSaveAndContinue, isSaveDisabled } =
        useFormGuard<TradePlan | '__new__' | null>({
            isDirty,
            onNavigate: doNavigate,
            onSave: async () => {
                await handleSave()
            },
            isFormInvalid: () => !form.ticker?.trim() || !form.strategy_name?.trim(),
        })

    const handleClose = useCallback(() => {
        setSelectedPlan(null)
        setIsCreating(false)
        setFieldErrors({})
    }, [])

    const updateField = useCallback(<K extends keyof TradePlan>(key: K, value: TradePlan[K]) => {
        setForm((prev) => ({ ...prev, [key]: value }))
    }, [])

    // Fetch live quote when ticker is selected from autocomplete dropdown
    const handleTickerSelect = useCallback((result: { symbol: string }) => {
        const sym = result.symbol
        updateField('ticker', sym)
        apiFetch<{ price: number }>(`/api/v1/market-data/quote?ticker=${encodeURIComponent(sym)}`)
            .then((quote) => {
                const price = Math.round(quote.price * 100) / 100
                setForm((prev) => ({
                    ...prev,
                    entry_price: price,
                    // Auto-fill stop and target when both are at 0 (fresh plan)
                    stop_loss: (prev.stop_loss === 0 || prev.stop_loss == null) ? price : prev.stop_loss,
                    target_price: (prev.target_price === 0 || prev.target_price == null) ? price : prev.target_price,
                }))
            })
            .catch((err: unknown) => {
                setStatus(`Could not fetch quote: ${err instanceof Error ? err.message : 'error'}`)
            })
    }, [updateField, setStatus])

    // Live R:R computation (AC-4)
    const rr = useMemo(() => {
        return computeRiskReward(
            form.entry_price ?? 0,
            form.stop_loss ?? 0,
            form.target_price ?? 0,
        )
    }, [form.entry_price, form.stop_loss, form.target_price])

    // Auto-recalculate position_size when shares_planned or entry_price changes
    useEffect(() => {
        const shares = form.shares_planned
        const entry = form.entry_price
        if (shares != null && shares > 0 && entry != null && entry > 0) {
            const newSize = Math.round(shares * entry * 100) / 100
            setForm((prev) => prev.position_size === newSize ? prev : { ...prev, position_size: newSize })
        }
    }, [form.shares_planned, form.entry_price])

    // Save (AC-5)
    const handleSave = useCallback(async () => {
        // Frontend validation — show inline errors matching Trade form UX
        const errors: Record<string, string> = {}
        if (!form.ticker?.trim()) {
            errors.ticker = 'Ticker is required'
        }
        if (!form.strategy_name?.trim()) {
            errors.strategy_name = 'Strategy Name is required'
        }
        if (Object.keys(errors).length > 0) {
            setFieldErrors(errors)
            setStatus('Error: Please fix the highlighted fields')
            throw new Error('Validation failed')
        }
        setFieldErrors({})
        const payload: Record<string, unknown> = {
            ticker: form.ticker,
            direction: form.direction,
            conviction: form.conviction,
            strategy_name: form.strategy_name,
            strategy_description: form.strategy_description,
            entry_price: form.entry_price,
            stop_loss: form.stop_loss,
            target_price: form.target_price,
            entry_conditions: form.entry_conditions,
            exit_conditions: form.exit_conditions,
            timeframe: form.timeframe,
            account_id: form.account_id || null,
            shares_planned: form.shares_planned || null,
            position_size: form.position_size || null,
        }
        // R1: linked_trade_id is only accepted on UPDATE (not CREATE — backend extra="forbid")
        if (!isCreating) {
            payload.linked_trade_id = linkedTradeId || form.linked_trade_id || null
        }

        try {
            if (isCreating) {
                setStatus('Creating plan...')
                await apiFetch('/api/v1/trade-plans', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload),
                })
                setStatus('Plan created')
            } else if (selectedPlan) {
                setStatus('Updating plan...')
                await apiFetch(`/api/v1/trade-plans/${selectedPlan.id}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload),
                })
                setStatus('Plan updated')
            }
            await queryClient.invalidateQueries({ queryKey: ['trade-plans'] })
            handleClose()
        } catch (err) {
            setStatus(`Error: ${err instanceof Error ? err.message : 'Failed to save'}`)
        }
    }, [form, isCreating, selectedPlan, queryClient, setStatus, handleClose, linkedTradeId])

    // Status transition (AC-5a)
    // R3: updateField fires only on success so local state never diverges from server state on failure
    const handleStatusChange = useCallback(async (planId: number, newStatus: string) => {
        try {
            setStatus(`Changing status to ${newStatus}...`)
            await apiFetch(`/api/v1/trade-plans/${planId}/status`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                // R1: include linked_trade_id when transitioning to executed with a trade selected
                body: JSON.stringify({
                    status: newStatus,
                    ...(newStatus === 'executed' && linkedTradeId
                        ? { linked_trade_id: linkedTradeId }
                        : {}),
                }),
            })
            // Defer local state update until server confirms success (R3)
            updateField('status', newStatus)
            setStatus(`Status \u2192 ${newStatus}`)
            await queryClient.invalidateQueries({ queryKey: ['trade-plans'] })
        } catch (err) {
            setStatus(`Error: ${err instanceof Error ? err.message : 'Failed'}`)
            // No updateField here — local status stays as-is on server failure
        }
    }, [linkedTradeId, queryClient, setStatus, updateField])

    // MEU-201: Multi-select handlers
    const toggleSelect = useCallback((planId: number) => {
        setSelectedIds(prev => {
            const next = new Set(prev)
            if (next.has(planId)) next.delete(planId)
            else next.add(planId)
            return next
        })
    }, [])

    const toggleSelectAll = useCallback(() => {
        setSelectedIds(prev => {
            if (prev.size === filteredPlans.length && prev.size > 0) {
                return new Set()
            }
            return new Set(filteredPlans.map(p => p.id))
        })
    }, [filteredPlans])

    const handleBulkDelete = useCallback(async () => {
        const ids = Array.from(selectedIds)
        setStatus(`Deleting ${ids.length} plans...`)
        try {
            await Promise.all(ids.map(id => apiFetch(`/api/v1/trade-plans/${id}`, { method: 'DELETE' })))
            setStatus(`Deleted ${ids.length} plans`)
            setSelectedIds(new Set())
            setShowBulkConfirm(false)
            await queryClient.invalidateQueries({ queryKey: ['trade-plans'] })
        } catch (err) {
            setStatus(`Error: ${err instanceof Error ? err.message : 'Bulk delete failed'}`)
            setShowBulkConfirm(false)
        }
    }, [selectedIds, queryClient, setStatus])

    // Delete (AC-5, G2: disabled on new)
    const deleteConfirm = useConfirmDelete()
    const handleDelete = useCallback(() => {
        if (!selectedPlan) return
        const planLabel = selectedPlan.strategy_name
            ? `${selectedPlan.ticker} — ${selectedPlan.strategy_name}`
            : selectedPlan.ticker
        deleteConfirm.confirmSingle('trade plan', planLabel, async () => {
            try {
                setStatus('Deleting plan...')
                await apiFetch(`/api/v1/trade-plans/${selectedPlan.id}`, { method: 'DELETE' })
                setStatus('Plan deleted')
                await queryClient.invalidateQueries({ queryKey: ['trade-plans'] })
                handleClose()
            } catch (err) {
                setStatus(`Error: ${err instanceof Error ? err.message : 'Failed'}`)
            }
        })
    }, [selectedPlan, deleteConfirm, queryClient, setStatus, handleClose])

    // T2: Open calculator with plan prices and ticker (G11: custom event pattern)
    // R5: include ticker so modal can prefill the instrument field
    // When creating a new plan, save it first so it gets an ID and appears in the calculator picker
    const handleCalculatePosition = useCallback(async () => {
        let planId: number | null = selectedPlan?.id ?? null

        if (isCreating) {
            // Validate required fields before saving
            const errors: Record<string, string> = {}
            if (!form.ticker?.trim()) errors.ticker = 'Ticker is required'
            if (!form.strategy_name?.trim()) errors.strategy_name = 'Strategy Name is required'
            if (Object.keys(errors).length > 0) {
                setFieldErrors(errors)
                setStatus('Error: Save plan before opening calculator')
                return
            }
            setFieldErrors({})

            try {
                const payload: Record<string, unknown> = {
                    ticker: form.ticker,
                    direction: form.direction,
                    conviction: form.conviction,
                    strategy_name: form.strategy_name,
                    strategy_description: form.strategy_description,
                    entry_price: form.entry_price,
                    stop_loss: form.stop_loss,
                    target_price: form.target_price,
                    entry_conditions: form.entry_conditions,
                    exit_conditions: form.exit_conditions,
                    timeframe: form.timeframe,
                    account_id: form.account_id || null,
                    shares_planned: form.shares_planned || null,
                    position_size: form.position_size || null,
                }

                setStatus('Saving plan before opening calculator...')
                const created = await apiFetch<TradePlan>('/api/v1/trade-plans', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload),
                })

                // Use the POST response ID directly — no refetch+filter needed
                planId = created.id
                setSelectedPlan(created)
                setIsCreating(false)
                setForm({ ...created })
                setStatus('Plan saved — opening calculator')
                await queryClient.invalidateQueries({ queryKey: ['trade-plans'] })
            } catch (err) {
                setStatus(`Error: ${err instanceof Error ? err.message : 'Failed to save plan'}`)
                return
            }
        }

        window.dispatchEvent(new CustomEvent('zorivest:open-calculator', {
            detail: {
                plan_id: planId,
                ticker: form.ticker ?? '',
                entry_price: form.entry_price ?? 0,
                stop_loss: form.stop_loss ?? 0,
                target_price: form.target_price ?? 0,
            },
        }))
    }, [selectedPlan?.id, isCreating, form, queryClient, setStatus])

    // MEU-70a Sub-MEU C: Listen for calculator-apply event (AC-22)
    useEffect(() => {
        const handler = (e: Event) => {
            const detail = (e as CustomEvent)?.detail
            if (!detail) return
            // If a plan_id is specified and it matches current plan (or __new__), apply
            // If no plan_id, apply to whatever plan is currently open (backwards compat)
            const targetPlanId = detail.plan_id
            const currentPlanId = selectedPlan?.id ?? (isCreating ? '__new__' : null)
            if (targetPlanId && targetPlanId !== currentPlanId) {
                // Calculator is targeting a different plan — auto-select it
                if (typeof targetPlanId === 'number') {
                    const targetPlan = plans.find(p => p.id === targetPlanId)
                    if (targetPlan) {
                        setSelectedPlan(targetPlan)
                        setIsCreating(false)
                        setForm({ ...targetPlan })
                    }
                }
            }

            // Resolve __ALL__ account to the largest-balance account
            let resolvedAccountId = detail.account_id
            if (detail.account_id === '__ALL__') {
                const largestAccount = accounts
                    .filter(a => (a.latest_balance ?? 0) > 0)
                    .sort((a, b) => (b.latest_balance ?? 0) - (a.latest_balance ?? 0))[0]
                if (largestAccount) {
                    resolvedAccountId = largestAccount.account_id
                    const balStr = largestAccount.latest_balance?.toLocaleString('en-US', { style: 'currency', currency: 'USD' }) ?? '$0'
                    setAllAccountsDefaultInfo(
                        `"All Accounts" (${portfolioTotal.toLocaleString('en-US', { style: 'currency', currency: 'USD' })}) was selected in Calculator. Defaulted to "${largestAccount.name}" (${balStr}) — the account with the largest balance. You can change this above.`
                    )
                } else {
                    resolvedAccountId = undefined
                    setAllAccountsDefaultInfo(
                        `"All Accounts" was selected in Calculator but no accounts have a recorded balance. Please select an account manually.`
                    )
                }
            } else {
                // Clear the info message when a specific account is applied
                setAllAccountsDefaultInfo(null)
            }

            // Apply the values
            setForm((prev) => ({
                ...prev,
                ...(detail.shares_planned != null ? { shares_planned: detail.shares_planned } : {}),
                ...(detail.position_size != null ? { position_size: detail.position_size } : {}),
                ...(resolvedAccountId ? { account_id: resolvedAccountId } : {}),
                ...(detail.entry_price != null ? { entry_price: detail.entry_price } : {}),
                ...(detail.stop_loss != null ? { stop_loss: detail.stop_loss } : {}),
                ...(detail.target_price != null ? { target_price: detail.target_price } : {}),
            }))
        }
        window.addEventListener('zorivest:calculator-apply', handler)
        return () => window.removeEventListener('zorivest:calculator-apply', handler)
    }, [selectedPlan?.id, isCreating, plans, accounts, portfolioTotal])

    const isDetailOpen = isCreating || selectedPlan !== null

    return (
        <>
        <div data-testid="trade-plan-page" className="flex h-full">
            {/* Left: Plan List */}
            <div className={`flex-1 min-w-0 transition-all ${isDetailOpen ? 'w-[55%]' : 'w-full'}`}>
                <div className="p-4">
                    <div className="flex items-center justify-between mb-4">
                        <h2 className="text-lg font-semibold text-fg">Trade Plans</h2>
                        <div className="flex items-center gap-2">
                            {onOpenCalculator && (
                                <button
                                    data-testid="open-calculator-btn"
                                    onClick={onOpenCalculator}
                                    className="px-3 py-1.5 text-sm font-medium rounded-md border border-bg-subtle bg-bg hover:bg-bg-elevated text-fg transition-colors cursor-pointer"
                                >
                                    🧮 Calculator
                                </button>
                            )}
                            <button
                                data-testid="new-plan-btn"
                                onClick={() => guardedSelect('__new__')}
                                className="px-4 py-1.5 text-sm font-medium rounded-md border border-bg-subtle bg-bg hover:bg-bg-elevated text-fg transition-colors cursor-pointer"
                            >
                                + New Plan
                            </button>
                        </div>
                    </div>

                    {/* Filters (AC-6) */}
                    <div className="flex gap-2 mb-4">
                        <select
                            data-testid="plan-status-filter"
                            aria-label="Filter by status"
                            value={statusFilter}
                            onChange={(e) => setStatusFilter(e.target.value)}
                            className="px-3 py-1.5 text-sm rounded-md bg-bg border border-bg-subtle text-fg"
                        >
                            <option value="">All Statuses</option>
                            {STATUS_OPTIONS.map((s) => (
                                <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>
                            ))}
                        </select>
                        <select
                            data-testid="plan-conviction-filter"
                            aria-label="Filter by conviction"
                            value={convictionFilter}
                            onChange={(e) => setConvictionFilter(e.target.value)}
                            className="px-3 py-1.5 text-sm rounded-md bg-bg border border-bg-subtle text-fg"
                        >
                            <option value="">All Convictions</option>
                            {CONVICTION_OPTIONS.map((c) => (
                                <option key={c} value={c}>{convictionIcon(c)} {c.charAt(0).toUpperCase() + c.slice(1)}</option>
                            ))}
                        </select>
                    </div>

                    {/* MEU-201: Text search */}
                    <TableFilterBar
                        searchValue={searchQuery}
                        onSearchChange={setSearchQuery}
                        searchPlaceholder="Search by ticker or strategy…"
                        debounceMs={0}
                    />

                    {/* MEU-201: Select-all + BulkActionBar */}
                    <div className="flex items-center gap-2 mb-2 mt-2">
                        <SelectionCheckbox
                            checked={selectedIds.size === filteredPlans.length && filteredPlans.length > 0}
                            indeterminate={selectedIds.size > 0 && selectedIds.size < filteredPlans.length}
                            onChange={toggleSelectAll}
                            ariaLabel="Select all plans"
                            data-testid="select-all-plan-checkbox"
                        />
                        <span className="text-xs text-fg-muted">{filteredPlans.length} plans</span>
                    </div>

                    {selectedIds.size > 0 && (
                        <BulkActionBar
                            selectedCount={selectedIds.size}
                            entityLabel="trade plan"
                            onDelete={() => setShowBulkConfirm(true)}
                            onClearSelection={() => setSelectedIds(new Set())}
                        />
                    )}

                    {/* Plan Cards */}
                    <div className="space-y-2" data-testid="plan-list">
                        {filteredPlans.length === 0 && (
                            <p className="text-sm text-fg-muted py-4 text-center">No plans found</p>
                        )}
                        {filteredPlans.map((plan) => (
                            <button
                                key={plan.id}
                                data-testid={`plan-card-${plan.id}`}
                                onClick={() => guardedSelect(plan)}
                                className={`w-full text-left px-4 py-3 rounded-md border cursor-pointer transition-colors ${selectedPlan?.id === plan.id
                                    ? 'border-accent bg-accent/10'
                                    : selectedIds.has(plan.id)
                                        ? 'border-accent/50 bg-bg-subtle'
                                        : 'border-bg-subtle bg-bg hover:bg-bg-elevated'
                                    }`}
                            >
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-2">
                                        {/* MEU-201: Row checkbox */}
                                        <span onClick={(e) => e.stopPropagation()}>
                                            <SelectionCheckbox
                                                checked={selectedIds.has(plan.id)}
                                                onChange={() => toggleSelect(plan.id)}
                                                ariaLabel={`Select ${plan.ticker}`}
                                                data-testid={`plan-row-checkbox-${plan.id}`}
                                            />
                                        </span>
                                        <span data-testid="conviction-indicator">
                                            {convictionIcon(plan.conviction)}
                                        </span>
                                        <span className="font-medium text-fg">{plan.ticker}</span>
                                        <span className="text-xs text-fg-muted">{plan.direction}</span>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <span className={`text-xs px-2 py-0.5 rounded-full ${plan.status === 'active' ? 'bg-green-500/20 text-green-400' :
                                            plan.status === 'executed' ? 'bg-blue-500/20 text-blue-400' :
                                                plan.status === 'cancelled' ? 'bg-red-500/20 text-red-400' :
                                                    'bg-bg-elevated text-fg-muted'
                                            }`}>
                                            {plan.status}
                                        </span>
                                        {plan.risk_reward_ratio > 0 && (
                                            <span className="text-xs text-fg-muted">
                                                R:R {plan.risk_reward_ratio.toFixed(1)}
                                            </span>
                                        )}
                                    </div>
                                </div>
                                <div className="text-xs text-fg-muted mt-1">
                                    {plan.strategy_name} · {plan.timeframe}
                                </div>
                            </button>
                        ))}
                    </div>
                </div>
            </div>

            {/* Right: Detail Panel */}
            {isDetailOpen && (
                <div className="w-[45%] border-l border-bg-subtle overflow-y-auto" data-testid="plan-detail-panel">
                    <div className="p-4">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-md font-semibold text-fg">
                                {isCreating ? 'New Trade Plan' : `Plan #${selectedPlan?.id}`}
                            </h3>
                            <button
                                onClick={handleClose}
                                className="text-fg-muted hover:text-fg cursor-pointer"
                                data-testid="close-plan-detail"
                            >
                                ✕
                            </button>
                        </div>

                        <div className="space-y-3">
                            {/* Ticker + Direction */}
                            <div className="grid grid-cols-2 gap-2">
                                <div>
                                    <label className="block text-xs text-fg-muted mb-1">Ticker</label>
                                    <TickerAutocomplete
                                        value={form.ticker ?? ''}
                                        onChange={(val) => { updateField('ticker', val); setFieldErrors(prev => { const n = { ...prev }; delete n.ticker; return n }) }}
                                        onSelect={handleTickerSelect}
                                        placeholder="AAPL"
                                        data-testid="plan-ticker"
                                    />
                                    {fieldErrors.ticker && (
                                        <span className="text-xs text-red-400">{fieldErrors.ticker}</span>
                                    )}
                                </div>
                                <div>
                                    <label className="block text-xs text-fg-muted mb-1">Direction</label>
                                    <select
                                        data-testid="plan-direction"
                                        value={form.direction ?? 'BOT'}
                                        onChange={(e) => updateField('direction', e.target.value)}
                                        className="w-full px-3 py-1.5 text-sm rounded-md bg-bg border border-bg-subtle text-fg"
                                    >
                                        {DIRECTION_OPTIONS.map((d) => (
                                            <option key={d} value={d}>{d === 'BOT' ? 'Buy' : 'Sell'}</option>
                                        ))}
                                    </select>
                                </div>
                            </div>

                            {/* Conviction + Timeframe */}
                            <div className="grid grid-cols-2 gap-2">
                                <div>
                                    <label className="block text-xs text-fg-muted mb-1">Conviction</label>
                                    <select
                                        data-testid="plan-conviction"
                                        value={form.conviction ?? 'medium'}
                                        onChange={(e) => updateField('conviction', e.target.value)}
                                        className="w-full px-3 py-1.5 text-sm rounded-md bg-bg border border-bg-subtle text-fg"
                                    >
                                        {CONVICTION_OPTIONS.map((c) => (
                                            <option key={c} value={c}>{convictionIcon(c)} {c.charAt(0).toUpperCase() + c.slice(1)}</option>
                                        ))}
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-xs text-fg-muted mb-1">Timeframe</label>
                                    <select
                                        data-testid="plan-timeframe"
                                        value={form.timeframe ?? 'intraday'}
                                        onChange={(e) => updateField('timeframe', e.target.value)}
                                        className="w-full px-3 py-1.5 text-sm rounded-md bg-bg border border-bg-subtle text-fg"
                                    >
                                        {TIMEFRAME_OPTIONS.map((t) => (
                                            <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>
                                        ))}
                                    </select>
                                </div>
                            </div>

                            {/* T6: Strategy Name with datalist suggestions */}
                            <div>
                                <label className="block text-xs text-fg-muted mb-1">Strategy Name</label>
                                <input
                                    data-testid="plan-strategy-name"
                                    list="strategy-suggestions"
                                    value={form.strategy_name ?? ''}
                                    onChange={(e) => { updateField('strategy_name', e.target.value); setFieldErrors(prev => { const n = { ...prev }; delete n.strategy_name; return n }) }}
                                    className={`w-full px-3 py-1.5 text-sm rounded-md bg-bg border text-fg ${fieldErrors.strategy_name ? 'border-red-500' : 'border-bg-subtle'}`}
                                    placeholder="Breakout above resistance"
                                />
                                <datalist id="strategy-suggestions">
                                    {strategyNames.map((name) => (
                                        <option key={name} value={name} />
                                    ))}
                                </datalist>
                                {fieldErrors.strategy_name && (
                                    <span className="text-xs text-red-400">{fieldErrors.strategy_name}</span>
                                )}
                            </div>
                            <div>
                                <label className="block text-xs text-fg-muted mb-1">Strategy Description</label>
                                <textarea
                                    data-testid="plan-strategy-description"
                                    value={form.strategy_description ?? ''}
                                    onChange={(e) => updateField('strategy_description', e.target.value)}
                                    rows={2}
                                    className="w-full px-3 py-1.5 text-sm rounded-md bg-bg border border-bg-subtle text-fg resize-y"
                                />
                            </div>

                            {/* Price Levels: Entry Price, Planned Shares, Stop Loss, Target (4-col) */}
                            <div className="grid grid-cols-4 gap-2">
                                <div>
                                    <label className="block text-xs text-fg-muted mb-1">Entry Price</label>
                                    <input
                                        data-testid="plan-entry-price"
                                        type="number"
                                        step="0.01"
                                        value={form.entry_price ?? 0}
                                        onChange={(e) => updateField('entry_price', parseFloat(e.target.value) || 0)}
                                        className="w-full px-3 py-1.5 text-sm rounded-md bg-bg border border-bg-subtle text-fg"
                                    />
                                </div>
                                <div>
                                    <label className="block text-xs text-fg-muted mb-1">Planned Shares</label>
                                    <input
                                        data-testid="plan-shares-planned"
                                        type="number"
                                        min="0"
                                        step="1"
                                        value={form.shares_planned ?? ''}
                                        onChange={(e) => updateField('shares_planned', e.target.value === '' ? null : (parseInt(e.target.value) || 0))}
                                        placeholder="—"
                                        className="w-full px-3 py-1.5 text-sm rounded-md bg-bg border border-bg-subtle text-fg"
                                    />
                                </div>
                                <div>
                                    <label className="block text-xs text-fg-muted mb-1">Stop Loss</label>
                                    <input
                                        data-testid="plan-stop-loss"
                                        type="number"
                                        step="0.01"
                                        value={form.stop_loss ?? 0}
                                        onChange={(e) => updateField('stop_loss', parseFloat(e.target.value) || 0)}
                                        className="w-full px-3 py-1.5 text-sm rounded-md bg-bg border border-bg-subtle text-fg"
                                    />
                                </div>
                                <div>
                                    <label className="block text-xs text-fg-muted mb-1">Target</label>
                                    <input
                                        data-testid="plan-target-price"
                                        type="number"
                                        step="0.01"
                                        value={form.target_price ?? 0}
                                        onChange={(e) => updateField('target_price', parseFloat(e.target.value) || 0)}
                                        className="w-full px-3 py-1.5 text-sm rounded-md bg-bg border border-bg-subtle text-fg"
                                    />
                                </div>
                            </div>

                            {/* Calculator action — centered below inputs per UX best practice */}
                            <div className="flex justify-center">
                                <button
                                    data-testid="plan-copy-from-calc-btn"
                                    type="button"
                                    onClick={handleCalculatePosition}
                                    className="px-4 py-1.5 text-sm rounded-md border border-accent/30 bg-accent/5 text-accent hover:bg-accent/10 cursor-pointer transition-colors"
                                >
                                    🧮 Calculator
                                </button>
                            </div>

                            {/* Computed metrics: Position Size, Risk/Share, Reward/Share, R:R (4-col) */}
                            <div className="grid grid-cols-4 gap-2 py-2 px-3 rounded-md bg-bg-elevated text-sm" data-testid="plan-rr-display">
                                <div>
                                    <span className="text-xs text-fg-muted">Position Size</span>
                                    <div className="text-fg font-mono" data-testid="plan-position-size">
                                        {form.position_size != null ? `$${form.position_size.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '—'}
                                    </div>
                                </div>
                                <div>
                                    <span className="text-xs text-fg-muted">Risk/Share</span>
                                    <div className="text-fg font-mono">${rr.riskPerShare.toFixed(2)}</div>
                                </div>
                                <div>
                                    <span className="text-xs text-fg-muted">Reward/Share</span>
                                    <div className="text-fg font-mono">${rr.rewardPerShare.toFixed(2)}</div>
                                </div>
                                <div>
                                    <span className="text-xs text-fg-muted">R:R Ratio</span>
                                    <div className={`font-mono font-semibold ${rr.ratio >= 2 ? 'text-green-400' : rr.ratio >= 1 ? 'text-yellow-400' : 'text-red-400'}`}>
                                        {rr.ratio.toFixed(2)}
                                    </div>
                                </div>
                            </div>

                            {/* Conditions */}
                            <div>
                                <label className="block text-xs text-fg-muted mb-1">Entry Conditions</label>
                                <textarea
                                    data-testid="plan-entry-conditions"
                                    value={form.entry_conditions ?? ''}
                                    onChange={(e) => updateField('entry_conditions', e.target.value)}
                                    rows={2}
                                    className="w-full px-3 py-1.5 text-sm rounded-md bg-bg border border-bg-subtle text-fg resize-y"
                                    placeholder="What must be true before entering?"
                                />
                            </div>
                            <div>
                                <label className="block text-xs text-fg-muted mb-1">Exit Conditions</label>
                                <textarea
                                    data-testid="plan-exit-conditions"
                                    value={form.exit_conditions ?? ''}
                                    onChange={(e) => updateField('exit_conditions', e.target.value)}
                                    rows={2}
                                    className="w-full px-3 py-1.5 text-sm rounded-md bg-bg border border-bg-subtle text-fg resize-y"
                                    placeholder="When to exit?"
                                />
                            </div>

                            {/* T3: Account Dropdown — shows balances, resolves __ALL__ */}
                            <div>
                                <label className="block text-xs text-fg-muted mb-1">Account</label>
                                <select
                                    data-testid="plan-account-select"
                                    value={form.account_id ?? ''}
                                    onChange={(e) => {
                                        updateField('account_id', e.target.value || null)
                                        setAllAccountsDefaultInfo(null) // Clear info when user manually changes
                                    }}
                                    className="w-full px-3 py-1.5 text-sm rounded-md bg-bg border border-bg-subtle text-fg"
                                >
                                    <option value="">None (no account)</option>
                                    {accounts.map((acct) => (
                                        <option key={acct.account_id} value={acct.account_id}>
                                            {acct.name} ({acct.account_type}){acct.latest_balance != null ? ` — $${acct.latest_balance.toLocaleString()}` : ''}
                                        </option>
                                    ))}
                                </select>
                                {allAccountsDefaultInfo && (
                                    <div
                                        data-testid="all-accounts-default-info"
                                        className="mt-1.5 px-3 py-2 text-xs rounded-md bg-blue-500/10 border border-blue-500/20 text-blue-300"
                                    >
                                        ℹ️ {allAccountsDefaultInfo}
                                    </div>
                                )}
                            </div>

                            {/* Linked Trade (AC-7: readonly) */}
                            {selectedPlan?.linked_trade_id && (
                                <div>
                                    <label className="block text-xs text-fg-muted mb-1">Linked Trade</label>
                                    <input
                                        data-testid="plan-linked-trade"
                                        value={selectedPlan.linked_trade_id}
                                        readOnly
                                        className="w-full px-3 py-1.5 text-sm rounded-md bg-bg-elevated border border-bg-subtle text-fg-muted cursor-not-allowed"
                                    />
                                </div>
                            )}

                            {/* T5: Status timestamps (read-only) */}
                            {selectedPlan?.executed_at && (
                                <div className="text-xs text-fg-muted" data-testid="plan-executed-at">
                                    Executed on {formatTimestamp(selectedPlan.executed_at)}
                                </div>
                            )}
                            {selectedPlan?.cancelled_at && (
                                <div className="text-xs text-fg-muted" data-testid="plan-cancelled-at">
                                    Cancelled on {formatTimestamp(selectedPlan.cancelled_at)}
                                </div>
                            )}

                            {/* MEU-70b Issue 1: Segmented Status Buttons — single control, no dropdown */}
                            {selectedPlan && !isCreating && (
                                <div data-testid="plan-status-section">
                                    <label className="block text-xs text-fg-muted mb-1">Status</label>
                                    <div className="flex gap-1" data-testid="plan-status-buttons" role="group" aria-label="Plan status">
                                        {([
                                            { value: 'draft', label: 'Draft', active: 'bg-bg-elevated text-fg border-bg-subtle' },
                                            { value: 'active', label: 'Active', active: 'bg-blue-500/20 text-blue-300 border-blue-500/40' },
                                            { value: 'executed', label: 'Executed', active: 'bg-green-500/20 text-green-300 border-green-500/40' },
                                            { value: 'cancelled', label: 'Cancelled', active: 'bg-red-500/15 text-red-400 border-red-500/30' },
                                        ] as const).map(({ value, label, active }) => {
                                            const isCurrent = (form.status ?? selectedPlan.status) === value
                                            return (
                                                <button
                                                    key={value}
                                                    type="button"
                                                    data-testid={`plan-status-${value}`}
                                                    onClick={() => handleStatusChange(selectedPlan.id, value)}
                                                    className={`flex-1 px-2 py-1.5 text-xs rounded-md border cursor-pointer transition-colors font-medium ${isCurrent
                                                        ? active
                                                        : 'bg-bg text-fg-muted border-bg-subtle hover:bg-bg-elevated'
                                                        }`}
                                                    aria-pressed={isCurrent}
                                                >
                                                    {label}
                                                </button>
                                            )
                                        })}
                                    </div>
                                </div>
                            )}

                            {/* MEU-70b Issue 2+3: Link to Trade — always visible, disabled unless Executed */}
                            {selectedPlan && !isCreating && (
                                <div data-testid="plan-trade-picker">
                                    {/* Section divider to show causal relationship */}
                                    <div className="flex items-center gap-2 mb-1">
                                        <span className={`text-xs font-medium ${isExecutedStatus ? 'text-green-400' : 'text-fg-muted'
                                            }`}>⚡ Execution</span>
                                        {!isExecutedStatus && (
                                            <span className="text-xs text-fg-muted/60 italic">
                                                — Set status to Executed to link an execution record
                                            </span>
                                        )}
                                    </div>

                                    <label className="block text-xs text-fg-muted mb-1">Link to Trade</label>

                                    {/* MEU-70b Issue 3: Search input shows selected label, not raw query */}
                                    <div className="relative">
                                        <input
                                            data-testid="trade-picker-search"
                                            type="text"
                                            value={tradePickerLabel || tradePickerSearch}
                                            disabled={!isExecutedStatus}
                                            onChange={(e) => {
                                                setTradePickerLabel('')
                                                setTradePickerSearch(e.target.value)
                                            }}
                                            placeholder={isExecutedStatus ? 'Filter trades...' : 'Select Executed status first'}
                                            title={!isExecutedStatus ? 'Change plan status to Executed to link an execution record' : undefined}
                                            className={`w-full px-3 py-1.5 text-sm rounded-md border text-fg pr-8 transition-colors ${isExecutedStatus
                                                ? 'bg-bg border-green-500/30 cursor-text'
                                                : 'bg-bg-elevated border-bg-subtle text-fg-muted cursor-not-allowed opacity-50'
                                                }`}
                                        />
                                        {/* Clear button when a trade is selected */}
                                        {isExecutedStatus && (linkedTradeId || form.linked_trade_id) && (
                                            <button
                                                type="button"
                                                data-testid="trade-picker-clear"
                                                onClick={() => {
                                                    setLinkedTradeId('')
                                                    setTradePickerLabel('')
                                                    setTradePickerSearch('')
                                                    updateField('linked_trade_id', null)
                                                }}
                                                className="absolute right-2 top-1/2 -translate-y-1/2 text-fg-muted hover:text-fg text-xs cursor-pointer"
                                                title="Remove linked trade"
                                            >
                                                ×
                                            </button>
                                        )}
                                    </div>

                                    {/* Trade list — only shown when active and no label selected */}
                                    {isExecutedStatus && !tradePickerLabel && (
                                        <div className="max-h-40 overflow-y-auto rounded-md border border-bg-subtle text-sm mt-1">
                                            {linkableTrades
                                                .filter((t) => {
                                                    if (!tradePickerSearch) return true
                                                    const label = `${formatTimestamp(t.time)} ${t.action} ${t.quantity}@${t.price} ${t.instrument}`.toLowerCase()
                                                    return label.includes(tradePickerSearch.toLowerCase())
                                                })
                                                .map((t) => {
                                                    const label = `${formatTimestamp(t.time)} — ${t.action} ${t.quantity}@${t.price}`
                                                    const isSelected = (linkedTradeId || form.linked_trade_id) === t.exec_id
                                                    return (
                                                        <div
                                                            key={t.exec_id}
                                                            role="option"
                                                            aria-selected={isSelected}
                                                            data-testid={`trade-option-${t.exec_id}`}
                                                            onClick={() => {
                                                                setLinkedTradeId(t.exec_id)
                                                                setTradePickerLabel(label)  // MEU-70b: populate input with label
                                                                setTradePickerSearch('')
                                                                updateField('linked_trade_id', t.exec_id)
                                                            }}
                                                            className={`px-3 py-1.5 cursor-pointer transition-colors flex items-center gap-2 ${isSelected ? 'bg-accent/20 text-fg font-medium' : 'text-fg hover:bg-bg-subtle'
                                                                }`}
                                                        >
                                                            {isSelected && <span className="text-accent text-xs">✓</span>}
                                                            {label}
                                                        </div>
                                                    )
                                                })}
                                            {linkableTrades.length === 0 && (
                                                <div className="px-3 py-1.5 text-fg-muted">No trades found for {planTicker}</div>
                                            )}
                                        </div>
                                    )}
                                </div>
                            )}

                            {/* Action Buttons (G1: borders, G2: disabled destructive on new) */}
                            <div className="flex gap-2 pt-3 border-t border-bg-subtle">
                                <button
                                    data-testid="plan-save-btn"
                                    onClick={() => handleSave().catch(() => { /* validation errors already rendered inline */ })}
                                    className={`px-4 py-1.5 text-sm rounded-md bg-accent text-accent-fg hover:bg-accent/90 border border-accent cursor-pointer${isDirty ? ' btn-save-dirty' : ''}`}
                                >
                                    {isCreating ? 'Create Plan' : (isDirty ? 'Save Changes •' : 'Save Changes')}
                                </button>
                                {selectedPlan && !isCreating && (
                                    <button
                                        data-testid="plan-delete-btn"
                                        onClick={handleDelete}
                                        className="px-4 py-1.5 text-sm rounded-md bg-red-500/10 text-red-400 border border-red-500/20 hover:bg-red-500/20 cursor-pointer"
                                    >
                                        Delete
                                    </button>
                                )}
                                <button
                                    onClick={handleClose}
                                    className="px-4 py-1.5 text-sm rounded-md bg-bg text-fg-muted hover:text-fg border border-bg-subtle cursor-pointer"
                                >
                                    Cancel
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>

            <UnsavedChangesModal
                open={showModal}
                onCancel={handleCancel}
                onDiscard={handleDiscard}
                onSave={handleSaveAndContinue}
                isSaveDisabled={isSaveDisabled}
            />

            {deleteConfirm.target && (
                <ConfirmDeleteModal
                    open={deleteConfirm.showModal}
                    target={deleteConfirm.target}
                    onCancel={deleteConfirm.handleCancel}
                    onConfirm={deleteConfirm.handleConfirm}
                />
            )}

            {/* MEU-201: Bulk delete confirmation */}
            <ConfirmDeleteModal
                open={showBulkConfirm}
                target={{ count: selectedIds.size, type: selectedIds.size === 1 ? 'trade plan' : 'trade plans' }}
                onCancel={() => setShowBulkConfirm(false)}
                onConfirm={handleBulkDelete}
            />
        </>
    )
}
