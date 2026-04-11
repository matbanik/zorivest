---
project: "2026-04-11-watchlist-redesign-plan-size"
date: "2026-04-11"
source: "docs/build-plan/06i-gui-watchlist-visual.md"
meus: ["MEU-70a"]
status: "approved"
template_version: "2.0"
---

# Implementation Plan: Watchlist Visual Redesign + Plan Size Propagation

> **Project**: `2026-04-11-watchlist-redesign-plan-size`
> **Build Plan Section(s)**: 06i §1–8 (Watchlist Visual Level 1) + [PLAN-NOSIZE] cross-cutting
> **Status**: `approved`

---

## Goal

Redesign the Watchlist GUI from a basic list/detail layout into a professional financial data table with dark trading palette, price columns, gain/loss coloring, and volume formatting. Simultaneously, propagate the `position_size` field through the full stack (Domain → SQLAlchemy → API → MCP → GUI) and integrate the Position Calculator write-back to the Trade Plan form, resolving the `[PLAN-NOSIZE]` known issue.

---

## User Review Required

> [!IMPORTANT]
> **Colorblind-safe toggle persistence**: The design spec defines a blue/orange alternate palette for colorblind users. This plan implements it as a toggle button in the watchlist toolbar, persisted via the existing Settings API (`PUT /api/v1/settings`). The setting key will be `ui.watchlist.colorblind_mode` (registered in `SETTINGS_REGISTRY`). If you prefer a different UX (e.g., user profile, global settings page), please flag now.

> [!IMPORTANT]
> **Position Size semantic**: `position_size` is defined as the **total dollar value** of the position (`shares_planned × entry_price`). The calculator already computes this as `positionValue`. This plan uses that definition. If you want `position_size` to mean something else (e.g., % of portfolio), please clarify.

> [!IMPORTANT]
> **`shares_planned` naming (Human-Approved, decision record: pomera note #795)**: The repo standardized on `shares_planned` (not `shares`) during MEU-70b to avoid ambiguity. All layers already use `shares_planned`. The build-plan spec (06i), known-issues, and BUILD_PLAN.md have been updated to match. No alias mapping is needed.

---

## Proposed Changes

### Sub-MEU A: PLAN-NOSIZE — Backend + MCP Propagation

#### Boundary Inventory

| Surface | Schema Owner | Field Constraints | Extra-Field Policy |
|---------|-------------|-------------------|-------------------|
| REST POST `/api/v1/trade-plans` | `CreatePlanRequest` (Pydantic) | `position_size: Optional[float] = None` | `extra="forbid"` (existing) |
| REST PUT `/api/v1/trade-plans/{id}` | `UpdatePlanRequest` (Pydantic) | `position_size: Optional[float] = None` | `extra="forbid"` (existing) |
| MCP `create_trade_plan` | Zod schema (planning-tools.ts) | `position_size: z.number().optional()`, `shares_planned: z.number().int().optional()` | Zod default strips unknown |

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-1 | `TradePlan` entity has `position_size: Optional[float] = None` field | Spec (06i §PLAN-NOSIZE line 41) | N/A — additive field |
| AC-2 | `TradePlanModel` has `position_size = Column(Float, nullable=True)` | Local Canon (models.py pattern) | N/A — schema addition |
| AC-3 | ALTER TABLE migration adds `position_size` column for existing DBs | Local Canon (main.py L161-166 pattern) | DB without column still works |
| AC-4 | `CreatePlanRequest` and `UpdatePlanRequest` accept `position_size` | Spec (06i §PLAN-NOSIZE line 44-45) | Extra fields rejected (existing `extra="forbid"`) |
| AC-5 | `PlanResponse` includes `position_size` | Spec (06i §PLAN-NOSIZE line 46) | Missing field returns `null` |
| AC-6 | `_to_response()` serializes `position_size` | Local Canon (plans.py L270-298 pattern) | N/A |
| AC-7 | MCP `create_trade_plan` schema includes `shares_planned` and `position_size` optional fields | Spec (06i §PLAN-NOSIZE line 48), Standard M2 | Omitting fields creates plan with nulls |
| AC-8 | MCP tool body includes both fields in POST payload | Standard M2 (API↔MCP parity) | N/A |

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| `position_size` field type and semantics | Spec | `Optional[float]` — total dollar value of position |
| `shares_planned` already exists in entity/model/API | Local Canon | Verified: entity L141, model L144, API L64/104/124/289 |
| `shares_planned` missing from MCP tools | Spec + M2 | Add to `create_trade_plan` Zod schema + body |
| ALTER TABLE pattern for new columns | Local Canon | Follow main.py L161-166 precedent |
| `shares` → `shares_planned` naming | Human-Approved (pomera #795) | Repo standardized on `shares_planned` in MEU-70b. Spec/known-issues/BUILD_PLAN updated to match. No alias. |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| [entities.py](file:///p:/zorivest/packages/core/src/zorivest_core/domain/entities.py) | modify | Add `position_size: Optional[float] = None` to `TradePlan` |
| [models.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/database/models.py) | modify | Add `position_size = Column(Float, nullable=True)` to `TradePlanModel` |
| [main.py](file:///p:/zorivest/packages/api/src/zorivest_api/main.py) | modify | Add `ALTER TABLE trade_plans ADD COLUMN position_size REAL` migration |
| [plans.py](file:///p:/zorivest/packages/api/src/zorivest_api/routes/plans.py) | modify | Add `position_size` to Create/Update/Response schemas + `_to_response()` |
| [planning-tools.ts](file:///p:/zorivest/mcp-server/src/tools/planning-tools.ts) | modify | Add `shares_planned` + `position_size` to `create_trade_plan` schema + body |
| [test_api_plans.py](file:///p:/zorivest/tests/unit/test_api_plans.py) | modify | Add tests for position_size round-trip |

---

### Sub-MEU B: Watchlist Visual Redesign

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-9 | Dark trading palette (bg `#131722`, rows `#1a1e2e`) applied via CSS variables | Spec (06i §2 design tokens) | N/A — visual |
| AC-10 | Professional data table with columns: Ticker, Last Price, Chg $, Chg %, Volume | Spec (06i §1 column hierarchy) | Empty watchlist shows placeholder row |
| AC-11 | Gain/loss coloring: green `#26A69A` for positive, red `#EF5350` for negative, muted for zero | Spec (06i §2 token table, §5 coloring rules) | Zero change uses muted color |
| AC-12 | ▲/▼ arrows prefix on change values, ±sign on both Chg columns | Spec (06i §5 L104-112) | Negative value shows ▼ and minus sign |
| AC-13 | Typography: Inter font, `tabular-nums`, right-aligned numerics | Spec (06i §3 typography) | N/A — visual |
| AC-14 | 32px rows, zebra striping (odd row alternate bg), hover highlights | Spec (06i §4 layout) | N/A — visual |
| AC-15 | Volume formatted as abbreviated (1.2M, 45.3K, 0 for null) | Spec (06i §1 L18) | null volume shows "—" |
| AC-16 | Sticky header row | Spec (06i §4 L93) | N/A — visual |
| AC-17 | "Updated Xs ago" freshness indicator | Spec (06i §6 L131) | No quote data shows "No data" |
| AC-18 | Colorblind-safe toggle (blue `#2962FF` / orange `#FF6D00` alternate palette) | Spec (06i §7 L143-156) | Toggle persists across page navigation |
| AC-19 | Quote polling with stagger interval `4000 + Math.random() * 1000` ms | Spec (06i §6 L134) | N/A — network behavior |
| AC-29 | `ui.watchlist.colorblind_mode` registered in `SETTINGS_REGISTRY` with `bool` type, category `ui`, default `false` | Local Canon (settings.py registry pattern) | Unknown key returns 404 from Settings API |

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| All CSS token values | Spec | 06i §2 — complete hex codes provided |
| Column order and content | Spec | 06i §1 — Ticker, Last, Chg $, Chg %, Vol |
| Coloring rules (gain/loss/zero) | Spec | 06i §5 — green/red/muted with arrows |
| Volume abbreviation format | Research-backed | Standard financial: K (thousands), M (millions), B (billions), one decimal |
| Colorblind toggle persistence | Local Canon | Register `ui.watchlist.colorblind_mode` in `SETTINGS_REGISTRY`, persist via Settings API |
| Stagger interval formula | Spec | 06i §6 L134 — `4000 + Math.random() * 1000` |
| Quote data structure | Local Canon | `MarketQuote` DTO: `price, change, change_pct, volume` (market_dtos.py L1-65) |
| Notes indicator in table | Spec | 06i §1 L19 — notes column with icon/indicator |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `ui/src/renderer/src/styles/watchlist-tokens.css` | new | Design token CSS variables for dark palette, typography, coloring |
| `ui/src/renderer/src/features/planning/WatchlistTable.tsx` | new | Professional data table component with all column formatting |
| `ui/src/renderer/src/features/planning/watchlist-utils.ts` | new | Utility functions: formatVolume, formatPrice, getChangeColor, formatFreshness |
| [WatchlistPage.tsx](file:///p:/zorivest/ui/src/renderer/src/features/planning/WatchlistPage.tsx) | modify | Integrate WatchlistTable, add colorblind toggle, update quote hook stagger |
| `ui/src/renderer/src/features/planning/__tests__/watchlist-utils.test.ts` | new | Unit tests for formatting utilities |
| [planning.test.tsx](file:///p:/zorivest/ui/src/renderer/src/features/planning/__tests__/planning.test.tsx) | modify | Add tests for WatchlistTable rendering, coloring, and toggle |
| [settings.py](file:///p:/zorivest/packages/core/src/zorivest_core/domain/settings.py) | modify | Register `ui.watchlist.colorblind_mode` in `SETTINGS_REGISTRY` |
| [test_settings_registry.py](file:///p:/zorivest/tests/unit/test_settings_registry.py) | modify | Add test for new setting key |

---

### Sub-MEU C: PLAN-NOSIZE GUI + Calculator Write-Back

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-20 | Trade Plan detail panel shows readonly `position_size` field (computed, not editable). Existing `shares_planned` field stays **editable** (MEU-70b approved behavior). | Spec (06i §PLAN-NOSIZE line 50-51), Human-Approved (MEU-70b) | Field shows "—" when null |
| AC-21 | Position Calculator "Apply to Plan" button dispatches `zorivest:calculator-apply` event with payload `{ shares_planned: number, position_size: number }` | Local Canon (G11 custom event pattern), Spec (06i §PLAN-NOSIZE line 53) | Button disabled when no plan is being edited |
| AC-22 | TradePlanPage listens for `zorivest:calculator-apply` and populates the existing editable `shares_planned` + new readonly `position_size` | Local Canon (G11 AppShell event pattern) | Event without payload is ignored |
| AC-23 | Applied values are included in PUT request when saving plan | Spec (06i §PLAN-NOSIZE line 54) | N/A — follows existing form save flow |

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| Calculator write-back mechanism | Local Canon | Use `zorivest:calculator-apply` CustomEvent following G11 pattern (same as `zorivest:open-calculator`) |
| Where position_size displays | Spec | 06i §PLAN-NOSIZE line 50-51: Trade Plan detail panel, readonly |
| `shares_planned` editability | Human-Approved (pomera #795) | MEU-70b shipped editable field at TradePlanPage.tsx L617-630. Must not regress. |
| Apply button location | Local Canon | Inside PositionCalculatorModal, below existing results — follows existing button patterns |
| Event payload shape | Local Canon + Human-Approved (pomera #795) | `{ shares_planned: number, position_size: number }` — uses repo-standard field names |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| [TradePlanPage.tsx](file:///p:/zorivest/ui/src/renderer/src/features/planning/TradePlanPage.tsx) | modify | Add readonly `position_size` display + calculator-apply listener for existing editable `shares_planned` field |
| [PositionCalculatorModal.tsx](file:///p:/zorivest/ui/src/renderer/src/features/planning/PositionCalculatorModal.tsx) | modify | Add "Apply to Plan" button that dispatches calculator-apply event |
| [planning.test.tsx](file:///p:/zorivest/ui/src/renderer/src/features/planning/__tests__/planning.test.tsx) | modify | Add tests for calculator write-back and readonly position_size display |

---

### Sub-MEU D: Post-Implementation Maintenance

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-24 | OpenAPI spec regenerated after API schema changes | Standard G8 | `--check` mode confirms no drift |
| AC-25 | `docs/BUILD_PLAN.md` MEU-70a status updated from ⬜ to ✅ | Workflow (create-plan Step 4) | Grep confirms updated row |
| AC-26 | MEU registry updated with MEU-70a row | Workflow (create-plan Step 6.2) | Row with ✅ status present |
| AC-27 | `[PLAN-NOSIZE]` removed from `known-issues.md` | Workflow (session discipline) | Grep confirms removal |
| AC-28 | MCP dist rebuilt after source changes | Standard M4 | `npm run build` succeeds |

---

## Out of Scope

- **Batch quote endpoint** — remains individual polling per spec §6; batch API is a future MEU
- **Level 2 features** (mini-charts, sector grouping, alerts) — explicitly deferred by spec §8
- **Watchlist reordering** (drag-and-drop row reorder) — not in Level 1 scope
- **Notes editing in table** — table shows notes *indicator* only; editing remains in detail panel
- **Dark mode theme for entire app** — tokens scoped to watchlist table only

---

## BUILD_PLAN.md Audit

MEU-70a row already exists at `docs/BUILD_PLAN.md` L262 with status ⬜. After implementation:
- Update status from ⬜ to ✅
- Remove ~~[BOUNDARY-GAP]~~ prerequisite note (satisfied per critical review verification)

```powershell
rg "MEU-70a" docs/BUILD_PLAN.md *> C:\Temp\zorivest\buildplan-70a.txt; Get-Content C:\Temp\zorivest\buildplan-70a.txt
```

---

## Verification Plan

### 1. Python Backend Tests
```powershell
uv run pytest tests/unit/test_api_plans.py -x --tb=short -v *> C:\Temp\zorivest\pytest-plans.txt; Get-Content C:\Temp\zorivest\pytest-plans.txt | Select-Object -Last 40
```

### 2. Python Type Checks
```powershell
uv run pyright packages/ *> C:\Temp\zorivest\pyright.txt; Get-Content C:\Temp\zorivest\pyright.txt | Select-Object -Last 30
```

### 3. Python Lint
```powershell
uv run ruff check packages/ *> C:\Temp\zorivest\ruff.txt; Get-Content C:\Temp\zorivest\ruff.txt | Select-Object -Last 20
```

### 4. TypeScript Type Checks
```powershell
cd ui; npx tsc --noEmit *> C:\Temp\zorivest\tsc.txt; Get-Content C:\Temp\zorivest\tsc.txt | Select-Object -Last 30
```

### 5. TypeScript Unit Tests
```powershell
cd ui; npx vitest run *> C:\Temp\zorivest\vitest.txt; Get-Content C:\Temp\zorivest\vitest.txt | Select-Object -Last 40
```

### 6. MCP Build
```powershell
cd mcp-server; npm run build *> C:\Temp\zorivest\mcp-build.txt; Get-Content C:\Temp\zorivest\mcp-build.txt | Select-Object -Last 20
```

### 7. OpenAPI Drift Check
```powershell
uv run python tools/export_openapi.py --check openapi.committed.json *> C:\Temp\zorivest\openapi-check.txt; Get-Content C:\Temp\zorivest\openapi-check.txt
```

### 8. MEU Gate
```powershell
uv run python tools/validate_codebase.py --scope meu *> C:\Temp\zorivest\validate.txt; Get-Content C:\Temp\zorivest\validate.txt | Select-Object -Last 50
```

---

## Open Questions

None — all behaviors resolved. Naming conflict (`shares` vs `shares_planned`) resolved as Human-Approved per MEU-70b.

---

## Research References

- [Watchlist Visual Design Spec](file:///p:/zorivest/_inspiration/_watchlist-visual-design-research/watchlist-design-spec.md) — Detailed design research
- [Build Plan 06i](file:///p:/zorivest/docs/build-plan/06i-gui-watchlist-visual.md) — Source spec
- [Emerging Standards](file:///p:/zorivest/.agent/docs/emerging-standards.md) — M2, M4, G5, G6, G8, G11, G14, UX2 applied
- [Market DTOs](file:///p:/zorivest/packages/core/src/zorivest_core/application/market_dtos.py) — MarketQuote structure
