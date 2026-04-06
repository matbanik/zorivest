# packages/infrastructure/src/zorivest_infra/database/seed_system_account.py
"""Idempotent seeding of the System Reassignment Account.

Source: BUILD_PLAN.md §MEU-37, pomera note 732 (D1 — Human-approved)

Called at app startup after Base.metadata.create_all() to ensure the
SYSTEM_DEFAULT account exists for trade reassignment workflows.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from zorivest_infra.database.models import AccountModel

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def seed_system_account(session: Session) -> None:
    """Ensure the System Reassignment Account exists.

    Idempotent: safe to call multiple times. If the account already
    exists, no changes are made. If it does not exist, it is created
    with ``is_system=True`` so it is hidden from user-facing lists.

    Args:
        session: Active SQLAlchemy session (caller must commit).
    """
    existing = session.get(AccountModel, "SYSTEM_DEFAULT")
    if existing is None:
        session.add(
            AccountModel(
                account_id="SYSTEM_DEFAULT",
                name="System Reassignment Account",
                account_type="broker",
                institution="System",
                currency="USD",
                is_tax_advantaged=False,
                is_system=True,
                is_archived=False,
                notes="System account for orphaned trade reassignment. Do not delete.",
                created_at=datetime.now(timezone.utc),
            )
        )
