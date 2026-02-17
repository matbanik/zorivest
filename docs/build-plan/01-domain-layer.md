# Phase 1: Project Skeleton & Domain Layer

> Part of [Zorivest Build Plan](../BUILD_PLAN.md) | Prerequisites: None | Outputs: [Phase 2](02-infrastructure.md)

---

## Goal

Establish the monorepo structure, define all domain entities, value objects, ports (Protocol interfaces), DTOs/commands, and the position size calculator logic. No runtime infrastructure dependencies (no database, no network). Commands/DTOs use Pydantic for validation.

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
│   │       │   └── exceptions.py      # DomainError, ValidationError
│   │       ├── application/
│   │       │   ├── __init__.py
│   │       │   ├── ports.py           # Protocol interfaces (Repository, UoW)
│   │       │   ├── commands.py        # CreateTrade, AttachImage, CreatePlan, etc.
│   │       │   ├── queries.py         # GetTrade, ListTrades, GetImage, etc.
│   │       │   └── dtos.py           # Data transfer objects
│   │       └── services/
│   │           ├── __init__.py
│   │           ├── trade_service.py
│   │           ├── account_service.py
│   │           ├── image_service.py    # Screenshot management
│   │           ├── watchlist_service.py    # (Future) Watchlist management
│   │           ├── tradeplan_service.py   # (Future) Trade plan management
│   │           ├── report_service.py      # Trade meta review / reports
│   │           ├── portfolio_service.py   # Total portfolio balance, % of portfolio calculations
│   │           ├── display_service.py     # Display mode management ($ hide, % hide, % mode)
│   │           ├── account_review_service.py  # Guided balance update workflow
│   │           ├── calculator_service.py
│   │           └── tax_service.py         # Tax estimation orchestration
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
│   │       │   └── tradingview_adapter.py
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
    DOLLAR_VISIBLE = "dollar_visible"       # Show/hide all $ amounts
    PERCENT_VISIBLE = "percent_visible"     # Show/hide all % values
    PERCENT_MODE = "percent_mode"           # Show % of total portfolio alongside $
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
            data=b"\x89PNG...",  # raw bytes
            mime_type="image/png",
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


class AbstractUnitOfWork(Protocol):
    trades: TradeRepository
    images: ImageRepository
    def __enter__(self) -> "AbstractUnitOfWork": ...
    def __exit__(self, *args) -> None: ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...
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
