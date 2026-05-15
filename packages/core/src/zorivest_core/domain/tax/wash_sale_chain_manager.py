# packages/core/src/zorivest_core/domain/tax/wash_sale_chain_manager.py
"""Wash sale chain state machine.

MEU-131 AC-131.1 through AC-131.7.
Manages lifecycle: DISALLOWED → ABSORBED → RELEASED (or DESTROYED).

Reference: IRS Publication 550 — wash sale rule.
"""

from __future__ import annotations

import uuid
from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal

from zorivest_core.domain.entities import TaxLot
from zorivest_core.domain.enums import WashSaleEventType, WashSaleStatus
from zorivest_core.domain.tax.wash_sale import WashSaleChain, WashSaleEntry


class WashSaleChainManager:
    """State machine managing wash sale chain lifecycle.

    AC-131.1: Four methods — start_chain, absorb_loss, release_chain, continue_chain.
    AC-131.7: get_trapped_losses query.
    """

    def start_chain(
        self,
        loss_lot: TaxLot,
        disallowed_amount: Decimal,
    ) -> WashSaleChain:
        """AC-131.2: Create a new chain with DISALLOWED status and LOSS_DISALLOWED entry.

        Args:
            loss_lot: The closed lot that realized the loss.
            disallowed_amount: Total dollar amount disallowed.

        Returns:
            New WashSaleChain in DISALLOWED state.
        """
        chain_id = str(uuid.uuid4())
        loss_close = loss_lot.close_date or datetime.now(tz=timezone.utc)
        entry = WashSaleEntry(
            entry_id=str(uuid.uuid4()),
            chain_id=chain_id,
            event_type=WashSaleEventType.LOSS_DISALLOWED,
            lot_id=loss_lot.lot_id,
            amount=disallowed_amount,
            event_date=loss_close,
            account_id=loss_lot.account_id,
        )
        return WashSaleChain(
            chain_id=chain_id,
            ticker=loss_lot.ticker,
            loss_lot_id=loss_lot.lot_id,
            loss_date=loss_close,
            loss_amount=loss_lot.cost_basis - loss_lot.proceeds,
            disallowed_amount=disallowed_amount,
            status=WashSaleStatus.DISALLOWED,
            loss_open_date=loss_lot.open_date,  # Store for holding period tacking
            entries=[entry],
        )

    def absorb_loss(
        self,
        chain: WashSaleChain,
        replacement_lot: TaxLot,
        *,
        amount: Decimal | None = None,
    ) -> TaxLot:
        """AC-131.3 + AC-131.4: Absorb disallowed loss into replacement lot.

        - Adds the per-match disallowed amount to replacement lot's wash_sale_adjustment.
        - Tacks holding period: replacement gets original lot's open_date (IRS Pub 550).
        - Sets chain status to ABSORBED.
        - Adds BASIS_ADJUSTED entry.

        Args:
            chain: The chain to absorb into.
            replacement_lot: The replacement purchase lot.
            amount: Per-match disallowed amount. If None, falls back to
                chain.disallowed_amount (single-replacement case).

        Returns:
            Updated replacement TaxLot with adjusted basis and tacked holding period.

        Raises:
            ValueError: If chain is DESTROYED or RELEASED.
        """
        if chain.status in (WashSaleStatus.DESTROYED, WashSaleStatus.RELEASED):
            raise ValueError(
                f"Cannot absorb into chain {chain.chain_id}: chain is {chain.status}"
            )

        adjustment = amount if amount is not None else chain.disallowed_amount

        # AC-131.3: Adjust replacement lot's wash_sale_adjustment
        new_adjustment = replacement_lot.wash_sale_adjustment + adjustment

        # AC-131.4: Tack holding period — replacement inherits original lot's open_date
        tacked_open_date = chain.loss_open_date or replacement_lot.open_date

        updated_lot = replace(
            replacement_lot,
            wash_sale_adjustment=new_adjustment,
            open_date=tacked_open_date,
        )

        # Add BASIS_ADJUSTED entry
        entry = WashSaleEntry(
            entry_id=str(uuid.uuid4()),
            chain_id=chain.chain_id,
            event_type=WashSaleEventType.BASIS_ADJUSTED,
            lot_id=replacement_lot.lot_id,
            amount=adjustment,
            event_date=datetime.now(tz=timezone.utc),
            account_id=replacement_lot.account_id,
        )
        chain.entries.append(entry)
        chain.status = WashSaleStatus.ABSORBED

        return updated_lot

    def release_chain(
        self,
        chain: WashSaleChain,
        replacement_lot_id: str,
        *,
        account_id: str = "",
    ) -> None:
        """AC-131.5: Release chain — loss becomes deductible.

        Can only release a chain in ABSORBED status.

        Args:
            chain: The chain to release.
            replacement_lot_id: The lot ID of the replacement that was sold.
            account_id: Account that triggered the release event.

        Raises:
            ValueError: If chain is not in ABSORBED status.
        """
        if chain.status != WashSaleStatus.ABSORBED:
            raise ValueError(
                f"Cannot release chain {chain.chain_id}: "
                f"expected ABSORBED, got {chain.status}"
            )

        entry = WashSaleEntry(
            entry_id=str(uuid.uuid4()),
            chain_id=chain.chain_id,
            event_type=WashSaleEventType.LOSS_RELEASED,
            lot_id=replacement_lot_id,
            amount=chain.disallowed_amount,
            event_date=datetime.now(tz=timezone.utc),
            account_id=account_id,
        )
        chain.entries.append(entry)
        chain.status = WashSaleStatus.RELEASED

    def continue_chain(
        self,
        chain: WashSaleChain,
        new_replacement_lot: TaxLot,
    ) -> None:
        """AC-131.6: Extend chain when replacement lot triggers another wash sale.

        Adds CHAIN_CONTINUED entry and resets status to DISALLOWED.
        """
        entry = WashSaleEntry(
            entry_id=str(uuid.uuid4()),
            chain_id=chain.chain_id,
            event_type=WashSaleEventType.CHAIN_CONTINUED,
            lot_id=new_replacement_lot.lot_id,
            amount=chain.disallowed_amount,
            event_date=datetime.now(tz=timezone.utc),
            account_id=new_replacement_lot.account_id,
        )
        chain.entries.append(entry)
        chain.status = WashSaleStatus.DISALLOWED

    def destroy_chain(
        self,
        chain: WashSaleChain,
        lot_id: str,
        account_id: str,
    ) -> None:
        """MEU-132 AC-132.4: Permanently destroy a chain (IRA loss).

        Sets status to DESTROYED with LOSS_DESTROYED entry.
        Does NOT adjust replacement lot basis — the loss is gone.

        Raises:
            ValueError: If chain is already RELEASED or DESTROYED.
        """
        if chain.status in (WashSaleStatus.RELEASED, WashSaleStatus.DESTROYED):
            raise ValueError(
                f"Cannot destroy chain {chain.chain_id}: already {chain.status}"
            )

        entry = WashSaleEntry(
            entry_id=str(uuid.uuid4()),
            chain_id=chain.chain_id,
            event_type=WashSaleEventType.LOSS_DESTROYED,
            lot_id=lot_id,
            amount=chain.disallowed_amount,
            event_date=datetime.now(tz=timezone.utc),
            account_id=account_id,
        )
        chain.entries.append(entry)
        chain.status = WashSaleStatus.DESTROYED

    def get_trapped_losses(
        self,
        chains: list[WashSaleChain],
    ) -> list[WashSaleChain]:
        """AC-131.7: Return chains in ABSORBED status (trapped, non-deductible losses)."""
        return [c for c in chains if c.status == WashSaleStatus.ABSORBED]
