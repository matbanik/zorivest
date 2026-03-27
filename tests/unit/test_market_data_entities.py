"""Market data entity tests — MEU-56 acceptance criteria.

Tests written FIRST (Red phase) before any implementation exists.
All values from docs/build-plan/08-market-data.md §8.1a–§8.1d.
"""

from __future__ import annotations

import inspect
from dataclasses import FrozenInstanceError
from enum import StrEnum
from typing import Protocol

import pytest

pytestmark = pytest.mark.unit


# ── AC-1: AuthMethod StrEnum with 4 members ──────────────────────────────


class TestAuthMethodEnum:
    """AC-1 [Local Canon]: AuthMethod StrEnum defines exactly 4 members."""

    def test_auth_method_is_strenum(self) -> None:
        from zorivest_core.domain.enums import AuthMethod

        assert issubclass(AuthMethod, StrEnum)
        # Value: verify all members are strings with snake_case values
        for member in AuthMethod:
            assert isinstance(member.value, str)
            assert member.value == member.value.lower()

    def test_auth_method_has_exactly_4_members(self) -> None:
        from zorivest_core.domain.enums import AuthMethod

        assert len(AuthMethod) == 5

    def test_auth_method_query_param(self) -> None:
        from zorivest_core.domain.enums import AuthMethod

        assert AuthMethod.QUERY_PARAM.value == "query_param"

    def test_auth_method_bearer_header(self) -> None:
        from zorivest_core.domain.enums import AuthMethod

        assert AuthMethod.BEARER_HEADER.value == "bearer_header"

    def test_auth_method_custom_header(self) -> None:
        from zorivest_core.domain.enums import AuthMethod

        assert AuthMethod.CUSTOM_HEADER.value == "custom_header"

    def test_auth_method_raw_header(self) -> None:
        from zorivest_core.domain.enums import AuthMethod

        assert AuthMethod.RAW_HEADER.value == "raw_header"


# ── AC-2 through AC-6: ProviderConfig frozen dataclass ──────────────────


class TestProviderConfig:
    """AC-2–6 [Spec]: ProviderConfig is a frozen dataclass with 10 fields."""

    def test_provider_config_creation_all_fields(self) -> None:
        from zorivest_core.domain.enums import AuthMethod
        from zorivest_core.domain.market_data import ProviderConfig

        config = ProviderConfig(
            name="Alpha Vantage",
            base_url="https://www.alphavantage.co/query",
            auth_method=AuthMethod.QUERY_PARAM,
            auth_param_name="apikey",
            headers_template={},
            test_endpoint="/query?function=TIME_SERIES_INTRADAY",
            default_rate_limit=5,
            default_timeout=30,
            signup_url="https://www.alphavantage.co/support/#api-key",
            response_validator_key="Time Series (5min)",
        )
        assert config.name == "Alpha Vantage"
        assert config.auth_method == AuthMethod.QUERY_PARAM
        assert config.default_rate_limit == 5

    def test_provider_config_frozen(self) -> None:
        """AC-2: ProviderConfig must be frozen (immutable)."""
        from zorivest_core.domain.enums import AuthMethod
        from zorivest_core.domain.market_data import ProviderConfig

        config = ProviderConfig(
            name="test",
            base_url="https://example.com",
            auth_method=AuthMethod.QUERY_PARAM,
            auth_param_name="key",
            headers_template={},
            test_endpoint="/test",
            default_rate_limit=10,
        )
        with pytest.raises(FrozenInstanceError):
            config.name = "changed"  # type: ignore[misc]

    def test_provider_config_headers_template_dict(self) -> None:
        """AC-3: headers_template accepts dict[str, str]."""
        from zorivest_core.domain.enums import AuthMethod
        from zorivest_core.domain.market_data import ProviderConfig

        config = ProviderConfig(
            name="Finnhub",
            base_url="https://finnhub.io/api/v1",
            auth_method=AuthMethod.CUSTOM_HEADER,
            auth_param_name="X-Finnhub-Token",
            headers_template={"X-Finnhub-Token": "{api_key}"},
            test_endpoint="/stock/profile2",
            default_rate_limit=60,
        )
        assert isinstance(config.headers_template, dict)
        assert config.headers_template["X-Finnhub-Token"] == "{api_key}"

    def test_provider_config_default_timeout(self) -> None:
        """AC-4: default_timeout defaults to 30."""
        from zorivest_core.domain.enums import AuthMethod
        from zorivest_core.domain.market_data import ProviderConfig

        config = ProviderConfig(
            name="test",
            base_url="https://example.com",
            auth_method=AuthMethod.QUERY_PARAM,
            auth_param_name="key",
            headers_template={},
            test_endpoint="/test",
            default_rate_limit=10,
        )
        assert config.default_timeout == 30

    def test_provider_config_signup_url_default(self) -> None:
        """AC-5: signup_url defaults to empty string."""
        from zorivest_core.domain.enums import AuthMethod
        from zorivest_core.domain.market_data import ProviderConfig

        config = ProviderConfig(
            name="test",
            base_url="https://example.com",
            auth_method=AuthMethod.QUERY_PARAM,
            auth_param_name="key",
            headers_template={},
            test_endpoint="/test",
            default_rate_limit=10,
        )
        assert config.signup_url == ""

    def test_provider_config_response_validator_key_default(self) -> None:
        """AC-6: response_validator_key defaults to empty string."""
        from zorivest_core.domain.enums import AuthMethod
        from zorivest_core.domain.market_data import ProviderConfig

        config = ProviderConfig(
            name="test",
            base_url="https://example.com",
            auth_method=AuthMethod.QUERY_PARAM,
            auth_param_name="key",
            headers_template={},
            test_endpoint="/test",
            default_rate_limit=10,
        )
        assert config.response_validator_key == ""

    def test_provider_config_missing_required_field_raises(self) -> None:
        """Missing required field raises TypeError."""
        from zorivest_core.domain.market_data import ProviderConfig

        with pytest.raises(TypeError):
            ProviderConfig(name="test")  # type: ignore[call-arg]


# ── AC-7: MarketDataPort Protocol ────────────────────────────────────────


class TestMarketDataPort:
    """AC-7 [Spec]: MarketDataPort Protocol defines 4 async method signatures."""

    def test_market_data_port_is_protocol(self) -> None:
        from zorivest_core.application.ports import MarketDataPort

        assert issubclass(MarketDataPort, Protocol)
        # Value: verify exactly 4 public methods
        public_methods = {
            name
            for name, _ in inspect.getmembers(
                MarketDataPort, predicate=inspect.isfunction
            )
            if not name.startswith("_")
        }
        assert public_methods == {
            "get_quote",
            "get_news",
            "search_ticker",
            "get_sec_filings",
        }

    def test_market_data_port_has_get_quote(self) -> None:
        from zorivest_core.application.ports import MarketDataPort

        assert hasattr(MarketDataPort, "get_quote")
        sig = inspect.signature(MarketDataPort.get_quote)
        params = list(sig.parameters.keys())
        # Value: verify exact parameter names
        assert params == ["self", "ticker"], (
            f"Expected ['self', 'ticker'], got {params}"
        )

    def test_market_data_port_has_get_news(self) -> None:
        from zorivest_core.application.ports import MarketDataPort

        assert hasattr(MarketDataPort, "get_news")
        sig = inspect.signature(MarketDataPort.get_news)
        params = list(sig.parameters.keys())
        assert "ticker" in params
        assert "count" in params
        # Value: verify exact parameter set
        assert set(params) == {"self", "ticker", "count"}

    def test_market_data_port_has_search_ticker(self) -> None:
        from zorivest_core.application.ports import MarketDataPort

        assert hasattr(MarketDataPort, "search_ticker")
        sig = inspect.signature(MarketDataPort.search_ticker)
        params = list(sig.parameters.keys())
        # Value: verify exact parameter names
        assert params == ["self", "query"], f"Expected ['self', 'query'], got {params}"

    def test_market_data_port_has_get_sec_filings(self) -> None:
        from zorivest_core.application.ports import MarketDataPort

        assert hasattr(MarketDataPort, "get_sec_filings")
        sig = inspect.signature(MarketDataPort.get_sec_filings)
        params = list(sig.parameters.keys())
        # Value: verify exact parameter names
        assert params == ["self", "ticker"], (
            f"Expected ['self', 'ticker'], got {params}"
        )

    def test_market_data_port_methods_are_async(self) -> None:
        """All 4 methods should be coroutine functions."""
        from zorivest_core.application.ports import MarketDataPort

        for method_name in (
            "get_quote",
            "get_news",
            "search_ticker",
            "get_sec_filings",
        ):
            method = getattr(MarketDataPort, method_name)
            assert inspect.iscoroutinefunction(method), f"{method_name} should be async"

    def test_market_data_port_return_annotations(self) -> None:
        """Return annotations must reference actual DTO types, not Any."""
        import typing

        from zorivest_core.application.ports import MarketDataPort

        hints = typing.get_type_hints(MarketDataPort.get_quote)
        assert hints["return"].__name__ == "MarketQuote"

        hints = typing.get_type_hints(MarketDataPort.get_news)
        assert "list" in str(hints["return"]).lower()

        hints = typing.get_type_hints(MarketDataPort.search_ticker)
        assert "list" in str(hints["return"]).lower()

        hints = typing.get_type_hints(MarketDataPort.get_sec_filings)
        assert "list" in str(hints["return"]).lower()
