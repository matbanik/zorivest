# Trade Report Entity + Service + API + MCP Tools

> Project: `trade-report`
> MEUs: 52 (TradeReport entity + service), 53 (MCP tools + API routes)
> Date: 2026-03-11
> Build Plan: [01-domain-layer.md](../../../build-plan/01-domain-layer.md) §entities; [04a-api-trades.md](../../../build-plan/04a-api-trades.md) §Trade report routes; [05c-mcp-trade-analytics.md](../../../build-plan/05c-mcp-trade-analytics.md) §Report Tools

---

## Proposed Changes

### MEU-52: TradeReport Entity + Service (bp01 §entities, bp17 matrix)

#### [MODIFY] [enums.py](file:///p:/zorivest/packages/core/src/zorivest_core/domain/enums.py)

Add two new enums and grade ↔ int conversion maps:

```python
class QualityGrade(StrEnum):
    """Trade quality rating — maps to int 1-5 for storage."""
    A = "A"  # Excellent (5)
    B = "B"  # Good (4)
    C = "C"  # Average (3)
    D = "D"  # Below average (2)
    F = "F"  # Failing (1)

class EmotionalState(StrEnum):
    """Trader's emotional state during execution.
    Superset of MCP spec (05c L585-587) + GUI spec (06b L332).
    """
    CALM = "calm"              # MCP + GUI
    ANXIOUS = "anxious"        # MCP + GUI (implied)
    FEARFUL = "fearful"        # MCP + GUI
    GREEDY = "greedy"          # MCP + GUI
    FRUSTRATED = "frustrated"  # MCP
    CONFIDENT = "confident"    # MCP + GUI
    NEUTRAL = "neutral"        # MCP
    IMPULSIVE = "impulsive"    # GUI
    HESITANT = "hesitant"      # GUI

# Grade ↔ int conversion (used by API/MCP layers)
QUALITY_INT_MAP: dict[str, int] = {"A": 5, "B": 4, "C": 3, "D": 2, "F": 1}
QUALITY_GRADE_MAP: dict[int, str] = {v: k for k, v in QUALITY_INT_MAP.items()}
```

#### [MODIFY] [entities.py](file:///p:/zorivest/packages/core/src/zorivest_core/domain/entities.py)

Add `TradeReport` dataclass. Update `Trade.report` type from `Optional[object]` to `Optional[TradeReport]`:

```python
@dataclass
class TradeReport:
    """Post-trade review and meta-analysis for a completed trade."""
    id: int
    trade_id: str               # FK → Trade.exec_id (unique)
    setup_quality: int          # 1-5 rating
    execution_quality: int      # 1-5 rating
    followed_plan: bool
    emotional_state: str        # EmotionalState value
    created_at: datetime
    lessons_learned: str = ""
    tags: list[str] = field(default_factory=list)
    images: list[ImageAttachment] = field(default_factory=list)
```

#### [MODIFY] [ports.py](file:///p:/zorivest/packages/core/src/zorivest_core/application/ports.py)

Add `TradeReportRepository` Protocol and `trade_reports` attribute to `UnitOfWork`:

```python
class TradeReportRepository(Protocol):
    """Repository for TradeReport entities."""
    def get_for_trade(self, trade_id: str) -> Optional[TradeReport]: ...
    def save(self, report: TradeReport) -> int: ...
    def update(self, report: TradeReport) -> None: ...
    def delete_for_trade(self, trade_id: str) -> None: ...
```

#### [MODIFY] [repositories.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/database/repositories.py)

Add `_report_to_model`, `_model_to_report` mappers and `SqlAlchemyTradeReportRepository`:

- `get_for_trade(trade_id)` — query by `trade_id`, return domain entity or `None`
- `save(report)` — insert new `TradeReportModel`, return `id`. Tags stored as JSON text via `json.dumps`/`json.loads`.
- `update(report)` — merge existing model
- `delete_for_trade(trade_id)` — delete by `trade_id`

#### [MODIFY] [unit_of_work.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/database/unit_of_work.py)

Import `SqlAlchemyTradeReportRepository`, add `trade_reports` attribute in `__enter__`.

#### [NEW] [report_service.py](file:///p:/zorivest/packages/core/src/zorivest_core/services/report_service.py)

```python
class ReportService:
    """Trade documentation: post-trade reports.
    Canon: 03-service-layer.md L387-409 (absorbs TradeReportService + TradePlanService).
    This MEU implements report-only methods; plan/journal methods deferred to MEU-66/117.

    Method names follow 04a-api-trades.md L126-151 (authoritative, newer):
      create(), get_for_trade(), update(), delete()
    Note: 03-service-layer.md L399-400 uses older create_report()/get_report()
    which is stale on this point — 04a is the downstream consumer and takes precedence.
    """
    def __init__(self, uow: UnitOfWork) -> None: ...
    def create(self, trade_id: str, report_data: dict) -> TradeReport:
        """Create report. Validates trade exists. Raises BusinessRuleError if report already exists."""
    def get_for_trade(self, trade_id: str) -> TradeReport:
        """Get report by trade_id. Raises NotFoundError."""
    def update(self, trade_id: str, report_data: dict) -> TradeReport:
        """Update existing report. Raises NotFoundError."""
    def delete(self, trade_id: str) -> None:
        """Delete report. Raises NotFoundError if no report exists."""
```

---

### MEU-53: TradeReport API Routes + MCP Tools (bp04a §Trade report routes, bp05c §Report Tools)

#### [MODIFY] [dependencies.py](file:///p:/zorivest/packages/api/src/zorivest_api/dependencies.py)

Add `get_report_service` dependency provider.

#### [MODIFY] [trades.py](file:///p:/zorivest/packages/api/src/zorivest_api/routes/trades.py)

Add report routes per 04a spec:

| Method | Path | Status | Description |
|--------|------|--------|-------------|
| `POST` | `/{exec_id}/report` | 201 | Create report |
| `GET` | `/{exec_id}/report` | 200/404 | Get report |
| `PUT` | `/{exec_id}/report` | 200/404 | Update report |
| `DELETE` | `/{exec_id}/report` | 204 | Delete report |

Grade ↔ int conversion at API boundary using `QUALITY_INT_MAP` / `QUALITY_GRADE_MAP`.

#### [MODIFY] [trade-tools.ts](file:///p:/zorivest/mcp-server/src/tools/trade-tools.ts)

Add two MCP tools per 05c spec:

- `create_report` — POST to `/trades/{exec_id}/report`. `destructiveHint: false` per 05c L609 — uses `withMetrics` only (not `withConfirmation`).
- `get_report_for_trade` — GET from `/trades/{exec_id}/report`. Read-only, `withMetrics` only.

#### [MODIFY] [BUILD_PLAN.md](file:///p:/zorivest/docs/BUILD_PLAN.md)

Update MEU-52 and MEU-53 status from ⬜ to ✅ after completion. Verify 04a implementation status note is updated to reflect reports as implemented.

---

## Spec Sufficiency

### MEU-52: TradeReport Entity + Service

| Behavior / Contract | Source Type | Source | Resolved? | Notes |
|---|---|---|---|---|
| `TradeReport` entity fields | Spec | [domain-model-reference.md L50-60](../../../build-plan/domain-model-reference.md) | ✅ | id, trade_id, quality ratings, followed_plan, emotional_state, lessons_learned, tags, images, created_at |
| Quality field type: int 1-5 | Spec | [domain-model-reference.md L53-54](../../../build-plan/domain-model-reference.md) | ✅ | Domain uses int; API/MCP accept letter grades via adapter |
| `TradeReportModel` already exists | Local Canon | [models.py L91-104](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/database/models.py) | ✅ | Integer columns for quality, FK to trades |
| `Trade.report` field exists as placeholder | Local Canon | [entities.py L67](file:///p:/zorivest/packages/core/src/zorivest_core/domain/entities.py) | ✅ | `Optional[object] = None` → update to `Optional[TradeReport]` |
| EmotionalState enum values | Spec + Local Canon | [05c L585-587](../../../build-plan/05c-mcp-trade-analytics.md), [06b L332](../../../build-plan/06b-gui-trades.md) | ✅ | 9-value superset: calm, anxious, fearful, greedy, frustrated, confident, neutral (MCP) + impulsive, hesitant (GUI) |
| Quality grade ↔ int mapping | Human-approved | This plan | ✅ | A=5, B=4, C=3, D=2, F=1 — bridges domain-model-ref (int) and API/MCP specs (letter) |
| One report per trade (unique constraint) | Spec | [models.py L95](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/database/models.py) | ✅ | `unique=True` on `trade_id` FK |
| Tags stored as JSON text | Local Canon | [models.py L101](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/database/models.py) | ✅ | `Column(Text)` for JSON array |

### MEU-53: TradeReport API Routes + MCP Tools

| Behavior / Contract | Source Type | Source | Resolved? | Notes |
|---|---|---|---|---|
| POST/GET/PUT/DELETE `/{exec_id}/report` | Spec | [04a-api-trades.md L116-151](../../../build-plan/04a-api-trades.md) | ✅ | Full route signatures and schemas |
| `CreateReportRequest` schema | Spec | [04a-api-trades.md L118-124](../../../build-plan/04a-api-trades.md) | ✅ | Quality grades, followed_plan, emotional_state, lessons, tags |
| `create_report` MCP tool | Spec | [05c-mcp-trade-analytics.md](../../../build-plan/05c-mcp-trade-analytics.md) | ✅ | Full tool spec with zod schema |
| `get_report_for_trade` MCP tool | Spec | [05c-mcp-trade-analytics.md](../../../build-plan/05c-mcp-trade-analytics.md) | ✅ | trade_id input, GET endpoint |
| MCP annotations and middleware | Spec | [05c L606-612](../../../build-plan/05c-mcp-trade-analytics.md) | ✅ | `create_report`: `destructiveHint: false`, `withMetrics` only; `get_report`: read-only |
| `_meta.toolset: "trade-analytics"` | Local Canon | existing trade-tools pattern | ✅ | Same toolset as other trade tools |
| Grade conversion at API boundary | Human-approved | This plan | ✅ | API accepts A-F, service stores 1-5 |

---

## Feature Intent Contracts (FICs)

### FIC-52: TradeReport Entity + Service

| AC | Description | Source |
|----|-------------|--------|
| AC-1 | `TradeReport` dataclass exists with fields: id, trade_id, setup_quality (int), execution_quality (int), followed_plan (bool), emotional_state (str), created_at (datetime), lessons_learned (str), tags (list[str]), images (list[ImageAttachment]) | Spec |
| AC-2 | `Trade.report` type is `Optional[TradeReport]` (not `Optional[object]`) | Spec |
| AC-3 | `QualityGrade` enum has members A, B, C, D, F. `QUALITY_INT_MAP` maps A→5, B→4, C→3, D→2, F→1 | Human-approved |
| AC-4 | `EmotionalState` enum has 9 members: calm, anxious, fearful, greedy, frustrated, confident, neutral, impulsive, hesitant (MCP+GUI superset) | Spec + Local Canon |
| AC-5 | `TradeReportRepository` Protocol defines: `get_for_trade`, `save`, `update`, `delete_for_trade` | Spec |
| AC-6 | `UnitOfWork` Protocol includes `trade_reports: TradeReportRepository` attribute | Spec |
| AC-7 | `SqlAlchemyTradeReportRepository` implements all 4 methods using existing `TradeReportModel` | Local Canon |
| AC-8 | Tags serialized as JSON text (`json.dumps`/`json.loads`) | Local Canon |
| AC-9 | `SqlAlchemyUnitOfWork.__enter__` creates `trade_reports` repo | Local Canon |
| AC-10 | `ReportService.create()` validates trade exists, rejects duplicate report | Spec |
| AC-11 | `ReportService.get_for_trade()` raises `NotFoundError` when no report exists | Spec |
| AC-12 | `ReportService.update()` updates fields on existing report | Spec |
| AC-13 | `ReportService.delete()` removes report for trade | Spec |
| AC-14 | `TestModuleIntegrity.test_module_has_expected_classes` updated to include `TradeReport` | Local Canon |

### FIC-53: TradeReport API Routes + MCP Tools

| AC | Description | Source |
|----|-------------|--------|
| AC-1 | `POST /{exec_id}/report` returns 201 with created report (grades converted int→letter) | Spec |
| AC-2 | `GET /{exec_id}/report` returns 200 with report or 404 if not found | Spec |
| AC-3 | `PUT /{exec_id}/report` returns 200 with updated report or 404 | Spec |
| AC-4 | `DELETE /{exec_id}/report` returns 204 | Spec |
| AC-5 | API accepts letter grades (A-F), converts to int (1-5) via `QUALITY_INT_MAP` | Human-approved |
| AC-6 | API returns letter grades in response via `QUALITY_GRADE_MAP` | Human-approved |
| AC-7 | `create_report` MCP tool POSTs to `/trades/{id}/report` with correct payload | Spec |
| AC-8 | `get_report_for_trade` MCP tool GETs from `/trades/{id}/report` | Spec |
| AC-9 | `create_report` uses `withMetrics` only — `destructiveHint: false` per 05c L609 (no `withConfirmation`) | Spec |
| AC-10 | `get_report_for_trade` is read-only, `withMetrics` only | Local Canon |
| AC-11 | Both MCP tools have `_meta.toolset: "trade-analytics"` and correct annotations | Local Canon |
| AC-12 | Both MCP tools return `{content: [{type: "text", text: JSON}]}` | Local Canon |
| AC-13 | `get_report_service` dependency provider added to `dependencies.py` | Spec |
| AC-14 | `BUILD_PLAN.md` MEU-52/53 status updated from ⬜ to ✅ | Local Canon |

---

## Task Table

| # | Task | owner_role | Deliverable | Validation | Status |
|---|------|------------|-------------|------------|--------|
| 0 | Scope project, verify specs, create plan | orchestrator | `implementation-plan.md` | `Test-Path docs/execution/plans/2026-03-11-trade-report/implementation-plan.md` | ⬜ |
| 1 | Write entity + enum tests (RED) | coder | `test_entities.py` additions | `uv run pytest tests/unit/test_entities.py -v` — new tests FAIL | ⬜ |
| 2 | Add `QualityGrade`, `EmotionalState` enums + maps | coder | `enums.py` | `uv run python -c "from zorivest_core.domain.enums import QualityGrade, EmotionalState, QUALITY_INT_MAP"` | ⬜ |
| 3 | Add `TradeReport` entity, update `Trade.report` type | coder | `entities.py` | `uv run python -c "from zorivest_core.domain.entities import TradeReport"` | ⬜ |
| 4 | Add `TradeReportRepository` port + UoW attribute | coder | `ports.py` | `uv run python -c "from zorivest_core.application.ports import TradeReportRepository"` | ⬜ |
| 5 | Write repo + UoW integration tests (RED) | coder | `test_repositories.py`, `test_unit_of_work.py` additions | `uv run pytest tests/integration/test_repositories.py tests/integration/test_unit_of_work.py -v` — new tests FAIL | ⬜ |
| 6 | Implement `SqlAlchemyTradeReportRepository` | coder | `repositories.py` | `uv run python -c "from zorivest_infra.database.repositories import SqlAlchemyTradeReportRepository"` | ⬜ |
| 7 | Wire `trade_reports` in `SqlAlchemyUnitOfWork` (GREEN) | coder | `unit_of_work.py` | `uv run pytest tests/integration/test_repositories.py tests/integration/test_unit_of_work.py -v` — PASS | ⬜ |
| 8 | Write `ReportService` tests (RED) | coder | `test_report_service.py` | `uv run pytest tests/unit/test_report_service.py -v` — FAIL | ⬜ |
| 9 | Implement `ReportService` (GREEN) | coder | `report_service.py` | `uv run pytest tests/unit/test_entities.py tests/unit/test_report_service.py -v` — PASS | ⬜ |
| 10 | Create MEU-52 handoff | coder | Handoff file | `Test-Path .agent/context/handoffs/*trade-report-entity*` | ⬜ |
| 11 | Write API route tests (RED) | coder | `test_api_trades.py` additions | `uv run pytest tests/unit/test_api_trades.py -v` — new tests FAIL | ⬜ |
| 12 | Add `get_report_service` dependency | coder | `dependencies.py` | `uv run python -c "from zorivest_api.dependencies import get_report_service"` | ⬜ |
| 13 | Add report API routes (GREEN) | coder | `trades.py` | `uv run pytest tests/unit/test_api_trades.py -v` — PASS | ⬜ |
| 14 | Write MCP tool tests (RED) | coder | `trade-tools.test.ts` additions | `cd mcp-server; npx vitest run tests/trade-tools.test.ts` — new tests FAIL | ⬜ |
| 15 | Add `create_report` + `get_report_for_trade` MCP tools (GREEN) | coder | `trade-tools.ts` | `cd mcp-server; npx vitest run tests/trade-tools.test.ts` — PASS | ⬜ |
| 16 | Create MEU-53 handoff | coder | Handoff file | `Test-Path .agent/context/handoffs/*trade-report-mcp*` | ⬜ |
| 17 | Run MEU gate | tester | Pass/fail evidence | `uv run python tools/validate_codebase.py --scope meu` | ⬜ |
| 18 | Update `meu-registry.md` | coder | MEU-52/53 rows | `rg "MEU-52.*✅" .agent/context/meu-registry.md` | ⬜ |
| 19 | Update `BUILD_PLAN.md` | coder | Status ✅ for MEU-52/53 | `rg "trade-report.*✅" docs/BUILD_PLAN.md` | ⬜ |
| 20 | Run full regression | tester | All tests pass | `uv run pytest tests/ -v` | ⬜ |
| 21 | Create reflection file (provisional — finalize after Codex review) | coder | `2026-03-11-trade-report-reflection.md` | `Test-Path docs/execution/reflections/2026-03-11-trade-report-reflection.md` | ⬜ |
| 22 | Update metrics table (provisional — finalize after Codex review) | coder | New row in `metrics.md` | `rg "trade-report" docs/execution/metrics.md` | ⬜ |
| 23 | Save session state to pomera | coder | pomera note ID | Saved via `pomera_notes` MCP tool | ⬜ |
| 24 | Prepare commit messages | coder | Commit messages text | Presented to human | ⬜ |
| 25 | Final review and plan–code sync | reviewer | Updated plan artifacts | `rg -n "TODO\|FIXME\|NotImplementedError" packages/ mcp-server/src/` | ⬜ |

---

## Verification Plan

### Automated Tests

```powershell
# MEU-52: Entity + Service (unit)
uv run pytest tests/unit/test_entities.py tests/unit/test_report_service.py -v

# MEU-52: Repo + UoW (integration — per testing-strategy.md L290-293)
uv run pytest tests/integration/test_repositories.py tests/integration/test_unit_of_work.py -v

# MEU-53: API routes
uv run pytest tests/unit/test_api_trades.py -v

# MEU-53: MCP tools (run from mcp-server/)
cd mcp-server; npx vitest run tests/trade-tools.test.ts

# TypeScript checks
cd mcp-server; npx tsc --noEmit
cd mcp-server; npm run build

# Full regression
uv run pytest tests/ -v

# Quality gates
uv run python tools/validate_codebase.py --scope meu
```

### Manual Verification

None required — all verification is automated via pytest and vitest with mocked dependencies.
