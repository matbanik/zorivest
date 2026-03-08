"""Trade identity functions — fingerprint hashing for deduplication.

Source: 03-service-layer.md §TradeFingerprint
"""

from __future__ import annotations

import hashlib

from zorivest_core.domain.entities import Trade


def trade_fingerprint(trade: Trade) -> str:
    """Compute a deterministic SHA-256 fingerprint from core trade fields.

    The fingerprint is based on: instrument, action, quantity, price,
    account_id, and time. The exec_id is intentionally excluded because
    duplicate detection needs to identify trades with different exec_ids
    but identical economic parameters.

    Returns:
        64-character lowercase hex string (SHA-256 digest).
    """
    payload = (
        f"{trade.instrument}|"
        f"{trade.action.value}|"
        f"{trade.quantity}|"
        f"{trade.price}|"
        f"{trade.account_id}|"
        f"{trade.time.isoformat()}"
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
