# tests/unit/test_pipeline_enums.py
"""MEU-77: Pipeline enum tests (Red phase — these must FAIL before implementation)."""

from __future__ import annotations

import pytest
from enum import StrEnum

from zorivest_core.domain.enums import (
    DataType,
    PipelineStatus,
    StepErrorMode,
)

# ---------------------------------------------------------------------------
# AC-1: PipelineStatus is a StrEnum with 6 members
# ---------------------------------------------------------------------------


class TestPipelineStatus:
    """Tests for PipelineStatus enum — Spec §9.1a."""

    def test_is_str_enum(self) -> None:
        assert issubclass(PipelineStatus, StrEnum)

    def test_member_count(self) -> None:
        assert len(PipelineStatus) == 6

    @pytest.mark.parametrize(
        "member, value",
        [
            (PipelineStatus.PENDING, "pending"),
            (PipelineStatus.RUNNING, "running"),
            (PipelineStatus.SUCCESS, "success"),
            (PipelineStatus.FAILED, "failed"),
            (PipelineStatus.SKIPPED, "skipped"),
            (PipelineStatus.CANCELLED, "cancelled"),
        ],
    )
    def test_member_values(self, member: PipelineStatus, value: str) -> None:
        assert member.value == value

    def test_string_conversion(self) -> None:
        """StrEnum members should be directly usable as strings."""
        assert str(PipelineStatus.PENDING) == "pending"
        assert f"{PipelineStatus.RUNNING}" == "running"

    def test_membership_lookup(self) -> None:
        assert PipelineStatus("pending") is PipelineStatus.PENDING


# ---------------------------------------------------------------------------
# AC-2: StepErrorMode is a StrEnum with 3 members
# ---------------------------------------------------------------------------


class TestStepErrorMode:
    """Tests for StepErrorMode enum — Spec §9.1b."""

    def test_is_str_enum(self) -> None:
        assert issubclass(StepErrorMode, StrEnum)

    def test_member_count(self) -> None:
        assert len(StepErrorMode) == 3

    @pytest.mark.parametrize(
        "member, value",
        [
            (StepErrorMode.FAIL_PIPELINE, "fail_pipeline"),
            (StepErrorMode.LOG_AND_CONTINUE, "log_and_continue"),
            (StepErrorMode.RETRY_THEN_FAIL, "retry_then_fail"),
        ],
    )
    def test_member_values(self, member: StepErrorMode, value: str) -> None:
        assert member.value == value

    def test_string_conversion(self) -> None:
        assert str(StepErrorMode.FAIL_PIPELINE) == "fail_pipeline"

    def test_membership_lookup(self) -> None:
        assert StepErrorMode("log_and_continue") is StepErrorMode.LOG_AND_CONTINUE


# ---------------------------------------------------------------------------
# AC-3: DataType is a StrEnum with 4 members (Spec §9.4a line 1384)
# ---------------------------------------------------------------------------


class TestDataType:
    """Tests for DataType enum — Spec §9.4a."""

    def test_is_str_enum(self) -> None:
        assert issubclass(DataType, StrEnum)

    def test_member_count(self) -> None:
        assert len(DataType) == 4

    @pytest.mark.parametrize(
        "member, value",
        [
            (DataType.QUOTE, "quote"),
            (DataType.OHLCV, "ohlcv"),
            (DataType.NEWS, "news"),
            (DataType.FUNDAMENTALS, "fundamentals"),
        ],
    )
    def test_member_values(self, member: DataType, value: str) -> None:
        assert member.value == value

    def test_string_conversion(self) -> None:
        assert str(DataType.OHLCV) == "ohlcv"

    def test_membership_lookup(self) -> None:
        assert DataType("fundamentals") is DataType.FUNDAMENTALS


# ---------------------------------------------------------------------------
# AC-4: All 3 enums live in enums.py (verified by imports above)
# AC-5: String values use snake_case lowercase
# ---------------------------------------------------------------------------


class TestSnakeCaseValues:
    """AC-5: all enum values should be lowercase snake_case."""

    @pytest.mark.parametrize("enum_cls", [PipelineStatus, StepErrorMode, DataType])
    def test_values_are_lowercase(self, enum_cls: type[StrEnum]) -> None:
        for member in enum_cls:
            assert member.value == member.value.lower(), (
                f"{enum_cls.__name__}.{member.name} value is not lowercase"
            )

    @pytest.mark.parametrize("enum_cls", [PipelineStatus, StepErrorMode, DataType])
    def test_values_are_snake_case(self, enum_cls: type[StrEnum]) -> None:
        import re
        pattern = re.compile(r"^[a-z][a-z0-9_]*$")
        for member in enum_cls:
            assert pattern.match(member.value), (
                f"{enum_cls.__name__}.{member.name} value '{member.value}' "
                "is not snake_case"
            )
