# tests/unit/test_step_registry.py
"""MEU-79: Step type registry tests (Red phase)."""

from __future__ import annotations

import asyncio
import pytest
from typing import Any

from zorivest_core.domain.step_registry import (
    STEP_REGISTRY,
    RegisteredStep,
    StepBase,
    get_all_steps,
    get_step,
    has_step,
    list_steps,
)
from zorivest_core.domain.pipeline import StepContext, StepResult
from zorivest_core.domain.enums import PipelineStatus


# ---------------------------------------------------------------------------
# Fixtures — create isolated test steps, clean up registry between tests
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _clean_registry() -> Any:
    """Save and restore STEP_REGISTRY around each test."""
    saved = dict(STEP_REGISTRY)
    STEP_REGISTRY.clear()
    yield
    STEP_REGISTRY.clear()
    STEP_REGISTRY.update(saved)


def _make_step_class(name: str, *, side_effects: bool = False) -> type:
    """Dynamically create a RegisteredStep subclass."""
    return type(
        f"Test{name.title()}Step",
        (RegisteredStep,),
        {"type_name": name, "side_effects": side_effects},
    )


# ---------------------------------------------------------------------------
# AC-1: RegisteredStep subclasses auto-register via __init_subclass__
# ---------------------------------------------------------------------------


class TestAutoRegistration:
    def test_subclass_registers(self) -> None:
        cls = _make_step_class("test_fetch")
        assert "test_fetch" in STEP_REGISTRY
        assert STEP_REGISTRY["test_fetch"] is cls

    def test_empty_type_name_skipped(self) -> None:
        """Base class (empty type_name) should not register."""

        class _NoName(RegisteredStep):
            pass

        assert "" not in STEP_REGISTRY

    def test_multiple_registrations(self) -> None:
        _make_step_class("alpha")
        _make_step_class("beta")
        assert len(STEP_REGISTRY) == 2


# ---------------------------------------------------------------------------
# AC-2: Duplicate type_name raises ValueError
# ---------------------------------------------------------------------------


class TestDuplicateDetection:
    def test_duplicate_raises(self) -> None:
        _make_step_class("dupe")
        with pytest.raises(ValueError, match="Duplicate step type"):
            _make_step_class("dupe")


# ---------------------------------------------------------------------------
# AC-3: get_step() returns class or None
# ---------------------------------------------------------------------------


class TestGetStep:
    def test_existing(self) -> None:
        cls = _make_step_class("lookup")
        assert get_step("lookup") is cls

    def test_missing(self) -> None:
        assert get_step("nonexistent") is None


# ---------------------------------------------------------------------------
# AC-4: has_step() returns bool
# ---------------------------------------------------------------------------


class TestHasStep:
    def test_existing(self) -> None:
        _make_step_class("exists")
        assert has_step("exists") is True

    def test_missing(self) -> None:
        assert has_step("nope") is False


# ---------------------------------------------------------------------------
# AC-5: list_steps() returns list of dicts
# ---------------------------------------------------------------------------


class TestListSteps:
    def test_returns_dicts(self) -> None:
        _make_step_class("s1", side_effects=True)
        _make_step_class("s2")
        result = list_steps()
        assert len(result) == 2
        assert all(isinstance(d, dict) for d in result)
        names = {d["type_name"] for d in result}
        assert names == {"s1", "s2"}

    def test_dict_keys(self) -> None:
        _make_step_class("check_keys")
        result = list_steps()
        assert len(result) == 1
        d = result[0]
        assert "type_name" in d
        assert "side_effects" in d
        assert "params_schema" in d

    def test_side_effects_value(self) -> None:
        _make_step_class("with_effects", side_effects=True)
        result = list_steps()
        assert result[0]["side_effects"] is True


# ---------------------------------------------------------------------------
# AC-6: Base execute() raises NotImplementedError
# AC-6b: tagged with # noqa: placeholder
# ---------------------------------------------------------------------------


class TestBaseExecute:
    def test_base_execute_raises(self) -> None:
        step = RegisteredStep()
        ctx = StepContext(run_id="r1", policy_id="p1")
        with pytest.raises(NotImplementedError):
            asyncio.run(step.execute({}, ctx))


# ---------------------------------------------------------------------------
# AC-7: Default compensate() is a no-op
# ---------------------------------------------------------------------------


class TestCompensate:
    def test_default_compensate_noop(self) -> None:
        step = RegisteredStep()
        ctx = StepContext(run_id="r1", policy_id="p1")
        result = StepResult(status=PipelineStatus.SUCCESS)
        # Should not raise
        asyncio.run(step.compensate({}, ctx, result))


# ---------------------------------------------------------------------------
# AC-8: params_schema() returns JSON schema or empty dict
# ---------------------------------------------------------------------------


class TestParamsSchema:
    def test_no_params_class(self) -> None:
        _make_step_class("no_params")
        cls = get_step("no_params")
        assert cls is not None
        assert cls.params_schema() == {}

    def test_with_params_class(self) -> None:
        from pydantic import BaseModel

        class WithParams(RegisteredStep):
            type_name = "with_params"

            class Params(BaseModel):
                provider: str
                count: int = 10

        schema = WithParams.params_schema()
        assert "properties" in schema
        assert "provider" in schema["properties"]
        assert "count" in schema["properties"]


# ---------------------------------------------------------------------------
# AC-9: StepBase Protocol is @runtime_checkable
# ---------------------------------------------------------------------------


class TestStepBaseProtocol:
    def test_runtime_checkable(self) -> None:
        """RegisteredStep should satisfy StepBase Protocol."""
        step = RegisteredStep()
        assert isinstance(step, StepBase)

    def test_stepbase_importable_from_pipeline(self) -> None:
        """Finding 3 regression: spec imports StepBase from pipeline module."""
        from zorivest_core.domain.pipeline import StepBase as PipelineStepBase

        assert PipelineStepBase is StepBase


# ---------------------------------------------------------------------------
# AC-10: get_all_steps() returns step classes (spec §9.5 contract)
# ---------------------------------------------------------------------------


class TestGetAllSteps:
    def test_returns_classes(self) -> None:
        """get_all_steps returns step classes, not dicts."""
        cls = _make_step_class("class_test")
        result = get_all_steps()
        assert len(result) == 1
        assert result[0] is cls

    def test_classes_have_attributes(self) -> None:
        """Returned classes must support s.type_name and s.params_schema()."""
        _make_step_class("attr_test", side_effects=True)
        result = get_all_steps()
        step_cls = result[0]
        assert step_cls.type_name == "attr_test"
        assert step_cls.side_effects is True
        assert isinstance(step_cls.params_schema(), dict)

    def test_multiple_classes(self) -> None:
        _make_step_class("c1")
        _make_step_class("c2")
        result = get_all_steps()
        names = {cls.type_name for cls in result}
        assert names == {"c1", "c2"}

