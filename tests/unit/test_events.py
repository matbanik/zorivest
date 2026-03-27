# tests/unit/test_events.py
"""MEU-7: Domain Events — tests for AC-1 through AC-7."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import pytest

from zorivest_core.domain.enums import (
    ConvictionLevel,
    ImageOwnerType,
    TradeAction,
)
from zorivest_core.domain.events import (
    BalanceUpdated,
    DomainEvent,
    ImageAttached,
    PlanCreated,
    TradeCreated,
)

pytestmark = pytest.mark.unit


# ── AC-1: DomainEvent base ──────────────────────────────────────────────


class TestDomainEvent:
    """AC-1: Base DomainEvent structure."""

    def test_domain_event_has_defaults(self) -> None:
        """AC-1: event_id and occurred_at have default factories."""
        event = DomainEvent()
        assert isinstance(event.event_id, str)
        assert len(event.event_id) > 0
        assert isinstance(event.occurred_at, datetime)

    def test_domain_event_unique_ids(self) -> None:
        """AC-1: Each event gets a unique UUID."""
        e1 = DomainEvent()
        e2 = DomainEvent()
        assert e1.event_id != e2.event_id

    def test_domain_event_is_frozen(self) -> None:
        """AC-6: DomainEvent is frozen."""
        event = DomainEvent()
        with pytest.raises(AttributeError):
            event.event_id = "changed"  # type: ignore[misc]


# ── AC-2: TradeCreated ───────────────────────────────────────────────────


class TestTradeCreated:
    """AC-2: TradeCreated event."""

    def test_trade_created_fields(self) -> None:
        """AC-2: TradeCreated carries trade identification data."""
        event = TradeCreated(
            exec_id="T001",
            instrument="AAPL",
            action=TradeAction.BOT,
            quantity=100.0,
            price=150.50,
            account_id="ACC-1",
        )
        assert event.exec_id == "T001"
        assert event.instrument == "AAPL"
        assert event.action == TradeAction.BOT
        assert event.quantity == 100.0
        assert event.price == 150.50
        assert event.account_id == "ACC-1"

    def test_trade_created_inherits_base(self) -> None:
        """AC-2: TradeCreated inherits DomainEvent fields."""
        event = TradeCreated(exec_id="T001")
        assert isinstance(event, DomainEvent)
        # Value: verify inherited fields have real generated values
        assert len(event.event_id) == 36  # UUID4 format
        assert "-" in event.event_id  # UUID separator
        assert event.occurred_at.year >= 2025

    def test_trade_created_is_frozen(self) -> None:
        """AC-6: TradeCreated is frozen."""
        event = TradeCreated(exec_id="T001")
        with pytest.raises(AttributeError):
            event.exec_id = "changed"  # type: ignore[misc]


# ── AC-3: BalanceUpdated ─────────────────────────────────────────────────


class TestBalanceUpdated:
    """AC-3: BalanceUpdated event."""

    def test_balance_updated_fields(self) -> None:
        """AC-3: BalanceUpdated carries balance change data."""
        event = BalanceUpdated(
            account_id="ACC-1",
            new_balance=Decimal("15000.50"),
            snapshot_id=42,
        )
        assert event.account_id == "ACC-1"
        assert event.new_balance == Decimal("15000.50")
        assert event.snapshot_id == 42

    def test_balance_updated_inherits_base(self) -> None:
        """AC-3: BalanceUpdated inherits DomainEvent."""
        event = BalanceUpdated(account_id="ACC-1")
        assert isinstance(event, DomainEvent)
        assert len(event.event_id) == 36
        assert event.occurred_at.year >= 2025
        assert event.account_id == "ACC-1"

    def test_balance_updated_is_frozen(self) -> None:
        """AC-6: BalanceUpdated is frozen."""
        event = BalanceUpdated(account_id="ACC-1")
        with pytest.raises(AttributeError):
            event.account_id = "changed"  # type: ignore[misc]


# ── AC-4: ImageAttached ──────────────────────────────────────────────────


class TestImageAttached:
    """AC-4: ImageAttached event."""

    def test_image_attached_fields(self) -> None:
        """AC-4: ImageAttached carries image identification data."""
        event = ImageAttached(
            owner_type=ImageOwnerType.TRADE,
            owner_id="T001",
            image_id=7,
        )
        assert event.owner_type == ImageOwnerType.TRADE
        assert event.owner_id == "T001"
        assert event.image_id == 7

    def test_image_attached_inherits_base(self) -> None:
        """AC-4: ImageAttached inherits DomainEvent."""
        event = ImageAttached()
        assert isinstance(event, DomainEvent)
        assert len(event.event_id) == 36
        assert event.occurred_at.year >= 2025

    def test_image_attached_is_frozen(self) -> None:
        """AC-6: ImageAttached is frozen."""
        event = ImageAttached()
        with pytest.raises(AttributeError):
            event.image_id = 99  # type: ignore[misc]


# ── AC-5: PlanCreated ────────────────────────────────────────────────────


class TestPlanCreated:
    """AC-5: PlanCreated event."""

    def test_plan_created_fields(self) -> None:
        """AC-5: PlanCreated carries plan identification data."""
        event = PlanCreated(
            plan_id=1,
            ticker="TSLA",
            direction=TradeAction.BOT,
            conviction=ConvictionLevel.HIGH,
        )
        assert event.plan_id == 1
        assert event.ticker == "TSLA"
        assert event.direction == TradeAction.BOT
        assert event.conviction == ConvictionLevel.HIGH

    def test_plan_created_inherits_base(self) -> None:
        """AC-5: PlanCreated inherits DomainEvent."""
        event = PlanCreated(plan_id=1)
        assert isinstance(event, DomainEvent)
        assert len(event.event_id) == 36
        assert event.occurred_at.year >= 2025
        assert event.plan_id == 1

    def test_plan_created_is_frozen(self) -> None:
        """AC-6: PlanCreated is frozen."""
        event = PlanCreated(plan_id=1)
        with pytest.raises(AttributeError):
            event.ticker = "changed"  # type: ignore[misc]


# ── AC-7: Module imports ─────────────────────────────────────────────────


class TestEventsModuleImports:
    """AC-7: Module import constraints."""

    def test_events_module_exports(self) -> None:
        """AC-7: events module has all expected classes."""
        import zorivest_core.domain.events as mod

        # Value: verify actual class identity, not just presence
        assert mod.DomainEvent is DomainEvent
        assert mod.TradeCreated is TradeCreated
        assert mod.BalanceUpdated is BalanceUpdated
        assert mod.ImageAttached is ImageAttached
        assert mod.PlanCreated is PlanCreated
        # Verify all are dataclass subclasses of DomainEvent
        for cls in (TradeCreated, BalanceUpdated, ImageAttached, PlanCreated):
            assert issubclass(cls, DomainEvent)

    def test_events_module_no_unexpected_exports(self) -> None:
        """AC-7: events module has no unexpected public classes."""
        import zorivest_core.domain.events as mod

        public = {n for n in dir(mod) if not n.startswith("_")}
        expected = {
            "DomainEvent",
            "TradeCreated",
            "BalanceUpdated",
            "ImageAttached",
            "PlanCreated",
            "dataclass",
            "field",
            "datetime",
            "Decimal",
            "uuid4",
            "ConvictionLevel",
            "ImageOwnerType",
            "TradeAction",
            "annotations",
        }
        unexpected = public - expected
        assert not unexpected, f"Unexpected exports: {unexpected}"
