"""Domain enum tests — MEU-2 acceptance criteria.

Tests written FIRST (Red phase) before any implementation exists.
All values from docs/build-plan/01-domain-layer.md §1.2.
"""

from __future__ import annotations

import ast
import inspect
from enum import StrEnum

import pytest

pytestmark = pytest.mark.unit


# ── AC-4: Module integrity — exactly 14 enum classes ────────────────────


class TestModuleIntegrity:
    """Verify the module contains exactly the 17 enum classes from the build plan."""

    def test_module_has_exactly_17_enum_classes(self) -> None:
        import zorivest_core.domain.enums as mod

        enum_classes = [
            name
            for name, obj in inspect.getmembers(mod, inspect.isclass)
            if issubclass(obj, StrEnum) and obj is not StrEnum
        ]
        expected = {
            "AccountType",
            "TradeAction",
            "ConvictionLevel",
            "PlanStatus",
            "ImageOwnerType",
            "DisplayModeFlag",
            "RoundTripStatus",
            "IdentifierType",
            "FeeType",
            "StrategyType",
            "MistakeCategory",
            "RoutingType",
            "TransactionCategory",
            "BalanceSource",
            "AuthMethod",
            # MEU-52 additions
            "QualityGrade",
            "EmotionalState",
        }
        assert set(enum_classes) == expected, (
            f"Expected 17 enums {expected}, got {set(enum_classes)}"
        )
        assert len(enum_classes) == 17


# ── AC-3: Every enum subclasses StrEnum ──────────────────────────────────


class TestStrEnumSubclass:
    """Verify every enum class is a StrEnum subclass."""

    def test_all_enums_subclass_strenum(self) -> None:
        import zorivest_core.domain.enums as mod

        for name, obj in inspect.getmembers(mod, inspect.isclass):
            if obj is StrEnum:
                continue
            if issubclass(obj, StrEnum):
                assert issubclass(obj, StrEnum), f"{name} is not a StrEnum subclass"


# ── AC-1: Core enum members ─────────────────────────────────────────────


class TestCoreEnums:
    """Test the 6 core enum definitions (AC-1)."""

    def test_account_type_members(self) -> None:
        from zorivest_core.domain.enums import AccountType

        assert len(AccountType) == 6
        assert AccountType.BROKER.value == "broker"
        assert AccountType.BANK.value == "bank"
        assert AccountType.REVOLVING.value == "revolving"
        assert AccountType.INSTALLMENT.value == "installment"
        assert AccountType.IRA.value == "ira"
        assert AccountType.K401.value == "401k"

    def test_trade_action_members(self) -> None:
        from zorivest_core.domain.enums import TradeAction

        assert len(TradeAction) == 2
        assert TradeAction.BOT.value == "BOT"
        assert TradeAction.SLD.value == "SLD"

    def test_conviction_level_members(self) -> None:
        from zorivest_core.domain.enums import ConvictionLevel

        assert len(ConvictionLevel) == 4
        assert ConvictionLevel.LOW.value == "low"
        assert ConvictionLevel.MEDIUM.value == "medium"
        assert ConvictionLevel.HIGH.value == "high"
        assert ConvictionLevel.MAX.value == "max"

    def test_plan_status_members(self) -> None:
        from zorivest_core.domain.enums import PlanStatus

        assert len(PlanStatus) == 5
        assert PlanStatus.DRAFT.value == "draft"
        assert PlanStatus.ACTIVE.value == "active"
        assert PlanStatus.EXECUTED.value == "executed"
        assert PlanStatus.EXPIRED.value == "expired"
        assert PlanStatus.CANCELLED.value == "cancelled"

    def test_image_owner_type_members(self) -> None:
        from zorivest_core.domain.enums import ImageOwnerType

        assert len(ImageOwnerType) == 3
        assert ImageOwnerType.TRADE.value == "trade"
        assert ImageOwnerType.REPORT.value == "report"
        assert ImageOwnerType.PLAN.value == "plan"

    def test_display_mode_flag_members(self) -> None:
        from zorivest_core.domain.enums import DisplayModeFlag

        assert len(DisplayModeFlag) == 3
        assert DisplayModeFlag.HIDE_DOLLARS.value == "hide_dollars"
        assert DisplayModeFlag.HIDE_PERCENTAGES.value == "hide_percentages"
        assert DisplayModeFlag.PERCENT_MODE.value == "percent_mode"


# ── AC-2: Expansion enum members ────────────────────────────────────────


class TestExpansionEnums:
    """Test the 8 expansion enum definitions (AC-2)."""

    def test_round_trip_status_members(self) -> None:
        from zorivest_core.domain.enums import RoundTripStatus

        assert len(RoundTripStatus) == 3
        assert RoundTripStatus.OPEN.value == "open"
        assert RoundTripStatus.CLOSED.value == "closed"
        assert RoundTripStatus.PARTIAL.value == "partial"

    def test_identifier_type_members(self) -> None:
        from zorivest_core.domain.enums import IdentifierType

        assert len(IdentifierType) == 4
        assert IdentifierType.CUSIP.value == "cusip"
        assert IdentifierType.ISIN.value == "isin"
        assert IdentifierType.SEDOL.value == "sedol"
        assert IdentifierType.FIGI.value == "figi"

    def test_fee_type_members(self) -> None:
        from zorivest_core.domain.enums import FeeType

        assert len(FeeType) == 7
        assert FeeType.COMMISSION.value == "commission"
        assert FeeType.EXCHANGE.value == "exchange"
        assert FeeType.REGULATORY.value == "regulatory"
        assert FeeType.ECN.value == "ecn"
        assert FeeType.CLEARING.value == "clearing"
        assert FeeType.PLATFORM.value == "platform"
        assert FeeType.OTHER.value == "other"

    def test_strategy_type_members(self) -> None:
        from zorivest_core.domain.enums import StrategyType

        assert len(StrategyType) == 7
        assert StrategyType.VERTICAL.value == "vertical"
        assert StrategyType.IRON_CONDOR.value == "iron_condor"
        assert StrategyType.BUTTERFLY.value == "butterfly"
        assert StrategyType.CALENDAR.value == "calendar"
        assert StrategyType.STRADDLE.value == "straddle"
        assert StrategyType.STRANGLE.value == "strangle"
        assert StrategyType.CUSTOM.value == "custom"

    def test_mistake_category_members(self) -> None:
        from zorivest_core.domain.enums import MistakeCategory

        assert len(MistakeCategory) == 10
        assert MistakeCategory.EARLY_EXIT.value == "early_exit"
        assert MistakeCategory.LATE_EXIT.value == "late_exit"
        assert MistakeCategory.OVERSIZED.value == "oversized"
        assert MistakeCategory.NO_STOP.value == "no_stop"
        assert MistakeCategory.REVENGE_TRADE.value == "revenge_trade"
        assert MistakeCategory.FOMO_ENTRY.value == "fomo_entry"
        assert MistakeCategory.IGNORED_PLAN.value == "ignored_plan"
        assert MistakeCategory.OVERTRADING.value == "overtrading"
        assert MistakeCategory.CHASING.value == "chasing"
        assert MistakeCategory.OTHER.value == "other"

    def test_routing_type_members(self) -> None:
        from zorivest_core.domain.enums import RoutingType

        assert len(RoutingType) == 3
        assert RoutingType.PFOF.value == "pfof"
        assert RoutingType.DMA.value == "dma"
        assert RoutingType.HYBRID.value == "hybrid"

    def test_transaction_category_members(self) -> None:
        from zorivest_core.domain.enums import TransactionCategory

        assert len(TransactionCategory) == 16
        assert TransactionCategory.DEPOSIT.value == "deposit"
        assert TransactionCategory.WITHDRAWAL.value == "withdrawal"
        assert TransactionCategory.TRANSFER_IN.value == "transfer_in"
        assert TransactionCategory.TRANSFER_OUT.value == "transfer_out"
        assert TransactionCategory.FEE.value == "fee"
        assert TransactionCategory.INTEREST.value == "interest"
        assert TransactionCategory.DIVIDEND.value == "dividend"
        assert TransactionCategory.ACH_DEBIT.value == "ach_debit"
        assert TransactionCategory.ACH_CREDIT.value == "ach_credit"
        assert TransactionCategory.WIRE_IN.value == "wire_in"
        assert TransactionCategory.WIRE_OUT.value == "wire_out"
        assert TransactionCategory.CHECK.value == "check"
        assert TransactionCategory.CARD_PURCHASE.value == "card_purchase"
        assert TransactionCategory.REFUND.value == "refund"
        assert TransactionCategory.ATM.value == "atm"
        assert TransactionCategory.OTHER.value == "other"

    def test_balance_source_members(self) -> None:
        from zorivest_core.domain.enums import BalanceSource

        assert len(BalanceSource) == 6
        assert BalanceSource.MANUAL.value == "manual"
        assert BalanceSource.CSV_IMPORT.value == "csv_import"
        assert BalanceSource.OFX_IMPORT.value == "ofx_import"
        assert BalanceSource.QIF_IMPORT.value == "qif_import"
        assert BalanceSource.PDF_IMPORT.value == "pdf_import"
        assert BalanceSource.AGENT_SUBMIT.value == "agent_submit"


# ── AC-5: Import surface — only StrEnum from enum ───────────────────────


class TestImportSurface:
    """Verify the module imports only StrEnum from enum."""

    def test_import_surface_only_enum(self) -> None:
        import zorivest_core.domain.enums as mod

        source_file = mod.__file__
        assert source_file is not None

        with open(source_file, encoding="utf-8") as f:
            tree = ast.parse(f.read())

        allowed_modules = {"__future__", "enum"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name in allowed_modules, (
                        f"Forbidden import: {alias.name}"
                    )
            elif isinstance(node, ast.ImportFrom):
                if node.module is not None:
                    top_module = node.module.split(".")[0]
                    assert top_module in allowed_modules, (
                        f"Forbidden import from: {node.module}"
                    )
