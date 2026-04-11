"""Domain entity tests — MEU-3 acceptance criteria.

Tests written FIRST (Red phase) before any implementation exists.
Fields sourced from docs/build-plan/domain-model-reference.md lines 16–111.
FIC defined in implementation-plan.md §MEU-3.
"""

from __future__ import annotations

import ast
import inspect
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from zorivest_core.domain.entities import (
        Account,
        BalanceSnapshot,
        ImageAttachment,
        Trade,
        TradePlan,
        TradeReport,
        Watchlist,
        WatchlistItem,
    )

pytestmark = pytest.mark.unit


# ── Helpers ──────────────────────────────────────────────────────────────


def _make_trade(**overrides: object) -> Trade:
    """Construct a Trade with sensible defaults. Stays within test file."""
    from zorivest_core.domain.entities import Trade
    from zorivest_core.domain.enums import TradeAction

    defaults: dict = {
        "exec_id": "EX-001",
        "time": datetime(2026, 3, 7, 9, 30, 0),
        "instrument": "SPY",
        "action": TradeAction.BOT,
        "quantity": 100.0,
        "price": 619.61,
        "account_id": "DU3584717",
    }
    defaults.update(overrides)
    return Trade(**defaults)


def _make_account(**overrides: object) -> Account:
    """Construct an Account with sensible defaults."""
    from zorivest_core.domain.entities import Account
    from zorivest_core.domain.enums import AccountType

    defaults: dict = {
        "account_id": "ACC-001",
        "name": "IBKR Margin",
        "account_type": AccountType.BROKER,
    }
    defaults.update(overrides)
    return Account(**defaults)


def _make_image_attachment(**overrides: object) -> ImageAttachment:
    """Construct an ImageAttachment with sensible defaults."""
    from zorivest_core.domain.entities import ImageAttachment
    from zorivest_core.domain.enums import ImageOwnerType

    defaults: dict = {
        "id": 1,
        "owner_type": ImageOwnerType.TRADE,
        "owner_id": "EX-001",
        "data": b"RIFF\x00\x00\x00\x00WEBP",
        "width": 1920,
        "height": 1080,
        "file_size": 102400,
        "created_at": datetime(2026, 3, 7, 9, 31, 0),
    }
    defaults.update(overrides)
    return ImageAttachment(**defaults)


def _make_balance_snapshot(**overrides: object) -> BalanceSnapshot:
    """Construct a BalanceSnapshot with sensible defaults."""
    from zorivest_core.domain.entities import BalanceSnapshot

    defaults: dict = {
        "id": 1,
        "account_id": "ACC-001",
        "datetime": datetime(2026, 3, 7, 16, 0, 0),
        "balance": Decimal("437903.03"),
    }
    defaults.update(overrides)
    return BalanceSnapshot(**defaults)


# ── AC-1: Trade dataclass ────────────────────────────────────────────────


class TestTrade:
    """AC-1: Trade with all fields from domain-model-reference lines 37–48."""

    def test_trade_construction_with_required_fields(self) -> None:
        from zorivest_core.domain.enums import TradeAction

        trade = _make_trade()
        assert trade.exec_id == "EX-001"
        assert trade.time == datetime(2026, 3, 7, 9, 30, 0)
        assert trade.instrument == "SPY"
        assert trade.action == TradeAction.BOT
        assert trade.quantity == 100.0
        assert trade.price == 619.61
        assert trade.account_id == "DU3584717"

    def test_trade_defaults(self) -> None:
        trade = _make_trade()
        assert trade.commission == 0.0
        assert trade.realized_pnl == 0.0
        assert trade.images == []
        assert trade.report is None

    def test_trade_with_explicit_optional_fields(self) -> None:
        trade = _make_trade(
            commission=1.25,
            realized_pnl=450.0,
        )
        assert trade.commission == 1.25
        assert trade.realized_pnl == 450.0


# ── AC-2: Trade.attach_image ─────────────────────────────────────────────


class TestTradeAttachImage:
    """AC-2: attach_image appends to trade.images."""

    def test_attach_image_appends(self) -> None:
        trade = _make_trade()
        img = _make_image_attachment()
        trade.attach_image(img)
        assert len(trade.images) == 1
        assert trade.images[0] is img

    def test_attach_multiple_images(self) -> None:
        trade = _make_trade()
        img1 = _make_image_attachment(id=1)
        img2 = _make_image_attachment(id=2)
        trade.attach_image(img1)
        trade.attach_image(img2)
        assert len(trade.images) == 2


# ── AC-3: Account dataclass ──────────────────────────────────────────────


class TestAccount:
    """AC-3: Account with all fields from domain-model-reference lines 16–27."""

    def test_account_construction_with_required_fields(self) -> None:
        from zorivest_core.domain.enums import AccountType

        account = _make_account()
        assert account.account_id == "ACC-001"
        assert account.name == "IBKR Margin"
        assert account.account_type == AccountType.BROKER

    def test_account_defaults(self) -> None:
        from zorivest_core.domain.enums import BalanceSource

        account = _make_account()
        assert account.institution == ""
        assert account.currency == "USD"
        assert account.is_tax_advantaged is False
        assert account.notes == ""
        assert account.sub_accounts == []
        assert account.balance_source == BalanceSource.MANUAL
        assert account.balance_snapshots == []

    def test_account_with_explicit_optional_fields(self) -> None:
        from zorivest_core.domain.enums import AccountType, BalanceSource

        account = _make_account(
            account_type=AccountType.IRA,
            institution="Vanguard",
            currency="USD",
            is_tax_advantaged=True,
            notes="Roth IRA",
            sub_accounts=["sub-1", "sub-2"],
            balance_source=BalanceSource.CSV_IMPORT,
        )
        assert account.is_tax_advantaged is True
        assert account.institution == "Vanguard"
        assert account.sub_accounts == ["sub-1", "sub-2"]
        assert account.balance_source == BalanceSource.CSV_IMPORT


# ── MEU-37 AC-1: is_archived field ──────────────────────────────────────


class TestAccountIsArchived:
    """MEU-37 AC-1: Account has is_archived: bool = False."""

    def test_is_archived_defaults_to_false(self) -> None:
        account = _make_account()
        assert account.is_archived is False

    def test_is_archived_can_be_set_true(self) -> None:
        account = _make_account(is_archived=True)
        assert account.is_archived is True

    def test_is_archived_can_be_toggled(self) -> None:
        account = _make_account()
        assert account.is_archived is False
        account.is_archived = True
        assert account.is_archived is True


# ── MEU-37 AC-2: is_system field ────────────────────────────────────────


class TestAccountIsSystem:
    """MEU-37 AC-2: Account has is_system: bool = False."""

    def test_is_system_defaults_to_false(self) -> None:
        account = _make_account()
        assert account.is_system is False

    def test_is_system_can_be_set_true(self) -> None:
        account = _make_account(is_system=True)
        assert account.is_system is True

    def test_system_account_construction(self) -> None:
        """System Reassignment Account can be created with is_system=True."""
        from zorivest_core.domain.enums import AccountType

        system_acct = _make_account(
            account_id="SYSTEM_DEFAULT",
            name="System Reassignment Account",
            account_type=AccountType.BROKER,
            is_system=True,
        )
        assert system_acct.account_id == "SYSTEM_DEFAULT"
        assert system_acct.name == "System Reassignment Account"
        assert system_acct.is_system is True


# ── AC-4: BalanceSnapshot frozen dataclass ───────────────────────────────


class TestBalanceSnapshot:
    """AC-4: BalanceSnapshot with id, account_id, datetime, balance. Frozen."""

    def test_balance_snapshot_construction(self) -> None:
        snap = _make_balance_snapshot()
        assert snap.id == 1
        assert snap.account_id == "ACC-001"
        assert snap.datetime == datetime(2026, 3, 7, 16, 0, 0)
        assert snap.balance == Decimal("437903.03")

    def test_balance_snapshot_is_frozen(self) -> None:
        snap = _make_balance_snapshot()
        with pytest.raises(AttributeError):
            snap.balance = Decimal("0")  # type: ignore[misc]


# ── AC-5: ImageAttachment frozen dataclass ───────────────────────────────


class TestImageAttachment:
    """AC-5: ImageAttachment with all fields from domain-model-ref lines 100–111. Frozen."""

    def test_image_attachment_construction(self) -> None:
        from zorivest_core.domain.enums import ImageOwnerType

        img = _make_image_attachment()
        assert img.id == 1
        assert img.owner_type == ImageOwnerType.TRADE
        assert img.owner_id == "EX-001"
        assert img.data == b"RIFF\x00\x00\x00\x00WEBP"
        assert img.thumbnail == b""
        assert img.mime_type == "image/webp"
        assert img.caption == ""
        assert img.width == 1920
        assert img.height == 1080
        assert img.file_size == 102400
        assert isinstance(img.created_at, datetime)

    def test_image_attachment_is_frozen(self) -> None:
        img = _make_image_attachment()
        with pytest.raises(AttributeError):
            img.caption = "new caption"  # type: ignore[misc]

    def test_image_attachment_custom_values(self) -> None:
        img = _make_image_attachment(
            thumbnail=b"thumb-data",
            caption="Entry chart",
        )
        assert img.thumbnail == b"thumb-data"
        assert img.caption == "Entry chart"


# ── AC-6: mime_type is always "image/webp" ───────────────────────────────


class TestMimeTypeEnforcement:
    """AC-6: mime_type is always 'image/webp' — enforced at construction."""

    def test_default_mime_type_is_webp(self) -> None:
        img = _make_image_attachment()
        assert img.mime_type == "image/webp"

    def test_non_webp_mime_type_raises(self) -> None:
        """Attempting to construct with a non-webp mime_type must raise ValueError."""
        with pytest.raises(ValueError, match="image/webp"):
            _make_image_attachment(mime_type="image/png")


# ── AC-7: Import surface ────────────────────────────────────────────────


class TestImportSurface:
    """AC-7: Module imports only from allowed modules."""

    def test_import_surface_entities(self) -> None:
        import zorivest_core.domain.entities as mod

        source_file = mod.__file__
        assert source_file is not None

        with open(source_file, encoding="utf-8") as f:
            tree = ast.parse(f.read())

        allowed_modules = {
            "__future__",
            "dataclasses",
            "datetime",
            "decimal",
            "typing",
            "zorivest_core",
        }
        import_count = 0
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top = alias.name.split(".")[0]
                    assert top in allowed_modules, f"Forbidden import: {alias.name}"
                    import_count += 1
            elif isinstance(node, ast.ImportFrom):
                if node.module is not None:
                    top_module = node.module.split(".")[0]
                    assert top_module in allowed_modules, (
                        f"Forbidden import from: {node.module}"
                    )
                    import_count += 1
        # Value: verify at least 2 imports were checked
        assert import_count >= 2, f"Only {import_count} imports found"


# ── Module integrity ────────────────────────────────────────────────────


class TestModuleIntegrity:
    """Verify the module exports exactly the expected entity classes."""

    def test_module_has_expected_classes(self) -> None:
        import zorivest_core.domain.entities as mod

        class_names = [
            name
            for name, obj in inspect.getmembers(mod, inspect.isclass)
            if obj.__module__ == mod.__name__
        ]
        expected = {
            "Trade",
            "Account",
            "BalanceSnapshot",
            "ImageAttachment",
            "TradeReport",  # MEU-52
            "TradePlan",  # MEU-66
            "Watchlist",  # MEU-68
            "WatchlistItem",  # MEU-68
        }
        assert set(class_names) == expected, (
            f"Expected {expected}, got {set(class_names)}"
        )


# ── MEU-52: TradeReport entity ──────────────────────────────────────────


def _make_trade_report(**overrides: object) -> TradeReport:
    """Construct a TradeReport with sensible defaults. Stays within test file."""
    from zorivest_core.domain.entities import TradeReport

    defaults: dict[str, object] = {
        "id": 1,
        "trade_id": "TEST001",
        "setup_quality": 4,
        "execution_quality": 3,
        "followed_plan": True,
        "emotional_state": "neutral",
        "created_at": datetime(2025, 7, 15, 10, 30, 0),
    }
    defaults.update(overrides)
    return TradeReport(**defaults)  # type: ignore[arg-type]


class TestTradeReport:
    """FIC-52 AC-1: TradeReport dataclass with all fields from plan."""

    def test_trade_report_construction_with_required_fields(self) -> None:
        from zorivest_core.domain.entities import TradeReport

        report = TradeReport(
            id=1,
            trade_id="T001",
            setup_quality=5,
            execution_quality=4,
            followed_plan=True,
            emotional_state="confident",
            created_at=datetime(2025, 7, 15, 10, 30, 0),
        )
        assert report.id == 1
        assert report.trade_id == "T001"
        assert report.setup_quality == 5
        assert report.execution_quality == 4
        assert report.followed_plan is True
        assert report.emotional_state == "confident"

    def test_trade_report_defaults(self) -> None:
        report = _make_trade_report()
        assert report.lessons_learned == ""
        assert report.tags == []
        assert report.images == []

    def test_trade_report_with_all_fields(self) -> None:
        report = _make_trade_report(
            lessons_learned="Should have waited for confirmation",
            tags=["options", "spy"],
        )
        assert report.lessons_learned == "Should have waited for confirmation"
        assert report.tags == ["options", "spy"]


class TestTradeReportType:
    """FIC-52 AC-2: Trade.report type is Optional[TradeReport]."""

    def test_trade_report_field_accepts_trade_report(self) -> None:
        from zorivest_core.domain.entities import TradeReport

        report = _make_trade_report()
        trade = _make_trade(report=report)
        assert isinstance(trade.report, TradeReport)
        # Value: verify the actual report fields are accessible
        assert trade.report.trade_id == "TEST001"
        assert trade.report.setup_quality == 4
        assert trade.report is report

    def test_trade_report_field_defaults_to_none(self) -> None:
        trade = _make_trade()
        assert trade.report is None


# ── MEU-52: QualityGrade + EmotionalState enums ─────────────────────────


class TestQualityGrade:
    """FIC-52 AC-3: QualityGrade enum with A-F members and int maps."""

    def test_quality_grade_members(self) -> None:
        from zorivest_core.domain.enums import QualityGrade

        assert QualityGrade.A == "A"
        assert QualityGrade.B == "B"
        assert QualityGrade.C == "C"
        assert QualityGrade.D == "D"
        assert QualityGrade.F == "F"
        assert len(QualityGrade) == 5

    def test_quality_int_map(self) -> None:
        from zorivest_core.domain.enums import QUALITY_INT_MAP

        assert QUALITY_INT_MAP == {"A": 5, "B": 4, "C": 3, "D": 2, "F": 1}

    def test_quality_grade_map(self) -> None:
        from zorivest_core.domain.enums import QUALITY_GRADE_MAP

        assert QUALITY_GRADE_MAP == {5: "A", 4: "B", 3: "C", 2: "D", 1: "F"}

    def test_roundtrip_conversion(self) -> None:
        from zorivest_core.domain.enums import QUALITY_GRADE_MAP, QUALITY_INT_MAP

        for grade, value in QUALITY_INT_MAP.items():
            assert QUALITY_GRADE_MAP[value] == grade


class TestEmotionalState:
    """FIC-52 AC-4: EmotionalState enum — 9-value MCP+GUI superset."""

    def test_emotional_state_members(self) -> None:
        from zorivest_core.domain.enums import EmotionalState

        expected = {
            "calm",
            "anxious",
            "fearful",
            "greedy",
            "frustrated",
            "confident",
            "neutral",
            "impulsive",
            "hesitant",
        }
        actual = {e.value for e in EmotionalState}
        assert actual == expected

    def test_emotional_state_count(self) -> None:
        from zorivest_core.domain.enums import EmotionalState

        assert len(EmotionalState) == 9

    def test_emotional_state_default_is_neutral(self) -> None:
        from zorivest_core.domain.enums import EmotionalState

        assert EmotionalState.NEUTRAL == "neutral"


# ── MEU-66: TradePlan entity ──────────────────────────────────────────────


def _make_trade_plan(**overrides: object) -> TradePlan:
    """Construct a TradePlan with sensible defaults."""
    from zorivest_core.domain.entities import TradePlan
    from zorivest_core.domain.enums import ConvictionLevel, PlanStatus, TradeAction

    defaults: dict[str, object] = {
        "id": 1,
        "ticker": "AAPL",
        "direction": TradeAction.BOT,
        "conviction": ConvictionLevel.HIGH,
        "strategy_name": "Gap & Go",
        "strategy_description": "Long after morning gap on volume",
        "entry_price": 200.0,
        "stop_loss": 195.0,
        "target_price": 215.0,
        "entry_conditions": "Gap > 2%, volume > 1M",
        "exit_conditions": "Target hit or EOD",
        "timeframe": "intraday",
        "risk_reward_ratio": 3.0,
        "status": PlanStatus.DRAFT,
        "linked_trade_id": None,
        "account_id": None,
        "created_at": datetime(2026, 3, 12, 9, 0, 0),
        "updated_at": datetime(2026, 3, 12, 9, 0, 0),
    }
    defaults.update(overrides)
    return TradePlan(**defaults)  # type: ignore[arg-type]


class TestTradePlan:
    """FIC-66 AC-1: TradePlan dataclass with all 18 fields."""

    def test_trade_plan_construction_with_all_fields(self) -> None:
        from zorivest_core.domain.enums import (
            ConvictionLevel,
            PlanStatus,
            TradeAction,
        )

        plan = _make_trade_plan()
        assert plan.id == 1
        assert plan.ticker == "AAPL"
        assert plan.direction == TradeAction.BOT
        assert plan.conviction == ConvictionLevel.HIGH
        assert plan.strategy_name == "Gap & Go"
        assert plan.strategy_description == "Long after morning gap on volume"
        assert plan.entry_price == 200.0
        assert plan.stop_loss == 195.0
        assert plan.target_price == 215.0
        assert plan.entry_conditions == "Gap > 2%, volume > 1M"
        assert plan.exit_conditions == "Target hit or EOD"
        assert plan.timeframe == "intraday"
        assert plan.risk_reward_ratio == 3.0
        assert plan.status == PlanStatus.DRAFT
        assert plan.linked_trade_id is None
        assert plan.account_id is None
        assert isinstance(plan.created_at, datetime)
        assert isinstance(plan.updated_at, datetime)

    def test_trade_plan_defaults(self) -> None:
        plan = _make_trade_plan()
        assert plan.images == []
        assert plan.linked_trade_id is None
        assert plan.account_id is None

    def test_trade_plan_with_images(self) -> None:
        img = _make_image_attachment()
        plan = _make_trade_plan(images=[img])
        assert len(plan.images) == 1


class TestTradePlanRiskReward:
    """FIC-66 AC-2: risk_reward_ratio computed from entry, stop, target."""

    def test_compute_risk_reward_bullish(self) -> None:
        from zorivest_core.domain.entities import TradePlan

        rr = TradePlan.compute_risk_reward(
            entry_price=200.0,
            stop_loss=195.0,
            target_price=215.0,
        )
        # (215 - 200) / (200 - 195) = 15 / 5 = 3.0
        assert rr == pytest.approx(3.0)

    def test_compute_risk_reward_bearish(self) -> None:
        from zorivest_core.domain.entities import TradePlan

        rr = TradePlan.compute_risk_reward(
            entry_price=200.0,
            stop_loss=205.0,
            target_price=185.0,
        )
        # abs(185 - 200) / abs(200 - 205) = 15 / 5 = 3.0
        assert rr == pytest.approx(3.0)

    def test_compute_risk_reward_zero_risk_returns_zero(self) -> None:
        from zorivest_core.domain.entities import TradePlan

        rr = TradePlan.compute_risk_reward(
            entry_price=200.0,
            stop_loss=200.0,
            target_price=210.0,
        )
        assert rr == 0.0


class TestConvictionLevel:
    """FIC-66: ConvictionLevel enum (4 values)."""

    def test_conviction_level_members(self) -> None:
        from zorivest_core.domain.enums import ConvictionLevel

        expected = {"low", "medium", "high", "max"}
        actual = {e.value for e in ConvictionLevel}
        assert actual == expected

    def test_conviction_level_count(self) -> None:
        from zorivest_core.domain.enums import ConvictionLevel

        assert len(ConvictionLevel) == 4


class TestPlanStatus:
    """FIC-66: PlanStatus enum (5 values)."""

    def test_plan_status_members(self) -> None:
        from zorivest_core.domain.enums import PlanStatus

        expected = {"draft", "active", "executed", "expired", "cancelled"}
        actual = {e.value for e in PlanStatus}
        assert actual == expected

    def test_plan_status_count(self) -> None:
        from zorivest_core.domain.enums import PlanStatus

        assert len(PlanStatus) == 5


# ── MEU-68: Watchlist entity ─────────────────────────────────────────────


def _make_watchlist(**overrides: object) -> Watchlist:
    """Construct a Watchlist with sensible defaults."""
    from zorivest_core.domain.entities import Watchlist

    defaults: dict[str, object] = {
        "id": 1,
        "name": "Momentum Plays",
        "description": "High-beta names for swing trades",
        "created_at": datetime(2026, 3, 12, 10, 0, 0),
        "updated_at": datetime(2026, 3, 12, 10, 0, 0),
    }
    defaults.update(overrides)
    return Watchlist(**defaults)  # type: ignore[arg-type]


def _make_watchlist_item(**overrides: object) -> WatchlistItem:
    """Construct a WatchlistItem with sensible defaults."""
    from zorivest_core.domain.entities import WatchlistItem

    defaults: dict[str, object] = {
        "id": 1,
        "watchlist_id": 1,
        "ticker": "AAPL",
        "added_at": datetime(2026, 3, 12, 10, 0, 0),
    }
    defaults.update(overrides)
    return WatchlistItem(**defaults)  # type: ignore[arg-type]


class TestWatchlist:
    """MEU-68 AC-1: Watchlist dataclass with all fields from domain-model-reference."""

    def test_watchlist_construction(self) -> None:
        wl = _make_watchlist()
        assert wl.id == 1
        assert wl.name == "Momentum Plays"
        assert wl.description == "High-beta names for swing trades"
        assert isinstance(wl.created_at, datetime)
        assert isinstance(wl.updated_at, datetime)

    def test_watchlist_defaults(self) -> None:
        wl = _make_watchlist()
        assert wl.tickers == []

    def test_watchlist_with_tickers(self) -> None:
        item = _make_watchlist_item()
        wl = _make_watchlist(tickers=[item])
        assert len(wl.tickers) == 1


class TestWatchlistItem:
    """MEU-68 AC-1: WatchlistItem frozen dataclass."""

    def test_watchlist_item_construction(self) -> None:
        item = _make_watchlist_item()
        assert item.id == 1
        assert item.watchlist_id == 1
        assert item.ticker == "AAPL"
        assert isinstance(item.added_at, datetime)
        assert item.notes == ""

    def test_watchlist_item_is_frozen(self) -> None:
        item = _make_watchlist_item()
        with pytest.raises(AttributeError):
            item.ticker = "MSFT"  # type: ignore[misc]
