# packages/core/src/zorivest_core/services/emulator_budget.py
"""Session budget tracker for the policy emulator (§9F.2b).

Security controls:
    - MAX_BYTES_PER_SESSION: 64 KiB cumulative per policy-hash per session
    - MAX_CALLS_PER_MINUTE: 10 calls per policy-hash per rolling minute

Defeats chunked exfiltration (F35) by capping total bytes and rate.

Spec reference: 09f §9F.2a, §9F.2b
"""

from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass, field

from zorivest_core.services.sql_sandbox import SecurityError

MAX_BYTES_PER_SESSION = 64 * 1024  # 64 KiB
MAX_CALLS_PER_MINUTE = 10


@dataclass
class SessionBudget:
    """Tracks cumulative byte usage and rate per policy-hash per session."""

    _usage: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    _call_times: dict[str, list[float]] = field(
        default_factory=lambda: defaultdict(list)
    )

    def check_budget(self, policy_hash: str, response_bytes: int) -> None:
        """Check and record a call against the budget.

        Args:
            policy_hash: SHA-256 hash of the policy document.
            response_bytes: Size of the response payload in bytes.

        Raises:
            SecurityError: If rate limit or byte budget is exceeded.
        """
        # Rate limit check
        now = time.monotonic()
        recent = [t for t in self._call_times[policy_hash] if now - t < 60]
        if len(recent) >= MAX_CALLS_PER_MINUTE:
            raise SecurityError(
                f"Rate limit exceeded: {MAX_CALLS_PER_MINUTE} calls/min per policy"
            )
        self._call_times[policy_hash] = [*recent, now]

        # Byte budget check
        projected = self._usage[policy_hash] + response_bytes
        if projected > MAX_BYTES_PER_SESSION:
            raise SecurityError(
                f"Session byte budget exceeded: {projected} > {MAX_BYTES_PER_SESSION}"
            )
        self._usage[policy_hash] = projected

    def get_usage(self, policy_hash: str) -> int:
        """Return cumulative bytes used for a policy hash."""
        return self._usage[policy_hash]
