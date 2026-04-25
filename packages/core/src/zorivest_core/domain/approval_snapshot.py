# packages/core/src/zorivest_core/domain/approval_snapshot.py
"""ApprovalSnapshot — runtime approval provenance for pipeline execution (§9C.3c).

Frozen dataclass created from PolicyModel approval fields at pipeline run
start. Injected into StepContext for SendStep confirmation gate checks.

Source: 09c-pipeline-security-hardening.md §9C.3c
Human-approved: Reuses existing PolicyModel fields (content_hash, approved_hash,
approved_at) via runtime snapshot — no second persistent store.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ApprovalSnapshot:
    """Immutable snapshot of policy approval state at execution time.

    Fields mirror PolicyModel columns:
    - approved: Whether the policy is approved for execution.
    - approved_hash: The content_hash value at the time of approval.
    - approved_at: Timestamp when approval was granted.
    """

    approved: bool
    approved_hash: str | None
    approved_at: datetime | None
