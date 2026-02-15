# Domain Model — Zorivest

## Entities

### Trade
The core entity. Represents a single execution from the broker.

```python
@dataclass(frozen=True)
class Trade:
    exec_id: str          # Primary key (from broker)
    time: datetime
    instrument: str       # e.g., "SPY", "AAPL"
    action: TradeAction   # BOT or SLD
    quantity: float
    price: float
    account: str          # FK to Account
    commission: float = 0.0
    realized_pnl: float = 0.0
    images: list[ImageAttachment] = field(default_factory=list)
```

### Account
Represents a brokerage or investment account.

```python
@dataclass(frozen=True)
class Account:
    account_id: str       # Primary key (e.g., "DU123456")
    alias: str            # User-friendly name
    account_type: str     # "broker", "ira", "bank", "crypto"
    currency: str = "USD"
```

### ImageAttachment
Polymorphic — can be attached to Trade, TradeReport, or TradePlan.

```python
@dataclass(frozen=True)
class ImageAttachment:
    id: Optional[int] = None
    owner_type: str       # "trade", "report", "plan"
    owner_id: str         # FK varies by owner_type
    data: bytes
    thumbnail: Optional[bytes] = None
    mime_type: str = "image/png"
    caption: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    file_size: Optional[int] = None
    created_at: Optional[datetime] = None
```

### Other Entities

| Entity | Purpose |
|--------|---------|
| `BalanceSnapshot` | Daily account balance recording |
| `TradeReport` | End-of-day / end-of-week summary with metrics |
| `TradePlan` | Pre-trade planning (entry, stop, target, thesis) |
| `Watchlist` | Named list of instruments to monitor |
| `WatchlistItem` | Individual instrument in a watchlist |
| `DisplayMode` | UI layout preferences per user |

## Value Objects / Enums

```python
class TradeAction(str, Enum):
    BOT = "BOT"  # Bought
    SLD = "SLD"  # Sold
```

## Ports (Protocol Interfaces)

Defined in `packages/core/application/ports.py`:

```python
class TradeRepository(Protocol):
    def get(self, exec_id: str) -> Optional[Trade]: ...
    def save(self, trade: Trade) -> None: ...
    def list_all(self, limit: int = 100, offset: int = 0) -> list[Trade]: ...
    def exists(self, exec_id: str) -> bool: ...

class ImageRepository(Protocol):
    def save(self, trade_id: str, image: ImageAttachment) -> int: ...
    def get(self, image_id: int) -> Optional[ImageAttachment]: ...
    def get_for_trade(self, trade_id: str) -> list[ImageAttachment]: ...
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

## Calculator

Pure function in `packages/core/domain/calculator.py`:

```python
def calculate_position_size(
    balance: float,    # Account balance
    risk_pct: float,   # Risk % (e.g., 1.0 = 1%)
    entry: float,      # Entry price
    stop: float,       # Stop-loss price
    target: float,     # Target price
) -> PositionSizeResult:
    """Pure function — no side effects, no I/O, no dependencies."""
```

Returns: `account_risk_1r`, `risk_per_share`, `share_size`, `position_size`, `position_to_account_pct`, `reward_risk_ratio`, `potential_profit`.

## Entity Relationships

```
Account 1──∞ Trade
Trade   1──∞ ImageAttachment
Account 1──∞ BalanceSnapshot
Trade   ∞──1 TradeReport (via grouping)
Watchlist 1──∞ WatchlistItem
```
