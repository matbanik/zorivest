"""Domain exception hierarchy for Zorivest.

Source: 03-service-layer.md §exceptions (lines 61–77)

Hierarchy:
    ZorivestError (base)
    ├── ValidationError
    ├── NotFoundError
    ├── BusinessRuleError
    ├── BudgetExceededError
    └── ImportError
"""

from __future__ import annotations


class ZorivestError(Exception):
    """Base exception for all Zorivest domain errors."""


class ValidationError(ZorivestError):
    """Input validation failed (field constraints, format, range)."""


class NotFoundError(ZorivestError):
    """Requested entity does not exist."""


class BusinessRuleError(ZorivestError):
    """A domain business rule was violated."""


class BudgetExceededError(ZorivestError):
    """Spending or position budget was exceeded."""


class ImportError(ZorivestError):  # noqa: A001 — shadows builtin intentionally
    """File import parsing or format detection failed."""
