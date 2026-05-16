"""Domain exception hierarchy for Zorivest.

Source: 03-service-layer.md §exceptions (lines 61–77)

Hierarchy:
    ZorivestError (base)
    ├── ValidationError
    ├── NotFoundError
    ├── ForbiddenError
    ├── ConflictError
    ├── BusinessRuleError
    ├── BudgetExceededError
    ├── ImportError
    ├── InvalidPassphraseError
    ├── CorruptedBackupError
    └── SyncAbortError
"""

from __future__ import annotations


class ZorivestError(Exception):
    """Base exception for all Zorivest domain errors."""


class ValidationError(ZorivestError):
    """Input validation failed (field constraints, format, range)."""


class NotFoundError(ZorivestError):
    """Requested entity does not exist."""


class ForbiddenError(ZorivestError):
    """Operation forbidden (e.g., mutating a system-protected entity)."""


class ConflictError(ZorivestError):
    """Operation conflicts with current state (e.g., deleting entity with dependents)."""


class BusinessRuleError(ZorivestError):
    """A domain business rule was violated."""


class BudgetExceededError(ZorivestError):
    """Spending or position budget was exceeded."""


class ImportError(ZorivestError):  # noqa: A001 — shadows builtin intentionally
    """File import parsing or format detection failed."""


class InvalidPassphraseError(ZorivestError):
    """Passphrase decryption failed (wrong passphrase for backup/DB)."""


class CorruptedBackupError(ZorivestError):
    """Backup file is corrupted (hash mismatch, invalid manifest)."""


class SyncAbortError(ZorivestError):
    """Tax lot sync aborted due to conflict resolution policy (block mode)."""
