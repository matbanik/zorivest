# packages/infrastructure/src/zorivest_infra/broker_adapters/ninjatrader_csv.py
"""NinjaTrader CSV parser — handles pre-paired round-trip format.

NinjaTrader exports trades as completed round-trips (entry+exit already
matched), with built-in MFE/MAE and Strategy columns.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from zorivest_core.domain.enums import AssetClass, BrokerType, TradeAction
from zorivest_core.domain.import_types import RawExecution
from zorivest_infra.broker_adapters.csv_base import CSVParserBase

# NinjaTrader header fingerprint
_NT_REQUIRED_HEADERS = {"Trade-#", "Instrument", "Account", "Strategy"}


class NinjaTraderCSVParser(CSVParserBase):
    """NinjaTrader CSV export parser.

    Parses pre-paired round-trip format with MFE/MAE preservation
    in raw_data for future enrichment.
    """

    @property
    def broker_type(self) -> BrokerType:
        return BrokerType.NINJATRADER

    def detect(self, headers: list[str]) -> bool:
        """Check if headers match NinjaTrader fingerprint."""
        header_set = set(headers)
        return _NT_REQUIRED_HEADERS.issubset(header_set)

    def parse_rows(self, rows: list[dict[str, str]]) -> list[RawExecution]:
        """Parse NinjaTrader CSV rows into RawExecution records."""
        executions: list[RawExecution] = []

        for row in rows:
            instrument = row.get("Instrument", "").strip()
            if not instrument:
                continue

            # Market position → side
            market_pos = row.get("Market pos.", "").strip().upper()
            if market_pos == "LONG":
                side = TradeAction.BOT
            elif market_pos == "SHORT":
                side = TradeAction.SLD
            else:
                continue

            # Quantity
            qty_str = row.get("Quantity", "0").strip().replace(",", "")
            try:
                quantity = abs(Decimal(qty_str))
            except Exception:
                continue

            # Entry price
            entry_price_str = row.get("Entry price", "0").strip().replace(",", "")
            try:
                entry_price = Decimal(entry_price_str)
            except Exception:
                continue

            # Entry time
            entry_time_str = row.get("Entry time", "").strip()
            try:
                dt = datetime.strptime(entry_time_str, "%m/%d/%Y %I:%M:%S %p")
                exec_time = dt.replace(tzinfo=timezone.utc)
            except ValueError:
                continue

            # Commission
            commission_str = row.get("Commission", "0").strip().replace(",", "")
            try:
                commission = abs(Decimal(commission_str))
            except Exception:
                commission = Decimal("0")

            # Determine asset class from instrument
            # NinjaTrader instruments: "ES 03-26", "NQ 03-26" → futures
            asset_class = AssetClass.FUTURE  # Default for NinjaTrader

            # Symbol normalization: "ES 03-26" → "ES"
            symbol = instrument.split()[0] if " " in instrument else instrument

            # Preserve MFE/MAE and strategy in raw_data
            raw_data = dict(row)

            executions.append(
                RawExecution(
                    broker=BrokerType.NINJATRADER,
                    account_id=row.get("Account", ""),
                    exec_time=exec_time,
                    symbol=symbol,
                    asset_class=asset_class,
                    side=side,
                    quantity=quantity,
                    price=entry_price,
                    commission=commission,
                    currency="USD",
                    base_currency="USD",
                    contract_multiplier=Decimal("1"),
                    raw_data=raw_data,
                )
            )

        return executions
