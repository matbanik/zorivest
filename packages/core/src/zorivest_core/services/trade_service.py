"""TradeService — trade lifecycle, deduplication, round-trip matching.

Source: 03-service-layer.md §TradeService
Uses: CreateTrade command (commands.py)
"""

from __future__ import annotations

from zorivest_core.application.commands import CreateTrade
from zorivest_core.application.ports import UnitOfWork
from zorivest_core.domain.entities import Trade
from zorivest_core.domain.exceptions import BusinessRuleError, NotFoundError
from zorivest_core.domain.trades.identity import trade_fingerprint


class TradeService:
    """Trade lifecycle: create, dedup, round-trip matching."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    def create_trade(self, command: CreateTrade) -> Trade:
        """Create a trade with exec_id + fingerprint deduplication.

        Raises:
            BusinessRuleError: If exec_id already exists or fingerprint
                matches within 30-day window.
        """
        with self.uow:
            # Dedup by exec_id
            if self.uow.trades.exists(command.exec_id):
                raise BusinessRuleError(
                    f"Trade with exec_id '{command.exec_id}' already exists"
                )

            trade = Trade(
                exec_id=command.exec_id,
                time=command.time,
                instrument=command.instrument,
                action=command.action,
                quantity=command.quantity,
                price=command.price,
                account_id=command.account_id,
                commission=command.commission,
                realized_pnl=command.realized_pnl,
            )

            # Dedup by fingerprint
            fp = trade_fingerprint(trade)
            if self.uow.trades.exists_by_fingerprint_since(fp, lookback_days=30):
                raise BusinessRuleError(
                    "Trade with matching fingerprint found within 30-day window"
                )

            self.uow.trades.save(trade)
            self.uow.commit()
            return trade

    def get_trade(self, exec_id: str) -> Trade:
        """Retrieve a trade by exec_id.

        Raises:
            NotFoundError: If trade does not exist.
        """
        with self.uow:
            trade = self.uow.trades.get(exec_id)
            if trade is None:
                raise NotFoundError(f"Trade not found: {exec_id}")
            return trade

    def match_round_trips(self, account_id: str) -> list:
        """Group executions via list_for_account and save to round_trips repo.

        Returns:
            List of matched round trips.
        """
        with self.uow:
            trades = self.uow.trades.list_for_account(account_id)

            # Group trades by instrument to find entry/exit pairs
            by_instrument: dict[str, list[Trade]] = {}
            for t in trades:
                by_instrument.setdefault(t.instrument, []).append(t)

            matched = []
            for instrument, instrument_trades in by_instrument.items():
                if len(instrument_trades) >= 2:
                    # Simple round-trip: at least an entry and exit
                    round_trip = {
                        "account_id": account_id,
                        "instrument": instrument,
                        "trades": [t.exec_id for t in instrument_trades],
                    }
                    self.uow.round_trips.save(round_trip)
                    matched.append(round_trip)

            self.uow.commit()
            return matched

    def list_round_trips(
        self,
        account_id: str | None = None,
        status: str = "all",
        ticker: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list:
        """List round-trips with optional filters.

        Canonical API per 04a-api-trades.md §Round-Trip.
        Delegates to match_round_trips for matching logic,
        then applies client-side filters.
        """
        if account_id:
            matched = self.match_round_trips(account_id)
        else:
            matched = []

        # Apply filters
        if ticker:
            matched = [rt for rt in matched if rt.get("instrument") == ticker]
        if status and status != "all":
            matched = [rt for rt in matched if rt.get("status") == status]

        # Pagination
        return matched[offset : offset + limit]

    def list_trades(
        self,
        limit: int = 100,
        offset: int = 0,
        account_id: str | None = None,
        sort: str = "-time",
    ) -> list[Trade]:
        """List trades with optional filtering and sorting."""
        with self.uow:
            return self.uow.trades.list_filtered(
                limit=limit, offset=offset, account_id=account_id, sort=sort,
            )

    def update_trade(self, exec_id: str, **kwargs: object) -> Trade:
        """Update trade fields by exec_id.

        Raises:
            NotFoundError: If trade does not exist.
        """
        with self.uow:
            trade = self.uow.trades.get(exec_id)
            if trade is None:
                raise NotFoundError(f"Trade not found: {exec_id}")
            # Frozen dataclass — create new instance with updated fields
            updated = Trade(**{**trade.__dict__, **kwargs})
            self.uow.trades.update(updated)
            self.uow.commit()
            return updated

    def delete_trade(self, exec_id: str) -> None:
        """Delete a trade by exec_id."""
        with self.uow:
            self.uow.trades.delete(exec_id)
            self.uow.commit()

