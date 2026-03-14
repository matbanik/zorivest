# packages/infrastructure/src/zorivest_infra/broker_adapters/ibkr_flexquery.py
"""IBKR FlexQuery XML adapter — parses Activity Flex reports.

Uses defusedxml for XXE-safe XML parsing (OWASP XXE Prevention).
Implements BrokerFileAdapter protocol from zorivest_core.application.ports.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from xml.etree.ElementTree import Element

import defusedxml.ElementTree as ET

from zorivest_core.domain.enums import (
    AssetClass,
    BrokerType,
    ImportStatus,
    TradeAction,
)
from zorivest_core.domain.import_types import (
    ImportError as ImportErr,
    ImportResult,
    RawExecution,
)

logger = logging.getLogger(__name__)

# IBKR assetCategory → AssetClass mapping
_ASSET_CLASS_MAP: dict[str, AssetClass] = {
    "STK": AssetClass.EQUITY,
    "OPT": AssetClass.OPTION,
    "FUT": AssetClass.FUTURE,
    "CASH": AssetClass.FOREX,
    "BOND": AssetClass.BOND,
    "FUND": AssetClass.MUTUAL_FUND,
    "CRYPTO": AssetClass.CRYPTO,
}

# IBKR buySell → TradeAction mapping
_SIDE_MAP: dict[str, TradeAction] = {
    "BOT": TradeAction.BOT,
    "BUY": TradeAction.BOT,
    "SLD": TradeAction.SLD,
    "SELL": TradeAction.SLD,
}


class IBKRFlexQueryAdapter:
    """IBKR FlexQuery Activity XML parser.

    Satisfies the BrokerFileAdapter protocol. Parses FlexQueryResponse
    XML and converts Trade elements into RawExecution records.
    """

    @property
    def broker_type(self) -> BrokerType:
        return BrokerType.IBKR

    def parse_file(self, file_path: Path) -> ImportResult:
        """Parse a FlexQuery Activity XML file into an ImportResult."""
        try:
            tree = ET.parse(str(file_path))
        except Exception as exc:
            logger.warning("Failed to parse XML from %s: %s", file_path, exc)
            return ImportResult(
                status=ImportStatus.FAILED,
                broker=BrokerType.IBKR,
                errors=[
                    ImportErr(
                        field="xml",
                        message=f"XML parse error: {exc}",
                        raw_line=str(file_path),
                    )
                ],
            )

        root = tree.getroot()
        if root is None:
            return ImportResult(
                status=ImportStatus.FAILED,
                broker=BrokerType.IBKR,
                errors=[
                    ImportErr(field="xml", message="Empty XML document")
                ],
            )
        trade_elements = root.findall(".//Trade")

        if not trade_elements:
            return ImportResult(
                status=ImportStatus.SUCCESS,
                broker=BrokerType.IBKR,
                total_rows=0,
                parsed_rows=0,
            )

        executions: list[RawExecution] = []
        errors: list[ImportErr] = []

        for idx, elem in enumerate(trade_elements):
            try:
                execution = self._parse_trade_element(elem)
                executions.append(execution)
            except Exception as exc:
                raw_attrs = " ".join(f'{k}="{v}"' for k, v in elem.attrib.items())
                errors.append(
                    ImportErr(
                        row_number=idx + 1,
                        field="trade",
                        message=str(exc),
                        raw_line=raw_attrs[:500],
                    )
                )

        total = len(trade_elements)
        parsed = len(executions)

        if parsed == 0:
            status = ImportStatus.FAILED
        elif errors:
            status = ImportStatus.PARTIAL
        else:
            status = ImportStatus.SUCCESS

        return ImportResult(
            status=status,
            broker=BrokerType.IBKR,
            executions=executions,
            errors=errors,
            total_rows=total,
            parsed_rows=parsed,
            skipped_rows=total - parsed,
        )

    def _parse_trade_element(self, elem: Element) -> RawExecution:
        """Map a single XML Trade element to RawExecution."""
        attrib = elem.attrib

        # Required fields — raise on missing/invalid
        symbol_raw = attrib.get("symbol", "")
        if not symbol_raw:
            raise ValueError("Missing required field: symbol")

        asset_category = attrib.get("assetCategory", "")
        asset_class = self._classify_asset_class(asset_category)

        # Normalize symbol
        symbol = self._normalize_symbol(symbol_raw, asset_category)

        # Parse datetime
        dt_str = attrib.get("dateTime", "")
        exec_time = self._parse_ibkr_datetime(dt_str)

        # Parse decimals
        quantity = self._parse_decimal(attrib.get("quantity", "0"), "quantity")
        price = self._parse_decimal(attrib.get("tradePrice", "0"), "tradePrice")

        # Commission is reported as negative by IBKR, we store positive
        raw_commission = self._parse_decimal(attrib.get("ibCommission", "0"), "ibCommission")
        commission = abs(raw_commission)

        # Side mapping
        buy_sell = attrib.get("buySell", "")
        side = _SIDE_MAP.get(buy_sell.upper())
        if side is None:
            raise ValueError(f"Unknown buySell value: {buy_sell!r}")

        # Currency and FX
        currency = attrib.get("currency", "USD")
        fx_rate_str = attrib.get("fxRateToBase", "1")
        fx_rate = self._parse_decimal(fx_rate_str, "fxRateToBase")

        # Base amount: price × abs(quantity) × fx_rate
        abs_qty = abs(quantity)
        base_amount = (price * abs_qty * fx_rate).quantize(Decimal("0.01"))

        # Contract multiplier
        multiplier_str = attrib.get("multiplier", "1")
        contract_multiplier = self._parse_decimal(multiplier_str, "multiplier")

        # Preserve all raw attributes
        raw_data = dict(attrib)

        return RawExecution(
            broker=BrokerType.IBKR,
            account_id=attrib.get("accountId", ""),
            exec_time=exec_time,
            symbol=symbol,
            asset_class=asset_class,
            side=side,
            quantity=abs_qty,
            price=price,
            commission=commission,
            currency=currency,
            base_currency="USD",
            base_amount=base_amount,
            contract_multiplier=contract_multiplier,
            order_id=attrib.get("ibOrderRef"),
            raw_data=raw_data,
        )

    @staticmethod
    def _normalize_symbol(raw: str, asset_class: str) -> str:
        """IBKR symbology → OCC standard for options; passthrough for others."""
        if asset_class != "OPT":
            return raw.strip()

        # IBKR option format: "AAPL  260320C00200000"
        # OCC standard: "AAPL 260320 C 200"
        raw = raw.strip()

        # Find the date portion (6 digits after the underlying)
        # IBKR pads underlying to at least 6 chars with spaces
        parts = raw.split()
        if len(parts) >= 1:
            # Try to parse the concatenated IBKR format
            # Remove all spaces first for uniform parsing
            compact = raw.replace(" ", "")

            # Find where the date starts (first digit sequence of length >= 6)
            i = 0
            while i < len(compact) and compact[i].isalpha():
                i += 1

            if i < len(compact):
                underlying = compact[:i]
                rest = compact[i:]  # e.g., "260320C00200000"

                if len(rest) >= 8:  # date(6) + C/P(1) + strike(1+)
                    date_str = rest[:6]
                    put_call = rest[6]
                    strike_raw = rest[7:]

                    # Convert strike: "00200000" → 200, "00200500" → 200.5
                    try:
                        strike_val = int(strike_raw) / 1000
                        strike = (str(int(strike_val))
                                  if strike_val == int(strike_val)
                                  else str(strike_val))
                    except ValueError:
                        strike = strike_raw

                    return f"{underlying} {date_str} {put_call} {strike}"

        return raw

    @staticmethod
    def _parse_ibkr_datetime(value: str) -> datetime:
        """Parse IBKR's 'YYYYMMDD;HHMMSS' datetime format to UTC."""
        if not value:
            raise ValueError("Missing datetime field")

        # IBKR uses "YYYYMMDD;HHMMSS" format
        value = value.strip()
        try:
            dt = datetime.strptime(value, "%Y%m%d;%H%M%S")
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            # Try alternate formats
            try:
                dt = datetime.strptime(value, "%Y%m%d")
                return dt.replace(tzinfo=timezone.utc)
            except ValueError as exc:
                raise ValueError(f"Cannot parse IBKR datetime: {value!r}") from exc

    @staticmethod
    def _classify_asset_class(code: str) -> AssetClass:
        """Map IBKR assetCategory code to AssetClass enum."""
        result = _ASSET_CLASS_MAP.get(code.upper())
        if result is None:
            raise ValueError(f"Unknown IBKR asset category: {code!r}")
        return result

    @staticmethod
    def _parse_decimal(value: str, field_name: str) -> Decimal:
        """Parse a string to Decimal, raising on invalid."""
        if not value:
            return Decimal("0")
        try:
            return Decimal(value)
        except InvalidOperation as exc:
            raise ValueError(f"Cannot parse {field_name} as Decimal: {value!r}") from exc
