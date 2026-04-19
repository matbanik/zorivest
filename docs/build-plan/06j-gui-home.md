# Phase 6j: GUI — Home Dashboard

> Part of [Phase 6: GUI](06-gui.md) | Prerequisites: [Phase 3](03-service-layer.md) (DashboardService), [Phase 4](04-rest-api.md) (dashboard endpoints) | Optional WebSocket enhancement: [MEU-174](build-priority-matrix.md)

---

## Goal

Build the Home Dashboard — the **default startup route** (`/`). The Home Dashboard is a read-only aggregation page that summarizes the user's most important data across accounts, trades, plans, watchlists, and scheduled jobs. It orchestrates existing services without introducing new domain entities or repositories.

### Key UX Principles

1. **Instant perceived readiness** — Local database content (accounts, recent trades) loads immediately. External data (market prices, P&L) loads asynchronously with animated progress indicators.
2. **Progressive disclosure** — Content that takes longer to load is placed lower on the page, keeping the user's attention on fast-loading summaries (especially important for first-time users).
3. **User-configurable** — A Settings entry allows users to toggle, reorder, and disable dashboard sections.

---

## 6j.1: Dashboard Sections

| # | Section | Data Source | Existing Service | Load Priority |
|---|---------|------------|-----------------|:------------:|
| 1 | Account Summaries | Portfolio total, per-account balances | `AccountService.get_portfolio_total()` | 🟢 Instant |
| 2 | Active Trades | Open positions across accounts | `TradeService` (status=`OPEN` filter) | 🟢 Instant |
| 3 | Recent Trades | Last 10 executed trades (closed) | `TradeService` (date sort, limit 10) | 🟢 Instant |
| 4 | Plan Highlights | Active plans, high conviction entries | `TradePlanService` (status=`ACTIVE`) | 🟢 Instant |
| 5 | Watchlist Summary | Tickers with price changes | `WatchlistService` + `MarketDataService` | 🟡 Deferred |
| 6 | Upcoming Jobs | Next scheduled pipeline runs | `SchedulingService` (next_run query) | 🟢 Instant |

> **Load Priority**: 🟢 Instant = served from local SQLite, renders within 200ms. 🟡 Deferred = requires network calls (market data), placed lower on page with animated loading indicators.

---

## 6j.2: Service Layer Wiring

> The `DashboardService` is a **read-only aggregation service** — no new repositories, no write operations. It orchestrates existing services through the existing Unit of Work.

```python
# packages/core/src/zorivest_core/services/dashboard_service.py

from __future__ import annotations
from dataclasses import dataclass, field
from zorivest_core.ports.unit_of_work import UnitOfWork


@dataclass(frozen=True)
class DashboardAccountSummary:
    """Per-account summary for dashboard card."""
    account_id: str
    account_name: str
    account_type: str
    current_balance: float
    balance_change_pct: float | None  # vs prior snapshot


@dataclass(frozen=True)
class DashboardSummary:
    """Aggregate dashboard response."""
    portfolio_total: float
    accounts: list[DashboardAccountSummary]
    active_trade_count: int
    recent_trades: list[dict]  # Serialized Trade subset
    active_plan_count: int
    high_conviction_plans: list[dict]  # Serialized TradePlan subset
    upcoming_jobs: list[dict]  # Serialized next-run entries
    watchlist_tickers: int


class DashboardService:
    """Read-only aggregation service. No new repos — orchestrates existing services."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def get_account_summary(self, account_ids: list[str] | None = None) -> list[DashboardAccountSummary]:
        """Portfolio total + per-account balance cards."""
        with self._uow:
            accounts = self._uow.accounts.list_all()
            if account_ids:
                accounts = [a for a in accounts if a.id in account_ids]
            # ... aggregate balances
            return [
                DashboardAccountSummary(
                    account_id=a.id,
                    account_name=a.name,
                    account_type=a.account_type.value,
                    current_balance=a.current_balance,
                    balance_change_pct=None,  # Computed from latest vs prior snapshot
                )
                for a in accounts
            ]

    def get_active_trades(self) -> list[dict]:
        """Open positions across all accounts."""
        with self._uow:
            return self._uow.trades.list_by_status("OPEN")

    def get_recent_trades(self, limit: int = 10) -> list[dict]:
        """Last N executed trades (most recent first)."""
        with self._uow:
            return self._uow.trades.list_recent(limit=limit)

    def get_plan_highlights(self) -> dict:
        """Active plans + high conviction entries."""
        with self._uow:
            plans = self._uow.trade_plans.list_active()
            return {
                "active_count": len(plans),
                "high_conviction": [p for p in plans if getattr(p, 'conviction', None) in ('HIGH', 'VERY_HIGH')],
            }

    def get_upcoming_jobs(self, limit: int = 5) -> list[dict]:
        """Next scheduled pipeline runs."""
        with self._uow:
            return self._uow.policies.list_next_runs(limit=limit)
```

---

## 6j.3: REST API Endpoints

> Dashboard endpoints are granular (one per section) to support independent loading and user-configurable sections.

```
GET /api/v1/dashboard/accounts         → list[DashboardAccountSummary]
GET /api/v1/dashboard/active-trades    → list[TradeResponse]  (status=OPEN)
GET /api/v1/dashboard/recent-trades    → list[TradeResponse]  (limit=10)
GET /api/v1/dashboard/plan-highlights  → PlanHighlightsResponse
GET /api/v1/dashboard/watchlists       → WatchlistSummaryResponse
GET /api/v1/dashboard/upcoming-jobs    → list[UpcomingJobResponse]
```

**Router registration:**

```python
# packages/api/src/zorivest_api/routes/dashboard.py

from fastapi import APIRouter, Depends
from zorivest_api.dependencies import get_dashboard_service

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])

@router.get("/accounts")
async def get_account_summaries(svc=Depends(get_dashboard_service)):
    return svc.get_account_summary()

@router.get("/active-trades")
async def get_active_trades(svc=Depends(get_dashboard_service)):
    return svc.get_active_trades()

@router.get("/recent-trades")
async def get_recent_trades(limit: int = 10, svc=Depends(get_dashboard_service)):
    return svc.get_recent_trades(limit=limit)

@router.get("/plan-highlights")
async def get_plan_highlights(svc=Depends(get_dashboard_service)):
    return svc.get_plan_highlights()

@router.get("/watchlists")
async def get_watchlist_summary(svc=Depends(get_dashboard_service)):
    # Requires MarketDataService for price data
    ...

@router.get("/upcoming-jobs")
async def get_upcoming_jobs(limit: int = 5, svc=Depends(get_dashboard_service)):
    return svc.get_upcoming_jobs(limit=limit)
```

---

## 6j.4: React Component Architecture

### Page Structure

```
HomePage (/)
├── DashboardHeader (greeting, portfolio total, settings gear)
├── DashboardGrid (CSS Grid layout, user-reorderable)
│   ├── AccountSummaryCard[] → GET /dashboard/accounts
│   ├── ActiveTradesPanel → GET /dashboard/active-trades
│   ├── RecentTradesPanel → GET /dashboard/recent-trades
│   ├── PlanHighlightsPanel → GET /dashboard/plan-highlights
│   ├── WatchlistSummaryPanel → GET /dashboard/watchlists
│   └── UpcomingJobsPanel → GET /dashboard/upcoming-jobs
└── DashboardSettingsDrawer (toggle/reorder sections)
```

### Animated Loading States

```tsx
// ui/src/renderer/src/components/DashboardSkeleton.tsx

/**
 * Skeleton card with pulse animation for dashboard sections.
 * Shows immediately while data loads from local DB.
 * Transitions to data once TanStack Query resolves.
 */
export function DashboardSkeleton({ label }: { label: string }) {
  return (
    <div className="dashboard-card skeleton" data-testid={`dashboard-skeleton-${label}`}>
      <div className="skeleton-header">
        <div className="skeleton-bar w-32 h-4 animate-pulse" />
      </div>
      <div className="skeleton-body">
        <div className="skeleton-bar w-full h-6 animate-pulse" />
        <div className="skeleton-bar w-3/4 h-4 animate-pulse" />
        <div className="skeleton-bar w-1/2 h-4 animate-pulse" />
      </div>
    </div>
  );
}
```

### Data Hooks (TanStack Query)

```tsx
// ui/src/renderer/src/features/home/hooks/useDashboard.ts

import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';

export function useAccountSummary() {
  return useQuery({
    queryKey: ['dashboard', 'accounts'],
    queryFn: () => apiClient.get('/api/v1/dashboard/accounts'),
    staleTime: 0,  // Financial data — always fresh
  });
}

export function useActiveTrades() {
  return useQuery({
    queryKey: ['dashboard', 'active-trades'],
    queryFn: () => apiClient.get('/api/v1/dashboard/active-trades'),
    staleTime: 0,
  });
}

export function useRecentTrades(limit = 10) {
  return useQuery({
    queryKey: ['dashboard', 'recent-trades', limit],
    queryFn: () => apiClient.get(`/api/v1/dashboard/recent-trades?limit=${limit}`),
    staleTime: 0,
  });
}

export function usePlanHighlights() {
  return useQuery({
    queryKey: ['dashboard', 'plan-highlights'],
    queryFn: () => apiClient.get('/api/v1/dashboard/plan-highlights'),
    staleTime: 30_000,  // Plans change less frequently
  });
}

export function useUpcomingJobs(limit = 5) {
  return useQuery({
    queryKey: ['dashboard', 'upcoming-jobs', limit],
    queryFn: () => apiClient.get(`/api/v1/dashboard/upcoming-jobs?limit=${limit}`),
    staleTime: 30_000,
  });
}
```

---

## 6j.5: Dashboard Settings

> Part of **Settings** sidebar ([06f-gui-settings.md](06f-gui-settings.md)). Added as **§6f.11: Home Dashboard Settings**.

### Settings Schema

```python
# Dashboard settings stored via SettingsResolver (Phase 2A pattern)

DASHBOARD_DEFAULTS = {
    "dashboard.sections.account_summary.enabled": True,
    "dashboard.sections.account_summary.order": 1,
    "dashboard.sections.active_trades.enabled": True,
    "dashboard.sections.active_trades.order": 2,
    "dashboard.sections.recent_trades.enabled": True,
    "dashboard.sections.recent_trades.order": 3,
    "dashboard.sections.plan_highlights.enabled": True,
    "dashboard.sections.plan_highlights.order": 4,
    "dashboard.sections.watchlist_summary.enabled": True,
    "dashboard.sections.watchlist_summary.order": 5,
    "dashboard.sections.upcoming_jobs.enabled": True,
    "dashboard.sections.upcoming_jobs.order": 6,
}
```

### Settings GUI

```
┌──────────────────────────────────────────────────────────┐
│  Settings > Home Dashboard                                │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  Dashboard Sections                                      │
│  Drag to reorder. Toggle to show/hide.                   │
│                                                          │
│  ┌─ ≡ ─────────────────────────────────────────┐        │
│  │ ☰  Account Summaries           [✅ Enabled] │        │
│  ├──────────────────────────────────────────────┤        │
│  │ ☰  Active Trades               [✅ Enabled] │        │
│  ├──────────────────────────────────────────────┤        │
│  │ ☰  Recent Trades               [✅ Enabled] │        │
│  ├──────────────────────────────────────────────┤        │
│  │ ☰  Plan Highlights             [✅ Enabled] │        │
│  ├──────────────────────────────────────────────┤        │
│  │ ☰  Watchlist Summary           [✅ Enabled] │        │
│  ├──────────────────────────────────────────────┤        │
│  │ ☰  Upcoming Jobs               [✅ Enabled] │        │
│  └──────────────────────────────────────────────┘        │
│                                                          │
│  [Reset to Default]                                      │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

**Implementation notes:**
- Drag-to-reorder uses `@dnd-kit/core` + `@dnd-kit/sortable` (already available via shadcn/ui)
- Settings persisted via `PUT /api/v1/settings` (existing endpoint)
- React component: `DashboardSettingsPage` in `ui/src/renderer/src/features/settings/DashboardSettingsPage.tsx`

---

## 6j.6: Navigation Rail Update

The Home Dashboard becomes the **first item** in the navigation rail, shifting Accounts to 2nd position:

| Position | Icon | Label | Route | Shortcut | Notes |
|---|---|---|---|---|---|
| Top (1st) | 🏠 | Home | `/` | `Ctrl+1` | **NEW default** — Dashboard |
| Top (2nd) | 💰 | Accounts | `/accounts` | `Ctrl+2` | Moved from `/` |
| Top (3rd) | 📈 | Trades | `/trades` | `Ctrl+3` | Unchanged |
| Top (4th) | 📊 | Planning | `/planning` | `Ctrl+4` | Unchanged |
| Top (5th) | 📅 | Scheduling | `/scheduling` | `Ctrl+5` | Unchanged |
| Bottom | ⚙️ | Settings | `/settings` | `Ctrl+,` | Unchanged |

### Router Update

```typescript
// Addition to router.tsx — Home Dashboard route

const homeRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/',
  component: HomePage,  // In main bundle (startup page)
})

const accountsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/accounts',  // Changed from '/'
}).lazy(() => import('./features/accounts/AccountsHome'))
// Note: AccountsHome moves to lazy loading since it's no longer the startup page
```

### Startup Sequence Update

```
 Renderer (React) — Updated for Home Dashboard
 ─────────────────
 4. React mounts AppShell
    └─ Nav rail renders (sync)
    └─ Home Dashboard skeleton (6 cards with pulse animation)
    └─ Log: startup.shell_paint_ms

 6. User sees app structure
    (skeleton cards, not blank)

 7. Fetch dashboard data (parallel queries):
    └─ GET /dashboard/accounts      → Card 1 hydrates
    └─ GET /dashboard/active-trades → Card 2 hydrates
    └─ GET /dashboard/recent-trades → Card 3 hydrates
    └─ GET /dashboard/plan-highlights → Card 4 hydrates
    └─ GET /dashboard/upcoming-jobs → Card 6 hydrates
    └─ (watchlist deferred — loads last)
    └─ Log: startup.data_ready_ms
```

---

## 6j.7: E2E Waves

> Added as **Wave 7** in the E2E test activation plan.

| Wave | Name | Tests | Cumulative |
|------|------|:-----:|:----------:|
| 7 | Home Dashboard | +3 | TBD |

**Test cases:**
1. `home-loads-on-startup` — Navigate to `/`, verify dashboard skeleton renders, then data hydrates
2. `home-section-toggle` — Disable a section in settings, verify it disappears from dashboard
3. `home-section-reorder` — Reorder sections in settings, verify new order on dashboard

---

## 6j.8: Test Plan

### Unit Tests (Python — pytest)

```python
# tests/unit/test_dashboard_service.py

class TestDashboardService:
    def test_get_account_summary_returns_all_accounts(self, uow):
        svc = DashboardService(uow)
        result = svc.get_account_summary()
        assert len(result) > 0

    def test_get_account_summary_filters_by_id(self, uow):
        svc = DashboardService(uow)
        result = svc.get_account_summary(account_ids=["acc-1"])
        assert all(a.account_id == "acc-1" for a in result)

    def test_get_recent_trades_respects_limit(self, uow):
        svc = DashboardService(uow)
        result = svc.get_recent_trades(limit=5)
        assert len(result) <= 5

    def test_get_plan_highlights_returns_high_conviction(self, uow):
        svc = DashboardService(uow)
        result = svc.get_plan_highlights()
        assert "high_conviction" in result
```

### Integration Tests (Python — pytest)

```python
# tests/integration/test_dashboard_api.py

class TestDashboardAPI:
    async def test_accounts_endpoint(self, client):
        resp = await client.get("/api/v1/dashboard/accounts")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_recent_trades_defaults_limit_10(self, client):
        resp = await client.get("/api/v1/dashboard/recent-trades")
        assert resp.status_code == 200
        assert len(resp.json()) <= 10

    async def test_recent_trades_custom_limit(self, client):
        resp = await client.get("/api/v1/dashboard/recent-trades?limit=3")
        assert resp.status_code == 200
        assert len(resp.json()) <= 3
```

### Component Tests (TypeScript — Vitest)

```typescript
// ui/src/__tests__/HomePage.test.tsx

describe('HomePage', () => {
  it('renders skeleton cards on mount', () => {
    render(<HomePage />);
    expect(screen.getAllByTestId(/dashboard-skeleton/)).toHaveLength(6);
  });

  it('hydrates account summary card after fetch', async () => {
    mockApi('/dashboard/accounts', [{ account_name: 'Main Trading' }]);
    render(<HomePage />);
    await waitFor(() => {
      expect(screen.getByText('Main Trading')).toBeInTheDocument();
    });
  });

  it('respects disabled sections from settings', async () => {
    mockSettings({ 'dashboard.sections.upcoming_jobs.enabled': false });
    render(<HomePage />);
    expect(screen.queryByTestId('dashboard-upcoming-jobs')).not.toBeInTheDocument();
  });
});
```

---

## Exit Criteria

- Home Dashboard renders as the default route (`/`) on app startup
- All 6 dashboard sections load with animated skeleton → data transition
- Sections backed by local database (accounts, trades, plans, jobs) render within 200ms
- Market-data-dependent sections (watchlist) load asynchronously with progress indicators
- First-time users see a welcoming dashboard with empty-state cards (not a blank/broken page)
- Dashboard Settings page allows toggling and reordering sections
- Settings persist across app restarts via the SettingsResolver
- Navigation rail shows Home as the first item with `Ctrl+1` shortcut
- AccountsHome moved to `/accounts` with `Ctrl+2` shortcut
- E2E Wave 7 tests pass (3 tests)

## Outputs

- **Python**: `DashboardService` class (read-only aggregation), 6 REST endpoints under `/api/v1/dashboard/`
- **TypeScript/React**: `HomePage` component, 6 section components, `DashboardSettingsPage`, `useDashboard` hooks
- **Router**: New `homeRoute` at `/`, `accountsRoute` moved to `/accounts`
- **Settings**: 12 new settings keys (`dashboard.sections.*.enabled` + `dashboard.sections.*.order`)
- **Tests**: ~15 unit + integration + component tests
