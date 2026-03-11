"""Market data domain types — MEU-56.

Source: docs/build-plan/08-market-data.md §8.1b.
"""

from __future__ import annotations

from dataclasses import dataclass

from zorivest_core.domain.enums import AuthMethod


@dataclass(frozen=True)
class ProviderConfig:
    """Immutable configuration for a market data API provider."""

    name: str
    base_url: str
    auth_method: AuthMethod
    auth_param_name: str
    headers_template: dict[str, str]
    test_endpoint: str
    default_rate_limit: int
    default_timeout: int = 30
    signup_url: str = ""
    response_validator_key: str = ""
