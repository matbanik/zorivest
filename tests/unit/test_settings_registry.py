# tests/unit/test_settings_registry.py
"""Tests for SettingSpec, Sensitivity, SETTINGS_REGISTRY, and seed_defaults (MEU-17).

AC-17.1: SETTINGS_REGISTRY contains exactly 24 entries
AC-17.2: Every entry has valid value_type
AC-17.3: Every entry has valid category
AC-17.4: seed_defaults() populates all 24 rows
AC-17.5: seed_defaults() is idempotent
AC-17.6: Dynamic key ui.panel.*.collapsed is present
"""

from __future__ import annotations


from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from zorivest_core.domain.settings import (
    SETTINGS_REGISTRY,
    Sensitivity,
    SettingSpec,
)
from zorivest_infra.database.models import AppDefaultModel, Base
from zorivest_infra.database.seed_defaults import seed_defaults

VALID_VALUE_TYPES = {"str", "int", "float", "bool", "json"}
VALID_CATEGORIES = {"dialog", "logging", "display", "backup", "ui", "notification"}


def _engine():
    """Create a fresh in-memory SQLite engine with all tables."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


# ── AC-17.1: Registry count ──────────────────────────────────────────────


class TestRegistryCount:
    """AC-17.1: SETTINGS_REGISTRY contains exactly 24 entries."""

    def test_registry_has_24_entries(self) -> None:
        assert len(SETTINGS_REGISTRY) == 24


# ── AC-17.2: Value types ─────────────────────────────────────────────────


class TestValueTypes:
    """AC-17.2: Every registry entry has a valid value_type."""

    def test_all_value_types_valid(self) -> None:
        for key, spec in SETTINGS_REGISTRY.items():
            assert spec.value_type in VALID_VALUE_TYPES, (
                f"Setting '{key}' has invalid value_type '{spec.value_type}'"
            )

    def test_every_entry_is_setting_spec(self) -> None:
        for key, spec in SETTINGS_REGISTRY.items():
            assert isinstance(spec, SettingSpec), (
                f"Setting '{key}' is not a SettingSpec instance"
            )


# ── AC-17.3: Categories ──────────────────────────────────────────────────


class TestCategories:
    """AC-17.3: Every registry entry has a valid category."""

    def test_all_categories_valid(self) -> None:
        for key, spec in SETTINGS_REGISTRY.items():
            assert spec.category in VALID_CATEGORIES, (
                f"Setting '{key}' has invalid category '{spec.category}'"
            )

    def test_all_categories_represented(self) -> None:
        """All 6 expected categories appear at least once."""
        categories = {spec.category for spec in SETTINGS_REGISTRY.values()}
        assert categories == VALID_CATEGORIES


# ── AC-17.4: Seed defaults ───────────────────────────────────────────────


class TestSeedDefaults:
    """AC-17.4: seed_defaults() populates app_defaults with all 24 rows."""

    def test_seed_populates_all_rows(self) -> None:
        engine = _engine()
        with Session(engine) as session:
            seed_defaults(session, SETTINGS_REGISTRY)
            session.commit()
            count = session.query(AppDefaultModel).count()
            assert count == 24

    def test_seed_values_match_registry(self) -> None:
        """Seeded values match the registry's hardcoded_default."""
        engine = _engine()
        with Session(engine) as session:
            seed_defaults(session, SETTINGS_REGISTRY)
            session.commit()
            for key, spec in SETTINGS_REGISTRY.items():
                row = session.get(AppDefaultModel, key)
                assert row is not None, f"Missing seed row for '{key}'"
                assert row.value == str(spec.hardcoded_default), (
                    f"Value mismatch for '{key}': {row.value!r} != {str(spec.hardcoded_default)!r}"
                )
                assert row.value_type == spec.value_type
                assert row.category == spec.category

    def test_seed_sets_description(self) -> None:
        """Seeded rows carry the spec description."""
        engine = _engine()
        with Session(engine) as session:
            seed_defaults(session, SETTINGS_REGISTRY)
            session.commit()
            # Pick a known entry to verify description propagation
            row = session.get(AppDefaultModel, "dialog.confirm_delete")
            assert row is not None
            assert row.description is not None
            assert len(row.description) > 0


# ── AC-17.5: Idempotent re-seeding ───────────────────────────────────────


class TestIdempotentSeeding:
    """AC-17.5: Re-running seed_defaults() doesn't duplicate or error."""

    def test_seed_is_idempotent(self) -> None:
        engine = _engine()
        with Session(engine) as session:
            seed_defaults(session, SETTINGS_REGISTRY)
            session.commit()
            # Run again — should not raise or duplicate
            seed_defaults(session, SETTINGS_REGISTRY)
            session.commit()
            count = session.query(AppDefaultModel).count()
            assert count == 24

    def test_seed_updates_existing_on_rerun(self) -> None:
        """Re-seeding updates value/description if the registry changed."""
        engine = _engine()
        with Session(engine) as session:
            seed_defaults(session, SETTINGS_REGISTRY)
            session.commit()

            # Manually change a row to simulate stale DB
            row = session.get(AppDefaultModel, "ui.theme")
            assert row is not None
            row.value = "stale_value"
            session.commit()

            # Re-seed should restore the registry value
            seed_defaults(session, SETTINGS_REGISTRY)
            session.commit()
            row = session.get(AppDefaultModel, "ui.theme")
            assert row is not None
            assert row.value == "dark"


# ── AC-17.6: Dynamic key ─────────────────────────────────────────────────


class TestDynamicKey:
    """AC-17.6: Dynamic key ui.panel.*.collapsed is in the registry."""

    def test_dynamic_key_in_registry(self) -> None:
        assert "ui.panel.*.collapsed" in SETTINGS_REGISTRY

    def test_dynamic_key_is_bool(self) -> None:
        spec = SETTINGS_REGISTRY["ui.panel.*.collapsed"]
        assert spec.value_type == "bool"
        assert spec.hardcoded_default is False


# ── Sensitivity enum ──────────────────────────────────────────────────────


class TestSensitivityEnum:
    """Verify Sensitivity enum has the three expected values."""

    def test_three_sensitivity_levels(self) -> None:
        assert len(Sensitivity) == 3

    def test_sensitivity_values(self) -> None:
        assert Sensitivity.NON_SENSITIVE.value == "non_sensitive"
        assert Sensitivity.SENSITIVE.value == "sensitive"
        assert Sensitivity.SECRET.value == "secret"
