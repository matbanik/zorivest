"""Evaluates skip conditions for pipeline steps (§9.3c).

The ConditionEvaluator checks whether a ``SkipCondition`` is met by
resolving the field path from the pipeline context and comparing
against the target value using the specified operator.
"""

from __future__ import annotations

from typing import Any

from zorivest_core.domain.pipeline import (
    SkipCondition,
    SkipConditionOperator,
    StepContext,
)


class ConditionEvaluator:
    """Evaluates SkipCondition against the pipeline context."""

    def evaluate(self, condition: SkipCondition, context: StepContext) -> bool:
        """Return True if the condition is met (step should be skipped)."""
        value = self._resolve_field(condition.field, context)
        return self._compare(value, condition.operator, condition.value)

    def _resolve_field(self, field_path: str, context: StepContext) -> Any:
        """Resolve a dot-path field reference, returning None for missing keys."""
        parts = field_path.split(".")
        if parts[0] != "ctx" or len(parts) < 3:
            raise ValueError(f"Invalid field path: {field_path}")

        step_id = parts[1]
        try:
            value = context.get_output(step_id)
        except KeyError:
            return None  # Graceful None on missing step

        for part in parts[2:]:
            if isinstance(value, dict):
                value = value.get(part)  # Graceful None on missing key
            else:
                return None
        return value

    def _compare(
        self, value: Any, op: SkipConditionOperator | str, target: Any
    ) -> bool:
        """Compare value against target using the specified operator."""
        match op:
            case SkipConditionOperator.EQ:
                return value == target
            case SkipConditionOperator.NE:
                return value != target
            case SkipConditionOperator.GT:
                return value > target
            case SkipConditionOperator.LT:
                return value < target
            case SkipConditionOperator.GE:
                return value >= target
            case SkipConditionOperator.LE:
                return value <= target
            case SkipConditionOperator.IN:
                return value in target
            case SkipConditionOperator.NOT_IN:
                return value not in target
            case SkipConditionOperator.IS_NULL:
                return value is None
            case SkipConditionOperator.IS_NOT_NULL:
                return value is not None
            case _:
                raise ValueError(f"Unknown operator: {op}")
