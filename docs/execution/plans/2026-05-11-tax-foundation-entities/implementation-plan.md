---
project: "2026-05-11-tax-foundation-entities"
date: "2026-05-11"
source: "docs/build-plan/build-priority-matrix.md §3A rows 50-51"
meus: ["MEU-123", "MEU-124"]
status: "draft"
template_version: "2.0"
---

# Implementation Plan: Tax Foundation Entities

> **Project**: `2026-05-11-tax-foundation-entities`
> **Build Plan Section(s)**: [build-priority-matrix.md §3A](../../build-plan/build-priority-matrix.md) rows 50–51, [domain-model-reference.md §Tax Estimator](../../build-plan/domain-model-reference.md) lines 346–401
> **Status**: `draft`

---

## Goal

Implement the foundational domain entities for the Phase 3A Core Tax Engine. This project creates the `TaxLot` and `TaxProfile` entities, their associated enums (`CostBasisMethod`, `FilingStatus`, `WashSaleMatchingMethod`), repository ports, SQLAlchemy persistence models, and in-memory stubs — establishing the data layer that all subsequent tax MEUs (125–129) depend on.

This is **Session 1** of the 3-session Phase 3A build, as documented in the [session plan](file:///C:/Users/Mat/.gemini/antigravity/brain/0b93626a-3c9d-4014-bc8d-3a06692e9edb/phase3a-session-plan.md).

---

## Pre-Flight Domain Audit Summary

> [!NOTE]
> **Pre-flight domain audit — resolved (spec-backed deferrals):**
>
> The Session 1 canon requires "pre-flight risks resolved" before entity implementation. The audit identified 3 findings about the `Trade` entity (option fields, DRIP tracking, fill granularity). All 3 are **genuinely irrelevant to MEU-123/124** — these MEUs define new entities (`TaxLot`, `TaxProfile`) that do not consume Trade fields.
>
> **Scope resolution (Spec-backed):** The canonical [domain-model-reference.md L353-401](../../build-plan/domain-model-reference.md) defines TaxLot with 11 stored fields + 2 computed properties, and TaxProfile with 14 fields. None of the 3 audit findings (option fields, DRIP tracking, fill granularity) appear in the TaxLot or TaxProfile spec. The deferrals are therefore spec-backed scope boundaries — the spec decides what is in and out of scope — not human approval gates. See §Pre-Flight Domain Audit Findings below for per-finding resolution and future MEU assignments.

---

## Proposed Changes

### MEU-123: TaxLot Entity + CostBasisMethod Enum

#### Boundary Inventory

No external input surfaces. TaxLot is a pure domain entity — external inputs arrive via API routes in Phase 3E (MEU-148).

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-1 | `CostBasisMethod` enum has exactly 8 values: FIFO, LIFO, HIFO, SPEC_ID, MAX_LT_GAIN, MAX_LT_LOSS, MAX_ST_GAIN, MAX_ST_LOSS | Spec: [domain-model-reference.md L395-397](../../build-plan/domain-model-reference.md) | Constructing with invalid value raises ValueError |
| AC-2 | `TaxLot` entity has 11 stored fields + 2 computed properties (`holding_period_days`, `is_long_term`) matching domain model reference. SQLAlchemy model stores only the 11 source fields — computed properties are Python-only, not database columns. | Spec: [domain-model-reference.md L353-366](../../build-plan/domain-model-reference.md) | Missing required field raises TypeError |
| AC-3 | `holding_period_days` is computed from `open_date` and `close_date` (or today if open) | Spec: [domain-model-reference.md L364](../../build-plan/domain-model-reference.md) | Open lot with future open_date returns 0 |
| AC-4 | `is_long_term` returns True when `holding_period_days >= 366` | Spec: [domain-model-reference.md L365](../../build-plan/domain-model-reference.md) | 365 days → False; 366 days → True (boundary test) |
| AC-5 | `TaxLotRepository` protocol with get, save, update, list_for_account, list_filtered, count_filtered, delete | Local Canon: [ports.py](../../../../packages/core/src/zorivest_core/application/ports.py) existing patterns | N/A (protocol definition) |
| AC-6 | `TaxLotModel` SQLAlchemy model maps to `tax_lots` table with correct column types | Local Canon: [models.py](../../../../packages/infrastructure/src/zorivest_infra/database/models.py) patterns | Model with missing FK constraint fails on commit |
| AC-7 | ~~`InMemoryTaxLotRepository` stub passes all repository contract tests~~ **RETIRED**: InMemory stubs retired project-wide per MEU-90a (see `stubs.py` retirement note, `meu-registry.md` MEU-90a entry). | Local Canon: [stubs.py](../../../../packages/api/src/zorivest_api/stubs.py) patterns | N/A — blocked |

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| TaxLot field definitions (11 stored fields + 2 computed properties) | Spec | domain-model-reference.md L353-366. `holding_period_days` and `is_long_term` are computed at runtime, not persisted. |
| CostBasisMethod 8 values | Spec | domain-model-reference.md L395-397 |
| holding_period_days computation | Spec | "computed from open/close dates" L364 |
| is_long_term threshold (366 days) | Spec | "holding_period >= 366 days" L365 |
| lot_id format | Local Canon | UUID string, matching `exec_id` pattern |
| linked_trade_ids storage | Spec | list[str] FK → Trade.exec_id |
| Repository port shape | Local Canon | Follows TradeRepository / TradePlanRepository patterns |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `packages/core/src/zorivest_core/domain/enums.py` | modify | Add `CostBasisMethod` enum (8 values) |
| `packages/core/src/zorivest_core/domain/entities.py` | modify | Add `TaxLot` dataclass with computed properties |
| `packages/core/src/zorivest_core/application/ports.py` | modify | Add `TaxLotRepository` protocol + extend `UnitOfWork` |
| `packages/infrastructure/src/zorivest_infra/database/models.py` | modify | Add `TaxLotModel` |
| `packages/infrastructure/src/zorivest_infra/database/repositories.py` | modify | Add `SqlTaxLotRepository` |
| `packages/api/src/zorivest_api/stubs.py` | modify | Add `InMemoryTaxLotRepository` |
| `tests/unit/test_tax_entities.py` | new | TaxLot construction, validation, computed properties |
| `tests/unit/test_tax_enums.py` | new | CostBasisMethod membership, str coercion |
| `tests/integration/test_tax_repo_integration.py` | new | TaxLot repo CRUD against in-memory SQLite |

---

### MEU-124: TaxProfile Entity + FilingStatus Enum

#### Boundary Inventory

No external input surfaces. TaxProfile is stored as a settings entity — external inputs arrive via API routes in Phase 3E (MEU-148).

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-1 | `FilingStatus` enum has exactly 4 values: SINGLE, MARRIED_JOINT, MARRIED_SEPARATE, HEAD_OF_HOUSEHOLD | Spec: [domain-model-reference.md L382-383](../../build-plan/domain-model-reference.md) | Invalid status raises ValueError |
| AC-2 | `WashSaleMatchingMethod` enum has exactly 2 values: CONSERVATIVE, AGGRESSIVE | Spec: [domain-model-reference.md L391-394](../../build-plan/domain-model-reference.md) | Invalid method raises ValueError |
| AC-3 | `TaxProfile` entity has 14 fields matching domain model reference | Spec: [domain-model-reference.md L381-401](../../build-plan/domain-model-reference.md) | Missing required field raises TypeError |
| AC-4 | `TaxProfileRepository` protocol with get, save, update, get_for_year | Local Canon: [ports.py](../../../../packages/core/src/zorivest_core/application/ports.py) patterns | N/A |
| AC-5 | `TaxProfileModel` SQLAlchemy model maps to `tax_profiles` table | Local Canon: [models.py](../../../../packages/infrastructure/src/zorivest_infra/database/models.py) patterns | N/A |
| AC-6 | ~~`InMemoryTaxProfileRepository` stub passes all repository contract tests~~ **RETIRED**: InMemory stubs retired project-wide per MEU-90a (see `stubs.py` retirement note, `meu-registry.md` MEU-90a entry). | Local Canon: [stubs.py](../../../../packages/api/src/zorivest_api/stubs.py) patterns | N/A — blocked |

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| TaxProfile field definitions (14 fields) | Spec | domain-model-reference.md L381-401 |
| FilingStatus 4 values | Spec | domain-model-reference.md L382-383 |
| WashSaleMatchingMethod 2 values | Spec | domain-model-reference.md L391-394 |
| Default values for boolean flags | Spec | L398-401 explicit defaults |
| TaxProfile PK strategy | Local Canon | Composite PK (tax_year) since one profile per year, or auto-increment ID with unique(tax_year). Decision: auto-increment with unique tax_year constraint — matches Account/TradePlan pattern |
| Repository port shape | Local Canon | Simplified — get, save, update, get_for_year |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `packages/core/src/zorivest_core/domain/enums.py` | modify | Add `FilingStatus`, `WashSaleMatchingMethod` enums |
| `packages/core/src/zorivest_core/domain/entities.py` | modify | Add `TaxProfile` dataclass |
| `packages/core/src/zorivest_core/application/ports.py` | modify | Add `TaxProfileRepository` protocol + extend `UnitOfWork` |
| `packages/infrastructure/src/zorivest_infra/database/models.py` | modify | Add `TaxProfileModel` |
| `packages/infrastructure/src/zorivest_infra/database/repositories.py` | modify | Add `SqlTaxProfileRepository` |
| `packages/api/src/zorivest_api/stubs.py` | modify | Add `InMemoryTaxProfileRepository` |
| `tests/unit/test_tax_entities.py` | modify | TaxProfile construction, validation |
| `tests/unit/test_tax_enums.py` | modify | FilingStatus, WashSaleMatchingMethod membership |
| `tests/integration/test_tax_repo_integration.py` | modify | TaxProfile repo CRUD against in-memory SQLite |

---

## Out of Scope

- TaxService method implementations (MEU-125+)
- Cost-basis lot assignment algorithms (MEU-125)
- ST/LT gains calculation logic (MEU-126)
- Capital loss carryforward logic (MEU-127)
- Options assignment pairing (MEU-128)
- YTD P&L aggregation (MEU-129)
- WashSaleChain entity (Phase 3B)
- QuarterlyEstimate entity (Phase 3D)
- Tax API routes (Phase 3E, MEU-148)
- Tax MCP tools (Phase 3E, MEU-149)
- Tax GUI (Phase 3E, 06g-gui-tax.md)
- Alembic migration generation (deferred to persistence integration)

---

## Pre-Flight Domain Audit Findings

> [!NOTE]
> **Resolved findings — spec-backed deferrals (see §Pre-Flight Domain Audit Summary):**
>
> The session plan (L71-72, L75) requires pre-flight risks to be resolved in Session 1. Resolution means each risk has an explicit disposition: addressed in this project, or deferred to a named future MEU with documented rationale. All 3 findings below are resolved as out-of-scope deferrals because the canonical domain-model-reference.md (L353-401) does not include these fields in the TaxLot or TaxProfile entity specs.

| Finding | Impacts | Resolved To | Rationale |
|---------|---------|:-----------:|----------|
| Trade entity lacks option fields (strike, expiration, put_call, underlying) | MEU-128 (options assignment, S3) | Deferred → MEU-128 | Option fields are consumed by lot-assignment logic (MEU-128), not by entity definitions (MEU-123/124). Adding them here would be premature — the field shape depends on MEU-128's FIC. |
| Trade entity lacks DRIP acquisition source tracking | Phase 3B (wash sale DRIP detection) | Deferred → Phase 3B | DRIP wash detection requires an `acquisition_source` enum on Trade. This is a Phase 3B concern, not a 3A entity concern. |
| Trade entity treats each exec_id as a single fill (no fill-level granularity) | MEU-125 (lot tracking, S2) | Accepted (no change needed) | Domain model reference (L366) specifies `TaxLot.linked_trade_ids: list[str]` linking to `Trade.exec_id`. The spec treats each trade as a single fill — no fill-level granularity is required by the canonical spec. |

---

## BUILD_PLAN.md Audit

This project will require updating MEU-123 and MEU-124 status from ⬜ to ✅ in `docs/BUILD_PLAN.md` lines 614-615 upon completion. No stale references found — the MEU slugs and descriptions match the build-priority-matrix.

```powershell
rg "MEU-123|MEU-124" docs/BUILD_PLAN.md  # Expected: 2 matches (status rows)
```

---

## Verification Plan

### 1. Type Check
```powershell
uv run pyright packages/ *> C:\Temp\zorivest\pyright.txt; Get-Content C:\Temp\zorivest\pyright.txt | Select-Object -Last 30
```

### 2. Lint
```powershell
uv run ruff check packages/ *> C:\Temp\zorivest\ruff.txt; Get-Content C:\Temp\zorivest\ruff.txt | Select-Object -Last 20
```

### 3. Unit Tests
```powershell
uv run pytest tests/unit/test_tax_entities.py tests/unit/test_tax_enums.py -x --tb=short -v *> C:\Temp\zorivest\pytest-tax-unit.txt; Get-Content C:\Temp\zorivest\pytest-tax-unit.txt | Select-Object -Last 40
```

### 4. Integration Tests
```powershell
uv run pytest tests/integration/test_tax_repo_integration.py -x --tb=short -v *> C:\Temp\zorivest\pytest-tax-integ.txt; Get-Content C:\Temp\zorivest\pytest-tax-integ.txt | Select-Object -Last 40
```

### 5. Anti-Placeholder Scan
```powershell
rg "TODO|FIXME|NotImplementedError" packages/core/src/zorivest_core/domain/entities.py packages/core/src/zorivest_core/domain/enums.py packages/core/src/zorivest_core/application/ports.py *> C:\Temp\zorivest\placeholder.txt; Get-Content C:\Temp\zorivest\placeholder.txt
```

### 6. Full Regression
```powershell
uv run pytest tests/ -x --tb=short -v *> C:\Temp\zorivest\pytest-full.txt; Get-Content C:\Temp\zorivest\pytest-full.txt | Select-Object -Last 40
```

### 7. MEU Gate
```powershell
uv run python tools/validate_codebase.py --scope meu *> C:\Temp\zorivest\validate.txt; Get-Content C:\Temp\zorivest\validate.txt | Select-Object -Last 50
```

---

## Open Questions

> [!WARNING]
> **No blocking questions identified.** All entity fields, enum values, and repository shapes are fully specified in the domain model reference and follow established codebase patterns.

---

## Research References

- [domain-model-reference.md §Tax Estimator](../../build-plan/domain-model-reference.md) — Lines 346-401 (TaxLot, TaxProfile, CostBasisMethod, FilingStatus)
- [build-priority-matrix.md §3A](../../build-plan/build-priority-matrix.md) — Rows 50-51
- [03-service-layer.md §TaxService](../../build-plan/03-service-layer.md) — Lines 336-386 (service contract for downstream MEUs)
- [phase3a-session-plan.md](file:///C:/Users/Mat/.gemini/antigravity/brain/0b93626a-3c9d-4014-bc8d-3a06692e9edb/phase3a-session-plan.md) — Session division and context load model
