"""Tests for provider registry — MEU-59 + MEU-90b.

FIC-59 acceptance criteria (updated MEU-90b to reflect 14-provider reality):
AC-1: PROVIDER_REGISTRY has exactly 14 entries (12 API-key + 2 free)
AC-2: Each API-key provider entry has all required fields populated
AC-3: Provider names match the full known set exactly (closed set)
AC-4: get_provider_config returns config or raises KeyError
AC-5: list_provider_names returns sorted list of 14 names
AC-6: Auth methods match spec per API-key provider
AC-7: Free providers (Yahoo Finance, TradingView) are registered with AuthMethod.NONE
"""

from __future__ import annotations

import pytest

from zorivest_core.domain.enums import AuthMethod
from zorivest_core.domain.market_data import ProviderConfig
from zorivest_infra.market_data.provider_registry import (
    PROVIDER_REGISTRY,
    get_provider_config,
    list_provider_names,
)

# ── MEU-59 canonical API-key providers (spec §8.2c) ──

EXPECTED_NAMES = sorted(
    [
        "Alpha Vantage",
        "Polygon.io",
        "Finnhub",
        "Financial Modeling Prep",
        "EODHD",
        "Nasdaq Data Link",
        "SEC API",
        "API Ninjas",
        "Benzinga",
        "OpenFIGI",
        "Alpaca",
        "Tradier",
    ]
)

# ── MEU-65 free providers (GUI-layer, no API key required) ──

FREE_PROVIDER_NAMES = sorted(
    [
        "TradingView",
        "Yahoo Finance",
    ]
)

# ── Expected auth methods per API-key provider (spec §8.2c + §8.7) ──

EXPECTED_AUTH_METHODS: dict[str, AuthMethod] = {
    "Alpha Vantage": AuthMethod.QUERY_PARAM,
    "Polygon.io": AuthMethod.BEARER_HEADER,
    "Finnhub": AuthMethod.CUSTOM_HEADER,
    "Financial Modeling Prep": AuthMethod.QUERY_PARAM,
    "EODHD": AuthMethod.QUERY_PARAM,
    "Nasdaq Data Link": AuthMethod.QUERY_PARAM,
    "SEC API": AuthMethod.RAW_HEADER,
    "API Ninjas": AuthMethod.CUSTOM_HEADER,
    "Benzinga": AuthMethod.QUERY_PARAM,
    "OpenFIGI": AuthMethod.CUSTOM_HEADER,
    "Alpaca": AuthMethod.CUSTOM_HEADER,
    "Tradier": AuthMethod.BEARER_HEADER,
}


class TestProviderRegistryAC1:
    """AC-1: PROVIDER_REGISTRY has exactly 14 entries (12 API-key + 2 free)."""

    def test_registry_count(self) -> None:
        assert len(PROVIDER_REGISTRY) == len(EXPECTED_NAMES) + len(FREE_PROVIDER_NAMES)

    def test_registry_is_dict(self) -> None:
        assert isinstance(PROVIDER_REGISTRY, dict)
        # Value: verify dict keys are all strings
        assert all(isinstance(k, str) for k in PROVIDER_REGISTRY.keys())

    def test_all_values_are_provider_config(self) -> None:
        for name, config in PROVIDER_REGISTRY.items():
            assert isinstance(config, ProviderConfig), f"{name} is not ProviderConfig"
            # Value: verify each config has a non-empty name
            assert config.name == name


class TestProviderRegistryAC2:
    """AC-2: Each API-key provider entry has all required fields populated."""

    @pytest.mark.parametrize("name", EXPECTED_NAMES)
    def test_provider_has_non_empty_base_url(self, name: str) -> None:
        config = PROVIDER_REGISTRY[name]
        assert config.base_url, f"{name} has empty base_url"

    @pytest.mark.parametrize("name", EXPECTED_NAMES)
    def test_provider_has_non_empty_test_endpoint(self, name: str) -> None:
        config = PROVIDER_REGISTRY[name]
        assert config.test_endpoint, f"{name} has empty test_endpoint"

    @pytest.mark.parametrize("name", EXPECTED_NAMES)
    def test_provider_has_non_empty_auth_param_name(self, name: str) -> None:
        config = PROVIDER_REGISTRY[name]
        assert config.auth_param_name, f"{name} has empty auth_param_name"

    @pytest.mark.parametrize("name", EXPECTED_NAMES)
    def test_provider_has_positive_rate_limit(self, name: str) -> None:
        config = PROVIDER_REGISTRY[name]
        assert config.default_rate_limit > 0, f"{name} has non-positive rate limit"

    @pytest.mark.parametrize("name", EXPECTED_NAMES)
    def test_provider_name_matches_key(self, name: str) -> None:
        config = PROVIDER_REGISTRY[name]
        assert config.name == name, f"Key '{name}' != config.name '{config.name}'"


class TestProviderRegistryAC3:
    """AC-3: Provider names match the full known set exactly (closed contract)."""

    def test_all_expected_names_present(self) -> None:
        actual_set = set(PROVIDER_REGISTRY.keys())
        expected_set = set(EXPECTED_NAMES) | set(FREE_PROVIDER_NAMES)
        assert actual_set == expected_set

    def test_no_unexpected_names(self) -> None:
        actual_set = set(PROVIDER_REGISTRY.keys())
        known_set = set(EXPECTED_NAMES) | set(FREE_PROVIDER_NAMES)
        unexpected = actual_set - known_set
        assert not unexpected, f"Unexpected providers: {unexpected}"


class TestGetProviderConfigAC4:
    """AC-4: get_provider_config returns config or raises KeyError."""

    def test_returns_provider_config_for_known(self) -> None:
        config = get_provider_config("Alpha Vantage")
        assert isinstance(config, ProviderConfig)
        assert config.name == "Alpha Vantage"

    def test_returns_correct_config(self) -> None:
        config = get_provider_config("Finnhub")
        assert config.auth_method == AuthMethod.CUSTOM_HEADER

    def test_raises_key_error_for_unknown(self) -> None:
        with pytest.raises(KeyError, match="Unknown market data provider"):
            get_provider_config("NonexistentProvider")


class TestListProviderNamesAC5:
    """AC-5: list_provider_names returns sorted list of 14 names (12 API-key + 2 free)."""

    def test_returns_sorted_list(self) -> None:
        names = list_provider_names()
        assert names == sorted(names)

    def test_returns_14_names(self) -> None:
        names = list_provider_names()
        assert len(names) == len(EXPECTED_NAMES) + len(FREE_PROVIDER_NAMES)

    def test_matches_expected_names(self) -> None:
        names = list_provider_names()
        assert set(names) == set(EXPECTED_NAMES) | set(FREE_PROVIDER_NAMES)


class TestAuthMethodsAC6:
    """AC-6: Auth methods match spec per API-key provider."""

    @pytest.mark.parametrize(
        "provider_name,expected_auth",
        list(EXPECTED_AUTH_METHODS.items()),
    )
    def test_auth_method_matches_spec(
        self, provider_name: str, expected_auth: AuthMethod
    ) -> None:
        config = PROVIDER_REGISTRY[provider_name]
        assert config.auth_method == expected_auth, (
            f"{provider_name}: expected {expected_auth}, got {config.auth_method}"
        )


class TestFreeProvidersAC7:
    """AC-7: Free providers (MEU-65) are registered with AuthMethod.NONE."""

    @pytest.mark.parametrize("name", FREE_PROVIDER_NAMES)
    def test_free_provider_is_in_registry(self, name: str) -> None:
        assert name in PROVIDER_REGISTRY, f"Free provider '{name}' not in registry"

    @pytest.mark.parametrize("name", FREE_PROVIDER_NAMES)
    def test_free_provider_has_none_auth(self, name: str) -> None:
        config = PROVIDER_REGISTRY[name]
        assert config.auth_method == AuthMethod.NONE, (
            f"{name}: expected AuthMethod.NONE, got {config.auth_method}"
        )

    @pytest.mark.parametrize("name", FREE_PROVIDER_NAMES)
    def test_free_provider_is_provider_config(self, name: str) -> None:
        config = PROVIDER_REGISTRY[name]
        assert isinstance(config, ProviderConfig)
        assert config.name == name
