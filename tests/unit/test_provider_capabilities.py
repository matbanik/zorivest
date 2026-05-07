"""Tests for provider capabilities registry — MEU-184.

FIC-184 acceptance criteria:
AC-1: ProviderCapabilities frozen dataclass with 7 fields
AC-2: FreeTierConfig frozen dataclass with 4 fields
AC-3: Registry contains exactly 11 entries
AC-4: Each provider's builder_mode matches spec table
AC-5: Each provider's extractor_shape matches spec table
AC-6: Each provider's supported_data_types matches spec table
AC-7: Free tier config values match verified 2026 rate limits
AC-8: get_capabilities(name) returns correct ProviderCapabilities
AC-9: get_capabilities(name) for unknown provider raises KeyError
"""

from __future__ import annotations

import dataclasses

import pytest

from zorivest_infra.market_data.provider_capabilities import (
    CAPABILITIES_REGISTRY,
    FreeTierConfig,
    ProviderCapabilities,
    get_capabilities,
)


# ── Expected Provider Names (from spec §8a.3) ──────────────────────────

EXPECTED_PROVIDERS = sorted(
    [
        "Alpha Vantage",
        "Polygon.io",
        "Finnhub",
        "Financial Modeling Prep",
        "EODHD",
        "Nasdaq Data Link",
        "SEC API",
        "API Ninjas",
        "OpenFIGI",
        "Alpaca",
        "Tradier",
    ]
)

# ── Expected builder_mode per provider (from spec §8a.3 table) ─────────

EXPECTED_BUILDER_MODES = {
    "Alpha Vantage": "function_get",
    "Polygon.io": "simple_get",
    "Finnhub": "simple_get",
    "Financial Modeling Prep": "simple_get",
    "EODHD": "simple_get",
    "Nasdaq Data Link": "dataset_get",
    "SEC API": "post_body",
    "API Ninjas": "simple_get",
    "OpenFIGI": "post_body",
    "Alpaca": "simple_get",
    "Tradier": "simple_get",
}

# Expected supported_data_types per provider.
# MEU-207 updated 8 normalizer-backed providers; 3 structural providers
# (Nasdaq Data Link, OpenFIGI, Tradier) carry forward from MEU-184.
EXPECTED_DATA_TYPES = {
    "Alpha Vantage": sorted(
        ["quote", "earnings", "fundamentals", "economic_calendar", "ticker_search"]
    ),
    "Polygon.io": sorted(["quote", "ohlcv", "dividends", "splits"]),
    "Finnhub": sorted(
        ["quote", "news", "earnings", "insider", "economic_calendar", "company_profile"]
    ),
    "Financial Modeling Prep": sorted(
        [
            "fundamentals",
            "earnings",
            "dividends",
            "splits",
            "insider",
            "economic_calendar",
            "company_profile",
            "ticker_search",
        ]
    ),
    "EODHD": sorted(
        ["ohlcv", "fundamentals", "dividends", "splits", "quote", "company_profile"]
    ),
    "Nasdaq Data Link": sorted(["fundamentals"]),
    "SEC API": sorted(["insider", "sec_filings"]),
    "API Ninjas": sorted(["quote"]),
    "OpenFIGI": sorted(["identifier_mapping"]),
    "Alpaca": sorted(["ohlcv"]),
    "Tradier": sorted(["quote", "ohlcv"]),
}


# ── AC-1: ProviderCapabilities frozen dataclass ────────────────────────


class TestProviderCapabilitiesDataclass:
    """AC-1: ProviderCapabilities frozen dataclass with 7 fields."""

    def test_is_dataclass(self) -> None:
        assert dataclasses.is_dataclass(ProviderCapabilities)

    def test_field_count(self) -> None:
        fields = dataclasses.fields(ProviderCapabilities)
        assert len(fields) == 7

    def test_field_names(self) -> None:
        field_names = {f.name for f in dataclasses.fields(ProviderCapabilities)}
        expected = {
            "builder_mode",
            "auth_mode",
            "multi_symbol_style",
            "pagination_style",
            "extractor_shape",
            "supported_data_types",
            "free_tier",
        }
        assert field_names == expected

    def test_frozen(self) -> None:
        cap = get_capabilities("Alpaca")
        with pytest.raises(dataclasses.FrozenInstanceError):
            cap.builder_mode = "post_body"  # type: ignore[misc]


# ── AC-2: FreeTierConfig frozen dataclass ──────────────────────────────


class TestFreeTierConfigDataclass:
    """AC-2: FreeTierConfig frozen dataclass with 4 fields."""

    def test_is_dataclass(self) -> None:
        assert dataclasses.is_dataclass(FreeTierConfig)

    def test_field_count(self) -> None:
        fields = dataclasses.fields(FreeTierConfig)
        assert len(fields) == 4

    def test_field_names(self) -> None:
        field_names = {f.name for f in dataclasses.fields(FreeTierConfig)}
        expected = {
            "requests_per_minute",
            "requests_per_day",
            "history_depth_years",
            "delay_minutes",
        }
        assert field_names == expected

    def test_frozen(self) -> None:
        ft = FreeTierConfig(
            requests_per_minute=60,
            requests_per_day=None,
            history_depth_years=5,
            delay_minutes=0,
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            ft.delay_minutes = 15  # type: ignore[misc]


# ── AC-3: Registry completeness ───────────────────────────────────────


class TestRegistryCompleteness:
    """AC-3: Registry contains exactly 11 entries."""

    def test_registry_has_11_entries(self) -> None:
        assert len(CAPABILITIES_REGISTRY) == 11

    def test_all_expected_providers_present(self) -> None:
        actual = sorted(CAPABILITIES_REGISTRY.keys())
        assert actual == EXPECTED_PROVIDERS

    def test_all_entries_are_provider_capabilities(self) -> None:
        for name, cap in CAPABILITIES_REGISTRY.items():
            assert isinstance(cap, ProviderCapabilities), (
                f"{name} is not a ProviderCapabilities instance"
            )


# ── AC-4: builder_mode matches spec ───────────────────────────────────


class TestBuilderModes:
    """AC-4: Each provider's builder_mode matches spec table."""

    @pytest.mark.parametrize("provider,expected_mode", EXPECTED_BUILDER_MODES.items())
    def test_builder_mode(self, provider: str, expected_mode: str) -> None:
        cap = get_capabilities(provider)
        assert cap.builder_mode == expected_mode, (
            f"{provider}: expected builder_mode={expected_mode}, got {cap.builder_mode}"
        )


# ── AC-5: extractor_shape matches spec ─────────────────────────────────


class TestExtractorShapes:
    """AC-5: Each provider's extractor_shape matches spec table."""

    def test_alpha_vantage_shape(self) -> None:
        assert (
            get_capabilities("Alpha Vantage").extractor_shape == "named_section_object"
        )

    def test_polygon_shape(self) -> None:
        assert get_capabilities("Polygon.io").extractor_shape == "wrapper_array"

    def test_fmp_shape(self) -> None:
        assert (
            get_capabilities("Financial Modeling Prep").extractor_shape == "root_array"
        )

    def test_eodhd_shape(self) -> None:
        # EODHD has root_object / root_array — primary shape is root_object
        cap = get_capabilities("EODHD")
        assert cap.extractor_shape in ("root_object", "root_array")

    def test_nasdaq_shape(self) -> None:
        assert get_capabilities("Nasdaq Data Link").extractor_shape == "parallel_arrays"

    def test_sec_api_shape(self) -> None:
        assert get_capabilities("SEC API").extractor_shape == "root_array"

    def test_api_ninjas_shape(self) -> None:
        assert get_capabilities("API Ninjas").extractor_shape == "root_object"

    def test_openfigi_shape(self) -> None:
        assert get_capabilities("OpenFIGI").extractor_shape == "root_array"

    def test_tradier_shape(self) -> None:
        assert get_capabilities("Tradier").extractor_shape == "root_object"


# ── AC-6: supported_data_types matches spec ────────────────────────────


class TestSupportedDataTypes:
    """AC-6: Each provider's supported_data_types matches spec table."""

    @pytest.mark.parametrize("provider,expected_types", EXPECTED_DATA_TYPES.items())
    def test_supported_data_types(
        self, provider: str, expected_types: list[str]
    ) -> None:
        cap = get_capabilities(provider)
        actual = sorted(cap.supported_data_types)
        assert actual == expected_types, (
            f"{provider}: expected {expected_types}, got {actual}"
        )


# ── AC-7: Free tier config values ─────────────────────────────────────


class TestFreeTierValues:
    """AC-7: Free tier config values match verified 2026 rate limits."""

    def test_alpaca_free_tier(self) -> None:
        ft = get_capabilities("Alpaca").free_tier
        assert ft.requests_per_minute == 200
        assert ft.delay_minutes == 15  # IEX feed, 15-min delay

    def test_alpha_vantage_free_tier(self) -> None:
        ft = get_capabilities("Alpha Vantage").free_tier
        assert ft.requests_per_day == 25

    def test_finnhub_free_tier(self) -> None:
        ft = get_capabilities("Finnhub").free_tier
        assert ft.requests_per_minute == 60

    def test_polygon_free_tier(self) -> None:
        ft = get_capabilities("Polygon.io").free_tier
        assert ft.requests_per_minute == 5

    def test_fmp_free_tier(self) -> None:
        ft = get_capabilities("Financial Modeling Prep").free_tier
        assert ft.requests_per_day == 250

    def test_all_providers_have_free_tier(self) -> None:
        for name, cap in CAPABILITIES_REGISTRY.items():
            assert isinstance(cap.free_tier, FreeTierConfig), (
                f"{name} missing FreeTierConfig"
            )


# ── AC-8 / AC-9: get_capabilities lookup ──────────────────────────────


class TestGetCapabilities:
    """AC-8/AC-9: get_capabilities lookup."""

    def test_known_provider(self) -> None:
        """AC-8: Returns correct ProviderCapabilities for known provider."""
        cap = get_capabilities("Alpaca")
        assert isinstance(cap, ProviderCapabilities)
        assert cap.builder_mode == "simple_get"

    def test_unknown_provider_raises(self) -> None:
        """AC-9: Unknown provider raises KeyError."""
        with pytest.raises(KeyError):
            get_capabilities("Unknown Provider")


# ── AC-10: Immutability guarantee (regression for F1) ─────────────────


class TestImmutabilityGuarantee:
    """AC-10: supported_data_types must be immutable to prevent registry corruption."""

    def test_supported_data_types_is_tuple(self) -> None:
        """supported_data_types must be a tuple, not a mutable list."""
        cap = get_capabilities("Alpaca")
        assert isinstance(cap.supported_data_types, tuple)

    def test_mutation_attempt_raises_type_error(self) -> None:
        """Appending to supported_data_types must raise TypeError."""
        cap = get_capabilities("Alpaca")
        with pytest.raises(AttributeError):
            cap.supported_data_types.append("mutated")  # type: ignore[union-attr]

    def test_global_registry_not_corrupted_after_lookup(self) -> None:
        """Two successive lookups must return identical supported_data_types."""
        original = get_capabilities("Alpaca").supported_data_types
        _ = get_capabilities("Alpaca")
        assert get_capabilities("Alpaca").supported_data_types == original
