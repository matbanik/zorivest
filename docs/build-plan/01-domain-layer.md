# Phase 1: Project Skeleton & Domain Layer

> Part of [Zorivest Build Plan](../BUILD_PLAN.md) | Prerequisites: None | Outputs: [Phase 2](02-infrastructure.md)

---

## Goal

Establish the monorepo structure, define all domain entities, value objects, ports (Protocol interfaces), DTOs/commands, and the position size calculator logic. No runtime infrastructure dependencies (no database, no network). Commands/DTOs use `dataclasses` with manual validation in Phase 1; Pydantic validation is added in Phase 4 when `pydantic` is installed alongside FastAPI.

## Step 1.1: Scaffold the Monorepo

```
zorivest/
├── pyproject.toml                    # Root workspace
├── uv.lock
├── CLAUDE.md
├── AGENTS.md
├── docs/decisions/
│   └── ADR-0001-architecture.md
├── packages/
│   ├── core/
│   │   ├── pyproject.toml
│   │   └── src/zorivest_core/
│   │       ├── __init__.py
│   │       ├── domain/
│   │       │   ├── __init__.py
│   │       │   ├── entities.py         # Core entities (see Domain Model below)
│   │       │   ├── value_objects.py    # Money, PositionSize, Ticker, ImageData, Conviction
│   │       │   ├── enums.py           # AccountType, TradeAction, ConvictionLevel, etc.
│   │       │   ├── events.py          # TradeCreated, BalanceUpdated, ImageAttached, PlanCreated
│   │       │   ├── calculator.py      # Position size calculator (pure math)
│   │       │   ├── tax_estimator.py   # Tax estimation logic (pure math)
│   │       │   ├── exceptions.py      # ZorivestError hierarchy (see Phase 3)
│   │       │   ├── trades/            # Trade domain logic
│   │       │   │   ├── __init__.py
│   │       │   │   └── identity.py    # trade_fingerprint() — dedup hash
│   │       │   └── analytics/         # Pure-math functions (no UoW, no state)
│   │       │       ├── __init__.py
│   │       │       ├── expectancy.py   # calculate_expectancy(trades) → ExpectancyResult
│   │       │       ├── drawdown.py     # drawdown_probability_table(trades, sims) → DrawdownResult
│   │       │       ├── sqn.py          # calculate_sqn(trades) → SQNResult
│   │       │       ├── excursion.py    # calculate_mfe_mae(trade, bars) → ExcursionResult
│   │       │       ├── execution_quality.py  # score_execution(trade, nbbo) → QualityResult
│   │       │       ├── pfof.py         # analyze_pfof(trades, period) → PFOFResult
│   │       │       ├── cost_of_free.py # analyze_costs(trades) → CostResult
│   │       │       ├── strategy.py     # breakdown_by_strategy(trades) → list[StrategyResult]
│   │       │       └── results.py      # All frozen dataclass result types
│   │       ├── application/
│   │       │   ├── __init__.py
│   │       │   ├── ports.py           # Protocol interfaces (Repository, UoW, ImportParser)
│   │       │   ├── commands.py        # CreateTrade, AttachImage, CreatePlan, etc.
│   │       │   ├── queries.py         # GetTrade, ListTrades, GetImage, etc.
│   │       │   └── dtos.py           # Data transfer objects
│   │       └── services/             # ~10 consolidated services (see Phase 3)
│   │           ├── __init__.py
│   │           ├── trade_service.py        # Trade lifecycle + dedup + round-trip matching
│   │           ├── import_service.py      # Unified import (CSV, PDF, OFX, QIF) + Strategy parsers
│   │           ├── tax_service.py         # Tax computation (8 cohesive methods)
│   │           ├── analytics_service.py   # Thin orchestrator → domain/analytics/ pure functions
│   │           ├── account_service.py     # Account management + balance snapshots
│   │           ├── image_service.py       # Chart/screenshot management
│   │           ├── report_service.py      # Reports + journal linking + trade plans
│   │           ├── review_service.py      # Mistake tracking + AI review (behavioral)
│   │           ├── market_data_service.py # Identifier resolution + options grouping
│   │           └── system_service.py      # Backup, config export, calculator wrapper
│   ├── infrastructure/
│   │   ├── pyproject.toml
│   │   └── src/zorivest_infra/
│   │       ├── __init__.py
│   │       ├── database/
│   │       │   ├── __init__.py
│   │       │   ├── connection.py      # SQLCipher connection factory
│   │       │   ├── models.py         # SQLAlchemy models
│   │       │   ├── repositories.py   # Concrete repo implementations
│   │       │   ├── unit_of_work.py   # UoW implementation
│   │       │   └── migrations/       # Alembic migrations
│   │       ├── external_apis/
│   │       │   ├── __init__.py
│   │       │   ├── ibkr_adapter.py   # Interactive Brokers adapter
│   │       │   ├── alpaca_adapter.py # Alpaca broker adapter (Build Plan Expansion §24)
│   │       │   ├── tradier_adapter.py # Tradier broker adapter (Build Plan Expansion §25)
│   │       │   └── tradingview_adapter.py
│   │       ├── parsers/              # File import parsers (Build Plan Expansion §18, §26)
│   │       │   ├── __init__.py
│   │       │   ├── csv_parser.py     # Multi-broker CSV import
│   │       │   ├── ofx_parser.py     # OFX/QFX bank statement parser
│   │       │   ├── pdf_parser.py     # PDF statement extraction (P3 — fallback)
│   │       │   └── qif_parser.py     # QIF format parser (P2)
│   │       └── logging/              # See Phase 1A (01a-logging.md)
│   │           ├── __init__.py
│   │           ├── config.py         # LoggingManager (QueueHandler/Listener)
│   │           ├── filters.py        # FeatureFilter (per-file routing)
│   │           ├── formatters.py     # JsonFormatter (JSONL output)
│   │           ├── redaction.py      # RedactionFilter (API key masking)
│   │           └── bootstrap.py      # Usage patterns
│   ├── api/                                # Python — FastAPI REST layer
│   │   ├── pyproject.toml
│   │   └── src/zorivest_api/
│   │       ├── __init__.py
│   │       ├── routes/
│   │       ├── middleware/
│   │       └── bootstrap.py
│   │
│   │   ═══ TYPESCRIPT PACKAGES (managed by npm/pnpm) ═══════════════
│   │
├── mcp-server/                              # TypeScript — MCP server (calls REST)
│   ├── package.json
│   ├── tsconfig.json
│   └── src/
│       ├── index.ts                         # MCP server setup
│       └── tools/
│           ├── trade-tools.ts
│           ├── account-tools.ts
│           ├── calculator-tools.ts
│           └── image-tools.ts
├── ui/                                      # TypeScript — Electron + React
│   ├── package.json
│   ├── electron/
│   │   ├── main.ts                          # Electron main + Python process mgmt
│   │   └── preload.ts
│   └── src/
│       ├── App.tsx
│       ├── pages/                           # Dashboard, Trades, Plans, Reports
│       ├── components/                      # Trade table, charts, screenshot panel
│       ├── hooks/                           # useApi(), useTrades(), useAccounts()
│       └── styles/
└── tests/
    ├── conftest.py                          # Shared fixtures
    ├── unit/                                # pytest
    │   ├── test_calculator.py               # FIRST TEST YOU WRITE
    │   ├── test_entities.py
    │   ├── test_value_objects.py
    │   ├── test_trade_service.py
    │   ├── test_account_service.py
    │   └── test_image_service.py
    ├── integration/
    │   ├── test_repositories.py
    │   ├── test_unit_of_work.py
    │   └── test_database_images.py
    ├── e2e/
    │   └── test_api_endpoints.py
    └── typescript/                           # Vitest
        ├── mcp/
        │   └── trade-tools.test.ts
        └── ui/
            └── App.test.tsx
```

## Step 1.2: Domain Model — Complete Entity Map

See [Domain Model Reference](domain-model-reference.md) for the full entity map.

### Enum Definitions

```python
# packages/core/src/zorivest_core/domain/enums.py

from enum import StrEnum

class AccountType(StrEnum):
    BROKER = "broker"           # Brokerage account (Interactive Brokers, etc.)
    BANK = "bank"               # Checking/savings
    REVOLVING = "revolving"     # Credit cards, lines of credit
    INSTALLMENT = "installment" # Loans (mortgage, auto, student)
    IRA = "ira"                 # Individual Retirement Account
    K401 = "401k"               # Employer-sponsored retirement

class TradeAction(StrEnum):
    BOT = "BOT"  # Bought
    SLD = "SLD"  # Sold

class ConvictionLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    MAX = "max"

class PlanStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    EXECUTED = "executed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"

class ImageOwnerType(StrEnum):
    TRADE = "trade"
    REPORT = "report"
    PLAN = "plan"

class DisplayModeFlag(StrEnum):
    """GUI display privacy toggles — stored in user settings."""
    HIDE_DOLLARS = "hide_dollars"            # Privacy mode — hide all $ amounts
    HIDE_PERCENTAGES = "hide_percentages"    # Privacy mode — hide all % values
    PERCENT_MODE = "percent_mode"            # Show % of total portfolio alongside $

# ── Build Plan Expansion enums ──────────────────────────────────────────

class RoundTripStatus(StrEnum):  # §3
    OPEN = "open"
    CLOSED = "closed"
    PARTIAL = "partial"

class IdentifierType(StrEnum):  # §5
    CUSIP = "cusip"
    ISIN = "isin"
    SEDOL = "sedol"
    FIGI = "figi"

class FeeType(StrEnum):  # §9
    COMMISSION = "commission"
    EXCHANGE = "exchange"
    REGULATORY = "regulatory"
    ECN = "ecn"
    CLEARING = "clearing"
    PLATFORM = "platform"
    OTHER = "other"

class StrategyType(StrEnum):  # §8
    VERTICAL = "vertical"
    IRON_CONDOR = "iron_condor"
    BUTTERFLY = "butterfly"
    CALENDAR = "calendar"
    STRADDLE = "straddle"
    STRANGLE = "strangle"
    CUSTOM = "custom"

class MistakeCategory(StrEnum):  # §17
    EARLY_EXIT = "early_exit"
    LATE_EXIT = "late_exit"
    OVERSIZED = "oversized"
    NO_STOP = "no_stop"
    REVENGE_TRADE = "revenge_trade"
    FOMO_ENTRY = "fomo_entry"
    IGNORED_PLAN = "ignored_plan"
    OVERTRADING = "overtrading"
    CHASING = "chasing"
    OTHER = "other"

class RoutingType(StrEnum):  # §23
    PFOF = "pfof"
    DMA = "dma"
    HYBRID = "hybrid"

class TransactionCategory(StrEnum):  # §26
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRANSFER_IN = "transfer_in"
    TRANSFER_OUT = "transfer_out"
    FEE = "fee"
    INTEREST = "interest"
    DIVIDEND = "dividend"
    ACH_DEBIT = "ach_debit"
    ACH_CREDIT = "ach_credit"
    WIRE_IN = "wire_in"
    WIRE_OUT = "wire_out"
    CHECK = "check"
    CARD_PURCHASE = "card_purchase"
    REFUND = "refund"
    ATM = "atm"
    OTHER = "other"

class BalanceSource(StrEnum):  # §26
    MANUAL = "manual"
    CSV_IMPORT = "csv_import"
    OFX_IMPORT = "ofx_import"
    QIF_IMPORT = "qif_import"
    PDF_IMPORT = "pdf_import"
    AGENT_SUBMIT = "agent_submit"
```

### Build Priority for Domain Objects

Not everything needs to be built at once. Here's the phased approach:

| Priority | Entity | When to Build | Why |
|----------|--------|---------------|-----|
| **P0 — Now** | Trade, Account, BalanceSnapshot, ImageAttachment | Phase 1 | Core trading functionality |
| **P0 — Now** | TotalPortfolioBalance + DisplayMode | Phase 1 | Core UX: privacy modes, % reference |
| **P0 — Now** | PositionSizeCalculator | Phase 1 | Already in spec, pure math |
| **P1 — Soon** | TradeReport | Phase 1 (after trades work) | Post-trade review is immediate value |
| **P1 — Soon** | AccountType enum + multi-account | Phase 1 | Different account types affect tax treatment |
| **P2 — Next** | TradePlan | After P1 ships | Forward-looking trade planning |
| **P2 — Next** | Watchlist, WatchlistItem | After P1 ships | Ticker tracking |
| **P3 — Later** | TaxEstimator | After research phase | Complex rules, needs accuracy verification |
| **P1 — Soon** | RoundTrip | After trades work | Round-trip matching for P&L (Expansion §3) |
| **P1 — Soon** | ExcursionMetrics (MFE/MAE/BSO) | After market data | Auto-enrichment from bar data (Expansion §7) |
| **P1 — Soon** | TransactionLedger | After trades work | Per-trade fee decomposition (Expansion §9) |
| **P1 — Soon** | MistakeEntry | After trade reports | Behavior feedback loop (Expansion §17) |
| **P1 — Soon** | BankTransaction | After accounts work | Bank statement import (Expansion §26, phased) |
| **P2 — Next** | IdentifierMapping | After core import | CUSIP/ISIN resolution cache (Expansion §5) |
| **P2 — Next** | OptionsStrategy | After multi-leg needs | Multi-leg options grouping (Expansion §8) |
| **P2 — Next** | BrokerModel | After broker adapters | PDT, settlement, leverage constraints (Expansion §23) |

**P0 entities get tests and implementation now. P1–P3 get Protocol interfaces (ports) now but concrete implementations later.** This way the architecture supports future growth without blocking current development.

## Step 1.3: First Code — Position Size Calculator (Write Tests First!)

**This is literally the first code you write.** Start with the position size calculator because it's pure math with zero dependencies — perfect for TDD.

```python
# tests/unit/test_calculator.py — WRITE THIS FIRST

import pytest
from zorivest_core.domain.calculator import calculate_position_size

class TestPositionSizeCalculator:
    """Test the pure calculation logic with known values from the spec."""

    def test_basic_calculation(self):
        result = calculate_position_size(
            balance=437_903.03, risk_pct=1.0,
            entry=619.61, stop=618.61, target=620.61
        )
        assert result.account_risk_1r == pytest.approx(4379.03, abs=0.01)
        assert result.risk_per_share == pytest.approx(1.00, abs=0.01)
        assert result.share_size == 4379
        assert result.reward_risk_ratio == 1.00
        assert result.potential_profit == pytest.approx(4379.00, abs=0.01)

    def test_zero_entry_returns_zero_shares(self):
        result = calculate_position_size(
            balance=100_000, risk_pct=1.0,
            entry=0.0, stop=0.0, target=0.0
        )
        assert result.share_size == 0
        assert result.risk_per_share == 0

    def test_risk_out_of_range_defaults_to_one_percent(self):
        result = calculate_position_size(
            balance=100_000, risk_pct=200.0,  # > 100%
            entry=100.0, stop=99.0, target=101.0
        )
        # Should default to 1%
        assert result.account_risk_1r == pytest.approx(1000.0, abs=0.01)

    def test_division_by_zero_entry_equals_stop(self):
        result = calculate_position_size(
            balance=100_000, risk_pct=1.0,
            entry=100.0, stop=100.0, target=105.0  # entry == stop
        )
        assert result.share_size == 0
        assert result.reward_risk_ratio == 0

    def test_zero_balance(self):
        result = calculate_position_size(
            balance=0.0, risk_pct=1.0,
            entry=100.0, stop=99.0, target=101.0
        )
        assert result.position_to_account_pct == 0.0
```

Then implement to make tests pass:

```python
# packages/core/src/zorivest_core/domain/calculator.py

from __future__ import annotations
import math
from dataclasses import dataclass


@dataclass(frozen=True)
class PositionSizeResult:
    account_risk_1r: float
    risk_per_share: float
    share_size: int
    position_size: int
    position_to_account_pct: float
    reward_risk_ratio: float
    potential_profit: float


def calculate_position_size(
    balance: float,
    risk_pct: float,
    entry: float,
    stop: float,
    target: float,
) -> PositionSizeResult:
    """Pure function — no side effects, no I/O, no dependencies."""
    risk_decimal = risk_pct / 100.0
    if not (0.0001 <= risk_decimal <= 1.0):
        risk_decimal = 0.01

    acc_1r = balance * risk_decimal
    risk_per_share = abs(entry - stop) if entry > 0 and stop > 0 else 0.0

    share_size = math.floor(acc_1r / risk_per_share) if risk_per_share > 0 else 0
    position_size = math.ceil(entry * share_size)

    potential_per_share = abs(target - entry) if target > 0 else 0.0
    reward_risk = (potential_per_share / risk_per_share) if risk_per_share > 0 else 0.0
    reward_risk = math.floor(reward_risk * 100) / 100

    potential_profit = potential_per_share * share_size

    pos_to_acct = (position_size / balance * 100) if balance > 0 else 0.0
    pos_to_acct = math.floor(pos_to_acct * 100) / 100

    return PositionSizeResult(
        account_risk_1r=acc_1r,
        risk_per_share=risk_per_share,
        share_size=share_size,
        position_size=position_size,
        position_to_account_pct=pos_to_acct,
        reward_risk_ratio=reward_risk,
        potential_profit=potential_profit,
    )
```

## Step 1.4: Domain Entities

```python
# tests/unit/test_entities.py

from zorivest_core.domain.entities import Trade, ImageAttachment
from datetime import datetime

class TestTrade:
    def test_create_trade(self):
        trade = Trade(
            exec_id="ABC123", time=datetime.now(),
            instrument="SPY STK (USD)", action="BOT",
            quantity=100.0, price=619.61,
            account_id="DU3584717",
        )
        assert trade.exec_id == "ABC123"
        assert trade.commission == 0.0  # default
        assert trade.realized_pnl == 0.0  # default

    def test_attach_image_to_trade(self):
        trade = Trade(
            exec_id="ABC123",
            time=datetime.now(),
            instrument="SPY STK (USD)",
            action="BOT",
            quantity=100.0,
            price=619.61,
            account_id="DU3584717",
        )
        img = ImageAttachment(
            data=b"RIFF\x00\x00\x00\x00WEBP...",  # raw bytes (WebP-standardized)
            mime_type="image/webp",
            caption="Entry screenshot",
            width=1920, height=1080,
        )
        trade.attach_image(img)
        assert len(trade.images) == 1
```

## Step 1.5: Port Definitions (Protocol Interfaces)

```python
# packages/core/src/zorivest_core/application/ports.py

from typing import Protocol, Optional
from zorivest_core.domain.entities import Trade, ImageAttachment


class TradeRepository(Protocol):
    def get(self, exec_id: str) -> Optional[Trade]: ...
    def save(self, trade: Trade) -> None: ...
    def list_all(self, limit: int = 100, offset: int = 0) -> list[Trade]: ...
    def exists(self, exec_id: str) -> bool: ...


class ImageRepository(Protocol):
    def save(self, owner_type: str, owner_id: str, image: ImageAttachment) -> int: ...
    def get(self, image_id: int) -> Optional[ImageAttachment]: ...
    def get_for_owner(self, owner_type: str, owner_id: str) -> list[ImageAttachment]: ...
    def delete(self, image_id: int) -> None: ...
    def get_thumbnail(self, image_id: int, max_size: int = 200) -> bytes: ...


class UnitOfWork(Protocol):
    trades: TradeRepository
    images: ImageRepository
    def __enter__(self) -> "UnitOfWork": ...
    def __exit__(self, *args) -> None: ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...


# ── Build Plan Expansion ports ──────────────────────────────────────────

class BrokerPort(Protocol):  # §1 IBroker Interface Pattern
    """Abstract broker adapter — all brokers implement this protocol."""
    def get_account(self) -> dict: ...
    def get_positions(self) -> list[dict]: ...
    def get_orders(self, status: str = "closed") -> list[dict]: ...
    def get_bars(self, symbol: str, timeframe: str, start: str, end: str) -> list[dict]: ...
    def get_order_history(self, start: str, end: str) -> list[dict]: ...


class BankImportPort(Protocol):  # §26 Bank Statement Import
    """Abstract parser for bank statement files."""
    def detect_format(self, file_path: str) -> str: ...
    def parse_statement(self, file_path: str, config: dict | None = None) -> dict: ...
    def detect_bank(self, headers: list[str]) -> str | None: ...


class IdentifierResolverPort(Protocol):  # §5 Identifier Resolution
    """Resolve CUSIP/ISIN/SEDOL to ticker symbol."""
    def resolve(self, id_type: str, id_value: str, exchange_hint: str | None = None) -> dict | None: ...
    def batch_resolve(self, identifiers: list[dict]) -> list[dict]: ...
```

## Exit Criteria

**Run `pytest tests/unit/` — everything should pass. No database, no network, no GUI.**

## Test Plan

| Test File | What It Tests |
|-----------|--------------|
| `tests/unit/test_calculator.py` | Position size calculator, edge cases |
| `tests/unit/test_entities.py` | Entity creation, image attachment |
| `tests/unit/test_value_objects.py` | Value object validation |

## Outputs

- All P0 domain entities defined and tested
- Calculator fully functional with spec values
- Port interfaces defined for all repositories
- Enums and value objects in place
