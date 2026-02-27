# Phase 3: Application — Service Layer & Use Cases

> Part of [Zorivest Build Plan](../BUILD_PLAN.md) | Prerequisites: [Phase 1](01-domain-layer.md), [Phase 2](02-infrastructure.md), [Phase 2A](02a-backup-restore.md) | Outputs: [Phase 4](04-rest-api.md)

---

## Goal

Build the service layer that orchestrates domain logic through the Unit of Work. Test by mocking repositories.

## Step 3.1: Service Layer Tests (Mock Repositories)

```python
# tests/unit/test_trade_service.py

from unittest.mock import MagicMock
from zorivest_core.services.trade_service import TradeService
from zorivest_core.application.commands import CreateTradeCommand

class TestTradeService:
    def setup_method(self):
        self.uow = MagicMock()
        self.uow.__enter__ = MagicMock(return_value=self.uow)
        self.uow.__exit__ = MagicMock(return_value=False)
        self.service = TradeService(uow=self.uow)

    def test_create_trade_deduplicates(self):
        self.uow.trades.exists.return_value = True
        result = self.service.create_trade(CreateTradeCommand(
            exec_id="DUP001", instrument="SPY", action="BOT",
            quantity=100, price=619.61, account_id="DU123",
        ))
        assert result is None  # skipped duplicate
        self.uow.trades.save.assert_not_called()

    def test_create_trade_success(self):
        self.uow.trades.exists.return_value = False
        result = self.service.create_trade(CreateTradeCommand(
            exec_id="NEW001", instrument="SPY", action="BOT",
            quantity=100, price=619.61, account_id="DU123",
        ))
        assert result is not None
        self.uow.trades.save.assert_called_once()
        self.uow.commit.assert_called_once()


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
            image_data=b"\x89PNG...",  # raw input — service validates, standardizes to WebP, persists as image/webp
            mime_type="image/png",  # advisory — service normalizes to image/webp
            caption="Entry chart",
        ))
        assert result.image_id is not None
        self.uow.images.save.assert_called_once()

    def test_attach_image_to_nonexistent_trade_fails(self):
        self.uow.trades.get.return_value = None
        with pytest.raises(TradeNotFoundError):
            self.service.attach_image(AttachImageCommand(
                trade_id="NONEXIST", image_data=b"...",
            ))

    def test_get_images_for_trade(self):
        self.uow.images.get_for_trade.return_value = [make_stored_image(), make_stored_image()]
        images = self.service.get_trade_images("TRADE1")
        assert len(images) == 2

    def test_get_thumbnail(self):
        self.uow.images.get_thumbnail.return_value = b"RIFF_webp_thumb"
        thumb = self.service.get_thumbnail(image_id=1, max_size=200)
        assert len(thumb) > 0
```

## Step 3.2: Build Plan Expansion Services

> Source: [Build Plan Expansion Ideas](../../_inspiration/import_research/Build%20Plan%20Expansion%20Ideas.md) §1–§26

### Enhanced Deduplication (§6)

The existing `TradeService.create_trade` uses simple `exec_id` existence checks. The enhanced deduplication uses a multi-signal approach:

```python
# packages/core/src/zorivest_core/services/dedup_service.py

import hashlib
from datetime import timedelta

class DeduplicationService:
    """Hash + exec_id + bounded lookback window deduplication."""

    LOOKBACK_DAYS = 30  # Only check duplicates within this window

    def compute_dedup_hash(self, instrument: str, action: str,
                           quantity: float, price: float,
                           time: str, account_id: str) -> str:
        """Generate deterministic hash from core trade fields."""
        canonical = f"{instrument}|{action}|{quantity}|{price}|{time}|{account_id}"
        return hashlib.md5(canonical.encode()).hexdigest()

    def is_duplicate(self, trade, uow) -> bool:
        """Check for duplicates using exec_id, hash, and time window."""
        # 1. Exact exec_id match (fastest)
        if uow.trades.exists(trade.exec_id):
            return True
        # 2. Hash match within lookback window
        dedup_hash = self.compute_dedup_hash(
            trade.instrument, trade.action, trade.quantity,
            trade.price, str(trade.time), trade.account_id
        )
        cutoff = trade.time - timedelta(days=self.LOOKBACK_DAYS)
        return uow.trades.exists_by_hash_since(dedup_hash, cutoff)
```

### Broker Adapter Services (§1, §2)

```python
# packages/core/src/zorivest_core/services/broker_adapter_service.py

class BrokerAdapterService:
    """Unified broker sync — wraps BrokerPort implementations."""

    def __init__(self, uow, registry: dict):
        # registry maps broker_id → BrokerPort implementation
        self.uow = uow
        self.registry = registry

    def sync_account(self, broker_id: str) -> dict:
        """Fetch latest account data from broker and update local state."""
        adapter = self.registry[broker_id]
        return adapter.get_account()

    def import_trades(self, broker_id: str, start: str, end: str) -> dict:
        """Import order history from broker, dedup, and persist."""
        adapter = self.registry[broker_id]
        orders = adapter.get_order_history(start, end)
        # Convert broker-specific format to domain Trade entities
        # Apply deduplication, persist
        return {"imported": len(orders), "duplicates_skipped": 0}
```

### Analytics Services (§3, §7, §10, §11, §13, §14, §15, §21)

```python
# Stubs for analytics services — each follows UoW + pure-math pattern

class RoundTripService:  # §3
    """Groups raw executions into entry→exit round-trips."""
    def match_round_trips(self, executions: list, account_id: str) -> list: ...
    def get_round_trips(self, account_id: str, status: str = "all") -> list: ...

class ExcursionService:  # §7
    """Calculates MFE/MAE/BSO from historical bar data."""
    def calculate_mfe_mae(self, trade, bars: list) -> dict: ...
    def enrich_trade(self, trade_exec_id: str) -> dict: ...

class ExecutionQualityService:  # §10
    """Scores execution quality vs NBBO benchmark — gated on data availability."""
    def score_execution(self, trade, nbbo: dict | None) -> dict: ...
    def grade(self, score: float) -> str: ...  # Returns A/B/C/D/F

class PFOFAnalysisService:  # §11
    """Generates probabilistic PFOF impact reports — labeled as ESTIMATE."""
    def generate_report(self, account_id: str, period: str) -> dict: ...

class ExpectancyService:  # §13
    """Win rate, avg win/loss, expectancy per trade, Kelly %."""
    def calculate_expectancy(self, trades: list) -> dict: ...
    def edge_metrics(self, trades: list) -> dict: ...

class DrawdownService:  # §14
    """Monte Carlo simulation for drawdown probability tables."""
    def drawdown_probability_table(self, trades: list, simulations: int = 10000) -> dict: ...
    def recommended_risk_pct(self, probability_table: dict) -> float: ...

class StrategyBreakdownService:  # §21
    """P&L breakdown by strategy_name from TradeReport tags."""
    def breakdown_by_strategy(self, trades: list) -> list: ...
```

### Additional Services (§5, §8, §9, §12, §17, §26)

```python
class IdentifierResolverService:  # §5
    """Resolver chain: cache → OpenFIGI (rate-limited) → Finnhub → AI fallback."""
    def resolve(self, id_type: str, id_value: str) -> dict | None: ...
    def batch_resolve(self, identifiers: list) -> list: ...

class OptionsGroupingService:  # §8
    """Detects multi-leg strategies from concurrent executions."""
    def detect_strategy(self, legs: list) -> str: ...  # Returns StrategyType
    def group_legs(self, executions: list) -> list: ...

class TransactionLedgerService:  # §9
    """Decomposes trade commission into component fees."""
    def decompose_fees(self, trade) -> list: ...
    def get_fee_summary(self, account_id: str, period: str) -> dict: ...

class AIReviewService:  # §12
    """Multi-persona AI trade review — opt-in only, budget-capped."""
    def multi_persona_review(self, trade, budget_cap: float = 0.10) -> dict: ...

class MistakeTrackingService:  # §17
    """Behavioral mistake tracking with cost attribution."""
    def classify_mistake(self, trade) -> dict | None: ...
    def cost_attribution(self, trade, mistake_category: str) -> float: ...
    def get_summary(self, account_id: str, period: str) -> dict: ...

class BankImportService:  # §26
    """Bank statement import orchestrator — CSV, OFX, QIF, PDF (phased)."""
    def import_statement(self, file_path: str, account_id: str,
                         format_hint: str = "auto") -> dict: ...
    def detect_format(self, file_path: str) -> str: ...
    def detect_bank(self, csv_headers: list) -> str | None: ...
```

### Tax Services

```python
# packages/core/src/zorivest_core/services/tax_service.py

class TaxService:
    """Tax computation, lot management, and quarterly estimate tracking."""

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

### Report and Trade Plan Services

```python
# packages/core/src/zorivest_core/services/report_service.py

class ReportService:
    """Post-trade report creation and retrieval."""

    def __init__(self, uow):
        self.uow = uow

    def create(self, trade_id: str, report_data: dict) -> dict:
        """Create a new TradeReport linked to a trade."""
        ...

    def get_for_trade(self, trade_id: str) -> dict | None:
        """Retrieve report for a specific trade. Returns None if not found."""
        ...


# packages/core/src/zorivest_core/services/trade_plan_service.py

class TradePlanService:
    """Forward-looking trade plan creation."""

    def __init__(self, uow):
        self.uow = uow

    def create(self, plan_data: dict) -> dict:
        """Create TradePlan with computed risk_reward_ratio."""
        ...
```

## Exit Criteria

**Run `pytest tests/unit/` — all should pass with no database or network.**

## Test Plan

| Test File | What It Tests |
|-----------|--------------|
| `tests/unit/test_trade_service.py` | Trade creation, deduplication, via mocked repos |
| `tests/unit/test_image_service.py` | Image attach, retrieval, thumbnails, error handling |
| `tests/unit/test_account_service.py` | Account management, balance snapshots |
| `tests/unit/test_settings_resolver.py` | Three-tier resolution, type coercion, unknown key rejection |
| `tests/unit/test_config_export.py` | Allowlist enforcement, sensitivity filtering |
| `tests/unit/test_dedup_service.py` | Hash + exec_id + lookback dedup (Expansion §6) |
| `tests/unit/test_round_trip_service.py` | Execution matching, partial round-trips (Expansion §3) |
| `tests/unit/test_expectancy_service.py` | Win rate, edge, Kelly % calculations (Expansion §13) |
| `tests/unit/test_bank_import_service.py` | Format detection, CSV/OFX parsing, dedup (Expansion §26) |
| `tests/unit/test_excursion_service.py` | MFE/MAE/BSO from bar data (Expansion §7) |

## Outputs

- `TradeService` fully tested with deduplication
- `ImageService` with attach, retrieve, thumbnail operations
- `AccountService` for balance management
- `CalculatorService` wrapping the pure calculator function
- `SettingsService` with `SettingsResolver` (three-tier resolution, reset-to-default) — see [Phase 2A](02a-backup-restore.md)
- `BackupService` wrapping `BackupManager` + `BackupRecoveryManager` — see [Phase 2A](02a-backup-restore.md)
- `ConfigExportService` for JSON config export/import with allowlist — see [Phase 2A](02a-backup-restore.md)
- All services use Unit of Work pattern for transactions

> [!NOTE]
> **MCP discovery and toolset management** logic lives entirely in the TypeScript MCP server (Phase 5), not the Python service layer. The `ToolsetRegistry`, discovery meta-tools, and confirmation token generation are implemented in [05j-mcp-discovery.md](05j-mcp-discovery.md).

### Build Plan Expansion Services

- `DeduplicationService` — enhanced hash + exec_id + lookback window (§6)
- `BrokerAdapterService` — unified broker sync via `BrokerPort` registry (§1, §2)
- `RoundTripService` — execution-to-round-trip matching (§3)
- `ExcursionService` — MFE/MAE/BSO auto-enrichment (§7)
- `ExecutionQualityService` — NBBO scoring, gated on data (§10)
- `PFOFAnalysisService` — probabilistic PFOF impact estimates (§11)
- `ExpectancyService` — win rate, edge metrics, Kelly % (§13)
- `DrawdownService` — Monte Carlo drawdown probability tables (§14)
- `StrategyBreakdownService` — P&L by strategy_name (§21)
- `IdentifierResolverService` — CUSIP/ISIN/SEDOL → ticker chain (§5)
- `OptionsGroupingService` — multi-leg strategy detection (§8)
- `TransactionLedgerService` — per-trade fee decomposition (§9)
- `AIReviewService` — multi-persona AI review, opt-in (§12)
- `MistakeTrackingService` — behavioral mistakes + cost attribution (§17)
- `BankImportService` — bank statement import orchestrator (§26)
- `SQNService` — System Quality Number calculation + grade (§15)
- `CostOfFreeService` — hidden cost analysis (PFOF + fees) (§22)
- `TradeReportService` (enhanced) — bidirectional trade ↔ journal linking (§16)

