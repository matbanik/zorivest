# tests/unit/test_image_service.py
"""Tests for ImageService (MEU-12, AC-12.5, AC-12.6)."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock

import pytest

from zorivest_core.application.commands import AttachImage
from zorivest_core.domain.entities import ImageAttachment, Trade
from zorivest_core.domain.enums import ImageOwnerType, TradeAction
from zorivest_core.domain.exceptions import NotFoundError
from zorivest_core.services.image_service import ImageService


def _make_uow() -> MagicMock:
    uow = MagicMock()
    uow.__enter__ = MagicMock(return_value=uow)
    uow.__exit__ = MagicMock(return_value=False)
    return uow


class TestAttachImage:
    """AC-12.5."""

    def test_attach_image_success(self) -> None:
        trade = Trade(
            exec_id="E001", time=datetime(2025, 1, 15),
            instrument="AAPL", action=TradeAction.BOT,
            quantity=100.0, price=150.0, account_id="ACC001",
        )
        uow = _make_uow()
        uow.trades.get.return_value = trade
        uow.images.save.return_value = 42

        svc = ImageService(uow)
        cmd = AttachImage(
            owner_type=ImageOwnerType.TRADE,
            owner_id="E001",
            data=b"\x00" * 100,
            mime_type="image/webp",
            width=800,
            height=600,
        )
        result = svc.attach_image(cmd)

        assert result == 42
        uow.images.save.assert_called_once()
        # Value: verify the saved image has correct owner info
        saved_args = uow.images.save.call_args[0]
        assert saved_args[0] == "trade"  # owner_type.value
        assert saved_args[1] == "E001"  # owner_id
        assert saved_args[2].owner_type == ImageOwnerType.TRADE
        uow.commit.assert_called_once()

    def test_attach_image_to_nonexistent_trade_raises(self) -> None:
        """AC-12.5: raises NotFoundError for nonexistent owner."""
        uow = _make_uow()
        uow.trades.get.return_value = None

        svc = ImageService(uow)
        cmd = AttachImage(
            owner_type=ImageOwnerType.TRADE,
            owner_id="MISSING",
            data=b"\x00" * 100,
            mime_type="image/webp",
            width=800,
            height=600,
        )
        with pytest.raises(NotFoundError, match="MISSING"):
            svc.attach_image(cmd)


class TestGetTradeImages:
    """AC-12.6."""

    def test_get_images_for_trade(self) -> None:
        """AC-12.6: returns all images for a trade."""
        img = MagicMock(spec=ImageAttachment)
        uow = _make_uow()
        uow.images.get_for_owner.return_value = [img]

        svc = ImageService(uow)
        result = svc.get_trade_images("E001")

        assert len(result) == 1
        uow.images.get_for_owner.assert_called_once_with("trade", "E001")
