# tests/unit/test_commands_dtos.py
"""MEU-6: Commands, Queries & DTOs — Red phase tests.

Tests cover AC-1 through AC-20 from the implementation plan FIC.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import pytest

from zorivest_core.application.commands import (
    AttachImage,
    CreateAccount,
    CreateTrade,
    UpdateBalance,
)
from zorivest_core.application.dtos import (
    AccountDTO,
    BalanceSnapshotDTO,
    ImageAttachmentDTO,
    TradeDTO,
)
from zorivest_core.application.queries import (
    GetAccount,
    GetImage,
    GetTrade,
    ListAccounts,
    ListImages,
    ListTrades,
)
from zorivest_core.domain.enums import (
    AccountType,
    BalanceSource,
    ImageOwnerType,
    TradeAction,
)

pytestmark = pytest.mark.unit


# ── AC-1: CreateTrade frozen dataclass ──────────────────────────────────


class TestCreateTrade:
    """AC-1, AC-2, AC-3: CreateTrade structure and validation."""

    def test_create_trade_valid(self) -> None:
        """AC-1: CreateTrade has all required fields."""
        cmd = CreateTrade(
            exec_id="T001",
            time=datetime(2025, 1, 15, 10, 30),
            instrument="AAPL",
            action=TradeAction.BOT,
            quantity=100.0,
            price=150.50,
            account_id="ACC-1",
        )
        assert cmd.exec_id == "T001"
        assert cmd.instrument == "AAPL"
        assert cmd.action == TradeAction.BOT
        assert cmd.quantity == 100.0
        assert cmd.price == 150.50
        assert cmd.account_id == "ACC-1"
        assert cmd.commission == 0.0
        assert cmd.realized_pnl == 0.0

    def test_create_trade_with_optional_fields(self) -> None:
        """AC-1: CreateTrade with commission and realized_pnl."""
        cmd = CreateTrade(
            exec_id="T002",
            time=datetime(2025, 1, 15),
            instrument="MSFT",
            action=TradeAction.SLD,
            quantity=50.0,
            price=400.0,
            account_id="ACC-1",
            commission=1.50,
            realized_pnl=250.0,
        )
        assert cmd.commission == 1.50
        assert cmd.realized_pnl == 250.0

    def test_create_trade_is_frozen(self) -> None:
        """AC-9: CreateTrade is frozen."""
        cmd = CreateTrade(
            exec_id="T003",
            time=datetime(2025, 1, 1),
            instrument="GOOG",
            action=TradeAction.BOT,
            quantity=10.0,
            price=100.0,
            account_id="ACC-1",
        )
        with pytest.raises(AttributeError):
            cmd.exec_id = "CHANGED"  # type: ignore[misc]

    def test_create_trade_rejects_empty_exec_id(self) -> None:
        """AC-2: CreateTrade rejects empty exec_id."""
        with pytest.raises(ValueError, match="exec_id must not be empty"):
            CreateTrade(
                exec_id="",
                time=datetime(2025, 1, 1),
                instrument="AAPL",
                action=TradeAction.BOT,
                quantity=10.0,
                price=100.0,
                account_id="ACC-1",
            )

    def test_create_trade_rejects_whitespace_exec_id(self) -> None:
        """AC-2: CreateTrade rejects whitespace-only exec_id."""
        with pytest.raises(ValueError, match="exec_id must not be empty"):
            CreateTrade(
                exec_id="   ",
                time=datetime(2025, 1, 1),
                instrument="AAPL",
                action=TradeAction.BOT,
                quantity=10.0,
                price=100.0,
                account_id="ACC-1",
            )

    def test_create_trade_rejects_zero_quantity(self) -> None:
        """AC-3: CreateTrade rejects non-positive quantity."""
        with pytest.raises(ValueError, match="quantity must be positive"):
            CreateTrade(
                exec_id="T004",
                time=datetime(2025, 1, 1),
                instrument="AAPL",
                action=TradeAction.BOT,
                quantity=0.0,
                price=100.0,
                account_id="ACC-1",
            )

    def test_create_trade_rejects_negative_quantity(self) -> None:
        """AC-3: CreateTrade rejects negative quantity."""
        with pytest.raises(ValueError, match="quantity must be positive"):
            CreateTrade(
                exec_id="T005",
                time=datetime(2025, 1, 1),
                instrument="AAPL",
                action=TradeAction.BOT,
                quantity=-5.0,
                price=100.0,
                account_id="ACC-1",
            )


# ── AC-4, AC-5: AttachImage ─────────────────────────────────────────────


class TestAttachImage:
    """AC-4, AC-5: AttachImage structure and WebP enforcement."""

    def test_attach_image_valid(self) -> None:
        """AC-4: AttachImage has all required fields."""
        cmd = AttachImage(
            owner_type=ImageOwnerType.TRADE,
            owner_id="T001",
            data=b"\x00\x01\x02",
            mime_type="image/webp",
            caption="Chart screenshot",
            width=800,
            height=600,
        )
        assert cmd.owner_type == ImageOwnerType.TRADE
        assert cmd.owner_id == "T001"
        assert cmd.data == b"\x00\x01\x02"
        assert cmd.mime_type == "image/webp"
        assert cmd.caption == "Chart screenshot"
        assert cmd.width == 800
        assert cmd.height == 600

    def test_attach_image_is_frozen(self) -> None:
        """AC-9: AttachImage is frozen."""
        cmd = AttachImage(
            owner_type=ImageOwnerType.TRADE,
            owner_id="T001",
            data=b"\x00",
            mime_type="image/webp",
            caption="",
            width=100,
            height=100,
        )
        with pytest.raises(AttributeError):
            cmd.caption = "changed"  # type: ignore[misc]

    def test_attach_image_rejects_non_webp(self) -> None:
        """AC-5: AttachImage enforces mime_type == 'image/webp'."""
        with pytest.raises(ValueError, match="mime_type must be 'image/webp'"):
            AttachImage(
                owner_type=ImageOwnerType.TRADE,
                owner_id="T001",
                data=b"\x00",
                mime_type="image/png",
                caption="",
                width=100,
                height=100,
            )

    def test_attach_image_caption_defaults_to_empty(self) -> None:
        """AC-4: AttachImage.caption defaults to empty string."""
        cmd = AttachImage(
            owner_type=ImageOwnerType.TRADE,
            owner_id="T001",
            data=b"\x00",
            mime_type="image/webp",
            width=100,
            height=100,
        )
        assert cmd.caption == ""


# ── AC-6, AC-7: CreateAccount ───────────────────────────────────────────


class TestCreateAccount:
    """AC-6, AC-7: CreateAccount structure and validation."""

    def test_create_account_valid(self) -> None:
        """AC-6: CreateAccount has all required fields with defaults."""
        cmd = CreateAccount(
            account_id="ACC-1",
            name="Interactive Brokers",
            account_type=AccountType.BROKER,
        )
        assert cmd.account_id == "ACC-1"
        assert cmd.name == "Interactive Brokers"
        assert cmd.account_type == AccountType.BROKER
        assert cmd.institution == ""
        assert cmd.currency == "USD"
        assert cmd.is_tax_advantaged is False
        assert cmd.notes == ""
        assert cmd.balance_source == BalanceSource.MANUAL

    def test_create_account_with_all_fields(self) -> None:
        """AC-6: CreateAccount with all optional fields specified."""
        cmd = CreateAccount(
            account_id="ACC-2",
            name="Roth IRA",
            account_type=AccountType.IRA,
            institution="Vanguard",
            currency="USD",
            is_tax_advantaged=True,
            notes="Rollover from 401k",
            balance_source=BalanceSource.CSV_IMPORT,
        )
        assert cmd.institution == "Vanguard"
        assert cmd.is_tax_advantaged is True
        assert cmd.notes == "Rollover from 401k"
        assert cmd.balance_source == BalanceSource.CSV_IMPORT

    def test_create_account_is_frozen(self) -> None:
        """AC-9: CreateAccount is frozen."""
        cmd = CreateAccount(
            account_id="ACC-3",
            name="Checking",
            account_type=AccountType.BANK,
        )
        with pytest.raises(AttributeError):
            cmd.name = "changed"  # type: ignore[misc]

    def test_create_account_rejects_empty_account_id(self) -> None:
        """AC-7: CreateAccount rejects empty account_id."""
        with pytest.raises(ValueError, match="account_id must not be empty"):
            CreateAccount(
                account_id="",
                name="Test",
                account_type=AccountType.BROKER,
            )

    def test_create_account_rejects_empty_name(self) -> None:
        """AC-7: CreateAccount rejects empty name."""
        with pytest.raises(ValueError, match="name must not be empty"):
            CreateAccount(
                account_id="ACC-4",
                name="",
                account_type=AccountType.BROKER,
            )

    def test_create_account_rejects_whitespace_name(self) -> None:
        """AC-7: CreateAccount rejects whitespace-only name."""
        with pytest.raises(ValueError, match="name must not be empty"):
            CreateAccount(
                account_id="ACC-5",
                name="   ",
                account_type=AccountType.BROKER,
            )


# ── AC-8: UpdateBalance ─────────────────────────────────────────────────


class TestUpdateBalance:
    """AC-8: UpdateBalance structure."""

    def test_update_balance_valid(self) -> None:
        """AC-8: UpdateBalance has all required fields."""
        now = datetime(2025, 3, 7, 12, 0)
        cmd = UpdateBalance(
            account_id="ACC-1",
            balance=Decimal("15000.50"),
            snapshot_datetime=now,
        )
        assert cmd.account_id == "ACC-1"
        assert cmd.balance == Decimal("15000.50")
        assert cmd.snapshot_datetime == now

    def test_update_balance_is_frozen(self) -> None:
        """AC-9: UpdateBalance is frozen."""
        cmd = UpdateBalance(
            account_id="ACC-1",
            balance=Decimal("100"),
            snapshot_datetime=datetime(2025, 1, 1),
        )
        with pytest.raises(AttributeError):
            cmd.balance = Decimal("999")  # type: ignore[misc]

    def test_update_balance_snapshot_datetime_defaults_to_now(self) -> None:
        """AC-8: UpdateBalance.snapshot_datetime defaults to datetime.now."""
        before = datetime.now()
        cmd = UpdateBalance(
            account_id="ACC-1",
            balance=Decimal("5000"),
        )
        after = datetime.now()
        assert before <= cmd.snapshot_datetime <= after


# ── AC-10 through AC-15: Queries ─────────────────────────────────────────


class TestQueries:
    """AC-10 through AC-15: Query frozen dataclasses."""

    def test_get_trade(self) -> None:
        """AC-10: GetTrade has exec_id field."""
        q = GetTrade(exec_id="T001")
        assert q.exec_id == "T001"

    def test_get_trade_is_frozen(self) -> None:
        """AC-10: GetTrade is frozen."""
        q = GetTrade(exec_id="T001")
        with pytest.raises(AttributeError):
            q.exec_id = "X"  # type: ignore[misc]

    def test_list_trades_defaults(self) -> None:
        """AC-11: ListTrades has defaults for limit, offset, account_id."""
        q = ListTrades()
        assert q.limit == 100
        assert q.offset == 0
        assert q.account_id is None

    def test_list_trades_with_filter(self) -> None:
        """AC-11: ListTrades with account filter."""
        q = ListTrades(limit=50, offset=10, account_id="ACC-1")
        assert q.limit == 50
        assert q.offset == 10
        assert q.account_id == "ACC-1"

    def test_get_account(self) -> None:
        """AC-12: GetAccount has account_id field."""
        q = GetAccount(account_id="ACC-1")
        assert q.account_id == "ACC-1"

    def test_list_accounts(self) -> None:
        """AC-13: ListAccounts has no fields."""
        q = ListAccounts()
        # Value: verify it's a frozen dataclass with no custom fields
        with pytest.raises(AttributeError):
            q.nonexistent = True  # type: ignore[attr-defined]

    def test_get_image(self) -> None:
        """AC-14: GetImage has image_id field."""
        q = GetImage(image_id=42)
        assert q.image_id == 42

    def test_list_images(self) -> None:
        """AC-15: ListImages has owner_type and owner_id fields."""
        q = ListImages(owner_type=ImageOwnerType.TRADE, owner_id="T001")
        assert q.owner_type == ImageOwnerType.TRADE
        assert q.owner_id == "T001"


# ── AC-16 through AC-19: DTOs ────────────────────────────────────────────


class TestTradeDTO:
    """AC-16: TradeDTO mirrors Trade fields with image_count."""

    def test_trade_dto_valid(self) -> None:
        """AC-16: TradeDTO has all fields, image_count replaces images list."""
        dto = TradeDTO(
            exec_id="T001",
            time=datetime(2025, 1, 15),
            instrument="AAPL",
            action=TradeAction.BOT,
            quantity=100.0,
            price=150.50,
            account_id="ACC-1",
            commission=1.50,
            realized_pnl=0.0,
            image_count=3,
        )
        assert dto.exec_id == "T001"
        assert dto.image_count == 3

    def test_trade_dto_is_frozen(self) -> None:
        """AC-16: TradeDTO is frozen."""
        dto = TradeDTO(
            exec_id="T001",
            time=datetime(2025, 1, 15),
            instrument="AAPL",
            action=TradeAction.BOT,
            quantity=100.0,
            price=150.50,
            account_id="ACC-1",
            commission=0.0,
            realized_pnl=0.0,
            image_count=0,
        )
        with pytest.raises(AttributeError):
            dto.image_count = 5  # type: ignore[misc]


class TestAccountDTO:
    """AC-17: AccountDTO mirrors Account fields with latest_balance."""

    def test_account_dto_valid(self) -> None:
        """AC-17: AccountDTO has all fields, latest_balance replaces snapshots."""
        dto = AccountDTO(
            account_id="ACC-1",
            name="Interactive Brokers",
            account_type=AccountType.BROKER,
            institution="IBKR",
            currency="USD",
            is_tax_advantaged=False,
            notes="",
            balance_source=BalanceSource.MANUAL,
            latest_balance=Decimal("15000.50"),
        )
        assert dto.account_id == "ACC-1"
        assert dto.latest_balance == Decimal("15000.50")

    def test_account_dto_null_balance(self) -> None:
        """AC-17: AccountDTO allows None for latest_balance."""
        dto = AccountDTO(
            account_id="ACC-2",
            name="Empty",
            account_type=AccountType.BANK,
            institution="",
            currency="USD",
            is_tax_advantaged=False,
            notes="",
            balance_source=BalanceSource.MANUAL,
            latest_balance=None,
        )
        assert dto.latest_balance is None

    def test_account_dto_is_frozen(self) -> None:
        """AC-17: AccountDTO is frozen."""
        dto = AccountDTO(
            account_id="ACC-1",
            name="Test",
            account_type=AccountType.BROKER,
            institution="",
            currency="USD",
            is_tax_advantaged=False,
            notes="",
            balance_source=BalanceSource.MANUAL,
            latest_balance=None,
        )
        with pytest.raises(AttributeError):
            dto.name = "changed"  # type: ignore[misc]


class TestBalanceSnapshotDTO:
    """AC-18: BalanceSnapshotDTO."""

    def test_balance_snapshot_dto_valid(self) -> None:
        """AC-18: BalanceSnapshotDTO has all fields."""
        dto = BalanceSnapshotDTO(
            id=1,
            account_id="ACC-1",
            datetime=datetime(2025, 3, 7),
            balance=Decimal("15000"),
        )
        assert dto.id == 1
        assert dto.account_id == "ACC-1"
        assert dto.balance == Decimal("15000")

    def test_balance_snapshot_dto_is_frozen(self) -> None:
        """AC-18: BalanceSnapshotDTO is frozen."""
        dto = BalanceSnapshotDTO(
            id=1,
            account_id="ACC-1",
            datetime=datetime(2025, 1, 1),
            balance=Decimal("0"),
        )
        with pytest.raises(AttributeError):
            dto.balance = Decimal("999")  # type: ignore[misc]


class TestImageAttachmentDTO:
    """AC-19: ImageAttachmentDTO — no data/thumbnail."""

    def test_image_attachment_dto_valid(self) -> None:
        """AC-19: ImageAttachmentDTO has all fields, no data/thumbnail."""
        now = datetime(2025, 3, 7, 12, 0)
        dto = ImageAttachmentDTO(
            id=42,
            owner_type=ImageOwnerType.TRADE,
            owner_id="T001",
            mime_type="image/webp",
            caption="Chart",
            width=800,
            height=600,
            file_size=12345,
            created_at=now,
        )
        assert dto.id == 42
        assert dto.mime_type == "image/webp"
        assert dto.file_size == 12345
        assert not hasattr(dto, "data")
        assert not hasattr(dto, "thumbnail")

    def test_image_attachment_dto_is_frozen(self) -> None:
        """AC-19: ImageAttachmentDTO is frozen."""
        dto = ImageAttachmentDTO(
            id=1,
            owner_type=ImageOwnerType.TRADE,
            owner_id="T001",
            mime_type="image/webp",
            caption="",
            width=100,
            height=100,
            file_size=1000,
            created_at=datetime(2025, 1, 1),
        )
        with pytest.raises(AttributeError):
            dto.caption = "changed"  # type: ignore[misc]


# ── AC-20: Module imports ────────────────────────────────────────────────


class TestModuleImports:
    """AC-20: Module import constraints."""

    def test_commands_module_exists(self) -> None:
        """AC-20: commands module importable."""
        import zorivest_core.application.commands as mod

        # Value: verify class identity, not just presence
        assert mod.CreateTrade is CreateTrade
        assert mod.AttachImage is AttachImage
        assert mod.CreateAccount is CreateAccount
        assert mod.UpdateBalance is UpdateBalance

    def test_commands_module_no_unexpected_exports(self) -> None:
        """AC-20: commands module has exactly 4 command classes."""
        import zorivest_core.application.commands as mod

        public = {n for n in dir(mod) if not n.startswith("_")}
        expected = {
            "CreateTrade",
            "AttachImage",
            "CreateAccount",
            "UpdateBalance",
            "dataclass",
            "field",
            "datetime",
            "Decimal",
            "AccountType",
            "BalanceSource",
            "ImageOwnerType",
            "TradeAction",
            "annotations",
        }
        unexpected = public - expected
        assert not unexpected, f"Unexpected exports: {unexpected}"

    def test_queries_module_exists(self) -> None:
        """AC-20: queries module importable."""
        import zorivest_core.application.queries as mod

        # Value: verify class identity
        assert mod.GetTrade is GetTrade
        assert mod.ListTrades is ListTrades
        assert mod.GetAccount is GetAccount
        assert mod.ListAccounts is ListAccounts
        assert mod.GetImage is GetImage
        assert mod.ListImages is ListImages

    def test_queries_module_no_unexpected_exports(self) -> None:
        """AC-20: queries module has exactly 6 query classes."""
        import zorivest_core.application.queries as mod

        public = {n for n in dir(mod) if not n.startswith("_")}
        expected = {
            "GetTrade",
            "ListTrades",
            "GetAccount",
            "ListAccounts",
            "GetImage",
            "ListImages",
            "dataclass",
            "ImageOwnerType",
            "annotations",
        }
        unexpected = public - expected
        assert not unexpected, f"Unexpected exports: {unexpected}"

    def test_dtos_module_exists(self) -> None:
        """AC-20: dtos module importable."""
        import zorivest_core.application.dtos as mod

        # Value: verify class identity
        assert mod.TradeDTO is TradeDTO
        assert mod.AccountDTO is AccountDTO
        assert mod.BalanceSnapshotDTO is BalanceSnapshotDTO
        assert mod.ImageAttachmentDTO is ImageAttachmentDTO

    def test_dtos_module_no_unexpected_exports(self) -> None:
        """AC-20: dtos module has exactly 4 DTO classes."""
        import zorivest_core.application.dtos as mod

        public = {n for n in dir(mod) if not n.startswith("_")}
        expected = {
            "TradeDTO",
            "AccountDTO",
            "BalanceSnapshotDTO",
            "ImageAttachmentDTO",
            "dataclass",
            "datetime",
            "Decimal",
            "AccountType",
            "BalanceSource",
            "ImageOwnerType",
            "TradeAction",
            "annotations",
        }
        unexpected = public - expected
        assert not unexpected, f"Unexpected exports: {unexpected}"
