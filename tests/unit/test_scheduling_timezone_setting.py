# tests/unit/test_scheduling_timezone_setting.py
"""Tests for scheduling.default_timezone setting registration (BUG-SCHED-TIMEZONE).

FIC — Feature Intent Contract:
  The scheduling.default_timezone setting must be a registered, validatable,
  persistable setting in SETTINGS_REGISTRY so the Settings API works for it.

Acceptance Criteria:
  AC-TZ-1 (Spec)       : Key exists in SETTINGS_REGISTRY
  AC-TZ-2 (Local Canon): value_type=str, default=UTC, category=scheduling
  AC-TZ-3 (Local Canon): max_length=64, no allowed_values
  AC-TZ-4 (Local Canon): exportable=True, sensitivity=NON_SENSITIVE
  AC-TZ-5 (Spec)       : Validator accepts valid timezone strings
  AC-TZ-6 (Spec)       : Validator rejects values exceeding max_length=64
  AC-TZ-7 (Spec)       : PUT → GET roundtrip via API preserves the value
  AC-TZ-8 (Spec)       : DELETE resets to hardcoded default "UTC"
  AC-TZ-9 (Spec)       : Seed defaults includes the entry

Bug context: The timezone setting was missing from SETTINGS_REGISTRY, causing
the SettingsValidator to reject PUT requests with 422 "Unknown setting".
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from zorivest_core.domain.settings import (
    SETTINGS_REGISTRY,
    Sensitivity,
    SettingSpec,
)
from zorivest_core.domain.settings_validator import SettingsValidator
from zorivest_infra.database.models import AppDefaultModel, Base
from zorivest_infra.database.seed_defaults import seed_defaults

SETTING_KEY = "scheduling.default_timezone"


# ── Helpers ──────────────────────────────────────────────────────────────


def _engine():
    """Create a fresh in-memory SQLite engine with all tables."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture()
def client():
    """HTTP test client with lifespan (services initialized)."""
    from zorivest_api.main import create_app

    app = create_app()
    with TestClient(app, raise_server_exceptions=False) as c:
        app.state.db_unlocked = True
        app.state.start_time = __import__("time").time()
        yield c


# ── AC-TZ-1: Key exists in SETTINGS_REGISTRY ────────────────────────────


class TestTimezoneKeyExists:
    """AC-TZ-1: scheduling.default_timezone is a registered setting."""

    def test_key_in_registry(self) -> None:
        assert SETTING_KEY in SETTINGS_REGISTRY

    def test_key_is_setting_spec(self) -> None:
        assert isinstance(SETTINGS_REGISTRY[SETTING_KEY], SettingSpec)


# ── AC-TZ-2: Correct type, default, and category ────────────────────────


class TestTimezoneMetadata:
    """AC-TZ-2: value_type=str, hardcoded_default=UTC, category=scheduling."""

    def test_value_type_is_str(self) -> None:
        spec = SETTINGS_REGISTRY[SETTING_KEY]
        assert spec.value_type == "str"

    def test_hardcoded_default_is_utc(self) -> None:
        spec = SETTINGS_REGISTRY[SETTING_KEY]
        assert spec.hardcoded_default == "UTC"

    def test_category_is_scheduling(self) -> None:
        spec = SETTINGS_REGISTRY[SETTING_KEY]
        assert spec.category == "scheduling"


# ── AC-TZ-3: max_length and no enum constraint ──────────────────────────


class TestTimezoneConstraints:
    """AC-TZ-3: max_length=64, no allowed_values constraint."""

    def test_max_length_64(self) -> None:
        spec = SETTINGS_REGISTRY[SETTING_KEY]
        assert spec.max_length == 64

    def test_no_allowed_values(self) -> None:
        spec = SETTINGS_REGISTRY[SETTING_KEY]
        assert spec.allowed_values is None

    def test_no_numeric_range(self) -> None:
        spec = SETTINGS_REGISTRY[SETTING_KEY]
        assert spec.min_value is None
        assert spec.max_value is None

    def test_no_custom_validator(self) -> None:
        spec = SETTINGS_REGISTRY[SETTING_KEY]
        assert spec.validator is None


# ── AC-TZ-4: Exportable and non-sensitive ────────────────────────────────


class TestTimezoneExportSensitivity:
    """AC-TZ-4: exportable=True, sensitivity=NON_SENSITIVE."""

    def test_exportable(self) -> None:
        spec = SETTINGS_REGISTRY[SETTING_KEY]
        assert spec.exportable is True

    def test_non_sensitive(self) -> None:
        spec = SETTINGS_REGISTRY[SETTING_KEY]
        assert spec.sensitivity == Sensitivity.NON_SENSITIVE

    def test_description_not_empty(self) -> None:
        spec = SETTINGS_REGISTRY[SETTING_KEY]
        assert spec.description
        assert len(spec.description) > 0


# ── AC-TZ-5: Validator accepts valid timezone strings ────────────────────


class TestTimezoneValidation:
    """AC-TZ-5: The SettingsValidator accepts valid timezone strings."""

    @pytest.fixture()
    def validator(self) -> SettingsValidator:
        return SettingsValidator(SETTINGS_REGISTRY)

    def test_accepts_utc(self, validator: SettingsValidator) -> None:
        result = validator.validate(SETTING_KEY, "UTC")
        assert result.valid is True

    def test_accepts_named_timezone(self, validator: SettingsValidator) -> None:
        result = validator.validate(SETTING_KEY, "America/New_York")
        assert result.valid is True

    def test_accepts_short_timezone_name(self, validator: SettingsValidator) -> None:
        result = validator.validate(SETTING_KEY, "EST")
        assert result.valid is True

    def test_accepts_offset_format(self, validator: SettingsValidator) -> None:
        result = validator.validate(SETTING_KEY, "Etc/GMT+5")
        assert result.valid is True

    def test_accepts_complex_timezone(self, validator: SettingsValidator) -> None:
        result = validator.validate(SETTING_KEY, "Asia/Kolkata")
        assert result.valid is True

    def test_accepts_us_timezone(self, validator: SettingsValidator) -> None:
        result = validator.validate(SETTING_KEY, "US/Eastern")
        assert result.valid is True


# ── AC-TZ-6: Validator rejects values exceeding max_length ──────────────


class TestTimezoneValidationNegative:
    """AC-TZ-6: Values exceeding max_length=64 are rejected."""

    @pytest.fixture()
    def validator(self) -> SettingsValidator:
        return SettingsValidator(SETTINGS_REGISTRY)

    def test_rejects_string_exceeding_max_length(
        self, validator: SettingsValidator
    ) -> None:
        long_value = "A" * 65  # max_length=64
        result = validator.validate(SETTING_KEY, long_value)
        assert result.valid is False
        assert any("length" in err.lower() for err in result.errors)

    def test_accepts_string_at_max_length(self, validator: SettingsValidator) -> None:
        exact_value = "A" * 64  # exactly at max_length
        result = validator.validate(SETTING_KEY, exact_value)
        assert result.valid is True

    def test_rejects_sql_injection(self, validator: SettingsValidator) -> None:
        """Security stage: SQL injection patterns are rejected."""
        result = validator.validate(SETTING_KEY, "'; DROP TABLE policies;--")
        assert result.valid is False
        assert any("sql" in err.lower() for err in result.errors)

    def test_rejects_script_injection(self, validator: SettingsValidator) -> None:
        """Security stage: Script injection patterns are rejected."""
        result = validator.validate(SETTING_KEY, "<script>alert('xss')</script>")
        assert result.valid is False
        assert any("script" in err.lower() for err in result.errors)


# ── AC-TZ-7: PUT → GET roundtrip via API ────────────────────────────────


class TestTimezoneApiRoundtrip:
    """AC-TZ-7: PUT → GET roundtrip via API preserves the timezone value."""

    def test_put_single_key_returns_200(self, client: TestClient) -> None:
        resp = client.put(
            f"/api/v1/settings/{SETTING_KEY}",
            json={"value": "America/New_York"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "updated"
        assert data["count"] == 1

    def test_put_get_roundtrip(self, client: TestClient) -> None:
        # PUT the timezone
        client.put(
            f"/api/v1/settings/{SETTING_KEY}",
            json={"value": "Europe/London"},
        )
        # GET it back
        get_resp = client.get(f"/api/v1/settings/{SETTING_KEY}")
        assert get_resp.status_code == 200
        data = get_resp.json()
        assert data["key"] == SETTING_KEY
        assert data["value"] == "Europe/London"
        assert data["value_type"] == "str"

    def test_bulk_put_includes_timezone(self, client: TestClient) -> None:
        """Timezone is settable via bulk PUT alongside other settings."""
        resp = client.put(
            "/api/v1/settings",
            json={SETTING_KEY: "Asia/Tokyo"},
        )
        assert resp.status_code == 200
        # Verify via GET
        get_resp = client.get(f"/api/v1/settings/{SETTING_KEY}")
        assert get_resp.json()["value"] == "Asia/Tokyo"

    def test_resolved_includes_timezone(self, client: TestClient) -> None:
        """GET /settings/resolved includes the timezone with source attribution."""
        resp = client.get("/api/v1/settings/resolved")
        assert resp.status_code == 200
        data = resp.json()
        assert SETTING_KEY in data
        entry = data[SETTING_KEY]
        assert entry["key"] == SETTING_KEY
        assert entry["value_type"] == "str"
        assert entry["source"] in ("user", "default", "hardcoded")


# ── AC-TZ-8: DELETE resets to hardcoded default "UTC" ────────────────────


class TestTimezoneDeleteReset:
    """AC-TZ-8: DELETE resets the timezone to the hardcoded default 'UTC'."""

    def test_delete_resets_to_utc(self, client: TestClient) -> None:
        # Set a non-default timezone
        client.put(
            f"/api/v1/settings/{SETTING_KEY}",
            json={"value": "America/Chicago"},
        )
        # Verify it's set
        get_resp = client.get(f"/api/v1/settings/{SETTING_KEY}")
        assert get_resp.json()["value"] == "America/Chicago"

        # DELETE the override
        del_resp = client.delete(f"/api/v1/settings/{SETTING_KEY}")
        assert del_resp.status_code == 204

        # GET should return the hardcoded default
        get_resp2 = client.get(f"/api/v1/settings/{SETTING_KEY}")
        assert get_resp2.status_code == 200
        assert get_resp2.json()["value"] == "UTC"

    def test_resolved_shows_hardcoded_after_delete(self, client: TestClient) -> None:
        # Set then delete
        client.put(f"/api/v1/settings/{SETTING_KEY}", json={"value": "US/Pacific"})
        client.delete(f"/api/v1/settings/{SETTING_KEY}")

        # Resolved should show hardcoded source
        resp = client.get("/api/v1/settings/resolved")
        data = resp.json()
        assert data[SETTING_KEY]["value"] == "UTC"
        assert data[SETTING_KEY]["source"] == "hardcoded"


# ── AC-TZ-9: Seed defaults includes the entry ───────────────────────────


class TestTimezoneSeedDefaults:
    """AC-TZ-9: seed_defaults() includes scheduling.default_timezone."""

    def test_seed_creates_timezone_row(self) -> None:
        engine = _engine()
        with Session(engine) as session:
            seed_defaults(session, SETTINGS_REGISTRY)
            session.commit()
            row = session.get(AppDefaultModel, SETTING_KEY)
            assert row is not None

    def test_seed_timezone_value_is_utc(self) -> None:
        engine = _engine()
        with Session(engine) as session:
            seed_defaults(session, SETTINGS_REGISTRY)
            session.commit()
            row = session.get(AppDefaultModel, SETTING_KEY)
            assert row is not None
            assert row.value == "UTC"  # type: ignore[operator]

    def test_seed_timezone_type_is_str(self) -> None:
        engine = _engine()
        with Session(engine) as session:
            seed_defaults(session, SETTINGS_REGISTRY)
            session.commit()
            row = session.get(AppDefaultModel, SETTING_KEY)
            assert row is not None
            assert row.value_type == "str"  # type: ignore[operator]

    def test_seed_timezone_category_is_scheduling(self) -> None:
        engine = _engine()
        with Session(engine) as session:
            seed_defaults(session, SETTINGS_REGISTRY)
            session.commit()
            row = session.get(AppDefaultModel, SETTING_KEY)
            assert row is not None
            assert row.category == "scheduling"  # type: ignore[operator]

    def test_seed_timezone_description_set(self) -> None:
        engine = _engine()
        with Session(engine) as session:
            seed_defaults(session, SETTINGS_REGISTRY)
            session.commit()
            row = session.get(AppDefaultModel, SETTING_KEY)
            assert row is not None
            assert row.description is not None  # type: ignore[operator]
            assert len(row.description) > 0  # type: ignore[arg-type]
