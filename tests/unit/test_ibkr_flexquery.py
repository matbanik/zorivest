# tests/unit/test_ibkr_flexquery.py
"""MEU-96 Red Phase: IBKR FlexQuery adapter tests.

Tests written FIRST per TDD protocol. All tests should FAIL until
the IBKRFlexQueryAdapter is implemented (Green phase).
"""

from datetime import datetime, timezone
from decimal import Decimal


from zorivest_core.domain.enums import AssetClass, BrokerType, ImportStatus, TradeAction
from zorivest_core.domain.import_types import ImportResult

# Import will fail during Red phase — that's expected
from zorivest_infra.broker_adapters.ibkr_flexquery import IBKRFlexQueryAdapter


# ── AC-1: parse_file returns ImportResult with RawExecution list ─────────


class TestParseFileBasic:
    """FIC-96 AC-1: parse_file() returns ImportResult with extracted trades."""

    def test_parse_valid_flexquery_returns_import_result(self, flexquery_xml_file):
        adapter = IBKRFlexQueryAdapter()
        result = adapter.parse_file(flexquery_xml_file)
        assert isinstance(result, ImportResult)

    def test_parse_valid_flexquery_has_correct_trade_count(self, flexquery_xml_file):
        adapter = IBKRFlexQueryAdapter()
        result = adapter.parse_file(flexquery_xml_file)
        assert len(result.executions) == 3
        assert result.parsed_rows == 3
        assert result.total_rows == 3

    def test_parse_valid_flexquery_status_success(self, flexquery_xml_file):
        adapter = IBKRFlexQueryAdapter()
        result = adapter.parse_file(flexquery_xml_file)
        assert result.status == ImportStatus.SUCCESS

    def test_parse_valid_flexquery_broker_is_ibkr(self, flexquery_xml_file):
        adapter = IBKRFlexQueryAdapter()
        result = adapter.parse_file(flexquery_xml_file)
        assert result.broker == BrokerType.IBKR


# ── AC-2: RawExecution fields ───────────────────────────────────────────


class TestRawExecutionFields:
    """FIC-96 AC-2: broker, UTC exec_time, Decimal fields."""

    def test_stock_trade_broker_type(self, flexquery_xml_file):
        adapter = IBKRFlexQueryAdapter()
        result = adapter.parse_file(flexquery_xml_file)
        trade = result.executions[0]
        assert trade.broker == BrokerType.IBKR

    def test_stock_trade_account_id(self, flexquery_xml_file):
        adapter = IBKRFlexQueryAdapter()
        result = adapter.parse_file(flexquery_xml_file)
        trade = result.executions[0]
        assert trade.account_id == "U1234567"

    def test_stock_trade_exec_time_utc(self, flexquery_xml_file):
        adapter = IBKRFlexQueryAdapter()
        result = adapter.parse_file(flexquery_xml_file)
        trade = result.executions[0]
        expected = datetime(2026, 1, 15, 9, 30, 15, tzinfo=timezone.utc)
        assert trade.exec_time == expected

    def test_stock_trade_decimal_price(self, flexquery_xml_file):
        adapter = IBKRFlexQueryAdapter()
        result = adapter.parse_file(flexquery_xml_file)
        trade = result.executions[0]
        assert trade.price == Decimal("185.50")
        assert isinstance(trade.price, Decimal)

    def test_stock_trade_decimal_quantity(self, flexquery_xml_file):
        adapter = IBKRFlexQueryAdapter()
        result = adapter.parse_file(flexquery_xml_file)
        trade = result.executions[0]
        assert trade.quantity == Decimal("100")

    def test_stock_trade_decimal_commission(self, flexquery_xml_file):
        adapter = IBKRFlexQueryAdapter()
        result = adapter.parse_file(flexquery_xml_file)
        trade = result.executions[0]
        # IBKR reports commission as negative; we store positive
        assert trade.commission == Decimal("1.00")

    def test_buy_side(self, flexquery_xml_file):
        adapter = IBKRFlexQueryAdapter()
        result = adapter.parse_file(flexquery_xml_file)
        trade = result.executions[0]  # BOT
        assert trade.side == TradeAction.BOT

    def test_sell_side(self, flexquery_xml_file):
        adapter = IBKRFlexQueryAdapter()
        result = adapter.parse_file(flexquery_xml_file)
        trade = result.executions[1]  # SLD
        assert trade.side == TradeAction.SLD


# ── AC-3: Symbol normalization (options → OCC) ──────────────────────────


class TestSymbolNormalization:
    """FIC-96 AC-3: IBKR options → OCC standard format."""

    def test_stock_symbol_passthrough(self, flexquery_xml_file):
        adapter = IBKRFlexQueryAdapter()
        result = adapter.parse_file(flexquery_xml_file)
        assert result.executions[0].symbol == "AAPL"

    def test_option_symbol_to_occ(self, flexquery_xml_file):
        adapter = IBKRFlexQueryAdapter()
        result = adapter.parse_file(flexquery_xml_file)
        option_trade = result.executions[2]
        # IBKR "AAPL  260320C00200000" → OCC "AAPL 260320 C 200"
        assert option_trade.symbol == "AAPL 260320 C 200"

    def test_fractional_strike_preserved(self):
        """Regression: fractional strikes must not be truncated by integer division."""
        result = IBKRFlexQueryAdapter._normalize_symbol(
            "AAPL  260320C00200500", "OPT"
        )
        assert result == "AAPL 260320 C 200.5"


# ── AC-4: Asset class classification ────────────────────────────────────


class TestAssetClassification:
    """FIC-96 AC-4: IBKR assetCategory → AssetClass enum."""

    def test_stk_maps_to_equity(self, flexquery_xml_file):
        adapter = IBKRFlexQueryAdapter()
        result = adapter.parse_file(flexquery_xml_file)
        assert result.executions[0].asset_class == AssetClass.EQUITY

    def test_opt_maps_to_option(self, flexquery_xml_file):
        adapter = IBKRFlexQueryAdapter()
        result = adapter.parse_file(flexquery_xml_file)
        assert result.executions[2].asset_class == AssetClass.OPTION

    def test_fut_maps_to_future(self, flexquery_future_xml_file):
        adapter = IBKRFlexQueryAdapter()
        result = adapter.parse_file(flexquery_future_xml_file)
        assert result.executions[0].asset_class == AssetClass.FUTURE

    def test_cash_maps_to_forex(self, flexquery_forex_xml_file):
        adapter = IBKRFlexQueryAdapter()
        result = adapter.parse_file(flexquery_forex_xml_file)
        assert result.executions[0].asset_class == AssetClass.FOREX


# ── AC-5: Error handling — partial-success (ADR-0003) ───────────────────


class TestErrorHandling:
    """FIC-96 AC-5: malformed rows produce ImportErrors, not exceptions."""

    def test_malformed_row_produces_import_error(self, flexquery_malformed_xml_file):
        adapter = IBKRFlexQueryAdapter()
        result = adapter.parse_file(flexquery_malformed_xml_file)
        assert len(result.errors) > 0

    def test_malformed_row_status_partial(self, flexquery_malformed_xml_file):
        adapter = IBKRFlexQueryAdapter()
        result = adapter.parse_file(flexquery_malformed_xml_file)
        assert result.status == ImportStatus.PARTIAL

    def test_malformed_row_valid_trades_still_parsed(self, flexquery_malformed_xml_file):
        adapter = IBKRFlexQueryAdapter()
        result = adapter.parse_file(flexquery_malformed_xml_file)
        # One valid AAPL trade + one malformed → 1 parsed
        assert result.parsed_rows == 1
        assert len(result.executions) == 1

    def test_completely_malformed_xml_returns_failed(self, malformed_xml_file):
        adapter = IBKRFlexQueryAdapter()
        result = adapter.parse_file(malformed_xml_file)
        assert result.status == ImportStatus.FAILED
        assert len(result.executions) == 0

    def test_empty_trades_section(self, flexquery_empty_xml_file):
        adapter = IBKRFlexQueryAdapter()
        result = adapter.parse_file(flexquery_empty_xml_file)
        assert result.status == ImportStatus.SUCCESS
        assert len(result.executions) == 0
        assert result.total_rows == 0


# ── AC-6: XXE prevention (defusedxml) ───────────────────────────────────


class TestXXEPrevention:
    """FIC-96 AC-6: XML parsing rejects XXE attack payloads."""

    def test_xxe_attack_does_not_expose_file_content(self, xxe_attack_xml_file):
        adapter = IBKRFlexQueryAdapter()
        result = adapter.parse_file(xxe_attack_xml_file)
        # defusedxml should reject the DTD entity declaration
        assert result.status == ImportStatus.FAILED


# ── AC-7: Multi-currency (base_currency + base_amount) ──────────────────


class TestMultiCurrency:
    """FIC-96 AC-7: currency, base_currency, base_amount via fxRateToBase."""

    def test_usd_trade_currency(self, flexquery_xml_file):
        adapter = IBKRFlexQueryAdapter()
        result = adapter.parse_file(flexquery_xml_file)
        assert result.executions[0].currency == "USD"

    def test_usd_trade_base_currency(self, flexquery_xml_file):
        adapter = IBKRFlexQueryAdapter()
        result = adapter.parse_file(flexquery_xml_file)
        assert result.executions[0].base_currency == "USD"

    def test_eur_trade_currency(self, flexquery_fx_xml_file):
        adapter = IBKRFlexQueryAdapter()
        result = adapter.parse_file(flexquery_fx_xml_file)
        trade = result.executions[0]
        assert trade.currency == "EUR"

    def test_eur_trade_base_amount_populated(self, flexquery_fx_xml_file):
        adapter = IBKRFlexQueryAdapter()
        result = adapter.parse_file(flexquery_fx_xml_file)
        trade = result.executions[0]
        # base_amount = tradePrice * quantity * fxRateToBase
        # = 95.20 * 50 * 1.08 = 5140.80
        assert trade.base_amount is not None
        assert trade.base_amount == Decimal("5140.80")


# ── AC-8: raw_data audit trail ──────────────────────────────────────────


class TestRawDataPreservation:
    """FIC-96 AC-8: raw_data dict preserves original XML attributes."""

    def test_raw_data_has_original_fields(self, flexquery_xml_file):
        adapter = IBKRFlexQueryAdapter()
        result = adapter.parse_file(flexquery_xml_file)
        trade = result.executions[0]
        assert isinstance(trade.raw_data, dict)
        assert len(trade.raw_data) > 0

    def test_raw_data_preserves_order_ref(self, flexquery_xml_file):
        adapter = IBKRFlexQueryAdapter()
        result = adapter.parse_file(flexquery_xml_file)
        trade = result.executions[0]
        assert trade.order_id == "ORDER001"


# ── Adapter protocol compliance ─────────────────────────────────────────


class TestAdapterProtocol:
    """Verify IBKRFlexQueryAdapter satisfies BrokerFileAdapter protocol."""

    def test_broker_type_property(self):
        adapter = IBKRFlexQueryAdapter()
        assert adapter.broker_type == BrokerType.IBKR

    def test_option_contract_multiplier(self, flexquery_xml_file):
        adapter = IBKRFlexQueryAdapter()
        result = adapter.parse_file(flexquery_xml_file)
        option_trade = result.executions[2]
        assert option_trade.contract_multiplier == Decimal("100")

    def test_future_contract_multiplier(self, flexquery_future_xml_file):
        adapter = IBKRFlexQueryAdapter()
        result = adapter.parse_file(flexquery_future_xml_file)
        future_trade = result.executions[0]
        assert future_trade.contract_multiplier == Decimal("50")
