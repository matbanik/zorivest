"""Core-owned market provider settings entity.

Mirrors the ORM ``MarketProviderSettingModel`` but lives in core/domain
so that port protocols and services never import from infrastructure.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class MarketProviderSettings:
    """Persisted provider configuration and test status.

    This is the core-layer representation. The infrastructure layer maps
    it to/from ``MarketProviderSettingModel`` (SQLAlchemy ORM).
    """

    provider_name: str
    encrypted_api_key: str | None = None
    encrypted_api_secret: str | None = None
    rate_limit: int = 5
    timeout: int = 30
    is_enabled: bool = False
    last_tested_at: datetime | None = None
    last_test_status: str | None = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime | None = None
