"""Port interface tests — MEU-5 acceptance criteria.

Tests written FIRST (Red phase) before any implementation exists.
FIC defined in implementation-plan.md §MEU-5.
All protocols sourced from 01-domain-layer.md §1.5 lines 452–507.
"""

from __future__ import annotations

import ast
import inspect
from typing import Protocol

import pytest

pytestmark = pytest.mark.unit


# ── AC-1 through AC-6: Protocol classes exist with correct methods ───────


class TestTradeRepository:
    """AC-1: TradeRepository Protocol with get, save, list_all, exists."""

    def test_trade_repository_is_protocol(self) -> None:
        from zorivest_core.application.ports import TradeRepository

        assert issubclass(TradeRepository, Protocol)

    def test_trade_repository_methods(self) -> None:
        from zorivest_core.application.ports import TradeRepository

        expected_methods = {"get", "save", "list_all", "exists"}
        actual_methods = {
            name
            for name, _ in inspect.getmembers(
                TradeRepository, predicate=inspect.isfunction
            )
            if not name.startswith("_")
        }
        assert expected_methods <= actual_methods, (
            f"Missing methods: {expected_methods - actual_methods}"
        )


class TestImageRepository:
    """AC-2: ImageRepository Protocol with save, get, get_for_owner, delete, get_thumbnail."""

    def test_image_repository_is_protocol(self) -> None:
        from zorivest_core.application.ports import ImageRepository

        assert issubclass(ImageRepository, Protocol)

    def test_image_repository_methods(self) -> None:
        from zorivest_core.application.ports import ImageRepository

        expected_methods = {"save", "get", "get_for_owner", "delete", "get_thumbnail"}
        actual_methods = {
            name
            for name, _ in inspect.getmembers(
                ImageRepository, predicate=inspect.isfunction
            )
            if not name.startswith("_")
        }
        assert expected_methods <= actual_methods, (
            f"Missing methods: {expected_methods - actual_methods}"
        )


class TestUnitOfWork:
    """AC-3: UnitOfWork Protocol with trades, images, __enter__/__exit__, commit, rollback."""

    def test_unit_of_work_is_protocol(self) -> None:
        from zorivest_core.application.ports import UnitOfWork

        assert issubclass(UnitOfWork, Protocol)

    def test_unit_of_work_methods(self) -> None:
        from zorivest_core.application.ports import UnitOfWork

        expected_methods = {"commit", "rollback"}
        actual_methods = {
            name
            for name, _ in inspect.getmembers(
                UnitOfWork, predicate=inspect.isfunction
            )
            if not name.startswith("_")
        }
        assert expected_methods <= actual_methods, (
            f"Missing methods: {expected_methods - actual_methods}"
        )

    def test_unit_of_work_has_context_manager(self) -> None:
        from zorivest_core.application.ports import UnitOfWork

        all_methods = {
            name
            for name, _ in inspect.getmembers(
                UnitOfWork, predicate=inspect.isfunction
            )
        }
        assert "__enter__" in all_methods
        assert "__exit__" in all_methods

    def test_unit_of_work_has_repository_attributes(self) -> None:
        from zorivest_core.application.ports import UnitOfWork

        # Protocol attrs may appear in annotations or class vars
        cls_annotations: dict = {}
        for cls in UnitOfWork.__mro__:
            cls_annotations.update(getattr(cls, "__annotations__", {}))
        assert "trades" in cls_annotations, "UnitOfWork missing 'trades' attribute"
        assert "images" in cls_annotations, "UnitOfWork missing 'images' attribute"
        assert "settings" in cls_annotations, "UnitOfWork missing 'settings' attribute"
        assert "app_defaults" in cls_annotations, "UnitOfWork missing 'app_defaults' attribute"


class TestBrokerPort:
    """AC-4: BrokerPort Protocol with get_account, get_positions, get_orders, get_bars, get_order_history."""

    def test_broker_port_is_protocol(self) -> None:
        from zorivest_core.application.ports import BrokerPort

        assert issubclass(BrokerPort, Protocol)

    def test_broker_port_methods(self) -> None:
        from zorivest_core.application.ports import BrokerPort

        expected_methods = {
            "get_account",
            "get_positions",
            "get_orders",
            "get_bars",
            "get_order_history",
        }
        actual_methods = {
            name
            for name, _ in inspect.getmembers(
                BrokerPort, predicate=inspect.isfunction
            )
            if not name.startswith("_")
        }
        assert expected_methods <= actual_methods, (
            f"Missing methods: {expected_methods - actual_methods}"
        )


class TestBankImportPort:
    """AC-5: BankImportPort Protocol with detect_format, parse_statement, detect_bank."""

    def test_bank_import_port_is_protocol(self) -> None:
        from zorivest_core.application.ports import BankImportPort

        assert issubclass(BankImportPort, Protocol)

    def test_bank_import_port_methods(self) -> None:
        from zorivest_core.application.ports import BankImportPort

        expected_methods = {"detect_format", "parse_statement", "detect_bank"}
        actual_methods = {
            name
            for name, _ in inspect.getmembers(
                BankImportPort, predicate=inspect.isfunction
            )
            if not name.startswith("_")
        }
        assert expected_methods <= actual_methods, (
            f"Missing methods: {expected_methods - actual_methods}"
        )


class TestIdentifierResolverPort:
    """AC-6: IdentifierResolverPort Protocol with resolve, batch_resolve."""

    def test_identifier_resolver_port_is_protocol(self) -> None:
        from zorivest_core.application.ports import IdentifierResolverPort

        assert issubclass(IdentifierResolverPort, Protocol)

    def test_identifier_resolver_port_methods(self) -> None:
        from zorivest_core.application.ports import IdentifierResolverPort

        expected_methods = {"resolve", "batch_resolve"}
        actual_methods = {
            name
            for name, _ in inspect.getmembers(
                IdentifierResolverPort, predicate=inspect.isfunction
            )
            if not name.startswith("_")
        }
        assert expected_methods <= actual_methods, (
            f"Missing methods: {expected_methods - actual_methods}"
        )


# ── AC-7: All are Protocol subclasses (not runtime_checkable) ───────────


class TestProtocolConvention:
    """AC-7: All port classes are Protocol subclasses, not runtime_checkable."""

    def test_all_ports_are_protocols(self) -> None:
        import zorivest_core.application.ports as mod

        port_classes = [
            obj
            for name, obj in inspect.getmembers(mod, inspect.isclass)
            if obj.__module__ == mod.__name__
        ]
        for cls in port_classes:
            assert issubclass(cls, Protocol), f"{cls.__name__} is not a Protocol"

    def test_none_are_runtime_checkable(self) -> None:
        """Protocols MUST NOT use @runtime_checkable decorator."""
        import zorivest_core.application.ports as mod

        for name, obj in inspect.getmembers(mod, inspect.isclass):
            if obj.__module__ == mod.__name__:
                # runtime_checkable sets _is_runtime_protocol = True
                is_runtime = getattr(obj, "_is_runtime_protocol", False)
                assert not is_runtime, (
                    f"{name} must NOT be @runtime_checkable"
                )


# ── AC-8: Import surface ────────────────────────────────────────────────


class TestImportSurface:
    """AC-8: Module imports only from allowed modules."""

    def test_import_surface_ports(self) -> None:
        import zorivest_core.application.ports as mod

        source_file = mod.__file__
        assert source_file is not None

        with open(source_file, encoding="utf-8") as f:
            tree = ast.parse(f.read())

        allowed_modules = {
            "__future__",
            "typing",
            "zorivest_core",
        }
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top = alias.name.split(".")[0]
                    assert top in allowed_modules, (
                        f"Forbidden import: {alias.name}"
                    )
            elif isinstance(node, ast.ImportFrom):
                if node.module is not None:
                    top_module = node.module.split(".")[0]
                    assert top_module in allowed_modules, (
                        f"Forbidden import from: {node.module}"
                    )


# ── Module integrity ────────────────────────────────────────────────────


class TestModuleIntegrity:
    """Verify the module exports exactly the 14 expected Protocol classes."""

    def test_module_has_exactly_15_protocol_classes(self) -> None:
        import zorivest_core.application.ports as mod

        class_names = [
            name
            for name, obj in inspect.getmembers(mod, inspect.isclass)
            if obj.__module__ == mod.__name__
        ]
        expected = {
            "TradeRepository",
            "ImageRepository",
            "UnitOfWork",
            "BrokerPort",
            "BankImportPort",
            "IdentifierResolverPort",
            # Phase 2 additions (MEU-12)
            "AccountRepository",
            "BalanceSnapshotRepository",
            "RoundTripRepository",
            # Phase 2A additions (MEU-18)
            "SettingsRepository",
            "AppDefaultsRepository",
            # Phase 8 additions (MEU-56)
            "MarketDataPort",
            # Phase 8 additions (MEU-60)
            "MarketProviderSettingsRepository",
            # Phase 1 additions (MEU-52)
            "TradeReportRepository",
            # Phase 1 additions (MEU-66)
            "TradePlanRepository",
        }
        assert set(class_names) == expected, (
            f"Expected {expected}, got {set(class_names)}"
        )

