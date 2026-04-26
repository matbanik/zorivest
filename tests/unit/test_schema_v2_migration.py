# tests/unit/test_schema_v2_migration.py
"""FIC Red-phase tests for schema v2 migration (PH7, AC-7.8–AC-7.18).

Spec: 09d-pipeline-step-extensions.md §9D.5–§9D.6
"""

from __future__ import annotations

from typing import Any

import pytest
from pydantic import ValidationError

from zorivest_core.domain.pipeline import PolicyDocument


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _trigger() -> Any:
    """Minimal valid trigger config (dict coerced by Pydantic)."""
    return {"cron_expression": "0 8 * * 1-5", "timezone": "UTC"}


def _step(step_id: str = "s1", step_type: str = "fetch", **extra: object) -> Any:
    """Minimal valid step dict (dict coerced by Pydantic)."""
    return {"id": step_id, "type": step_type, "params": {}, **extra}


# ---------------------------------------------------------------------------
# AC-7.8: Policy with 20 steps validates
# ---------------------------------------------------------------------------


def test_20_steps_validates() -> None:
    """AC-7.8: 20 steps should be accepted."""
    steps = [_step(f"s{i}", "fetch") for i in range(20)]
    doc = PolicyDocument(
        schema_version=1,
        name="big-policy",
        trigger=_trigger(),
        steps=steps,
    )
    assert len(doc.steps) == 20


# ---------------------------------------------------------------------------
# AC-7.9: Policy with 21 steps raises ValidationError
# ---------------------------------------------------------------------------


def test_21_steps_rejected() -> None:
    """AC-7.9: 21 steps should raise ValidationError."""
    steps = [_step(f"s{i}", "fetch") for i in range(21)]
    with pytest.raises(ValidationError):
        PolicyDocument(
            schema_version=1,
            name="huge-policy",
            trigger=_trigger(),
            steps=steps,
        )


# ---------------------------------------------------------------------------
# AC-7.10: v1 policy with no v2 features still validates
# ---------------------------------------------------------------------------


def test_v1_no_v2_features_validates() -> None:
    """AC-7.10: Plain v1 policy with no v2 features validates cleanly."""
    doc = PolicyDocument(
        schema_version=1,
        name="simple-v1",
        trigger=_trigger(),
        steps=[_step("s1", "fetch")],
    )
    assert doc.schema_version == 1


# ---------------------------------------------------------------------------
# AC-7.11: v2 features on v1 schema raise ValidationError
# ---------------------------------------------------------------------------


def test_variables_on_v1_rejected() -> None:
    """AC-7.11: variables field with schema_version=1 raises ValidationError."""
    with pytest.raises(ValidationError, match="schema_version"):
        PolicyDocument(
            schema_version=1,
            name="bad-v1",
            trigger=_trigger(),
            steps=[_step("s1", "fetch")],
            variables={"threshold": 0.05},
        )


def test_query_step_on_v1_rejected() -> None:
    """AC-7.11: query step type with schema_version=1 raises ValidationError."""
    with pytest.raises(ValidationError, match="schema_version"):
        PolicyDocument(
            schema_version=1,
            name="bad-v1-query",
            trigger=_trigger(),
            steps=[_step("s1", "query")],
        )


# ---------------------------------------------------------------------------
# AC-7.12: v2 features with schema_version=2 pass
# ---------------------------------------------------------------------------


def test_variables_on_v2_accepted() -> None:
    """AC-7.12: variables with schema_version=2 passes validation."""
    doc = PolicyDocument(
        schema_version=2,
        name="good-v2",
        trigger=_trigger(),
        steps=[_step("s1", "fetch")],
        variables={"threshold": 0.05},
    )
    assert doc.variables == {"threshold": 0.05}


# ---------------------------------------------------------------------------
# AC-7.13: PolicyValidator allows query/compose on v2
# ---------------------------------------------------------------------------


def test_validator_allows_query_on_v2() -> None:
    """AC-7.13: PolicyValidator should not flag query step type on v2 schema."""
    from zorivest_core.domain.policy_validator import validate_policy

    doc = PolicyDocument(
        schema_version=2,
        name="v2-query",
        trigger=_trigger(),
        steps=[_step("s1", "query")],
    )
    errors = validate_policy(doc)
    type_errors = [e for e in errors if "query" in e.message and "Unknown" in e.message]
    assert len(type_errors) == 0


# ---------------------------------------------------------------------------
# AC-7.14: PolicyValidator rejects query/compose on v1
# ---------------------------------------------------------------------------


def test_validator_rejects_query_on_v1() -> None:
    """AC-7.14: PolicyValidator rejects query step type on v1 policies.

    Note: The model_validator on PolicyDocument will catch this first.
    PolicyValidator provides defense-in-depth. This test validates
    that if the model_validator is bypassed (e.g., direct construction),
    the validator still catches it.
    """
    from zorivest_core.domain.policy_validator import validate_policy

    # Build a v2 doc then manually set schema_version back to 1
    # to test PolicyValidator's own v1 gating (bypassing model_validator)
    doc = PolicyDocument(
        schema_version=2,
        name="sneaky-v1",
        trigger=_trigger(),
        steps=[_step("s1", "query")],
    )
    doc.schema_version = 1  # Bypass model_validator
    errors = validate_policy(doc)
    v2_errors = [
        e for e in errors if "v2" in e.message.lower() or "query" in e.message.lower()
    ]
    assert len(v2_errors) > 0


# ---------------------------------------------------------------------------
# AC-7.15: PolicyValidator rejects {var: ...} refs on v1
# ---------------------------------------------------------------------------


def test_validator_rejects_var_ref_on_v1() -> None:
    """AC-7.15: PolicyValidator rejects {var: ...} refs on v1 policies."""
    from zorivest_core.domain.policy_validator import validate_policy

    # Build v2 then backdoor to v1
    doc = PolicyDocument(
        schema_version=2,
        name="sneaky-v1-vars",
        trigger=_trigger(),
        steps=[_step("s1", "fetch", params={"limit": {"var": "threshold"}})],
        variables={"threshold": 10},
    )
    doc.schema_version = 1  # Bypass model_validator
    doc.variables = {}  # Clear vars to avoid model_validator complaint
    errors = validate_policy(doc)
    var_errors = [e for e in errors if "var" in e.message.lower()]
    assert len(var_errors) > 0


# ---------------------------------------------------------------------------
# AC-7.16: PolicyValidator warns on unused variables
# ---------------------------------------------------------------------------


def test_validator_warns_unused_vars() -> None:
    """AC-7.16: PolicyValidator emits warning for unused v2 variables."""
    from zorivest_core.domain.policy_validator import validate_policy

    doc = PolicyDocument(
        schema_version=2,
        name="v2-unused",
        trigger=_trigger(),
        steps=[_step("s1", "fetch")],
        variables={"unused_var": 42},
    )
    errors = validate_policy(doc)
    warnings = [
        e for e in errors if e.severity == "warning" and "unused" in e.message.lower()
    ]
    assert len(warnings) >= 1


# ---------------------------------------------------------------------------
# AC-7.17: PolicyValidator step-count cap updated to 20
# ---------------------------------------------------------------------------


def test_validator_step_cap_20() -> None:
    """AC-7.17: PolicyValidator no longer rejects 15-step policies (old cap was 10)."""
    from zorivest_core.domain.policy_validator import validate_policy

    steps = [_step(f"s{i}", "fetch") for i in range(15)]
    doc = PolicyDocument(
        schema_version=1,
        name="fifteen-steps",
        trigger=_trigger(),
        steps=steps,
    )
    errors = validate_policy(doc)
    step_errors = [
        e for e in errors if "step" in e.message.lower() and "max" in e.message.lower()
    ]
    assert len(step_errors) == 0


# ---------------------------------------------------------------------------
# AC-7.18: PolicyDocument rejects unknown top-level fields (extra="forbid")
# ---------------------------------------------------------------------------


def test_extra_fields_rejected() -> None:
    """AC-7.18: PolicyDocument with extra='forbid' rejects unknown fields."""
    with pytest.raises(ValidationError, match="extra"):
        PolicyDocument(
            schema_version=1,
            name="extra-field-test",
            trigger=_trigger(),
            steps=[_step("s1", "fetch")],
            bogus_field="should_fail",  # type: ignore[call-arg]
        )
