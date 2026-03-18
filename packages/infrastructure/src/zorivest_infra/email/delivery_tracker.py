# packages/infrastructure/src/zorivest_infra/email/delivery_tracker.py
"""SHA-256 delivery deduplication (§9.8c).

Computes a deterministic dedup key from delivery parameters to prevent
duplicate sends of the same report to the same recipient.
"""

from __future__ import annotations

import hashlib


def compute_dedup_key(
    *,
    report_id: str,
    channel: str,
    recipient: str,
    snapshot_hash: str,
) -> str:
    """Compute a deterministic SHA-256 dedup key.

    Key = SHA-256("{report_id}|{channel}|{recipient}|{snapshot_hash}")

    Returns:
        64-character lowercase hex string.
    """
    payload = f"{report_id}|{channel}|{recipient}|{snapshot_hash}"
    return hashlib.sha256(payload.encode()).hexdigest()
