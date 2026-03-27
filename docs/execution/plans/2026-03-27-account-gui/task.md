# MEU-71a: Account Management GUI

## Implementation

- [ ] 1. Write FIC tests for `AccountContext` (AC-14)
- [ ] 2. Implement `AccountContext.tsx` — global account selection provider
- [ ] 3. Extend `Account` interface in `useAccounts.ts` — add full `AccountResponse` fields
- [ ] 4. Add mutation hooks (`useCreateAccount`, `useUpdateAccount`, `useDeleteAccount`, `useBalanceHistory`)
- [ ] 5. Write FIC tests for `AccountsHome` (AC-1, AC-2, AC-3, AC-4, AC-15)
- [ ] 6. Implement `AccountsHome.tsx` — MRU cards, All Accounts table, split layout
- [ ] 7. Write FIC tests for `AccountDetailPanel` (AC-5, AC-6, AC-7, AC-8)
- [ ] 8. Implement `AccountDetailPanel.tsx` — CRUD form, save/delete/balance update
- [ ] 9. Write FIC tests for `BalanceHistory` (AC-9)
- [ ] 10. Implement `BalanceHistory.tsx` — sparkline chart + scrollable table
- [ ] 11. Write FIC tests for `AccountReviewWizard` (AC-10, AC-11, AC-12, AC-13)
- [ ] 12. Implement `AccountReviewWizard.tsx` — multi-step wizard dialog
- [ ] 13. Run `npx tsc --noEmit` — verify zero type errors
- [ ] 14. Run full Vitest suite — verify all new tests pass
- [ ] 15. Run MEU gate: `uv run python tools/validate_codebase.py --scope meu`

## Post-MEU Deliverables

- [ ] 16. Update `BUILD_PLAN.md` — MEU-71a status ⏸ → ✅
- [ ] 17. Update `meu-registry.md` — add MEU-71a entry
- [ ] 18. Create handoff: `007-2026-03-27-account-gui-bp06ds35a1.md`
- [ ] 19. Prepare commit messages
- [ ] 20. Save session to `pomera_notes`
