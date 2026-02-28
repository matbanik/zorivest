# Phase 3: Application — Service Layer & Use Cases

> Part of [Zorivest Build Plan](../BUILD_PLAN.md) | Prerequisites: [Phase 1](01-domain-layer.md), [Phase 2](02-infrastructure.md), [Phase 2A](02a-backup-restore.md) | Outputs: [Phase 4](04-rest-api.md)
>
> [!NOTE]
> **Research-validated design:** This service layer architecture was independently validated by three AI research models (Gemini, ChatGPT, Claude) against current industry best practices. See `_inspiration/service_layer_research/research-composite.md` for the full synthesis. Key changes from the original design: service consolidation (~25 → ~10), pure-math extraction to domain functions, in-memory SQLite integration testing, and Hypothesis property-based testing.

---

## Goal

Build the service layer that orchestrates domain logic through the Unit of Work. Services are the boundary between external access (MCP server, REST API, GUI) and domain logic.

### Design Principles

1. **Services orchestrate, domain computes** — Business logic lives in domain entities and pure functions; services fetch data, call domain logic, persist results
2. **UoW only for services that touch the database** — Pure computation does NOT get a UoW dependency
3. **Uniform return contract** — Frozen dataclasses for success, domain exceptions for expected failures
4. **Constructor DI, no framework** — Manual composition root with Protocol interfaces

## Architecture Overview

### Consolidated Service Map (~10 services)

| Service | Responsibility | UoW? |
|---------|---------------|:----:|
| `TradeService` | Trade lifecycle: create, dedup, round-trip matching | ✅ |
| `ImportService` | Unified import pipeline: CSV, PDF, OFX, QIF with Strategy parsers | ✅ |
| `TaxService` | Tax computation, lot management, quarterly estimates (8 methods) | ✅ |
| `AnalyticsService` | Thin orchestrator — fetches data, calls pure domain functions | ✅ |
| `AccountService` | Account management, balance snapshots | ✅ |
| `ImageService` | Chart/screenshot attach, retrieve, thumbnail | ✅ |
| `ReportService` | Trade reports, journal linking, trade plans | ✅ |
| `ReviewService` | Mistake tracking, AI review (behavioral analysis) | ✅ |
| `MarketDataService` | Identifier resolution, options grouping | ✅ |
| `SystemService` | Backup, config export, calculator wrapper | ✅ |

### Pure Domain Functions (`domain/analytics/`)

These are **NOT services** — they are stateless, side-effect-free functions that take data in and return typed results. No UoW, no database, no state.

```
domain/analytics/
├── __init__.py
├── expectancy.py         → calculate_expectancy(trades) → ExpectancyResult
├── drawdown.py           → drawdown_probability_table(trades, simulations, seed) → DrawdownResult
├── sqn.py                → calculate_sqn(trades) → SQNResult
├── excursion.py          → calculate_mfe_mae(trade, bars) → ExcursionResult
├── execution_quality.py  → score_execution(trade, nbbo) → QualityResult
├── pfof.py               → analyze_pfof(trades, period) → PFOFResult
├── cost_of_free.py       → analyze_costs(trades) → CostResult
├── strategy.py           → breakdown_by_strategy(trades) → list[StrategyResult]
└── results.py            → All frozen dataclass result types
```

### Domain Exception Hierarchy

```python
# packages/core/src/zorivest_core/domain/exceptions.py

class ZorivestError(Exception):
    """Base error for all Zorivest domain exceptions."""

class ValidationError(ZorivestError):
    """Input validation failed (bad data shape, missing fields)."""

class NotFoundError(ZorivestError):
    """Requested entity does not exist."""

class BusinessRuleError(ZorivestError):
    """Business constraint violated (insufficient balance, duplicate trade)."""

class BudgetExceededError(ZorivestError):
    """AI review budget cap exceeded."""

class ImportError(ZorivestError):
    """File import parsing or format detection failed."""
```

### Analytics Result Types

```python
# packages/core/src/zorivest_core/domain/analytics/results.py

from dataclasses import dataclass
from decimal import Decimal

@dataclass(frozen=True)
class ExpectancyResult:
    expectancy: Decimal
    win_rate: Decimal
    avg_win: Decimal
    avg_loss: Decimal
    profit_factor: Decimal
    kelly_fraction: Decimal
    trade_count: int

@dataclass(frozen=True)
class DrawdownResult:
    probability_table: dict          # {5%: x, 10%: y, ...}
    max_drawdown_median: Decimal
    recommended_risk_pct: Decimal
    simulations_run: int

@dataclass(frozen=True)
class SQNResult:
    sqn: Decimal
    grade: str                       # Holy Grail / Excellent / Good / Average / Poor
    trade_count: int
    mean_r: Decimal
    std_r: Decimal

@dataclass(frozen=True)
class ExcursionResult:
    mfe: Decimal                     # Maximum Favorable Excursion
    mae: Decimal                     # Maximum Adverse Excursion
    bso: Decimal                     # Best Scale Out point
    holding_bars: int

@dataclass(frozen=True)
class QualityResult:
    score: Decimal
    grade: str                       # A / B / C / D / F
    slippage_estimate: Decimal

@dataclass(frozen=True)
class PFOFResult:
    estimated_cost: Decimal
    routing_type: str
    confidence: str                  # labeled as ESTIMATE
    period: str

@dataclass(frozen=True)
class CostResult:
    total_hidden_cost: Decimal
    pfof_component: Decimal
    fee_component: Decimal
    period: str

@dataclass(frozen=True)
class StrategyResult:
    strategy_name: str
    total_pnl: Decimal
    trade_count: int
    win_rate: Decimal
```

---

## Step 3.1: Core Service Implementations

### TradeService (absorbs Dedup + RoundTrip)

```python
# packages/core/src/zorivest_core/services/trade_service.py

from zorivest_core.application.commands import CreateTradeCommand
from zorivest_core.domain.trades.identity import trade_fingerprint
from zorivest_core.domain.exceptions import NotFoundError, BusinessRuleError

class TradeService:
    """Trade lifecycle: create, dedup, round-trip matching."""

    def __init__(self, uow):
        self.uow = uow

    def create_trade(self, command: CreateTradeCommand):
        """Create trade with integrated dedup (exec_id + fingerprint + lookback)."""
        with self.uow:
            # Exact exec_id match (fastest)
            if self.uow.trades.exists(command.exec_id):
                raise BusinessRuleError(f"Duplicate trade: exec_id={command.exec_id}")

            # Fingerprint match within lookback window
            fp = trade_fingerprint(command)
            if self.uow.trades.exists_by_fingerprint_since(fp, lookback_days=30):
                raise BusinessRuleError(f"Duplicate trade: fingerprint match within 30-day window")

            trade = Trade.from_command(command)
            self.uow.trades.save(trade)
            self.uow.commit()
            return trade

    def match_round_trips(self, account_id: str) -> list:
        """Group raw executions into entry→exit round-trips."""
        with self.uow:
            executions = self.uow.trades.list_for_account(account_id)
            # Pure domain logic for matching
            round_trips = match_executions_to_round_trips(executions)
            for rt in round_trips:
                self.uow.round_trips.save(rt)
            self.uow.commit()
            return round_trips

    def get_round_trips(self, account_id: str, status: str = "all") -> list:
        """Retrieve round-trips for an account."""
        with self.uow:
            return self.uow.round_trips.list_for_account(account_id, status)
```

### Trade Fingerprint (Domain Logic)

```python
# packages/core/src/zorivest_core/domain/trades/identity.py

import hashlib
from datetime import timedelta

def trade_fingerprint(trade) -> str:
    """Deterministic hash from core trade fields — domain logic, not service logic."""
    canonical = f"{trade.instrument}|{trade.action}|{trade.quantity}|{trade.price}|{trade.time}|{trade.account_id}"
    return hashlib.md5(canonical.encode()).hexdigest()
```

### AnalyticsService (Thin Orchestrator)

```python
# packages/core/src/zorivest_core/services/analytics_service.py

from zorivest_core.domain.analytics.expectancy import calculate_expectancy
from zorivest_core.domain.analytics.drawdown import drawdown_probability_table
from zorivest_core.domain.analytics.sqn import calculate_sqn
from zorivest_core.domain.analytics.excursion import calculate_mfe_mae
from zorivest_core.domain.analytics.results import ExpectancyResult, DrawdownResult, SQNResult

class AnalyticsService:
    """Thin orchestrator — fetches trade data from DB, calls pure domain functions."""

    def __init__(self, uow):
        self.uow = uow

    def get_expectancy(self, account_id: str, strategy: str | None = None) -> ExpectancyResult:
        with self.uow:
            trades = self.uow.trades.list_for_account(account_id, strategy=strategy)
        # After leaving UoW: pure compute, no DB
        return calculate_expectancy(trades)

    def get_drawdown_table(self, account_id: str, simulations: int = 10000) -> DrawdownResult:
        with self.uow:
            trades = self.uow.trades.list_for_account(account_id)
        return drawdown_probability_table(trades, simulations)

    def get_sqn(self, account_id: str) -> SQNResult:
        with self.uow:
            trades = self.uow.trades.list_for_account(account_id)
        return calculate_sqn(trades)

    def get_excursion(self, trade_exec_id: str, bars: list) -> ExcursionResult:
        with self.uow:
            trade = self.uow.trades.get(trade_exec_id)
        return calculate_mfe_mae(trade, bars)
```

### ImportService (Strategy Pattern)

```python
# packages/core/src/zorivest_core/services/import_service.py

from zorivest_core.application.ports import ImportParser
from zorivest_core.domain.exceptions import ImportError
from zorivest_core.domain.trades.identity import trade_fingerprint

class ImportService:
    """Unified import pipeline: detect format → parse → validate → dedup → persist."""

    def __init__(self, uow, parsers: list[ImportParser]):
        self.uow = uow
        self.parsers = parsers

    def import_file(self, file_path: str, account_id: str,
                    format_hint: str = "auto") -> dict:
        parser = self._detect_parser(file_path, format_hint)
        if parser is None:
            raise ImportError(f"No parser detected for: {file_path}")

        raw_transactions = parser.parse(file_path)
        imported, skipped = 0, 0

        with self.uow:
            for raw in raw_transactions:
                trade = raw.to_domain_trade(account_id)
                fp = trade_fingerprint(trade)
                if self.uow.trades.exists_by_fingerprint_since(fp, lookback_days=30):
                    skipped += 1
                    continue
                self.uow.trades.save(trade)
                imported += 1
            self.uow.commit()

        return {"imported": imported, "skipped": skipped, "total": len(raw_transactions)}

    def _detect_parser(self, file_path: str, hint: str) -> ImportParser | None:
        if hint != "auto":
            return next((p for p in self.parsers if p.format_id == hint), None)
        return next((p for p in self.parsers if p.detect(file_path)), None)
```

### ImageService

```python
# packages/core/src/zorivest_core/services/image_service.py

from zorivest_core.application.commands import AttachImageCommand
from zorivest_core.domain.exceptions import NotFoundError

class ImageService:
    """Chart/screenshot management: attach, retrieve, thumbnail."""

    def __init__(self, uow):
        self.uow = uow

    def attach_image(self, command: AttachImageCommand):
        with self.uow:
            trade = self.uow.trades.get(command.trade_id)
            if trade is None:
                raise NotFoundError(f"Trade not found: {command.trade_id}")
            image = ImageAttachment(
                data=command.image_data,
                mime_type=command.mime_type,
                caption=command.caption,
            )
            image_id = self.uow.images.save("trade", command.trade_id, image)
            self.uow.commit()
            return image_id

    def get_trade_images(self, trade_id: str) -> list:
        with self.uow:
            return self.uow.images.get_for_owner("trade", trade_id)

    def get_thumbnail(self, image_id: int, max_size: int = 200) -> bytes:
        with self.uow:
            return self.uow.images.get_thumbnail(image_id, max_size)
```

### TaxService (Keep As-Is — 8 Methods Are Cohesive)

```python
# packages/core/src/zorivest_core/services/tax_service.py

class TaxService:
    """Tax computation, lot management, and quarterly estimate tracking.
    
    All 8 methods share one axis of change: federal/state tax rules.
    Research consensus: cohesive, NOT an SRP violation.
    """

    def __init__(self, uow):
        self.uow = uow

    def simulate_impact(self, request) -> dict:
        """Pre-trade what-if: lot-level close preview, ST/LT split, estimated tax, wash risk."""
        ...

    def estimate(self, request) -> dict:
        """Overall tax estimate: federal + state with bracket breakdown."""
        ...

    def find_wash_sales(self, request) -> dict:
        """Detect wash sale chains within 30-day windows."""
        ...

    def get_lots(self, account_id: str, ticker: str | None,
                 status: str, sort_by: str) -> list:
        """List tax lots with basis, holding period, gain/loss."""
        ...

    def quarterly_estimate(self, quarter: str, tax_year: int,
                           estimation_method: str) -> dict:
        """Compute quarterly estimated tax payment obligations."""
        ...

    def record_payment(self, request) -> dict:
        """Record actual quarterly tax payment. Updates cumulative totals."""
        ...

    def harvest_scan(self, account_id: str | None,
                     min_loss_threshold: float,
                     exclude_wash_risk: bool) -> dict:
        """Scan portfolio for harvestable loss opportunities."""
        ...

    def ytd_summary(self, tax_year: int, account_id: str | None) -> dict:
        """Year-to-date aggregated tax summary (ST/LT, wash, estimates)."""
        ...
```

### ReportService (absorbs TradeReportService + TradePlanService)

```python
# packages/core/src/zorivest_core/services/report_service.py

class ReportService:
    """Trade documentation: post-trade reports, journal linking, trade plans."""

    def __init__(self, uow):
        self.uow = uow

    # Post-trade reports
    def create_report(self, trade_id: str, report_data: dict) -> dict: ...
    def get_report(self, trade_id: str) -> dict | None: ...

    # Journal linking (§16 bidirectional)
    def link_journal(self, trade_id: str, journal_entry_id: str) -> dict: ...
    def get_linked_entries(self, trade_id: str) -> list: ...

    # Trade plans (forward-looking)
    def create_plan(self, plan_data: dict) -> dict:
        """Create TradePlan with computed risk_reward_ratio."""
        ...
```

### ReviewService (Mistake Tracking + AI Review)

```python
# packages/core/src/zorivest_core/services/review_service.py

from zorivest_core.domain.exceptions import BudgetExceededError

class ReviewService:
    """Behavioral analysis: mistake tracking + AI-assisted review."""

    def __init__(self, uow, ai_client=None):
        self.uow = uow
        self.ai_client = ai_client

    # Mistake tracking (§17)
    def classify_mistake(self, trade) -> dict | None: ...
    def cost_attribution(self, trade, mistake_category: str) -> float: ...
    def get_mistake_summary(self, account_id: str, period: str) -> dict: ...

    # AI review (§12 — opt-in, budget-capped)
    def multi_persona_review(self, trade, budget_cap: float = 0.10) -> dict:
        """AI trade review. Raises BudgetExceededError if cap exceeded."""
        ...
```

### MarketDataService (Identifier Resolution + Options Grouping)

```python
# packages/core/src/zorivest_core/services/market_data_service.py

class MarketDataService:
    """Instrument resolution and classification."""

    def __init__(self, uow, resolver_chain: list):
        self.uow = uow
        self.resolver_chain = resolver_chain  # cache → OpenFIGI → Finnhub → AI

    # Identifier resolution (§5)
    def resolve(self, id_type: str, id_value: str) -> dict | None: ...
    def batch_resolve(self, identifiers: list) -> list: ...

    # Options grouping (§8)
    def detect_strategy(self, legs: list) -> str: ...
    def group_legs(self, executions: list) -> list: ...
```

### SystemService (Backup + Config Export + Calculator)

```python
# packages/core/src/zorivest_core/services/system_service.py

class SystemService:
    """System utilities: backup, config export, calculator wrapper."""

    def __init__(self, uow, backup_manager=None):
        self.uow = uow
        self.backup_manager = backup_manager

    def create_backup(self, path: str) -> dict: ...
    def restore_backup(self, path: str) -> dict: ...
    def export_config(self, allowlist: list) -> dict: ...
    def import_config(self, config_data: dict) -> dict: ...
```

---

## Step 3.2: Service Layer Tests

### Unit Tests (Mock UoW — for orchestration logic)

```python
# tests/unit/test_trade_service.py

from unittest.mock import Mock
from zorivest_core.services.trade_service import TradeService
from zorivest_core.application.commands import CreateTradeCommand
from zorivest_core.domain.exceptions import BusinessRuleError

class TestTradeService:
    def setup_method(self):
        self.uow = Mock(spec=UnitOfWork)
        self.uow.__enter__ = Mock(return_value=self.uow)
        self.uow.__exit__ = Mock(return_value=False)
        self.service = TradeService(uow=self.uow)

    def test_create_trade_deduplicates_by_exec_id(self):
        self.uow.trades.exists.return_value = True
        with pytest.raises(BusinessRuleError, match="Duplicate trade"):
            self.service.create_trade(CreateTradeCommand(
                exec_id="DUP001", instrument="SPY", action="BOT",
                quantity=100, price=619.61, account_id="DU123",
            ))
        self.uow.trades.save.assert_not_called()

    def test_create_trade_success(self):
        self.uow.trades.exists.return_value = False
        self.uow.trades.exists_by_fingerprint_since.return_value = False
        result = self.service.create_trade(CreateTradeCommand(
            exec_id="NEW001", instrument="SPY", action="BOT",
            quantity=100, price=619.61, account_id="DU123",
        ))
        assert result is not None
        self.uow.trades.save.assert_called_once()
        self.uow.commit.assert_called_once()
```

```python
# tests/unit/test_image_service.py

class TestImageService:
    def setup_method(self):
        self.uow = Mock(spec=UnitOfWork)
        self.uow.trades = Mock()
        self.uow.images = Mock()
        self.service = ImageService(self.uow)

    def test_attach_screenshot_to_trade(self):
        self.uow.trades.get.return_value = make_trade("TRADE1")
        result = self.service.attach_image(AttachImageCommand(
            trade_id="TRADE1",
            image_data=b"\x89PNG...",
            mime_type="image/png",
            caption="Entry chart",
        ))
        assert result is not None
        self.uow.images.save.assert_called_once()

    def test_attach_image_to_nonexistent_trade_raises(self):
        self.uow.trades.get.return_value = None
        with pytest.raises(NotFoundError):
            self.service.attach_image(AttachImageCommand(
                trade_id="NONEXIST", image_data=b"...",
            ))

    def test_get_images_for_trade(self):
        self.uow.images.get_for_owner.return_value = [make_stored_image(), make_stored_image()]
        images = self.service.get_trade_images("TRADE1")
        assert len(images) == 2

    def test_get_thumbnail(self):
        self.uow.images.get_thumbnail.return_value = b"RIFF_webp_thumb"
        thumb = self.service.get_thumbnail(image_id=1, max_size=200)
        assert len(thumb) > 0
```

### Pure Domain Function Tests (No Mocks, No UoW)

```python
# tests/unit/test_analytics_expectancy.py

from zorivest_core.domain.analytics.expectancy import calculate_expectancy

class TestExpectancy:
    def test_all_winners(self):
        trades = [make_trade(pnl=100), make_trade(pnl=50), make_trade(pnl=200)]
        result = calculate_expectancy(trades)
        assert result.win_rate == 1.0
        assert result.expectancy > 0

    def test_all_losers(self):
        trades = [make_trade(pnl=-100), make_trade(pnl=-50)]
        result = calculate_expectancy(trades)
        assert result.win_rate == 0.0
        assert result.expectancy < 0

    def test_empty_trades_returns_zero(self):
        result = calculate_expectancy([])
        assert result.trade_count == 0
        assert result.expectancy == 0
```

### Hypothesis Property-Based Tests (Math Invariants)

```python
# tests/unit/test_analytics_properties.py

from hypothesis import given, strategies as st, example
from zorivest_core.domain.analytics.expectancy import calculate_expectancy
from zorivest_core.domain.analytics.drawdown import drawdown_probability_table
from zorivest_core.domain.analytics.sqn import calculate_sqn
import math

@given(st.lists(st.floats(min_value=-1e6, max_value=1e6,
                           allow_nan=False, allow_infinity=False), min_size=1))
@example([0.0])
def test_expectancy_is_always_finite(pnls):
    trades = [make_trade(pnl=p) for p in pnls]
    result = calculate_expectancy(trades)
    assert math.isfinite(result.expectancy)
    assert 0 <= result.win_rate <= 1

@given(st.lists(st.floats(min_value=-1e4, max_value=1e4,
                           allow_nan=False, allow_infinity=False), min_size=2))
def test_drawdown_is_never_positive(pnls):
    trades = [make_trade(pnl=p) for p in pnls]
    result = drawdown_probability_table(trades, simulations=100, seed=42)
    assert result.max_drawdown_median <= 0

@given(st.lists(st.floats(min_value=-1e4, max_value=1e4,
                           allow_nan=False, allow_infinity=False), min_size=5))
def test_sqn_sign_matches_expectancy(pnls):
    trades = [make_trade(pnl=p) for p in pnls]
    sqn = calculate_sqn(trades)
    exp = calculate_expectancy(trades)
    if sqn.std_r > 0:
        # SQN sign should match expectancy sign
        assert (sqn.sqn > 0) == (exp.expectancy > 0) or sqn.sqn == 0
```

### Integration Tests (In-Memory SQLite — Real Stack)

```python
# tests/integration/test_tax_service_integration.py

import pytest
from zorivest_core.services.tax_service import TaxService

class TestTaxServiceIntegration:
    """Test TaxService against real in-memory SQLite — catches SQL bugs mocks miss."""

    @pytest.fixture
    def tax_service(self, integration_uow):
        return TaxService(uow=integration_uow)

    def test_wash_sale_30_day_boundary(self, tax_service, seed_trades):
        """Off-by-one in 30-day lookback would pass mocked tests but fail here."""
        result = tax_service.find_wash_sales({"account_id": "DU123"})
        # Verify exact boundary: day 30 IS wash sale, day 31 is NOT
        assert any(ws["days_apart"] == 30 for ws in result["wash_sales"])
        assert not any(ws["days_apart"] == 31 for ws in result["wash_sales"])

    def test_lot_matching_fifo_order(self, tax_service, seed_lots):
        """FIFO ordering depends on actual SQL ORDER BY behavior."""
        lots = tax_service.get_lots("DU123", "AAPL", "open", "date_asc")
        dates = [lot["open_date"] for lot in lots]
        assert dates == sorted(dates)
```

---

## Exit Criteria

**Run `pytest tests/unit/` — all should pass with no database or network.**

**Run `pytest tests/integration/ -m service` — pass with in-memory SQLite.**

## Test Plan

### Unit Tests (Mocked UoW — Orchestration)

| Test File | What It Tests |
|-----------|--------------|
| `tests/unit/test_trade_service.py` | Trade creation, dedup (exec_id + fingerprint), round-trip matching |
| `tests/unit/test_image_service.py` | Image attach, retrieval, thumbnails, error handling |
| `tests/unit/test_account_service.py` | Account management, balance snapshots |
| `tests/unit/test_settings_resolver.py` | Three-tier resolution, type coercion, unknown key rejection |
| `tests/unit/test_config_export.py` | Allowlist enforcement, sensitivity filtering |
| `tests/unit/test_import_service.py` | Parser detection, format dispatch, dedup during import |
| `tests/unit/test_report_service.py` | Report CRUD, journal linking, trade plan creation |
| `tests/unit/test_review_service.py` | Mistake classification, AI budget enforcement |

### Pure Function Tests (No Mocks — Domain Analytics)

| Test File | What It Tests |
|-----------|--------------|
| `tests/unit/test_analytics_expectancy.py` | Win rate, avg win/loss, expectancy, Kelly % |
| `tests/unit/test_analytics_drawdown.py` | Monte Carlo simulation, seed reproducibility |
| `tests/unit/test_analytics_sqn.py` | SQN calculation, grade classification |
| `tests/unit/test_analytics_excursion.py` | MFE/MAE/BSO from bar data |
| `tests/unit/test_analytics_properties.py` | Hypothesis property-based invariants (all functions) |
| `tests/unit/test_trade_fingerprint.py` | Dedup hash determinism, collision resistance |

### Integration Tests (In-Memory SQLite)

| Test File | What It Tests |
|-----------|--------------|
| `tests/integration/test_tax_service_integration.py` | Wash sales, lot matching, quarterly estimates against real SQL |
| `tests/integration/test_import_service_integration.py` | CSV/OFX parsing + dedup + persist against real DB |
| `tests/integration/test_trade_service_integration.py` | Trade create + dedup + round-trip matching end-to-end |

## Outputs

- `TradeService` with integrated deduplication and round-trip matching
- `AnalyticsService` as thin orchestrator over 9 pure domain functions
- `ImportService` with Strategy pattern for format-specific parsers
- `TaxService` with 8 cohesive methods (unchanged scope)
- `ImageService` for chart/screenshot management
- `ReportService` for trade documentation (reports + plans + journal linking)
- `ReviewService` for behavioral analysis (mistakes + AI review)
- `MarketDataService` for identifier resolution and options grouping
- `SystemService` for backup, config export, calculator
- `SettingsService` with `SettingsResolver` (three-tier resolution, reset-to-default) — see [Phase 2A](02a-backup-restore.md)
- `BackupService` wrapping `BackupManager` + `BackupRecoveryManager` — see [Phase 2A](02a-backup-restore.md)
- All services use Unit of Work pattern for transactions
- Pure analytics functions return frozen dataclasses — no raw dicts

> [!NOTE]
> **MCP discovery and toolset management** logic lives entirely in the TypeScript MCP server (Phase 5), not the Python service layer. The `ToolsetRegistry`, discovery meta-tools, and confirmation token generation are implemented in [05j-mcp-discovery.md](05j-mcp-discovery.md).
