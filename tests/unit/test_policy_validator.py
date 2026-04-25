# tests/unit/test_policy_validator.py
"""MEU-80: Policy validator tests (Red phase)."""

from __future__ import annotations

import pytest
from typing import Any

from zorivest_core.domain.pipeline import PolicyDocument
from zorivest_core.domain.policy_validator import (
    compute_content_hash,
    validate_policy,
)
from zorivest_core.domain.step_registry import STEP_REGISTRY, RegisteredStep


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _register_test_steps() -> Any:
    """Register test step types for validation."""
    saved = dict(STEP_REGISTRY)
    STEP_REGISTRY.clear()

    # Register mock step types
    type("FetchStep", (RegisteredStep,), {"type_name": "fetch", "side_effects": False})
    type(
        "TransformStep",
        (RegisteredStep,),
        {"type_name": "transform", "side_effects": False},
    )
    type("NotifyStep", (RegisteredStep,), {"type_name": "notify", "side_effects": True})

    yield

    STEP_REGISTRY.clear()
    STEP_REGISTRY.update(saved)


def _build_policy(**overrides: Any) -> PolicyDocument:
    defaults: dict[str, Any] = {
        "name": "test-policy",
        "trigger": {"cron_expression": "0 9 * * 1-5"},
        "steps": [{"id": "fetch_data", "type": "fetch", "params": {}}],
    }
    defaults.update(overrides)
    return PolicyDocument(**defaults)


# ---------------------------------------------------------------------------
# AC-1: validate_policy() returns empty list for valid policy
# ---------------------------------------------------------------------------


class TestValidPolicy:
    def test_valid_policy(self) -> None:
        doc = _build_policy()
        errors = validate_policy(doc)
        assert errors == []

    def test_multi_step_valid(self) -> None:
        doc = _build_policy(
            steps=[
                {"id": "fetch_data", "type": "fetch", "params": {}},
                {"id": "transform_data", "type": "transform", "params": {}},
            ]
        )
        errors = validate_policy(doc)
        assert errors == []


# ---------------------------------------------------------------------------
# AC-2: Rejects unsupported schema_version (≠ 1)
# ---------------------------------------------------------------------------


class TestSchemaVersion:
    def test_version_2_rejected(self) -> None:
        doc = _build_policy(schema_version=2)
        errors = validate_policy(doc)
        assert any(e.field == "schema_version" for e in errors)

    def test_version_1_accepted(self) -> None:
        doc = _build_policy(schema_version=1)
        errors = validate_policy(doc)
        assert not any(e.field == "schema_version" for e in errors)


# ---------------------------------------------------------------------------
# AC-3: Rejects >10 steps (Pydantic catches this too, but validator double-checks)
# ---------------------------------------------------------------------------


class TestStepCount:
    def test_ten_steps_accepted(self) -> None:
        steps = [{"id": f"s{i}", "type": "fetch", "params": {}} for i in range(10)]
        doc = _build_policy(steps=steps)
        errors = validate_policy(doc)
        assert not any(e.field == "steps" for e in errors)


# ---------------------------------------------------------------------------
# AC-4: Rejects unknown step types (not in STEP_REGISTRY)
# ---------------------------------------------------------------------------


class TestUnknownStepType:
    def test_unknown_type_rejected(self) -> None:
        doc = _build_policy(
            steps=[
                {"id": "bad_step", "type": "unknown_type", "params": {}},
            ]
        )
        errors = validate_policy(doc)
        step_errors = [e for e in errors if "Unknown step type" in e.message]
        assert len(step_errors) == 1
        assert "type" in step_errors[0].field
        assert "unknown_type" in step_errors[0].message

    def test_known_type_accepted(self) -> None:
        doc = _build_policy(
            steps=[
                {"id": "good_step", "type": "fetch", "params": {}},
            ]
        )
        errors = validate_policy(doc)
        assert errors == []  # valid policy has zero errors


# ---------------------------------------------------------------------------
# AC-5: Rejects forward references (ref to step not yet seen)
# ---------------------------------------------------------------------------


class TestReferentialIntegrity:
    def test_valid_backward_ref(self) -> None:
        doc = _build_policy(
            steps=[
                {"id": "fetch_data", "type": "fetch", "params": {}},
                {
                    "id": "transform",
                    "type": "transform",
                    "params": {
                        "input": {"ref": "ctx.fetch_data.output.data"},
                    },
                },
            ]
        )
        errors = validate_policy(doc)
        assert errors == []

    def test_forward_ref_rejected(self) -> None:
        doc = _build_policy(
            steps=[
                {
                    "id": "transform",
                    "type": "transform",
                    "params": {
                        "input": {"ref": "ctx.fetch_data.output.data"},
                    },
                },
                {"id": "fetch_data", "type": "fetch", "params": {}},
            ]
        )
        errors = validate_policy(doc)
        ref_errors = [e for e in errors if "hasn't executed yet" in e.message]
        assert len(ref_errors) == 1
        assert "fetch_data" in ref_errors[0].message

    def test_nested_ref_checked(self) -> None:
        doc = _build_policy(
            steps=[
                {
                    "id": "s1",
                    "type": "fetch",
                    "params": {
                        "nested": {"inner": {"ref": "ctx.nonexistent.output"}},
                    },
                },
            ]
        )
        errors = validate_policy(doc)
        ref_errors = [e for e in errors if "hasn't executed yet" in e.message]
        assert len(ref_errors) == 1
        assert "nonexistent" in ref_errors[0].message

    def test_malformed_ref_rejected(self) -> None:
        """Finding 1 regression: refs not starting with ctx. must be rejected."""
        doc = _build_policy(
            steps=[
                {
                    "id": "s1",
                    "type": "fetch",
                    "params": {
                        "x": {"ref": "not-a-ctx-ref"},
                    },
                },
            ]
        )
        errors = validate_policy(doc)
        fmt_errors = [e for e in errors if "Invalid ref format" in e.message]
        assert len(fmt_errors) == 1
        assert "not-a-ctx-ref" in fmt_errors[0].message

    def test_ref_in_nested_list(self) -> None:
        """Finding 2 regression: refs inside list-of-list structures must be checked."""
        doc = _build_policy(
            steps=[
                {
                    "id": "s1",
                    "type": "fetch",
                    "params": {
                        "items": [[{"ref": "ctx.missing.output"}]],
                    },
                },
            ]
        )
        errors = validate_policy(doc)
        ref_errors = [e for e in errors if "hasn't executed yet" in e.message]
        assert len(ref_errors) == 1
        assert "missing" in ref_errors[0].message

    def test_non_string_ref_rejected(self) -> None:
        """F6 regression: non-string ref values must produce ValidationError, not crash."""
        doc = _build_policy(
            steps=[
                {
                    "id": "s1",
                    "type": "fetch",
                    "params": {
                        "x": {"ref": 123},
                    },
                },
            ]
        )
        errors = validate_policy(doc)
        ref_errors = [e for e in errors if "ref value must be a string" in e.message]
        assert len(ref_errors) == 1

    def test_non_string_ref_in_list_rejected(self) -> None:
        """F6 regression: non-string ref values in lists must also be caught."""
        doc = _build_policy(
            steps=[
                {
                    "id": "s1",
                    "type": "fetch",
                    "params": {
                        "items": [{"ref": True}],
                    },
                },
            ]
        )
        errors = validate_policy(doc)
        ref_errors = [e for e in errors if "ref value must be a string" in e.message]
        assert len(ref_errors) == 1


# ---------------------------------------------------------------------------
# AC-6: Rejects invalid cron expressions
# ---------------------------------------------------------------------------


class TestCronValidation:
    def test_valid_cron(self) -> None:
        doc = _build_policy()
        errors = validate_policy(doc)
        assert errors == []

    def test_invalid_cron(self) -> None:
        doc = _build_policy(trigger={"cron_expression": "invalid cron"})
        errors = validate_policy(doc)
        cron_errors = [e for e in errors if "cron" in e.field]
        assert len(cron_errors) >= 1
        assert (
            "invalid" in cron_errors[0].message.lower()
            or "cron" in cron_errors[0].message.lower()
        )

    def test_six_field_cron(self) -> None:
        """Standard 5-field cron should work."""
        doc = _build_policy(trigger={"cron_expression": "*/5 * * * *"})
        errors = validate_policy(doc)
        assert errors == []


# ---------------------------------------------------------------------------
# AC-7: Detects SQL blocklist keywords in step params
# ---------------------------------------------------------------------------


class TestSQLBlocklist:
    def test_clean_params(self) -> None:
        doc = _build_policy(
            steps=[
                {
                    "id": "s1",
                    "type": "fetch",
                    "params": {"query": "SELECT * FROM prices"},
                },
            ]
        )
        errors = validate_policy(doc)
        assert errors == []

    def test_blocked_keyword(self) -> None:
        doc = _build_policy(
            steps=[
                {"id": "s1", "type": "fetch", "params": {"query": "DROP TABLE users"}},
            ]
        )
        errors = validate_policy(doc)
        sql_errors = [
            e
            for e in errors
            if "SQL validation failed" in e.message or "DML/DDL" in e.message
        ]
        assert len(sql_errors) >= 1

    def test_multiple_blocked(self) -> None:
        doc = _build_policy(
            steps=[
                {
                    "id": "s1",
                    "type": "fetch",
                    "params": {"q": "DELETE FROM t; INSERT INTO t VALUES(1)"},
                },
            ]
        )
        errors = validate_policy(doc)
        sql_errors = [
            e
            for e in errors
            if "SQL validation failed" in e.message or "DML/DDL" in e.message
        ]
        assert len(sql_errors) >= 1

    def test_punctuation_bypass_blocked(self) -> None:
        """F5 regression: punctuation-separated SQL keywords must be caught."""
        doc = _build_policy(
            steps=[
                {"id": "s1", "type": "fetch", "params": {"query": "DROP;TABLE users"}},
            ]
        )
        errors = validate_policy(doc)
        sql_errors = [
            e
            for e in errors
            if "SQL validation failed" in e.message or "DML/DDL" in e.message
        ]
        assert len(sql_errors) >= 1

    def test_semicolon_concat_blocked(self) -> None:
        """F5 regression: DELETE;SELECT must be caught."""
        doc = _build_policy(
            steps=[
                {
                    "id": "s1",
                    "type": "fetch",
                    "params": {"query": "DELETE;SELECT * FROM t"},
                },
            ]
        )
        errors = validate_policy(doc)
        sql_errors = [
            e
            for e in errors
            if "SQL validation failed" in e.message or "DML/DDL" in e.message
        ]
        assert len(sql_errors) >= 1


# ---------------------------------------------------------------------------
# AC-8: compute_content_hash() returns deterministic SHA-256
# ---------------------------------------------------------------------------


class TestContentHash:
    def test_deterministic(self) -> None:
        doc = _build_policy()
        h1 = compute_content_hash(doc)
        h2 = compute_content_hash(doc)
        assert h1 == h2

    def test_sha256_length(self) -> None:
        doc = _build_policy()
        h = compute_content_hash(doc)
        assert len(h) == 64  # SHA-256 hex digest

    def test_different_docs_different_hash(self) -> None:
        doc1 = _build_policy(name="policy-a")
        doc2 = _build_policy(name="policy-b")
        assert compute_content_hash(doc1) != compute_content_hash(doc2)


# ---------------------------------------------------------------------------
# AC-9: SqlSandbox.DENY_TABLES replaces SQL_BLOCKLIST as the security contract
# ---------------------------------------------------------------------------


class TestDenyTablesContract:
    """AC-9: SqlSandbox.DENY_TABLES contains required credential tables."""

    def test_deny_tables_contains_settings(self) -> None:
        from zorivest_core.services.sql_sandbox import SqlSandbox

        assert "settings" in SqlSandbox.DENY_TABLES
        assert isinstance(SqlSandbox.DENY_TABLES, frozenset)


# ---------------------------------------------------------------------------
# AC-10: Nested dict/list values in params are recursively scanned
# ---------------------------------------------------------------------------


class TestRecursiveSQLScan:
    def test_nested_dict(self) -> None:
        doc = _build_policy(
            steps=[
                {
                    "id": "s1",
                    "type": "fetch",
                    "params": {
                        "config": {"inner": {"query": "DROP TABLE users"}},
                    },
                },
            ]
        )
        errors = validate_policy(doc)
        sql_errors = [
            e
            for e in errors
            if "SQL validation failed" in e.message or "DML/DDL" in e.message
        ]
        assert len(sql_errors) >= 1

    def test_nested_list(self) -> None:
        doc = _build_policy(
            steps=[
                {
                    "id": "s1",
                    "type": "fetch",
                    "params": {
                        "items": [{"query": "DELETE FROM prices"}],
                    },
                },
            ]
        )
        errors = validate_policy(doc)
        sql_errors = [
            e
            for e in errors
            if "SQL validation failed" in e.message or "DML/DDL" in e.message
        ]
        assert len(sql_errors) >= 1

    def test_deeply_nested(self) -> None:
        doc = _build_policy(
            steps=[
                {
                    "id": "s1",
                    "type": "fetch",
                    "params": {
                        "a": {"b": [{"c": {"d": "ALTER TABLE t"}}]},
                    },
                },
            ]
        )
        errors = validate_policy(doc)
        sql_errors = [
            e
            for e in errors
            if "SQL validation failed" in e.message or "DML/DDL" in e.message
        ]
        assert len(sql_errors) >= 1


# ---------------------------------------------------------------------------
# AC-9 (MEU-PW12): Step params validated against Params model at boundary
# ---------------------------------------------------------------------------


class TestStepParamsValidation:
    """AC-9: validate_policy() rule 7: for each step with a known type in
    STEP_REGISTRY, validate step.params against the step class's Params model.
    Invalid values → ValidationError → 422 at API boundary."""

    @pytest.fixture(autouse=True)
    def _register_real_steps(self) -> Any:
        """Register step types with actual Params models for param validation."""
        from pydantic import BaseModel, Field

        saved = dict(STEP_REGISTRY)
        STEP_REGISTRY.clear()

        # Step with Params model (required fields + constrained fields)
        class FetchParams(BaseModel):
            provider: str = Field(..., description="Data provider")
            data_type: str = Field(..., description="Data type")
            batch_size: int = Field(default=100, ge=1, le=500)

        type(
            "FetchStepWithParams",
            (RegisteredStep,),
            {
                "type_name": "fetch",
                "side_effects": False,
                "Params": FetchParams,
            },
        )

        # Step with extra="forbid" (boundary strictness)
        class TransformParams(BaseModel):
            model_config = {"extra": "forbid"}

            target_table: str = Field(...)
            min_records: int = Field(default=0, ge=0)

        type(
            "TransformStepWithParams",
            (RegisteredStep,),
            {
                "type_name": "transform",
                "side_effects": False,
                "Params": TransformParams,
            },
        )

        # Step WITHOUT a Params class (should skip param validation)
        type(
            "NotifyStepNoParams",
            (RegisteredStep,),
            {
                "type_name": "notify",
                "side_effects": True,
            },
        )

        yield

        STEP_REGISTRY.clear()
        STEP_REGISTRY.update(saved)

    def test_valid_params_pass(self) -> None:
        """Valid params for known step type → no validation error."""
        doc = _build_policy(
            steps=[
                {
                    "id": "fetch_data",
                    "type": "fetch",
                    "params": {
                        "provider": "yahoo",
                        "data_type": "quote",
                        "batch_size": 50,
                    },
                },
            ]
        )
        errors = validate_policy(doc)
        param_errors = [e for e in errors if "params" in e.field.lower()]
        assert len(param_errors) == 0

    def test_invalid_value_rejected(self) -> None:
        """min_records=-1 in transform params → validation error."""
        doc = _build_policy(
            steps=[
                {
                    "id": "transform_data",
                    "type": "transform",
                    "params": {
                        "target_table": "market_quotes",
                        "min_records": -1,
                    },
                },
            ]
        )
        errors = validate_policy(doc)
        param_errors = [e for e in errors if "param" in e.field.lower()]
        assert len(param_errors) >= 1
        assert any(
            "min_records" in e.message or "-1" in e.message for e in param_errors
        )

    def test_extra_key_rejected_when_extra_forbid(self) -> None:
        """Unknown extra key in transform params (extra='forbid') → error."""
        doc = _build_policy(
            steps=[
                {
                    "id": "transform_data",
                    "type": "transform",
                    "params": {
                        "target_table": "market_quotes",
                        "unknown_field": "surprise",
                    },
                },
            ]
        )
        errors = validate_policy(doc)
        param_errors = [e for e in errors if "param" in e.field.lower()]
        assert len(param_errors) >= 1

    def test_step_without_params_class_skips_validation(self) -> None:
        """Step type without Params class → no param validation error."""
        doc = _build_policy(
            steps=[
                {
                    "id": "notify_user",
                    "type": "notify",
                    "params": {"anything": "goes", "here": True},
                },
            ]
        )
        errors = validate_policy(doc)
        # Should not have param validation errors (step has no Params model)
        param_errors = [e for e in errors if "param" in e.field.lower()]
        assert len(param_errors) == 0

    def test_missing_required_field_rejected(self) -> None:
        """Missing required field (provider, data_type) in fetch params → error."""
        doc = _build_policy(
            steps=[
                {
                    "id": "fetch_data",
                    "type": "fetch",
                    "params": {
                        # Missing 'provider' and 'data_type' which are required
                        "batch_size": 50,
                    },
                },
            ]
        )
        errors = validate_policy(doc)
        param_errors = [e for e in errors if "param" in e.field.lower()]
        assert len(param_errors) >= 1

    def test_batch_size_out_of_range_rejected(self) -> None:
        """batch_size=0 (below ge=1) → validation error."""
        doc = _build_policy(
            steps=[
                {
                    "id": "fetch_data",
                    "type": "fetch",
                    "params": {
                        "provider": "yahoo",
                        "data_type": "quote",
                        "batch_size": 0,
                    },
                },
            ]
        )
        errors = validate_policy(doc)
        param_errors = [e for e in errors if "param" in e.field.lower()]
        assert len(param_errors) >= 1
