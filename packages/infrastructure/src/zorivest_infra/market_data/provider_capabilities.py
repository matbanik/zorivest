"""Provider capabilities registry — MEU-184.

Frozen dataclass lookup registry mapping each of the 11 API-key providers
to their URL construction mode, authentication mode, response shape,
supported data types, and free-tier rate limits.

Source: docs/build-plan/08a-market-data-expansion.md §8a.3
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class FreeTierConfig:
    """Free-tier rate limit configuration for a provider."""

    requests_per_minute: int | None
    requests_per_day: int | None
    history_depth_years: int | None
    delay_minutes: int  # 0 = real-time


@dataclass(frozen=True)
class ProviderCapabilities:
    """Structural metadata for a market data provider.

    Fields describe HOW to build URLs, authenticate, parse responses,
    and WHAT data types a provider supports. These are static facts
    about each provider's API design — not runtime configuration.
    """

    builder_mode: Literal["simple_get", "function_get", "dataset_get", "post_body"]
    auth_mode: Literal["header", "query", "bearer", "dual_header"]
    multi_symbol_style: Literal["csv", "repeated_filter", "body_array", "none"]
    pagination_style: Literal[
        "offset_limit", "next_page_token", "next_cursor_id", "next_url", "none"
    ]
    extractor_shape: Literal[
        "root_object",
        "root_array",
        "wrapper_array",
        "symbol_keyed_dict",
        "named_section_object",
        "parallel_arrays",
    ]
    supported_data_types: tuple[str, ...]
    free_tier: FreeTierConfig


# ── 11 API-key provider entries (§8a.3 table) ───────────────────────────

CAPABILITIES_REGISTRY: dict[str, ProviderCapabilities] = {
    "Alpha Vantage": ProviderCapabilities(
        builder_mode="function_get",
        auth_mode="query",
        multi_symbol_style="none",
        pagination_style="none",
        extractor_shape="named_section_object",
        supported_data_types=(
            "earnings",
            "economic_calendar",
            "fundamentals",
            "quote",
            "ticker_search",
        ),
        free_tier=FreeTierConfig(
            requests_per_minute=None,
            requests_per_day=25,
            history_depth_years=20,
            delay_minutes=0,
        ),
    ),
    "Polygon.io": ProviderCapabilities(
        builder_mode="simple_get",
        auth_mode="bearer",
        multi_symbol_style="csv",
        pagination_style="next_url",
        extractor_shape="wrapper_array",
        supported_data_types=(
            "dividends",
            "ohlcv",
            "quote",
            "splits",
        ),
        free_tier=FreeTierConfig(
            requests_per_minute=5,
            requests_per_day=None,
            history_depth_years=2,
            delay_minutes=15,
        ),
    ),
    "Finnhub": ProviderCapabilities(
        builder_mode="simple_get",
        auth_mode="header",
        multi_symbol_style="none",
        pagination_style="none",
        extractor_shape="parallel_arrays",
        supported_data_types=(
            "company_profile",
            "earnings",
            "economic_calendar",
            "insider",
            "news",
            "quote",
        ),
        free_tier=FreeTierConfig(
            requests_per_minute=60,
            requests_per_day=None,
            history_depth_years=None,
            delay_minutes=0,
        ),
    ),
    "Financial Modeling Prep": ProviderCapabilities(
        builder_mode="simple_get",
        auth_mode="query",
        multi_symbol_style="csv",
        pagination_style="offset_limit",
        extractor_shape="root_array",
        supported_data_types=(
            "company_profile",
            "dividends",
            "earnings",
            "economic_calendar",
            "fundamentals",
            "insider",
            "splits",
            "ticker_search",
        ),
        free_tier=FreeTierConfig(
            requests_per_minute=None,
            requests_per_day=250,
            history_depth_years=5,
            delay_minutes=0,
        ),
    ),
    "EODHD": ProviderCapabilities(
        builder_mode="simple_get",
        auth_mode="query",
        multi_symbol_style="csv",
        pagination_style="offset_limit",
        extractor_shape="root_object",
        supported_data_types=(
            "company_profile",
            "dividends",
            "fundamentals",
            "ohlcv",
            "quote",
            "splits",
        ),
        free_tier=FreeTierConfig(
            requests_per_minute=None,
            requests_per_day=20,
            history_depth_years=1,
            delay_minutes=15,
        ),
    ),
    "Nasdaq Data Link": ProviderCapabilities(
        builder_mode="dataset_get",
        auth_mode="query",
        multi_symbol_style="repeated_filter",
        pagination_style="next_cursor_id",
        extractor_shape="parallel_arrays",
        supported_data_types=("fundamentals",),
        free_tier=FreeTierConfig(
            requests_per_minute=300,
            requests_per_day=50_000,
            history_depth_years=None,
            delay_minutes=0,
        ),
    ),
    "SEC API": ProviderCapabilities(
        builder_mode="post_body",
        auth_mode="header",
        multi_symbol_style="body_array",
        pagination_style="offset_limit",
        extractor_shape="root_array",
        supported_data_types=("insider", "sec_filings"),
        free_tier=FreeTierConfig(
            requests_per_minute=None,
            requests_per_day=None,
            history_depth_years=None,
            delay_minutes=0,
        ),
    ),
    "API Ninjas": ProviderCapabilities(
        builder_mode="simple_get",
        auth_mode="header",
        multi_symbol_style="none",
        pagination_style="none",
        extractor_shape="root_object",
        supported_data_types=("quote",),
        free_tier=FreeTierConfig(
            requests_per_minute=None,
            requests_per_day=None,
            history_depth_years=None,
            delay_minutes=0,
        ),
    ),
    "OpenFIGI": ProviderCapabilities(
        builder_mode="post_body",
        auth_mode="header",
        multi_symbol_style="body_array",
        pagination_style="none",
        extractor_shape="root_array",
        supported_data_types=("identifier_mapping",),
        free_tier=FreeTierConfig(
            requests_per_minute=None,
            requests_per_day=None,
            history_depth_years=None,
            delay_minutes=0,
        ),
    ),
    "Alpaca": ProviderCapabilities(
        builder_mode="simple_get",
        auth_mode="dual_header",
        multi_symbol_style="csv",
        pagination_style="next_page_token",
        extractor_shape="symbol_keyed_dict",
        supported_data_types=("ohlcv",),
        free_tier=FreeTierConfig(
            requests_per_minute=200,
            requests_per_day=None,
            history_depth_years=7,
            delay_minutes=15,
        ),
    ),
    "Tradier": ProviderCapabilities(
        builder_mode="simple_get",
        auth_mode="bearer",
        multi_symbol_style="csv",
        pagination_style="none",
        extractor_shape="root_object",
        supported_data_types=("ohlcv", "quote"),
        free_tier=FreeTierConfig(
            requests_per_minute=120,
            requests_per_day=None,
            history_depth_years=None,
            delay_minutes=0,
        ),
    ),
}


def get_capabilities(name: str) -> ProviderCapabilities:
    """Look up a provider's capabilities by name.

    Args:
        name: Provider name (e.g. "Alpaca", "Finnhub").

    Returns:
        The ProviderCapabilities for the given name.

    Raises:
        KeyError: If no provider with that name exists.
    """
    try:
        return CAPABILITIES_REGISTRY[name]
    except KeyError:
        raise KeyError(
            f"Unknown market data provider: '{name}'. "
            f"Available: {', '.join(sorted(CAPABILITIES_REGISTRY))}"
        ) from None
