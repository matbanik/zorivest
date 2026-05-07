"""MEU-207: Capability wiring — normalizer injection + capability enrichment.

Tests verify:
  AC-1: NORMALIZERS dict injected as normalizers= kwarg in MarketDataService
        constructor in main.py
  AC-2: provider_capabilities.py supported_data_types updated to match
        Expected Capability Tuples table in implementation-plan.md
  AC-3: Every key in NORMALIZERS dict has a matching entry in
        supported_data_types for that provider (alignment invariant)
  AC-4: Existing Yahoo-first data types (ohlcv, fundamentals, dividends,
        splits) still work with Yahoo fallback + API-key chain
"""

from __future__ import annotations

import ast
import inspect
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from zorivest_infra.market_data.normalizers import (
    NORMALIZERS,
    QUOTE_NORMALIZERS,
    NEWS_NORMALIZERS,
    SEARCH_NORMALIZERS,
)
from zorivest_infra.market_data.provider_capabilities import (
    CAPABILITIES_REGISTRY,
)
from zorivest_core.services.market_data_service import MarketDataService


# ── AC-1: NORMALIZERS injection in main.py ──────────────────────────────


class TestNormalizerInjection:
    """AC-1: NORMALIZERS dict injected as normalizers= kwarg in main.py."""

    def test_main_py_imports_normalizers(self) -> None:
        """main.py imports NORMALIZERS from normalizers module."""
        main_path = (
            Path(__file__).resolve().parents[2]
            / "packages"
            / "api"
            / "src"
            / "zorivest_api"
            / "main.py"
        )
        source = main_path.read_text(encoding="utf-8")
        tree = ast.parse(source)

        # Find import of NORMALIZERS from the normalizers module
        found = False
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module and "normalizers" in node.module:
                    for alias in node.names:
                        if alias.name == "NORMALIZERS":
                            found = True
                            break
        assert found, (
            "main.py must import NORMALIZERS from "
            "zorivest_infra.market_data.normalizers"
        )

    def test_main_py_passes_normalizers_kwarg(self) -> None:
        """main.py passes normalizers=NORMALIZERS to MarketDataService()."""
        main_path = (
            Path(__file__).resolve().parents[2]
            / "packages"
            / "api"
            / "src"
            / "zorivest_api"
            / "main.py"
        )
        source = main_path.read_text(encoding="utf-8")
        # Check for the kwarg in the source text — the constructor call
        # should contain 'normalizers=NORMALIZERS'
        assert "normalizers=NORMALIZERS" in source, (
            "MarketDataService() constructor in main.py must include "
            "normalizers=NORMALIZERS kwarg"
        )

    def test_service_constructor_accepts_normalizers(self) -> None:
        """MarketDataService.__init__ has a 'normalizers' parameter."""
        sig = inspect.signature(MarketDataService.__init__)
        assert "normalizers" in sig.parameters, (
            "MarketDataService.__init__ must accept a 'normalizers' parameter"
        )

    def test_service_stores_normalizers(self) -> None:
        """MarketDataService stores injected normalizers dict."""
        mock_uow = MagicMock()
        mock_enc = MagicMock()
        mock_http = MagicMock()
        mock_limiters: dict = {}
        mock_registry: dict = {}

        svc = MarketDataService(
            uow=mock_uow,
            encryption=mock_enc,
            http_client=mock_http,
            rate_limiters=mock_limiters,
            provider_registry=mock_registry,
            normalizers=NORMALIZERS,
        )
        assert svc._normalizers == NORMALIZERS
        assert len(svc._normalizers) > 0, "NORMALIZERS must not be empty"


# ── AC-2: Expected Capability Tuples ────────────────────────────────────

# Expected tuples from the MEU-207 scope table in implementation-plan.md.
# Only the 8 normalizer-backed providers are set by MEU-207.
EXPECTED_TUPLES: dict[str, tuple[str, ...]] = {
    "Alpha Vantage": (
        "earnings",
        "economic_calendar",
        "fundamentals",
        "quote",
        "ticker_search",
    ),
    "Polygon.io": ("dividends", "ohlcv", "quote", "splits"),
    "Finnhub": (
        "company_profile",
        "earnings",
        "economic_calendar",
        "insider",
        "news",
        "quote",
    ),
    "Financial Modeling Prep": (
        "company_profile",
        "dividends",
        "earnings",
        "economic_calendar",
        "fundamentals",
        "insider",
        "splits",
        "ticker_search",
    ),
    "EODHD": (
        "company_profile",
        "dividends",
        "fundamentals",
        "ohlcv",
        "quote",
        "splits",
    ),
    "SEC API": ("insider", "sec_filings"),
    "API Ninjas": ("quote",),
    "Alpaca": ("ohlcv",),
}


class TestExpectedCapabilityTuples:
    """AC-2: supported_data_types match Expected Capability Tuples table."""

    @pytest.mark.parametrize(
        "provider,expected",
        list(EXPECTED_TUPLES.items()),
        ids=list(EXPECTED_TUPLES.keys()),
    )
    def test_provider_supported_data_types(
        self, provider: str, expected: tuple[str, ...]
    ) -> None:
        """Each provider's supported_data_types matches the plan table."""
        assert provider in CAPABILITIES_REGISTRY, (
            f"Provider '{provider}' must exist in CAPABILITIES_REGISTRY"
        )
        actual = CAPABILITIES_REGISTRY[provider].supported_data_types
        assert tuple(sorted(actual)) == tuple(sorted(expected)), (
            f"Provider '{provider}' supported_data_types mismatch.\n"
            f"  Expected: {expected}\n"
            f"  Actual:   {actual}"
        )


# ── AC-3: Normalizer-Capability Alignment Invariant ─────────────────────


class TestNormalizerCapabilityAlignment:
    """AC-3: Every normalizer registry entry has a matching capability."""

    def test_normalizers_have_matching_capabilities(self) -> None:
        """Every key in NORMALIZERS dict has matching supported_data_types."""
        missing: list[str] = []
        for data_type, providers in NORMALIZERS.items():
            for provider_name in providers:
                if provider_name not in CAPABILITIES_REGISTRY:
                    continue  # Provider not in registry — not our concern
                caps = CAPABILITIES_REGISTRY[provider_name]
                if data_type not in caps.supported_data_types:
                    missing.append(f"{provider_name}:{data_type}")

        assert not missing, (
            f"Normalizer exists but capability not advertised (dead code): {missing}"
        )

    def test_quote_normalizers_have_matching_capabilities(self) -> None:
        """Every QUOTE_NORMALIZERS provider advertises 'quote'."""
        missing: list[str] = []
        for provider_name in QUOTE_NORMALIZERS:
            if provider_name not in CAPABILITIES_REGISTRY:
                continue
            caps = CAPABILITIES_REGISTRY[provider_name]
            if "quote" not in caps.supported_data_types:
                missing.append(provider_name)

        assert not missing, (
            f"Quote normalizer exists but 'quote' not in "
            f"supported_data_types: {missing}"
        )

    def test_news_normalizers_have_matching_capabilities(self) -> None:
        """Every NEWS_NORMALIZERS provider advertises 'news'."""
        missing: list[str] = []
        for provider_name in NEWS_NORMALIZERS:
            if provider_name not in CAPABILITIES_REGISTRY:
                continue
            caps = CAPABILITIES_REGISTRY[provider_name]
            if "news" not in caps.supported_data_types:
                missing.append(provider_name)

        assert not missing, (
            f"News normalizer exists but 'news' not in supported_data_types: {missing}"
        )

    def test_search_normalizers_have_matching_capabilities(self) -> None:
        """Every SEARCH_NORMALIZERS provider advertises 'ticker_search'."""
        missing: list[str] = []
        for provider_name in SEARCH_NORMALIZERS:
            if provider_name not in CAPABILITIES_REGISTRY:
                continue
            caps = CAPABILITIES_REGISTRY[provider_name]
            if "ticker_search" not in caps.supported_data_types:
                missing.append(provider_name)

        assert not missing, (
            f"Search normalizer exists but 'ticker_search' not in "
            f"supported_data_types: {missing}"
        )


# ── AC-4: Yahoo-first Regression ────────────────────────────────────────


class TestYahooFirstRegression:
    """AC-4: Yahoo-first data types still work with fallback chain."""

    YAHOO_DATA_TYPES = frozenset({"ohlcv", "fundamentals", "dividends", "splits"})

    def test_yahoo_data_types_frozenset_exists(self) -> None:
        """MarketDataService._YAHOO_DATA_TYPES matches expected set."""
        assert hasattr(MarketDataService, "_YAHOO_DATA_TYPES"), (
            "MarketDataService must have _YAHOO_DATA_TYPES frozenset"
        )
        assert MarketDataService._YAHOO_DATA_TYPES == self.YAHOO_DATA_TYPES

    def test_each_yahoo_type_has_normalizer_providers(self) -> None:
        """Each Yahoo data type has at least one API-key provider normalizer
        in NORMALIZERS for fallback when Yahoo fails."""
        for data_type in self.YAHOO_DATA_TYPES:
            providers = NORMALIZERS.get(data_type, {})
            assert len(providers) > 0, (
                f"Yahoo data type '{data_type}' must have at least one "
                f"API-key provider normalizer in NORMALIZERS for fallback"
            )

    @pytest.mark.asyncio
    async def test_yahoo_failure_falls_through_to_api_provider(self) -> None:
        """When Yahoo fails, service falls through to API-key provider."""
        from unittest.mock import patch

        mock_uow = MagicMock()
        mock_enc = MagicMock()
        mock_http = MagicMock()
        mock_limiters: dict = {}
        # Need at least one "enabled" provider in the registry
        mock_provider_setting = MagicMock()
        mock_provider_setting.api_key_encrypted = b"test-key"
        mock_provider_setting.is_enabled = True
        mock_registry: dict = {}

        # Create a mock normalizer that returns test data
        mock_normalizer = MagicMock(return_value=[{"ticker": "TEST", "price": 100.0}])
        test_normalizers = {
            "ohlcv": {"TestProvider": mock_normalizer},
        }

        svc = MarketDataService(
            uow=mock_uow,
            encryption=mock_enc,
            http_client=mock_http,
            rate_limiters=mock_limiters,
            provider_registry=mock_registry,
            normalizers=test_normalizers,
        )

        # Mock Yahoo to fail
        with (
            patch.object(svc, "_yahoo_ohlcv", side_effect=Exception("Yahoo down")),
            patch.object(
                svc,
                "_get_enabled_providers",
                return_value=[("TestProvider", mock_provider_setting)],
            ),
            patch.object(
                svc,
                "_generic_api_fetch",
                new_callable=AsyncMock,
                return_value={"data": "raw"},
            ),
        ):
            result = await svc._fetch_data_type("ohlcv", "TEST")

        # Verify the normalizer was called (fallback path reached)
        mock_normalizer.assert_called_once()
        assert result == [{"ticker": "TEST", "price": 100.0}]
