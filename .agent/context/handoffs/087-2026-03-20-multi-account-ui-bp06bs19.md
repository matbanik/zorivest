---
meu: 54
slug: multi-account-ui
phase: 6B
priority: P1
status: ready_for_review
agent: claude-opus-4-6
iteration: 1
files_changed: 4
tests_added: 9
tests_passing: 9
---

# MEU-54: Multi-Account UI

## Scope

Adds per-trade account identification to the Trades GUI: an `AccountTypeBadge` chip on every row in `TradesTable.tsx`, a truncation rule for long account names (≥15 chars), and an account filter dropdown in `TradesLayout.tsx` that fetches available accounts and passes `account_id` as a query param to `GET /api/v1/trades`.

Build plan reference: [06b-gui-trades.md](../../../../docs/build-plan/06b-gui-trades.md) §19

## Feature Intent Contract

### Intent Statement
Users can identify which account each trade belongs to at a glance via a colored badge, filter the trades list to a single account, and always see account names truncated to a readable length regardless of how long the underlying name is.

### Acceptance Criteria
- AC-1 (Source: 06b-gui-trades.md §19): `AccountTypeBadge` renders color-coded chips for account types: `broker`=blue, `ira`=green, `401k`=purple, `custom`=gray. Case-insensitive matching.
- AC-2 (Source: 06b-gui-trades.md §19): Account column shows badge + name, truncated at 15 characters with CSS `truncate` class.
- AC-3 (Source: 06b-gui-trades.md §19): Filter dropdown fetches `GET /api/v1/accounts` and renders one option per account. "All Accounts" resets filter.
- AC-4 (Source: 06b-gui-trades.md §19): Selecting an account in the dropdown passes `account_id` to the `GET /api/v1/trades` query. Changing filter triggers refetch.
- AC-5 (Source: Local Canon — G7/G5 in emerging-standards.md): `refetchInterval: 5_000` on all queries. Filter state persists via `useState`.

### Negative Cases
- Must NOT: show badge when `account_type` is undefined/null (badge is suppressed)
- Must NOT: send invalid `account_id` if "All Accounts" is selected (param omitted)

### Test Mapping
| Criterion | Test File | Test Function |
|-----------|-----------|---------------|
| AC-1 badge colors | `trades.test.tsx` | `AccountTypeBadge > renders broker badge` / `ira` / `401k` / `custom` |
| AC-1 case-insensitive | `trades.test.tsx` | `AccountTypeBadge > handles uppercase` |
| AC-3 filter dropdown | `trades.test.tsx` | `Account filter > renders account options` |
| AC-4 re-query on filter | `trades.test.tsx` | `Account filter > re-queries on filter change` |

## Design Decisions & Known Risks

- **Decision**: Badge implemented as a standalone `AccountTypeBadge.tsx` component — **Reasoning**: Follows the established pattern for `ConvictionIndicator`; testable in isolation and reusable. **ADR**: inline.
- **Decision**: Filter dropdown placed in `TradesLayout.tsx` header alongside existing controls — **Reasoning**: Consistent with how account filter is positioned in spec §19. **ADR**: inline.
- **Source Basis**: `docs/build-plan/06b-gui-trades.md §19`; `ui/src/renderer/src/features/trades/TradesTable.tsx`
- **Risk**: `account_type` values are free-string from the API. Badge defaults to gray `custom` style for unrecognized types — consistent fallback.

## Changed Files

| File | Action | Description |
|------|--------|-------------|
| `ui/src/renderer/src/features/trades/AccountTypeBadge.tsx` | Created | Color-coded badge component for trade account types |
| `ui/src/renderer/src/features/trades/TradesTable.tsx` | Modified | Import `AccountTypeBadge`, render in account column with truncation |
| `ui/src/renderer/src/features/trades/TradesLayout.tsx` | Modified | Add account filter dropdown with `GET /api/v1/accounts`, pass `account_id` to trades query |
| `ui/src/renderer/src/features/trades/__tests__/trades.test.tsx` | Modified | Added 9 tests: badge rendering (5), filter dropdown (1), re-query (1), truncation (1), null suppression (1) |

## Commands Executed

| Command | Result | Notes |
|---------|--------|-------|
| `npx vitest run src/renderer/src/features/trades` | PASS | All trades tests pass |
| `npx vitest run` | PASS (15 files) | Full regression — no regressions |
| `npx tsc --noEmit` | PASS | 0 errors |

## FAIL_TO_PASS Evidence

| Test | Before | After |
|------|--------|-------|
| `AccountTypeBadge > renders broker badge` | FAIL (component didn't exist) | PASS |
| `AccountTypeBadge > renders ira badge` | FAIL (component didn't exist) | PASS |
| `Account filter > renders account options` | FAIL (feature didn't exist) | PASS |
| `Account filter > re-queries on filter change` | FAIL (feature didn't exist) | PASS |

---
## Codex Validation Report
{Left blank — Codex fills this section during validation-review workflow}
