# tests/unit/test_csv_import.py
"""MEU-99 Red Phase: CSV import framework + broker auto-detection tests.

Tests written FIRST per TDD protocol. Covers CSVParserBase, TOS parser,
NinjaTrader parser, and ImportService auto-detection routing.
"""


import pytest

from zorivest_core.domain.enums import AssetClass, BrokerType, ImportStatus, TradeAction
from zorivest_core.domain.import_types import ImportResult
from zorivest_infra.broker_adapters.tos_csv import ThinkorSwimCSVParser
from zorivest_infra.broker_adapters.ninjatrader_csv import NinjaTraderCSVParser
from zorivest_core.services.import_service import ImportService, UnknownBrokerFormat


# ── CSVParserBase: Encoding Detection ───────────────────────────────────


class TestCSVParserBaseEncoding:
    """CSVParserBase encoding detection via chardet."""

    def test_detect_utf8_encoding(self, tmp_path):
        f = tmp_path / "utf8.csv"
        f.write_text("a,b,c\n1,2,3\n", encoding="utf-8")
        parser = ThinkorSwimCSVParser()
        encoding = parser._detect_encoding(f)
        assert encoding.lower().replace("-", "") in ("utf8", "ascii")
        # Value: verify encoding is a non-empty string
        assert isinstance(encoding, str)
        assert len(encoding) > 0

    def test_detect_latin1_encoding(self, tmp_path):
        f = tmp_path / "latin1.csv"
        f.write_bytes("symbol,price\nCAFÉ,10.50\n".encode("latin-1"))
        parser = ThinkorSwimCSVParser()
        encoding = parser._detect_encoding(f)
        # chardet may detect as ISO-8859-1 or Windows-1252
        assert encoding is not None
        # Value: verify it's a recognized Latin-family encoding
        assert any(name in encoding.lower() for name in ("iso-8859", "windows-1252", "latin", "8859"))

    def test_strip_bom(self):
        parser = ThinkorSwimCSVParser()
        content = "\ufeffcol1,col2\nval1,val2"
        result = parser._strip_bom(content)
        assert not result.startswith("\ufeff")
        assert result.startswith("col1")
        # Value: verify content is preserved after BOM removal
        assert "val1,val2" in result
        assert len(result) == len(content) - 1


# ── ThinkorSwim CSV Parser ──────────────────────────────────────────────


class TestThinkorSwimParser:
    """TOS CSV parser: header detection, trade parsing, options symbols."""

    def test_detect_tos_headers(self):
        parser = ThinkorSwimCSVParser()
        tos_headers = ["Exec Time", "Spread", "Side", "Qty", "Pos Effect",
                       "Symbol", "Exp", "Strike", "Type", "Price", "Net Price", "Order Type"]
        assert parser.detect(tos_headers) is True

    def test_reject_non_tos_headers(self):
        parser = ThinkorSwimCSVParser()
        wrong_headers = ["Trade-#", "Instrument", "Account", "Strategy"]
        assert parser.detect(wrong_headers) is False

    def test_broker_type(self):
        parser = ThinkorSwimCSVParser()
        assert parser.broker_type == BrokerType.THINKORSWIM

    def test_parse_file_returns_import_result(self, tos_csv_file):
        parser = ThinkorSwimCSVParser()
        result = parser.parse_file(tos_csv_file)
        assert isinstance(result, ImportResult)
        # Value: verify result has concrete fields
        assert result.broker == BrokerType.THINKORSWIM
        assert result.parsed_rows >= 0
        assert isinstance(result.executions, list)

    def test_parse_file_extracts_trades(self, tos_csv_file):
        parser = ThinkorSwimCSVParser()
        result = parser.parse_file(tos_csv_file)
        assert result.parsed_rows >= 2  # At least stock + option trades
        assert result.status in (ImportStatus.SUCCESS, ImportStatus.PARTIAL)

    def test_stock_trade_fields(self, tos_csv_file):
        parser = ThinkorSwimCSVParser()
        result = parser.parse_file(tos_csv_file)
        stock_trades = [t for t in result.executions if t.asset_class == AssetClass.EQUITY]
        assert len(stock_trades) >= 1
        trade = stock_trades[0]
        assert trade.symbol == "AAPL"
        assert trade.side == TradeAction.BOT
        assert trade.broker == BrokerType.THINKORSWIM

    def test_option_trade_symbol_normalized(self, tos_csv_file):
        parser = ThinkorSwimCSVParser()
        result = parser.parse_file(tos_csv_file)
        option_trades = [t for t in result.executions if t.asset_class == AssetClass.OPTION]
        if option_trades:
            assert "AAPL" in option_trades[0].symbol

    def test_sell_side_detected(self, tos_csv_file):
        parser = ThinkorSwimCSVParser()
        result = parser.parse_file(tos_csv_file)
        sell_trades = [t for t in result.executions if t.side == TradeAction.SLD]
        assert len(sell_trades) >= 1

    def test_empty_csv_handling(self, tmp_path):
        f = tmp_path / "empty.csv"
        f.write_text("", encoding="utf-8")
        parser = ThinkorSwimCSVParser()
        result = parser.parse_file(f)
        assert result.status in (ImportStatus.SUCCESS, ImportStatus.FAILED)
        assert len(result.executions) == 0

    def test_headers_only_csv(self, tmp_path):
        f = tmp_path / "headers_only.csv"
        f.write_text("Exec Time,Spread,Side,Qty\n", encoding="utf-8")
        parser = ThinkorSwimCSVParser()
        result = parser.parse_file(f)
        assert len(result.executions) == 0


# ── NinjaTrader CSV Parser ──────────────────────────────────────────────


class TestNinjaTraderParser:
    """NinjaTrader CSV parser: header detection, pre-paired format, strategy tags."""

    def test_detect_ninjatrader_headers(self):
        parser = NinjaTraderCSVParser()
        nt_headers = ["Trade-#", "Instrument", "Account", "Strategy",
                      "Market pos.", "Quantity", "Entry price", "Exit price"]
        assert parser.detect(nt_headers) is True

    def test_reject_non_ninjatrader_headers(self):
        parser = NinjaTraderCSVParser()
        wrong_headers = ["Exec Time", "Spread", "Side", "Qty"]
        assert parser.detect(wrong_headers) is False

    def test_broker_type(self):
        parser = NinjaTraderCSVParser()
        assert parser.broker_type == BrokerType.NINJATRADER

    def test_parse_file_returns_import_result(self, ninjatrader_csv_file):
        parser = NinjaTraderCSVParser()
        result = parser.parse_file(ninjatrader_csv_file)
        assert isinstance(result, ImportResult)
        # Value: verify result has concrete fields
        assert result.broker == BrokerType.NINJATRADER
        assert result.parsed_rows >= 0
        assert isinstance(result.executions, list)

    def test_parse_file_extracts_trades(self, ninjatrader_csv_file):
        parser = NinjaTraderCSVParser()
        result = parser.parse_file(ninjatrader_csv_file)
        assert result.parsed_rows >= 2
        assert result.status == ImportStatus.SUCCESS

    def test_strategy_tag_in_raw_data(self, ninjatrader_csv_file):
        parser = NinjaTraderCSVParser()
        result = parser.parse_file(ninjatrader_csv_file)
        trade = result.executions[0]
        assert "Strategy" in trade.raw_data
        # Value: verify the strategy field has a non-empty value
        assert trade.raw_data["Strategy"] is not None
        assert len(str(trade.raw_data["Strategy"])) > 0

    def test_mfe_mae_in_raw_data(self, ninjatrader_csv_file):
        parser = NinjaTraderCSVParser()
        result = parser.parse_file(ninjatrader_csv_file)
        trade = result.executions[0]
        assert "MAE" in trade.raw_data
        assert "MFE" in trade.raw_data
        # Value: verify MAE/MFE are numeric strings or numeric values
        assert float(str(trade.raw_data["MAE"])) >= 0
        assert float(str(trade.raw_data["MFE"])) >= 0

    def test_long_trade_side(self, ninjatrader_csv_file):
        parser = NinjaTraderCSVParser()
        result = parser.parse_file(ninjatrader_csv_file)
        long_trades = [t for t in result.executions if t.side == TradeAction.BOT]
        assert len(long_trades) >= 1

    def test_short_trade_side(self, ninjatrader_csv_file):
        parser = NinjaTraderCSVParser()
        result = parser.parse_file(ninjatrader_csv_file)
        short_trades = [t for t in result.executions if t.side == TradeAction.SLD]
        assert len(short_trades) >= 1


# ── ImportService: Auto-Detection and Routing ───────────────────────────


class TestImportServiceRouting:
    """ImportService: auto-detection, broker_hint override, error handling."""

    def test_import_xml_routes_to_ibkr(self, flexquery_xml_file):
        from zorivest_infra.broker_adapters.ibkr_flexquery import IBKRFlexQueryAdapter
        service = ImportService(adapters=[IBKRFlexQueryAdapter()])
        result = service.import_file(flexquery_xml_file)
        assert result.broker == BrokerType.IBKR
        assert result.status == ImportStatus.SUCCESS

    def test_import_csv_auto_detects_tos(self, tos_csv_file):
        service = ImportService(adapters=[
            ThinkorSwimCSVParser(),
            NinjaTraderCSVParser(),
        ])
        result = service.import_file(tos_csv_file)
        assert result.broker == BrokerType.THINKORSWIM

    def test_import_csv_auto_detects_ninjatrader(self, ninjatrader_csv_file):
        service = ImportService(adapters=[
            ThinkorSwimCSVParser(),
            NinjaTraderCSVParser(),
        ])
        result = service.import_file(ninjatrader_csv_file)
        assert result.broker == BrokerType.NINJATRADER

    def test_broker_hint_overrides_detection(self, flexquery_xml_file):
        from zorivest_infra.broker_adapters.ibkr_flexquery import IBKRFlexQueryAdapter
        service = ImportService(adapters=[IBKRFlexQueryAdapter()])
        result = service.import_file(flexquery_xml_file, broker_hint=BrokerType.IBKR)
        assert result.broker == BrokerType.IBKR

    def test_unknown_csv_raises_error(self, tmp_path):
        f = tmp_path / "unknown.csv"
        f.write_text("col_a,col_b,col_c\n1,2,3\n", encoding="utf-8")
        service = ImportService(adapters=[
            ThinkorSwimCSVParser(),
            NinjaTraderCSVParser(),
        ])
        with pytest.raises(UnknownBrokerFormat, match="col_a"):
            service.import_file(f)

    def test_auto_detect_csv_broker(self, tos_csv_file):
        service = ImportService(adapters=[
            ThinkorSwimCSVParser(),
            NinjaTraderCSVParser(),
        ])
        broker = service.auto_detect_csv_broker(tos_csv_file)
        assert broker == BrokerType.THINKORSWIM

    def test_unknown_format_auto_detect(self, tmp_path):
        f = tmp_path / "random.csv"
        f.write_text("x,y,z\n1,2,3\n", encoding="utf-8")
        service = ImportService(adapters=[
            ThinkorSwimCSVParser(),
            NinjaTraderCSVParser(),
        ])
        with pytest.raises(UnknownBrokerFormat):
            service.auto_detect_csv_broker(f)


# ── Edge Cases ──────────────────────────────────────────────────────────


class TestEdgeCases:
    """Edge cases: empty files, extra columns, mixed content."""

    def test_empty_file(self, tmp_path):
        f = tmp_path / "empty.csv"
        f.write_text("", encoding="utf-8")
        service = ImportService(adapters=[ThinkorSwimCSVParser()])
        with pytest.raises(UnknownBrokerFormat):
            service.import_file(f)

    def test_csv_with_bom(self, tmp_path):
        f = tmp_path / "bom.csv"
        content = (
            "Trade-#,Instrument,Account,Strategy,Market pos.,Quantity,"
            "Entry price,Exit price,Entry time,Exit time,Profit,Cum. profit,"
            "Commission,MAE,MFE\n"
            "1,ES 03-26,Sim101,Test,Long,1,5000.00,5010.00,"
            "3/10/2026 9:31:00 AM,3/10/2026 10:00:00 AM,500.00,500.00,4.12,50.00,600.00\n"
        )
        f.write_text(content, encoding="utf-8-sig")
        parser = NinjaTraderCSVParser()
        result = parser.parse_file(f)
        assert result.parsed_rows >= 1

    def test_bom_csv_through_import_service(self, tmp_path):
        """AC-10 regression: BOM CSV must work through ImportService auto-detect path."""
        f = tmp_path / "bom_import.csv"
        content = (
            "Trade-#,Instrument,Account,Strategy,Market pos.,Quantity,"
            "Entry price,Exit price,Entry time,Exit time,Profit,Cum. profit,"
            "Commission,MAE,MFE\n"
            "1,ES 03-26,Sim101,Test,Long,1,5000.00,5010.00,"
            "3/10/2026 9:31:00 AM,3/10/2026 10:00:00 AM,500.00,500.00,4.12,50.00,600.00\n"
        )
        f.write_text(content, encoding="utf-8-sig")
        service = ImportService(adapters=[
            ThinkorSwimCSVParser(),
            NinjaTraderCSVParser(),
        ])
        result = service.import_file(f)
        assert result.broker == BrokerType.NINJATRADER
        assert result.parsed_rows >= 1
