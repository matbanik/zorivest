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
                notes=command.notes,
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
        search: str | None = None,
    ) -> list[Trade]:
        """List trades with optional filtering, search, and sorting."""
        with self.uow:
            return self.uow.trades.list_filtered(
                limit=limit,
                offset=offset,
                account_id=account_id,
                sort=sort,
                search=search,
            )

    def count_trades(
        self,
        account_id: str | None = None,
        search: str | None = None,
    ) -> int:
        """Return total count of trades matching filters (ignoring pagination)."""
        with self.uow:
            return self.uow.trades.count_filtered(
                account_id=account_id,
                search=search,
            )

    def update_trade(self, exec_id: str, **kwargs: object) -> Trade:
        """Update trade fields by exec_id.

        Raises:
            NotFoundError: If trade does not exist.
            ValueError: If invariants are violated (quantity <= 0, blank instrument).
        """
        with self.uow:
            trade = self.uow.trades.get(exec_id)
            if trade is None:
                raise NotFoundError(f"Trade not found: {exec_id}")
            # Filter kwargs to only fields that Trade accepts.
            valid_fields = {f for f in trade.__dataclass_fields__}
            filtered = {k: v for k, v in kwargs.items() if k in valid_fields}
            # Validate create/update invariant parity
            if "quantity" in filtered and filtered["quantity"] is not None:
                qty = filtered["quantity"]
                if not isinstance(qty, (int, float, str)):
                    msg = f"quantity must be numeric, got {type(qty).__name__}"
                    raise ValueError(msg)
                if float(qty) <= 0:
                    msg = f"quantity must be positive, got {qty}"
                    raise ValueError(msg)
            if "instrument" in filtered and (
                not filtered["instrument"] or not str(filtered["instrument"]).strip()
            ):
                msg = "instrument must not be empty"
                raise ValueError(msg)
            updated = Trade(**{**trade.__dict__, **filtered})
            self.uow.trades.update(updated)
            self.uow.commit()
            return updated

    def delete_trade(self, exec_id: str) -> None:
        """Delete a trade and all linked records (report, images).

        Cleanup order:
        1. Delete report-owned images (polymorphic, no FK cascade)
        2. Delete the linked TradeReport (also cascaded by ORM, but
           explicit delete ensures image cleanup happens first)
        3. Delete trade-owned images (polymorphic, no FK cascade)
        4. Delete the trade itself

        Raises:
            NotFoundError: If trade does not exist.
        """
        with self.uow:
            trade = self.uow.trades.get(exec_id)
            if trade is None:
                raise NotFoundError(f"Trade not found: {exec_id}")

            # Clean up linked report and its images
            report = self.uow.trade_reports.get_for_trade(exec_id)
            if report is not None:
                self.uow.images.delete_for_owner("report", str(report.id))
                self.uow.trade_reports.delete(report.id)

            # Clean up trade-owned images (polymorphic — no FK cascade)
            self.uow.images.delete_for_owner("trade", exec_id)

            # Delete the trade
            self.uow.trades.delete(exec_id)
            self.uow.commit()
