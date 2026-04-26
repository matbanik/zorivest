# Emerging Standards

Living reference of implementation standards discovered during development sessions. Each standard includes its origin use case and severity. Standards here are **mandatory** — they are checked during `/plan-critical-review` and `/execution-critical-review` and enforced as subtasks in `/create-plan`.

> [!IMPORTANT]
> This document is a living artifact. Add new standards as they are discovered during sessions. Each entry follows the template below.

## How to Use This Document

- **During planning** (`/create-plan`): Scan applicable sections and add matching standards as subtasks
- **During review** (`/plan-critical-review`, `/execution-critical-review`): Verify all applicable standards were followed
- **During corrections** (`/plan-corrections`, `/execution-corrections`): Reference standard IDs in findings

### Standard Template

```markdown
### [ID] — [Title]
- **Severity:** 🔴 Critical | 🟡 Medium | 🟢 Minor
- **Applies to:** [MCP | GUI | API | Infra]
- **Rule:** [One-sentence imperative statement]
- **Origin:** [Session date + prompt/finding that surfaced it]
- **Bad example:** [What went wrong]
- **Good example:** [Correct approach]
```

---

## MCP Tool Standards

### M1 — Schema Field Parity
- **Severity:** 🔴 Critical
- **Applies to:** MCP
- **Rule:** Every field that middleware or handlers inspect must be declared in the tool's Zod schema.
- **Origin:** 2026-03-19 — `confirmation_token` was consumed by `withConfirmation()` but missing from `create_trade` schema; Zod stripped it silently.
- **Bad example:** Middleware reads `params.confirmation_token` but field not in schema → stripped → middleware blocks forever
- **Good example:** Add `confirmation_token: z.string().optional()` to the tool's input schema

### M2 — API ↔ MCP Parity
- **Severity:** 🟡 Medium
- **Applies to:** MCP
- **Rule:** For every REST API endpoint, verify a corresponding MCP tool exists with matching capabilities.
- **Origin:** 2026-03-19 — `DELETE /trades/{id}` existed in the API but no `delete_trade` MCP tool was wired.
- **Bad example:** API has 4 CRUD endpoints, MCP only exposes 3 → users can't delete via AI
- **Good example:** Checklist: GET→list, POST→create, PUT→update, DELETE→delete (with confirmation if destructive)

### M3 — Destructive Tool Gate
- **Severity:** 🔴 Critical
- **Applies to:** MCP
- **Rule:** Destructive tools must be registered in `DESTRUCTIVE_TOOLS` set and wrapped with `withConfirmation()`.
- **Origin:** 2026-03-19 — `delete_trade` needed both the set entry and the middleware wrapper.
- **Bad example:** New destructive tool added with `registerTool()` only → no confirmation required
- **Good example:** Add to `DESTRUCTIVE_TOOLS`, wrap handler with `withConfirmation(toolName, handler)`

### M4 — Build dist/ After Source Changes
- **Severity:** 🔴 Critical
- **Applies to:** MCP
- **Rule:** After editing `mcp-server/src/**`, run `cd mcp-server && npm run build` before testing live. The MCP server runs compiled JS from `dist/`, not source TS.
- **Origin:** 2026-03-19 — Schema fix applied to `src/` but MCP server kept running old `dist/`; required 2 unnecessary IDE restarts.
- **Bad example:** Edit source → restart IDE → wonder why fix didn't take effect
- **Good example:** Edit source → `npm run build` → restart IDE → test

### M5 — TDD Red Phase Must Fail for the Right Reason
- **Severity:** 🟡 Medium
- **Applies to:** MCP, API
- **Rule:** When a TDD red-phase test fails, log the actual response and verify the failure matches the expected bug, not a test setup issue.
- **Origin:** 2026-03-19 — AC-1 vs AC-2 confusion cost ~30 lines of reasoning; the wrong test was assumed to be failing.
- **Bad example:** See "1 failed" → assume it's the test you just wrote → proceed to green phase
- **Good example:** Run with `--reporter=verbose`, confirm failure line + actual vs expected values

### M6 — No Vacuous Test Assertions
- **Severity:** 🟡 Medium
- **Applies to:** MCP, API
- **Rule:** Tests must fail if the bug they target is reintroduced. A test that passes regardless of the fix is vacuous.
- **Origin:** 2026-03-19 — AC-1 ran in dynamic mode where `withConfirmation()` passes through regardless of token presence; test would pass with or without the schema fix.
- **Bad example:** Test in dynamic mode that succeeds whether field exists or not
- **Good example:** Test in static mode where missing field causes middleware to block → test fails → proves schema preserved the field

### M7 — Tool Description Workflow Context
- **Severity:** 🟡 Medium
- **Applies to:** MCP
- **Rule:** MCP tool descriptions and server instructions must include workflow ordering, prerequisite state, return shape examples, and error conditions. An AI agent reading only the tool list should be able to discover the correct multi-step workflow without external documentation.
- **Origin:** 2026-04-12 — AI agent could not discover how to use scheduling tools. `run_pipeline` didn't mention the approval prerequisite. `create_policy` had no example of the expected JSON shape. Server instructions said only "Automated task scheduling" with no mention of the `create → approve → run` lifecycle. MCP resources (`pipeline://policies/schema`, `pipeline://step-types`) existed but were not referenced in any tool description.
- **Bad example:** `description: "Trigger a manual pipeline run for an approved policy."` — doesn't explain what "approved" means, what happens on failure, or what the return shape looks like
- **Good example:**
  ```typescript
  description: "Trigger a manual pipeline run. Prerequisite: policy must have "
      + "approved=true (use approve_policy tool first). Returns {run_id, status, "
      + "error}. Status is 'running'|'success'|'failed'. For policy JSON schema, "
      + "see pipeline://policies/schema resource.\n\n"
      + "Workflow: create_policy → approve_policy → run_pipeline → get_run_detail",
  ```
- **Checklist for new toolsets:**
  1. [ ] Server instructions include 1-line workflow summary for the toolset
  2. [ ] Each tool description mentions prerequisite state (if any)
  3. [ ] Create/update tools include example JSON shape or reference an MCP resource
  4. [ ] Execution tools mention possible return statuses and error shapes
  5. [ ] MCP resources are referenced from the tools that consume them

---

## GUI Standards

### G1 — Buttons Must Have Visible Borders
- **Severity:** 🟢 Minor
- **Applies to:** GUI
- **Rule:** All interactive buttons must have a visible border or background to distinguish them from plain text.
- **Origin:** 2026-03-19 — Save/Cancel buttons rendered as borderless text, users didn't recognize them as clickable.
- **Bad example:** `className="text-sm text-fg"` — looks like a label
- **Good example:** `className="px-4 py-1.5 rounded-md border border-bg-subtle bg-bg hover:bg-bg-elevated"`

### G2 — Destructive Buttons Disabled When Inapplicable
- **Severity:** 🟡 Medium
- **Applies to:** GUI
- **Rule:** Destructive actions (Delete, Remove) must be disabled or hidden when they don't apply (e.g., on unsaved new records).
- **Origin:** 2026-03-19 — Delete button shown on new trade form before the trade was saved.
- **Bad example:** Delete button always visible and clickable, even on new records
- **Good example:** `disabled={!existingTrade}` or conditionally render

### G3 — Server-Side Search for Lists > 50 Items
- **Severity:** 🔴 Critical
- **Applies to:** GUI, API
- **Rule:** Any list that can exceed 50 items must use server-side search, not client-side filtering. Command palettes must not hold large datasets.
- **Origin:** 2026-03-19 — Command palette tried to cache all trades as Fuse.js entries; user said "this app will have THOUSANDS of trades."
- **Bad example:** Load all records into memory → filter with `useMemo` → breaks at scale
- **Good example:** Debounced input → `GET /api/v1/trades?search=NVDA&limit=25` → paginated results

### G4 — Pagination Defaults: 25/Page with Count
- **Severity:** 🟢 Minor
- **Applies to:** GUI
- **Rule:** Tables default to 25 rows per page. Footer shows `Page X of Y (N items)`.
- **Origin:** 2026-03-19 — `pageSize=50` matched API `limit=50`, showing "Page 1 of 1" with no count.
- **Bad example:** `pageSize: 50` + API `limit: 50` → always 1 page
- **Good example:** `pageSize: 25` + API `limit: 200` → `Page 1 of 4 (100 trades)`

### G5 — Auto-Refresh for Externally Mutated Data
- **Severity:** 🟡 Medium
- **Applies to:** GUI
- **Rule:** Queries whose data can change from external sources (MCP, API, other windows) must use `refetchInterval` polling.
- **Origin:** 2026-03-19 — Trades created via MCP didn't appear in GUI until manual page reload.
- **Bad example:** Query with no `refetchInterval` → stale data until user navigates away and back
- **Good example:** `refetchInterval: 5_000` on the trades query

### G6 — Field Name Contracts
- **Severity:** 🔴 Critical
- **Applies to:** GUI
- **Rule:** UI components must use the exact field names from the API response type. Never assume field names without checking the TypeScript interface.
- **Origin:** 2026-03-19 — `useDynamicEntries.ts` used `trade.id` and `trade.symbol` but API returns `trade.exec_id` and `trade.instrument`.
- **Bad example:** `trade.id` → `undefined` because field is actually `exec_id`
- **Good example:** Reference the `Trade` interface: `trade.exec_id`, `trade.instrument`

### G7 — Column Truncation Minimum 15 Characters
- **Severity:** 🟢 Minor
- **Applies to:** GUI
- **Rule:** Table columns that truncate text must show at least 15-20 characters before ellipsis.
- **Origin:** 2026-03-19 — Account column truncated at 5 characters, making IDs unreadable.
- **Bad example:** `val.slice(0, 5) + "…"` → `"U1234…"` — can't distinguish accounts
- **Good example:** `val.length > 20 ? val.slice(0, 20) + "…" : val`

### G8 — OpenAPI Spec Regen After Route Changes
- **Severity:** 🔴 Critical
- **Applies to:** API, Infra
- **Rule:** After any API route change, run `uv run python tools/export_openapi.py --check openapi.committed.json`. If drift detected, regenerate with `-o`.
- **Origin:** 2026-03-19 — Added `search` query param to trades route, CI quality gate failed due to spec drift.
- **Bad example:** Add new query param → commit → CI fails → debug for 10 minutes
- **Good example:** Add param → `--check` → `❌ drift` → `-o` regen → commit with spec

### G9 — Search Must Include All User-Visible Text Columns
- **Severity:** 🟡 Medium
- **Applies to:** GUI, API
- **Rule:** Search/filter must cover every text column visible in the table, including notes and formatted timestamps.
- **Origin:** 2026-03-19 — Initial search only matched instrument, exec_id, account_id. User expected to search by notes and date.
- **Bad example:** Search covers 3 of 8 visible columns → user types note content → no results
- **Good example:** `OR` filter across all text columns + `strftime` for datetime

### G10 — DateTime Search via strftime Not CAST
- **Severity:** 🟡 Medium
- **Applies to:** API (SQLite)
- **Rule:** When searching datetime columns as text, use `strftime('%Y-%m-%d %H:%M', column)` not `CAST(column AS TEXT)`.
- **Origin:** 2026-03-19 — `CAST(time AS TEXT)` produced unusable format in SQLite; searching "2026" returned nothing.
- **Bad example:** `cast(TradeModel.time, String).like(pattern)` — format is implementation-dependent
- **Good example:** `func.strftime('%Y-%m-%d %H:%M', TradeModel.time).like(pattern)`

### G11 — Global Actions Must Route Through AppShell via Custom Events
- **Severity:** 🔴 Critical
- **Applies to:** GUI
- **Rule:** Command palette actions and global keyboard shortcuts that open modals/panels must be owned by `AppShell` (always-mounted root), not by feature-specific layouts. Use custom DOM events (`window.dispatchEvent(new CustomEvent('zorivest:action-name'))`) to bridge the command registry → AppShell gap.
- **Origin:** 2026-03-20 — Position Calculator command palette entry was a console-log stub. After wiring it to `PlanningLayout`, it only worked on the `/planning` page. Keyboard shortcut `Ctrl+Shift+C` had the same bug — the `useEffect` listener was inside `PlanningLayout` which only mounts on one route.
- **Bad example:** Calculator state + `Ctrl+Shift+C` listener inside `PlanningLayout` → only works when user is on `/planning` page → Command Palette "Position Calculator" does nothing on `/trades`
- **Good example:**
  1. `commandRegistry.ts`: `action: () => window.dispatchEvent(new CustomEvent('zorivest:open-calculator'))`
  2. `AppShell.tsx`: `useEffect(() => { window.addEventListener('zorivest:open-calculator', handler); ... }, [])`
  3. `AppShell.tsx`: Renders `<PositionCalculatorModal>` + owns `calculatorOpen` state + `Ctrl+Shift+C` listener
  4. `PlanningLayout.tsx`: Calculator button dispatches same event: `window.dispatchEvent(new CustomEvent('zorivest:open-calculator'))`

**Pattern summary:**

| Layer | Responsibility | File |
|-------|---------------|------|
| Command Registry | Dispatch named custom event | `commandRegistry.ts` |
| AppShell | Listen for event + own state + render modal + own keyboard shortcut | `AppShell.tsx` |
| Feature Layout | Button triggers same event (convenience shortcut) | e.g. `PlanningLayout.tsx` |

**Event naming convention:** `zorivest:{verb}-{noun}` (e.g. `zorivest:open-calculator`, `zorivest:import-trades`, `zorivest:start-review`)

**Checklist for new global actions:**
1. [ ] Modal/panel component exists with `isOpen` + `onClose` props
2. [ ] State + `useEffect` listener added to `AppShell.tsx`
3. [ ] `commandRegistry.ts` action dispatches `CustomEvent`
4. [ ] Keyboard shortcut listener in `AppShell.tsx` (not feature layout)
5. [ ] Feature page button (if any) dispatches same `CustomEvent`
6. [ ] Tests verify event dispatch (not modal presence in feature layout)

---

## Pagination Standards

### P1 — Paginated Responses Must Return Real DB Count
- **Severity:** 🔴 Critical
- **Applies to:** API, MCP
- **Rule:** Every paginated list endpoint must return the real database count (matching the same filters) in the `total` field, not `len(items)` from the current page.
- **Origin:** 2026-03-19 — `list_trades` returned `total: 100` (page size) instead of real DB count. MCP agents had no way to discover how many trades exist without fetching all of them.
- **Bad example:** `total=len(items)` — always equals page size; agents can't detect more pages
- **Good example:** `total=service.count_trades(account_id=account_id, search=search)` — real count from DB

**Implementation template** (6 layers, bottom-up):

**Layer 1 — Repository Port** (`ports.py`):
```python
def count_filtered(
    self,
    account_id: str | None = None,
    search: str | None = None,
) -> int:
    """Return total count matching filters (ignoring limit/offset)."""
    ...
```

**Layer 2 — SQLAlchemy Repository** (`repositories.py`):
```python
def _build_filter_query(self, account_id=None, search=None):
    """Shared filter builder (used by both list + count)."""
    query = self._session.query(Model)
    if account_id:
        query = query.filter(Model.account_id == account_id)
    # ... same filter logic as list_filtered ...
    return query

def list_filtered(self, limit, offset, account_id, sort, search):
    query = self._build_filter_query(account_id, search)
    # add sort + offset + limit
    return query.offset(offset).limit(limit).all()

def count_filtered(self, account_id, search):
    return self._build_filter_query(account_id, search).count()
```

**Layer 3 — In-Memory Stub** (`stubs.py`):
```python
def count_filtered(self, account_id=None, search=None, **kw):
    items = list(self._store.values())
    # apply same filters as list_filtered (no slice)
    return len(items)
```

**Layer 4 — Service** (`*_service.py`):
```python
def count_items(self, account_id=None, search=None) -> int:
    with self.uow:
        return self.uow.repo.count_filtered(account_id=account_id, search=search)
```

**Layer 5 — API Route** (`routes/*.py`):
```python
items = service.list_items(limit=limit, offset=offset, ...)
total = service.count_items(account_id=account_id, search=search)
return PaginatedResponse(items=items, total=total, limit=limit, offset=offset)
```

**Layer 6 — MCP Tool Description** (`*-tools.ts`):
```typescript
description: "List items with pagination. Returns {items, total, limit, offset} "
    + "where `total` is the real database count matching filters (not page size). "
    + "Use limit=1&offset=0 to efficiently discover total count before fetching all.",
```

**Key principles:**
- Extract shared filter logic into `_build_filter_query()` to avoid duplication between list + count
- Count query uses same filters as list but no `LIMIT`/`OFFSET`/`ORDER BY`
- MCP description must explicitly tell agents that `total` is real, and suggest `limit=1` for count-only discovery
- For datasets < 100K rows, inline COUNT is negligible cost; at scale, consider caching or approximate counts

---

## Date & Time Formatting

### DT1 — Trade Timestamp Display Format
- **Severity:** 🟡 Medium
- **Applies to:** GUI
- **Rule:** Format all trade/event timestamps as `MM-DD-YYYY h:mmAM/PM` (e.g. `03-20-2026 2:35PM`). Never use locale strings (`toLocaleString`, `Mar 20, 2026`).
- **Origin:** 2026-03-20 — Trade picker displayed `"3/20/2026, 2:35:00 PM"` (locale format); required format `"03-20-2026 2:35PM"`.
- **Bad example:** `new Date(iso).toLocaleString()` → `"3/20/2026, 2:35:00 PM"` (varies by locale)
- **Good example:**
  ```ts
  function formatTimestamp(iso: string | null | undefined): string {
      if (!iso) return ''
      const d = new Date(iso)
      const mm = String(d.getMonth() + 1).padStart(2, '0')
      const dd = String(d.getDate()).padStart(2, '0')
      const h = d.getHours() % 12 || 12
      const minutes = String(d.getMinutes()).padStart(2, '0')
      const ampm = d.getHours() >= 12 ? 'PM' : 'AM'
      return `${mm}-${dd}-${d.getFullYear()} ${h}:${minutes}${ampm}`
  }
  ```

### DT2 — No Seconds in UI Display
- **Severity:** 🟢 Minor
- **Applies to:** GUI
- **Rule:** Trade timestamps in the UI omit seconds (`h:mmAM/PM`, not `h:mm:ssAM/PM`). Full ISO precision is preserved in the data layer.
- **Origin:** 2026-03-20 — Seconds added visual noise without adding value for typical trading use cases.
- **Bad example:** `"03-20-2026 2:35:12PM"` — seconds shown
- **Good example:** `"03-20-2026 2:35PM"` — minutes-only display

---

## GUI Element System Decisions

Decisions made based on web research (UX Stack Exchange, Nielsen Norman Group, IxDF, Material Design) during the 2026-03-24 MEU-70b session. Apply these patterns whenever similar controls appear in any Zorivest GUI.

### UX1 — Mutually Exclusive State Controls: Segmented Buttons, Not Select + Buttons
- **Severity:** 🔴 Critical
- **Applies to:** GUI
- **Rule:** For 2–5 mutually exclusive options with known labels (status, direction, timeframe), use a **segmented button group** (`<div role="group">` of `<button>`s). Never combine a `<select>` and tag buttons for the same field.
- **Origin:** 2026-03-24 MEU-70b — Trade Planner had a status `<select>` AND four tag buttons. Clicking a tag did nothing until the dropdown was changed first (two controls, one truth). Research: UX Stack Exchange + r/userexperience confirm segmented buttons are canonical for ≤5 known options.
- **Bad example:** `<select>` for status + separate quick-transition `<button>` row → user must think about which control to use
- **Good example:**
  ```tsx
  <div className="flex gap-1" role="group" aria-label="Plan status">
      {OPTIONS.map(({ value, label, activeClass }) => (
          <button key={value} aria-pressed={current === value}
              onClick={() => setCurrent(value)}
              className={current === value ? activeClass : 'ghost-class'}>
              {label}
          </button>
      ))}
  </div>
  ```
- **Visual rule:** Active state = filled background + colored text. Inactive = ghost/muted, no fill.
- **Color conventions:**

  | State | Classes |
  |-------|---------|
  | Draft | `bg-bg-elevated text-fg border-bg-subtle` |
  | Active | `bg-blue-500/20 text-blue-300 border-blue-500/40` |
  | Executed | `bg-green-500/20 text-green-300 border-green-500/40` |
  | Cancelled | `bg-red-500/15 text-red-400 border-red-500/30` |

### UX2 — Conditional Fields: Responsive Enabling (Grayout + Tooltip), Not Progressive Disclosure (Hide)
- **Severity:** 🟡 Medium
- **Applies to:** GUI
- **Rule:** When a field requires a prerequisite state, **disable it with a tooltip** explaining the prerequisite — do not hide it. Hidden fields are not discoverable; disabled fields teach the causal relationship.
- **Origin:** 2026-03-24 MEU-70b — "Link to Trade" picker was hidden behind `{isExecutedStatus && ...}`. Users had no way to discover the field or understand that Executed status would reveal it. NNG + IxDF: responsive enabling is preferred when the field's existence *signals a capability*; progressive disclosure only for entire optional sections.
- **Bad example:** `{condition && <TradePickerField />}` — field doesn't exist until condition is met; not discoverable
- **Good example:**
  ```tsx
  <input
      disabled={!condition}
      placeholder={condition ? 'Filter trades...' : 'Set status to Executed first'}
      title={!condition ? 'Change status to Executed to link a trade' : undefined}
      className={condition
          ? 'bg-bg border-green-500/30'
          : 'opacity-50 cursor-not-allowed bg-bg-elevated'}
  />
  ```
- **When to use progressive disclosure instead:** Only when the field is always irrelevant unless a major condition is met AND there is a visible containing section header explaining the context.

### UX3 — Combobox/Picker: Show Selected Label in Input After Selection (Not Search Text)
- **Severity:** 🟡 Medium
- **Applies to:** GUI
- **Rule:** When a user selects an item from a combobox picker list, the **input shows the selected item's human-readable label** and the list collapses. A `×` clear button deselects. Never leave the search query text in the input after selection.
- **Origin:** 2026-03-24 MEU-70b — Trade linker picker showed `✓` on the selected item while the list was visible, but the input still showed the search query (`"8:"`) after scrolling away. NNG combobox pattern + Material Design: input value must reflect the selection post-close.
- **Bad example:** User searches `"8:"`, selects trade, input still shows `"8:"` — unclear what is linked
- **Good example:**
  ```tsx
  // Two states: search text (typing) vs label (selected)
  <input value={pickerLabel || pickerSearch}
      onChange={(e) => { setPickerLabel(''); setPickerSearch(e.target.value) }} />
  // On item select:
  setPickerLabel(humanLabel)   // collapses list
  setPickerSearch('')
  // List rendered only when: isActive && !pickerLabel
  ```
- **Clear button rule:** Absolute-positioned `×` inside the input wrapper; visible only when `pickerLabel` is set.

### G12 — Modal Positioning: Fixed-Top, Not Centered
- **Severity:** 🟡 Medium
- **Applies to:** GUI
- **Rule:** Modals that contain dynamic-height content (autocomplete dropdowns, loading states, expandable sections) must use fixed-top positioning (`items-start pt-[10vh]`), not vertical centering (`items-center justify-center`). Centering causes the modal to jump/shift whenever content height changes.
- **Origin:** 2026-04-05 — Position Calculator modal jumped on every keystroke and dropdown toggle because `items-center` recalculated vertical position as the autocomplete dropdown appeared/disappeared.
- **Bad example:** `className="fixed inset-0 flex items-center justify-center"` → modal bounces when dropdown opens
- **Good example:** `className="fixed inset-0 flex items-start justify-center pt-[10vh]"` → modal stays pinned

### G13 — Archived/Soft-Deleted Entities: Include in Name Lookups with Suffix
- **Severity:** 🔴 Critical
- **Applies to:** GUI, API
- **Rule:** When an entity is soft-deleted (archived), it must remain resolvable in name lookup maps for related data. Fetch with `include_archived=true` for lookup queries and append `(Archived)` to the display name. The main entity list page should still exclude archived items.
- **Origin:** 2026-04-05 — Archiving an account caused all trades referencing it to display raw UUIDs instead of the account name, because the accounts query excluded archived accounts from the name map.
- **Bad example:** `GET /api/v1/accounts` (excludes archived) → trades show `"a1b2c3d4-..."` for archived account
- **Good example:**
  ```tsx
  // Lookup query includes archived for name resolution
  apiFetch('/api/v1/accounts?include_system=true&include_archived=true')
  // Name map appends suffix
  m.set(a.account_id, a.is_archived ? `${a.name} (Archived)` : a.name)
  ```
- **Decision rationale:** Sequential thinking analysis of 5 options (suffix, generic label, reassign, styling, transparent) — suffix preserves full history context and is the industry-standard pattern used by brokerage platforms.

### G14 — Auto-Populate Related Fields on Entity Selection
- **Severity:** 🟡 Medium
- **Applies to:** GUI
- **Rule:** When a user selects a primary entity (ticker, account) from an autocomplete/dropdown, auto-populate related dependent fields (price, balance, stop/target) from a live data source. If dependent fields are at their default/zero value, fill them with the fetched value; if the user has already edited them, preserve the user's value.
- **Origin:** 2026-04-05/06 — Calculator and Trade Plan ticker selection did not auto-fill entry price from spot quote. Users had to manually type the current price after selecting a ticker, defeating the purpose of the autocomplete. Stop/target at 0 also needed seeding.
- **Bad example:** Ticker selected → only ticker field updated → entry/stop/target stay at 0 → user must look up and type current price
- **Good example:**
  ```tsx
  const handleTickerSelect = useCallback((result) => {
      apiFetch(`/api/v1/market-data/quote?ticker=${result.symbol}`)
          .then((quote) => {
              const price = Math.round(quote.price * 100) / 100
              setEntryPrice(price)
              setStopPrice((prev) => (prev === 0 ? price : prev))
              setTargetPrice((prev) => (prev === 0 ? price : prev))
          })
  }, [])
  ```
- **Consistency rule:** If this pattern exists in one form (Calculator), apply it to all forms with the same field (Trade Plan, Watchlist). Use [TickerAutocomplete's `onSelect` callback](file:///p:/zorivest/ui/src/renderer/src/components/TickerAutocomplete.tsx#L17) to wire it uniformly.

### G15 — API Conflict/Error Responses Must Surface in UI
- **Severity:** 🔴 Critical
- **Applies to:** GUI, API
- **Rule:** Every mutation hook (`useMutation`) must have an `onError` handler that parses the API error response (especially 409 Conflict) and displays it to the user. Silent swallowing of API errors is never acceptable for destructive operations.
- **Origin:** 2026-04-05 — Deleting an account with assigned trades returned 409 Conflict from the API, but the frontend `deleteAccount.mutate()` had no `onError` callback — the error was silently swallowed, and the user saw no feedback.
- **Bad example:**
  ```tsx
  deleteAccount.mutate(id) // no onError → 409 silently swallowed
  ```
- **Good example:**
  ```tsx
  const [deleteError, setDeleteError] = useState<string | null>(null)
  deleteAccount.mutate(id, {
      onError: (err: Error) => {
          try {
              const body = JSON.parse(err.message.split('\n').pop() ?? '')
              setDeleteError(body.detail ?? 'Deletion failed')
          } catch {
              setDeleteError(err.message || 'Deletion failed')
          }
      },
  })
  // Render dismissible error banner when deleteError is set
  ```
- **Checklist for new mutations:**
  1. [ ] `onError` handler added to `mutate()` call
  2. [ ] Error state variable declared for UI display
  3. [ ] Error banner/toast rendered with dismiss capability
  4. [ ] 409 Conflict `detail` field parsed for actionable message

### G16 — Electron CSP Must Include img-src for Local API Images
- **Severity:** 🔴 Critical
- **Applies to:** GUI (Electron)
- **Rule:** The Electron renderer's `Content-Security-Policy` meta tag must include `img-src 'self' http://localhost:* http://127.0.0.1:* data:`. Without this, `<img>` tags pointing to the local API will silently fail (`naturalWidth === 0`) with no console error.
- **Origin:** 2026-04-06 — Screenshots uploaded via the API rendered as broken images in the ScreenshotPanel. Root cause: `default-src 'self'` blocked images from `http://127.0.0.1:17787`. No browser console error was visible; debugging required checking `naturalWidth` in DevTools.
- **Bad example:** CSP with only `default-src 'self' http://localhost:*` — `default-src` does NOT cascade to `img-src` for cross-origin images when the page is loaded from `file://` or Electron's custom protocol
- **Good example:**
  ```html
  <meta http-equiv="Content-Security-Policy"
    content="default-src 'self' http://localhost:* http://127.0.0.1:*;
             img-src 'self' http://localhost:* http://127.0.0.1:* data:;
             script-src 'self'; style-src 'self' 'unsafe-inline'" />
  ```
- **Debugging tip:** If images fail to load in Electron, inspect with `document.querySelector('img').naturalWidth` — `0` means CSP blocked, not a network error.
- **Checklist for CSP changes:**
  1. [ ] `img-src` directive explicitly listed (not relying on `default-src` fallback)
  2. [ ] Both `localhost` and `127.0.0.1` origins included (Node may resolve either)
  3. [ ] `data:` included if thumbnails use data URIs
  4. [ ] E2E test verifies `naturalWidth > 0` on at least one `<img>` element

### G20 — Confirmation Dialogs Must Use Themed Portaled Modals, Not Native Dialogs
- **Severity:** 🔴 Critical
- **Applies to:** GUI
- **Rule:** Never use `window.confirm()`, `window.alert()`, or `window.prompt()`. These render native OS chrome that ignores the application's dark theme. Use a React portal-based modal (`createPortal(modal, document.body)`) with inline styles referencing CSS variables for theme consistency.
- **Origin:** 2026-04-25 — Delete policy confirmation used `window.confirm()`, which rendered a white OS dialog that clashed with the dark-themed application.
- **Bad example:**
  ```tsx
  if (window.confirm('Are you sure?')) deletePolicy()
  ```
- **Good example:**
  ```tsx
  import { createPortal } from 'react-dom'

  const [showConfirm, setShowConfirm] = useState(false)

  // Render via portal to escape parent overflow constraints
  {showConfirm && createPortal(
      <div style={{
          position: 'fixed', inset: 0, zIndex: 9999,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          backgroundColor: 'rgba(0,0,0,0.6)',
      }}>
          <div style={{
              backgroundColor: 'var(--color-bg-elevated)',
              border: '1px solid var(--color-border)',
              borderRadius: '12px', padding: '24px',
              color: 'var(--color-fg)',
          }}>
              {/* ... buttons ... */}
          </div>
      </div>,
      document.body
  )}
  ```
- **Why portal?** Components inside scrollable panes or panels with `overflow: hidden/auto` will clip fixed-position modals. `createPortal` to `document.body` guarantees the modal escapes all parent overflow constraints.
- **Checklist for new confirmation dialogs:**
  1. [ ] No `window.confirm/alert/prompt` calls
  2. [ ] Modal rendered via `createPortal(_, document.body)`
  3. [ ] Styles use CSS variables (`--color-bg-elevated`, `--color-fg`, `--color-border`)
  4. [ ] Backdrop click and Escape key dismiss the modal
  5. [ ] Destructive button uses red/danger styling

### G21 — Mutually Exclusive State Controls Must Support Direct Selection, Not Cycling
- **Severity:** 🟡 Medium
- **Applies to:** GUI
- **Rule:** When presenting 2–5 mutually exclusive states as a segmented button group (per UX1), each button must directly set its state on click. Never implement a "cycling" pattern where clicking any button advances to the next state in sequence. Users expect to click the label they want and get that state immediately.
- **Origin:** 2026-04-25 — Pipeline scheduling state selector (Draft/Ready/Scheduled) initially cycled through states on each click. User reported: "There is issue when I click on Ready, it cycles to Scheduled."
- **Bad example:**
  ```tsx
  // Cycling — user clicks "Ready" but gets "Scheduled" instead
  const nextState = { draft: 'ready', ready: 'scheduled', scheduled: 'draft' }
  onClick={() => setState(nextState[currentState])}
  ```
- **Good example:**
  ```tsx
  // Direct selection — user clicks "Ready" and gets "Ready"
  {STATES.map(s => (
      <button key={s.value}
          onClick={() => setState(s.value)}
          className={currentState === s.value ? s.activeClass : 'text-gray-500'}>
          {currentState === s.value && <span className="dot" />}
          {s.label}
      </button>
  ))}
  ```
- **Visual rule:** Active state gets colored text + left dot indicator. Inactive states are gray/muted. All buttons are always visible to show available options.

### G22 — Default Templates Must Satisfy Backend Validation Schemas
- **Severity:** 🔴 Critical
- **Applies to:** GUI, API
- **Rule:** When the GUI provides a "New" button that creates an entity with a default template (e.g., default pipeline policy), the template must include all required fields per the backend Pydantic/Zod schema. Never ship a template with empty objects (`{}`) for fields that have required nested properties.
- **Origin:** 2026-04-25 — `+ New Policy` button sent a default policy with `params: {}` for the `fetch` step, but `FetchStep.Params` requires `provider` and `data_type`. This caused a 422 Unprocessable Entity on every creation attempt.
- **Bad example:**
  ```tsx
  steps: [{ type: 'fetch', params: {} }]  // 422 — missing required fields
  ```
- **Good example:**
  ```tsx
  steps: [{ type: 'fetch', params: { provider: 'yahoo', data_type: 'ohlcv' } }]
  ```
- **Verification:** After creating a default template, test it against the backend validation endpoint before shipping. Run a manual `POST` with the template body and confirm 201, not 422.

### G17 — Fetch Wrapper Must Detect FormData and Omit Content-Type
- **Severity:** 🟡 Medium
- **Applies to:** GUI (API client)
- **Rule:** Any shared `fetch` wrapper that sets `Content-Type: application/json` must detect when the request body is a `FormData` instance and omit the `Content-Type` header entirely. The browser auto-sets `multipart/form-data` with the correct boundary; manually setting it corrupts the boundary.
- **Origin:** 2026-04-06 — Image upload via `apiFetch()` returned 422/400 because the wrapper injected `Content-Type: application/json` on a `FormData` body, corrupting the multipart boundary. The server couldn't parse the file.
- **Bad example:**
  ```ts
  // Always sets JSON content type — breaks FormData uploads
  const res = await fetch(url, {
      headers: { 'Content-Type': 'application/json' },
      body: data,
  })
  ```
- **Good example:**
  ```ts
  const headers: Record<string, string> = {}
  if (!(body instanceof FormData)) {
      headers['Content-Type'] = 'application/json'
  }
  const res = await fetch(url, { headers, body })
  ```
- **When this applies:** Any time a new file upload feature is added that uses the shared `apiFetch`/`fetchWithAuth` wrapper.

---

## E2E Testing Standards

### E1 — E2E Test Data Seeding Must Use Node fetch, Not page.request
- **Severity:** 🟡 Medium
- **Applies to:** GUI (E2E/Playwright)
- **Rule:** When seeding test data in Playwright E2E tests for Electron apps, use Node's native `fetch()` (runs in the test process) instead of Playwright's `page.request.post()` (routes through the Electron renderer's network stack). The renderer may enforce CSP, CORS, or other policies that block test seeding requests.
- **Origin:** 2026-04-06 — E2E test `seedImage()` used `page.request.post()` with multipart data. The request failed because it was routed through the Electron renderer's network context, which applied the app's CSP policy. Switching to Node's native `fetch()` bypassed this entirely.
- **Bad example:**
  ```ts
  // Routes through Electron's network stack → CSP may block
  const res = await page.page.request.post(`${API}/trades/${id}/images`, {
      multipart: { file: { ... } },
  })
  ```
- **Good example:**
  ```ts
  // Runs in Node context → bypasses Electron CSP/CORS
  const formData = new FormData()
  formData.append('file', new Blob([png], { type: 'image/png' }), 'test.png')
  const res = await fetch(`${API}/trades/${id}/images`, {
      method: 'POST',
      body: formData,
  })
  ```
- **Rule of thumb:** `page.request` is for testing the app's own API behavior (verifying CORS, auth headers). `fetch()` is for seeding test fixtures that should not be subject to the app's security policies.

---

## Test Infrastructure Standards

### G18 — Shared Hook Mock Inventory
- **Severity:** 🟡 Medium
- **Applies to:** GUI (Unit Tests)
- **Rule:** When adding a shared hook (e.g., `usePersistedState`, `useNotifications`) to an existing component, audit ALL existing test blocks that render that component and update their API mocks to handle the hook's endpoint. Unknown endpoints returning `{}` cause React Query "data cannot be undefined" warnings that mask real failures.
- **Origin:** 2026-04-11 MEU-70a continuation — `usePersistedState('ui.watchlist.colorblind_mode')` was added to `WatchlistPage.tsx`. Only the new redesign tests had the settings API mock. Five existing test blocks returned `{}` for unmatched URLs, causing `.value` to be `undefined` → React Query warnings.
- **Bad example:** Add `usePersistedState` to component → only mock settings API in new tests → 5 existing tests emit warnings → warnings mask real failures
- **Good example:**
  ```bash
  # After adding a shared hook to a component:
  rg "render(<WatchlistPage" tests/ --files-with-matches
  # For each file: add settings API handler to mockApiFetch before the catch-all
  ```
  ```ts
  mockApiFetch.mockImplementation((url: string) => {
      if (url === '/api/v1/watchlists/') return Promise.resolve(MOCK_WATCHLISTS)
      if (url.includes('/api/v1/settings/')) return Promise.resolve({ value: false })
      return Promise.resolve({})
  })
  ```
- **Checklist for adding shared hooks:**
  1. [ ] `rg` all test files rendering the component
  2. [ ] Add mock handler for the hook's API endpoint to each `beforeEach` or per-test mock
  3. [ ] Verify no React Query warnings in test output after change

### G19 — Bug-Fix TDD Protocol
- **Severity:** 🔴 Critical
- **Applies to:** All layers
- **Rule:** Bug reports ALWAYS require Red→Green TDD. Write a failing test that reproduces the bug BEFORE touching production code. The test must fail for the exact reason the bug exists (not a setup issue). Never go directly from "user reports bug" to "fix code."
- **Origin:** 2026-04-11 MEU-70a continuation — User reported 5 WatchlistPage bugs (colorblind toggle, notes editing, market data display). Agent initially jumped straight to fixing production code. User had to explicitly correct: "perform TDD do not just adjust the code!" — adding ~30 minutes of rework.
- **Bad example:**
  ```
  User: "Colorblind toggle only changes button color, not table cells"
  Agent: *immediately edits WatchlistTable.tsx to fix getChangeColor()*
  ```
- **Good example:**
  ```
  User: "Colorblind toggle only changes button color, not table cells"
  Agent:
  1. Write test: render WatchlistTable with colorblind=true, assert cell uses blue (#2962FF) not green (#26A69A)
  2. Run test → RED (actual: green, expected: blue) — confirms bug reproduction
  3. Fix getChangeColor() to read colorblind prop
  4. Run test → GREEN
  ```
- **Why this matters:** Bug-fix tests serve as regression guards. Without them, the same bug can be silently reintroduced in future refactors. The test IS the documentation of what broke.

### G20 — Corrections Agent Must Not Self-Approve

- **Severity:** 🔴 Critical
- **Applies to:** Workflow governance (`/execution-corrections`, `/plan-corrections`)
- **Rule:** The corrections agent (coder role) MUST NOT set the review verdict to `approved`. After applying corrections, set verdict to `corrections_applied`. Only a subsequent critical-review pass — run by the reviewer role — may issue `approved`. The three-state lifecycle is: `changes_required` → `corrections_applied` → `approved`.
- **Origin:** 2026-04-26 Pipeline Emulator MCP corrections — Agent set `approved` verdict in its own corrections handoff, bypassing reviewer separation of concerns. The `execution-corrections.md` Step 6 was labeled "Reviewer" but executed by the coder, creating a self-approval loop. Agent also made a forbidden write to `task.md` (changing `[B]` → `[x]`). Both violations identified by user.
- **Bad example:**
  ```
  # In /execution-corrections Step 6:
  verdict: "approved"  # ← Coder approving its own work
  ```
- **Good example:**
  ```
  # In /execution-corrections Step 6:
  verdict: "corrections_applied"  # ← Coder signals readiness for re-review
  # Then user runs /execution-critical-review which may set:
  verdict: "approved"  # ← Reviewer approves independently
  ```
- **Why this matters:** Self-approval eliminates the quality gate that review cycles provide. The corrections agent wrote the code AND judged it sufficient — the same conflict of interest that code review processes exist to prevent. Without this guard, any number of review passes can be short-circuited by the corrections agent declaring itself done.
