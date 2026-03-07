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

import pytest

pytestmark = pytest.mark.unit


# ── Helpers ──────────────────────────────────────────────────────────────


def _make_trade(**overrides: object) -> object:
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


def _make_account(**overrides: object) -> object:
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


def _make_image_attachment(**overrides: object) -> object:
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


def _make_balance_snapshot(**overrides: object) -> object:
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
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top = alias.name.split(".")[0]
                    assert top in allowed_modules, (
                        f"Forbidden import: {alias.name}"
                    )
            elif isinstance(node, ast.ImportFrom):
                if node.module is not None:
                    top_module = node.module.split(".")[0]
                    assert top_module in allowed_modules, (
                        f"Forbidden import from: {node.module}"
                    )


# ── Module integrity ────────────────────────────────────────────────────


class TestModuleIntegrity:
    """Verify the module exports exactly the 4 expected entity classes."""

    def test_module_has_expected_classes(self) -> None:
        import zorivest_core.domain.entities as mod

        class_names = [
            name
            for name, obj in inspect.getmembers(mod, inspect.isclass)
            if obj.__module__ == mod.__name__
        ]
        expected = {"Trade", "Account", "BalanceSnapshot", "ImageAttachment"}
        assert set(class_names) == expected, (
            f"Expected {expected}, got {set(class_names)}"
        )
