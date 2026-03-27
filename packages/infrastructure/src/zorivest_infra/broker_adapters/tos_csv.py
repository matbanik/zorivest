# packages/infrastructure/src/zorivest_infra/broker_adapters/tos_csv.py
"""ThinkorSwim CSV parser — handles multi-section TOS export format.

Detects Trade History section, parses stock and options trades,
normalizes TOS option symbols to OCC standard format.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from decimal import Decimal

from zorivest_core.domain.enums import AssetClass, BrokerType, TradeAction
from zorivest_core.domain.import_types import RawExecution
from zorivest_infra.broker_adapters.csv_base import CSVParserBase

# TOS header fingerprint
_TOS_REQUIRED_HEADERS = {"Exec Time", "Spread", "Side", "Qty"}


class ThinkorSwimCSVParser(CSVParserBase):
    """ThinkorSwim CSV export parser.

    Handles multi-section CSV format where the "Trade History" section
    contains the actual trade data.
    """

    @property
    def broker_type(self) -> BrokerType:
        return BrokerType.THINKORSWIM

    def detect(self, headers: list[str]) -> bool:
        """Check if headers match TOS fingerprint."""
        header_set = set(headers)
        return _TOS_REQUIRED_HEADERS.issubset(header_set)

    def _extract_data_lines(self, content: str) -> list[str]:
        """Extract Trade History section from multi-section TOS CSV."""
        lines = content.splitlines()

        # Find "Trade History" section
        trade_section_start = None
        for i, line in enumerate(lines):
            if "Trade History" in line:
                trade_section_start = i + 1  # Header row is next
                break

        if trade_section_start is None:
            # No multi-section format — try treating entire file as trades
            return [line for line in lines if line.strip()]

        # Collect lines until next section or end
        data_lines: list[str] = []
        for i in range(trade_section_start, len(lines)):
            line = lines[i].strip()
            if not line:
                continue
            # Stop at next section (non-CSV line without commas,
            # or a section header like "Cash Balance")
            if i > trade_section_start and "," not in line:
                break
            data_lines.append(lines[i])

        return data_lines

    def parse_rows(self, rows: list[dict[str, str]]) -> list[RawExecution]:
        """Parse TOS CSV rows into RawExecution records."""
        executions: list[RawExecution] = []

        for row in rows:
            exec_time_str = row.get("Exec Time", "").strip()
            if not exec_time_str:
                continue

            # Parse datetime: "01/15/2026 09:30:15"
            try:
                dt = datetime.strptime(exec_time_str, "%m/%d/%Y %H:%M:%S")
                exec_time = dt.replace(tzinfo=timezone.utc)
            except ValueError:
                continue

            # Side
            side_str = row.get("Side", "").strip().upper()
            if side_str == "BUY":
                side = TradeAction.BOT
            elif side_str == "SELL":
                side = TradeAction.SLD
            else:
                continue

            # Quantity (TOS uses negative for sells sometimes)
            qty_str = row.get("Qty", "0").strip().replace(",", "")
            try:
                quantity = abs(Decimal(qty_str))
            except Exception:
                continue

            # Symbol and asset class
            symbol_raw = row.get("Symbol", "").strip()
            spread = row.get("Spread", "").strip().upper()

            if spread == "STOCK":
                asset_class = AssetClass.EQUITY
                symbol = symbol_raw
            elif symbol_raw.startswith("."):
                asset_class = AssetClass.OPTION
                symbol = self._normalize_tos_option(symbol_raw)
            else:
                asset_class = AssetClass.EQUITY
                symbol = symbol_raw

            # Price
            price_str = row.get("Price", "0").strip().replace(",", "")
            try:
                price = Decimal(price_str)
            except Exception:
                price = Decimal("0")

            # Net Price for commission calc
            net_price_str = row.get("Net Price", "0").strip().replace(",", "")
            try:
                net_price = Decimal(net_price_str)
                commission = abs(price - net_price) * quantity
            except Exception:
                commission = Decimal("0")

            # Multiplier
            multiplier = (
                Decimal("100") if asset_class == AssetClass.OPTION else Decimal("1")
            )

            executions.append(
                RawExecution(
                    broker=BrokerType.THINKORSWIM,
                    account_id="",
                    exec_time=exec_time,
                    symbol=symbol,
                    asset_class=asset_class,
                    side=side,
                    quantity=quantity,
                    price=price,
                    commission=commission,
                    currency="USD",
                    base_currency="USD",
                    contract_multiplier=multiplier,
                    raw_data=dict(row),
                )
            )

        return executions

    @staticmethod
    def _normalize_tos_option(raw: str) -> str:
        """Normalize TOS option symbol to OCC format.

        TOS format: ".AAPL260320C200" or ".AAPL260116C225"
        OCC format: "AAPL 260320 C 200"
        """
        if raw.startswith("."):
            raw = raw[1:]

        # Match: underlying + date(6) + C/P + strike
        match = re.match(r"^([A-Z]+)(\d{6})([CP])(\d+)$", raw)
        if match:
            underlying, date_str, put_call, strike = match.groups()
            return f"{underlying} {date_str} {put_call} {strike}"

        return raw
