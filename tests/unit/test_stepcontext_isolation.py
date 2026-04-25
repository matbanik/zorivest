"""Test StepContext deep-copy isolation (MEU-PH1).

Feature Intent Contract
=======================

Intent: StepContext must return isolated deep copies from get_output()
and store isolated deep copies via put_output(). The Secret carrier class
must block stringification and deep-copying to prevent credential leakage.

Acceptance Criteria:
    AC-1.1: get_output() returns a deep copy, not a reference       [Spec §9C.1b]
    AC-1.2: put_output() stores a deep copy                        [Spec §9C.1b]
    AC-1.3: Secret blocks str(), format(), deepcopy()               [Spec §9C.1b]
    AC-1.4: Secret.reveal() returns the original value              [Spec §9C.1b]
    AC-1.5: safe_deepcopy rejects objects exceeding 10 MB           [Spec §9C.1c]
    AC-1.6: safe_deepcopy rejects nesting > 64 levels               [Spec §9C.1c]
    AC-1.7: safe_deepcopy handles circular references               [Spec §9C.1c]
    AC-1.8: Nested objects containing Secret raise on deepcopy      [Spec §9C.1c]
    AC-1.9: PipelineRunner uses put_output() for all step results   [Spec §9C.1b]

Negative Cases:
    - Mutating returned output must NOT affect stored value
    - Mutating original after put must NOT affect stored value
    - Secret must NOT be convertible to string via str() or format()
    - Secret must NOT survive deepcopy

Test Mapping:
    AC-1.1 → test_get_output_returns_isolated_copy
    AC-1.2 → test_put_stores_isolated_copy
    AC-1.3 → test_secret_blocks_stringify, test_secret_blocks_format
    AC-1.4 → test_secret_reveal
    AC-1.5 → test_safe_deepcopy_rejects_oversized
    AC-1.6 → test_safe_deepcopy_rejects_deep_nesting
    AC-1.7 → test_safe_deepcopy_handles_cycles
    AC-1.8 → test_safe_deepcopy_secret_in_nested_obj
    AC-1.9 → test_runner_uses_put_output (integration, verifies no direct assignment)
"""

import copy
import pytest

from zorivest_core.services.safe_copy import Secret, safe_deepcopy
from zorivest_core.domain.pipeline import StepContext


# ---------------------------------------------------------------------------
# AC-1.1: get_output() returns a deep copy, not a reference
# ---------------------------------------------------------------------------


class TestGetOutputIsolation:
    """AC-1.1: Mutating returned value does NOT change stored value."""

    def test_get_output_returns_isolated_copy(self) -> None:
        ctx = StepContext(run_id="r1", policy_id="p1")
        original = {"prices": [100, 200, 300]}
        ctx.put_output("fetch_prices", original)

        retrieved = ctx.get_output("fetch_prices")
        retrieved["prices"].append(999)  # mutate the returned copy

        stored = ctx.get_output("fetch_prices")
        assert 999 not in stored["prices"], (
            "Mutation of returned value must not affect stored value"
        )


# ---------------------------------------------------------------------------
# AC-1.2: put_output() stores a deep copy
# ---------------------------------------------------------------------------


class TestPutOutputIsolation:
    """AC-1.2: Mutating original after put() does NOT change stored value."""

    def test_put_stores_isolated_copy(self) -> None:
        ctx = StepContext(run_id="r1", policy_id="p1")
        original = {"prices": [100, 200, 300]}
        ctx.put_output("fetch_prices", original)

        original["prices"].append(999)  # mutate the original

        stored = ctx.get_output("fetch_prices")
        assert 999 not in stored["prices"], (
            "Mutation of original after put must not affect stored value"
        )


# ---------------------------------------------------------------------------
# AC-1.3: Secret blocks str() and format()
# ---------------------------------------------------------------------------


class TestSecretBlocking:
    """AC-1.3: Secret blocks str(), format(), deepcopy()."""

    def test_secret_blocks_stringify(self) -> None:
        s = Secret("my-api-key")
        with pytest.raises(RuntimeError, match="must not be stringified"):
            str(s)

    def test_secret_blocks_format(self) -> None:
        s = Secret("my-api-key")
        # format() should return <REDACTED>, not the raw value
        result = format(s)
        assert result == "<REDACTED>"
        assert "my-api-key" not in result

    def test_secret_blocks_deepcopy(self) -> None:
        s = Secret("my-api-key")
        with pytest.raises(RuntimeError, match="must not be deep-copied"):
            copy.deepcopy(s)


# ---------------------------------------------------------------------------
# AC-1.4: Secret.reveal() returns the original value
# ---------------------------------------------------------------------------


class TestSecretReveal:
    """AC-1.4: Secret.reveal() returns the original value."""

    def test_secret_reveal(self) -> None:
        s = Secret("my-api-key")
        assert s.reveal() == "my-api-key"

    def test_secret_repr_is_masked(self) -> None:
        s = Secret("my-api-key")
        assert repr(s) == "Secret(***)"
        assert "my-api-key" not in repr(s)


# ---------------------------------------------------------------------------
# AC-1.5: safe_deepcopy rejects objects exceeding 10 MB
# ---------------------------------------------------------------------------


class TestSafeDeepcopySizeGuard:
    """AC-1.5: Objects > 10 MB raise ValueError."""

    def test_safe_deepcopy_rejects_oversized(self) -> None:
        # Create a large object that exceeds 10 MB
        huge = "x" * (11 * 1024 * 1024)  # 11 MB string
        with pytest.raises(ValueError, match="too large"):
            safe_deepcopy(huge)


# ---------------------------------------------------------------------------
# AC-1.6: safe_deepcopy rejects nesting > 64 levels
# ---------------------------------------------------------------------------


class TestSafeDeepcopDepthGuard:
    """AC-1.6: 65-deep nested dict raises ValueError."""

    def test_safe_deepcopy_rejects_deep_nesting(self) -> None:
        # Build a 65-deep nested dict
        obj: dict = {}
        current = obj
        for _ in range(65):
            child: dict = {}
            current["nested"] = child
            current = child
        with pytest.raises(ValueError, match="depth"):
            safe_deepcopy(obj)


# ---------------------------------------------------------------------------
# AC-1.7: safe_deepcopy handles circular references
# ---------------------------------------------------------------------------


class TestSafeDeepcopyCycleGuard:
    """AC-1.7: Cyclic reference does not infinite-loop."""

    def test_safe_deepcopy_handles_cycles(self) -> None:
        a: dict = {"key": "value"}
        b: dict = {"ref_a": a}
        a["ref_b"] = b  # cycle: a -> b -> a

        # Should not hang; deepcopy handles cycles natively
        # The size estimator must also handle cycles without infinite recursion
        result = safe_deepcopy(a)
        assert result["key"] == "value"
        assert result is not a  # it's a copy


# ---------------------------------------------------------------------------
# AC-1.8: Nested objects containing Secret raise on deepcopy
# ---------------------------------------------------------------------------


class TestSafeDeepcopSecretNested:
    """AC-1.8: Dict containing Secret raises on deepcopy."""

    def test_safe_deepcopy_secret_in_nested_obj(self) -> None:
        data = {"creds": {"api_key": Secret("sk-123")}}
        with pytest.raises(RuntimeError, match="must not be deep-copied"):
            safe_deepcopy(data)


# ---------------------------------------------------------------------------
# AC-1.9: PipelineRunner uses put_output() — no direct context.outputs[] assignment
# ---------------------------------------------------------------------------


class TestRunnerMigration:
    """AC-1.9: Verify runner no longer does direct context.outputs[x] = y."""

    def test_runner_uses_put_output(self) -> None:
        """Static analysis: pipeline_runner.py must not contain 'context.outputs[' assignment."""
        import inspect
        from zorivest_core.services import pipeline_runner

        source = inspect.getsource(pipeline_runner)
        # The pattern "context.outputs[" followed by "=" indicates direct assignment
        # We allow "context.outputs[" for reads (e.g., in conditions) but not writes
        # Look for assignment pattern specifically
        import re

        # Match: context.outputs[...] = (direct assignment)
        matches = re.findall(r"context\.outputs\[.*?\]\s*=", source)
        assert len(matches) == 0, (
            f"Found {len(matches)} direct context.outputs[] assignment(s) in "
            f"pipeline_runner.py — should use context.put_output() instead: "
            f"{matches}"
        )
