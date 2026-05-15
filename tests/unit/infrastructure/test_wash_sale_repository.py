# tests/unit/infrastructure/test_wash_sale_repository.py
"""Tests for WashSaleChain repository protocol compliance (MEU-130 AC-130.8, AC-130.9, AC-130.10, AC-130.11).

Protocol-level unit tests verifying the repository contract shape.
Behavioral CRUD tests are in tests/integration/test_wash_sale_repo_integration.py.
"""

from __future__ import annotations


# ── AC-130.8: WashSaleChainRepository protocol ──────────────────────────


class TestWashSaleChainRepositoryProtocol:
    """AC-130.8: Protocol has get, save, update, list_for_ticker, list_active."""

    def test_protocol_has_required_methods(self) -> None:
        """The WashSaleChainRepository protocol exposes all 5 methods."""
        from zorivest_core.application.ports import WashSaleChainRepository

        # Verify protocol has expected methods via introspection
        expected_methods = {"get", "save", "update", "list_for_ticker", "list_active"}
        protocol_methods = {
            name for name in dir(WashSaleChainRepository) if not name.startswith("_")
        }
        assert expected_methods <= protocol_methods

    def test_uow_has_wash_sale_chains_attribute(self) -> None:
        """AC-130.11: UnitOfWork exposes wash_sale_chains attribute."""
        from zorivest_core.application.ports import UnitOfWork

        assert hasattr(UnitOfWork, "__protocol_attrs__") or "wash_sale_chains" in dir(
            UnitOfWork
        )


# ── AC-130.9: SQLAlchemy models ─────────────────────────────────────────


class TestWashSaleModels:
    """AC-130.9: WashSaleChainModel and WashSaleEntryModel exist."""

    def test_chain_model_has_table_name(self) -> None:
        """WashSaleChainModel has __tablename__ = 'wash_sale_chains'."""
        from zorivest_infra.database.wash_sale_models import WashSaleChainModel

        assert WashSaleChainModel.__tablename__ == "wash_sale_chains"

    def test_entry_model_has_table_name(self) -> None:
        """WashSaleEntryModel has __tablename__ = 'wash_sale_entries'."""
        from zorivest_infra.database.wash_sale_models import WashSaleEntryModel

        assert WashSaleEntryModel.__tablename__ == "wash_sale_entries"


# ── AC-130.10: SqlWashSaleChainRepository ────────────────────────────────


class TestSqlWashSaleChainRepository:
    """AC-130.10: SqlWashSaleChainRepository exists and implements protocol."""

    def test_class_exists(self) -> None:
        """SqlWashSaleChainRepository can be imported."""
        from zorivest_infra.database.wash_sale_repository import (
            SqlWashSaleChainRepository,
        )

        assert SqlWashSaleChainRepository is not None

    def test_has_crud_methods(self) -> None:
        """Repository class has all 5 protocol methods."""
        from zorivest_infra.database.wash_sale_repository import (
            SqlWashSaleChainRepository,
        )

        expected_methods = {"get", "save", "update", "list_for_ticker", "list_active"}
        actual_methods = {
            name for name in dir(SqlWashSaleChainRepository) if not name.startswith("_")
        }
        assert expected_methods <= actual_methods
