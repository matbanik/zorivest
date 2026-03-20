# tests/unit/test_service_extensions.py
"""Tests for MEU-Prep: service layer extensions + version module.

Tests written FIRST (Red phase) per TDD protocol.
Covers: TradeService list/update/delete, AccountService update/delete,
        ImageService get_image/get_full_image/get_images_for_owner,
        version module get_version/get_version_context.
"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock

import pytest

from zorivest_core.domain.entities import Account, ImageAttachment, Trade
from zorivest_core.domain.enums import (
    AccountType,
    ImageOwnerType,
    TradeAction,
)
from zorivest_core.domain.exceptions import NotFoundError
from zorivest_core.services.account_service import AccountService
from zorivest_core.services.image_service import ImageService
from zorivest_core.services.trade_service import TradeService


def _make_uow() -> MagicMock:
    """Create a mock UoW with standard context-manager support."""
    uow = MagicMock()
    uow.__enter__ = MagicMock(return_value=uow)
    uow.__exit__ = MagicMock(return_value=False)
    return uow


def _sample_trade(exec_id: str = "E001", **overrides: object) -> Trade:
    defaults = {
        "exec_id": exec_id,
        "time": datetime(2025, 1, 15, 10, 30),
        "instrument": "AAPL",
        "action": TradeAction.BOT,
        "quantity": 100.0,
        "price": 150.50,
        "account_id": "ACC001",
    }
    defaults.update(overrides)
    return Trade(**defaults)  # type: ignore[arg-type]


def _sample_account(account_id: str = "ACC001", **overrides: object) -> Account:
    defaults = {
        "account_id": account_id,
        "name": "Main Brokerage",
        "account_type": AccountType.BROKER,
    }
    defaults.update(overrides)
    return Account(**defaults)  # type: ignore[arg-type]


def _sample_image(image_id: int = 1) -> ImageAttachment:
    return ImageAttachment(
        id=image_id,
        owner_type=ImageOwnerType.TRADE,
        owner_id="E001",
        data=b"\x00" * 100,
        width=800,
        height=600,
        file_size=100,
        created_at=datetime(2025, 1, 15),
        thumbnail=b"\x00" * 10,
        mime_type="image/webp",
        caption="chart screenshot",
    )


# ── TradeService extensions ─────────────────────────────────────────────

class TestListTrades:
    """MEU-Prep: TradeService.list_trades."""

    def test_list_trades_default(self) -> None:
        """Returns paginated list with defaults (limit=100, offset=0)."""
        uow = _make_uow()
        trades = [_sample_trade("E001"), _sample_trade("E002")]
        uow.trades.list_filtered.return_value = trades

        svc = TradeService(uow)
        result = svc.list_trades()

        assert len(result) == 2
        uow.trades.list_filtered.assert_called_once_with(
            limit=100, offset=0, account_id=None, sort="-time", search=None,
        )

    def test_list_trades_with_filters(self) -> None:
        """Passes account_id and sort through to repo."""
        uow = _make_uow()
        uow.trades.list_filtered.return_value = [_sample_trade()]

        svc = TradeService(uow)
        result = svc.list_trades(limit=10, offset=5, account_id="ACC001", sort="time")

        assert len(result) == 1
        uow.trades.list_filtered.assert_called_once_with(
            limit=10, offset=5, account_id="ACC001", sort="time", search=None,
        )


class TestUpdateTrade:
    """MEU-Prep: TradeService.update_trade."""

    def test_update_trade_success(self) -> None:
        """Updates trade fields and commits."""
        trade = _sample_trade()
        uow = _make_uow()
        uow.trades.get.return_value = trade

        svc = TradeService(uow)
        result = svc.update_trade("E001", commission=5.0, realized_pnl=100.0)

        assert result.commission == 5.0
        assert result.realized_pnl == 100.0
        uow.trades.update.assert_called_once()
        uow.commit.assert_called_once()

    def test_update_trade_not_found(self) -> None:
        """Raises NotFoundError for nonexistent trade."""
        uow = _make_uow()
        uow.trades.get.return_value = None

        svc = TradeService(uow)
        with pytest.raises(NotFoundError, match="E999"):
            svc.update_trade("E999", commission=5.0)


class TestDeleteTrade:
    """MEU-Prep: TradeService.delete_trade."""

    def test_delete_trade_success(self) -> None:
        """Deletes trade and commits."""
        uow = _make_uow()

        svc = TradeService(uow)
        svc.delete_trade("E001")

        uow.trades.delete.assert_called_once_with("E001")
        uow.commit.assert_called_once()
        uow.__enter__.assert_called_once()


# ── AccountService extensions ───────────────────────────────────────────

class TestUpdateAccount:
    """MEU-Prep: AccountService.update_account."""

    def test_update_account_success(self) -> None:
        """Updates account fields and commits."""
        account = _sample_account()
        uow = _make_uow()
        uow.accounts.get.return_value = account

        svc = AccountService(uow)
        result = svc.update_account("ACC001", name="Updated Name", institution="Fidelity")

        assert result.name == "Updated Name"
        assert result.institution == "Fidelity"
        uow.accounts.update.assert_called_once()
        uow.commit.assert_called_once()

    def test_update_account_not_found(self) -> None:
        """Raises NotFoundError for nonexistent account."""
        uow = _make_uow()
        uow.accounts.get.return_value = None

        svc = AccountService(uow)
        with pytest.raises(NotFoundError, match="UNKNOWN"):
            svc.update_account("UNKNOWN", name="New Name")


class TestDeleteAccount:
    """MEU-Prep: AccountService.delete_account."""

    def test_delete_account_success(self) -> None:
        """Deletes account and commits."""
        uow = _make_uow()

        svc = AccountService(uow)
        svc.delete_account("ACC001")

        uow.accounts.delete.assert_called_once_with("ACC001")
        uow.commit.assert_called_once()
        uow.__enter__.assert_called_once()


# ── ImageService extensions ─────────────────────────────────────────────

class TestGetImage:
    """MEU-Prep: ImageService.get_image."""

    def test_get_image_success(self) -> None:
        """Returns ImageAttachment for valid id."""
        img = _sample_image(42)
        uow = _make_uow()
        uow.images.get.return_value = img

        svc = ImageService(uow)
        result = svc.get_image(42)

        assert result.id == 42
        assert result.caption == "chart screenshot"

    def test_get_image_not_found(self) -> None:
        """Raises NotFoundError for nonexistent image."""
        uow = _make_uow()
        uow.images.get.return_value = None

        svc = ImageService(uow)
        with pytest.raises(NotFoundError, match="999"):
            svc.get_image(999)


class TestGetFullImage:
    """MEU-Prep: ImageService.get_full_image."""

    def test_get_full_image_returns_bytes(self) -> None:
        """Returns full image bytes via repo."""
        uow = _make_uow()
        uow.images.get_full_data.return_value = b"\x00" * 500

        svc = ImageService(uow)
        result = svc.get_full_image(42)

        assert len(result) == 500
        uow.images.get_full_data.assert_called_once_with(42)


class TestGetImagesForOwner:
    """MEU-Prep: ImageService.get_images_for_owner (renamed from get_trade_images)."""

    def test_get_images_for_owner(self) -> None:
        """Returns all images for an owner_type/owner_id pair."""
        img = _sample_image()
        uow = _make_uow()
        uow.images.get_for_owner.return_value = [img]

        svc = ImageService(uow)
        result = svc.get_images_for_owner("trade", "E001")

        assert len(result) == 1
        uow.images.get_for_owner.assert_called_once_with("trade", "E001")


# ── Version module ──────────────────────────────────────────────────────

class TestVersionModule:
    """MEU-Prep: zorivest_core.version."""

    def test_get_version_returns_semver(self) -> None:
        """Returns a SemVer-like version string."""
        from zorivest_core.version import get_version

        version = get_version()
        assert isinstance(version, str)
        # At minimum, should contain a dot-separated format
        parts = version.split(".")
        assert len(parts) >= 2, f"Expected SemVer, got: {version}"

    def test_get_version_context_returns_valid_value(self) -> None:
        """Returns one of: frozen, installed, dev."""
        from zorivest_core.version import get_version_context

        context = get_version_context()
        assert context in {"frozen", "installed", "dev"}, f"Unexpected context: {context}"
