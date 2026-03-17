# tests/unit/test_exceptions.py
"""Tests for domain exception hierarchy (MEU-12, AC-12.11)."""

from __future__ import annotations

import pytest

from zorivest_core.domain.exceptions import (
    BudgetExceededError,
    BusinessRuleError,
    ImportError as ZorivestImportError,
    NotFoundError,
    ValidationError,
    ZorivestError,
)


class TestExceptionHierarchy:
    """AC-12.11: Domain exceptions hierarchy — 6 classes with correct inheritance."""

    def test_zorivest_error_is_exception(self) -> None:
        assert issubclass(ZorivestError, Exception)
        err = ZorivestError("base error")
        assert str(err) == "base error"
        assert isinstance(err, Exception)

    def test_validation_error_inherits_zorivest_error(self) -> None:
        assert issubclass(ValidationError, ZorivestError)
        err = ValidationError("invalid input")
        assert str(err) == "invalid input"
        assert isinstance(err, ZorivestError)

    def test_not_found_error_inherits_zorivest_error(self) -> None:
        assert issubclass(NotFoundError, ZorivestError)
        err = NotFoundError("not found")
        assert str(err) == "not found"
        assert isinstance(err, ZorivestError)

    def test_business_rule_error_inherits_zorivest_error(self) -> None:
        assert issubclass(BusinessRuleError, ZorivestError)
        err = BusinessRuleError("rule violated")
        assert str(err) == "rule violated"
        assert isinstance(err, ZorivestError)

    def test_budget_exceeded_error_inherits_zorivest_error(self) -> None:
        assert issubclass(BudgetExceededError, ZorivestError)
        err = BudgetExceededError("budget exceeded")
        assert str(err) == "budget exceeded"
        assert isinstance(err, ZorivestError)

    def test_import_error_inherits_zorivest_error(self) -> None:
        assert issubclass(ZorivestImportError, ZorivestError)
        err = ZorivestImportError("import failed")
        assert str(err) == "import failed"
        assert isinstance(err, ZorivestError)

    def test_hierarchy_has_exactly_six_classes(self) -> None:
        """Verify all 6 exception classes exist and are distinct."""
        classes = {
            ZorivestError,
            ValidationError,
            NotFoundError,
            BusinessRuleError,
            BudgetExceededError,
            ZorivestImportError,
        }
        assert len(classes) == 6

    def test_all_exceptions_are_catchable_as_zorivest_error(self) -> None:
        for exc_cls in (
            ValidationError,
            NotFoundError,
            BusinessRuleError,
            BudgetExceededError,
            ZorivestImportError,
        ):
            with pytest.raises(ZorivestError):
                raise exc_cls("test message")

    def test_exception_message_preserved(self) -> None:
        msg = "something went wrong"
        err = ValidationError(msg)
        assert str(err) == msg

    def test_import_error_does_not_shadow_builtin(self) -> None:
        """Our ImportError is namespaced under ZorivestError, not builtins."""
        assert ZorivestImportError is not builtins_import_error()


def builtins_import_error() -> type:
    """Return the builtin ImportError for comparison."""
    import builtins

    return builtins.ImportError
