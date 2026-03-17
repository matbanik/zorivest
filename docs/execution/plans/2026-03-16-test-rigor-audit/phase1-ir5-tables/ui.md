# UI Tests

Per-test rating table for Phase 1 IR-5 audit.

Summary: 56 tests audited | 🟢 48 | 🟡 8 | 🔴 0

| Rating | File | Line | Test | Reason |
|---|---|---:|---|---|
| 🟢 | `ui/src/main/__tests__/python-manager.test.ts` | 63 | `should generate a 64-character hex string` | specific value or behavioral assertions |
| 🟢 | `ui/src/main/__tests__/python-manager.test.ts` | 68 | `should generate different tokens each time` | specific value or behavioral assertions |
| 🟡 | `ui/src/main/__tests__/python-manager.test.ts` | 76 | `should return a valid port number (>= 1024)` | right target, but weak assertions only |
| 🟢 | `ui/src/main/__tests__/python-manager.test.ts` | 81 | `should return a number` | specific value or behavioral assertions |
| 🟢 | `ui/src/main/__tests__/python-manager.test.ts` | 88 | `should return false when health check times out` | specific value or behavioral assertions |
| 🟢 | `ui/src/main/__tests__/python-manager.test.ts` | 95 | `should return true when health check succeeds` | specific value or behavioral assertions |
| 🟢 | `ui/src/main/__tests__/python-manager.test.ts` | 104 | `should send Authorization header with Bearer token` | specific value or behavioral assertions |
| 🟢 | `ui/src/main/__tests__/python-manager.test.ts` | 126 | `should attempt graceful shutdown via /shutdown endpoint` | specific value or behavioral assertions |
| 🟢 | `ui/src/main/__tests__/python-manager.test.ts` | 143 | `should expose baseUrl` | specific value or behavioral assertions |
| 🟢 | `ui/src/main/__tests__/python-manager.test.ts` | 148 | `should expose authToken` | specific value or behavioral assertions |
| 🟢 | `ui/src/main/__tests__/window-state.test.ts` | 26 | `should have width 1280 and height 800` | specific value or behavioral assertions |
| 🟢 | `ui/src/main/__tests__/window-state.test.ts` | 33 | `should return stored bounds when available` | specific value or behavioral assertions |
| 🟢 | `ui/src/main/__tests__/window-state.test.ts` | 41 | `should return default bounds when no stored value` | specific value or behavioral assertions |
| 🟢 | `ui/src/main/__tests__/window-state.test.ts` | 49 | `should save bounds to store` | specific value or behavioral assertions |
| 🟡 | `ui/src/renderer/src/__tests__/app.test.tsx` | 62 | `should render without crashing` | weak structural or mock-only assertions |
| 🟢 | `ui/src/renderer/src/__tests__/app.test.tsx` | 67 | `should have a <nav> ARIA landmark for NavRail` | specific value or behavioral assertions |
| 🟢 | `ui/src/renderer/src/__tests__/app.test.tsx` | 73 | `should have a <main> ARIA landmark` | specific value or behavioral assertions |
| 🟢 | `ui/src/renderer/src/__tests__/app.test.tsx` | 79 | `should have a <header> element (banner role)` | specific value or behavioral assertions |
| 🟢 | `ui/src/renderer/src/__tests__/app.test.tsx` | 85 | `should have a skip-to-content link` | specific value or behavioral assertions |
| 🟡 | `ui/src/renderer/src/__tests__/app.test.tsx` | 92 | `should render 5 navigation items in NavRail` | right target, but weak assertions only |
| 🟢 | `ui/src/renderer/src/__tests__/app.test.tsx` | 99 | `should render children inside <main> (Outlet injection point)` | specific value or behavioral assertions |
| 🟢 | `ui/src/renderer/src/__tests__/app.test.tsx` | 111 | `should open CommandPalette on Ctrl+K and close on second press` | specific value or behavioral assertions |
| 🟢 | `ui/src/renderer/src/components/__tests__/CommandPalette.test.tsx` | 58 | `should render when open=true` | specific value or behavioral assertions |
| 🟢 | `ui/src/renderer/src/components/__tests__/CommandPalette.test.tsx` | 63 | `should NOT render when open=false` | specific value or behavioral assertions |
| 🟢 | `ui/src/renderer/src/components/__tests__/CommandPalette.test.tsx` | 68 | `should have a search input` | specific value or behavioral assertions |
| 🟡 | `ui/src/renderer/src/components/__tests__/CommandPalette.test.tsx` | 73 | `should call onClose when Escape is pressed` | weak structural or mock-only assertions |
| 🟡 | `ui/src/renderer/src/components/__tests__/CommandPalette.test.tsx` | 81 | `should group results by category when query is empty` | right target, but weak assertions only |
| 🟢 | `ui/src/renderer/src/components/__tests__/CommandPalette.test.tsx` | 91 | `should filter results when typing` | specific value or behavioral assertions |
| 🟢 | `ui/src/renderer/src/components/__tests__/CommandPalette.test.tsx` | 98 | `should highlight selected item with aria-selected` | specific value or behavioral assertions |
| 🟡 | `ui/src/renderer/src/components/__tests__/CommandPalette.test.tsx` | 108 | `should execute action on Enter and close palette` | weak structural or mock-only assertions |
| 🟢 | `ui/src/renderer/src/components/__tests__/CommandPalette.test.tsx` | 121 | `should call navigate when selecting a navigation entry` | specific value or behavioral assertions |
| 🟢 | `ui/src/renderer/src/lib/__tests__/api.test.ts` | 25 | `should include Bearer token in Authorization header` | specific value or behavioral assertions |
| 🟢 | `ui/src/renderer/src/lib/__tests__/api.test.ts` | 44 | `should set Content-Type to application/json` | specific value or behavioral assertions |
| 🟢 | `ui/src/renderer/src/lib/__tests__/api.test.ts` | 63 | `should throw on non-ok response` | specific value or behavioral assertions |
| 🟢 | `ui/src/renderer/src/lib/__tests__/api.test.ts` | 73 | `should return parsed JSON on success` | specific value or behavioral assertions |
| 🟢 | `ui/src/renderer/src/lib/__tests__/api.test.ts` | 84 | `should merge custom headers with defaults` | specific value or behavioral assertions |
| 🟢 | `ui/src/renderer/src/lib/__tests__/query-client.test.ts` | 5 | `should have staleTime = 0 (financial data always stale)` | specific value or behavioral assertions |
| 🟢 | `ui/src/renderer/src/lib/__tests__/query-client.test.ts` | 10 | `should have gcTime = 300000 (5 minutes)` | specific value or behavioral assertions |
| 🟢 | `ui/src/renderer/src/lib/__tests__/query-client.test.ts` | 15 | `should have mutations.retry = false (never auto-retry financial transactions)` | specific value or behavioral assertions |
| 🟢 | `ui/src/renderer/src/lib/__tests__/query-client.test.ts` | 20 | `should have refetchOnWindowFocus = true` | specific value or behavioral assertions |
| 🟢 | `ui/src/renderer/src/lib/__tests__/query-client.test.ts` | 25 | `should have retry = 2 for queries` | specific value or behavioral assertions |
| 🟢 | `ui/src/renderer/src/registry/__tests__/commandRegistry.test.ts` | 8 | `should have all required fields on every entry` | specific value or behavioral assertions |
| 🟢 | `ui/src/renderer/src/registry/__tests__/commandRegistry.test.ts` | 23 | `every entry.id should be a non-empty string` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `ui/src/renderer/src/registry/__tests__/commandRegistry.test.ts` | 30 | `every entry.action should be a function` | specific value or behavioral assertions |
| 🟡 | `ui/src/renderer/src/registry/__tests__/commandRegistry.test.ts` | 38 | `should have ≥13 entries: 5 nav + 3 action + 5 settings` | right target, but weak assertions only |
| 🟢 | `ui/src/renderer/src/registry/__tests__/commandRegistry.test.ts` | 42 | `all ids should be unique` | specific value or behavioral assertions |
| 🟢 | `ui/src/renderer/src/registry/__tests__/commandRegistry.test.ts` | 47 | `should have 5 navigation entries matching canonical routes` | specific value or behavioral assertions |
| 🟢 | `ui/src/renderer/src/registry/__tests__/commandRegistry.test.ts` | 58 | `should have 3 action entries per spec (calc, import, review)` | specific value or behavioral assertions |
| 🟢 | `ui/src/renderer/src/registry/__tests__/commandRegistry.test.ts` | 67 | `should have 5 settings entries navigating to /settings sub-routes` | specific value or behavioral assertions |
| 🟡 | `ui/src/renderer/src/registry/__tests__/commandRegistry.test.ts` | 78 | `navigation entries should have shortcut field` | weak structural or mock-only assertions |
| 🟢 | `ui/src/renderer/src/registry/__tests__/commandRegistry.test.ts` | 85 | `navigation entries should call navigate with correct path` | specific value or behavioral assertions |
| 🟢 | `ui/src/renderer/src/registry/__tests__/commandRegistry.test.ts` | 96 | `settings entries should call navigate with /settings sub-routes` | specific value or behavioral assertions |
| 🟢 | `ui/src/renderer/src/registry/__tests__/useDynamicEntries.test.tsx` | 27 | `should return empty array when cache has no trade data` | specific value or behavioral assertions |
| 🟢 | `ui/src/renderer/src/registry/__tests__/useDynamicEntries.test.tsx` | 37 | `should return search entries when trades are in the query cache` | specific value or behavioral assertions |
| 🟢 | `ui/src/renderer/src/registry/__tests__/useDynamicEntries.test.tsx` | 60 | `should reactively update when cache changes` | specific value or behavioral assertions |
| 🟢 | `ui/src/renderer/src/registry/__tests__/useDynamicEntries.test.tsx` | 84 | `should cap entries at 10 trades` | specific value or behavioral assertions |
