"""Tests for RefResolver and ConditionEvaluator (MEU-84).

Covers:
- RefResolver: AC-1 through AC-6
- ConditionEvaluator: AC-7 through AC-10
"""

from __future__ import annotations

import pytest

from zorivest_core.domain.pipeline import (
    SkipCondition,
    SkipConditionOperator,
    StepContext,
)
from zorivest_core.services.condition_evaluator import ConditionEvaluator
from zorivest_core.services.ref_resolver import RefResolver


def _make_context(**outputs: dict) -> StepContext:
    """Helper to build a StepContext with pre-populated outputs."""
    return StepContext(
        run_id="test-run",
        policy_id="test-policy",
        outputs=outputs,
    )


# ── RefResolver Tests ─────────────────────────────────────────────────────


class TestRefResolver:
    """AC-1 through AC-6 for RefResolver."""

    def setup_method(self):
        self.resolver = RefResolver()

    # AC-1: resolve() returns new dict with refs replaced
    def test_resolve_simple_ref(self):
        ctx = _make_context(
            fetch_data={"quotes": [1, 2, 3], "count": 3}
        )
        params = {"data": {"ref": "ctx.fetch_data"}}
        result = self.resolver.resolve(params, ctx)
        assert result["data"] == {"quotes": [1, 2, 3], "count": 3}

    # AC-2: Nested dict traversal
    def test_resolve_nested_path(self):
        ctx = _make_context(
            fetch_prices={"output": {"nested": {"key": "found"}}}
        )
        params = {"target": {"ref": "ctx.fetch_prices.output.nested.key"}}
        result = self.resolver.resolve(params, ctx)
        assert result["target"] == "found"

    # AC-3: List index traversal
    def test_resolve_list_index(self):
        ctx = _make_context(
            fetch_data={"items": ["a", "b", "c"]}
        )
        params = {"first": {"ref": "ctx.fetch_data.items.0"}}
        result = self.resolver.resolve(params, ctx)
        assert result["first"] == "a"

    # AC-4: Non-ref dicts traversed recursively
    def test_non_ref_dict_traversed(self):
        ctx = _make_context(step1={"val": 42})
        params = {
            "config": {"setting": "keep_this", "nested": {"ref": "ctx.step1.val"}},
        }
        result = self.resolver.resolve(params, ctx)
        assert result["config"]["setting"] == "keep_this"
        assert result["config"]["nested"] == 42

    # AC-4: Lists with mixed refs
    def test_list_with_refs(self):
        ctx = _make_context(s1={"a": 1})
        params = {"items": [{"ref": "ctx.s1.a"}, "literal", 42]}
        result = self.resolver.resolve(params, ctx)
        assert result["items"] == [1, "literal", 42]

    # AC-5: Missing step raises KeyError
    def test_missing_step_raises_keyerror(self):
        ctx = _make_context()
        params = {"val": {"ref": "ctx.nonexistent"}}
        with pytest.raises(KeyError):
            self.resolver.resolve(params, ctx)

    # AC-5: Missing nested key raises KeyError
    def test_missing_nested_key_raises_keyerror(self):
        ctx = _make_context(s1={"a": 1})
        params = {"val": {"ref": "ctx.s1.b"}}
        with pytest.raises(KeyError):
            self.resolver.resolve(params, ctx)

    # AC-6: Invalid ref format raises ValueError
    def test_invalid_ref_no_ctx_prefix(self):
        ctx = _make_context(s1={"a": 1})
        params = {"val": {"ref": "invalid.path"}}
        with pytest.raises(ValueError, match="Invalid ref"):
            self.resolver.resolve(params, ctx)

    # AC-6: Ref with only "ctx" (no step_id)
    def test_invalid_ref_only_ctx(self):
        ctx = _make_context()
        params = {"val": {"ref": "ctx"}}
        with pytest.raises(ValueError, match="Invalid ref"):
            self.resolver.resolve(params, ctx)

    # Edge: no refs in params → passthrough
    def test_no_refs_passthrough(self):
        ctx = _make_context()
        params = {"a": 1, "b": "text", "c": [1, 2]}
        result = self.resolver.resolve(params, ctx)
        assert result == params

    # Edge: dict with "ref" key but also other keys → not a ref
    def test_dict_with_ref_and_other_keys_not_a_ref(self):
        ctx = _make_context()
        params = {"x": {"ref": "ctx.step1", "extra": True}}
        result = self.resolver.resolve(params, ctx)
        assert result == params  # Should NOT resolve — it's a regular dict


# ── ConditionEvaluator Tests ──────────────────────────────────────────────


class TestConditionEvaluator:
    """AC-7 through AC-10 for ConditionEvaluator."""

    def setup_method(self):
        self.evaluator = ConditionEvaluator()

    def _cond(self, field: str, op: str, value=None) -> SkipCondition:
        return SkipCondition(field=field, operator=SkipConditionOperator(op), value=value)

    # AC-7: All 10 operators
    def test_eq(self):
        ctx = _make_context(s1={"count": 5})
        assert self.evaluator.evaluate(self._cond("ctx.s1.count", "eq", 5), ctx) is True
        assert self.evaluator.evaluate(self._cond("ctx.s1.count", "eq", 3), ctx) is False

    def test_ne(self):
        ctx = _make_context(s1={"count": 5})
        assert self.evaluator.evaluate(self._cond("ctx.s1.count", "ne", 3), ctx) is True
        assert self.evaluator.evaluate(self._cond("ctx.s1.count", "ne", 5), ctx) is False

    def test_gt(self):
        ctx = _make_context(s1={"count": 5})
        assert self.evaluator.evaluate(self._cond("ctx.s1.count", "gt", 3), ctx) is True
        assert self.evaluator.evaluate(self._cond("ctx.s1.count", "gt", 5), ctx) is False

    def test_lt(self):
        ctx = _make_context(s1={"count": 5})
        assert self.evaluator.evaluate(self._cond("ctx.s1.count", "lt", 10), ctx) is True
        assert self.evaluator.evaluate(self._cond("ctx.s1.count", "lt", 5), ctx) is False

    def test_ge(self):
        ctx = _make_context(s1={"count": 5})
        assert self.evaluator.evaluate(self._cond("ctx.s1.count", "ge", 5), ctx) is True
        assert self.evaluator.evaluate(self._cond("ctx.s1.count", "ge", 6), ctx) is False

    def test_le(self):
        ctx = _make_context(s1={"count": 5})
        assert self.evaluator.evaluate(self._cond("ctx.s1.count", "le", 5), ctx) is True
        assert self.evaluator.evaluate(self._cond("ctx.s1.count", "le", 4), ctx) is False

    def test_in(self):
        ctx = _make_context(s1={"status": "active"})
        assert self.evaluator.evaluate(
            self._cond("ctx.s1.status", "in", ["active", "paused"]), ctx
        ) is True
        assert self.evaluator.evaluate(
            self._cond("ctx.s1.status", "in", ["stopped"]), ctx
        ) is False

    def test_not_in(self):
        ctx = _make_context(s1={"status": "active"})
        assert self.evaluator.evaluate(
            self._cond("ctx.s1.status", "not_in", ["stopped"]), ctx
        ) is True
        assert self.evaluator.evaluate(
            self._cond("ctx.s1.status", "not_in", ["active"]), ctx
        ) is False

    def test_is_null(self):
        ctx = _make_context(s1={"data": None})
        assert self.evaluator.evaluate(self._cond("ctx.s1.data", "is_null"), ctx) is True
        ctx2 = _make_context(s1={"data": "value"})
        assert self.evaluator.evaluate(self._cond("ctx.s1.data", "is_null"), ctx2) is False

    def test_is_not_null(self):
        ctx = _make_context(s1={"data": "value"})
        assert self.evaluator.evaluate(self._cond("ctx.s1.data", "is_not_null"), ctx) is True
        ctx2 = _make_context(s1={"data": None})
        assert self.evaluator.evaluate(self._cond("ctx.s1.data", "is_not_null"), ctx2) is False

    # AC-8: Returns True when condition is met (step should be skipped)
    def test_returns_true_when_met(self):
        ctx = _make_context(s1={"done": True})
        result = self.evaluator.evaluate(self._cond("ctx.s1.done", "eq", True), ctx)
        assert result is True
        # Value: also verify False case returns False
        result_false = self.evaluator.evaluate(self._cond("ctx.s1.done", "eq", False), ctx)
        assert result_false is False

    # AC-9: Missing field resolves to None
    def test_missing_field_resolves_to_none(self):
        ctx = _make_context(s1={"a": 1})
        # "missing_key" doesn't exist → resolves to None → is_null should be True
        assert self.evaluator.evaluate(
            self._cond("ctx.s1.missing_key", "is_null"), ctx
        ) is True
        # Value: also verify is_not_null returns False for missing field
        assert self.evaluator.evaluate(
            self._cond("ctx.s1.missing_key", "is_not_null"), ctx
        ) is False

    # AC-9: Missing step in context → gracefully None via _resolve_field
    def test_missing_step_resolves_to_none(self):
        ctx = _make_context()
        # ConditionEvaluator._resolve_field should handle missing step gracefully
        # by returning None (unlike RefResolver which raises)
        assert self.evaluator.evaluate(
            self._cond("ctx.nonexistent.field", "is_null"), ctx
        ) is True
        # Value: verify eq comparison with None also works
        assert self.evaluator.evaluate(
            self._cond("ctx.nonexistent.field", "eq", None), ctx
        ) is True

    # AC-10: Unknown operator raises ValueError
    def test_unknown_operator_raises_valueerror(self):
        # Can't create SkipCondition with invalid op via enum, test _compare directly
        with pytest.raises(ValueError, match="Unknown operator|Unsupported operator|invalid_op"):
            self.evaluator._compare(5, "invalid_op", 3)
