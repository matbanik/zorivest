# tests/unit/test_emulator_budget.py
"""RED phase tests for SessionBudget — AC-12..AC-15 (09f §9F.2b).

Tests:
  - AC-12: Cumulative byte tracking per policy hash
  - AC-13: >64 KiB raises SecurityError
  - AC-14: >10 calls/min raises SecurityError
  - AC-15: Different policy hashes have independent budgets
"""

from __future__ import annotations

import pytest

from zorivest_core.services.emulator_budget import (
    MAX_BYTES_PER_SESSION,
    MAX_CALLS_PER_MINUTE,
    SessionBudget,
)
from zorivest_core.services.sql_sandbox import SecurityError


# ---------------------------------------------------------------------------
# AC-12: SessionBudget tracks cumulative bytes per policy hash
# ---------------------------------------------------------------------------


class TestBudgetTrackBytes:
    """AC-12: Cumulative bytes tracked per policy hash."""

    def test_budget_tracks_bytes(self) -> None:
        budget = SessionBudget()
        policy_hash = "abc123"

        # First call: 1000 bytes
        budget.check_budget(policy_hash, 1000)
        assert budget.get_usage(policy_hash) == 1000

        # Second call: 2000 bytes more
        budget.check_budget(policy_hash, 2000)
        assert budget.get_usage(policy_hash) == 3000


# ---------------------------------------------------------------------------
# AC-13: >64 KiB cumulative raises SecurityError
# ---------------------------------------------------------------------------


class TestBudgetRejectsOverLimit:
    """AC-13: Exceeding 64 KiB raises SecurityError."""

    def test_budget_rejects_over_limit(self) -> None:
        budget = SessionBudget()
        policy_hash = "abc123"

        # Use most of the budget
        budget.check_budget(policy_hash, MAX_BYTES_PER_SESSION - 100)

        # Next call pushes over the limit
        with pytest.raises(SecurityError, match="budget exceeded"):
            budget.check_budget(policy_hash, 200)

    def test_budget_exactly_at_limit_passes(self) -> None:
        budget = SessionBudget()
        policy_hash = "abc123"

        # Exactly at limit should NOT raise
        budget.check_budget(policy_hash, MAX_BYTES_PER_SESSION)
        assert budget.get_usage(policy_hash) == MAX_BYTES_PER_SESSION


# ---------------------------------------------------------------------------
# AC-14: >10 calls/min per policy hash raises SecurityError
# ---------------------------------------------------------------------------


class TestRateLimitEnforced:
    """AC-14: >10 calls/min per policy hash raises SecurityError."""

    def test_rate_limit_enforced(self) -> None:
        budget = SessionBudget()
        policy_hash = "rate-test"

        # Make 10 calls — should succeed
        for _ in range(MAX_CALLS_PER_MINUTE):
            budget.check_budget(policy_hash, 1)

        # 11th call should fail
        with pytest.raises(SecurityError, match="[Rr]ate limit"):
            budget.check_budget(policy_hash, 1)


# ---------------------------------------------------------------------------
# AC-15: Different policy hashes have independent budgets
# ---------------------------------------------------------------------------


class TestBudgetPerPolicyHash:
    """AC-15: Different policy hashes have independent budgets."""

    def test_budget_per_policy_hash(self) -> None:
        budget = SessionBudget()
        hash_a = "policy-a"
        hash_b = "policy-b"

        # Exhaust hash_a's budget
        budget.check_budget(hash_a, MAX_BYTES_PER_SESSION)

        # hash_b should still have full budget
        budget.check_budget(hash_b, 1000)
        assert budget.get_usage(hash_b) == 1000

    def test_rate_limit_per_policy_hash(self) -> None:
        budget = SessionBudget()
        hash_a = "rate-a"
        hash_b = "rate-b"

        # Exhaust rate limit for hash_a
        for _ in range(MAX_CALLS_PER_MINUTE):
            budget.check_budget(hash_a, 1)

        # hash_b should still allow calls
        budget.check_budget(hash_b, 1)  # Should not raise
