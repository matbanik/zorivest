"""ProviderStatus DTO — MEU-60.

Typed response model for list_providers().
Source: docs/build-plan/08-market-data.md §8.6, 06f-gui-settings.md L65-72.
"""

from __future__ import annotations

from pydantic import BaseModel


class ProviderStatus(BaseModel):
    """Status information for a single market data provider.

    Mirrors the TypeScript ``ProviderStatus`` interface from
    the GUI settings spec (06f-gui-settings.md).
    """

    provider_name: str
    is_enabled: bool
    has_api_key: bool
    rate_limit: int
    timeout: int
    last_test_status: str | None = None
    signup_url: str | None = None
