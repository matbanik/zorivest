# Emerging Standards

Living reference of implementation standards discovered during development sessions. Each standard includes its origin use case and severity. Standards here are **mandatory** — they are checked during `/critical-review-feedback` and enforced as subtasks in `/create-plan`.

> [!IMPORTANT]
> This document is a living artifact. Add new standards as they are discovered during sessions. Each entry follows the template below.

## How to Use This Document

- **During planning** (`/create-plan`): Scan applicable sections and add matching standards as subtasks
- **During review** (`/critical-review-feedback`): Verify all applicable standards were followed
- **During corrections** (`/planning-corrections`): Reference standard IDs in findings

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
