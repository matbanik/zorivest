# Handoff: Account GUI Refinements (Session 2)

**Date:** 2026-03-28
**MEU:** MEU-71a (`account-gui`) — continuation
**Build Plan:** [06d §35a.1](../../docs/build-plan/06d-gui-accounts.md)
**Previous Handoff:** [094](094-2026-03-27-account-gui-bp06ds35a1.md)

## Summary

Follow-up refinements to Account Management GUI per user feedback. Replaced redundant Actions column with Portfolio %, enlarged portfolio summary with account count, fixed Start Review wizard stripe bug, added Cancel button to wizard, commented out Currency dropdown (deferred), and documented Account CRUD MCP tools for MEU-37.

## Files Changed

| File | Action | Description |
|------|--------|-------------|
| `ui/src/renderer/src/features/accounts/AccountsHome.tsx` | MODIFY | Replaced Actions column with Portfolio % column; enlarged portfolio summary to `text-sm font-semibold` with account count; removed redundant `Select`/`Delete` buttons from `AccountRow` |
| `ui/src/renderer/src/features/accounts/AccountReviewWizard.tsx` | MODIFY | Fixed stripe bug: added `min-h-[250px]` + fixed `w-[480px]`; added Cancel button to step view header; added backdrop click-to-close with `stopPropagation`; replaced `null` empty state with "No accounts to review" fallback |
| `ui/src/renderer/src/features/accounts/AccountDetailPanel.tsx` | MODIFY | Commented out Currency dropdown with explicit deferral note — multi-currency requires coordinated planning after full GUI build |
| `ui/tests/e2e/test-ids.ts` | MODIFY | Renamed `SELECT_BTN` → `PORTFOLIO_PCT` |
| `docs/build-plan/05f-mcp-accounts.md` | NEW | 5 Account CRUD tool specs (list, get, create, update, record_balance) |
| `docs/build-plan/mcp-tool-index.md` | MODIFY | Added 5 account CRUD tools, updated counts (8→13) |
| `docs/build-plan/05-mcp-server.md` | MODIFY | Updated hub file counts and toolset table |
| `docs/BUILD_PLAN.md` | MODIFY | MEU-37 status → 🔴 changes_required |
| `.agent/context/meu-registry.md` | MODIFY | MEU-37 status → 🔴 changes_required |

## Key Decisions

1. **Portfolio % over Actions:** User confirmed row-click selection makes the Actions column redundant. Portfolio % provides better data visibility.
2. **Currency Deferred:** $ symbol and USD are hardcoded throughout GUI (`Intl.NumberFormat`, portfolio totals, balance displays). Multi-currency needs a dedicated planning phase covering dynamic formatting, FX rates, and portfolio aggregation. DB column `AccountModel.currency` (String(3), default USD) is ready.
3. **MCP Account CRUD:** 5 tools documented for MEU-37 (extends existing `accounts` toolset from 8→13 tools). Not yet implemented — awaiting Codex review.
4. **Wizard stripe fix:** Root cause was empty modal container rendering as a bordered div with no content. Fixed with explicit min dimensions, empty-state fallback, and backdrop dismiss.

## Remaining Work

- **Start Review wizard** still shows a stripe in some scenarios — needs further investigation if `w-[480px] min-h-[250px]` fix doesn't resolve. The backdrop-click-to-close is confirmed working.
- **Unit tests** for `AccountsHome.test.tsx` may need update for Portfolio % column assertions (no `Select` button test existed, so no test breakage expected).
- **MEU-37 MCP implementation** blocked on Codex review of expanded tool specs.
