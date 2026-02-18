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
            image_data=b"\x89PNG...",
            mime_type="image/png",
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
        self.uow.images.get_for_trade.return_value = [make_image(), make_image()]
        images = self.service.get_trade_images("TRADE1")
        assert len(images) == 2

    def test_get_thumbnail(self):
        self.uow.images.get_thumbnail.return_value = b"\x89PNG_thumb"
        thumb = self.service.get_thumbnail(image_id=1, max_size=200)
        assert len(thumb) > 0
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

## Outputs

- `TradeService` fully tested with deduplication
- `ImageService` with attach, retrieve, thumbnail operations
- `AccountService` for balance management
- `CalculatorService` wrapping the pure calculator function
- `SettingsService` with `SettingsResolver` (three-tier resolution, reset-to-default) — see [Phase 2A](02a-backup-restore.md)
- `BackupService` wrapping `BackupManager` + `BackupRecoveryManager` — see [Phase 2A](02a-backup-restore.md)
- `ConfigExportService` for JSON config export/import with allowlist — see [Phase 2A](02a-backup-restore.md)
- All services use Unit of Work pattern for transactions
