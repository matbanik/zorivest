/**
 * TaxProfileManager — Watchlist-style CRUD for multi-year Tax Profiles.
 *
 * Layout: Left sidebar (year card list + search + bulk-delete) | Right detail panel (form).
 * Pattern: Mirrors WatchlistPage.tsx exactly (MEU-218f).
 *
 * Source: implementation-plan.md §MEU-218f
 * API: GET/POST /api/v1/tax/profiles, GET/PUT/DELETE /api/v1/tax/profiles/{year}
 */

import { useState, useCallback, useMemo } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { apiFetch } from '@/lib/api'
import { useStatusBar } from '@/hooks/useStatusBar'
import { useConfirmDelete } from '@/hooks/useConfirmDelete'
import ConfirmDeleteModal from '@/components/ConfirmDeleteModal'
import SelectionCheckbox from '@/components/SelectionCheckbox'
import BulkActionBar from '@/components/BulkActionBar'
import { TAX_TEST_IDS } from './test-ids'
import TaxHelpCard from './TaxHelpCard'
import { TAX_HELP } from './tax-help-content'

// ── Types ────────────────────────────────────────────────────────────

interface TaxProfile {
    id: number
    tax_year: number
    filing_status: string
    federal_bracket: number
    state_tax_rate: number
    state: string
    prior_year_tax: number
    agi_estimate: number
    capital_loss_carryforward: number
    wash_sale_method: string
    default_cost_basis: string
    include_drip_wash_detection: boolean
    include_spousal_accounts: boolean
    section_475_elected: boolean
    section_1256_eligible: boolean
}

const FILING_STATUSES = [
    { value: 'SINGLE', label: 'Single' },
    { value: 'MARRIED_JOINT', label: 'Married Filing Jointly' },
    { value: 'MARRIED_SEPARATE', label: 'Married Filing Separately' },
    { value: 'HEAD_OF_HOUSEHOLD', label: 'Head of Household' },
]

const WASH_METHODS = [
    { value: 'CONSERVATIVE', label: 'Conservative' },
    { value: 'AGGRESSIVE', label: 'Aggressive' },
]

const COST_BASIS_METHODS = [
    { value: 'FIFO', label: 'FIFO (First In, First Out)' },
    { value: 'LIFO', label: 'LIFO (Last In, First Out)' },
    { value: 'HIFO', label: 'HIFO (Highest In, First Out)' },
    { value: 'SPEC_ID', label: 'Specific Identification' },
    { value: 'MAX_LT_GAIN', label: 'Max Long-Term Gain' },
    { value: 'MAX_LT_LOSS', label: 'Max Long-Term Loss' },
    { value: 'MAX_ST_GAIN', label: 'Max Short-Term Gain' },
    { value: 'MAX_ST_LOSS', label: 'Max Short-Term Loss' },
]

const DEFAULT_FORM: Omit<TaxProfile, 'id'> = {
    tax_year: new Date().getFullYear(),
    filing_status: 'SINGLE',
    federal_bracket: 0.24,
    state_tax_rate: 0.05,
    state: 'NJ',
    prior_year_tax: 0,
    agi_estimate: 0,
    capital_loss_carryforward: 0,
    wash_sale_method: 'CONSERVATIVE',
    default_cost_basis: 'FIFO',
    include_drip_wash_detection: true,
    include_spousal_accounts: false,
    section_475_elected: false,
    section_1256_eligible: false,
}

// ── Component ────────────────────────────────────────────────────────

export default function TaxProfileManager() {
    const [selectedProfile, setSelectedProfile] = useState<TaxProfile | null>(null)
    const [isCreating, setIsCreating] = useState(false)
    const [form, setForm] = useState<Omit<TaxProfile, 'id'>>(DEFAULT_FORM)
    const queryClient = useQueryClient()
    const { setStatus } = useStatusBar()

    // Sidebar state
    const [sidebarSearch, setSidebarSearch] = useState('')
    const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set())
    const [showBulkConfirm, setShowBulkConfirm] = useState(false)

    // Fetch all profiles
    const { data: profiles = [] } = useQuery<TaxProfile[]>({
        queryKey: ['tax-profiles'],
        queryFn: async () => {
            try {
                return await apiFetch<TaxProfile[]>('/api/v1/tax/profiles')
            } catch {
                return []
            }
        },
        refetchInterval: 10_000,
    })

    // Filtered list
    const filteredProfiles = useMemo(() => {
        if (!sidebarSearch.trim()) return profiles
        const q = sidebarSearch.toLowerCase()
        return profiles.filter((p) =>
            String(p.tax_year).includes(q) ||
            p.filing_status.toLowerCase().includes(q) ||
            p.state.toLowerCase().includes(q)
        )
    }, [profiles, sidebarSearch])

    // Selection handlers
    const toggleSelect = useCallback((id: number) => {
        setSelectedIds((prev) => {
            const next = new Set(prev)
            if (next.has(id)) next.delete(id)
            else next.add(id)
            return next
        })
    }, [])

    const toggleSelectAll = useCallback(() => {
        setSelectedIds((prev) => {
            if (prev.size === filteredProfiles.length && prev.size > 0) return new Set()
            return new Set(filteredProfiles.map((p) => p.id))
        })
    }, [filteredProfiles])

    // Handlers
    const handleSelect = useCallback((profile: TaxProfile) => {
        setSelectedProfile(profile)
        setIsCreating(false)
        setForm({
            tax_year: profile.tax_year,
            filing_status: profile.filing_status,
            federal_bracket: profile.federal_bracket,
            state_tax_rate: profile.state_tax_rate,
            state: profile.state,
            prior_year_tax: profile.prior_year_tax,
            agi_estimate: profile.agi_estimate,
            capital_loss_carryforward: profile.capital_loss_carryforward,
            wash_sale_method: profile.wash_sale_method,
            default_cost_basis: profile.default_cost_basis,
            include_drip_wash_detection: profile.include_drip_wash_detection,
            include_spousal_accounts: profile.include_spousal_accounts,
            section_475_elected: profile.section_475_elected,
            section_1256_eligible: profile.section_1256_eligible,
        })
    }, [])

    const handleNew = useCallback(() => {
        setSelectedProfile(null)
        setIsCreating(true)
        setForm({ ...DEFAULT_FORM, tax_year: new Date().getFullYear() })
    }, [])

    const handleClose = useCallback(() => {
        setSelectedProfile(null)
        setIsCreating(false)
    }, [])

    const handleSave = useCallback(async () => {
        try {
            if (isCreating) {
                setStatus('Creating tax profile...')
                await apiFetch('/api/v1/tax/profiles', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(form),
                })
                setStatus(`Tax profile for ${form.tax_year} created`)
            } else if (selectedProfile) {
                setStatus('Updating tax profile...')
                await apiFetch(`/api/v1/tax/profiles/${selectedProfile.tax_year}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(form),
                })
                setStatus(`Tax profile for ${selectedProfile.tax_year} updated`)
            }
            await queryClient.invalidateQueries({ queryKey: ['tax-profiles'] })
            handleClose()
        } catch (err) {
            const msg = err instanceof Error ? err.message : 'Failed'
            setStatus(`Error: ${msg}`)
        }
    }, [isCreating, selectedProfile, form, queryClient, setStatus, handleClose])

    // Delete single
    const deleteConfirm = useConfirmDelete()
    const handleDelete = useCallback(() => {
        if (!selectedProfile) return
        deleteConfirm.confirmSingle('tax profile', String(selectedProfile.tax_year), async () => {
            try {
                setStatus('Deleting tax profile...')
                await apiFetch(`/api/v1/tax/profiles/${selectedProfile.tax_year}`, { method: 'DELETE' })
                setStatus(`Tax profile for ${selectedProfile.tax_year} deleted`)
                await queryClient.invalidateQueries({ queryKey: ['tax-profiles'] })
                handleClose()
            } catch (err) {
                setStatus(`Error: ${err instanceof Error ? err.message : 'Failed'}`)
            }
        })
    }, [selectedProfile, deleteConfirm, queryClient, setStatus, handleClose])

    // Bulk delete
    const handleBulkDelete = useCallback(async () => {
        const years = profiles.filter((p) => selectedIds.has(p.id)).map((p) => p.tax_year)
        for (const year of years) {
            await apiFetch(`/api/v1/tax/profiles/${year}`, { method: 'DELETE' })
        }
        setSelectedIds(new Set())
        setShowBulkConfirm(false)
        await queryClient.invalidateQueries({ queryKey: ['tax-profiles'] })
        setSelectedProfile(null)
        setStatus(`${years.length} profile(s) deleted`)
    }, [selectedIds, profiles, queryClient, setStatus])

    const updateField = useCallback(<K extends keyof Omit<TaxProfile, 'id'>>(
        key: K,
        value: Omit<TaxProfile, 'id'>[K],
    ) => {
        setForm((prev) => ({ ...prev, [key]: value }))
    }, [])

    const isDetailOpen = isCreating || selectedProfile !== null

    return (
        <>
            <div data-testid={TAX_TEST_IDS.PROFILE_MANAGER} className="flex flex-col h-full">
                <div className="px-4 pt-4">
                    <TaxHelpCard content={TAX_HELP.profiles} />
                </div>
                <div className="flex flex-1 min-h-0">
                {/* Left: Profile List */}
                <div className={`flex-1 min-w-0 transition-all ${isDetailOpen ? 'w-[35%]' : 'w-full'}`}>
                    <div className="p-4">
                        <div className="flex items-center justify-between mb-4">
                            <h2 className="text-lg font-semibold text-fg">Tax Profiles</h2>
                            <button
                                data-testid={TAX_TEST_IDS.PROFILE_NEW_BTN}
                                onClick={handleNew}
                                className="px-4 py-1.5 text-sm font-medium rounded-md border border-bg-subtle bg-bg hover:bg-bg-elevated text-fg transition-colors cursor-pointer"
                            >
                                + New Profile
                            </button>
                        </div>

                        {/* Search */}
                        <div className="mb-3">
                            <input
                                data-testid={TAX_TEST_IDS.PROFILE_SEARCH}
                                type="text"
                                value={sidebarSearch}
                                onChange={(e) => setSidebarSearch(e.target.value)}
                                placeholder="Search by year, status, state…"
                                aria-label="Search tax profiles"
                                className="w-full px-3 py-1.5 text-sm rounded-md bg-bg border border-bg-subtle text-fg placeholder:text-fg-muted/50"
                            />
                        </div>

                        {/* Select-all */}
                        {filteredProfiles.length > 0 && (
                            <div className="flex items-center gap-2 mb-2">
                                <SelectionCheckbox
                                    checked={selectedIds.size === filteredProfiles.length && filteredProfiles.length > 0}
                                    indeterminate={selectedIds.size > 0 && selectedIds.size < filteredProfiles.length}
                                    onChange={toggleSelectAll}
                                    ariaLabel="Select all profiles"
                                />
                                <span className="text-xs text-fg-muted">Select all</span>
                            </div>
                        )}

                        {/* Bulk action bar */}
                        {selectedIds.size > 0 && (
                            <BulkActionBar
                                selectedCount={selectedIds.size}
                                entityLabel="profile"
                                onDelete={() => setShowBulkConfirm(true)}
                                onClearSelection={() => setSelectedIds(new Set())}
                            />
                        )}

                        {/* Profile cards */}
                        <div className="space-y-2" data-testid={TAX_TEST_IDS.PROFILE_LIST} aria-label="Tax profiles">
                            {filteredProfiles.length === 0 && (
                                <p className="text-sm text-fg-muted py-4 text-center">No tax profiles yet</p>
                            )}
                            {filteredProfiles.map((p) => (
                                <button
                                    key={p.id}
                                    data-testid={`${TAX_TEST_IDS.PROFILE_CARD}-${p.tax_year}`}
                                    onClick={() => handleSelect(p)}
                                    className={`w-full text-left px-4 py-3 rounded-md border cursor-pointer transition-colors ${
                                        selectedProfile?.id === p.id
                                            ? 'border-accent bg-accent/10'
                                            : 'border-bg-subtle bg-bg hover:bg-bg-elevated'
                                    }`}
                                    aria-current={selectedProfile?.id === p.id ? 'true' : undefined}
                                >
                                    <div className="flex items-center gap-2">
                                        <span onClick={(e) => e.stopPropagation()}>
                                            <SelectionCheckbox
                                                checked={selectedIds.has(p.id)}
                                                onChange={() => toggleSelect(p.id)}
                                                ariaLabel={`Select ${p.tax_year}`}
                                            />
                                        </span>
                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-center justify-between">
                                                <span className="font-medium text-fg text-base">{p.tax_year}</span>
                                                <span className="text-xs text-fg-muted">
                                                    {FILING_STATUSES.find((f) => f.value === p.filing_status)?.label ?? p.filing_status}
                                                </span>
                                            </div>
                                            <div className="text-xs text-fg-muted mt-1">
                                                {p.state} · {(p.federal_bracket * 100).toFixed(0)}% Fed · {(p.state_tax_rate * 100).toFixed(1)}% State · AGI ${p.agi_estimate.toLocaleString()}
                                            </div>
                                        </div>
                                    </div>
                                </button>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Right: Detail Panel */}
                {isDetailOpen && (
                    <div className="w-[65%] border-l border-bg-subtle overflow-y-auto" data-testid={TAX_TEST_IDS.PROFILE_DETAIL} aria-label="Tax profile details">
                        <div className="p-4">
                            <div className="flex items-center justify-between mb-4">
                                <h3 className="text-md font-semibold text-fg">
                                    {isCreating ? 'New Tax Profile' : `Tax Year ${selectedProfile?.tax_year}`}
                                </h3>
                                <button
                                    onClick={handleClose}
                                    aria-label="Close detail panel"
                                    className="text-fg-muted hover:text-fg cursor-pointer"
                                >
                                    ✕
                                </button>
                            </div>

                            {/* ── Form sections ──────────────────────────── */}
                            <div className="space-y-5">

                                {/* Section 1: General */}
                                <fieldset className="border border-bg-subtle rounded-lg p-4">
                                    <legend className="text-xs font-semibold text-fg-muted px-2 uppercase tracking-wider">General</legend>
                                    <div className="grid grid-cols-2 gap-3 mt-2">
                                        <div>
                                            <label className="block text-xs text-fg-muted mb-1">Tax Year</label>
                                            <input
                                                data-testid={TAX_TEST_IDS.PROFILE_YEAR_INPUT}
                                                type="number"
                                                min={2020}
                                                max={2030}
                                                value={form.tax_year}
                                                onChange={(e) => updateField('tax_year', Number(e.target.value))}
                                                disabled={!isCreating}
                                                className="w-full px-3 py-1.5 text-sm rounded-md bg-bg border border-bg-subtle text-fg disabled:opacity-50"
                                            />
                                        </div>
                                        <div>
                                            <label className="block text-xs text-fg-muted mb-1">Filing Status</label>
                                            <select
                                                value={form.filing_status}
                                                onChange={(e) => updateField('filing_status', e.target.value)}
                                                className="w-full px-3 py-1.5 text-sm rounded-md bg-bg border border-bg-subtle text-fg cursor-pointer"
                                            >
                                                {FILING_STATUSES.map((fs) => (
                                                    <option key={fs.value} value={fs.value}>{fs.label}</option>
                                                ))}
                                            </select>
                                        </div>
                                    </div>
                                </fieldset>

                                {/* Section 2: Tax Rates */}
                                <fieldset className="border border-bg-subtle rounded-lg p-4">
                                    <legend className="text-xs font-semibold text-fg-muted px-2 uppercase tracking-wider">Tax Rates</legend>
                                    <div className="grid grid-cols-3 gap-3 mt-2">
                                        <div>
                                            <label className="block text-xs text-fg-muted mb-1">Federal Bracket (%)</label>
                                            <input
                                                type="number"
                                                step="0.01"
                                                min="0"
                                                max="100"
                                                value={(form.federal_bracket * 100).toFixed(1)}
                                                onChange={(e) => updateField('federal_bracket', Number(e.target.value) / 100)}
                                                className="w-full px-3 py-1.5 text-sm rounded-md bg-bg border border-bg-subtle text-fg"
                                            />
                                        </div>
                                        <div>
                                            <label className="block text-xs text-fg-muted mb-1">State Tax Rate (%)</label>
                                            <input
                                                type="number"
                                                step="0.01"
                                                min="0"
                                                max="100"
                                                value={(form.state_tax_rate * 100).toFixed(1)}
                                                onChange={(e) => updateField('state_tax_rate', Number(e.target.value) / 100)}
                                                className="w-full px-3 py-1.5 text-sm rounded-md bg-bg border border-bg-subtle text-fg"
                                            />
                                        </div>
                                        <div>
                                            <label className="block text-xs text-fg-muted mb-1">State (2-letter)</label>
                                            <input
                                                type="text"
                                                maxLength={2}
                                                value={form.state}
                                                onChange={(e) => updateField('state', e.target.value.toUpperCase())}
                                                className="w-full px-3 py-1.5 text-sm rounded-md bg-bg border border-bg-subtle text-fg uppercase"
                                            />
                                        </div>
                                    </div>
                                </fieldset>

                                {/* Section 3: Income */}
                                <fieldset className="border border-bg-subtle rounded-lg p-4">
                                    <legend className="text-xs font-semibold text-fg-muted px-2 uppercase tracking-wider">Income & Prior Year</legend>
                                    <div className="grid grid-cols-2 gap-3 mt-2">
                                        <div>
                                            <label className="block text-xs text-fg-muted mb-1">AGI Estimate ($)</label>
                                            <input
                                                type="number"
                                                min="0"
                                                value={form.agi_estimate}
                                                onChange={(e) => updateField('agi_estimate', Number(e.target.value))}
                                                className="w-full px-3 py-1.5 text-sm rounded-md bg-bg border border-bg-subtle text-fg"
                                            />
                                        </div>
                                        <div>
                                            <label className="block text-xs text-fg-muted mb-1">Prior Year Tax ($)</label>
                                            <input
                                                type="number"
                                                min="0"
                                                value={form.prior_year_tax}
                                                onChange={(e) => updateField('prior_year_tax', Number(e.target.value))}
                                                className="w-full px-3 py-1.5 text-sm rounded-md bg-bg border border-bg-subtle text-fg"
                                            />
                                        </div>
                                    </div>
                                </fieldset>

                                {/* Section 4: Loss Tracking */}
                                <fieldset className="border border-bg-subtle rounded-lg p-4">
                                    <legend className="text-xs font-semibold text-fg-muted px-2 uppercase tracking-wider">Loss Tracking</legend>
                                    <div className="mt-2">
                                        <label className="block text-xs text-fg-muted mb-1">Capital Loss Carryforward ($)</label>
                                        <input
                                            type="number"
                                            min="0"
                                            value={form.capital_loss_carryforward}
                                            onChange={(e) => updateField('capital_loss_carryforward', Number(e.target.value))}
                                            className="w-full px-3 py-1.5 text-sm rounded-md bg-bg border border-bg-subtle text-fg"
                                        />
                                    </div>
                                </fieldset>

                                {/* Section 5: Methods */}
                                <fieldset className="border border-bg-subtle rounded-lg p-4">
                                    <legend className="text-xs font-semibold text-fg-muted px-2 uppercase tracking-wider">Methods</legend>
                                    <div className="grid grid-cols-2 gap-3 mt-2">
                                        <div>
                                            <label className="block text-xs text-fg-muted mb-1">Wash Sale Method</label>
                                            <select
                                                value={form.wash_sale_method}
                                                onChange={(e) => updateField('wash_sale_method', e.target.value)}
                                                className="w-full px-3 py-1.5 text-sm rounded-md bg-bg border border-bg-subtle text-fg cursor-pointer"
                                            >
                                                {WASH_METHODS.map((m) => (
                                                    <option key={m.value} value={m.value}>{m.label}</option>
                                                ))}
                                            </select>
                                        </div>
                                        <div>
                                            <label className="block text-xs text-fg-muted mb-1">Default Cost Basis</label>
                                            <select
                                                value={form.default_cost_basis}
                                                onChange={(e) => updateField('default_cost_basis', e.target.value)}
                                                className="w-full px-3 py-1.5 text-sm rounded-md bg-bg border border-bg-subtle text-fg cursor-pointer"
                                            >
                                                {COST_BASIS_METHODS.map((m) => (
                                                    <option key={m.value} value={m.value}>{m.label}</option>
                                                ))}
                                            </select>
                                        </div>
                                    </div>
                                </fieldset>

                                {/* Section 6: Elections */}
                                <fieldset className="border border-bg-subtle rounded-lg p-4">
                                    <legend className="text-xs font-semibold text-fg-muted px-2 uppercase tracking-wider">Elections & Detection</legend>
                                    <div className="grid grid-cols-2 gap-3 mt-2">
                                        {[
                                            { key: 'include_drip_wash_detection' as const, label: 'DRIP Wash Sale Detection' },
                                            { key: 'include_spousal_accounts' as const, label: 'Include Spousal Accounts' },
                                            { key: 'section_475_elected' as const, label: 'Section 475 (Mark-to-Market)' },
                                            { key: 'section_1256_eligible' as const, label: 'Section 1256 (Futures 60/40)' },
                                        ].map(({ key, label }) => (
                                            <label key={key} className="flex items-center gap-2 text-sm text-fg cursor-pointer">
                                                <input
                                                    type="checkbox"
                                                    checked={form[key]}
                                                    onChange={(e) => updateField(key, e.target.checked)}
                                                    className="rounded border-bg-subtle cursor-pointer"
                                                />
                                                {label}
                                            </label>
                                        ))}
                                    </div>
                                </fieldset>
                            </div>

                            {/* Action buttons */}
                            <div className="flex gap-2 mt-5">
                                <button
                                    data-testid={TAX_TEST_IDS.PROFILE_SAVE_BTN}
                                    onClick={handleSave}
                                    className="px-4 py-1.5 text-sm rounded-md bg-accent text-accent-fg hover:bg-accent/90 border border-accent cursor-pointer"
                                >
                                    {isCreating ? 'Create' : 'Save Changes'}
                                </button>
                                {selectedProfile && !isCreating && (
                                    <button
                                        data-testid={TAX_TEST_IDS.PROFILE_DELETE_BTN}
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
                )}
                </div>
            </div>

            {/* Delete confirmation modals */}
            {deleteConfirm.target && (
                <ConfirmDeleteModal
                    open={deleteConfirm.showModal}
                    target={deleteConfirm.target}
                    onCancel={deleteConfirm.handleCancel}
                    onConfirm={deleteConfirm.handleConfirm}
                />
            )}

            <ConfirmDeleteModal
                open={showBulkConfirm}
                target={{ count: selectedIds.size, type: selectedIds.size === 1 ? 'profile' : 'profiles' }}
                onCancel={() => setShowBulkConfirm(false)}
                onConfirm={handleBulkDelete}
            />
        </>
    )
}
