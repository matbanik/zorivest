# packages/infrastructure/src/zorivest_infra/database/seed_defaults.py
"""Idempotent seeding of AppDefaultModel from the canonical SETTINGS_REGISTRY.

Source: 02a-backup-restore.md §2A.1

Called at app startup after Base.metadata.create_all() to ensure the
app_defaults table contains all registry entries with correct values.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from zorivest_infra.database.models import AppDefaultModel

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from zorivest_core.domain.settings import SettingSpec


def seed_defaults(
    session: Session,
    registry: dict[str, SettingSpec],
) -> None:
    """Populate or update app_defaults table from the settings registry.

    Idempotent: safe to call multiple times. Existing rows are updated
    to match current registry values (handles spec evolution across versions).

    Args:
        session: Active SQLAlchemy session (caller must commit).
        registry: The canonical SETTINGS_REGISTRY dict.
    """
    now = datetime.now(timezone.utc)

    for key, spec in registry.items():
        existing = session.get(AppDefaultModel, key)

        if existing is None:
            # New entry — insert
            row = AppDefaultModel(
                key=key,
                value=str(spec.hardcoded_default),
                value_type=spec.value_type,
                category=spec.category,
                description=spec.description or None,
                updated_at=now,
            )
            session.add(row)
        else:
            # Existing entry — update to match current registry
            existing.value = str(spec.hardcoded_default)  # type: ignore[assignment]
            existing.value_type = spec.value_type  # type: ignore[assignment]
            existing.category = spec.category  # type: ignore[assignment]
            existing.description = spec.description or None  # type: ignore[assignment]
            existing.updated_at = now  # type: ignore[assignment]
