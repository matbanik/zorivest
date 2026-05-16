# tests/unit/test_tax_sync_service.py
"""FIC tests for Tax Sync Service — MEU-217 ACs 217.1–217.10.

Feature Intent Contract:
  TaxService.sync_lots(account_id=None) materializes BOT trades into TaxLots
  with provenance tracking. Returns a SyncReport with counts and conflicts.

  Behaviors:
    - AC-217-1: Creates new lots from BOT trades with no existing lot
    - AC-217-2: Idempotent — same source hash skips re-creation
    - AC-217-3: Changed source hash + is_user_modified=False → auto-update
    - AC-217-4: Changed source hash + is_user_modified=True → flag conflict
    - AC-217-5: Orphaned lots flagged when source trade is deleted
    - AC-217-6: SyncReport returned with created/updated/conflict/orphaned counts
    - AC-217-7: conflict_resolution='block' aborts with SyncAbortError
    - AC-217-8: conflict_resolution='auto_resolve' overwrites even user-modified
    - AC-217-9: Per-account scope (account_id param)
    - AC-217-10: Cross-account sync (account_id=None syncs all accounts)

All tests written FIRST (RED phase) per TDD protocol.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from zorivest_core.domain.entities import TaxLot, Trade
from zorivest_core.domain.enums import TradeAction
from zorivest_core.services.tax_service import TaxService


# ── Helpers ──────────────────────────────────────────────────────────────


def _bot_trade(
    exec_id: str = "T-BOT-1",
    ticker: str = "AAPL",
    quantity: float = 100.0,
    price: float = 150.0,
    account_id: str = "ACC-1",
    time: datetime | None = None,
) -> Trade:
    return Trade(
        exec_id=exec_id,
        time=time or datetime(2024, 3, 15, 10, 0, tzinfo=timezone.utc),
        instrument=ticker,
        action=TradeAction.BOT,
        quantity=quantity,
        price=price,
        account_id=account_id,
    )


def _lot(
    lot_id: str = "L1",
    ticker: str = "AAPL",
    account_id: str = "ACC-1",
    source_hash: str | None = None,
    is_user_modified: bool = False,
    sync_status: str = "synced",
    is_closed: bool = False,
    open_date: datetime | None = None,
) -> TaxLot:
    return TaxLot(
        lot_id=lot_id,
        account_id=account_id,
        ticker=ticker,
        open_date=open_date or datetime(2024, 3, 15, tzinfo=timezone.utc),
        close_date=None,
        quantity=100.0,
        cost_basis=Decimal("150.00"),
        proceeds=Decimal("0.00"),
        wash_sale_adjustment=Decimal("0.00"),
        is_closed=is_closed,
        linked_trade_ids=["T-BOT-1"],
        source_hash=source_hash,
        is_user_modified=is_user_modified,
        sync_status=sync_status,
    )


def _mock_uow(
    trades: list[Trade] | None = None,
    lots: list[TaxLot] | None = None,
    conflict_resolution: str = "flag",
) -> MagicMock:
    """Create a mock UoW suitable for sync_lots tests."""
    uow = MagicMock()
    uow.__enter__ = MagicMock(return_value=uow)
    uow.__exit__ = MagicMock(return_value=False)

    # trades repo
    all_trades = trades or []
    uow.trades.list_all.return_value = all_trades
    uow.trades.list_for_account.side_effect = lambda aid: [
        t for t in all_trades if t.account_id == aid
    ]

    # tax_lots repo
    all_lots = lots or []
    lot_map = {lot.lot_id: lot for lot in all_lots}
    uow.tax_lots.list_for_account.side_effect = lambda aid: [
        lot for lot in all_lots if lot.account_id == aid
    ]
    uow.tax_lots.list_all_filtered.return_value = all_lots
    uow.tax_lots.get.side_effect = lambda lid: lot_map.get(lid)
    uow.tax_lots.list_filtered.return_value = all_lots

    # accounts repo — return unique accounts
    account_ids = list({t.account_id for t in all_trades})
    accounts = []
    for aid in account_ids:
        acct = MagicMock()
        acct.account_id = aid
        acct.is_tax_advantaged = False
        accounts.append(acct)
    uow.accounts.list_all.return_value = accounts

    # settings resolver — tax.conflict_resolution
    settings_mock = MagicMock()
    settings_mock.get.return_value = conflict_resolution
    uow.settings = settings_mock

    # tax_profiles repo
    uow.tax_profiles.get_for_year.return_value = None

    return uow


def _compute_expected_hash(trade: Trade) -> str:
    """Mirror the expected hash computation for test verification."""
    raw = f"{trade.exec_id}|{trade.instrument}|{trade.quantity}|{trade.price}|{trade.time.isoformat()}"
    return hashlib.sha256(raw.encode()).hexdigest()


# ── AC-217-1: New lot creation ──────────────────────────────────────────


class TestSyncLotsNewCreation:
    """AC-217-1: sync_lots creates new lots from BOT trades with no existing lot."""

    def test_creates_lot_from_bot_trade(self) -> None:
        trade = _bot_trade()
        uow = _mock_uow(trades=[trade])
        svc = TaxService(uow)

        report = svc.sync_lots()

        assert report.created == 1
        uow.tax_lots.save.assert_called()

    def test_skips_sell_trades(self) -> None:
        """Only BOT trades create lots; SLD trades are ignored."""
        sell = Trade(
            exec_id="T-SELL-1",
            time=datetime(2024, 3, 15, 10, 0, tzinfo=timezone.utc),
            instrument="AAPL",
            action=TradeAction.SLD,
            quantity=100.0,
            price=160.0,
            account_id="ACC-1",
        )
        uow = _mock_uow(trades=[sell])
        svc = TaxService(uow)

        report = svc.sync_lots()

        assert report.created == 0

    def test_created_lot_has_source_hash(self) -> None:
        trade = _bot_trade()
        uow = _mock_uow(trades=[trade])
        svc = TaxService(uow)

        svc.sync_lots()

        saved_lot = uow.tax_lots.save.call_args[0][0]
        assert saved_lot.source_hash is not None
        assert len(saved_lot.source_hash) == 64  # SHA-256 hex

    def test_created_lot_has_materialized_at(self) -> None:
        trade = _bot_trade()
        uow = _mock_uow(trades=[trade])
        svc = TaxService(uow)

        svc.sync_lots()

        saved_lot = uow.tax_lots.save.call_args[0][0]
        assert saved_lot.materialized_at is not None


# ── AC-217-2: Idempotency ───────────────────────────────────────────────


class TestSyncLotsIdempotency:
    """AC-217-2: Re-syncing with same source hash skips re-creation."""

    def test_same_hash_skips_update(self) -> None:
        trade = _bot_trade()
        expected_hash = _compute_expected_hash(trade)
        existing_lot = _lot(
            lot_id=f"lot-{trade.exec_id}",
            source_hash=expected_hash,
        )
        uow = _mock_uow(trades=[trade], lots=[existing_lot])
        svc = TaxService(uow)

        report = svc.sync_lots()

        assert report.created == 0
        assert report.updated == 0
        assert report.skipped == 1


# ── AC-217-3: Auto-update changed source ─────────────────────────────────


class TestSyncLotsAutoUpdate:
    """AC-217-3: Changed source hash + is_user_modified=False → auto-update."""

    def test_changed_hash_auto_updates(self) -> None:
        trade = _bot_trade()
        existing_lot = _lot(
            lot_id=f"lot-{trade.exec_id}",
            source_hash="old_stale_hash_value",
            is_user_modified=False,
        )
        uow = _mock_uow(trades=[trade], lots=[existing_lot])
        svc = TaxService(uow)

        report = svc.sync_lots()

        assert report.updated == 1


# ── AC-217-4: Conflict flagging ──────────────────────────────────────────


class TestSyncLotsConflictFlagging:
    """AC-217-4: Changed source hash + is_user_modified=True → flag conflict."""

    def test_user_modified_lot_flagged_as_conflict(self) -> None:
        trade = _bot_trade()
        existing_lot = _lot(
            lot_id=f"lot-{trade.exec_id}",
            source_hash="old_stale_hash_value",
            is_user_modified=True,
        )
        uow = _mock_uow(trades=[trade], lots=[existing_lot])
        svc = TaxService(uow)

        report = svc.sync_lots()

        assert report.conflicts == 1

    def test_conflict_details_include_lot_id(self) -> None:
        trade = _bot_trade()
        existing_lot = _lot(
            lot_id=f"lot-{trade.exec_id}",
            source_hash="old_stale_hash_value",
            is_user_modified=True,
        )
        uow = _mock_uow(trades=[trade], lots=[existing_lot])
        svc = TaxService(uow)

        report = svc.sync_lots()

        assert len(report.conflict_details) == 1
        assert report.conflict_details[0].lot_id == f"lot-{trade.exec_id}"


# ── AC-217-5: Orphan detection ───────────────────────────────────────────


class TestSyncLotsOrphanDetection:
    """AC-217-5: Lots without matching source trade are flagged as orphaned."""

    def test_orphaned_lot_flagged(self) -> None:
        # Lot exists but no matching trade
        orphan_lot = _lot(lot_id="lot-T-DELETED", source_hash="some_hash")
        uow = _mock_uow(trades=[], lots=[orphan_lot])
        svc = TaxService(uow)

        report = svc.sync_lots()

        assert report.orphaned == 1


# ── AC-217-6: SyncReport structure ───────────────────────────────────────


class TestSyncReport:
    """AC-217-6: SyncReport has required fields."""

    def test_report_has_all_counts(self) -> None:
        uow = _mock_uow(trades=[])
        svc = TaxService(uow)

        report = svc.sync_lots()

        assert report.created == 0
        assert report.updated == 0
        assert report.skipped == 0
        assert report.conflicts == 0
        assert report.orphaned == 0
        assert report.conflict_details == []

    def test_report_has_account_id(self) -> None:
        uow = _mock_uow(trades=[])
        svc = TaxService(uow)

        report = svc.sync_lots(account_id="ACC-1")

        assert report.account_id == "ACC-1"


# ── AC-217-7: Block strategy ────────────────────────────────────────────


class TestSyncLotsBlockStrategy:
    """AC-217-7: conflict_resolution='block' aborts with SyncAbortError."""

    def test_block_raises_on_conflict(self) -> None:
        from zorivest_core.domain.exceptions import SyncAbortError

        trade = _bot_trade()
        existing_lot = _lot(
            lot_id=f"lot-{trade.exec_id}",
            source_hash="old_stale_hash_value",
            is_user_modified=True,
        )
        uow = _mock_uow(
            trades=[trade], lots=[existing_lot], conflict_resolution="block"
        )
        svc = TaxService(uow)

        with pytest.raises(SyncAbortError):
            svc.sync_lots()


# ── AC-217-8: Auto-resolve strategy ─────────────────────────────────────


class TestSyncLotsAutoResolve:
    """AC-217-8: conflict_resolution='auto_resolve' overwrites user-modified."""

    def test_auto_resolve_overwrites_user_modified(self) -> None:
        trade = _bot_trade()
        existing_lot = _lot(
            lot_id=f"lot-{trade.exec_id}",
            source_hash="old_stale_hash_value",
            is_user_modified=True,
        )
        uow = _mock_uow(
            trades=[trade],
            lots=[existing_lot],
            conflict_resolution="auto_resolve",
        )
        svc = TaxService(uow)

        report = svc.sync_lots()

        # Auto-resolve should update, not flag
        assert report.updated == 1
        assert report.conflicts == 0


# ── AC-217-9: Per-account scope ──────────────────────────────────────────


class TestSyncLotsPerAccount:
    """AC-217-9: account_id param scopes sync to that account only."""

    def test_scoped_to_account(self) -> None:
        trade_a = _bot_trade(exec_id="T-A1", account_id="ACC-1")
        trade_b = _bot_trade(exec_id="T-B1", account_id="ACC-2")
        uow = _mock_uow(trades=[trade_a, trade_b])
        svc = TaxService(uow)

        report = svc.sync_lots(account_id="ACC-1")

        # Should only process ACC-1 trade
        assert report.created == 1
        saved_lot = uow.tax_lots.save.call_args[0][0]
        assert saved_lot.account_id == "ACC-1"


# ── AC-217-10: Cross-account sync ───────────────────────────────────────


class TestSyncLotsAllAccounts:
    """AC-217-10: account_id=None syncs all accounts."""

    def test_syncs_all_accounts(self) -> None:
        trade_a = _bot_trade(exec_id="T-A1", account_id="ACC-1")
        trade_b = _bot_trade(exec_id="T-B1", account_id="ACC-2")
        uow = _mock_uow(trades=[trade_a, trade_b])
        svc = TaxService(uow)

        report = svc.sync_lots()

        assert report.created == 2


# ── Helpers for SLD closing tests (MEU-218b) ────────────────────────────


def _sld_trade(
    exec_id: str = "T-SLD-1",
    ticker: str = "AAPL",
    quantity: float = 100.0,
    price: float = 160.0,
    account_id: str = "ACC-1",
    time: datetime | None = None,
) -> Trade:
    return Trade(
        exec_id=exec_id,
        time=time or datetime(2024, 6, 15, 10, 0, tzinfo=timezone.utc),
        instrument=ticker,
        action=TradeAction.SLD,
        quantity=quantity,
        price=price,
        account_id=account_id,
    )


def _mock_uow_with_tracking(
    trades: list[Trade] | None = None,
    lots: list[TaxLot] | None = None,
    conflict_resolution: str = "flag",
) -> MagicMock:
    """Create a mock UoW that tracks saved lots for re-query after BOT pass.

    The SLD closing pass re-queries lots after the BOT pass to build the
    open lots index. This mock tracks save() calls and includes them in
    subsequent list_all_filtered() responses.
    """
    uow = _mock_uow(trades=trades, lots=lots, conflict_resolution=conflict_resolution)

    # Track lots saved during BOT pass so SLD pass can see them
    saved_lots: list[TaxLot] = []
    original_lots = list(lots or [])

    def save_and_track(lot: TaxLot) -> None:
        saved_lots.append(lot)

    uow.tax_lots.save.side_effect = save_and_track

    # After BOT pass, list_all_filtered should return original + newly saved
    def list_all_with_saved(**kwargs: object) -> list[TaxLot]:
        return original_lots + saved_lots

    uow.tax_lots.list_all_filtered.side_effect = list_all_with_saved

    # Same for per-account queries
    def list_for_account_with_saved(aid: str) -> list[TaxLot]:
        return [lot for lot in (original_lots + saved_lots) if lot.account_id == aid]

    uow.tax_lots.list_for_account.side_effect = list_for_account_with_saved

    return uow


# ── AC-218b-1: SLD exact match closing ──────────────────────────────────


class TestSyncLotsCloseSLD:
    """AC-218b-1: sync_lots closes open lots by matching SLD trades using FIFO."""

    def test_sld_closes_matching_open_lot(self) -> None:
        """A SLD trade matching an open lot by ticker+account closes it."""
        bot = _bot_trade(exec_id="T-BOT-1", ticker="AAPL", price=150.0)
        sell = _sld_trade(
            exec_id="T-SLD-1",
            ticker="AAPL",
            price=170.0,
            quantity=100.0,
            time=datetime(2024, 6, 15, 10, 0, tzinfo=timezone.utc),
        )
        uow = _mock_uow_with_tracking(trades=[bot, sell])
        svc = TaxService(uow)

        report = svc.sync_lots()

        assert report.created == 1  # BOT creates lot
        assert report.closed == 1  # SLD closes it
        # Verify the lot was updated with close data
        update_calls = uow.tax_lots.update.call_args_list
        closed_updates = [call[0][0] for call in update_calls if call[0][0].is_closed]
        assert len(closed_updates) == 1
        closed_lot = closed_updates[0]
        assert closed_lot.is_closed is True
        assert closed_lot.close_date is not None
        assert closed_lot.proceeds == Decimal("170.0")
        assert closed_lot.realized_gain_loss != Decimal("0")

    def test_sld_no_matching_lot_skipped(self) -> None:
        """A SLD trade with no matching open lot is silently skipped."""
        # Only a sell, no corresponding buy
        sell = _sld_trade(exec_id="T-SLD-ORPHAN", ticker="NVDA")
        uow = _mock_uow_with_tracking(trades=[sell])
        svc = TaxService(uow)

        report = svc.sync_lots()

        assert report.created == 0
        assert report.closed == 0

    def test_already_closed_lot_not_reclosed(self) -> None:
        """An already-closed lot should not be matched again."""
        bot = _bot_trade(exec_id="T-BOT-1", ticker="AAPL", price=150.0)
        sell = _sld_trade(exec_id="T-SLD-1", ticker="AAPL", price=170.0)
        closed_lot = _lot(
            lot_id="lot-T-BOT-1",
            ticker="AAPL",
            source_hash=_compute_expected_hash(bot),
            is_closed=True,
        )
        uow = _mock_uow_with_tracking(trades=[bot, sell], lots=[closed_lot])
        svc = TaxService(uow)

        report = svc.sync_lots()

        # BOT skipped (idempotent), SLD skipped (lot already closed)
        assert report.closed == 0

    def test_fifo_closes_oldest_lot_first(self) -> None:
        """With multiple open lots for same ticker, FIFO closes the oldest."""
        bot_old = _bot_trade(
            exec_id="T-BOT-OLD",
            ticker="TSLA",
            price=200.0,
            time=datetime(2024, 1, 1, 10, 0, tzinfo=timezone.utc),
        )
        bot_new = _bot_trade(
            exec_id="T-BOT-NEW",
            ticker="TSLA",
            price=250.0,
            time=datetime(2024, 3, 1, 10, 0, tzinfo=timezone.utc),
        )
        sell = _sld_trade(
            exec_id="T-SLD-TSLA",
            ticker="TSLA",
            price=220.0,
            time=datetime(2024, 6, 1, 10, 0, tzinfo=timezone.utc),
        )
        uow = _mock_uow_with_tracking(trades=[bot_old, bot_new, sell])
        svc = TaxService(uow)

        report = svc.sync_lots()

        assert report.created == 2  # Both BOTs create lots
        assert report.closed == 1  # Only oldest closed
        # Verify the OLDEST lot was closed (by checking lot_id pattern)
        update_calls = uow.tax_lots.update.call_args_list
        closed_updates = [call[0][0] for call in update_calls if call[0][0].is_closed]
        assert len(closed_updates) == 1
        assert closed_updates[0].lot_id == "lot-T-BOT-OLD"

    def test_partial_quantity_skipped(self) -> None:
        """SLD with different quantity than open lot is skipped (no partial close)."""
        bot = _bot_trade(exec_id="T-BOT-1", ticker="AAPL", quantity=100.0, price=150.0)
        sell = _sld_trade(exec_id="T-SLD-1", ticker="AAPL", quantity=50.0, price=170.0)
        uow = _mock_uow_with_tracking(trades=[bot, sell])
        svc = TaxService(uow)

        report = svc.sync_lots()

        assert report.created == 1
        assert report.closed == 0  # Partial not handled


# ── AC-218b E2E: Full pipeline test ─────────────────────────────────────


class TestSyncLotsEndToEnd:
    """End-to-end: BOT creates lots + SLD closes lots in single sync_lots call."""

    def test_full_pipeline_bot_and_sld(self) -> None:
        """Mimics real data: 3 buys, 2 sells. One lot stays open."""
        bot_aapl = _bot_trade(
            exec_id="AAPL-BUY",
            ticker="AAPL",
            quantity=100.0,
            price=170.0,
            time=datetime(2025, 1, 15, 10, 0, tzinfo=timezone.utc),
        )
        bot_msft = _bot_trade(
            exec_id="MSFT-BUY",
            ticker="MSFT",
            quantity=75.0,
            price=380.0,
            time=datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc),
        )
        bot_nvda = _bot_trade(
            exec_id="NVDA-BUY",
            ticker="NVDA",
            quantity=40.0,
            price=850.0,
            time=datetime(2025, 3, 1, 10, 0, tzinfo=timezone.utc),
        )
        sld_aapl = _sld_trade(
            exec_id="AAPL-SELL",
            ticker="AAPL",
            quantity=100.0,
            price=195.0,
            time=datetime(2025, 4, 20, 10, 0, tzinfo=timezone.utc),
        )
        sld_msft = _sld_trade(
            exec_id="MSFT-SELL",
            ticker="MSFT",
            quantity=75.0,
            price=420.0,
            time=datetime(2025, 4, 15, 10, 0, tzinfo=timezone.utc),
        )

        uow = _mock_uow_with_tracking(
            trades=[bot_aapl, bot_msft, bot_nvda, sld_aapl, sld_msft]
        )
        svc = TaxService(uow)

        report = svc.sync_lots()

        # 3 BOT → 3 created, 2 SLD → 2 closed, 0 skipped (fresh sync)
        assert report.created == 3
        assert report.closed == 2
        assert report.skipped == 0

        # Verify closed lots have non-zero gains
        update_calls = uow.tax_lots.update.call_args_list
        closed_lots = [call[0][0] for call in update_calls if call[0][0].is_closed]
        assert len(closed_lots) == 2
        for lot in closed_lots:
            assert lot.is_closed is True
            assert lot.close_date is not None
            assert lot.realized_gain_loss != Decimal("0")

    def test_report_has_closed_field(self) -> None:
        """SyncReport includes the new 'closed' field."""
        uow = _mock_uow_with_tracking(trades=[])
        svc = TaxService(uow)

        report = svc.sync_lots()

        assert hasattr(report, "closed")
        assert report.closed == 0
