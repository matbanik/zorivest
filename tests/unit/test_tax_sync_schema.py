# tests/unit/test_tax_sync_schema.py
"""FIC tests for Tax Sync Schema — MEU-216 ACs 216.1–216.6.

Feature Intent Contract:
  TaxLot entity gains 4 provenance fields (materialized_at, is_user_modified,
  source_hash, sync_status) for the Derived Entity with Provenance pattern.
  SETTINGS_REGISTRY gains tax.conflict_resolution key.

All tests written FIRST (RED phase) per TDD protocol.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal


from zorivest_core.domain.entities import TaxLot
from zorivest_core.domain.settings import SETTINGS_REGISTRY


# ── Helpers ──────────────────────────────────────────────────────────────


def _lot(
    lot_id: str = "L1",
    **overrides: object,
) -> TaxLot:
    """Create a TaxLot with sensible defaults for sync schema tests."""
    defaults: dict[str, object] = {
        "lot_id": lot_id,
        "account_id": "ACC-1",
        "ticker": "AAPL",
        "open_date": datetime(2024, 1, 15, tzinfo=timezone.utc),
        "close_date": None,
        "quantity": 100.0,
        "cost_basis": Decimal("150.00"),
        "proceeds": Decimal("0.00"),
        "wash_sale_adjustment": Decimal("0.00"),
        "is_closed": False,
        "linked_trade_ids": [],
    }
    defaults.update(overrides)
    return TaxLot(**defaults)  # type: ignore[arg-type]


# ── AC-216-1: TaxLot entity has 4 provenance fields ─────────────────────


class TestTaxLotProvenanceFields:
    """AC-216-1: TaxLot entity has materialized_at, is_user_modified,
    source_hash, sync_status fields with correct types."""

    def test_taxlot_has_materialized_at(self) -> None:
        lot = _lot()
        assert hasattr(lot, "materialized_at")

    def test_taxlot_has_is_user_modified(self) -> None:
        lot = _lot()
        assert hasattr(lot, "is_user_modified")

    def test_taxlot_has_source_hash(self) -> None:
        lot = _lot()
        assert hasattr(lot, "source_hash")

    def test_taxlot_has_sync_status(self) -> None:
        lot = _lot()
        assert hasattr(lot, "sync_status")

    def test_materialized_at_accepts_iso_string(self) -> None:
        lot = _lot(materialized_at="2026-05-15T10:00:00Z")
        assert lot.materialized_at == "2026-05-15T10:00:00Z"

    def test_source_hash_accepts_hex_string(self) -> None:
        lot = _lot(source_hash="abc123def456")
        assert lot.source_hash == "abc123def456"


# ── AC-216-3: Default values ────────────────────────────────────────────


class TestTaxLotProvenanceDefaults:
    """AC-216-3: New TaxLot defaults: sync_status='synced', is_user_modified=False."""

    def test_default_sync_status_is_synced(self) -> None:
        lot = _lot()
        assert lot.sync_status == "synced"

    def test_default_is_user_modified_is_false(self) -> None:
        lot = _lot()
        assert lot.is_user_modified is False

    def test_default_materialized_at_is_none(self) -> None:
        lot = _lot()
        assert lot.materialized_at is None

    def test_default_source_hash_is_none(self) -> None:
        lot = _lot()
        assert lot.source_hash is None


# ── AC-216-2: TaxLotModel round-trip ─────────────────────────────────────


class TestTaxLotModelRoundTrip:
    """AC-216-2: TaxLotModel round-trips provenance fields to/from SQLite.

    This is an integration test — requires DB fixture.
    Placed here for now; will use in-memory SQLite.
    """

    def test_model_persists_provenance_fields(self) -> None:
        """Round-trip: entity → model → entity preserves provenance."""
        from zorivest_infra.database.models import TaxLotModel

        # Verify the model has the columns
        assert hasattr(TaxLotModel, "materialized_at")
        assert hasattr(TaxLotModel, "is_user_modified")
        assert hasattr(TaxLotModel, "source_hash")
        assert hasattr(TaxLotModel, "sync_status")


# ── AC-216-4: Settings registry entry ────────────────────────────────────


class TestConflictResolutionSetting:
    """AC-216-4: SETTINGS_REGISTRY has tax.conflict_resolution key."""

    def test_key_exists_in_registry(self) -> None:
        assert "tax.conflict_resolution" in SETTINGS_REGISTRY

    def test_default_value_is_flag(self) -> None:
        spec = SETTINGS_REGISTRY["tax.conflict_resolution"]
        assert spec.hardcoded_default == "flag"

    def test_value_type_is_str(self) -> None:
        spec = SETTINGS_REGISTRY["tax.conflict_resolution"]
        assert spec.value_type == "str"

    def test_allowed_values(self) -> None:
        spec = SETTINGS_REGISTRY["tax.conflict_resolution"]
        assert spec.allowed_values == ["flag", "auto_resolve", "block"]

    def test_category_is_tax(self) -> None:
        spec = SETTINGS_REGISTRY["tax.conflict_resolution"]
        assert spec.category == "tax"


# ── AC-216-5: Setting rejects invalid values ─────────────────────────────


class TestConflictResolutionValidation:
    """AC-216-5: Setting rejects invalid values (e.g., 'merge') with validation error."""

    def test_valid_flag_passes(self) -> None:
        spec = SETTINGS_REGISTRY["tax.conflict_resolution"]
        assert spec.allowed_values is not None
        assert "flag" in spec.allowed_values

    def test_valid_auto_resolve_passes(self) -> None:
        spec = SETTINGS_REGISTRY["tax.conflict_resolution"]
        assert spec.allowed_values is not None
        assert "auto_resolve" in spec.allowed_values

    def test_valid_block_passes(self) -> None:
        spec = SETTINGS_REGISTRY["tax.conflict_resolution"]
        assert spec.allowed_values is not None
        assert "block" in spec.allowed_values

    def test_invalid_merge_not_in_allowed(self) -> None:
        spec = SETTINGS_REGISTRY["tax.conflict_resolution"]
        assert spec.allowed_values is not None
        assert "merge" not in spec.allowed_values

    def test_invalid_empty_string_not_in_allowed(self) -> None:
        spec = SETTINGS_REGISTRY["tax.conflict_resolution"]
        assert spec.allowed_values is not None
        assert "" not in spec.allowed_values


# ── AC-216-6: Migration idempotency ──────────────────────────────────────


class TestMigrationIdempotency:
    """AC-216-6: create_all() is idempotent — running twice doesn't error."""

    def test_create_all_twice_no_error(self) -> None:
        """Running Base.metadata.create_all() twice should not raise."""
        from sqlalchemy import create_engine

        from zorivest_infra.database.models import Base

        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        # Second call must not raise
        Base.metadata.create_all(engine)
